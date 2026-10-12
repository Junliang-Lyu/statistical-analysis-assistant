"""StateGraph orchestration. In-process checkpoints; bounded independent retry counters."""
from typing import TypedDict, Any
import pandas as pd
import json

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt

from .agents import Plan, check_interpretation, render_interpretation
from .tools import profile, fingerprint, diagnose, compute


class State(TypedDict, total=False):
    data: Any
    question: str
    metadata: dict
    overview: dict
    dataset_id: str
    plan: dict | None
    prior_plan: dict | None
    result: dict | None
    interpretation: dict | None
    draft: dict | None
    diagnostics: dict
    feedback: list[str]
    text_feedback: list[str]
    revisions: int
    rewrites: int
    calls: int
    status: str
    trace: list[str]
    history: list[dict]
    error: str | None
    method: str | None
    mode: str


def build_graph(agents, checkpointer=None):
    def traced(s, name, **update):
        return {'trace': [*s.get('trace', []), name], **update}

    def prepare(s):
        try:
            overview = profile(pd.DataFrame(s['data'])); identity = fingerprint(pd.DataFrame(s['data']))
            prior = s.get('plan') if identity == s.get('dataset_id') else None
            return {'overview': overview, 'dataset_id': identity, 'prior_plan': prior, 'plan': None,
                    'result': None, 'interpretation': None, 'draft': None, 'diagnostics': {},
                    'feedback': [], 'text_feedback': [], 'revisions':0, 'rewrites':0, 'calls':0,
                    'status':'running', 'trace':['profile'], 'error':None, 'method':None, 'mode':agents.mode}
        except (ValueError, KeyError, TypeError) as exc:
            return {'status':'stopped','error':str(exc), 'trace':['profile'], 'result':None, 'interpretation':None}

    def planner(s):
        try:
            if s['calls'] >= 5:
                raise ValueError('Model request limit reached.')
            p = agents.plan(s['question'], s['overview'], s.get('prior_plan'), s.get('metadata', {}), s['feedback'])
            p = Plan.model_validate(p).model_dump()
            # LLM may NOT invent design: these values come only from explicit user metadata.
            m = s.get('metadata', {})
            p['design'] = m.get('design', 'unknown'); p['study_type'] = m.get('study_type','unknown')
            if m.get('filter'):
                p['filter'] = m['filter']
            p = Plan.model_validate(p).model_dump()
            return traced(s,'planner', plan=p, calls=s['calls']+1, error=None)
        except Exception as exc:
            return traced(s,'planner', plan=None, calls=s['calls']+1, error='Planner failed: '+str(exc))

    def after_planner(s):
        if s.get('error'):
            return 'revise' if s['revisions'] < 1 else 'report_issue'
        p = s['plan']
        missing = (p['goal']=='difference' and (not p['outcome'] or not p['group'])) or (
            p['goal'] in ('correlation','categorical','regression') and (not p['x'] or not p['y']))
        return 'ask_user' if p.get('clarification') or (p['goal']!='unsupported' and (p['design']=='unknown' or missing)) else 'select_method'

    def ask_user(s):
        # Separate node: resume replays only this node, not the paid Planner call.
        answer = interrupt({'question': s['plan'].get('clarification') or
            'Confirm independent/paired/clustered design, study type and variable roles.',
            'plan':s['plan'], 'accepted_keys':['design','study_type','outcome','group','x','y','filter']})
        try:
            if not isinstance(answer,dict):
                raise ValueError('Clarification must be a dictionary.')
            allowed = {'design','study_type','outcome','group','x','y','filter'}
            if set(answer)-allowed:
                raise ValueError('Unknown clarification field.')
            p = Plan.model_validate({**s['plan'], **answer, 'clarification': None}).model_dump()
            p['reason'] = (f"After user clarification: goal={p['goal']}; design={p['design']}; study_type={p['study_type']}; "
                           f"variable roles: outcome={p['outcome']}, group={p['group']}, x={p['x']}, y={p['y']}. "
                           'Current user confirmations supersede the earlier missing-information assessment; method rules still require checks.')
            if p['design']=='unknown':
                raise ValueError('Design still unknown; restart with clarified metadata.')
            return traced(s,'ask_user', plan=p, metadata={**s.get('metadata', {}), **answer}, error=None)
        except ValueError as exc:
            return traced(s,'ask_user', error=str(exc), status='stopped')

    def select(s):
        p=s['plan']
        return traced(s,'select_method', method={'difference':'welch_t_test','correlation':'pearson',
            'categorical':'chi_square','regression':'linear_regression'}.get(p['goal']))

    def checks(s):
        d=diagnose(pd.DataFrame(s['data']),s['plan'])
        return traced(s,'check_assumptions', diagnostics=d, feedback=d['errors'], error=None)

    def after_checks(s):
        if not s['diagnostics']['errors']:
            return 'run_test'
        # Only repair plan/column selection. Never silently change a design or estimand.
        p=s['plan']; issues=' '.join(s['diagnostics']['errors']).lower()
        repairable = 'existing columns' in issues or 'must be numeric' in issues
        return 'revise' if repairable and s['revisions']<1 else 'report_issue'

    def revise(s):
        return traced(s,'revise', revisions=s['revisions']+1,
                      feedback=s.get('feedback') or [s.get('error') or 'Correct the plan.'], error=None)

    def run(s):
        try:
            return traced(s,'run_test',result=compute(pd.DataFrame(s['data']),s['plan']))
        except (ValueError,TypeError) as exc:
            return traced(s,'run_test',error=str(exc))

    def interpret(s):
        try:
            if s['calls']>=5:
                raise ValueError('Model request limit reached.')
            draft=agents.interpret(s['plan'],s['result'],s['text_feedback'])
            return traced(s,'interpret',draft=draft,calls=s['calls']+1,error=None)
        except Exception as exc:
            return traced(s,'interpret',draft={},calls=s['calls']+1,error='Interpreter failed: '+str(exc))

    def critique(s):
        issues=[s['error']] if s.get('error') else check_interpretation(s['draft'],s['result'])
        return traced(s,'critique',text_feedback=issues)

    def rewrite(s):
        return traced(s,'rewrite',rewrites=s['rewrites']+1,error=None,
                      text_feedback=[*s['text_feedback'], 'Previous rejected draft: '+json.dumps(s['draft'], ensure_ascii=False)])

    def report(s):
        return traced(s,'report_issue',status='stopped',result=None,interpretation=None,
                      error=s.get('error') or '; '.join(s.get('feedback',[])) or 'Unsupported analysis.')

    def finish(s):
        valid=not s['text_feedback']
        text=render_interpretation(s['draft'],s['result']) if valid else None
        record={'dataset_id':s['dataset_id'],'question':s['question'],'plan':s['plan'],
                'result':s['result'],'interpretation':text,'mode':agents.mode}
        return traced(s,'output_memory',status='completed' if valid else 'results_only',interpretation=text,
                      history=[*s.get('history',[]),record][-10:],
                      error=None if valid else 'Interpretation withheld after one rewrite: '+'; '.join(s['text_feedback']))

    g=StateGraph(State)
    for name,fn in [('profile',prepare),('planner',planner),('ask_user',ask_user),('select_method',select),
                    ('check_assumptions',checks),('revise',revise),('run_test',run),('interpret',interpret),
                    ('critique',critique),('rewrite',rewrite),('report_issue',report),('output_memory',finish)]:
        g.add_node(name,fn)
    g.add_edge(START,'profile')
    g.add_conditional_edges('profile',lambda s:'planner' if s['status']=='running' else 'report_issue', ['planner','report_issue'])
    g.add_conditional_edges('planner',after_planner,['ask_user','select_method','revise','report_issue'])
    g.add_conditional_edges('ask_user',lambda s:'report_issue' if s.get('error') else ('planner' if s['plan']['goal']=='unsupported' else 'select_method'),['report_issue','planner','select_method'])
    g.add_edge('select_method','check_assumptions')
    g.add_conditional_edges('check_assumptions',after_checks,['run_test','revise','report_issue'])
    g.add_edge('revise','planner')
    g.add_conditional_edges('run_test',lambda s:'report_issue' if s.get('error') else 'interpret',['report_issue','interpret'])
    g.add_edge('interpret','critique')
    g.add_conditional_edges('critique',lambda s:'rewrite' if s['text_feedback'] and s['rewrites']<1 else 'output_memory',['rewrite','output_memory'])
    g.add_edge('rewrite','interpret')
    g.add_edge('report_issue',END); g.add_edge('output_memory',END)
    return g.compile(checkpointer=checkpointer or InMemorySaver())

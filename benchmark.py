"""Small live evaluation with prespecified expectations, not a statistical safety certification."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from langgraph.types import Command

from demo import fixtures, public_result
from stat_assistant.agents import DeepSeekAgents, load_local_env
from stat_assistant.workflow import build_graph

ROOT = Path(__file__).resolve().parent


def cases():
    trial, corr = fixtures()
    rng = np.random.default_rng(20261010)
    unequal = pd.DataFrame({'arm': ['A']*40+['B']*40,
                            'score': np.r_[rng.normal(0,.5,40),rng.normal(1,3,40)]})
    missing = trial.copy(); missing.loc[[0,26], 'outcome'] = np.nan
    ambiguous = trial.rename(columns={'outcome':'score_before'})
    ambiguous['score_after'] = ambiguous.score_before + rng.normal(0,1,50)
    x = np.linspace(-2,2,40)
    nonlinear = pd.DataFrame({'x':x,'y':x*x})
    metadata = {'design':'independent','study_type':'observational'}

    def case(name, data, question, expected, **extra):
        return {'id': name, 'data':data, 'question':question, 'metadata':dict(metadata),
                'expected':expected, **extra}

    return [
        case('welch_clean',trial,'Compare mean outcome between treatment and control.',
             {'status':['completed'],'goal':['difference'],'roles':{'outcome':'outcome','group':'group'},'n':50}),
        case('welch_unequal_variances',unequal,'Is the mean score different between arm A and arm B?',
             {'status':['completed'],'goal':['difference'],'roles':{'outcome':'score','group':'arm'},'n':80}),
        case('missing_complete_cases',missing,'Compare the mean outcome between the two groups.',
             {'status':['completed'],'goal':['difference'],'roles':{'outcome':'outcome','group':'group'},'n':48}),
        case('pearson_clean',corr,'Measure the linear association between x and y using Pearson correlation.',
             {'status':['completed'],'goal':['correlation'],'roles':{'x':'x','y':'y'},'n':20}),
        {**case('unknown_design',trial,'Compare mean outcome between groups.',
             {'status':['completed'],'goal':['difference'],'roles':{'outcome':'outcome','group':'group'},'n':50}),
             'metadata':{},'must_interrupt':True,'answer':metadata},
        case('ambiguous_outcome',ambiguous,'Compare the outcome between groups; I have not decided which score to use.',
             {'status':['interrupted'],'goal':['difference','unsupported']},must_interrupt=True),
        case('unsupported_regression',corr,'Fit a simple linear regression of y on x and report its slope.',
             {'status':['stopped'],'goal':['unsupported']}),
        {**case('paired_design',trial,'Compare mean outcome between groups.',
             {'status':['stopped'],'goal':['difference','unsupported']}),'metadata':{'design':'paired'}},
        case('constant_variable',pd.DataFrame({'x':[1.]*10,'y':range(10)}),'Compute Pearson correlation between x and y.',
             {'status':['stopped'],'goal':['correlation','unsupported']}),
        case('too_few_pairs',pd.DataFrame({'x':[1.,2.,3.],'y':[2.,4.,5.]}),'Compute Pearson correlation between x and y.',
             {'status':['stopped'],'goal':['correlation','unsupported']}),
        case('ambiguous_last_year',corr,'Only look at the last year of that correlation.',
             {'status':['interrupted'],'goal':['correlation','unsupported']},
             warmup=True,must_interrupt=True),
        case('nonlinear_boundary',nonlinear,'Does x have a relationship with y? Assess using Pearson linear correlation.',
             {'status':['completed'],'goal':['correlation'],'roles':{'x':'x','y':'y'},'n':40},
             note='Pearson tests linear association only. U-shaped dependence is present. Interpretation needs manual review; absence of linear evidence does not mean no relationship.'),
    ]


def score(case, state, interrupted):
    expected=case['expected']; p=state.get('plan') or {}; result=state.get('result')
    checks={'outcome':state.get('status') in expected['status'],
            'goal':p.get('goal') in expected['goal']}
    if case.get('must_interrupt'):
        checks['clarification']=interrupted
    if expected.get('roles'):
        checks['roles']=all(p.get(k)==v for k,v in expected['roles'].items())
    if 'n' in expected:
        checks['sample_count']=bool(result and result['n']==expected['n'])
        checks['numeric_reference']=False
        if result and checks.get('roles'):
            d=case['data']; roles=expected['roles']
            if p['goal']=='difference':
                clean=d[[roles['group'],roles['outcome']]].dropna()
                labels=sorted(clean[roles['group']].unique(),key=str)
                a=clean.loc[clean[roles['group']]==labels[1],roles['outcome']]
                b=clean.loc[clean[roles['group']]==labels[0],roles['outcome']]
                ref=stats.ttest_ind(a,b,equal_var=False); effect=float(a.mean()-b.mean())
            else:
                ref=stats.pearsonr(d[roles['x']],d[roles['y']]);effect=float(ref.statistic)
            ci=ref.confidence_interval()
            checks['numeric_reference']=all(np.isclose(result[k],v,rtol=1e-8,atol=1e-12)
                for k,v in [('p',ref.pvalue),('effect',effect),('ci_low',ci.low),('ci_high',ci.high)])
    return checks


def run(limit=None, selected=None, prefix="benchmark"):
    if not prefix.replace("_", "").isalnum():
        raise ValueError("Output prefix must be alphanumeric/underscore.")
    load_local_env(ROOT/'.env'); agents=DeepSeekAgents(); rows=[]
    out=ROOT/'artifacts'; out.mkdir(exist_ok=True)
    chosen=[c for c in cases() if not selected or c['id'] in selected]
    for case in chosen[:limit]:
        graph=build_graph(agents);config={'configurable':{'thread_id':case['id']}}
        if case.get('warmup'):
            graph.invoke({'data':case['data'].to_dict(orient='records'),
                          'question':'Compute Pearson correlation between x and y.',
                          'metadata':case['metadata']},config)
        state=graph.invoke({'data':case['data'].to_dict(orient='records'),
                           'question':case['question'],'metadata':case['metadata']},config)
        interrupted='__interrupt__' in state
        if interrupted and case.get('answer'):
            state=graph.invoke(Command(resume=case['answer']),config)
        if '__interrupt__' in state:
            state={**state,'status':'interrupted'}
        checks=score(case,state,interrupted)
        rows.append({'id':case['id'],'question':case['question'],'expected':case['expected'],
                     'checks':checks,'passed':all(checks.values()),'note':case.get('note'),
                     'output':public_result(state), 'last_draft':state.get('draft'), 'text_feedback':state.get('text_feedback'),
                     'pending_question':state['__interrupt__'][0].value if '__interrupt__' in state else None})
        (out/(prefix+'_live.json')).write_text(json.dumps({'model':agents.model,'cases':rows,
              'usage':agents.calls},indent=2,ensure_ascii=False),encoding='utf-8')
        print(case['id'],state['status'],'PASS' if all(checks.values()) else 'FAIL',flush=True)
    total=len(rows); passed=sum(r['passed'] for r in rows)
    lines=['# Live MVP benchmark','',f'Model: {agents.model}. Cases: {total}. Prespecified mechanical checks passed: {passed}/{total}.',
           '', 'Synthetic fixed datasets; one run per case. Not a general accuracy estimate. Interpreter semantics require independent human review.',
           '', '| Case | Status | Checks |','|---|---|---|']
    for r in rows:
        failed=', '.join(k for k,v in r['checks'].items() if not v) or 'pass'
        lines.append(f"| {r['id']} | {r['output']['status']} | {failed} |")
    lines += ['', '## Manual interpretation review',
              'Read the interpretations in benchmark_live.json. Check direction, effect/interval meaning, uncertainty, causal language, missingness and nonlinear boundary. A code check passing does not certify semantics.',
              '', 'The nonlinear case deliberately has U-shaped dependence and near-zero Pearson r. A claim of no relationship would be a genuine failure; a qualified lack of linear evidence is acceptable.']
    (out/(prefix+'_report.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Summary:',passed,'/',total)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int);p.add_argument('--case',action='append');p.add_argument('--output',default='benchmark')
    args=p.parse_args();run(args.limit,args.case,args.output)

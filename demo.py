"""CLI and synthetic examples; offline mode never impersonates a live model."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from langgraph.types import Command

from stat_assistant.agents import OfflineAgents, DeepSeekAgents, load_local_env
from stat_assistant.workflow import build_graph

ROOT = Path(__file__).resolve().parent


def fixtures():
    rng=np.random.default_rng(42)
    trial=pd.DataFrame({'group':['control']*25+['treatment']*25,
                       'outcome':np.r_[rng.normal(0,1,25),rng.normal(1,1,25)]})
    x=np.arange(20,dtype=float)
    corr=pd.DataFrame({'x':x,'y':x+np.sin(x),'date':['2024-01-01']*10+['2025-01-01']*10})
    return trial,corr


def extra_fixtures():
    rng=np.random.default_rng(20261012);x=np.linspace(-3,3,60)
    regression=pd.DataFrame({'x':x,'y':3+1.5*x+rng.normal(0,.8,len(x)),
                             'date':['2024-06-01']*30+['2025-06-01']*30})
    def labels(table):
        return pd.DataFrame([(f'A{i}',f'B{j}') for i,row in enumerate(table)
             for j,n in enumerate(row) for _ in range(n)],columns=['category_a','category_b'])
    return {'chi_square':labels([[30,10],[10,30]]), 'regression':regression,
            'chi_sparse':labels([[2,0],[0,2]])}


def public_result(state):
    return {k:state.get(k) for k in ['mode','status','plan','method','diagnostics','result','interpretation',
                                   'revisions','rewrites','calls','trace','error']}


def synthetic_demo(agents):
    trial,corr=fixtures(); g=build_graph(agents)
    tc={'configurable':{'thread_id':'trial'}}
    pending=g.invoke({'data':trial.to_dict(orient='records'),'question':'Compare mean outcome between treatment and control.', 'metadata':{}},tc)
    if '__interrupt__' in pending:
        done=g.invoke(Command(resume={'design':'independent','study_type':'observational'}),tc)
    else:
        done=pending
    cc={'configurable':{'thread_id':'correlation'}}
    first=g.invoke({'data':corr.to_dict(orient='records'),'question':'What is the Pearson correlation between x and y?',
                    'metadata':{'design':'independent','study_type':'observational'}},cc)
    follow=g.invoke({'question':'Repeat that correlation only for calendar year 2025.',
                    'metadata':{'design':'independent','study_type':'observational',
                    'filter':{'column':'date','start':'2025-01-01','end':'2025-12-31'}}},cc)
    stopped=g.invoke({'data':trial.to_dict(orient='records'),'question':'Compare mean outcome between groups.',
                      'metadata':{'design':'paired'}},{'configurable':{'thread_id':'unsupported'}})
    return g,{'comparison':public_result(done),'correlation':public_result(first),
              'followup':public_result(follow),'unsupported_design':public_result(stopped)}


def export_graph(g, png=False):
    out=ROOT/'artifacts'; out.mkdir(exist_ok=True)
    (out/'graph.mmd').write_text(g.get_graph().draw_mermaid(),encoding='utf-8')
    if png:
        (out/'graph.png').write_bytes(g.get_graph().draw_mermaid_png())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true'); parser.add_argument('--diagram',action='store_true')
    parser.add_argument('--csv'); parser.add_argument('--question')
    args=parser.parse_args(); load_local_env(ROOT/'.env')
    try:
        agents=DeepSeekAgents() if args.live else OfflineAgents()
    except ValueError as exc:
        parser.error(str(exc))
    if args.csv:
        if not args.question:
            parser.error('--question is required with --csv')
        g=build_graph(agents); config={'configurable':{'thread_id':'interactive'}}
        r=g.invoke({'data':pd.read_csv(args.csv).to_dict(orient='records'),'question':args.question,'metadata':{}},config)
        while '__interrupt__' in r:
            print(json.dumps(r['__interrupt__'][0].value,ensure_ascii=False,indent=2))
            answer=json.loads(input('Clarification JSON (or Ctrl+C to stop): '))
            r=g.invoke(Command(resume=answer),config)
        print(json.dumps(public_result(r),ensure_ascii=False,indent=2))
    else:
        trial,corr=fixtures(); examples=ROOT/'examples'; examples.mkdir(exist_ok=True)
        trial.to_csv(examples/'trial.csv',index=False); corr.to_csv(examples/'correlation.csv',index=False)
        g,results=synthetic_demo(agents)
        out=ROOT/'artifacts'; out.mkdir(exist_ok=True)
        (out/('live_results.json' if args.live else 'demo_results.json')).write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
        for label,result in results.items():
            print(label, result['mode'], result['status'], 'n=', (result['result'] or {}).get('n'), 'trace=', ' -> '.join(result['trace']))
        if args.live:
            (out/'live_usage.json').write_text(json.dumps(agents.calls,indent=2),encoding='utf-8')
    export_graph(g,args.diagram)


if __name__=='__main__':
    main()

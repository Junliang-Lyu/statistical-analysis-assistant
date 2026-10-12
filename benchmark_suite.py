"""Versioned four-method benchmark. Gold offline plans test mechanics, never LLM accuracy."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from langgraph.types import Command
from demo import fixtures, public_result
from stat_assistant.agents import DeepSeekAgents, OfflineAgents, Plan, load_local_env
from stat_assistant.workflow import build_graph

ROOT=Path(__file__).resolve().parent
GROUPS=['normal','boundary','clarification','stop','followup']
METHODS={'difference':'welch_t_test','correlation':'pearson','categorical':'chi_square','regression':'linear_regression'}


def table_data(table):
    return pd.DataFrame([(f'A{i}',f'B{j}') for i,row in enumerate(table)
        for j,n in enumerate(row) for _ in range(n)],columns=['category_a','category_b'])


def cases():
    trial,corr=fixtures();rng=np.random.default_rng(20261012)
    x=np.linspace(-3,3,60)
    reg=pd.DataFrame({'x':x,'y':3+1.5*x+rng.normal(0,.8,len(x)),
                      'date':['2024-06-01']*30+['2025-06-01']*30})
    cat=table_data([[30,10],[10,30]])
    metadata={'design':'independent','study_type':'observational'}
    rows=[]
    def add(name,group,data,goal,question,behavior='result',note='',**kw):
        roles={'outcome':'outcome','group':'group'} if goal=='difference' else (
            {'x':'category_a','y':'category_b'} if goal=='categorical' else {'x':'x','y':'y'})
        rows.append({'id':name,'category':group,'data':data,'question':question,
            'metadata':dict(metadata),'plan':{'goal':goal,**roles,'reason':'Prespecified evaluation plan'},
            'expected_behavior':behavior,'note':note,**kw})
    add('welch_clean','normal',trial,'difference','Compare mean outcome between treatment and control.')
    add('pearson_clean','normal',corr,'correlation','Measure Pearson linear correlation between x and y.')
    add('chi_square_2x2','normal',cat,'categorical','Use chi-square independence to test association between category_a and category_b, both categorical labels.')
    add('regression_clean','normal',reg,'regression','Fit a simple linear regression with x as predictor and y as outcome. Report the slope.')
    unequal=trial.copy();unequal.loc[unequal.group=='treatment','outcome']*=3
    add('welch_unequal_variance','boundary',unequal,'difference','Compare mean outcome between groups.',note='Welch does not require equal variances.')
    for name,d,goal,q in [('welch_missing',trial,'difference','Compare mean outcome between groups.'),
         ('pearson_missing',corr,'correlation','Compute Pearson correlation between x and y.'),
         ('chi_square_missing',cat,'categorical','Compute chi-square independence between category_a and category_b.'),
         ('regression_missing',reg,'regression','Regress y on x with one predictor.')]:
        d=d.copy();d.loc[0,'outcome' if goal=='difference' else ('category_a' if goal=='categorical' else 'y')]=None
        add(name,'boundary',d,goal,q,note='Complete-case deletion; report one omitted row.')
    add('chi_square_2x3','boundary',table_data([[12,10,8],[8,10,12]]),'categorical',
        'Test chi-square independence of category_a and category_b.',note='Non-square table, degrees of freedom two.')
    nonlinear=pd.DataFrame({'x':np.linspace(-2,2,40)});nonlinear['y']=nonlinear.x**2
    add('pearson_nonlinear','boundary',nonlinear,'correlation','Assess the relationship between x and y using Pearson linear correlation.',
        note='Near-zero linear correlation does not mean no relationship; U-shaped dependence is present.')
    outlier=reg.copy();outlier.loc[59,'y']=100
    add('regression_influential','boundary',outlier,'regression','Fit simple regression of y on x.',note='Influential-point warning; no automatic deletion.',warning_contains='influential')
    hetero=reg.copy();hetero['y']=2+x+rng.normal(0,1,len(x))*np.exp(x)
    add('regression_heteroscedastic','boundary',hetero,'regression','Fit simple regression with predictor x and outcome y.',
        note='Report residual diagnostics. Ordinary slope inference may be unreliable; no automatic robust estimator.')
    negative=reg.copy();negative['y']=5-2*x+rng.normal(0,.8,len(x))
    add('regression_negative_slope','boundary',negative,'regression','Regress outcome y on predictor x.',note='Negative slope; not a causal effect.')
    add('unknown_design','clarification',trial,'difference','Compare mean outcome between groups.',
        note='Must pause; synthetic evaluator confirms independent observations.',metadata={},answer=metadata,must_interrupt=True)
    ambiguous=trial.rename(columns={'outcome':'before'});ambiguous['after']=ambiguous.before+1
    add('ambiguous_outcome','clarification',ambiguous,'difference','Compare groups; I have not decided whether before or after is the outcome.',
        behavior='interrupt',note='No arbitrary outcome choice.',plan={'goal':'difference','group':'group','reason':'Unspecified outcome','clarification':'Choose before or after.'})
    add('ambiguous_last_year','clarification',corr,'correlation','Repeat that correlation only for last year.',behavior='interrupt',
        note='Date boundaries not supplied; must ask.',warmup=True)
    add('regression_direction','clarification',reg,'regression','Run a simple regression between x and y; I have not chosen which is the outcome.',
        behavior='interrupt',note='Must ask which variable is predictor/outcome.',plan={'goal':'regression','reason':'Direction unspecified','clarification':'Which is the outcome?'})
    add('paired_design','stop',trial,'difference','Compare mean outcome between groups.',metadata={'design':'paired'},behavior='stop',note='No silent change to independent design.')
    sparse=table_data([[2,0],[0,2]])
    add('chi_square_sparse','stop',sparse,'categorical','Test chi-square independence between category_a and category_b.',behavior='stop',note='Expected frequencies violate approximation policy.')
    single=cat.copy();single.category_a='one'
    add('chi_square_one_category','stop',single,'categorical','Test chi-square independence between category_a and category_b.',behavior='stop')
    coded=cat.copy();coded.category_a=coded.category_a.map({'A0':0,'A1':1});coded.category_b=coded.category_b.map({'B0':0,'B1':1})
    add('chi_square_numeric_codes','stop',coded,'categorical','Test chi-square independence; these numeric columns are category codes.',behavior='stop',note='Ask for text-label preprocessing or stop; do not silently recode.',allow_interrupt=True)
    add('pearson_constant','stop',pd.DataFrame({'x':[1.]*10,'y':range(10)}),'correlation','Compute Pearson correlation between x and y.',behavior='stop')
    add('pearson_too_few','stop',pd.DataFrame({'x':[1.,2.,3.],'y':[2.,4.,5.]}),'correlation','Compute Pearson correlation between x and y.',behavior='stop')
    add('regression_constant','stop',pd.DataFrame({'x':[1.]*10,'y':range(10)}),'regression','Regress y on x.',behavior='stop')
    add('regression_too_few','stop',reg.head(4),'regression','Regress y on x.',behavior='stop')
    add('regression_perfect','stop',pd.DataFrame({'x':range(10),'y':np.arange(10)*2.}),'regression','Regress y on x.',behavior='stop',note='Near-perfect fit: conservative residual-inference policy.')
    severe=trial.copy();severe.loc[0,'outcome']=100
    add('welch_extreme_small_group','stop',severe,'difference','Compare mean outcome between groups.',behavior='stop',note='Severe small-sample/extreme-value policy; no method switch.')
    add('unsupported_multivariable','stop',reg,'unsupported','Fit a multiple regression using x and date together to predict y.',behavior='stop',
        plan={'goal':'unsupported','reason':'Multiple regression is unsupported.'})
    for goal,d in [('correlation',corr),('regression',reg)]:
        add(goal+'_2025','followup',d,goal,'Repeat that same analysis only for calendar year 2025.',
            warmup=True,metadata={**metadata,'filter':{'column':'date','start':'2025-01-01','end':'2025-12-31'}},
            note='Same session; retain roles but recompute from filtered data.')
    return rows


def reference(case):
    """Independent explicit oracle; deliberately does not call application compute/diagnose."""
    d=case['data'];p=case['plan'];goal=p['goal']
    f=case['metadata'].get('filter')
    if f:
        dates=pd.to_datetime(d[f['column']]);d=d[(dates>=pd.Timestamp(f['start']))&(dates<=pd.Timestamp(f['end']))]
    if goal=='difference':
        d=d[[p['outcome'],p['group']]].dropna();labels=sorted(d[p['group']].unique(),key=str)
        a=d.loc[d[p['group']]==labels[1],p['outcome']];b=d.loc[d[p['group']]==labels[0],p['outcome']]
        test=stats.ttest_ind(a,b,equal_var=False);ci=test.confidence_interval()
        return {'n':len(d),'effect':float(a.mean()-b.mean()),'statistic':float(test.statistic),'p':float(test.pvalue),'df':float(test.df),'ci_low':float(ci.low),'ci_high':float(ci.high),'dropped':len(case['data'])-len(d) if not f else 0}
    before=len(d);d=d[[p['x'],p['y']]].dropna();dropped=before-len(d)
    if goal=='correlation':
        test=stats.pearsonr(d[p['x']],d[p['y']]);ci=test.confidence_interval()
        return {'n':len(d),'dropped':dropped,'effect':float(test.statistic),'statistic':float(test.statistic),'p':float(test.pvalue),'ci_low':float(ci.low),'ci_high':float(ci.high)}
    if goal=='categorical':
        t=pd.crosstab(d[p['x']],d[p['y']]).values
        expected=t.sum(axis=1)[:,None]*t.sum(axis=0)[None,:]/t.sum()
        statistic=float(np.sum((t-expected)**2/expected));df=(t.shape[0]-1)*(t.shape[1]-1)
        return {'n':len(d),'dropped':dropped,'statistic':statistic,'p':float(stats.chi2.sf(statistic,df)),'df':df,
            'effect':float(np.sqrt(statistic/(len(d)*min(t.shape[0]-1,t.shape[1]-1)))),'ci_low':None,'ci_high':None}
    x=d[p['x']].to_numpy(dtype=float);y=d[p['y']].to_numpy(dtype=float);X=np.column_stack([np.ones(len(x)),x])
    beta=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@beta;df=len(x)-2
    se=float(np.sqrt((e@e/df*np.linalg.inv(X.T@X))[1,1]));statistic=beta[1]/se;critical=stats.t.ppf(.975,df)
    return {'n':len(d),'dropped':dropped,'effect':float(beta[1]),'intercept':float(beta[0]),'r_squared':float(1-(e@e)/np.sum((y-y.mean())**2)),
        'statistic':float(statistic),'p':float(2*stats.t.sf(abs(statistic),df)),'df':df,
        'ci_low':float(beta[1]-critical*se),'ci_high':float(beta[1]+critical*se)}


class PrespecifiedAgents(OfflineAgents):
    mode='offline-prespecified-plans'
    def __init__(self,case):
        self.case=case
    def plan(self,question,overview,prior,metadata,feedback):
        p=dict(self.case['plan'])
        if self.case.get('warmup') and question=='Warmup analysis':
            p['clarification']=None
        elif self.case['expected_behavior']=='interrupt':
            p['clarification']=p.get('clarification') or 'Provide exact date boundaries.'
        p.update(design=metadata.get('design','unknown'),study_type=metadata.get('study_type','unknown'),filter=metadata.get('filter'))
        return Plan.model_validate(p)


def export_catalog(rows):
    root=ROOT/'examples/benchmark_v2';root.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for c in rows:
        folder=root/c['category'];folder.mkdir(exist_ok=True)
        c['data'].to_csv(folder/(c['id']+'.csv'),index=False)
        record={k:v for k,v in c.items() if k!='data'}
        if c['expected_behavior']=='result':record['numeric_reference']=reference(c)
        record['expected_method']=METHODS.get(c['plan']['goal'])
        (folder/(c['id']+'.json')).write_text(json.dumps(record,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        manifest.append({'id':c['id'],'category':c['category'],'expected_behavior':c['expected_behavior'],'note':c['note']})
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    for category in GROUPS:
        group=[c for c in manifest if c['category']==category]
        lines=[f'# {category.title()} cases','', 'Each CSV has a same-named JSON containing question, confirmed metadata, expected behavior, plan and (where applicable) numerical reference. All data are synthetic.','', '| Case | Expected | Note |','|---|---|---|']
        lines += [f"| {c['id']} | {c['expected_behavior']} | {c['note']} |" for c in group]
        (root/category/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def evaluate(case,agents):
    graph=build_graph(agents);config={'configurable':{'thread_id':case['id']}}
    records=json.loads(case['data'].to_json(orient='records'))
    warmup=None
    if case.get('warmup'):
        p=case['plan'];q='Warmup analysis' if isinstance(agents,PrespecifiedAgents) else (
            f"Regress {p['y']} on {p['x']}." if p['goal']=='regression' else f"Compute Pearson correlation between {p['x']} and {p['y']}.")
        warmup=graph.invoke({'data':records,'question':q,'metadata':{'design':'independent','study_type':'observational'}},config)
        if '__interrupt__' in warmup:
            warmup=graph.invoke(Command(resume={'design':'independent','study_type':'observational','x':p['x'],'y':p['y']}),config)
    state=graph.invoke({'data':records,'question':case['question'],'metadata':case['metadata']},config)
    interrupted='__interrupt__' in state
    if interrupted and case.get('answer'):
        state=graph.invoke(Command(resume=case['answer']),config)
    if '__interrupt__' in state:state={**state,'status':'interrupted'}
    p=state.get('plan') or {};r=state.get('result');goal=case['plan']['goal'];behavior=case['expected_behavior']
    checks={'goal':p.get('goal')==goal}
    if behavior=='result':
        checks['execution']=state.get('status') in ('completed','results_only') and r is not None
        checks['method']=bool(r and r['method']==METHODS[goal])
        roles=[k for k in ('outcome','group','x','y') if case['plan'].get(k)]
        checks['roles']=all(p.get(k)==case['plan'][k] for k in roles)
        ref=reference(case)
        checks['numbers']=bool(r and all(r.get(k) is None if v is None else
            r.get(k) is not None and np.isclose(r[k],v,rtol=1e-8,atol=1e-12) for k,v in ref.items()))
        if case.get('warning_contains'):
            checks['warning']=bool(r and case['warning_contains'] in ' '.join(r['warnings']).lower())
        if case.get('warmup'):
            checks['warmup']=bool(warmup and warmup.get('result'))
            checks['memory_roles']=bool(state.get('prior_plan') and all(state['prior_plan'].get(k)==case['plan'][k] for k in roles))
    elif behavior=='interrupt':
        checks['clarification']=interrupted and state.get('status')=='interrupted' and r is None
    else:
        checks['stopped']=state.get('status')=='stopped' and r is None
        if case.get('allow_interrupt') and interrupted and r is None:checks['stopped']=True
    if case.get('must_interrupt'):checks['clarification']=interrupted
    return {'id':case['id'],'category':case['category'],'question':case['question'],'metadata':case['metadata'],
        'expected_behavior':behavior,'expected_plan':case['plan'],'checks':checks,'mechanical_pass':all(checks.values()),
        'interpretation_accepted':bool(state.get('interpretation')),'semantic_review':'not independently reviewed',
        'note':case['note'],'output':public_result(state),'draft':state.get('draft'),
        'text_feedback':state.get('text_feedback'),'pending':state['__interrupt__'][0].value if '__interrupt__' in state else None}


def run(mode='offline',selected=None,categories=None,prefix=None,export_only=False):
    catalog=cases();export_catalog(catalog)
    known={c['id'] for c in catalog}
    if selected and set(selected)-known:raise ValueError('Unknown cases: '+', '.join(sorted(set(selected)-known)))
    chosen=[c for c in catalog if (not selected or c['id'] in selected) and (not categories or c['category'] in categories)]
    if not chosen:raise ValueError('No cases selected.')
    if export_only:return
    prefix=prefix or ('live_v2' if mode=='live' else 'offline_v2')
    if not prefix.replace('_','').isalnum():raise ValueError('Output prefix must be alphanumeric/underscore.')
    out=ROOT/'artifacts/benchmark_v2'/prefix
    if out.exists():raise ValueError('Output directory exists; choose a new --output to preserve evidence.')
    out.mkdir(parents=True)
    load_local_env(ROOT/'.env');live=DeepSeekAgents() if mode=='live' else None;rows=[]
    for c in chosen:
        row=evaluate(c,live or PrespecifiedAgents(c));rows.append(row)
        folder=out/c['category'];folder.mkdir(exist_ok=True)
        (folder/(c['id']+'.json')).write_text(json.dumps(row,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print(c['id'],row['output']['status'],'PASS' if row['mechanical_pass'] else 'FAIL',flush=True)
        (out/'results.json').write_text(json.dumps({'mode':mode,'cases':rows,'usage':live.calls if live else []},indent=2,ensure_ascii=False),encoding='utf-8')
    passed=sum(r['mechanical_pass'] for r in rows);eligible=[r for r in rows if r['output'].get('result')]
    lines=['# Four-method benchmark','',f'Mode: {mode}; mechanical checks: {passed}/{len(rows)}.',
        f'Interpretations accepted by code: {sum(r["interpretation_accepted"] for r in eligible)}/{len(eligible)} computed results. This is NOT semantic accuracy.',
        '', 'Offline uses prespecified gold plans, not language reasoning. Numerical agreement is not proof of statistical assumptions. Live runs are one attempt per case with bounded internal repair; failures retained. Human semantic labels are not fabricated.',
        '', '| Category | Case | Status | Failed checks | Text accepted |','|---|---|---|---|---|']
    lines += [f"| {r['category']} | {r['id']} | {r['output']['status']} | {', '.join(k for k,v in r['checks'].items() if not v) or 'none'} | {r['interpretation_accepted']} |" for r in rows]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Mechanical checks:',passed,'/',len(rows),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['offline','live'],default='offline')
    parser.add_argument('--case',action='append');parser.add_argument('--category',choices=GROUPS,action='append')
    parser.add_argument('--output');parser.add_argument('--export-only',action='store_true');args=parser.parse_args()
    run(args.mode,args.case,args.category,args.output,args.export_only)

import numpy as np
import pandas as pd
import pytest
from scipy import stats
from stat_assistant.agents import Plan, OfflineAgents, check_interpretation, render_interpretation
from stat_assistant.tools import compute, diagnose
from stat_assistant.workflow import build_graph


def categorical(table=((30,10),(10,30))):
    return pd.DataFrame([(f'A{i}',f'B{j}') for i,row in enumerate(table)
                         for j,n in enumerate(row) for _ in range(n)],columns=['category_a','category_b'])


def plan(goal):
    return Plan(goal=goal,x='category_a' if goal=='categorical' else 'x',
                y='category_b' if goal=='categorical' else 'y',design='independent',
                study_type='observational',reason='Test').model_dump()


def regression():
    rng=np.random.default_rng(12);x=np.linspace(-3,3,50)
    return pd.DataFrame({'x':x,'y':2+1.7*x+rng.normal(0,.8,len(x))})


@pytest.mark.parametrize('table',[((30,10),(10,30)),((12,10,8),(8,10,12))])
def test_chi_square_reference_and_no_fabricated_interval(table):
    r=compute(categorical(table),plan('categorical'));ref=stats.chi2_contingency(table,correction=False)
    assert r['method']=='chi_square' and r['statistic']==pytest.approx(ref.statistic)
    assert r['p']==pytest.approx(ref.pvalue) and r['df']==ref.dof
    assert r['effect']==pytest.approx(np.sqrt(ref.statistic/(np.sum(table)*min(len(table)-1,len(table[0])-1))))
    assert r['ci_low'] is None and r['ci_high'] is None and r['confidence_level'] is None
    raw=OfflineAgents().interpret(plan('categorical'),r,[])
    assert check_interpretation(raw,r)==[]
    assert 'not computed' in render_interpretation(raw,r)['summary']


def test_chi_sparse_numeric_codes_and_constant_stop():
    assert diagnose(categorical(((2,0),(0,2))),plan('categorical'))['errors']
    assert diagnose(pd.DataFrame({'category_a':[1,2]*10,'category_b':[0,1]*10}),plan('categorical'))['errors']
    d=categorical();d.category_a='one'
    assert diagnose(d,plan('categorical'))['errors']


def test_chi_missing_rows_reported():
    d=categorical();d.loc[0,'category_a']=None
    r=compute(d,plan('categorical'));assert r['n']==79 and r['dropped']==1


def test_regression_independent_matrix_reference():
    d=regression();r=compute(d,plan('regression'))
    X=np.column_stack([np.ones(len(d)),d.x]);beta=np.linalg.lstsq(X,d.y,rcond=None)[0]
    residual=d.y-X@beta;mse=(residual@residual)/(len(d)-2)
    se=np.sqrt((mse*np.linalg.inv(X.T@X))[1,1]);t=beta[1]/se;critical=stats.t.ppf(.975,len(d)-2)
    assert r['method']=='linear_regression'
    assert r['effect']==pytest.approx(beta[1]) and r['intercept']==pytest.approx(beta[0])
    assert r['statistic']==pytest.approx(t) and r['p']==pytest.approx(2*stats.t.sf(abs(t),len(d)-2))
    assert r['ci_low']==pytest.approx(beta[1]-critical*se)
    assert r['ci_high']==pytest.approx(beta[1]+critical*se)
    assert r['r_squared']==pytest.approx(1-(residual@residual)/np.sum((d.y-d.y.mean())**2))
    assert 'residuals' in diagnose(d,plan('regression'))['details']


def test_regression_tiny_constant_perfect_and_nonfinite_stop():
    for d in [regression().head(4),pd.DataFrame({'x':[1]*10,'y':range(10)}),
              pd.DataFrame({'x':range(10),'y':np.arange(10)*2.}),
              pd.DataFrame({'x':range(10),'y':[np.inf]+list(range(9))})]:
        assert diagnose(d,plan('regression'))['errors']


def test_regression_outlier_diagnostic_does_not_delete():
    d=regression();d.loc[49,'y']=100
    report=diagnose(d,plan('regression'))
    assert report['details']['influential_count']>0 and report['warnings']
    assert compute(d,plan('regression'))['n']==50


@pytest.mark.parametrize('goal,question',[('categorical','Chi-square category_a category_b'),('regression','Regress y on x')])
def test_new_methods_end_to_end(goal,question):
    d=categorical() if goal=='categorical' else regression()
    g=build_graph(OfflineAgents());r=g.invoke({'data':d.to_dict(orient='records'),'question':question,
        'metadata':{'design':'independent','study_type':'observational'}},{'configurable':{'thread_id':goal}})
    assert r['status']=='completed' and r['result']['n']==len(d)
    assert r['interpretation']['causal_claim'] is False

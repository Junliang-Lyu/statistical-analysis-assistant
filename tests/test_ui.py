import pytest
from ui_server import Workspace


def test_ui_pause_resume_and_isolation():
    w = Workspace()
    a = w.handle({'action':'analyze','mode':'offline','case':'trial','question':'Compare mean outcome between groups.'})
    assert a['pending']
    b = w.handle({'action':'resume','session':a['session'],'answer':{'design':'independent','study_type':'observational'}})
    assert b['status']=='completed' and b['result']['n']==50
    c = w.handle({'action':'analyze','mode':'offline','case':'correlation','question':'Correlation between x and y','metadata':{'design':'independent'}})
    assert c['session']!=a['session'] and c['result']['n']==20
    d = w.handle({'action':'followup','session':c['session'],'question':'Repeat that correlation only for 2025','metadata':{'design':'independent','filter':{'column':'date','start':'2025-01-01','end':'2025-12-31'}}})
    assert d['result']['n']==10


def test_ui_invalid_session_and_csv():
    w=Workspace()
    with pytest.raises(ValueError):
        w.handle({'action':'resume','session':'missing','answer':{}})
    with pytest.raises(ValueError):
        w.handle({'action':'analyze','mode':'offline','csv':''})


def test_csv_upload_and_paired_boundary():
    w=Workspace()
    csv='x,y\n0,0\n1,2\n2,1\n3,4\n4,3\n5,6\n'
    r=w.handle({'action':'analyze','mode':'offline','csv':csv,'question':'Correlation between x and y','metadata':{'design':'independent'}})
    assert r['status']=='completed' and r['result']['n']==6
    assert r['columns']==['x','y'] and len(r['preview'])==6
    bad=w.handle({'action':'analyze','mode':'offline','case':'paired','question':'Compare mean outcome between groups'})
    assert bad['status']=='stopped' and bad['result'] is None


@pytest.mark.parametrize('case,question,method,n',[
    ('chi_square','Chi-square category_a category_b','chi_square',80),
    ('regression','Regress y on x','linear_regression',60)])
def test_ui_new_methods(case,question,method,n):
    w=Workspace();r=w.handle({'action':'analyze','mode':'offline','case':case,'question':question,
        'metadata':{'design':'independent','study_type':'observational'}})
    assert r['status']=='completed' and r['result']['method']==method and r['result']['n']==n


def test_explanation_reuses_result_and_passes_question():
    w=Workspace()
    a=w.handle({'action':'analyze','case':'trial','question':'Compare mean outcome','metadata':{'design':'independent','study_type':'observational'}})
    graph,config,_=w.sessions[a['session']]
    b=w.handle({'action':'followup','session':a['session'],'intent':'explain','question':'Can I conclude that treatment caused the difference?'})
    assert b['pending'] is None and b['status']=='completed'
    assert b['result']==a['result'] and b['diagnostics']==a['diagnostics']
    assert 'run_test' not in b['trace'] and 'planner' not in b['trace']
    assert b['calls']==1
    assert 'cannot conclude' in b['interpretation']['summary'].lower()


def test_explanation_without_result_is_rejected():
    w=Workspace()
    a=w.handle({'action':'analyze','case':'paired','question':'Compare mean outcome'})
    with pytest.raises(ValueError,match='completed'):
        w.handle({'action':'followup','session':a['session'],'intent':'explain','question':'Explain this'})


def test_builtin_csv_matches_analysis_data():
    w=Workspace()
    material=w.example_material('trial')
    import pandas as pd
    import io
    frame=pd.read_csv(io.StringIO(material['csv']))
    assert len(frame)==50 and list(frame)==['group','outcome']
    assert material['filename']=='trial.csv'
    with pytest.raises(ValueError):
        w.example_material('../.env')


def test_analysis_after_explanation_recomputes_subset():
    w=Workspace()
    a=w.handle({'action':'analyze','case':'correlation','question':'Correlation x and y','metadata':{'design':'independent'}})
    b=w.handle({'action':'followup','session':a['session'],'intent':'explain','question':'Explain the result'})
    c=w.handle({'action':'followup','session':a['session'],'intent':'analyze','question':'Repeat only for 2025',
                'metadata':{'design':'independent','filter':{'column':'date','start':'2025-01-01','end':'2025-12-31'}}})
    assert b['result']['n']==20 and c['result']['n']==10
    assert 'run_test' in c['trace']


def test_builtin_nonlinear_case_does_not_imply_no_relationship():
    w=Workspace()
    r=w.handle({'action':'analyze','case':'nonlinear','question':'Pearson correlation between x and y',
                'metadata':{'design':'independent','study_type':'observational'}})
    assert r['status']=='completed' and r['result']['n']==40
    assert abs(r['result']['effect'])<1e-12
    assert any('linear' in warning.lower() for warning in r['result']['warnings'])

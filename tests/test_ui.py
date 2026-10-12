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

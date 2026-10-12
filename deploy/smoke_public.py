"""Offline HTTP test of the exact image; no provider key or model request required."""
import json
import os
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from public_server import Budget, PublicWorkspace, make_handler

with tempfile.TemporaryDirectory() as tmp:
    w=PublicWorkspace(Budget(Path(tmp)/'b.sqlite3'))
    server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(w,'http://stats.test'))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_port}'
    def call(path,payload=None,cookie=None,origin='http://stats.test'):
        headers={'Host':'stats.test','Origin':origin,'Content-Type':'application/json'}
        if cookie: headers['Cookie']=cookie
        r=urlopen(Request(base+path,data=json.dumps(payload).encode() if payload else None,headers=headers),timeout=15)
        return json.loads(r.read()),r.headers.get('Set-Cookie','').split(';')[0]
    assert call('/api/health')[0]=={'status':'ok'}
    for case,question,method in [
      ('trial','Compare mean outcome between treatment and control','welch_t_test'),
      ('correlation','Pearson correlation between x and y','pearson'),
      ('chi_square','Chi-square association between category_a and category_b','chi_square'),
      ('regression','Regress y on x','linear_regression')]:
        a,cookie=call('/api',{'action':'analyze','mode':'offline','case':case,'question':question,
                             'metadata':{'design':'independent','study_type':'observational'}})
        assert a['status']=='completed',(case,a)
        assert a['method']==method,(case,a['method'])
        b,_=call('/api',{'action':'followup','session':a['session'],'intent':'explain','question':'Explain this result'},cookie)
        assert b['result']==a['result'] and 'run_test' not in b['trace']
    try: call('/api',{'action':'analyze','case':'trial','question':'test'},origin='http://evil.test')
    except HTTPError as e: assert e.code==403
    else: raise AssertionError('Cross-origin request accepted')
    assert os.getuid()!=0,'Container must run as non-root'
    assert not Path('/app/.env').exists()
    assert not Path('/app/.git').exists()
    assert not Path('/app/assignments').exists()
    server.shutdown()
print('PASS: health, four analyses, explanation reuse, origin rejection, non-root and image boundaries')

"""Public adapter behind an HTTPS reverse proxy; local adapter remains separate."""
import hashlib
import io
import json
import math
import os
import secrets
import sqlite3
import threading
import time
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
from ui_server import Workspace, ROOT
from stat_assistant.agents import DeepSeekAgents, OfflineAgents


class PublicError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status=status


class Budget:
    """Persist conservative reservations; never refund uncertain/provider-failed calls."""
    def __init__(self, path, daily=.5, monthly=5., per_client=10, global_operations=100):
        self.path=str(path)
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        self.daily=round(daily*1_000_000); self.monthly=round(monthly*1_000_000)
        self.per_client=per_client; self.global_operations=global_operations
        if min(self.daily,self.monthly,per_client,global_operations)<=0: raise ValueError('Limits must be positive.')
        with self.connection() as c:
            c.execute('CREATE TABLE IF NOT EXISTS spend(day TEXT, amount INTEGER)')
            c.execute('CREATE TABLE IF NOT EXISTS operations(day TEXT, client TEXT)')

    def connection(self): return sqlite3.connect(self.path,timeout=10)

    def reserve(self, amount):
        if not math.isfinite(amount) or amount<=0: raise ValueError('Invalid reservation.')
        amount=math.ceil(amount*1_000_000)
        day=datetime.now(timezone.utc).strftime('%Y-%m-%d')
        with self.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            d=c.execute('SELECT COALESCE(SUM(amount),0) FROM spend WHERE day=?',(day,)).fetchone()[0]
            m=c.execute('SELECT COALESCE(SUM(amount),0) FROM spend WHERE day LIKE ?',(day[:7]+'%',)).fetchone()[0]
            if d+amount>self.daily or m+amount>self.monthly: raise PublicError('Model budget exhausted. Try another day or use offline mode.',429)
            c.execute('INSERT INTO spend VALUES (?,?)',(day,amount))

    def operation(self, client):
        day=datetime.now(timezone.utc).strftime('%Y-%m-%d')
        client=hashlib.sha256(client.encode()).hexdigest()
        with self.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            n=c.execute('SELECT COUNT(*) FROM operations WHERE day=?',(day,)).fetchone()[0]
            own=c.execute('SELECT COUNT(*) FROM operations WHERE day=? AND client=?',(day,client)).fetchone()[0]
            if n>=self.global_operations or own>=self.per_client: raise PublicError('Daily demo request limit reached.',429)
            c.execute('INSERT INTO operations VALUES (?,?)',(day,client))
            c.execute('DELETE FROM operations WHERE day<?',(day[:7]+'-01',))
            c.execute('DELETE FROM spend WHERE day<?',(day[:7]+'-01',))


class BudgetAgents(DeepSeekAgents):
    def __init__(self, budget):
        super().__init__()
        self.budget=budget
        # Explicit ceilings must be configured for the actual provider/model before live access.
        self.input_price=float(os.environ.get('STATS_INPUT_USD_PER_MILLION','0'))
        self.output_price=float(os.environ.get('STATS_OUTPUT_USD_PER_MILLION','0'))
        if not all(math.isfinite(p) and p>0 for p in (self.input_price,self.output_price)):
            raise PublicError('Live analysis is not configured. Offline mode remains available.',503)
        if self.model != os.environ.get('STATS_PRICED_MODEL',''):
            raise PublicError('Model pricing configuration does not match the selected model.',503)

    def _json(self, system, payload, schema, role):
        user=json.dumps({'input':payload,'schema':schema},ensure_ascii=False,default=str)
        if len(user)>40000: raise PublicError('Model context exceeds demo limit.')
        # Byte-per-token upper bound with generous framing margin; max output is 1600.
        upper=len(system.encode())+len(user.encode())+4096
        self.budget.reserve((upper*self.input_price+1600*self.output_price)/1_000_000)
        return super()._json(system,payload,schema,role)


class PublicWorkspace(Workspace):
    def __init__(self,budget,clock=time.monotonic,ttl=1800):
        super().__init__(lambda mode:BudgetAgents(budget) if mode=='live' else OfflineAgents())
        self.budget=budget; self.clock=clock; self.ttl=ttl
        self.owners={}; self.public_lock=threading.Lock()

    def expire(self):
        with self.public_lock:
            now=self.clock()
            for sid,(_,last) in list(self.owners.items()):
                if now-last>self.ttl:
                    self.owners.pop(sid,None); self.sessions.pop(sid,None)

    def handle_public(self,payload,owner,client):
        with self.public_lock:
            now=self.clock()
            for sid,(_,last) in list(self.owners.items()):
                if now-last>self.ttl:
                    self.owners.pop(sid,None); self.sessions.pop(sid,None)
            action=payload.get('action')
            if action not in ('analyze','resume','followup'): raise PublicError('Unknown action.')
            if action!='resume' and not 1<=len(str(payload.get('question','')).strip())<=2000:
                raise PublicError('Question must contain 1–2000 characters.')
            if action=='analyze':
                if len(self.sessions)>=30: raise PublicError('Demo is busy. Please try later.',503)
                if not payload.get('case'):
                    csv=payload.get('csv','')
                    if not isinstance(csv,str) or len(csv.encode())>1_000_000: raise PublicError('CSV limit is 1 MB.')
                    try: frame=pd.read_csv(io.StringIO(csv),nrows=10001)
                    except Exception: raise PublicError('CSV could not be read.') from None
                    if len(frame)>10000 or len(frame.columns)>50: raise PublicError('CSV limit is 10,000 rows and 50 columns.')
            else:
                sid=payload.get('session')
                if sid not in self.owners or self.owners[sid][0]!=owner:
                    raise PublicError('Session expired or unavailable. Start a new analysis.',403)
            self.budget.operation(client)
            output=super().handle(payload)
            self.owners[output['session']]=(owner,self.clock())
            return output


def valid_origin(host,origin,configured):
    expected=urlsplit(configured)
    return expected.scheme in ('https','http') and host==expected.netloc and origin==configured


def make_handler(workspace,origin):
    gate=threading.BoundedSemaphore(2)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,status,content,kind='application/json',cookie=None):
            self.send_response(status)
            self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Content-Length',str(len(content)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            if cookie: self.send_header('Set-Cookie',cookie)
            self.end_headers(); self.wfile.write(content)
        def do_GET(self):
            if self.headers.get('Host')!=urlsplit(origin).netloc:
                return self.respond(403,b'Invalid host','text/plain')
            if self.path=='/api/health': return self.respond(200,b'{"status":"ok"}')
            if self.path=='/release.txt': return self.respond(200,os.environ.get('STATS_RELEASE','development').encode(),'text/plain')
            if self.path.startswith('/examples/'):
                try: output=workspace.example_material(self.path.removeprefix('/examples/').removesuffix('.json'))
                except ValueError: return self.respond(404,b'Unknown example','text/plain')
                return self.respond(200,json.dumps(output).encode())
            assets={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
            if self.path not in assets: return self.respond(404,b'Not found','text/plain')
            name=assets[self.path]; content=(ROOT/'ui'/name).read_bytes()
            if name=='index.html':
                s=content.decode().replace('LOCAL RESEARCH WORKSPACE','PUBLIC RESEARCH DEMO')
                s=s.replace('Or upload a CSV (up to 4 MB)','Or upload a CSV (up to 1 MB; 10,000 rows; 50 columns)')
                s=s.replace('Local in-memory sessions; cleared when the server restarts.',
                  'Uploads stay in server memory for up to thirty minutes of inactivity and clear on restart. Questions, column names, category labels and statistical summaries may be sent to DeepSeek. Do not upload sensitive data. Daily usage and model budgets apply.')
                content=s.encode()
            kind={'index.html':'text/html','app.js':'text/javascript','style.css':'text/css'}[name]
            self.respond(200,content,kind)
        def do_POST(self):
            if self.path!='/api': return self.respond(404,b'Not found','text/plain')
            if not valid_origin(self.headers.get('Host'),self.headers.get('Origin'),origin):
                return self.respond(403,b'{"error":"Cross-origin request rejected."}')
            if not gate.acquire(blocking=False): return self.respond(503,b'{"error":"Demo is busy. Try again shortly."}')
            try:
                self.connection.settimeout(10)
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=1_100_000: raise PublicError('Request exceeds demo upload limit.',413)
                payload=json.loads(self.rfile.read(size))
                if not isinstance(payload,dict): raise PublicError('Expected JSON object.')
                cookies=SimpleCookie(); cookies.load(self.headers.get('Cookie',''))
                token=cookies['stats_client'].value if 'stats_client' in cookies else secrets.token_urlsafe(32)
                if len(token)>100: raise PublicError('Invalid session cookie.')
                owner=hashlib.sha256(token.encode()).hexdigest()
                # Caddy must replace this header; service port is inaccessible outside its network.
                client=self.headers.get('X-Forwarded-For',self.client_address[0]).split(',')[0].strip()
                result=workspace.handle_public(payload,owner,client)
                cookie=f'stats_client={token}; Path=/; HttpOnly; SameSite=Strict'+('; Secure' if origin.startswith('https:') else '')
                self.respond(200,json.dumps(result,allow_nan=False).encode(),cookie=cookie)
            except Exception as exc:
                status=exc.status if isinstance(exc,PublicError) else 400 if isinstance(exc,ValueError) else 503
                message=str(exc) if isinstance(exc,PublicError) else 'Analysis could not complete. Check your input or try later; no result is claimed.'
                self.respond(status,json.dumps({'error':message}).encode())
            finally: gate.release()
    return Handler


if __name__=='__main__':
    origin=os.environ.get('STATS_PUBLIC_ORIGIN','https://stats.jun-liang-lyu.com').rstrip('/')
    budget=Budget(os.environ.get('STATS_BUDGET_DB','/data/budget.sqlite3'),
                  daily=float(os.environ.get('STATS_DAILY_BUDGET_USD','.5')),
                  monthly=float(os.environ.get('STATS_MONTHLY_BUDGET_USD','5')),
                  per_client=int(os.environ.get('STATS_PER_CLIENT_DAILY','10')),
                  global_operations=int(os.environ.get('STATS_GLOBAL_DAILY','100')))
    workspace=PublicWorkspace(budget)
    def reap():
        while True:
            time.sleep(30)
            workspace.expire()
    threading.Thread(target=reap,daemon=True).start()
    server=ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','8082'))),make_handler(workspace,origin))
    server.serve_forever()

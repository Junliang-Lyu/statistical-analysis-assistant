"""Local browser adapter; no public hosting, persistence or generated code execution."""
import argparse
import io
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd
from langgraph.types import Command
from demo import fixtures, extra_fixtures, public_result
from stat_assistant.agents import DeepSeekAgents, OfflineAgents, load_local_env
from stat_assistant.workflow import build_graph

ROOT = Path(__file__).resolve().parent


class Workspace:
    def __init__(self):
        self.sessions = {}
        self.lock = threading.Lock()

    def handle(self, payload):
        action = payload.get('action')
        with self.lock:
            if action == 'analyze':
                if len(self.sessions) >= 100:
                    raise ValueError('Session limit reached; restart the local server.')
                question = str(payload.get('question', '')).strip()
                if not question:
                    raise ValueError('Enter a research question.')
                mode = payload.get('mode', 'offline')
                if mode not in ('offline', 'live'):
                    raise ValueError('Unknown model mode.')
                if payload.get('case'):
                    trial, corr = fixtures()
                    case = payload['case']
                    examples={'trial':trial,'correlation':corr,'paired':trial,**extra_fixtures()}
                    if case not in examples:
                        raise ValueError('Unknown example.')
                    data = examples[case]
                else:
                    csv = payload.get('csv', '')
                    if not isinstance(csv, str) or not csv.strip():
                        raise ValueError('Upload a nonempty CSV or choose an example.')
                    data = pd.read_csv(io.StringIO(csv))
                if len(data)>100000 or len(data.columns)>100:
                    raise ValueError('Maximum 100,000 rows and 100 columns.')
                agents = DeepSeekAgents() if mode == 'live' else OfflineAgents()
                graph = build_graph(agents)
                sid = secrets.token_urlsafe(24)
                config = {'configurable':{'thread_id':sid}}
                metadata = payload.get('metadata') or {}
                if payload.get('case') == 'paired':
                    metadata = {**metadata, 'design':'paired'}
                records = json.loads(data.to_json(orient='records', date_format='iso'))
                state = graph.invoke({'data':records, 'question':question, 'metadata':metadata}, config)
                self.sessions[sid] = (graph, config, data)
            else:
                sid = payload.get('session')
                if sid not in self.sessions:
                    raise ValueError('Session expired or unknown; start a new analysis.')
                graph, config, data = self.sessions[sid]
                pending = bool(graph.get_state(config).tasks and any(t.interrupts for t in graph.get_state(config).tasks))
                if action == 'resume':
                    if not pending:
                        raise ValueError('This session is not awaiting clarification.')
                    state = graph.invoke(Command(resume=payload.get('answer',{})), config)
                elif action == 'followup':
                    if pending:
                        raise ValueError('Answer the pending clarification first.')
                    question = str(payload.get('question','')).strip()
                    if not question:
                        raise ValueError('Enter a follow-up question.')
                    state = graph.invoke({'question':question, 'metadata':payload.get('metadata') or {}}, config)
                else:
                    raise ValueError('Unknown action.')
            result = public_result(state)
            result.update(session=sid, columns=list(data.columns), rows=len(data),
                          preview=json.loads(data.head(6).to_json(orient='records')),
                          pending=state['__interrupt__'][0].value if '__interrupt__' in state else None)
            return result


def make_handler(workspace):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def send(self, status, content, kind='application/json; charset=utf-8'):
            self.send_response(status)
            self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(content)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers()
            self.wfile.write(content)

        def valid_host(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}'

        def do_GET(self):
            if not self.valid_host():
                return self.send(403,b'Invalid host','text/plain')
            assets={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
            if self.path not in assets:
                return self.send(404,b'Not found','text/plain')
            filename=assets[self.path]
            kind={'index.html':'text/html','app.js':'text/javascript','style.css':'text/css'}[filename]
            self.send(200,(ROOT/'ui'/filename).read_bytes(),kind+'; charset=utf-8')

        def do_POST(self):
            origin=f'http://127.0.0.1:{self.server.server_port}'
            if not self.valid_host() or self.headers.get('Origin') != origin:
                return self.send(403,b'Cross-origin request rejected','text/plain')
            if self.path != '/api':
                return self.send(404,b'Not found','text/plain')
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=5_000_000:
                    raise ValueError('Request must be under five megabytes.')
                payload=json.loads(self.rfile.read(size))
                if not isinstance(payload,dict):
                    raise ValueError('Expected a JSON object.')
                output=workspace.handle(payload)
                self.send(200,json.dumps(output,ensure_ascii=False,allow_nan=False).encode())
            except Exception as exc:
                # Provider adapters sanitize credentials; do not expose raw exception bodies.
                message=str(exc) if isinstance(exc,(ValueError,KeyError)) else 'Analysis failed. Check CSV format and local configuration.'
                self.send(400,json.dumps({'error':message}).encode())
    return Handler


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args(); load_local_env(ROOT/'.env')
    server=ThreadingHTTPServer(('127.0.0.1',args.port),make_handler(Workspace()))
    print(f'Open http://127.0.0.1:{args.port} — Ctrl+C to stop',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

"""Build the teaching notebook; notebook itself uses the public project modules."""
from pathlib import Path
import nbformat as nb

root=Path(__file__).resolve().parent
cells=[
nb.v4.new_markdown_cell('''# Agentic Statistical Analysis Assistant MVP

This notebook executes a real compiled LangGraph and SciPy tools using synthetic data.
**Default mode is an offline deterministic test double, not an LLM.** To validate real agents, configure this project's DeepSeek API key, set `LIVE=True`, and rerun. Offline tests do not establish natural-language accuracy.

Planner: map intent to variable roles and ask about study design. Interpreter: consume the plan and numerical tool results; produce a cautious explanation. Other nodes are deterministic tools. No automatic nonparametric fallback or significance-driven method search.'''),
nb.v4.new_code_cell('''from pathlib import Path
import json
from IPython.display import Image, display
from langgraph.types import Command
from stat_assistant.agents import OfflineAgents, DeepSeekAgents, load_local_env
from stat_assistant.workflow import build_graph
from demo import fixtures, public_result

LIVE = False
load_local_env(Path('.env'))
agents = DeepSeekAgents() if LIVE else OfflineAgents()
graph = build_graph(agents)
trial, corr = fixtures()
print('Mode:', agents.mode)
display(trial.head())'''),
nb.v4.new_markdown_cell('''## A concrete comparison
Question: compare mean outcome between treatment and control. CSV does not prove independence. The graph pauses for explicit user metadata; resume happens in a separate node and does not repeat the planner API call.'''),
nb.v4.new_code_cell('''config = {'configurable': {'thread_id': 'notebook-trial'}}
pending = graph.invoke({'data': trial.to_dict(orient='records'), 'question': 'Compare mean outcome between treatment and control.', 'metadata': {}}, config)
print('Paused:', '__interrupt__' in pending)
if '__interrupt__' in pending:
    display(pending['__interrupt__'][0].value)
    result = graph.invoke(Command(resume={'design': 'independent', 'study_type': 'observational'}), config)
else:
    result = pending
display(public_result(result))'''),
nb.v4.new_markdown_cell('''## Short-term memory and follow-up
Reuse column roles and intent, not old conclusions. This example defines the year explicitly; an ambiguous "last year" must ask for date boundaries. The same thread retains the dataset, but diagnostics and statistics are recomputed.'''),
nb.v4.new_code_cell('''config_corr = {'configurable': {'thread_id': 'notebook-correlation'}}
first = graph.invoke({'data': corr.to_dict(orient='records'), 'question': 'Pearson correlation between x and y', 'metadata': {'design': 'independent'}}, config_corr)
follow = graph.invoke({'question': 'Only calendar year 2025', 'metadata': {'design': 'independent', 'filter': {'column': 'date', 'start': '2025-01-01', 'end': '2025-12-31'}}}, config_corr)
print('Full n:', first['result']['n'], 'subset n:', follow['result']['n'])
display(public_result(follow))'''),
nb.v4.new_markdown_cell('''## Unsupported design is handled, not hidden
Paired observations are outside the independent-sample MVP. Stopping is correct behavior, not a genuine system failure. A course breaking scenario must be an actual observed incorrect behavior, preferably from real model evaluation. Interpretation heuristics cannot guarantee semantic correctness.'''),
nb.v4.new_code_cell('''stopped = graph.invoke({'data': trial.to_dict(orient='records'), 'question': 'Compare outcome between groups', 'metadata': {'design': 'paired'}}, {'configurable': {'thread_id': 'notebook-paired'}})
display(public_result(stopped))'''),
nb.v4.new_markdown_cell('''## Diagram of this actual compiled graph
Each edge is an execution transition. Conditional edges depend on missing metadata, diagnostics, retry count or text checks. Handoff: Planner plan -> method/tools; plan + tool results -> Interpreter; draft -> critique. Ask-user uses an interrupt and resume.

PNG rendering uses LangGraph's built-in Mermaid renderer; network access to the renderer is required. The Mermaid source is always exported directly from this graph.'''),
nb.v4.new_code_cell('''Path('artifacts').mkdir(exist_ok=True)
Path('artifacts/graph.mmd').write_text(graph.get_graph().draw_mermaid(), encoding='utf-8')
try:
    png = graph.get_graph().draw_mermaid_png()
    Path('artifacts/graph.png').write_bytes(png)
    display(Image(png))
except Exception as exc:
    print('PNG rendering unavailable:', type(exc).__name__, '- use graph.mmd or rerun with network access.')''')]
n=nb.v4.new_notebook(cells=cells)
n.metadata['kernelspec']={'display_name':'Python 3 (project .venv)','language':'python','name':'python3'}
nb.write(n,root/'demo.ipynb')

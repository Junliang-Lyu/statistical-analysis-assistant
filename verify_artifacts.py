"""Execute the actual notebook with a project-local kernel definition."""
import json
import os
import sys
from pathlib import Path
import nbformat
from nbclient import NotebookClient

root=Path(__file__).resolve().parent
kernel=root/'.jupyter/kernels/python3'; kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                 'display_name':'Statistical Assistant (.venv)','language':'python'}),encoding='utf-8')
os.environ['JUPYTER_PATH']=str(root/'.jupyter')
os.environ['JUPYTER_RUNTIME_DIR']=str(root/'.jupyter/runtime')
os.environ['IPYTHONDIR']=str(root/'.jupyter/ipython')
book=nbformat.read(root/'demo.ipynb',as_version=4)
NotebookClient(book,timeout=120,kernel_name='python3',resources={'metadata':{'path':str(root)}}).execute()
nbformat.write(book,root/'demo.ipynb')
print('Executed notebook:',len([c for c in book.cells if c.cell_type=='code']),'code cells')
print('PNG exists:',(root/'artifacts/graph.png').exists())

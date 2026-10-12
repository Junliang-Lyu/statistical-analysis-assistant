# Coursework baseline — 2026-10-12

This is a self-contained coursework snapshot. The notebook embeds the current graph implementation and synthetic demonstration data; it does not depend on the version of application code elsewhere in this repository.

## LangGraph visualization assignment

Submit the two files in `langgraph/`:
- `LangGraph_Submission.ipynb`: executed notebook, actual graph rendering and node/edge/agent-handoff explanation below the image.
- `graph.png`: PNG generated from the compiled graph using `draw_mermaid_png()`.

The notebook has saved real DeepSeek outputs. To inspect it, open the rendered notebook on GitHub or in VS Code/Jupyter. To rerun, use Python 3.12+ with langgraph, pydantic, pandas, numpy, scipy, IPython and a Jupyter kernel installed. Without DEEPSEEK_API_KEY the notebook explicitly uses offline mode, which tests mechanics rather than LLM performance. Set that environment variable locally before launching the notebook kernel for live mode. Never paste a key into the notebook. PNG rendering requires network access to the Mermaid renderer.

Run cells in order. Check that the graph is compiled, the Welch demonstration reports n=50 and mean difference approximately 1.2532, and the explanation follow-up trace starts with reuse_result and omits run_test. The final code cell generates graph.png; compare the displayed image with the submitted PNG. The image must show the real graph, including conditional branches, clarification and bounded repair/rewrite paths.

## Midterm deliverables

- `midterm/Midterm_Presentation_Final.pptx`: five editable English slides, with speaker notes timed for five minutes.
- `midterm/Midterm_Writeup.docx`: editable English writeup.
- `midterm/Midterm_Writeup.pdf`: verified two-page version of the writeup.

The slides and writeup share a two-group walkthrough. The breaking scenario is a controlled, deliberately planted semantic error accepted by the checker, not an asserted DeepSeek-generated mistake. Benchmark counts distinguish mechanical checks, numerical agreement and semantic detector coverage. Human semantic accuracy has not been measured.

This folder is a baseline for team review; course submission and oral-exam booking are separate actions.

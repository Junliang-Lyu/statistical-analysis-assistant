# LangGraph visualization submission

Historical executed two-method snapshot (2026-10-11). Its supporting modules intentionally match its saved live outputs. The current four-method project is in the repository root and demo.ipynb; see docs/BENCHMARK_V2.md. Do not describe this historical notebook as a freshly executed four-method submission.

Open `LangGraph_Submission.ipynb` to inspect saved real-model outputs and the diagram. Submit this notebook, `graph.png`, and `GRAPH_EXPLANATION.md`; retain the supporting files in the ZIP so the notebook can be rerun.

## Rerun

Use Python 3.12. In this folder, install `requirements-lock.txt`, configure `DEEPSEEK_API_KEY` in the environment or copy the blank `.env.example` to `.env` and fill it locally, then run the notebook top-to-bottom. Select the Python environment with these dependencies. Do not upload `.env`. Saved outputs do not require credentials to read. Real execution calls DeepSeek and the Mermaid image renderer.

The included stat_assistant package is a copy of the implemented project, not pseudocode. The synthetic CSV is included. The image-generation cell directly uses `graph.get_graph().draw_mermaid_png()` on the graph that executed the analyses. The final markdown cell explains nodes, edges and handoff; the same text is provided separately.

This package addresses the LangGraph visualization assignment only. The presentation, two-page writeup and independent group review are separate tasks.

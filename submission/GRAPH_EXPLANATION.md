# Actual LangGraph explanation

## Nodes, edges and actual agent handoff

**LLM roles:** `planner` maps the question to variable roles, a goal and a filter, and requests clarification. `interpret` consumes the validated plan and numerical tool result to produce an English interpretation. These roles use the same DeepSeek model with distinct prompts.

**Other nodes:** `profile` describes the CSV; `ask_user` pauses/resumes with user metadata; `select_method` applies supported-method rules; `check_assumptions` diagnoses data and confirmed design; `run_test` executes SciPy; `critique` checks the interpretation; `revise` prepares one plan correction; `rewrite` prepares one text correction; `report_issue` stops; `output_memory` records the result in the session.

**Edges:** ordinary edges move shared state to the next processing step. After profiling, invalid inputs stop. After planning, missing information routes to `ask_user`; otherwise selection continues. Clarification errors stop; an unsupported plan needing clarification can return to planning. Checks route to computation, one repairable plan revision, or a stop. A computation error stops. Text review routes to one rewrite or output. Failed text after rewriting produces numerical results only. Both output and issue-reporting terminate. Retry counters prevent indefinite loops.

**Handoff:** the Planner's structured plan becomes input to `select_method`, `check_assumptions` and `run_test`. The plan together with the computed result becomes the Interpreter's input at `interpret`. Thus the actual agent-to-agent handoff is mediated by deterministic tools and shared graph state; there is no direct conversation or autonomous model-selected tool calling. The draft then passes to deterministic review, whose feedback can return to the Interpreter once.

**Memory:** the checkpointer isolates sessions by thread_id. The follow-up reuses prior roles on the same dataset but recomputes diagnostics, statistics and interpretation. It is in-process memory, not persistence across restarts.

**Limits:** only independent two-group Welch and Pearson are supported. Independence is user-confirmed. Diagnostics do not establish linearity, bivariate normality, missingness validity or causality. Interpretation checking is heuristic. Stopping an unsupported design is correct boundary behavior, not proof of a genuine model failure.

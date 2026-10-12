# Local statistical assistant MVP implementation plan

Goal: run a small real StateGraph locally, with a configured DeepSeek planner and interpreter and an explicitly labelled offline test double.

Approved scope: independent two-group Welch tests and Pearson correlation; no website, deployment, paired tests, automatic nonparametric fallback, or arbitrary generated code.

Architecture: tools.py handles CSV profiling, rule checks and SciPy computation. agents.py handles validated plans, interpretation and the API boundary. workflow.py owns routing, separate human interrupts, one plan revision, one interpretation rewrite and in-process session memory. demo.py and demo.ipynb show real graph runs using synthetic data. Tests cover numerical reference results, invalid inputs, human resume, retry bounds, follow-up recomputation and interpretation failure.

- [ ] Write tests first and observe missing implementation failures.
- [ ] Implement tools and bounded model adapters.
- [ ] Build StateGraph with checkpointer and explicit terminal states.
- [ ] Verify offline traces, numerical results, memory isolation and invalid outputs.
- [ ] Generate synthetic CSVs, executed notebook and graph diagram from compiled graph.
- [ ] Validate a real DeepSeek run if this project's credentials are available; otherwise document the exact remaining configuration step.

Statistical policy: confirm independence from user metadata; warn on distribution diagnostics, stop on severe small-sample/extreme-outlier combinations under an explicitly conservative project policy. No p-value-driven method search. Pearson small-n is not a reason to switch to Spearman. Observational and unverified designs never yield causal conclusions. All results retain effective n, missing-row counts and uncertainty.

Tests use a deterministic fake agent only to validate code paths, never to claim LLM method accuracy. In-memory checkpoints disappear on process restart. Each new analysis resets counters/results while keeping the prior plan only for explicit follow-ups on the same dataset fingerprint.

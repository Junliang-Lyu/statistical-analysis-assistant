# MVP verification record

Local scope: actual LangGraph, SciPy, in-memory checkpoints, separate planner/interpreter adapters and explicitly labelled offline doubles. No deployment or GitHub publishing.

Verified with pytest: Welch statistic, p and interval against SciPy; Pearson result and interval; complete-case missing count; nonfinite and constant data refusal; invalid date rejection; human pause/resume; planner not called again on resume; follow-up recomputation (20 -> 10); new dataset resets prior plan; thread isolation; paired design refusal; one invalid-plan revision; one invalid-interpretation rewrite then numeric-only output.

Offline CLI demonstration: independent-group comparison n=50, correlation n=20, explicit-calendar-year follow-up n=10, paired-design stop. The notebook was executed in the project Python environment, five code cells completed. Built-in draw_mermaid_png generated graph.png from the same compiled StateGraph, and the PNG was visually inspected.

Verified live: DeepSeek comparison n=50 with user interrupt/resume, correlation n=20, follow-up n=10, and refusal of paired design. Final smoke run completed all three supported analyses with interpretations. Seventeen tests passed.

At the initial smoke-test stage, natural-language benchmarking and a real model breaking scenario were not yet verified. The dated addendum below supersedes those two items. Independent human interpretation labels, long-term persistence, website UI and PPT/writeup remain outstanding. Test doubles validate software mechanics, not agent intelligence. Do not submit offline results as live multi-agent evidence.

Known statistical limits: only independent observations, two groups or Pearson; conservative diagnostic policy rather than universal decision tree; CSV cannot establish independence or randomization; missingness may bias complete-case analysis; univariate diagnostics cannot establish linearity; interpretation checks catch some errors but do not verify full semantics. Fixed thresholds and alternative methods must be reviewed before extending scope.


## Real smoke-test findings and fixes

- Planner initially treated unknown study design as unsupported and skipped clarification. Routing now prioritizes explicit clarification, and the planner prompt separates ambiguity from unsupported methods. A regression test reproduces the original behavior.
- Causal keyword matching rejected negated causal statements; a regression test and sentence-level negation handling reduce this false positive. This remains heuristic, not full semantic validation.
- Model interpretations sometimes inserted numeric literals rather than tool placeholders. The prompt now specifies thresholds/confidence levels in words, and rewrite feedback includes offending literals plus the rejected draft. Retry remains capped at one. Final smoke outputs used the approved placeholders and passed.
- The key was initially entered in .env.example. It was moved to ignored .env and the example restored to blank-key template without displaying the key. No files were published.

The CLI live artifacts are synthetic only. demo.ipynb remains an explicitly offline teaching notebook; set LIVE=True to run it against the configured provider. A successful final smoke run is not evidence of general statistical or interpretation accuracy.

## 2026-10-11 benchmark addendum

Local UI addendum: standard-library localhost service and English-first interface with Chinese assistance added without new dependencies. Twenty-six tests pass, including UI-adapter pause/resume, session isolation, CSV parsing, paired refusal and follow-up n=20 to n=10. Browser verified initial page and offline Welch pause/confirmation/result cards. Live provider behavior was not rerun specifically through the UI. Default offline planner/interpreter are labelled test doubles; real DeepSeek is selectable. No deployment.

Current code passes 23 tests, the offline CLI demonstrations and all five executed notebook code cells. The graph PNG was regenerated from the compiled graph. The initial 12-case live benchmark achieved 10/12 expected outcomes and 6/6 assessed numerical reference matches. A genuine method-description failure was found despite correct calculation. Targeted fixes produced a three-case successful recheck, but a subsequent clarification-only run still withheld interpretation for a missing p-value placeholder. No full-suite pass or general semantic accuracy is claimed. See EVALUATION.md for the retained evidence, fixes and instructor-question mapping.

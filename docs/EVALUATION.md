# MVP evaluation — 2026-10-11

Update 2026-10-12: the current application now supports all four methods (Welch, Pearson, chi-square, simple OLS). See BENCHMARK_V2.md for the separate 31-case evaluation and interpretation challenge set. Sections below describe the retained two-method baseline, not current scope. The submission folder retains its historical live notebook snapshot.

## What is implemented

Actual LangGraph orchestration with a DeepSeek Planner and Interpreter; deterministic CSV profiling, method selection, assumption diagnostics and SciPy computation. Supported analyses are independent two-group Welch tests and Pearson correlation. Human clarification, one plan revision, one interpretation rewrite and in-process follow-up memory are implemented. Other designs stop explicitly.

## Evidence and limits

- Current local verification: 23 pytest tests passed; offline demonstration completed comparison (n=50), correlation (n=20), follow-up recomputation (n=10), and paired-design refusal. All five notebook code cells executed and the compiled graph produced a PNG.
- Initial live benchmark: 12 fixed synthetic cases; 10/12 expected outcomes, 12/12 acceptable goals, 6/6 assessed variable-role assignments, 6/6 sample counts, 6/6 numerical comparisons against reference computation, and 3/3 clarification cases. See ../artifacts/benchmark_report.md and benchmark_live.json.
- After targeted fixes, three selected live cases passed. See ../artifacts/benchmark_recheck_report.md and benchmark_recheck_live.json. This is a selective recheck, not a full-suite pass.
- A later clarification-only live recheck returned numeric results without interpretation: the rewritten explanation omitted the required p-value placeholder. See ../artifacts/benchmark_clarification_final_report.md and benchmark_clarification_final_live.json. This failure is retained; no additional calls were made to select a successful run.

These are small, single-run synthetic evaluations. Interpretation examples were reviewed by the development assistant, not independently labelled by human reviewers. Numerical agreement does not establish statistical validity, semantic accuracy or causality. No interpretation-accuracy percentage is claimed.

## A genuine breaking scenario for the presentation

Input: the supplied trial dataset and a question comparing the treatment and control outcomes. The initial live run selected and computed Welch correctly, but the Interpreter described the result as a Pearson-type linear association and treated uncontrolled confounding as a Welch assumption. The earlier mechanical checks accepted this text. The original output remains in benchmark_live.json under welch_clean.

Why it breaks: correct tool results do not constrain every sentence of generated interpretation. Placeholder validation prevents invented numbers, but cannot by itself detect a wrong methodological explanation.

Changes made: stronger method-specific instructions, checks for Welch/Pearson terminology conflicts, more specific rewrite feedback, and updated plan reasons after human clarification. Tests cover these regressions. Remaining risk: a fluent but misleading explanation can evade keyword checks. Independent human review of the benchmark is the next evaluation step; additional semantic validation would require its own evaluation.

The later missing-placeholder failure demonstrates a different boundary: after at most one rewrite, the system withholds the explanation and displays the computed results. It terminates instead of forcing a successful interpretation.

## Responses to the instructor's design questions

1. **Concrete plan and method choice:** expose the structured plan, variable roles, design and reason. Two independent groups plus a continuous outcome route to Welch; two numeric variables and an association question route to Pearson. Unknown design triggers a question.
2. **Actual checks:** group/sample counts, finite values, constants, missing rows, Shapiro-Wilk where supported, skew and outlier diagnostics. Independence requires user confirmation. Severe small-sample distribution problems stop under the documented conservative policy. No automatic change to Mann–Whitney is implemented, because it changes the target of inference.
3. **Stopping condition:** at most one invalid-plan revision and one interpretation rewrite. Unsupported designs and serious diagnostic problems stop. Failed interpretation validation preserves numeric results only.
4. **Memory:** on the same dataset, reuse prior variable roles and intent for a follow-up. Filter the requested dates and recompute diagnostics, effective sample size, statistics and interpretation. The example changes n=20 to n=10. Checkpoints are in memory and disappear when the process exits.
5. **Nonmisleading interpretation:** code supplies effect, p, interval and n; generated text must reference their placeholders. Checks reject some causal/overconfident statements. This is partial protection, not a semantic guarantee; the genuine failure above is evidence of its limits.
6. **Borderline benchmark:** includes unequal variances, missing values, unknown independence, ambiguous outcome columns, ambiguous year filtering, paired designs, constant variables, tiny samples and a nonlinear relationship with near-zero Pearson correlation. Ambiguous questions must ask or stop; there is no requirement that every case produce an answer.

## Still to do before submission

Have group members independently review interpretations and explain the entire workflow. Prepare the five-slide deck and two-page writeup using the same actual walkthrough and retained failure. Confirm that the submitted notebook, compiled graph image and handoff explanation meet the original assignment. The live notebook mode uses the configured API; its default offline mode is explicitly a software demonstration, not evidence of LLM performance. Website and GitHub publication remain future work.

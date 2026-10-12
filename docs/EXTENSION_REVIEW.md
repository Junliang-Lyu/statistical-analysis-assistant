# Four-method extension review — 2026-10-12

## Proposed minimal scope

Add categorical association via Pearson chi-square independence test, and simple ordinary least-squares regression with one predictor and intercept. Retain independent-observation confirmation and conservative no-causality interpretation. Do not add multivariable models, paired/clustered inference, arbitrary generated code or automatic significance-driven method search.

Chi-square: two explicitly categorical columns, complete-case contingency table, at least two observed categories per variable. Reject all expected cell counts below one, or more than twenty percent below five, under a documented approximation policy; report the actual expected table. No automatic Fisher fallback in this scope. Report chi-square, degrees of freedom, p, sample count and Cramer's V. Do not invent a generic ninety-five percent interval for V; method-specific interpretation/UI must permit an unavailable interval.

Regression: x predictor, y outcome, two distinct numeric nonconstant columns, at least five complete cases under service policy. Report slope, intercept, R-squared, slope t/p and ninety-five percent slope interval. Diagnose residual distribution, leverage/influence and heteroscedasticity with clearly stated limits. Suspicious diagnostics produce warnings or a documented stop, not a silent new estimator. No automatic predictor/outcome inversion or causal wording.

## Existing benchmark audit findings

- The unsupported_regression case becomes obsolete when regression is implemented; replace it with a supported reference case, preserving historical baseline artifacts.
- Numeric-reference scoring currently has only Welch and Pearson branches. Add explicit branches for chi-square and regression, including coefficients/statistic/df and method-specific uncertainty.
- Require explicit expected method checks, not only goal checks.
- Separate execution/numerical success from interpretation acceptance. results_only can be a safe text failure while statistics are correct; do not hide it in one pass percentage.
- Follow-up benchmark coverage must assert filtered n and reference results in the same thread, not merely verify an ambiguous last-year interruption.
- Keep ambiguous and nonlinear cases. Standard references check implementation agreement, not whether all statistical assumptions or conclusions are valid.
- Require a nonempty selected-case set, and report invalid case IDs rather than a misleading zero-case run.
- Reports must refer to their actual output prefix rather than hard-coded benchmark_live.json.
- Independent human interpretation review remains missing. Code-generated scores or another model's review do not replace human labels.

## Manual interpretation review procedure

Freeze the evaluated output and associated question, plan, diagnostics and numeric result. Two team members independently label each interpretation before discussing disagreements. Fields: numerical consistency; correct method/variables/direction; effect and uncertainty meaning; causality/overstatement; required caveats; overall acceptable/misleading/uncertain. Record a quotation and rationale for each problem. Missing interpretation is withheld, not an acceptable generated interpretation. Resolve disagreements with a documented discussion; report both counts and unresolved cases, never fabricate human labels.

## Assignment scope confirmed

Midterm-Deliverables: upload both a maximum-five-slide deck and maximum-two-page written document by October 16, 2026, 11:59pm according to the supplied course screenshot. Oral exam: book a slot and prepare all members for Q&A. Course timezone and available appointment slots require separate confirmation. Do not book on behalf of the team without an explicit slot instruction. Presentation authoring follows completion of core methods and evaluation.

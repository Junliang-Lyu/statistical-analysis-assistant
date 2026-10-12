# Four-method benchmark guide

All datasets are synthetic and generated with fixed seeds. Individual CSV and same-named JSON files are in `examples/benchmark_v2/`, separated into five folders:

| Folder | Purpose | Cases |
|---|---|---:|
| normal | Clean Welch, Pearson, chi-square and regression | 4 |
| boundary | Unequal variance, missing values for all methods, non-square categorical table, nonlinear correlation, influential/heteroscedastic/negative-slope regression | 10 |
| clarification | Unknown design, ambiguous outcome, unspecified year and regression direction | 4 |
| stop | Paired design, sparse/constant/coded categories, constant/tiny numerical data, perfect fit, extreme small groups, unsupported multivariable regression | 11 |
| followup | Same-thread 2025 Pearson and regression recomputation | 2 |

Each JSON contains a specific question, metadata, prespecified plan, expected action and reason. Computable cases also have explicit numerical reference values. The CSVs and JSONs are separated from result records to avoid confusing ground truth with model output.

## Run

```powershell
.\.venv\Scripts\python.exe benchmark_suite.py --export-only
.\.venv\Scripts\python.exe benchmark_suite.py --mode offline --output offline_my_run
.\.venv\Scripts\python.exe benchmark_suite.py --mode live --output live_my_run
.\.venv\Scripts\python.exe benchmark_suite.py --mode live --category normal --output live_normal_my_run
.\.venv\Scripts\python.exe benchmark_suite.py --mode live --case regression_2025 --output live_followup_my_run
```

Choose a fresh output name; existing evidence is never overwritten. Results are separated by category inside `artifacts/benchmark_v2/<output>/`, with REPORT.md and results.json. Real model mode requires the configured API and incurs usage. Offline uses prespecified gold plans, not a language model; it validates numerical tools and orchestration only.

## What scores mean

- Mechanical checks: extracted goal/roles, expected method, execution/stop/clarification, numerical references and selected warning/memory assertions. Regression references use a separate design-matrix calculation; chi-square references use the contingency formula and chi-square tail. Welch/Pearson use separately called SciPy references. Agreement cannot prove statistical assumptions.
- Interpretation accepted: schema/placeholders and partial wording checks passed. This is not a semantic accuracy label. Computation success and explanation acceptance are reported separately.
- Semantic evaluation: inspect whether text uses the correct effect meaning, reflects uncertainty/warnings and avoids causal or no-effect claims. An automated challenge set can measure detection of specific planted errors, but not all fluent misleading statements. Human spot-checks remain useful; no mandatory two-person approval step is inside the graph.

Run `python interpretation_benchmark.py` to inspect the controlled interpretation challenge set in `examples/interpretation_checks/valid` and `planted_errors`. Four valid templates were accepted; nine of twelve planted errors were caught. Three semantic errors escaped: correlation described as a percentage increase, a frequentist interval described as probability of a fixed parameter, and zero linear evidence described as no relationship. These are authored mutations, not measured errors from a real model or human-review labels. The misses are retained to demonstrate limits of automatic checking.

## Initial live result and expectation audit

The initial live run completed 31 cases: strict mechanical checks 28/31; 17 statistical results were computed, with matching reference values, and all 17 explanations passed the partial code checks. No general reliability percentage is claimed.

Three strict mismatches are retained:
- paired_design: model selected unsupported and stopped correctly; the strict goal expected difference. This is an overly narrow goal expectation, not unsafe computation.
- chi_square_one_category: model explained that the test is not estimable and requested different columns/data, whereas the strict benchmark expected direct stop.
- pearson_constant: model explained zero variance and requested different columns, whereas the strict benchmark expected direct stop.

All three avoided producing a numeric inference. They are safe deviations from a strict expected route; do not relabel the saved run as 31/31. Future benchmark specifications can prespecify acceptable rejection/clarification sets before running. Historical two-method artifacts and the first v2 run remain separate.

The development assistant inspected selected live explanations for influence/heteroscedasticity warnings, slope direction, unsigned Cramer's V and the nonlinear caveat. This is not independent human annotation or a measured semantic-accuracy score.

Sources: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html ; https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.linregress.html . The chi-square expected-count threshold and minimum sample sizes are explicit project policies, not universally sufficient conditions.

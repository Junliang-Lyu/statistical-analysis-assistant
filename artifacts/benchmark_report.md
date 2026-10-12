# Live MVP benchmark

Model: deepseek-chat. Cases: 12. Prespecified mechanical checks passed: 10/12.

Synthetic fixed datasets; one run per case. Not a general accuracy estimate. Interpreter semantics require independent human review.

| Case | Status | Checks |
|---|---|---|
| welch_clean | completed | pass |
| welch_unequal_variances | results_only | outcome |
| missing_complete_cases | completed | pass |
| pearson_clean | completed | pass |
| unknown_design | results_only | outcome |
| ambiguous_outcome | interrupted | pass |
| unsupported_regression | stopped | pass |
| paired_design | stopped | pass |
| constant_variable | stopped | pass |
| too_few_pairs | stopped | pass |
| ambiguous_last_year | interrupted | pass |
| nonlinear_boundary | completed | pass |

## Manual interpretation review
Read the interpretations in benchmark_live.json. Check direction, effect/interval meaning, uncertainty, causal language, missingness and nonlinear boundary. A code check passing does not certify semantics.

The nonlinear case deliberately has U-shaped dependence and near-zero Pearson r. A claim of no relationship would be a genuine failure; a qualified lack of linear evidence is acceptable.

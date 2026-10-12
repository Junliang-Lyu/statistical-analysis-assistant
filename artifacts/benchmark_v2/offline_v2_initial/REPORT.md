# Four-method benchmark

Mode: offline; mechanical checks: 31/31.
Interpretations accepted by code: 14/17 computed results. This is NOT semantic accuracy.

Offline uses prespecified gold plans, not language reasoning. Numerical agreement is not proof of statistical assumptions. Live runs are one attempt per case with bounded internal repair; failures retained. Human semantic labels are not fabricated.

| Category | Case | Status | Failed checks | Text accepted |
|---|---|---|---|---|
| normal | welch_clean | completed | none | True |
| normal | pearson_clean | completed | none | True |
| normal | chi_square_2x2 | results_only | none | False |
| normal | regression_clean | completed | none | True |
| boundary | welch_unequal_variance | completed | none | True |
| boundary | welch_missing | completed | none | True |
| boundary | pearson_missing | completed | none | True |
| boundary | chi_square_missing | results_only | none | False |
| boundary | regression_missing | completed | none | True |
| boundary | chi_square_2x3 | results_only | none | False |
| boundary | pearson_nonlinear | completed | none | True |
| boundary | regression_influential | completed | none | True |
| boundary | regression_heteroscedastic | completed | none | True |
| boundary | regression_negative_slope | completed | none | True |
| clarification | unknown_design | completed | none | True |
| clarification | ambiguous_outcome | interrupted | none | False |
| clarification | ambiguous_last_year | interrupted | none | False |
| clarification | regression_direction | interrupted | none | False |
| stop | paired_design | stopped | none | False |
| stop | chi_square_sparse | stopped | none | False |
| stop | chi_square_one_category | stopped | none | False |
| stop | chi_square_numeric_codes | stopped | none | False |
| stop | pearson_constant | stopped | none | False |
| stop | pearson_too_few | stopped | none | False |
| stop | regression_constant | stopped | none | False |
| stop | regression_too_few | stopped | none | False |
| stop | regression_perfect | stopped | none | False |
| stop | welch_extreme_small_group | stopped | none | False |
| stop | unsupported_multivariable | stopped | none | False |
| followup | correlation_2025 | completed | none | True |
| followup | regression_2025 | completed | none | True |

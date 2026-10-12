# Boundary cases

Each CSV has a same-named JSON containing question, confirmed metadata, expected behavior, plan and (where applicable) numerical reference. All data are synthetic.

| Case | Expected | Note |
|---|---|---|
| welch_unequal_variance | result | Welch does not require equal variances. |
| welch_missing | result | Complete-case deletion; report one omitted row. |
| pearson_missing | result | Complete-case deletion; report one omitted row. |
| chi_square_missing | result | Complete-case deletion; report one omitted row. |
| regression_missing | result | Complete-case deletion; report one omitted row. |
| chi_square_2x3 | result | Non-square table, degrees of freedom two. |
| pearson_nonlinear | result | Near-zero linear correlation does not mean no relationship; U-shaped dependence is present. |
| regression_influential | result | Influential-point warning; no automatic deletion. |
| regression_heteroscedastic | result | Report residual diagnostics. Ordinary slope inference may be unreliable; no automatic robust estimator. |
| regression_negative_slope | result | Negative slope; not a causal effect. |

# Stop cases

Each CSV has a same-named JSON containing question, confirmed metadata, expected behavior, plan and (where applicable) numerical reference. All data are synthetic.

| Case | Expected | Note |
|---|---|---|
| paired_design | stop | No silent change to independent design. |
| chi_square_sparse | stop | Expected frequencies violate approximation policy. |
| chi_square_one_category | stop |  |
| chi_square_numeric_codes | stop | Ask for text-label preprocessing or stop; do not silently recode. |
| pearson_constant | stop |  |
| pearson_too_few | stop |  |
| regression_constant | stop |  |
| regression_too_few | stop |  |
| regression_perfect | stop | Near-perfect fit: conservative residual-inference policy. |
| welch_extreme_small_group | stop | Severe small-sample/extreme-value policy; no method switch. |
| unsupported_multivariable | stop |  |

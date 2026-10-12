# Clarification cases

Each CSV has a same-named JSON containing question, confirmed metadata, expected behavior, plan and (where applicable) numerical reference. All data are synthetic.

| Case | Expected | Note |
|---|---|---|
| unknown_design | result | Must pause; synthetic evaluator confirms independent observations. |
| ambiguous_outcome | interrupt | No arbitrary outcome choice. |
| ambiguous_last_year | interrupt | Date boundaries not supplied; must ask. |
| regression_direction | interrupt | Must ask which variable is predictor/outcome. |

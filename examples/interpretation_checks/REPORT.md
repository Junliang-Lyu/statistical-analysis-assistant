# Interpretation challenge set

Controlled templates and deliberately planted errors. This measures known detector coverage, not real-model semantic accuracy.
Planted errors caught: 9/12. Valid templates accepted: 4/4.

| Case | Expected valid | Code accepted | Note |
|---|---|---|---|
| welch_clean_valid | True | True | Correct controlled template with tool placeholders. |
| welch_clean_wrong_number | False | False | Inserted unsupported numerical literal and removed p placeholder. |
| welch_clean_causal | False | False | Unqualified causal assertion despite observational design. |
| pearson_clean_valid | True | True | Correct controlled template with tool placeholders. |
| pearson_clean_wrong_number | False | False | Inserted unsupported numerical literal and removed p placeholder. |
| pearson_clean_causal | False | False | Unqualified causal assertion despite observational design. |
| chi_square_2x2_valid | True | True | Correct controlled template with tool placeholders. |
| chi_square_2x2_wrong_number | False | False | Inserted unsupported numerical literal and removed p placeholder. |
| chi_square_2x2_causal | False | False | Unqualified causal assertion despite observational design. |
| regression_clean_valid | True | True | Correct controlled template with tool placeholders. |
| regression_clean_wrong_number | False | False | Inserted unsupported numerical literal and removed p placeholder. |
| regression_clean_causal | False | False | Unqualified causal assertion despite observational design. |
| welch_wrong_method | False | False | Welch misdescribed as Pearson. |
| pearson_percent_misinterpretation | False | True | Semantic blind spot: coefficient described as an eighty-percent increase using words, which can evade the current checks. |
| regression_interval_probability | False | True | Semantic blind spot: frequentist interval described as probability of the fixed parameter. |
| nonlinear_no_relationship | False | True | Near-zero Pearson does not exclude U-shaped dependence; this wording can evade current phrase checks. |

Do not infer overall reliability from these counts. Missing semantic detections illustrate why format/keyword checks are insufficient. Inspect actual model outputs separately; no fabricated human-review scores.

# Test cases and expected behavior

All included CSVs are synthetic. No student or patient records are included.

## Browser walkthrough (real DeepSeek)

Start `python ui_server.py --port 8766` and open http://127.0.0.1:8766/ . Upload `examples/student_study_demo.csv`, select DeepSeek, and ask:

`Is study_hours associated with exam_score? Calculate the Pearson correlation.`

Confirm Independent, Observational, x=study_hours and y=exam_score. Expected numerical output: n=60, r≈0.79970119, p≈1.82356e-14, 95% interval≈[0.68484346, 0.87578549]. Then click the explicit 2025 date-window button in the same session. Expected: n=30, r≈0.81310555, p≈4.75843e-8, interval≈[0.64044684, 0.90752671]. Interpretations vary and may be withheld if validation fails. No causality is established.

## Built-in browser cases

| Case | Expected behavior |
|---|---|
| Two-group comparison | Ask for independent-design confirmation, run Welch; n=50, treatment-minus-control mean difference≈1.25320204 |
| Correlation | Ask for design confirmation, run Pearson with n=20; explicit 2025 follow-up recomputes n=10 |
| Paired design | Stop: paired observations are unsupported; do not force independent-sample inference |

Default offline mode uses deterministic agent doubles. It exercises mechanics, not arbitrary natural-language reasoning or LLM accuracy.

## Automated verification

`python -m pytest -q` runs numerical references, missing/nonfinite/constant-data checks, invalid dates, human pause/resume, retry limits, thread isolation, dataset changes, interpretation refusal, CSV parsing and UI follow-ups. Twenty-six tests passed at this version.

`python benchmark.py` calls real DeepSeek for twelve predefined cases and writes synthetic benchmark artifacts. This incurs provider usage and may replace the local baseline report; preserve supplied evidence before running. Cases include clean/unequal-variance Welch comparisons, missing complete cases, correlation, unknown design, ambiguous outcome, unsupported regression, paired design, constant variables, too few pairs, ambiguous last-year filtering, and a nonlinear boundary.

The supplied baseline achieved 10/12 expected outcomes. Targeted rechecks are separate from a full rerun. A genuine initial failure described Welch results as Pearson despite correct numbers. A later missing-placeholder failure caused numerical-only output after the bounded rewrite. No general semantic-accuracy claim is made; independent human interpretation review remains pending. See EVALUATION.md and artifacts/benchmark_report.md.

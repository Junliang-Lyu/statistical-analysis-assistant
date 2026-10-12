# Student study demo — live UI test, 2026-10-11

Synthetic data only: examples/student_study_demo.csv. Seed 20261011, sixty independent fictional participants, thirty each in 2024 and 2025. Columns: participant_id (identifier, not an analysis variable), study_hours, exam_score, date. Scores are generated from hours with noise; this is not empirical evidence about students.

## Two completed UI rounds

Uploaded CSV through the browser file picker and selected DeepSeek real-model mode.

Round one question: `Is study_hours associated with exam_score? Calculate the Pearson correlation.`
Planner chose x=study_hours and y=exam_score. The graph paused for design confirmation. Confirmed independent observations and observational study. Browser showed Analysis complete, n=60, r=0.79970, p=1.824e-14, interval [0.6848, 0.8758]. Generated interpretation stated no causality. Trace included planner, human clarification, diagnostic checks, SciPy calculation, interpreter and review.

Round two: clicked `Use explicit 2025 date window` in the same session, without reuploading. Browser showed Analysis complete, n=30, r=0.81311, p=4.758e-8, interval [0.6404, 0.9075]. Planner explicitly reused prior variable roles and applied the date filter. Interpretation did not imply causation. Results match separately computed SciPy reference values in artifacts/student_demo_reference.json at displayed precision. These two successes are not a general accuracy guarantee.

## Repeat the test

1. Open http://127.0.0.1:8766/ . If unavailable, run `.\.venv\Scripts\python.exe ui_server.py --port 8766` from the project directory.
2. Upload examples/student_study_demo.csv using the file control.
3. Enter the round-one question above. Select DeepSeek, then Run analysis.
4. If asked, choose Independent and Observational. Check x=study_hours, y=exam_score. Click Confirm & continue.
5. Read Effective n, Effect (Pearson r), confidence interval and explanation. Inspect Analysis plan and Actual execution trail.
6. Click Use explicit 2025 date window in the results area. Do not use Run analysis for this follow-up; that starts a new session.
7. Expect n=30 and a recomputed r around 0.81311. Model wording may vary or be withheld if validation fails; the calculation should match.

The data preview continues to show the original uploaded dataset; Effective n is the number used by the current analysis after filtering. The example date button supplies an explicit interval, so no ambiguous-year clarification is needed.

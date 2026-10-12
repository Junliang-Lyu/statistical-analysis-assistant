# Follow-up and test CSV update

The follow-up selector defaults to **Explain existing result**. This reuses the current session result, plan and diagnostics, skips Planner/method selection/statistical execution, and passes the actual follow-up question to Interpreter. Its trace begins with `reuse_result`. Existing text validation and one rewrite still apply. This is model-generated explanation, not a semantic correctness guarantee.

Choose **Run a new analysis** when changing variables, dates or research goals. The existing year button always recalculates. Explanation mode intentionally cannot change the dataset or filter. A completed numeric result is required; interrupted/stopped sessions cannot be explained.

The input sidebar exposes the selected built-in synthetic CSV filename, row count, first six rows and a Download CSV button, even before analysis. These files are generated from the same fixed fixtures used for computation. Uploaded CSVs can also be downloaded locally; their preview appears after analysis. No arbitrary filesystem paths or secrets are exposed by the example endpoint.

Validation: regression tests cover unchanged result/diagnostics, no Planner or run_test during explanation, missing-result rejection, analysis after explanation recalculating a subset, and CSV content/unknown case validation. Browser checks and live model results are recorded separately from automated tests.

Verified on 2026-10-12: 74 automated tests passed. Live DeepSeek browser test answered the original mean-difference/interval/causality follow-up directly, preserving the numeric result with trace reuse_result -> interpret -> critique -> output_memory. Browser download produced trial.csv; sidebar preview displayed the first six rows. JavaScript syntax check passed.

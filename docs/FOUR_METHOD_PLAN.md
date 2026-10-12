# Four-method implementation and evaluation plan

Approved scope: add chi-square independence for two categorical variables and one-predictor OLS regression with intercept. No Fisher fallback, method search, multivariable/paired/clustered inference, or AI Reviewer. Preserve original benchmark artifacts and existing tests.

- Write reference and boundary tests for chi-square (2x2/2x3, sparse counts, constants, missing rows) and regression (matrix-reference slope/interval, direction, residual warnings, tiny/constant/perfect data).
- Implement method-specific preparation, checks and numeric results without dependencies. Chi-square uses correction=False and documents it; Cramer's V interval is unavailable. Numeric categorical codes require explicit preprocessing to labels.
- Extend plan schema, method mapping, offline doubles and real-model prompts. Keep placeholder checking method-aware and bounded retries.
- Extend English UI sample menu and result labels, including unavailable interval and OLS fit fields.
- Create versioned benchmark_v2 datasets in separate normal/boundary/clarification/stop/followup directories, with questions, prespecified plans, expected outcomes and independent numeric references. Separate computation success from interpretation acceptance and semantic review.
- Run tools/graph tests, full offline benchmark (mechanics only) and one live run per case. Retain failures. Export interpretable records for manual review without inventing human labels.
- Update docs, refresh supporting submission modules/graph consistently, and verify local UI. Preserve historical executed submission evidence if fresh live notebook execution is not performed.

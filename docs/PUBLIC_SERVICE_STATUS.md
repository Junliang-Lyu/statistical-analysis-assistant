# Public service preparation

The public adapter and release tooling are local preparation only. No Lightsail connection, server configuration change, Investment Lab change, or production deployment has been performed.

## Boundaries

- Existing local adapter remains the default local workflow.
- Public adapter validates configured Host and exact Origin; Caddy must overwrite X-Forwarded-For and the application port must remain private.
- Browser cookie owns its session. Thirty-minute idle expiry is checked periodically; no uploaded CSV is written to disk. Provider requests include questions, column names/category labels and statistical summaries.
- CSV: 1 MB, 10,000 rows, 50 columns. Question: 2,000 characters. At most 30 sessions and two admitted API requests, with serialized analysis.
- SQLite persists hashed-client daily quotas and conservative model-cost reservations. Default daily/monthly budgets are $0.50/$5; 10 operations per client and 100 global operations per UTC day.
- Cost ceilings must be explicitly configured for the selected model. Live mode remains disabled if pricing or key is missing. Reservations use a conservative input-size bound and maximum output size; failed calls are not refunded. This intentionally understates remaining credit and is not a provider invoice. Provider price changes require updating configured ceilings.
- Containers run non-root, with read-only application files, no host application port and a separate stats network. The budget volume is retained during rollback.

## Deployment gates

An unapplied shared-Caddy proposal is now prepared in [the integration review](CADDY_INTEGRATION_REVIEW.md): add a stable directory mount/import and external stats network to the main site's base configuration. It requires no Investment Lab changes, but does require approval to change the main site's two configuration files and maintain them in future releases/rollbacks. `stats.caddy` remains a proposal, not an instruction to change/recreate existing Caddy. Do not enable server auto-deployment before this is reviewed and confirmed.

The server should only receive verified release archives. `deploy/build-release.ps1` tests, builds, runs an offline HTTP image smoke test, saves the image and packages checksums. GitHub CI performs the same tests and image check without secrets. A stats-only puller and systemd templates are prepared: the service defaults to verification-only. Applying a release additionally requires `--apply` and `STATS_GATEWAY_READY=1`; do not enable those before shared ingress is resolved. The site Lab entry is deferred; no unverified live link is published.

## Local verification (2026-10-12)

- 85 automated tests passed; image HTTP smoke tests covered all four methods and explanation follow-ups without credentials.
- Release `20261012T204229Z` was built locally, and its archive layout and SHA-256 were verified. Release files are excluded from Git.
- An isolated local Caddy served two stub sites and the stats service together; explanation reused statistics and the 2025 filter recomputed 20 rows as 10 rows. Cross-browser session access was rejected.
- The application image runs as UID 10001 and has no published host port. This test does not demonstrate persistence across production Investment Lab releases.

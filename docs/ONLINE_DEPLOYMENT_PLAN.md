# Online Lab implementation plan

**Goal:** Host the existing statistical assistant as a real online demo linked from the personal site's bilingual Lab pages.

**Architecture:** Preserve the local adapter. Add a public server behind the existing Caddy HTTPS proxy on an isolated Docker network. Reuse the current UI and graph. Server-side DeepSeek key only; no raw-file persistence; expiring in-memory sessions. A SQLite request quota persists across restarts and bounds public model activity.

**Tech stack:** Existing Python/LangGraph/SciPy stack, Python standard library, Docker/Caddy, existing MDX site. No additional application dependencies.

## Steps

- [x] Add meaningful tests for host/origin validation, session-owner isolation, expiry, persistent global/per-client quotas and public CSV limits.
- [x] Add isolated public adapter with HTTPS origin configuration, request/concurrency quotas, bounded sessions and health endpoint. Preserve local adapter defaults.
- [x] Add deployment image, isolated Compose override and Caddy site configuration; keep secrets out of images and source.
- [x] Add public-demo privacy/usage guidance without altering local behavior.
- [x] Run existing tests plus public-adapter tests and verify local public-mode HTTP flow.
- [ ] Prepare bilingual Lab entries following the current content schema and existing styling; preserve unrelated edits.
- [ ] Resolve and confirm persistent shared-Caddy integration, deploy only the new service, verify HTTPS and real model analysis/follow-up before publishing Lab links.

## Default public limits

Each API operation consumes a quota slot before execution: 10 operations per client per UTC day and 100 globally per UTC day, at most 5 model calls per operation from the existing graph. Quota storage must survive container restarts. Limit CSV uploads to 1 MB, 10,000 rows and 50 columns; question length to 2,000 characters. Expire sessions after 30 minutes, bound memory session count and cap concurrent operations. Rejections do not pretend analysis succeeded. State resets on process restart.

## Pending deployment information

No server connection is authorized yet. Shared Caddy must retain the stats network and site configuration across existing release operations without changing Investment Lab. Proposed hostname: `stats.jun-liang-lyu.com`, subject to actual DNS configuration. Do not publish links or claim a live deployment until end-to-end checks pass.

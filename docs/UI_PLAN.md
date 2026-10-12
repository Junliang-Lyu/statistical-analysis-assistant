# Local bilingual UI plan

Approved direction: English presentation with Chinese assistance, built-in test cases, browser interface. Reuse existing graph; no new dependencies or statistical behavior changes.

Architecture: ui_server.py binds only localhost, serves fixed UI assets and a same-origin JSON endpoint. Each browser receives an isolated in-memory session. Analysis and clarification run the existing graph. Uploaded CSV is parsed server-side and not saved. API key stays server-side. Request sizes are capped and cross-origin mutations rejected.

Implementation and verification:
- Add failing tests for case loading, interruption/resume, follow-up recomputation and session isolation.
- Implement the session adapter and localhost HTTP server with standard-library modules.
- Add English-first HTML/CSS/JS with Chinese toggle, sample cases, CSV preview, clarification controls, result cards and actual node trace.
- Run all tests and verify the HTTP/browser workflow using offline mode; keep live mode explicitly selectable.
- Document one-command startup and limitations. No deployment or publication.

# Personal-site Lab demo: proposed integration

## Verified context

- Target site: `C:/Users/ASUS/Desktop/学习/codex/self_web`.
- Existing site exports static Next.js pages from bilingual MDX content.
- Lab articles use the existing collection layout and optional GitHub/demo links.
- The statistical assistant runs a Python local server and keeps the DeepSeek key server-side.
- The existing site has unrelated uncommitted Investment Lab content changes; preserve them.
- The statistical-assistant GitHub repository is now public.

## Option A — interactive replay (recommended initial release)

Add bilingual Lab content and a dedicated, English-first replay of recorded real DeepSeek runs. Visitors select Welch, Pearson, chi-square or simple regression; inspect the synthetic CSV; view the plan, checks, numerical results, interpretation and execution trail. Explanation reuse and date-filter recomputation are separate recorded steps. Include an explicit recorded-run label, a genuine checker-failure example, source links and the compiled graph.

No visitor-provided data is analyzed and no model request is made. Do not call this a live assistant. CSV downloads and notebook links remain available. Keep PPT/writeup out of Lab and reserve Writing placement for a separate request.

Reuse existing site styles and content schema. Add no dependencies, no backend and no changes to unrelated Lab content. Validate the existing site build, language routes, replay controls, downloads and mobile layout before publishing.

## Option B — live assistant

Deploy the existing Python service separately with HTTPS, a server-side key, explicit upload/privacy behavior, request-size constraints and a model-call budget/rate limit. Link or embed it from a bilingual Lab article. The static website alone cannot host the Python service. Hosting target, operating budget and public access policy must be chosen before deployment; do not expose the current local server as a public service unchanged.

## Pending decision

User choice between recorded replay and a separately hosted live assistant. No website implementation or deployment has been performed yet.

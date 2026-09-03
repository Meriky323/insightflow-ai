# InsightFlow 2.0 — Functional QA

Automated backend tests: **13 passed**.

Verified contracts:
- `/api/health` returns 2.0.0 + bilingual/community/evidence-thread feature flags.
- Portfolio demo loads and keeps traceable evidence.
- Market comparison guardrail blocks unsupported US/AU consumer claims.
- Public mode hides non-demo research and blocks paid/live paths.
- Public Ask InsightFlow stays local and grounded.
- English/Chinese Ask surfaces are supported.
- PDF and CSV exports work.
- Insta360 X6 case surface exists.
- Railway auto-public-mode behavior remains intact.
- New `community` source is accepted and adds one SerpAPI call.
- Google Discussions/Forums response parsing labels community evidence GLOBAL and preserves source URL/snippet.
- Motion system and Evidence Drawer surfaces exist.

Static checks:
- Python compile: PASS
- app.js syntax: PASS
- motion.js syntax: PASS
- No external React/runtime dependency added.
- Mobile root viewport horizontal overflow is clipped/contained.

Research limitations are documented in `RESEARCH_CAPABILITY_AUDIT.md`.

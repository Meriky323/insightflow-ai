# InsightFlow AI v1.4 — Final self-check

Checked on **2026-09-01**.

## Automated checks

- Python compile: **PASS** — `python -m compileall -q app`
- JavaScript syntax: **PASS** — `node --check static/app.js`
- Pytest: **PASS — 6/6**
- FastAPI root / case-study routes: **PASS**
- Recruiter demo seeding: **PASS**
- Demo evidence: **18 traceable consumer rows**
- Product benchmark: **8 product signals**
- Historical topic delta: **PASS**
- Market-comparison guardrail: **PASS** — unsupported US/AU consumer preference comparison is blocked
- Public live-research protection: **PASS**
- Public connector diagnostics protection: **PASS**
- Public LLM-quota protection: **PASS**
- PDF export: **PASS**
- Evidence CSV export: **PASS**
- CSV formula-injection protection: **PASS**
- Test isolation: **PASS** — tests use a temporary data directory and no longer mutate packaged runtime data

## PDF QA

Final Executive Brief was rendered at 180 DPI and visually inspected page by page.

- Pages: **3**
- Openable: **PASS**
- Clipped text: **none observed**
- Overlap: **none observed**
- Broken glyphs / black boxes: **none observed**
- Page 2 contains only opportunity cards with real Product / GTM / Next Validation decisions attached

## Evidence-source QA

Official product/support URLs for Anker US/AU, UGREEN US/AU, Baseus and Belkin US/AU were re-checked on 2026-09-01. The final snapshot removed an unverified Amazon AU category row and replaced it with a verified Belkin AU official product signal. Anker US price is intentionally omitted because the current sold-out page does not expose a stable product price.

The ESR customer-review evidence remains linked to the exact product URL used to source the review snapshot. The page can redirect by locale, so the demo treats it as GLOBAL evidence rather than assigning a market.

## Visual QA

Desktop recruiter landing, executive workspace, case-study and 390px mobile layouts were visually reviewed during the v1.4 pass. The final data-source cleanup does not change frontend structure or CSS.

## Intentionally not tested with user credentials

- Live SerpApi request — not used to protect quota
- Local Sub2API request — the user's `127.0.0.1:8080` gateway is not reachable from this runtime

Use **API Settings → Test connections & quota** on the user's machine for these two checks.

## Known boundaries — deliberate

1. Flagship demo is a compact public-evidence case, not a population-representative study.
2. Most consumer voice is GLOBAL; country preference claims stay blocked.
3. No fake Google Trends line is generated in the saved demo.
4. Product prices/review counts are snapshots and can change after collection.
5. Opportunity scores prioritize validation; they are not TAM, sales forecasts or proof of PMF.
6. TikTok / Instagram are not added merely to increase connector count; CSV/JSON import remains the compliant bridge for licensed/first-party exports.

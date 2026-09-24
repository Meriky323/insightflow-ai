# Cloudflare public deployment

The public recruiter site uses Cloudflare Pages Advanced Mode. Python/FastAPI remains the local analyst application. No React migration, paid live connector, database binding, or external LLM is needed by the public site.

## Rebuild

```sh
python -m pip install -r requirements.txt
python scripts/build_public.py
node --test tests/worker.test.mjs
```

Upload `cloudflare/insightflow-pages.zip` to Cloudflare Pages Direct Upload. The archive includes `_worker.js`, `_routes.json`, the frontend, and pre-generated PDF/CSV/DOCX downloads. Only `/api/*` invokes the Worker. Keep the whole archive together; uploading the HTML alone will not produce a working app.

The build deliberately creates a fresh temporary database, disables dotenv, clears live credentials, and seeds only the repository's portfolio snapshots. It never exports the analyst's research database. All public mutations and connection diagnostics return 403. Unknown research IDs return 404. Ask uses deterministic retrieval, not an LLM, and returns insufficient evidence when no supported answer exists.

The alternate Workers configuration in `wrangler.jsonc` uses the same generated handler and assets. `wrangler deploy` requires normal Cloudflare authorization. Dashboard Direct Upload avoids local CLI authorization.

## Local analyst

Keep using `START_WINDOWS.bat` or `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Set `PUBLIC_DEPLOYMENT=0` locally. Configure connectors through local Settings. Do not expose this unauthenticated local analyst service to the Internet.

## Evidence boundaries

- Portfolio consumer rows are manually curated source paraphrases, not verbatim reviews, unique respondents, or a representative survey.
- Changes are descriptive shares of selected rows, not population trends or causal explanations.
- Brand mentions are discovery links, not proof that a sentiment targets every mentioned brand or model. Negative share is calculated only for direct product-linked rows.
- GLOBAL evidence remains GLOBAL; US/AU preference comparison is blocked for this snapshot.
- The X6 page is a separate editorial application case, not a second fully ingested live study.
- Real SerpAPI collection and Sub2API generation require separate live verification. Offline tests do not establish these credentials or endpoints work.

References: [Pages Direct Upload](https://developers.cloudflare.com/pages/get-started/direct-upload/), [Advanced Mode](https://developers.cloudflare.com/pages/functions/advanced-mode/).

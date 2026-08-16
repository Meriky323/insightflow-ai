# Railway deployment

1. Deploy this repository as a Railway service.
2. Add environment variables:
   - `SERPAPI_API_KEY` = your secret key
   - `PUBLIC_DEPLOYMENT` = `1`
   - optional: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`
3. Attach one Volume to the service at `/data`.
4. Generate a Railway domain and verify `/api/health` returns `ok: true`.
5. Add the custom domain `insightflow.meriky.online` and apply the CNAME/TXT records Railway provides.

Secrets must never be committed to GitHub.

# InsightFlow AI

## Live recruiter website

**https://insightflow-ai.up.railway.app/**

This Railway URL is the resume-facing entry point. On Railway, InsightFlow automatically switches to recruiter-safe public mode, so visitors can open the flagship case and target-company case without API keys while live connector settings and paid quota remain protected.


**Global Consumer & GTM Intelligence — portfolio-grade prototype**

InsightFlow turns fragmented overseas consumer signals into an auditable decision workflow:

**Evidence → Consumer Signal → Competitive Context → Opportunity Hypothesis → Product / GTM Action → Next Validation**

The project is intentionally designed around the part of AI research that matters in real business work: **what the evidence supports, what it does not support, and what a team should do next.**

## Why this project exists

Overseas market research often lives across product pages, retail reviews, community discussions, videos and trend tools. A generic chatbot can summarize those inputs, but it can also produce confident conclusions from weak or incomparable evidence.

InsightFlow adds a research layer before the model:

- source / market / date provenance
- multi-label consumer topic extraction
- driver / barrier / scenario / purchase-impact structuring
- competitor evidence linkage
- historical topic delta
- cross-market comparability checks
- evidence confidence
- explicit Product Action / GTM Action / Next Validation

## Preview

![InsightFlow recruiter landing](docs/assets/recruiter-landing.png)

![InsightFlow executive workspace](docs/assets/executive-workspace.png)

The repository also includes a narrative [Case Study](static/case-study.html), a sample [Executive Brief PDF](examples/flagship_case/InsightFlow_Executive_Brief.pdf), and a sample [Evidence CSV](examples/flagship_case/InsightFlow_Evidence.csv).

## Recruiter-facing flagship demo

The repository ships with a **saved, traceable portfolio snapshot** for:

**10,000mAh Magnetic Power Bank · US / AU**

The public demo:

- needs **no API key**
- consumes **no SerpApi or LLM quota**
- uses concise paraphrases of linked public consumer sources
- includes two historical evidence periods and eight product signals
- deliberately blocks US/AU consumer-preference claims because equivalent country-level consumer-voice coverage is missing

Open locally and visit:

```text
http://127.0.0.1:8000/
```

Direct flagship case:

```text
http://127.0.0.1:8000/?demo=1
```

Case study:

```text
http://127.0.0.1:8000/case-study.html
```

## Product surfaces

- **Executive Snapshot** — decision memo, top signals, confidence and evidence chain
- **Trend Radar** — within-market Google Trends momentum + historical topic-share delta
- **Consumer Voice** — searchable traceable evidence with topics / drivers / barriers / scenarios
- **Competitive Benchmark** — product signals plus conservatively linked consumer evidence
- **Market Comparison** — only compares consumer markets when the same source basis covers all requested markets
- **Opportunity Board** — evidence-backed priority hypotheses with Product Action / GTM Action / Next Validation
- **Ask InsightFlow** — OpenAI-compatible grounded analysis locally; deterministic evidence-grounded answers in public recruiter mode
- **Executive Brief** — PDF decision brief + Evidence CSV

## Data architecture

```text
Live connectors                         Imported evidence
Google Shopping                        Reddit / TikTok exports
Walmart + Reviews                      Social listening exports
YouTube + Comments                     Survey / CRM / support CSV
Google Trends                          Other CSV / JSON
       \                                   /
        └────────── Evidence Layer ────────┘
                       ↓
          Normalize · dedupe · time scope
                       ↓
     AI extraction / explicit local fallback
                       ↓
 Topic · Driver · Barrier · Scenario · Impact
                       ↓
 Historical / market / competitor analysis
                       ↓
 Evidence confidence + decision guardrails
                       ↓
      Product Action · GTM Action · Validation
```

## AI engine

InsightFlow accepts any **OpenAI-compatible** gateway.

For local Sub2API, the common configuration is:

```env
LLM_BASE_URL=http://127.0.0.1:8080/v1
LLM_MODEL=<model returned by /v1/models>
LLM_API_KEY=<your local Sub2API API key>
```

The current LLM layer is used for:

1. batch review/comment structuring;
2. topic-label normalization;
3. grounded evidence Q&A;
4. Product / GTM decision drafting.

If the LLM is unavailable, the system does **not** fabricate rows. It falls back to visibly labeled local analysis.

## SerpApi usage

One SerpApi key powers multiple SerpApi engines used by the project. Research depth hides crawler-page controls from the product UX:

- **Quick** — lean evidence / lowest call count
- **Standard** — recommended
- **Deep** — wider sample

Repeated identical SerpApi requests use a local cache when possible.

## Run on Windows

Double-click:

```text
START_WINDOWS.bat
```

Or:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Run on macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

## Public portfolio deployment

Recommended environment:

```env
PUBLIC_DEPLOYMENT=1
ALLOW_PUBLIC_LIVE_RESEARCH=0
```

This keeps the recruiter demo interactive while disabling:

- live API-consuming research
- evidence uploads
- API settings changes
- connector diagnostics
- paid LLM consumption
- access to non-portfolio research IDs

A public reviewer can still explore the saved case, evidence, benchmark, opportunity logic, grounded local Q&A and exports.

## Research integrity rules

1. **No synthetic-review fallback.**
2. **Review count is never presented as unit sales.**
3. **GLOBAL YouTube / community evidence is not assigned to a country.**
4. **Cross-market consumer comparisons require equivalent source coverage.**
5. **Google Trends 0–100 is treated as a normalized within-market index, not absolute demand.**
6. **Opportunity priority is a validation heuristic, not TAM / revenue / PMF proof.**
7. **AI may structure and reason over supplied evidence; it does not fill missing market evidence.**

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

The test suite checks the recruiter demo, evidence guardrails, public-mode access restrictions and export behavior.

## Repository map

```text
app/
  collectors/serpapi.py   live data connector
  importers.py            CSV / JSON evidence import
  analysis.py             confidence / benchmark / market / trend logic
  llm.py                  OpenAI-compatible AI layer
  demo.py                 traceable recruiter snapshot
  reports.py              PDF / CSV export
  main.py                 FastAPI application
static/
  index.html               portfolio landing + research workspace
  app.js                   workspace interaction
  styles.css               recruiter-facing UI
  case-study.html          flagship narrative case study
tests/
  test_portfolio_demo.py   regression / safety tests
```

## Positioning

This is **not** a replacement for enterprise platforms such as Brandwatch, Sprinklr or Meltwater. It is a focused prototype that demonstrates how a small AI-native workflow can connect overseas consumer evidence to product and GTM decisions while preserving research boundaries.

## Target-company application case · Insta360 X6

To prove the workflow generalizes beyond one product category, v1.5 includes a second evidence-backed case focused on the 2026 Insta360 X6 launch.

**Business question:** what should X6 launch marketing prove beyond the spec sheet, and which workflow risks deserve immediate validation?

The case highlights a useful global-business tension: users may value Insta360's mature 360 editing ecosystem, while the same workflow becomes a churn risk when export metadata, app stability, long-form editing or transfer friction fails. The resulting recommendation is to prove **time-to-share / workflow advantage**, not compete on imaging specifications alone.

Open locally: `http://127.0.0.1:8000/case-insta360-x6.html`

See `docs/TARGET_CASE_INSTA360_X6.md` and `docs/APPLICATION_PLAYBOOK.md`.

<sub>🌐 <a href="README.md">中文</a> · <b>English</b></sub>

<div align="center">

# InsightFlow AI

### Turn fragmented market signals into traceable consumer insight and action

**Evidence-first Consumer & GTM Intelligence**

Not “AI summarizes reviews”, but a reusable workflow from **evidence → insight → product / GTM action → next validation**.

</div>

---

## Why I built it

When researching an overseas product, category or campaign, the problem is rarely a lack of information. The real problems are:

1. **Fragmented signals** across products, reviews, videos, search trends, communities and competitors;
2. **Repeated manual research** every time the category changes;
3. **Shallow insight** that stops at “users like / dislike this” instead of explaining purchase drivers and barriers;
4. **Weak evidence boundaries** when an LLM can produce a polished answer without showing what is fact versus hypothesis.

InsightFlow starts with evidence, structures it, and only then produces actions.

---

## What it solves

### 1. Consumer insight

Consumer evidence is structured into:

- pain points
- purchase drivers
- barriers
- usage scenarios
- explicit purchase impact
- competitor mentions and alternatives

The key questions are:

> **Why do people choose this product? Why do they reject it? Which needs actually influence purchase?**

### 2. Market & competitor framing

Product facts, positioning and consumer evidence are analyzed together, instead of relying only on competitor marketing claims.

Outputs include:

- common market claims
- competitive sameness
- repeated consumer problems
- differentiation hypotheses worth validating

### 3. Insight → action

InsightFlow does not stop at a dashboard. It produces:

- **Product Action** — what product / supply should do next
- **GTM Action** — what messaging, content, localization or launch strategy should do next
- **Next Validation** — what still needs evidence before a hypothesis becomes a decision

---

## Core workflow

```text
Real market signals
Google Shopping · Walmart · YouTube · Google Trends
Public community discovery · CSV / JSON imports
        ↓
Evidence Layer
source · date · original text · market boundary
        ↓
Structured analysis
pain point · driver · barrier · scenario · purchase impact
        ↓
Market / Consumer / Competitor insight
        ↓
Opportunity prioritization
        ↓
Product Action · GTM Action · Next Validation
```

---

## Core product surfaces

| Surface | Question it answers |
|---|---|
| **Executive Snapshot** | What is the recommendation, confidence and decision boundary? |
| **Trend Radar** | Which topics / search signals are moving? |
| **Consumer Voice** | What are consumers actually saying, and where is the evidence? |
| **Competitors** | What exists in the market, and how do consumers respond to it? |
| **Opportunity Board** | What should be validated first, and what should Product / GTM do next? |
| **Ask InsightFlow** | What can we infer from the evidence already collected? |

---

## Portfolio cases

### Magnetic Power Bank · US / AU

A general consumer-electronics case focused on portability, thermal stability, device fit, magnetic experience and purchase trade-offs.

The product deliberately blocks unreliable cross-market preference claims when the US and AU consumer evidence is not genuinely comparable.

### Insta360 X6 · Launch Intelligence

A target-company case exploring whether the creator workflow — **record → reframe → export → share** — can become a stronger moat as hardware specifications converge.

---

## Data sources

### Live / structured collection

- Google Shopping
- Walmart Reviews
- YouTube videos / comments
- Google Trends
- public community signals discovered via Google Discussions & Forums

### Import layer

CSV / JSON can ingest compliant exports from:

- TikTok / Instagram
- Brandwatch / Sprinklr-like social listening
- surveys
- CRM / support logs
- other review or research datasets

---

## Research integrity

InsightFlow intentionally keeps decision boundaries visible:

- no synthetic-review fallback
- review count is never treated as unit sales
- GLOBAL evidence is never reassigned to a country
- Google Trends indices are not treated as market size
- opportunity priority means **what to validate first**, not TAM / sales / PMF
- cross-market preference comparisons are blocked unless equivalent evidence exists

---

## Two operating modes

### Public Recruiter Mode

Designed for portfolio viewing:

- no API keys exposed
- no owner-paid model / search quota consumed
- saved real-case evidence
- full workflow and evidence traceability visible

### Local Analyst Mode

Can connect to:

- SerpAPI
- an OpenAI-compatible LLM / Sub2API endpoint
- CSV / JSON evidence imports

---

## Local setup

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Tests:

```bash
python -m pytest -q
node --check static/app.js
```

---

## What this project is meant to demonstrate

InsightFlow is not primarily an AI feature showcase. It is an attempt to productize a real operating problem:

> **How can fragmented, repetitive and intuition-heavy consumer research become a workflow with evidence, boundaries and clear next actions?**

For recruiters / hiring managers, the most useful things to inspect are:

1. how the business problem is defined;
2. how consumer voice becomes structured judgment;
3. how evidence is separated from inference;
4. how insight connects to Product / GTM action.

---

## Disclaimer

InsightFlow is intended for exploratory consumer intelligence, competitor framing, concept prioritization and marketing hypotheses. It is not a representative survey, TAM estimate, sales forecast or proof of product-market fit.

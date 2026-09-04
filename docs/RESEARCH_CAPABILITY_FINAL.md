# InsightFlow 2.1 — Final Research Capability

## What “real research” means here

InsightFlow does not treat “API connected” as equivalent to “good research.” The final workflow separates **coverage**, **analysis**, and **decision confidence**.

### Structured live collection
- Google Shopping: market-specific product/price/rating/review-count signals.
- Walmart US: product results + real review text.
- YouTube: review-video discovery + public comments; comment geography stays GLOBAL.
- Google Trends: within-market interest-over-time direction; never interpreted as absolute market size.
- Community discovery: Reddit/forum discussion and answer snippets discovered via Google Discussions & Forums. Standard/Deep research now uses a small objective-aware query plan to cover broad, problem, and comparison intent while keeping geography GLOBAL.

### External evidence import
CSV/JSON remains the stable ingestion layer for compliant exports from TikTok, Instagram, Brandwatch/Sprinklr-like social listening, surveys, CRM/support logs, Amazon/review datasets, or manually assembled research evidence.

### AI analysis
With a configured OpenAI-compatible LLM/Sub2API endpoint, evidence is batch-structured into sentiment, multi-label topics, drivers, barriers, usage scenarios, explicit purchase impact, and competitor mentions. Topic labels are normalized and the strongest repeated signals become bounded Product Action / GTM Action / Next Validation hypotheses.

### Why this can produce useful findings
The system gets strongest when the evidence triangle is complete:
1. **Market/commerce facts** — what exists and how it is positioned.
2. **Consumer voice** — what people praise, reject, compare, and struggle with.
3. **Demand/time signal** — whether the topic/search interest is stable, rising, or cooling.

The output is suitable for exploratory consumer intelligence, competitor framing, concept prioritization, messaging hypotheses, and deciding what to validate next. It is not a representative survey, TAM estimate, or sales forecast.

## Practical ceiling

The free SerpAPI tier is enough for focused category work and recruiter cases, not enterprise-scale listening. Standard/Deep can now spend a few additional searches on community intent coverage; the UI should surface the estimated calls before running.

## Reliability design

- Each connector fails independently; a partial source does not destroy the whole study.
- Unknown dates remain visibly unknown.
- GLOBAL evidence is never reassigned to a country.
- Cross-market voice comparison is blocked unless equivalent voice sources exist across markets.
- Public recruiter mode never uses the owner's paid/live API quota.

# InsightFlow 2.0 — Research Capability Audit

## What is genuinely live

In local Analyst Mode, a configured SerpAPI key can collect:
- Google Shopping: product, price, seller, rating/review-count signals by market.
- Walmart: US product results plus real review text.
- YouTube: product-review discovery plus public comment text. Comment geography remains GLOBAL.
- Google Trends: within-market interest-over-time direction. Raw index levels are not used as cross-country market-size estimates.
- Community Search: real public Reddit/forum discussion titles and answer snippets discovered through Google Discussions & Forums. Geography remains GLOBAL because author country is not reliably known.

A CSV/JSON import path accepts additional compliant evidence such as TikTok/Instagram exports, social-listening exports, surveys, support logs, or other review datasets.

## What the AI actually does

When an OpenAI-compatible LLM / Sub2API endpoint is configured, the system batch-extracts:
- sentiment
- multi-label topics
- positive drivers
- barriers
- usage scenarios
- explicit purchase impact
- explicit competitor mentions

It then normalizes topic labels and creates bounded Product Action / GTM Action / Next Validation recommendations. If the LLM is unavailable, a clearly labelled local fallback keeps the research usable but less semantically rich.

Ask InsightFlow now retrieves evidence relevant to the user's question before giving the LLM context. It does not simply send the first N rows.

## Research quality tiers

- **Thin**: useful for exploration only. Usually too few rows or too little source diversity.
- **Directional**: enough independent evidence to prioritize what to validate next, but not to generalize to the whole market.
- **Strong**: larger multi-source evidence base with time-window coverage. Still not a statistically representative survey unless the underlying data source is representative.

The UI exposes this as a research-readiness heuristic, not a statistical confidence interval.

## Important guardrails

- Review count is not converted to unit sales.
- Google Trends index is not treated as market size.
- GLOBAL community / YouTube evidence is never reassigned to US, AU, UK or CA.
- Cross-market consumer comparison is blocked unless the same consumer-voice source exists across all requested markets.
- Opportunity priority is not TAM, whitespace proof, or product-market fit.
- Public recruiter mode never spends the owner's SerpAPI or LLM quota.

## Practical capability ceiling

With only the free SerpAPI tier, InsightFlow is best used for focused category research and portfolio cases, not full-enterprise social listening. A Standard US+AU run is roughly 14 SerpAPI calls; Deep is roughly 20. The strongest workflow is:

1. run structured live collection;
2. import additional social/listening evidence if available;
3. use AI topic extraction;
4. inspect Evidence Threads;
5. convert the strongest repeated signals into validation hypotheses;
6. rerun the same scope later to unlock real historical deltas.

This is a credible small-scale Consumer Intelligence / GTM research system, not a replacement for Brandwatch/Sprinklr-scale data coverage.

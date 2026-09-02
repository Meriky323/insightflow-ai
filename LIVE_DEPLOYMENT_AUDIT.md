# InsightFlow v1.5 live-deployment audit

## What was checked before deployment

The deployment package contains the complete recruiter-facing v1.5 product, not a separate offline showcase.

Critical website surfaces present in the build:

- Recruiter landing page
- Executive Snapshot
- Trend Radar
- Consumer Voice & traceable evidence
- Competitive Benchmark
- Market Comparison guardrail
- Opportunity Board
- Ask InsightFlow
- Method & guardrails
- Recent Research / historical comparison
- CSV / JSON evidence import in local analyst mode
- Research Depth abstraction
- Evidence Confidence and source coverage
- Product Action / GTM Action / Next Validation
- Magnetic Power Bank flagship saved case
- Insta360 X6 target-company case
- Case Study page
- Executive Brief + Evidence CSV export
- Railway recruiter-safe public mode

## Public-mode protections

Railway is detected automatically through Railway system environment variables. In recruiter mode:

- live API-consuming research is blocked by default;
- connector settings and diagnostics are hidden;
- server-side SerpApi / LLM configuration is not disclosed;
- paid LLM quota is not consumed by the public demo;
- evidence upload is disabled;
- non-portfolio research IDs are hidden.

## Local verification completed

- Python compile: PASS
- JavaScript syntax: PASS
- pytest: 8/8 PASS
- Railway-mode simulation: PASS
- landing / case-study / Insta360 X6 routes: PASS
- recruiter snapshot: 18 current consumer evidence rows + 8 product signals
- historical delta: PASS
- cross-market guardrail: PASS
- all local HTML links: PASS

## Live verification requirement

`VERIFY_LIVE_WEBSITE.ps1` checks the deployed Railway URL for:

1. API version `1.5.0`;
2. recruiter-safe public config;
3. all seven core product surfaces on the landing page;
4. case-study route;
5. Insta360 X6 case route;
6. saved flagship demo loading without external API usage;
7. 18+ consumer evidence rows;
8. 8+ product signals;
9. historical delta;
10. market comparison guardrail.

Do not treat deployment as complete until this verifier prints `PASS`.

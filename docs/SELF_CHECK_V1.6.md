# InsightFlow v1.6 Final Self Check

## Product scope
- Recruiter-first landing page: PASS
- Executive Snapshot: PASS
- Trend Radar: PASS
- Consumer Voice: PASS
- Competitor Benchmark: PASS
- Opportunity Board: PASS
- Ask InsightFlow: PASS
- Chinese / English language switch: PASS
- Flagship case language switch: PASS
- Insta360 X6 case language switch: PASS

## Research integrity
- No synthetic-review fallback: PASS
- Market-comparison guardrail: PASS
- Review-count != sales boundary: PASS
- Google Trends normalization note: PASS
- Opportunity score positioned as validation priority: PASS
- Public mode hides connector status: PASS
- Public mode blocks live API-consuming research: PASS

## Engineering checks
- Python compile: PASS
- JavaScript syntax: PASS
- pytest: 10 / 10 PASS
- HTML duplicate IDs: none
- Desktop landing visual QA: PASS
- Mobile width: 390px viewport / 390px document width
- Workspace layout static visual QA: PASS

## Deployment acceptance
`VERIFY_LIVE_WEBSITE.ps1` requires:
- `/api/health` version = 1.6.0
- `bilingual_ui = true`
- landing contains core product surfaces
- bilingual flagship + X6 pages
- >=18 demo evidence rows
- >=8 product signals
- historical delta present
- US/AU market guardrail active
- Chinese + English public Ask checks
- public mode hides SerpAPI / LLM and disables public live research

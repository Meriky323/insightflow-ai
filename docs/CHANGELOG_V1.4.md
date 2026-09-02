# InsightFlow v1.4 — Recruiter-ready final pass

## Product positioning
- Rebuilt the entry experience into a portfolio landing page rather than auto-dropping reviewers into an API workspace.
- Added a single flagship-case narrative centered on a business question and decision boundary.
- Added a clear “how teams would use this” layer for Consumer Insights, Product, GTM/Marketing and Growth/User Ops.

## Executive UX
- Replaced KPI-first overview with a **Decision Memo**.
- Added explicit Product Action / GTM Action / Next Validation at the top of the research.
- Added Evidence → Signal → Decision → Guardrail chain.
- Added methodology modal and suggested grounded questions.

## Data integrity
- Demo schema versioning prevents old seeded snapshots from silently persisting after upgrades.
- Unknown customer-review dates are now marked unknown rather than assigning the snapshot date as if it were the review date.
- Uncertain marketplace price/rating metrics are omitted instead of presented as facts.
- “Purchase impact” scoring now counts explicit decision-changing outcomes rather than every generic purchase criterion.
- Public mode now prevents direct-ID access to non-portfolio research, not merely hiding it from history.

## Public demo safety
- Public demo does not consume SerpApi quota.
- Public demo does not consume private LLM quota.
- Uploads, settings and connector diagnostics remain disabled.
- Recruiters can still use deterministic evidence-grounded Ask InsightFlow answers.

## Portfolio delivery
- Added complete README, Windows/macOS/Linux start scripts, Railway configuration and gitignore.
- Added regression tests for recruiter demo, public access, guardrails, Q&A and exports.
- Reworked PDF Executive Brief into a decision-oriented multi-page report.
- Rebuilt Case Study page around Problem → Architecture → Findings → Decision → Guardrail → Sources.

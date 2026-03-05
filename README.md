# 45-iac-delivery-incident

Portfolio-grade, runnable guardrails that target three real-world DevOps/SRE pain points:

1) **Infrastructure drift & fragile automation** (IaC changes are inconsistent, hard to review, easy to break)  
2) **Delivery friction** (slow/flaky CI/CD and risky releases → rollbacks)  
3) **Reliability under on-call pressure** (reduce incident frequency, shorten MTTR)

## What breaks in real orgs (and why it hurts)
- Manual changes create drift; environments diverge; automation becomes brittle.
- Releases ship without consistent tests/plan/review gates; failures reach production.
- Incidents repeat because learnings don’t get operationalized into guardrails and runbooks.

This repo provides a deterministic demo CLI that reads realistic sample inputs and generates a report with risks, recommended guardrails, and linked runbooks.

## Architecture Overview
**Inputs → Checks → Outputs → Runbooks**

- Inputs: JSON files under `examples/`
- Checks: `portfolio_proof validate` enforces key controls
- Outputs: `artifacts/report.md` (gitignored)
- Runbooks: `docs/runbooks/` operational steps tied to findings

Details: `docs/architecture.md`

## Quick Start
```bash
make setup
make demo
```

## Demo
Generate a report and review how it maps to the pain points:
```bash
make demo
sed -n '1,200p' artifacts/report.md
```

The report includes:
- Drift findings (desired vs current state) and guardrail failures
- Delivery safety findings (required gates, release approvals, traceability)
- Reliability findings (MTTR signals, recurrence, missing postmortems/runbooks)

## Security
- No secrets are stored in this repo; example inputs are sanitized.
- `artifacts/` is gitignored; reports are local build outputs.
- See `docs/security.md` for controls and out-of-scope items.

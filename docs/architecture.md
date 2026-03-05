# Architecture

## Goal
Provide a **local, deterministic** “portfolio proof” that models how to reduce risk across:
1) Infrastructure drift and fragile automation  
2) Delivery friction and risky releases  
3) Reliability under real on-call pressure

## Data Flow
**Inputs → Checks → Outputs → Runbooks**

- Inputs: versioned JSON files under `examples/`
  - `desired_state.json`: intended infrastructure baseline (reviewable / code-reviewed)
  - `current_state.json`: observed state snapshot (what’s actually running)
  - `pipeline.json`: CI/CD + release controls signals
  - `incident_log.json`: incident history signals (MTTR, recurrence, follow-ups)
- Checks: standard-library Python validators
  - Drift + guardrail enforcement on infra definitions
  - Delivery controls for safe, repeatable releases
  - Reliability signals (recurrence, MTTR, missing postmortems/runbooks)
- Outputs: `artifacts/report.md`
  - Human-readable risk report
  - Validation summary suitable for CI gates
  - Pointers to runbooks to operationalize fixes

## Components
- `src/portfolio_proof/`:
  - `cli.py`: command entrypoints (`report`, `validate`)
  - `checks.py`: control checks across the 3 pain points
  - `report.py`: Markdown report generation
  - `io.py`: input loading and schema/shape validation
- `scripts/portfolio_proof`: convenience wrapper (still uses stdlib only)
- `docs/runbooks/`: operational playbooks linked from the report

## Threat Model Notes (high-level)
Primary risks this repo models and mitigates:
- **Misconfiguration exposure**: public resources, missing ownership tags, unsafe defaults
- **Change-risk amplification**: “apply” without plan/review gates; missing tests; no approvals
- **Incident-repeat loops**: repeated failures without postmortems, follow-ups, or runbook usage

What’s intentionally out-of-scope:
- Live cloud enumeration, IAM policy evaluation, container image scanning
- Secrets scanning beyond explicit guardrails (no tokens/keys in repo)

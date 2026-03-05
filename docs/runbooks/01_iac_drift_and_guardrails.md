# Runbook: IaC Drift & Guardrails

## When to Use
- Drift detected between intended (`desired_state`) and observed (`current_state`) state.
- Repeated breakage from manual changes or inconsistent environments.

## Goal
Make infrastructure changes **reviewable, repeatable, and boring**.

## Procedure
1) **Confirm drift scope**
   - Generate report: `make demo`
   - Review the “IaC Drift & Guardrails” section in `artifacts/report.md`.
2) **Stop the bleeding**
   - Freeze manual changes for the impacted resource class.
   - Require all changes via PR and tracked `change_id`.
3) **Normalize ownership + environment tags**
   - Enforce: `owner`, `environment`, `change_id` for every resource.
4) **Introduce a safe plan/apply workflow**
   - Require “plan” output for review; separate apply with approvals.
5) **Add regression controls**
   - Run `make lint` + `make test` in CI.
   - Gate merges on `portfolio_proof validate` (or equivalent guardrails).

## Success Criteria
- Drift findings trend to zero.
- Every change has an owner and a change identifier.
- Plan/apply controls are consistently enforced across environments.

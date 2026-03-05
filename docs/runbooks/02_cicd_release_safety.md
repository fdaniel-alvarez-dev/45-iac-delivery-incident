# Runbook: CI/CD Delivery Friction & Release Safety

## When to Use
- Builds are slow/flaky, releases require heroics, or rollbacks are common.
- Production changes bypass tests or plan/approval gates.

## Goal
Increase deployment throughput **without increasing incident rate**.

## Procedure
1) **Baseline current delivery signals**
   - Generate report: `make demo`
   - Review “Delivery Controls” findings in `artifacts/report.md`.
2) **Make failures actionable**
   - Ensure lint/tests run early and fail fast.
   - Separate “plan” from “apply” to reduce blast radius.
3) **Enforce release gates**
   - Require tests + plan + policy checks prior to deployment.
   - Require an explicit approval signal for production deploys.
4) **Reduce flakiness**
   - Quarantine flaky tests; track failure reasons; set an SLO for pipeline reliability.
5) **Operationalize rollback**
   - Define rollback criteria and steps; rehearse; ensure artifact traceability.

## Success Criteria
- Flaky rate decreases; pipeline success rate increases.
- Releases are gated and auditable; fewer emergency rollbacks.

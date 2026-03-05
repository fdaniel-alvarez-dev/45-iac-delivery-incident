# Runbook: Incident Response & MTTR Reduction

## When to Use
- Repeat incidents with the same root causes.
- High MTTR, missing postmortems, or inconsistent runbook usage.

## Goal
Reduce incident frequency and make failures boring by tightening feedback loops.

## Procedure
1) **Triage and stabilize**
   - Confirm severity, scope, and customer impact.
   - Apply immediate mitigations; document timestamps and actions.
2) **Use the right runbook**
   - Select a runbook per service/component; record `runbook_used`.
3) **Postmortem discipline**
   - For sev-1/sev-2: write postmortem with clear “what/why/learned”.
   - Track follow-ups with owners and due dates.
4) **Prevent recurrence**
   - Convert fixes into guardrails (pipeline gates, config checks, monitoring).
   - Add automated regression tests where feasible.
5) **Measure**
   - Track MTTR, recurrence rate, and percentage of incidents with postmortems.

## Success Criteria
- MTTR trends down.
- Recurrence trends down.
- Postmortem + follow-up closure rate trends up.

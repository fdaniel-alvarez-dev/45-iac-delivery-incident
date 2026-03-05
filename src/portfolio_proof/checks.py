from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .io import InfraState, IncidentLog, Inputs, Pipeline, Resource, iter_resource_map


@dataclass(frozen=True)
class Finding:
    area: str
    control: str
    severity: str  # "ERROR" | "WARN" | "INFO"
    message: str
    evidence: dict[str, Any] | None = None


def _iso_to_dt(value: str) -> datetime:
    # Expect UTC "Z". Keep strict: deterministic parsing.
    if not value.endswith("Z"):
        raise ValueError(f"Timestamp must end with 'Z': {value}")
    return datetime.fromisoformat(value.removesuffix("Z")).replace(tzinfo=timezone.utc)


def _mttr_minutes(started_at: str, resolved_at: str) -> int:
    start = _iso_to_dt(started_at)
    end = _iso_to_dt(resolved_at)
    delta = end - start
    return max(0, int(delta.total_seconds() // 60))


def _resource_requires_encryption(resource: Resource) -> bool:
    return resource.type in {"bucket", "database"}


def _resource_requires_versioning(resource: Resource) -> bool:
    return resource.type in {"bucket"}


def check_iac_drift(desired: InfraState, current: InfraState) -> list[Finding]:
    findings: list[Finding] = []
    desired_map = iter_resource_map(desired.resources)
    current_map = iter_resource_map(current.resources)

    for rid, d in desired_map.items():
        c = current_map.get(rid)
        if c is None:
            findings.append(
                Finding(
                    area="iac",
                    control="resource-present",
                    severity="ERROR",
                    message=f"Resource missing in current state: {rid}",
                    evidence={"resource_id": rid, "type": d.type},
                )
            )
            continue

        for key in ("owner", "environment", "change_id"):
            dv = getattr(d, key)
            cv = getattr(c, key)
            if dv != cv:
                findings.append(
                    Finding(
                        area="iac",
                        control="metadata-consistency",
                        severity="WARN",
                        message=f"Metadata drift for {rid}: {key} differs (desired={dv!r}, current={cv!r})",
                        evidence={"resource_id": rid, "field": key, "desired": dv, "current": cv},
                    )
                )

        if d.public != c.public:
            findings.append(
                Finding(
                    area="iac",
                    control="public-exposure-drift",
                    severity="ERROR" if c.public else "WARN",
                    message=f"Public exposure drift for {rid}: desired public={d.public}, current public={c.public}",
                    evidence={"resource_id": rid, "desired_public": d.public, "current_public": c.public},
                )
            )

        desired_settings = d.settings
        current_settings = c.settings
        for skey, svalue in sorted(desired_settings.items()):
            if current_settings.get(skey) != svalue:
                findings.append(
                    Finding(
                        area="iac",
                        control="settings-drift",
                        severity="WARN",
                        message=f"Settings drift for {rid}: '{skey}' differs",
                        evidence={
                            "resource_id": rid,
                            "setting": skey,
                            "desired": svalue,
                            "current": current_settings.get(skey),
                        },
                    )
                )

    # Guardrails: required tags + baseline security posture
    for r in desired.resources:
        missing: list[str] = []
        for key in ("owner", "environment", "change_id"):
            if not getattr(r, key).strip():
                missing.append(key)
        if missing:
            findings.append(
                Finding(
                    area="iac",
                    control="required-metadata",
                    severity="ERROR",
                    message=f"Resource missing required metadata: {r.id} ({', '.join(missing)})",
                    evidence={"resource_id": r.id, "missing": missing},
                )
            )

        if r.public:
            findings.append(
                Finding(
                    area="iac",
                    control="no-public-resources",
                    severity="ERROR",
                    message=f"Resource is public but should not be: {r.id}",
                    evidence={"resource_id": r.id, "type": r.type},
                )
            )

        if _resource_requires_encryption(r):
            encrypted = bool(r.settings.get("encryption", False))
            if not encrypted:
                findings.append(
                    Finding(
                        area="iac",
                        control="encryption-required",
                        severity="ERROR",
                        message=f"Encryption is required but not enabled: {r.id}",
                        evidence={"resource_id": r.id, "type": r.type},
                    )
                )

        if _resource_requires_versioning(r):
            versioning = bool(r.settings.get("versioning", False))
            if not versioning:
                findings.append(
                    Finding(
                        area="iac",
                        control="versioning-required",
                        severity="WARN",
                        message=f"Versioning recommended for rollback safety: {r.id}",
                        evidence={"resource_id": r.id, "type": r.type},
                    )
                )

    return _sorted(findings)


def check_delivery(pipeline: Pipeline) -> list[Finding]:
    findings: list[Finding] = []
    stage_names = {s.name for s in pipeline.stages}
    required = {"lint", "test", "plan", "policy", "apply"}
    missing = sorted(required - stage_names)
    if missing:
        findings.append(
            Finding(
                area="delivery",
                control="required-stages",
                severity="ERROR",
                message=f"Pipeline is missing required stages: {', '.join(missing)}",
                evidence={"missing": missing},
            )
        )

    if not pipeline.requires_approval:
        findings.append(
            Finding(
                area="delivery",
                control="prod-approval-gate",
                severity="ERROR",
                message="Production deploys should require an explicit approval signal.",
                evidence={"requires_approval": pipeline.requires_approval},
            )
        )

    success_rate = float(pipeline.metrics.get("success_rate_30d", 0.0))
    if success_rate < 0.95:
        findings.append(
            Finding(
                area="delivery",
                control="pipeline-reliability",
                severity="WARN" if success_rate >= 0.9 else "ERROR",
                message=f"Pipeline success rate is low (30d): {success_rate:.2%}",
                evidence={"success_rate_30d": success_rate},
            )
        )

    flaky_rate = float(pipeline.metrics.get("flaky_test_rate", 0.0))
    if flaky_rate > 0.05:
        findings.append(
            Finding(
                area="delivery",
                control="flaky-tests",
                severity="WARN" if flaky_rate <= 0.1 else "ERROR",
                message=f"Flaky test rate is elevated: {flaky_rate:.2%}",
                evidence={"flaky_test_rate": flaky_rate},
            )
        )

    median_duration = int(pipeline.metrics.get("median_duration_seconds", 0))
    if median_duration > 900:
        findings.append(
            Finding(
                area="delivery",
                control="pipeline-latency",
                severity="WARN",
                message=f"Pipeline median duration is high: {median_duration}s",
                evidence={"median_duration_seconds": median_duration},
            )
        )

    return _sorted(findings)


def check_reliability(incidents: IncidentLog) -> list[Finding]:
    findings: list[Finding] = []
    by_cause: dict[str, list[tuple[str, str]]] = {}
    mttr_values: list[int] = []

    for inc in incidents.incidents:
        mttr = _mttr_minutes(inc.started_at, inc.resolved_at)
        mttr_values.append(mttr)
        if inc.severity in (1, 2):
            if not inc.postmortem_completed:
                findings.append(
                    Finding(
                        area="reliability",
                        control="postmortem-required",
                        severity="ERROR",
                        message=f"Missing completed postmortem for {inc.id} (sev-{inc.severity})",
                        evidence={"incident_id": inc.id, "severity": inc.severity},
                    )
                )
            if inc.followups_open > 0:
                findings.append(
                    Finding(
                        area="reliability",
                        control="followups-closed",
                        severity="WARN",
                        message=f"Open postmortem follow-ups for {inc.id}: {inc.followups_open}",
                        evidence={"incident_id": inc.id, "open_followups": inc.followups_open},
                    )
                )
            if not inc.runbook_used:
                findings.append(
                    Finding(
                        area="reliability",
                        control="runbook-usage",
                        severity="WARN",
                        message=f"No runbook recorded for {inc.id}; standardize response to reduce MTTR.",
                        evidence={"incident_id": inc.id},
                    )
                )

        by_cause.setdefault(inc.root_cause, []).append((inc.id, inc.started_at))

    # Recurrence detection (simple): more than 1 incident per root cause.
    for cause, entries in sorted(by_cause.items()):
        if len(entries) > 1:
            ids = [eid for eid, _ in entries]
            findings.append(
                Finding(
                    area="reliability",
                    control="recurrence",
                    severity="WARN",
                    message=f"Recurring root cause detected ({cause}): incidents {', '.join(ids)}",
                    evidence={"root_cause": cause, "incidents": ids},
                )
            )

    if mttr_values:
        avg_mttr = sum(mttr_values) / len(mttr_values)
        if avg_mttr > 30:
            findings.append(
                Finding(
                    area="reliability",
                    control="mttr",
                    severity="WARN",
                    message=f"Average MTTR is elevated: {avg_mttr:.1f} minutes",
                    evidence={"average_mttr_minutes": round(avg_mttr, 1)},
                )
            )

    return _sorted(findings)


def run_all_checks(inputs: Inputs) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_iac_drift(inputs.desired, inputs.current))
    findings.extend(check_delivery(inputs.pipeline))
    findings.extend(check_reliability(inputs.incidents))
    return _sorted(findings)


def blocking_findings(findings: Iterable[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == "ERROR"]


def _sorted(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda f: (f.area, f.severity, f.control, f.message))

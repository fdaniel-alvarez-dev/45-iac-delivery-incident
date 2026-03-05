from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .checks import Finding


@dataclass(frozen=True)
class Report:
    title: str
    generated_at: str
    findings: tuple[Finding, ...]


def build_report(*, title: str, findings: Iterable[Finding]) -> Report:
    now = datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return Report(title=title, generated_at=now, findings=tuple(findings))


def to_markdown(report: Report) -> str:
    by_area: dict[str, list[Finding]] = {}
    for f in report.findings:
        by_area.setdefault(f.area, []).append(f)

    lines: list[str] = []
    lines.append(f"# {report.title}")
    lines.append("")
    lines.append(f"_Generated at: {report.generated_at}_")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(
        "This report is generated from versioned sample inputs under `examples/` and demonstrates "
        "how to reduce risk across infrastructure drift, delivery safety, and incident reliability."
    )
    lines.append("")
    lines.append("## Validation Summary")
    errors = [f for f in report.findings if f.severity == "ERROR"]
    warns = [f for f in report.findings if f.severity == "WARN"]
    infos = [f for f in report.findings if f.severity == "INFO"]
    lines.append(f"- Errors: {len(errors)}")
    lines.append(f"- Warnings: {len(warns)}")
    lines.append(f"- Info: {len(infos)}")
    lines.append("")
    lines.append("## Findings")
    lines.append("")

    for area in ("iac", "delivery", "reliability"):
        area_title = {
            "iac": "IaC Drift & Guardrails",
            "delivery": "Delivery Controls (CI/CD + Release Safety)",
            "reliability": "Reliability (Incidents + MTTR)",
        }[area]
        lines.append(f"### {area_title}")
        area_findings = by_area.get(area, [])
        if not area_findings:
            lines.append("- No findings.")
            lines.append("")
            continue

        for f in area_findings:
            lines.append(f"- **{f.severity}** `{f.control}` — {f.message}")
        lines.append("")

        if area == "iac":
            lines.append("Recommended runbook: `docs/runbooks/01_iac_drift_and_guardrails.md`")
        elif area == "delivery":
            lines.append("Recommended runbook: `docs/runbooks/02_cicd_release_safety.md`")
        elif area == "reliability":
            lines.append("Recommended runbook: `docs/runbooks/03_incident_response_and_mttr.md`")
        lines.append("")

    lines.append("## How This Maps To The 3 Pain Points")
    lines.append("- Infrastructure drift & fragile automation: desired vs current drift + baseline guardrails.")
    lines.append("- Delivery friction: pipeline gates (lint/test/plan/policy/apply) + approval expectations.")
    lines.append("- Reliability under on-call pressure: postmortems, follow-ups, recurrence and MTTR signals.")
    lines.append("")
    return "\n".join(lines)

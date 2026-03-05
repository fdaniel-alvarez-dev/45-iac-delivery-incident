from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


class InputError(ValueError):
    pass


def _require(obj: dict[str, Any], key: str, *, where: str) -> Any:
    if key not in obj:
        raise InputError(f"Missing key '{key}' in {where}.")
    return obj[key]


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError(f"Input not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"Invalid JSON in {path}: {exc}") from exc


@dataclass(frozen=True)
class Resource:
    id: str
    type: str
    owner: str
    environment: str
    change_id: str
    public: bool
    settings: dict[str, Any]


@dataclass(frozen=True)
class InfraState:
    resources: tuple[Resource, ...]


@dataclass(frozen=True)
class PipelineStage:
    name: str
    required: bool


@dataclass(frozen=True)
class Pipeline:
    name: str
    stages: tuple[PipelineStage, ...]
    requires_approval: bool
    metrics: dict[str, Any]


@dataclass(frozen=True)
class Incident:
    id: str
    service: str
    severity: int
    started_at: str
    resolved_at: str
    root_cause: str
    runbook_used: str | None
    postmortem_completed: bool
    followups_open: int


@dataclass(frozen=True)
class IncidentLog:
    incidents: tuple[Incident, ...]


def _as_bool(value: Any, *, where: str) -> bool:
    if isinstance(value, bool):
        return value
    raise InputError(f"Expected boolean in {where}.")


def _as_str(value: Any, *, where: str) -> str:
    if isinstance(value, str) and value.strip():
        return value
    raise InputError(f"Expected non-empty string in {where}.")


def _as_int(value: Any, *, where: str) -> int:
    if isinstance(value, int):
        return value
    raise InputError(f"Expected integer in {where}.")


def _as_dict(value: Any, *, where: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    raise InputError(f"Expected object/dict in {where}.")


def _as_list(value: Any, *, where: str) -> list[Any]:
    if isinstance(value, list):
        return value
    raise InputError(f"Expected array/list in {where}.")


def parse_infra_state(obj: Any, *, where: str) -> InfraState:
    data = _as_dict(obj, where=where)
    resources_raw = _as_list(_require(data, "resources", where=where), where=f"{where}.resources")
    resources: list[Resource] = []
    for idx, item in enumerate(resources_raw):
        item_where = f"{where}.resources[{idx}]"
        r = _as_dict(item, where=item_where)
        resources.append(
            Resource(
                id=_as_str(_require(r, "id", where=item_where), where=f"{item_where}.id"),
                type=_as_str(_require(r, "type", where=item_where), where=f"{item_where}.type"),
                owner=_as_str(_require(r, "owner", where=item_where), where=f"{item_where}.owner"),
                environment=_as_str(
                    _require(r, "environment", where=item_where), where=f"{item_where}.environment"
                ),
                change_id=_as_str(_require(r, "change_id", where=item_where), where=f"{item_where}.change_id"),
                public=_as_bool(_require(r, "public", where=item_where), where=f"{item_where}.public"),
                settings=_as_dict(_require(r, "settings", where=item_where), where=f"{item_where}.settings"),
            )
        )
    resources.sort(key=lambda x: (x.type, x.id))
    return InfraState(resources=tuple(resources))


def parse_pipeline(obj: Any, *, where: str) -> Pipeline:
    data = _as_dict(obj, where=where)
    name = _as_str(_require(data, "name", where=where), where=f"{where}.name")
    stages_raw = _as_list(_require(data, "stages", where=where), where=f"{where}.stages")
    stages: list[PipelineStage] = []
    for idx, item in enumerate(stages_raw):
        item_where = f"{where}.stages[{idx}]"
        s = _as_dict(item, where=item_where)
        stages.append(
            PipelineStage(
                name=_as_str(_require(s, "name", where=item_where), where=f"{item_where}.name"),
                required=_as_bool(_require(s, "required", where=item_where), where=f"{item_where}.required"),
            )
        )
    requires_approval = _as_bool(
        _require(_as_dict(_require(data, "release", where=where), where=f"{where}.release"), "requires_approval", where=f"{where}.release"),
        where=f"{where}.release.requires_approval",
    )
    metrics = _as_dict(_require(data, "metrics", where=where), where=f"{where}.metrics")
    stages.sort(key=lambda x: x.name)
    return Pipeline(name=name, stages=tuple(stages), requires_approval=requires_approval, metrics=metrics)


def parse_incident_log(obj: Any, *, where: str) -> IncidentLog:
    data = _as_dict(obj, where=where)
    incidents_raw = _as_list(_require(data, "incidents", where=where), where=f"{where}.incidents")
    incidents: list[Incident] = []
    for idx, item in enumerate(incidents_raw):
        item_where = f"{where}.incidents[{idx}]"
        inc = _as_dict(item, where=item_where)
        post = _as_dict(_require(inc, "postmortem", where=item_where), where=f"{item_where}.postmortem")
        followups = _as_list(_require(post, "followups", where=f"{item_where}.postmortem"), where=f"{item_where}.postmortem.followups")
        open_followups = 0
        for fidx, follow in enumerate(followups):
            f_where = f"{item_where}.postmortem.followups[{fidx}]"
            f = _as_dict(follow, where=f_where)
            status = _as_str(_require(f, "status", where=f_where), where=f"{f_where}.status").lower()
            if status not in {"done", "closed"}:
                open_followups += 1
        runbook_used = inc.get("runbook_used")
        runbook_used_str: str | None
        if runbook_used is None:
            runbook_used_str = None
        else:
            runbook_used_str = _as_str(runbook_used, where=f"{item_where}.runbook_used")
        incidents.append(
            Incident(
                id=_as_str(_require(inc, "id", where=item_where), where=f"{item_where}.id"),
                service=_as_str(_require(inc, "service", where=item_where), where=f"{item_where}.service"),
                severity=_as_int(_require(inc, "severity", where=item_where), where=f"{item_where}.severity"),
                started_at=_as_str(_require(inc, "started_at", where=item_where), where=f"{item_where}.started_at"),
                resolved_at=_as_str(_require(inc, "resolved_at", where=item_where), where=f"{item_where}.resolved_at"),
                root_cause=_as_str(_require(inc, "root_cause", where=item_where), where=f"{item_where}.root_cause"),
                runbook_used=runbook_used_str,
                postmortem_completed=_as_bool(
                    _require(post, "completed", where=f"{item_where}.postmortem"),
                    where=f"{item_where}.postmortem.completed",
                ),
                followups_open=open_followups,
            )
        )
    incidents.sort(key=lambda x: (x.service, x.started_at, x.id))
    return IncidentLog(incidents=tuple(incidents))


@dataclass(frozen=True)
class Inputs:
    desired: InfraState
    current: InfraState
    pipeline: Pipeline
    incidents: IncidentLog


def load_inputs(examples_dir: Path) -> Inputs:
    desired = parse_infra_state(load_json(examples_dir / "desired_state.json"), where="desired_state.json")
    current = parse_infra_state(load_json(examples_dir / "current_state.json"), where="current_state.json")
    pipeline = parse_pipeline(load_json(examples_dir / "pipeline.json"), where="pipeline.json")
    incidents = parse_incident_log(load_json(examples_dir / "incident_log.json"), where="incident_log.json")
    return Inputs(desired=desired, current=current, pipeline=pipeline, incidents=incidents)


def iter_resource_map(resources: Iterable[Resource]) -> dict[str, Resource]:
    out: dict[str, Resource] = {}
    for r in resources:
        if r.id in out:
            raise InputError(f"Duplicate resource id: {r.id}")
        out[r.id] = r
    return out

from __future__ import annotations

import argparse
from pathlib import Path

from .checks import blocking_findings, run_all_checks
from .io import InputError, load_inputs
from .report import build_report, to_markdown


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def cmd_report(args: argparse.Namespace) -> int:
    inputs = load_inputs(Path(args.examples))
    findings = run_all_checks(inputs)
    report = build_report(title="45-iac-delivery-incident — Guardrail Report", findings=findings)
    md = to_markdown(report)
    out_path = Path(args.out)
    _write_text(out_path, md)
    print(str(out_path))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    inputs = load_inputs(Path(args.examples))
    findings = run_all_checks(inputs)
    blockers = blocking_findings(findings)
    if not blockers:
        print("OK: no blocking findings (ERROR).")
        return 0

    print(f"FAIL: {len(blockers)} blocking finding(s).")
    for f in blockers:
        print(f"- [{f.area}] {f.control}: {f.message}")
    return 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="portfolio_proof", description="Deterministic guardrails demo (stdlib only).")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("report", help="Generate a human-readable report under artifacts/.")
    pr.add_argument("--examples", default="examples", help="Path to example inputs directory (default: examples).")
    pr.add_argument("--out", default="artifacts/report.md", help="Output Markdown path (default: artifacts/report.md).")
    pr.set_defaults(func=cmd_report)

    pv = sub.add_parser("validate", help="Exit non-zero if inputs violate key controls.")
    pv.add_argument("--examples", default="examples", help="Path to example inputs directory (default: examples).")
    pv.set_defaults(func=cmd_validate)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        return int(args.func(args))
    except InputError as exc:
        print(f"INPUT ERROR: {exc}")
        return 2

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(args: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        ["python3", "-m", "portfolio_proof", *args],
        cwd=str(REPO_ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


class SmokeTests(unittest.TestCase):
    def test_report_generates_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            proc = run_cli(["report", "--examples", "examples", "--out", str(out)])
            self.assertEqual(proc.returncode, 0, proc.stdout)
            self.assertTrue(out.exists(), "report.md not created")
            text = out.read_text(encoding="utf-8")
            self.assertIn("# 45-iac-delivery-incident — Guardrail Report", text)
            self.assertIn("## Findings", text)
            self.assertIn("### IaC Drift & Guardrails", text)
            self.assertIn("### Delivery Controls (CI/CD + Release Safety)", text)
            self.assertIn("### Reliability (Incidents + MTTR)", text)

    def test_validate_fails_on_example_violations(self) -> None:
        proc = run_cli(["validate", "--examples", "examples"])
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("FAIL:", proc.stdout)
        self.assertIn("no-public-resources", proc.stdout)
        self.assertIn("prod-approval-gate", proc.stdout)


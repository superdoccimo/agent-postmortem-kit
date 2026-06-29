from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_postmortem_kit.detectors import analyze_events
from agent_postmortem_kit.parser import parse_paths
from agent_postmortem_kit.report import write_html_report, write_json_report


class SmokeTest(unittest.TestCase):
    def test_sample_log_generates_expected_findings(self) -> None:
        events, files_scanned = parse_paths([Path("examples/sample-agent-session.jsonl")])
        report = analyze_events(
            events,
            files_scanned=files_scanned,
            title="Smoke Test",
        )

        kinds = {finding.kind for finding in report.findings}
        self.assertIn("dangerous_command", kinds)
        self.assertIn("secret_exposure", kinds)
        self.assertIn("repeated_failure", kinds)
        self.assertIn("evidence_gap", kinds)
        self.assertIn("unfinished_work", kinds)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            html_path = tmp_path / "report.html"
            json_path = tmp_path / "report.json"
            write_html_report(report, html_path)
            write_json_report(report, json_path)
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("Smoke Test", html)
            self.assertIn("Findings", html)
            self.assertIn("dangerous_command", json_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

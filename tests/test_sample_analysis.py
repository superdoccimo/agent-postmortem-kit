from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agent_postmortem_kit.detectors import analyze_events
from agent_postmortem_kit.parser import parse_paths
from agent_postmortem_kit.report import write_html_report, write_json_report

SAMPLE_LOG = Path("examples/sample-agent-session.jsonl")


def _sample_report():
    events, files_scanned = parse_paths([SAMPLE_LOG])
    return analyze_events(events, files_scanned=files_scanned, title="Pytest Sample")


def test_sample_agent_session_can_be_parsed() -> None:
    events, files_scanned = parse_paths([SAMPLE_LOG])

    assert files_scanned == 1
    assert len(events) == 9
    assert sum(1 for event in events if event.command) == 3


def test_sample_detects_repeated_failure() -> None:
    report = _sample_report()

    assert any(finding.kind == "repeated_failure" for finding in report.findings)


def test_sample_detects_dangerous_command() -> None:
    report = _sample_report()

    assert any(finding.kind == "dangerous_command" for finding in report.findings)


def test_sample_detects_secret_exposure_risk() -> None:
    report = _sample_report()

    assert any(finding.kind == "secret_exposure" for finding in report.findings)
    assert all("ghp_" not in evidence.excerpt for finding in report.findings for evidence in finding.evidence)


def test_sample_detects_evidence_gap_and_unfinished_work() -> None:
    report = _sample_report()
    kinds = {finding.kind for finding in report.findings}

    assert "evidence_gap" in kinds
    assert "unfinished_work" in kinds


def test_sample_report_writes_html_and_json() -> None:
    report = _sample_report()
    reports_root = Path("reports").resolve()
    reports_root.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pytest-sample-", dir=reports_root) as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "sample.html"
        json_path = tmp_path / "sample.json"

        write_html_report(report, html_path)
        write_json_report(report, json_path)

        html = html_path.read_text(encoding="utf-8")
        data = json.loads(json_path.read_text(encoding="utf-8"))

    assert "Pytest Sample" in html
    assert "Findings" in html
    assert data["stats"]["events"] == 9
    assert len(data["findings"]) >= 5

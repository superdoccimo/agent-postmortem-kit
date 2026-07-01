from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agent_postmortem_kit.cli import main


def test_cli_generates_html_and_json_reports() -> None:
    reports_root = Path("reports").resolve()
    reports_root.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pytest-", dir=reports_root) as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "sample.html"
        json_path = tmp_path / "sample.json"
        skill_path = tmp_path / "skill-candidates.md"

        exit_code = main(
            [
                "analyze",
                "examples/sample-agent-session.jsonl",
                "--out",
                str(html_path),
                "--json",
                str(json_path),
                "--skill-out",
                str(skill_path),
            ]
        )

        assert exit_code == 0
        assert html_path.exists()
        assert json_path.exists()
        assert skill_path.exists()

        report = json.loads(json_path.read_text(encoding="utf-8"))
        kinds = {finding["kind"] for finding in report["findings"]}

        assert report["stats"]["events"] == 9
        assert report["stats"]["shell_commands"] == 3
        assert {
            "dangerous_command",
            "secret_exposure",
            "repeated_failure",
            "evidence_gap",
            "unfinished_work",
        }.issubset(kinds)
        assert "[REDACTED_SECRET]" in html_path.read_text(encoding="utf-8")

        skill_markdown = skill_path.read_text(encoding="utf-8")
        assert "# Skill Candidate Export" in skill_markdown
        assert "Failure pattern:" in skill_markdown
        assert "Evidence" in skill_markdown
        assert "Next-run rule" in skill_markdown
        assert "Verification command" in skill_markdown

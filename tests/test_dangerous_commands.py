from __future__ import annotations

import pytest

from agent_postmortem_kit.detectors import detect_dangerous_commands
from agent_postmortem_kit.model import Event


@pytest.mark.parametrize("flags", ["-rf", "-fr", "-fR"])
def test_recursive_forced_delete_detects_flag_order_variants(flags: str) -> None:
    event = Event(
        source="synthetic.jsonl",
        line=1,
        event_type="tool_call",
        role="assistant",
        content="synthetic command fixture",
        command=f"rm {flags} build-output",
    )

    findings = detect_dangerous_commands([event])

    assert any(
        finding.title == "Dangerous command: destructive recursive delete"
        for finding in findings
    )

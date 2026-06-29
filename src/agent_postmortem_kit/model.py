from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    source: str
    line: int | None
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return {"source": self.source, "line": self.line, "excerpt": self.excerpt}


@dataclass(frozen=True)
class Event:
    source: str
    line: int | None
    event_type: str
    role: str | None
    content: str
    command: str | None = None
    timestamp: str | None = None
    raw: dict[str, Any] | None = None


@dataclass
class Finding:
    kind: str
    severity: str
    title: str
    summary: str
    evidence: list[Evidence] = field(default_factory=list)
    recommendation: str | None = None
    human_approval_required: bool = False
    skill_candidate: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "severity": self.severity,
            "title": self.title,
            "summary": self.summary,
            "evidence": [item.to_dict() for item in self.evidence],
            "recommendation": self.recommendation,
            "human_approval_required": self.human_approval_required,
            "skill_candidate": self.skill_candidate,
        }


@dataclass
class Stats:
    files_scanned: int
    events: int
    shell_commands: int
    error_like_events: int

    def to_dict(self) -> dict[str, int]:
        return {
            "files_scanned": self.files_scanned,
            "events": self.events,
            "shell_commands": self.shell_commands,
            "error_like_events": self.error_like_events,
        }


@dataclass
class PostmortemReport:
    title: str
    goal: str
    completed: str
    failed: list[str]
    risk: list[str]
    evidence: list[Evidence]
    next_action: list[str]
    human_approval_required: list[str]
    skill_candidate: list[str]
    findings: list[Finding]
    stats: Stats

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "goal": self.goal,
            "completed": self.completed,
            "failed": self.failed,
            "risk": self.risk,
            "evidence": [item.to_dict() for item in self.evidence],
            "next_action": self.next_action,
            "human_approval_required": self.human_approval_required,
            "skill_candidate": self.skill_candidate,
            "findings": [finding.to_dict() for finding in self.findings],
            "stats": self.stats.to_dict(),
        }

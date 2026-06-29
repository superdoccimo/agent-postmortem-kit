from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Iterable

from .model import Event, Evidence, Finding, PostmortemReport, Stats

ERROR_RE = re.compile(
    r"(?i)\b(error|failed|failure|exception|traceback|exit code:\s*[1-9]|nonzero|timed out)\b"
)
VERIFY_GAP_RE = re.compile(
    r"(?i)\b(not tested|did not run tests|could not verify|unable to verify|not verified|"
    r"assum(?:e|ed|ing)|probably|maybe|looks like|should work)\b"
)
UNFINISHED_RE = re.compile(
    r"(?i)\b(todo|fixme|blocked|unresolved|still failing|not generated|could not create|"
    r"missing artifact|incomplete|follow[- ]?up required)\b"
)
APPROVAL_RE = re.compile(
    r"(?i)\b(approval|approve|confirm|permission|require_escalated|human approval)\b"
)
SECRET_RE = re.compile(r"\[REDACTED_SECRET\]")

DANGEROUS_COMMANDS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "destructive recursive delete",
        re.compile(r"(?i)\brm\s+-[^\n]*r[^\n]*f\b|Remove-Item\b[^\n]*-Recurse"),
        "Require an explicit approval gate and path boundary check before recursive deletes.",
    ),
    (
        "forced git history or workspace reset",
        re.compile(r"(?i)\bgit\s+(reset\s+--hard|checkout\s+--|clean\s+-[fdx])\b"),
        "Require human approval before commands that discard local work.",
    ),
    (
        "pipe remote script to shell",
        re.compile(r"(?i)\b(curl|wget)\b[^\n|]*\|\s*(sh|bash|powershell|pwsh)\b"),
        "Download scripts to a file, inspect them, and pin the source before execution.",
    ),
    (
        "privileged shell command",
        re.compile(r"(?i)\bsudo\b|\bStart-Process\b[^\n]*-Verb\s+RunAs"),
        "Require a clear justification and user approval before privileged execution.",
    ),
    (
        "broad permission change",
        re.compile(r"(?i)\bchmod\s+(-R\s+)?777\b|\bicacls\b[^\n]*/grant\b[^\n]*:F\b"),
        "Prefer least-privilege file permissions and document why permission changes are needed.",
    ),
    (
        "disk or filesystem destructive command",
        re.compile(r"(?i)\b(dd|mkfs|diskpart|format)\b"),
        "Block disk-level commands unless the user explicitly requests them.",
    ),
]


def analyze_events(
    events: list[Event],
    *,
    files_scanned: int,
    title: str,
    goal: str | None = None,
) -> PostmortemReport:
    findings: list[Finding] = []
    findings.extend(detect_secret_exposure(events))
    findings.extend(detect_dangerous_commands(events))
    findings.extend(detect_repeated_failures(events))
    findings.extend(detect_evidence_gaps(events))
    findings.extend(detect_unfinished_work(events))
    findings.extend(detect_approval_language(events))

    stats = Stats(
        files_scanned=files_scanned,
        events=len(events),
        shell_commands=sum(1 for event in events if event.command),
        error_like_events=sum(1 for event in events if ERROR_RE.search(event.content)),
    )

    inferred_goal = goal or infer_goal(events)
    failed = [
        finding.title
        for finding in findings
        if finding.severity in {"critical", "high", "medium"}
    ]
    risk = [
        finding.title
        for finding in findings
        if finding.kind in {"secret_exposure", "dangerous_command", "approval_required"}
    ]
    evidence = [item for finding in findings for item in finding.evidence[:1]][:10]
    next_action = _unique(
        finding.recommendation for finding in findings if finding.recommendation
    )
    human_approval_required = _unique(
        finding.title for finding in findings if finding.human_approval_required
    )
    skill_candidate = _unique(
        finding.skill_candidate for finding in findings if finding.skill_candidate
    )

    completed = infer_completion(events, findings)

    return PostmortemReport(
        title=title,
        goal=inferred_goal,
        completed=completed,
        failed=failed or ["No high-confidence failure was detected."],
        risk=risk or ["No high-confidence risk signal was detected."],
        evidence=evidence,
        next_action=next_action or ["Review the source log manually for intent and context."],
        human_approval_required=human_approval_required,
        skill_candidate=skill_candidate,
        findings=sorted(findings, key=_finding_sort_key),
        stats=stats,
    )


def detect_secret_exposure(events: Iterable[Event]) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        if SECRET_RE.search(event.content) or (event.command and SECRET_RE.search(event.command)):
            findings.append(
                Finding(
                    kind="secret_exposure",
                    severity="critical",
                    title="Possible secret exposure in log",
                    summary="A token-like value was found and redacted while parsing the log.",
                    evidence=[_evidence(event)],
                    recommendation="Rotate the exposed credential if it was real, and add log redaction before storing agent traces.",
                    human_approval_required=True,
                    skill_candidate="Create a log-redaction skill that scans agent transcripts before sharing or reporting.",
                )
            )
    return findings


def detect_dangerous_commands(events: Iterable[Event]) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        command = event.command or ""
        content = event.content
        haystack = f"{command}\n{content}"
        for label, pattern, recommendation in DANGEROUS_COMMANDS:
            if pattern.search(haystack):
                findings.append(
                    Finding(
                        kind="dangerous_command",
                        severity="high",
                        title=f"Dangerous command: {label}",
                        summary="A command matched a destructive or high-authority operation pattern.",
                        evidence=[_evidence(event, command or content)],
                        recommendation=recommendation,
                        human_approval_required=True,
                        skill_candidate="Create an approval-gate skill for destructive shell commands.",
                    )
                )
    return findings


def detect_repeated_failures(events: Iterable[Event]) -> list[Finding]:
    grouped: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        if ERROR_RE.search(event.content):
            key = _normalize_failure(event.content)
            grouped[key].append(event)

    findings: list[Finding] = []
    for key, group in grouped.items():
        if len(group) < 2:
            continue
        findings.append(
            Finding(
                kind="repeated_failure",
                severity="high",
                title="Repeated failure pattern",
                summary=f"The same failure-like pattern appeared {len(group)} times: {key}",
                evidence=[_evidence(event) for event in group[:5]],
                recommendation="Stop retrying and inspect the first failure, environment assumptions, and missing prerequisites.",
                skill_candidate="Create a troubleshooting skill for recurring command or test failures.",
            )
        )
    return findings


def detect_evidence_gaps(events: Iterable[Event]) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        if VERIFY_GAP_RE.search(event.content):
            findings.append(
                Finding(
                    kind="evidence_gap",
                    severity="medium",
                    title="Evidence or verification gap",
                    summary="The log contains language indicating an assumption or missing verification.",
                    evidence=[_evidence(event)],
                    recommendation="Add the exact verification command, result, or reason verification was impossible.",
                    skill_candidate="Create a final-verification skill that blocks completion claims without evidence.",
                )
            )
    return findings


def detect_unfinished_work(events: Iterable[Event]) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        if UNFINISHED_RE.search(event.content):
            findings.append(
                Finding(
                    kind="unfinished_work",
                    severity="medium",
                    title="Unfinished work signal",
                    summary="The log contains a blocker, TODO, unresolved state, or missing artifact signal.",
                    evidence=[_evidence(event)],
                    recommendation="Convert the unfinished item into a next action with owner, file path, and verification step.",
                    skill_candidate="Create a postmortem checklist skill for unresolved work and missing artifacts.",
                )
            )
    return findings


def detect_approval_language(events: Iterable[Event]) -> list[Finding]:
    findings: list[Finding] = []
    for event in events:
        if APPROVAL_RE.search(event.content):
            findings.append(
                Finding(
                    kind="approval_required",
                    severity="medium",
                    title="Human approval language detected",
                    summary="The log mentions approval, confirmation, permission, or escalated execution.",
                    evidence=[_evidence(event)],
                    recommendation="Record whether approval was requested, granted, denied, or bypassed.",
                    human_approval_required=True,
                    skill_candidate="Create an approval-ledger skill for commands that need user consent.",
                )
            )
    return findings


def infer_goal(events: list[Event]) -> str:
    for event in events:
        if event.role and event.role.lower() in {"user", "human"} and event.content:
            return _shorten(event.content, 240)
    for event in events[:5]:
        if event.content:
            return _shorten(event.content, 240)
    return "No goal could be inferred from the supplied log."


def infer_completion(events: list[Event], findings: list[Finding]) -> str:
    if not events:
        return "No log events were parsed."
    if any(finding.severity == "critical" for finding in findings):
        return "Completion is not trusted because critical risk signals were detected."
    success_signals = Counter()
    for event in events:
        if re.search(r"(?i)\b(done|completed|fixed|passed|success|verified)\b", event.content):
            success_signals["success"] += 1
    if success_signals:
        return "Possible completion signals were found, but the report should be checked against the evidence."
    return "No explicit completion evidence was found in the supplied log."


def _evidence(event: Event, override_excerpt: str | None = None) -> Evidence:
    return Evidence(
        source=event.source,
        line=event.line,
        excerpt=_shorten((override_excerpt or event.content).replace("\n", " "), 300),
    )


def _normalize_failure(text: str) -> str:
    first_line = text.strip().splitlines()[0] if text.strip() else text
    normalized = re.sub(r"\b\d+\b", "<n>", first_line.lower())
    normalized = re.sub(r"['\"][^'\"]{20,}['\"]", "<value>", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return _shorten(normalized, 140)


def _shorten(text: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def _unique(values: Iterable[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _finding_sort_key(finding: Finding) -> tuple[int, str]:
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return (severity_rank.get(finding.severity, 9), finding.title)

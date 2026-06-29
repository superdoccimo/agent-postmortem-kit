# Agent Postmortem Kit

Local-first postmortem reports for AI coding-agent sessions.

Agent Postmortem Kit reads local agent logs and turns them into an audit-oriented report:

- repeated failures
- dangerous commands
- secret exposure risk
- weak or missing evidence
- unfinished work
- human approval points
- candidate rules or skills to prevent the same failure next time

This is not an agent dashboard. The v0 goal is narrower: read logs, extract failure evidence, and produce a report a human can act on.

## Status

Early v0.1 scaffold. The CLI currently supports generic JSONL and text logs with heuristic detectors. OpenClaw, Hermes, Codex, Claude Code, and AgentTrace-specific adapters should be added as focused parsers once sample logs are available.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
agent-postmortem analyze examples/sample-agent-session.jsonl --out reports/sample.html --json reports/sample.json
```

Without installing:

```powershell
$env:PYTHONPATH = "src"
python -m agent_postmortem_kit analyze examples/sample-agent-session.jsonl --out reports/sample.html --json reports/sample.json
```

Open `reports/sample.html` in a browser to inspect the static report.

If `agent-postmortem` is not on your `PATH`, use `python -m agent_postmortem_kit analyze ...` instead.

## Output Shape

Each report is organized around the MMPR-style fields used for this project:

```text
Goal:
Completed:
Failed:
Risk:
Evidence:
Next action:
Human approval required:
Skill candidate:
```

The JSON output preserves the same fields plus structured findings and stats for downstream tooling.

## Design Principles

- Local-first: no network calls, no upload step, no hosted service required.
- Evidence-first: every finding should point back to source file and line when possible.
- Conservative detection: findings are signals for human review, not proof of intent.
- Adapter-based: agent-specific parsing should live at the edge; shared detectors stay generic.
- Postmortem-focused: the product should explain what failed and what to change next, not just visualize tokens and timing.

## Current CLI

```text
agent-postmortem analyze <paths...> [--out report.html] [--json report.json] [--goal "..."] [--title "..."]
```

Paths can be files or directories. Directories are scanned for `.jsonl`, `.json`, `.log`, `.txt`, and `.md` files.

## Roadmap

- Add OpenClaw log adapter once representative logs are available.
- Add Codex and Claude Code JSONL adapters.
- Add AgentTrace import so this tool can analyze AgentTrace exports instead of competing with its TUI layer.
- Add richer timeline and repeated-failure clustering.
- Add policy packs for approval gates and dangerous operations.
- Add skill-candidate export as Markdown.

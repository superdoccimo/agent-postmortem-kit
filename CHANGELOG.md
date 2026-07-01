# Changelog

## v0.1.0 - Working Demo

Initial public demo scaffold for Agent Postmortem Kit.

### Added

- Generic JSONL, JSON, text, log, and Markdown input parsing.
- Heuristic detectors for repeated failures, dangerous commands, secret exposure risk, evidence gaps, unfinished work, and human approval signals.
- Static HTML report generation.
- Structured JSON report generation.
- Markdown skill-candidate export with failure pattern, evidence, next-run rule, and verification command sections.
- Sample AI-agent session log for safe local demos.
- Pytest and unittest smoke coverage.
- Safety-oriented `.gitignore` rules for generated reports, real logs, env files, and key material.
- v0.1 demo notes, OpenClaw adapter plan, and Oracle consultation plan.

### Notes

- This is a working v0.1 demo, not a finished observability platform.
- OpenClaw, Hermes, Codex, Claude Code, and AgentTrace adapters are not complete yet.
- Secret redaction is heuristic and must be reviewed by a human before sharing reports.

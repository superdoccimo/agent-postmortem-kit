# Agent Postmortem Kit Brief

## Purpose

Agent Postmortem Kit is an early v0.1 technical preview for turning AI coding-agent session logs into local postmortem reports.

The current version demonstrates a small loop:

```text
sample agent log -> postmortem findings -> HTML/JSON report -> skill-candidate draft
```

It is not production-ready, and it should not be described as a complete observability or audit platform.

## Background

AI coding agents increasingly read files, run shell commands, retry failed work, and produce final summaries. The human often sees the final answer but not the failure path. This makes it hard to answer:

- Where did the agent fail?
- Did it retry the same broken command?
- Did it attempt a risky operation?
- Did it claim completion without evidence?
- What rule would prevent the same failure next time?

Agent Postmortem Kit focuses on this postmortem layer.

## Difference From AgentTrace

AgentTrace is stronger for local agent history, timing, cost, token use, tool failures, health, and TUI-style inspection.

Agent Postmortem Kit is not trying to replace AgentTrace. The planned direction is to analyze logs or exports, including possible AgentTrace exports, and produce postmortem findings:

- failure patterns
- risky actions
- evidence gaps
- human approval points
- next-run skill candidates

The differentiator is the transition from trace review to postmortem rule creation.

## What Works Now

The current private technical preview can:

- parse generic JSONL, JSON, text, log, and Markdown files
- detect repeated failure-like output
- detect dangerous commands such as forced Git resets or recursive deletes
- detect token-like secret exposure risk and redact matching values
- detect evidence gaps such as "could not verify"
- detect unfinished work such as TODOs or missing artifacts
- generate static HTML reports
- generate structured JSON reports
- export Markdown skill candidates with failure pattern, evidence, next-run rule, and verification command sections
- run tests with pytest and unittest
- run GitHub Actions CI across Python 3.10, 3.11, and 3.12

The sample report screenshot is generated only from the synthetic sample log in `examples/sample-agent-session.jsonl`.

## What It Cannot Do Yet

The project cannot yet:

- parse OpenClaw, Hermes, Codex, Claude Code, or AgentTrace formats with dedicated adapters
- guarantee complete secret redaction
- safely process private real-world logs without human review
- infer intent with high confidence
- replace a human postmortem
- call Oracle or another external model by default
- provide production-grade policy enforcement

## Safety Notes

Do not publish real logs.

Keep real sessions under ignored local paths such as:

- `logs/`
- `private-logs/`
- `real-logs/`
- `agent-logs/`

Generated reports under `reports/` are ignored by Git. Secret redaction is heuristic and incomplete, so every report needs human review before sharing.

## Near-Term Direction

The next useful implementation candidates are:

1. AgentTrace JSON export adapter.
2. OpenClaw adapter after reviewing representative local logs.
3. Policy packs for approval gates, dangerous commands, and verification requirements.

Public release should be reconsidered after at least one real adapter or policy pack exists.

## Suggested Safe Video Framing

Use this framing for a NotebookLM video:

```text
This is a private v0.1 technical preview of Agent Postmortem Kit.
It shows how a synthetic AI-agent session log can be turned into a local postmortem report and skill-candidate draft.
It is not production-ready and does not use real logs.
```

Avoid claims such as:

- complete AI agent observability platform
- production-ready audit tool
- full OpenClaw, Codex, Claude Code, Hermes, or AgentTrace support
- complete secret detection
- automatic safe processing of real logs

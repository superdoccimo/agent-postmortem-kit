# Oracle Consultation Plan

## Position

Oracle is a second-opinion path for moments when Codex or another local agent is stuck.

It is not part of the default postmortem analyzer. Agent Postmortem Kit remains local-first by default. Oracle integration should be opt-in because it can bundle prompts and files for another AI system.

Reference: https://github.com/steipete/oracle

## Intended Workflow

```text
Codex gets stuck
-> Agent Postmortem Kit identifies the failure context
-> Human reviews the exact files and excerpts to share
-> Oracle bundles the prompt and selected files
-> ChatGPT Pro, GPT API, Gemini, Claude, or another model reviews it
-> Codex reads the answer as advisory input
-> Codex verifies against local code and tests before acting
```

## Preferred Modes

1. API mode
   - Best for repeatability and automation.
   - Requires provider API keys.
   - Should use dry-run or preflight checks before expensive calls.
2. Render/copy mode
   - Safest fallback.
   - Produces a bundle that a human can paste manually.
   - Good default for sensitive repositories.
3. Browser mode
   - Useful when ChatGPT Pro browser access is required.
   - More fragile because it depends on browser login state and UI behavior.
   - Should not be the first integration path for this repository.

## What Agent Postmortem Kit Should Provide

Future Oracle support should generate a review bundle from a postmortem report:

- goal and failure summary
- relevant findings
- cited log excerpts
- selected source files
- commands already run
- verification gaps
- explicit questions for the outside model

The bundle must be readable before it is sent anywhere.

## Safety Rules

- Never send real logs automatically.
- Never include files from `logs/`, `reports/`, `.env`, key files, or ignored paths by default.
- Redact secret-like values before bundle generation.
- Require an explicit allowlist of files for Oracle consultation.
- Treat Oracle output as advisory, not authoritative.
- Re-run local tests and checks before applying a recommendation.
- Record whether the consultation used API, render/copy, or browser mode.

## Report Fields

If Oracle consultation is added, reports should include:

```text
Oracle consultation:
Mode:
Files shared:
Prompt summary:
Models asked:
Response summary:
Accepted recommendations:
Rejected recommendations:
Verification after consultation:
```

## Non-Goals

Initial Oracle integration should not:

- install Oracle automatically
- read or upload real agent logs automatically
- decide file-sharing scope without human review
- replace local detectors
- auto-apply Oracle recommendations
- use browser automation as the default path

## First Implementation Step

Add a local-only command that renders an Oracle-ready Markdown bundle without sending it:

```text
agent-postmortem oracle-bundle reports/sample.json --file src/... --out reports/oracle-bundle.md
```

Only after that path is reviewed should API/browser execution be considered.

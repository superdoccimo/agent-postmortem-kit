# OpenClaw Adapter Plan

OpenClaw support should be added after reviewing one or more representative local logs. The adapter should stay thin: normalize OpenClaw-specific records into the shared `Event` model, then reuse the generic detectors.

## Required Mapping

Map each OpenClaw record to:

- `timestamp`
- `event_type`
- `role`
- `content`
- `command`
- `source`
- `line`
- `raw`

## Questions to Answer From Real Logs

- Where are OpenClaw logs stored by default?
- Are logs JSONL, JSON, SQLite, plain text, or mixed artifacts?
- How are tool calls represented?
- How are shell commands represented?
- Are command outputs separate records or embedded in the tool call?
- Is approval/escalation represented explicitly?
- Are OpenClaw failures typed, or only visible through text output?

## Detector Candidates

OpenClaw-specific detectors may be useful if the logs expose structured signals for:

- permission prompts
- sandbox escapes
- retry loops
- subagent handoffs
- tool failures
- stalled tasks
- missing final artifacts

Do not add OpenClaw-specific detectors until the same signal cannot be captured cleanly by generic rules.

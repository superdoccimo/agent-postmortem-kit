from __future__ import annotations

import html
import json
from pathlib import Path

from .model import Evidence, Finding, PostmortemReport


def write_json_report(report: PostmortemReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_html_report(report: PostmortemReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(report), encoding="utf-8")


def render_html(report: PostmortemReport) -> str:
    stats = report.stats
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(report.title)}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f8fa;
      --panel: #ffffff;
      --ink: #18202a;
      --muted: #5f6b7a;
      --line: #d9dee7;
      --critical: #b42318;
      --high: #b54708;
      --medium: #7a5af8;
      --low: #067647;
      --accent: #0f766e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    header {{
      background: #111827;
      color: #ffffff;
      padding: 28px 32px;
      border-bottom: 4px solid var(--accent);
    }}
    header h1 {{
      margin: 0 0 8px;
      font-size: clamp(24px, 4vw, 40px);
      line-height: 1.08;
      letter-spacing: 0;
    }}
    header p {{ margin: 0; color: #cbd5e1; max-width: 960px; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    section {{ margin: 0 0 22px; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    h3 {{ margin: 0 0 8px; font-size: 15px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin-top: 18px;
    }}
    .metric, .panel, .finding {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric {{ padding: 14px; color: var(--ink); }}
    .metric strong {{ display: block; font-size: 24px; line-height: 1; }}
    .metric span {{ color: var(--muted); font-size: 12px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
    }}
    .panel {{ padding: 16px; }}
    .panel p {{ margin: 0; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li + li {{ margin-top: 6px; }}
    .findings {{ display: grid; gap: 12px; }}
    .finding {{ padding: 16px; border-left-width: 5px; }}
    .finding.critical {{ border-left-color: var(--critical); }}
    .finding.high {{ border-left-color: var(--high); }}
    .finding.medium {{ border-left-color: var(--medium); }}
    .finding.low {{ border-left-color: var(--low); }}
    .badge {{
      display: inline-flex;
      align-items: center;
      min-height: 22px;
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      color: #fff;
      text-transform: uppercase;
    }}
    .badge.critical {{ background: var(--critical); }}
    .badge.high {{ background: var(--high); }}
    .badge.medium {{ background: var(--medium); }}
    .badge.low {{ background: var(--low); }}
    .meta {{ color: var(--muted); font-size: 12px; margin-top: 4px; }}
    code {{
      background: #eef2f7;
      border: 1px solid #dde3ec;
      border-radius: 5px;
      padding: 1px 4px;
      word-break: break-word;
    }}
    .evidence {{
      margin-top: 10px;
      padding: 10px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
    }}
    .evidence + .evidence {{ margin-top: 8px; }}
    .empty {{ color: var(--muted); }}
  </style>
</head>
<body>
  <header>
    <h1>{_e(report.title)}</h1>
    <p>{_e(report.goal)}</p>
    <div class="metrics">
      <div class="metric"><strong>{stats.files_scanned}</strong><span>files scanned</span></div>
      <div class="metric"><strong>{stats.events}</strong><span>events parsed</span></div>
      <div class="metric"><strong>{stats.shell_commands}</strong><span>shell commands</span></div>
      <div class="metric"><strong>{stats.error_like_events}</strong><span>error-like events</span></div>
    </div>
  </header>
  <main>
    <section class="grid">
      {_panel("Completed", [report.completed])}
      {_panel("Failed", report.failed)}
      {_panel("Risk", report.risk)}
      {_panel("Next Action", report.next_action)}
      {_panel("Human Approval Required", report.human_approval_required)}
      {_panel("Skill Candidate", report.skill_candidate)}
    </section>
    <section>
      <h2>Evidence</h2>
      {_evidence_list(report.evidence)}
    </section>
    <section>
      <h2>Findings</h2>
      <div class="findings">
        {''.join(_finding(item) for item in report.findings) or '<p class="empty">No findings.</p>'}
      </div>
    </section>
  </main>
</body>
</html>
"""


def _panel(title: str, items: list[str]) -> str:
    body = _list(items)
    return f'<div class="panel"><h2>{_e(title)}</h2>{body}</div>'


def _list(items: list[str]) -> str:
    if not items:
        return '<p class="empty">None detected.</p>'
    if len(items) == 1:
        return f"<p>{_e(items[0])}</p>"
    return "<ul>" + "".join(f"<li>{_e(item)}</li>" for item in items) + "</ul>"


def _finding(finding: Finding) -> str:
    evidence = _evidence_list(finding.evidence)
    recommendation = (
        f"<p><strong>Recommendation:</strong> {_e(finding.recommendation)}</p>"
        if finding.recommendation
        else ""
    )
    skill = (
        f"<p><strong>Skill candidate:</strong> {_e(finding.skill_candidate)}</p>"
        if finding.skill_candidate
        else ""
    )
    approval = (
        '<p><strong>Human approval:</strong> required or should be audited.</p>'
        if finding.human_approval_required
        else ""
    )
    return f"""
    <article class="finding {_e(finding.severity)}">
      <span class="badge {_e(finding.severity)}">{_e(finding.severity)}</span>
      <h3>{_e(finding.title)}</h3>
      <p>{_e(finding.summary)}</p>
      <p class="meta">kind: <code>{_e(finding.kind)}</code></p>
      {recommendation}
      {approval}
      {skill}
      {evidence}
    </article>
    """


def _evidence_list(items: list[Evidence]) -> str:
    if not items:
        return '<p class="empty">No evidence captured.</p>'
    chunks = []
    for item in items:
        line = f":{item.line}" if item.line is not None else ""
        chunks.append(
            '<div class="evidence">'
            f'<div class="meta">{_e(item.source)}{_e(line)}</div>'
            f'<div>{_e(item.excerpt)}</div>'
            "</div>"
        )
    return "".join(chunks)


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)

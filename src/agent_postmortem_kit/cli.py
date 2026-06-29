from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .detectors import analyze_events
from .parser import parse_paths
from .report import write_html_report, write_json_report


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return run_analyze(args)

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-postmortem",
        description="Generate local-first postmortem reports for AI agent logs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser("analyze", help="Analyze agent logs")
    analyze.add_argument("paths", nargs="+", help="Log files or directories to analyze")
    analyze.add_argument(
        "--out",
        default="reports/postmortem.html",
        help="Path for the static HTML report",
    )
    analyze.add_argument(
        "--json",
        default=None,
        help="Optional path for the structured JSON report",
    )
    analyze.add_argument(
        "--title",
        default="Agent Postmortem Report",
        help="Report title",
    )
    analyze.add_argument(
        "--goal",
        default=None,
        help="Override inferred goal",
    )
    analyze.add_argument(
        "--fail-on-critical",
        action="store_true",
        help="Exit with status 2 if a critical finding is detected",
    )
    return parser


def run_analyze(args: argparse.Namespace) -> int:
    paths = [Path(item).expanduser().resolve() for item in args.paths]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing path: {path}", file=sys.stderr)
        return 1

    events, files_scanned = parse_paths(paths)
    report = analyze_events(
        events,
        files_scanned=files_scanned,
        title=args.title,
        goal=args.goal,
    )

    html_path = Path(args.out).expanduser().resolve()
    write_html_report(report, html_path)

    json_path = None
    if args.json:
        json_path = Path(args.json).expanduser().resolve()
        write_json_report(report, json_path)

    _print_summary(report, html_path, json_path)

    if args.fail_on_critical and any(
        finding.severity == "critical" for finding in report.findings
    ):
        return 2
    return 0


def _print_summary(report, html_path: Path, json_path: Path | None) -> None:
    print(f"Report: {html_path}")
    if json_path:
        print(f"JSON:   {json_path}")
    print(
        "Scanned "
        f"{report.stats.files_scanned} files, "
        f"{report.stats.events} events, "
        f"{len(report.findings)} findings."
    )
    if report.human_approval_required:
        print("Human approval required:")
        for item in report.human_approval_required:
            print(f"- {item}")
    if report.skill_candidate:
        print("Skill candidates:")
        for item in report.skill_candidate:
            print(f"- {item}")

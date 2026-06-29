from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .model import Event

LOG_EXTENSIONS = {".jsonl", ".json", ".log", ".txt", ".md"}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(
        r"(?i)\b(api[_-]?key|token|secret|password)\s*=\s*['\"]?[^'\"\s]{8,}"
    ),
]


def discover_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix.lower() in LOG_EXTENSIONS:
                    files.append(child)
        elif path.is_file():
            files.append(path)
    return sorted(files)


def parse_paths(paths: Iterable[Path]) -> tuple[list[Event], int]:
    files = discover_files(paths)
    events: list[Event] = []
    for path in files:
        events.extend(parse_file(path))
    return events, len(files)


def parse_file(path: Path) -> list[Event]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return _parse_jsonl(path)
    if suffix == ".json":
        return _parse_json(path)
    return _parse_text(path)


def _parse_jsonl(path: Path) -> list[Event]:
    events: list[Event] = []
    for line_number, line in enumerate(_read_lines(path), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            events.append(_event_from_text(path, line_number, stripped))
            continue
        if isinstance(obj, dict):
            events.append(_event_from_object(path, line_number, obj))
        else:
            events.append(_event_from_text(path, line_number, str(obj)))
    return events


def _parse_json(path: Path) -> list[Event]:
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return _parse_text(path)
    if isinstance(obj, list):
        return [
            _event_from_object(path, index + 1, item)
            if isinstance(item, dict)
            else _event_from_text(path, index + 1, str(item))
            for index, item in enumerate(obj)
        ]
    if isinstance(obj, dict):
        records = obj.get("events") or obj.get("messages") or obj.get("records")
        if isinstance(records, list):
            return [
                _event_from_object(path, index + 1, item)
                if isinstance(item, dict)
                else _event_from_text(path, index + 1, str(item))
                for index, item in enumerate(records)
            ]
        return [_event_from_object(path, 1, obj)]
    return [_event_from_text(path, 1, str(obj))]


def _parse_text(path: Path) -> list[Event]:
    events: list[Event] = []
    for line_number, line in enumerate(_read_lines(path), start=1):
        stripped = line.strip()
        if stripped:
            events.append(_event_from_text(path, line_number, stripped))
    return events


def _event_from_object(path: Path, line: int, obj: dict[str, Any]) -> Event:
    command = _extract_command(obj)
    content = _extract_content(obj)
    if command and command not in content:
        content = f"{content}\nCOMMAND: {command}".strip()
    event_type = str(
        obj.get("type")
        or obj.get("event")
        or obj.get("kind")
        or ("tool_call" if command else "message")
    )
    role = obj.get("role") or obj.get("actor") or obj.get("speaker")
    timestamp = obj.get("timestamp") or obj.get("time") or obj.get("created_at")
    return Event(
        source=str(path),
        line=line,
        event_type=event_type,
        role=str(role) if role is not None else None,
        content=redact(content),
        command=redact(command) if command else None,
        timestamp=str(timestamp) if timestamp is not None else None,
        raw=obj,
    )


def _event_from_text(path: Path, line: int, text: str) -> Event:
    command = _extract_inline_command(text)
    return Event(
        source=str(path),
        line=line,
        event_type="text",
        role=None,
        content=redact(text),
        command=redact(command) if command else None,
    )


def _extract_content(obj: dict[str, Any]) -> str:
    for key in ("content", "message", "text", "output", "result", "error"):
        if key in obj:
            return _stringify(obj[key])
    return _stringify(obj)


def _extract_command(obj: dict[str, Any]) -> str | None:
    for key in ("command", "cmd", "shell_command"):
        value = obj.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    for key in ("args", "arguments", "input", "parameters"):
        value = obj.get(key)
        if isinstance(value, dict):
            for command_key in ("command", "cmd", "shell_command"):
                command = value.get(command_key)
                if isinstance(command, str) and command.strip():
                    return command.strip()
        elif isinstance(value, str) and _looks_like_shell_tool(obj):
            return value.strip()

    return None


def _looks_like_shell_tool(obj: dict[str, Any]) -> bool:
    text = " ".join(str(obj.get(key, "")) for key in ("tool", "name", "type", "event"))
    return bool(re.search(r"(?i)\b(shell|bash|powershell|cmd|terminal|exec)\b", text))


def _extract_inline_command(text: str) -> str | None:
    match = re.search(r"(?i)\b(command|cmd|shell)\s*:\s*(.+)$", text)
    if match:
        return match.group(2).strip()
    return None


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_stringify(item) for item in value)
    if isinstance(value, dict):
        for key in ("content", "text", "message"):
            if key in value:
                return _stringify(value[key])
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def redact(text: str | None) -> str:
    if not text:
        return ""
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted

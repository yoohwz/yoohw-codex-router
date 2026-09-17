from __future__ import annotations

import re
from pathlib import Path

from .errors import TaskError

_FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 /_-]*):\s*(.+?)\s*$")


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def unique_fields(body: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _normalize(body).splitlines():
        match = _FIELD_RE.match(line.strip())
        if not match:
            continue
        key, value = match.groups()
        if key in values:
            raise TaskError(f"TASK_METADATA_REQUIRED: duplicate field {key!r}")
        values[key] = value
    return values


def top_level_fields(text: str) -> dict[str, str]:
    lines = []
    for line in _normalize(text).splitlines():
        if line.startswith("## "):
            break
        lines.append(line)
    return unique_fields("\n".join(lines))


def section_body(text: str, heading: str) -> str | None:
    lines = _normalize(text).splitlines()
    wanted = f"## {heading}"
    start = None
    for index, line in enumerate(lines):
        if line.strip() == wanted:
            if start is not None:
                raise TaskError(f"TASK_METADATA_REQUIRED: duplicate section {heading!r}")
            start = index + 1
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip("\n")


def section_fields(text: str, heading: str) -> dict[str, str]:
    body = section_body(text, heading)
    return unique_fields(body) if body is not None else {}


def subsection_body(text: str, parent: str, heading: str) -> str | None:
    body = section_body(text, parent)
    if body is None:
        return None
    lines = body.splitlines()
    wanted = f"### {heading}"
    start = None
    for index, line in enumerate(lines):
        if line.strip() == wanted:
            if start is not None:
                raise TaskError(f"TASK_METADATA_REQUIRED: duplicate subsection {heading!r}")
            start = index + 1
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("### "):
            end = index
            break
    return "\n".join(lines[start:end]).strip("\n")


def subsection_fields(text: str, parent: str, heading: str) -> dict[str, str]:
    body = subsection_body(text, parent, heading)
    return unique_fields(body) if body is not None else {}


def bullets_after_label(body: str | None, label: str) -> list[str]:
    if not body:
        return []
    lines = body.splitlines()
    result: list[str] = []
    active = False
    prefix = f"{label}:"
    for line in lines:
        stripped = line.strip()
        if stripped == prefix:
            active = True
            continue
        if active:
            if stripped.startswith("- "):
                result.append(stripped[2:].strip())
                continue
            if not stripped:
                continue
            break
    return result


def find_task_file(repo_root: Path, task_id: str) -> Path:
    task_dir = repo_root / "docs" / "tasks"
    matches = sorted(path for path in task_dir.glob(f"{task_id}-*.md") if path.is_file())
    if len(matches) != 1:
        raise TaskError(
            f"TASK_DISCOVERY_REQUIRED: expected exactly one {task_id}-*.md in {task_dir}, found {len(matches)}"
        )
    return matches[0]

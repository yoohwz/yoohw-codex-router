from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import RouterError
from .render import render_compact, render_json, render_text
from .router import route


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yoohw-profile",
        description="Read-only Codex model/effort advisor for YoOhw repositories.",
    )
    parser.add_argument("task", nargs="?", help="Task ID such as BM-0152 or AOA-0023; inferred from branch when omitted")
    parser.add_argument("--repo", default=".", help="Target product repository path (default: current directory)")
    parser.add_argument("--task-file", help="Explicit task file path inside the target repository")
    parser.add_argument("--review", action="store_true", help="Route the independent technical-review phase")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Emit structured JSON")
    output.add_argument("--compact", action="store_true", help="Emit only MODEL / EFFORT or NO_CODEX_ACTION")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rec = route(Path(args.repo), args.task, review=args.review, task_file=args.task_file)
    except RouterError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(render_json(rec))
    elif args.compact:
        print(render_compact(rec))
    else:
        print(render_text(rec))
    return 0

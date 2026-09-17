from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import RepositoryError


@dataclass(frozen=True)
class RepoContext:
    root: Path
    repository: str
    branch: str | None


def _run_git(path: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(path), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise RepositoryError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def normalize_origin(value: str) -> str:
    value = value.strip()
    for prefix in ("https://github.com/", "git@github.com:", "ssh://git@github.com/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    if value.endswith(".git"):
        value = value[:-4]
    if value.count("/") != 1:
        raise RepositoryError(f"SOURCE_ROOT_MISMATCH: unsupported GitHub origin {value!r}")
    return value


def discover_repo(path: str | Path) -> RepoContext:
    requested = Path(path).expanduser().resolve()
    try:
        root = Path(_run_git(requested, "rev-parse", "--show-toplevel")).resolve()
        origin = normalize_origin(_run_git(root, "remote", "get-url", "origin"))
        branch = _run_git(root, "symbolic-ref", "--short", "-q", "HEAD") or None
    except RepositoryError:
        # Useful for fixtures and source archives. Production use should normally be a Git checkout.
        root = requested
        origin = f"local/{root.name}"
        branch = None
    return RepoContext(root=root, repository=origin, branch=branch)


def infer_task_from_branch(branch: str | None) -> str | None:
    if not branch:
        return None
    match = re.search(r"(?:^|/)(bm|aoa)-([0-9]{4})(?:-|$)", branch, re.I)
    if not match:
        return None
    return f"{match.group(1).upper()}-{match.group(2)}"

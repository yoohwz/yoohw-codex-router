from __future__ import annotations

from pathlib import Path

from .adapters import AOAAdapter, BlacklistManagerAdapter
from .errors import RepositoryError, TaskError
from .markdown import find_task_file
from .model import Recommendation
from .repo import RepoContext, discover_repo, infer_task_from_branch

_ADAPTERS = (BlacklistManagerAdapter(), AOAAdapter())


def _adapter_for(context: RepoContext):
    repo_name = context.repository.rsplit("/", 1)[-1]
    if context.repository.startswith("local/"):
        repo_name = context.root.name
    for adapter in _ADAPTERS:
        if repo_name in adapter.repo_names:
            return adapter
    raise RepositoryError(
        f"UNSUPPORTED_REPOSITORY: {context.repository}; MVP supports Blacklist Manager and Advanced Order Actions"
    )


def route(
    repo_path: str | Path,
    task_id: str | None = None,
    *,
    review: bool = False,
    task_file: str | Path | None = None,
) -> Recommendation:
    context = discover_repo(repo_path)
    task_id = task_id or infer_task_from_branch(context.branch)
    if not task_id:
        raise TaskError("TASK_DISCOVERY_REQUIRED: provide a task ID or use a BM/AOA task branch")
    task_id = task_id.upper()
    adapter = _adapter_for(context)

    if task_file:
        file_path = Path(task_file).expanduser()
        if not file_path.is_absolute():
            file_path = context.root / file_path
        file_path = file_path.resolve()
        try:
            file_path.relative_to(context.root)
        except ValueError as exc:
            raise TaskError("TASK_DISCOVERY_REQUIRED: --task-file must stay inside the target repository") from exc
        if not file_path.is_file():
            raise TaskError(f"TASK_DISCOVERY_REQUIRED: task file not found: {file_path}")
    else:
        file_path = find_task_file(context.root, task_id)

    text = file_path.read_text(encoding="utf-8")
    result = adapter.route(context.root, task_id, text, review)
    result.warnings.append(f"Task source: {file_path.relative_to(context.root)}")
    if context.repository.startswith("local/"):
        result.warnings.append("Git origin was not observable; repository identity fell back to the directory name.")
    return result

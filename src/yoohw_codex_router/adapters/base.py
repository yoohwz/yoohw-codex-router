from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from ..model import Recommendation


class Adapter(ABC):
    name: str
    repo_names: tuple[str, ...]

    @abstractmethod
    def route(self, repo_root: Path, task_id: str, task_text: str, review: bool) -> Recommendation:
        raise NotImplementedError

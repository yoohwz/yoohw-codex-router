from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Profile:
    model: str
    effort: str

    def display(self) -> str:
        return f"{self.model} / {self.effort.upper()}"


@dataclass
class Recommendation:
    repository: str
    task_id: str
    adapter: str
    lane: str
    phase: str
    authority_source: str
    launchable: bool
    profile: Optional[Profile]
    reasons: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    escalation: Optional[Profile] = None
    escalate_when: list[str] = field(default_factory=list)
    downgrade: Optional[Profile] = None
    downgrade_when: list[str] = field(default_factory=list)
    review_floor: Optional[Profile] = None

    def to_dict(self) -> dict:
        raw = asdict(self)
        raw["profile"] = asdict(self.profile) if self.profile else None
        raw["escalation"] = asdict(self.escalation) if self.escalation else None
        raw["downgrade"] = asdict(self.downgrade) if self.downgrade else None
        raw["review_floor"] = asdict(self.review_floor) if self.review_floor else None
        return raw

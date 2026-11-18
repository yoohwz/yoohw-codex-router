from __future__ import annotations

import json

from .model import Recommendation


def render_json(rec: Recommendation) -> str:
    return json.dumps(rec.to_dict(), indent=2, sort_keys=True)


def render_compact(rec: Recommendation) -> str:
    if not rec.launchable or not rec.profile:
        return "NO_CODEX_ACTION"
    return rec.profile.display()


def _items(title: str, values: list[str]) -> list[str]:
    if not values:
        return []
    lines = ["", title]
    lines.extend(f"- {value}" for value in values)
    return lines


def render_text(rec: Recommendation) -> str:
    lines = [
        "YoOhw Codex Profile Advisor",
        "",
        f"Repository: {rec.repository}",
        f"Task: {rec.task_id}",
        f"Lane: {rec.lane}",
        f"Phase: {rec.phase}",
        f"Authority: {rec.authority_source}",
        "",
        "----------------------------------------",
    ]
    if rec.launchable and rec.profile:
        lines.extend(
            [
                "SELECT IN CODEX APP",
                f"Model:  {rec.profile.model}",
                f"Effort: {rec.profile.effort.upper()}",
            ]
        )
    else:
        lines.extend(["CODEX ACTION: NONE", "Current authority is at a non-Codex gate."])
    lines.append("----------------------------------------")
    lines.extend(_items("Why", rec.reasons))
    if rec.downgrade:
        lines.extend(["", f"Downgrade target: {rec.downgrade.display()}"])
        lines.extend(_items("Downgrade when", rec.downgrade_when))
    if rec.escalation:
        lines.extend(["", f"Escalation target: {rec.escalation.display()}"])
        lines.extend(_items("Escalate when", rec.escalate_when))
    if rec.review_floor:
        lines.extend(["", f"Independent review floor: {rec.review_floor.display()}"])
    lines.extend(_items("Notes", rec.warnings))
    return "\n".join(lines).rstrip()

from pathlib import Path

from ..errors import PolicyError
from ..markdown import section_body

SOL_MODELS = {
    "GPT-6.1 Sol": "gpt-6.1-sol",
    "GPT-6.2 Sol": "gpt-6.2-sol",
}


def verified_sol_model(policy: Path, heading: str, expected: dict[str, str]) -> str:
    """Read a known policy table, rejecting mixed models and effort drift."""
    if not policy.is_file():
        raise PolicyError(f"PROFILE_REQUIRED: local compute policy is missing: {policy}")

    section = section_body(policy.read_text(encoding="utf-8"), heading) or ""
    profiles: dict[str, list[str]] = {phase: [] for phase in expected}
    for line in section.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line[1:-1].split("|")]
            if len(cells) == 2 and cells[0] in profiles:
                profiles[cells[0]].append(cells[1])

    for label, model in SOL_MODELS.items():
        if all(profiles[phase] == [f"{label} / {effort}"] for phase, effort in expected.items()):
            return model
    raise PolicyError(f"PROFILE_REQUIRED: compute policy no longer matches the verified contract: {policy}")

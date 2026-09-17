from __future__ import annotations

import re
from pathlib import Path

from ..errors import PolicyError, TaskError
from ..markdown import (
    bullets_after_label,
    section_body,
    section_fields,
    subsection_body,
    subsection_fields,
    top_level_fields,
)
from ..model import Profile, Recommendation
from .base import Adapter

LUNA_LOW = Profile("gpt-5.6-luna", "LOW")
TERRA_MEDIUM = Profile("gpt-5.6-terra", "MEDIUM")
SOL_HIGH = Profile("gpt-5.6-sol", "HIGH")
_VALID_EFFORTS = {"LOW", "MEDIUM", "HIGH", "XHIGH"}


class AOAAdapter(Adapter):
    name = "advanced-order-actions"
    repo_names = ("wc-advanced-order-actions",)

    def _qualified_models(self, repo_root: Path) -> dict[str, str]:
        policy_file = repo_root / "docs" / "codex" / "aoa_compute_policy.py"
        if not policy_file.is_file():
            raise PolicyError(
                "PROFILE_REQUIRED: AOA qualified compute policy is missing; the router will not invent model authority"
            )
        text = policy_file.read_text(encoding="utf-8")
        matches = re.findall(
            r'\("(gpt-[^"]+)",\s*"(ECONOMY|STANDARD|DEEP)",\s*True,\s*True,', text
        )
        catalog = dict(matches)
        required = {
            "gpt-5.6-luna": "ECONOMY",
            "gpt-5.6-terra": "STANDARD",
            "gpt-5.6-sol": "DEEP",
        }
        if any(catalog.get(model) != tier for model, tier in required.items()):
            raise PolicyError(
                "PROFILE_REQUIRED: AOA qualified model registry changed; router validation must be updated first"
            )
        return catalog

    @staticmethod
    def _profile(fields: dict[str, str], catalog: dict[str, str], source: str) -> Profile | None:
        if not fields:
            return None
        model = fields.get("Model")
        effort = fields.get("Reasoning effort")
        if not model or not effort:
            raise TaskError(f"TASK_METADATA_REQUIRED: incomplete {source} compute profile")
        effort = effort.upper()
        if model not in catalog or effort not in _VALID_EFFORTS:
            raise PolicyError(f"PROFILE_REQUIRED: unqualified {source} profile {model} / {effort}")
        declared_tier = fields.get("Tier")
        if declared_tier and declared_tier != catalog[model]:
            raise PolicyError(
                f"PROFILE_REQUIRED: {source} tier {declared_tier} contradicts qualified {catalog[model]} for {model}"
            )
        return Profile(model, effort)

    @staticmethod
    def _lane(text: str, top: dict[str, str], launch: dict[str, str], catalog: dict[str, str]) -> str:
        lane = top.get("Execution lane") or top.get("Lane")
        if not lane:
            lane = section_fields(text, "Routing decision").get("Lane")
        if lane:
            return lane
        model = launch.get("Model")
        tier = catalog.get(model or "")
        return {
            "ECONOMY": "CODEX_DIRECT",
            "STANDARD": "STANDARD_AOA",
            "DEEP": "DEEP_AOA",
        }.get(tier, "UNKNOWN")

    def route(self, repo_root: Path, task_id: str, task_text: str, review: bool) -> Recommendation:
        catalog = self._qualified_models(repo_root)
        top = top_level_fields(task_text)
        status = top.get("Status", "UNKNOWN")
        launch = section_fields(task_text, "Codex launch contract")
        lane = self._lane(task_text, top, launch, catalog)

        if lane not in {"CODEX_DIRECT", "STANDARD_AOA", "DEEP_AOA"}:
            raise TaskError(f"TASK_METADATA_REQUIRED: unsupported AOA lane {lane!r}")

        if review:
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="REVIEW",
                authority_source="AOA qualified compute policy review floor",
                launchable=True,
                profile=SOL_HIGH,
                reasons=["AOA independent review requires DEEP/HIGH or expressly approved XHIGH."],
                warnings=["--review advises compute only; it does not create or prove AOA review authority."],
                review_floor=SOL_HIGH,
            )

        if status in {
            "PLAN_REVIEW_REQUIRED",
            "ARCHITECTURE_REVIEW_REQUIRED",
            "ACCEPTANCE_REVIEW_REQUIRED",
            "READY_FOR_HUMAN_GATE",
            "READY_TO_MERGE",
            "MERGED",
            "RELEASED",
            "BLOCKED",
        }:
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="HUMAN_OR_CHATGPT_GATE",
                authority_source="current AOA task status",
                launchable=False,
                profile=None,
                reasons=[f"{status} is not treated as an implementation launch by the advisor."],
                review_floor=SOL_HIGH if lane == "DEEP_AOA" else None,
            )

        explicit = self._profile(launch, catalog, "Codex launch contract")
        baseline_fields = subsection_fields(task_text, "Codex execution policy", "Baseline")
        baseline = self._profile(baseline_fields, catalog, "Baseline")
        if explicit and baseline and baseline != explicit:
            raise PolicyError("PROFILE_REQUIRED: AOA Baseline contradicts the Codex launch contract")
        workflow_mode = launch.get("Workflow mode", "").upper()
        if workflow_mode == "DISCOVERY_ONLY":
            phase = "DISCOVERY"
        elif workflow_mode == "IMPLEMENTATION":
            phase = "IMPLEMENTATION"
        elif "TECHNICAL_REVIEW" in status:
            phase = "REVIEW"
        elif lane == "DEEP_AOA" and status == "READY":
            phase = "DISCOVERY"
        else:
            phase = "IMPLEMENTATION"

        if explicit:
            profile = explicit
            authority = "task Codex launch contract"
            reasons = ["The task's explicit launch contract overrides global/default routing."]
        else:
            authority = "AOA lane/phase fallback within qualified registry"
            if lane == "CODEX_DIRECT":
                profile = LUNA_LOW
            elif lane == "STANDARD_AOA":
                profile = TERRA_MEDIUM
            elif phase == "DISCOVERY":
                profile = SOL_HIGH
            else:
                profile = TERRA_MEDIUM
            reasons = ["No explicit launch contract was found; the advisor used the minimum qualified lane/phase profile."]

        escalation = self._profile(
            subsection_fields(task_text, "Codex execution policy", "Escalation"), catalog, "Escalation"
        )
        downgrade = self._profile(
            subsection_fields(task_text, "Codex execution policy", "Downgrade"), catalog, "Downgrade"
        )
        escalation_body = subsection_body(task_text, "Codex execution policy", "Escalation")
        downgrade_body = subsection_body(task_text, "Codex execution policy", "Downgrade")

        return Recommendation(
            repository=repo_root.name,
            task_id=task_id,
            adapter=self.name,
            lane=lane,
            phase=phase,
            authority_source=authority,
            launchable=True,
            profile=profile,
            reasons=reasons,
            escalation=escalation,
            escalate_when=bullets_after_label(escalation_body, "Triggers"),
            downgrade=downgrade,
            downgrade_when=bullets_after_label(downgrade_body, "Allowed when"),
            review_floor=SOL_HIGH if lane == "DEEP_AOA" else None,
        )

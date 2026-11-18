from __future__ import annotations

from pathlib import Path

from ..errors import PolicyError, TaskError
from ..markdown import section_fields, subsection_fields, top_level_fields
from ..model import Profile, Recommendation
from .base import Adapter
from .compute import verified_sol_model


class AOAAdapter(Adapter):
    name = "advanced-order-actions"
    repo_names = ("wc-advanced-order-actions",)

    _PHASE_EFFORTS = {
        "Root orchestration": "MEDIUM",
        "Fast implementation": "MEDIUM",
        "Controlled deterministic implementation after boundary settlement": "MEDIUM",
        "In-scope correction of current findings": "MEDIUM",
        "Optional read-only support subagent": "MEDIUM",
        "Optional complex technical discovery": "HIGH when justified",
        "Fresh independent Controlled Technical Review or re-review": "HIGH",
    }
    _NON_EXECUTION = {
        "PLAN_REVIEW_REQUIRED", "ARCHITECTURE_REVIEW_REQUIRED", "ACCEPTANCE_REVIEW_REQUIRED",
        "HUMAN_DECISION_REQUIRED", "READY_FOR_HUMAN_GATE", "READY_FOR_HUMAN_MERGE", "READY_TO_MERGE",
        "MERGED", "RELEASED", "BLOCKED", "HUMAN_PAUSED", "NOT_READY_BLOCKED_PROVIDER_SETTLEMENT",
    }
    _IMPLEMENTATION = {"READY", "IMPLEMENTING"}
    _CORRECTION = {"CHANGES_REQUIRED", "TECHNICAL_CHANGES_REQUIRED", "TECHNICAL_REVIEW_FAIL"}

    def route(self, repo_root: Path, task_id: str, task_text: str, review: bool) -> Recommendation:
        model = verified_sol_model(
            repo_root / "docs" / "workflow.md", "Compute and delegation", self._PHASE_EFFORTS
        )
        top = top_level_fields(task_text)
        if top.get("Task-ID", task_id).upper() != task_id:
            raise TaskError(f"TASK_METADATA_REQUIRED: AOA Task-ID does not match {task_id}")
        lanes = {
            top[key].strip("*").strip().title() for key in ("Risk", "Risk lane", "Lane", "Execution lane")
            if key in top
        }
        if lanes not in ({"Fast"}, {"Controlled"}):
            raise TaskError("TASK_METADATA_REQUIRED: AOA requires a consistent Fast or Controlled risk lane")
        lane = lanes.pop()
        status = top.get("Status", "").upper()
        medium = Profile(model, "MEDIUM")
        high = Profile(model, "HIGH")
        review_floor = high if lane == "Controlled" else None

        if status in self._NON_EXECUTION:
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="HUMAN_OR_CHATGPT_GATE",
                authority_source="current AOA task status",
                launchable=False,
                profile=None,
                reasons=[f"{status} requires the task's existing handoff or hold to be resolved."],
                review_floor=review_floor,
            )

        if status not in self._IMPLEMENTATION | self._CORRECTION | {"TECHNICAL_REVIEW_REQUIRED"}:
            raise TaskError(f"TASK_NOT_READY: unsupported or missing AOA status {status!r}")

        if review or status == "TECHNICAL_REVIEW_REQUIRED":
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="REVIEW",
                authority_source="AOA workflow independent review profile",
                launchable=True,
                profile=high,
                reasons=["Fresh independent Controlled Technical Review or re-review uses Sol/HIGH."],
                warnings=["This recommendation does not establish reviewer independence or freeze a candidate."],
                review_floor=high,
            )

        launch = section_fields(task_text, "Codex launch contract")
        mode = launch.get("Workflow mode", "").upper()
        if mode not in {"", "DISCOVERY_ONLY", "IMPLEMENTATION"}:
            raise TaskError(f"TASK_METADATA_REQUIRED: unsupported AOA workflow mode {mode!r}")
        discovery = mode == "DISCOVERY_ONLY"
        phase = "DISCOVERY" if discovery else "CORRECTION" if status in self._CORRECTION else "IMPLEMENTATION"
        profile = high if discovery else medium
        authority = "AOA workflow phase default"
        baseline = subsection_fields(task_text, "Codex execution policy", "Baseline")
        if launch and baseline and (
            baseline.get("Model") != launch.get("Model")
            or baseline.get("Reasoning effort", "").upper() != launch.get("Reasoning effort", "").upper()
        ):
            raise PolicyError("PROFILE_REQUIRED: AOA Baseline contradicts the Codex launch contract")
        if launch:
            effort = launch.get("Reasoning effort", "").upper()
            # Current workflow names Sol and treats XHIGH as an explicit exception.
            if launch.get("Model") != model or effort not in {"MEDIUM", "HIGH", "XHIGH"}:
                raise PolicyError("PROFILE_REQUIRED: explicit AOA profile does not match the verified workflow")
            if discovery and effort == "MEDIUM":
                raise PolicyError("PROFILE_REQUIRED: complex AOA discovery uses at least HIGH")
            if effort == "XHIGH" and not launch.get("Escalation reason"):
                raise PolicyError("PROFILE_REQUIRED: AOA XHIGH needs a specific unresolved technical reason")
            profile = Profile(model, effort)
            authority = "task Codex launch contract + AOA workflow"

        return Recommendation(
            repository=repo_root.name,
            task_id=task_id,
            adapter=self.name,
            lane=lane,
            phase=phase,
            authority_source=authority,
            launchable=True,
            profile=profile,
            reasons=["AOA selects effort by the current phase and specific unresolved technical work."],
            escalation=high if profile == medium else None,
            escalate_when=["A specific unresolved technical boundary justifies optional complex discovery."] if profile == medium else [],
            downgrade=medium if discovery else None,
            downgrade_when=["The boundary is settled and deterministic implementation or correction is authorized."] if discovery else [],
            review_floor=review_floor,
        )

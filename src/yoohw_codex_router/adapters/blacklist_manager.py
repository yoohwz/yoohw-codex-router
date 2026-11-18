from __future__ import annotations

import os
from pathlib import Path

from ..errors import TaskError
from ..markdown import top_level_fields
from ..model import Profile, Recommendation
from .base import Adapter
from .compute import verified_sol_model


class BlacklistManagerAdapter(Adapter):
    name = "blacklist-manager"
    repo_names = (
        "wc-blacklist-manager",
        "wc-blacklist-manager-premium",
        "yoohw-global-blacklist-server",
    )

    _PHASE_EFFORTS = {
        "Desktop Main Agent / Root for governed native orchestration": "MEDIUM",
        "`STANDARD_BM` implementation": "MEDIUM",
        "`DEEP_BM` Discovery/Architecture": "HIGH",
        "`DEEP_BM` deterministic implementation and correction after architecture is settled": "MEDIUM",
        "`DEEP_BM` independent technical review, including every fresh re-review": "HIGH",
    }

    def _policy_model(self, repo_root: Path) -> str:
        relative = Path("docs/CODEX-EXECUTION-PROFILES.md")
        local = repo_root / relative
        if local.is_file() and "Canonical compute policy is Core-hosted and lane-based:" not in local.read_text(
            encoding="utf-8"
        ):
            return verified_sol_model(local, "Defaults", self._PHASE_EFFORTS)

        # Premium's local document points to Core. Global uses Core directly.
        core_env = os.environ.get("BM_CORE_DIR")
        core = Path(core_env).expanduser() if core_env else repo_root.parent / "wc-blacklist-manager"
        return verified_sol_model(core / relative, "Defaults", self._PHASE_EFFORTS)

    def route(self, repo_root: Path, task_id: str, task_text: str, review: bool) -> Recommendation:
        model = self._policy_model(repo_root)
        sol_medium = Profile(model, "MEDIUM")
        sol_high = Profile(model, "HIGH")
        fields = top_level_fields(task_text)
        declared_task = fields.get("Task-ID")
        if declared_task and declared_task != task_id:
            raise TaskError(f"TASK_METADATA_REQUIRED: Task-ID {declared_task!r} != requested {task_id!r}")
        lane = fields.get("Lane")
        status = fields.get("Status")
        if lane not in {"STANDARD_BM", "DEEP_BM"}:
            raise TaskError(f"TASK_METADATA_REQUIRED: unsupported or missing Lane: {lane!r}")
        if not status:
            raise TaskError("TASK_METADATA_REQUIRED: Status missing")

        if review:
            if status != "TECHNICAL_REVIEW_REQUIRED":
                raise TaskError(
                    f"TASK_NOT_READY: --review requires TECHNICAL_REVIEW_REQUIRED, found {status}"
                )
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="REVIEW",
                authority_source="BM canonical compute policy + current task status",
                launchable=True,
                profile=sol_high,
                reasons=["Independent Blacklist Manager technical review has a Sol/HIGH floor."],
                review_floor=sol_high,
            )

        no_run = {
            "PLAN_REVIEW_REQUIRED",
            "ACCEPTANCE_REVIEW_REQUIRED",
            "READY_TO_MERGE",
            "BLOCKED",
        }
        if status in no_run:
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="HUMAN_OR_CHATGPT_GATE",
                authority_source="current task status",
                launchable=False,
                profile=None,
                reasons=[f"{status} is not a Codex execution state under the canonical BM workflow."],
                review_floor=sol_high if lane == "DEEP_BM" else None,
            )
        if status == "TECHNICAL_REVIEW_REQUIRED":
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="REVIEW",
                authority_source="BM canonical compute policy + current task status",
                launchable=True,
                profile=sol_high,
                reasons=["The next executable phase is Independent Technical Review."],
                review_floor=sol_high,
            )
        if status not in {"READY", "IMPLEMENTING", "CHANGES_REQUIRED"}:
            raise TaskError(f"TASK_NOT_READY: unsupported BM status {status!r}")

        if lane == "DEEP_BM" and status == "READY":
            return Recommendation(
                repository=repo_root.name,
                task_id=task_id,
                adapter=self.name,
                lane=lane,
                phase="DISCOVERY",
                authority_source="BM canonical compute policy + lane/status",
                launchable=True,
                profile=sol_high,
                reasons=["Deep READY work performs Discovery/Architecture before implementation."],
                downgrade=sol_medium,
                downgrade_when=[
                    "The authorized workflow has settled the architecture/boundary and permits implementation.",
                    "No unresolved Deep semantic decision remains in the implementation phase.",
                ],
                review_floor=sol_high,
            )

        phase = "CORRECTION" if status == "CHANGES_REQUIRED" else "IMPLEMENTATION"
        reasons = [
            "Standard BM execution defaults to Sol/MEDIUM."
            if lane == "STANDARD_BM"
            else "Deep implementation may downgrade to Sol/MEDIUM after the architecture/boundary is settled."
        ]
        return Recommendation(
            repository=repo_root.name,
            task_id=task_id,
            adapter=self.name,
            lane=lane,
            phase=phase,
            authority_source="BM canonical compute policy + lane/status",
            launchable=True,
            profile=sol_medium,
            reasons=reasons,
            escalation=sol_high,
            escalate_when=[
                "security/auth/payment/licensing/privacy/persistence/concurrency semantics become unresolved",
                "a compatibility-sensitive shared contract or architecture boundary becomes ambiguous",
                "the approved implementation boundary no longer fits repository evidence",
            ],
            review_floor=sol_high if lane == "DEEP_BM" else None,
        )

from __future__ import annotations

import os
from pathlib import Path

from ..errors import PolicyError, TaskError
from ..markdown import top_level_fields
from ..model import Profile, Recommendation
from .base import Adapter

TERRA_MEDIUM = Profile("gpt-5.6-terra", "MEDIUM")
SOL_HIGH = Profile("gpt-5.6-sol", "HIGH")


class BlacklistManagerAdapter(Adapter):
    name = "blacklist-manager"
    repo_names = (
        "wc-blacklist-manager",
        "wc-blacklist-manager-premium",
        "yoohw-global-blacklist-server",
    )

    _POLICY_MARKERS = (
        "`STANDARD_BM` | GPT-5.6 Terra / MEDIUM",
        "`DEEP_BM` Discovery/Architecture | GPT-5.6 Sol / HIGH",
        "`DEEP_BM` deterministic implementation after architecture is settled | GPT-5.6 Terra / MEDIUM when appropriate",
        "`DEEP_BM` independent technical review | GPT-5.6 Sol / HIGH",
    )

    def _verify_policy(self, repo_root: Path) -> Path:
        # Core owns the canonical compute policy. Cross-repository BM tasks may be
        # launched from Premium/Global, so resolve a local Core checkout without
        # performing network discovery.
        candidates = [repo_root / "docs" / "CODEX-EXECUTION-PROFILES.md"]
        core_env = os.environ.get("BM_CORE_DIR")
        if core_env:
            candidates.append(Path(core_env).expanduser() / "docs" / "CODEX-EXECUTION-PROFILES.md")
        candidates.append(repo_root.parent / "wc-blacklist-manager" / "docs" / "CODEX-EXECUTION-PROFILES.md")
        policy = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
        if policy is None:
            raise PolicyError(
                "PROFILE_REQUIRED: canonical BM docs/CODEX-EXECUTION-PROFILES.md was not found locally; "
                "set BM_CORE_DIR or keep the Core checkout beside this repository"
            )
        text = policy.read_text(encoding="utf-8")
        missing = [marker for marker in self._POLICY_MARKERS if marker not in text]
        if missing:
            raise PolicyError(
                "PROFILE_REQUIRED: Blacklist Manager compute policy no longer matches the router's verified contract"
            )
        return policy

    def route(self, repo_root: Path, task_id: str, task_text: str, review: bool) -> Recommendation:
        policy_path = self._verify_policy(repo_root)
        fields = top_level_fields(task_text)
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
                profile=SOL_HIGH,
                reasons=["Independent Blacklist Manager technical review has a Sol/HIGH floor."],
                review_floor=SOL_HIGH,
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
                review_floor=SOL_HIGH if lane == "DEEP_BM" else None,
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
                profile=SOL_HIGH,
                reasons=["The next executable phase is Independent Technical Review."],
                review_floor=SOL_HIGH,
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
                profile=SOL_HIGH,
                reasons=["Deep READY work performs Discovery/Architecture before implementation."],
                downgrade=TERRA_MEDIUM,
                downgrade_when=[
                    "ChatGPT has settled the architecture/boundary and task status advances to IMPLEMENTING.",
                    "No unresolved Deep semantic decision remains in the implementation phase.",
                ],
                review_floor=SOL_HIGH,
            )

        phase = "CORRECTION" if status == "CHANGES_REQUIRED" else "IMPLEMENTATION"
        reasons = [
            "Standard BM execution defaults to Terra/MEDIUM."
            if lane == "STANDARD_BM"
            else "Deep implementation may downgrade to Terra/MEDIUM after the architecture/boundary is settled."
        ]
        return Recommendation(
            repository=repo_root.name,
            task_id=task_id,
            adapter=self.name,
            lane=lane,
            phase=phase,
            authority_source="BM canonical compute policy + lane/status",
            launchable=True,
            profile=TERRA_MEDIUM,
            reasons=reasons,
            escalation=SOL_HIGH,
            escalate_when=[
                "security/auth/payment/licensing/privacy/persistence/concurrency semantics become unresolved",
                "a compatibility-sensitive shared contract or architecture boundary becomes ambiguous",
                "the approved implementation boundary no longer fits repository evidence",
            ],
            review_floor=SOL_HIGH if lane == "DEEP_BM" else None,
        )

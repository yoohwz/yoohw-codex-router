import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from yoohw_codex_router.adapters.blacklist_manager import BlacklistManagerAdapter
from yoohw_codex_router.errors import PolicyError, TaskError


POLICY = """# Codex Execution Policy

## Defaults

| Work | Default |
| --- | --- |
| Desktop Main Agent / Root for governed native orchestration | GPT-6.2 Sol / MEDIUM |
| `STANDARD_BM` implementation | GPT-6.2 Sol / MEDIUM |
| `DEEP_BM` Discovery/Architecture | GPT-6.2 Sol / HIGH |
| `DEEP_BM` deterministic implementation and correction after architecture is settled | GPT-6.2 Sol / MEDIUM |
| `DEEP_BM` independent technical review, including every fresh re-review | GPT-6.2 Sol / HIGH |
"""


def task(lane, status):
    return f"""# Task\n\nTask-ID: BM-0152\nLane: {lane}\nScope: CORE_ONLY\nStatus: {status}\n\n## Mission\nTest.\n"""


class BlacklistManagerAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "wc-blacklist-manager"
        (self.root / "docs").mkdir(parents=True)
        (self.root / "docs" / "CODEX-EXECUTION-PROFILES.md").write_text(POLICY)
        self.adapter = BlacklistManagerAdapter()

    def tearDown(self):
        self.temp.cleanup()

    def test_standard_ready_is_sol_medium(self):
        rec = self.adapter.route(self.root, "BM-0152", task("STANDARD_BM", "READY"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "MEDIUM"))
        self.assertEqual(rec.phase, "IMPLEMENTATION")

    def test_deep_ready_is_sol_high(self):
        rec = self.adapter.route(self.root, "BM-0152", task("DEEP_BM", "READY"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "HIGH"))
        self.assertEqual(rec.phase, "DISCOVERY")
        self.assertEqual(rec.downgrade.model, "gpt-6.2-sol")

    def test_deep_implementation_downgrades_to_sol_medium(self):
        rec = self.adapter.route(self.root, "BM-0152", task("DEEP_BM", "IMPLEMENTING"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "MEDIUM"))
        self.assertEqual(rec.review_floor.model, "gpt-6.2-sol")

    def test_technical_review_is_sol_high(self):
        rec = self.adapter.route(
            self.root, "BM-0152", task("DEEP_BM", "TECHNICAL_REVIEW_REQUIRED"), True
        )
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "HIGH"))
        self.assertEqual(rec.phase, "REVIEW")

    def test_review_fails_when_task_not_ready(self):
        with self.assertRaises(TaskError):
            self.adapter.route(self.root, "BM-0152", task("DEEP_BM", "IMPLEMENTING"), True)

    def test_acceptance_gate_has_no_codex_action(self):
        rec = self.adapter.route(
            self.root, "BM-0152", task("DEEP_BM", "ACCEPTANCE_REVIEW_REQUIRED"), False
        )
        self.assertFalse(rec.launchable)
        self.assertIsNone(rec.profile)

    def test_policy_drift_fails_closed(self):
        (self.root / "docs" / "CODEX-EXECUTION-PROFILES.md").write_text("changed")
        with self.assertRaises(PolicyError):
            self.adapter.route(self.root, "BM-0152", task("STANDARD_BM", "READY"), False)

    def test_reads_previous_model_during_rollout(self):
        policy = self.root / "docs" / "CODEX-EXECUTION-PROFILES.md"
        policy.write_text(POLICY.replace("GPT-6.2 Sol", "GPT-6.1 Sol"))
        rec = self.adapter.route(self.root, "BM-0152", task("DEEP_BM", "READY"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.1-sol", "HIGH"))

    def test_premium_policy_pointer_resolves_sibling_core(self):
        premium = self.root.parent / "wc-blacklist-manager-premium"
        (premium / "docs").mkdir(parents=True)
        (premium / "docs" / "CODEX-EXECUTION-PROFILES.md").write_text(
            "Canonical compute policy is Core-hosted and lane-based:"
        )
        with patch.dict("os.environ", {"BM_CORE_DIR": ""}):
            rec = self.adapter.route(premium, "BM-0152", task("STANDARD_BM", "READY"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "MEDIUM"))

    def test_review_effort_drift_fails_closed(self):
        policy = self.root / "docs" / "CODEX-EXECUTION-PROFILES.md"
        policy.write_text(POLICY.replace(
            "re-review | GPT-6.2 Sol / HIGH", "re-review | GPT-6.2 Sol / MEDIUM"
        ))
        with self.assertRaises(PolicyError):
            self.adapter.route(self.root, "BM-0152", task("DEEP_BM", "TECHNICAL_REVIEW_REQUIRED"), True)

    def test_task_id_mismatch_fails_closed(self):
        with self.assertRaises(TaskError):
            self.adapter.route(self.root, "BM-9999", task("STANDARD_BM", "READY"), False)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from yoohw_codex_router.adapters.blacklist_manager import BlacklistManagerAdapter
from yoohw_codex_router.errors import PolicyError, TaskError


POLICY = """# Codex Execution Policy

| Work | Default |
| --- | --- |
| `STANDARD_BM` | GPT-5.6 Terra / MEDIUM |
| `DEEP_BM` Discovery/Architecture | GPT-5.6 Sol / HIGH |
| `DEEP_BM` deterministic implementation after architecture is settled | GPT-5.6 Terra / MEDIUM when appropriate |
| `DEEP_BM` independent technical review | GPT-5.6 Sol / HIGH |
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

    def test_standard_ready_is_terra_medium(self):
        rec = self.adapter.route(self.root, "BM-0152", task("STANDARD_BM", "READY"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-5.6-terra", "MEDIUM"))
        self.assertEqual(rec.phase, "IMPLEMENTATION")

    def test_deep_ready_is_sol_high(self):
        rec = self.adapter.route(self.root, "BM-0152", task("DEEP_BM", "READY"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-5.6-sol", "HIGH"))
        self.assertEqual(rec.phase, "DISCOVERY")
        self.assertEqual(rec.downgrade.model, "gpt-5.6-terra")

    def test_deep_implementation_downgrades_to_terra_medium(self):
        rec = self.adapter.route(self.root, "BM-0152", task("DEEP_BM", "IMPLEMENTING"), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-5.6-terra", "MEDIUM"))
        self.assertEqual(rec.review_floor.model, "gpt-5.6-sol")

    def test_technical_review_is_sol_high(self):
        rec = self.adapter.route(
            self.root, "BM-0152", task("DEEP_BM", "TECHNICAL_REVIEW_REQUIRED"), True
        )
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-5.6-sol", "HIGH"))
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

    def test_task_id_mismatch_fails_closed(self):
        with self.assertRaises(TaskError):
            self.adapter.route(self.root, "BM-9999", task("STANDARD_BM", "READY"), False)


if __name__ == "__main__":
    unittest.main()

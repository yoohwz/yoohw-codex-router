import tempfile
import unittest
from pathlib import Path

from yoohw_codex_router.adapters.aoa import AOAAdapter
from yoohw_codex_router.errors import PolicyError


POLICY = '''MODELS = (\n    ("gpt-5.6-luna", "ECONOMY", True, True, tuple(), 1),\n    ("gpt-5.6-terra", "STANDARD", True, True, tuple(), 2),\n    ("gpt-5.6-sol", "DEEP", True, True, tuple(), 3),\n)\n'''


def task(model="gpt-5.6-terra", effort="MEDIUM", lane="STANDARD_AOA", status="IMPLEMENTING"):
    tier = {
        "gpt-5.6-luna": "ECONOMY",
        "gpt-5.6-terra": "STANDARD",
        "gpt-5.6-sol": "DEEP",
    }.get(model, "DEEP")
    return f"""# AOA task\n\nStatus: {status}\nExecution lane: {lane}\n\n## Codex launch contract\n\nModel: {model}\nReasoning effort: {effort}\nProfile source: BASELINE\nIntent: RUN\nWorkflow mode: IMPLEMENTATION\n\n## Codex execution policy\n\n### Baseline\n\nTier: {tier}\nModel: {model}\nReasoning effort: {effort}\n\n### Escalation\n\nTier: DEEP\nModel: gpt-5.6-sol\nReasoning effort: HIGH\nTriggers:\n- architecture becomes unresolved\n- public contract changes\n\n### Downgrade\n\nTier: ECONOMY\nModel: gpt-5.6-luna\nReasoning effort: LOW\nAllowed when:\n- only mechanical evidence remains\n"""


class AOAAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "wc-advanced-order-actions"
        (self.root / "docs" / "codex").mkdir(parents=True)
        (self.root / "docs" / "codex" / "aoa_compute_policy.py").write_text(POLICY)
        self.adapter = AOAAdapter()

    def tearDown(self):
        self.temp.cleanup()

    def test_explicit_launch_contract_wins(self):
        rec = self.adapter.route(self.root, "AOA-0010", task(), False)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-5.6-terra", "MEDIUM"))
        self.assertEqual(rec.authority_source, "task Codex launch contract")
        self.assertEqual(rec.escalation.model, "gpt-5.6-sol")
        self.assertEqual(rec.downgrade.model, "gpt-5.6-luna")
        self.assertIn("architecture becomes unresolved", rec.escalate_when)

    def test_deep_explicit_sol_high_is_preserved(self):
        rec = self.adapter.route(
            self.root,
            "AOA-0023",
            task(model="gpt-5.6-sol", effort="HIGH", lane="DEEP_AOA"),
            False,
        )
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-5.6-sol", "HIGH"))

    def test_review_floor_is_sol_high(self):
        rec = self.adapter.route(self.root, "AOA-0023", task(lane="DEEP_AOA"), True)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-5.6-sol", "HIGH"))
        self.assertEqual(rec.phase, "REVIEW")

    def test_human_gate_has_no_codex_action(self):
        rec = self.adapter.route(
            self.root, "AOA-0010", task(status="READY_FOR_HUMAN_GATE"), False
        )
        self.assertFalse(rec.launchable)
        self.assertIsNone(rec.profile)

    def test_unknown_model_fails_closed(self):
        with self.assertRaises(PolicyError):
            self.adapter.route(
                self.root,
                "AOA-9999",
                task(model="gpt-future", effort="HIGH", lane="DEEP_AOA"),
                False,
            )

    def test_baseline_must_match_launch_contract(self):
        text = task().replace(
            "### Baseline\n\nTier: STANDARD\nModel: gpt-5.6-terra\nReasoning effort: MEDIUM",
            "### Baseline\n\nTier: DEEP\nModel: gpt-5.6-sol\nReasoning effort: HIGH",
        )
        with self.assertRaises(PolicyError):
            self.adapter.route(self.root, "AOA-0010", text, False)


if __name__ == "__main__":
    unittest.main()

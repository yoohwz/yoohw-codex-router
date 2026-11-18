import tempfile
import unittest
from pathlib import Path

from yoohw_codex_router.adapters.aoa import AOAAdapter
from yoohw_codex_router.errors import PolicyError, TaskError


WORKFLOW = """# AOA workflow

## Compute and delegation

| Phase | Default compute |
| --- | --- |
| Root orchestration | GPT-6.2 Sol / MEDIUM |
| Fast implementation | GPT-6.2 Sol / MEDIUM |
| Controlled deterministic implementation after boundary settlement | GPT-6.2 Sol / MEDIUM |
| In-scope correction of current findings | GPT-6.2 Sol / MEDIUM |
| Optional read-only support subagent | GPT-6.2 Sol / MEDIUM |
| Optional complex technical discovery | GPT-6.2 Sol / HIGH when justified |
| Fresh independent Controlled Technical Review or re-review | GPT-6.2 Sol / HIGH |
"""


def task(lane="Controlled", status="IMPLEMENTING", extra=""):
    return f"# AOA Issue 269\n\nTask-ID: AOA-269\nRisk lane: {lane}\nStatus: {status}\n{extra}"


def launch(model="gpt-6.2-sol", effort="HIGH", mode="DISCOVERY_ONLY", reason=""):
    return (
        f"\n## Codex launch contract\n\nModel: {model}\nReasoning effort: {effort}\n"
        f"Workflow mode: {mode}\n{reason}"
    )


class AOAAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "wc-advanced-order-actions"
        (self.root / "docs").mkdir(parents=True)
        self.policy = self.root / "docs" / "workflow.md"
        self.policy.write_text(WORKFLOW)
        self.adapter = AOAAdapter()

    def route(self, text, review=False):
        return self.adapter.route(self.root, "AOA-269", text, review)

    def test_implementation_and_correction_are_sol_medium(self):
        for lane, status, phase in (
            ("Fast", "READY", "IMPLEMENTATION"),
            ("Controlled", "IMPLEMENTING", "IMPLEMENTATION"),
            ("Controlled", "TECHNICAL_CHANGES_REQUIRED", "CORRECTION"),
        ):
            with self.subTest(lane=lane, status=status):
                rec = self.route(task(lane, status))
                self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "MEDIUM"))
                self.assertEqual(rec.phase, phase)
                self.assertEqual(rec.escalation.effort, "HIGH")

    def test_explicit_discovery_is_sol_high_and_downgrades_to_medium(self):
        rec = self.route(task(extra=launch()))
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "HIGH"))
        self.assertEqual(rec.phase, "DISCOVERY")
        self.assertEqual(rec.downgrade.effort, "MEDIUM")

    def test_review_floor_is_sol_high_even_with_an_implementation_contract(self):
        rec = self.route(task(extra=launch(effort="MEDIUM", mode="IMPLEMENTATION")), review=True)
        self.assertEqual((rec.profile.model, rec.profile.effort), ("gpt-6.2-sol", "HIGH"))
        self.assertEqual(rec.phase, "REVIEW")

    def test_human_hold_has_no_codex_action_even_with_review_flag(self):
        rec = self.route(task(status="HUMAN_PAUSED"), review=True)
        self.assertFalse(rec.launchable)
        self.assertIsNone(rec.profile)

    def test_unknown_model_or_unjustified_xhigh_fails_closed(self):
        for profile in (launch(model="gpt-6.2-astra"), launch(effort="XHIGH")):
            with self.subTest(profile=profile), self.assertRaises(PolicyError):
                self.route(task(extra=profile))

    def test_explicit_reason_preserves_exceptional_xhigh(self):
        rec = self.route(task(extra=launch(effort="XHIGH", reason="Escalation reason: unresolved recovery invariant")))
        self.assertEqual(rec.profile.effort, "XHIGH")

    def test_baseline_must_match_launch_contract(self):
        baseline = "\n## Codex execution policy\n\n### Baseline\n\nModel: gpt-6.2-sol\nReasoning effort: MEDIUM\n"
        with self.assertRaises(PolicyError):
            self.route(task(extra=launch() + baseline))

    def test_previous_accepted_policy_and_mixed_policy(self):
        self.policy.write_text(WORKFLOW.replace("GPT-6.2 Sol", "GPT-6.1 Sol"))
        self.assertEqual(self.route(task()).profile.model, "gpt-6.1-sol")
        self.policy.write_text(WORKFLOW.replace("GPT-6.2 Sol", "GPT-6.1 Sol", 1))
        with self.assertRaises(PolicyError):
            self.route(task())

    def test_unresolved_task_metadata_fails_closed(self):
        for text in (task(lane="DEEP_AOA"), task(status="UNKNOWN"), task().replace("AOA-269", "AOA-270")):
            with self.subTest(text=text), self.assertRaises(TaskError):
                self.route(text)


if __name__ == "__main__":
    unittest.main()

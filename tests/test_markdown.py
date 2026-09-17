import unittest

from yoohw_codex_router.errors import TaskError
from yoohw_codex_router.markdown import section_fields, top_level_fields


class MarkdownTests(unittest.TestCase):
    def test_top_level_stops_at_first_h2(self):
        text = "Status: READY\nLane: DEEP_BM\n\n## Mission\nStatus: ignored\n"
        self.assertEqual(top_level_fields(text)["Status"], "READY")

    def test_section_fields_are_exact(self):
        text = "## Codex launch contract\nModel: gpt-5.6-sol\nReasoning effort: HIGH\n\n## Other\nModel: no\n"
        fields = section_fields(text, "Codex launch contract")
        self.assertEqual(fields["Model"], "gpt-5.6-sol")

    def test_duplicate_field_fails_closed(self):
        with self.assertRaises(TaskError):
            top_level_fields("Status: READY\nStatus: BLOCKED\n")


if __name__ == "__main__":
    unittest.main()

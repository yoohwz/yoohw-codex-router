import unittest

from yoohw_codex_router.repo import infer_task_from_branch, normalize_origin


class RepoTests(unittest.TestCase):
    def test_origin_normalization(self):
        self.assertEqual(normalize_origin("git@github.com:yoohwz/wc-blacklist-manager.git"), "yoohwz/wc-blacklist-manager")

    def test_task_inference(self):
        self.assertEqual(infer_task_from_branch("bm-0152-blocked-auth"), "BM-0152")
        self.assertEqual(infer_task_from_branch("feature/aoa-0023-kernel"), "AOA-0023")
        self.assertIsNone(infer_task_from_branch("main"))


if __name__ == "__main__":
    unittest.main()

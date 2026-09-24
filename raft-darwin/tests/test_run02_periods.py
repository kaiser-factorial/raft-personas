"""Verify Run 02 period configuration, scope, and non-regression."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_period import PERIODS, discovery_reasons


class Run02PeriodTests(unittest.TestCase):
    def test_run02_period_keys_registered(self):
        expected = [
            "1859-post-origin", "1860", "1861", "1862", "1863",
            "1864", "1865", "1866", "1867", "1868"
        ]
        for key in expected:
            self.assertIn(key, PERIODS)

    def test_1859_post_origin_boundaries(self):
        start, end = PERIODS["1859-post-origin"]
        self.assertEqual(start, "1859-11-25")
        self.assertEqual(end, "1859-12-31")

    def test_1868_endpoint(self):
        start, end = PERIODS["1868"]
        self.assertEqual(start, "1868-01-01")
        self.assertEqual(end, "1868-12-31")

    def test_scope_json_consistency(self):
        scope_path = ROOT / "reports/research/runs/run-02-variation/scope.json"
        self.assertTrue(scope_path.exists())
        scope = json.loads(scope_path.read_text())
        self.assertEqual(scope["run_id"], "run-02-variation")
        self.assertEqual(scope["new_interval"]["start"], "1859-11-25")
        self.assertEqual(scope["new_interval"]["end"], "1868-12-31")
        for p in scope["periods"]:
            self.assertEqual(PERIODS[p["key"]], (p["start"], p["end"]))

    def test_discovery_for_post_origin_boundary(self):
        start, end = PERIODS["1859-post-origin"]
        reasons = discovery_reasons({"date": "25 Nov [1859]", "sorting_date": "1859-11-25"}, start, end)
        self.assertIn("catalogue_sorting_date", reasons)
        self.assertIn("display_year", reasons)


if __name__ == "__main__":
    unittest.main()

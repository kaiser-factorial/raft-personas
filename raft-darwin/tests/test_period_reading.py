"""Prevent synopsis-as-voice errors and lossy date-set display."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from period_review import body_unavailable, compact_constraints


class PeriodReadingTests(unittest.TestCase):
    def test_discusses_catalogue_entry_is_not_surviving_prose(self):
        self.assertTrue(body_unavailable('[Discusses books returned and desired and invites him to come for a few days.]'))
        self.assertFalse(body_unavailable('[Discusses books: “please return my volume”.]'))

    def test_monthly_compression_keeps_every_alternative(self):
        dates = [f'{year}-{month:02d}-22' for year in (1844, 1845) for month in range(1, 13)]
        constraints = [{'text': d, 'lower': d, 'upper': d, 'attributes': {'when': d}} for d in dates]
        value = compact_constraints(constraints, True)
        self.assertEqual(value['count'], 24)
        self.assertEqual(value['day_of_month'], 22)
        # Omitting a month must prevent a false continuous monthly description.
        self.assertIsInstance(compact_constraints(constraints[:5] + constraints[6:], True), list)
        self.assertIsInstance(compact_constraints(constraints, False), list)


if __name__ == '__main__':
    unittest.main()

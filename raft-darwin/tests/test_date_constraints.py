"""Regression checks for historical date boundaries and alternative dates."""

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_metadata import classify_period, date_bounds, source_flags, temporal_constraint


def constraint(attributes, text=""):
    element = ET.Element("date", attributes)
    element.text = text
    return temporal_constraint(element)


class DateConstraintsTests(unittest.TestCase):
    def test_expansion_window_is_explicit_and_preserves_alternatives(self):
        day = constraint({"when": "1837-01-01"})
        self.assertEqual(classify_period([day])[0], "outside_period_later")
        self.assertEqual(classify_period([day], "1837-01-01", "1843-12-31")[0], "safe_within_period")
        later = constraint({"when": "1861-01-01"})
        self.assertEqual(classify_period([day, later], "1837-01-01", "1843-12-31")[0], "ambiguous_period")

    def test_both_period_endpoints_are_inclusive(self):
        for day in ("1828-01-01", "1836-12-31"):
            self.assertEqual(classify_period([constraint({"when": day})])[0], "safe_within_period")

    def test_range_must_fit_at_both_ends(self):
        dates = [constraint({"notBefore": "1836-12-19", "notAfter": "1837-03-06"})]
        self.assertEqual(classify_period(dates)[0], "ambiguous_period")

    def test_lower_boundary_crossing_is_held(self):
        dates = [constraint({"notBefore": "1827-12-01", "notAfter": "1828-01-31"})]
        self.assertEqual(classify_period(dates)[0], "ambiguous_period")

    def test_wholly_later_and_wholly_earlier_dates(self):
        for day, status in [("1837-01-01", "outside_period_later"), ("1827-12-31", "outside_period_before")]:
            self.assertEqual(classify_period([constraint({"when": day})])[0], status)

    def test_alternative_future_date_cannot_be_ignored(self):
        dates = [constraint({"when": "1831-10-04"}), constraint({"when": "1861-10-04"})]
        self.assertEqual(classify_period(dates)[0], "ambiguous_period")

    def test_outer_envelope_does_not_fill_gaps_between_alternatives(self):
        dates = [constraint({"when": "1827-12-31"}), constraint({"when": "1837-01-01"})]
        self.assertEqual(classify_period(dates)[0], "outside_period_disjoint")

    def test_two_in_period_alternatives_are_period_eligible(self):
        dates = [constraint({"when": "1831-10-04"}), constraint({"when": "1831-10-11"})]
        self.assertEqual(classify_period(dates)[0], "safe_within_period")

    def test_open_bound_cannot_be_called_safe(self):
        dates = [constraint({"notBefore": "1830-01-01"})]
        self.assertEqual(classify_period(dates)[0], "ambiguous_period")

    def test_missing_dates_are_not_assigned_sorting_dates(self):
        self.assertEqual(classify_period([])[0], "needs_review")

    def test_partial_dates_expand_to_their_actual_precision(self):
        self.assertEqual(tuple(map(str, date_bounds("1832-02"))), ("1832-02-01", "1832-02-29"))
        self.assertEqual(tuple(map(str, date_bounds("1836"))), ("1836-01-01", "1836-12-31"))

    def test_reversed_and_conflicting_dates_fail(self):
        for attributes in [
            {"notBefore": "1831-02-01", "notAfter": "1831-01-01"},
            {"when": "1831-01-01", "notAfter": "1832-01-01"},
        ]:
            with self.assertRaises(ValueError):
                constraint(attributes)

    def test_unhandled_certainty_attributes_fail_visibly(self):
        with self.assertRaises(ValueError):
            constraint({"when": "1831-01-01", "cert": "low"})

    def test_editorial_brackets_are_distinct_from_questioned_dates(self):
        self.assertEqual(source_flags("31 [December 1827]"), ["editorially_supplied_component"])
        self.assertIn("questioned_component", source_flags("[31?] Oct [1831]"))
        self.assertIn("circa", source_flags("[c. 26 Aug 1831]"))
        self.assertIn("before", source_flags("[before 13 Oct 1834]"))

    def test_date_evidence_is_preserved_without_rewording(self):
        attributes = {"notBefore": "1829-01-25", "notAfter": "1829-01-29"}
        result = constraint(attributes, "[25–9 Jan 1829]")
        self.assertEqual(result["attributes"], attributes)
        self.assertEqual(result["text"], "[25–9 Jan 1829]")
        self.assertEqual((result["lower"], result["upper"]), ("1829-01-25", "1829-01-29"))


if __name__ == "__main__":
    unittest.main()

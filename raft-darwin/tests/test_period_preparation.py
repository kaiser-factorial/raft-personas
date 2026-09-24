"""Candidate discovery must not silently drop historical boundary cases."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_period import PERIODS, discovery_reasons


class PeriodPreparationTests(unittest.TestCase):
    def discover(self, label, sort="1842-01-01"):
        return discovery_reasons({"date": label, "sorting_date": sort}, "1844-01-01", "1846-12-31")

    def test_abbreviated_range_across_boundary_is_discovered(self):
        self.assertIn("display_year_envelope_including_abbreviated_ranges", self.discover("10 Dec [1842-5]"))

    def test_wide_range_not_just_explicit_endpoints(self):
        self.assertTrue(self.discover("[September 1831 – May 1861]", "1831-09-01"))

    def test_open_bound_goes_to_xml_instead_of_assuming_year(self):
        self.assertIn("display_open_upper_bound", self.discover("[before 20 Jan 1847]", "1847-01-20"))
        self.assertIn("display_open_lower_bound", self.discover("[after 1836?]", "1836-12-30"))

    def test_potential_disjoint_alternative_is_only_a_candidate(self):
        self.assertTrue(self.discover("[1842 or 1850]"))
        # The existing XML classifier, not this broad textual discovery, excludes the gap.

    def test_ordinary_later_record_is_not_selected(self):
        self.assertFalse(self.discover("11 January 1867", "1867-01-11"))

    def test_missing_display_year_retains_uncertainty(self):
        self.assertIn("display_has_no_full_year", self.discover("[undated]"))

    def test_publication_cutoff_not_whole_1859(self):
        self.assertEqual(PERIODS["1858-1859"][1], "1859-11-24")
        reasons = discovery_reasons({"date": "25 Nov 1859", "sorting_date": "1859-11-25"}, *PERIODS["1858-1859"])
        self.assertNotIn("catalogue_sorting_date", reasons)
        # Broader year discovery retains this for XML exclusion / boundary inspection.


if __name__ == "__main__":
    unittest.main()

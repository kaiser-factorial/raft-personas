"""Checks against date leakage and lost evidence in the body search."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from search_body_dates import parse_page, temporal_matches


class BodyDateTests(unittest.TestCase):
    def test_header_editorial_notes_and_salutation_are_separate(self):
        source = b'''<div id="letter"><div class="opener"><h1>1830</h1></div>
        <div class="body-content"><p class="salute">Dear Caroline,</p>
        <div class="supplemental"><p>Added in 1882</p></div>
        <p>I received yours of December 31 this morning.<sup class="footnote">1</sup></p>
        <p>April 5th. I write again.</p></div>
        <div class="footnotes">Published in 1899</div></div>
        <div id="summary">Reprinted in 1900</div>'''
        result = parse_page(source)
        body = " ".join(p["text"] for p in result["paragraphs"])
        self.assertIn("December 31", body)
        self.assertIn("April 5th", body)
        for forbidden in ("1830", "1882", "1899", "1900", "Dear Caroline"):
            self.assertNotIn(forbidden, body)
        self.assertEqual(len(result["paragraphs"]), 2)

    def test_period_colon_and_superscript_joining(self):
        source = b'''<div id="letter"><div class="body-content"><p>
        Yours of Jan: 15<sup>th</sup> and 31<sup>st</sup>. of May.
        </p></div></div>'''
        text = parse_page(source)["paragraphs"][0]["text"]
        matches = [text[a:b] for a, b, _, _ in temporal_matches(text)]
        self.assertIn("Jan: 15th", matches)
        self.assertTrue(any("31st. of May" in m for m in matches))

    def test_modal_may_is_not_a_month(self):
        text = "There is no saying how long it may last; I wrote yesterday."
        self.assertFalse(any("may" in text[a:b] for a, b, _, _ in temporal_matches(text)))
        text = "Thank Susan for her letter of May."
        self.assertTrue(any(text[a:b] == "May" for a, b, _, _ in temporal_matches(text)))

    def test_editorial_correction_is_preserved(self):
        text = "July [August] 12th I have received three more letters."
        self.assertIn(("editorially_corrected_date", "July [August] 12th"),
                      [(kind, text[a:b]) for a, b, _, kind in temporal_matches(text)])

    def test_impossible_source_date_is_not_silently_corrected(self):
        text = "On the 31st of June we received your letter."
        self.assertTrue(any(text[a:b] == "31st of June" for a, b, _, _ in temporal_matches(text)))

    def test_height_is_not_a_year(self):
        self.assertEqual(temporal_matches("An elevation of 1830 feet."), [])

    def test_unusual_layout_does_not_lose_text(self):
        source = b'''<div id="letter"><div class="body-content">On May 3 I received it.
        <p>I wrote on June 2.</p></div></div>'''
        result = parse_page(source)
        self.assertTrue(result["used_whole_body_fallback"])
        self.assertIn("May 3", result["paragraphs"][0]["text"])
        self.assertIn("June 2", result["paragraphs"][0]["text"])


if __name__ == "__main__":
    unittest.main()

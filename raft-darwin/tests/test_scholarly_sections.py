"""Prevent loss or accidental body attribution of DCP marginalia."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from period_review import check_quotes, scholarly_sections


class ScholarlySectionsTests(unittest.TestCase):
    def fixture(self, text):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "letter.html"
        path.write_text(text)
        return str(path), hashlib.sha256(path.read_bytes()).hexdigest()

    def test_keeps_all_sibling_notes_separate_from_letter_and_footnotes(self):
        path, sha = self.fixture('''<div id="letter">
        <div class="body"><div class="body-content"><p>Incoming letter.</p></div></div>
        <div class="annotations"><p>CD pencil: not forms.</p></div>
        <div class="cdnotes"><p>Separate research note.</p></div>
        <div class="unusual-enclosure"><p>Needs individual attribution.</p></div>
        <div class="footnotes">Editorial note.</div>
        <div id="bibliography">Book citation.</div></div>''')
        sections = scholarly_sections(path, sha)
        self.assertEqual([s["section_class"] for s in sections],
                         ["annotations", "cdnotes", "unusual-enclosure"])
        self.assertEqual([s["text"] for s in sections],
                         ["CD pencil: not forms.", "Separate research note.", "Needs individual attribution."])

    def test_annotation_quote_cannot_be_verified_as_incoming_body(self):
        path, sha = self.fixture('<div id="letter"><div class="body">letter</div><div class="cdnote">Darwin marginal thought</div></div>')
        section = scholarly_sections(path, sha)[0]
        rows = {"one": {"source": {"path": path, "sha256": sha},
                        "paragraphs": [{"body_paragraph": 1, "text": "letter", "locator": "body"}]}}
        quote = {"letter_id": "one", "quote": "Darwin marginal thought", "scholarly_section": section["locator"]}
        self.assertEqual(len(check_quotes(quote, rows)), 1)
        with self.assertRaises(ValueError):
            check_quotes({"letter_id": "one", "quote": "Darwin marginal thought", "body_paragraph": 1}, rows)

    def test_changed_evidence_rejected(self):
        path, _ = self.fixture('<div id="letter"><div class="annotations">note</div></div>')
        with self.assertRaises(AssertionError):
            scholarly_sections(path, "0" * 64)


if __name__ == "__main__":
    unittest.main()

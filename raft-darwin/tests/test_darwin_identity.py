"""Keep Charles Robert Darwin distinct from relatives and other correspondents."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_metadata
from fetch_metadata import is_darwin


class DarwinIdentityTests(unittest.TestCase):
    def row(self, sender=("Darwin", "C. R."), recipient=("Wedgwood", "Emma")):
        return {
            "id": "DCP-LETT-IDENTITY", " filename": "DCP-LETT-IDENTITY.xml",
            "sender_surname": sender[0], "sender_forename": sender[1],
            "recipient_surname": recipient[0], "recipient_forename": recipient[1],
            "date": "1 Jan 1860", "sorting_date": "1860-01-01",
        }

    def audit(self, row, sender_key, recipient_key):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "letters" / row[" filename"]
            path.parent.mkdir()
            raw = (
                '<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="DCP-LETT-IDENTITY">'
                '<teiHeader><profileDesc><correspDesc><correspAction type="sent">'
                f'<persName key="../nameregs/{sender_key}">Sender</persName>'
                '<date when="1860-01-01">1 Jan 1860</date></correspAction>'
                '<correspAction type="received">'
                f'<persName key="../nameregs/{recipient_key}">Recipient</persName>'
                '</correspAction></correspDesc></profileDesc></teiHeader>'
                '<text><body><div/></body></text></TEI>'
            ).encode()
            path.write_bytes(raw)
            index = {str(path.relative_to(root)): {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "url": "https://example.invalid/identity.xml",
            }}
            with patch.object(audit_metadata, "ROOT", root), patch.object(audit_metadata, "RAW", root):
                return audit_metadata.audit_record(
                    (1, 2, 2, row), index, raw_root=root,
                    start="1860-01-01", end="1860-12-31")

    def test_charles_is_recognized_on_either_side(self):
        for side in ("sender", "recipient"):
            row = self.row(sender=("Darwin", "C. R."), recipient=("Darwin", "C. R."))
            with self.subTest(side=side):
                self.assertTrue(is_darwin(row, side))

    def test_family_names_do_not_identify_charles(self):
        for name in (("Wedgwood", "Emma"), ("Darwin", "Emma"),
                     ("Darwin", "E."), ("Darwin", "E. A."),
                     ("Darwin", "F."), ("Darwin", "C. G. H.")):
            with self.subTest(name=name):
                row = self.row(sender=name, recipient=name)
                self.assertFalse(is_darwin(row, "sender"))
                self.assertFalse(is_darwin(row, "recipient"))

    def test_charles_on_one_side_does_not_change_the_other_person(self):
        row = self.row()
        self.assertTrue(is_darwin(row, "sender"))
        self.assertFalse(is_darwin(row, "recipient"))

    def test_emma_to_charles_is_incoming_and_never_darwin_authorship(self):
        row = self.row(sender=("Wedgwood", "Emma"), recipient=("Darwin", "C. R."))
        record = self.audit(row, "emma.xml", "nameregs_1.xml")
        self.assertEqual(record["direction"], "to_darwin")
        self.assertEqual(record["prospective_role"], "incoming_context_pending_receipt_and_reply_evidence")
        self.assertFalse(record["training_target_eligible"])

    def test_alias_cannot_hide_csv_xml_identity_disagreement(self):
        row = self.row(sender=("Wedgwood", "Emma"), recipient=("Hooker", "J. D."))
        with self.assertRaisesRegex(ValueError, "CSV/XML Darwin identity mismatch"):
            self.audit(row, "nameregs_1.xml", "hooker.xml")

    def test_third_party_emma_letter_is_rejected(self):
        row = self.row(sender=("Wedgwood", "Emma"), recipient=("Wedgwood", "F. E. E."))
        with self.assertRaisesRegex(ValueError, "Third-party correspondence selected"):
            self.audit(row, "emma.xml", "fanny.xml")


if __name__ == "__main__":
    unittest.main()

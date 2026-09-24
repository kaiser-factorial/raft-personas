"""Retain unaddressed memoranda without silently repairing malformed letters."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_metadata
from prepare_period import group_key


class MetadataTopologyTests(unittest.TestCase):
    def audit(self, *, memorandum=True, recipient_xml=False, recipient_csv=False,
              uncertain_author=False, second_author=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "letters/DCP-LETT-2115F.xml"
            path.parent.mkdir()
            notes = '<note type="description">mem</note>' if memorandum else ''
            received = ('<correspAction type="received"><persName key="other.xml">'
                        'Hooker, J. D.</persName></correspAction>') if recipient_xml else ''
            certainty = ' cert="low"' if uncertain_author else ''
            second = '<persName key="other.xml">Ansted, D. T.</persName>' if second_author else ''
            raw = (f'<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="DCP-LETT-2115F">'
                   f'<teiHeader><fileDesc><notesStmt>{notes}</notesStmt></fileDesc>'
                   f'<profileDesc><correspDesc><correspAction type="sent">'
                   f'<persName key="../nameregs/nameregs_1.xml"{certainty}>Darwin, C. R.</persName>{second}'
                   '<date notBefore="1857-07-01" notAfter="1857-08-01">July 1857</date>'
                   f'</correspAction>{received}</correspDesc></profileDesc></teiHeader>'
                   '<text><body><div/></body></text></TEI>').encode()
            path.write_bytes(raw)
            row = {'id': 'DCP-LETT-2115F', ' filename': path.name,
                   'sender_surname': 'Darwin', 'sender_forename': 'C. R.',
                   'recipient_surname': 'Hooker' if recipient_csv else '',
                   'recipient_forename': 'J. D.' if recipient_csv else '',
                   'date': 'July 1857', 'sorting_date': '1857-07-01'}
            index = {'letters/' + path.name: {'sha256': hashlib.sha256(raw).hexdigest(),
                                            'url': 'https://example.invalid/source.xml'}}
            with patch.object(audit_metadata, 'ROOT', root), patch.object(audit_metadata, 'RAW', root):
                return audit_metadata.audit_record((1, 2, 2, row), index, raw_root=root,
                                                   start='1856-01-01', end='1857-12-31')

    def test_explicit_author_only_memo_is_retained_without_recipient_or_pair(self):
        record = self.audit()
        self.assertEqual(record['recipient_evidence'], [])
        self.assertEqual(record['correspondence_topology'], 'author_only_memorandum')
        self.assertFalse(record['conversation_pairing_eligible'])
        self.assertFalse(record['training_target_eligible'])
        self.assertIsNone(record['known_by_date'])
        self.assertEqual(record['xml_latest'], '1857-08-01')  # Do not silently fix to July31.
        self.assertEqual(group_key(record), 'unaddressed_darwin_memoranda')

    def test_missing_recipient_in_an_ordinary_letter_still_fails(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected correspondence topology'):
            self.audit(memorandum=False)

    def test_memorandum_exception_cannot_erase_a_csv_recipient_or_joint_author(self):
        for changes in ({'recipient_csv': True}, {'second_author': True}):
            with self.subTest(**changes), self.assertRaisesRegex(ValueError, 'Unexpected correspondence topology'):
                self.audit(**changes)

    def test_uncertain_darwin_identity_is_still_held(self):
        with self.assertRaisesRegex(ValueError, 'Uncertain Darwin identity'):
            self.audit(uncertain_author=True)

    def test_normal_correspondence_retains_existing_shape(self):
        record = self.audit(memorandum=False, recipient_xml=True, recipient_csv=True)
        self.assertNotIn('correspondence_topology', record)
        self.assertNotIn('conversation_pairing_eligible', record)
        self.assertEqual(record['direction'], 'from_darwin')
        self.assertEqual(group_key(record), 'other.xml')


if __name__ == '__main__':
    unittest.main()

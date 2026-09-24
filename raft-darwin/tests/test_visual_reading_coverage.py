import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from period_review import validate_visual_readings


class VisualReadingCoverageTests(unittest.TestCase):
    def test_alt_text_is_not_visual_reading_and_asset_hash_is_required(self):
        source = {'path': 'letter.html', 'sha256': 'html-hash'}
        node = {'dom_locator': '/letter/img', 'tag': 'img', 'src': '/diagram.jpg', 'alt': 'diagram'}
        record = {'letter_id':'DCP-LETT-1', 'dom_locator':'/letter/img',
                  'source_path':'letter.html', 'source_html_sha256':'html-hash',
                  'figure_path':'figure.jpg', 'sha256':'asset-hash',
                  'visual_observation':'The diagram compares two distinct strata.'}
        with patch('period_review.visual_nodes', return_value=[node]), patch('period_review.digest', return_value='asset-hash'):
            with self.assertRaisesRegex(AssertionError, 'missing primary visual reading'):
                validate_visual_readings('DCP-LETT-1', source, [])
            self.assertEqual(validate_visual_readings('DCP-LETT-1', source, [record]), ['/letter/img'])
            with self.assertRaisesRegex(AssertionError, 'Figure hash mismatch'):
                validate_visual_readings('DCP-LETT-1', source, [record | {'sha256':'changed'}])


if __name__ == '__main__':
    unittest.main()

"""Checks of the archival-to-rendered boundary, including actual source cases."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from raft_export_text import projected_slice, text_holds, render_spans, render_supplement
from period_review import load


class ProjectionTests(unittest.TestCase):
    def test_cut_inside_changed_fraction_is_refused(self):
        with self.assertRaises(ValueError):projected_slice('Intro long enough 12 end','Intro long enough ½ end',18,20)

    def test_repeated_short_boundary_is_refused(self):
        with self.assertRaises(ValueError):projected_slice('abc 12 abc','abc ½ abc',1,3)

    def test_whitespace_only_projection_uses_exact_positions(self):
        text,_=projected_slice('P.S. Wednesday','P.S.\u00a0Wednesday',0,4)
        self.assertEqual(text,'P.S.')
        text,_=projected_slice('abc abc','abc\n\nabc',4,7)
        self.assertEqual(text,'abc')

    def test_preserves_integer_in_real_source_fraction(self):
        source=load('1858-1859')['DCP-LETT-796'];t=source['paragraphs'][0]['text']
        r=render_spans(source,[{'paragraph':1,'start':0,'end':len(t),'original_excerpt':t,'source_sha256':source['source']['sha256']}])
        self.assertIn('3¼',r['content']);self.assertNotIn('31/4',r['content'])
        self.assertGreater(r['blocks'][0]['source_audit']['fraction_nodes'],0)

    def test_supplement_is_authorial_note_not_address(self):
        r=render_supplement(load('1858-1859')['DCP-LETT-1732'],'supplemental')
        self.assertIn('Both your last letters have gone wrong',r['content'])
        self.assertNotEqual(r['content'],'Down Farnborough Kent')

    def test_budget_request_is_not_page_navigation(self):
        self.assertFalse(text_holds('I should be willing to go to 5s per bird.'))
        self.assertTrue(text_holds('Go to 1st page'))

    def test_artifact_does_not_match_real_words(self):
        self.assertFalse(text_holds('your Programme was crammed with events'))
        self.assertTrue(text_holds('Borough.ramme'))

    def test_unreadable_transcription_is_held(self):
        self.assertTrue(text_holds('There were [2 words illeg] in the letter.'))


if __name__=='__main__':unittest.main()

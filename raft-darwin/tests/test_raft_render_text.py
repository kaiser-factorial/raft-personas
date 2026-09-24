import tempfile, unittest
from pathlib import Path
from scripts.raft_render_text import render_html

FIXTURE='''<html><body><div id="letter"><div class="body-content">
<p class="authorial">A <math><mfrac><mn>3</mn><mn>4</mn></mfrac> mile.</p>
<p>Rows<table><tr><td>Feet</td><td>Value</td></tr><tr><td>Great Bell</td><td>4716</td></tr></table></p>
<p>Keep this prose<sup class="footnote">1</sup>.</p>
<div class="footnotes"><p>Do not export this.</p></div>
<p>Ambiguous QQQQ marker.</p>
</div></div></body></html>'''

class RendererTests(unittest.TestCase):
    def test_real_preserved_sources_match_body_boundaries(self):
        root=Path(__file__).resolve().parents[1]
        paths=[root/'data/raw/dcp/body-date-search-37-337'/f'DCP-LETT-{i}.html'
               for i in ('42','43','45','105','124','143','172')]
        for p in paths:
            r=render_html(p)
            self.assertTrue(r['blocks'], p.name)
            self.assertFalse(r['blocks'][0]['text'].startswith(('My dear Fox', 'Dear Fox', 'My dear Darwin')))
            self.assertEqual(r['provenance']['sha256'], __import__('hashlib').sha256(p.read_bytes()).hexdigest())

    def test_real_mixed_fraction_rendering(self):
        root=Path(__file__).resolve().parents[1]
        for i, expected in [('796','3¼'),('2396','7¼')]:
            r=render_html(root/'data/raw/dcp'/('1844-1846/pages' if i=='796' else '1856-1857/pages')/f'DCP-LETT-{i}.html')
            self.assertIn(expected, r['content'])

    def test_fraction_table_exclusion_and_hold(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.html'; p.write_text(FIXTURE)
            r=render_html(p)
            self.assertIn('¾',r['content'])
            self.assertIn('Great Bell | 4716',r['content'])
            self.assertNotIn('Do not export',r['content'])
            self.assertNotIn('1.',r['content'])
            self.assertTrue(r['audit']['holds'])
            self.assertEqual(r['provenance']['paragraph_count'],4)
    def test_superscript_is_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.html'; p.write_text('<div id="letter"><div class="body-content"><p>n<sup>2</sup></p></div></div>')
            self.assertEqual(render_html(p)['content'], 'n²')

    def test_suspicious_joined_word_is_held(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.html'; p.write_text('<div id="letter"><div class="body-content"><p>trans- ported</p></div></div>')
            self.assertTrue(any(h['kind']=='possible_joined_word_artifact' for h in render_html(p)['audit']['holds']))
    def test_scopes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'x.html'; p.write_text(FIXTURE)
            r=render_html(p,paragraphs=[1],codepoint_scopes={1:[2,7]})
            self.assertEqual(r['content'],'A ¾ mile.')
            self.assertTrue(any(h['kind']=='non_lossless_scope' for h in r['audit']['holds']))

if __name__=='__main__': unittest.main()

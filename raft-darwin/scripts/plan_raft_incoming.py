"""Root decisions for actual incoming prose, separate from reply selection."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from period_review import load

ROOT = Path(__file__).resolve().parents[1]
L = load('1858-1859')
P = ROOT / 'reports/raft-prep/direct-export-plan.working.json'
d = json.loads(P.read_text())


def numbers(s):
    out = []
    for item in s.split(','):
        b = item.split('-'); out.extend(range(int(b[0]), int(b[-1])+1))
    return out


SCOPES = {
    '153':'1-11', '157':'1', '196':'2,3', '197':'1,2',
    '1911':'2-6', '1923':'2-4,8-11,16', '1934':'3,5-9', '1983':'1-10',
    '1622':'1-4', '1995':'2-4,6', '2074':'2-10', '2144':'1-3', '2178':'1,2',
    '2204':'1-4,8', '2277':'1-3', '2307':'2-14',
}
HOLDS = {
    '1915A':'Lyell journal extract depends on three figures and unresolved source readings; unsent postscript is excluded. No complete dispatched letter is reconstructed.',
    '2119':'Received Huxley body depends on numbered Brulle extract with unresolved conseacute;quent artifact; preserve historical link but hold text-only prompt.',
    '2427':'Huxley memorandum depends on an actual figure; no source-supported text rendering of that visual has been admitted.',
}
for r in d['rows']:
    for unit in r['export_decision']['units']:
        for q in unit['inputs']:
            ident = q['source_id']; short = ident.removeprefix('DCP-LETT-')
            if short in HOLDS:
                q.update(state='held', reason=HOLDS[short], spans=[]); continue
            if short == '1651A':
                q.update(state='printed_witness_pending_final_comparison', spans=[],
                         witness='reports/raft-prep/candidates/davy-1651A-text.luna.json'); continue
            src = L[ident]
            selection = numbers(SCOPES[short]) if short in SCOPES else list(range(1, len(src['paragraphs'])+1))
            if short == '2225' and r['response_id'] == 'DCP-LETT-2235': selection = [1]
            spans = []
            for n in selection:
                t = src['paragraphs'][n-1]['text']; lo, hi = 0, len(t)
                if short == '1911' and n == 6:
                    assert t.count('It proves to be') == 1
                    hi = t.index('It proves to be')
                if short == '2114':
                    assert n == 1 and t.count('I have often recommended') == 1
                    hi = t.index('I have often recommended')
                while hi > lo and t[hi-1].isspace(): hi -= 1
                spans.append({'paragraph':n,'start':lo,'end':hi,'original_excerpt':t[lo:hi],
                              'source_sha256':src['source']['sha256']})
            assert spans
            q.update(state='scoped_pending_render_and_content_checks',spans=spans,
                     scope='Primary admitted incoming letter prose, narrowed where accepted relationship or authorship requires it.')
            if short == '153': q['participant_override'] = 'Caroline Sarah Darwin'
            if short == '1911': q['excluded_scope'] = 'Darwin-added terminal words and preceding incomplete introductory clause in P6.'
            if short == '1983': q['excluded_scope'] = 'Separately transmitted memorandum P11–30, outside the established November11 prompt.'
            if short == '1959': q['excluded_scope'] = 'Separate full Statistics article; ordinary letter retained.'
            if short == '2186': q['excluded_scope'] = 'Separately preserved lists are not transcribed or reconstructed in this letter question.'
d['incoming_rules_pin'] = {'path':str(Path(__file__).relative_to(ROOT)),
                           'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
d['status'] = 'root_response_and_incoming_scopes_resolved_pending_render_checks'
P.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
from collections import Counter
print(dict(Counter(q['state'] for r in d['rows'] for u in r['export_decision']['units'] for q in u['inputs'])))

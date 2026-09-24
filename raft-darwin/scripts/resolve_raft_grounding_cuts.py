"""Root-inspected grounding excerpts and separately dated continuations."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from period_review import load

ROOT = Path(__file__).resolve().parents[1]
LETTERS = load('1858-1859')
PLAN = ROOT / 'reports/raft-prep/grounding-review.working.json'
plan = json.loads(PLAN.read_text())
rows = {r['source_id']: r for r in plan['rows']}


def span(ident, paragraph, start=None, end=None, lo=None, hi=None):
    src = LETTERS[ident]
    text = src['paragraphs'][paragraph-1]['text']
    if start is not None:
        assert text.count(start) == 1
        lo = text.index(start)
    if end is not None:
        assert text.count(end) == 1
        hi = text.index(end)
    lo = 0 if lo is None else lo
    hi = len(text) if hi is None else hi
    while lo < hi and text[lo].isspace(): lo += 1
    while hi > lo and text[hi-1].isspace(): hi -= 1
    assert 0 <= lo < hi <= len(text)
    return {'paragraph': paragraph, 'start': lo, 'end': hi,
            'original_excerpt': text[lo:hi], 'source_sha256': src['source']['sha256']}


cuts = {
    '1230': (1, 'I am at present so much engaged', '’]'),
    '1337': (4, None, '[From Emma Darwin'),
    '1426': (3, None, 'My dearest Fanny'),
    '2058': (2, None, 'R Kippist Esq'),
    '2492': (6, None, 'I start for'),
}
for short, (n, start, end) in cuts.items():
    ident = 'DCP-LETT-' + short
    row = rows[ident]
    assert len(row['units']) == 1
    spans = row['units'][0]['spans']
    row['units'][0]['spans'] = [span(ident, n, start, end) if s['paragraph'] == n else s for s in spans]
    row['fragment_check'] = {'status': 'root_source_boundary_verified', 'paragraph': n,
                             'start_literal': start, 'end_literal': end}
    row.pop('pending_fragment_check', None)

# The address/itinerary crosses P6–8 and contains unresolved literal "ramme".
# Independent prose survives before and after it; do not invent that repair.
r = rows['DCP-LETT-2492']
r['units'][0]['spans'] = [s for s in r['units'][0]['spans'] if s['paragraph'] not in (7, 8)]
r['held_subscopes'] = [{'paragraphs': [6, 7, 8], 'scope': 'Itinerary beginning I start for',
                       'reason': 'Broken address layout with literal ramme; independent earlier and later prose retained.'}]

# Inspection confirms that the canonical P5 already excludes the dateline.
r = rows['DCP-LETT-1834']
r.pop('pending_fragment_check', None)
r['fragment_check'] = {'status': 'root_source_boundary_verified', 'paragraph': 5,
                       'reason': 'Canonical pea paragraph contains authorial prose only; no embedded dateline remains.'}

graph = json.loads((ROOT / 'reports/1837-1843/correspondence-map/graph.json').read_text())
for short in ('481', '649', '673'):
    ident = 'DCP-LETT-' + short
    row = rows[ident]
    assert row['state'] == 'held'
    units = []
    for sec in graph['dated_sections']:
        if sec['letter_id'] != ident: continue
        spans = [span(ident, n) for n in sec['paragraphs']]
        for s in sec.get('paragraph_fragments', []):
            if ident == 'DCP-LETT-649' and s['body_paragraph'] == 4 and s['char_start'] == 117:
                continue  # Friday morning is a dateline, not authored prose.
            spans.append(span(ident, s['body_paragraph'], lo=s['char_start'], hi=s['char_end']))
        units.append({'date': sec['date'], 'spans': sorted(spans, key=lambda s:(s['paragraph'],s['start'])),
                      'date_basis': 'Primary accepted dated section', 'primary_section': sec})
    assert len(units) == 2
    row.update(state='scoped_pending_render_and_content_checks', units=units,
               reason='Primary accepted separately dated Charles Darwin sections; no whole-letter scalar date invented.')

plan['status'] = 'root_grounding_spans_resolved_pending_render_checks'
plan['fragment_rules_pin'] = {'path': str(Path(__file__).relative_to(ROOT)),
                             'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
from collections import Counter
plan['counts'] = dict(Counter(r['state'] for r in plan['rows']))
PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'counts': plan['counts'], 'units': sum(len(r['units']) for r in plan['rows'])}))

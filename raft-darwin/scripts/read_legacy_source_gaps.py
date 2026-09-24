"""Display legacy primary body notes and source layers for explicit reconciliation.

Incoming records without a primary body note are displayed in full. This tool
does not make reading claims or admit any source or relationship.
"""
import json
import sys
from lxml import etree, html
from prepare_period import ROOT, read, digest
from period_review import load, scholarly_sections, bibliography_sections, visual_nodes

letters = load('1858-1859')
dossiers = {r['letter_id']: r for r in (
    json.loads(line) for line in
    (ROOT / 'reports/pre-beagle-1828-1831/dossiers.jsonl').read_text().splitlines())}
covered = {i for p in (ROOT / 'data/annotations/beagle-voyage').glob('*.primary.json')
           for i in read(p).get('full_read_ids', [])}
gap = read(ROOT / 'reports/research/beagle-historical-reuse-gap-map.luna.json')
remaining = [r['id'] for r in gap['records'] if r['id'] not in covered]
if sys.argv[1:] == ['--list']:
    for i, ident in enumerate(remaining):
        print(i, ident, 'primary_body_reuse' if ident in dossiers else 'fresh_body_needed')
    raise SystemExit

start, end = map(int, sys.argv[1:3])
for index, ident in enumerate(remaining[start:end], start):
    r = letters[ident]
    a = r['metadata_audit']
    assert digest(ROOT / r['source']['path']) == r['source']['sha256']
    assert digest(ROOT / a['provenance']['xml_path']) == a['provenance']['xml_sha256']
    print('\nINDEX', index, ident, r['header_text'])
    print('DATES', a['original_csv']['date'], a['xml_earliest'], a['xml_latest'], a['source_date_flags'])
    print('XML', a['xml_notes'])
    if ident in dossiers:
        d = dossiers[ident]
        initial = d['initial_survey']
        assert initial['target_body_read_in_full'] is True
        assert initial['body_source']['sha256'] == r['source']['sha256']
        print('PRIOR_PRIMARY_BODY_NOTE', initial['summary'], initial['observations'])
        print('PRIMARY_ADJUDICATION', d['parent_adjudication'])
        print('REVIEWED_ROLE', d['training_role'], d['established_prompt_ids'])
    else:
        print('PEOPLE', a['sender_evidence'], a['recipient_evidence'])
        for p in r['paragraphs']:
            print('P' + str(p['body_paragraph']), p['text'])
    print('EXCLUDED', r['excluded_body_annotations_and_salutations'])
    print('FOOTNOTES', r['editorial_footnotes'])
    for fn in (scholarly_sections, bibliography_sections, visual_nodes):
        for section in fn(r['source']['path'], r['source']['sha256']):
            print(fn.__name__, section)
    tree = html.parse(str(ROOT / r['source']['path']))
    for m in tree.xpath('//*[local-name()="math"]'):
        print('MATH', etree.tostring(m, encoding='unicode', with_tail=False))

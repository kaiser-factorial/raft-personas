"""Display full preserved sources for independent human/model reading."""
import sys
from prepare_period import ROOT, digest
from period_review import load, scholarly_sections, bibliography_sections, visual_nodes

letters = load('1858-1859')
for n in sys.argv[1:]:
    r = letters['DCP-LETT-' + n]
    a = r['metadata_audit']
    print('\nLETTER', r['id'], r['header_text'])
    print('SOURCE', r['source']['path'], r['source']['sha256'])
    print('DATE', a['original_csv']['date'], a['xml_earliest'], a['xml_latest'], a['source_date_flags'])
    print('XML_CONSTRAINTS', [(x['text'], x['lower'], x['upper']) for x in a['sent_date_constraints']])
    print('PEOPLE', a['sender_evidence'], a['recipient_evidence'])
    print('XMLNOTES', a['xml_notes'])
    assert digest(ROOT / r['source']['path']) == r['source']['sha256']
    assert digest(ROOT / a['provenance']['xml_path']) == a['provenance']['xml_sha256']
    for p in r['paragraphs']:
        print('P' + str(p['body_paragraph']), p['text'])
    print('EXCLUDED', r['excluded_body_annotations_and_salutations'])
    print('EDITORIAL_SUMMARY', r['editorial_summary'])
    print('FOOTNOTES', r['editorial_footnotes'])
    for fn in [scholarly_sections, bibliography_sections, visual_nodes]:
        for section in fn(r['source']['path'], r['source']['sha256']):
            print(fn.__name__, section)

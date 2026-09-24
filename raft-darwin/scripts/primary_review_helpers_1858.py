"""Package explicit primary readings; never infer historical adjudications."""
import copy
from prepare_period import ROOT, read, write, digest
from period_review import load, scholarly_sections, bibliography_sections, validate_visual_readings

b = ROOT / 'reports/1858-1859/review'
l = load('1858-1859')
I = lambda n: 'DCP-LETT-' + str(n)

def q(n, pn, text):
    r = l[I(n)]
    body = next(p['text'] for p in r['paragraphs'] if p['body_paragraph'] == pn)
    start = body.index(text)
    return {'letter_id': I(n), 'body_paragraph': pn, 'quote': text,
            'char_start': start, 'char_end': start + len(text), 'source_sha256': r['source']['sha256']}

def accept(batch, notes, decisions, reuse_map=None, visuals=None, unavailable=None):
    key = f'batch-{batch:02}'
    packet = read(b / 'packets' / f'{key}.json')
    visuals, unavailable = copy.deepcopy(visuals or []), list(unavailable or [])
    notes = dict(notes)
    reuse = []
    for ident, (period, prior_batch) in (reuse_map or {}).items():
        path = ROOT / f'reports/{period}/review/parent-reading/batch-{prior_batch:02}.json'
        ledger_path = ROOT / f'data/annotations/periods/{period}/batch-{prior_batch:02}.json'
        prior, ledger = read(path), read(ledger_path)
        assert ident in prior['source_record_ids_read']
        assert next(x['sha256'] for x in ledger['inputs'] if x['path'] == str(path.relative_to(ROOT))) == digest(path)
        source = next(x for x in ledger['sources'] if x['letter_id'] == ident)
        assert source['body_source']['sha256'] == l[ident]['source']['sha256']
        assert source['metadata_provenance']['xml_sha256'] == l[ident]['metadata_audit']['provenance']['xml_sha256']
        for fn, field in [(scholarly_sections, 'supplemental_sections_read_ids'), (bibliography_sections, 'bibliography_sections_read_ids')]:
            if fn(l[ident]['source']['path'], l[ident]['source']['sha256']):
                assert ident in prior.get(field, []), (ident, field)
        notes[ident] = 'Explicit accepted primary full-source reading reused after matching note, ledger and source hashes. ' + prior['record_notes'][ident]
        body_read = ident in prior['body_ids_read']
        if not body_read:
            unavailable.append(ident)
        reuse.append({'letter_id': ident, 'primary_note': str(path.relative_to(ROOT)),
                      'primary_note_sha256': digest(path), 'accepted_ledger': str(ledger_path.relative_to(ROOT)),
                      'accepted_ledger_sha256': digest(ledger_path), 'html_sha256': l[ident]['source']['sha256'],
                      'xml_sha256': l[ident]['metadata_audit']['provenance']['xml_sha256'],
                      'source_record_read_in_full': True, 'body_read_in_full': body_read})
        visuals.extend(copy.deepcopy([x for x in prior.get('visual_readings', []) if x['letter_id'] == ident]))
    assert set(packet['target_ids'] + packet['context_ids']) <= set(notes)
    for ident in notes:
        r = l[ident]
        assert digest(ROOT / r['source']['path']) == r['source']['sha256']
        p = r['metadata_audit']['provenance']
        assert digest(ROOT / p['xml_path']) == p['xml_sha256']
        validate_visual_readings(ident, r['source'], visuals)
    nd = {'batch_id': key, 'status': 'parent_full_source_read_complete',
          'source_record_ids_read': list(notes), 'body_ids_read': [i for i in notes if i not in unavailable],
          'record_notes': notes, 'prior_primary_reading_reuse': reuse, 'visual_readings': visuals,
          'supplemental_sections_read_ids': [i for i in notes if scholarly_sections(l[i]['source']['path'], l[i]['source']['sha256'])],
          'bibliography_sections_read_ids': [i for i in notes if bibliography_sections(l[i]['source']['path'], l[i]['source']['sha256'])],
          'reading_method': 'Root independently read complete surviving new source bodies, metadata constraints, exclusions, footnotes, scholarly sections and bibliography. Actual special markup and figures inspected where present. Reused explicit accepted primary readings only after matching source and accepted evidence hashes. Historical decisions and notes are handwritten; validation packages evidence rather than adjudicating it.'}
    dec = {'batch_id': key, 'status': 'parent_adjudicated', 'body_unavailable_ids': unavailable,
           'direct_reply_pairs': [], 'correspondent_replies': [], 'cross_correspondent_knowledge': [],
           'proposal_adjudications': [], **decisions}
    write(b / 'parent-reading' / f'{key}.json', nd, frozen=True)
    write(b / 'parent-decisions' / f'{key}.json', dec, frozen=True)
    print('Saved explicit primary notes and decisions for', key)

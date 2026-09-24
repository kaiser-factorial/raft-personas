"""Verify recorded Beagle evidence, including explicit additive corrections.

This checks provenance and recorded coverage. It cannot establish that a source
was read or that a historical relationship is true.
"""
from datetime import datetime, timezone

from prepare_period import ROOT, read, write, digest
from period_review import (load, check_quotes, scholarly_sections,
                           bibliography_sections, validate_visual_readings)


def verify():
    letters = load('1858-1859')
    folder = ROOT / 'data/annotations/beagle-voyage'
    addenda = [(p, read(p)) for p in sorted((folder / 'addenda').glob('*.primary.json'))]
    results = []
    for path in sorted(folder.glob('*.primary.json')):
        ledger = read(path)
        assert ledger['status'] == 'parent_adjudicated'
        rel = str(path.relative_to(ROOT))
        supplements = [(p, d) for p, d in addenda
                       if rel in {x['path'] for x in d.get('inputs', [])}]
        note_path = next(ROOT / x['path'] for x in ledger['inputs']
                         if '/parent-reading/' in x['path'] and ledger['group_id'] in x['path'])
        note = read(note_path)
        decisions_path = next(ROOT / x['path'] for x in ledger['inputs']
                              if '/parent-decisions/' in x['path'])
        decisions = read(decisions_path)
        documents = [note] + [d for _, d in supplements]
        pins = list(ledger['inputs'])
        for _, d in supplements:
            pins.extend(d.get('inputs', []))
        for pin in pins:
            assert digest(ROOT / pin['path']) == pin['sha256'], pin['path']
        sources = {s['letter_id']: s for s in ledger['sources']}
        for _, d in supplements:
            sources.update({s['letter_id']: s for s in d.get('sources', [])})
        expected = set(ledger['reviewed_record_ids'] + ledger.get('review_context_read_ids', [])
                       + ledger.get('additional_parent_read_ids', []))
        # Also check actual first-pass scope, so an omitted context cannot be
        # hidden by copying the same incomplete list into the ledger.
        for pin in ledger['inputs']:
            if '/reviews/' not in pin['path'] or not pin['path'].endswith('.json'):
                continue
            report = read(ROOT / pin['path'])
            if report.get('group_id') != ledger['group_id']:
                continue  # A neighbouring report may be pinned for a disputed lead.
            for field in ['record_reviews', 'outgoing_reviews', 'incoming_reviews', 'additional_record_reviews']:
                expected.update(r['letter_id'] for r in report.get(field, []))
        assert expected <= sources.keys(), (ledger['group_id'], expected - sources.keys())
        full_ids = {i for d in documents for i in d.get('source_record_ids_read', [])}
        bodies = {i for d in documents for i in d.get('body_ids_read', [])}
        notes = {i: text for d in documents for i, text in d.get('record_notes', {}).items()}
        visuals = [v for d in documents for v in d.get('visual_readings', [])]
        assert expected <= full_ids and expected <= notes.keys()
        unavailable = set(ledger.get('body_unavailable_ids', []))
        assert expected <= bodies | unavailable
        for ident, source in sources.items():
            assert notes.get(ident), ident
            html_source, xml_source = source['body_source'], source['metadata_provenance']
            assert digest(ROOT / html_source['path']) == html_source['sha256']
            assert digest(ROOT / xml_source['xml_path']) == xml_source['xml_sha256']
            assert letters[ident]['source']['sha256'] == html_source['sha256']
            assert letters[ident]['metadata_audit']['provenance']['xml_sha256'] == xml_source['xml_sha256']
            for fn, field in [(scholarly_sections, 'supplemental_sections_read_ids'),
                              (bibliography_sections, 'bibliography_sections_read_ids')]:
                if fn(html_source['path'], html_source['sha256']):
                    assert any(ident in d.get(field, []) for d in documents), (ident, field)
            validate_visual_readings(ident, html_source, visuals)
        checks = check_quotes(decisions, letters)
        results.append({'group_id': ledger['group_id'], 'ledger_path': rel,
                        'ledger_sha256': digest(path), 'input_hash_checks': len(pins),
                        'source_pairs_checked': len(sources), 'quotes_checked': len(checks),
                        'visual_readings_checked': len(visuals),
                        'addenda': [{'path': str(p.relative_to(ROOT)), 'sha256': digest(p)}
                                    for p, _ in supplements], 'error_count': 0})
    result = {'created_at': datetime.now(timezone.utc).isoformat(), 'accepted_groups': len(results),
              'source_pair_checks': sum(r['source_pairs_checked'] for r in results),
              'quote_checks': sum(r['quotes_checked'] for r in results), 'error_count': 0,
              'groups': results,
              'limitation': 'Structural provenance and recorded coverage only; not historical adjudication.'}
    write(ROOT / 'reports/beagle-voyage-review/ledger-integrity-audit.json', result)
    return {k: v for k, v in result.items() if k != 'groups'}


if __name__ == '__main__':
    print(verify())

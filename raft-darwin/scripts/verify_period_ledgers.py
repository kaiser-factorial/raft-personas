"""Read-only verification of accepted ledgers and explicit reading addenda.

Recorded provenance and source coverage are not historical truth.
"""
import argparse
import json
import re
from collections import Counter

from period_review import bibliography_sections, check_quotes, load, scholarly_sections, visual_nodes, validate_visual_readings
from prepare_period import PERIODS, ROOT, digest, read, write


def supplemental_addenda(period, batch, ident, source):
    matches = []
    for path in sorted((ROOT / 'data/annotations/periods' / period / 'addenda').glob('*.json')):
        data = read(path)
        if data.get('status') != 'primary_supplemental_source_read_complete':
            continue
        if batch not in data.get('applies_to', []):
            continue
        for record in data.get('records', []):
            if record.get('letter_id') != ident:
                continue
            assert record['source']['path'] == source['path'], 'Addendum source path changed'
            assert record['source']['sha256'] == source['sha256'], 'Addendum source hash changed'
            assert record['sections_read_in_full'] == scholarly_sections(source['path'], source['sha256']), 'Addendum does not cover complete current sections'
            matches.append({'path': str(path.relative_to(ROOT)), 'sha256': digest(path), 'letter_id': ident})
    return matches


def bibliography_addenda(period, batch, ident, source):
    matches = []
    for path in sorted((ROOT / 'data/annotations/periods' / period / 'addenda').glob('*.json')):
        data = read(path)
        if data.get('status') != 'primary_bibliography_source_read_complete' or batch not in data.get('applies_to', []):
            continue
        for record in data.get('records', []):
            if record.get('letter_id') != ident:
                continue
            assert record['source'] == source, 'Bibliography addendum source changed'
            assert record['sections_read_in_full'] == bibliography_sections(source['path'], source['sha256']), 'Bibliography addendum section mismatch'
            matches.append({'path': str(path.relative_to(ROOT)), 'sha256': digest(path), 'letter_id': ident})
    return matches


def verify(period, batches=None):
    base = ROOT / 'reports' / period / 'review'
    letters = load(period)
    folder = ROOT / 'data/annotations/periods' / period
    paths = sorted(p for p in folder.glob('batch-*.json') if re.fullmatch(r'batch-\d{2}\.json', p.name))
    if batches is not None:
        wanted = {b if b.startswith('batch-') else 'batch-' + b for b in batches}
        paths = [p for p in paths if p.stem in wanted]
        assert {p.stem for p in paths} == wanted, 'Requested accepted ledger missing'
    results = []
    for path in paths:
        ledger = read(path)
        batch = ledger['batch_id']
        result = {'batch_id': batch, 'ledger_path': str(path.relative_to(ROOT)),
                  'ledger_sha256': digest(path), 'input_hash_checks': 0,
                  'source_hash_pairs_checked': 0, 'exact_quote_checks': 0,
                  'supplemental_reading_via_original_note': [],
                  'supplemental_reading_addenda': [], 'errors': []}
        result['visual_readings_checked'] = 0
        result['visual_reading_addenda'] = []
        result['bibliography_sources_checked'] = 0
        result['bibliography_reading_addenda'] = []
        for entry in ledger['inputs']:
            input_path = ROOT / entry['path']
            actual = digest(input_path) if input_path.exists() else None
            result['input_hash_checks'] += 1
            if actual != entry['sha256']:
                result['errors'].append({'kind': 'recorded_input_hash_mismatch', 'path': entry['path'], 'expected': entry['sha256'], 'actual': actual})
        try:
            assert ledger['status'] == 'parent_adjudicated'
            notes = read(base / 'parent-reading' / f'{batch}.json')
            packet = read(base / 'packets' / f'{batch}.json')
            assert notes['status'] == 'parent_full_source_read_complete'
            source_ids = set(notes['source_record_ids_read'])
            assert source_ids == set(notes['record_notes'])
            assert set(packet['target_ids'] + packet['context_ids']) <= source_ids
            assert Counter(x['letter_id'] for x in ledger['letter_adjudications']) == Counter(packet['target_ids'])
            assert source_ids == {x['letter_id'] for x in ledger['sources']}
            unavailable = set(read(base / 'parent-decisions' / f'{batch}.json').get('body_unavailable_ids', []))
            assert set(notes['body_ids_read']) == source_ids - unavailable
            result['primary_source_record_count'] = len(source_ids)
            for ref in ledger['sources']:
                ident = ref['letter_id']
                source = ref['body_source']
                metadata = ref['metadata_provenance']
                assert source == letters[ident]['source'], ident + ': current projection source differs from ledger'
                assert metadata == letters[ident]['metadata_audit']['provenance'], ident + ': metadata provenance differs'
                if (ROOT / source['path']).exists():
                    assert digest(ROOT / source['path']) == source['sha256'], ident + ': HTML hash mismatch'
                if (ROOT / metadata['xml_path']).exists():
                    assert digest(ROOT / metadata['xml_path']) == metadata['xml_sha256'], ident + ': XML hash mismatch'
                result['source_hash_pairs_checked'] += 1
                if bibliography_sections(source['path'], source['sha256']):
                    if ident not in notes.get('bibliography_sections_read_ids', []):
                        matches = bibliography_addenda(period, batch, ident, source)
                        assert matches, ident + ': missing primary editorial bibliography reading'
                        result['bibliography_reading_addenda'].extend(matches)
                    result['bibliography_sources_checked'] += 1
                if visual_nodes(source['path'], source['sha256']):
                    visual_readings = notes.get('visual_readings', []).copy()
                    for addendum in sorted((folder / 'addenda').glob('*.json')):
                        data = read(addendum)
                        if data.get('status') != 'primary_visual_source_read_complete' or batch not in data.get('applies_to', []):
                            continue
                        matching = [r for r in data.get('records', []) if r['letter_id'] == ident]
                        if matching:
                            visual_readings.extend(matching)
                            result['visual_reading_addenda'].append({'path':str(addendum.relative_to(ROOT)), 'sha256':digest(addendum), 'letter_id':ident})
                    result['visual_readings_checked'] += len(validate_visual_readings(ident, source, visual_readings))
                if not scholarly_sections(source['path'], source['sha256']):
                    continue
                if ident in notes.get('supplemental_sections_read_ids', []):
                    result['supplemental_reading_via_original_note'].append(ident)
                else:
                    matches = supplemental_addenda(period, batch, ident, source)
                    assert matches, ident + ': missing primary supplemental reading'
                    result['supplemental_reading_addenda'].extend(matches)
            result['exact_quote_checks'] = len(check_quotes(ledger, letters))
        except (AssertionError, KeyError, ValueError, OSError, StopIteration) as exc:
            result['errors'].append({'kind': 'integrity_or_coverage_failure', 'detail': str(exc) or type(exc).__name__})
        results.append(result)
    return {'period': period, 'read_only_with_respect_to_accepted_evidence': True,
            'accepted_ledgers_checked': len(results),
            'recorded_input_hash_checks': sum(r['input_hash_checks'] for r in results),
            'source_hash_pairs_checked': sum(r['source_hash_pairs_checked'] for r in results),
            'exact_quote_checks': sum(r['exact_quote_checks'] for r in results),
            'visual_readings_checked': sum(r['visual_readings_checked'] for r in results),
            'bibliography_sources_checked': sum(r['bibliography_sources_checked'] for r in results),
            'error_count': sum(len(r['errors']) for r in results), 'ledgers': results,
            'limitation': 'Verifies exact source and input provenance, locator-specific quotes, and recorded primary coverage. It does not establish historical truth or convert extraction into a reading attestation.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--period', choices=PERIODS, default='1844-1846')
    parser.add_argument('--batches', nargs='+')
    args = parser.parse_args()
    audit = verify(args.period, args.batches)
    write(ROOT / 'reports' / args.period / 'review/ledger-integrity-audit.json', audit)
    print(json.dumps({k: v for k, v in audit.items() if k != 'ledgers'}))
    if audit['error_count']:
        print(json.dumps([{'batch': r['batch_id'], 'errors': r['errors']} for r in audit['ledgers'] if r['errors']]))
        raise SystemExit(1)

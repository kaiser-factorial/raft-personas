"""Package explicit primary decisions after source reading, without inferring them.

All coverage and source checks run before any immutable output is created.
The checks establish recorded provenance, not historical truth or actual reading.
"""
from datetime import datetime, timezone

from prepare_period import ROOT, read, write, digest
from period_review import (load, check_quotes, scholarly_sections,
                          bibliography_sections, validate_visual_readings)


def quote(letters, ident, paragraph, text):
    record = letters[ident]
    body = next(p['text'] for p in record['paragraphs']
                if p['body_paragraph'] == paragraph)
    start = body.index(text)
    return {'letter_id': ident, 'body_paragraph': paragraph, 'quote': text,
            'char_start': start, 'char_end': start + len(text),
            'source_sha256': record['source']['sha256']}


def package(group, notes, decisions, *, targets, contexts=(), additional=(),
            visuals=(), reuse=(), extra_inputs=(), reading_method):
    letters = load('1858-1859')
    base = ROOT / 'reports/beagle-voyage-review'
    candidate = base / f'reviews/{group}.luna.json'
    candidate_data = read(candidate)
    expected = set(targets) | set(contexts) | set(additional)
    for field in ['record_reviews', 'outgoing_reviews', 'incoming_reviews',
                  'additional_record_reviews']:
        expected.update(r['letter_id'] for r in candidate_data.get(field, []))
    assert expected == set(notes), (group, expected - set(notes), set(notes) - expected)
    assert decisions['group_id'] == group
    assert decisions['status'] == 'parent_adjudicated'
    for ident, note in notes.items():
        assert isinstance(note, str) and note.strip(), ident
        record = letters[ident]
        assert digest(ROOT / record['source']['path']) == record['source']['sha256']
        meta = record['metadata_audit']['provenance']
        assert digest(ROOT / meta['xml_path']) == meta['xml_sha256']
        validate_visual_readings(ident, record['source'], list(visuals))
    checks = check_quotes(decisions, letters)
    source_ids = list(notes)
    primary = {
        'group_id': group, 'status': 'parent_full_source_read_complete',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'source_record_ids_read': source_ids, 'body_ids_read': source_ids,
        'record_notes': notes, 'prior_primary_reading_reuse': list(reuse),
        'visual_readings': list(visuals), 'reading_method': reading_method,
        'supplemental_sections_read_ids': [i for i in notes if scholarly_sections(
            letters[i]['source']['path'], letters[i]['source']['sha256'])],
        'bibliography_sections_read_ids': [i for i in notes if bibliography_sections(
            letters[i]['source']['path'], letters[i]['source']['sha256'])],
    }
    note_path = base / f'parent-reading/{group}.primary.json'
    decision_path = base / f'parent-decisions/{group}.primary.json'
    ledger_path = ROOT / f'data/annotations/beagle-voyage/{group}.primary.json'
    # Never partially replace accepted evidence. Corrections require an addendum.
    for path in [note_path, decision_path, ledger_path]:
        assert not path.exists(), path
    pins = [note_path, decision_path, candidate] + [ROOT / p for p in extra_inputs]
    for path in pins[2:]:
        assert path.is_file(), path
    write(note_path, primary, frozen=True)
    write(decision_path, decisions, frozen=True)
    ledger = {
        'schema_version': 2, 'period': '1828-1836', 'group_id': group,
        'status': 'parent_adjudicated', 'reviewed_record_ids': list(targets),
        'review_context_read_ids': list(contexts),
        'additional_parent_read_ids': list(additional),
        'full_read_ids': source_ids, 'body_unavailable_ids': [],
        'letter_adjudications': decisions.get('record_dispositions', []),
        'inputs': [{'path': str(p.relative_to(ROOT)), 'sha256': digest(p)} for p in pins],
        'sources': [{'letter_id': i, 'body_source': letters[i]['source'],
                     'metadata_provenance': letters[i]['metadata_audit']['provenance']}
                    for i in notes],
        'validation': {'sources_checked': len(notes), 'quote_checks': len(checks),
                       'visual_readings_checked': len(visuals), 'error_count': 0},
        'training_export_performed': False,
    }
    for field in ['direct_reply_pairs', 'correspondent_replies', 'cross_correspondent_knowledge']:
        ledger[field] = decisions.get(field, [])
    for field in ['retained_prior_relationships', 'unresolved_references']:
        if field in decisions:
            ledger[field] = decisions[field]
    write(ledger_path, ledger, frozen=True)
    return {'group': group, 'sources': len(notes), 'quotes': len(checks),
            'direct': len(ledger['direct_reply_pairs']),
            'reverse': len(ledger['correspondent_replies']),
            'knowledge': len(ledger['cross_correspondent_knowledge'])}

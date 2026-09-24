"""Record explicit primary notes during legacy reconciliation, never infer them."""
from datetime import datetime, timezone
from prepare_period import ROOT, read, write, digest
from period_review import load, scholarly_sections, bibliography_sections, visual_nodes

PATH = ROOT / 'reports/beagle-voyage-review/legacy-reconciliation-working.json'

def record(notes, *, fresh=(), visuals=()):
    letters = load('1858-1859')
    dossier = ROOT / 'reports/pre-beagle-1828-1831/dossiers.jsonl'
    parent = ROOT / 'reports/pre-beagle-1828-1831/parent_review.json'
    import json
    dossiers = {r['letter_id']: r for r in map(json.loads, dossier.read_text().splitlines())}
    data = read(PATH) if PATH.exists() else {
        'status': 'primary_reconciliation_in_progress_not_export_approval',
        'record_notes': {}, 'visual_readings': [],
        'scope': 'Read existing primary initial_survey body notes, verify source pins, and read outstanding metadata/apparatus/visual layers. Fresh incoming body reading is distinguished from prior primary body reuse.',
    }
    for number, note in notes.items():
        ident = 'DCP-LETT-' + str(number)
        assert ident not in data['record_notes'], ident
        r = letters[ident]
        assert digest(ROOT / r['source']['path']) == r['source']['sha256']
        p = r['metadata_audit']['provenance']
        assert digest(ROOT / p['xml_path']) == p['xml_sha256']
        mode = 'fresh_primary_body_read' if str(number) in {str(n) for n in fresh} else 'prior_primary_body_note_read_and_reused'
        reused = []
        if mode.startswith('prior'):
            d = dossiers[ident]['initial_survey']
            assert d['target_body_read_in_full'] is True
            assert d['body_source']['sha256'] == r['source']['sha256']
            reused = [{'path': str(x.relative_to(ROOT)), 'sha256': digest(x)} for x in [dossier, parent]]
        data['record_notes'][ident] = {
            'body_reading_mode': mode, 'note': note,
            'body_source': r['source'], 'metadata_provenance': p,
            'prior_primary_inputs': reused,
            'metadata_exclusions_footnotes_read': True,
            'scholarly_sections_read': scholarly_sections(r['source']['path'], r['source']['sha256']),
            'bibliography_sections_read': bibliography_sections(r['source']['path'], r['source']['sha256']),
            'visual_nodes': visual_nodes(r['source']['path'], r['source']['sha256']),
        }
    data['visual_readings'].extend(visuals)
    data['updated_at'] = datetime.now(timezone.utc).isoformat()
    write(PATH, data)
    return len(data['record_notes'])

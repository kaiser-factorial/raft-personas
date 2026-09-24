#!/usr/bin/env python3
"""Write/check one cumulative, reviewed RAFT export, without importing RAFT.

Only the installed package's pure schema/date functions are AST-extracted.
No embedding, LLM, network, import-conversation, or training code is executed.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, date, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag

from period_review import load
from raft_export_text import text_holds

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT/'reports/raft-prep'
REPORT = ROOT/'reports/raft-export'
PROJECT = ROOT/'darwin_0'
RAFT = Path('/opt/anaconda3/lib/python3.13/site-packages/raft')
SINCE, UNTIL = '1828-01-01', '1859-11-24'
SNAPSHOTS = {
    'rendered-staging.json': PREP/'rendered-staging.working.json',
    'grounding-plan.json': PREP/'grounding-review.working.json',
    'direct-plan.json': PREP/'direct-export-plan.working.json',
    'relationship-inventory.json': PREP/'candidates/raft-export-inventory.dry-run.json',
}


def dump(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()


def jsonlines(rows):
    return ''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in rows).encode()


def digest(raw): return hashlib.sha256(raw).hexdigest()


def pin(path):
    path=Path(path)
    return {'path':str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            'sha256':digest(path.read_bytes())}


def assert_pin(p):
    path=ROOT/p['path']
    assert path.is_file(), f'Missing pinned input: {path}'
    assert digest(path.read_bytes())==p['sha256'], f'Changed pinned input: {path}'


def native_functions():
    env={'Any':Any,'datetime':datetime,'parsedate_to_datetime':parsedate_to_datetime}
    for filename,names in [('convo_structurer.py',{'is_transcript'}),('sources.py',{'iso_date','date_num'})]:
        tree=ast.parse((RAFT/filename).read_text())
        definitions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        assert {n.name for n in definitions}==names
        exec(compile(ast.Module(body=definitions,type_ignores=[]),str(RAFT/filename),'exec'),env)
    return env


def validate_day(day, native):
    assert isinstance(day,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',day),day
    assert date.fromisoformat(day).isoformat()==day and SINCE<=day<=UNTIL,day
    assert native['iso_date'](day)==day and native['date_num'](day)==int(day.replace('-',''))>0


def check_text(text):
    assert isinstance(text,str) and text.strip() and text==text.strip()
    assert not text_holds(text),text_holds(text)
    assert not re.search(r'<(?:p|div|sup|sub|span|math|img|table)\b|&(?:nbsp|amp|lt|gt);',text)
    assert '\\n' not in text and '\\t' not in text


def hold_list(row): return row.get('holds',row.get('rendered',{}).get('holds',[]))


def unit_key(row):
    return (row.get('source_id',row.get('response_id')),str(row['unit_index']))


def order(row): return (row['date'],*unit_key(row))


def build(s,g,d):
    native=native_functions(); L=load('1858-1859')
    grows={r['source_id']:r for r in g['rows']}; drows={r['response_id']:r for r in d['rows']}
    assert len(grows)==len(g['rows'])==len(L)==3031
    assert len(drows)==len(d['rows'])==205
    assert sum(len(r['accepted_edges']) for r in d['rows'])==221
    assert len({unit_key(r) for r in s['grounding']})==len(s['grounding'])
    assert len({unit_key(r) for r in s['conversations']})==len(s['conversations'])
    assert sum(len(r['export_decision']['units']) for r in d['rows'])==len(s['conversations'])
    assert len(s['grounding'])==sum(len(r['units']) for r in g['rows'] if r['state']=='scoped_pending_render_and_content_checks')+1
    grounds=sorted((r for r in s['grounding'] if not hold_list(r)),key=order)
    convos=sorted((r for r in s['conversations'] if not hold_list(r)),key=order)
    assert {r['source_id'] for r in grounds}.isdisjoint(drows)
    assert {r['source_id'] for r in grounds}.isdisjoint(q['source_id'] for r in convos for q in r['incoming'])
    source_pins={}; verified_spans=0; verified_blocks=0; transform_count=0

    def check_rendered(sid,rendered,spans=None):
        nonlocal verified_spans,verified_blocks,transform_count
        assert not rendered['holds'],(sid,rendered['holds'])
        check_text(rendered['content'])
        src=rendered['source'];key=src['path']
        if key not in source_pins:
            source_pins[key]={'path':key,'sha256':src['sha256']};assert_pin(source_pins[key])
        if 'primary_witness' in rendered:
            assert_pin(rendered['primary_witness'])
            witness=json.loads((ROOT/rendered['primary_witness']['path']).read_text())
            assert witness['content']==rendered['content']
            assert witness['content_sha256']==digest(rendered['content'].encode())
            assert witness['primary_verification']['all_nine_images_viewed_this_review']
            for page in witness['pages']:
                image=page['page_image'];assert_pin(image);source_pins[image['path']]=image
            return
        assert rendered['source']['sha256']==L[sid]['source']['sha256']
        blocks=rendered['blocks']
        if spans is not None:
            assert [b['scope'] for b in blocks]==spans,(sid,'span drift')
        for b in blocks:
            verified_blocks+=1
            a=b['source_audit'];assert not a['holds'] and not a['visual_nodes'],(sid,a)
            if 'scope' in b:
                scope=b['scope'];text=L[sid]['paragraphs'][scope['paragraph']-1]['text']
                assert text[scope['start']:scope['end']]==scope['original_excerpt']
                assert scope['source_sha256']==src['sha256'];verified_spans+=1
            transform_count+=len(b.get('transformations',[]))
        expected='\n\n'.join(b['text'] for b in blocks if b['text'])
        for extra in rendered.get('supplements',[]):
            check_rendered(sid,extra);expected+='\n\n'+extra['content']
        assert expected==rendered['content'],(sid,'content/block mismatch')

    files={}; provenance=[]; output_by_unit={}; docs=[]; titles=set(); targets=set(); questions=set(); memory_ids=set()
    for line,r in enumerate(grounds,1):
        sid=r['source_id'];row=grows[sid];idx=r['unit_index']
        assert row['state']=='scoped_pending_render_and_content_checks'
        if idx=='enclosure':
            assert sid=='DCP-LETT-2175' and r['date']=='1857-11-22'
            unit={'date':'1857-11-22','date_basis':'Separately dated authorial enclosure; final dateline excluded.',
                  'layer_scope':r['rendered']['layer_scope']}
            check_rendered(sid,r['rendered'])
        else:
            unit=row['units'][idx];assert unit['date']==r['date']
            assert row.get('accepted_disposition_pointers') or row.get('primary_graph_record') or unit.get('primary_section'),sid
            check_rendered(sid,r['rendered'],unit['spans'])
        doc=dict(r['document']);assert doc['content']==r['rendered']['content']
        doc['title']+=f' [{sid}; section {idx}]'
        assert set(doc)=={'title','link','date','content'}
        validate_day(doc['date'],native);check_text(doc['content'])
        assert doc['title'] not in titles; titles.add(doc['title'])
        content_hash=digest(doc['content'].encode())
        assert content_hash not in questions,('duplicate grounding text',sid)
        questions.add(content_hash);docs.append(doc)
        location={'path':'darwin_0/corpus/documents.jsonl','line':line}
        output_by_unit[('grounding',*unit_key(r))]=location
        provenance.append({'kind':'grounding',**location,'source_id':sid,'unit_index':idx,'date':doc['date'],
            'canonical_source_url':r['document']['link'],'content_sha256':content_hash,
            'source':r['rendered']['source'],'date_and_scope':unit,
            'snapshot_pointer':{'file':'inputs/rendered-staging.json','array':'grounding','source_id':sid,'unit_index':idx},
            'primary_plan_pointer':{'file':'inputs/grounding-plan.json','source_id':sid},
            'checks':{'no_content_holds':True,'original_spans_verified':True,'apparatus_excluded':True}})
    files['darwin_0/corpus/documents.jsonl']=jsonlines(docs)
    for number,r in enumerate(convos,1):
        sid=r['response_id'];row=drows[sid];unit=row['export_decision']['units'][r['unit_index']]
        assert unit['date']==r['date'];validate_day(r['date'],native)
        check_rendered(sid,r['answer'],unit['spans'])
        assert len(r['incoming'])==len(unit['inputs'])>0
        for q in r['incoming']:
            plan=next(x for x in unit['inputs'] if x['source_id']==q['source_id'])
            check_rendered(q['source_id'],q['rendered'],plan.get('spans'))
        t=dict(r['transcript']);t['participants']=dict(t['participants'])
        assert native['is_transcript'](t)
        assert set(t)=={'participants','exchanges','date','url','context'}
        assert set(t['participants'])=={'q','a'} and t['participants']['a']=='Charles Darwin'
        assert isinstance(t['participants']['q'],str) and t['participants']['q'].strip()
        assert t['participants']['q']!='Charles Darwin'
        assert isinstance(t['exchanges'],list) and len(t['exchanges'])==1
        exchange=t['exchanges'][0];assert isinstance(exchange,list) and len(exchange)==2
        for text in exchange:check_text(text)
        assert exchange[0]=='\n\n'.join(q['rendered']['content'] for q in r['incoming'])
        assert exchange[1]==r['answer']['content']
        content_hash=digest(exchange[1].encode())
        assert content_hash not in targets,('duplicate target text',sid)
        assert content_hash not in questions,('target also in grounding',sid)
        targets.add(content_hash)
        canonical=t['url'];base,_=urldefrag(canonical)
        t['url']=base+f'#raft-response-{sid}-{r["date"]}-section-{r["unit_index"]}'
        memory_id=''.join(c for c in t['url']+exchange[0][:20] if c.isalnum()).lower()
        assert memory_id not in memory_ids;memory_ids.add(memory_id)
        path=f'darwin_0/conversations/transcript-{number:04d}.json';files[path]=dump(t)
        output_by_unit[('conversation',*unit_key(r))]={'path':path}
        provenance.append({'kind':'conversation','path':path,'response_id':sid,'unit_index':r['unit_index'],
            'question_ids':[q['source_id'] for q in r['incoming']], 'date':r['date'],
            'canonical_source_url':canonical,'raft_exchange_id':memory_id,
            'question_sha256':digest(exchange[0].encode()),'answer_sha256':content_hash,
            'date_and_scope':unit,'original_date_constraints':row['metadata_audit'],
            'accepted_edges':[row['accepted_edges'][i] for i in unit['edge_indices']],
            'snapshot_pointer':{'file':'inputs/rendered-staging.json','array':'conversations','response_id':sid,'unit_index':r['unit_index']},
            'primary_plan_pointer':{'file':'inputs/direct-plan.json','response_id':sid},
            'checks':{'no_content_holds':True,'original_spans_verified':True,'apparatus_excluded':True,'native_schema':True}})

    holds=[]; outside=[]
    for row in g['rows']:
        if row['state']=='held':
            item={'kind':'grounding_source','source_id':row['source_id'],'reason':row['reason'],'date_constraints':row['date']}
            (outside if row['reason']=='outside_corpus_endpoint' else holds).append(item)
        for sub in row.get('held_subscopes',[]):
            holds.append({'kind':'grounding_subscope','source_id':row['source_id'],**sub})
    holds.append({'kind':'grounding_subscope','source_id':'DCP-LETT-2185','layer':'enclosure',
                  'reason':'Conjectural enclosure association/date; main letter considered separately.'})
    for row in d['rows']:
        if row['export_decision']['state']=='held':
            holds.append({'kind':'whole_response','response_id':row['response_id'],'reason':row['export_decision']['reason']})
        for sub in row.get('held_subscopes',[]):
            # Historical draft gate was explicitly resolved by the admitted 1857 enclosure.
            if row['response_id']=='DCP-LETT-2136' and sub.get('layer')=='authorial_enclosure':continue
            holds.append({'kind':'response_subscope','response_id':row['response_id'],**sub})
    for kind,rows in [('grounding',s['grounding']),('conversation',s['conversations'])]:
        for r in rows:
            if hold_list(r):
                holds.append({'kind':kind+'_rendered_unit','source_id':unit_key(r)[0],
                              'unit_index':r['unit_index'],'date':r['date'],'holds':hold_list(r)})
    account=[]
    for sid,row in grows.items():
        uses=[p for p in provenance if p.get('source_id')==sid or p.get('response_id')==sid or sid in p.get('question_ids',[])]
        account.append({'source_id':sid,'selection_state':row['state'],'selection_reason':row['reason'],
            'uses':[{'kind':p['kind'],'role':'question' if sid in p.get('question_ids',[]) else ('answer' if p['kind']=='conversation' else 'grounding'),
                     **{k:p[k] for k in ('path','line','unit_index') if k in p}} for p in uses]})
    relationships=[]
    for row in d['rows']:
        sid=row['response_id']
        for i,edge in enumerate(row['accepted_edges']):
            units=[(j,u) for j,u in enumerate(row['export_decision']['units']) if i in u['edge_indices']]
            emitted=[output_by_unit[('conversation',sid,str(j))] for j,u in units if ('conversation',sid,str(j)) in output_by_unit]
            held_scopes=[x for x in row.get('held_subscopes',[]) if x.get('edge_index')==i]
            assert units or row['export_decision']['state']=='held' or held_scopes,(sid,i,'unaccounted edge')
            relationships.append({'question_id':edge['question_id'],'response_id':sid,'ledger':edge['ledger'],
                'planned_response_sections':len(units),'exported_sections':emitted,
                'held_sections':len(units)-len(emitted),'held_subscopes':held_scopes,
                'whole_response_hold':row['export_decision'].get('reason') if row['export_decision']['state']=='held' else None})
    counts={'source_records_accounted':len(account),'accepted_direct_links':len(relationships),
        'accepted_response_sources':len(drows),'candidate_conversation_units':len(s['conversations']),
        'conversation_files':len(convos),'conversation_response_sources':len({r['response_id'] for r in convos}),
        'held_whole_responses':sum(x['kind']=='whole_response' for x in holds),
        'held_conversation_units':sum(bool(hold_list(r)) for r in s['conversations']),
        'candidate_grounding_units':len(s['grounding']),'grounding_documents':len(docs),
        'grounding_sources':len({r['source_id'] for r in grounds}),
        'held_grounding_units':sum(bool(hold_list(r)) for r in s['grounding']),
        'held_grounding_sources_before_rendering':sum(x['kind']=='grounding_source' for x in holds),
        'outside_window_sources':len(outside),'genuinely_excluded_from_grounding':sum(r['state']=='genuine_excluded' for r in g['rows']),
        'verified_output_body_spans':verified_spans,'verified_output_body_and_supplement_blocks':verified_blocks,
        'source_supported_markup_transformations':transform_count,'unique_output_source_files_checked':len(source_pins)}
    files['reports/raft-export/provenance.jsonl']=jsonlines(provenance)
    files['reports/raft-export/source-accounting.jsonl']=jsonlines(account)
    files['reports/raft-export/relationship-accounting.jsonl']=jsonlines(relationships)
    files['reports/raft-export/hold-queue.json']=dump({'window':{'since':SINCE,'until':UNTIL},'holds':holds,'outside_window':outside,
        'resolved_previous_plan_flags':[{'response_id':'DCP-LETT-2136','layer':'authorial_enclosure',
            'resolution':'Explicit 1857 authorial abstract rendered from original enclosure; old draft pending flag superseded by rendered source checks.'},
            {'source_id':'DCP-LETT-2175','layer':'enclosure','resolution':'Separate 1857-11-22 document; body remains dated 1857-11-23.'}],
        'note':'Counts have different units; source, response, section and relationship rows must not be added together.'})
    return files,counts,list(source_pins.values())


def load_inputs(check=False):
    paths={name:(REPORT/'inputs'/name if check else path) for name,path in SNAPSHOTS.items()}
    values={name:json.loads(p.read_text()) for name,p in paths.items()}
    staging=values['rendered-staging.json']
    if not check:
        for p in staging['inputs']:assert_pin(p)
    return values,paths


def main():
    ap=argparse.ArgumentParser();group=ap.add_mutually_exclusive_group()
    group.add_argument('--write',action='store_true');group.add_argument('--check',action='store_true')
    args=ap.parse_args();values,paths=load_inputs(args.check)
    files,counts,sources=build(values['rendered-staging.json'],values['grounding-plan.json'],values['direct-plan.json'])
    if args.check:
        manifest=json.loads((REPORT/'manifest.json').read_text())
        assert counts==manifest['counts']
        for p in manifest['inputs']+manifest['outputs']+manifest['source_files']+manifest['raft_implementation']:assert_pin(p)
        for relative,raw in files.items():assert (ROOT/relative).read_bytes()==raw,relative
        actual=sorted(p.name for p in (PROJECT/'conversations').glob('transcript-*.json'))
        assert actual==[f'transcript-{n:04d}.json' for n in range(1,counts['conversation_files']+1)]
        assert not (PROJECT/'conversations/benchmark.json').exists()
        result={'status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),
                'checks':'All written files, source pins, frozen selections, original text spans, native date/schema helpers, gapless numbering, unique RAFT IDs, exact text deduplication and response/grounding disjointness.',
                'counts':counts,'paid_or_network_operations':False}
        (REPORT/'validation.json').write_bytes(dump(result))
        manifest['status']='validated';manifest['validation']=pin(REPORT/'validation.json')
        (REPORT/'manifest.json').write_bytes(dump(manifest))
        print(json.dumps(result));return
    if not args.write:
        print(json.dumps({'status':'dry_run_passed','counts':counts}));return
    assert not (REPORT/'manifest.json').exists(),'Existing export: use --check; do not overwrite a frozen export.'
    for relative in files:assert not (ROOT/relative).exists(),f'Refusing overwrite: {relative}'
    assert not list((PROJECT/'conversations').glob('transcript-*.json'))
    assert not (PROJECT/'conversations/benchmark.json').exists()
    extras=[ROOT/'docs/raft-export-content-policy.md',ROOT/'docs/raft-formatting-readiness.md',
            PREP/'candidate-resolution.primary.json',PREP/'davy-1651A-text.primary.json',
            PREP/'source-boundary-clearance.working.json',PREP/'residual-header-clearance.primary.json',
            PREP/'routing-block-clearance.primary.json',ROOT/'scripts/clear_raft_routing_blocks.py',
            Path(__file__),ROOT/'scripts/raft_render_text.py',ROOT/'scripts/raft_export_text.py',ROOT/'scripts/render_raft_staging.py']
    # Pin all accepted ledger files and primary rendering decisions used by the plans.
    ledgers=set()
    def collect(value):
        if isinstance(value,dict):
            if isinstance(value.get('ledger'),str):ledgers.add(value['ledger'])
            for x in value.values():collect(x)
        elif isinstance(value,list):
            for x in value:collect(x)
    collect(values['grounding-plan.json']);collect(values['direct-plan.json'])
    extras.extend(ROOT/p for p in sorted(ledgers))
    extras.extend(sorted(PREP.glob('source-text-rendering-requirements.primary*.json')))
    input_pins=[pin(path) for path in dict.fromkeys(extras)]
    for name in paths:assert not (REPORT/'inputs'/name).exists()
    (REPORT/'inputs').mkdir(parents=True,exist_ok=True)
    for name,path in paths.items():
        dest=REPORT/'inputs'/name;dest.write_bytes(path.read_bytes());input_pins.append(pin(dest))
    output_pins=[]
    for relative,raw in files.items():
        dest=ROOT/relative;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);output_pins.append(pin(dest))
    manifest={'schema':'darwin.cumulative-raft-export.v1','status':'exported_pending_written_file_validation',
        'created_at':datetime.now(timezone.utc).isoformat(),'window':{'since':SINCE,'until':UNTIL,'inclusive':True},
        'counts':counts,'inputs':input_pins,'outputs':output_pins,'source_files':sources,
        'raft_implementation':[pin(RAFT/p) for p in ('convo_structurer.py','sources.py','memories.py','embeddings_helpers.py','generate_finetune.py')],
        'format_policy':{'exchanges_per_transcript':1,'dating':'Exact established response day or separately dated section; ambiguous days held.',
            'retrieval':'RAFT date_num strictly less than transcript day; no undated documents.',
            'ids':'Grounding titles include source and section IDs; transcript URLs have unique export fragments. These are export identifiers, not website anchors. Canonical URLs are in provenance.',
            'context':'Direct JSON writes preserve letter-specific context.',
            'snapshot':'One cumulative snapshot; earlier chronological groups are research provenance, not separate RAFT exports.'},
        'review_boundary':'Reuses full primary source readings and adjudication, then checks every selected source span and rendered block; source-specific header/voice/date/artifact decisions are retained in pinned plans. This is not a claim of a fresh manual rereading of every letter during conversion.',
        'training_embedding_or_generation_performed':False}
    (REPORT/'manifest.json').write_bytes(dump(manifest))
    print(json.dumps({'status':'written','counts':counts,'next':'Run --check against written files.'}))


if __name__=='__main__':main()

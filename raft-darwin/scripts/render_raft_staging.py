"""Render the cumulative reviewed selection outside the RAFT project."""
from __future__ import annotations
import hashlib
import json
import re
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from period_review import load
from raft_export_text import render_spans, render_supplement

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/raft-prep'


def pin(p):
    return {'path':str(p.relative_to(ROOT)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def person(evidence):
    names = []
    for e in evidence:
        text = e['text']
        if ', ' in text:
            surname, forename = text.split(', ',1); text = forename+' '+surname
        if text not in names: names.append(text)
    return ' and '.join(names)


SUPPLEMENTS = {'700':'supplemental','1732':'supplemental','1589':'enclosure',
               '1820A':'enclosure','2151':'enclosure','2222':'enclosure','2254':'enclosure',
               '2425':'enclosure','2437':'enclosure','2457':'enclosure','2136':'enclosure'}


def render_unit(source, unit):
    return render_spans(source, unit['spans'])


def append_supplements(source, rendered):
    short = source['id'].removeprefix('DCP-LETT-')
    if short not in SUPPLEMENTS: return
    for ordinal in (range(1,4) if short=='2457' else [1]):
        supplemental = render_supplement(source, SUPPLEMENTS[short],ordinal)
        rendered.setdefault('supplements',[]).append(supplemental)
        rendered['content'] += '\n\n'+supplemental['content']
        rendered['holds'].extend(supplemental['holds'])


def main():
    L = load('1858-1859')
    gp = OUT / 'grounding-review.working.json'; dp = OUT / 'direct-export-plan.working.json'
    G=json.loads(gp.read_text()); D=json.loads(dp.read_text())
    grounds=[]; conversations=[]; issues=[]
    for row in G['rows']:
        if row['state'] != 'scoped_pending_render_and_content_checks': continue
        src=L[row['source_id']]
        for i,u in enumerate(row['units']):
            rendered=render_unit(src,u);append_supplements(src,rendered)
            title=(row.get('document_kind') or 'To '+person(src['metadata_audit']['recipient_evidence']))+', '+u['date']
            grounds.append({'source_id':src['id'],'unit_index':i,'date':u['date'],
                            'rendered':rendered,'document':{'title':title,'link':src['source']['url'],
                                'date':u['date'],'content':rendered['content']}})
        if src['id']=='DCP-LETT-2175':
            rendered=render_supplement(src,'enclosure',drop_last=True)
            grounds.append({'source_id':src['id'],'unit_index':'enclosure','date':'1857-11-22',
                'rendered':rendered,'document':{'title':'Questions concerning Indian horses, 1857-11-22',
                    'link':src['source']['url'],'date':'1857-11-22','content':rendered['content']}})
    for row in D['rows']:
        src=L[row['response_id']]
        for i,u in enumerate(row['export_decision']['units']):
            a=render_unit(src,u);append_supplements(src,a);qs=[]
            names=[];holds=list(a['holds'])
            ordered_inputs=sorted(u['inputs'],key=lambda q:(L[q['source_id']]['metadata_audit']['xml_earliest'] or '',q['source_id']))
            for q in ordered_inputs:
                if q['state']=='held':
                    holds.append({'kind':'incoming_content_hold','source_id':q['source_id'],'reason':q['reason']});continue
                if q['state']=='printed_witness_pending_final_comparison':
                    holds.append({'kind':'printed_witness_pending','source_id':q['source_id']});continue
                if q['state']=='primary_verified_printed_witness':
                    witness_path=ROOT/q['witness'];w=json.loads(witness_path.read_text())
                    assert hashlib.sha256(w['content'].encode()).hexdigest()==w['content_sha256']
                    qr={'content':w['content'],'blocks':[],'holds':[],
                        'source':w['source'],'primary_witness':pin(witness_path),
                        'verification':w['primary_verification']}
                    qs.append({'source_id':q['source_id'],'rendered':qr})
                    if 'John Davy' not in names:names.append('John Davy')
                    continue
                qsrc=L[q['source_id']];qr=render_unit(qsrc,q);qs.append({'source_id':qsrc['id'],'rendered':qr})
                holds.extend({**h,'question_id':qsrc['id']} for h in qr['holds'])
                name=q.get('participant_override') or person(qsrc['metadata_audit']['sender_evidence'])
                if name not in names: names.append(name)
            # A pair has one questioner. Multiple letters by that person are
            # concatenated in established chronology, never duplicated answers.
            if len(names)>1:
                holds.append({'kind':'participant_conflict','names':names})
            text='\n\n'.join(q['rendered']['content'] for q in qs)
            name=names[0] if len(names)==1 else ' / '.join(names)
            form='letters' if len(u['inputs'])>1 else 'a letter'
            artifact={'participants':{'q':name,'a':'Charles Darwin'},'date':u['date'],
                'url':src['source']['url'],'context':f'{form} from {name}, which you are answering',
                'exchanges':[[text,a['content']]]}
            conversations.append({'response_id':src['id'],'unit_index':i,'date':u['date'],
                'incoming':qs,'answer':a,'holds':holds,'transcript':artifact})
    for kind,rows in [('grounding',grounds),('conversation',conversations)]:
        for r in rows:
            holds=r.get('holds',r.get('rendered',{}).get('holds',[]))
            if holds:issues.append({'kind':kind,'source_id':r.get('source_id',r.get('response_id')),
                                    'unit_index':r['unit_index'],'holds':holds})
    inputs=[pin(gp),pin(dp),pin(Path(__file__)),pin(ROOT/'scripts/raft_export_text.py'),pin(ROOT/'scripts/raft_render_text.py'),pin(OUT/'davy-1651A-text.primary.json')]
    summary={'grounding_units':len(grounds),'conversation_units':len(conversations),
             'held_grounding_units':sum(bool(r['rendered']['holds']) for r in grounds),
             'held_conversation_units':sum(bool(r['holds']) for r in conversations)}
    out={'status':'rendered_staging_pending_root_content_clearance','no_export':True,'inputs':inputs,
         'summary':summary,'grounding':grounds,'conversations':conversations}
    (OUT/'rendered-staging.working.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    (OUT/'rendered-issues.working.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary))
    print('Issue kinds:',dict(Counter(h['kind'] for r in issues for h in r['holds'])))

if __name__=='__main__': main()

"""Source-verified final addressee cuts; refresh only affected rendered units."""
import hashlib
import json
from pathlib import Path
from period_review import load
from raft_export_text import render_spans
from render_raft_staging import pin

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/raft-prep'
DROPS={'1103F':3,'1158A':5,'1466G':4,'1466H':4,'1507F':3,
       '2283F':3,'2377F':3,'507':3,'907':3,'402A':4}


def main():
    gp=OUT/'grounding-review.working.json';dp=OUT/'direct-export-plan.working.json'
    sp=OUT/'rendered-staging.working.json'
    G=json.loads(gp.read_text());D=json.loads(dp.read_text());S=json.loads(sp.read_text())
    report=OUT/'routing-block-clearance.primary.json'
    assert not report.exists(),'This additive clearance has already run.'
    for item in S['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    L=load('1858-1859');changes=[]

    def cut(sid,unit):
        short=sid.removeprefix('DCP-LETT-');kept=[]
        for span in unit['spans']:
            n=span['paragraph'];text=L[sid]['paragraphs'][n-1]['text']
            assert text[span['start']:span['end']]==span['original_excerpt']
            if DROPS.get(short)==n:
                assert text.startswith('To | ')
                changes.append({'source_id':sid,'original_span':span,'action':'exclude_addressee_block'})
                continue
            if short=='907' and n==2:
                end=text.index(' Down House')
                changes.append({'source_id':sid,'original_span':span,'action':'exclude_trailing_address','cut_before':' Down House'})
                span={**span,'end':end,'original_excerpt':text[span['start']:end]}
            kept.append(span)
        unit['spans']=kept

    grows={r['source_id']:r for r in G['rows']};drows={r['response_id']:r for r in D['rows']}
    for row in G['rows']:
        if row['source_id'].removeprefix('DCP-LETT-') in DROPS:
            for u in row.get('units',[]):cut(row['source_id'],u)
    for row in D['rows']:
        if row['response_id'].removeprefix('DCP-LETT-') in DROPS:
            for u in row['export_decision']['units']:cut(row['response_id'],u)
    for r in S['grounding']:
        sid=r['source_id']
        if sid.removeprefix('DCP-LETT-') not in DROPS:continue
        assert not r['rendered'].get('supplements')
        rendered=render_spans(L[sid],grows[sid]['units'][r['unit_index']]['spans'])
        r['rendered']=rendered;r['document']['content']=rendered['content']
    for r in S['conversations']:
        sid=r['response_id']
        if sid.removeprefix('DCP-LETT-') not in DROPS:continue
        assert not r['answer'].get('supplements') and not r['holds']
        rendered=render_spans(L[sid],drows[sid]['export_decision']['units'][r['unit_index']]['spans'])
        assert not rendered['holds']
        r['answer']=rendered;r['transcript']['exchanges'][0][1]=rendered['content']
    G['routing_block_rules_pin']=pin(Path(__file__));D['routing_block_rules_pin']=pin(Path(__file__))
    for path,value in [(gp,G),(dp,D)]:path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    S['inputs']=[pin(ROOT/p['path']) for p in S['inputs']]+[pin(Path(__file__))]
    issues=[]
    for kind,rows in [('grounding',S['grounding']),('conversation',S['conversations'])]:
        for r in rows:
            holds=r.get('holds',r.get('rendered',{}).get('holds',[]))
            if holds:issues.append({'kind':kind,'source_id':r.get('source_id',r.get('response_id')),'unit_index':r['unit_index'],'holds':holds})
    S['summary']['held_grounding_units']=sum(bool(r['rendered']['holds']) for r in S['grounding'])
    S['summary']['held_conversation_units']=sum(bool(r['holds']) for r in S['conversations'])
    for path,value in [(sp,S),(OUT/'rendered-issues.working.json',issues),
                       (report,{'status':'primary_source_verified','rules':pin(Path(__file__)),'changes':changes})]:
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cuts':len(changes),'summary':S['summary']}))

if __name__=='__main__':main()

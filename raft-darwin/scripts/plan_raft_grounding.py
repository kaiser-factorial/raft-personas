"""Project primary authorship/date restrictions into an auditable grounding plan."""
import hashlib,json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).parent))
from period_review import load
ROOT=Path(__file__).resolve().parents[1]

def pin(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def idof(x):return 'DCP-LETT-'+x
HOLD={
'1195':'Written weekday and calendar date conflict.', '1283':'October7Sunday versus writtenMonday and October8 alternative.', '1310':'March8 conjectural; March15 alternative remains.',
'1244':'Garbled duplicated Reader clause has no supported fluent repair.',
'1287':'Broken subtraction/layout and diagram need faithful source rendering.',
'1340':'Unresolved raw120,000th numeric typography.', '1345':'Unresolved18glass typography and source diagram.',
'1386':'Unresolved45s source typography.', '1428':'Unresolved12porterage typography.',
'1490':'Account layout diag/ramme and currency require separately checked source rendering.',
'1501':'Unresolved125th typography and source diagrams.',
'1554A':'Duplicated damaged Beagle/booms/trade-wind passage unresolved.',
'1620':'Unresolved optical numerals110 and18, no fraction markup.',
'1660':'Unresolved1610ft multiplication/dimensions typography.',
'1675':'Broken abstract diag/ramme formatting unresolved.',
'1710':'Source species/condition table alignment unresolved.',
'1712':'Diagram-dependent main body and independently uncertain P7–9 postscript.',
'1745':'Broken specimen list diag/ramme layout unresolved.',
'1766':'Broken specimen list diag/ramme layout unresolved.',
'1788':'Unresolved1100th source typography.',
'1796':'Unresolved13542th/13395th/13600th source typography.',
'1860':'Substantive routing instructions mixed with unresolved diag/ramme/SYMBOL.',
'1871':'Unresolved110 source typography.',
'1943':'Substantive routing instructions mixed with unresolved diag/ramme/SYMBOL.',
'1980':'November1Saturday versus sourceSunday date conflict; diagrams.',
'1981':'Broken five-category nine-skin list layout unresolved.',
'2019':'Vase bare s and clock86 currency unresolved.',
'2068':'Substantive routing instructions mixed with unresolved diag/ramme/SYMBOL.',
'2089':'P4 plain18 proportion unresolved; other MathML cannot repair it.',
'2097':'Unlabelled1 12 0 amount cannot be assigned currency units.',
'2107':'Printed/editorial year conflict; no exact composition day.',
'2155':'Keel-pistil reading unresolved; editor EarlyMazagan span also requires exclusion.',
'2237':'Cannot collect never my wits and SYMBOL artifacts unresolved.',
'2239':'Such as I have always later artifact unresolved.',
'2264':'AprilWednesday may21or28; exact day unresolved.',
'2351':'330/550/£2s2 currency typography unresolved.',
'2361F':'Dot-in-circle source marker unresolved; annotation answers excluded.',
'2446':'Ensure heavy loss and conjectural0-scientific reading unresolved.',
'2527':'SaturdayNovember12versus19 alternatives.',
'2532':'TuesdayNovember15versus22 alternatives.',
}
EXCLUDE={'330':'Minute-book report of letter, not verbatim Darwin prose.','766':'Joint Charles/Emma financial instrument with other hand.','779':'Joint instrument with other hand and later signing.','1078':'Editorial synopsis, authentic body unavailable.','1201':'Editorial synopsis, authentic body unavailable.','1570':'Exhibition catalogue synopsis, no verbatim Darwin body.'}
PARS={'50':[5,6], '1134':[1,2,3,4], '1234':[1,2,3,4,5], '1337':[1,2,3,4], '1417':[1,2,3], '1426':[1,2,3], '1875':[2]}
DROP={'2347':[6]}
# Exact source-based cuts are added by a separate root-reviewed fragment step.
CUT_PENDING={'1230':'Extract only genuine Darwin quotation within catalogue synopsis.', '1337':'P4 stop before editorial From Emma Darwin heading.', '1426':'P3 stop before Emma salutation My dearest Fanny.', '1834':'P5 remove place/dateline while preserving pea request.', '2058':'Remove terminal addressee R Kippist Esq.', '2492':'Separate itinerary from terminal address and ramme artifact.'}
SUPPLEMENT={'700','1732','1589','1820A','2151','2175','2222','2254','2425','2437','2457','2185'}

def main():
    L=load('1858-1859');basep=ROOT/'reports/raft-prep/candidates/grounding-plan.luna.json';base=json.loads(basep.read_text())
    reqp=ROOT/'reports/raft-prep/candidates/ground-requirements.luna.json';reqs={r['source_id']:r for r in json.loads(reqp.read_text())['requirements']}
    gp=ROOT/'reports/1837-1843/correspondence-map/graph.json';graph=json.loads(gp.read_text());nodes={n['id']:n for n in graph['nodes']}
    rows=[]
    for b in base['plans']:
        ident=b['source_id'];short=ident.removeprefix('DCP-LETT-');src=L[ident];a=src['metadata_audit'];r={**b,'date':{**b['date'],'original_label':a.get('original_csv',{}).get('date')},'source_requirements':reqs.get(ident,{}).get('requirements',[]),'units':[]}
        if b['state']!='candidate_pending_render_check':rows.append(r);continue
        n=nodes.get(ident)
        if short in EXCLUDE:r.update(state='genuine_excluded',reason=EXCLUDE[short]);rows.append(r);continue
        if n and (not n.get('individual_Darwin_voice_eligible') or n.get('text_scope',{}).get('english_voice_training_eligible') is False):
            r.update(state='held',reason='Primary1837graphvoice/sourcehold',primary_graph_record=n);rows.append(r);continue
        if n and n.get('whole_letter_scalar_date') is None:
            r.update(state='held',reason='Primary1837graphexactdatehold',primary_graph_record=n);rows.append(r);continue
        if short in HOLD:r.update(state='held',reason=HOLD[short]);rows.append(r);continue
        selection=PARS.get(short,list(range(1,len(src['paragraphs'])+1)));selection=[x for x in selection if x not in DROP.get(short,[])]
        spans=[]
        sc=n.get('text_scope',{}) if n else {}
        if sc.get('voice_spans') or sc.get('voice_paragraphs'):
            selection=sc.get('voice_paragraphs',[])
            for s in sc.get('voice_spans',[]):spans.append({'paragraph':s['body_paragraph'],'start':s['char_start'],'end':s['char_end']})
        for num in selection:spans.append({'paragraph':num,'start':0,'end':len(src['paragraphs'][num-1]['text'])})
        for s in spans:
            text=src['paragraphs'][s['paragraph']-1]['text'];assert 0<=s['start']<s['end']<=len(text),(ident,s)
            s['original_excerpt']=text[s['start']:s['end']];s['source_sha256']=src['source']['sha256']
        r['units']=[{'date':a['xml_earliest'],'spans':sorted(spans,key=lambda s:(s['paragraph'],s['start'])),'date_basis':'Primary composition date, retaining supplied components and original XML constraints in sidecar.'}]
        r['state']='scoped_pending_render_and_content_checks'
        if short in CUT_PENDING:r['pending_fragment_check']=CUT_PENDING[short]
        if short in SUPPLEMENT:r['pending_authorial_supplement']=True
        if n:r['primary_graph_record']=n
        rows.append(r)
    out={'status':'root_primary_requirement_and_voice_scope_review_in_progress','cutoff':'1859-11-24','no_export':True,'inputs':[pin(basep),pin(reqp),pin(gp),pin(Path(__file__))],'counts':dict(Counter(r['state'] for r in rows)),'rows':rows}
    p=ROOT/'reports/raft-prep/grounding-review.working.json';p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out['counts']))
if __name__=='__main__':main()

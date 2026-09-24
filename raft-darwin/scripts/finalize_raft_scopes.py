"""Root content review: primary exclusions, dated sections and literal headers."""
import hashlib
import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
from period_review import load

ROOT=Path(__file__).resolve().parents[1]
L=load('1858-1859')
GP=ROOT/'reports/raft-prep/grounding-review.working.json'
DP=ROOT/'reports/raft-prep/direct-export-plan.working.json'
G=json.loads(GP.read_text());D=json.loads(DP.read_text())
GR={r['source_id']:r for r in G['rows']}


def source_span(ident,n,start=0,end=None):
    src=L[ident];t=src['paragraphs'][n-1]['text'];end=len(t) if end is None else end
    while start<end and t[start].isspace():start+=1
    while end>start and t[end-1].isspace():end-=1
    assert start<end,(ident,n,start,end)
    return {'paragraph':n,'start':start,'end':end,'original_excerpt':t[start:end],
            'source_sha256':src['source']['sha256']}


HOLDS={
    '1522':'Primary exact-day hold: July15,16,17 or unknown in actual dateline.',
    '2157':'Primary exact-day hold: catalogued October23 versus October30 Friday before October31.',
    '2255A':'Oral question memorandum with undated later insertions and cancellations.',
    '2466':'Primary exact-year hold: supplied1859 lacks conclusive support.',
    '733':'Primary exact-date hold: assigned January27 derived from intermediary, not established composition.',
    '761':'Original1844 letter incorporates later authorial revisions with unresolved dates.',
    '2342':'Assumed year remains under primary date review; no independently established exact date.',
}
EXCLUSIONS={
    '1070F':'Collective signatories; primary ledger explicitly excludes individual Darwin voice.',
    '2365':'Editorial appendix and collective memorials; Darwin only a signatory, not individual author.',
}
for short,reason in {**HOLDS,**EXCLUSIONS}.items():
    r=GR['DCP-LETT-'+short]
    r.update(state='genuine_excluded' if short in EXCLUSIONS else 'held',reason=reason,units=[])

# Calendar days are composition sections, never a last-date proxy for the whole.
for short,sections in {
    '158':[('1832-02-08',range(1,7)),('1832-02-26',range(7,10)),('1832-03-01',range(10,17))],
    '913':[('1845-09-03',range(1,3)),('1845-09-04',[3])],
    '754F':[('1844-06-01',range(1,4))],
}.items():
    ident='DCP-LETT-'+short;r=GR[ident]
    r['units']=[{'date':date,'spans':[source_span(ident,n) for n in ns],
                 'date_basis':'Primary source dateline and explicit continuation boundary, root verified.'}
                for date,ns in sections]
    if short=='754F':r['held_subscopes']=[{'paragraphs':[4,5],'reason':'Later undated continuation; June1 belongs only to P1–3.'}]

# Actual Darwin notes, explicitly attributed reported speech retained in prose.
r=GR['DCP-LETT-798']
r['units'][0]['spans']=[s for s in r['units'][0]['spans'] if s['paragraph']>=4]
r['document_kind']='Darwin notes arising from conversations with Joseph Dalton Hooker'
r['excluded_scope']='Editorial AppendixIII heading and source title/dateline P1–3.'

# Publisher document attached to a letter is not Darwin's authored body.
ident='DCP-LETT-843';r=GR[ident];t=L[ident]['paragraphs'][1]['text']
assert t.count('London Sept.')==1
r['units'][0]['spans']=[source_span(ident,1),source_span(ident,2,end=t.index('London Sept.'))]
r['excluded_scope']='Copied1837 Colburn agreement and document heading, distinct from1845 Darwin letter.'

# Catalogue summaries are excluded; only the verbatim quoted fragments survive.
for short,marker in [('757','… I have'),('852','I consider your having'),('972','… My health')]:
    ident='DCP-LETT-'+short;r=GR[ident];t=L[ident]['paragraphs'][0]['text']
    assert t.count(marker)==1
    r['units'][0]['spans'][0]=source_span(ident,1,start=t.index(marker))
    last=r['units'][0]['spans'][-1];text=L[ident]['paragraphs'][last['paragraph']-1]['text']
    end=text.rfind('’')
    if end>=0 and len(text[end:])<=3:
        last['end']=end;last['original_excerpt']=text[last['start']:end]
    r['excluded_scope']='Catalogue narrator and quotation wrapper; genuine surviving Darwin quotation only.'

DROP={
    '131':[4],'142':[4],'146':[4],'148':[8],'310':[6],'311':[2],'320':[3],
    '357':[4],'361A':[4],'366F':[5],'370F':[7],'383F':[4],'394':[5],'395':[4],
    '415':[4],'454':[3],'459':[3],'491':[6],'497':[6],'499':[2],'565G':[3],
    '59':[8],'593':[3],'87':[9], '381A':[2],'402F':[4],'506':[4],'803A':[5],
}
# Literal start markers mark authorial prose after a header, not regex guesses.
START={
    ('1301',4):'P.S.',('1402',3):'We expect',('158',7):'On the 10th',
    ('158',10):'I arrived',('481',6):'After doing',('673',2):'I was called',
    ('913',3):'I had not time',('153',5):'I have just had',('153',6):'I got your second',
    ('184',2):'When I wrote',('184',3):'Again was I stopped',('425',3):'Many thanks',
    ('444',3):'On Friday Caroline',('448',7):'I was delighted',('466',3):'Once',
    ('484',7):'Fanny has just called',('2307',9):'The E.I.C',
    ('305',7):'There is a Ship',
}
END={('1836',5):'King’s Cliff'}
changes=[]


def apply(ident,unit):
    short=ident.removeprefix('DCP-LETT-');result=[]
    for s in unit.get('spans',[]):
        n=s['paragraph'];old=s.copy();t=L[ident]['paragraphs'][n-1]['text']
        if n in DROP.get(short,[]):
            changes.append({'source_id':ident,'paragraph':n,'action':'exclude_header_or_layout_marker','original_excerpt':s['original_excerpt']});continue
        if (short,n) in START:
            m=START[(short,n)];assert t.count(m)==1,(ident,n,m)
            s=source_span(ident,n,max(s['start'],t.index(m)),s['end'])
        if (short,n) in END:
            m=END[(short,n)];assert t.count(m)==1
            s=source_span(ident,n,s['start'],min(s['end'],t.index(m)))
        if s!=old:changes.append({'source_id':ident,'paragraph':n,'action':'exclude_inline_header',
                                 'before':old,'after':s})
        result.append(s)
    unit['spans']=result


for r in G['rows']:
    for u in r['units']:apply(r['source_id'],u)
for r in D['rows']:
    for u in r['export_decision']['units']:
        apply(r['response_id'],u)
        for q in u['inputs']:
            if q.get('spans'):apply(q['source_id'],q)
            if q['source_id']=='DCP-LETT-1651A':
                q.update(state='primary_verified_printed_witness',witness='reports/raft-prep/davy-1651A-text.primary.json')

pin={'path':str(Path(__file__).relative_to(ROOT)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
for d,p in [(G,GP),(D,DP)]:
    d['content_scope_rules_pin']=pin
    d['status']='root_source_voice_date_header_scopes_checked_pending_final_render'
    if p==GP:d['counts']=dict(Counter(r['state'] for r in G['rows']))
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
out={'status':'root_reviewed_source_boundaries','rules':pin,'changes':changes,
     'note':'Primary voice/date decisions supersede single-key sender and single XML sorting date heuristics.'}
(ROOT/'reports/raft-prep/source-boundary-clearance.working.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'grounding_counts':G['counts'],'literal_boundary_changes':len(changes)}))

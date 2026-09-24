"""Pin root-inspected reply excerpts to original retained-block character offsets."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from period_review import load
ROOT=Path(__file__).resolve().parents[1]
L=load('1858-1859')
# start inclusive, stop exclusive. Each marker is literal source text.
C={
('164',4):[('I this morning received','We lay to')],
('164',6):[('I direct of course','I want to write to Charlotte')],
('171',4):[(None,'I am very good friends')],
('171',10):[(None,'Excuse this')],
('207',4):[(None,'I have told you nothing')],
('230',1):[(None,'Since I wrote from B. Ayres')],
('242',1):[('I have received your letter','Since leaving the Plata')],
('248',1):[('I have received the whole series','I wrote last from the Falkland')],
('248',2):[('You ask me about the specimens',None)],
('248',5):[('I am much pleased to hear my Father',None)],
('248',7):[('I am much obliged for your chain','Thank Granny')],
('251',1):[('By what fatality',None)],
('251',3):[(None,'With respect to the December letter')],
('253',1):[('I am much pleased, with what you have told me',None)],
('275',1):[(None,'I returned a week ago')],
('275',4):[('Amongst the various pieces of news',None)],
('289',9):[(None,'I am almost afraid')],
('973',1):[('I have sent off the Ascension plants',None)],
('1239',2):[('I have considered to the very best',None)],
('1562',2):[(None,'I am very glad to hear of the second Edit.'),('I shall be curious to hear what Humboldt',None)],
('1601',1):[(None,'I have been trying to do')],
('1866',1):[(None,'but I wish')],
('1867',3):[(None,'If any fact should ever occur')],
('1874',1):[(None,'By the way what a noble')],
('1924',1):[(None,'By the way do you remember'),('With respect to crossing','By the way R. Brown')],
('1938',1):[('I quite agree about Lyell',None)],
('2010',1):[(None,'I have attended a little')],
('2018',1):[(None,'It is a most tiresome drawback')],
('2018',2):[(None,'Give my best thanks')],
('2094',2):[(None,'Prof. Huxley')],
('2094',3):[('I am glad Lyell',None)],
('2109',1):[(None,'It is extremely kind'),('Your remarks on that head',None)],
('2189',1):[(None,'All the other forms')],
('2192',1):[('You say that you have been somewhat surprised',None)],
('2311',1):[(None,'I think your Introduction')],
('2313',1):[(None,'But I write now')],
('2368',1):[(None,'I have received from a Gardener')],
('2388',14):[(None,'When we are dead and gone')],
('2411',1):[(None,'What a splendid joke')],
('2411',3):[('Your cases of important organs',None)],
('2851',1):[(None,'I am sorry about Siberia'),('I shd like to put in some such sentence',None)],
('2479A',1):[(None,'Now these facts made me anxious')],
('2542',3):[(None,'I had a letter from him')],
('2547',2):[('But I will as far as I can',None)],
('2547',3):[('About Rattle-snake',None)]
}
def bounds(text,start,stop):
    assert start is None or text.count(start)==1,(start,text)
    assert stop is None or text.count(stop)==1,(stop,text)
    lo=text.index(start) if start else 0;hi=text.index(stop) if stop else len(text)
    assert lo<hi
    while lo<hi and text[lo].isspace():lo+=1
    while hi>lo and text[hi-1].isspace():hi-=1
    return lo,hi
p=ROOT/'reports/raft-prep/direct-export-plan.working.json';d=json.loads(p.read_text())
for r in d['rows']:
    short=r['response_id'].removeprefix('DCP-LETT-');source=L[r['response_id']]
    for u in r['export_decision']['units']:
        out=[];seen=set()
        for s in u['spans']:
            n=s['paragraph'];t=source['paragraphs'][n-1]['text'];key=(short,n)
            if key in C:
                if key in seen:continue
                seen.add(key)
                for a,b in C[key]:
                    lo,hi=bounds(t,a,b);out.append({'paragraph':n,'start':lo,'end':hi,'original_excerpt':t[lo:hi],'source_sha256':source['source']['sha256'],'basis':'Root inspected exact canonical paragraph and narrowed to accepted response content; excluded unrelated or missing inputs.'})
            else:
                assert 'cut_pending' not in s,(short,s)
                lo=s.get('start',0);hi=s.get('end',len(t));lo=0 if lo is None else lo;hi=len(t) if hi is None else hi
                assert 0<=lo<hi<=len(t),(short,s,len(t))
                out.append({**s,'start':lo,'end':hi,'original_excerpt':t[lo:hi],'source_sha256':source['source']['sha256']})
        # 1239 Athenaeum answer is a safe additional excerpt of the same scoped reply.
        if short=='1239':
            t=source['paragraphs'][1]['text'];lo,hi=bounds(t,*C[(short,2)][0]);out.append({'paragraph':2,'start':lo,'end':hi,'original_excerpt':t[lo:hi],'source_sha256':source['source']['sha256']})
            u['inputs']=[x for x in u['inputs'] if x['source_id']=='DCP-LETT-1220'];u['edge_indices']=[1]
            r['held_subscopes']=[{'edge_index':0,'reason':'Geological answer P1–4 also depends on unlocated Hooker-to-Lyell Nepal narrative; preserve historical1219 link, exclude unsupported geological target.'}]
        u['spans']=sorted(out,key=lambda s:(s['paragraph'],s['start']))
    if short=='1695':r['held_subscopes']=[{'paragraph':3,'reason':'Four raw numeric strings unresolved per primary addendum12; retain other independent response paragraphs.'}]
    if short=='2136':r['held_subscopes']=[{'layer':'authorial_enclosure','reason':'Needs separately attributed enclosure extraction; not covered by retained body renderer.'}]
d['status']='root_response_spans_resolved_pending_render_and_incoming_checks'
d['fragment_rules_pin']={'path':str(Path(__file__).relative_to(ROOT)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('Resolved and pinned',sum(len(u['spans']) for r in d['rows'] for u in r['export_decision']['units']),'response spans')

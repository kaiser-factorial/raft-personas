"""Root-reviewed projection of accepted reply scopes; no training export writes."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).parent))
from period_review import load
ROOT=Path(__file__).resolve().parents[1]
ID=lambda x:'DCP-LETT-'+str(x)

def ps(spec):
    out=[]
    for part in spec.split(','):
        a=part.split('-');out.extend(range(int(a[0]),int(a[-1])+1))
    return [{'paragraph':p} for p in out]

# Each entry below was read against the original accepted response_scope prose.
# A missing mapping is an error, never implicit permission for a whole letter.
SCOPES={
'164':'4,6','206':'1,4','207':'1,3,6','209':'1-3','230':'1','242':'1','251':'2','253':'1-3','275':'1,4,5,10','289':'4,9',
'973':'2-8','996':'3,5-12','1003':'1-7','1098':'1-4','1174':'1-9','1197':'1','1202':'1,2,4,5','1221':'1-10','1225':'1-11','1227':'1-5','1236':'1-4','1239':'5,6','1260':'1-9','1339':'2,3,5,6',
'1484G':'1-3','1485':'1-3','1509':'3-6','1540':'1-7','1556':'1-10','1562':'2','1573':'1-7','1577':'1-8','1588':'1-4','1597':'4-6','1601':'','1609':'3','1610':'1-3','1612':'1-4','1643':'1-7','1653':'1-4','1654':'1-6','1695':'1,2,4-10','1696':'1-9,11-13','1717':'2,3','1725':'1-4','1727':'1-4','1734':'2-6','1750':'1-7','1777':'1-3,5,6','4354':'1-3',
'1843':'1-4','1843A':'1-3','1856':'1,2,4-10,12,13','1866':'2,3,6','1867':'2','1870':'2','1874':'2','1879':'1,2','1885F':'1,2','1910':'2-6','1917':'1-4','1919':'4-10','1924':'4-7','1931':'1-4','1938':'2-6','1939':'1,2,4','1944':'1,2,6','1964':'1,2','1973':'1,2,6,7','1991':'2','1993':'1-3','1997':'2,3','1999':'1-5','2010':'','2018':'3','2020F':'6-8','2037G':'1,2','2057':'4','2075':'1,2','2094':'1','2109':'2-4','2116':'2,3','2122':'1-6','2125':'1-5','2136':'3,6-8,10','2150':'1-7','2180':'6','2182':'1-6','2189':'','2192':'','2194':'1,3,5,6,8',
'2203':'7-9','2228':'1-3','2233':'1-3','2235':'1','2242':'1-5,8','2269':'1,6','2296':'3,4','2311':'2-7,9','2313':'','2346H':'1,3-9,11','2348F':'1-3','2361':'1-4,6-10,12','2368':'2,4','2369':'1,3,4','2384':'1-5,13-15','2388':'2-5,7','2406':'1-7,9','2411':'4','2429':'8','2430':'1-4','2434':'1-5','2445':'1-5','2851':'2-4','2476H':'1,2','2479A':'','2503':'1-16,19-25','2507':'5,6','2510':'1-4,7-10','2513':'1-5','2514':'1-6','2542':'1,2,4,5','2543':'3,4','2547':'1'
}
# Literal marker cuts are resolved and pinned against the canonical original text.
CUTS={
'207':[(4,None,'I saw your Sisters')],
'251':[(1,None,None),(3,None,'With respect to the December letter')],
'973':[(1,'I have sent off the Ascension plants',None)],
'1601':[(1,None,'which I have been studying on the map.')],
'1866':[(1,None,'Your letter')],
'1867':[(3,None,None)],
'1874':[(1,None,'By the way')],
'1924':[(1,None,'By the way'),(1,'With respect to crossing',None)],
'1938':[(1,None,None)],
'2010':[(1,None,None)],
'2018':[(1,None,None),(2,None,None)],
'2094':[(2,None,None),(3,None,None)],
'2109':[(1,None,None)],
'2189':[(1,None,None)],
'2192':[(1,'You say that you have been somewhat surprised','speculative notions.')],
'2311':[(1,None,None)],
'2313':[(1,None,None)],
'2368':[(1,None,None)],
'2388':[(14,None,None)],
'2411':[(1,None,None),(3,None,None)],
'2851':[(1,None,None)],
'2479A':[(1,None,'I have as yet made no precise measurements.')],
'2542':[(3,None,None)],
'2547':[(2,None,None),(3,'About Rattle-snake',None)]
}
SPECIAL_DATES={'164':'1832-04-05','206':'1833-05-22','251':'1834-07-24','253':'1834-08-09'}
HOLDS={'2032':'Only broad before-date, no exact composition day.','139':'Mutually exclusive October4/11,1831 dates.','169':'Initial response section has no established exact day.','172':'June1–6 range not an exact day.','188':'Undated acknowledgement section before November11.','238':'March1834 month only.','282':'Corrected August9–12,1835 interval.','863':'May1845 interval.','864A':'AfterMay22,1845 no bounded composition day.','892':'July22–August19 interval.','963':'Mutually exclusive March29/April5 dates.','1899':'June11–20 outer interval, no exact day.','2060':'March16–31 interval, no exact day.','1480A':'Question survives only in editorial footnote; user excludes that content layer.'}

def pin(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    path=ROOT/'reports/raft-prep/direct-export-plan.working.json';d=json.loads(path.read_text());letters=load('1858-1859')
    g=json.loads((ROOT/'reports/1837-1843/correspondence-map/graph.json').read_text());secs={s['id']:s for s in g['dated_sections']}
    unknown=[]
    for r in d['rows']:
        ident=r['response_id'];short=ident.removeprefix('DCP-LETT-');a=r['metadata_audit'];edges=r['accepted_edges'];groups=defaultdict(lambda:{'spans':[],'incoming_ids':[],'edge_indices':[]})
        if short in HOLDS:
            r['export_decision']={'state':'held','reason':HOLDS[short],'units':[]};continue
        def add(date,spans,edge_indices):
            unit=groups[date];unit['spans'].extend(x for x in spans if x not in unit['spans'])
            for i in edge_indices:
                if i not in unit['edge_indices']:unit['edge_indices'].append(i)
                q=edges[i]['question_id']
                if q not in unit['incoming_ids']:unit['incoming_ids'].append(q)
        if short=='171':
            add('1832-05-18',ps('4'),[0]);add('1832-06-16',[{'paragraph':10,'cut_pending':'first sentence only: Ramsay print request'}],[0])
        elif short=='248':
            add('1834-07-20',ps('1,2,5'),[0]);add('1834-07-29',[{'paragraph':7,'cut_pending':'chain thanks and pencil-case use only'}],[1])
        elif short=='1986':
            add('1856-11-11',ps('1,2'),[0]);add('1856-11-12',ps('10,11'),[0])
        elif short=='2371':
            add('1858-11-24',ps('5,6'),[0]);add('1858-11-25',ps('11'),[0])
        elif short in SCOPES:
            date=SPECIAL_DATES.get(short,a['xml_earliest'])
            add(date,ps(SCOPES[short]) if SCOPES[short] else [],list(range(len(edges))))
            if short in CUTS:
                for p,s,e in CUTS[short]:groups[date]['spans'].append({'paragraph':p,'cut_pending':{'start_marker':s,'end_marker':e}})
        else:
            for i,e in enumerate(edges):
                scope=e['scope'];ss=scope.get('response_sections') or []
                if ss:
                    for sec in ss:
                        if isinstance(sec,str):
                            sec=secs[sec];add(sec['date'],[{'paragraph':p} for p in sec['paragraphs']],[i])
                        elif sec.get('body_paragraphs'):
                            add(sec.get('date') or a['xml_earliest'],[{'paragraph':p} for p in sec['body_paragraphs']],[i])
                        elif sec.get('body_paragraph'):
                            start=sec.get('start_char',sec.get('char_start'));end=sec.get('end_char',sec.get('char_end'))
                            add(sec.get('date') or a['xml_earliest'],[{'paragraph':sec['body_paragraph'],'start':start,'end':end}],[i])
                        elif sec.get('scholarly_section_class'):
                            r.setdefault('held_subscopes',[]).append({'scope':sec,'reason':'Outside body layer and no exact dated section; retain separate source, no automatic export.'})
                        else:unknown.append((short,sec))
                elif scope.get('response_paragraphs'):
                    add(a['xml_earliest'],[{'paragraph':p} for p in scope['response_paragraphs']],[i])
                elif scope.get('response_scope') in ['single_date_surviving_body','whole_surviving_body'] or e['source_family']=='1828-1836 legacy':
                    add(a['xml_earliest'],ps(f'1-{r["paragraph_count"]}'),[i])
                else:unknown.append((short,scope))
        units=[]
        for date,u in groups.items():
            u['date']=date;u['spans'].sort(key=lambda x:(x['paragraph'],x.get('start') or 0));u['scope_basis']='Root read accepted scope and date policy; exact original paragraph/codepoint coordinates, renderer clearance pending.'
            u['inputs']=[{'source_id':q,'scope':'retained_body_pending_voice_and_content_clearance'} for q in u.pop('incoming_ids')];units.append(u)
        r['export_decision']={'state':'scoped_pending_render_and_content_checks','units':units}
    d['status']='root_reviewed_scope_prose_with_explicit_pending_fragment_cuts';d['scope_rules_pin']=pin(Path(__file__));path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'rows':len(d['rows']),'units':sum(len(r['export_decision']['units']) for r in d['rows']),'unknown':unknown,'held':[r['response_id'] for r in d['rows'] if r['export_decision']['state']=='held']}))
if __name__=='__main__':main()

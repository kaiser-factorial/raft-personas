"""Apply source-verified final cuts found by reading the rendered selection.

These are explicit archival decisions, not a general address/date regex.
Postal instructions in authored prose (1032F, 1269, 1698, 2182F, 659) remain.
"""
import hashlib
import json
from pathlib import Path
from period_review import load

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/raft-prep'

# Role, source, paragraph. Standalone headings/addressee blocks are omitted.
DROPS = {
    'grounding': {
        '138': [6, 7], '2454': [8, 9], '408F': [3], '598F': [3],
        '361': [5], '366F': [6], '370F': [6], '395': [5], '412': [6],
        '419': [9], '430': [4], '473': [4], '514': [3], '515': [4],
        '517': [3], '530': [4], '609F': [3], '618': [6], '63': [5],
        '851': [7], '96': [7], '2181F': [3], '1465F': [3, 4],
    },
    'question': {'1158': [12, 13, 18, 19, 22], '1883': [80],
                 '1951': [21], '1026F': [5], '2476G': [5]},
    'answer': {},
}

# End immediately before this exact string in the original source paragraph.
CUTS = {
    'grounding': [
        ('595',11,' Friday'), ('1238',3,' Sunday morning.'),
        ('1301',3,' Down Farnborough Kent'), ('1359',7,' Sept. 20th. 1850.—'),
        ('1385',2,' Down Jan 1st. 1851.'), ('1650',2,' Down'),
        ('1744',4,' Down'), ('2066',9,' March 15th.—'), ('2463A',2,' Down'),
        ('339',2,' 3. Fitz William St.'), ('352',4,' March 27th.'),
        ('362',2,' Wednesday'), ('368',7,' 36 Grt'), ('369',4,' August 2d.'),
        ('370',2,' August 3d.'), ('370A',5,' 36 | Great'), ('372',4,' Wednesday'),
        ('383',6,' October 20th.'), ('412',5,' Tuesday Morning'),
        ('426',2,' September 7th.'), ('427',5,' 36 Great'), ('430',3,' Friday 2d'),
        ('454',2,' 36 Great'), ('459',2,' 36 Grt.'), ('461',5,' Decemb 25th.'),
        ('473',3,' Monday Morning'), ('483',4,' 12 Upper'), ('491',5,' 12 Upper'),
        ('496',4,' 12 Upper'), ('497',5,' 12 Upper'), ('514',2,' 12 Upper'),
        ('515',3,' 12 Upper'), ('517',2,' June 6th.'), ('530',3,' 12 Upper'),
        ('580',2,' November 18th.'), ('597',5,' Wednesday'), ('599',4,' June 24th'),
        ('606',5,' 12 Upper'), ('618',5,' Feb. 7th.'), ('647',3,' October 4th.'),
        ('650',2,' Octob. 13th'), ('667',4,' March 31st.'), ('672',2,' April 23d.'),
        ('1184',5,' J. Higgins Esq'), ('1334',3,' J. Higgins, Esq'),
        ('1427',2,' J S Disnurr Esq'), ('1466',3,' Adam White, Esq.'),
        ('1479',2,' G. Hyndman Esq'), ('1494',2,' J. Higgins Esq'),
        ('1503',5,' Jos. Wedgwood Esq'), ('1524',2,' J. Murray Esq'),
        ('680',3,' H. Colburn Esq'), ('1930',2,' To the Secy'),
    ],
    'question': [
        ('1600',6,' Kew Monday'), ('1790',14,' 5th December 55'),
        ('785',4,' Chas Darwin Esq'), ('802',4,' Chas Darwin Esq.'),
        ('816',6,' Charles Darwin Esq'), ('979',3,' Charles Darwin Esq.'),
        ('2366',6,' C. Darwin Esq.'), ('2443',2,' (signed)'),
        ('2476G',4,' (signed)'),
    ],
    'answer': [('506',3,' 12 Upper'), ('1986',10,' Wednesday')],
}


def main():
    L = load('1858-1859')
    gp=OUT/'grounding-review.working.json'; dp=OUT/'direct-export-plan.working.json'
    G=json.loads(gp.read_text()); D=json.loads(dp.read_text()); changes=[]

    def apply(role, sid, unit):
        short=sid.removeprefix('DCP-LETT-'); source=L[sid]
        cuts={n:literal for s,n,literal in CUTS[role] if s==short}
        kept=[]
        for span in unit.get('spans',[]):
            n=span['paragraph']; text=source['paragraphs'][n-1]['text']
            assert text[span['start']:span['end']]==span['original_excerpt']
            change={'role':role,'source_id':sid,'paragraph':n,
                    'source_sha256':source['source']['sha256'], 'original_span':dict(span)}
            if n in DROPS[role].get(short,[]):
                change.update(action='exclude_standalone_header',removed=span['original_excerpt'])
                changes.append(change);continue
            if n in cuts:
                literal=cuts[n];assert text.count(literal)==1,(sid,n,literal)
                end=text.index(literal)
                if span['start'] < end < span['end']:
                    change.update(action='exclude_trailing_dateline_or_addressee',removed=text[end:span['end']],literal_boundary=literal)
                    changes.append(change)
                    span={**span,'end':end,'original_excerpt':text[span['start']:end]}
            kept.append(span)
        unit['spans']=kept

    for row in G['rows']:
        for unit in row.get('units',[]):apply('grounding',row['source_id'],unit)
        if row['source_id']=='DCP-LETT-2357':
            row.update(state='held',reason='Unresolved flattened currency: original HTML has plain 10100 without separators or currency markup; no supported repair.',units=[])
    for row in D['rows']:
        for unit in row['export_decision']['units']:
            apply('answer',row['response_id'],unit)
            for q in unit['inputs']:apply('question',q['source_id'],q)
    script={'path':str(Path(__file__).relative_to(ROOT)), 'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    G['residual_header_rules_pin']=script;D['residual_header_rules_pin']=script
    G['counts']={s:sum(r['state']==s for r in G['rows']) for s in sorted({r['state'] for r in G['rows']})}
    for p,value in [(gp,G),(dp,D)]:p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    report=OUT/'residual-header-clearance.primary.json'
    if not report.exists():
        report.write_text(json.dumps({'status':'primary_source_verified_exact_cuts','rules':script,'changes':changes,
             'retained_authorial_postal_instructions':['1032F','1269','1698','2182F','659'],
             'new_currency_hold':'DCP-LETT-2357','note':'Signatures and authored closing prose retained; datelines, recipient routing and metadata omitted.'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'scope_changes':len(changes),'grounding_counts':G['counts']}))

if __name__=='__main__':main()

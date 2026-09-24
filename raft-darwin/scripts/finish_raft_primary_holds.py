"""Apply remaining explicit primary voice/date restrictions before export."""
import hashlib,json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).parent))
from period_review import load
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'reports/raft-prep/grounding-review.working.json'
d=json.loads(P.read_text());L=load('1858-1859');rows={r['source_id']:r for r in d['rows']}
holds={
 '1014':'Assembly of separately dated/attributed passages remains uncertain; primary requires scoped temporal review.',
 '1106':'Primary exact-date hold, despite singleton XML sorting date.',
 '1123':'Primary exact-date hold, despite singleton XML sorting date.',
 '1119':'Copied incomplete extract: September11 possibly16; copied heading and later Francis conjectures are not secure original prose.',
 '1264':'Source dateline6 or8 November1849 differs from assigned single catalogue day; also visual dependencies.',
 '1265':'Primary date and recipient uncertainty remains unresolved.',
 '1381':'Literal reverse-question-mark placeholder has no verified textual repair.',
 '1881':'Exact-year hold: May28 assigned most likely1854, not a secure single year.',
 '1965':'Primary exact-day review hold explicitly retained despite singleton XML.',
 '2273':'Written Saturday14 conflicts with FridayMay14; hypothetical May15 continuation is unproved.',
 '2400':'Unidentified-hand alterations not recorded by edition; visible text not securely original unmodified authorial layer.',
 '2438':'Unresolved plain220 currency representation; £2 2s account evidence remains separate from a verified body-text rendering.',
 '798':'Oral research notes contain indeterminate verso/marginal additions; hold pending temporal and spatial layer projection.',
}
for short,reason in holds.items():rows['DCP-LETT-'+short].update(state='held',reason=reason,units=[])
r=rows['DCP-LETT-1116']
for u in r['units']:u['spans']=[s for s in u['spans'] if s['paragraph']!=2]
r['held_subscopes']=[{'paragraph':2,'reason':'Later deletions/insertions differ from contemporary retained copy; no silent version substitution.'}]
# The Secretary address follows the signature; it is a header, not prose.
r=rows['DCP-LETT-2138'];t=L[r['source_id']]['paragraphs'][2]['text'];marker='To the Honourable Secretary'
assert t.count(marker)==1
for u in r['units']:
 for s in u['spans']:
  if s['paragraph']==3:s.update(end=t.index(marker),original_excerpt=t[s['start']:t.index(marker)])
r['excluded_scope']='Terminal recipient address after the authorial signature.'
d['final_primary_hold_rules_pin']={'path':str(Path(__file__).relative_to(ROOT)),'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
d['counts']=dict(Counter(r['state'] for r in d['rows']))
P.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(d['counts'])

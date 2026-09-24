"""Score the adjudicators against their blind controls BEFORE counting any verdict.
An adjudicator that cannot reject planted bad pairs is not adjudicating."""
import json, os, glob, collections
ROOT="/Users/corinakaiser/Projects/personas/raft-darwin/reports/paragraph-split"
key=json.load(open(os.path.join(ROOT,"control-key.json")))
verdicts={}
for f in sorted(glob.glob(os.path.join(ROOT,"verdicts","batch-*.json"))):
    b=os.path.basename(f).replace(".json","")
    try: rows=json.load(open(f))
    except Exception as e: print(f"  {b}: unreadable ({e})"); continue
    # adjudicators returned either a list of records or an id->record map
    if isinstance(rows, dict):
        rows=[dict(r, item_id=i) for i,r in rows.items()]
    verdicts[b]={r["item_id"]:(r.get("verdict","?").upper(), r.get("reason","")) for r in rows}

print(f"{'batch':9s} {'items':>6s} {'CROSS caught':>13s} {'SAME (diag)':>12s} {'real KEEP':>10s}  usable")
usable=set()
for b,rows in sorted(verdicts.items()):
    cross=[i for i in rows if key.get(i)=="CROSS"]; same=[i for i in rows if key.get(i)=="SAME"]
    real=[i for i in rows if key.get(i)=="none"]
    cc=sum(1 for i in cross if rows[i][0]!="KEEP")
    sc=sum(1 for i in same  if rows[i][0]!="KEEP")
    rk=sum(1 for i in real  if rows[i][0]=="KEEP")
    # GATE: CROSS controls only. The answer is lifted from a different letter, so
    # rejecting it is ground truth by construction. SAME controls were INVALID -- they
    # assumed split_all's non-links were correct, but audit showed 5/5 "missed" SAME
    # controls were real links the splitter had failed to find (e.g. Balanidae/Barnacle).
    # SAME is now reported as a diagnostic only and never gates.
    ok = (cc>=max(1,len(cross)-1)) and len(real)>0
    if ok: usable.add(b)
    print(f"{b:9s} {len(rows):6d} {cc:6d}/{len(cross):<6d} {sc:5d}/{len(same):<6d} "
          f"{rk:5d}/{len(real):<4d}  {'yes' if ok else 'NO -- discarded'}")

# agreement on the overlapped items (same item_id judged by two batches)
seen=collections.defaultdict(dict)
for b,rows in verdicts.items():
    for i,(v,_) in rows.items():
        if key.get(i)=="none": seen[i][b]=v
dual={i:d for i,d in seen.items() if len(d)>1}
if dual:
    agree=sum(1 for d in dual.values() if len(set(d.values()))==1)
    print(f"\noverlap agreement: {agree}/{len(dual)} items judged identically by two adjudicators "
          f"({100*agree/len(dual):.0f}%)")

# Final verdicts are merged on the PAIR, not the item id: batch 7 re-judges
# batch 1's pairs under fresh ids, so agreement has to be keyed by what the
# pair actually is. Any DROP vetoes; a disagreement is resolved as DROP, which
# loses nothing -- the whole letter still carries the content.
batch_items={}
for f in glob.glob(os.path.join(ROOT,"batches","batch-*.json")):
    for it in json.load(open(f)): batch_items[it["item_id"]]=it
def sig(i):
    it=batch_items[i]
    return (it["source_transcript"], tuple(it["incoming_paras"]), tuple(it["reply_paras"]))

bysig=collections.defaultdict(list)
for b in usable:
    for i,(v,r) in verdicts[b].items():
        if key.get(i)!="none" or i not in batch_items: continue
        bysig[sig(i)].append((b,i,v,r))

final={}
for s_,rows in bysig.items():
    votes={v for _,_,v,_ in rows}
    rep=rows[0]
    if votes=={"KEEP"}: final[rep[1]]=("KEEP", rep[3])
    elif "KEEP" not in votes: final[rep[1]]=("DROP", rep[3])
    else:
        final[rep[1]]=("DROP", "adjudicators disagreed -- vetoed ("
                       + "; ".join(f"{b}:{v}" for b,_,v,_ in rows) + ")")
dual=[s_ for s_,rows in bysig.items() if len({b for b,_,_,_ in rows})>1]
agree=[s_ for s_ in dual if len({v for _,_,v,_ in bysig[s_]})==1]
if dual:
    print(f"\nindependently double-judged pairs: {len(dual)}, agreed {len(agree)} "
          f"({100*len(agree)/len(dual):.0f}%)")
c=collections.Counter(v for v,_ in final.values())
print(f"\n{len(bysig)} unique pairs from {len(usable)}/{len(verdicts)} usable batches: {dict(c)}")
json.dump({i:{"verdict":v,"reason":r} for i,(v,r) in final.items()},
          open(os.path.join(ROOT,"final-verdicts.json"),"w"), indent=1)
print(f"-> {sum(1 for v,_ in final.values() if v=='KEEP')} KEEP written to final-verdicts.json")

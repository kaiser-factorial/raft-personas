"""Stage 2 prep: split candidates into batches for subagent adjudication, salted with
two kinds of known-bad control so each adjudicator can be scored before its verdicts count.

  CROSS  - reply taken from a different letter entirely (easy negative)
  SAME   - reply paragraph from the SAME letter that the aligner did NOT link to this
           incoming paragraph (hard negative: shares subject, wrong answer)
"""
import argparse, json, os, random, glob, collections
from common import add_project_args, resolve, paras

ap=argparse.ArgumentParser(description="Stage 2 prep: candidates -> adjudication batches + control key")
add_project_args(ap)
g=ap.add_mutually_exclusive_group()
g.add_argument("--batches", type=int, default=6, help="number of batches (default %(default)s)")
g.add_argument("--per-batch", type=int, help="target candidates per batch; sets the batch count "
               "instead of --batches. The original run was ~40, so scale --batches with the corpus.")
ap.add_argument("--seed", type=int, default=41)
ap.add_argument("--overlap", type=float, default=0.20,
                help="fraction of each batch also given to the next adjudicator (default %(default)s)")
ap.add_argument("--controls", type=int, default=3,
                help="CROSS and SAME controls planted per batch, each (default %(default)s)")
cfg=resolve(ap.parse_args())
SPLIT=cfg.work
TDIR=os.path.join(cfg.src,"conversations")
cands=[json.loads(l) for l in open(os.path.join(SPLIT,"candidates.jsonl"))]

random.seed(cfg.seed)
by_src=collections.defaultdict(list)
for c in cands: by_src[c["source_transcript"]].append(c)

# build hard same-letter negatives
same_neg=[]
for src, group in by_src.items():
    t=json.load(open(os.path.join(TDIR,src)))
    P,R=paras(t["exchanges"][0][0]), paras(t["exchanges"][0][1])
    used_r={i for c in group for i in c["reply_paras"]}
    unused=[i for i in range(1,len(R)+1) if i not in used_r]
    if not unused: continue
    c=random.choice(group)
    ans=" ".join(R[i-1] for i in unused[:2])
    same_neg.append({"control":"SAME","source_transcript":src,"date":c["date"],
        "participants":c["participants"],"url":c.get("url",""),
        "incoming_paras":c["incoming_paras"],"reply_paras":unused[:2],
        "topic":c.get("topic",""),"question":c["question"],"answer":ans,
        "answer_words":len(ans.split()),"status":"derived_unadjudicated"})

cross_neg=[]
for i,c in enumerate(cands):
    o=cands[(i+len(cands)//3)%len(cands)]
    if o["source_transcript"]==c["source_transcript"]: continue
    cross_neg.append({"control":"CROSS","source_transcript":c["source_transcript"],
        "date":c["date"],"participants":c["participants"],"url":c.get("url",""),
        "incoming_paras":c["incoming_paras"],"reply_paras":o["reply_paras"],
        "topic":c.get("topic",""),"question":c["question"],"answer":o["answer"],
        "answer_words":o["answer_words"],"status":"derived_unadjudicated"})

random.shuffle(same_neg); random.shuffle(cross_neg)
NB=-(-len(cands)//cfg.per_batch) if cfg.per_batch else cfg.batches   # number of subagent batches
per=(len(cands)+NB-1)//NB
overlap=max(1,int(cfg.overlap*per))    # ~20% of each batch also given to the next agent
batches=[]
for b in range(NB):
    core=cands[b*per:(b+1)*per]
    if not core: continue
    nxt=cands[(b+1)*per:(b+1)*per+overlap]           # shared with the following agent
    items=[dict(x, control="none") for x in core+nxt]
    items += [same_neg[b::NB][:cfg.controls]][0] + [cross_neg[b::NB][:cfg.controls]][0]
    random.shuffle(items)
    for n,it in enumerate(items,1): it["item_id"]=f"b{b+1}-{n:03d}"
    batches.append(items)
os.makedirs(os.path.join(SPLIT,"batches"), exist_ok=True)
key={}
for b,items in enumerate(batches,1):
    p=os.path.join(SPLIT,"batches",f"batch-{b}.json")
    # the agent must not see which are controls
    json.dump([{k:v for k,v in it.items() if k!="control"} for it in items], open(p,"w"), indent=1)
    key.update({it["item_id"]:it["control"] for it in items})
json.dump(key, open(os.path.join(SPLIT,"control-key.json"),"w"), indent=1)
c=collections.Counter(key.values())
print(f"{len(cands)} candidates -> {len(batches)} batches of ~{per} (+{overlap} overlap)")
print("salted controls:", dict(c))
print("batch files:", os.path.join(SPLIT,"batches"))

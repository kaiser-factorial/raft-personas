"""Stage 1: derive paragraph-aligned pairs across every transcript in --src.
Emits candidates + provenance. Nothing here is adjudicated -- stage 2 does that.

  python pipeline/split_all.py [--src darwin_1] [--work DIR] [--model gpt-4o-mini]

Resumable: transcripts already present in <work>/candidates.jsonl are skipped.
Needs OPENAI_API_KEY."""
import argparse, json, glob, os, re, urllib.request, collections
from common import add_project_args, resolve, paras

ap=argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
add_project_args(ap)
ap.add_argument("--model", default="gpt-4o-mini", help="aligner/verifier model (default %(default)s)")
cfg=resolve(ap.parse_args())

OAI="https://api.openai.com/v1/chat/completions"; KEY=os.environ["OPENAI_API_KEY"]
OUT=cfg.work
os.makedirs(OUT, exist_ok=True)
CAND=os.path.join(OUT,"candidates.jsonl")

def ask(p, model=None, maxtok=1400):
    b={"model":model or cfg.model,"max_tokens":maxtok,"temperature":0,"messages":[{"role":"user","content":p}]}
    r=urllib.request.Request(OAI,data=json.dumps(b).encode(),
        headers={"Content-Type":"application/json","Authorization":f"Bearer {KEY}"})
    with urllib.request.urlopen(r,timeout=300) as f:
        return json.load(f)["choices"][0]["message"]["content"].strip()

ALIGN="""An incoming letter to Charles Darwin and his reply, both split into numbered paragraphs.

Group the exchange into TOPICAL THREADS. For each thread give:
 - "incoming": incoming paragraph numbers raising it (several, or [] if Darwin raises it himself)
 - "reply": reply paragraph numbers addressing it (may be several)
 - "confidence": "high" only if the reply paragraphs plainly respond to those incoming paragraphs
 - "topic": 5 words

A thread may be one-to-one or many-to-many. Reply paragraphs answering nothing -- his own news,
salutations, valedictions -- go in a thread with "incoming": [].

JSON list only.

INCOMING:
{inc}

REPLY:
{rep}"""
VERIFY=("Was the REPLY passage prompted by the INCOMING passage? Count as YES any genuine response: "
 "answering a question, reacting to news, acknowledging, thanking, sending regards prompted by it, or "
 "taking up its subject. Count as NO only if the reply would read the same had the incoming passage "
 "never been written. Answer only YES or NO.\n\nINCOMING:\n{q}\n\nREPLY:\n{a}")

done=set()
if os.path.exists(CAND):
    for l in open(CAND):
        try: done.add(json.loads(l)["source_transcript"])
        except Exception: pass
    print(f"resuming: {len(done)} transcripts already processed")

files=sorted(glob.glob(os.path.join(cfg.src,"conversations","transcript-*.json")))
print(f"{cfg.src_name}: {len(files)} transcripts -> {CAND}")
stats=collections.Counter()
with open(CAND,"a") as fh:
    for n,f in enumerate(files,1):
        base=os.path.basename(f)
        if base in done: continue
        t=json.load(open(f)); q,a=t["exchanges"][0]
        P,R=paras(q),paras(a)
        if len(P)<2 or len(R)<2:
            stats["too_short"]+=1; continue
        inc="\n".join(f"[{i+1}] {p}" for i,p in enumerate(P))
        rep="\n".join(f"[{i+1}] {p}" for i,p in enumerate(R))
        try:
            raw=ask(ALIGN.replace("{inc}",inc[:7000]).replace("{rep}",rep[:7000]))
            threads=json.loads(re.search(r"\[.*\]",raw,re.S).group(0))
        except Exception as e:
            stats["align_failed"]+=1; continue
        # Merge to a FIXPOINT: a naive single pass is not transitive -- if {1} and {3}
        # are separate and {1,3} arrives, it joins one and leaves the other behind, so
        # the same reply paragraph ends up answering two different questions.
        merged=[]
        for th in threads:
            merged.append({"reply":{int(x) for x in th.get("reply",[]) if str(x).isdigit()},
                           "incoming":{int(x) for x in th.get("incoming",[]) if str(x).isdigit()},
                           "topic":th.get("topic","")[:70],
                           "confidence":th.get("confidence","low")})
        changed=True
        while changed:
            changed=False
            for i in range(len(merged)):
                for j in range(i+1,len(merged)):
                    if merged[i]["reply"] & merged[j]["reply"]:
                        merged[i]["reply"]|=merged[j]["reply"]
                        merged[i]["incoming"]|=merged[j]["incoming"]
                        merged[i]["topic"]=(merged[i]["topic"]+"; "+merged[j]["topic"])[:70]
                        if merged[j]["confidence"]!="high": merged[i]["confidence"]="low"
                        merged.pop(j); changed=True; break
                if changed: break
        for m in merged:
            ii=sorted(x for x in m["incoming"] if 1<=x<=len(P))
            rr=sorted(x for x in m["reply"] if 1<=x<=len(R))
            if not rr: continue
            if not ii: stats["unprompted_paras"]+=len(rr); continue
            if m["confidence"]!="high": stats["low_confidence"]+=1; continue
            Q=" ".join(P[i-1] for i in ii); A=" ".join(R[i-1] for i in rr)
            try:
                if ask(VERIFY.replace("{q}",Q[:3000]).replace("{a}",A[:3000]),maxtok=5).upper().startswith("NO"):
                    stats["verify_no"]+=1; continue
            except Exception:
                stats["verify_failed"]+=1; continue
            fh.write(json.dumps({
              "source_transcript":base, "date":t["date"], "participants":t["participants"],
              "url":t.get("url",""), "incoming_paras":ii, "reply_paras":rr,
              "topic":m["topic"], "question":Q, "answer":A, "answer_words":len(A.split()),
              "status":"derived_unadjudicated"})+"\n"); fh.flush()
            stats["pairs"]+=1
        stats["letters"]+=1
        if n%20==0: print(f"  {n}/{len(files)} letters | {stats['pairs']} pairs so far", flush=True)
print("\nstage 1 complete:", dict(stats))

"""
Phase A: retrieve and word the memories each arm would see, for every probe.

Split from generation deliberately. Retrieval and summarization need the chroma
store and the summarizer LLM (this machine); generation needs the adapters
(bigmac). Precomputing also means every arm faces byte-identical memories, and
the 3x3 train-mode x serve-mode grid costs nothing extra.

One simplification, recorded rather than hidden: memories are built with an
empty prev_answer. In a real conversation the summarizer sees the persona's own
previous reply, which differs per arm -- and then the arms would diverge on
input, so a difference in their replies could not be attributed to the mode.
Retrieval itself is unaffected: get_similar_extracts embeds the question alone.
"""
import json, os, sys
sys.path.insert(0, "/Users/corinakaiser/Projects/raft/src")
from raft.project import dataset_paths, find_project
import raft.prompt_manager as pm
from raft.memories import MemoryManager, grounded_recall, MetaDataKeyEnum

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = "/Users/corinakaiser/Projects/personas/raft-darwin/darwin_split"
probes = json.load(open(os.path.join(HERE, "probes.json")))
DATE = probes["date"]

os.chdir(PROJECT)
paths = find_project()
pm.SUMMARY_MODEL = os.environ.get("RAFT_LLM_MODEL", "gpt-4o")

questions = [(p["id"], p["q"]) for p in probes["single"]]
questions += [(f"{probes['conversation']['id']}-t{i}", t)
              for i, t in enumerate(probes["conversation"]["turns"], 1)]

mm = MemoryManager(paths, {MetaDataKeyEnum.DATE: DATE,
                           MetaDataKeyEnum.PARTICIPANTS: {"q": "a correspondent", "a": "Charles Darwin"},
                           MetaDataKeyEnum.URL: ""})
mm.prompt_manager.retry_rate_limits = True
P = mm.prompt_manager

out = {}
for qid, q in questions:
    sims = mm.get_similar_extracts([q, ""], store=False)   # store=False: never contaminate the corpus
    per_mode = {"summary": [], "source": [], "register": []}
    for s in sims:
        doc, kind = str(s["document"]), str(s.get("kind") or "")
        date = str(s.get("date") or "")
        # One reply serves summary and source: they read its RECALL and its
        # SOURCE. Register asks the model something else, so it needs its own.
        pm.RECALL_MODE = "summary"
        raw = P.summarize_memory(doc, q, "", "Charles Darwin", date=date, kind=kind)
        for mode in ("summary", "source"):
            text = grounded_recall(raw, doc, mode=mode)
            if text:
                per_mode[mode].append({"date": date, "memory": text})
        pm.RECALL_MODE = "register"
        raw_r = P.summarize_memory(doc, q, "", "Charles Darwin", date=date, kind=kind)
        text = grounded_recall(raw_r, doc, mode="register")
        if text:
            per_mode["register"].append({"date": date, "memory": text})
    out[qid] = {"question": q, "retrieved": len(sims), "modes": per_mode}
    kept = {m: len(v) for m, v in per_mode.items()}
    print(f"  {qid:22s} retrieved {len(sims)} -> kept {kept}", flush=True)

json.dump(out, open(os.path.join(HERE, "memories.json"), "w"), indent=1)
print(f"\n-> {os.path.join(HERE, 'memories.json')}")

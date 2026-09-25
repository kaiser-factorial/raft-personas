"""Calibrate a stage-1 aligner (model) against the adjudicated darwin_thinking run.

Before trusting a different model in split_all.py, run it on a small, deliberately
mixed set of letters whose right answers we already know, and score it.

  python pipeline/calibrate_aligner.py select [--n-keep 16]
      -> prints a comma-separated list for `split_all.py --only ...`
  python pipeline/split_all.py --base-url ... --model ... --work /tmp/cal --only <list>
  python pipeline/calibrate_aligner.py compare --cand /tmp/cal/candidates.jsonl --only <list>

The selection mixes three kinds of letter:
  keep    letters with adjudicated KEEP pairs, evenly spread     -> RECALL
  long    the longest letters, which stress the context window   -> TRUNCATION
  nopair  letters that passed the paragraph filter but yielded   -> FALSE POSITIVES
          no candidate under the baseline aligner

Ground truth is the 219 KEEP / 24 DROP verdicts in reports/paragraph-split. It is
truth about the pairs the baseline proposed, not about every real link (the
splitter's recall was itself found to be imperfect), so candidates the baseline
never proposed are reported as NEW for a human to read, not counted as wrong.
"""
import argparse, collections, glob, json, os

from common import ROOT, paras

BASE = os.path.join(ROOT, "reports/paragraph-split")
SRC = os.path.join(ROOT, "darwin_thinking")


def load_truth():
    key = json.load(open(os.path.join(BASE, "control-key.json")))
    final = json.load(open(os.path.join(BASE, "final-verdicts.json")))
    items = {}
    for f in glob.glob(os.path.join(BASE, "batches", "batch-*.json")):
        for it in json.load(open(f)):
            if key.get(it["item_id"]) == "none":
                items[it["item_id"]] = it
    sig = lambda it: (it["source_transcript"], tuple(it["incoming_paras"]), tuple(it["reply_paras"]))
    truth = {}
    for i, v in final.items():
        if i in items:
            truth[sig(items[i])] = (v["verdict"], items[i])
    return truth


def load_baseline():
    return [json.loads(l) for l in open(os.path.join(BASE, "candidates.jsonl"))]


def letter_stats():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, "conversations", "transcript-*.json"))):
        q, a = json.load(open(f))["exchanges"][0]
        out[os.path.basename(f)] = (len(paras(q)), len(paras(a)), len(q.split()) + len(a.split()))
    return out


def select(n_keep, n_long, n_nopair):
    truth = load_truth()
    stats = letter_stats()
    keep_letters = sorted({s for (s, _, _), (v, _) in truth.items() if v == "KEEP"})
    step = max(1, len(keep_letters) // n_keep)
    keep = keep_letters[::step][:n_keep]
    long_ = [n for n, _ in sorted(((n, s[2]) for n, s in stats.items()), key=lambda x: (-x[1], x[0]))
             if n not in keep][:n_long]
    has_cand = {c["source_transcript"] for c in load_baseline()}
    nopair_pool = [n for n, (p, r, _) in stats.items() if p >= 2 and r >= 2 and n not in has_cand]
    nopair = nopair_pool[::max(1, len(nopair_pool) // n_nopair)][:n_nopair]
    return keep, long_, nopair


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a | b else 0.0


def compare(cand_paths, only):
    truth = load_truth()
    base = load_baseline()
    runs = [[json.loads(l) for l in open(p)] for p in cand_paths]
    local = [c for r in runs for c in r]   # several runs are UNIONED; duplicates are harmless here
    kinds = {}
    for tag, names in only.items():
        for n in names:
            kinds[n] = tag
    by = collections.defaultdict(list)
    for c in local:
        by[c["source_transcript"]].append(c)
    base_by = collections.defaultdict(list)
    for c in base:
        base_by[c["source_transcript"]].append(c)

    def matches(c, t_inc, t_rep):
        return jaccard(c["reply_paras"], t_rep) >= 0.5 and set(c["incoming_paras"]) & set(t_inc)

    print(f"{len(only['keep'])} keep + {len(only['long'])} long + {len(only['nopair'])} no-pair letters; "
          f"{len(local)} local candidates\n")
    kept = [(s, i, r) for (s, i, r), (v, _) in truth.items() if v == "KEEP" and s in kinds]
    if len(runs) > 1:
        print("recall of adjudicated KEEP pairs (overlap), per run and unioned:")
        for p, r in zip(cand_paths + ["UNION"], runs + [local]):
            rb = collections.defaultdict(list)
            for c in r:
                rb[c["source_transcript"]].append(c)
            hit = sum(1 for s, i, rr in kept if any(matches(c, i, rr) for c in rb[s]))
            print(f"  {hit:2d}/{len(kept)}  {len(r):3d} candidates  {p}")
        print()

    # RECALL: adjudicated KEEP pairs on the calibration letters
    rows = [(s, i, r) for (s, i, r), (v, _) in truth.items() if v == "KEEP" and s in kinds]
    exact = sum(1 for s, i, r in rows if any(tuple(c["incoming_paras"]) == i and tuple(c["reply_paras"]) == r for c in by[s]))
    loose = sum(1 for s, i, r in rows if any(matches(c, i, r) for c in by[s]))
    print(f"RECALL of adjudicated KEEP pairs: exact {exact}/{len(rows)}, "
          f"overlapping (reply Jaccard>=0.5 + shared incoming) {loose}/{len(rows)}")
    for s, i, r in rows:
        if not any(matches(c, i, r) for c in by[s]):
            print(f"   missed: {s} in={list(i)} reply={list(r)}")

    # FALSE-POSITIVE PROXY: local candidates that match a pair adjudicated DROP
    drops = [(s, i, r) for (s, i, r), (v, _) in truth.items() if v == "DROP" and s in kinds]
    hit = [(s, i, r) for s, i, r in drops if any(matches(c, i, r) for c in by[s])]
    print(f"\nlocal candidates matching pairs adjudicated DROP: {len(hit)} of {len(drops)} DROP pairs on these letters")

    # NEW: local candidates matching nothing the baseline proposed
    new = []
    for c in local:
        s = c["source_transcript"]
        if not any(matches(b, c["incoming_paras"], c["reply_paras"]) for b in base_by[s]):
            new.append(c)
    print(f"\nNEW (matching no baseline candidate; needs a human read): {len(new)}")
    for c in new[:30]:
        print(f"  [{kinds.get(c['source_transcript'])}] {c['source_transcript']} in={c['incoming_paras']} reply={c['reply_paras']}")
        print(f"      Q: {c['question'][:160]}")
        print(f"      A: {c['answer'][:160]}")

    # per-kind yield
    print("\ncandidates per letter kind (local vs baseline):")
    for tag in ("keep", "long", "nopair"):
        ns = only[tag]
        print(f"  {tag:7s} {sum(len(by[n]) for n in ns):3d} vs {sum(len(base_by[n]) for n in ns):3d}  ({len(ns)} letters)")
    done = {c["source_transcript"] for c in local}
    print(f"letters yielding >=1 candidate: {len(done & set(kinds))}/{len(kinds)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["select", "compare"])
    ap.add_argument("--n-keep", type=int, default=16)
    ap.add_argument("--n-long", type=int, default=4)
    ap.add_argument("--n-nopair", type=int, default=6)
    ap.add_argument("--cand", nargs="+", help="candidates.jsonl from the aligner(s) under test; several are unioned")
    ap.add_argument("--only", help="the list printed by `select`")
    a = ap.parse_args()
    keep, long_, nopair = select(a.n_keep, a.n_long, a.n_nopair)
    if a.cmd == "select":
        print(",".join(keep + long_ + nopair))
        import sys
        print(f"# {len(keep)} keep, {len(long_)} long, {len(nopair)} nopair", file=sys.stderr)
    else:
        compare(a.cand, {"keep": keep, "long": long_, "nopair": nopair})

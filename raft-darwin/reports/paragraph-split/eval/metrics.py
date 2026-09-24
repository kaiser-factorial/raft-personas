"""
Local eval metrics for the three recall-mode arms. No API, no GPU.

    python eval/metrics.py            # controls, then per-arm tables
    python eval/metrics.py --json out.json

Metrics 1-6 of OUTSTANDING.md section 1, thinking and reply scored separately.
Every metric has a ground-truth control that is RUN FIRST and printed with a
verdict; arm numbers are not to be read until the controls pass.

Deliberate simplifications (recorded, not hidden):
  * memorisation floor / register ceiling use leave-one-document-out on the
    1,405 real Darwin documents, because no held-out post-1859 text exists yet.
  * collapse and modern-leak are lexical detectors. They are cheap and
    controllable, not judges; they under-count paraphrased capitulation.
  * gen-{arm}[-sN].json are all read, so more seeds need no code change.
"""
import argparse, glob, json, os, re, random, statistics as st
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                     # reports/paragraph-split
DOCS = os.path.join(ROOT, "..", "..", "darwin_split", "corpus", "documents.jsonl")
ARMS = ("summary", "source", "register")
NGRAM = 4

WORD = re.compile(r"[a-z]+(?:'[a-z]+)?")


def words(t):
    return WORD.findall(t.lower().replace("’", "'"))


# ---------------------------------------------------------------- data loading
def load_docs():
    return [json.loads(l) for l in open(DOCS)]


def load_train(arm):
    """Assistant text of the training set, think block and reply separated."""
    think, reply = [], []
    for l in open(os.path.join(ROOT, "arms", f"chat-{arm}.jsonl")):
        c = json.loads(l)["messages"][-1]["content"]
        t, _, r = c.partition("</think>")
        think.append(BOILER.sub("", t.replace("<think>", "")).strip())
        reply.append(r.strip())
    return think, reply


def load_gens(arm):
    """[(seed_label, gen_dict)] for every gen file of an arm."""
    fs = sorted(glob.glob(os.path.join(HERE, "gen", f"gen-{arm}.json")) +
                glob.glob(os.path.join(HERE, "gen", f"gen-{arm}-s*.json")))
    return [(os.path.basename(f)[4:-5], json.load(open(f))) for f in fs]


def records(gen):
    for r in gen["single"]:
        yield r
    for r in gen["conversation"]:
        yield r


# ------------------------------------------------- 1. memorisation (verbatim)
class RunIndex:
    """Longest verbatim word run of a text against a corpus, via 4-gram index."""

    def __init__(self, texts):
        self.docs = [words(t) for t in texts]
        self.idx = defaultdict(list)
        for d, w in enumerate(self.docs):
            for i in range(len(w) - NGRAM + 1):
                self.idx[tuple(w[i:i + NGRAM])].append((d, i))

    def longest(self, text, skip_doc=None):
        w = words(text)
        best = 0
        for i in range(len(w) - NGRAM + 1):
            for d, j in self.idx.get(tuple(w[i:i + NGRAM]), ()):
                if d == skip_doc:
                    continue
                dw, n = self.docs[d], NGRAM
                while i + n < len(w) and j + n < len(dw) and w[i + n] == dw[j + n]:
                    n += 1
                best = max(best, n)
        return best


def run_vs_memories(text, mems):
    """Longest run shared with the memories that were fed (echo, not memorisation)."""
    if not mems:
        return 0
    return RunIndex([m["memory"] for m in mems]).longest(text)


# ----------------------------------------------------------- 2. register
class Vocab:
    """Document-frequency vocabulary of period text, for exact leave-one-out."""

    def __init__(self, texts):
        self.df = Counter()
        for t in texts:
            self.df.update(set(words(t)))

    def oov(self, text, own=None):
        """Share of tokens absent from period text (own = the doc to exclude)."""
        ws = words(text)
        if not ws:
            return None
        own_set = set(words(own)) if own is not None else set()
        bad = sum(1 for w in ws if self.df[w] - (w in own_set) < 1)
        return bad / len(ws)


# ------------------------------------------------ 3. letter structure (1a)
CLOSERS = re.compile(r"\b(ever yours|yours (very )?(sincerely|truly|affectionately|most truly)|"
                     r"believe me|my dear \w+|yours ever|farewell|adieu)\b", re.I)


def shape(text):
    ps = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    n = len(words(text))
    return {"words": n, "paras": len(ps), "closer": bool(CLOSERS.search(text[-160:]))
            or bool(re.search(r"\byours\b.*\bDarwin\b|\bC\. ?D(arwin)?\.?\s*$", text[-80:], re.I)),
            "opener": bool(re.match(r"\s*(my )?dear\b", text, re.I))}


def letter_shaped(s):
    """Letter shape = multi-paragraph, or a formal opener/closer. Real long
    letters are multi-paragraph 96% of the time but carry a formal opener or
    closer only ~half (the corpus is section-chunked), so requiring both was
    a miscalibrated rule the control caught."""
    return s["paras"] >= 2 or s["closer"] or s["opener"]


def repeat_share(text, n=5):
    """Share of word n-grams that repeat an earlier n-gram: degeneration."""
    w = words(text)
    g = [tuple(w[i:i + n]) for i in range(len(w) - n + 1)]
    return 1 - len(set(g)) / len(g) if g else 0.0


BOILER = re.compile(r"nothing i have written (before )?bears on this( directly)?\.?", re.I)


# ---------------------------------------------- 4. conversational collapse (1b)
CAPIT = re.compile(
    r"\b(i concede|i admit|i confess|you are (quite |perfectly |entirely )?(right|correct)|"
    r"you have (convinced|persuaded)|i was (afraid|a coward|mistaken|wrong)|i grant (you )?(that|the)|"
    r"i (was|am) (indeed )?(wrong|mistaken)|i agree (with you|that)|we agree|"
    r"quite (right|true)|you have (the )?better of|i yield)\b", re.I)


# Runaway generation: the reply continues into a fake next turn ("... user I have read").
# Case-sensitive on purpose: lowercase role token followed by a capitalised word.
BLEED = re.compile(r"(?:^|[\s.;])(?:user|assistant)\s+[A-Z]")


def jaccard(a, b):
    a, b = set(words(a)), set(words(b))
    return len(a & b) / len(a | b) if a | b else 0.0


# ------------------------------------------------------ 5. modern leakage
# Terms Darwin could not have known or used. Word-bounded; validated against
# the real documents in controls() -- a term that fires there is dropped.
MODERN = ["dna", "gene", "genes", "genetic", "genetics", "genome", "chromosome",
          "chromosomes", "computer", "computers", "internet",
          "online", "website", "software", "algorithm", "database", "digital", "electron",
          "electrons", "radio", "television", "aeroplane", "airplane", "aeroplanes",
          "nazi", "hitler", "wwi", "world war", "first world war", "second world war",
          "atomic", "nuclear", "quantum mechanics", "relativity", "einstein", "mendel",
          "crick", "double helix", "helical", "open access", "preprint", "peer review", "peer-reviewed",
          "ai", "artificial intelligence", "machine learning", "sequencing", "biotechnology",
          "neo-darwinian", "synthesis", "ecosystem", "ecology", "biodiversity", "dinosaur",
          "dinosaurs", "big bang", "plate tectonics", "continental drift"]
MODERN_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, MODERN), key=len, reverse=True)) + r")\b", re.I)


def modern_hits(text, question=""):
    """Modern terms in `text` that the question itself did not supply."""
    # stem on a trailing 's' so "computer" in the question also excuses "computers"
    # (an exact match scored the mod-computer reply as a leak: a false positive)
    stem = lambda w: w[:-1] if w.endswith("s") else w
    q = {stem(m.group(0).lower()) for m in MODERN_RE.finditer(question)}
    return [m.group(0).lower() for m in MODERN_RE.finditer(text) if stem(m.group(0).lower()) not in q]


# ---------------------------------------------------------------- controls
def controls(docs, train_idx, train_txt, vocab):
    """Run each metric on ground truth. Returns (list of lines, all_ok)."""
    rng = random.Random(0)
    out, ok = [], True

    def verdict(name, passed, detail):
        nonlocal ok
        ok &= passed
        out.append(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

    # register: real Darwin leave-one-out OOV must sit below every persona and
    # below a modern-pastiche negative control.
    sample = rng.sample(docs, 200)
    real = [vocab.oov(d["content"][:600], own=d["content"]) for d in sample]
    real = [x for x in real if x is not None]
    pastiche = ("I have been thinking a great deal about how this connects to the wider picture, and "
                "honestly I think we should look at the data before jumping to conclusions. It's "
                "fascinating stuff, and I'd love to hear what you make of the results so far!")
    pas = vocab.oov(pastiche)
    rm = st.mean(real)
    verdict("register: real Darwin < modern pastiche (OOV share)", rm < pas,
            f"real Darwin {rm:.3f} (n={len(real)}, leave-one-out) vs pastiche {pas:.3f}")

    # modern-leak: must not fire on real Darwin; must fire on a leaking text.
    fires = Counter()
    for d in docs:
        for h in modern_hits(d["content"]):
            fires[h] += 1
    verdict("leakage: detector silent on real Darwin", not fires,
            "no hits in %d documents" % len(docs) if not fires else
            "FIRES on real Darwin: " + ", ".join(f"{k}x{v}" for k, v in fires.most_common(8)) +
            " -- remove these terms from MODERN")
    leak = "DNA carries the genes, and a computer could sequence the genome."
    verdict("leakage: detector fires on a leaking text", len(modern_hits(leak)) >= 3,
            f"{modern_hits(leak)}")

    # memorisation: (a) the detector must find a planted verbatim slice; (b) real
    # Darwin docs give the shared-idiom floor. Most documents are NOT training
    # targets (1,405 docs vs 232 exchanges), so they are a floor, not a ceiling
    # -- treating them as a ceiling was the first version of this control.
    plant = train_txt.split()[:30]
    got = train_idx.longest(" ".join(plant))
    verdict("memorisation: detector finds a planted 30-word training slice",
            got >= 25, f"longest run reported {got} (of {len(plant)} planted)")
    runs = [train_idx.longest(d["content"][:800]) for d in sample[:100]]
    out.append(f"  [info] shared-idiom floor, real Darwin docs vs training longest run: "
               f"median {st.median(runs)}, p90 {sorted(runs)[89]}, max {max(runs)} words. "
               f"A persona run at or below this is shared idiom, not memorisation.")

    # repetition: real letters must be low, a synthetic loop high.
    rep = [repeat_share(d["content"]) for d in docs if len(words(d["content"])) > 250]
    loop = "the vessel placed in a box in which the air is exhausted, " * 12
    verdict("repetition: real long letters low, synthetic loop high",
            st.mean(rep) < 0.05 and repeat_share(loop) > 0.6,
            f"real mean {st.mean(rep):.3f} (max {max(rep):.2f}), loop {repeat_share(loop):.2f}")

    # letter shape: real multi-paragraph letters must be flagged.
    long_docs = [d for d in docs if len(words(d["content"])) > 250]
    flagged = sum(letter_shaped(shape(d["content"])) for d in long_docs)
    verdict("letter-structure: flags real long letters",
            flagged / len(long_docs) > 0.6, f"{flagged}/{len(long_docs)} = {flagged/len(long_docs):.0%}")

    # collapse: detector must fire on a capitulating text and stay silent on a firm one.
    cap = "You are quite right, I admit it; I was afraid, and I concede the point."
    firm = "I deny it. Twenty years of experiments were needed, and I do not regret them."
    verdict("collapse: fires on capitulation, silent on firmness",
            bool(CAPIT.search(cap)) and not CAPIT.search(firm), "")
    bleed_real = sum(bool(BLEED.search(d["content"])) for d in docs)
    verdict("role-bleed: silent on real Darwin, fires on a bleeding text",
            bleed_real == 0 and bool(BLEED.search("I do not think so. user I have read your book")),
            f"{bleed_real}/{len(docs)} real documents flagged")
    # echo: real replies must not parrot their question. Pair each doc-section's
    # neighbour is unavailable, so use the training set: reply vs its own prompt.
    echo = []
    for l in open(os.path.join(ROOT, "arms", "chat-summary.jsonl")):
        m = json.loads(l)["messages"]
        echo.append(jaccard(m[-1]["content"].partition("</think>")[2], m[-2]["content"]))
    verdict("echo: real training replies rarely parrot the prompt",
            st.mean(e > 0.6 for e in echo) < 0.02 and jaccard("I am glad you see it my way at last.",
                                                                "I am glad you see it my way at last.") == 1,
            f"{sum(e > 0.6 for e in echo)}/{len(echo)} training replies exceed jaccard 0.6")
    return out, ok


# ------------------------------------------------------------ arm scoring
def score_arm(arm, docs_idx, train_idx, vocab):
    rows = []
    for seed, gen in load_gens(arm):
        for r in records(gen):
            for part in ("thinking", "reply"):
                t = r[part]
                s = shape(t)
                rows.append({
                    "arm": arm, "seed": seed, "qid": r["qid"], "kind": r.get("kind", "conversation"),
                    "part": part, "words": s["words"], "paras": s["paras"],
                    "letter_shaped": letter_shaped(s),
                    "mem_run_train": train_idx[part].longest(BOILER.sub("", t)),
                    "repeat": repeat_share(t),
                    "mem_run_fed": run_vs_memories(t, r.get("memories", [])),
                    "n_memories": len(r.get("memories", [])),
                    # boilerplate stripped: most thinking traces are only that sentence
                    "oov": vocab.oov(BOILER.sub("", t)),
                    "substantive": bool(words(BOILER.sub("", t))),
                    "modern": modern_hits(t, r["question"]),
                    "boilerplate": part == "thinking" and t.strip().lower().startswith("nothing i have written"),
                    "capit": bool(CAPIT.search(t)) if part == "reply" else None,
                    "bleed": bool(BLEED.search(t)),
                    "echo": jaccard(t, r["question"]) if part == "reply" else None,
                    "text": t,
                })
    return rows


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 3) if xs else None


def table(title, header, lines):
    print(f"\n{title}")
    w = [max(len(str(x)) for x in col) for col in zip(header, *lines)]
    fmt = "  " + "  ".join(f"{{:<{n}}}" for n in w)
    print(fmt.format(*header))
    for l in lines:
        print(fmt.format(*[str(x) for x in l]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()

    docs = load_docs()
    vocab = Vocab(d["content"] for d in docs)
    # memorisation is scored per part: think against training think, reply against reply.
    train = {arm: load_train(arm) for arm in ARMS}
    train_idx = {arm: {"thinking": RunIndex(train[arm][0]), "reply": RunIndex(train[arm][1])} for arm in ARMS}
    # controls use the summary arm's reply index; that is valid only if the reply
    # text is identical across arms, so check rather than assume.
    assert train["summary"][1] == train["source"][1] == train["register"][1], \
        "training replies differ across arms: controls must be run per arm"
    ctl_lines, ok = controls(docs, train_idx["summary"]["reply"], max(train["summary"][1], key=len), vocab)
    print("CONTROLS (ground truth first)")
    print("\n".join(ctl_lines))
    print("\n  ALL CONTROLS PASS" if ok else "\n  *** A CONTROL FAILED: do not read the arm numbers below as findings ***")

    rows = []
    for arm in ARMS:
        rows += score_arm(arm, docs, train_idx[arm], vocab)
    seeds = {arm: len({r["seed"] for r in rows if r["arm"] == arm}) for arm in ARMS}
    print(f"\nseeds per arm: {seeds}   (1 seed = descriptive only; no ranking)")

    def sel(**kw):
        return [r for r in rows if all(r[k] == v for k, v in kw.items())]

    for part in ("reply", "thinking"):
        lines = []
        for arm in ARMS:
            rs = sel(arm=arm, part=part)
            lines.append([arm, mean(r["words"] for r in rs),
                          mean(r["mem_run_train"] for r in rs), max(r["mem_run_train"] for r in rs),
                          mean(r["mem_run_fed"] for r in rs if r["n_memories"]),
                          mean(r["oov"] for r in rs), mean(r["repeat"] for r in rs),
                          sum(bool(r["modern"]) for r in rs)]
                         + ([sum(r["boilerplate"] for r in rs), sum(r["substantive"] for r in rs)] if part == "thinking" else []))
        hdr = ["arm", "words", "run/train", "max", "run/fed*", "oov", "repeat5", "modern-hit n"] + (["boilerplate n", "n substantive"] if part == "thinking" else [])
        table(f"[{part.upper()}]  run/train = mean longest verbatim run vs training; run/fed* = vs fed memories "
              f"(probes with memories only)", hdr, lines)

    # 3. letter structure by probe kind (reply only)
    kinds = ["brevity", "domain-short", "period-offdomain", "modern-leak", "letter-mode", "conversation"]
    lines = []
    for k in kinds:
        row = [k]
        for arm in ARMS:
            rs = sel(arm=arm, part="reply", kind=k)
            row.append(f"{mean(r['words'] for r in rs)}w / {sum(r['letter_shaped'] for r in rs)}/{len(rs)} letter")
        lines.append(row)
    table("[LETTER STRUCTURE] mean reply words / letter-shaped count, by probe kind. "
          "letter-mode is the positive control: it should be letter-shaped, brevity should not.",
          ["kind"] + list(ARMS), lines)

    # 4. collapse: capitulation per conversation turn
    lines = []
    for arm in ARMS:
        cs = []
        for t in range(1, 7):
            rs = [r for r in sel(arm=arm, part="reply") if r["qid"].endswith(f"-t{t}")]
            cs.append(f"{sum(r['capit'] for r in rs)}/{len(rs)}")
        lines.append([arm] + cs)
    table("[COLLAPSE 1] lexical capitulation flags by turn. This is a FLOOR: it missed the one "
          "near-capitulation seen by eye (summary t4, 'I have always believed that you were afraid').",
          ["arm", "t1", "t2", "t3", "t4", "t5", "t6"], lines)

    lines = []
    for arm in ARMS:
        conv = sorted((r for r in sel(arm=arm, part="reply") if r["kind"] == "conversation"), key=lambda r: r["qid"])
        sims = [jaccard(a["text"], b["text"]) for a, b in zip(conv, conv[1:])]
        lines.append([arm,
                      f"{sum(r['bleed'] for r in conv)}/{len(conv)}",
                      f"{sum(r['repeat'] > 0.2 for r in conv)}/{len(conv)}",
                      f"{sum(r['echo'] > 0.6 for r in conv)}/{len(conv)}",
                      mean(sims), max(round(s, 2) for s in sims)])
    table("[COLLAPSE 2] observed failure modes over the 6 turns: role-bleed (runs on into a fake 'user' "
          "turn), degenerate loops (repeat5>0.2), parroting the interlocutor, and consecutive-turn "
          "similarity (identical replies to different questions).",
          ["arm", "role-bleed", "loops", "parrot", "turn-to-turn jaccard", "max"], lines)

    print("\n[DEGENERATION, ALL PROBES] replies with role-bleed or repeat5>0.2:")
    for arm in ARMS:
        rs = sel(arm=arm, part="reply")
        bad = [r["qid"] for r in rs if r["bleed"] or r["repeat"] > 0.2]
        print(f"  {arm:9s} {len(bad)}/{len(rs)}  {bad}")

    # 5. leakage on the four modern-leak probes, split by what was retrieved
    print("\n[MODERN LEAK] hits on modern-leak probes (0 memories retrieved in every mode, "
          "so any hit is parametric). period-offdomain must not flag.")
    for arm in ARMS:
        for k in ("modern-leak", "period-offdomain"):
            for part in ("reply", "thinking"):
                rs = sel(arm=arm, part=part, kind=k)
                hits = [(r["qid"], r["modern"]) for r in rs if r["modern"]]
                print(f"  {arm:9s} {k:17s} {part:8s} {len(hits)}/{len(rs)} flagged {hits if hits else ''}")

    # thinking boilerplate
    print("\n[THINKING] 'Nothing I have written before bears on this' rate "
          "(thinking that ignores the memories fed):")
    for arm in ARMS:
        rs = sel(arm=arm, part="thinking")
        withm = [r for r in rs if r["n_memories"]]
        print(f"  {arm:9s} all {sum(r['boilerplate'] for r in rs)}/{len(rs)}   "
              f"with memories fed {sum(r['boilerplate'] for r in withm)}/{len(withm)}")

    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)  # includes reply text for inspection
        print(f"\nper-item rows -> {a.json}")


if __name__ == "__main__":
    main()

"""
Settle the RECALL wording for the "register" arm, before it is trained on.

    cd darwin_thinking && python ../reports/paragraph-split/pipeline/tune_register_prompt.py

Candidate instructions are injected at run time rather than committed, so the
wording can be iterated without churning raft. The winner goes into
prompt_manager._RECALL_IN_REGISTER.

`useful_check` is OFF here. This is a test of *wording*, not of relevance, and
leaving the skip filter on starves it -- gpt-4o skips ~90% of retrieved
passages, which left earlier rounds judging three samples per cell.

Two metrics, because either alone is fooled:

  borrowed   share of the recollection's content words present in the source.
             Catches modern pastiche ("I am always fascinated by discussions
             on the breeding of animals"), which a modernism-counter passes.
  reporting  writes ABOUT what the author said rather than saying it ("I
             expressed my curiosity", "I was asked to aid"). High borrowed
             share does not catch this -- gpt-4o-mini scored 86% while
             three of four recollections were in reporting voice.

Note that `reporting` has false positives on genuinely verbatim text, since
Darwin does sometimes write "I think I argued that ...". Read the samples.
"""
import collections
import glob
import json
import os
import re
import sys

from raft.project import find_project
import raft.prompt_manager as pm
from raft.memories import MemoryManager, MetaDataKeyEnum, grounded_recall

MODELS = os.environ.get("TUNE_MODELS", "gpt-4o,gpt-4o-mini").split(",")
ONLY = [c for c in os.environ.get("TUNE_ONLY", "").split(",") if c]
SINCE = os.environ.get("TUNE_SINCE", "1855")
N_LETTERS = int(os.environ.get("TUNE_LETTERS", "8"))
PER_LETTER = int(os.environ.get("TUNE_PER_LETTER", "3"))

CANDIDATES = {
    # What ships today.
    "v2": (
        "<one or two sentences, first person, compressing that point into a recollection you "
        "could draw on, built AS FAR AS POSSIBLE out of the material's own words. Cut and "
        "join its phrases; do not substitute modern words for its words, do not explain, "
        "interpret or characterise it, and add nothing that is not there. Keep its spelling, "
        "abbreviations and punctuation, even where they look wrong. Do not open with a fixed "
        "formula.>"
    ),
    # v2 plus an explicit ban on reporting voice, which is how v2 fails on
    # weaker models: "I expressed my greatest curiosity about the alpine Flora".
    "v3": (
        "<one or two sentences, first person, compressing that point into a recollection you "
        "could draw on, built AS FAR AS POSSIBLE out of the material's own words. Cut and "
        "join its phrases; do not substitute modern words for its words, do not explain, "
        "interpret or characterise it, and add nothing that is not there. Keep its spelling, "
        "abbreviations and punctuation, even where they look wrong.\n"
        "Write the remembered thing ITSELF, never an account of it: do not write that you "
        "argued, mentioned, expressed, requested, noted, sought or were asked anything. "
        "\"I expressed my curiosity about the alpine Flora\" is wrong; \"I have the greatest "
        "curiosity about the alpine Flora\" is right. Do not open with a fixed formula.>"
    ),
    # v3's ban on reporting verbs was wrong: Darwin writes them himself ("I
    # think I argued that there was a good deal of concomitancy"), so banning
    # the construction bans his own. v4 keeps v3's extractive pressure, drops
    # the ban, and instead names the real defect the ban was groping at --
    # first-person compression silently reassigning other people's work to
    # Darwin ("He says further he shall work the Tasmanian Flora" becoming
    # "I am going on with the Tasmanian Flora").
    "v4": (
        "<one or two sentences, first person, compressing that point into a recollection you "
        "could draw on, built AS FAR AS POSSIBLE out of the material's own words. Cut and "
        "join its phrases; do not substitute modern words for its words, do not explain, "
        "interpret or characterise it, and add nothing that is not there. Keep its spelling, "
        "abbreviations and punctuation, even where they look wrong.\n"
        "Keep the people straight. Whatever the material attributes to someone else -- their "
        "work, their words, their opinion -- must stay theirs in your recollection; never "
        "compress it into something you did or thought. Do not open with a fixed formula.>"
    ),
    # The prohibitions in v3/v4 treat a symptom that the instruction invites.
    # Strictly, "first person" modifies the recollection's sentences, not the
    # content's attributions, and "Only restate what the material actually
    # says" ought to settle it. But the exemplar is a template whose subject is
    # I -- "I've argued that..." -- so filling it pushes whatever was retrieved
    # into an I-subject slot, and "He shall work the Tasmanian Flora" arrives as
    # "I am going on with the Tasmanian Flora". Nothing tells it to reassign;
    # nothing tells it not to, and the exemplar biases the shape. v5 asks for
    # the speaker's voice, drops the exemplar, and so needs no ban list.
    "v5": (
        "<one or two sentences in your own voice, bringing that point back to mind as you "
        "would recall it, built AS FAR AS POSSIBLE out of the material's own words: cut and "
        "join its phrases rather than rewriting them, add nothing, explain nothing, and keep "
        "its spelling, abbreviations and punctuation. What you said there of other people "
        "stays theirs.>"
    ),
    # v5 without the closing clause, to see whether dropping "first person" is
    # by itself enough -- i.e. whether the person clause earns its words.
    "v5min": (
        "<one or two sentences in your own voice, bringing that point back to mind as you "
        "would recall it, built AS FAR AS POSSIBLE out of the material's own words: cut and "
        "join its phrases rather than rewriting them, add nothing, explain nothing, and keep "
        "its spelling, abbreviations and punctuation.>"
    ),
}

STOP = set("i a an the and or but of to in on at for with that this it is was am are be been "
           "as if so my me you your he she they we not no have has had do did will would can "
           "could shall should may might there their his her its".split())
REPORT = re.compile(r"\b(argued|mentioned|expressed|noted|acknowledged|stated|requested|"
                    r"remarked|indicated|was asked|have sought|am informed|conveyed|"
                    r"described)\b", re.I)


def borrowed(recall, document):
    have = set(re.findall(r"[a-z0-9]+", document.lower()))
    words = [w for w in re.findall(r"[a-z0-9]+", recall.lower()) if w not in STOP]
    return (sum(1 for w in words if w in have) / len(words)) if words else 0.0


def jaccard(a, b):
    """Token overlap between a recollection and the verbatim span it cites."""
    ta = set(re.findall(r"[a-z0-9]+", a.lower()))
    tb = set(re.findall(r"[a-z0-9]+", b.lower()))
    return len(ta & tb) / len(ta | tb) if (ta or tb) else 0.0


def recall_line(raw):
    m = re.search(r"RECALL:\s*(.+?)\Z", str(raw), re.S | re.I)
    return " ".join(m.group(1).split()) if m else ""


def main():
    paths = find_project()
    if paths is None:
        sys.exit("run this from inside a raft project (e.g. cd darwin_thinking)")

    retrieved = []
    for f in sorted(glob.glob("conversations/transcript-*.json")):
        t = json.load(open(f))
        if t["date"] < SINCE:
            continue
        mm = MemoryManager(paths, {MetaDataKeyEnum(k): t[k] for k in ("participants", "date", "url")})
        mm.prompt_manager.retry_rate_limits = True
        q = t["exchanges"][0][0]
        for s in mm.get_similar_extracts([q, ""], store=False)[:PER_LETTER]:
            retrieved.append({"q": q, "doc": str(s["document"]), "date": str(s.get("date") or ""),
                              "pm": mm.prompt_manager})
        if len({r["q"] for r in retrieved}) >= N_LETTERS:
            break
    print(f"{len(retrieved)} passages from {len({r['q'] for r in retrieved})} letters, "
          f"useful_check OFF\n")

    results, samples = {}, []
    original = pm._RECALL_IN_REGISTER
    try:
        for model in MODELS:
            pm.SUMMARY_MODEL = model
            pm.RECALL_MODE = "register"
            for name, text in CANDIDATES.items():
                if ONLY and name not in ONLY:
                    continue
                pm._RECALL_IN_REGISTER = text
                got = []
                for r in retrieved:
                    raw = r["pm"].summarize_memory(r["doc"], r["q"], "", "Charles Darwin",
                                                   useful_check=False, date=r["date"])
                    rec = recall_line(raw)
                    if not rec:
                        continue
                    got.append(rec)
                    span = grounded_recall(raw, r["doc"], mode="source")
                    samples.append({"model": model, "candidate": name, "recall": rec,
                                    "borrowed": borrowed(rec, r["doc"]),
                                    "reporting": bool(REPORT.search(rec)),
                                    "document": r["doc"],
                                    "source_span": span,
                                    "like_source": jaccard(rec, span) if span else None})
                results[(model, name)] = got
    finally:
        pm._RECALL_IN_REGISTER = original

    print(f"{'model':13s} {'cand':6s} {'n':>4s} {'borrowed':>9s} {'reporting':>11s} {'len':>5s} {'like source':>11s}")
    for (model, name), got in results.items():
        rows = [s for s in samples if s["model"] == model and s["candidate"] == name]
        b = sum(s["borrowed"] for s in rows) / len(rows) if rows else 0
        rep = sum(1 for s in rows if s["reporting"])
        ln = sum(len(s["recall"].split()) for s in rows) / len(rows) if rows else 0
        sim = [s_["like_source"] for s_ in rows if s_["like_source"] is not None]
        sm = f"{sum(sim)/len(sim):.0%}" if sim else "-"
        print(f"{model:13s} {name:6s} {len(got):4d} {b:8.0%} {rep:7d}/{len(rows):<3d} {ln:5.0f} {sm:>11s}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                       "register-prompt-tuning.json")
    json.dump({"passages": len(retrieved), "candidates": CANDIDATES, "samples": samples},
              open(os.path.normpath(out), "w"), indent=1)
    print(f"\n-> {os.path.normpath(out)}")


if __name__ == "__main__":
    main()

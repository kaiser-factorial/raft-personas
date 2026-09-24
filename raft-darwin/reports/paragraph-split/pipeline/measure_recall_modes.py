"""
Matched measurement of summarizer model x recall mode, on ONE retrieved set.

    cd darwin_thinking && python ../reports/paragraph-split/pipeline/measure_recall_modes.py

Retrieval is programmatic and identical for every cell: the same transcripts,
the same top-k documents, fetched once. Only the summarizer model and the
RECALL instruction vary, so every number shares a denominator. An earlier
comparison here did not -- it read gpt-4o on 5 memories against gpt-4o-mini on
24 *different* memories, which cannot support a claim about either.

Reports, per cell: how many memories survive, and why the rest do not
(the model's own "skip" vs the citation check), plus borrowed-vocabulary
share -- the fraction of the recollection's content words that occur in the
source document. Borrowed share is the metric that distinguishes recall in the
author's register from modern pastiche; counting modernisms does not.
"""
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))

from raft.project import find_project                      # noqa: E402
import raft.prompt_manager as pm                           # noqa: E402
from raft.memories import MemoryManager, grounded_recall, MetaDataKeyEnum  # noqa: E402

MODELS = os.environ.get("MEASURE_MODELS", "gpt-4o,gpt-4o-mini").split(",")
MODES = ("summary", "register")
SINCE = os.environ.get("MEASURE_SINCE", "1855")
N_LETTERS = int(os.environ.get("MEASURE_LETTERS", "8"))
PER_LETTER = int(os.environ.get("MEASURE_PER_LETTER", "3"))

STOP = set("i a an the and or but of to in on at for with that this it is was am are be been "
           "as if so my me you your he she they we not no have has had do did will would can "
           "could shall should may might there their his her its".split())


def borrowed(recall, document):
    """Share of the recollection's content words that occur in the document."""
    have = set(re.findall(r"[a-z0-9]+", document.lower()))
    words = [w for w in re.findall(r"[a-z0-9]+", recall.lower()) if w not in STOP]
    return (sum(1 for w in words if w in have) / len(words)) if words else 0.0


def source_line(raw):
    """The SOURCE the model claimed, for diagnosing why a citation failed."""
    m = re.search(r"SOURCE:\s*(.+?)(?=\s*RECALL:|\Z)", str(raw), re.S | re.I)
    return " ".join(m.group(1).split()).strip('"\u201c\u201d') if m else ""


def outcome(raw, document, mode):
    """Why a retrieved memory did or did not become a recollection."""
    if re.match(r"^\W*skip\b", str(raw), re.IGNORECASE):
        return "skip", ""
    if not re.search(r"SOURCE:.*RECALL:", str(raw), re.S | re.I):
        return "unstructured", ""
    text = grounded_recall(raw, document, mode=mode)
    return ("kept", text) if text else ("citation rejected", "")


def main():
    paths = find_project()
    if paths is None:
        sys.exit("run this from inside a raft project (e.g. cd darwin_thinking)")

    # Fetch the retrieved set ONCE, so every cell is measured on it.
    retrieved = []
    for f in sorted(glob.glob("conversations/transcript-*.json")):
        t = json.load(open(f))
        if t["date"] < SINCE:
            continue
        mm = MemoryManager(paths, {MetaDataKeyEnum(k): t[k] for k in ("participants", "date", "url")})
        # gpt-4o's TPM limit is low enough that a sequential sweep trips it;
        # a lost call here would silently shrink one cell's denominator.
        mm.prompt_manager.retry_rate_limits = True
        question = t["exchanges"][0][0]
        for s in mm.get_similar_extracts([question, ""], store=False)[:PER_LETTER]:
            retrieved.append({"question": question, "document": str(s["document"]),
                              "date": str(s.get("date") or ""), "manager": mm})
        if len({r["question"] for r in retrieved}) >= N_LETTERS:
            break
    print(f"retrieved set: {len(retrieved)} memories from "
          f"{len({r['question'] for r in retrieved})} letters since {SINCE}\n")

    rows, cells, raws = [], {}, {}
    for model in MODELS:
        pm.SUMMARY_MODEL = model
        # One summarizer call serves BOTH "summary" and "source": they read the
        # RECALL and the SOURCE of the same reply, so their memory selection is
        # identical by construction. Only "register" needs its own call, because
        # it changes the instruction.
        for mode, reuse in (("summary", None), ("source", "summary"), ("register", None)):
            tally, kept = collections.Counter(), []
            pm.RECALL_MODE = mode if mode == "register" else "summary"
            for i, r in enumerate(retrieved):
                if reuse:
                    raw = raws[(model, reuse)][i]
                else:
                    raw = r["manager"].prompt_manager.summarize_memory(
                        r["document"], r["question"], "", "Charles Darwin", date=r["date"])
                    raws.setdefault((model, mode), []).append(raw)
                why, text = outcome(raw, r["document"], mode)
                tally[why] += 1
                if text:
                    kept.append((text, r["document"]))
                rows.append({"model": model, "mode": mode, "outcome": why,
                             "recall": text, "source_line": source_line(raw),
                             "document": r["document"],
                             "borrowed": borrowed(text, r["document"]) if text else None})
            cells[(model, mode)] = (tally, kept)

    n = len(retrieved)
    print(f"{'model':14s} {'mode':9s} {'kept':>9s} {'borrowed':>9s} {'len':>5s}   why not kept")
    for (model, mode), (tally, kept) in cells.items():
        b = sum(borrowed(a, d) for a, d in kept) / len(kept) if kept else 0
        ln = sum(len(a.split()) for a, _ in kept) / len(kept) if kept else 0
        rest = {k: v for k, v in tally.items() if k != "kept"}
        print(f"{model:14s} {mode:9s} {tally['kept']:4d}/{n:<4d} {b:8.0%} {ln:5.0f}   {rest}")

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "recall-mode-measurements.json")
    json.dump({"retrieved": n, "since": SINCE, "models": MODELS,
               "cells": {f"{m}/{d}": {"kept": t["kept"], "outcomes": dict(t)}
                         for (m, d), (t, _) in cells.items()},
               "samples": rows}, open(os.path.normpath(out), "w"), indent=1)
    print(f"\n-> {os.path.normpath(out)}")


if __name__ == "__main__":
    main()

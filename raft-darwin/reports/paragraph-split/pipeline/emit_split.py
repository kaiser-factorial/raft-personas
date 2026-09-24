"""
Stage 3: build the darwin_split RAFT project from the adjudicated verdicts.

Every letter is used in exactly ONE mode, so no reply text is ever trained on
twice:

  letter mode  the whole incoming letter -> the whole reply. Used for the 34
               letters that produced no surviving pair, plus RESERVE letters
               held back from splitting because they have the richest replies.
               Without that reservation letter mode would be 34 mostly
               single-paragraph notes -- too thin to learn a distinct
               behaviour from.
  split mode   one passage -> the paragraphs answering it, for every other
               letter. One pair per file: generate_finetune threads
               prev_answer across exchanges in a file, so grouping a letter's
               pairs would present Darwin's own paragraph 1 as a prior turn.

The two modes carry DIFFERENT `context` strings, which become the setting in
the system prompt (prompt_manager: `setting = context or "an interview"`).
Identical framing was a real defect: it gave contradictory supervision -- same
prompt shape, targets from 27 to 800 words -- and made the distinction
unlearnable and unsteerable at serve time.

Grounding = the original documents + Darwin's unprompted paragraphs from
split-mode letters only. Those paragraphs answer nothing in the incoming
letter and are never a training target in any mode, so adding them is not a
reservation leak. Letter-mode letters contribute nothing: their whole reply is
the target.
"""
import argparse
import collections
import datetime
import glob
import json
import os
import re
import shutil
import subprocess

from common import ROOT as ROOT_DIR, add_project_args, paras, resolve

ap = argparse.ArgumentParser(description="Stage 3: emit the split RAFT project from adjudicated verdicts")
add_project_args(ap)
#: Letters held back from splitting to serve as letter-mode examples. On the
#: original 162-letter corpus, 15 took letter mode to 49 examples / ~22k words /
#: 24 multi-paragraph replies at a cost of 36 derived pairs. That is a count
#: chosen for that corpus, not a ratio: rescale it for a larger one.
ap.add_argument("--reserve", type=int, default=int(os.environ.get("SPLIT_RESERVE", "15")),
                help="richest-reply letters kept whole (default %(default)s; env SPLIT_RESERVE)")
cfg = resolve(ap.parse_args())
SPLIT, SRC, DST, RESERVE = cfg.work, cfg.src, cfg.dst, cfg.reserve

LETTER_CONTEXT = "a letter from {q}, which you are answering"
PASSAGE_CONTEXT = "a single passage from a letter by {q}, which you are answering on its own"


# ---------------------------------------------------------------- verdicts
key = json.load(open(os.path.join(SPLIT, "control-key.json")))
final = json.load(open(os.path.join(SPLIT, "final-verdicts.json")))
items = {}
for f in glob.glob(os.path.join(SPLIT, "batches", "batch-*.json")):
    for it in json.load(open(f)):
        if key.get(it["item_id"]) == "none":
            items[it["item_id"]] = it

seen, uniq = set(), []
for i, v in final.items():
    if v["verdict"] != "KEEP" or i not in items:
        continue
    it = items[i]
    sig = (it["source_transcript"], tuple(it["incoming_paras"]), tuple(it["reply_paras"]))
    if sig in seen:
        continue
    seen.add(sig)
    uniq.append(it)

letters = {}
for f in sorted(glob.glob(os.path.join(SRC, "conversations", "transcript-*.json"))):
    t = json.load(open(f))
    reply = t["exchanges"][0][1]
    letters[os.path.basename(f)] = {"path": f, "doc": t,
                                    "n_paras": len(paras(reply)),
                                    "n_words": len(reply.split())}

# Transcript numbers collide across corpora (transcript-0015 exists in every one),
# so verdicts from another --work dir would otherwise be applied to the wrong
# letters without a murmur. Every verdict carries its letter's URL: check it.
_stale = [it["item_id"] for it in uniq
          if it["source_transcript"] not in letters
          or letters[it["source_transcript"]]["doc"].get("url", "") != it.get("url", "")]
if _stale:
    raise SystemExit(f"{len(_stale)} adjudicated pairs (e.g. {_stale[:3]}) do not match the letters in "
                     f"--src {SRC}; --work {SPLIT} was built from a different source project")

# A plain dict, deliberately: probing a defaultdict here would mint a key for
# every letter, and the no-pair letters would then join split mode as well as
# letter mode -- their whole reply a training target while their paragraphs sat
# in grounding, which is the leak this partition exists to prevent.
pairs_by_letter = {}
for it in uniq:
    pairs_by_letter.setdefault(it["source_transcript"], []).append(it)

# ------------------------------------------------------------- partition
no_pair = [n for n in letters if n not in pairs_by_letter]
# Richest replies first; the name breaks ties so the choice is reproducible.
richest = sorted(pairs_by_letter, key=lambda n: (-letters[n]["n_paras"], -letters[n]["n_words"], n))
reserved = richest[:RESERVE]
letter_mode = sorted(set(no_pair) | set(reserved))
split_mode = [n for n in sorted(pairs_by_letter) if n not in set(reserved)]
emitted_pairs = [it for n in split_mode for it in pairs_by_letter[n]]

print(f"{len(uniq)} adjudicated pairs from {len(pairs_by_letter)} letters; "
      f"{len(no_pair)} letters produced none")
print(f"letter mode: {len(letter_mode)} letters ({len(no_pair)} no-pair + {len(reserved)} reserved), "
      f"{sum(letters[n]['n_words'] for n in letter_mode):,} reply words, "
      f"{sum(1 for n in letter_mode if letters[n]['n_paras'] > 1)} multi-paragraph")
print(f"split mode : {len(split_mode)} letters -> {len(emitted_pairs)} pairs "
      f"({len(uniq) - len(emitted_pairs)} dropped with the reserved letters)")

# ----------------------------------------------------------------- rebuild
# The rebuild below deletes DST outright, so never let it be (or contain, or sit
# inside) the source project.
_d, _s = os.path.realpath(DST), os.path.realpath(SRC)
if _d == _s or _s.startswith(_d + os.sep) or _d.startswith(_s + os.sep):
    raise SystemExit(f"--dst {DST} overlaps --src {SRC}; refusing to delete and rebuild it")
if os.path.exists(DST):
    if subprocess.run(["pgrep", "-f", "[r]aft embed"], capture_output=True).returncode == 0:
        raise SystemExit("a `raft embed` is running against this project; stop it before "
                         "re-emitting (it would delete the store underneath it)")
    shutil.rmtree(DST)
for d in ("conversations", "corpus", "metadata", "blobs", "fetch"):
    os.makedirs(os.path.join(DST, d))
json.dump({"format": "raft.project.v1", "name": cfg.dst_name,
           "collection": cfg.dst_name, "target": "Charles Darwin"},
          open(os.path.join(DST, "raft.json"), "w"), indent=2)
state = os.path.join(SRC, "metadata", "state.json")
if os.path.exists(state):   # darwin_thinking has one; darwin_1 does not
    shutil.copy(state, os.path.join(DST, "metadata", "state.json"))
readme = os.path.join(SPLIT, f"{cfg.dst_name}_README.md")
if os.path.exists(readme):
    shutil.copy(readme, os.path.join(DST, "README.md"))

prov, n = [], 0


def write(doc, record):
    global n
    n += 1
    name = f"transcript-{n:04d}.json"
    json.dump(doc, open(os.path.join(DST, "conversations", name), "w"), indent=2)
    prov.append(dict(record, transcript=name, url=doc["url"]))


# 1. letter mode, the reply whole and unaltered
for name in sorted(letter_mode, key=lambda x: letters[x]["doc"]["date"]):
    t = dict(letters[name]["doc"])
    t["context"] = LETTER_CONTEXT.format(q=t["participants"]["q"])
    write(t, {"kind": "whole_letter", "source": name, "date": t["date"],
              "reserved_from_splitting": name in set(reserved),
              "status": "adjudicated_upstream"})
whole = n

# 2. split mode, one passage pair per file
for it in sorted(emitted_pairs, key=lambda x: (x["date"], x["source_transcript"], x["reply_paras"])):
    base = it.get("url", "")
    t = {"participants": it["participants"], "date": it["date"],
         # Extend the existing fragment: two '#' in a URL is malformed.
         "url": base + ("-" if "#" in base else "#") + "para-"
                + "-".join(map(str, it["reply_paras"])),
         "context": PASSAGE_CONTEXT.format(q=it["participants"]["q"]),
         "exchanges": [[it["question"], it["answer"]]]}
    write(t, {"kind": "derived_paragraph_pair", "source": it["source_transcript"],
              "date": it["date"], "incoming_paras": it["incoming_paras"],
              "reply_paras": it["reply_paras"], "topic": it.get("topic", ""),
              "item_id": it["item_id"], "verdict_reason": final[it["item_id"]]["reason"],
              "status": "derived_adjudicated"})
print(f"transcripts: {whole} letter-mode + {n - whole} split-mode = {n}")

# ---------------------------------------------------------------- grounding
answered = collections.defaultdict(set)
for it in emitted_pairs:
    answered[it["source_transcript"]].update(it["reply_paras"])

SIGNOFF = re.compile(r"(believe me|yours (most |very )?(sincerely|truly|faithfully)|kindest "
                     r"remembrances|pray give my|God bless you|your affectionate|obliged & obedient|"
                     r"Ch\. Darwin|C\. Darwin|Chas\. Darwin|Charles Darwin)", re.I)


def apparatus(text):
    """Epistolary furniture, not recollectable substance."""
    w = len(text.split())
    if SIGNOFF.search(text) and w < 45:
        return "signoff"
    if "|" in text and w < 45:          # the transcription's line-break marker
        return "signature"
    if w < 15:
        return "fragment"
    if re.match(r"^\s*P\.?\s*S\.?\b", text):
        return "postscript"
    return ""


docs = [json.loads(l) for l in open(os.path.join(SRC, "corpus", "documents.jsonl"))]
norm = lambda x: " ".join(re.findall(r"[a-z0-9]+", x.lower()))
hay = " || ".join(norm(d["content"]) for d in docs)

added, held = 0, collections.Counter()
with open(os.path.join(DST, "corpus", "documents.jsonl"), "w") as fh:
    for d in docs:
        fh.write(json.dumps(d) + "\n")
    for name in split_mode:
        t = letters[name]["doc"]
        for i, p in enumerate(paras(t["exchanges"][0][1]), 1):
            if i in answered[name]:
                held["answers_something"] += 1
                continue
            why = apparatus(p)
            if why:
                held[why] += 1
                continue
            if norm(p)[:120] in hay:
                held["already_in_grounding"] += 1
                continue
            fh.write(json.dumps({
                "title": f"[derived: unprompted] To {t['participants']['q']}, {t['date']} "
                         f"[{name} ¶{i}]",
                "link": t.get("url", ""), "date": t["date"], "content": p}) + "\n")
            added += 1
held["letter_mode_letter"] = sum(letters[n]["n_paras"] for n in letter_mode)
print(f"grounding: {len(docs)} original + {added} unprompted = {len(docs) + added}")
print("  paragraphs withheld:", dict(held))

json.dump({
    "created_from": os.path.relpath(SPLIT, ROOT_DIR),
    "source_project": cfg.src_name,
    "reserve": RESERVE,
    "note_transcript_field": "`transcript` is the CURRENT filename and is rewritten whenever "
                             "select_kind.py renumbers. Join on `url`, which is stable.",
    "letter_mode": whole, "split_mode": n - whole,
    "letter_mode_no_pair": len(no_pair), "letter_mode_reserved": len(reserved),
    "pairs_adjudicated": len(uniq), "pairs_emitted": len(emitted_pairs),
    "grounding_original": len(docs), "grounding_unprompted": added,
    "grounding_withheld": dict(held),
    "policy_note": "Grounding gains Darwin's unprompted paragraphs from SPLIT-MODE letters only. "
                   "They answer nothing in the incoming letter and are never a training target in "
                   "any mode, so this is not a reservation leak; retrieval additionally filters on "
                   "date_num < transcript date. Letter-mode letters contribute nothing, their whole "
                   "reply being the target. Tagged '[derived: unprompted]' to be reversible.",
    "records": prov,
}, open(os.path.join(SPLIT, "emitted-provenance.json"), "w"), indent=1)

# --------------------------------------------------------------- validation
bad = 0
ctx = collections.Counter()
for f in glob.glob(os.path.join(DST, "conversations", "transcript-*.json")):
    t = json.load(open(f))
    assert set(t) >= {"participants", "date", "url", "exchanges", "context"}
    datetime.date.fromisoformat(t["date"])
    ctx["passage" if "single passage" in t["context"] else "letter"] += 1
    for ex in t["exchanges"]:
        if not (isinstance(ex, list) and len(ex) == 2
                and all(isinstance(x, str) and x.strip() for x in ex)):
            bad += 1
nums = sorted(int(re.search(r"(\d+)", os.path.basename(f)).group(1))
              for f in glob.glob(os.path.join(DST, "conversations", "transcript-*.json")))
# No letter may appear in both modes -- that is the whole point of the partition.
kinds = collections.defaultdict(set)
for r in prov:
    kinds[r["source"]].add(r["kind"])
both = [s for s, k in kinds.items() if len(k) > 1]
print(f"validation: {len(nums)} transcripts, gapless={nums == list(range(1, len(nums) + 1))}, "
      f"malformed={bad}, letters in both modes={len(both)}")
print(f"  context framings: {dict(ctx)}")
print(f"next: cd {cfg.dst_name} && raft chunk && raft embed")

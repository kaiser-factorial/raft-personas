"""
Choose which kind of transcript darwin_split trains on.

    python select_kind.py derived_paragraph_pair   # short, targeted answers only
    python select_kind.py whole_letter             # long-form letters only
    python select_kind.py                          # restore everything

The two kinds overlap -- the derived pairs re-cover 61% of the whole-letter
answer volume -- so training on both shows most of Darwin's reply text twice.
This makes the alternative one command rather than a manual reshuffle.

Held-back transcripts move to conversations_held/ and the remainder is
renumbered so the sequence stays gapless, which ft:gen relies on. Grounding
and the embedding store are untouched, so no re-chunk or re-embed is needed.

Renumbering means a transcript's filename is not its identity: transcript-0007
can be a different letter after every run. Identity is the url, which is unique
across the project and never changes, so held files are stored under a name
derived from the url and the live ordering is rebuilt by sorting on it.
Filenames are therefore never reused for two different letters, which an earlier
version of this script got wrong -- it held files under their live names and a
restore silently overwrote 162 transcripts.
"""
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(HERE, "..", "..", "darwin_split"))
LIVE = os.path.join(PROJECT, "conversations")
HELD = os.path.join(PROJECT, "conversations_held")
PROV = os.path.join(HERE, "emitted-provenance.json")
KINDS = ("whole_letter", "derived_paragraph_pair")


def held_name(url):
    """A name for a held file that cannot collide with a live transcript."""
    return "held-" + hashlib.sha1(url.encode()).hexdigest()[:16] + ".json"


def resync_provenance(numbered):
    """
    Point each provenance record at the filename it now has.

    The provenance file records a `transcript` name, and renumbering makes that
    name refer to a different letter. Anything joining provenance to the corpus
    on the filename then reads the wrong record -- which is how a 12-word
    salutation came to be reported as a 2,381-word answer. `url` is the stable
    key; this keeps the convenience field honest as well.
    """
    if not os.path.exists(PROV):
        return
    doc = json.load(open(PROV))
    for r in doc["records"]:
        if r.get("url") in numbered:
            r["transcript"] = numbered[r["url"]]
        else:
            r["transcript"] = None  # held back, not currently in the corpus
    json.dump(doc, open(PROV, "w"), indent=1)


def gather():
    """Every transcript, live or held, as (url, kind, current path)."""
    out = []
    for directory in (LIVE, HELD):
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(directory, name)
            url = json.load(open(path))["url"]
            kind = "derived_paragraph_pair" if "-para-" in url else "whole_letter"
            out.append((url, kind, path))
    return out


def main(wanted):
    if wanted and wanted not in KINDS:
        sys.exit(f"unknown kind {wanted!r}; expected one of {', '.join(KINDS)}")
    os.makedirs(HELD, exist_ok=True)

    everything = gather()
    if not everything:
        sys.exit(f"no transcripts found under {PROJECT}")

    # Order by url: unique, stable, and independent of the current numbering,
    # so repeated runs converge instead of drifting.
    seen = {}
    for url, kind, path in everything:
        seen[url] = (kind, path)

    keep = sorted(
        [(u, k, p) for u, (k, p) in seen.items() if not wanted or k == wanted],
        key=lambda x: x[0],
    )
    hold = [(u, k, p) for u, (k, p) in seen.items() if wanted and k != wanted]

    # Move everything out of the way first: no rename can land on a name that
    # another transcript still occupies.
    staged = []
    for url, kind, path in keep:
        tmp = os.path.join(LIVE, ".stage-" + hashlib.sha1(url.encode()).hexdigest()[:16])
        shutil.move(path, tmp)
        staged.append((url, tmp))
    for url, kind, path in hold:
        dst = os.path.join(HELD, held_name(url))
        if os.path.abspath(path) != os.path.abspath(dst):
            shutil.move(path, dst)

    staged.sort(key=lambda x: x[0])
    numbered = {}
    for i, (url, tmp) in enumerate(staged, 1):
        name = f"transcript-{i:04d}.json"
        os.rename(tmp, os.path.join(LIVE, name))
        numbered[url] = name
    resync_provenance(numbered)

    label = wanted or "all"
    print(f"{label}: {len(staged)} transcripts live, {len(hold)} held in conversations_held/")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")

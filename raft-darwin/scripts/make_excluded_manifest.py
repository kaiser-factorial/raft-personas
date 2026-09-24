#!/usr/bin/env python3
"""
Record what the GitHub copy of this project deliberately leaves out, so it can
be verified or rebuilt: path, size, line count and sha256 for each excluded
completed-period file, plus the pinned upstream for data/raw.

    python scripts/make_excluded_manifest.py        # writes EXCLUDED_MANIFEST.json

Run 2 (post-Origin -> 1868) is still being written and is skipped entirely --
not hashed, not listed, not opened. Re-run this after it finishes.

The `generated_by` hints are read from which scripts name the file, and are
pointers, NOT a promise of reproducibility: several of these files are read
back and merged by later scripts (e.g. curate_remaining_review.py), so keep the
local copies until a rebuild has been verified against the hashes below.
"""
import hashlib, json, os, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)

RUN2 = ("reports/1859-post-origin", *(f"reports/{y}" for y in range(1860, 1869)), "reports/research")
FAMILIES = {"all_letters.jsonl", "letters.jsonl", "audit.jsonl", "discovery_audit.jsonl",
            "ambiguous_or_later.jsonl", "letter_references.jsonl"}
GENERATORS = ["scripts/prepare_period.py", "scripts/curate_remaining_review.py",
              "scripts/prepare_remaining_expansion.py", "scripts/period_review.py"]


def in_run2(path):
    return any(path == r or path.startswith(r + "/") for r in RUN2)


def digest(path):
    h, lines = hashlib.sha256(), 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            lines += chunk.count(b"\n")
    return h.hexdigest(), lines


def excluded_files():
    for root, _, files in os.walk("reports"):
        rel = root.replace(os.sep, "/")
        if in_run2(rel):
            continue
        for f in files:
            p = f"{rel}/{f}"
            size = os.path.getsize(p)
            if f in FAMILIES and size >= 5_000_000:
                yield p, "machine-derived family, >=5MB"
            elif f.endswith(".pdf"):
                yield p, "downloaded third-party PDF"
            elif f in ("rendered-staging.json", "rendered-staging.working.json"):
                yield p, "rendered letter text staged for export"


def main():
    files = []
    for p, why in sorted(excluded_files()):
        sha, lines = digest(p)
        files.append({"path": p, "why": why, "bytes": os.path.getsize(p), "lines": lines, "sha256": sha})
        print(f"  {os.path.getsize(p)/1048576:7.1f} MB  {p}", file=sys.stderr)

    raw = {}
    for sub in sorted(os.listdir("data/raw")) if os.path.isdir("data/raw") else []:
        n = size = 0
        for r, _, fs in os.walk(f"data/raw/{sub}"):
            for f in fs:
                n += 1
                size += os.path.getsize(os.path.join(r, f))
        raw[sub] = {"files": n, "bytes": size}

    manifest = {
        "note": ("Files excluded from the GitHub copy. Nothing here was deleted: the local originals are the "
                 "source of truth. Hashes let a rebuild be checked; they do not prove one is possible."),
        "run2_pending": ("reports/1859-post-origin, reports/1860..1868, reports/research and data/annotations are "
                         "still being written and are NOT in the repository or in this manifest. Add them after the run."),
        "upstream": {
            "name": "Epsilon (epsilon.ac.uk) project data",
            "repo": "https://github.com/cambridge-collection/epsilon-data",
            "revision": "ab0d973bae05b54d68d82d068211015996cfec06",
            "csv": "csv/darwin-correspondence.csv",
            "csv_sha256": "cbe31878e4557db7f1e96f4c1fccdfa3144a88b2e8f2dcbf7441f8d430d73f9a",
            "licence": "CC BY-NC 4.0",
            "per_file_hashes": "data/raw carries its own per-source manifests with paths and hashes; not duplicated here.",
        },
        "data_raw_local_summary": raw,
        "generated_by_hints": GENERATORS,
        "excluded_files": files,
    }
    json.dump(manifest, open("EXCLUDED_MANIFEST.json", "w"), indent=1)
    print(f"-> EXCLUDED_MANIFEST.json ({len(files)} files, {sum(f['bytes'] for f in files)/1048576:.0f} MB excluded)", file=sys.stderr)


if __name__ == "__main__":
    main()

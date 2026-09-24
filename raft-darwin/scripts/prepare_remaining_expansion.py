"""Freeze the remaining 1837–1843 workload and preserve sources for Luna review.

This is a source/coverage preparation step, never a relationship inference.
Packets keep a correspondent group intact and include already-reviewed context.
"""

import argparse
import hashlib
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetch_metadata import ROOT, fetch
from fetch_letter_bodies import validate
from search_body_dates import parse_page, write_jsonl

BASE = ROOT / "reports/1837-1843"
OUT = BASE / "remaining-review"
RAW = ROOT / "data/raw/dcp/remaining-review-1837-1843"


def read(p):
    return json.loads(p.read_text())


def write(p, r):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n")


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def group_key(row):
    side = "recipient" if row["direction"] == "from_darwin" else "sender"
    return " | ".join(sorted(p["attributes"].get("key", p["text"]) for p in row[side + "_evidence"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    audit = {r["id"]: r for r in map(json.loads, (BASE / "audit.jsonl").read_text().splitlines())}
    selection_path = OUT / "selection.json"
    if not selection_path.exists():
        graph = read(BASE / "correspondence-map/graph.json")
        reviewed = sorted(n["id"] for n in graph["nodes"] if n["source_record_reviewed"])
        target = sorted(set(audit) - set(reviewed))
        write(selection_path, {"scope": "Every previously uninspected source record in the pinned 1837–1843 candidate inventory, including all 31 date-held records across phases. Not a corpus-wide re-dating of records outside the pinned selection.",
                               "target_ids": target, "previously_reviewed_ids": reviewed,
                               "target_safe_count": sum(audit[i]["period_selection_eligible"] for i in target),
                               "target_held_count": sum(not audit[i]["period_selection_eligible"] for i in target)})
        frozen = [BASE / "audit.jsonl", BASE / "summary.json", BASE / "correspondents.json",
                  ROOT / "data/annotations/expansion_1837_1843.json", ROOT / "data/annotations/henslow_lyell_1837_1843.json",
                  BASE / "correspondent-review/parent_review.json", BASE / "henslow-lyell/parent_review.json",
                  ROOT / "reports/correspondence-map/graph.json", ROOT / "reports/correspondence-map/summary.json"]
        write(OUT / "baseline_hashes.json", {"files": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in frozen]})
        for name, source in [("prior_expansion_graph.json", BASE / "correspondence-map/graph.json"),
                             ("prior_expansion_summary.json", BASE / "correspondence-map/summary.json"),
                             ("prior_corpus_status.json", ROOT / "reports/corpus-status.json")]:
            (OUT / name).write_bytes(source.read_bytes())
    selection = read(selection_path)
    target = selection["target_ids"]
    assert set(target) | set(selection["previously_reviewed_ids"]) == set(audit)
    assert not set(target) & set(selection["previously_reviewed_ids"])

    known_letters = {}
    for path in (BASE / "pilot/letters.jsonl", BASE / "correspondent-review/letters.jsonl",
                 BASE / "correspondent-review/seed-context.letters.jsonl", BASE / "henslow-lyell/letters.jsonl",
                 BASE / "henslow-lyell/context.letters.jsonl"):
        known_letters.update({r["id"]: r for r in map(json.loads, path.read_text().splitlines())})
    known_sources = {i: r["source"] for i, r in known_letters.items()}
    # Reuse earlier-period pages (e.g. boundary 326) without changing provenance.
    earlier = read(ROOT / "data/raw/dcp/body-date-search-37-337/manifest.json")
    for source in earlier["files"]:
        known_sources.setdefault(source["id"], source)
    manifest_path = RAW / "manifest.json"
    manifest = read(manifest_path) if manifest_path.exists() else {"requested_ids": target, "files": [], "errors": []}
    assert manifest["requested_ids"] == target
    sources = {r["id"]: r for r in manifest["files"]}
    known_sources.update(sources)

    groups = defaultdict(list)
    for row in audit.values():
        groups[group_key(row)].append(row["id"])
    priority_names = ["Owen, Richard", "Waterhouse, G. R.", "Fox, W. D.", "Darwin, S. E.",
                      "Jenyns, Leonard", "FitzRoy, Robert", "Lonsdale, William", "Hooker, J. D."]
    def order(key):
        labels = " | ".join(p["text"] for i in groups[key] for side in ("sender", "recipient")
                            for p in audit[i][side + "_evidence"])
        match = min([n for n, name in enumerate(priority_names) if name in labels] or [99])
        return (match, -sum(i in target for i in groups[key]), key)
    group_order = sorted((k for k in groups if set(groups[k]) & set(target)), key=order)
    fetch_order = [i for k in group_order for i in groups[k] if i in target]

    def preserve(i):
        if i in known_sources:
            source = known_sources[i]
            assert digest(ROOT / source["path"]) == source["sha256"], i
        else:
            if not args.fetch:
                raise ValueError(f"Missing source {i}; run --fetch")
            url = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{i}.xml"
            source = {**fetch(url, RAW / f"{i}.html", {}), "id": i}
        validate((ROOT / source["path"]).read_bytes(), i)
        return source

    manifest["errors"] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(preserve, i): i for i in fetch_order}
        for n, future in enumerate(as_completed(futures), 1):
            i = futures[future]
            try:
                sources[i] = future.result()
            except Exception as exc:
                manifest["errors"].append({"id": i, "error": str(exc)})
                print(f"ERROR {i}: {exc}", flush=True)
            manifest["files"] = [sources[k] for k in sorted(sources)]
            write(manifest_path, manifest)
            if n % 20 == 0 or n == len(futures):
                print(f"Preserved {len(sources)}/{len(target)} remaining sources", flush=True)
    if manifest["errors"]:
        raise ValueError("Source preservation incomplete; see manifest, do not count missing fetches as reviewed")
    letters = dict(known_letters)
    for i in target:
        source = sources[i]
        letters[i] = {"id": i, "source": source, "metadata_audit": audit[i],
                      **parse_page((ROOT / source["path"]).read_bytes())}
    assert set(letters) == set(audit)
    write_jsonl(OUT / "letters.jsonl", [letters[i] for i in target])
    write_jsonl(OUT / "all_letters.jsonl", [letters[i] for i in sorted(letters)])

    # Keep whole correspondent groups, then combine small groups into bounded
    # packets. Word budget concerns reading size, not a truncation rule.
    batches, current, count, words = [], [], 0, 0
    for key in group_order:
        ids = groups[key]
        n = sum(i in target for i in ids)
        size = sum(sum(len(p["text"].split()) for p in letters[i]["paragraphs"])
                   + len(letters[i]["editorial_footnotes"].split()) for i in ids)
        if current and (count + n > 24 or words + size > 15000):
            batches.append(current)
            current, count, words = [], 0, 0
        current.append(key)
        count += n
        words += size
    if current:
        batches.append(current)
    packets = []
    for n, keys in enumerate(batches, 1):
        ids = sorted({i for k in keys for i in groups[k]}, key=lambda i: (audit[i]["original_csv"]["sorting_date"], i))
        targets = [i for i in ids if i in target]
        group = f"batch-{n:02d}"
        packet = {"batch_id": group, "target_ids": targets, "context_ids": [i for i in ids if i not in target],
                  "groups": [{"authority_key": k, "labels": sorted({" | ".join(p["text"] for p in audit[i][("recipient" if audit[i]["direction"] == "from_darwin" else "sender") + "_evidence"]) for i in groups[k]}),
                              "letter_ids": groups[k]} for k in keys],
                  "scope": selection["scope"], "letters": [letters[i] for i in ids],
                  "instructions": "Read every target and context body, header and editorial note in full. Make per-record judgments on incoming prompt identity, knowledge witnesses, date sections, gaps and authorship. Surviving content may be a fragment, printed extract, official report, joint text or no transcript. Do not mark an online placeholder as a full body. Match actual distinctive answers, not nearest date or shared subject. An incoming letter may answer Darwin but is never his voice. Original XML and catalogue dates must remain intact; period-held records cannot become eligible without separate parent adjudication. Direct reply arrows are response -> antecedent; knowledge arrows incoming -> dated Darwin witness. Record exact paragraph-located quotations, competing hypotheses and unlocated references. Search the complete preserved expansion at all_letters.jsonl for cross-correspondent witnesses when your evidence suggests one. No synthetic prompts, no future editorial facts as Darwin knowledge. Submit proposals only; primary agent adjudicates."}
        path = OUT / "packets" / f"{group}.json"
        rendered = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
        if path.exists():
            assert path.read_text() == rendered, f"Frozen packet differs: {group}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered)
        packets.append({"batch_id": group, "path": str(path.relative_to(ROOT)), "sha256": digest(path),
                        "target_ids": targets, "context_ids": packet["context_ids"],
                        "groups": [r["labels"] for r in packet["groups"]],
                        "target_count": len(targets),
                        "word_count_including_notes": sum(sum(len(p["text"].split()) for p in letters[i]["paragraphs"])
                                                         + len(letters[i]["editorial_footnotes"].split()) for i in ids)})
    assert [i for p in packets for i in p["target_ids"]].__len__() == len(target)
    assert {i for p in packets for i in p["target_ids"]} == set(target)
    write(OUT / "manifest.json", {"selection": str(selection_path.relative_to(ROOT)), "packets": packets,
                                   "total_target_records": len(target), "source_manifest": str(manifest_path.relative_to(ROOT)),
                                   "source_manifest_sha256": digest(manifest_path)})
    print(json.dumps([{k: p[k] for k in ("batch_id", "target_count", "word_count_including_notes", "groups")} for p in packets], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

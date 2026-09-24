"""Preserve and audit the separate 1837-1843 extension, using the pinned CSV.

The earlier source manifest, period audit, and reviewed graph are read-only inputs.
CSV dates select candidates; all XML possibilities determine period eligibility.
This inventory does not establish any reply, receipt date, or voice eligibility.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from audit_metadata import audit_record, read_csv_records, write_jsonl
from fetch_metadata import BASE, RAW, REVISION, ROOT, fetch, is_darwin

START, END = "1837-01-01", "1843-12-31"
DEST = RAW / "expansions" / "1837-1843"
OUT = ROOT / "reports" / "1837-1843"
CSV = RAW / "darwin-correspondence.csv"


def selection():
    headers, rows = read_csv_records(CSV)
    selected, excluded = [], []
    for info in rows:
        row = info[3]
        in_window = START <= row["sorting_date"] <= END
        explicit_year = any(1837 <= int(y) <= 1843 for y in re.findall(r"(?<!\d)\d{4}(?!\d)", row["date"]))
        direct = is_darwin(row, "sender") or is_darwin(row, "recipient")
        if direct and (in_window or explicit_year):
            selected.append(info)
        elif in_window and not direct:
            excluded.append(info)
    return headers, rows, selected, excluded


def source_manifest():
    original = json.loads((RAW / "manifest.json").read_text())
    csv_source = next(r for r in original["files"] if r["path"] == str(CSV.relative_to(ROOT)))
    if hashlib.sha256(CSV.read_bytes()).hexdigest() != csv_source["sha256"]:
        raise ValueError("Pinned CSV checksum mismatch")
    path = DEST / "manifest.json"
    result = json.loads(path.read_text()) if path.exists() else {
        "repository": "https://github.com/cambridge-collection/epsilon-data",
        "revision": REVISION,
        "period": {"start": START, "end": END, "inclusive": True},
        "selection": "Darwin-only CSV sorting-date window plus explicit display-date years in 1837-1843; not an XML-wide search of the complete catalogue.",
        "csv_source": csv_source,
        "files": [], "errors": [],
    }
    if result["csv_source"] != csv_source or result["revision"] != REVISION:
        raise ValueError("Expansion provenance mismatch")
    return path, result


def preserve(selected):
    path, manifest = source_manifest()
    DEST.mkdir(parents=True, exist_ok=True)
    previous = {r["path"]: r for r in manifest["files"]}
    manifest["errors"] = []
    print(f"Preserving {len(selected)} separate 1837-1843 XML candidates", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        for info in selected:
            row = info[3]
            name = row[" filename"]
            if not re.fullmatch(r"DCP-LETT-\d+[A-Z]*\.xml", name):
                raise ValueError(f"Unexpected filename: {name}")
            pending[pool.submit(fetch, f"{BASE}/xml/darwin-correspondence/letters/{name}", DEST / "letters" / name, previous.copy())] = row["id"]
        for n, future in enumerate(as_completed(pending), 1):
            try:
                entry = future.result()
                previous[entry["path"]] = entry
            except Exception as exc:
                manifest["errors"].append({"id": pending[future], "error": str(exc)})
                print(f"ERROR {pending[future]}: {exc}", flush=True)
            manifest["files"] = [previous[k] for k in sorted(previous)]
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
            if n % 50 == 0 or n == len(pending):
                print(f"Processed {n}/{len(pending)}; errors={len(manifest['errors'])}", flush=True)
    if manifest["errors"]:
        raise SystemExit("Incomplete preservation; inspect the separate manifest.")


def audit(headers, all_rows, selected, excluded):
    _, manifest = source_manifest()
    sources = {r["path"]: r for r in manifest["files"]}
    expected = {str((DEST / "letters" / i[3][" filename"]).relative_to(ROOT)) for i in selected}
    if set(sources) != expected or manifest["errors"]:
        raise ValueError("Manifest does not cover exactly the selected candidate XML")
    for relative, source in sources.items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Source checksum mismatch: {relative}")
    records = [audit_record(i, sources, raw_root=DEST, start=START, end=END) for i in selected]
    for record in records:
        record["metadata_multiple_senders"] = len(record["sender_evidence"]) > 1
        record["individual_voice_attribution_review_required"] = record["direction"] == "from_darwin"
        if record["period_selection_eligible"] and record["direction"] == "from_darwin" and record["metadata_multiple_senders"]:
            record["prospective_role"] = "hold_for_individual_authorship_review"
    records.sort(key=lambda r: (r["original_csv"]["sorting_date"], r["id"]))
    safe = [r for r in records if r["period_selection_eligible"]]
    held = [r for r in records if not r["period_selection_eligible"]]
    correspondents = defaultdict(lambda: {"from_darwin": [], "to_darwin": [], "labels": set()})
    for record in safe:
        side = "recipient" if record["direction"] == "from_darwin" else "sender"
        evidence = record[side + "_evidence"]
        key = " | ".join(sorted(p["attributes"].get("key", p["text"]) for p in evidence))
        entry = correspondents[key]
        entry[record["direction"]].append(record["id"])
        entry["labels"].add(" | ".join(p["text"] for p in evidence))
    correspondent_rows = []
    for key, entry in correspondents.items():
        correspondent_rows.append({"authority_key": key, "labels": sorted(entry["labels"]),
            "outgoing_count": len(entry["from_darwin"]), "incoming_count": len(entry["to_darwin"]),
            "outgoing_ids": entry["from_darwin"], "incoming_ids": entry["to_darwin"]})
    correspondent_rows.sort(key=lambda r: (-min(r["outgoing_count"], r["incoming_count"]), -r["incoming_count"], r["authority_key"]))
    summary = {
        "period": {"start": START, "end": END, "inclusive": True}, "revision": REVISION,
        "csv_sha256": manifest["csv_source"]["sha256"], "source_rows": len(all_rows),
        "candidates": len(records), "safe_records": len(safe), "held_records": len(held),
        "classification_counts": dict(Counter(r["classification"] for r in records)),
        "safe_by_direction": dict(Counter(r["direction"] for r in safe)),
        "held_by_direction": dict(Counter(r["direction"] for r in held)),
        "safe_by_csv_sort_year": {year: dict(Counter(r["direction"] for r in safe if r["original_csv"]["sorting_date"].startswith(year))) for year in map(str, range(1837, 1844))},
        "safe_records_requiring_exact_order_review": sum(r["exact_order_needs_review"] for r in safe),
        "date_structure_counts": dict(Counter(r["date_structure"] for r in records)),
        "supplemental_candidates_outside_sort_window": [r["id"] for r in records if not START <= r["original_csv"]["sorting_date"] <= END],
        "third_party_records_excluded_by_csv_filter": len(excluded),
        "source_checksum_verified_count": len(sources) + 1,
        "records_with_transcriptions_in_xml": sum(r["has_transcription_in_preserved_xml"] for r in records),
        "records_with_structured_receipt_dates": sum(bool(r["received_date_constraints"]) for r in records),
        "safe_outgoing_with_multiple_senders": [r["id"] for r in safe if r["direction"] == "from_darwin" and r["metadata_multiple_senders"]],
        "reply_matching_status": "not performed by this inventory; see a separate pilot if present",
        "voice_attribution_status": "CSV/XML correspondent identities checked; individual prose authorship, quoted text, joint authorship, extracts, and text survival still require review",
        "scope_limit": manifest["selection"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, values in [("audit.jsonl", records), ("safe_within_period.jsonl", safe), ("ambiguous_or_later.jsonl", held)]:
        write_jsonl(OUT / name, values)
    for name, value in [("summary.json", summary), ("correspondents.json", correspondent_rows),
                        ("excluded_third_party.json", [i[3] for i in excluded])]:
        (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    fields = ["classification", "direction", "xml_earliest", "xml_latest", "date_structure", "exact_order_needs_review", "xml_path", "xml_sha256"]
    with (OUT / "audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers + fields)
        writer.writeheader()
        for r in records:
            writer.writerow({**r["original_csv"], **{k: r[k] for k in fields if k in r},
                             **{k: r["provenance"][k] for k in fields if k in r["provenance"]}})
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Preserve missing XML files before the offline audit")
    args = parser.parse_args()
    headers, rows, selected, excluded = selection()
    if args.fetch:
        preserve(selected)
    audit(headers, rows, selected, excluded)


if __name__ == "__main__":
    main()

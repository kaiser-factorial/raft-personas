"""Preserve full bodies and prepare bounded Luna-first correspondent packets."""

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetch_metadata import ROOT, fetch
from fetch_letter_bodies import validate
from search_body_dates import parse_page, write_jsonl

OUT = ROOT / "reports/1837-1843/correspondent-review"
RAW = ROOT / "data/raw/dcp/correspondent-review-1837-1843"
GROUPS = {"emma": "../nameregs/nameregs_1218.xml", "kemp": "../nameregs/nameregs_2657.xml"}


def main():
    global OUT, RAW, GROUPS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--batch", choices=("emma-kemp", "henslow-lyell"), default="emma-kemp")
    args = parser.parse_args()
    if args.batch == "henslow-lyell":
        OUT = ROOT / "reports/1837-1843/henslow-lyell"
        RAW = ROOT / "data/raw/dcp/henslow-lyell-1837-1843"
        GROUPS = {"henslow": "../nameregs/nameregs_2235.xml", "lyell": "../nameregs/nameregs_3051.xml"}
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    audit = {r["id"]: r for r in map(json.loads, (ROOT / "reports/1837-1843/audit.jsonl").read_text().splitlines())}
    inventory = {r["authority_key"]: r for r in json.loads((ROOT / "reports/1837-1843/correspondents.json").read_text())}
    groups = {name: inventory[key] for name, key in GROUPS.items()}
    if args.batch == "henslow-lyell":
        for name, key in GROUPS.items():
            held = [r for r in audit.values() if not r["period_selection_eligible"]
                    and any(p["attributes"].get("key") == key for p in r["sender_evidence"] + r["recipient_evidence"])]
            groups[name]["supplementary_held_ids"] = [r["id"] for r in held]
            for row in held:
                direction = "outgoing" if row["direction"] == "from_darwin" else "incoming"
                groups[name][direction + "_ids"].append(row["id"])
                groups[name][direction + "_count"] += 1
    ids = sorted({i for g in groups.values() for direction in ("outgoing_ids", "incoming_ids") for i in g[direction]})
    path = RAW / "manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {"period": "1837-1843", "selection": groups, "requested_ids": ids, "files": [], "errors": []}
    if manifest["requested_ids"] != ids:
        raise ValueError("Selection changed; preserve the existing batch")
    previous = {r["id"]: r for r in manifest["files"]}
    pilot = {r["id"]: r for r in json.loads((ROOT / "data/raw/dcp/expansion-1837-1843-pilot/manifest.json").read_text())["files"]}
    if args.batch == "henslow-lyell":
        for earlier in [ROOT / "data/raw/dcp/correspondent-review-1837-1843/manifest.json",
                        ROOT / "data/raw/dcp/correspondent-review-1837-1843/seed-context/manifest.json"]:
            pilot.update({r["id"]: r for r in json.loads(earlier.read_text())["files"]})
    sources = dict(previous)

    def preserve(ident):
        if ident in previous or ident in pilot:
            old = (previous if ident in previous else pilot)[ident]
            raw = (ROOT / old["path"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != old["sha256"]:
                raise ValueError(f"Changed preserved source: {ident}")
            validate(raw, ident)
            return old
        if not args.fetch:
            raise ValueError(f"Missing source {ident}; run --fetch")
        url = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{ident}.xml"
        result = fetch(url, RAW / f"{ident}.html", {})
        validate((ROOT / result["path"]).read_bytes(), ident)
        return {**result, "id": ident}

    manifest["errors"] = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(preserve, ident): ident for ident in ids}
        for n, future in enumerate(as_completed(futures), 1):
            ident = futures[future]
            try:
                sources[ident] = future.result()
            except Exception as exc:
                manifest["errors"].append({"id": ident, "error": str(exc)})
                print(f"ERROR {ident}: {exc}", flush=True)
            manifest["files"] = [sources[k] for k in sorted(sources)]
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
            if n % 10 == 0 or n == len(ids):
                print(f"Preserved or reused {n}/{len(ids)}", flush=True)
    if manifest["errors"]:
        raise ValueError("Source preservation incomplete")
    letters = {}
    for ident in ids:
        source = sources[ident]
        letters[ident] = {"id": ident, "source": source, "metadata_audit": audit[ident],
                          **parse_page((ROOT / source["path"]).read_bytes())}
        if not letters[ident]["paragraphs"]:
            print(f"WARNING no transcribed body: {ident}", flush=True)
    write_jsonl(OUT / "letters.jsonl", list(letters.values()))
    packets = []
    for name, selection in groups.items():
        ordered = sorted(selection["outgoing_ids"] + selection["incoming_ids"], key=lambda i: (audit[i]["original_csv"]["sorting_date"], i))
        packet = {"group_id": name, "scope": "All safe-period direct letters in this correspondent group from the current pinned candidate set; not an exhaustive archive-wide search.",
                  "outgoing_ids": selection["outgoing_ids"], "incoming_ids": selection["incoming_ids"],
                  "instructions": "Read every body and editorial note in full. Propose links or explain absent/ambiguous antecedents for every outgoing. Incoming voice is never Darwin. Replies point response -> incoming; knowledge points incoming -> dated Darwin witness. Original dates remain unchanged. Missing texts are reference observations, never invented prompts. No automatic promotion from dates, correspondent identity, adjacency, or topic overlap. Parent adjudication controls accepted relationships.",
                  "letters": [letters[i] for i in ordered]}
        if args.batch == "henslow-lyell":
            packet["scope"] = "All safe-period letters in this correspondent group from the pinned inventory, plus matching held-period candidates listed separately. Held records remain ineligible until an explicit, evidenced refinement; not an archive-wide completeness claim."
            packet["supplementary_held_ids"] = selection["supplementary_held_ids"]
        packet_path = OUT / f"{name}.packet.json"
        if packet_path.exists() and packet_path.read_text() != json.dumps(packet, indent=2, ensure_ascii=False) + "\n":
            raise ValueError(f"Existing reviewer packet differs: {name}")
        packet_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n")
        packets.append({"group": name, "path": str(packet_path.relative_to(ROOT)), "sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
                        "outgoing_count": len(selection["outgoing_ids"]), "incoming_count": len(selection["incoming_ids"])})
    (OUT / "manifest.json").write_text(json.dumps({"method": "Luna first full-body proposals followed by primary-agent evidence adjudication", "packets": packets,
             "source_manifest": str(path.relative_to(ROOT)), "source_manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}, indent=2) + "\n")
    print(json.dumps(packets, indent=2))


if __name__ == "__main__":
    main()

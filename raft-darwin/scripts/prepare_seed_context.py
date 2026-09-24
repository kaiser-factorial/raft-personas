"""Preserve five incoming-to-Darwin sources explicitly cited in the Kemp chain."""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetch_metadata import ROOT, fetch
from fetch_letter_bodies import validate
from search_body_dates import parse_page, write_jsonl

IDS = ["669", "690", "701", "707", "708"]
RAW = ROOT / "data/raw/dcp/correspondent-review-1837-1843/seed-context"
OUT = ROOT / "reports/1837-1843/correspondent-review"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / "manifest.json"
    manifest = json.loads(path.read_text()) if path.exists() else {"requested_ids": ["DCP-LETT-" + i for i in IDS], "purpose": "Incoming-to-Darwin context sources explicitly referenced by the Kemp letters; two retain ambiguous raw XML period classifications.", "files": []}
    previous = {s["path"]: s for s in manifest["files"]}
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = {pool.submit(fetch, f"https://www.darwinproject.ac.uk/letter/?docId=letters/{ident}.xml", RAW / f"{ident}.html", previous.copy()): ident for ident in manifest["requested_ids"]}
        for future in as_completed(pending):
            source = {**future.result(), "id": pending[future]}
            validate((ROOT / source["path"]).read_bytes(), source["id"])
            previous[source["path"]] = source
            manifest["files"] = [previous[k] for k in sorted(previous)]
            path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    audit = {r["id"]: r for r in map(json.loads, (ROOT / "reports/1837-1843/audit.jsonl").read_text().splitlines())}
    letters = []
    for s in manifest["files"]:
        raw = (ROOT / s["path"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == s["sha256"]
        assert audit[s["id"]]["direction"] == "to_darwin"
        letters.append({"id": s["id"], "source": s, "metadata_audit": audit[s["id"]], **parse_page(raw)})
    write_jsonl(OUT / "seed-context.letters.jsonl", letters)
    kemp = json.loads((OUT / "kemp.packet.json").read_text())
    (OUT / "seed-context.packet.json").write_text(json.dumps({"incoming_ids": [r["id"] for r in letters], "incoming_letters": letters,
        "Darwin_witness_letters": [r for r in kemp["letters"] if r["metadata_audit"]["direction"] == "from_darwin"],
        "scope": "Evaluate explicit cross-correspondent knowledge use only. These incoming letters cannot be conversation prompts for Darwin's letters to Kemp. Preserve original XML period holds; no automatic promotion or receipt day inferred from composition."}, indent=2, ensure_ascii=False) + "\n")
    print(f"Preserved {len(letters)} incoming context sources")


if __name__ == "__main__":
    main()

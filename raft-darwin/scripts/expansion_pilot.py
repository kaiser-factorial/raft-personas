"""Preserve an explicitly bounded pilot of public 1837-1843 letter pages.

Extraction retains the original source page and keeps editorial notes distinct
from prose. It does not infer pairings; those require a separate evidence review.
"""

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from fetch_metadata import ROOT, fetch
from fetch_letter_bodies import validate
from search_body_dates import parse_page, write_jsonl

IDS = ["345", "346", "441", "444", "445", "699", "701F", "711", "711F", "720", "720F"]
RAW = ROOT / "data/raw/dcp/expansion-1837-1843-pilot"
OUT = ROOT / "reports/1837-1843/pilot"


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "purpose": "Purposive pilot, not a random sample or corpus-wide reply audit",
        "selection_reason": "One early post-return family exchange, one courtship exchange, and three late-1843 Kemp exchanges selected from bidirectional catalogue sequences. These selections are not confirmed pairs until read.",
        "requested_ids": [f"DCP-LETT-{s}" for s in IDS], "files": [],
    }
    manifest.setdefault("initial_requested_ids", manifest["requested_ids"].copy())
    additions = [f"DCP-LETT-{s}" for s in IDS if f"DCP-LETT-{s}" not in manifest["requested_ids"]]
    if additions:
        manifest.setdefault("selection_amendments", []).append({
            "added_ids": additions,
            "reason": "Full-text reading showed that 445 answers Emma's reading and housing comments absent from 441. Add intervening incoming 444 to test the actual antecedent; retain 441 as the original rejected candidate.",
        })
        manifest["requested_ids"].extend(additions)
    previous = {s["path"]: s for s in manifest["files"]}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {}
        for ident in manifest["requested_ids"]:
            url = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{ident}.xml"
            futures[pool.submit(fetch, url, RAW / f"{ident}.html", previous.copy())] = ident
        for future in as_completed(futures):
            source = future.result()
            source["id"] = futures[future]
            validate((ROOT / source["path"]).read_bytes(), source["id"])
            previous[source["path"]] = source
            manifest["files"] = [previous[k] for k in sorted(previous)]
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
            print(f"Preserved {source['id']}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    letters = []
    for source in manifest["files"]:
        raw = (ROOT / source["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError(f"Changed archived page: {source['id']}")
        letters.append({"id": source["id"], "source": source, **parse_page(raw)})
    write_jsonl(OUT / "letters.jsonl", letters)
    print(f"Extracted {len(letters)} pilot letters", flush=True)


if __name__ == "__main__":
    main()

"""Preserve incoming sources cited in the Henslow/Lyell review witnesses."""

import json
import hashlib

from fetch_metadata import ROOT, fetch
from fetch_letter_bodies import validate
from search_body_dates import parse_page, write_jsonl

OUT = ROOT / "reports/1837-1843/henslow-lyell"
RAW = ROOT / "data/raw/dcp/henslow-lyell-1837-1843/context"
IDS = ["DCP-LETT-534", "DCP-LETT-690", "DCP-LETT-706", "DCP-LETT-708"]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"requested_ids": IDS, "files": []}
    known = {s["id"]: s for s in manifest["files"]}
    for p in [ROOT / "data/raw/dcp/correspondent-review-1837-1843/manifest.json",
              ROOT / "data/raw/dcp/correspondent-review-1837-1843/seed-context/manifest.json"]:
        known.update({s["id"]: s for s in json.loads(p.read_text())["files"]})
    sources = []
    for ident in IDS:
        if ident in known:
            source = known[ident]
            assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
        else:
            source = {**fetch(f"https://www.darwinproject.ac.uk/letter/?docId=letters/{ident}.xml", RAW / f"{ident}.html", {}), "id": ident}
        validate((ROOT / source["path"]).read_bytes(), ident)
        sources.append(source)
    manifest["files"] = sources
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    audit = {r["id"]: r for r in map(json.loads, (ROOT / "reports/1837-1843/audit.jsonl").read_text().splitlines())}
    incoming = [{"id": s["id"], "source": s, "metadata_audit": audit[s["id"]], **parse_page((ROOT / s["path"]).read_bytes())} for s in sources]
    assert all(r["metadata_audit"]["direction"] == "to_darwin" for r in incoming)
    write_jsonl(OUT / "context.letters.jsonl", incoming)
    witnesses = [r for r in map(json.loads, (OUT / "letters.jsonl").read_text().splitlines())
                 if r["id"] in ["DCP-LETT-543", "DCP-LETT-660", "DCP-LETT-691", "DCP-LETT-696", "DCP-LETT-705", "DCP-LETT-712"]]
    (OUT / "context.packet.json").write_text(json.dumps({"incoming_letters": incoming, "Darwin_witness_letters": witnesses,
         "scope": "Cross-correspondent knowledge only; source letters to Darwin retain authorship and original dates. Distinguish same-topic continuity, oral information, and exact content matches. Later witnesses do not overwrite earlier known-by evidence. 690 remains held by the raw period audit; 696 has alternative dates."}, ensure_ascii=False, indent=2) + "\n")
    print(f"Preserved {len(incoming)} incoming sources; {len(witnesses)} witness letters")


if __name__ == "__main__":
    main()

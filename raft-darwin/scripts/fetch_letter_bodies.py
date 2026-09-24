"""Preserve public letter pages for the bounded 37-337 body-date search."""

import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
REVISION = "ab0d973bae05b54d68d82d068211015996cfec06"
CSV = ROOT / "data/raw/epsilon" / REVISION / "darwin-correspondence.csv"
RAW = ROOT / "data/raw/dcp/body-date-search-37-337"


def selected_rows():
    rows, excluded = [], []
    for row in csv.DictReader(CSV.open()):
        match = re.fullmatch(r"DCP-LETT-(\d+)([A-Z]*)", row["id"])
        if not match or not 37 <= int(match[1]) <= 337:
            continue
        direct = any((row[f"{side}_surname"], row[f"{side}_forename"])
                     == ("Darwin", "C. R.") for side in ("sender", "recipient"))
        (rows if direct else excluded).append(row)
    return rows, excluded


def validate(raw, ident):
    doc = html.fromstring(raw)
    details = doc.xpath('//div[@id="letter_details"]')
    if len(details) != 1 or ident not in details[0].text_content():
        raise ValueError(f"Missing or wrong letter details: {ident}")


def preserve(ident, previous, reusable):
    if ident in previous:
        record = previous[ident]
        raw = (ROOT / record["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError(f"Changed archived page: {ident}")
        validate(raw, ident)
        return record
    url = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{ident}.xml"
    if ident in reusable:
        old = reusable[ident]
        raw = (ROOT / old["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != old["sha256"]:
            raise ValueError(f"Changed reusable page: {ident}")
        validate(raw, ident)
        return {"id": ident, "url": url, "path": old["path"], "sha256": old["sha256"],
                "bytes": len(raw), "retrieved_at": old["retrieval_completed_at_utc"],
                "reused_from": "receipt-case-301-306/manifest.json"}
    path = RAW / f"{ident}.html"
    if path.exists():
        raise ValueError(f"Unmanifested source exists: {path}")
    scratch = Path("/tmp") / f"raft-darwin-letter{ident.removeprefix('DCP-LETT-')}.html"
    if scratch.exists() and ident in {"DCP-LETT-303", "DCP-LETT-156", "DCP-LETT-174", "DCP-LETT-194"}:
        raw = scratch.read_bytes()
        retrieved = datetime.fromtimestamp(scratch.stat().st_mtime, timezone.utc).isoformat()
        method = "preserved_from_initial_page_check"
        headers = {}
    else:
        for attempt in range(4):
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "Darwin-chronology-research/1.0"})
                with urllib.request.urlopen(request, timeout=40) as response:
                    raw = response.read()
                    headers = {"http_status": response.status,
                               "content_type": response.headers.get("Content-Type"),
                               "etag": response.headers.get("ETag")}
                retrieved = datetime.now(timezone.utc).isoformat()
                method = "downloaded"
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == 3 or (isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 404)):
                    raise
                time.sleep(2 ** attempt)
        time.sleep(0.2)
    validate(raw, ident)
    path.write_bytes(raw)
    return {"id": ident, "url": url, "path": str(path.relative_to(ROOT)),
            "retrieved_at": retrieved, "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw), "method": method, **headers}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / "manifest.json"
    rows, excluded = selected_rows()
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "requested_numeric_range": [37, 337], "include_suffix_entries": True,
        "csv_path": str(CSV.relative_to(ROOT)),
        "csv_sha256": hashlib.sha256(CSV.read_bytes()).hexdigest(),
        "csv_revision": REVISION,
        "selected_original_metadata": rows,
        "excluded_third_party_original_metadata": excluded,
        "csv_gap_checks": [
            {"id": "DCP-LETT-156", "status": "cancelled_not_clearly_a_letter"},
            {"id": "DCP-LETT-174", "status": "cancelled_third_party_letter"},
            {"id": "DCP-LETT-194", "status": "cancelled_not_clearly_a_letter"},
        ], "files": [], "errors": [],
    }
    previous = {entry["id"]: entry for entry in manifest["files"]}
    old_manifest = json.loads((ROOT / "data/raw/dcp/receipt-case-301-306/manifest.json").read_text())
    reusable = {entry["id"]: entry for entry in old_manifest["sources"]}
    ids = [row["id"] for row in rows] + ["DCP-LETT-156", "DCP-LETT-174", "DCP-LETT-194"]
    manifest["errors"] = []

    def save():
        manifest["files"] = [previous[k] for k in sorted(previous)]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    print(f"Retrieving {len(rows)} Darwin-involved pages and preserving 3 catalogue-gap checks", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(preserve, ident, previous.copy(), reusable): ident for ident in ids}
        for n, future in enumerate(as_completed(futures), 1):
            ident = futures[future]
            try:
                previous[ident] = future.result()
            except Exception as exc:
                manifest["errors"].append({"id": ident, "error": str(exc)})
                print(f"ERROR {ident}: {exc}", flush=True)
            save()
            if n % 30 == 0 or n == len(ids):
                print(f"Processed {n}/{len(ids)}; {len(manifest['errors'])} errors", flush=True)
    if manifest["errors"]:
        raise SystemExit("Some pages could not be retrieved; inspect manifest errors.")


if __name__ == "__main__":
    main()

"""Preserve a pinned CSV and the XML evidence for the requested date audit."""

import csv
import hashlib
import io
import json
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "ab0d973bae05b54d68d82d068211015996cfec06"
RAW = ROOT / "data" / "raw" / "epsilon" / REVISION
BASE = f"https://raw.githubusercontent.com/cambridge-collection/epsilon-data/{REVISION}"
START, END = "1828-01-01", "1836-12-31"


def is_darwin(row, side):
    """Match Charles Robert Darwin's catalogue identity on the given side."""
    return (row[f"{side}_surname"], row[f"{side}_forename"]) == ("Darwin", "C. R.")


def fetch(url, path, previous):
    relative = str(path.relative_to(ROOT))
    if path.exists():
        content = path.read_bytes()
        old = previous.get(relative)
        digest = hashlib.sha256(content).hexdigest()
        if not old or old["sha256"] != digest or old["url"] != url:
            raise ValueError(f"Unmanifested or changed source file: {relative}")
        return old
    path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "raft-darwin-metadata-audit/1.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                content = response.read()
                metadata = {
                    "path": relative,
                    "url": url,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "bytes": len(content),
                    "http_status": response.status,
                    "etag": response.headers.get("ETag"),
                    "content_type": response.headers.get("Content-Type"),
                }
            if path.suffix == ".xml":
                xml = ET.fromstring(content)
                if xml.get("{http://www.w3.org/XML/1998/namespace}id") != path.stem:
                    raise ValueError(f"Unexpected XML identity in {relative}")
            path.write_bytes(content)
            return metadata
        except (urllib.error.URLError, TimeoutError) as exc:
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 404):
                raise
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest_path = RAW / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "repository": "https://github.com/cambridge-collection/epsilon-data",
        "revision": REVISION,
        "period": {"start": START, "end": END},
        "files": [],
    }
    previous = {entry["path"]: entry for entry in manifest["files"]}

    def save(entry):
        previous[entry["path"]] = entry
        manifest["files"] = [previous[k] for k in sorted(previous)]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    for filename in ["csv/darwin-correspondence.csv", "README.md", "LICENSE.txt"]:
        save(fetch(f"{BASE}/{filename}", RAW / Path(filename).name, previous))
    content = (RAW / "darwin-correspondence.csv").read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(content)))
    selected = []
    for row in rows:
        if not (is_darwin(row, "sender") or is_darwin(row, "recipient")):
            continue
        in_window = START <= row["sorting_date"] <= END
        explicit_overlap = any(1828 <= int(y) <= 1836 for y in re.findall(r"(?<!\d)\d{4}(?!\d)", row["date"]))
        if in_window or explicit_overlap:
            selected.append(row)
    print(f"Pinned source: {len(rows)} CSV records; {len(selected)} Darwin-only XML candidates", flush=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {}
        for row in selected:
            filename = row[" filename"]
            if not re.fullmatch(r"DCP-LETT-[0-9]+[A-Z]*\.xml", filename):
                raise ValueError(f"Unexpected XML filename: {filename!r}")
            futures[pool.submit(fetch, f"{BASE}/xml/darwin-correspondence/letters/{filename}", RAW / "letters" / filename, previous)] = row["id"]
        for n, future in enumerate(as_completed(futures), 1):
            save(future.result())
            if n % 40 == 0 or n == len(futures):
                print(f"Preserved {n}/{len(futures)} XML records", flush=True)
    print(str(manifest_path.relative_to(ROOT)), flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compile all unique letters across all periods into data/letters.sqlite.

Preserves:
- Letter ID, title, sender, recipient, direction, date bounds, classification
- Canonical online Darwin Correspondence Project URL & HTML SHA256
- Raw Epsilon XML GitHub URL & XML SHA256
- Parsed paragraphs, headers, and metadata (zlib compressed)
"""
from __future__ import annotations

import json
import sqlite3
import zlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/letters.sqlite"

PERIODS = [
    "1844-1846", "1847-1850", "1851-1855", "1856-1857", "1858-1859",
    "1859-post-origin", "1860", "1861", "1862", "1863", "1864", "1865",
    "1866", "1867", "1868"
]


def person_text(evidence: list[dict[str, Any]]) -> str:
    names = []
    for e in evidence:
        text = e.get("text", "")
        if ", " in text:
            s, f = text.split(", ", 1)
            text = f"{f} {s}"
        if text and text not in names:
            names.append(text)
    return " and ".join(names) if names else ""


def init_db(conn: sqlite3.Connection):
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS letters (
            id TEXT PRIMARY KEY,
            title TEXT,
            sender TEXT,
            recipient TEXT,
            direction TEXT,
            xml_earliest TEXT,
            xml_latest TEXT,
            dcp_url TEXT,
            dcp_sha256 TEXT,
            xml_url TEXT,
            xml_sha256 TEXT,
            classification TEXT,
            periods_json TEXT,
            paragraphs_blob BLOB,
            record_blob BLOB
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_letters_direction ON letters(direction);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_letters_dates ON letters(xml_earliest, xml_latest);")


def build():
    print("Collecting all unique letters across periods...")
    letters: dict[str, dict[str, Any]] = {}
    letter_periods: dict[str, set[str]] = {}

    for p in PERIODS:
        # Load from all_letters.jsonl if present, or letters.jsonl
        p_paths = [
            ROOT / f"reports/{p}/review/all_letters.jsonl",
            ROOT / f"reports/{p}/review/letters.jsonl"
        ]
        for path in p_paths:
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    lid = r["id"]
                    if lid not in letter_periods:
                        letter_periods[lid] = set()
                    letter_periods[lid].add(p)
                    # Keep most detailed version if duplicate
                    if lid not in letters or len(r.get("paragraphs", [])) > len(letters[lid].get("paragraphs", [])):
                        letters[lid] = r

    # Also check remaining review 1837-1843
    rem = ROOT / "reports/1837-1843/remaining-review/all_letters.jsonl"
    if rem.exists():
        with open(rem, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                lid = r["id"]
                if lid not in letter_periods:
                    letter_periods[lid] = set()
                letter_periods[lid].add("1837-1843")
                if lid not in letters:
                    letters[lid] = r

    print(f"Discovered {len(letters)} unique letters.")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    rows_to_insert = []
    for lid, r in letters.items():
        meta = r.get("metadata_audit", {})
        prov = meta.get("provenance", {})
        source = r.get("source", {})

        sender = person_text(meta.get("sender_evidence", []))
        recipient = person_text(meta.get("recipient_evidence", []))
        direction = meta.get("direction", "")
        earliest = meta.get("xml_earliest", "")
        latest = meta.get("xml_latest", "")
        classification = meta.get("classification", "")

        dcp_url = source.get("url") or f"https://www.darwinproject.ac.uk/letter/?docId=letters/{lid}.xml"
        dcp_sha256 = source.get("sha256", "")
        xml_url = prov.get("xml_url") or f"https://raw.githubusercontent.com/cambridge-collection/epsilon-data/ab0d973bae05b54d68d82d068211015996cfec06/xml/darwin-correspondence/letters/{lid}.xml"
        xml_sha256 = prov.get("xml_sha256", "")

        periods_str = json.dumps(sorted(letter_periods.get(lid, [])))
        paragraphs_compressed = zlib.compress(json.dumps(r.get("paragraphs", [])).encode("utf-8"))
        record_compressed = zlib.compress(json.dumps(r).encode("utf-8"))

        rows_to_insert.append((
            lid,
            r.get("title", ""),
            sender,
            recipient,
            direction,
            earliest,
            latest,
            dcp_url,
            dcp_sha256,
            xml_url,
            xml_sha256,
            classification,
            periods_str,
            paragraphs_compressed,
            record_compressed
        ))

    conn.executemany("""
        INSERT INTO letters (
            id, title, sender, recipient, direction,
            xml_earliest, xml_latest, dcp_url, dcp_sha256,
            xml_url, xml_sha256, classification, periods_json,
            paragraphs_blob, record_blob
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows_to_insert)

    conn.commit()
    conn.execute("VACUUM;")
    conn.close()

    db_size = DB_PATH.stat().st_size
    print(f"Successfully created {DB_PATH}: {len(rows_to_insert)} letters stored ({db_size / 1e6:.2f} MB).")


if __name__ == "__main__":
    build()

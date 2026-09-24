#!/usr/bin/env python3
"""Refetch letter raw HTML from Cambridge DCP or raw XML from Epsilon on demand.

Usage:
  python scripts/refetch_letter.py DCP-LETT-5779 [--html] [--xml] [--out DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data/letters.sqlite"


def get_letter_info(letter_id: str):
    if not DB_PATH.exists():
        sys.exit(f"Error: Database not found at {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, dcp_url, dcp_sha256, xml_url, xml_sha256
        FROM letters WHERE id = ?
    """, (letter_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        sys.exit(f"Error: Letter ID {letter_id} not found in database.")
    return {
        "id": row[0],
        "title": row[1],
        "dcp_url": row[2],
        "dcp_sha256": row[3],
        "xml_url": row[4],
        "xml_sha256": row[5]
    }


def fetch_url(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (RAFT Persona Letter Refetcher)"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def main():
    parser = argparse.ArgumentParser(description="Refetch letter from DCP or Epsilon.")
    parser.add_argument("letter_id", help="Letter ID (e.g. DCP-LETT-5779)")
    parser.add_argument("--html", action="store_true", help="Refetch raw DCP HTML")
    parser.add_argument("--xml", action="store_true", help="Refetch raw Epsilon XML")
    parser.add_argument("--out", type=Path, default=Path("."), help="Output directory")
    args = parser.parse_args()

    info = get_letter_info(args.letter_id)
    args.out.mkdir(parents=True, exist_ok=True)

    if not args.html and not args.xml:
        print(json.dumps(info, indent=2))
        print("\nSpecify --html to download raw HTML, or --xml to download Epsilon XML.")
        return

    if args.xml:
        xml_url = info["xml_url"]
        print(f"Fetching XML from {xml_url}...")
        raw_xml = fetch_url(xml_url)
        xml_sha = hashlib.sha256(raw_xml).hexdigest()
        out_file = args.out / f"{info['id']}.xml"
        out_file.write_bytes(raw_xml)
        print(f"Saved {out_file} ({len(raw_xml)} bytes). SHA256: {xml_sha}")
        if info["xml_sha256"]:
            match = "MATCH" if xml_sha == info["xml_sha256"] else "MISMATCH"
            print(f"Catalog SHA256 verification: {match}")

    if args.html:
        html_url = info["dcp_url"]
        print(f"Fetching HTML from {html_url}...")
        raw_html = fetch_url(html_url)
        html_sha = hashlib.sha256(raw_html).hexdigest()
        out_file = args.out / f"{info['id']}.html"
        out_file.write_bytes(raw_html)
        print(f"Saved {out_file} ({len(raw_html)} bytes). SHA256: {html_sha}")
        if info["dcp_sha256"]:
            match = "MATCH" if html_sha == info["dcp_sha256"] else "CHANGED (DCP live update)"
            print(f"Catalog SHA256 verification: {match}")


if __name__ == "__main__":
    main()

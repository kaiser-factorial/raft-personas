#!/usr/bin/env python3
"""Print complete, bounded groups of preserved bodies for manual review."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
packet = json.loads((ROOT / "reports/pre-beagle-1828-1831/source_packet.json").read_text())
group = sys.argv[1]
start, stop = map(int, sys.argv[2:4])
for letter in packet[group][start:stop]:
    meta = letter["original_csv"]
    print(f"\n{letter['id']} | {meta['date']} | {meta['sender_forename']} {meta['sender_surname']} -> {meta['recipient_forename']} {meta['recipient_surname']}")
    print("XML", json.dumps(letter["xml_date_bounds"]), "BODY WORDS", letter["body_word_count"])
    for paragraph in letter["paragraphs"]:
        print(f"P{paragraph['body_paragraph']}: {paragraph['text']}")
    print("END BODY", letter["id"])

#!/usr/bin/env python3
"""Build and format darwin_1 persona dataset for post-origin (1859-11-25 through 1868-12-31).

Conforms strictly to RAFT project format (raft.project.v1) and Darwin persona standards:
- One single-exchange transcript per conversation file (gapless 1-based numbering)
- Verified incoming question -> Darwin answer exchanges
- Unpaired Darwin prose as dated grounding documents in corpus/documents.jsonl
- Pure plain text (no HTML apparatus, footnotes, or annotations)
- Clean recipient / sender name formatting
- Complete source provenance and accounting
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from period_review import load
from prepare_period import ROOT, read, rows, write
from raft_render_text import render_html


DEST = ROOT / "darwin_1"
START_DATE = "1859-11-25"
END_DATE = "1868-12-31"
RUN02_PERIODS = [
    "1859-post-origin", "1860", "1861", "1862", "1863",
    "1864", "1865", "1866", "1867", "1868"
]


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def person(evidence: list[dict[str, Any]]) -> str:
    names = []
    for e in evidence:
        text = e.get("text", "")
        if ", " in text:
            surname, forename = text.split(", ", 1)
            text = f"{forename} {surname}"
        if text and text not in names:
            names.append(text)
    return " and ".join(names) if names else "Correspondent"


def clean_text(text: str) -> str:
    # Ensure stripped, normalized newlines, no HTML artifacts
    text = text.strip()
    text = re.sub(r"\r\n|\r", "\n", text)
    # Strip any stray HTML tags if any leaked
    text = re.sub(r"<[^>]+>", "", text)
    # Remove consecutive spaces
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize multiple newlines to double newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_date(pair: dict[str, Any], letter: dict[str, Any]) -> str | None:
    meta = letter.get("metadata_audit", {})
    e, l = meta.get("xml_earliest"), meta.get("xml_latest")
    if e and e == l and re.fullmatch(r"\d{4}-\d{2}-\d{2}", e):
        return e
    pol = pair.get("response_date_policy") or ""
    m = re.search(r"\d{4}-\d{2}-\d{2}", pol)
    if m:
        return m.group(0)
    rec = pair.get("actual_receipt_date") or ""
    m = re.search(r"\d{4}-\d{2}-\d{2}", rec)
    if m:
        return m.group(0)
    if e and re.fullmatch(r"\d{4}-\d{2}-\d{2}", e):
        return e
    return None


def build_darwin_1():
    print(f"Building darwin_1 dataset for post-origin interval {START_DATE} to {END_DATE}...")

    # 1. Load all letters across Run 02
    all_letters: dict[str, dict[str, Any]] = {}
    db_path = ROOT / "data/letters.sqlite"
    if db_path.exists():
        import sqlite3
        import zlib
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, record_blob FROM letters")
        for lid, blob in cur.fetchall():
            all_letters[lid] = json.loads(zlib.decompress(blob).decode("utf-8"))
        conn.close()
        print(f"Loaded {len(all_letters)} total letters from {db_path}.")
    else:
        for p in RUN02_PERIODS:
            path = ROOT / "reports" / p / "review/all_letters.jsonl"
            if path.exists():
                for r in rows(path):
                    all_letters[r["id"]] = r
        print(f"Loaded {len(all_letters)} total letters from all_letters.jsonl across {len(RUN02_PERIODS)} periods.")

    # 2. Collect all direct reply pairs from accepted ledgers
    # Filter to pairs whose Darwin response falls strictly within the post-origin research interval
    outgoing_to_incoming: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pair_count_in_window = 0
    pairs_outside_window = []

    for p in RUN02_PERIODS:
        ledgers = sorted((ROOT / "data/annotations/periods" / p).glob("batch-*.json"))
        for lf in ledgers:
            ledger_data = read(lf)
            for pair in ledger_data.get("direct_reply_pairs", []):
                out_id = pair["outgoing_id"]
                out_letter = all_letters.get(out_id)
                if not out_letter:
                    continue
                date = extract_date(pair, out_letter)
                if not date or not (START_DATE <= date <= END_DATE):
                    pairs_outside_window.append({
                        "period": p, "ledger": lf.name, "outgoing_id": out_id,
                        "incoming_id": pair.get("incoming_id"), "date": date
                    })
                    continue

                pair_count_in_window += 1
                outgoing_to_incoming[out_id].append({
                    "period": p,
                    "ledger": str(lf.relative_to(ROOT)),
                    "pair": pair,
                    "date": date,
                })

    print(f"Found {pair_count_in_window} direct reply pairs inside post-origin window ({len(pairs_outside_window)} outside context pairs omitted).")
    print(f"Grouped into {len(outgoing_to_incoming)} distinct outgoing response letters.")

    # Prepare directories
    DEST.mkdir(parents=True, exist_ok=True)
    conv_dir = DEST / "conversations"
    corpus_dir = DEST / "corpus"
    meta_dir = DEST / "metadata"
    blobs_dir = DEST / "blobs"
    fetch_dir = DEST / "fetch"

    # Clean out any old conversation files in conv_dir to avoid stale numbering
    if conv_dir.exists():
        for old_f in conv_dir.glob("*.json"):
            old_f.unlink()

    for d in (conv_dir, corpus_dir, meta_dir, blobs_dir, fetch_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 3. Format conversations
    # Sort outgoing letters by response date, then by outgoing_id
    sorted_outgoings = []
    for out_id, entries in outgoing_to_incoming.items():
        out_letter = all_letters[out_id]
        date = entries[0]["date"]
        sorted_outgoings.append((date, out_id, entries, out_letter))

    sorted_outgoings.sort(key=lambda x: (x[0], x[1]))

    transcripts = []
    outgoing_ids_used = set()
    darwin_answer_hashes = set()
    conversation_provenance = []

    transcript_index = 1
    for date, out_id, entries, out_letter in sorted_outgoings:
        # Render Darwin answer
        out_source_path = ROOT / out_letter["source"]["path"]
        if out_source_path.exists():
            rendered_out = render_html(out_source_path)
            answer_text = clean_text(rendered_out["content"])
        else:
            answer_text = clean_text("\n\n".join(p["text"] for p in out_letter.get("paragraphs", [])))

        if not answer_text:
            print(f"Warning: Outgoing letter {out_id} rendered empty prose! Skipping.")
            continue

        # Render incoming question(s)
        # Sort incoming letters by date
        sorted_entries = []
        for e in entries:
            inc_id = e["pair"]["incoming_id"]
            inc_letter = all_letters.get(inc_id)
            if not inc_letter:
                print(f"Warning: Incoming letter {inc_id} missing from all_letters!")
                continue
            inc_date = (
                inc_letter["metadata_audit"].get("xml_earliest")
                or e["pair"].get("incoming_date")
                or ""
            )
            sorted_entries.append((inc_date, inc_id, inc_letter, e))

        sorted_entries.sort(key=lambda x: (x[0], x[1]))

        question_texts = []
        questioner_names = set()
        question_ids = []

        for inc_date, inc_id, inc_letter, e in sorted_entries:
            inc_source_path = ROOT / inc_letter["source"]["path"]
            if inc_source_path.exists():
                rendered_inc = render_html(inc_source_path)
                q_text = clean_text(rendered_inc["content"])
            else:
                q_text = clean_text("\n\n".join(p["text"] for p in inc_letter.get("paragraphs", [])))
            if q_text:
                question_texts.append(q_text)
                question_ids.append(inc_id)
                q_name = person(inc_letter["metadata_audit"].get("sender_evidence", []))
                questioner_names.add(q_name)

        if not question_texts:
            print(f"Warning: No valid incoming questions for outgoing {out_id}! Skipping.")
            continue

        full_question_text = "\n\n".join(question_texts)
        q_name_str = " and ".join(sorted(questioner_names)) if questioner_names else "Correspondent"
        q_form = "letters" if len(question_texts) > 1 else "a letter"

        url = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{out_id}.xml#raft-response-{out_id}-{date}-section-0"

        transcript_data = {
            "participants": {
                "q": q_name_str,
                "a": "Charles Darwin"
            },
            "date": date,
            "url": url,
            "context": f"{q_form} from {q_name_str}, which you are answering",
            "exchanges": [
                [full_question_text, answer_text]
            ]
        }

        transcript_filename = f"transcript-{transcript_index:04d}.json"
        transcript_path = conv_dir / transcript_filename
        transcript_path.write_text(json.dumps(transcript_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        answer_hash = digest(answer_text.encode("utf-8"))
        darwin_answer_hashes.add(answer_hash)
        outgoing_ids_used.add(out_id)

        conversation_provenance.append({
            "transcript": transcript_filename,
            "outgoing_id": out_id,
            "incoming_ids": question_ids,
            "date": date,
            "questioner": q_name_str,
            "answer_sha256": answer_hash,
            "question_sha256": digest(full_question_text.encode("utf-8")),
            "pairs_represented": len(entries),
        })

        transcript_index += 1

    print(f"Written {len(conversation_provenance)} conversation transcripts to {conv_dir}.")

    # 4. Format grounding documents
    # Find all Darwin-authored letters in the post-origin period not in outgoing_ids_used
    grounding_docs = []
    grounding_candidates = []

    for sid, r in all_letters.items():
        meta = r.get("metadata_audit", {})
        if meta.get("direction") != "from_darwin":
            continue
        if sid in outgoing_ids_used:
            continue

        earliest = meta.get("xml_earliest")
        latest = meta.get("xml_latest")
        if not (earliest and earliest == latest and re.fullmatch(r"\d{4}-\d{2}-\d{2}", earliest)):
            continue
        if not (START_DATE <= earliest <= END_DATE):
            continue

        grounding_candidates.append((earliest, sid, r))

    grounding_candidates.sort(key=lambda x: (x[0], x[1]))

    grounding_content_hashes = set()
    grounding_provenance = []

    for doc_date, sid, r in grounding_candidates:
        source_path = ROOT / r["source"]["path"]
        if source_path.exists():
            rendered = render_html(source_path)
            content = clean_text(rendered["content"])
        else:
            content = clean_text("\n\n".join(p["text"] for p in r.get("paragraphs", [])))

        if not content:
            continue

        content_hash = digest(content.encode("utf-8"))
        # Must be strictly disjoint from conversation answers
        if content_hash in darwin_answer_hashes:
            print(f"Notice: Grounding letter {sid} text identical to a conversation answer; excluding from grounding.")
            continue
        if content_hash in grounding_content_hashes:
            # Duplicate text within grounding
            continue

        grounding_content_hashes.add(content_hash)

        recipient_name = person(r["metadata_audit"].get("recipient_evidence", []))
        title = f"To {recipient_name}, {doc_date} [{sid}; section 0]"
        link = f"https://www.darwinproject.ac.uk/letter/?docId=letters/{sid}.xml"

        doc = {
            "title": title,
            "link": link,
            "date": doc_date,
            "content": content
        }
        grounding_docs.append(doc)
        grounding_provenance.append({
            "source_id": sid,
            "date": doc_date,
            "title": title,
            "recipient": recipient_name,
            "content_sha256": content_hash
        })

    # Write corpus/documents.jsonl
    documents_path = corpus_dir / "documents.jsonl"
    with open(documents_path, "w", encoding="utf-8") as f:
        for doc in grounding_docs:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Written {len(grounding_docs)} grounding documents to {documents_path}.")

    # 5. Write raft.json manifest
    raft_manifest = {
        "format": "raft.project.v1",
        "name": "darwin_1",
        "collection": "darwin_1",
        "target": "Charles Darwin"
    }
    (DEST / "raft.json").write_text(json.dumps(raft_manifest, indent=2) + "\n", encoding="utf-8")

    # 6. Write README.md
    readme_content = f"""# darwin_1 prepared data (Post-Origin Run 02)

Validated cumulative export for the post-*Origin* interval: **{START_DATE} through {END_DATE}**.

- **{len(conversation_provenance)}** single-exchange transcripts in `conversations/transcript-0001.json` through `transcript-{len(conversation_provenance):04d}.json`.
  - Representing **{pair_count_in_window}** accepted direct reply pairs across **{len(outgoing_ids_used)}** distinct Darwin response letters.
- **{len(grounding_docs)}** dated Darwin grounding documents in `corpus/documents.jsonl`.
  - Authored exclusively by Charles Darwin, with verified exact single-day dates strictly within the post-origin research interval.
  - Fully disjoint from conversation answers: no target answer text appears in grounding documents.

## Schema & Standards
- Conforms to RAFT project format `raft.project.v1` (`raft.json`).
- Transcripts feature gapless 1-based numbering, normalized participants (`q`: Correspondent, `a`: Charles Darwin), letter-specific context, and clean authorial letter prose with editorial apparatus, footnotes, and annotations excluded.
- Formatted on {datetime.now(timezone.utc).strftime("%Y-%m-%d")}.
"""
    (DEST / "README.md").write_text(readme_content, encoding="utf-8")

    # 7. Write provenance records
    write(meta_dir / "conversation_provenance.json", conversation_provenance)
    write(meta_dir / "grounding_provenance.json", grounding_provenance)
    write(meta_dir / "outside_window_context_pairs.json", pairs_outside_window)

    print("darwin_1 project successfully created and populated!")
    return len(conversation_provenance), len(grounding_docs)


if __name__ == "__main__":
    build_darwin_1()

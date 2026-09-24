#!/usr/bin/env python3
"""Index correspondence language in preserved bodies, without asserting links."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LETTERS = ROOT / "reports/body-date-search-37-337/letters.jsonl"
OUT = ROOT / "reports/correspondence-map"
LITERAL = re.compile(r"\bletters?\b", re.I)
CUES = re.compile(
    r"\b(?:notes?|packets?|bundles?|yours|receiv\w*|acknowledg\w*|"
    r"answer\w*|repl(?:y|ied|ies|ying)|forward\w*|enclos\w*)\b|"
    r"\bheard\s+from\b|\bwrote\s+to\b", re.I)
FLAGS = {
    "receipt_or_reading_language": r"\b(?:receiv\w*|read|reading|heard\s+from|acknowledg\w*)\b",
    "reply_language": r"\b(?:answer\w*|repl(?:y|ied|ies|ying))\b",
    "forwarding_or_enclosure_language": r"\b(?:forward\w*|enclos\w*|transmit\w*)\b",
    "missing_unread_or_failed_delivery_language": r"\b(?:not|never|unopened|missing|lost|fear\w*|wish\w*|hope\w*)\b",
    "request_or_future_language": r"\b(?:will|shall|pray|please|beg|hope\w*|wish\w*)\b",
}


def references(letter):
    result = []
    for paragraph in letter["paragraphs"]:
        text = paragraph["text"]
        for kind, pattern in (("literal_letter", LITERAL), ("related_cue", CUES)):
            for match in pattern.finditer(text):
                low, high = max(0, match.start() - 180), min(len(text), match.end() + 240)
                context = text[low:high]
                result.append({
                    "id": f"{letter['id']}-p{paragraph['body_paragraph']}-c{match.start()}-{kind}",
                    "letter_id": letter["id"], "direction": letter["direction"],
                    "author_is_darwin_in_metadata": letter["direction"] == "from_darwin",
                    "original_date": letter["original_csv"]["date"],
                    "xml_date_bounds": letter["xml_date_bounds"],
                    "body_paragraph": paragraph["body_paragraph"], "locator": paragraph["locator"],
                    "char_start": match.start(), "char_end": match.end(),
                    "matched_text": match.group(), "match_kind": kind,
                    "context": context, "context_char_start": low,
                    "search_flags": [k for k, p in FLAGS.items() if re.search(p, context, re.I)],
                    "source": letter["source"],
                    "review_status": "candidate_only",
                    "automatic_link_or_date": False,
                })
    return result


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    letters = [json.loads(s) for s in LETTERS.read_text().splitlines()]
    for letter in letters:
        source = letter["source"]
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Source changed: {letter['id']}")
    hits = [hit for letter in letters for hit in references(letter)]
    literal = [h for h in hits if h["match_kind"] == "literal_letter"]
    write_jsonl(OUT / "letter_references.jsonl", hits)
    summary = {
        "scope": "All 286 preserved Darwin-involved bodies in numeric range 37–337, including suffix IDs.",
        "letters_searched": len(letters), "references": len(hits),
        "literal_letter_occurrences": len(literal),
        "letters_with_literal_letter": len({h["letter_id"] for h in literal}),
        "letters_with_any_cue": len({h["letter_id"] for h in hits}),
        "counts_by_kind": dict(Counter(h["match_kind"] for h in hits)),
        "literal_occurrences_by_direction": dict(Counter(h["direction"] for h in literal)),
        "headers_salutations_and_editorial_notes_excluded": True,
        "first_body_paragraph_retained": True,
        "source_hashes_verified": len(letters),
        "input": {"path": str(LETTERS.relative_to(ROOT)),
                  "sha256": hashlib.sha256(LETTERS.read_bytes()).hexdigest()},
        "limitations": [
            "Search flags describe nearby words, not who received a letter or whether receipt occurred.",
            "Past, future, negated, quoted, and third-party mentions remain candidates for review.",
            "Incoming authors' receipt claims do not establish Darwin's receipt of their letters.",
            "No keyword match automatically creates a knowledge date, prompt, or graph edge.",
        ],
    }
    (OUT / "search_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("letters_searched", "references", "literal_letter_occurrences", "letters_with_literal_letter")}))


if __name__ == "__main__":
    main()

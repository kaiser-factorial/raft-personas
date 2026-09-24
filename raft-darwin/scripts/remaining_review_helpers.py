"""Read complete remaining packets and validate reviewer coverage/evidence."""

import argparse
import json
import re
from collections import Counter

from build_expansion_review import check_quotes
from fetch_metadata import ROOT

BASE = ROOT / "reports/1837-1843/remaining-review"


def read(path):
    return json.loads(path.read_text())


def all_letters():
    letters = {r["id"]: r for r in map(json.loads, (BASE / "all_letters.jsonl").read_text().splitlines())}
    audit = {r["id"]: r for r in map(json.loads, (BASE.parent / "audit.jsonl").read_text().splitlines())}
    for ident, row in letters.items():
        row.setdefault("metadata_audit", audit[ident])
    return letters


def unavailable_transcription(body_text):
    """A catalogue paraphrase is source evidence, not transcribed letter prose.

    A bracketed entry containing an actual quotation remains an excerpt and
    requires explicit voice spans in the parent adjudication.
    """
    explicit = not body_text or bool(re.search(r"(?:no (?:transcript|transcription)|transcript(?:ion)? (?:is )?(?:not |un)available|not (?:yet )?available online)", body_text, re.I))
    paraphrase = bool(re.fullmatch(r"\[(?:Asks|Sends|Reports|Informs|Declines|Regrets|Requests|Thanks|Acknowledges|Returns)\b.*\]", body_text, re.I))
    has_quote = any(mark in body_text for mark in ('‘', '“', '"'))
    return explicit or (paraphrase and not has_quote)


def validate_review(path):
    report = read(path)
    packet = read(BASE / "packets" / (report["batch_id"] + ".json"))
    letters = all_letters()
    expected = packet["target_ids"] + packet["context_ids"]
    assert Counter(r["letter_id"] for r in report["record_reviews"]) == Counter(expected)
    for review in report["record_reviews"]:
        i = review["letter_id"]
        body_text = " ".join(p["text"] for p in letters[i]["paragraphs"])
        explicit_unavailable = unavailable_transcription(body_text)
        assert review["source_record_read_in_full"] is True, i
        if review["surviving_transcription_available"]:
            assert not explicit_unavailable, (i, "A placeholder or pure catalogue paraphrase is not a surviving letter transcription.")
            assert review["body_read_in_full"] is True, i
            assert review["paragraphs_read"] == [p["body_paragraph"] for p in letters[i]["paragraphs"]], i
        else:
            assert explicit_unavailable, (i, "Unavailable-body claim contradicts the surviving HTML transcription; XML metadata is not the body.")
            assert review["body_read_in_full"] is False, i
            assert review["paragraphs_read"] == [], i
        assert review["summary"] and review["date_assessment"] and review["attribution_assessment"], i
        assert all(re.fullmatch(r"DCP-LETT-[A-Za-z0-9]+", candidate)
                   and candidate in letters for candidate in review.get("proposed_prompt_ids", [])), (i, "Prompt IDs must be surviving record identifiers, not prose.")
        assert all(isinstance(candidate, dict) and len(candidate.get("assessment", "").strip()) > 3
                   for candidate in review.get("alternative_candidates_considered", [])), (i, "Candidate assessments must be complete comparisons, not characters.")
    quotes = check_quotes(report, letters)
    return {"batch_id": report["batch_id"], "target_records": len(packet["target_ids"]),
            "context_records": len(packet["context_ids"]), "exact_quote_checks": len(quotes),
            "coverage_valid": True, "proposed_links": len(report["proposed_links"]),
            "warning": "Coverage and exact quotations do not by themselves validate a relationship; parent adjudication is required."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", type=str)
    parser.add_argument("--batch", type=str)
    parser.add_argument("--ids", nargs="*")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate_review(ROOT / args.validate), ensure_ascii=False))
        return
    letters = all_letters()
    if args.ids:
        ids = [i if i.startswith("DCP-LETT-") else "DCP-LETT-" + i for i in args.ids]
    else:
        packet = read(BASE / "packets" / (args.batch + ".json"))
        ids = [r["id"] for r in packet["letters"]][args.offset:args.offset + args.limit]
    for i in ids:
        row = letters[i]
        a = row["metadata_audit"]
        print("\nLETTER", i, row["title"])
        print("HEADER", " | ".join(row["header_text"]))
        print("DATE", json.dumps({k: a[k] for k in ("classification", "direction", "xml_earliest", "xml_latest", "date_structure", "exact_order_needs_review", "metadata_multiple_senders")}, ensure_ascii=False))
        print("ORIGINAL DATE", a["original_csv"]["date"])
        print("PARTICIPANTS", json.dumps({k: a[k] for k in ("sender_evidence", "recipient_evidence")}, ensure_ascii=False))
        for p in row["paragraphs"]:
            print(f"P{p['body_paragraph']}: {p['text']}")
        print("EXCLUDED ANNOTATIONS/SALUTATIONS", json.dumps(row["excluded_body_annotations_and_salutations"], ensure_ascii=False))
        print("SUMMARY", row["editorial_summary"])
        print("EDITORIAL NOTES", row["editorial_footnotes"])


if __name__ == "__main__":
    main()

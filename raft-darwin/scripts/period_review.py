"""Read whole sources and validate bounded first passes for new periods.

These checks establish structural coverage and exact quotation provenance only.
Historical acceptance requires the primary agent's separate full-source reading.
"""
import argparse
import json
import re
from collections import Counter
from functools import lru_cache

from lxml import html

from build_expansion_review import check_quotes as check_legacy_quotes
from fetch_metadata import ROOT
from prepare_period import PERIODS, digest, read, rows, write
from remaining_review_helpers import unavailable_transcription
from search_body_dates import normalized


@lru_cache(maxsize=128)
def scholarly_sections(source_path, source_sha256):
    """Read preserved marginalia/back matter without changing frozen body text."""
    path = ROOT / source_path
    if not path.exists():
        return []
    assert digest(path) == source_sha256, "Changed preserved HTML"
    doc = html.fromstring(path.read_bytes())
    result = []
    for node in doc.xpath('//div[@id="letter"]/*'):
        classes = set(node.get("class", "").split())
        if classes & {"body", "footnotes"} or node.get("id") == "bibliography":
            continue
        if node.tag in ("script", "style"):
            continue
        text = normalized(node.text_content())
        if text:
            result.append({"section_class": node.get("class", ""),
                           "locator": node.getroottree().getpath(node), "text": text})
    return result


@lru_cache(maxsize=128)
def visual_nodes(source_path, source_sha256):
    """Expose letter visuals that are absent from paragraph text."""
    path = ROOT / source_path
    if not path.exists():
        return []
    assert digest(path) == source_sha256, 'Changed preserved HTML'
    doc = html.fromstring(path.read_bytes())
    return [{'dom_locator': node.getroottree().getpath(node), 'tag': node.tag,
             'src': node.get('src') or node.get('data') or node.get('href'),
             'alt': node.get('alt')}
            for node in doc.xpath('//div[@id="letter"]//img | //div[@id="letter"]//svg | //div[@id="letter"]//object | //div[@id="letter"]//embed')]


@lru_cache(maxsize=128)
def bibliography_sections(source_path, source_sha256):
    """Expose editorial references without treating them as historical reading."""
    path = ROOT / source_path
    if not path.exists():
        return []
    assert digest(path) == source_sha256, 'Changed preserved HTML'
    doc = html.fromstring(path.read_bytes())
    return [{'locator': node.getroottree().getpath(node),
             'text': normalized(node.text_content())}
            for node in doc.xpath('//div[@id="letter"]//*[@id="bibliography"]')]


def validate_visual_readings(ident, source, readings):
    """Check explicit visual reading records against preserved source and asset.

    Hash checks cannot themselves establish that someone read the image.
    """
    covered = []
    for node in visual_nodes(source['path'], source['sha256']):
        matches = [r for r in readings if r['letter_id'] == ident
                   and r['dom_locator'] == node['dom_locator']]
        assert matches, ident + ': missing primary visual reading'
        for record in matches:
            assert record['source_path'] == source['path']
            assert record['source_html_sha256'] == source['sha256']
            assert record.get('visual_observation'), 'Visual reading needs a specific observation'
            assert digest(ROOT / record['figure_path']) == record['sha256'], 'Figure hash mismatch'
        covered.append(node['dom_locator'])
    return covered


def check_quotes(value, letters):
    """Legacy locators plus separately attributed scholarly sibling sections."""
    checks = []
    if isinstance(value, dict):
        if "letter_id" in value and "quote" in value:
            if "scholarly_section" in value:
                row = letters[value["letter_id"]]
                sections = scholarly_sections(row["source"]["path"], row["source"]["sha256"])
                section = next(s for s in sections if s["locator"] == value["scholarly_section"])
                assert value["quote"] in section["text"], "Quote absent from scholarly section"
                checks.append({"letter_id": value["letter_id"], "locator": section["locator"], "exact_quote_verified": True})
            else:
                # Pass just the quote object; recurse through nested data below.
                checks.extend(check_legacy_quotes({k: v for k, v in value.items() if not isinstance(v, (dict, list))}, letters))
        for child in value.values():
            checks.extend(check_quotes(child, letters))
    elif isinstance(value, list):
        for child in value:
            checks.extend(check_quotes(child, letters))
    return checks


def body_unavailable(text):
    synopsis = re.fullmatch(r"\[(?:Discusses|Describes|Offers|Suggests|Invites|Recommends|Encloses|Refers|Writes|Expresses|Mentions|Wishes|Agrees|Accepts)\b.*\]", text, re.I)
    return unavailable_transcription(text) or bool(synopsis and not any(mark in text for mark in ('‘', '“', '"')))


@lru_cache(maxsize=16)
def load(period):
    path = ROOT / "reports" / period / "review/all_letters.jsonl"
    if path.exists():
        return {r["id"]: r for r in rows(path)}
    db_path = ROOT / "data/letters.sqlite"
    if db_path.exists():
        import sqlite3
        import zlib
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, record_blob FROM letters WHERE periods_json LIKE ?", (f'%"{period}"%',))
        result = {}
        for lid, blob in cur.fetchall():
            result[lid] = json.loads(zlib.decompress(blob).decode("utf-8"))
        conn.close()
        if result:
            return result
    raise FileNotFoundError(f"Neither {path} nor {db_path} could supply letters for period {period}")


def compact_constraints(constraints, mutually_exclusive):
    """Lossless date-set rendering for huge mutually exclusive XML enumerations."""
    days = sorted(c["lower"] for c in constraints if c["lower"] == c["upper"] and c["lower"])
    if mutually_exclusive and len(days) == len(constraints) and len(days) > 12:
        first, last = days[0], days[-1]
        months = range(int(first[:4]) * 12 + int(first[5:7]) - 1,
                       int(last[:4]) * 12 + int(last[5:7]))
        expected = [f"{m // 12:04d}-{m % 12 + 1:02d}-{first[8:]}" for m in months]
        if days == expected:
            return {"equivalent_verified_date_set": "one mutually exclusive alternative on the stated day of every calendar month", "day_of_month": int(first[8:]), "first": first, "last": last, "count": len(days), "every_enumerated_XML_bound_compared": True}
        expected = [f"{year:04d}-{first[5:]}" for year in range(int(first[:4]), int(last[:4]) + 1)]
        if days == expected:
            return {"equivalent_verified_date_set": "one mutually exclusive alternative on the stated month/day of every year", "month_day": first[5:], "first": first, "last": last, "count": len(days), "every_enumerated_XML_bound_compared": True}
    return [{"text": c["text"], "lower": c["lower"], "upper": c["upper"],
             "attributes": {k: v for k, v in c["attributes"].items() if k != "exclude" or not mutually_exclusive}} for c in constraints]


def print_letter(row):
    a = row["metadata_audit"]
    print("\nLETTER", row["id"], row["title"])
    print("SOURCE", json.dumps(row["source"], ensure_ascii=False))
    print("HEADER", " | ".join(row["header_text"]))
    print("DATE", json.dumps({k: a[k] for k in ("classification", "direction", "xml_earliest", "xml_latest", "date_structure", "exact_order_needs_review")}, ensure_ascii=False))
    print("ORIGINAL DATE", a["original_csv"]["date"])
    constraints = a["sent_date_constraints"]
    xml_id = "{http://www.w3.org/XML/1998/namespace}id"
    ids = {c["attributes"].get(xml_id) for c in constraints}
    mutually_exclusive = bool(ids) and None not in ids and all(
        set(c["attributes"].get("exclude", "").replace("#", "").split()) == ids - {c["attributes"].get(xml_id)}
        for c in constraints)
    compact = compact_constraints(constraints, mutually_exclusive)
    print("XML DATE CONSTRAINTS", json.dumps({"all_alternatives_mutually_exclusive": mutually_exclusive, "constraints": compact}, ensure_ascii=False))
    print("PARTICIPANTS", json.dumps({k: a[k] for k in ("sender_evidence", "recipient_evidence")}, ensure_ascii=False))
    print("XML PHYSICAL/DESCRIPTIVE NOTES", json.dumps(a.get("xml_notes", []), ensure_ascii=False))
    for p in row["paragraphs"]:
        print(f"P{p['body_paragraph']}: {p['text']}")
    print("EXCLUDED ANNOTATIONS/SALUTATIONS", json.dumps(row["excluded_body_annotations_and_salutations"], ensure_ascii=False))
    print("SUMMARY", row["editorial_summary"])
    print("EDITORIAL NOTES", row["editorial_footnotes"])
    for section in bibliography_sections(row['source']['path'], row['source']['sha256']):
        print('EDITORIAL BIBLIOGRAPHY; NOT EVIDENCE OF CONTEMPORARY READING', json.dumps(section, ensure_ascii=False))
    for section in scholarly_sections(row["source"]["path"], row["source"]["sha256"]):
        print("SEPARATE SCHOLARLY SECTION; DATE/AUTHORSHIP NOT INHERITED", json.dumps(section, ensure_ascii=False))
    for visual in visual_nodes(row['source']['path'], row['source']['sha256']):
        print('VISUAL REQUIRES SEPARATE INSPECTION; ALT IS NOT ITS FULL CONTENT', json.dumps(visual, ensure_ascii=False))


def validate_review(period, path):
    report = read(path)
    base = ROOT / "reports" / period / "review"
    packet_path = base / "packets" / (report["batch_id"] + ".json")
    packet = read(packet_path)
    manifest = read(base / "manifest.json")
    entry = next(p for p in manifest["packets"] if p["batch_id"] == report["batch_id"])
    assert digest(packet_path) == entry["sha256"], "Reading packet changed"
    letters = load(period)
    expected = packet["target_ids"] + packet["context_ids"]
    assert Counter(r["letter_id"] for r in report["record_reviews"]) == Counter(expected), "Target/context coverage mismatch"
    extra = report.get("additional_record_reviews", [])
    assert not (set(expected) & {r["letter_id"] for r in extra}), "Additional reading duplicates packet coverage"
    assert len({r["letter_id"] for r in extra}) == len(extra)
    for review in report["record_reviews"] + extra:
        ident = review["letter_id"]
        row = letters[ident]
        if digest(ROOT / row["source"]["path"]) != row["source"]["sha256"]:
            raise ValueError(f"Changed source: {ident}")
        body = " ".join(p["text"] for p in row["paragraphs"])
        unavailable = body_unavailable(body)
        assert review["source_record_read_in_full"] is True, ident
        assert review["surviving_transcription_available"] is (not unavailable), (ident, "Inspect preserved HTML; metadata XML is not a transcription. Flag exceptional source kinds for primary adjudication.")
        assert review["body_read_in_full"] is (not unavailable), ident
        expected_paragraphs = [] if unavailable else [p["body_paragraph"] for p in row["paragraphs"]]
        assert review["paragraphs_read"] == expected_paragraphs, ident
        for field in ("summary", "date_assessment", "attribution_assessment", "source_kind"):
            assert isinstance(review[field], str) and review[field].strip(), (ident, field)
        assert all(re.fullmatch(r"DCP-LETT-\d+[A-Z]*", candidate) and candidate in letters for candidate in review.get("proposed_prompt_ids", [])), ident
        assert all(isinstance(c, dict) and c.get("id") and len(c.get("assessment", "").strip()) > 3 for c in review.get("alternative_candidates_considered", [])), ident
        if row["metadata_audit"]["direction"] == "from_darwin" and not review.get("proposed_prompt_ids"):
            assert review.get("unmatched_reason", "").strip(), ident
    reviewed = set(expected) | {r["letter_id"] for r in extra}
    for link in report["proposed_links"]:
        assert link["source_id"] in reviewed and link["target_id"] in reviewed, "Proposed source/witness must both be fully read and recorded"
        assert link["relationship"] in ("replies_to", "knowledge_before", "references_own_letter", "receipt_unread", "event_knowledge_only")
        assert link["status"] in ("supported", "candidate_only", "rejected")
        assert link.get("reason") and link.get("evidence"), "Each proposal needs a reason and source evidence"
    quotes = check_quotes(report, letters)
    return {"batch_id": report["batch_id"], "target_records": len(packet["target_ids"]),
            "context_records": len(packet["context_ids"]), "additional_records": len(extra),
            "exact_quote_checks": len(quotes), "coverage_valid": True,
            "proposed_links": len(report["proposed_links"]),
            "limitation": "Coverage and exact quotations do not establish historical identification or replace primary adjudication."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", choices=PERIODS, required=True)
    parser.add_argument("--validate")
    parser.add_argument("--batch")
    parser.add_argument("--ids", nargs="+")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()
    if args.validate:
        print(json.dumps(validate_review(args.period, ROOT / args.validate), ensure_ascii=False))
        return
    letters = load(args.period)
    if args.ids:
        ids = [i if i.startswith("DCP-LETT-") else "DCP-LETT-" + i for i in args.ids]
    else:
        packet = read(ROOT / "reports" / args.period / "review/packets" / (args.batch + ".json"))
        ids = [r["id"] for r in packet["letters"]][args.offset:args.offset + args.limit]
    for ident in ids:
        print_letter(letters[ident])


if __name__ == "__main__":
    main()

"""Offline audit of Darwin-only correspondence against preserved TEI dates.

Uses the correspondence action dates, never the edition publication date.
Does not infer receipt dates, match replies, or turn metadata into letter text.
"""

import calendar
import csv
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path

from fetch_metadata import END, RAW, REVISION, ROOT, START, is_darwin

NS = {"tei": "http://www.tei-c.org/ns/1.0"}
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
OUT = ROOT / "reports" / "1828-1836"
DARWIN_KEY = "nameregs_1.xml"


def element_text(element):
    return "".join(element.itertext()).strip() if element is not None else ""


def date_bounds(value):
    """Expand ISO year/month precision without manufacturing an exact day."""
    if re.fullmatch(r"\d{4}", value):
        return date(int(value), 1, 1), date(int(value), 12, 31)
    if re.fullmatch(r"\d{4}-\d{2}", value):
        year, month = map(int, value.split("-"))
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        day = date.fromisoformat(value)
        return day, day
    raise ValueError(f"Unsupported date value: {value!r}")


def temporal_constraint(element):
    attributes = dict(element.attrib)
    supported = {"when", "notBefore", "notAfter", "from", "to", "exclude", XML_ID}
    if set(attributes) - supported:
        raise ValueError(f"Unreviewed date attributes: {set(attributes) - supported}")
    if "when" in attributes:
        if set(attributes) & {"notBefore", "notAfter", "from", "to"}:
            raise ValueError("Conflicting exact date and bound attributes")
        lower, upper = date_bounds(attributes["when"])
    else:
        if "notBefore" in attributes and "from" in attributes:
            raise ValueError("Multiple lower-bound specifications")
        if "notAfter" in attributes and "to" in attributes:
            raise ValueError("Multiple upper-bound specifications")
        low = attributes.get("notBefore", attributes.get("from"))
        high = attributes.get("notAfter", attributes.get("to"))
        if not low and not high:
            raise ValueError("Date element has no machine-readable date constraint")
        lower = date_bounds(low)[0] if low else None
        upper = date_bounds(high)[1] if high else None
    if lower and upper and lower > upper:
        raise ValueError("Reversed date interval")
    return {
        "text": element_text(element),
        "attributes": attributes,
        "lower": lower.isoformat() if lower else None,
        "upper": upper.isoformat() if upper else None,
        "xml_fragment": ET.tostring(element, encoding="unicode").strip(),
    }


def classify_period(constraints, start=START, end=END):
    """All possible dates must fit; retain disjoint alternatives separately."""
    if not constraints:
        return "needs_review", "No parsed correspondence date constraints."
    if all(c["lower"] and c["upper"] and start <= c["lower"] <= c["upper"] <= end for c in constraints):
        return "safe_within_period", "Every XML-encoded date or bound lies inside the inclusive period."
    if all(c["upper"] and c["upper"] < start for c in constraints):
        return "outside_period_before", "Every XML date possibility precedes the period."
    if all(c["lower"] and c["lower"] > end for c in constraints):
        return "outside_period_later", "Every XML date possibility follows the period."
    if all((c["upper"] and c["upper"] < start) or (c["lower"] and c["lower"] > end) for c in constraints):
        return "outside_period_disjoint", "All alternative dates are outside the period; the outer envelope would be misleading."
    return "ambiguous_period", "At least one XML date possibility crosses a period boundary or lacks a limiting bound."


def source_flags(display):
    flags = []
    for name, pattern in [
        ("editorially_supplied_component", r"\["),
        ("questioned_component", r"\?"),
        ("circa", r"\bc\."),
        ("before", r"\bbefore\b"),
        ("after", r"\bafter\b"),
    ]:
        if re.search(pattern, display, re.I):
            flags.append(name)
    return flags


def read_csv_records(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames
        previous_line = reader.line_num
        result = []
        for number, row in enumerate(reader, 1):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV record {number}")
            result.append((number, previous_line + 1, reader.line_num, row))
            previous_line = reader.line_num
    return headers, result


def participant_evidence(action):
    people = action.findall("tei:persName", NS) + action.findall("tei:orgName", NS)
    return [{"text": element_text(p), "attributes": dict(p.attrib)} for p in people]


def action_is_darwin(action):
    return any(p.get("key", "").split("/")[-1] == DARWIN_KEY for p in action.findall("tei:persName", NS))


def audit_record(row_info, source_index, *, raw_root=RAW, start=START, end=END):
    number, line_start, line_end, row = row_info
    path = raw_root / "letters" / row[" filename"]
    relative = str(path.relative_to(ROOT))
    tree = ET.fromstring(path.read_bytes())
    if tree.get(XML_ID) != row["id"]:
        raise ValueError(f"XML identity differs from CSV: {row['id']}")
    actions = tree.findall("tei:teiHeader/tei:profileDesc/tei:correspDesc/tei:correspAction", NS)
    sent = [a for a in actions if a.get("type") == "sent"]
    received = [a for a in actions if a.get("type") == "received"]
    notes = tree.findall("tei:teiHeader/tei:fileDesc/tei:notesStmt/tei:note", NS)
    # The catalogue also contains explicitly described, unaddressed memoranda.
    # Preserve their author/date evidence without inventing a recipient or reply.
    memorandum = (
        len(actions) == len(sent) == 1 and not received
        and action_is_darwin(sent[0])
        and len(participant_evidence(sent[0])) == 1
        and not row["recipient_surname"] and not row["recipient_forename"]
        and any((n.get("type") == "description" and element_text(n).lower() == "mem")
                or (n.get("type") == "physdesc" and n.get("n") == "mem") for n in notes)
    )
    if len(sent) != 1 or (len(received) != 1 and not memorandum):
        raise ValueError(f"Unexpected correspondence topology: {row['id']}")
    # The authority key identifies Charles Robert Darwin within each action.
    # Other authors' aliases cannot reconcile a disagreement about his involvement.
    xml_from = action_is_darwin(sent[0])
    xml_to = bool(received) and action_is_darwin(received[0])
    if (xml_from, xml_to) != (is_darwin(row, "sender"), is_darwin(row, "recipient")):
        raise ValueError(f"CSV/XML Darwin identity mismatch: {row['id']}")
    if not (xml_from or xml_to):
        raise ValueError(f"Third-party correspondence selected: {row['id']}")
    for action in actions:
        for person in action.findall("tei:persName", NS):
            if person.get("key", "").split("/")[-1] == DARWIN_KEY and (person.get("exclude") or person.get("cert")):
                raise ValueError(f"Uncertain Darwin identity requires review: {row['id']}")
    elements = sent[0].findall("tei:date", NS)
    constraints = [temporal_constraint(d) for d in elements]
    classification, reason = classify_period(constraints, start=start, end=end)
    lower = min(c["lower"] for c in constraints) if constraints and all(c["lower"] for c in constraints) else None
    upper = max(c["upper"] for c in constraints) if constraints and all(c["upper"] for c in constraints) else None
    if len(elements) > 1:
        kind = "alternative_dates" if any(d.get("exclude") for d in elements) else "multiple_recorded_dates"
    elif constraints and constraints[0]["lower"] == constraints[0]["upper"]:
        kind = "single_xml_day"
    else:
        kind = "bounded_range" if lower and upper else "open_range"
    flags = source_flags(row["date"])
    qualified = bool(set(flags) - {"editorially_supplied_component"})
    direction = "from_darwin" if xml_from else "to_darwin"
    in_period = classification == "safe_within_period"
    ptr = tree.find("tei:teiHeader/tei:fileDesc/tei:publicationStmt/tei:ptr[@type='projectItem']", NS)
    body = tree.find("tei:text/tei:body", NS)
    result = {
        "id": row["id"],
        "classification": classification,
        "classification_reason": reason,
        "direction": direction,
        "period_selection_eligible": in_period,
        "xml_earliest": lower,
        "xml_latest": upper,
        "date_structure": kind,
        "source_date_flags": flags,
        "single_xml_day_without_textual_qualifier": kind == "single_xml_day" and not qualified,
        "exact_order_needs_review": kind != "single_xml_day" or qualified,
        "sorting_date_differs_from_xml_earliest": row["sorting_date"] != lower,
        "sent_date_constraints": constraints,
        "received_date_constraints": [temporal_constraint(d) for a in received for d in a.findall("tei:date", NS)],
        "sender_evidence": participant_evidence(sent[0]),
        "recipient_evidence": participant_evidence(received[0]) if received else [],
        "xml_sender_address": [element_text(p) for p in sent[0].findall("tei:placeName", NS)],
        "xml_notes": [{"text": element_text(n), "attributes": dict(n.attrib)} for n in notes],
        "has_transcription_in_preserved_xml": bool(element_text(body)),
        "reply_link_status": "not_audited",
        "training_target_eligible": False,
        "prospective_role": (
            "hold_for_date_review" if not in_period else
            "dated_grounding_unless_inbound_reply_link_is_established" if xml_from else
            "incoming_context_pending_receipt_and_reply_evidence"
        ),
        "known_by_date": None,
        "original_csv": row,
        "provenance": {
            "revision": REVISION,
            "csv_path": str((RAW / "darwin-correspondence.csv").relative_to(ROOT)),
            "csv_record_number": number,
            "csv_physical_line_start": line_start,
            "csv_physical_line_end": line_end,
            "xml_path": relative,
            "xml_sha256": source_index[relative]["sha256"],
            "xml_url": source_index[relative]["url"],
            "letter_page_url": ptr.get("target") if ptr is not None else None,
            "date_xpath": "/tei:TEI/tei:teiHeader/tei:profileDesc/tei:correspDesc/tei:correspAction[@type='sent']/tei:date",
        },
    }
    if memorandum:
        result.update(
            correspondence_topology="author_only_memorandum",
            conversation_pairing_eligible=False,
            source_kind_review_required=True,
            prospective_role="authored_memorandum_pending_voice_and_date_review",
        )
    return result


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")


def main():
    manifest = json.loads((RAW / "manifest.json").read_text())
    sources = {f["path"]: f for f in manifest["files"]}
    for relative, source in sources.items():
        if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Source checksum mismatch: {relative}")
    headers, all_rows = read_csv_records(RAW / "darwin-correspondence.csv")
    ids = [r[3]["id"] for r in all_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source identifiers")
    candidates, excluded_third_party, supplemental = [], [], []
    for info in all_rows:
        row = info[3]
        in_csv_period = START <= row["sorting_date"] <= END
        direct = is_darwin(row, "sender") or is_darwin(row, "recipient")
        if in_csv_period and not direct:
            excluded_third_party.append(row["id"])
        if not direct:
            continue
        explicit_overlap = any(1828 <= int(y) <= 1836 for y in re.findall(r"(?<!\d)\d{4}(?!\d)", row["date"]))
        if in_csv_period or explicit_overlap:
            candidates.append(info)
            if not in_csv_period:
                supplemental.append(row["id"])
    audited = [audit_record(info, sources) for info in candidates]
    audited.sort(key=lambda r: (r["original_csv"]["sorting_date"], r["id"]))
    expected = {r["id"] + ".xml" for r in audited}
    actual = {p.name for p in (RAW / "letters").glob("*.xml")}
    if expected != actual:
        raise ValueError("Downloaded XML set does not match the selected candidates")
    safe = [r for r in audited if r["classification"] == "safe_within_period"]
    held = [r for r in audited if r["classification"] != "safe_within_period"]
    assert len(safe) + len(held) == len(audited)
    counts = Counter(r["classification"] for r in audited)
    directions = {
        status: dict(Counter(r["direction"] for r in audited if r["classification"] == status))
        for status in sorted(counts)
    }
    summary = {
        "period": {"start": START, "end": END, "inclusive": True},
        "revision": REVISION,
        "source_rows": len(all_rows),
        "source_csv_sha256": sources[str((RAW / "darwin-correspondence.csv").relative_to(ROOT))]["sha256"],
        "candidates": len(audited),
        "classification_counts": dict(counts),
        "classification_by_direction": directions,
        "third_party_records_excluded_by_csv_filter": len(excluded_third_party),
        "third_party_xml_downloaded": 0,
        "supplemental_records_with_explicit_period_year_outside_sort_window": supplemental,
        "date_structure_counts": dict(Counter(r["date_structure"] for r in audited)),
        "safe_records_requiring_order_review": sum(r["exact_order_needs_review"] for r in safe),
        "source_qualified_dates": [r["id"] for r in audited if set(r["source_date_flags"]) - {"editorially_supplied_component"}],
        "csv_xml_sort_mismatches": [r["id"] for r in audited if r["sorting_date_differs_from_xml_earliest"]],
        "records_with_transcriptions_in_xml": sum(r["has_transcription_in_preserved_xml"] for r in audited),
        "records_with_structured_receipt_dates": sum(bool(r["received_date_constraints"]) for r in audited),
        "sources_checksum_verified": len(sources),
        "scope_limit": "Audits the CSV-selected 1828-1836 set plus any other Darwin-only CSV row explicitly mentioning a year in that period. It is not an XML-wide re-dating of all 15,238 records or a completeness claim for all surviving letters.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for filename, records in [("audit.jsonl", audited), ("safe_within_period.jsonl", safe), ("ambiguous_or_later.jsonl", held)]:
        write_jsonl(OUT / filename, records)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    audit_fields = ["classification", "direction", "xml_earliest", "xml_latest", "date_structure", "exact_order_needs_review", "source_date_flags", "prospective_role", "xml_path", "xml_sha256", "xml_url", "letter_page_url"]
    with (OUT / "audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers + audit_fields)
        writer.writeheader()
        for r in audited:
            extra = {k: r[k] for k in audit_fields if k in r}
            extra["source_date_flags"] = "; ".join(r["source_date_flags"])
            extra.update({k: r["provenance"][k] for k in audit_fields if k in r["provenance"]})
            writer.writerow({**r["original_csv"], **extra})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

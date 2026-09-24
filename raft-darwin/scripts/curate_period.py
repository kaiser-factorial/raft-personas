"""Validate and package explicit primary adjudications for a research period.

No reviewer proposal is accepted automatically. Full primary readings and
handwritten decisions are prerequisites. Earlier ledgers and evidence stay intact.
"""
import argparse
import json
from collections import Counter

from fetch_metadata import ROOT
from period_review import bibliography_sections, check_quotes, load, scholarly_sections, validate_review, validate_visual_readings
from prepare_period import PERIODS, digest, read, write


LIST_FIELDS = (
    "direct_reply_pairs", "cross_correspondent_knowledge", "correspondent_replies",
    "dated_sections", "reference_observations", "receipt_events", "within_day_events",
    "additional_exact_date_review_ids", "additional_period_hold_ids", "voice_held_ids",
    "rejected_or_candidate_links", "date_evidence", "corrections", "unlocated_references",
    "previously_recorded_relationships",
)


def relationship_keys(decisions):
    for link in decisions.get("direct_reply_pairs", []):
        yield (link["outgoing_id"], link["incoming_id"], "replies_to")
    for link in decisions.get("correspondent_replies", []):
        yield (link["response_id"], link["antecedent_id"], "replies_to")
    for link in decisions.get("cross_correspondent_knowledge", []):
        yield (link["incoming_id"], link["witness_id"], "knowledge_before")


def curate(period, batch):
    base = ROOT / "reports" / period / "review"
    paths = [base / folder / f"{batch}.json" for folder in
             ("packets", "parent-reading", "parent-decisions", "reviews")]
    packet, notes, decisions, review = map(read, paths)
    assert notes["status"] == "parent_full_source_read_complete"
    assert decisions["status"] == "parent_adjudicated"
    assert decisions["batch_id"] == notes["batch_id"] == packet["batch_id"] == batch
    letters = load(period)
    packet_ids = packet["target_ids"] + packet["context_ids"]
    source_read = set(notes["source_record_ids_read"])
    body_read = set(notes["body_ids_read"])
    unavailable = set(decisions.get("body_unavailable_ids", []))
    assert set(packet_ids) <= source_read <= set(letters)
    assert unavailable <= source_read
    assert body_read == source_read - unavailable
    assert source_read == set(notes["record_notes"])
    for ident in source_read:
        r = letters[ident]
        assert digest(ROOT / r["source"]["path"]) == r["source"]["sha256"], ident
        p = r["metadata_audit"]["provenance"]
        assert digest(ROOT / p["xml_path"]) == p["xml_sha256"], ident
        if scholarly_sections(r["source"]["path"], r["source"]["sha256"]):
            assert ident in notes.get("supplemental_sections_read_ids", []), "Primary must inspect marginalia and separate CD notes: " + ident
        if bibliography_sections(r['source']['path'], r['source']['sha256']):
            assert ident in notes.get('bibliography_sections_read_ids', []), 'Primary must inspect editorial bibliography separately: ' + ident
        validate_visual_readings(ident, r['source'], notes.get('visual_readings', []))
    review_checks = validate_review(period, paths[-1])
    key = lambda row: (row["source_id"], row["target_id"], row["relationship"])
    assert Counter(map(key, review["proposed_links"])) == Counter(map(key, decisions["proposal_adjudications"]))
    assert Counter(r["letter_id"] for r in decisions["record_dispositions"]) == Counter(packet["target_ids"])
    accepted_keys = set(relationship_keys(decisions))
    for item in decisions["proposal_adjudications"]:
        assert item.get("reason") and item.get("parent_decision")
        if item["parent_decision"].startswith("accepted_"):
            assert key(item) in accepted_keys, "Accepted proposal missing from the final graph"
    for first, second, relationship in accepted_keys:
        assert {first, second} <= body_read, "Both accepted endpoints require primary full-body reading"
        if relationship == "replies_to":
            for endpoint in (first, second):
                assert letters[endpoint]["metadata_audit"].get("conversation_pairing_eligible", True), "Unaddressed memorandum cannot be a correspondence pair"
    for pair in decisions.get("direct_reply_pairs", []):
        assert letters[pair["outgoing_id"]]["metadata_audit"]["direction"] == "from_darwin"
        assert letters[pair["incoming_id"]]["metadata_audit"]["direction"] == "to_darwin"
        assert pair.get("rationale") and pair.get("evidence") and pair.get("response_scope")
        assert "known_by_date" in pair and "actual_receipt_date" in pair
        assert pair.get("training_export_ready") is False
        assert pair.get("response_date_policy"), "Preserve uncertain dates rather than selecting a day"
    for field in ("correspondent_replies", "cross_correspondent_knowledge"):
        for link in decisions.get(field, []):
            assert link.get("rationale") and link.get("evidence")
    source_refs = []
    for ident in sorted(source_read):
        r = letters[ident]
        a = r["metadata_audit"]
        source_refs.append({"letter_id": ident, "body_source": r["source"],
                            "metadata_provenance": a["provenance"]})
    ledger = {
        "schema_version": 2, "period": period, "batch_id": batch,
        "status": "parent_adjudicated", "review_lane": packet["review_lane"],
        "method": "Luna first pass, independent primary full-source reading, then explicit primary adjudication; structural checks do not establish historical truth.",
        "reviewed_record_ids": packet["target_ids"],
        "full_read_ids": [i for i in packet["target_ids"] if i in body_read],
        "body_unavailable_ids": [i for i in packet["target_ids"] if i in unavailable],
        "review_context_read_ids": packet["context_ids"],
        "additional_parent_read_ids": sorted(source_read - set(packet_ids)),
        "letter_adjudications": [], "proposal_adjudications": decisions["proposal_adjudications"],
        "review_validation": review_checks, "training_export_performed": False,
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in paths + sorted(set((base / "reviews").glob(f"{batch}.initial*.json")) | set((base / "reviews").glob(f"{batch}.revision-*.json")))],
        "sources": source_refs,
    }
    for field in LIST_FIELDS:
        ledger[field] = decisions.get(field, [])
    for disposition in decisions["record_dispositions"]:
        ident = disposition["letter_id"]
        r = letters[ident]
        assert disposition.get("disposition") and disposition.get("source_kind")
        assert disposition.get("voice") and disposition.get("date_assessment")
        ledger["letter_adjudications"].append({
            **disposition, "parent_source_record_read": True,
            "parent_body_read_in_full": ident in body_read,
            "paragraphs_read": [p["body_paragraph"] for p in r["paragraphs"]] if ident in body_read else [],
            "reason": notes["record_notes"][ident],
            "original_date_label": r["metadata_audit"]["original_csv"]["date"],
            "raw_period_classification": r["metadata_audit"]["classification"],
            "source": r["source"],
        })
    ledger["parent_exact_quote_checks"] = len(check_quotes(ledger, letters))
    dest = ROOT / "data/annotations/periods" / period / f"{batch}.json"
    if dest.exists():
        assert read(dest) == ledger, "Preserve accepted ledger; record changes in an explicit addendum"
    else:
        write(dest, ledger)
    status = read(base / "work_status.json")
    for row in status["packets"]:
        if row["batch_id"] == batch:
            row.update(review_status="full_read_complete", parent_status="adjudicated",
                       ledger=str(dest.relative_to(ROOT)))
    write(base / "work_status.json", status)
    return {"period": period, "batch": batch, "target_count": len(packet["target_ids"]),
            "direct_links": len(ledger["direct_reply_pairs"]),
            "reverse_links": len(ledger["correspondent_replies"]),
            "knowledge_links": len(ledger["cross_correspondent_knowledge"]),
            "parent_quote_checks": ledger["parent_exact_quote_checks"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", choices=PERIODS, required=True)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    print(json.dumps(curate(args.period, args.batch)))

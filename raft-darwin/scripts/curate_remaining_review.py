"""Package explicit parent adjudications; never infer or accept reviewer edges.

Source readings and handwritten decisions must exist before this command runs.
The reviewer report remains separate so corrections and rejected proposals are
inspectable. Prior phases and raw evidence are never modified here.
"""

import argparse
import json
from collections import Counter

from build_expansion_review import check_quotes, digest, write
from fetch_metadata import ROOT
from remaining_review_helpers import BASE, all_letters, read, validate_review


LIST_FIELDS = ("direct_reply_pairs", "cross_correspondent_knowledge", "correspondent_replies",
               "dated_sections", "reference_observations", "receipt_events", "within_day_events",
               "additional_exact_date_review_ids", "additional_period_hold_ids", "voice_held_ids",
               "rejected_or_candidate_links", "date_evidence", "corrections")


def curate(batch):
    packet = read(BASE / "packets" / f"{batch}.json")
    notes_path = BASE / "parent-reading" / f"{batch}.json"
    decisions_path = BASE / "parent-decisions" / f"{batch}.json"
    review_path = BASE / "reviews" / f"{batch}.json"
    notes, decisions, review = map(read, (notes_path, decisions_path, review_path))
    assert notes["status"] == "parent_full_source_read_complete"
    assert decisions["status"] == "parent_adjudicated"
    letters = all_letters()
    ids = packet["target_ids"] + packet["context_ids"]
    assert set(notes["source_record_ids_read"]) >= set(ids)
    unavailable = set(decisions.get("body_unavailable_ids", []))
    assert unavailable <= set(packet["target_ids"])
    assert set(notes["body_ids_read"]) >= set(ids) - unavailable
    assert not (set(notes["body_ids_read"]) & unavailable)
    assert set(notes["record_notes"]) >= set(ids)
    review_checks = validate_review(review_path)
    proposals = review["proposed_links"]
    dispositions = decisions["proposal_adjudications"]
    key = lambda row: (row["source_id"], row["target_id"], row["relationship"])
    assert Counter(map(key, proposals)) == Counter(map(key, dispositions))
    ledger = {
        "schema_version": 1, "period": "1837-1843", "batch_id": batch,
        "status": "parent_adjudicated",
        "method": f"Remaining review {batch}: gpt-5.6-luna first pass followed by primary-agent full-source reading and individual adjudication. Reviewer proposals are preserved separately and never promoted automatically.",
        "reviewed_record_ids": packet["target_ids"],
        "full_read_ids": [i for i in packet["target_ids"] if i not in unavailable],
        "body_unavailable_ids": sorted(unavailable), "non_individual_voice_ids": decisions.get("non_individual_voice_ids", []),
        "individual_limits": {i: notes["record_notes"][i] for i in packet["target_ids"]},
        "letter_adjudications": [], "proposal_adjudications": dispositions,
        "review_validation": review_checks, "training_export_performed": False,
        "review_context_read_ids": packet["context_ids"],
        "additional_parent_read_ids": sorted(set(notes["source_record_ids_read"]) - set(ids)),
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)}
                   for p in (notes_path, decisions_path, review_path, BASE / "packets" / f"{batch}.json")],
    }
    for field in LIST_FIELDS:
        ledger[field] = decisions.get(field, [])
    response_ids = {p["outgoing_id"] for p in ledger["direct_reply_pairs"]}
    reviews = {r["letter_id"]: r for r in review["record_reviews"]}
    for i in packet["target_ids"]:
        r = letters[i]
        a = r["metadata_audit"]
        role = "incoming_context_only" if a["direction"] == "to_darwin" else "grounding_candidate"
        if i in response_ids:
            role = "response_candidate"
        if not a["period_selection_eligible"]:
            role = "period_held_incoming_context" if a["direction"] == "to_darwin" else "period_held_outgoing"
        if i in ledger["non_individual_voice_ids"]:
            role = "joint_document_not_individual_Darwin_voice"
        if i in ledger["additional_period_hold_ids"]:
            role = "editorial_period_hold_preserving_original_XML_classification"
        if i in ledger["voice_held_ids"]:
            role = "authorship_held_not_Darwin_voice"
        if i in unavailable:
            role = "source_record_only_no_transcription"
        ledger["letter_adjudications"].append({
            "letter_id": i, "parent_source_record_read": True, "parent_body_read_in_full": i not in unavailable,
            "paragraphs_read": [p["body_paragraph"] for p in r["paragraphs"]] if i not in unavailable else [],
            "disposition": role, "reason": notes["record_notes"][i],
            "source_kind": decisions.get("source_kind_corrections", {}).get(i, reviews[i]["source_kind"]),
            "original_metadata": a, "source": r["source"],
            "reviewer_evidence_checked_by_parent": reviews[i].get("evidence", []),
            **decisions.get("text_scope_overrides", {}).get(i, {}),
        })
    quote_checks = check_quotes(ledger, letters)
    ledger["parent_exact_quote_checks"] = len(quote_checks)
    dest = ROOT / "data/annotations/remaining_1837_1843" / f"{batch}.json"
    if dest.exists():
        assert read(dest) == ledger, "Finalized batch differs: preserve it and create an explicit correction addendum."
    else:
        write(dest, ledger)
    status = read(BASE / "work_status.json")
    for row in status["packets"]:
        if row["batch_id"] == batch:
            row.update(review_status="full_read_complete", parent_status="adjudicated", ledger=str(dest.relative_to(ROOT)))
    write(BASE / "work_status.json", status)
    return {"batch": batch, "target_count": len(packet["target_ids"]), "parent_quote_checks": len(quote_checks),
            "direct_links": len(ledger["direct_reply_pairs"]), "reverse_links": len(ledger["correspondent_replies"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    args = parser.parse_args()
    print(json.dumps(curate(args.batch)))

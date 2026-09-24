"""Derive review progress from canonical reports and accepted period ledgers.

Counts describe recorded work; report existence is not historical acceptance.
This only updates mutable progress files, never sources or adjudications.
"""
import argparse
from datetime import datetime, timezone

from fetch_metadata import ROOT
from prepare_period import PERIODS, read, write


def update(period):
    base = ROOT / "reports" / period / "review"
    state = read(base / "work_status.json")
    counts = {"review_packets": len(state["packets"]), "first_pass_reports": 0,
              "parent_adjudicated_packets": 0, "parent_adjudicated_targets": 0,
              "direct_reply_links": 0, "distinct_direct_reply_outputs": 0,
              "reverse_reply_links": 0, "cross_correspondent_knowledge_links": 0}
    outputs = set()
    for row in state["packets"]:
        batch = row["batch_id"]
        report_path = base / "reviews" / f"{batch}.json"
        if report_path.exists():
            report = read(report_path)
            assert report["batch_id"] == batch
            row["review_status"] = report["status"]
            counts["first_pass_reports"] += 1
        ledger_path = ROOT / "data/annotations/periods" / period / f"{batch}.json"
        if ledger_path.exists():
            ledger = read(ledger_path)
            assert ledger["status"] == "parent_adjudicated"
            row.update(parent_status="adjudicated", ledger=str(ledger_path.relative_to(ROOT)))
            counts["parent_adjudicated_packets"] += 1
            counts["parent_adjudicated_targets"] += len(ledger["reviewed_record_ids"])
            counts["direct_reply_links"] += len(ledger["direct_reply_pairs"])
            counts["reverse_reply_links"] += len(ledger["correspondent_replies"])
            counts["cross_correspondent_knowledge_links"] += len(ledger["cross_correspondent_knowledge"])
            outputs.update(p["outgoing_id"] for p in ledger["direct_reply_pairs"])
    counts["distinct_direct_reply_outputs"] = len(outputs)
    counts["remaining_parent_packets"] = counts["review_packets"] - counts["parent_adjudicated_packets"]
    state.update(status="primary_adjudication_in_progress", progress=counts,
                 progress_updated_at=datetime.now(timezone.utc).isoformat(),
                 count_scope="Current period ledgers only, before cumulative deduplication; first-pass existence is not primary acceptance.")
    write(base / "work_status.json", state)
    research_path = ROOT / "reports/research/work_status.json"
    research = read(research_path)
    for row in research["periods"]:
        if row["period"] == period:
            row.update(status=state["status"], **counts)
    # Progress derivation is not a test run. Preserve the last recorded result.
    research["quality_limitations"] = [
        "Some first-pass proposals and summaries require correction; all accepted relationships require independent primary source reading.",
        "139 complete scholarly sections are preserved in scholarly-sections.v2.jsonl (122 annotations, 4 CD notes, 13 enclosures). The initial supplemental artifact mostly stored headings and omitted enclosures; its completeness claim and the associated supplementary reading claims were not verified. Primary reading uses complete raw sections.",
        "97 inline figure nodes are preserved with asset hashes. Relevant visuals require explicit primary reading; preservation alone is not interpretation. Editorial bibliographies are now displayed separately and prior accepted sources have an additive reading record; bibliography citations do not prove contemporary reading.",
        "Composition, physical receipt, demonstrated reading and response dates remain distinct."
    ]
    research["progress_updated_at"] = state["progress_updated_at"]
    write(research_path, research)
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", choices=PERIODS, required=True)
    print(update(parser.parse_args().period))

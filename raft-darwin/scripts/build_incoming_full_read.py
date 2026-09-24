#!/usr/bin/env python3
"""Validate full-body review coverage and publish candidate assessments.

This publisher has no code path that promotes an assessment to a graph edge.
"""

import copy
import hashlib
import json
from collections import Counter

from build_correspondence_map import ROOT, enrich_evidence, load_jsonl, write_json
from build_post_return_review import escape, link

OUT = ROOT / "reports/post-return-1836/incoming-full-read"
STATUSES = {"supported_direct_reply", "supported_knowledge", "unconfirmed_specific_overlap",
            "background_only", "implausible_antecedent", "no_specific_link"}


def expected_pairs(dossiers):
    return {(candidate["id"], dossier["letter_id"]) for dossier in dossiers
            for candidate in dossier["same_correspondent_date_screen"]
            if candidate["screen_disposition"] == "chronologically_possible_identity_candidate"}


def validate_reviews(reviews, manifest, letters, pairs):
    by_letter = {r["id"]: r for r in letters}
    read_records, assessments, seen_pairs, seen_incoming = [], [], set(), set()
    for group, review in reviews.items():
        spec = manifest["groups"][group]
        expected_read = set(spec["incoming"] + spec["outgoing"])
        actual_read = [r["letter_id"] for r in review["read_records"]]
        if len(actual_read) != len(set(actual_read)) or set(actual_read) != expected_read:
            raise ValueError(f"Incomplete or duplicate reading coverage: {group}")
        if review["model"] != manifest["requested_model"]:
            raise ValueError(f"Unexpected reviewer model: {group}")
        for record in review["read_records"]:
            letter = by_letter[record["letter_id"]]
            expected_paragraphs = [p["body_paragraph"] for p in letter["paragraphs"]]
            if (record["full_body_read"] is not True
                    or record["paragraphs_read"] != expected_paragraphs
                    or record["source_sha256"] != letter["source"]["sha256"]
                    or record["body_word_count"] != letter["body_word_count"]):
                raise ValueError(f"Reading declaration does not cover preserved body: {record['letter_id']}")
            if record["letter_id"] in spec["incoming"]:
                if record["letter_id"] in seen_incoming:
                    raise ValueError("Incoming letter assigned to more than one reviewer")
                seen_incoming.add(record["letter_id"])
            read_records.append({**copy.deepcopy(record), "reviewer": review["reviewer"],
                                 "model": review["model"], "group": group,
                                 "synopsis_basis": ("source_editorial_summary" if record["synopsis"] == letter.get("editorial_summary") else "reviewer_synopsis"),
                                 "direction": letter["direction"], "source": letter["source"],
                                 "original_csv": letter["original_csv"],
                                 "sent_date_constraints": letter["sent_date_constraints"],
                                 "xml_date_bounds": letter["xml_date_bounds"]})
        group_pairs = {pair for pair in pairs if pair[0] in spec["incoming"]}
        actual_group_pairs = set()
        for raw in review["assessments"]:
            assessment = enrich_evidence(raw, by_letter)
            pair = (assessment["incoming_id"], assessment["outgoing_id"])
            if pair in seen_pairs or pair not in group_pairs or assessment["status"] not in STATUSES:
                raise ValueError(f"Duplicate, unexpected, or invalid assessment: {pair}")
            if not assessment["reason"].strip() or not assessment["evidence"]:
                raise ValueError(f"Assessment lacks rationale/evidence: {pair}")
            evidence_letters = {e["letter_id"] for e in assessment["evidence"]}
            if pair[0] not in evidence_letters:
                raise ValueError(f"Assessment lacks evidence from candidate incoming text: {pair}")
            if assessment["status"] in {"supported_direct_reply", "supported_knowledge", "unconfirmed_specific_overlap"} and not set(pair) <= evidence_letters:
                raise ValueError(f"Proposed content relationship needs both sides: {pair}")
            assessment.update({"id": f"full-read-{pair[0]}-to-{pair[1]}",
                               "reviewer": review["reviewer"], "model": review["model"], "group": group,
                               "automatic_graph_promotion": False,
                               "establishes_receipt_or_prompt_by_itself": False})
            seen_pairs.add(pair)
            actual_group_pairs.add(pair)
            assessments.append(assessment)
        if actual_group_pairs != group_pairs:
            raise ValueError(f"Missing candidate comparisons: {group}")
    if seen_pairs != pairs or seen_incoming != {pair[0] for pair in pairs}:
        raise ValueError("Full review does not cover the complete earlier-input screen")
    return {"schema_version": 1, "review_date": manifest["review_date"],
            "review_model": manifest["requested_model"], "read_records": read_records,
            "assessments": assessments, "reviewer_reports": copy.deepcopy(reviews),
            "policy": manifest["policy"], "automatic_graph_promotions": False,
            "validation_scope": "Checks reading declarations against every preserved paragraph, original metadata, source hashes, all expected pairs, and every quoted offset. Reading declarations are the reviewers' attestations; checked quotations do not alone prove full reading."}


def apply_parent_review(audit, decisions, by_letter):
    """Apply explicit editorial decisions while retaining the original proposals."""
    decisions = enrich_evidence(decisions, by_letter)
    if decisions["status"] != "reviewed" or decisions["automatic_graph_promotion"] is not False:
        raise ValueError("Parent review is not complete")
    by_pair = {(a["incoming_id"], a["outgoing_id"]): a for a in audit["assessments"]}
    seen = set()
    for decision in decisions["overrides"]:
        pair = (decision["incoming_id"], decision["outgoing_id"])
        if pair in seen or pair not in by_pair or decision["status"] not in STATUSES:
            raise ValueError("Invalid parent assessment decision")
        seen.add(pair)
        assessment = by_pair[pair]
        assessment["reviewer_assessment"] = copy.deepcopy(assessment)
        for key in ("status", "reason", "plausibility_factors", "alternatives_or_limits"):
            if key in decision:
                assessment[key] = decision[key]
        assessment["parent_review_basis"] = decision["review_basis"]
        assessment["parent_evidence"] = decision.get("evidence", [])
    audit["parent_review"] = copy.deepcopy(decisions)
    return audit


def render_report(audit):
    incoming = [r for r in audit["read_records"] if r["direction"] == "to_darwin"]
    assessments = audit["assessments"]
    lines = ["# Full reading of earlier incoming candidates", "",
             f"Three `{audit['review_model']}` reviewers read **{len(incoming)} distinct incoming letters in full** and compared them against the relevant post-return Darwin letters: **{len(assessments)} incoming/outgoing comparisons**. The 13-letter outgoing review had already been completed; 307, 320, and 329 have no same-correspondent earlier inputs in this screen.", "",
             "These are body-based assessments of a deliberately broad identity/date screen. **Chronologically possible does not mean a plausible conversational prompt.** Intervening shared experience, visits, changes in circumstances, and whether the earlier request still makes sense affect plausibility. No fixed age cutoff is used, and no assessment automatically creates a receipt date, knowledge link, or training pair.", "",
             audit.get("parent_review", {}).get("conclusion", "Parent assessment review pending; these remain reviewer proposals."), "",
             "## Review coverage", "",
             "| Group | Incoming letters read | Comparisons |",
             "| --- | ---: | ---: |"]
    for group in audit["reviewer_reports"]:
        lines.append(f"| {group.replace('_', ' ')} | {sum(r['group'] == group for r in incoming)} | {sum(a['group'] == group for a in assessments)} |")
    lines += ["", "## Assessment totals", "", "| Assessment | Comparisons |", "| --- | ---: |"]
    for status, count in sorted(Counter(a["status"] for a in assessments).items()):
        lines.append(f"| {status.replace('_', ' ')} | {count} |")
    lines += ["", "A background-only assessment describes a relationship in subject matter or history; it does not mean the incoming document has been established as available for persona memory. An implausible antecedent is not the same as a date-impossible record. Specific unresolved overlaps remain candidates until separately checked.",
              "", "## Full-reading record", "", "| Incoming letter | Original date | Body words | Reading synopsis |", "| --- | --- | ---: | --- |"]
    for record in incoming:
        lines.append(f"| {link(record['letter_id'])} | {escape(record['original_csv']['date'])} | {record['body_word_count']} | {escape(record['synopsis'])} |")
    lines += ["", "## Comparison decisions", ""]
    target_ids = sorted({a["outgoing_id"] for a in assessments})
    for target in target_ids:
        lines += [f"### Darwin {target.removeprefix('DCP-LETT-')}", ""]
        for assessment in assessments:
            if assessment["outgoing_id"] != target:
                continue
            lines += [f"**{link(assessment['incoming_id'])}: {assessment['status'].replace('_', ' ')}.** {assessment['reason']}", ""]
            if assessment.get("reviewer_assessment") and assessment["reviewer_assessment"]["status"] != assessment["status"]:
                lines += ["Parent review changed the proposed status from " + assessment["reviewer_assessment"]["status"].replace("_", " ") + "; the original proposal remains in the audit.", ""]
            if assessment.get("plausibility_factors"):
                lines += ["Plausibility: " + " ".join(assessment["plausibility_factors"]), ""]
            if assessment.get("alternatives_or_limits"):
                lines += ["Limits: " + " ".join(assessment["alternatives_or_limits"]), ""]
            for span in assessment["evidence"] + assessment.get("parent_evidence", []):
                lines.append(f"- {link(span['letter_id'])}, body paragraph {span['body_paragraph']}: “{escape(span['quote'])}”")
            lines.append("")
    lines += ["## Evidence files and limits", "",
              "[audit.json](audit.json) retains the review reports, full-reading declarations, all comparisons, original catalogue metadata, XML constraints, quoted offsets, and source hashes. The three `.packet.json` files preserve the complete texts supplied to reviewers; `.review.json` files preserve their returned assessments. Earlier proposals remain in `.initial.review.json`; [parent_review.json](parent_review.json) records the final adjudication and methodological corrections.", "",
              audit["validation_scope"], "",
              "These reviewers read all body paragraphs, including letters by joint senders. Reused source editorial summaries are labelled in each reading record; summaries are not treated as proof of full reading. Separate editorial apparatus is evidence for reconstruction only, not historical persona knowledge. No incoming author becomes Darwin's voice. The original source texts and XML audit remain unchanged. Accepted relationships continue to be maintained in the [canonical map](../../correspondence-map/README.md).", ""]
    return "\n".join(lines)


def main():
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    body_path = ROOT / manifest["input"]["path"]
    if hashlib.sha256(body_path.read_bytes()).hexdigest() != manifest["input"]["sha256"]:
        raise ValueError("Preserved body input changed")
    letters = load_jsonl(body_path)
    dossiers_path = ROOT / "reports/post-return-1836/dossiers.jsonl"
    dossiers = load_jsonl(dossiers_path)
    reviews, inputs = {}, [manifest_path, body_path]
    by_letter = {r["id"]: r for r in letters}
    for group in manifest["groups"]:
        review_path = OUT / f"{group}.review.json"
        packet_path = OUT / f"{group}.packet.json"
        packet = json.loads(packet_path.read_text())
        for row in packet["letters"]:
            original = by_letter[row["id"]]
            if any(row[key] != original[key] for key in ("paragraphs", "source", "original_csv", "xml_date_bounds", "sent_date_constraints")):
                raise ValueError("Reviewer packet differs from preserved source")
        reviews[group] = json.loads(review_path.read_text())
        inputs.extend([review_path, packet_path])
        initial_path = OUT / f"{group}.initial.review.json"
        if initial_path.exists():
            inputs.append(initial_path)
    audit = validate_reviews(reviews, manifest, letters, expected_pairs(dossiers))
    parent_path = OUT / "parent_review.json"
    if parent_path.exists():
        audit = apply_parent_review(audit, json.loads(parent_path.read_text()), by_letter)
        inputs.append(parent_path)
    audit["inputs"] = [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in inputs]
    audit["comparison_scope"] = sorted([list(pair) for pair in expected_pairs(dossiers)])
    write_json(OUT / "audit.json", audit)
    (OUT / "README.md").write_text(render_report(audit))
    summary = {"incoming_letters_read_in_full": sum(r["direction"] == "to_darwin" for r in audit["read_records"]),
               "outgoing_letters_reread_in_full": sum(r["direction"] == "from_darwin" for r in audit["read_records"]),
               "candidate_comparisons": len(audit["assessments"]),
               "statuses": dict(Counter(a["status"] for a in audit["assessments"])),
               "automatic_graph_promotions": False, "inputs": audit["inputs"],
               "audit_sha256": hashlib.sha256((OUT / "audit.json").read_bytes()).hexdigest()}
    write_json(OUT / "summary.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key not in {"inputs", "audit_sha256"}}))


if __name__ == "__main__":
    main()

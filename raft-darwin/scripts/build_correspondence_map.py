#!/usr/bin/env python3
"""Build an evidence-backed map with separate knowledge, reply, and voice roles."""

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/correspondence-map"
PERIOD = ROOT / "reports/1828-1836"
DARWIN = "nameregs_1.xml"


def load_jsonl(path):
    return [json.loads(s) for s in path.read_text().splitlines()]


def person_keys(people):
    return {p["attributes"]["key"].split("/")[-1] for p in people if p.get("attributes", {}).get("key")}


def resolved_day(record):
    if (not record["exact_order_needs_review"]
            and record["xml_earliest"] == record["xml_latest"]):
        return record["xml_latest"]
    return None


def enrich_evidence(value, by_letter):
    """Check every nested quotation against the preserved body and source hash."""
    if isinstance(value, list):
        return [enrich_evidence(item, by_letter) for item in value]
    if not isinstance(value, dict):
        return value
    value = {key: enrich_evidence(item, by_letter) for key, item in value.items()}
    if {"letter_id", "body_paragraph", "quote", "char_start", "char_end"} <= value.keys():
        letter = by_letter[value["letter_id"]]
        paragraph = next(p for p in letter["paragraphs"] if p["body_paragraph"] == value["body_paragraph"])
        start, end = value["char_start"], value["char_end"]
        if (not 0 <= start < end <= len(paragraph["text"])
                or paragraph["text"][start:end] != value["quote"]
                or letter["source"]["sha256"] != value["source_sha256"]):
            raise ValueError(f"Evidence changed: {value['letter_id']} paragraph {value['body_paragraph']}")
        value["locator"] = paragraph["locator"]
        value["source"] = copy.deepcopy(letter["source"])
    return value


def build_map(audit, letters, annotations):
    by_letter = {r["id"]: r for r in letters}
    if len(by_letter) != len(letters) or len({r["id"] for r in audit}) != len(audit):
        raise ValueError("Duplicate source IDs")
    annotations = enrich_evidence(annotations, by_letter)
    nodes = {}
    for record in audit:
        letter = by_letter.get(record["id"])
        if letter and letter["original_csv"] != record["original_csv"]:
            raise ValueError(f"Metadata mismatch: {record['id']}")
        attribution = (letter or {}).get("text_attribution_review") or {}
        body_available = bool(letter and letter["paragraphs"])
        voice = (record["direction"] == "from_darwin"
                 and person_keys(record["sender_evidence"]) == {DARWIN}
                 and record["period_selection_eligible"] and body_available
                 and attribution.get("darwin_voice_training_eligible") is not False)
        nodes[record["id"]] = {
            "id": record["id"], "node_kind": "catalogued_letter",
            "label": (letter or {}).get("title", record["id"]),
            "direction": record["direction"], "original_csv": copy.deepcopy(record["original_csv"]),
            "original_sent_date_constraints": copy.deepcopy(record["sent_date_constraints"]),
            "original_xml_notes": copy.deepcopy(record["xml_notes"]),
            "xml_date_bounds": {"earliest": record["xml_earliest"], "latest": record["xml_latest"],
                                "exact_order_needs_review": record["exact_order_needs_review"]},
            "writing_date": resolved_day(record),
            "period_selection_eligible": record["period_selection_eligible"],
            "sender_evidence": record["sender_evidence"], "recipient_evidence": record["recipient_evidence"],
            "provenance": record["provenance"], "body_source": letter["source"] if letter else None,
            "text_available": body_available, "text_attribution_review": attribution or None,
            "darwin_voice_eligible": voice,
            "voice_eligibility_basis": ("Sole Darwin sender in XML, preserved body, eligible period, no recorded exclusion; further editorial review may change this."
                                        if voice else "Incoming authorship, held date, missing text, joint attribution, or reported text excludes a Darwin voice target."),
            "response_to_ids": [], "established_prompt_ids": [], "own_letter_reference_ids": [],
            "known_by_date": None, "known_by_is_exact_receipt_date": False,
            "availability_attested_for_ids": [], "raft_export_ready": False,
        }
    for missing in annotations["unlocated_nodes"]:
        if missing["id"] in nodes:
            raise ValueError("Duplicate unlocated node")
        nodes[missing["id"]] = {
            **copy.deepcopy(missing), "original_sent_date_constraints": [],
            "writing_date": None, "period_selection_eligible": False,
            "darwin_voice_eligible": False, "body_source": None,
            "known_by_date": None, "known_by_is_exact_receipt_date": False,
            "availability_attested_for_ids": [], "response_to_ids": [],
            "established_prompt_ids": [], "own_letter_reference_ids": [], "raft_export_ready": False,
        }

    # Archival identification and the identity available to Darwin are distinct.
    # These restrictions travel with both the graph and its incoming-date view.
    for policy in annotations.get("context_identity_policies", []):
        node = nodes[policy["letter_id"]]
        if node["direction"] != "to_darwin" or not policy.get("evidence"):
            raise ValueError("Context identity policy requires an incoming source and evidence")
        node["context_identity_policy"] = copy.deepcopy(policy)

    edges, edge_ids = [], set()
    for annotation in annotations["edges"]:
        edge = copy.deepcopy(annotation)
        if edge["id"] in edge_ids:
            raise ValueError("Duplicate edge ID")
        edge_ids.add(edge["id"])
        if edge["review_status"] != "reviewed" or edge["confidence"] != "high":
            raise ValueError("Unreviewed or uncertain matches belong in the candidate queue")
        source, target = nodes[edge["source_id"]], nodes[edge["target_id"]]
        if not edge["evidence"]:
            raise ValueError("An assertion needs evidence")
        if edge["relationship"] == "knowledge_before":
            if source["direction"] != "to_darwin" or target["direction"] != "from_darwin":
                raise ValueError("Darwin knowledge must be attested in Darwin's own outgoing writing")
            if not target["darwin_voice_eligible"]:
                raise ValueError("Knowledge attestation requires individually attributed Darwin text")
            if source["node_kind"] == "catalogued_letter" and not source["period_selection_eligible"]:
                raise ValueError("Cannot activate a held incoming record")
            if not any(e["letter_id"] == target["id"] for e in edge["evidence"]):
                raise ValueError("Need evidence in the attesting Darwin letter")
            edge["known_by_date"] = target["writing_date"]
            edge["known_by_date_basis"] = "attesting_Darwin_writing_date"
            edge["attesting_date_constraints"] = target["original_sent_date_constraints"]
            edge["date_needs_review"] = edge["known_by_date"] is None
            edge["exact_receipt_date"] = None
            edge["other_same_day_events_require_ordering_evidence"] = True
            edge["conversation_prompt_eligible"] = False
            source["availability_attested_for_ids"].append(target["id"])
            if edge["known_by_date"]:
                earliest = source.get("xml_date_bounds", {}).get("earliest")
                if earliest and earliest > edge["known_by_date"]:
                    raise ValueError("Attestation predates all possible incoming writing dates")
                source["known_by_date"] = min(filter(None, (source["known_by_date"], edge["known_by_date"])))
        elif edge["relationship"] == "replies_to":
            if (not all(person_keys(n[k]) for n in (source, target) for k in ("sender_evidence", "recipient_evidence"))
                    or person_keys(source["sender_evidence"]) != person_keys(target["recipient_evidence"])
                    or person_keys(source["recipient_evidence"]) != person_keys(target["sender_evidence"])):
                raise ValueError("Direct reply participants do not match; use a knowledge link")
            source["response_to_ids"].append(target["id"])
            edge["conversation_prompt_eligible"] = False
        elif edge["relationship"] == "refers_to_own_letter":
            if (not source["darwin_voice_eligible"] or target["direction"] != "from_darwin"
                    or person_keys(target["sender_evidence"]) != {DARWIN}):
                raise ValueError("Own-letter references need Darwin authorship at both ends")
            if not any(e["letter_id"] == source["id"] for e in edge["evidence"]):
                raise ValueError("Own-letter reference needs evidence in the referring letter")
            source["own_letter_reference_ids"].append(target["id"])
            edge["conversation_prompt_eligible"] = False
            edge["creates_Darwin_incoming_availability"] = False
        elif edge["relationship"] == "receipt_without_reading":
            if (source["direction"] != "to_darwin" or not target["darwin_voice_eligible"]
                    or not any(e["letter_id"] == target["id"] for e in edge["evidence"])):
                raise ValueError("Unread receipt needs an incoming reference and a Darwin witness")
            edge["conversation_prompt_eligible"] = False
            edge["creates_Darwin_incoming_availability"] = False
            edge["known_by_date"] = None
            edge["receipt_witness_writing_date"] = target["writing_date"]
            # Receipt does not prove reading. Deliberately do not update the node's
            # known-by date or availability_attested_for_ids.
        elif edge["relationship"] == "source_event_match":
            if (source["direction"] != "to_darwin" or not target["darwin_voice_eligible"]
                    or not edge.get("event_scope")
                    or not any(e["letter_id"] == target["id"] for e in edge["evidence"])):
                raise ValueError("A source-event match needs a scoped event and Darwin evidence")
            edge["conversation_prompt_eligible"] = False
            edge["creates_Darwin_incoming_availability"] = False
            edge["full_source_text_reading_established"] = False
            edge["event_attested_by_writing_date"] = target["writing_date"]
        else:
            raise ValueError("Unknown relationship")
        edges.append(edge)

    candidates = annotations.get("candidate_links", [])
    for candidate in candidates:
        if candidate["id"] in edge_ids:
            raise ValueError("Candidate ID duplicates another relationship")
        edge_ids.add(candidate["id"])
        if (candidate["source_id"] not in nodes or candidate["target_id"] not in nodes
                or not candidate["evidence"] or candidate["review_status"] == "reviewed"):
            raise ValueError("Invalid candidate relationship")
        candidate["automatic_availability_or_prompt"] = False
        candidate["conversation_prompt_eligible"] = False

    reviews = annotations.get("reviewed_letters", [])
    reviewed_ids = set()
    for review in reviews:
        node = nodes[review["letter_id"]]
        if review["letter_id"] in reviewed_ids or not node["darwin_voice_eligible"]:
            raise ValueError("Duplicate or ineligible outgoing review")
        reviewed_ids.add(review["letter_id"])
        if review["review_status"] != "reviewed" or not review["target_body_read_in_full"]:
            raise ValueError("Incomplete outgoing review")
        evidence_ids = [e["evidence_id"] for e in review["evidence"]]
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("Duplicate evidence labels in review")
        for observation in review["observations"]:
            if not set(observation["evidence_ids"]) <= set(evidence_ids):
                raise ValueError("Observation refers to missing evidence")
        node["correspondence_review"] = {key: review[key] for key in ("batch_id", "review_status", "outcome", "summary")}

    knowledge_pairs = {(e["source_id"], e["target_id"]): e for e in edges if e["relationship"] == "knowledge_before"}
    for edge in edges:
        if edge["relationship"] != "replies_to":
            continue
        source, target = nodes[edge["source_id"]], nodes[edge["target_id"]]
        support = knowledge_pairs.get((target["id"], source["id"]))
        eligible = bool(source["darwin_voice_eligible"] and target["text_available"]
                        and target["direction"] == "to_darwin" and target["period_selection_eligible"]
                        and support and support["known_by_date"])
        edge["conversation_prompt_eligible"] = eligible
        if eligible:
            source["established_prompt_ids"].append(target["id"])
        edge["target_text_available"] = target["text_available"]

    for node in nodes.values():
        if node["node_kind"] == "referenced_unlocated_letter":
            role = ("attested_missing_outgoing_text" if node["direction"] == "from_darwin"
                    else "attested_missing_text_no_prompt")
        elif not node["period_selection_eligible"]:
            role = "held_date_constraints"
        elif node["direction"] == "to_darwin":
            role = "attributed_context" if node["known_by_date"] else "incoming_awaiting_availability_evidence"
        elif not node["darwin_voice_eligible"]:
            role = "excluded_from_Darwin_voice"
        else:
            role = "Darwin_response_candidate" if node["established_prompt_ids"] else "dated_Darwin_grounding"
        node["training_role"] = role
        node["general_context_available_after_date"] = (node["known_by_date"]
            if node["direction"] == "to_darwin" and node["text_available"] else None)
    return {"schema_version": 2, "nodes": list(nodes.values()), "edges": edges,
            "candidate_links": candidates, "reviewed_letters": reviews,
            "review_batches": annotations.get("review_batches", []),
            "incoming_full_read_review": annotations.get("incoming_full_read_review"),
            "pre_beagle_full_read_review": annotations.get("pre_beagle_full_read_review"),
            "relation_definitions": annotations["relation_definitions"], "search_cases": annotations["search_cases"],
            "policy_notes": annotations["policy_notes"],
            "coverage": "All 288 audited catalogue candidates plus explicitly attested unlocated references. Relationships reviewed incrementally; absence of an edge is not absence of a historical relationship.",
            "training_performed": False, "raft_export_performed": False}


def incoming_records(graph):
    output = []
    nodes = {n["id"]: n for n in graph["nodes"]}
    for node in graph["nodes"]:
        if node["node_kind"] != "catalogued_letter" or node["direction"] != "to_darwin" or not node["period_selection_eligible"]:
            continue
        knowledge = [e for e in graph["edges"] if e["relationship"] == "knowledge_before" and e["source_id"] == node["id"]]
        replies = [e for e in graph["edges"] if e["relationship"] == "replies_to" and e["target_id"] == node["id"] and nodes[e["source_id"]]["direction"] == "from_darwin"]
        response_links = [{
            "response_letter_id": e["source_id"], "response_date": nodes[e["source_id"]]["writing_date"],
            "response_date_original": nodes[e["source_id"]]["original_csv"]["date"],
            "response_sent_date_constraints": nodes[e["source_id"]]["original_sent_date_constraints"],
            "response_date_needs_review": nodes[e["source_id"]]["writing_date"] is None,
            "response_date_provenance": nodes[e["source_id"]]["provenance"],
            "context_for_this_response_established": True, "conversation_prompt_eligible": e["conversation_prompt_eligible"],
            "match_confidence": e["confidence"], "match_basis": e["basis"], "evidence": e["evidence"],
        } for e in replies]
        output.append({
            "id": node["id"], "original_csv": node["original_csv"],
            "original_sent_date_constraints": node["original_sent_date_constraints"], "provenance": node["provenance"],
            "response_links": response_links, "knowledge_links": knowledge,
            "knowledge_date": node["known_by_date"],
            "knowledge_date_basis": "earliest_reviewed_Darwin_attestation" if node["known_by_date"] else None,
            "knowledge_date_is_exact_receipt_date": False,
            "availability_status": ("dated_from_reviewed_attestation" if node["known_by_date"] else
                                    "attestation_date_needs_review" if knowledge else "no_established_availability_yet"),
            "available_for_response_ids": [r["response_letter_id"] for r in response_links],
            "available_for_outgoing_ids": node["availability_attested_for_ids"],
            "darwin_voice_training_eligible": False, "other_same_day_events_require_ordering_evidence": True,
            "context_identity_policy": node.get("context_identity_policy"),
        })
    return output


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [PERIOD / "audit.jsonl", ROOT / "reports/body-date-search-37-337/letters.jsonl",
             ROOT / "data/annotations/correspondence_links.json", ROOT / "data/annotations/text_attribution.json"]
    audit, letters = load_jsonl(paths[0]), load_jsonl(paths[1])
    current_attribution = json.loads(paths[3].read_text())
    for letter in letters:
        if letter.get("text_attribution_review") != current_attribution.get(letter["id"]):
            raise ValueError("Rebuild body extraction after changing attribution annotations")
        source = letter["source"]
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Body snapshot hash mismatch")
    graph = build_map(audit, letters, json.loads(paths[2].read_text()))
    graph["inputs"] = [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    observations = [ROOT / "reports/body-date-search-37-337/reviewed_findings.json", PERIOD / "receipt_evidence.json"]
    graph["prior_temporal_observations"] = json.loads(observations[0].read_text())
    graph["prior_receipt_observations"] = json.loads(observations[1].read_text())["observations"]
    graph["inputs"] += [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in observations]
    review_sources = [source for key in ("incoming_full_read_review", "pre_beagle_full_read_review")
                      for source in (graph.get(key) or {}).get("source_files", [])]
    for source in review_sources:
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Incoming full-read review source changed; re-review annotations")
        graph["inputs"].append(source)
    write_json(OUT / "graph.json", graph)
    incoming = incoming_records(graph)
    target = PERIOD / "incoming_knowledge_dates.jsonl"
    target.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in incoming))
    summary = {
        "catalogued_nodes": sum(n["node_kind"] == "catalogued_letter" for n in graph["nodes"]),
        "unlocated_nodes": sum(n["node_kind"] == "referenced_unlocated_letter" for n in graph["nodes"]),
        "edges_by_type": dict(Counter(e["relationship"] for e in graph["edges"])),
        "candidate_relationships": len(graph["candidate_links"]),
        "reviewed_outgoing_letters": len(graph["reviewed_letters"]),
        "incoming_candidates_read_in_full": (graph.get("incoming_full_read_review") or {}).get("incoming_count", 0),
        "incoming_candidate_comparisons": (graph.get("incoming_full_read_review") or {}).get("comparison_count", 0),
        "pre_beagle_outgoing_read_in_full": (graph.get("pre_beagle_full_read_review") or {}).get("outgoing_count", 0),
        "pre_beagle_incoming_read_in_full": (graph.get("pre_beagle_full_read_review") or {}).get("incoming_count", 0),
        "incoming_records": len(incoming), "incoming_with_knowledge_date": sum(r["knowledge_date"] is not None for r in incoming),
        "incoming_without_knowledge_date": sum(r["knowledge_date"] is None for r in incoming),
        "established_prompt_pairs": sum(e["conversation_prompt_eligible"] for e in graph["edges"]),
        "roles": dict(Counter(n["training_role"] for n in graph["nodes"])),
        "incoming_voice_targets": sum(n["darwin_voice_eligible"] for n in graph["nodes"] if n["direction"] == "to_darwin"),
        "unknown_dates_are_retrievable": False, "training_performed": False, "raft_export_performed": False,
        "inputs": graph["inputs"],
    }
    write_json(OUT / "summary.json", summary)
    write_json(PERIOD / "knowledge_dating_summary.json", {
        **summary, "policy": "Reviewed Darwin knowledge attestations and direct reply relationships are separate.",
        "status_counts": dict(Counter(r["availability_status"] for r in incoming)),
        "output": {"path": str(target.relative_to(ROOT)), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()},
    })
    print(json.dumps({k: summary[k] for k in ("catalogued_nodes", "unlocated_nodes", "edges_by_type", "incoming_with_knowledge_date", "established_prompt_pairs", "roles")}))


if __name__ == "__main__":
    main()

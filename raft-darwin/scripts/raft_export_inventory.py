"""Build a read-only inventory for the eventual cumulative RAFT export.

This module deliberately stops before transcript/corpus generation.  It reads
accepted research ledgers and graphs, normalizes relationship direction and
scope, and writes a dry-run audit outside ``darwin_0``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
REVISION = "ab0d973bae05b54d68d82d068211015996cfec06"
PERIODS = ("1844-1846", "1847-1850", "1851-1855", "1856-1857", "1858-1859")
BEAGLE = ROOT / "data/annotations/beagle-voyage"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text())


def load_jsonl_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return {row.get("id"): row for row in (json.loads(line) for line in path.read_text().splitlines()) if row.get("id")}


def accepted(path: Path) -> bool:
    try:
        return load(path).get("status") in {"parent_adjudicated", "accepted"}
    except (OSError, json.JSONDecodeError):
        return False


def source_ref(value: dict[str, Any], ident: str | None = None) -> dict[str, Any]:
    """Normalize body/source provenance without copying letter prose."""
    body = value.get("body_source") or value.get("source") or {}
    meta = value.get("metadata_provenance") or value.get("provenance") or {}
    if not meta and isinstance(value.get("metadata_audit"), dict):
        meta = value["metadata_audit"].get("provenance", {})
    return {
        "letter_id": ident or value.get("letter_id") or body.get("id"),
        "body_path": body.get("path") or value.get("source_path"),
        "body_url": body.get("url") or value.get("source_url"),
        "body_retrieved_at": body.get("retrieved_at") or value.get("retrieved_at"),
        "body_sha256": body.get("sha256") or value.get("source_sha256"),
        "xml_path": meta.get("xml_path"),
        "xml_url": meta.get("xml_url"),
        "xml_sha256": meta.get("xml_sha256"),
        "revision": meta.get("revision", REVISION),
        "csv_path": meta.get("csv_path"),
        "csv_sha256": meta.get("csv_sha256"),
        "csv_physical_line_start": meta.get("csv_physical_line_start"),
        "csv_physical_line_end": meta.get("csv_physical_line_end"),
    }


def add_pin(pins: OrderedDict[str, dict[str, Any]], path: Path, role: str) -> None:
    rel = str(path.relative_to(ROOT))
    pins.setdefault(rel, {"path": rel, "sha256": sha256(path), "role": role})


def scope_of(link: dict[str, Any]) -> dict[str, Any]:
    return {
        "response_scope": link.get("response_scope"),
        "response_sections": link.get("response_sections", []),
        "response_paragraphs": link.get("response_paragraphs", []),
        "response_fragments": link.get("response_fragments", []),
        "knowledge_scope": link.get("knowledge_scope"),
        "date_policy": link.get("response_date_policy") or link.get("knowledge_date_basis"),
    }


def period_ledgers(pins: OrderedDict[str, dict[str, Any]]) -> Iterable[tuple[str, Path, dict[str, Any]]]:
    for period in PERIODS:
        for path in sorted((ROOT / "data/annotations/periods" / period).glob("batch-*.json")):
            data = load(path)
            if not accepted(path):
                continue
            add_pin(pins, path, "accepted v2 period ledger")
            yield period, path, data


def beagle_ledgers(pins: OrderedDict[str, dict[str, Any]]) -> Iterable[tuple[Path, dict[str, Any]]]:
    for path in sorted(BEAGLE.glob("*.primary.json")):
        if accepted(path):
            add_pin(pins, path, "accepted Beagle group ledger")
            yield path, load(path)
    for path in sorted((BEAGLE / "addenda").glob("*.primary.json")):
        data = load(path)
        if str(data.get("status", "")).startswith("primary_"):
            add_pin(pins, path, "accepted Beagle additive correction (primary schema)")
            yield path, data


def relationship_rows(
    records: OrderedDict[str, dict[str, Any]],
    data: dict[str, Any],
    ledger_path: Path,
    kind: str,
    accounting: dict[str, Any] | None = None,
) -> None:
    """Collect relation records using stable IDs and preserve all date fields."""
    if accounting is not None:
        accounting["source_records_seen"] += len(data.get("sources", []))
    for pair in data.get("direct_reply_pairs", []):
        if accounting is not None: accounting["direct_reply_pairs_seen"] += 1
        incoming_ids = pair.get("incoming_ids") or [pair.get("incoming_id")]
        outgoing_ids = pair.get("outgoing_ids") or [pair.get("outgoing_id") or pair.get("reply_id")]
        incoming, outgoing = next((x for x in incoming_ids if x), None), next((x for x in outgoing_ids if x), None)
        if not incoming or not outgoing:
            if accounting is not None: accounting["unmapped_relationships"] += 1
            continue
        key = ("direct", incoming, outgoing, json.dumps(scope_of(pair), sort_keys=True))
        records.setdefault("|".join(key), {
            "record_kind": "direct_pair",
            "status": pair.get("status", "accepted"),
            "source_id": incoming,
            "target_id": outgoing,
            "question_id": incoming,
            "response_id": outgoing,
            "ledger": str(ledger_path.relative_to(ROOT)),
            "source_family": kind,
            "date": {k: pair.get(k) for k in ("known_by_date", "actual_receipt_date", "response_date_policy", "response_date_constraints") if k in pair},
            "scope": scope_of(pair),
            "training_export_ready": pair.get("training_export_ready"),
            "evidence": pair.get("evidence", []),
            "incoming_scope": pair.get("incoming_scope"),
            "shares_response_with": pair.get("shares_response_with"),
            "accepted_record": pair,
        })
    for field, relation in (("correspondent_replies", "reverse_reply"), ("cross_correspondent_knowledge", "knowledge")):
        for link in data.get(field, []):
            if accounting is not None: accounting[f"{field}_seen"] += 1
            source = link.get("incoming_id") or link.get("antecedent_id") or link.get("incoming_id_list")
            target = link.get("witness_id") or link.get("response_id") or link.get("outgoing_id") or link.get("reply_id")
            if isinstance(source, list): source = next(iter(source), None)
            if isinstance(target, list): target = next(iter(target), None)
            if not source or not target:
                if accounting is not None: accounting["unmapped_relationships"] += 1
                continue
            key = (relation, source, target, json.dumps(scope_of(link), sort_keys=True))
            records.setdefault("|".join(key), {
                "record_kind": relation,
                "status": link.get("status", "accepted"),
                "source_id": source,
                "target_id": target,
                "ledger": str(ledger_path.relative_to(ROOT)),
                "source_family": kind,
                "date": {k: link.get(k) for k in ("known_by_date", "actual_receipt_date", "receipt_date_supported", "knowledge_date_basis") if k in link},
                "scope": scope_of(link),
                "training_export_ready": link.get("training_export_ready"),
                "evidence": link.get("evidence", []),
                "accepted_record": link,
            })


def legacy_edge_rows(records: OrderedDict[str, dict[str, Any]], data: dict[str, Any], path: Path, accounting: dict[str, Any] | None = None, audit: dict[str, dict[str, Any]] | None = None) -> None:
    """Retain legacy edges with their adjudicated direction and uncertainty."""
    for edge in data.get("edges", []):
        if accounting is not None: accounting["legacy_edges_seen"] += 1
        source, target = edge.get("source_id"), edge.get("target_id")
        relation = edge.get("relationship")
        if not source or not target or not relation:
            if accounting is not None: accounting["unmapped_relationships"] += 1
            continue
        if relation == "replies_to":
            sd, td = (audit or {}).get(source, {}).get("direction"), (audit or {}).get(target, {}).get("direction")
            # Legacy arrows point from the REPLY to its antecedent. A received
            # correspondent reply is not a question answered by the older CD letter.
            kind = "direct_pair" if (sd, td) == ("from_darwin", "to_darwin") else "reverse_reply"
        else:
            kind = {"knowledge_before": "knowledge"}.get(relation, "reference_observation")
        scope = {"legacy_relationship": relation, "receipt_constraints": edge.get("receipt_constraints")}
        question, answer = (target, source) if relation == "replies_to" else (source, target)
        key = (kind, question, answer, json.dumps(scope, sort_keys=True))
        records.setdefault("|".join(key), {
            "record_kind": kind,
            "status": edge.get("review_status", "reviewed"),
            "source_id": question,
            "target_id": answer,
            "question_id": question if kind == "direct_pair" else None,
            "response_id": answer if kind == "direct_pair" else None,
            "ledger": str(path.relative_to(ROOT)),
            "source_family": "1828-1836 legacy",
            "date": {k: edge.get(k) for k in ("exact_receipt_date",) if k in edge},
            "scope": scope,
            "direction_policy": "legacy edge retained; reply direction is not reinterpreted by inventory",
            "evidence": edge.get("evidence", []),
            "accepted_record": edge,
        })


def legacy_disposition_rows(rows: OrderedDict[str, dict[str, Any]], data: dict[str, Any], path: Path, audit: dict[str, dict[str, Any]]) -> None:
    for item in data.get("reviewed_letters", []):
        ident = item.get("letter_id")
        if not ident:
            continue
        a = audit.get(ident, {})
        outcome = item.get("outcome", "unclassified")
        held = any(x in outcome.lower() for x in ("ambiguous", "uncertain", "needs_review", "hold"))
        state = "held" if held else "genuine_excluded"
        rows.setdefault(f"legacy|{ident}", {
            "record_kind": "letter_disposition",
            "letter_id": ident,
            "state": state,
            "disposition": outcome,
            "voice": "Darwin" if a.get("direction") == "from_darwin" else "correspondent",
            "source_family": "1828-1836 legacy",
            "ledger": str(path.relative_to(ROOT)),
            "paragraphs_read": [],
            "scope": {"review_status": item.get("review_status"), "target_body_read_in_full": item.get("target_body_read_in_full"), "classification": a.get("classification"), "date_assessment": {k: a.get(k) for k in ("xml_earliest", "xml_latest", "date_structure", "source_date_flags")}},
            "source": source_ref({"letter_id": ident, "metadata_audit": a}, ident),
            "training_export_ready": False,
            "synthetic_prompt": False,
        })


def disposition_rows(rows: OrderedDict[str, dict[str, Any]], data: dict[str, Any], ledger_path: Path, family: str, accounting: dict[str, Any] | None = None) -> None:
    for item in data.get("letter_adjudications", []):
        if accounting is not None: accounting["letter_adjudications_seen"] += 1
        ident = item.get("letter_id")
        if not ident:
            continue
        src = source_ref(next((x for x in data.get("sources", []) if x.get("letter_id") == ident), {}), ident)
        disposition = item.get("disposition", "unclassified")
        voice = item.get("voice")
        text = disposition.lower()
        voice_text = str(voice or "").lower()
        darwin_voice = ("darwin" in voice_text and "correspondent" not in voice_text and "reported" not in voice_text) or text.startswith("individual_darwin") or text.startswith("scoped_direct")
        genuine_exclusion = any(x in text for x in ("prior_adjudicated", "outside_", "not_admitted", "missing_prompt", "missing_input", "incoming_context_only", "exclude_", "reported_substance"))
        held = any(x in text for x in ("held", "hold_", "unresolved", "unavailable", "broad_date", "date_and_source_requirements"))
        authored = darwin_voice and any(x in text for x in ("grounding", "response_candidate", "scoped_response", "darwin_scoped_reply"))
        state = "candidate_authored_grounding" if authored else ("held" if held else ("genuine_excluded" if genuine_exclusion else "candidate_authored_grounding" if darwin_voice else "genuine_excluded"))
        key = f"{ident}|{json.dumps(item.get('voice_spans', item.get('voice_paragraphs', [])), sort_keys=True)}|{item.get('date_assessment')}"
        rows.setdefault(key, {
            "record_kind": "letter_disposition",
            "letter_id": ident,
            "state": state,
            "disposition": disposition,
            "voice": voice,
            "source_family": family,
            "ledger": str(ledger_path.relative_to(ROOT)),
            "paragraphs_read": item.get("paragraphs_read", []),
            "scope": {k: item.get(k) for k in ("body_text_scope", "voice_paragraphs", "voice_spans", "excluded_paragraphs", "exclusion_reason", "date_assessment", "original_date_label", "effective_period_eligible") if k in item},
            "source": src,
            "training_export_ready": item.get("training_export_ready"),
            "conversion_status": "export_clearance_pending" if state == "candidate_authored_grounding" and item.get("training_export_ready") is not True else state,
        })


def build_inventory() -> dict[str, Any]:
    pins: OrderedDict[str, dict[str, Any]] = OrderedDict()
    relation_records: OrderedDict[str, dict[str, Any]] = OrderedDict()
    letter_records: OrderedDict[str, dict[str, Any]] = OrderedDict()
    accounting = {"direct_reply_pairs_seen": 0, "correspondent_replies_seen": 0, "cross_correspondent_knowledge_seen": 0, "legacy_edges_seen": 0, "source_records_seen": 0, "letter_adjudications_seen": 0, "unmapped_relationships": 0}

    routing = ROOT / "reports/raft-prep/candidates/cumulative-export-input-routing.luna.json"
    if routing.exists():
        add_pin(pins, routing, "cumulative export input routing")

    legacy = ROOT / "data/annotations/correspondence_links.json"
    legacy_audit = load_jsonl_index(ROOT / "reports/1828-1836/audit.jsonl")
    retained_prior_keys: list[str] = []
    if legacy.exists():
        add_pin(pins, legacy, "accepted legacy graph/relation definitions")
        legacy_data = load(legacy)
        legacy_edge_rows(relation_records, legacy_data, legacy, accounting, legacy_audit)
        legacy_disposition_rows(letter_records, legacy_data, legacy, legacy_audit)
        for item in legacy_data.get("retained_prior_relationships", []):
            retained_prior_keys.append(json.dumps(item, sort_keys=True))
        for node in legacy_data.get("unlocated_nodes", []):
            ident = node.get("letter_id") or node.get("id")
            if ident:
                letter_records.setdefault(f"unlocated|{ident}", {
                    "record_kind": "unlocated_reference", "letter_id": ident,
                    "state": "genuine_excluded", "disposition": "unlocated_node",
                    "voice": None, "source_family": "1828-1836 legacy",
                    "ledger": str(legacy.relative_to(ROOT)), "scope": node,
                    "source": source_ref({"letter_id": ident}, ident),
                    "training_export_ready": False, "synthetic_prompt": False,
                })
        add_pin(pins, ROOT / "reports/1828-1836/audit.jsonl", "legacy date/direction audit")
    receipt = ROOT / "reports/1828-1836/receipt_evidence.json"
    if receipt.exists():
        add_pin(pins, receipt, "legacy receipt/known-by evidence")

    graph = ROOT / "reports/1837-1843/correspondence-map/graph.json"
    if graph.exists():
        add_pin(pins, graph, "composed 1837-1843 graph")
        gd = load(graph)
        for edge in gd.get("edges", []):
            if edge.get("type") not in {"replies_to", "knowledge_before"}:
                continue
            if edge["type"] == "knowledge_before":
                pair = {**edge, "incoming_id": edge["source"], "witness_id": edge["target"], "status": "accepted_graph_edge"}
                field = "cross_correspondent_knowledge"
            elif edge.get("is_Darwin_response") is True:
                pair = {**edge, "incoming_id": edge["target"], "outgoing_id": edge["source"], "status": "accepted_graph_edge"}
                field = "direct_reply_pairs"
            else:
                pair = {**edge, "antecedent_id": edge["target"], "response_id": edge["source"], "status": "accepted_graph_edge"}
                field = "correspondent_replies"
            relationship_rows(relation_records, {field: [pair]}, graph, "1837-1843 graph", accounting)

    for period, path, data in period_ledgers(pins):
        relationship_rows(relation_records, data, path, period, accounting)
        disposition_rows(letter_records, data, path, period, accounting)
    for path, data in beagle_ledgers(pins):
        relationship_rows(relation_records, data, path, "Beagle", accounting)
        disposition_rows(letter_records, data, path, "Beagle", accounting)
        retained_prior_keys.extend(json.dumps(x, sort_keys=True) for x in data.get("retained_prior_relationships", []))

    reconciliation = ROOT / "data/annotations/reconciliation"
    for path in sorted(reconciliation.glob("*.primary.json")):
        data = load(path)
        add_pin(pins, path, "accepted reconciliation supplement")
        relationship_rows(relation_records, data, path, "reconciliation", accounting)
        disposition_rows(letter_records, data, path, "reconciliation", accounting)

    # Regression guards for the two legacy orientations and the composed graph.
    def assert_direct(question: str, response: str) -> None:
        assert any(x.get("record_kind") == "direct_pair" and x.get("question_id") == question and x.get("response_id") == response for x in relation_records.values()), (question, response)
    for q, a in (("DCP-LETT-296", "DCP-LETT-302"), ("DCP-LETT-288", "DCP-LETT-306"), ("DCP-LETT-105", "DCP-LETT-107"), ("DCP-LETT-125", "DCP-LETT-135A"), ("DCP-LETT-143", "DCP-LETT-144"), ("DCP-LETT-345", "DCP-LETT-346")):
        assert_direct(q, a)
    assert not any(x.get("record_kind") == "direct_pair" and x.get("question_id") == "DCP-LETT-312" and x.get("response_id") == "DCP-LETT-310" for x in relation_records.values())
    assert any(x.get("record_kind") == "reverse_reply" and x["source_id"] == "DCP-LETT-310" and x["target_id"] == "DCP-LETT-312" for x in relation_records.values())
    assert not any(x.get("record_kind") == "direct_pair" and str(x.get("question_id", "")).startswith("UNLOCATED") for x in relation_records.values())

    policy = ROOT / "docs/raft-export-content-policy.md"
    add_pin(pins, policy, "export policy")
    return {
        "schema_version": 1,
        "status": "dry_run_inventory",
        "revision": REVISION,
        "training_or_export_performed": False,
        "darwin_0_written": False,
        "input_pins": list(pins.values()),
        "relationship_records": list(relation_records.values()),
        "letter_records": list(letter_records.values()),
        "unlocated_nodes_are_excluded": True,
        "counts": {
            "relationships": len(relation_records),
            "letter_dispositions": len(letter_records),
            "eligible_candidates": sum(x["state"] == "candidate_authored_grounding" and x.get("training_export_ready") is True for x in letter_records.values()),
            "candidate_authored_grounding": sum(x["state"] == "candidate_authored_grounding" for x in letter_records.values()),
            "genuine_excluded": sum(x["state"] == "genuine_excluded" for x in letter_records.values()),
            "held": sum(x["state"] == "held" for x in letter_records.values()),
        },
        "relationship_accounting": {**accounting, "relationship_records_emitted_after_dedup": len(relation_records), "letter_records_emitted_after_dedup": len(letter_records)},
        "dedup_key": "relationship: (record_kind, source_id, target_id, canonical scoped sections/fragments); letter: (letter_id, voice scope, date policy)",
        "retained_prior_relationships": {
            "count_seen": len(retained_prior_keys),
            "unique_declarations": len(set(retained_prior_keys)),
            "handling": "prior relationship declarations are audit-only and never appended; stable relation keys from authoritative ledgers win",
        },
        "routing_input": str(routing.relative_to(ROOT)) if routing.exists() else None,
        "guardrails": [
            "Incoming -> Darwin direct pairs are questions and Darwin outgoing IDs are responses; reverse correspondent replies and knowledge witnesses never become Darwin answers.",
            "Known-by, receipt, composition and response dates remain separate; null or uncertain dates are surfaced and never guessed.",
            "Unlocated/reference nodes and candidate followups are not converted into synthetic prompts.",
            "retained_prior_relationships and repeated context sources are deduplicated by stable IDs plus actual scope.",
            "Body text is not copied by this inventory; headings, notes, bibliography and unresolved apparatus remain outside eventual content until separately cleared."
        ],
    }


def write_dry_run(path: Path | None = None) -> dict[str, Any]:
    report = build_inventory()
    destination = path or ROOT / "reports/raft-prep/candidates/raft-export-inventory.dry-run.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return {"path": str(destination.relative_to(ROOT)), "counts": report["counts"], "inputs": len(report["input_pins"]), "written_to_darwin_0": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(json.dumps(write_dry_run(args.output), ensure_ascii=False))

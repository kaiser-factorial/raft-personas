"""Validate parent decisions and build the separate 1837–1843 evidence map.

No relationship is inferred here. The curated ledger is the authority; reviewer
proposals are checked for coverage and quotation accuracy, not auto-promoted.
"""

import hashlib
import json
from collections import Counter

from fetch_metadata import ROOT

BASE = ROOT / "reports/1837-1843"
REVIEW = BASE / "correspondent-review"
DEST = BASE / "correspondence-map"
ANNOTATIONS = ROOT / "data/annotations/expansion_1837_1843.json"
EXTENSION = ROOT / "data/annotations/henslow_lyell_1837_1843.json"
NEXT_REVIEW = BASE / "henslow-lyell"
REMAINING = BASE / "remaining-review"
REMAINING_ANNOTATIONS = ROOT / "data/annotations/remaining_1837_1843"


def remaining_sources():
    if not REMAINING_ANNOTATIONS.exists():
        return []
    batches = sorted(REMAINING_ANNOTATIONS.glob("batch-*.json"))
    assert [p.stem for p in batches] == [f"batch-{n:02d}" for n in range(1, 20)], "Remaining review is incomplete."
    return batches + [REMAINING_ANNOTATIONS / "supplementary.json"]


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_letters():
    letters = {}
    paths = [BASE / "pilot/letters.jsonl", REVIEW / "letters.jsonl", REVIEW / "seed-context.letters.jsonl"]
    if EXTENSION.exists():
        paths.extend([NEXT_REVIEW / "letters.jsonl", NEXT_REVIEW / "context.letters.jsonl"])
    if remaining_sources() and (REMAINING / "letters.jsonl").exists():
        paths.append(REMAINING / "letters.jsonl")
    for path in paths:
        if not path.exists():
            continue
        for row in map(json.loads, path.read_text().splitlines()):
            if row["id"] in letters:
                assert letters[row["id"]]["source"]["sha256"] == row["source"]["sha256"]
                assert letters[row["id"]]["paragraphs"] == row["paragraphs"]
            letters[row["id"]] = row
    db_path = ROOT / "data/letters.sqlite"
    if db_path.exists():
        import sqlite3
        import zlib
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT id, record_blob FROM letters WHERE periods_json LIKE ?", ('%"1837-1843"%',))
        for lid, blob in cur.fetchall():
            if lid not in letters:
                letters[lid] = json.loads(zlib.decompress(blob).decode("utf-8"))
        conn.close()
    return letters


def load_decisions():
    """Compose append-only review ledgers without rewriting prior decisions."""
    decisions = read(ANNOTATIONS)
    decisions["reviewed_record_ids"] = list(decisions["full_read_ids"])
    decisions["body_unavailable_ids"] = []
    decisions["non_individual_voice_ids"] = []
    sources = [ANNOTATIONS]
    for source in ([EXTENSION] if EXTENSION.exists() else []) + remaining_sources():
        new = read(source)
        assert new["status"] == "parent_adjudicated"
        if source.parent == REMAINING_ANNOTATIONS:
            assert not (set(decisions["reviewed_record_ids"]) & set(new["reviewed_record_ids"])), source
        for key in ("full_read_ids", "reviewed_record_ids", "body_unavailable_ids", "non_individual_voice_ids",
                    "additional_exact_date_review_ids", "additional_period_hold_ids", "voice_held_ids"):
            decisions[key] = sorted(set(decisions.get(key, [])) | set(new.get(key, [])))
        for key in ("direct_reply_pairs", "cross_correspondent_knowledge", "correspondent_replies", "dated_sections",
                    "reference_observations", "receipt_events", "within_day_events", "rejected_or_candidate_links", "corrections",
                    "letter_adjudications", "date_evidence"):
            decisions.setdefault(key, []).extend(new.get(key, []))
        decisions["individual_limits"].update(new.get("individual_limits", {}))
        decisions["method"] += " " + new["method"]
        sources.append(source)
    return decisions, sources


def validate_participants(record, inc, out, letters):
    """Keep personal identities intact while permitting evidenced official roles."""
    incoming = {p["attributes"]["key"] for p in inc["sender_evidence"]}
    recipient = {p["attributes"]["key"] for p in out["recipient_evidence"]}
    override = record.get("participant_match_override")
    if incoming == recipient:
        assert override is None
        return
    assert override and override.get("evidence"), (inc["id"], out["id"], "Unevidenced participant mismatch")
    check_quotes(override["evidence"], letters)
    if override["policy"] == "named_signatory_for_catalogued_institution":
        assert incoming == {override["incoming_institution_key"]}
        assert recipient == {override["outgoing_recipient_key"]}
        assert any(q["letter_id"] == inc["id"] and override["signatory"] in q["quote"] for q in override["evidence"])
    else:
        assert override["policy"] == "documented_institutional_representatives"
        assert incoming == set(override["incoming_sender_keys"])
        assert recipient == set(override["outgoing_recipient_keys"])
        assert override["scope_incoming_id"] == inc["id"] and override["scope_outgoing_id"] == out["id"]
        assert override["people_are_not_aliases"] is True and override["institution"] in ("Treasury", "Admiralty")


def adjudication_scopes(decisions, letters):
    scopes = {}
    fields = ("source_kind", "body_text_scope", "voice_spans", "voice_paragraphs", "excluded_paragraphs",
              "exclusion_reason", "editorial_paraphrase_excluded", "body_segments", "author_segments",
              "voice_eligible_text", "effective_period_eligible", "period_hold_reason", "individual_authorship_unresolved",
              "language", "english_voice_training_eligible", "translation_status", "supplemental_author_text_present",
              "supplemental_author_text_note")
    for row in decisions.get("letter_adjudications", []):
        scope = scopes.setdefault(row["letter_id"], {})
        scope.update({k: row[k] for k in fields if k in row})
    for ident, scope in scopes.items():
        paragraphs = {p["body_paragraph"]: p["text"] for p in letters[ident]["paragraphs"]}
        for span in scope.get("voice_spans", []):
            assert paragraphs[span["body_paragraph"]][span["char_start"]:span["char_end"]] == span["text"]
        assert set(scope.get("voice_paragraphs", [])) <= set(paragraphs)
        assert not set(scope.get("voice_paragraphs", [])) & set(scope.get("excluded_paragraphs", []))
    return scopes


def check_quotes(value, letters):
    checks = []
    if isinstance(value, dict):
        if "letter_id" in value and "quote" in value:
            row = letters[value["letter_id"]]
            if "body_paragraph" in value:
                paragraph = next(p for p in row["paragraphs"] if p["body_paragraph"] == value["body_paragraph"])
                text = paragraph["text"]
                locator = paragraph["locator"]
            elif "header" in value.get("locator", ""):
                text = " ".join(row["header_text"])
                locator = value["locator"]
            elif "summary" in value.get("locator", ""):
                text = row["editorial_summary"]
                locator = value["locator"]
            elif "footnote" in value.get("locator", "") or "editorial" in value.get("locator", ""):
                text = row["editorial_footnotes"]
                locator = value["locator"]
            else:
                raise ValueError(f"Unlocated quote: {value}")
            if value["quote"] not in text:
                raise ValueError(f"Quote not found: {value['letter_id']}, {locator}: {value['quote']}")
            checks.append({"letter_id": value["letter_id"], "locator": locator, "exact_quote_verified": True})
        for child in value.values():
            checks.extend(check_quotes(child, letters))
    elif isinstance(value, list):
        for child in value:
            checks.extend(check_quotes(child, letters))
    return checks


def can_condition(pair, response_id, body_paragraph, sections, char_offset=None):
    """Applicability inside the matched response; no general same-day inference."""
    if pair["outgoing_id"] != response_id:
        return False
    if pair["response_scope"] == "single_date_surviving_body":
        return True
    for name in pair["response_sections"]:
        section = sections[name]
        if body_paragraph in section["paragraphs"]:
            return True
        if char_offset is not None and any(f["body_paragraph"] == body_paragraph
                                          and f["char_start"] <= char_offset < f["char_end"]
                                          for f in section.get("paragraph_fragments", [])):
            return True
    return False


def validate_section_coverage(sections, letters):
    """Every source character belongs to one section, including mixed blocks."""
    for ident in {s["letter_id"] for s in sections.values()}:
        by_paragraph = {p["body_paragraph"]: [] for p in letters[ident]["paragraphs"]}
        texts = {p["body_paragraph"]: p["text"] for p in letters[ident]["paragraphs"]}
        for section in sections.values():
            if section["letter_id"] != ident:
                continue
            for number in section["paragraphs"]:
                by_paragraph[number].append((0, len(texts[number])))
            for fragment in section.get("paragraph_fragments", []):
                number = fragment["body_paragraph"]
                start, end = fragment["char_start"], fragment["char_end"]
                assert 0 <= start < end <= len(texts[number])
                assert texts[number][start:end] == fragment["text"]
                by_paragraph[number].append((start, end))
        for number, intervals in by_paragraph.items():
            cursor = 0
            for start, end in sorted(intervals):
                assert start == cursor, (ident, number, intervals)
                cursor = end
            assert cursor == len(texts[number]), (ident, number, intervals)


def write_corpus_status(expansion, decision_sources):
    old = read(ROOT / "reports/correspondence-map/summary.json")
    old_count = old["established_prompt_pairs"]
    status = {
        "established_prompt_pairs_across_reviewed_batches": old_count + expansion["single_date_direct_reply_links"],
        "established_prompt_pairs_definition": "Conservative single-date surviving incoming/Darwin-body relationships, not export-ready RAFT examples. Section-dependent relationships are counted separately below.",
        "confirmed_direct_reply_links_including_dated_sections": old_count + expansion["confirmed_direct_reply_links"],
        "distinct_Darwin_response_letters_including_dated_sections": old_count + expansion["distinct_Darwin_response_letters"],
        "additional_section_dependent_links": expansion["section_dependent_direct_reply_links"],
        "additional_section_dependent_response_letters": expansion["section_dependent_response_letters"],
        "batches": [
            {"period": "1828-1836", "single_date_pairs": old_count,
             "report": "reports/correspondence-map/README.md", "scope": "unchanged earlier review"},
            {"period": "1837-1843", "single_date_pairs": expansion["single_date_direct_reply_links"],
             "direct_links_including_sections": expansion["confirmed_direct_reply_links"],
             "distinct_Darwin_responses": expansion["distinct_Darwin_response_letters"],
             "full_read_count": expansion["full_read_count"],
             "report": ("reports/1837-1843/remaining-review/README.md" if remaining_sources() else "reports/1837-1843/henslow-lyell/README.md" if EXTENSION.exists()
                        else "reports/1837-1843/correspondent-review/README.md")}],
        "previously_identified_direct_reply_held_for_outgoing_date": "DCP-LETT-135 -> DCP-LETT-139; additional to all counts above",
        "old_graph_retained_as_period_specific": True,
        "combined_training_export_performed": False,
        "unpaired_count_limit": f"{expansion['unreviewed_source_record_count']} source records remain unreviewed. {expansion['reviewed_outgoing_without_identified_surviving_prompt']} reviewed, period-eligible individual Darwin bodies lack an identified surviving prompt. Held dates, unavailable text and excluded authorship are separate categories.",
        "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in
                   [ROOT / "reports/correspondence-map/summary.json", DEST / "summary.json"] + decision_sources],
    }
    write(ROOT / "reports/corpus-status.json", status)
    return status


def main():
    decisions, decision_sources = load_decisions()
    letters = load_letters()
    audit = {r["id"]: r for r in map(json.loads, (BASE / "audit.jsonl").read_text().splitlines())}
    assert set(decisions["reviewed_record_ids"]) == set(letters)
    assert set(decisions["full_read_ids"]) == set(letters) - set(decisions["body_unavailable_ids"])
    evidence_letters = dict(letters)
    if remaining_sources():
        # Boundary proposals cite the earlier frozen corpus but add no new nodes.
        for row in map(json.loads, (ROOT / "reports/body-date-search-37-337/letters.jsonl").read_text().splitlines()):
            evidence_letters.setdefault(row["id"], row)
        assert set(letters) == set(audit)
        assert len(read(REMAINING / "selection.json")["target_ids"]) == 363
    for row in letters.values():
        assert digest(ROOT / row["source"]["path"]) == row["source"]["sha256"]
        assert row["id"] in audit
    for row in audit.values():
        assert digest(ROOT / row["provenance"]["xml_path"]) == row["provenance"]["xml_sha256"]
    baseline = read(BASE / "verification/baseline_hashes.json")["files"]
    for source in baseline:
        assert digest(ROOT / source["path"]) == source["sha256"], source["path"]
    if EXTENSION.exists():
        baseline += read(NEXT_REVIEW / "baseline_hashes.json")["files"]
        for source in baseline:
            assert digest(ROOT / source["path"]) == source["sha256"], source["path"]
    if remaining_sources():
        baseline += read(REMAINING / "baseline_hashes.json")["files"]
        for source in baseline:
            assert digest(ROOT / source["path"]) == source["sha256"], source["path"]

    reviewer_checks = []
    groups = [(REVIEW, "emma"), (REVIEW, "kemp")]
    if EXTENSION.exists():
        groups += [(NEXT_REVIEW, "henslow"), (NEXT_REVIEW, "lyell")]
    for folder, group in groups:
        packet = read(folder / f"{group}.packet.json")
        report = read(folder / f"{group}.review.json")
        for direction in ("outgoing", "incoming"):
            reviews = report[f"{direction}_reviews"]
            assert Counter(r["letter_id"] for r in reviews) == Counter(packet[f"{direction}_ids"])
            for row in reviews:
                if row["letter_id"] in decisions["body_unavailable_ids"]:
                    assert row["body_read_in_full"] is False
                    assert row["source_record_read_in_full"] is True
                else:
                    assert row["body_read_in_full"] is True
                assert row["paragraphs_read"] == [p["body_paragraph"] for p in letters[row["letter_id"]]["paragraphs"]]
        reviewer_checks.append({"report": f"{group}.review.json", "quotes": len(check_quotes(report, letters)), "full_coverage": True})
    for name in ("section-dates", "seed-context"):
        reviewer_checks.append({"report": f"{name}.review.json", "quotes": len(check_quotes(read(REVIEW / f"{name}.review.json"), letters))})
    if EXTENSION.exists():
        for name in ("chronology", "context"):
            reviewer_checks.append({"report": f"{name}.review.json", "quotes": len(check_quotes(read(NEXT_REVIEW / f"{name}.review.json"), letters))})
        reviewer_checks.append({"report": "henslow-712.check.json", "quotes": len(check_quotes(read(NEXT_REVIEW / "henslow-712.check.json"), letters))})
        chronology = read(NEXT_REVIEW / "chronology.review.json")
        packet_ids = {
            r["id"] for r in map(json.loads, (NEXT_REVIEW / "letters.jsonl").read_text().splitlines())}
        assert set(chronology["source_record_read_ids"]) == packet_ids
        assert set(chronology["full_body_read_ids"]) == packet_ids - set(decisions["body_unavailable_ids"])
        assert {r["letter_id"] for r in chronology["record_reviews"]} == packet_ids
        for row in chronology["record_reviews"]:
            has_body = row["letter_id"] not in decisions["body_unavailable_ids"]
            expected_paragraphs = [p["body_paragraph"] for p in letters[row["letter_id"]]["paragraphs"]] if has_body else []
            assert row["paragraphs_read"] == expected_paragraphs
            assert row["body_read_in_full"] == has_body
        context = read(NEXT_REVIEW / "context.packet.json")
        context_review = read(NEXT_REVIEW / "context.review.json")
        assert set(context_review["full_read_ids"]) == {
            r["id"] for r in context["incoming_letters"] + context["Darwin_witness_letters"]}
        # Also validate extension-only date evidence and per-letter dossiers,
        # which are deliberately not merged into the prior phase's ledger.
        extension_quote_checks = check_quotes(read(EXTENSION), letters)
    if remaining_sources():
        from remaining_review_helpers import validate_review
        for source in remaining_sources():
            ledger = read(source)
            for input_source in ledger["inputs"]:
                assert digest(ROOT / input_source["path"]) == input_source["sha256"], input_source["path"]
            if source.stem.startswith("batch-"):
                packet = read(REMAINING / "packets" / source.name)
                notes = read(REMAINING / "parent-reading" / source.name)
                report = read(REMAINING / "reviews" / source.name)
                assert ledger["reviewed_record_ids"] == packet["target_ids"]
                assert set(ledger["full_read_ids"]) == set(packet["target_ids"]) - set(ledger["body_unavailable_ids"])
                assert notes["status"] == "parent_full_source_read_complete"
                expected = set(packet["target_ids"] + packet["context_ids"])
                assert set(notes["source_record_ids_read"]) >= expected
                assert set(notes["body_ids_read"]) >= expected - set(ledger["body_unavailable_ids"])
                assert set(notes["record_notes"]) >= expected
                proposal_key = lambda r: (r["source_id"], r["target_id"], r["relationship"])
                assert Counter(map(proposal_key, report["proposed_links"])) == Counter(map(proposal_key, ledger["proposal_adjudications"]))
                for row in ledger["letter_adjudications"]:
                    assert row["original_metadata"] == audit[row["letter_id"]]
                    assert row["source"] == letters[row["letter_id"]]["source"]
                reviewer_checks.append(validate_review(REMAINING / "reviews" / source.name))
            check_quotes(ledger, evidence_letters)
    parent_quotes = check_quotes(decisions, evidence_letters)
    scopes = adjudication_scopes(decisions, letters)
    period_holds = set(decisions.get("additional_period_hold_ids", []))
    voice_holds = set(decisions.get("voice_held_ids", []))
    def period_eligible(ident):
        return audit[ident]["period_selection_eligible"] and ident not in period_holds
    sections = {s["id"]: s for s in decisions["dated_sections"]}
    validate_section_coverage(sections, letters)

    edges, knowledge = [], []
    pair_keys = set()
    for pair in decisions["direct_reply_pairs"]:
        source, target = pair["incoming_id"], pair["outgoing_id"]
        assert (source, target) not in pair_keys
        pair_keys.add((source, target))
        inc, out = audit[source], audit[target]
        assert source in decisions["full_read_ids"] and target in decisions["full_read_ids"]
        assert target not in decisions["non_individual_voice_ids"]
        assert target not in voice_holds
        assert inc["direction"] == "to_darwin" and out["direction"] == "from_darwin"
        assert period_eligible(source) and period_eligible(target)
        assert not inc["metadata_multiple_senders"] and not out["metadata_multiple_senders"]
        validate_participants(pair, inc, out, letters)
        assert inc["xml_latest"] <= pair["known_by_date"]
        if pair["response_scope"] == "single_date_surviving_body":
            assert out["xml_earliest"] == out["xml_latest"] == pair["known_by_date"]
            assert not out["exact_order_needs_review"]
            assert target not in decisions["additional_exact_date_review_ids"]
        else:
            assert all(sections[s]["letter_id"] == target for s in pair["response_sections"])
            assert min(sections[s]["date"] for s in pair["response_sections"]) == pair["known_by_date"]
        edge_id = f"reply:{target}:{source}"
        scope = {"response_scope": pair["response_scope"], "response_sections": pair["response_sections"],
                 "response_paragraphs": [p["body_paragraph"] for p in letters[target]["paragraphs"]
                                         if can_condition(pair, target, p["body_paragraph"], sections)
                                         and p["body_paragraph"] not in scopes.get(target, {}).get("excluded_paragraphs", [])],
                 "response_fragments": [f for s in pair["response_sections"] for f in sections[s].get("paragraph_fragments", [])]}
        edges.append({"id": edge_id, "type": "replies_to", "source": target, "target": source,
                      "is_Darwin_response": True, "evidence": pair["evidence"], "rationale": pair["rationale"],
                      "participant_match_override": pair.get("participant_match_override"),
                      "relationship_subtype": pair.get("relationship_subtype"), **scope})
        knowledge.append({"type": "knowledge_before", "source": source, "target": target,
                          "known_by_date": pair["known_by_date"], "actual_receipt_date": pair.get("actual_receipt_date"),
                          "basis": edge_id, "evidence": pair["evidence"], **scope})
    for record in decisions["cross_correspondent_knowledge"]:
        source, target = record["incoming_id"], record["witness_id"]
        assert audit[source]["direction"] == "to_darwin" and audit[target]["direction"] == "from_darwin"
        assert source in decisions["full_read_ids"] and target in decisions["full_read_ids"]
        assert target not in decisions["non_individual_voice_ids"]
        assert target not in voice_holds and period_eligible(target)
        assert audit[source]["xml_earliest"] <= record["known_by_date"]
        if record.get("witness_date_policy") == "conservative_latest_possible_writing_date":
            assert audit[target]["xml_latest"] == record["known_by_date"]
        elif record.get("witness_date_policy") == "conservative_editorial_year_upper_bound":
            assert target in decisions["additional_exact_date_review_ids"]
            assert record["date_upper_bound_basis"] and record["evidence"]
            assert record["known_by_date"] >= audit[target]["xml_latest"]
            assert record["known_by_date"].endswith("-12-31")
            assert record["known_by_date"][:4] == record["original_assigned_date"][:4]
        else:
            assert audit[target]["xml_earliest"] == audit[target]["xml_latest"] == record["known_by_date"]
        knowledge.append({"type": "knowledge_before", "source": source, "target": target,
                          "known_by_date": record["known_by_date"], "direct_prompt": False,
                          "witness_date_policy": record.get("witness_date_policy", "resolved_single_writing_date"),
                          "witness_xml_constraints": audit[target]["sent_date_constraints"],
                          "source_raw_period_eligible": audit[source]["period_selection_eligible"],
                          "actual_receipt_date": record.get("actual_receipt_date"),
                          "evidence": record["evidence"], "rationale": record["rationale"],
                          "witness_paragraphs": record.get("witness_paragraphs"),
                          "basis": "parent-reviewed cross-correspondent content and attribution"})
    reverse_keys = set()
    for record in decisions["correspondent_replies"]:
        source, target = record["response_id"], record["antecedent_id"]
        assert (source, target) not in reverse_keys
        reverse_keys.add((source, target))
        assert audit[source]["direction"] == "to_darwin" and audit[target]["direction"] == "from_darwin"
        if record.get("participant_match_override"):
            validate_participants(record, audit[source], audit[target], letters)
        edges.append({"type": "replies_to", "source": source, "target": target,
                      "is_Darwin_response": False, "activates_Darwin_knowledge": False,
                      "source_raw_period_eligible": audit[source]["period_selection_eligible"],
                      "evidence": record["evidence"], "rationale": record["rationale"],
                      "participant_match_override": record.get("participant_match_override")})
    edges.extend(knowledge)
    edge_keys = Counter((e["type"], e["source"], e["target"]) for e in edges)
    assert all(count == 1 for count in edge_keys.values()), "Duplicate relationship in composed map."

    responses = {p["outgoing_id"] for p in decisions["direct_reply_pairs"]}
    full_read = set(decisions["full_read_ids"])
    reviewed_out = {i for i in full_read if audit[i]["direction"] == "from_darwin"}
    reviewed_safe_out = {i for i in reviewed_out if audit[i]["period_selection_eligible"]}
    individual_eligible = {i for i in reviewed_out if period_eligible(i)} - set(decisions["non_individual_voice_ids"]) - voice_holds
    individual_grounding = individual_eligible - responses
    dated = {s["letter_id"] for s in sections.values()}
    nodes = []
    for ident, row in audit.items():
        outgoing = row["direction"] == "from_darwin"
        matches = [e for e in knowledge if e["source"] == ident]
        held = row["exact_order_needs_review"] or ident in decisions["additional_exact_date_review_ids"] or not period_eligible(ident)
        role = ("response_candidate" if ident in responses else "dated_grounding_candidate") if outgoing and ident in letters else ("unreviewed_outgoing" if outgoing else "incoming_context_only")
        if not period_eligible(ident):
            role = "period_held_outgoing" if outgoing else "period_held_incoming_context"
        if ident in voice_holds:
            role = "authorship_held_not_Darwin_voice"
        if ident in decisions["body_unavailable_ids"]:
            role = "source_record_only_no_transcription"
        elif ident in decisions["non_individual_voice_ids"]:
            role = "joint_document_not_individual_Darwin_voice"
        nodes.append({"id": ident, "direction": row["direction"], "role": role,
                      "source_record_reviewed": ident in letters,
                      "body_read_in_full": ident in full_read, "raw_period_eligible": row["period_selection_eligible"],
                      "effective_period_eligible": period_eligible(ident),
                      "individual_Darwin_voice_eligible": ident in individual_eligible,
                      "text_scope": scopes.get(ident, {}),
                      "original_csv": row["original_csv"], "original_xml_constraints": row["sent_date_constraints"],
                      "metadata_provenance": row["provenance"],
        "body_source": letters[ident]["source"] if ident in letters else None,
                      "whole_letter_scalar_date": None if held or ident in dated else row["xml_earliest"],
                      "known_by_date": min(e["known_by_date"] for e in matches) if matches else None,
                      "knowledge_attestations": matches,
                      "incoming_is_Darwin_voice": False,
                      "training_export_ready": False,
                      "limits": decisions["individual_limits"].get(ident),
                      "same_day_rule": "Only established witness/section order is available on the known-by day; generic same-day retrieval requires separate ordering evidence."})

    singles = [p for p in decisions["direct_reply_pairs"] if p["response_scope"] == "single_date_surviving_body"]
    multi = [p for p in decisions["direct_reply_pairs"] if p["response_scope"] == "dated_sections"]
    safe_out = sum(r["direction"] == "from_darwin" and r["period_selection_eligible"] for r in audit.values())
    xml_review = {i for i, r in audit.items() if r["period_selection_eligible"] and r["exact_order_needs_review"]}
    summary = {
        "period": "1837-1843", "reviewed_source_record_count": len(letters), "full_read_count": len(full_read),
        "inventory_record_count": len(audit), "unreviewed_source_record_count": len(audit) - len(letters),
        "Darwin_outgoing_full_read_count": len(reviewed_out), "incoming_full_read_count": len(full_read) - len(reviewed_out),
        "safe_outgoing_full_read_count": len(reviewed_safe_out),
        "source_records_without_transcription": decisions["body_unavailable_ids"],
        "joint_documents_excluded_from_individual_voice": decisions["non_individual_voice_ids"],
        "authorship_held_ids": sorted(voice_holds), "additional_editorial_period_hold_ids": sorted(period_holds),
        "raw_XML_safe_count": sum(r["period_selection_eligible"] for r in audit.values()),
        "raw_XML_held_count": sum(not r["period_selection_eligible"] for r in audit.values()),
        "effective_period_eligible_count": sum(period_eligible(i) for i in audit),
        "effective_period_held_count": sum(not period_eligible(i) for i in audit),
        "eligible_individual_Darwin_body_count": len(individual_eligible),
        "raw_period_held_full_read_incoming_ids": sorted(i for i in full_read if audit[i]["direction"] == "to_darwin" and not audit[i]["period_selection_eligible"]),
        "raw_period_held_reviewed_outgoing_ids": sorted(i for i in letters if audit[i]["direction"] == "from_darwin" and not audit[i]["period_selection_eligible"]),
        "confirmed_direct_reply_links": len(decisions["direct_reply_pairs"]),
        "distinct_Darwin_response_letters": len(responses),
        "single_date_direct_reply_links": len(singles),
        "section_dependent_direct_reply_links": len(multi),
        "section_dependent_response_letters": len({p["outgoing_id"] for p in multi}),
        "cross_correspondent_knowledge_links": len(decisions["cross_correspondent_knowledge"]),
        "incoming_records_with_known_by_evidence": len({e["source"] for e in knowledge}),
        "reverse_reply_links_not_Darwin_outputs": len(decisions["correspondent_replies"]),
        "reviewed_outgoing_without_identified_surviving_prompt": len(individual_grounding),
        "reviewed_grounding_ids": sorted(individual_grounding),
        "safe_outgoing_not_yet_full_read": sum(i not in full_read and i not in decisions["body_unavailable_ids"] and r["direction"] == "from_darwin" and r["period_selection_eligible"] for i, r in audit.items()),
        "safe_outgoing_transcription_unavailable_ids": sorted(i for i in decisions["body_unavailable_ids"] if audit[i]["direction"] == "from_darwin" and audit[i]["period_selection_eligible"]),
        "safe_outgoing_source_records_not_reviewed": sum(i not in letters and r["direction"] == "from_darwin" and r["period_selection_eligible"] for i, r in audit.items()),
        "safe_incoming_source_records_not_reviewed": sum(i not in letters and r["direction"] == "to_darwin" and r["period_selection_eligible"] for i, r in audit.items()),
        "xml_exact_order_review_count": len(xml_review),
        "effective_whole_letter_exact_date_review_count": len(xml_review | set(decisions["additional_exact_date_review_ids"])),
        "training_export_performed": False,
        "count_limit": "All counts are source records or documented relationships, not export-ready RAFT examples. Missing source text is distinct from unread records. Multiple inputs and repeated responses do not multiply distinct response-letter counts. Unpaired means no surviving prompt identified in this review, not proof that no reply was written.",
    }
    write(DEST / "graph.json", {"nodes": nodes, "edges": edges, "dated_sections": decisions["dated_sections"],
                               "within_day_events": decisions["within_day_events"], "receipt_events": decisions["receipt_events"],
                               "reference_observations": decisions["reference_observations"],
                               "date_evidence": decisions.get("date_evidence", []),
                               "rejected_or_candidate_links": decisions["rejected_or_candidate_links"],
                               "decision_sources": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in decision_sources]})
    write(DEST / "summary.json", summary)
    (DEST / "incoming_knowledge_dates.jsonl").write_text("".join(json.dumps(n, ensure_ascii=False) + "\n" for n in nodes if n["direction"] == "to_darwin"))
    review_sources = [REVIEW / f"{n}.review.json" for n in ("emma", "kemp", "section-dates", "seed-context")]
    parent_output = REVIEW / "parent_review.json"
    if EXTENSION.exists():
        review_sources += [NEXT_REVIEW / f"{n}.review.json" for n in ("henslow", "lyell", "chronology", "context")]
        review_sources.append(NEXT_REVIEW / "henslow-712.check.json")
        parent_output = NEXT_REVIEW / "parent_review.json"
    if remaining_sources():
        review_sources += sorted((REMAINING / "reviews").glob("*.json"))
        parent_output = REMAINING / "parent_review.json"
    write(parent_output, {
        "status": "adjudicated", "summary": summary, "method": decisions["method"],
        "decision_sources": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in decision_sources],
        "model_dispatch": "All three child reviewers were dispatched as gpt-5.6-luna; role labels inside their prose are not model identities.",
        "review_sources": [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in review_sources],
        "reviewer_coverage_and_quote_checks": reviewer_checks,
        "parent_exact_quote_count": len(parent_quotes), "parent_quote_checks": parent_quotes,
        "extension_exact_quote_count": len(extension_quote_checks) if EXTENSION.exists() else None,
        "source_hashes_verified": {"preserved_source_pages": len(letters), "available_transcriptions": len(full_read), "XML_sources": len(audit)},
        "baseline_hashes_unchanged": baseline, "corrections": decisions["corrections"],
        "intermediate_version_limit": "Emma and section-date initial reports are preserved. The Kemp reviewer overwrote its first continuation report without retaining a snapshot; final quotes and coverage were independently revalidated. Henslow, Lyell and chronology initial reports from the subsequent phase are preserved separately.",
    })
    status = write_corpus_status(summary, decision_sources)
    print(json.dumps({"expansion": summary, "combined_single_date_pairs": status["established_prompt_pairs_across_reviewed_batches"],
                      "combined_direct_links": status["confirmed_direct_reply_links_including_dated_sections"],
                      "combined_distinct_Darwin_responses": status["distinct_Darwin_response_letters_including_dated_sections"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

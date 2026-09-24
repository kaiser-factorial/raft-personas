#!/usr/bin/env python3
"""Validate and publish a manually adjudicated pre-Beagle full-reading batch.

No keyword, date-screen or model proposal is promoted by this script. All graph
changes must be explicitly present in parent_review.json after adjudication.
"""

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

from build_correspondence_map import ROOT, build_map, enrich_evidence, load_jsonl, write_json

FOLDER = ROOT / "reports/pre-beagle-1828-1831"
BATCH = "pre-beagle-1828-1831"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def checked_reviewer_evidence(value, letters):
    """Validate reviewer quotes even when the reviewer did not supply offsets."""
    if isinstance(value, list):
        for item in value:
            checked_reviewer_evidence(item, letters)
    elif isinstance(value, dict):
        if {"letter_id", "body_paragraph", "quote"} <= value.keys():
            letter = letters[value["letter_id"]]
            paragraph = next(p for p in letter["paragraphs"] if p["body_paragraph"] == value["body_paragraph"])
            if not value["quote"] or value["quote"] not in paragraph["text"]:
                raise ValueError(f"Reviewer quote mismatch: {value['letter_id']}")
        for item in value.values():
            checked_reviewer_evidence(item, letters)


def validate_reviews(manifest, letters):
    by_direction = {"outgoing": {}, "incoming": {}}
    all_reviews, source_files = {}, []
    for group, assignment in manifest["luna_groups"].items():
        packet_path = FOLDER / "luna" / f"{group}.packet.json"
        if digest(packet_path) != assignment["packet_sha256"]:
            raise ValueError("Reviewer packet changed")
        path = FOLDER / "luna" / f"{group}.review.json"
        review = load(path)
        if review["group_id"] != group or review["model"] != "gpt-5.6-luna":
            raise ValueError("Wrong reviewer identity")
        checked_reviewer_evidence(review, letters)
        for direction in by_direction:
            records = review[f"{direction}_reviews"]
            ids = [r["letter_id"] for r in records]
            if len(set(ids)) != len(ids) or set(ids) != set(assignment[f"{direction}_ids"]):
                raise ValueError(f"Incomplete {group} {direction} review")
            for record in records:
                letter = letters[record["letter_id"]]
                if (record["body_read_in_full"] is not True
                        or record["paragraphs_read"] != [p["body_paragraph"] for p in letter["paragraphs"]]
                        or not record["summary"]):
                    raise ValueError("Incomplete full-body reading record")
                if record["letter_id"] in by_direction[direction]:
                    raise ValueError("Duplicate primary review assignment")
                by_direction[direction][record["letter_id"]] = {**record, "reviewer_group": group}
        all_reviews[group] = review
        source_files.extend({"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in (packet_path, path))
        initial_path = FOLDER / "luna" / f"{group}.initial.review.json"
        if initial_path.exists():
            source_files.append({"path": str(initial_path.relative_to(ROOT)), "sha256": digest(initial_path)})
    for direction in by_direction:
        if set(by_direction[direction]) != set(manifest[f"{direction}_ids"]):
            raise ValueError("Full batch not covered")
    return by_direction, all_reviews, source_files


def compile_annotations(initial, parent, reviews, sources, baseline):
    if parent["status"] != "adjudicated":
        raise ValueError("Parent adjudication is incomplete")
    annotation = copy.deepcopy(baseline)
    for key in ("edges", "candidate_links", "unlocated_nodes"):
        annotation[key].extend(copy.deepcopy(parent.get(key, [])))
    annotation.setdefault("context_identity_policies", []).extend(parent.get("context_identity_policies", []))
    annotation["relation_definitions"]["receipt_without_reading"] = (
        "An incoming letter or unresolved reference was physically received but explicitly unread at the Darwin witness. "
        "This creates no knowledge availability or prompt eligibility.")
    annotation["relation_definitions"]["source_event_match"] = (
        "A source documents an event reported by Darwin, but his wording does not establish reading its whole text. "
        "Only the explicit event is attested; no incoming full-text availability or prompt is created.")
    annotation["review_batches"].append({
        "id": BATCH, "letter_ids": [r["letter_id"] for r in initial["letters"]],
        "status": "reviewed", "method": "Parent full-body survey, three independent Luna full-text reviews, parent adjudication.",
        "evidence_limits": "80 outgoing and 34 incoming texts in the pinned audited corpus. Missing references are not a count of distinct physical letters. No claim of exhaustive archival search."
    })
    for row in initial["letters"]:
        final = copy.deepcopy(row)
        override = parent.get("outgoing_overrides", {}).get(row["letter_id"], {})
        final.update({k: v for k, v in override.items() if k != "observations"})
        for index, update in override.get("observations", {}).items():
            final["observations"][int(index)].update(update)
        evidence, observations = [], []
        for i, obs in enumerate(final["observations"]):
            ids = []
            for j, span in enumerate(obs["evidence"]):
                key = f"pre-{row['letter_id']}-{i}-{j}"
                evidence.append({**span, "evidence_id": key})
                ids.append(key)
            observations.append({k: v for k, v in obs.items() if k != "evidence"} | {"evidence_ids": ids})
        adjacent = [e for e in parent.get("edges", []) if row["letter_id"] in (e["source_id"], e["target_id"])]
        annotation["reviewed_letters"].append({
            "letter_id": row["letter_id"], "batch_id": BATCH, "review_status": "reviewed",
            "target_body_read_in_full": True, "paragraphs_read": row["paragraphs_read"],
            "summary": final["summary"], "outcome": "adjudicated_see_graph_for_role",
            "evidence": evidence, "observations": observations,
            "new_graph_links": [e["id"] for e in adjacent],
            "independent_review": reviews["outgoing"][row["letter_id"]],
            "independent_review_status": "Preserved proposal; parent adjudication and accepted graph edges control the final result.",
            "parent_adjudication": parent.get("outgoing_adjudications", {}).get(row["letter_id"],
                "Initial full-body observations retained after independent full-reading review; only explicitly accepted graph edges are active."),
        })
    annotation["pre_beagle_full_read_review"] = {
        "batch_id": BATCH, "status": "adjudicated", "outgoing_count": 80, "incoming_count": 34,
        "reviewer_groups": ["fox", "voyage", "family"], "source_files": sources,
        "incoming_reviews": list(reviews["incoming"].values()),
        "parent_decisions": parent.get("luna_adjudications", []),
        "candidate_and_rejected_proposals_never_activate_knowledge": True,
    }
    return annotation


def link(letter_id):
    return f"[{letter_id.removeprefix('DCP-LETT-')}](https://www.darwinproject.ac.uk/letter/?docId=letters/{letter_id}.xml)"


def clean(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def publish(graph, initial, parent, reviews, summary):
    nodes = {r["id"]: r for r in graph["nodes"]}
    final_reviews = [r for r in graph["reviewed_letters"] if r["batch_id"] == BATCH]
    dossiers = []
    for review in final_reviews:
        identifier = review["letter_id"]
        dossiers.append({**review, "target": nodes[identifier],
                         "initial_survey": next(r for r in initial["letters"] if r["letter_id"] == identifier),
                         "accepted_relationships": [e for e in graph["edges"] if identifier in (e["source_id"], e["target_id"])],
                         "candidate_relationships": [e for e in graph["candidate_links"] if identifier in (e["source_id"], e["target_id"])],
                         "training_role": nodes[identifier]["training_role"],
                         "established_prompt_ids": nodes[identifier]["established_prompt_ids"]})
    (FOLDER / "dossiers.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in dossiers))
    write_json(FOLDER / "incoming_reviews.json", list(reviews["incoming"].values()))
    write_json(FOLDER / "summary.json", summary)
    lines = ["# Pre-Beagle correspondence: 1828–1831", "",
             "Completed 16 September 2026. All 80 eligible Darwin outgoing bodies were read in full for the initial survey, then independently reviewed by three Luna reviewers. The reviewers also read all 34 incoming bodies. Letter 153, spanning 20–31 December 1831, remains outside the pre-departure comparison set and postdates every outgoing target here.", "",
             f"The batch has **{summary['complete_surviving_prompt_pairs']} complete surviving prompt–response pairs** under the current timing policy, including the previously established 125 → 135A. **{summary['grounding_targets']} outgoing letters retain grounding roles**; some have explicit missing prompts or a supported reply whose date is unresolved. Incoming prose never becomes Darwin's voice.", "",
             "## Findings", ""]
    lines.extend(f"- {finding}" for finding in parent["report_findings"])
    lines += ["", "## Selected correspondence flow", "", parent["mermaid"], "",
              "Solid arrows above are accepted information or reply relationships. Dashed arrows are unresolved identities or unavailable texts. Arrow direction in this diagram follows information flow; machine-readable replies point from response to input. The diagram is a selected view, not a complete timeline.", "",
              "## Every outgoing letter", "", "Original catalogue dates are retained, including alternatives and question marks. Each dossier includes the unchanged metadata and XML constraints, initial hypothesis, independent review, parent decision, exact evidence and source hashes.", "",
              "| Letter | Original date | Recipient | Final assessment | Prompt IDs |",
              "| --- | --- | --- | --- | --- |"]
    for d in dossiers:
        m = d["target"]["original_csv"]
        name = f"{m['recipient_forename']} {m['recipient_surname']}".strip()
        prompts = ", ".join(link(i) for i in d["established_prompt_ids"]) or "—"
        lines.append(f"| {link(d['letter_id'])} | {clean(m['date'])} | {clean(name)} | {clean(d['summary'])} | {prompts} |")
    lines += ["", "## Review and evidence", "",
              "- [Initial survey](initial_survey.json): frozen before delegation; includes hypotheses later corrected.",
              "- [All 80 final dossiers](dossiers.jsonl): reviewed observations and accepted versus candidate map links.",
              "- [All 34 incoming reviews](incoming_reviews.json): full reading coverage and proposed links, which require the parent decision before activation.",
              "- [Parent adjudication](parent_review.json): accepted edges, withheld identities, missing references, identity restrictions and reviewer corrections.",
              "- [Fox review](luna/fox.review.json), [voyage review](luna/voyage.review.json), [family review](luna/family.review.json): preserved independent proposals, including rejected ones.",
              "- [Coverage and integrity audit](summary.json): paragraph coverage, source hashes and unchanged earlier evidence.",
              "- [Current complete graph](../correspondence-map/graph.json): the integrated map. Reference nodes are not asserted to be distinct physical documents; repeated references may alias the same letter.", "",
              "The audit is complete for this batch; the historical correspondence remains incomplete. Original CSV/XML dates are not overwritten with response dates. Known-by dates are conservative bounds from Darwin's outgoing writing, while explicit relative receipt statements remain separate evidence. An incoming reply to an unlocated Darwin letter proves the other person's receipt, not Darwin's receipt of that reply. No missing text has been synthesized. No training export or model training has run.", "",
              "Rebuild offline after reviewing annotations:", "", "```sh", "python3 scripts/build_pre_beagle_review.py",
              "python3 scripts/build_correspondence_map.py", "python3 -m unittest discover -s tests -v", "```", ""]
    (FOLDER / "README.md").write_text("\n".join(lines))


def main():
    manifest, initial, parent = (load(FOLDER / n) for n in ("manifest.json", "initial_survey.json", "parent_review.json"))
    if digest(FOLDER / "initial_survey.json") != manifest["initial_survey_sha256"]:
        raise ValueError("Frozen initial survey changed")
    letters = load_jsonl(ROOT / "reports/body-date-search-37-337/letters.jsonl")
    by_letter = {r["id"]: r for r in letters}
    reviews, raw_reviews, sources = validate_reviews(manifest, by_letter)
    checked_reviewer_evidence(parent, by_letter)
    parent = enrich_evidence(parent, by_letter)
    paths = [FOLDER / n for n in ("manifest.json", "initial_survey.json", "parent_review.json", "source_packet.json")]
    paths.append(ROOT / "scripts/curate_pre_beagle_decisions.py")
    sources += [{"path": str(p.relative_to(ROOT)), "sha256": digest(p)} for p in paths]
    baseline = load(FOLDER / "baseline_annotations.json")
    annotations = compile_annotations(initial, parent, reviews, sources, baseline)
    graph = build_map(load_jsonl(ROOT / "reports/1828-1836/audit.jsonl"), letters, annotations)
    checks = {}
    for path, old_hash in load(FOLDER / "baseline_hashes.json").items():
        if path in ("data/annotations/correspondence_links.json", "reports/correspondence-map/graph.json"):
            continue
        checks[path] = {"sha256": digest(ROOT / path), "unchanged": digest(ROOT / path) == old_hash}
    if not all(c["unchanged"] for c in checks.values()):
        raise ValueError("Preserved source or prior case-study evidence changed")
    nodes = {n["id"]: n for n in graph["nodes"]}
    targets = [nodes[i] for i in manifest["outgoing_ids"]]
    summary = {
        "batch_id": BATCH, "status": "completed", "parent_outgoing_full_reads": len(initial["letters"]),
        "independent_outgoing_full_reads": len(reviews["outgoing"]), "independent_incoming_full_reads": len(reviews["incoming"]),
        "outgoing_body_words": sum(by_letter[i]["body_word_count"] for i in manifest["outgoing_ids"]),
        "incoming_body_words": sum(by_letter[i]["body_word_count"] for i in manifest["incoming_ids"]),
        "new_edges_by_type": dict(Counter(e["relationship"] for e in parent["edges"])),
        "new_unlocated_reference_nodes": len(parent["unlocated_nodes"]),
        "reference_nodes_are_distinct_letter_count": False,
        "complete_surviving_prompt_pairs": sum(len(n["established_prompt_ids"]) for n in targets),
        "response_targets": sum(bool(n["established_prompt_ids"]) for n in targets),
        "grounding_targets": sum(n["training_role"] == "dated_Darwin_grounding" for n in targets),
        "new_candidates": len(parent["candidate_links"]), "incoming_voice_targets": 0,
        "source_and_prior_evidence_checks": checks, "all_prior_annotations_preserved": all(
            entry in annotations[key] for key in ("edges", "candidate_links", "unlocated_nodes", "reviewed_letters") for entry in baseline[key]),
        "inputs": sources, "training_performed": False, "raft_export_performed": False,
    }
    write_json(ROOT / "data/annotations/correspondence_links.json", annotations)
    publish(graph, initial, parent, reviews, summary)
    print(json.dumps({k: v for k, v in summary.items() if k not in ("inputs", "source_and_prior_evidence_checks")}, indent=2))


if __name__ == "__main__":
    main()

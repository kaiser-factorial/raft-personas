#!/usr/bin/env python3
"""Publish the reviewed 13-letter batch without promoting search candidates."""

import copy
import hashlib
import json
import re
from collections import Counter

from build_correspondence_map import ROOT, load_jsonl, person_keys, write_json

OUT = ROOT / "reports/post-return-1836"
BATCH = "post-return-1836"
TARGET_IDS = {f"DCP-LETT-{n}" for n in (307, 310, 311, 313, 314, 317, 318, 319, 320, 321, 325, 327, 329)}


def link(letter_id):
    return f"[{letter_id.removeprefix('DCP-LETT-')}](https://www.darwinproject.ac.uk/letter/?docId=letters/{letter_id}.xml)"


def escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def candidate_record(node, letter, review, target):
    """A same-person date screen and reproducible retrieval, never a match decision."""
    earliest = node["xml_date_bounds"]["earliest"]
    latest = target["xml_date_bounds"]["latest"]
    if earliest and latest and earliest > latest:
        disposition = "too_late_under_XML_constraints"
    elif not node["period_selection_eligible"]:
        disposition = "held_period_constraints"
    else:
        disposition = "chronologically_possible_identity_candidate"
    pattern = re.compile(review["candidate_search_terms"], re.I)
    hits = []
    for paragraph in (letter or {}).get("paragraphs", []):
        for match in pattern.finditer(paragraph["text"]):
            start, end = max(0, match.start() - 160), min(len(paragraph["text"]), match.end() + 240)
            hits.append({
                "body_paragraph": paragraph["body_paragraph"], "locator": paragraph["locator"],
                "matched_text": match.group(), "char_start": match.start(), "char_end": match.end(),
                "excerpt": paragraph["text"][start:end], "excerpt_start": start, "excerpt_end": end,
            })
    return {
        "id": node["id"], "screen_disposition": disposition,
        "original_csv": node["original_csv"], "original_sent_date_constraints": node["original_sent_date_constraints"],
        "xml_date_bounds": node["xml_date_bounds"], "provenance": node["provenance"],
        "sender_evidence": node["sender_evidence"], "recipient_evidence": node["recipient_evidence"],
        "body_source": node["body_source"], "automatic_search_passages": hits,
        "search_passages_are_match_evidence": False,
        "screen_establishes_receipt_or_reply": False,
    }


def build_dossiers(graph, letters):
    nodes = {n["id"]: n for n in graph["nodes"]}
    by_letter = {r["id"]: r for r in letters}
    batch = next(b for b in graph["review_batches"] if b["id"] == BATCH)
    selected = {n["id"] for n in nodes.values() if n["darwin_voice_eligible"]
                and n["xml_date_bounds"]["earliest"] > "1836-10-02"
                and n["xml_date_bounds"]["latest"] <= "1836-12-31"}
    reviews = [r for r in graph["reviewed_letters"] if r["batch_id"] == BATCH]
    if selected != TARGET_IDS or set(batch["letter_ids"]) != selected or {r["letter_id"] for r in reviews} != selected:
        raise ValueError("Review coverage differs from the 13 eligible post-return targets")
    accepted = {e["id"]: e for e in graph["edges"]}
    candidates = {e["id"]: e for e in graph["candidate_links"]}
    incoming_reviews = {(r["incoming_id"], r["outgoing_id"]): r
                        for r in (graph.get("incoming_full_read_review") or {}).get("assessments", [])}
    output = []
    for review in reviews:
        target = nodes[review["letter_id"]]
        names = person_keys(target["recipient_evidence"])
        pool = [candidate_record(n, by_letter.get(n["id"]), review, target) for n in nodes.values()
                if n["node_kind"] == "catalogued_letter" and n["direction"] == "to_darwin"
                and names & person_keys(n["sender_evidence"])]
        for candidate in pool:
            candidate["full_read_assessment"] = copy.deepcopy(incoming_reviews.get((candidate["id"], target["id"])))
        edge_ids = set(review.get("existing_graph_links", []) + review.get("new_graph_links", [])
                       + review.get("related_graph_links", []))
        if not edge_ids <= accepted.keys():
            raise ValueError("Review references a missing accepted edge")
        local_candidates = [candidates[key] for key in review.get("candidate_graph_links", [])]
        local_edges = [accepted[key] for key in sorted(edge_ids)]
        if review["new_surviving_prompt_established"] != bool(target["established_prompt_ids"]):
            raise ValueError("Review prompt outcome disagrees with graph")
        output.append({
            **copy.deepcopy(review), "target": copy.deepcopy(target),
            "same_correspondent_date_screen": pool,
            "candidate_search_scope": "All 288 audited candidates, using XML person keys and interval possibility. Full-catalogue follow-up checks are documented in search_cases.",
            "accepted_relationships": local_edges, "candidate_relationships": local_candidates,
            "training_role": target["training_role"],
            "established_prompt_ids": target["established_prompt_ids"],
        })
    return output


def diagram(graph):
    # Reply arrows show information flow; own-letter arrows point to the referenced item.
    edges = [e for e in graph["edges"] if {e["source_id"], e["target_id"]} & TARGET_IDS
             or e["id"] == "reply-323-unlocated-darwin"]
    candidates = [e for e in graph["candidate_links"] if e["source_id"] in TARGET_IDS]
    replies = {(e["target_id"], e["source_id"]) for e in edges if e["relationship"] == "replies_to"}
    ids = sorted({e[k] for e in edges + candidates for k in ("source_id", "target_id")})
    aliases = {letter_id: f"n{i}" for i, letter_id in enumerate(ids)}
    nodes = {n["id"]: n for n in graph["nodes"]}
    missing_names = {
        "UNLOCATED-WHITLEY-BEFORE-314": "Whitley incoming · text unlocated",
        "UNLOCATED-FOX-BEFORE-319": "Fox incoming · identity unresolved",
        "UNLOCATED-DARWIN-TO-HERBERT-BEFORE-314": "Darwin to Herbert · unreceived note · text unlocated",
        "UNLOCATED-DARWIN-TO-HERBERT-ACKNOWLEDGED-323": "Darwin to Herbert · different letter · text unlocated",
    }
    lines = ["```mermaid", "flowchart TD"]
    for letter_id in ids:
        node = nodes[letter_id]
        if letter_id in missing_names:
            label = missing_names[letter_id]
        else:
            meta = node["original_csv"]
            prefix = "recipient" if node["direction"] == "from_darwin" else "sender"
            other = f"{meta[prefix + '_forename']} {meta[prefix + '_surname']}".strip()
            who = f"Darwin to {other}" if node["direction"] == "from_darwin" else f"{other} to Darwin"
            label = f"{letter_id.removeprefix('DCP-LETT-')} · {who} · {meta['date']}"
            if letter_id == "DCP-LETT-330":
                label += " · reported text, excluded from voice"
        lines.append(f'    {aliases[letter_id]}["{label.replace(chr(34), chr(39))}"]')
    for edge in edges:
        source, target = edge["source_id"], edge["target_id"]
        if edge["relationship"] == "knowledge_before":
            if (source, target) in replies:
                continue
            label = f"context known by {edge['known_by_date']}"
        elif edge["relationship"] == "replies_to":
            source, target = target, source
            label = "replies; missing text prevents a training pair" if not nodes[source]["text_available"] else "replies"
            if target == "DCP-LETT-323":
                label = "Herbert replies; Darwin receipt unproved"
        else:
            label = "references own letter; no receipt inferred"
        lines.append(f'    {aliases[source]} -->|"{label}"| {aliases[target]}')
    for edge in candidates:
        lines.append(f'    {aliases[edge["source_id"]]} -.->|"possible own-letter reference; unconfirmed"| {aliases[edge["target_id"]]}')
    return "\n".join(lines + ["```"])


def report_text(graph, dossiers):
    batch = next(b for b in graph["review_batches"] if b["id"] == BATCH)
    followup = graph.get("incoming_full_read_review")
    followup_text = (f"Follow-up: three Luna reviewers read all {followup['incoming_count']} distinct earlier incoming candidates in full, covering {len(followup['assessments'])} comparisons. Their checked assessments are recorded alongside the date screen; [full-reading report](incoming-full-read/README.md). The screen is a broad inventory, not a list of equally plausible prompts."
                     if followup else "The earlier incoming lists below are broad identity/date screens, not equally plausible prompts; full-body coverage of those inputs is described under evidence limits.")
    lines = [
        "# Post-return Darwin correspondence review: 13 letters",
        "", "Completed 16 September 2026. Covers individually attributed Darwin outgoing letters after 2 October through 31 December 1836.",
        "", "**All 13 target letters were read in full. No new complete surviving incoming-prompt / Darwin-response pair was established.** All 13 retain dated-grounding roles. At completion of this batch, the whole map had three established prompt pairs; later batches are reflected in the [current map](../correspondence-map/README.md). Incoming authors never become Darwin voice targets.",
        "", followup_text,
        "", "## What this pass establishes", "",
        "- **Missing incoming prompts:** Whitley’s input to 314 remains unlocated; Fox’s explicitly answered input to 319 is now recorded as an unresolved reference. Their conservative known-by dates are 24 October and 6 November 1836. No original writing dates, exact delivery dates, or prompt text have been invented.",
        "- **Information across correspondents:** retain FitzRoy 312 → Darwin 313 as context for the engagement news, not Caroline’s conversational prompt.",
        "- **Darwin’s own letters:** 318 references the long letter 317 accompanying the Galapagos plants. 329 references the Carlisle letter represented by 330; 330 remains a minute-book report excluded from Darwin voice. The reference in 329 proves neither dispatch nor Carlisle’s personal receipt; the later minute-book report is separate corroboration.",
        "- **Two Herbert references:** 314 describes an unreceived Shrewsbury note. Herbert’s 323 explains the failed handoff but answers a different Darwin letter received that morning. Both outgoing texts remain unlocated. 323 itself still has no established Darwin knowledge date.",
        "- **One uncertain identity:** 327 probably refers to 319 as the previous letter to Fox at Ryde, but another unlocated outgoing letter remains possible. This stays outside accepted links.",
        "", "Advice, invitations, loaned objects, future requests, and negated writing events are retained as observations. They do not automatically create incoming-letter nodes. A letter from E. Holland in 313 has an unconfirmed addressee and is therefore outside the to/from-Darwin graph pending identification.",
        "", "## Letter-by-letter outcomes", "",
        "Dates below retain the original catalogue wording. XML constraints and original metadata are preserved in every machine-readable dossier. The unusual wording for 317 is retained exactly; its XML interval is 30–31 October and its scalar writing date remains null.",
        "", "| Letter | Original date | Recipient | Reviewed result |",
        "| --- | --- | --- | --- |",
    ]
    for dossier in dossiers:
        meta = dossier["target"]["original_csv"]
        recipient = f"{meta['recipient_forename']} {meta['recipient_surname']}".strip()
        lines.append(f"| {link(dossier['letter_id'])} | {escape(meta['date'])} | {escape(recipient)} | {escape(dossier['summary'])} |")
    lines += ["", "## Reviewed flow", "",
              "Solid links are accepted relationships. Dashed links are unresolved identities. Reply arrows run from the earlier letter to its answer; an own-letter reference points from the mentioning letter to the document mentioned. The drawing is generated from the map and does not imply a complete postal chronology.",
              "", diagram(graph), "", "## Evidence and competing candidates", "",
              "Each item below preserves exact body evidence with paragraph numbers; JSON dossiers also preserve offsets, locators, source URLs, retrieval metadata, and hashes. Same-correspondent candidates come from the XML identity/date screen. Automatically retrieved passages in the dossiers are search aids, not accepted matches.",
              "", batch["evidence_limits"], "",
              "Full-catalogue checks and rejected identifications for Whitley, Fox, and Herbert are retained in the map’s `search_cases`. A catalogue search that finds no matching text is not proof the text has been destroyed."]
    for dossier in dossiers:
        lines += ["", f"### {dossier['letter_id'].removeprefix('DCP-LETT-')}", "", dossier["summary"]]
        pool = dossier["same_correspondent_date_screen"]
        possible = [r for r in pool if r["screen_disposition"] == "chronologically_possible_identity_candidate"]
        held = [r for r in pool if r["screen_disposition"] == "held_period_constraints"]
        late = [r for r in pool if r["screen_disposition"] == "too_late_under_XML_constraints"]
        lines += ["", "Earlier records passing the identity/date screen: " + (", ".join(link(r["id"]) for r in possible) or "none in the audited set") + "."]
        reviewed = [r for r in possible if r.get("full_read_assessment")]
        if reviewed:
            lines += ["", "Full-body comparison outcomes: " + "; ".join(
                f"{r['id'].removeprefix('DCP-LETT-')}: {r['full_read_assessment']['status'].replace('_', ' ')}"
                for r in reviewed) + ". See the linked full-reading report for reasons and evidence."]
        if held:
            lines += ["", "Held separately for date uncertainty: " + ", ".join(link(r["id"]) for r in held) + "."]
        if late:
            lines += ["", "Same-correspondent records too late under the XML bounds: " + ", ".join(link(r["id"]) for r in late) + "."]
        evidence = {e["evidence_id"]: e for e in dossier["evidence"]}
        for observation in dossier["observations"]:
            lines += ["", observation["interpretation"], ""]
            for key in observation["evidence_ids"]:
                span = evidence[key]
                lines.append(f"- {link(span['letter_id'])}, body paragraph {span['body_paragraph']}: “{escape(span['quote'])}”")
    lines += ["", "## Reproducibility and limits", "",
              "- [dossiers.jsonl](dossiers.jsonl): 13 complete review records, original metadata, XML constraints, reviewed evidence, and a reproducible same-correspondent search screen.",
              "- [summary.json](summary.json): coverage, outcomes, unchanged-source checks, and input hashes.",
              "- [Correspondence graph](../correspondence-map/graph.json): accepted and candidate links, the four unlocated reference nodes from this batch, detailed search cases, and later integrated reviews.",
              "- [Editable annotations](../../data/annotations/correspondence_links.json): the reviewed source for these derived outputs.",
              "", "The original XML audit, raw pages, and extracted letter bodies are unchanged. The 13 targets include uncertainly dated 317 but exclude reported text 330. Candidate pools can include voyage-era incoming letters; no recent-mail assumption excludes them. This pass is a completed review of these 13 outgoing texts, not an exhaustive search of every archive or a complete receipt chronology. No training export or model training has run.",
              "", "Rebuild offline with Python 3.11+:", "", "```sh",
              "python3 scripts/build_correspondence_map.py", "python3 scripts/build_post_return_review.py",
              "python3 -m unittest discover -s tests -v", "```", ""]
    return "\n".join(lines)


def main():
    graph_path = ROOT / "reports/correspondence-map/graph.json"
    graph = json.loads(graph_path.read_text())
    for source in graph["inputs"]:
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Rebuild correspondence graph: an input changed")
    letters = load_jsonl(ROOT / "reports/body-date-search-37-337/letters.jsonl")
    dossiers = build_dossiers(graph, letters)
    baseline = json.loads((OUT / "baseline_hashes.json").read_text())
    preserved = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest for path, digest in baseline.items()
                 if path in ("reports/1828-1836/audit.jsonl", "reports/body-date-search-37-337/letters.jsonl")}
    if not all(preserved.values()):
        raise ValueError("Original audit or extracted bodies changed during review")
    output = OUT / "dossiers.jsonl"
    output.write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in dossiers))
    (OUT / "README.md").write_text(report_text(graph, dossiers))
    summary = {
        "batch_id": BATCH, "reviewed_letter_ids": [d["letter_id"] for d in dossiers],
        "reviewed_outgoing_count": len(dossiers), "full_outgoing_body_read_count": sum(d["target_body_read_in_full"] for d in dossiers),
        "complete_surviving_prompt_pairs_in_batch": sum(bool(d["established_prompt_ids"]) for d in dossiers),
        "roles": dict(Counter(d["training_role"] for d in dossiers)),
        "outcomes": dict(Counter(d["outcome"] for d in dossiers)),
        "new_accepted_relationship_ids": sorted({key for d in dossiers for key in d.get("new_graph_links", [])}
                                                | {"reply-323-unlocated-darwin"}),
        "unresolved_candidate_ids": [e["id"] for e in graph["candidate_links"] if e["source_id"] in TARGET_IDS],
        "preserved_source_checks": preserved,
        "graph_input": {"path": str(graph_path.relative_to(ROOT)), "sha256": hashlib.sha256(graph_path.read_bytes()).hexdigest()},
        "output": {"path": str(output.relative_to(ROOT)), "sha256": hashlib.sha256(output.read_bytes()).hexdigest()},
        "training_performed": False, "raft_export_performed": False,
    }
    write_json(OUT / "summary.json", summary)
    print(json.dumps({k: summary[k] for k in ("reviewed_outgoing_count", "complete_surviving_prompt_pairs_in_batch", "roles", "preserved_source_checks")}))


if __name__ == "__main__":
    main()

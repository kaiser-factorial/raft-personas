"""Reproduce the primary-agent full-reading decisions for the expansion pilot.

The explicit, manually adjudicated links below are not a matching algorithm.
The script verifies quotations, source hashes, identities, and date constraints.
It writes a separate pilot graph and an aggregate count, leaving the old graph intact.
"""

import hashlib
import json

from fetch_metadata import ROOT

OUT = ROOT / "reports/1837-1843/pilot"


def main():
    audit = {r["id"]: r for r in map(json.loads, (ROOT / "reports/1837-1843/audit.jsonl").read_text().splitlines())}
    letters = {r["id"]: r for r in map(json.loads, (OUT / "letters.jsonl").read_text().splitlines())}
    for letter in letters.values():
        source = letter["source"]
        if hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError(f"Source changed: {letter['id']}")

    def evidence(ident, paragraph, quote):
        ident = "DCP-LETT-" + ident
        body = next(p for p in letters[ident]["paragraphs"] if p["body_paragraph"] == paragraph)
        if quote not in body["text"]:
            raise ValueError(f"Quote absent: {ident}, paragraph {paragraph}: {quote}")
        return {"letter_id": ident, "body_paragraph": paragraph, "locator": body["locator"],
                "quote": quote, "char_start": body["text"].index(quote), "source": letters[ident]["source"]}

    specs = [
        ("345", "346", "Caroline Darwin", "1837-02-27",
         "Darwin explicitly answers her last letter's questions about Lyell's speech and Herschel's chronology; both distinctive questions occur in 345.",
         [("345", 1, "We are longing to have an account of Lyells speech."),
          ("345", 3, "so I do not see how what Sir J Herschell says is new."),
          ("346", 1, "You enquired in yr. last letter about Lyell’s Speech;"),
          ("346", 2, "You tell me you do not see what is new in Sir J. Herschell’s idea about the chronology of the old Testament being wrong.")],
         "346 is a copyist transmission with an editorial date correction and a lacuna. Preserve those source features when exporting; it is Darwin's letter prose, not a meeting-minute paraphrase."),
        ("444", "445", "Emma Wedgwood", "1838-11-27",
         "Darwin acknowledges receipt and answers the distinctive discussion of Caroline Tollet's reading, Emma's already having read Nicholas Nickleby, and her wavering over suburban versus central housing. These occur in 444, not the initially selected 441.",
         [("444", 4, "Caroline Tollet says in her situation she finds she can read nothing but sermons & Nicholas Nickleby."),
          ("444", 2, "Elizabeth & Caroline are grown suburban again & it is very puzzling"),
          ("445", 2, "I was very glad to get your letter;"),
          ("445", 2, "You say Caroline Tollet has two works to read, & that you could read one, if not already read,"),
          ("445", 6, "I am glad to hear you are oscillating in opinion,")],
         "Keep 444's XML alternatives (25 and 26 November) and its Sunday/Monday body sections. Either date precedes the resolved 27 November response. No exact incoming composition or receipt day is manufactured. 445's cut-off postscript to Francis Wedgwood is not supplied by the surviving body."),
        ("699", "701F", "William Kemp", "1843-10-09",
         "Darwin acknowledges Kemp's paper-letter and responds directly to its sandpit description, proposed wet ancient climate, and plant observations. Editorial notes explicitly identify the 2 October letter.",
         [("699", 1, "From that seeming delicasy I intertained the opinion, that the Climate had been much more moist when the seed was deposited,"),
          ("701F", 1, "I write a line to inform you that your paper has reached me safely."),
          ("701F", 9, "I think your speculation about the former dampness of climate too bold")],
         "The year of 701F is editorially supplied from the relationship with 699. Preserve that reasoning. Other referenced Henslow/Lindley communications need their own receipt evidence."),
        ("711", "711F", "William Kemp", "1843-11-09",
         "Kemp accepts disappointing doubts about the seed discovery graciously. Darwin explicitly praises the tone of his last letter in that disappointment and reopens the publication question; editorial notes identify 711.",
         [("711", 3, "As for my part, it matters nothing, the investigation has given a pleasure that amply repays any trouble in the concern."),
          ("711F", 1, "Allow me to express my respect at the pleasant tone of your last letter,"),
          ("711F", 3, "With your permission I will draw up a short statement with as little theory as possible & will send it you for your approval.")],
         "The Thursday date of 711F is editorially resolved to 9 November using the surrounding exchange. This pilot has read 711 and 711F, but has not independently full-read every letter in that chain."),
        ("720", "720F", "William Kemp", "1843-12-07",
         "Kemp supplies further discovery particulars and enclosed testimonials; Darwin acknowledges adding the particulars last sent and receiving testimonial material. The editorial note identifies 720 as the source of those additions.",
         [("720", 1, "I have received your letter this morning for further information regarding the discovery of the seed."),
          ("720", 2, "I have enclosed certificates respecting those men, and could obtain 100 as good"),
          ("720F", 1, "with the particulars last sent added."),
          ("720F", 1, "I am sorry you thought it adviseable to send me a testimonial of yourself")],
         "The incoming body mentions testimonials about the two finders; Darwin and the editorial note additionally identify a testimonial about Kemp. The enclosures are not reconstructed as prompt text. The long-running exchange also requires earlier context before a final training export."),
    ]
    pairs, edges = [], []
    for source_id, target_id, correspondent, known_by, rationale, quotes, caveats in specs:
        source_id, target_id = "DCP-LETT-" + source_id, "DCP-LETT-" + target_id
        source, target = audit[source_id], audit[target_id]
        assert source["direction"] == "to_darwin" and target["direction"] == "from_darwin"
        assert source["period_selection_eligible"] and target["period_selection_eligible"]
        assert target["xml_earliest"] == target["xml_latest"] == known_by
        assert not target["exact_order_needs_review"]
        assert source["xml_latest"] <= known_by
        assert not source["metadata_multiple_senders"] and not target["metadata_multiple_senders"]
        source_people = {p["attributes"].get("key") for p in source["sender_evidence"]}
        target_people = {p["attributes"].get("key") for p in target["recipient_evidence"]}
        assert source_people == target_people
        pair = {"id": f"{source_id}--{target_id}", "incoming_id": source_id, "outgoing_id": target_id,
                "correspondent": correspondent, "status": "confirmed_direct_reply",
                "review_method": "primary-agent full reading of both surviving bodies and their editorial notes",
                "known_by_date": known_by, "actual_receipt_date": None,
                "availability_rule": "Incoming is evidenced available by the Darwin response, not by the incoming composition date; same-day use elsewhere needs ordering evidence.",
                "incoming_original_date": source["original_csv"]["date"],
                "outgoing_original_date": target["original_csv"]["date"],
                "incoming_xml_constraints": source["sent_date_constraints"],
                "outgoing_xml_constraints": target["sent_date_constraints"],
                "rationale": rationale, "evidence": [evidence(*q) for q in quotes],
                "caveats": caveats, "incoming_is_Darwin_voice": False,
                "surviving_Darwin_body_is_response_candidate": True,
                "training_export_ready": False,
                "export_preconditions": "Review the preceding context chain, preserve transcription gaps and section boundaries, and mask all incoming/context tokens from Darwin answer loss."}
        pairs.append(pair)
        edges.extend([
            {"type": "knowledge_before", "source": source_id, "target": target_id, "known_by_date": known_by, "review_id": pair["id"]},
            {"type": "replies_to", "source": target_id, "target": source_id, "review_id": pair["id"]},
        ])
    rejected = [{"incoming_id": "DCP-LETT-441", "outgoing_id": "DCP-LETT-445",
                 "status": "rejected_as_the_identified_direct_prompt",
                 "reason": "The distinctive reading and housing replies in 445 match 444. The editorial notes to 441 and 444 identify an earlier, now missing Darwin reply to 441. Do not substitute 441 or invent the missing response.",
                 "known_by_date_assigned": None,
                 "editorial_evidence": {"letter_id": "DCP-LETT-444", "locator": "editorial footnote 1",
                    "quote": "CD’s letter written in response to Emma’s of [21–2 November 1838] is missing.",
                    "source": letters["DCP-LETT-444"]["source"]}}]
    assert rejected[0]["editorial_evidence"]["quote"] in letters["DCP-LETT-444"]["editorial_footnotes"]
    outgoing_total = sum(r["period_selection_eligible"] and r["direction"] == "from_darwin" for r in audit.values())
    outgoing_read = sum(audit[i]["direction"] == "from_darwin" for i in letters)
    incoming_read = sum(audit[i]["direction"] == "to_darwin" for i in letters)
    result = {"period": "1837-1843", "full_read_ids": list(letters), "full_read_count": len(letters),
              "Darwin_outgoing_full_read_count": outgoing_read, "incoming_full_read_count": incoming_read,
              "confirmed_pair_count": len(pairs), "pairs": pairs, "rejected_candidates": rejected,
              "sampling_limit": "Purposively selected promising exchanges; no pairing-rate estimate and no claim that other records are unpaired.",
              "new_period_remaining_outgoing_metadata_records_unreviewed": outgoing_total - outgoing_read,
              "training_performed": False, "training_export_performed": False}
    (OUT / "review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (OUT / "graph.json").write_text(json.dumps({"nodes": [{"id": i, "direction": audit[i]["direction"]} for i in letters], "edges": edges,
                                               "rejected_candidates": rejected}, ensure_ascii=False, indent=2) + "\n")
    old = json.loads((ROOT / "reports/correspondence-map/summary.json").read_text())
    status = {"established_prompt_pairs_across_reviewed_batches": old["established_prompt_pairs"] + len(pairs),
              "batches": [{"period": "1828-1836", "confirmed_pairs": old["established_prompt_pairs"], "report": "reports/correspondence-map/README.md"},
                          {"period": "1837-1843", "confirmed_pairs": len(pairs), "report": "reports/1837-1843/README.md", "scope": "11-letter pilot only"}],
              "previously_identified_direct_reply_held_for_outgoing_date": "DCP-LETT-135 -> DCP-LETT-139; additional to the complete-pair count",
              "old_graph_retained_as_period_specific": True,
              "combined_training_export_performed": False,
              "unpaired_count_limit": f"Do not classify the {outgoing_total - outgoing_read} as-yet-unreviewed new-period outgoing metadata records as unpaired or independently voice eligible.",
              "inputs": [{"path": str(p.relative_to(ROOT)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in [ROOT / "reports/correspondence-map/summary.json", OUT / "review.json", ROOT / "reports/1837-1843/summary.json"]]}
    # The pilot is a historical subset. Rebuilding it must not erase a later,
    # separately adjudicated continuation from the aggregate status.
    continuation = ROOT / "reports/1837-1843/correspondence-map/summary.json"
    if continuation.exists():
        from build_expansion_review import write_corpus_status
        status = write_corpus_status(json.loads(continuation.read_text()))
    else:
        (ROOT / "reports/corpus-status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"pilot_pairs": len(pairs), "full_read_letters": len(letters), "total_confirmed_pairs_across_batches": status["established_prompt_pairs_across_reviewed_batches"]}))


if __name__ == "__main__":
    main()

"""Explicit parent adjudications, not an automatic correspondence matcher.

Luna proposals remain in their original reports. This separate decision ledger
records only relationships selected after primary-agent full-source review.
"""

import json
from pathlib import Path

from fetch_metadata import ROOT

OUT = ROOT / "reports/1837-1843/correspondent-review"
DEST = ROOT / "data/annotations/expansion_1837_1843.json"


def main():
    letters = {}
    for path in [ROOT / "reports/1837-1843/pilot/letters.jsonl", OUT / "letters.jsonl", OUT / "seed-context.letters.jsonl"]:
        letters.update({r["id"]: r for r in map(json.loads, path.read_text().splitlines())})

    def ident(value):
        return "DCP-LETT-" + value

    def ev(value, paragraph, quote):
        letter = letters[ident(value)]
        body = next(p for p in letter["paragraphs"] if p["body_paragraph"] == paragraph)
        assert quote in body["text"], (value, paragraph, quote)
        return {"letter_id": ident(value), "body_paragraph": paragraph,
                "quote": quote, "locator": body["locator"], "source": letter["source"]}

    def pair(inc, out, day, reason, quotes, sections=None, receipt=None):
        return {"incoming_id": ident(inc), "outgoing_id": ident(out),
                "status": "confirmed_direct_reply", "known_by_date": day,
                "actual_receipt_date": receipt,
                "response_scope": "dated_sections" if sections else "single_date_surviving_body",
                "response_sections": sections or [], "rationale": reason,
                "evidence": [ev(*q) for q in quotes], "training_export_ready": False}

    pilot = json.loads((ROOT / "reports/1837-1843/pilot/review.json").read_text())
    pairs = [{**p, "response_scope": "single_date_surviving_body", "response_sections": [],
              "verification_report": "reports/1837-1843/verification/parent_review.json"} for p in pilot["pairs"]]
    pairs += [
        pair("706", "710F", "1843-11-01",
             "Explicit answer to the last communication, defending Kemp against a hoax allegation and answering his publication question; editorial notes 1 and 3 identify 706.",
             [("706", 1, "detesting above all things, palming a hoax upon the Public"),
              ("706", 2, "and that I leave with you to judge what you think best"),
              ("710F", 1, "I shd have sooner answered your last communication"),
              ("710F", 2, "I would as soon believe myself capable of playing a hoax")]),
        pair("713", "715F", "1843-11-22",
             "The last-letter planting account matches Kemp's distinctive parallel rows and marked pot. The editorially supplied day is a resolved single day, not held solely because it is bracketed.",
             [("713", 4, "I planted about 3 dozen of the seed in parallel rows in a large pot, marking the rows"),
              ("715F", 1, "Your last letter with an account of your manner of planting &c &c was very useful.")]),
        pair("716", "716F", "1843-12-01",
             "Darwin's follow-up asks for the first name, eyewitness status and ownership of the Mr Bell introduced in 716. Preserve Darwin's invalid Nov. 31 dateline alongside the editor's 1 December resolution.",
             [("716", 2, "a Mr. Bell of Melrose, the proprietor of the place, was at the sand-pit at the time of the discovery"),
              ("716F", 1, "whether Mr — Bell (please inform me of his Christian name) actually saw the seeds disinterred?"),
              ("716F", 4, "Is Mr Bell of Melrose the actual land-owner of the Sand-pit? or does he rent it?")]),
        pair("492", "493", "1839-01-26",
             "Darwin answers Emma's straight-home wedding plan and her teasing about his consequence. This is the latest specifically answered letter, not merely the nearest incoming record.",
             [("492", 2, "we may as well go strait home on Tuesday I think."),
              ("492", 6, "don’t think yourself of such great consequence"),
              ("493", 1, "I think myself of sufficient consequence for you to care to hear our plans."),
              ("493", 3, "has just put me half way between the two plans.")]),
        pair("444", "448", "1838-11-30",
             "Friday's section explicitly quotes poor old gentleman from 444. A previous response in 445 does not prevent a later response to the same incoming text.",
             [("444", 3, "You have a great deal on your hands poor old gentleman"),
              ("448", 2, "In your last letter you say “poor old gentleman”")],
             ["DCP-LETT-448:friday"]),
        pair("447", "448", "1838-12-01",
             "Saturday's newly received letter supplies the Hensleighs' invitation for Emma to come house-hunting. It cannot condition the Friday section, which still awaits Emma's post.",
             [("447", 1, "The Hensleighs have asked me to go up with them for a week to look at houses with you."),
              ("448", 7, "Saturday Morning. I was delighted to receive your letter"),
              ("448", 7, "I want very much to know which day you will come.")],
             ["DCP-LETT-448:saturday"]),
        pair("464", "466", "1839-01-01",
             "Tuesday's agreement about Gordon Square identifies 464. Monday acknowledges a received bundle of two letters; Tuesday explicitly says he has just read the letters. Use Tuesday as the conservative content-availability bound, with Monday's receipt separately recorded at bundle level.",
             [("464", 1, "for I like it better than Gordon Sq."),
              ("466", 1, "which I received this morning"),
              ("466", 3, "I must thank you for your letters, which I have just read."),
              ("466", 4, "I quite agree with you, that this house is far pleasanter than Gordon Square.")],
             ["DCP-LETT-466:tuesday"]),
        pair("465", "466", "1839-01-01",
             "Tuesday responds to the cook/linen arrangements and the respirator requested in 465. Do not duplicate this one Darwin response into unrelated examples for its two incoming letters; keep the input bundle together. Receipt is distinguished from demonstrated reading.",
             [("465", 2, "I don’t know how we shall settle between the two cooks."),
              ("465", 4, "Papa would be much obliged to you to buy him a respirator"),
              ("466", 3, "After due deliberation, & having received your letters on Monday I write to Margaret"),
              ("466", 5, "go & get the Respirator for Uncle Jos")],
             ["DCP-LETT-466:tuesday"]),
        pair("482", "484", "1839-01-06",
             "Sunday answers Emma's your house, excised handwriting and delivery-date question; Monday continues with the cook. Darwin explicitly places receipt on Friday, the day after composition: 4 January. First reviewed writing that demonstrates the content is 6 January.",
             [("482", 1, "your new house"),
              ("482", 2, "so please to tell me when you receive this"),
              ("482", 2, "I enclose two specimens of Caligraphy"),
              ("484", 1, "sending me those square little sneers about my writing"),
              ("484", 6, "it came on Friday, the day after it was written")],
             ["DCP-LETT-484:sunday", "DCP-LETT-484:monday"], "1839-01-04"),
    ]

    seed = json.loads((OUT / "seed-context.review.json").read_text())
    knowledge = []
    for proposal in seed["proposed_links"]:
        # This explicit five-item parent selection was checked against all five
        # bodies, the earlier Henslow alternative, and the dated Kemp witnesses.
        assert (proposal["source_id"], proposal["target_id"]) in {
            (ident("669"), ident("672F")), (ident("690"), ident("691F")),
            (ident("701"), ident("705F")), (ident("707"), ident("710F")),
            (ident("708"), ident("710F"))}
        knowledge.append({"incoming_id": proposal["source_id"], "witness_id": proposal["target_id"],
                          "known_by_date": proposal["known_by_date"], "rationale": proposal["reason"],
                          "status": "supported_cross_correspondent_knowledge",
                          "identification": "content_and_attribution_inference",
                          "direct_prompt": False,
                          "evidence": [ev(q["letter_id"].removeprefix("DCP-LETT-"), q["body_paragraph"], q["quote"]) for q in proposal["exact_quotes"]]})
    knowledge[3]["competing_evidence"] = "701 already contained Henslow's tentative identification. 707 makes it definite and expressly contrasts the odd Lindley specimen with Kemp's A. patula; 710F relays that distinction and its editorial note 4 cites both Henslow letters. This is a supported identification, not an explicit dated receipt acknowledgment."
    knowledge[3]["evidence"].append(ev("707", 1, "The odd Atriplex came from Lindley alone"))

    section_specs = {
        "448": [("friday", "1838-11-30", list(range(1, 7))), ("saturday", "1838-12-01", [7, 8])],
        "466": [("monday", "1838-12-31", [1, 2]), ("tuesday", "1839-01-01", list(range(3, 8)))],
        "481": [("wednesday", "1839-01-02", list(range(1, 6))), ("thursday", "1839-01-03", [6, 7, 8])],
        "484": [("sunday", "1839-01-06", list(range(1, 7))), ("monday", "1839-01-07", [7])],
    }
    date_review = json.loads((OUT / "section-dates.review.json").read_text())
    sections = []
    for number, specs in section_specs.items():
        proposal = next(r for r in date_review["outgoing_reviews"] if r["letter_id"] == ident(number))
        for name, day, paras in specs:
            support = next(s for s in proposal["sections"] if s["paragraphs"] == paras)
            assert support["proposed_calendar_date"] == day
            sections.append({"id": ident(number) + ":" + name, "letter_id": ident(number),
                             "date": day, "paragraphs": paras, "basis": support["reason"],
                             "evidence": support["evidence"], "parent_accepted": True})

    # Incoming-author replies retain conversation structure, never Darwin targets.
    reverse_specs = [("447", "445"), ("449", "448"), ("482", "466"),
                     ("485", "481"), ("486", "484"), ("492", "489"),
                     ("699", "691F"), ("706", "705F"), ("711", "710F"),
                     ("713", "711F"), ("716", "715F"), ("720", "716F")]
    reverse = []
    proposals = [l for group in ("emma", "kemp")
                 for l in json.loads((OUT / f"{group}.review.json").read_text())["proposed_links"]]
    for response, antecedent in reverse_specs:
        proposal = next(p for p in proposals if p["source_id"] == ident(response) and p["target_id"] == ident(antecedent) and p["relationship"] == "replies_to")
        reverse.append({"response_id": ident(response), "antecedent_id": ident(antecedent),
                        "status": "supported_reply_by_correspondent", "rationale": proposal["reason"],
                        "evidence": proposal["evidence"], "is_Darwin_response": False,
                        "activates_Darwin_knowledge": False})
    # Parent accepts this additional reverse relation despite the Luna hold:
    # the 45-foot measurement answers an explicit question unique to 701F.
    reverse.append({"response_id": ident("706"), "antecedent_id": ident("701F"),
                    "status": "supported_reply_by_correspondent", "is_Darwin_response": False,
                    "activates_Darwin_knowledge": False,
                    "rationale": "706 answers 705F immediately and also supplies the earlier 701F depth and gravel/boulder requests. An incoming letter may answer several Darwin letters. The parent promotes the Luna candidate on the specific requested measurement, not shared subject alone.",
                    "evidence": [ev("706", 4, "you formerly requested to have a more particular description of the gravel bank"),
                                 ev("706", 8, "is 45 feet below the level of of the clay bed upon which the seed was found"),
                                 ev("701F", 4, "how many feet the layer with the seeds was above the present level of the nearest part of the present river"),
                                 ev("701F", 7, "Are there any large or angular boulders of foreign rocks") ]})

    # Unlocated references are observations, not invented unique physical letters.
    reference_specs = [
        ("423", 1, "just when I opened the letter", "Emma's bazaar news; surviving input not identified in this batch.", "unlocated_incoming"),
        ("437", 3, "I had a letter from Caroline yesterday", "Caroline engagement letter; separate from an Emma prompt.", "unlocated_incoming"),
        ("437", 6, "the Post has brought in your own dear note to Katty", "Emma to Catherine, relayed to Darwin; excluded third-party document. No direct Emma-to-Darwin input is invented.", "excluded_third_party_reference"),
        ("440", 4, "I have received a letter from Lyell, forwarded from Shrewsbury", "Lyell letter with Mrs Lyell postscript; search outside Emma packet remains.", "unlocated_incoming"),
        ("448", 1, "when I received a letter & saw Catherine’s hand writing", "Friday Catherine letter, distinct from Saturday's Emma letter.", "unlocated_incoming"),
        ("564", 1, "You are a good old soul for having written to me so soon.", "Current Emma input missing from this packet; do not use courtship letters as a substitute.", "unlocated_incoming"),
        ("601", 1, "though I have not to thank you for one", "Explicitly lacks a new Emma letter to acknowledge.", "negative_receipt_evidence"),
        ("601", 5, "I suppose Susan in her letter told you", "Susan to Emma; excluded third-party correspondence.", "excluded_third_party_reference"),
        ("622", 8, "your scratched out passage would give them plenty of work", "Recipient and route of Emma's crossed-out passage are unclear; do not call it an incoming letter to Darwin.", "document_route_uncertain"),
        ("623", 4, "I have just reread yesterday letter", "Emma's fires/puddings input; another passage mentions an opened wafer. Do not infer an exact number of distinct missing letters.", "unlocated_incoming"),
        ("626", 8, "After long watching the Postman your letter has at last arrived.", "New Emma letter arrives within the composition; no prompt text survives in the assigned set.", "unlocated_incoming"),
        ("704", 3, "Looking over your letter again", "Emma's pretty-brisk update; witness has a date range, so no exact knowledge day is assigned.", "unlocated_incoming"),
        ("667F", 1, "your communication has been slow in arriving here", "Delayed Kemp seed communication; editorial note says not found. Do not substitute the October 699 letter.", "unlocated_incoming"),
        ("672F", 1, "I am glad you are willing to follow my advice", "Unlocated Kemp assent and returned paper; paper and cover letter may differ.", "unlocated_incoming"),
        ("691F", 1, "who writes to me that he is carefully examining it", "Earlier Henslow communication; the October letters cannot supply this September witness.", "unlocated_incoming"),
        ("716F", 1, "Conversing yesterday with Mr. R. Brown", "Oral information from Brown; do not turn the conversation into an incoming letter.", "oral_information"),
        ("464", 1, "I could hardly believe the good news when I opened your letter", "Unlocated earlier Darwin house announcement; specific identification with same-day 463 is not established.", "unlocated_Darwin_document"),
    ]
    references = [{"id": f"REF-EXP-{n:03d}", "witness_id": ident(i), "type": kind,
                   "description": description, "evidence": [ev(i, para, quote)],
                   "creates_prompt": False, "invented_text": None}
                  for n, (i, para, quote, description, kind) in enumerate(reference_specs, 1)]

    result = {
        "schema_version": 1, "period": "1837-1843", "status": "parent_adjudicated",
        "method": "Three gpt-5.6-luna reviewers verified the pilot and XML audit, then performed bounded full-reading first passes for Emma, Kemp, section dates and specialist incoming context. The primary agent read all 56 distinct bodies and notes, checked competing sources, corrected chronology and judged each accepted relation. Proposals alone do not enter the map.",
        "full_read_ids": sorted(letters), "direct_reply_pairs": pairs,
        "cross_correspondent_knowledge": knowledge, "correspondent_replies": reverse,
        "dated_sections": sections, "reference_observations": references,
        "receipt_events": [{"id": "RECEIPT-466-BUNDLE", "witness_id": ident("466"),
                            "date": "1838-12-31", "incoming_candidates": [ident("464"), ident("465")],
                            "identity_status": "bundle identity supported by Tuesday content; Monday receipt explicitly attested",
                            "knowledge_policy": "Conservative content use begins in Tuesday paragraphs 3–7, not Monday paragraphs 1–2.",
                            "evidence": [ev("466", 1, "Many thanks for your two most kind, dear, & affectionate letters, which I received this morning.")]}],
        "within_day_events": [{"witness_id": ident("626"), "date": "1842-05-09",
                              "event": "unlocated Emma letter arrives during composition", "arrival_body_paragraph": 8,
                              "prior_paragraphs": list(range(1, 8)),
                              "rule": "Do not condition earlier paragraphs on newly arrived information even though the calendar date is the same.",
                              "evidence": [ev("626", 1, "I am anxious for the post today"), ev("626", 8, "your letter has at last arrived")]}],
        "additional_exact_date_review_ids": [ident("448"), ident("565F")],
        "individual_limits": {
            ident("565F"): "Incomplete surviving body and conflicting pre/post-conservation dateline readings. Preserve editorial May 11, 1840 and all readings, but hold an unconditional scalar date and complete-letter target pending source review.",
            ident("704"): "Retain 12–24 October 1843. Wednesday suggests October 18, but the editor's October 19 weighing entry has a different weight as well as conflicting relative timing; do not silently force an exact day.",
            ident("471"): "Emma's theological letter remains incoming-only. Later autobiographical evidence that Darwin kept it cannot create a contemporary pre-1844 availability date.",
            ident("669"): "XML upper bound remains 1882. Letter 672F supports an additional composed-by/known-by upper bound of April 24, 1843; keep the original held classification separate pending an explicit refined-period audit.",
            ident("690"): "XML lower bound remains 1809. A September 1843 knowledge witness alone does not prove the incoming letter was composed in 1837–1843. Keep the period hold.",
            ident("716F"): "Editorially resolved December 1 date retains the invalid Nov. 31 header; body has a missing line, which must remain a gap.",
        },
        "rejected_or_candidate_links": [
            {"source": ident("441"), "target": ident("445"), "status": "rejected_as_identified_prompt", "reason": "445 answers 444; the earlier Darwin response to 441 is missing.", "activates_knowledge": False},
            {"source": ident("482"), "target": ident("481"), "status": "rejected_as_identified_antecedent", "reason": "482 answers 466's moving day and prospective dinner; 481 already describes the completed dinner.", "activates_knowledge": False},
            {"source": ident("464"), "target": ident("463"), "status": "unresolved_candidate", "reason": "Shared date and house announcement do not establish this link. 464 already has an announcement while 463 is composed Saturday afternoon in London; a prior missing communication remains plausible.", "activates_knowledge": False},
            {"source": ident("701"), "target": ident("701F"), "status": "unresolved_candidate", "reason": "Same-day dating supplies no receipt order; 701F says he will urge Henslow to finish examining the plant.", "activates_knowledge": False},
        ],
        "corrections": [
            "Kept all five verified pilot pairs; added four single-day pairs and five section-dependent links across three Darwin letters.",
            "Corrected initial Emma reverse-link 482→481 to 482→466; kept 464→463 unresolved.",
            "Added overlooked direct follow-ups 444→448 and 716→716F, the two-letter 464/465→466 bundle, and reverse 492→489.",
            "Accepted 706→701F as an additional reverse reply on the 45-foot requested measurement, contrary to the Luna's candidate-only recommendation.",
            "Retained section-date review corrections for missed 481 and 484 headers; preserved initial report.",
            "Fixed body/editorial quote locators during review. A first Kemp continuation snapshot was not retained by its reviewer; do not claim complete intermediate-version preservation for that file.",
            "Removed unsupported missing-prompt inferences from engagement context, prior housing agreement and Emma's 471 theology letter. The verified reference observations preserve only the documented event or uncertainty.",
        ],
        "training_export_performed": False,
        "training_policy": "Incoming text is never Darwin voice. Keep original source constraints, transmission/gap markers, same-day ordering, section boundaries and author attribution. Multiple incoming letters may form one prompt bundle; repeated responses to the same incoming letter must stay together when splitting evaluation data. No accepted relation is automatically a ready training example.",
    }
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {DEST.relative_to(ROOT)}: {len(pairs)} direct links, {len(letters)} full-read sources")


if __name__ == "__main__":
    main()

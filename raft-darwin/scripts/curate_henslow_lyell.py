"""Explicit parent decisions after Luna first readings; never infer matches.

This additive ledger preserves the earlier expansion ledger and every reviewer
proposal, including proposals rejected in primary-agent adjudication.
"""

import json

from fetch_metadata import ROOT

BASE = ROOT / "reports/1837-1843"
OUT = BASE / "henslow-lyell"
DEST = ROOT / "data/annotations/henslow_lyell_1837_1843.json"


def main():
    batch = {}
    for name in ("letters.jsonl", "context.letters.jsonl"):
        batch.update({r["id"]: r for r in map(json.loads, (OUT / name).read_text().splitlines())})
    letters = dict(batch)
    for path in (BASE / "pilot/letters.jsonl", BASE / "correspondent-review/letters.jsonl",
                 BASE / "correspondent-review/seed-context.letters.jsonl"):
        for r in map(json.loads, path.read_text().splitlines()):
            if r["id"] in letters:
                assert letters[r["id"]]["source"]["sha256"] == r["source"]["sha256"]
            letters[r["id"]] = r
    audit = {r["id"]: r for r in map(json.loads, (BASE / "audit.jsonl").read_text().splitlines())}

    def ident(n):
        return "DCP-LETT-" + n

    def ev(n, paragraph, quote):
        row = letters[ident(n)]
        p = next(p for p in row["paragraphs"] if p["body_paragraph"] == paragraph)
        assert quote in p["text"], (n, paragraph, quote)
        return {"letter_id": ident(n), "body_paragraph": paragraph, "quote": quote,
                "locator": p["locator"], "source": row["source"]}

    def note(n, quote, locator="editorial_footnotes"):
        row = letters[ident(n)]
        text = " ".join(row["header_text"]) if locator == "header_text" else row[locator]
        assert quote in text, (n, locator, quote)
        return {"letter_id": ident(n), "quote": quote, "locator": locator, "source": row["source"]}

    def pair(inc, out, day, reason, quotes):
        return {"incoming_id": ident(inc), "outgoing_id": ident(out),
                "status": "confirmed_direct_reply", "known_by_date": day,
                "actual_receipt_date": None, "response_scope": "single_date_surviving_body",
                "response_sections": [], "rationale": reason, "evidence": [ev(*q) for q in quotes],
                "training_export_ready": False}

    pairs = [
        pair("425", "428", "1838-09-14",
             "Darwin explicitly works through Lyell's letter seriatim, including the Kinnordy invitation, De Beaumont question, principles and British Association. The Friday/September 13 conflict is resolved by the editor as September 14. The missing Prescott document in 428 is a separate reference, absent from 425. Both incoming writing sections precede this response; actual delivery day is unknown.",
             [("425", 5, "begged me this morning to invite you to come here"),
              ("428", 2, "pray give my best thanks to Mr Lyell, for his very kind invitation"),
              ("425", 3, "we may begin to hope that the great principles there insisted on"),
              ("428", 3, "I will now begin & go through your letter seriatim."),
              ("428", 7, "I am glad to hear what a favourable report you give of the British association")]),
        pair("701", "705", "1843-10-14",
             "The Atriplex variety/seed-soil discussion and the distinctive Roman-tomb exhibition receipts jointly identify 701. Darwin's 300 paying visitors follows the 25 pounds at one shilling reported by Henslow. This is stronger than topic or nearest-date matching. The earlier Kemp review already established knowledge of 701 by the same day through 705F.",
             [("701", 1, "only a strange var. of Atriplex patula"),
              ("701", 1, "I trust there is no mistake about the seeds of these plants being in the soil he used"),
              ("701", 1, "realized more than 25£"),
              ("705", 1, "I have written to Mr Kemp to ascertain what precautions he took in sowing his seeds."),
              ("705", 2, "300 people must have paid their shilling fee!")]),
    ]

    def reverse(response, antecedent, reason, quotes, scope=None):
        return {"response_id": ident(response), "antecedent_id": ident(antecedent),
                "status": "supported_reply_by_correspondent", "rationale": reason,
                "evidence": [ev(*q) for q in quotes], "response_paragraphs": scope,
                "is_Darwin_response": False, "activates_Darwin_knowledge": False}

    reverse_links = [
        reverse("425", "424", "Lyell explicitly rereads the already answered letter and returns to the Elements, Glen Roy and Association discussion. A preceding Newcastle reply is referenced but unlocated. This reverse edge alone does not establish Darwin's receipt of 425.",
                [("425", 1, "I must first read your letter again which I answered in a great hurry at Newcastle"),
                 ("424", 1, "Very many thanks for the present of your elements"),
                 ("425", 3, "You hope that the ‘Elements’ may send many")]),
        reverse("338", "384", "The fragment's numbered, colour-coded mineral entry fits Darwin's express request; the DCP editorial dating also uses 384. Supported as a fragmentary reply, with no claim that a complete response or its receipt survives. The inferred dating is not independent corroboration of the content match.",
                [("338", 1, "378 yellow =a prism of about 79 1/2"),
                 ("384", 1, "make soon a list of the numbers (specifying the colour of the paper)")], [1]),
        reverse("701", "691", "Henslow supplies the Atriplex examination requested by Darwin. This may continue a chain containing an unlocated September Henslow communication already attested in 691F; it is not proof that 691 was the immediately preceding letter.",
                [("691", 3, "When you have made out the Atriplex, will you let me hear what you think"),
                 ("701", 1, "the supposed A. hastata will turn out after all to be only a strange var. of Atriplex patula")], [1]),
        reverse("707", "705", "Henslow corrects both Darwin's conflation of the specimens and his specific estimate of 300 visitors. The latter supplies a distinctive response marker beyond the continuing Atriplex topic.",
                [("705", 2, "300 people must have paid their shilling fee!"),
                 ("707", 3, "Many more than 300, & probably double that No."),
                 ("707", 1, "The odd Atriplex came from Lindley alone")]),
    ]

    def knowledge(inc, witness, day, reason, quotes, latest=False):
        return {"incoming_id": ident(inc), "witness_id": ident(witness), "known_by_date": day,
                "status": "supported_cross_correspondent_knowledge", "direct_prompt": False,
                "identification": "content_and_attribution_inference", "rationale": reason,
                "witness_date_policy": ("conservative_latest_possible_writing_date" if latest else "resolved_single_writing_date"),
                "evidence": [ev(*q) for q in quotes]}

    knowledge_links = [
        knowledge("534", "543", "1839-11-10", "Humboldt's regret about Henslow's unfinished Galapagos plants is explicitly attributed to his letter. Incoming Humboldt prose is context only.",
                  [("534", 6, "Combien je regrette que M. Henslow n’ait pu terminer"),
                   ("543", 2, "Humboldt in a letter to Me expresses at great length his vivid regret")]),
        knowledge("534", "660", "1843-01-22", "Later reuse of the same Humboldt regret, already attested in 543. Reuse does not require a second delivery and does not move the earliest knowledge bound forward.",
                  [("534", 6, "Combien je regrette que M. Henslow n’ait pu terminer"),
                   ("660", 2, "remember the regret Humboldt expressed that you had not published some sketch of them")]),
        knowledge("690", "691", "1843-09-02", "The distinctive Ely ovule/nucleus discovery and unidentified Atriplex are explicitly attributed to Lindley's note. This advances the reviewed knowledge bound from September 8 to September 2; the original 1809 lower XML bound and raw period hold remain unchanged.",
                  [("690", 4, "a very curious monster found this year near Ely shows the ovule—its nucleus I mean—to be another of the forms of the growing point"),
                   ("691", 2, "Lindley in a note to me, speaks of some great discovery of a monster near Ely"),
                   ("691", 1, "Lindley tells me in a note that he has sent you an Atriplex to look at unknown to him")]),
        knowledge("690", "696", "1843-09-22", "A later reuse of the Rumex/Atriplex result. The witness remains September 15 OR 22; September 22 is only a conservative latest-possible-writing bound, not an exact writing or receipt date. The earlier 691 witness already establishes knowledge by September 2.",
                  [("690", 5, "Your Scotch seeds proved Rumex Acetosella & this Atriplex"),
                   ("696", 3, "Lindley writes to me, that they turn out to be a common Rumex & a species of Atriplex")], latest=True),
        knowledge("706", "712", "1843-11-04", "Kemp's distinctive seed-husk observation is reused in Darwin's Henslow letter. This is later knowledge reuse, not a second receipt or a direct reply to Kemp; the earlier 710F witness remains earlier.",
                  [("706", 1, "which the plants carried to the top"),
                   ("712", 1, "He informs me he saw each plant bring up the husk of the individual seed which he planted")]),
        knowledge("708", "712", "1843-11-04", "Babington's A. angustifolia identification and contrast with A. hastata are reused. Preserve the discrepancy: 708 reports seeing such plants, while 712 paraphrases this as Babington having reared a facsimile. The match does not independently verify that experiment, and an additional unlocated communication remains possible. Knowledge was already attested in 710F.",
                  [("708", 2, "a variety of the A. angustifolia"),
                   ("708", 3, "A. hastata"),
                   ("712", 1, "he has reared a fac-simile by sowing the seeds of A. angustifolia"),
                   ("712", 1, "He says he knows the A. hastata & that it is very different.")]),
    ]

    sections = []
    for n, specs in {
        "376": [("august29", "1837-08-29", [1, 2, 3, 4]), ("september5", "1837-09-05", [5, 6])],
        "425": [("september6", "1838-09-06", [1, 2]), ("september8", "1838-09-08", list(range(3, 10)))],
        "649": [("october5", "1842-10-05", [1, 2, 3]), ("october7", "1842-10-07", [5, 6, 7, 8])],
    }.items():
        for label, day, paras in specs:
            sections.append({"id": ident(n) + ":" + label, "letter_id": ident(n), "date": day,
                             "paragraphs": paras, "paragraph_fragments": [], "parent_accepted": True,
                             "basis": "DCP date/title plus internal continuation dateline; preserve all original XML constraints.",
                             "evidence": [note(n, letters[ident(n)]["header_text"][0], "header_text")]})
    next(s for s in sections if s["id"] == ident("376") + ":september5")["evidence"].append(ev("376", 5, "Paris, September 5.—"))
    next(s for s in sections if s["id"] == ident("425") + ":september8")["evidence"].append(ev("425", 3, "September 8.—"))
    text649 = next(p["text"] for p in letters[ident("649")]["paragraphs"] if p["body_paragraph"] == 4)
    cut = text649.index("Friday morning")
    for label, start, end in [("october5", 0, cut), ("october7", cut, len(text649))]:
        section = next(s for s in sections if s["id"] == ident("649") + ":" + label)
        section["paragraph_fragments"] = [{"body_paragraph": 4, "char_start": start, "char_end": end,
                                            "text": text649[start:end], "offset_unit": "Unicode code points"}]
        section["basis"] = "The title reads 5 AND 7 October, not two alternative dates. The Friday morning dateline ends extracted paragraph 4 and opens the October 7 continuation. Council attendance is reported retrospectively; no Friday Council date is invented."
        section["evidence"].append(ev("649", 4, "Friday morning"))

    reference_specs = [
        ("355", 1, "I was very glad to receive your letter.", "unlocated_incoming", "Henslow's Gamblingay/headache account; no surviving candidate identified."),
        ("356", 2, "I fear by your letter you cared more about the edible Fungi", "unlocated_incoming", "Henslow's fungi letter; the recorded date of Darwin's witness may instead be Henslow's receipt date."),
        ("378", 1, "The slips from Liverpool, arrived by the twopenny post last night", "proofs_and_annotations", "Received proof slips and corrections; do not invent an accompanying Henslow letter."),
        ("381", 1, "for allowing me to send the slips to you first", "communication_route_uncertain", "Henslow's assent to the proof route; surviving text and delivery route unidentified."),
        ("382", 2, "your message about the Secretaryship", "communication_route_uncertain", "Henslow message; not necessarily a separate paper letter."),
        ("388", 3, "I heard yesterday from Fox", "unlocated_communication", "Fox's planned visit; not a Henslow prompt."),
        ("388", 3, "writing to me himself about the Grant", "unlocated_incoming", "Spring Rice's grant letter; distinct from Henslow correspondence."),
        ("406", 1, "the invitation to the Ray dinner is formal", "unlocated_invitation", "Formal invitation; do not merge it with the Henslow journal letter without evidence."),
        ("406", 4, "Many thanks for your last letter, which delights me touching the Journal", "unlocated_incoming", "Journal/Cambridge society subject is not supplied by the two surviving 338 fragments."),
        ("429A", 3, "Many thanks for your letter, which I received some time.", "unlocated_incoming", "Henslow letter concerning Leonard Jenyns and the Savings Bank; no identified surviving input."),
        ("552", 1, "I have just received your letter.", "unlocated_incoming", "Immediate dispatch of specimens by waggon; unlocated current Henslow request."),
        ("660", 1, "your letter & two sermons", "unlocated_incoming_with_other_documents", "Henslow letter, newspaper and sermons remain distinct document types; none automatically becomes a reconstructed prompt."),
        ("424", 1, "together with your note", "unlocated_incoming_with_book", "Received Elements and Lyell's accompanying note; the book does not stand in for the missing note."),
        ("428", 1, "I only received one letter from you at Newcastle", "unlocated_incoming", "Earlier single Newcastle letter, separate from the September 6/8 letter 425."),
        ("428", 1, "that unfortunate letter of Governor Prescott", "excluded_third_party_reference", "Prescott document being sought; absent from 425, not a Lyell-to-Darwin prompt or verified new receipt."),
        ("428", 1, "my letter which accompanied it", "own_letter_reference", "Darwin's earlier covering letter requested back; do not count this as an incoming prompt."),
        ("480", 4, "Your information about the decaying shells", "unlocated_communication", "Specific supplied shell information; 425 reports shell absence rather than this decaying-shell account. Candidate retained separately."),
        ("554", 1, "Since receiving your note", "unlocated_incoming", "Current Lyell note about Scotsman/coral work; no identified surviving input."),
        ("590", 1, "I will write down my answers as I read", "unlocated_written_queries", "Written geological queries or manuscript; its form is not established as a conventional letter."),
        ("594", 1, "I have just received your note", "unlocated_incoming", "Lyell's glacier/upheaval objection; no identified surviving note."),
        ("595", 1, "Your extract has set me puzzling", "unlocated_extract", "An extract supplied by Lyell; not automatically a distinct accompanying letter."),
        ("602", 1, "Your letter was forwarded me here.", "unlocated_incoming", "Lyell's Silurian excursion letter predates 602; later 604 cannot be this input."),
        ("649", 4, "Once again thank you for your letter.", "unlocated_incoming", "Lyell's coral/dead-reef questions; assign acknowledgment to October 5 fragment, not the following Friday section."),
        ("712", 1, "Until your last note I had not heard that Mr Kemp’s seeds had produced 2 Polygonums.", "unresolved_incoming_identity", "An incoming Henslow note is attested, but 701, 707 and an unlocated follow-up remain alternatives. Do not claim that a separate missing physical letter is proved."),
    ]
    references = [{"id": f"REF-HL-{i:03d}", "witness_id": ident(n), "type": kind,
                   "description": description, "evidence": [ev(n, para, quote)],
                   "creates_prompt": False, "invented_text": None}
                  for i, (n, para, quote, kind, description) in enumerate(reference_specs, 1)]

    candidates = []
    def candidate(source, target, relation, reason, quotes, status="unresolved_candidate"):
        candidates.append({"source": ident(source), "target": ident(target), "relationship": relation,
                           "status": status, "reason": reason, "activates_knowledge": False,
                           "creates_prompt": False, "evidence": [ev(*q) for q in quotes]})

    candidate("701", "712", "incoming_prompt_for", "701 supplies the two Polygonums and soil warning, and is already known by October 14. Repeated replies to an old input are possible, but 'last note' does not uniquely identify 701 here; keep it a serious candidate without inventing receipt order.",
              [("701", 1, "His other two are equally common viz. Polygonum convolvulus & aviculare"),
               ("712", 1, "Until your last note I had not heard that Mr Kemp’s seeds had produced 2 Polygonums.")])
    candidate("707", "712", "incoming_prompt_for", "The first Henslow reviewer promoted this on topic/sequence. 707 contains Atriplex clarification and no two-Polygonum disclosure. Independent review supports holding the unique prompt unresolved; later surviving date is insufficient.",
              [("707", 1, "The odd Atriplex came from Lindley alone"),
               ("712", 1, "2 Polygonums")])
    candidate("338", "366", "replies_to", "Keeling-plant overlap survives only in a fragment; no distinctive answer uniquely ties it to this request.",
              [("338", 2, "your Keeling plant"), ("366", 1, "the number of species in my collection from the Keeling Isls:")])
    candidate("338", "406", "incoming_prompt_for", "Editorially plausible mineral context, but 338 says identification is not yet ascertained and cannot supply 406's Journal content. A missing later identification remains possible; fragment identity alone does not prove receipt before 406.",
              [("338", 1, "not yet ascertained what it belongs to"),
               ("406", 4, "Many thanks for your last letter, which delights me touching the Journal")])
    candidate("425", "480", "incoming_prompt_for", "Lyell's shell-less deposits are relevant context, but Darwin refers specifically to supplied decaying-shell information; the surviving 425 passage is not a unique match.",
              [("425", 8, "entirely destitute of shells"), ("480", 4, "Your information about the decaying shells")])
    candidate("604", "602", "replies_to", "602 expects to return July 15/16 and promises a further note if plans change, while 604 answers the father's persuasion to stay. The actual prompt may be that unlocated update; shared coral charts and illness are insufficient.",
              [("602", 8, "I think we shall return about 15th or 16th"),
               ("604", 1, "your father did righly in persuading you to stay")])
    candidate("579", "716F", "knowledge_before", "Mummy-wheat background does not establish receipt of Henslow's letter. Darwin expressly names a recent oral conversation with Brown; do not replace it with a convenient earlier letter.",
              [("716F", 1, "Conversing yesterday with Mr. R. Brown")], "not_established")
    candidate("343", "346", "knowledge_before", "Invitation and later attendance are compatible, but attendance alone does not identify the invitation as received/read. No new letter-receipt edge is activated.", [], "not_established")

    limits = {
        "338": "Incoming recto/verso fragment only. The 1837–1838 date range is inferred partly from 384/406; no exact receipt or complete prompt is established.",
        "356": "DCP XML says 28 May 1837, but Henslow's written date may be his receipt date. Preserve XML and hold an unconditional composition scalar; do not recode it as Darwin's receipt of an incoming letter.",
        "366": "Keep 12 OR 13 July 1837: body says today 12th, closing Thursday and postmark point to 13th. No forced single composition day.",
        "376": "Incoming two-section letter, August 29 and September 5. Composition dates do not establish Darwin availability.",
        "421F": "Joint petition to Thomas Spring Rice. Lyell is a co-signer, not the recipient; Darwin's signature does not identify him as individual author of the petition prose. Retain as screened metadata/source evidence, excluded from the Darwin–Lyell exchange and individual voice.",
        "425": "Incoming September 6 and 8 sections; Mary Lyell's role as amanuensis does not alone make her co-author. The Prescott document is absent. Receipt is bounded by Darwin's September 14 response, not by either composition date.",
        "428": "Friday/September 13 manuscript inconsistency is editorially resolved as September 14, 1838. Retain both readings; this resolved correction does not force a date hold.",
        "432": "Monday 13 and tomorrow 14 manuscript wording is editorially resolved as November 12, 1838. Preserve the correction without inferring an incoming engagement-congratulation letter here.",
        "505": "Henslow's note to Darwin is written at the foot of a William Herbert-to-Henslow letter. Only Henslow's retained note is in this Darwin-involved body; underlying third-party correspondence is excluded.",
        "579": "Fragment from a later published quotation; publication year is not contemporary receipt evidence. No pre-1844 availability established.",
        "582": "Henslow thyme letter: later publication/use is provenance, not proof of Darwin's knowledge during 1837–1843.",
        "598": "Henslow mouse note: use in a later Origin edition does not establish pre-1844 receipt.",
        "605": "September–December 1842 memorandum with uncertain date, not July 1841 correspondence. Its numerical adjacency to 604 is not chronological proof.",
        "649": "Written October 5 AND 7, 1842. Friday morning at the end of extracted paragraph 4 introduces the later section; character offsets preserve the mixed paragraph. A Council report in past tense does not prove a Friday Council meeting.",
        "670": "Incoming fragment only. Arrival in town may have been learned orally; no missing Darwin prompt is asserted from that alone.",
        "690": "Raw XML lower bound remains 1809 and period hold remains. Newly identified witness 691 advances demonstrated knowledge to September 2, 1843; it does not prove an 1837-or-later composition.",
        "691": "DCP resolves Saturday as September 2, 1843 from Henslow's September 8 receipt annotation. Composition and recipient receipt remain separate; the latter is not Darwin's knowledge date for Lindley's input.",
        "696": "Keep September 15 OR 22, 1843. A September 22 knowledge bound is conservative across alternatives and is not a selected exact writing/receipt day.",
        "699F": "Source page explicitly has no online transcription. Its placeholder and editorial summary are not Darwin prose and not a full-body reading. Keep the 1830–1843 XML hold; exclude from voice, prompt targets and grounding prose.",
        "708": "Babington says he has seen comparable plants, whereas 712 says he reared a facsimile. Preserve the paraphrase discrepancy; the knowledge link is not proof of the reported experiment.",
        "712": "Clear acknowledgment of a Henslow note; unique surviving prompt unresolved. 701 supplies Polygonums and soil doubt, 707 Atriplex clarification; prior 710F already relays Henslow's Polygonum information. Kemp/Babington text is attributed knowledge, never Darwin voice.",
        "724": "Darwin letter contains tabular/diagram labels (paragraphs 2–10 and 12–20); preserve source layout and do not flatten labels into ordinary prose at export. No identified incoming prompt.",
    }
    # Every inspected record gets an explicit parent disposition. The reasons
    # below are judgments from full reading, not copied reviewer summaries.
    outgoing_notes = {
        "353": "Reports publication and specimen work; prior in-person discussion does not identify an incoming prompt.",
        "355": "Explicit current Henslow letter, unlocated; earlier surviving records do not supply its account.",
        "356": "Fungi reply is explicit but prompt unidentified; witness composition date needs review.",
        "361A": "Beaufort's advice may be oral; the enclosed application is Darwin's own document.",
        "366": "Botanical queries and salt-water questions; no identified incoming prompt.",
        "368": "Requests answers and discusses election; no specific received body identified.",
        "373": "Receipt of fungus/plant box is a physical parcel, not proof of a letter prompt.",
        "378": "Corrected proof slips received; keep annotations and possible accompanying messages distinct.",
        "381": "Acknowledges assent to proof routing; the communication itself is unidentified.",
        "382": "Secretaryship message acknowledged, delivery medium uncertain.",
        "384": "Requests specimen numbers/colours; later fragment 338 is a reverse response, not an input.",
        "388": "Fox's intended visit and Spring Rice's grant letter supply context; no Henslow input identified.",
        "400": "Parcel for Miller and Mrs Henslow's invitation; do not turn the latter into a J. S. Henslow prompt.",
        "406": "Formal invitation, mineral information and Journal letter may be separate communications; 338 remains a partial candidate.",
        "429A": "Acknowledges Henslow letter, unlocated.",
        "543": "Uses Humboldt 534 as knowledge while writing to Henslow; no direct Henslow prompt.",
        "552": "Current specimen request acknowledged; source not identified.",
        "573": "Remembers lecture and poses new request; oral context is not a letter input.",
        "615": "Brown called the previous day; preserve oral source of the political request.",
        "642": "Specimen/museum gift communication; no identified inbound text.",
        "660": "Missing Henslow letter, newspaper and sermons; later reuse of Humboldt 534 remains context.",
        "691": "Lindley 690 supplies knowledge; examination request to Henslow is not a reply to a surviving Henslow letter.",
        "699F": "Metadata/source page only; no body exists in this preserved online record.",
        "705": "Confirmed reply to 701 on specimens, doubts and exhibition receipts.",
        "712": "Henslow note acknowledged but unique direct prompt unresolved; attributed Kemp/Babington knowledge accepted separately.",
        "367": "Question about Lyell's shell work does not establish a missing incoming letter; it may refer to shared work.",
        "394": "Answers geological questions; no surviving incoming source identified, medium uncertain.",
        "421F": "Joint petition to Spring Rice, outside the Darwin–Lyell exchange; no individual voice attribution.",
        "424": "Received Elements plus unlocated note; later 425 answers this letter.",
        "428": "Confirmed reply to both dated sections of 425; earlier Newcastle letter and Prescott document separate.",
        "432": "Announces engagement; anticipated congratulations are not an already received prompt.",
        "480": "Specific shell information may come from an intervening note; 425 is only a candidate.",
        "554": "Explicit receipt of Lyell note, unlocated.",
        "590": "Answers written queries/manuscript; do not assume complete formal letter input.",
        "592": "Discusses Agassiz material; source medium/route and prompt identity not established.",
        "594": "Explicit current Lyell note, unlocated.",
        "595": "Received extract acknowledged; distinct document type retained.",
        "602": "Explicit earlier forwarded Lyell letter; later 604 cannot supply it.",
        "605": "1842 memorandum arising from discussion; no proved incoming letter.",
        "649": "Two writing sections answer unlocated coral questions; preserve character-level date boundary.",
        "653": "Solicitor/Council material and pamphlet are third-party documents, not proof of a missing Lyell prompt.",
        "696": "Lindley's results reused; request for a future dictated letter is not evidence that it already arrived.",
        "724": "Tosca discussion may follow conversation or reading; no identified incoming prompt. Preserve diagrams.",
    }
    all_sources = set(batch)
    no_body = {ident("699F")}
    joint = {ident("421F")}
    pair_targets = {p["outgoing_id"] for p in pairs}
    dispositions = []
    for i, row in sorted(batch.items()):
        outgoing = audit[i]["direction"] == "from_darwin"
        status = ("confirmed_response" if i in pair_targets else "grounding_candidate_no_identified_prompt") if outgoing else "incoming_context_only"
        if i in no_body:
            status = "source_record_only_no_transcription"
        elif i in joint:
            status = "excluded_joint_petition"
        dispositions.append({"letter_id": i, "parent_source_record_read": True,
                             "parent_body_read_in_full": i not in no_body,
                             "paragraphs_read": [p["body_paragraph"] for p in row["paragraphs"]],
                             "disposition": status,
                             "reason": outgoing_notes.get(i.removeprefix("DCP-LETT-"), "Preserve incoming author and date constraints; availability is supported only by explicit accepted attestations, never by composition date alone."),
                             "limit": limits.get(i.removeprefix("DCP-LETT-")),
                             "original_metadata": audit[i], "source": row["source"]})

    result = {
        "schema_version": 1, "period": "1837-1843", "status": "parent_adjudicated",
        "method": "Luna-first workflow: separate gpt-5.6-luna full readings for Henslow and Lyell, independent Luna date/attribution review, then primary-agent full-source adjudication of positives, negatives and competing sources. A follow-up Luna read four specialist incoming sources and the Darwin witnesses; a further independent check reviewed 712. The primary agent read all retained bodies, headers and notes and distinguishes source-page inspection from unavailable transcription. Initial reviewer reports and the prior decision ledger are preserved; proposals are not automatically promoted.",
        "reviewed_record_ids": sorted(all_sources), "full_read_ids": sorted(all_sources - no_body),
        "body_unavailable_ids": sorted(no_body), "non_individual_voice_ids": sorted(joint),
        "direct_reply_pairs": pairs, "cross_correspondent_knowledge": knowledge_links,
        "correspondent_replies": reverse_links, "dated_sections": sections,
        "reference_observations": references, "receipt_events": [], "within_day_events": [],
        "additional_exact_date_review_ids": [ident("356")],
        "individual_limits": {ident(k): v for k, v in limits.items()},
        "rejected_or_candidate_links": candidates, "letter_adjudications": dispositions,
        "date_evidence": [note("428", "Friday was the 14th of September."),
                          note("356", letters[ident("356")]["editorial_footnotes"]),
                          note("691", letters[ident("691")]["editorial_footnotes"])],
        "corrections": [
            "Added two Darwin reply pairs, six cross-correspondent knowledge/reuse attestations and four incoming-author reply edges; incoming prose remains outside Darwin voice.",
            "Rejected the first Henslow review's promotion of 707→712; retained 701 and 707 as possible prompts. Independent review's assertion of a definitely separate missing note is stronger than the evidence: identity remains unresolved.",
            "Strengthened 701→705 and 707→705 identification with the distinctive 300-visitor exchange, absent from the reviewer's quoted rationale.",
            "Preserved the revised Lyell review's downgrade of 604→602; a missing change-of-plan note may intervene. Removed the initial claim that 425 contains Prescott material.",
            "Corrected chronology review's handling of 649: October 5 AND 7, with a mid-paragraph continuation marker; a Friday Council meeting is not established.",
            "Held 356's composition day because its recorded date may be Henslow's receipt. Resolved editorial calendar corrections in 428 and 432 do not automatically block those dates.",
            "Excluded 421F joint petition from individual voice and the Darwin–Lyell exchange. Counted 699F as inspected source metadata, not as a full-read transcript.",
            "Accepted later knowledge reuse in 660 without requiring a second Humboldt transmission. Allowed conservative latest-date knowledge in 696 while retaining both writing-date alternatives.",
            "Retained Babington seen-versus-reared discrepancy between 708 and 712. Topic overlap does not verify Darwin's paraphrase as an independent experiment.",
            "Dropped reviewer inferences that questions in 367, future correspondence requested in 696, third-party material in 653 or Lyell's knowledge of travel in 670 prove missing incoming or outgoing letters.",
        ],
        "training_export_performed": False,
    }
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (OUT / "dossiers.jsonl").write_text("".join(json.dumps(d, ensure_ascii=False) + "\n" for d in dispositions))
    print(json.dumps({"records": len(all_sources), "available_transcriptions": len(all_sources - no_body),
                      "new_direct_pairs": len(pairs), "knowledge_links": len(knowledge_links),
                      "reverse_links": len(reverse_links), "reference_observations": len(references)}))


if __name__ == "__main__":
    main()

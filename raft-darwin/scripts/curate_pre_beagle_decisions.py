#!/usr/bin/env python3
"""Explicit parent decisions after full reading; never infer links from search hits.

This is a reproducible record of human/model curation choices, not a matcher.
The independent proposals remain unchanged beside these adjudicated decisions.
"""
import copy
import json
from pathlib import Path

from pre_beagle_review_helpers import AUDIT, FOLDER, LETTERS, evidence as ev, ident

INITIAL = json.loads((FOLDER / "initial_survey.json").read_text())
REVIEWS = {r["letter_id"]: r for r in INITIAL["letters"]}
PARENT = {"batch_id": "pre-beagle-1828-1831", "status": "adjudicated",
          "edges": [], "candidate_links": [], "unlocated_nodes": [],
          "context_identity_policies": [], "outgoing_overrides": {},
          "outgoing_adjudications": {}, "luna_adjudications": []}


def obs(n, index):
    return copy.deepcopy(REVIEWS[ident(n)]["observations"][index])


def span(n, paragraph, quote):
    return ev(n, paragraph, quote)


def endpoint(value):
    return value if str(value).startswith("UNLOCATED-") else ident(value)


def edge(kind, source, target, basis, evidence, candidate=False, **extra):
    source, target = endpoint(source), endpoint(target)
    row = {"id": f"pre-{kind}-{source}-{target}", "relationship": kind,
           "source_id": source, "target_id": target,
           "review_status": "candidate" if candidate else "reviewed",
           "confidence": "unresolved" if candidate else "high",
           "basis": basis, "evidence": evidence, "batch_id": "pre-beagle-1828-1831", **extra}
    PARENT["candidate_links" if candidate else "edges"].append(row)
    return row


def authority(n, side):
    return copy.deepcopy(AUDIT[ident(n)][f"{side}_evidence"])


DARWIN = authority(42, "sender")
PEOPLE = {"W. D. Fox": authority(42, "recipient"), "C. T. Whitley": authority("45A", "recipient"),
          "J. M. Herbert": authority(47, "recipient"), "J. S. Henslow": authority(102, "recipient"),
          "Caroline Darwin": authority(145, "recipient"), "Catherine Darwin": authority(296, "sender"),
          "S. E. Darwin": authority(119, "recipient"), "Robert FitzRoy": authority(131, "recipient"),
          "G. Peacock": authority(106, "sender"), "A. Sedgwick": authority(116, "sender")}


def missing(identifier, direction, correspondent, witnesses, **extra):
    person = PEOPLE.get(correspondent, [{"text": correspondent, "attributes": {},
                                      "identity_status": "named_reference_without_resolved_authority"}])
    row = {"id": identifier, "node_kind": "referenced_unlocated_letter", "direction": direction,
           "label": f"{'Darwin to ' if direction == 'from_darwin' else ''}{correspondent} — unresolved letter reference",
           "sender_evidence": DARWIN if direction == "from_darwin" else person,
           "recipient_evidence": person if direction == "from_darwin" else DARWIN,
           "identity_provenance": "Participant identity inferred from cited body; any authority copied from an existing catalogue record is not a header of a newly located letter.",
           "original_csv": None, "sent_date_constraints": [], "text_available": False,
           "document_existence_attested": True, "lost_or_destroyed_claimed": False,
           "reference_identity_note": "A reference node, not a claim of a distinct physical document. It may alias another missing reference or an incompletely identified catalogue letter.",
           "search_scope": "Pinned 1828–1831 batch and comparison sources; not an exhaustive archive search.",
           "evidence": witnesses, "batch_id": "pre-beagle-1828-1831", **extra}
    PARENT["unlocated_nodes"].append(row)
    return identifier


def override(n, summary=None, observation_updates=None, adjudication=None):
    row = PARENT["outgoing_overrides"].setdefault(ident(n), {})
    if summary:
        row["summary"] = summary
    if observation_updates:
        row.setdefault("observations", {}).update({str(k): v for k, v in observation_updates.items()})
    if adjudication:
        PARENT["outgoing_adjudications"][ident(n)] = adjudication


# A physical gift is identified; reading the accompanying note is not proved.
gift_evidence = [span(99, 1, "accept the accompanying Coddington’s Microscope"),
                 span(100, 3, "a most magnificent anonymous present of a Microscope"),
                 span(100, 3, "one would like to know who it was")]
edge("source_event_match", 99, 100,
     "Distinctive anonymous microscope gift, corroborated by the edition's note to 99. The event is known; the complete note's reading is not established.",
     gift_evidence, event_scope="An anonymous donor has given Darwin a microscope; the donor's identity is unknown to him.")
PARENT["context_identity_policies"].append({
    "letter_id": ident(99), "context_author_label": "anonymous donor",
    "archival_author_identity_available_to_persona": False,
    "full_note_reading_established_at_100": False,
    "scope": "Use anonymous attribution unless a separately reviewed later witness establishes Darwin's identification. Original Herbert metadata remains archival only.",
    "evidence": gift_evidence,
})

# Both members of the offer bundle remain separately attributed.
offer = {
    105: span(105, 1, "I have been asked by Peacock who will read & forward this to you"),
    106: span(106, 1, "you may consider the situation as at your absolute disposal"),
}
for source in (105, 106):
    witness = span(107, 2, "I did not hear of poor Mr. Ramsays loss till a few days before your letter.") if source == 105 else span(107, 1, "Mr. Peacocks letter arrived on Saturday, & I received it late yesterday evening.")
    edge("knowledge_before", source, 107, "Named offer letter and matching offer context; 105's Ramsay reference separately identifies the Henslow component.", [offer[source], witness])
edge("replies_to", 107, 105, "Darwin's refusal is addressed to Henslow, acknowledging his offer and the Ramsay news.", [offer[105], span(107, 2, "I did not hear of poor Mr. Ramsays loss till a few days before your letter.")])
edge("knowledge_before", 106, 112, "Darwin follows Peacock's specific instruction to notify Beaufort. The letter to Beaufort is not a direct reply to Peacock.",
     [span(106, 4, "making known your acceptance to Captain Beaufort"), span(112, 1, "according to Mr. Peacocks desire")])
for target, paragraph, quote in ((120, 1, "a joint one from Henslow & Peacock of Trinity"),
                                 (121, 2, "I found letters from Peacock & Henslow")):
    for source in (105, 106):
        edge("knowledge_before", source, target, "Explicitly named offer communications; 105 and 106 establish how they were forwarded together, without merging authorship.", [offer[source], span(target, paragraph, quote)])
edge("knowledge_before", 106, 123, "Darwin and FitzRoy discuss the previously received Peacock offer; additional use of an already identified source.", [offer[106], span(123, 4, "the letter of Peacock")])

# The exact week-long postponement and quotation identify 135 across recipients.
edge("knowledge_before", 135, 138, "Darwin reports hearing from FitzRoy yesterday and receiving an extra week; 135 grants exactly another week and arrival on the 17th. This is correspondence-specific evidence, not generic delay vocabulary.",
     [span(135, 9, "You can remain away another week so as to be here on the 17th. if you like."), span(138, 4, "I heard from Cap Fitzroy yesterday he gives me a week more of respite")],
     receipt_constraints={"relative_statement": "yesterday", "source": ident(138), "exact_receipt_date": None})
fitz_quote = [span(135, 1, "Damn these shoregoing fellows they never know their own minds"), span(139, 1, "damn those shore-going fellows")]
edge("knowledge_before", 135, 139, "Distinctive quoted phrase identifies the source. The witness retains 4-or-11 October alternatives.", fitz_quote)
edge("replies_to", 139, 135, "Darwin reassures FitzRoy by returning FitzRoy's distinctive phrase.", fitz_quote)

account = [span(143, 1, "you ought to have pd. him 12\"7\"— instead of 7\"12."),
           span(144, 1, "If I merely trusted to recollection, I should yet think it was 7’12."),
           span(144, 1, "I am very much obliged for your directions about consingment")]
edge("knowledge_before", 143, 144, "The reversed sum, consignment instructions and brother's address identify the incoming correction.", account)
edge("replies_to", 144, 143, "Darwin answers Henslow's accounting correction and consignment directions.", account)

# Replies in the incoming direction do not date Darwin's receipt of them.
edge("replies_to", 125, 121, "Whitley's ordering/cannibal/fungus response and forwarding of Sedgwick's letter answer specific features of 121.",
     [span(125, 2, "your cannibal shooting, fungus describing anticipations"), span(121, 2, "It is such capital fun ordering things"), span(121, 8, "forward to Caernarvon a letter directed Prof: Sedgwick")])
edge("replies_to", 143, 140, "Henslow quotes the unusual £1 payment mistake and supplies the requested consignment address.",
     [span(143, 1, "your attempt to cheat my Brother of 1£"), span(140, 3, "there was 6 instead of 7’10"), span(140, 4, "about consingements")])
edge("replies_to", 150, 147, "Henslow answers Darwin's surds difficulty and the specific judgment that the expedition would not suit Jenyns. This incoming reply creates no knowledge date for 150.",
     [span(150, 1, "In working your Surds remember"), span(150, 2, "would have been no way fitted for L. Jenyns"), span(147, 1, "as for those wicked sulky surds"), span(147, 1, "I think L Jenyns did very wisely in not coming")])
edge("replies_to", 135, 131, "FitzRoy acknowledges the London parcel and answers the specific Beechey book question. His young-Owen answer concerns a separate unlocated Darwin request.",
     [span(135, 4, "I received the parcel from London & your letter"), span(135, 5, "I have Beechey’s Voyage"), span(131, 1, "I send with this the thickest sort"), span(131, 2, "Have you Cap. Beecheys voyage to the Pacific?")])

# Explicit reference decisions, selected manually from the initial full reading.
INCOMING = [(43,0),('45A',0),(46,0),(49,0),(49,1),(49,2),(52,0),(57,0),(59,0),(61,0),
            (62,0),(63,0),(63,1),(64,0),(64,1),(66,0),(68,0),(70,0),(71,0),(72,0),
            (75,0),(76,0),(79,0),(81,1),(82,0),(84,0),(86,0),(87,0),(92,0),(96,0),
            (101,0),('102A',0),(103,0),(120,0),(121,1),(128,0),(132,0),(142,0),
            (145,0),(145,1),(146,0),(148,0),(152,0)]
REFERENCES = {}
for number, index in INCOMING:
    observation = obs(number, index)
    correspondent = observation.get("correspondent") or ("J. S. Henslow" if number == 152 else "Robert FitzRoy")
    if number == 64 and index == 1:
        correspondent = "Pulleine (given name unresolved in this passage)"
    if number == 81:
        correspondent = "Simpson (given name not established by this passage)"
    identifier = f"UNLOCATED-PRE-IN-{number}-{index}"
    node = missing(identifier, "to_darwin", correspondent, observation["evidence"],
                   reference_scope="bundle" if observation.get("referenced_letter_count", 1) > 1 else "unresolved_reference",
                   minimum_letter_count_in_this_reference=observation.get("referenced_letter_count", 1))
    REFERENCES[(str(number), index)] = node
    edge("knowledge_before", node, number, "Explicit acknowledgment of this incoming reference; no original writing date or missing text is supplied. " + observation["interpretation"], observation["evidence"])
    if observation.get("direct_reply") is True or number in (142, 152):
        edge("replies_to", number, node, "Darwin answers or acknowledges the addressed correspondent's incoming letter; the missing source text prevents a training pair.", observation["evidence"])

# Original wording keeps receipt timing distinct from conservative known-by dates.
for row in PARENT["edges"]:
    if row["relationship"] == "knowledge_before" and row["source_id"] == REFERENCES[("120",0)]:
        row["receipt_constraints"] = {"reported_personal_receipt_date": "1831-08-29",
                                      "statement": "Monday 29th of August; I found your letter there",
                                      "not_a_replacement_for_original_sent_date": True}
    if row["relationship"] == "knowledge_before" and row["source_id"] == ident(106) and row["target_id"] == ident(107):
        row["receipt_constraints"] = {"arrival_at_destination": "Saturday", "Darwin_personal_receipt": "late yesterday evening",
                                      "calendar_conversion_performed": False}

# Explicitly unread letter: identify the reference, hold the catalogue match.
unread_evidence = [span(123, 2, "I received one to day from Prof: Sedgwick, but have not yet had time to read it.")]
unread = missing("UNLOCATED-PRE-SEDGWICK-UNREAD-123", "to_darwin", "A. Sedgwick", unread_evidence,
                 reported_reading_status="explicitly_unread_at_123", possible_catalogued_identity=ident(116))
edge("receipt_without_reading", unread, 123, "Receipt of a Sedgwick letter is explicit, and so is not having read it. Catalogue identity remains unproved.", unread_evidence)
edge("receipt_without_reading", 116, 123, "116 is a plausible Sedgwick letter before this witness, but author/date alone does not uniquely identify it.", unread_evidence, candidate=True)

# Actual earlier Darwin writing, not promised or unwritten future letters.
OUTGOING = [(49,3,'C. T. Whitley'),(57,1,'W. D. Fox'),(75,1,'Baker'),(87,1,'family at home; individual addressee unresolved'),
            (92,1,'Baker'),(100,2,'Baker'),(102,1,'Mr Ramsay'),(107,2,'G. Peacock'),
            (114,0,'J. S. Henslow'),(121,2,'A. Sedgwick'),(145,2,'Mr Ash'),(147,1,'Mr Ash')]
OWN_REFERENCES = {}
for number, index, correspondent in OUTGOING:
    observation = obs(number, index)
    node = missing(f"UNLOCATED-PRE-OUT-{number}-{index}", "from_darwin", correspondent, observation["evidence"])
    OWN_REFERENCES[(str(number), index)] = node
    edge("refers_to_own_letter", number, node, observation["interpretation"], observation["evidence"])
    if number == 57:
        PARENT["unlocated_nodes"][-1]["reported_delivery_status"] = "not_forwarded_when_discovered"

# Missing outgoing texts established by incoming acknowledgments.
for incoming, paragraph, quote in [
    (93,2,"I answer your kind letter"),
    (116,1,"the stupid red nosed waiter did not shew me your letter till a few hours before I started"),
    (124,1,"I was no less surprized than delighted to see your handwriting once more on a letter addressed to me"),
    (133,1,"I was very glad to receive your letter"),
    (135,1,"Before you judge of my conduct"),
    (141,1,"Our letters must have crossed on the road"),
]:
    evidence = [span(incoming,paragraph,quote)]
    record = AUDIT[ident(incoming)]
    name = ' '.join(filter(None,(record['original_csv']['sender_forename'],record['original_csv']['sender_surname'])))
    PEOPLE[name] = authority(incoming,"sender")
    node = missing(f"UNLOCATED-PRE-DARWIN-ANSWERED-{incoming}","from_darwin",name,evidence)
    edge("replies_to",incoming,node,"Incoming author explicitly answers a Darwin letter not identified in the surviving batch. This establishes the other person's receipt, not Darwin's receipt of the incoming answer.",evidence)

# Keep own-document identifications and possible repeated references tentative.
for number, index, earlier in [(45,0,43),(46,1,45),(60,2,59),(61,1,60),(62,1,61),(76,1,75),
                               (96,2,94),(100,1,96),(101,1,100),(117,0,115),(122,1,119),(127,0,126)]:
    observation=obs(number,index)
    edge("refers_to_own_letter", number, earlier, observation["interpretation"] + " Retained as a candidate after full reading; no recipient receipt is inferred.", observation["evidence"], candidate=True)
for source, target, number, index in [
    (REFERENCES[("63",0)],REFERENCES[("62",0)],63,0),
    (REFERENCES[("96",0)],REFERENCES[("92",0)],96,0),
    (OWN_REFERENCES[("147",1)],OWN_REFERENCES[("145",2)],147,1),
]:
    edge("possibly_same_document",source,target,"References may denote the same physical document; do not count them as established distinct letters or merge dates automatically.",obs(number,index)["evidence"],candidate=True)
edge("knowledge_before",REFERENCES[("103",0)],120,"The earlier hurtful Fox letter in 120 plausibly refers to the accusation answered in 103; exact identity remains unresolved.",
     [span(103,5,"how grieved I am to find that you think me capable of telling base, hollow & deliberate falsehoods"),span(120,2,"You cannot imagine how much your former letter annoyed & hurt me.")],candidate=True)
edge("knowledge_before",90,92,"Feversham and Simpson are shared information, but the address could already be known; no specific receipt acknowledgment identifies 90.",
     [span(90,1,"an awful distance from Feversham"),span(92,5,"Simpson’s direction is Feversham Kent")],candidate=True)
edge("knowledge_before",150,152,"Kind and affectionate advice makes 150 plausible, but the Ramsay memorial is absent and no unique date or passage securely identifies it as the acknowledged last letter.",
     [span(150,2,"I therefore exhort you most sincerely & affectionately"),span(152,1,"I am very much obliged for your last kind & affectionate letter"),span(152,2,"I shall be very glad to have some memorial of Ramsay")],candidate=True)

override(64,observation_updates={1:{"correspondent":"Pulleine (given name unresolved in this passage)"}})
override(100,"Reports an anonymous microscope gift matching 99's event; the donor's identity and reading of the accompanying note remain unestablished.",
         {0:{"kind":"supported_source_event_match","interpretation":"99 documents the anonymous microscope event. 100 does not prove the whole note was read; Herbert remains archival attribution only."}},
         "Accept the event match; reject both full-note knowledge activation and the label explicitly unread. Unknown reading and known unread are different states.")
override(107,adjudication="Accept knowledge from both 105 and 106, but only 105 is a direct prompt for this Henslow-addressed response. Correct the reviewer direction and cross-correspondent labels.")
override(94,"Carries out Fox's business instructions through Baker; may continue the same input as 92.")
override(101,"Answers Fox's response to Darwin's declined visit; the earlier outgoing letter is possibly 100, with identity held as a candidate.")
override('102A',"Answers an unlocated Whitley letter; reports hearing from Watkins, whose later 130 cannot be the source.")
override(114,"Announces arrival at Cambridge and refers to a second earlier Darwin-to-Henslow letter; requests a spoken answer.")
override(121,adjudication="105 and 106 are cross-correspondent context. 125 is a later incoming reply to 121, not knowledge already available for writing 121.")
override(123,observation_updates={0:{"interpretation":"A Sedgwick letter was physically received and explicitly unread; 116 is only a candidate identity. No full-text knowledge is activated."}},
         adjudication="Accept an unread receipt reference, hold the specific 116 identity; the reviewer's stronger incoming-side identity statement is not accepted.")
override(138,observation_updates={0:{"kind":"supported_cross_correspondent_knowledge","interpretation":"The precise extra-week permission in 135 identifies the update Darwin relays to Henslow. Receipt wording yesterday remains separate from the 28 September known-by witness."}},
         adjudication="Accept 135→138 on the exact extra-week permission and planned 17th arrival. The reviewer's first rejection omitted this portion of 135 paragraph 9.")
override(139,"Answers FitzRoy 135 through a distinctive quotation; the 4-or-11 October alternatives prevent an automatically dated prompt pair.",
         {0:{"kind":"supported_direct_reply","interpretation":"Quoted shoregoing-fellows phrase identifies 135; preserve uncertain witness date."}})
override(142,"Replies to an unlocated FitzRoy letter about shipping baggage on another vessel and obtaining talc; 135 lacks those details.",
         {0:{"kind":"unlocated_incoming","candidate_source_ids":[],"interpretation":"135 rejected as this source. Explicitly acknowledged baggage/talc advice belongs to an unresolved FitzRoy incoming reference."}})
override(144,"Answers Henslow 143 on accounting and consignment; the lost earlier letter or bill remains an unresolved reference.",observation_updates={0:{"kind":"supported_direct_reply","interpretation":"143's accounting correction and consignment address identify the prompt."},
                                1:{"kind":"unresolved_prior_letter_or_bill_reference","interpretation":"The lost account or earlier letter is not securely a second incoming document distinct from the current correction; retain as a reference without another activated node."}})
override(147,observation_updates={0:{"kind":"advice_channel_unresolved","interpretation":"Earlier mathematical advice is acknowledged, but its medium is implicit. 150 contains further surds advice and answers 147; its later date prevents it being 147's input."}},
         adjudication="Accept incoming150 replying to Darwin147. Reject knowledge150→147. Do not promote the earlier implicit advice channel to a definite missing letter.")
override(152,"Thanks Henslow for an unidentified affectionate letter; 150 remains a plausible candidate, and the Ramsay memorial source is unresolved.",
         {0:{"kind":"unlocated_incoming","correspondent":"J. S. Henslow","direct_reply":True,"interpretation":"A last affectionate incoming letter is attested. 150 is plausible but not securely identified; missing-reference identity may alias 150."},
          1:{"kind":"unresolved_knowledge_source","candidate_source_ids":[],"interpretation":"The Ramsay memorial offer is absent from 150. Do not use it to establish the 150 identity or invent a separate memorial-offer letter."}},
         "Reject the initial distinctive-memorial match. Keep150→152 candidate only; preserve an explicit incoming reference without asserting a separate physical document.")

PARENT["luna_adjudications"] = [
    {"group":"all","decision":"Reviewer outputs are proposals, not active annotations. Parent normalizes directions and applies only the edges in this file. Initial and revised reviewer outputs are preserved; reading coverage does not imply every proposal is correct."},
    {"group":"fox","decision":"Reject self-loops from the first draft; acknowledge missing Fox inputs using separate reference nodes. Turner, Catherine, Pulleine, Simpson and Matthew correspondence to/from Darwin is in scope even when addressed to someone other than Fox. Do not promote implicit channels in55/80/81 or third-party Irish-friend-to-Fox/Pulleine-to-Fox letters in61."},
    {"group":"fox","decision":"99→100 is a scoped gift-event match, not a statement that the note was unread and not proof of full-note reading. 100→101 own-letter identity remains a candidate. Matthew93 replying to a missing Darwin letter is an incoming reply, never Darwin-knowledge evidence."},
    {"group":"voyage","decision":"Correct reversed knowledge links and cross-correspondent reply claims:105/106→107,105/106→121 are knowledge; only107→105 is a direct Darwin reply. Incoming125→121,143→140,150→147 and135→131 are replies in the other direction and establish no Darwin receipt."},
    {"group":"voyage","decision":"135→138 accepted on precise extra-week permission,135→139 accepted on quoted wording;135→142 rejected. 116 identity for the unread Sedgwick letter in123 stays candidate. Retained raw incoming-side assertions identifying116 or calling105/106 unlocated are not promoted."},
    {"group":"voyage","decision":"150→152 remains candidate. The memorial content is absent from150; it cannot be used to identify that input. 147's earlier mathematical advice has an unresolved channel;150 is later and separately responds to147."},
    {"group":"family","decision":"Keep115's held letter and119's vague letter as identity/read-status uncertainty, not proof of unreadness. Parcels and Catherine's reported dispatch in41 are not Darwin receipt. Own115/117,119/122,126/127 remain candidate identities, and133→149 event overlap is rejected."},
]
PARENT["report_findings"] = [
    "**Three usable surviving prompt pairs in this batch:** 105 → 107 (Henslow's offer and Darwin's refusal), 125 → 135A (Whitley's farewell, previously established), and 143 → 144 (Henslow's bill correction and consignment directions). These remain curation candidates for a future exporter; no training was run.",
    "**A fourth direct reply has unresolved timing:** 135 → 139 is identified by the quoted shoregoing-fellows phrase. Letter 139 retains its original 4-or-11 October alternatives and no scalar writing date, so it is held out of automatic prompt pairing.",
    "**Knowledge can cross correspondents:** 135's extra week is relayed in 138 to Henslow. The separately attributed Henslow 105 and Peacock 106 offer letters are known by 107 and reused in later accounts to Fox and Whitley. Only Henslow 105 is the direct prompt for 107.",
    "**Receipt is not reading:** 123 explicitly says a Sedgwick letter was received that day but not read. The letter's identity as 116 is plausible, not proved. Neither the unresolved reference nor 116 supplies content to 123.",
    "**The anonymous microscope remains anonymous:** 99 and 100 describe the same gift event. The archive identifies Herbert, but Darwin in 100 wants to know who the donor was. Full-note reading is unproved; the gift fact and archival author are kept separate.",
    "**Two tempting matches fail:** 135 does not contain the other-vessel/talc advice answered in 142. And 150 contains no Ramsay memorial reference; 150 → 152 stays a candidate, with an explicit incoming reference whose identity is unresolved. No fictitious prompt text is supplied.",
    "**Fox dominates the earlier voice:** 46 of 80 outgoing letters are to Fox, with no surviving pre-departure Fox incoming text in this batch. Explicit acknowledgments, two-letter and three-letter bundles, crossed letters, failed forwarding and rereading are recorded as references; they are not a count of distinct missing physical letters.",
    "**Incoming replies work in the other direction too:** 125 answers 121, 143 answers 140, 150 answers 147, and 135 answers 131 plus a separate missing young-Owen request. These relations do not make the incoming texts Darwin's voice or prove when he received them.",
    "**Luna proposals were adjudicated:** corrected reversed edges, cross-correspondent reply labels, self-loops and inappropriate unread/third-party classifications. Original proposals remain available alongside parent decisions rather than silently replacing their evidence.",
]
PARENT["mermaid"] = '''```mermaid
flowchart LR
    H105["105 · Henslow offer"] -->|"direct prompt"| D107["107 · Darwin to Henslow"]
    P106["106 · Peacock offer"] -->|"cross-correspondent context"| D107
    W125["125 · Whitley"] -->|"direct prompt"| D135A["135A · Darwin to Whitley"]
    F135["135 · FitzRoy"] -->|"extra week known"| D138["138 · Darwin to Henslow"]
    F135 -->|"reply; 4 or 11 Oct unresolved"| D139["139 · Darwin to FitzRoy"]
    HM143["143 · Henslow accounts"] -->|"direct prompt"| D144["144 · Darwin to Henslow"]
    SU["Unidentified Sedgwick letter"] -->|"received, explicitly unread"| D123["123 · no source content activated"]
    S116["116 · Sedgwick"] -.->|"possible identity"| SU
    G99["99 · anonymous gift note"] -->|"gift event only"| D100["100 · donor unknown to Darwin"]
    H150["150 · Henslow"] -.->|"possible input; unproved"| D152["152 · last affectionate letter"]
```'''

if __name__ == "__main__":
    (FOLDER / "parent_review.json").write_text(json.dumps(PARENT,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:len(PARENT[k]) for k in ('edges','candidate_links','unlocated_nodes')}))

# Independent full-text verification

Read every assigned outgoing and incoming body in full in bounded batches, with no truncated output. Read bodies before consulting the parent's initial survey. Record actual paragraph coverage, not an inferred reading claim. The packet preserves original CSV metadata, XML date constraints, the body and editorial material. Editorial notes are evidence of editorial identification, not words Darwin wrote or facts he necessarily knew.

After reading, compare your assigned targets with `../initial_survey.json`. Reconsider its hypotheses independently; flag errors and overlooked evidence. Cross-group primary texts are in `../source_packet.json`. All 34 eligible incoming bodies have a primary reviewer, including those with no corresponding outgoing reply. Boundary letter 153 postdates every outgoing target and must not be activated.

Use a strict standard: same author, an earlier date, a familiar topic or a later shared event does not identify an incoming letter or prove Darwin read it before a target. Look for acknowledgments, distinctive questions and answers, quotes, dated references, forwarding, explicit delays and cross-correspondent reuse. Distinguish physical receipt from reading; requested future letters from actual receipt; parcels/newspapers from letters; oral information from letters. Record unlocated references without inventing contents, dates or a physical-letter count. Several references may denote the same letter. Incoming voices never become Darwin targets. Third-party letters remain outside the graph, even if mentioned or partially quoted. Earlier FitzRoy letters are not default prompts after lengthy personal contact.

Preserve all date alternatives, ranges and question marks. Do not use the CSV sorting date as an exact event. Letter 99's archival author is not necessarily known to Darwin. Direct reply and cross-correspondent knowledge are separate relations. Own-letter references do not prove the recipient received the earlier letter.

Write only `<group>.review.json` and optional `<group>.review.md` in this directory. Do not edit canonical annotations, sources, another reviewer's files or the parent's initial survey. Use this JSON structure:

```json
{
  "group_id": "group",
  "model": "gpt-5.6-luna",
  "method": "Describe actual full reading and subsequent comparison",
  "outgoing_reviews": [{
    "letter_id": "DCP-LETT-N",
    "body_read_in_full": true,
    "paragraphs_read": [1, 2],
    "summary": "Specific review of this letter",
    "initial_survey_verdict": "agree / qualify / correct",
    "corrections": [],
    "proposed_links": []
  }],
  "incoming_reviews": [{
    "letter_id": "DCP-LETT-N",
    "body_read_in_full": true,
    "paragraphs_read": [1, 2],
    "summary": "Specific contents, receipt/response evidence or absence thereof",
    "unlocated_references": [],
    "proposed_links": []
  }],
  "findings": [],
  "limitations": []
}
```

Every proposed link or correction needs a reason and exact evidence from its source body (letter ID, paragraph number and quote; include both bodies when identifying a match). Suggested relations: `knowledge_before` (incoming → Darwin target), `replies_to` (response → earlier input), `refers_to_own_letter`, or `receipt_without_reading`. Status: `supported`, `candidate_only`, or `rejected`. For missing references give a description, direction, correspondent if established, and evidence; never manufacture a source letter. Separate source statements from your interpretation. Validate all quotation substrings before finishing. Report editorial support separately.

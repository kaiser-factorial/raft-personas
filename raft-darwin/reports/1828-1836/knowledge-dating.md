# Dating from Darwin's knowledge

Use Darwin's outgoing writing as dated evidence of his knowledge. An incoming letter receives a conservative `knowledge_date` when reviewed evidence establishes that Darwin had received/read it. This may be a direct reply or a reference in a letter to someone else. Preserve the original incoming date. This recoding means "demonstrably available by this writing," not "delivered on this day."

| Incoming letter | Original writing date | Darwin evidence | Knowledge date |
| --- | --- | --- | --- |
| 125, Whitley | 13 September 1831 | 135A, direct reply | 23 September 1831 |
| 296, Catherine | 29 January 1836 | 302 | 3 June 1836 |
| 287, Catherine | 30 October 1835 | 306, addressed to Susan | 4 August 1836 |
| 288, Susan | 22 November 1835 | 306 | 4 August 1836 |
| 312, FitzRoy | [19–]20 October [1836] | 313, addressed to Caroline | 24 October 1836 |

The [correspondence map](../correspondence-map/README.md) holds the current reviewed links; the earlier [receipt case study](receipt-evidence.md) remains an unchanged evidence snapshot. The dates come from the attesting Darwin letter's audited XML. The unlocated Whitley letter attested in 314 and the unresolved Fox input to 319 have separate reference nodes, known by 24 October and 6 November 1836 respectively. Neither is counted among the 126 catalogued incoming records, and neither supplies actual prompt text.

The [completed 13-letter post-return review](../post-return-1836/README.md) also distinguishes two missing Darwin-to-Herbert texts. Herbert's 323 answers one of them, but this dates Herbert's receipt, not Darwin's knowledge of 323. Consequently 323 retains a null knowledge date. References to Darwin's own letters, such as 318→317 and 329→330, have a separate relation type that never creates incoming availability or a prompt. Unconfirmed candidates stay outside accepted edges.

## Fields and handling

- `original_csv`, `original_sent_date_constraints`, and `provenance` retain the incoming metadata and its source.
- `knowledge_links` holds all reviewed receipt/reading attestations, including evidence carried across correspondents, relative receipt constraints, and source hashes.
- `response_links` holds direct Darwin replies, with original wording, complete XML date constraints, provenance, match evidence, and prompt eligibility. Knowledge-only links do not populate it.
- `knowledge_date` uses the earliest established, sufficiently dated Darwin attestation among reviewed links. It remains null if there is no such link. "Earliest established" is relative to the evidence reviewed so far, not a claim that this was Darwin's earliest historical knowledge.
- If a response date is a range, alternative, or qualified day, its uncertainty is preserved and its scalar `response_date` stays null. A dated knowledge anchor requires further review or another established response with a sufficiently resolved date.
- Several incoming letters may share one Darwin response. One incoming letter may also be referenced in several responses. All links remain visible.

An unmatched incoming letter remains in the corpus with no inferred knowledge date. A null date must not mean always available. Relative receipt expressions are preserved, but resolving an earlier calendar day requires additional reviewed evidence; no travel plan or approximate postal delay is silently converted into an arrival date.

## Ordering each training exchange

1. At Darwin's response date, provide the identified correspondent's actual incoming letter as the prompt. Add separately attributed incoming information and earlier memories only where availability is supported.
2. Train against Darwin's actual response, keeping that answer out of its own retrieved context.
3. Add the incoming information and completed outgoing letter to subsequent memory, preserving authorship. Incoming text never becomes a Darwin voice target; any future exporter must mask its tokens from answer loss.

The incoming context is available for the particular response that proves the link. This does not make every event on that calendar day mutually available. An exporter must represent the within-exchange order explicitly; it should not invent a previous-day delivery date or indiscriminately include all memories with the same date.

Darwin's unpaired outgoing letters retain their own sent-date evidence and the agreed dated-grounding role. Dates supplied by the edition remain editorially supplied; approximate dates remain approximate. The period audit and its three held records are unchanged.

The [body-date search](../body-date-search-37-337/README.md) establishes that some records contain several dated writing sections and may have remained unsent for months. Further annotation must associate receipt evidence with the relevant section; the earliest overall date cannot be used for later contents. The current nine scalar knowledge dates use sufficiently resolved Darwin writing dates. Text-attribution annotations separately exclude jointly signed or third-person reported text from Darwin's individual-voice training.

## Current output

[incoming_knowledge_dates.jsonl](incoming_knowledge_dates.jsonl) contains all **126** period-eligible incoming records: **9** with reviewed knowledge dates and **117** awaiting full-text availability evidence. Five complete prompt–response pairs pass the timing policy. FitzRoy 135 also has an identified reply in 139, but that response's alternative dates remain unresolved. [knowledge_dating_summary.json](knowledge_dating_summary.json) records input and output hashes and counts. This remains an annotation layer, not a Raft training export.

The [pre-Beagle review](../pre-beagle-1828-1831/README.md) distinguishes explicitly unread receipt (123's Sedgwick letter) from uncertain reading (99's microscope note). Neither activates the whole incoming text. The gift event is recorded separately, and Herbert's archival authorship remains hidden from young Darwin unless later evidence establishes that he learned it. Incoming replies such as 150 → 147 establish the other correspondent's receipt of Darwin's writing, not Darwin's receipt of their response.

Rebuild offline with `python3 scripts/build_correspondence_map.py` (Python 3.11 or newer). `annotate_response_dates.py` remains a compatible entry point to the same builder. The original audit and earlier manual receipt evidence are not rewritten.

# Method for extending the correspondence map

Agreed review method, 16 September 2026. The [first 13-letter post-return batch](../post-return-1836/README.md) is complete, with six additional accepted relationships and no new complete surviving prompt pair. This document describes the continuing process; it does not authorize automatic promotion of candidates or export training examples.

## Start from Darwin's writing

Use each eligible Darwin-authored outgoing letter as the unit of review. Read it in full, retaining its addressee, XML date constraints, dated continuations, and source attribution. Process each correspondent's sequence in chronological order where the evidence permits. Overlapping or alternative dates remain partially ordered; catalogue IDs and CSV sorting dates do not resolve them.

The same evidential standard applies before, during, and after the Beagle voyage. Shorter presumed postal delays can prioritize candidates on land but never prove delivery. During the voyage, reconstruct receipt batches, port references, unopened bundles, and reversals of arrival order explicitly. Even after return, Darwin might be answering old mail or recalling a conversation in person.

The [Darwin Correspondence Project](https://www.darwinproject.ac.uk/voyage-beagle) dates departure to 27 December 1831 and return to 2 October 1836. Using the current XML bounds, with boundary-spanning records kept separate, the audited eligible collection divides as follows:

| Review period | Darwin outgoing | Incoming | Current individual-voice candidates |
| --- | ---: | ---: | ---: |
| Before departure, entirely before 27 December 1831 | 80 | 34 | 80 |
| Voyage, entirely between the departure and return days | 65 | 81 | 64 |
| After the return day, through 31 December 1836 | 14 | 10 | 13 |
| Spans the departure boundary: incoming 153 | 0 | 1 | 0 |

These 285 records are the safe-period set; the three possibly later records remain held. The voice exclusions are 303 and 330. These review periods organize work, not assumed delivery dates. Original brackets, qualifications, and ranges remain intact.

## One review dossier per outgoing letter

1. **Extract references before choosing a match.** Record each acknowledgment, question answered, request fulfilled or declined, quotation, thanks, discussed news, enclosure, and reference to earlier communication. Include negations, future plans, and uncertainty. Preserve exact outgoing spans and body-block locations. Generic first-person references such as “this letter” need no incoming link.
2. **Search the addressee's incoming letters first.** Use XML person identifiers, including coauthors, rather than surnames. Search the whole approved period when necessary. Recent plausible letters are convenient starting points, not an exclusive time window. Keep overlapping date intervals as candidates needing chronology review; reject a candidate only when the evidence makes the required order impossible.
3. **Compare specific content on both sides.** Match a distinctive question to its answer, a request to the promised action, or a specific report to Darwin's reaction. Sender plus a cited date is useful; a date shared by several letters still needs disambiguation. Record the strongest alternative and contrary evidence. Broad themes such as family news, geology, specimens, or marriage are insufficient on their own.
4. **Search across correspondents for information sources.** Use named people, quoted language, unusual events, enclosures, and forwarded material. Preserve the distinction between the person addressed and the source of Darwin's information. Other letters remain context unless a direct reply is independently established. A reference such as “as you told me” may concern a visit or conversation and must not automatically become a letter node.
5. **Record a reviewed disposition.** A dossier can establish more than one link, leave competing candidates unresolved, or conclude that no incoming prompt has been identified. Do not consume an incoming letter after its first match: several later letters may refer to it. Conversely, a reply may answer several incoming letters.

The dossier should hold: target ID and dated section; reference span; candidate incoming IDs and matching spans; temporal constraints; relevant author identities; competing explanations; disposition and rationale; exact source locators/hashes; prompt versus context role; and any unresolved receipt date. Machine suggestions belong in a candidate queue until reviewed.

The identity/date screen is deliberately broad; its records are not equally plausible conversational antecedents. Read candidate bodies in full before closing the review, and consider intervening shared experience, visits, fulfilled requests, changed plans, and whether the earlier topic still explains the outgoing wording. FitzRoy's earlier preparations and voyage logistics require particularly strong evidence to identify them as prompts after years of direct contact with Darwin. This lowers plausibility rather than imposing a blanket exclusion: a later letter can still recall or use an old document. Preserve the distinction between historical background, an unconfirmed specific overlap, an unlikely antecedent, and a date-impossible record.

## Evidence decisions

| Finding | Map treatment | Conversation consequence |
| --- | --- | --- |
| Identifiable incoming letter is directly answered | Reviewed reply plus knowledge link | Actual incoming text can be a prompt |
| Identifiable letter is acknowledged or its information used, without a direct reply to that writer | Reviewed knowledge link | Attributed context, not a fabricated prompt |
| Specific similarities, but alternatives remain or chronology is unresolved | Candidate with supporting and contrary evidence | No prompt promotion or new scalar knowledge date |
| Darwin explicitly refers to a letter whose text cannot be located | Attested unlocated reference, with only supported constraints | Darwin's outgoing text remains grounding |
| No identifiable correspondence reference, or the channel could be an in-person conversation | No asserted letter edge; retain the observation | Grounding unless later evidence resolves it |

An explicit “your letter” proves an antecedent, but does not identify which surviving record it was. Strong implicit question-and-answer evidence can establish a reply without the word “letter”; its inferential basis must be recorded. Editorial cross-references can corroborate identification, while remaining outside persona memory.

## Chronology and the voyage

Keep three dates or constraints separate: the incoming writing date, actual or inferred receipt/reading constraints, and the dated Darwin writing that attests knowledge. A sufficiently resolved Darwin date supplies a conservative known-by bound. Retain the earlier relative receipt expression even when it cannot be converted into a calendar day.

For voyage letters, add a delivery-event layer when the text supports it: receipt location; latest stated lack of the item; arrival or reading expression; letters explicitly included in a batch; and the acknowledging dated section. An unnamed batch can be a batch observation with unknown members. Never attach every earlier letter to it. A bundle delivered but unopened does not make its contents known.

Use a later acknowledgment to constrain earlier delivery only as far as its wording supports. Reading A, which mentions B, establishes access to the reported information from B; it does not prove Darwin possessed or read all of B. Similarly, the latest stated date of a received letter is not the day it arrived.

The map should retain local ordering constraints rather than manufacture a single exact receipt chronology. The named attesting response may use its proven incoming context; other writing on the same date needs separate order evidence. Dated continuations are reviewed at section level before applying knowledge to earlier sections.

## Assemble conversations after review

Each training candidate consists of its actual incoming prompt or prompt bundle, separately attributed context known to Darwin by the target writing, any established earlier exchange history, and the actual Darwin reply. Keep the target answer out of its own context.

When several incoming letters lead to one reply, preserve one answer with its documented inputs. Do not duplicate the entire answer into several supposedly independent pairs, blend speakers, or invent connecting turns. Whole-letter pairs are the first format; passage-level examples require a separate review showing that the selected question and answer remain coherent without omitted material.

Only individually attributed Darwin output can be the voice target. Incoming letters and other context retain their authors and are excluded from answer loss in any future exporter. Unpaired Darwin prose keeps the agreed grounding role. No model trainer or export changes are part of this proposal.

The diagram can be generated from the accepted graph: display a separate timeline for each correspondent's exchanges, connect a direct input to Darwin's reply, and show knowledge crossing between correspondents with a distinct edge style. Missing-text references and uncertain dates remain visibly marked. The graph, rather than a manually maintained drawing, is the source of truth.

## Practical first pass

Begin by calibrating decisions against already reviewed examples: 125→135A as a direct pair, 312→313 as cross-correspondent knowledge, the unlocated input to 314, and 287/288→306 as multiple inputs with different conversation roles. Also check negative evidence such as 305's unopened bundle.

The completed first batch reviewed all **13 eligible Darwin outgoing letters after return**: 307, 310, 311, 313, 314, 317, 318, 319, 320, 321, 325, 327, and 329. It records both successful information links and missing or non-written antecedents. 319 explicitly answers an unlocated Fox letter, while 317's “as you told me” leaves the communication channel open. All 13 retain grounding roles. See the [review report](../post-return-1836/README.md) for evidence and gaps.

The [completed incoming follow-up](../post-return-1836/incoming-full-read/README.md) assigned all 33 earlier incoming records to three Luna reviewers and checked all 85 comparisons. The parent reviewed the proposed matches against the original passages; topic overlap alone did not establish receipt or use. Reviewer proposals, corrections, full-body coverage declarations, and exact evidence remain separate from accepted graph edges.

The [completed pre-Beagle pass](../pre-beagle-1828-1831/README.md) then applied the same sequence to 80 outgoing and 34 incoming letters: parent full-body survey, three Luna full-text reviews, and parent adjudication. Reviewer suggestions are retained as proposals, including incorrect direction labels and rejected identities; only the separately adjudicated edge list changes availability. A physical gift match can establish its event without proving the accompanying note was read. Explicitly unread receipt, unknown reading status, and archival authorship unknown to Darwin are distinct annotation states.

Continue through the **80 pre-departure outgoing letters**, grouped by correspondent. Fox accounts for 46 and Henslow for 11, so correspondent-based review will reuse context efficiently. The six Henslow targets in August–September 1831 (107, 114, 118, 123, 128, 138) are a useful early cluster. Letter 107's reference to Peacock shows why the second, cross-correspondent pass is needed even here; no new match for it is asserted by this proposal.

Finally apply the method to the **64 eligible voyage-era Darwin voice candidates**, beginning with explicit dated acknowledgments and the existing 16 reviewed temporal findings, then unresolved semantic matches. Allow a voyage-era incoming letter to be answered after return; these work groups do not restrict candidate membership.

Review order is separate from training chronology. Reviewing a later letter first does not make its information available to an earlier Darwin response.

Automation can prepare dossiers, retrieve candidate passages, validate quoted offsets and date consistency, and redraw accepted links. A reading model can propose interpretations and alternatives. Acceptance should depend on checked source evidence, not a similarity score or the model's confidence. Prioritize accurate links and documented gaps over the number of pairs produced.

## Progress measures and safeguards

Track outgoing dossiers reviewed, confirmed direct pairs, knowledge-only links, unresolved candidates, attested unlocated inputs, and letters with no established prompt. Separately report date uncertainty and attribution exclusions. A completed dossier need not produce a pair.

Each accepted graph change should pass existing provenance, date, author, missing-text, and prompt/context checks. New delivery-event behavior will need tests for batch membership, multiple dated sections, and negative receipt evidence when implemented. Preserve raw sources and the original XML period audit. Rebuild the derived knowledge dates and diagram from reviewed annotations after each batch.

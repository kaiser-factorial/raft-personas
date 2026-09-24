# Darwin persona: research and RAFT handoff

**22 September continuation:** the completed data release ends on 24 November 1859. The proposed second collection run extends from 25 November 1859 through 31 December 1868, covering *Variation* publication and subsequent correspondence about the book. Read the [collection workflow](docs/collection-workflow.md) and [filesystem / run-02 plan](docs/collection-layout-and-run-02.md). This is a documented plan; the second fetch has not started. The older status narrative below records earlier collection milestones and does not report subsequent training activity.

The current checkout is `/Users/corinakaiser/Projects/personas/raft-darwin`. Earlier project paths below are retained as historical references.

Updated **17 September 2026**. Project root: `/Users/corinakaiser/Projects/Effort/experiments/raft-darwin`.

## Resume here

The authorized research and cumulative data preparation are complete through **24 November 1859**. The chronological inventories, including the Beagle follow-up, have primary adjudication. All **3,031 selected source records** are accounted for; this is a bounded inventory, not a claim that every letter in the worldwide collection has a complete surviving text.

The single RAFT export in `darwin_0` contains **162 conversation JSON files** across **155 Darwin response sources**, and **1,405 grounding documents** across **1,399 Darwin sources**. Each transcript has one established incoming → Darwin exchange with its own exact response/section date. Paired responses are excluded from grounding. No embeddings, fine-tuning generation, model training or benchmark evaluation has run.

Start with [the cumulative export report](reports/raft-export/README.md), [manifest](reports/raft-export/manifest.json), [validation](reports/raft-export/validation.json), and [hold queue](reports/raft-export/hold-queue.json). The [research status](reports/research/work_status.json) supplies period checkpoints. [Formatting readiness](docs/raft-formatting-readiness.md) records verified installed RAFT behavior and remaining training boundaries.

The 221 accepted direct relationships span 205 Darwin response sources. Fourteen whole responses are held before rendering; 199 planned response sections yield 162 exported and 37 held units. Grounding has 67 rendered-unit holds, 496 earlier source holds and 56 separate outside-window records. These categories use different denominators; consult the accounting files before combining them.

Final content work removed header/routing metadata, excluded other voices and later layers, rendered source-supported fractions/layout, verified the nine-page Davy printed witness, split independently dated sections, and held unresolved artifacts instead of guessing. The export validator checks every output, source span and source hash, native schema/date parsing, continuous numbering, duplicate IDs/text and target/grounding separation. Fourteen focused tests passed.

The frozen export is already written and validated. Do not restart completed pairing or overwrite the data using earlier draft plans. Future work can resolve named holds or prepare an explicitly requested training/evaluation run; keep related letters and response sections together when assigning any holdout. The user's chosen workflow remains Luna full-source first passes followed by root adjudication. Historical uncertainty and missing correspondence must stay explicit.

The sections below preserve the **16 September handoff's historical state and conventions**. Their phase counts and suggested future expansions are superseded by the current report above. `scope.json` and earlier period READMEs remain historical evidence, not current progress.

## 1. Objective and decisions already made

The user initially considered either a persona at a particular age or a mature Darwin drawing on his whole correspondence, then chose to begin with **younger Darwin**, starting in **1828** because little earlier writing survives. We expanded from 1828–1836 to 1837–1843 to find more genuine exchanges. The next expansion should capture his intellectual development through publication of *Origin*, not flatten every year into one timeless persona.

The final model cutoff and whether to train successive snapshots remain open. Expanding the research corpus does not decide those questions. Maintain enough temporal structure to support a persona at a chosen date, later snapshots, and comparisons between developmental periods.

Fixed collection and training policies:

- Include correspondence **to or from Charles Robert Darwin**, whose XML authority key is `nameregs_1.xml`. A matching surname is insufficient. Exclude third-party correspondence as independent corpus letters or prompts.
- Preserve both directions, but only surviving, individually attributed **Darwin prose** can supply his response voice. Incoming letters, editorial narration, and quoted words of other people are not his voice.
- An outgoing letter without an established surviving incoming prompt remains **dated grounding**. Do not manufacture a question, infer a missing letter's text, or ask an LLM to turn an essay into dialogue.
- Incoming letters can establish knowledge even when Darwin discusses them with somebody else. This is a separate relationship from replying to their authors.
- Preserve original CSV metadata, XML constraints, raw pages, source URLs and hashes. Add interpretations in annotations; never rewrite the originals to look certain.
- The user's emphasis is **Darwin's knowledge**, not catalogue order or the dates on incoming envelopes. His own dated writing supplies conservative evidence of what he knew by then.
- Missing correspondence is a legitimate result. Increasing pair counts must not lower the evidentiary standard.

The platform is the user's friend's [Hyperplex RAFT](https://raft.hyperplex.org/), with [documentation](https://raft.hyperplex.org/docs/). Do not substitute an unrelated RAFT research method or the distributed consensus protocol. The appeal here is persona training with retrieved memory, originally built around modern social interactions.

## 2. Verified state at handoff

### 1837–1843: selected inventory complete

| Measure | Current result | Meaning |
| --- | ---: | --- |
| Inspected source records | 476 | Entire frozen candidate inventory |
| Available transcriptions read in full | 474 | Two inspected records lack usable transcriptions |
| Unreviewed selected records | 0 | Do not restart the remaining-review phase |
| Raw XML safe / held | 445 / 31 | Immutable original period audit |
| Effective period eligible / held | 443 / 33 | Adds editorial holds for 631 and 13803 |
| Eligible individual Darwin body records | 314 | Not all ready for an exact-date export |
| Distinct Darwin responses with identified inputs | 22 | Some require section-level treatment |
| Direct incoming → Darwin links | 24 | 19 single-date links plus 5 section-dependent links |
| Section-dependent response records | 3 | Five links do not mean five separate answers |
| Eligible outgoing bodies without an identified surviving prompt | 292 | Grounding candidates, with scope/date restrictions |
| Cross-correspondent knowledge links | 16 | Context, not direct prompt pairs |
| Reverse replies by correspondents | 28 | Not Darwin outputs |
| Incoming records with accepted known-by evidence | 32 | 99 of the 131 incoming full-read records lack accepted activation |
| Whole-letter exact-date review flags among raw XML-safe records | 103 | Period eligibility is not exact-day certainty |

The remaining-review phase added **363 source inspections / 362 full transcriptions** to the earlier **113 / 112**, in **19 Luna packets**, all adjudicated by the primary agent. This includes negative matches and holds, not only positive pairs.

Specific exclusions overlap other categories: **699F** has no available transcription; **13864** has only a catalogue synopsis. **421F, 512, 612** are joint documents excluded from individual voice. **677** is held for possible forgery/corruption. Do not add these counts as mutually exclusive categories.

The last completed research validation recorded **88 passing tests**, with zero failures/errors, in [validation.json](reports/1837-1843/remaining-review/validation.json). This is a preserved result, not a claim that tests were rerun for this handoff. Source hashes, exact quotations, scopes and prior relationships were also checked. [work_status.json](reports/1837-1843/remaining-review/work_status.json) records completion and final-output hashes.

### Earlier work and aggregate counts

The 1828–1836 metadata audit has **288 candidates: 285 XML-safe and 3 held**. The 37–337 body search preserved 286 Darwin-involved bodies. The **80 outgoing / 34 incoming pre-Beagle review**, **13 post-return outgoing review**, and **33 earlier incoming / 85 comparison follow-up** are complete. Comprehensive Beagle-voyage pairing is **not** complete.

Earlier work established **5 single-date pairs**. **135 → 139** is additionally identified but held for the outgoing letter's uncertain date. Nine of 126 period-eligible incoming records have knowledge dates; 117 do not.

Across the reviewed periods we have **24 single-date pairs**, or **29 direct links across 27 distinct Darwin response letters** when section-dependent relationships are included. These are research relationships, **not counts of export-ready, independent training examples**. Do not count all graph edges as pairs. Do not add the earlier graph's grounding-role count to the 292 fully adjudicated expansion unpaired bodies as though they used the same denominator.

The claim of completeness is bounded by the selected 476-record inventory. It is neither a full-catalogue XML-overlap audit nor completion of all 1828–1843 matching. Cross-period records, such as **326**, require deduplication by DCP ID.

### Recent accepted examples worth retaining

The final pass added these eight direct relationships (shown incoming → Darwin):

| Pair | Dated Darwin witness | Evidence type |
| --- | --- | --- |
| 377 → 378A | 1837-09-20 | Explicitly dated Treasury grant instructions |
| 381A → 402A | 1838-02-16 | October approval cited in submission of first account |
| 402B → 402F | 1838-02-22 | Children's question about Gray answered specifically |
| 402C → 424A | 1838-08-18 | Dated Treasury payment instructions followed |
| 504 → 506 | 1839-04-16 | Whewell's wedding gift and letter acknowledged |
| 534 → 545 | 1839-11-01 | Humboldt's ocean-temperature question answered |
| 565H → 585 | 1840-12-22 | Distinctive Redfield publication bundle and explicit letter reference; a separate missing cover note remains a caveat |
| 717 → 722 | 1843-12-12 | Hooker's botanical questions and Darwin's collections |

The final pass also added knowledge-only relationships **377A → 378A, 431 → 437, 456 → 483, 487 → 489, 500 → 501**. Full evidence and qualifications are in the ledgers; this table does not replace them.

## 3. Source layers and where to find things

### Read in this order

1. [README](README.md), [aggregate corpus status](reports/corpus-status.json), [final expansion report](reports/1837-1843/remaining-review/README.md).
2. [Current expansion summary](reports/1837-1843/correspondence-map/summary.json), [graph](reports/1837-1843/correspondence-map/graph.json), [incoming knowledge dates](reports/1837-1843/correspondence-map/incoming_knowledge_dates.jsonl).
3. [Completion reconciliation](reports/1837-1843/remaining-review/reconciliation.json), [parent review](reports/1837-1843/remaining-review/parent_review.json), [work status](reports/1837-1843/remaining-review/work_status.json).
4. Original date audit, source records, and the exact adjudication entry for any relationship being reused.

Earlier phase READMEs, `integration-review.md`, rejected initial Luna reports, and candidate searches are **review history**, not current acceptance or completion status. Preserve their disagreements without promoting them over final decisions.

### Originals and annotations

- The [Cambridge epsilon-data repository](https://github.com/cambridge-collection/epsilon-data) is pinned at **`ab0d973bae05b54d68d82d068211015996cfec06`** under [data/raw/epsilon](data/raw/epsilon/ab0d973bae05b54d68d82d068211015996cfec06/).
- Its `darwin-correspondence.csv` has **15,238 metadata rows**. Preserve headers exactly, including leading spaces in ` filename` and ` extent`, physical CSV line provenance, original strings and filenames with suffixes.
- Earlier XML is under that revision's `letters/`; expansion XML under `expansions/1837-1843/letters/`. The selected XML records contain **metadata, not the full letter transcriptions**, and do not supply structured receipt dates for this inventory.
- Raw public pages live under [data/raw/dcp](data/raw/dcp/), organized by phase. Manifests preserve URL, retrieval information, SHA-256 and file size. Original pages are immutable.
- The [1837–1843 audit](reports/1837-1843/audit.jsonl), [raw safe records](reports/1837-1843/safe_within_period.jsonl), [raw held records](reports/1837-1843/ambiguous_or_later.jsonl), and [correspondent groups](reports/1837-1843/correspondents.json) describe the frozen metadata inventory. Its top-level `summary.json` is an XML audit summary, not the pairing summary.
- [all_letters.jsonl](reports/1837-1843/remaining-review/all_letters.jsonl) contains the 476 extracted records; `letters.jsonl` in the same directory contains the new 363. Headers, numbered body paragraphs, editorial summary, excluded annotations and footnotes remain distinguishable.
- Accepted phase ledgers: [initial expansion](data/annotations/expansion_1837_1843.json), [Henslow/Lyell](data/annotations/henslow_lyell_1837_1843.json), and [remaining review](data/annotations/remaining_1837_1843/) (`batch-01.json` through `batch-19.json`, plus `supplementary.json`). Preserve them; put future corrections in explicit additive decisions with rationale.
- The remaining-review directory preserves [packet instructions](reports/1837-1843/remaining-review/REVIEW-INSTRUCTIONS.md), [packets](reports/1837-1843/remaining-review/packets/), [Luna reviews](reports/1837-1843/remaining-review/reviews/), [primary reading notes](reports/1837-1843/remaining-review/parent-reading/), [primary decisions](reports/1837-1843/remaining-review/parent-decisions/), and [baseline hashes](reports/1837-1843/remaining-review/baseline_hashes.json).

Earlier sources of policy and evidence: [knowledge dating](reports/1828-1836/knowledge-dating.md), [original graph](reports/correspondence-map/graph.json), [body-date search](reports/body-date-search-37-337/README.md), [pre-Beagle review](reports/pre-beagle-1828-1831/README.md), [post-return review](reports/post-return-1836/README.md), [incoming follow-up](reports/post-return-1836/incoming-full-read/README.md), [original relationship annotations](data/annotations/correspondence_links.json), and [text attribution](data/annotations/text_attribution.json).

## 4. The knowledge clock

Maintain several distinct facts rather than one overwritten date:

| Fact | What it means |
| --- | --- |
| Original composition/sent constraints | What the edition's metadata says, with ranges, alternatives, uncertainty and provenance |
| Posting | A separate act; an XML sent date does not prove physical dispatch that day |
| Physical receipt | Delivery to a location/person, when specifically evidenced |
| Reading or content use | Whether Darwin actually knew the particular contents |
| `known_by_date` / earlier `knowledge_date` | Conservative bound from the earliest sufficiently dated **reviewed** Darwin witness |
| Response section date | Date of the particular writing that can be conditioned on the incoming information |
| Within-exchange order | Incoming source available before its demonstrated response; completed response available afterward |

“Known by” is **not** an exact arrival date and is not necessarily the earliest historical receipt. A better later-discovered witness can refine the annotation without changing the incoming original date. A null date must never mean always available.

Letter **301** motivated this policy: Darwin says the **date on the last letter received** was thirteen months earlier. It warns against treating sent dates as access dates during the voyage. It does **not** establish a universal thirteen-month period with no delivery from every correspondent. Use the particular Cape/subsequent acknowledgements, including **302 and 306**, rather than applying a blanket blackout rule.

Letter **312 → 313** is the central knowledge-only example: FitzRoy's engagement news reaches Darwin, who tells Caroline. The incoming letter is useful context; it is not Caroline's prompt and cannot train FitzRoy's words as Darwin's voice.

For every target, distinguish two questions:

1. Is a particular incoming source proved available **for this response or section**?
2. Is it proved available before some **other** target at that date?

The first does not automatically answer the second. Do not move an incoming date back one day to make retrieval work. Do not let the answer retrieve itself. Do not make all same-day letters mutually available.

For uncertain dates, preserve intervals/disjoint possibilities. A conservative latest bound can support delayed global availability where the evidence warrants it; it does not turn into the historical writing or receipt day. For example, **500 → 501** uses **1839-12-31** as a conservative latest witness bound because 501's assigned 21 March date is questionable. It is not evidence of delivery on 31 December or permission to feed that content to unrelated March responses.

Multi-day letters and arrivals during composition require scopes. Use paragraph boundaries or **Unicode code-point offsets** when a dateline occurs inside a paragraph. An incoming letter first acknowledged late in a letter cannot condition the earlier portion without independent evidence.

## 5. Pairing probe workflow

### A. Freeze a bounded inventory

Choose a chunk and inclusive dates. Keep its source paths and outputs separate from completed periods. For 1844–1846, new paths such as `reports/1844-1846/`, `data/annotations/1844_1846/`, and a new raw-page phase directory should be created by the next implementation; they do not exist merely because they are named here.

Select Darwin identity using the CSV and XML authority evidence. Retain joint/uncertain cases for review rather than silently accepting their voice. Preserve and report third-party exclusions. Audit all XML date possibilities; **every allowed possibility must fit** to call a record safely within a period. Keep raw safety and later editorial refinements separate.

The existing expansion selector uses a CSV sorting-date window **or an explicit display-date year in the window**. It is not a scan of every XML interval in the whole catalogue. A future driver must either improve overlap discovery or explicitly retain this limitation and inspect boundary/alternative-date candidates. Catalogue IDs, sorting dates and the first year in a label are not chronology.

Freeze target IDs, raw source hashes and baseline artifact hashes before review. Reuse a previously preserved source by ID/hash rather than counting it anew. A previous-period incoming letter can still be a new-period prompt.

### B. Fetch, preserve and extract

Fetch metadata XML and public full-text pages as separate resources. Reuse verified local files, keep manifest errors explicit, and use modest concurrency (the existing fetchers use three workers). A failed fetch, blank page, catalogue paraphrase, and absent transcription are different conditions.

Extract the full source: header, complete body, salutations/closings, editorial notes and any potentially relevant attachments. Number body paragraphs and retain exact text/locators. Editorial notes are useful identification evidence, but are not automatically text Darwin knew or wrote. A fragment can be fully read while still being an incomplete historical letter.

### C. Probe broadly, without treating a hit as a pair

Search below the opening dateline/salutation for dates and for `letter`, `letters`, `received`, `your last`, acknowledgements, answered questions, gifts, enclosures, bundles, personal names and distinctive content. The user's original request was to search beyond the first two or three introductory lines; the implemented searches identify body paragraphs rather than trusting display-line numbers.

Search both directions and relevant earlier context. Use correspondent authority keys, name variants and substantive comparison. Inspect editorial cross-references as leads. Look for explicit use of an incoming letter when writing to **another person**, including incoming-only correspondent groups. Do not stop at same-correspondent matching.

A candidate pool is deliberately broad. It is not a ranking of equally plausible prompts. Read alternatives; record why a same-topic or old same-correspondent letter does not identify the reference. Intervening meetings, shared travel, lost letters, enclosures and oral discussion may explain continuity better.

### D. Give Luna bounded full-reading packets

The agreed workflow uses **`gpt-5.6-luna`** for initial audits. Prior primary-first/Luna-verification passes exist in the history; use Luna-first going forward.

Group by correspondent and chronology so both sides and relevant context are visible. Existing packet construction caps approximately **24 target records / 15,000 target words**; reduce this for unusually long material and budget for context and notes as well. Keep `target_ids` separate from already reviewed `context_ids`. An overlap is context, not new coverage. Long exchanges may need several packets with explicit overlap.

Use up to three Luna readers alongside the primary agent, subject to the session's tool limits. This is user-authorized subagent work; do not create user-owned sidebar tasks unless separately requested. When a model override requires a non-full-history fork, send a self-contained brief with absolute workspace/packet paths. Old agent handles are not durable resumption infrastructure.

Every reviewer must read **all assigned target and context sources in full**: headers, body, original date constraints, summaries and notes. State explicitly that the preserved HTML supplies the body and the XML is metadata. Use the [existing review contract](reports/1837-1843/remaining-review/REVIEW-INSTRUCTIONS.md) as the template, adapted to the new period.

Require per record: actual coverage, source/transcription distinction, paragraph list, source kind, substantive summary, date assessment, attribution assessment, proposed real prompt IDs, alternatives with comparisons, unmatched reason, exact quotations and locators. Require per proposed relationship: type, direction, status, temporal evidence, response/text scope and uncertainties. Additional full-read witnesses must be listed separately from packet coverage.

Reviewers write only their own reports. They do not change accepted graphs, raw sources, another reviewer's output or final ledgers. Preserve the initial report before a revision. A report's `full_read` flag or quote-check success is not independent proof of sound reasoning.

### E. Primary agent verifies and adjudicates

Read the full sources independently; do not just accept Luna's summary or check a few quotations. Review both positive claims and negative/unpaired dispositions. Check identity, direction, chronology, distinctive wording, competing inputs, missing channels, authorship and scope. A disputed relationship may receive a further bounded independent review, but the primary agent owns the evidence-based decision.

Assign the appropriate relationship:

| Outcome | Treatment |
| --- | --- |
| Established direct incoming → Darwin response | Potential conversation, subject to date/text eligibility |
| Incoming content explicitly used in writing to someone else | Knowledge-only context |
| Incoming letter answers Darwin | Reverse reply; no automatic Darwin receipt or output |
| Darwin refers to his own earlier writing | Document reference, not incoming availability |
| Receipt explicitly unread | Receipt evidence only; do not activate full contents |
| Event known but letter/author not known | Limit context to the evidenced event |
| Acknowledged input is missing/unidentified | Unlocated reference with no invented prompt text |
| Plausible but unestablished identity | Candidate-only; no accepted edge/date activation |
| No identifiable surviving input | Dated grounding, if voice/date eligible |

**Arrow warning:** prose tables here show **incoming → Darwin output**. Graph `replies_to` edges point **response → antecedent**. Knowledge edges point **incoming source → dated Darwin witness**. A correspondent's reply to Darwin therefore has an incoming source node pointing back to his outgoing letter; this is not a Darwin training pair. Read the schema and participant identities before counting or converting edges.

Direct links normally involve corresponding people; a documented institutional routing exception can be accepted **per edge**. Preserve separate officials rather than creating a global alias. Several inputs may contribute to one output, or one input to several outputs. Preserve these relationships without duplicating the target as several supposedly independent examples.

### F. Preserve decisions and validate the chunk

Store primary full-reading notes and a disposition for every reviewer proposal and target. Freeze accepted decisions in additive ledgers with source hashes, exact quotes, date constraints, character/paragraph scopes, candidate rejections and exceptions. Keep original claims and corrections legible.

Build derived graphs and knowledge tables from these decisions. Check unique IDs, complete target coverage, raw/hash integrity, quote substrings and locators, role/direction, date and voice eligibility, section boundaries, prior-edge preservation, and absence of self/future-context leakage. Tests validate structural rules; they do not turn a merely plausible historical identification into proof.

Report source inspections, full transcriptions, unavailable texts, unresolved dates, excluded voices, distinct paired outputs, relationship counts, unpaired eligible bodies and remaining unreviewed records separately. Define denominators. Compare new results with the preserved baseline and deduplicate cross-period IDs.

A chunk is complete when every selected record and every proposal has a final disposition and the reports reconcile—not when every letter has a prompt. Only then move to the next chunk.

## 6. Failure modes already encountered

These examples should guide future probes and exporter tests. Inspect their exact ledgers before reusing a specific decision.

### Evidence and voice

- **Metadata mistaken for full text.** Initial Luna reports for batches 03, 06, 09, 12, 15 and 18 incorrectly claimed 117 bodies were unavailable because XML lacked transcriptions, despite available HTML. The reports were rejected and the bodies reread; initial versions are retained. Never infer full-text absence from an XML flag alone.
- **Synopsis mistaken for transcription.** 13864 is a catalogue summary, not Darwin prose; 699F is unavailable. Count source inspection separately. Conversely, a catalogue entry containing actual quoted extracts may contain usable attributed spans.
- **Catalogue narration leaking into Darwin's voice.** 451, 609F, 698 and 13865 require explicit permitted spans. In 609F, translated sale-catalogue narration and a quotation from Cordier are not Darwin prose; the surviving tail/close needs separate treatment. 545 has a trailing repository caption outside the answer. Preserve originals and export only reviewed spans.
- **Joint authorship, reported speech and authenticity.** The user flagged 303's joint attribution/signature problem; it is not an individual Darwin voice target. 330 is a minute-book report. 421F, 512 and 612 are joint documents. 677 is held for possible forgery/corruption. A scribal or amanuensis hand, as in 502 or 13925F, is not by itself evidence of coauthorship.
- **Translation, tables and attachments.** 350F survives in published French wording and needs explicit handling before an English voice export. 545's table has transcription/OCR issues. 675 includes possibly separate postscripts. A blanket removal of all annotations could discard Darwin-authored material such as 700's address supplement. Read and classify; do not apply a universal cleanup regex.
- **Summary overwrites source detail.** 703's body and editorial summary differ on the sum of money. Preserve the conflict and the source wording instead of silently replacing the body with the summary's amount.

### Relationship identification

- **Shared topic or nearest date mistaken for a reply.** The initial 441 → 445 idea was rejected in favor of the specific input 444. Book receipt and broad scientific continuity do not prove a particular cover letter. The Redfield/Allan and Malcolmson supplementary candidates retain such distinctions.
- **Old letter substituted for a lost contemporary one.** Fox 197/261 do not identify 348's “last letter”; Henslow 249 does not identify 353's input; Whitley 267 does not identify the letter acknowledged in 314. The 13 post-return review did not acquire new pairs by force-fitting old incoming records.
- **Intervening face-to-face communication ignored.** Darwin spent the voyage with FitzRoy; matching a post-return reference to an old pre-Beagle FitzRoy letter merely because the author matches is weak. This changes plausibility, not a universal rule that old letters are never answered.
- **Both records are outgoing.** 676 → 671A and 609 → 606 are examples of proposed correspondences that do not supply an incoming Darwin prompt. Inspect participant direction before semantic similarity.
- **Cross-correspondent knowledge collapsed into dialogue.** 312 → 313 and the Henslow/Herbert/FitzRoy knowledge examples above establish context, not direct replies to their source authors.
- **Reverse reply dates the wrong person's knowledge.** 524 replying to 523 establishes Herbert's access to Darwin's letter; 562F replying to 560 is analogous. Neither dates Darwin's reading of the answer. A “Received Dec 17” annotation inside 457's copied Heron-to-Yarrell material is not Darwin's receipt.
- **Identity merging.** Emma's maiden/married name is an authority-resolution issue; William Jackson Hooker and Joseph Dalton Hooker are distinct. So are Baring and Spearman: the Treasury chain has explicit per-edge institutional explanations. Beaufort/Wood in Admiralty correspondence is another official-routing case, not an identity alias.
- **Third-party evidence promoted to a corpus prompt.** Embedded reports or references in 523 or 664 do not admit the underlying third-party letter as Darwin's incoming text. Preserve Darwin's own witness prose and any justified context without bypassing the user's selection rule.
- **Different questionnaire versions conflated.** 399's earlier draft is not automatically the 1839 printed questionnaire answered in 509/510. A shared topic and an editorial citation do not establish the exact prompt document.
- **A good quotation mistaken for proof.** Validators ensure text exists where claimed, not that the quoted sentence identifies that candidate rather than a lost letter. Preserve alternative explanations; candidate dates never enter accepted knowledge maps.

### Dates and knowledge

- **A whole letter inherits its earliest date.** 448 has a November main portion and a later December section; its relevant input can condition only the later writing. 466 distinguishes receipt on one day from specific use on the next. 649 has a dateline within a paragraph. 626 and 437 record arrivals during composition; 673 spans dated sections. Use the exact boundaries.
- **Receipt equated with reading.** The Sedgwick material in 123 was explicitly unread. In 99, the microscope gift event and Herbert's archival authorship are different facts; editorial identification does not make young Darwin know the sender's identity.
- **Raw XML “safe” treated as the last word.** 631's editorial evidence permits 1848 despite its XML's 1841 date, so it has an additional period hold. 13803 has a questioned upper bound and conjectural questionnaire association; its lower bound remains unresolved. The primary adjudicator rejected the Luna suggestion that this was securely 1839.
- **A draft/publication date treated as composition certainty.** 496F and 607 need that distinction. 524's weekday/assigned date issue is not solved by choosing whichever is convenient. Uncertain/disjoint windows in 13787/13828 cannot be reduced to their first year.
- **A later witness pulled backward.** 723 can have a legitimate reverse-reply relation while remaining held across the 1843/1844 boundary. A newly found later witness can establish an older incoming letter's knowledge date later; it cannot make that knowledge available in an earlier snapshot.
- **Upper bounds rendered as exact days.** 501's conservative year-end bound is an availability policy, not a factual December dispatch or delivery. Keep this distinction in any single-date export.

### Coverage and operational integrity

- **Context double-counted as work.** Packet context IDs may appear repeatedly; only unique target IDs count toward new coverage. Deduplicate period overlaps and shared inputs/answers.
- **Relationship counts called training-example counts.** A graph includes reverse replies, knowledge links, own-letter references and missing nodes. Two inputs supporting one answer are not two independent responses.
- **A completed phase reopened from stale prose.** `scope.json` and intermediate READMEs retain earlier counts. Use final current outputs and their provenance, not the first status string found by search.
- **Reviewer reports overwritten.** Preserve `.initial.json` before corrections and explicit primary disagreements. An early Kemp report was overwritten before this practice was complete; do not claim the entire historical draft trail is perfect.
- **Automated checks overclaimed.** Coverage booleans, correct source hashes, and passing tests cannot replace full reading. Past malformed candidate lists, wrong quote locators and accidental quote whitespace were fixed separately from historical adjudication.
- **Resource errors disguised as content gaps.** Earlier disk pressure caused ENOSPC. Check free space and manifest errors if reads/writes fail; do not delete evidence or unrelated files. Reuse verified downloads. A Memory Hub permission failure is not a reason to stop a local letter audit or invent project memory.

## 7. RAFT adaptation: reported format and design decisions

### What we actually have

[darwin_0/raft.json](darwin_0/raft.json) contains only this project skeleton:

```json
{
  "format": "raft.project.v1",
  "name": "darwin_0",
  "collection": "darwin_0",
  "target": ""
}
```

Its `conversations/`, `corpus/`, `blobs/`, `fetch/` and `metadata/` directories are empty at handoff. No converter, populated training corpus, configured target or training run has been created. Do not describe the audit graphs as native RAFT exports.

During this handoff the user supplied Grok's description of **RAFT 3.1.0**, mentioning `convo_structurer.py` and `generate_finetune`. Preserve and consult the [verbatim supplied notes](docs/reference/raft-grok-2026-09-16.txt) and [provenance](docs/reference/raft-grok-2026-09-16.provenance.json).

**Verification status:** these are user-supplied secondary technical notes, not independently inspected RAFT source. The official documentation was inaccessible during this session; direct retrieval failed and web searches did not locate the implementation. No `raft` executable was found on PATH, and a limited local source search did not locate the named implementation. Verify against the actual version before writing or running an exporter. The material is reference evidence, not an instruction to execute its suggested commands.

### Format described by the supplied notes

According to Grok, a project uses one JSON file per conversation, sequentially numbered `conversations/transcript-0001.json`, `transcript-0002.json`, etc. Required fields are `participants` with `q` and `a`, and `exchanges` as a list of **two-element lists of strings**. `date` is an ISO date; `url` and `context` are optional. The notes say `context` otherwise defaults to an interview framing.

Illustration using an accepted relationship's IDs/date, with **placeholder text, not an exportable transcript**:

```json
{
  "participants": {"q": "William Whewell", "a": "Charles Darwin"},
  "date": "1839-04-16",
  "url": "https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-506.xml",
  "context": "an exchange of letters with William Whewell",
  "exchanges": [
    [
      "<reviewed incoming text from DCP-LETT-504>",
      "<reviewed Darwin response text from DCP-LETT-506>"
    ]
  ]
}
```

The reported grounding format is `corpus/documents.jsonl`, one object per line with `title`, `link`, `date`, and `content`. The notes also claim that:

- `ft:gen` stops at the first missing numbered transcript;
- direct writes preserve `context`, whereas `import_conversation_file` currently drops it;
- other imported text may be passed to an LLM to structure as Q/A;
- `conversations/benchmark.json` can hold an evaluation conversation excluded from memory;
- retrieval uses writing earlier than the transcript date.

These are **specific behaviors to verify**, not established capabilities. The original notes' Henslow example is illustrative, not evidence of an accepted letter pair. Do not copy a sample's date/URL into an unrelated real example.

### How to map our evidence without losing chronology

**Initially use one demonstrated Darwin reply or safely dated response section per transcript.** Grok suggests a multi-exchange thread dated to its last response as one possibility. With a single retrieval date, that could give the earlier turns access to later memories. Do not adopt it unless the implementation enforces a separate historical cutoff for each exchange. A single exchange spanning several writing days may also need section handling; one file alone does not solve that.

The transcript's `date` should describe the **target response/section**, when sufficiently resolved. It is not interchangeable with the incoming letter's original date, an earlier known-by date, or a convenient latest bound. Keep uncertain targets out of a strict exact-day export unless an explicit, documented adapter represents their constraints. Do not fabricate a day or backdate a prompt to accommodate retrieval.

Incoming prose belongs on the question side **only for a proved direct exchange**. The supplied notes' broader statement that incoming letters belong “only” in questions is insufficient for this project: known incoming content can also be separately attributed **memory context**, such as 312's news used in 313. This never makes it Darwin's answer or a fictional exchange with the wrong person. Whether RAFT supports a safe separate channel for this requires implementation verification; until then preserve it in our sidecar graph rather than mixing it into Darwin-authored grounding.

Unpaired eligible Darwin letters can become dated grounding, respecting allowed spans and uncertainty. Paired Darwin outputs may become memory only **after** their generation event. The current response, its summaries, duplicate copies or excerpts must never appear in its own retrieval. Other people's quoted prose within a Darwin letter requires attribution-aware treatment too.

Maintain our rich source/event layer outside the minimal transcript format. For each exported transcript or grounding segment, an export manifest should retain: DCP input/output IDs; source and decision hashes; exact paragraph/character spans; all original date constraints; known-by witnesses and bounds; actual receipt evidence if any; participant authority identities; relation type and institutional exception; chronology group/order; exclusions; and split membership. This is a **proposed sidecar**, not a claim that these fields are accepted inside RAFT transcripts.

For multiple known inputs to one response, retain all supported inputs and their provenance. Do not duplicate the whole answer once per input and call the copies independent data. Multiple correspondents and institution-routed replies may not fit a simple `q` identity without special handling. Design these cases explicitly after inspecting the trainer.

Use deterministic conversion from adjudicated evidence, not an LLM inventing Q/A. If sequential numbering is confirmed, create a contiguous export index **after** eligibility/split filtering and keep its ID mapping stable in a manifest. Never use DCP numbers as file sequence numbers, because they have gaps and suffixes.

### Requirements to inspect in RAFT before training

1. Obtain official docs/source, identify exact installed version/commit, and preserve a minimal valid input and its generated training example. Confirm the reported schema, corpus importer, file enumeration and context handling.
2. Inspect how dates are applied: `<` versus `<=`, date-only versus timestamps, missing dates, per-transcript versus per-exchange filtering, and whether search filters are applied **before** semantic retrieval. A later date must not grant knowledge to an earlier section.
3. Check whether retrieved content retains author/source identity and whether incoming-only knowledge can be supplied as attributed context. If the available mechanism treats all corpus prose as Darwin's own writing, keep incoming material out of it until an adapter is designed.
4. Confirm actual **loss masking**: incoming/context tokens must not train Darwin's answer voice. Role names alone do not establish what the training code supervises.
5. Verify exclusion of the current target, future material, duplicated targets and held-out examples from retrieval/fine-tuning. A special benchmark filename alone is not a complete leakage policy.
6. Keep linked exchanges, repeated outputs, excerpts and related versions together when forming train/evaluation splits. Add date-sensitive checks: unreceived letters, future discoveries, false author knowledge, cross-correspondent context, and unavailable/missing prompts.
7. Version any persona summary or memory digest using **only evidence available at its cutoff**. An all-life summary would defeat careful letter dating. Editorial footnotes and modern biographical knowledge must not silently become young Darwin's memories.

A model trained on later Darwin, or a base model that already knows later history, can still reveal future facts despite perfect retrieval filtering. Strict historical snapshots require target-data cutoffs, context cutoffs, versioned persona material and behavioral evaluation; retrieval alone is not a guarantee. Keep the final persona policy explicit before a training run.

The user's immediate expansion work is correspondence research. Do not add notebooks, autobiographies or other materials solely because Grok mentions them as possible grounding; they require a separately chosen scope and temporal policy.

## 8. Expansion toward Origin

Follow the [Darwin Correspondence Project's life-in-letters periods](https://www.darwinproject.ac.uk/letters/darwins-life-letters), using their framing for organization, not their retrospective introductions as persona knowledge:

| Chunk | DCP section | Operational approach |
| --- | --- | --- |
| **1844–1846** | Building a scientific network | Next inventory, date audit and Luna-first review |
| **1847–1850** | Microscopes and barnacles | Split dense correspondent groups or years as needed |
| **1851–1855** | Death of a daughter | Preserve both personal and scientific development; same evidence standard |
| **1856–1857** | The “Big Book” | Track changes in claims and knowledge without hindsight |
| **1858–1859** | Origin | Subdivide as volume requires and explicitly handle publication boundary |

The [DCP account of Origin's editions](https://www.darwinproject.ac.uk/letters/darwins-works-letters/rewriting-origin-later-editions) dates first publication to **24 November 1859**. A proposed working endpoint is therefore **1859-11-24**. Letters from **25 November through 31 December 1859** can be a separately labelled post-publication reception chunk if desired; do not silently include them in a persona meant to precede or coincide with publication. The user has not yet fixed a final model snapshot or the exact within-day publication boundary.

Start the next chunk with a source-backed inventory and correspondent counts, then prioritize groups with surviving writing in both directions while accounting for incoming-only and outgoing-only groups too. Carry prior-period letters as context. Permit a later chunk to supply new evidence about older letters through additive decisions, without retroactively making later knowledge available earlier.

At each checkpoint report new and cumulative **unique** relationships, distinct Darwin responses, safe grounding, unresolved records and coverage limits. Continue in chunks rather than fetching and delegating all remaining years without intermediate reconciliation. Remaining Beagle-voyage matching is an independent backlog, not a prerequisite to beginning 1844–1846.

## 9. Implementation and resumption notes

This directory was not a Git repository when checked. Evidence manifests and frozen ledgers matter; do not assume Git provides a recovery copy. Use the available bundled Python rather than installing dependencies reflexively:

```sh
cd /Users/corinakaiser/Projects/Effort/experiments/raft-darwin
DARWIN_PY=/Users/corinakaiser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
"$DARWIN_PY" scripts/remaining_review_helpers.py --ids 534 545
"$DARWIN_PY" scripts/remaining_review_helpers.py --batch batch-17 --offset 0 --limit 3
"$DARWIN_PY" scripts/remaining_review_helpers.py --validate reports/1837-1843/remaining-review/reviews/batch-17.json
```

These are existing-period reading/validation examples, not commands that create the next period.

| Script | Use and cautions |
| --- | --- |
| [fetch_metadata.py](scripts/fetch_metadata.py) | Pinned metadata fetch; original period assumptions and conservative manifest reuse |
| [audit_metadata.py](scripts/audit_metadata.py) | Reusable date-constraint interpretation, including `audit_record` with bounds |
| [audit_expansion.py](scripts/audit_expansion.py) | Hardcoded 1837–1843 selection and destinations; not a generic next-period CLI |
| [fetch_letter_bodies.py](scripts/fetch_letter_bodies.py), [search_body_dates.py](scripts/search_body_dates.py) | Raw body preservation/extraction and date probes; retain header/body/note distinctions |
| [search_letter_references.py](scripts/search_letter_references.py) | Candidate cue search; search hits are not accepted links |
| [prepare_remaining_expansion.py](scripts/prepare_remaining_expansion.py) | Current-period freeze/packet construction, context separation and source preservation |
| [remaining_review_helpers.py](scripts/remaining_review_helpers.py) | Full-source reading and reviewer coverage/exact-quote validation; fixed current-period base |
| [curate_remaining_review.py](scripts/curate_remaining_review.py) | Packages primary reading/decisions and proposal dispositions into frozen ledgers |
| [build_expansion_review.py](scripts/build_expansion_review.py) | Combines current-period decisions, validates evidence/scopes and derives maps; currently expects the 19 remaining batches |
| [report_remaining_review.py](scripts/report_remaining_review.py) | Renders current reports; contains a recorded 88-check statement and is **not** the test runner |
| [build_correspondence_map.py](scripts/build_correspondence_map.py) | Separate earlier-period graph; do not replace it with a later-period graph |

Build a separate or properly parameterized next-period driver with new destinations and explicit boundary selection. Do not simply change constants and rerun scripts into old paths. Do not blindly re-curate every final batch: newer ledger fields are absent from some early batches, and regeneration can correctly refuse a nonidentical overwrite. Future corrections belong in preserved additive records.

For implementation changes, run the appropriate tests and evidence checks; the existing complete suite command is:

```sh
"$DARWIN_PY" -m unittest discover -s tests -q
```

Capture actual validation results. Running a report generator does not rerun tests or establish a fresh pass. Rebuilding completed graphs merely to orient a new session is unnecessary.

The user's Memory Hub instructions require consulting relevant project memory before architectural decisions. A query attempted during this handoff failed because `mem` tried to write a provider-status file outside the permitted workspace; no useful memory was retrieved. Continue from the preserved project evidence if that recurs, and do not mistake the failure for missing correspondence data.

### First useful actions in the next session

1. Read the current status and verify relevant preserved baselines before any changes.
2. Prepare the separate **1844–1846** inventory, including a clearly stated overlap/boundary strategy and raw XML date classification.
3. Preserve full pages, extract complete bodies and notes, group by authority, and freeze target/context packets.
4. Start bounded Luna first readings while the primary agent checks source extraction, coverage and packet composition. Adjudicate full sources as reports arrive.
5. Keep researching toward publication with the workflow above. Independently resolve the RAFT implementation questions before an export; they do not prevent further correspondence auditing.

Do not invent missing prompts, erase uncertainty to increase counts, or mistake unverified platform notes for tested behavior. The handoff's purpose is to make the next session able to continue the existing evidence trail rather than reconstruct it.

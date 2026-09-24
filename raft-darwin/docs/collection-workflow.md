# Darwin collection workflow

Written 22 September 2026 from the fetching scripts, packet instructions, primary adjudication records and September 17 export. This is a continuation guide for collecting more material. It covers research and data preparation; training is a separate activity.

**Project objective.** Build an evidence-grounded Charles Darwin persona that preserves the development of his knowledge, relationships and voice. Genuine incoming → Darwin reply pairs provide examples of how he responds; eligible unpaired Darwin writing provides dated retrieval material. Historical fidelity depends on what he demonstrably knew by the relevant date, as well as whose words survive and what they say.

The starting choice was younger Darwin, beginning in 1828; the completed collection extends through publication of *Origin* on 24 November 1859. The collection preserves the temporal structure needed for a chosen historical cutoff, successive persona snapshots or comparisons between periods. Choosing the final persona date and evaluating its historical fidelity are separate model decisions. The [original objective and decisions](../HANDOFF.md#1-objective-and-decisions-already-made) preserve that context; the [current RAFT compatibility note](raft-compatibility-2026-09-22.md) explains the remaining difference between dated training examples and a chat persona constrained to a historical date.

The workflow is: **define a chronological window → preserve sources → assign correspondent packets → read backwards from Darwin's replies → independently adjudicate → reconcile the whole collection → prepare one cumulative export.** The chronological chunks organize research. They do not become separate training datasets. The next proposed research endpoint is the end of 1868, covering *Variation* publication and its reception; the completed baseline still ends in November 1859.

The checkout inspected for this guide is `/Users/corinakaiser/Projects/personas/raft-darwin`. Earlier documents name `/Users/corinakaiser/Projects/Effort/experiments/raft-darwin`; that location has moved. Resolve the actual checkout and installed tools at the start of another session.

## 1. Start from the completed work

Read [HANDOFF.md](../HANDOFF.md), [research status](../reports/research/work_status.json), the [export report](../reports/raft-export/README.md), and the [export manifest](../reports/raft-export/manifest.json). Consult the [hold queue](../reports/raft-export/hold-queue.json) before commissioning new searches: a relevant source may already be preserved, reviewed or explicitly unresolved. Older progress fields in `scope.json` and earlier phase reports are historical.

The September 17 baseline covered an export window of **1828-01-01 through 1859-11-24, inclusive**. It accounted for 3,031 source records and established 221 direct relationships across 205 Darwin response sources. After date, attribution and content checks, it produced **162 conversation transcripts** and **1,405 grounding documents**. Relationships, source letters and exported sections have different counts. These are the recorded data-preparation results, not a report on subsequent training.

**Proposed second collection run: *The Variation of Animals and Plants under Domestication*, including its reception through the end of 1868.** Use **31 December 1868** as the inclusive endpoint. The new research interval is **25 November 1859–31 December 1868**, and the eventual cumulative release would cover **1 January 1828–31 December 1868**. This retains the weeks immediately after *Origin* and includes letters about *Variation* after publication. Its first English publication on **30 January 1868** is a milestone within the run, as documented in [Freeman's bibliographical introduction](https://darwin-online.org.uk/EditorialIntroductions/Freeman_VariationunderDomestication.html).

The supplied timeline entry highlights the book's extensive evidence about domesticated breeds and its use of smaller type for supporting material. Publication and the correspondence that follows form a useful sequence for studying Darwin's evidence gathering and responses to readers. The proposed run extends the correspondence collection; adding the book itself would require a separate edition-and-text-layer decision. Its authorial evidence in smaller type must not be mistaken for modern editorial apparatus.

The [filesystem map and second-run organization plan](collection-layout-and-run-02.md) explains the existing materials, proposes annual research periods and one run-level index, and separates a cumulative data release from training workspaces. A read-only catalogue sorting-date screen finds **4,182** Darwin-related records in the new interval; this is a workload estimate, not an audited inventory or pair count. The proposal is documented here; the second fetch has not been started.

For an expansion, establish the next chronological window and intended cumulative endpoint. Continue using the Darwin Correspondence Project's life-and-letters periods as contextual reading guides. Their selected examples help explain the period; they are not exhaustive inventories. A chart of yearly letter counts likewise does not establish completeness.

Preserve the release being used for training. Develop the next collection in new research/staging locations and eventually create a new, explicitly versioned cumulative release. That keeps one coherent dataset per release while retaining the previous experiment's reproducibility.

## 2. Keep the data roles distinct

| Evidence found | Research interpretation | RAFT treatment |
| --- | --- | --- |
| Surviving incoming letter demonstrably answered by Darwin | Confirmed direct incoming → Darwin relationship | Conversation candidate: incoming prose is the question; the supported Darwin reply or section is the answer. |
| Eligible Darwin writing with no established surviving incoming prompt | Unpaired Darwin writing | Dated grounding document. An unavailable prompt stays unavailable. |
| Incoming letter whose contents Darwin demonstrably knew, without an established reply to its author | Knowledge-only relationship | Keep the dated witness and attribution in research records; do not put the incoming prose into Darwin-voice grounding. |
| Correspondent answers a Darwin letter | Reverse reply | Preserve that relationship. It does not make the correspondent's answer a Darwin training target. |
| Shared topic, nearby date, possible missing letter, uncertain identity, date or source layer | Candidate, missing reference or hold | Retain the evidence and uncertainty; emit no unsupported exchange. |

“Question” means the historical incoming communication, including statements and requests; it need not contain a question mark. Do not invent a modern question or use an LLM to turn a lone Darwin letter into dialogue.

A letter can have more than one relationship, and a response can answer several inputs. Keep all established edges while exporting the Darwin response once. Several incoming letters from the same correspondent can form one question in their established order. Distinct authors need explicit attribution and an appropriate representation; do not silently merge them into one person.

In the completed export, **all accepted Darwin response source IDs were reserved from grounding, including responses held out of conversations**. Reuse that separation when reconciling a new release. If new evidence turns an old grounding letter into a confirmed response, change its role in the next release and record the change; preserve the dataset already used for training.

## 3. Discover broadly, then preserve the actual sources

The metadata source was Cambridge's `epsilon-data`, pinned at revision `ab0d973bae05b54d68d82d068211015996cfec06`. The preserved CSV contains 15,238 rows. [fetch_metadata.py](../scripts/fetch_metadata.py) records that revision; [prepare_period.py](../scripts/prepare_period.py) implements the broader discovery used for later periods.

Discovery considers catalogue sorting dates, years in displayed labels, abbreviated year ranges, open “before”/“after” bounds, missing full years, and overlap or uncertainty in already preserved XML. A sorting date is a discovery aid, not proof of composition on that day. Keep the original label, alternatives and XML constraints.

Confirm **Charles Robert Darwin's identity**, rather than matching the surname alone. The CSV screen uses `Darwin, C. R.`; XML authority evidence uses `nameregs_1.xml`. Preserve sender/recipient authority evidence, joint authorship and correspondence direction. Inspect unaddressed memoranda separately: they may contain attributable writing but are not automatically correspondence pairs. Third-party letters may be separately admitted as research context when they explain a chain; they do not become independent Darwin-voice documents or direct prompts merely through that connection.

The broad selector is not a full XML audit of every catalogue row. State the actual discovery method and coverage limit, and preserve metadata-only exclusions and boundary probes. Deduplicate by the complete DCP ID, including suffixes such as `A` or `F`.

Preserve two distinct layers:

- **Metadata:** original CSV strings and row provenance, XML, revision, identity and date constraints.
- **Source text:** full public HTML, plus separately needed enclosure, figure, manuscript or printed-witness material.

XML in this collection supplies metadata, not the full transcription. The public letter pages supply the body. Check that a retrieved page actually identifies the requested letter; a successful HTTP response alone is insufficient. Store URL, retrieval time, SHA-256, byte count and available response metadata. Reuse a preserved source only after checking its hash. Record missing pages and retrieval failures explicitly.

Sources live under `data/raw/epsilon/` and `data/raw/dcp/`. Keep their bytes unchanged. New witnesses or enlarged inventories get explicit supplemental admissions and provenance rather than replacing earlier evidence. The fetcher used modest concurrency, bounded retries and incremental manifests so interrupted collection could be resumed.

## 4. Route bounded packets by correspondent and chronology

The later-period packet builder grouped letters by correspondent authority and ordered them chronologically, with preceding letters supplied as context. It ordinarily split work around **18 target records or 10,000 estimated words**; unusually long sources and added context require judgment. These are reading-workload limits, not truncation limits.

Keep ordinary period correspondence separate from **boundary-date probes**. A record discovered through a broad date possibility may actually belong much later. Its presence in a packet does not admit it to the period or make its contents available to Darwin at the target date.

Each target belongs to exactly one packet within a period; context may recur across packets and periods. Workers can request additional source retrieval when the comparison requires it. The initially supplied context is a starting point, not the universe of plausible antecedents.

The parallel arrangement we used was:

| Role | Responsibility and write ownership |
| --- | --- |
| Primary agent | Scope, source preparation, independent full-source adjudication, accepted ledgers, cross-period reconciliation and final export. |
| Two Luna readers initially | Independent first passes on separate correspondent packets; write only their assigned review reports. |
| Preparation worker initially | Inspect installed RAFT behavior and compile formatting requirements while research continues. |
| Third Luna reader after preparation | Take further packets once the preparation slot is free. |

Pipeline the work: while readers examine their next packets, the primary adjudicates completed ones. A formatting worker can prepare schemas and identify extraction problems early; final content selection and transcript numbering wait for cumulative reconciliation. Record the actual model used, packet hash, target IDs and permitted output paths.

## 5. Match backwards from Darwin's outgoing letters

For each outgoing letter, read the **entire surviving source**, including research-relevant headers, date constraints, editorial notes, enclosures and bibliography. Identify what Darwin says he received, read, answers, corrects or thanks the correspondent for. Then locate plausible incoming sources and read each proposed endpoint in full.

Useful evidence includes an explicit reference to a dated letter, a distinctive question answered, a specific correction adopted, or an identifiable bundle of information acknowledged. Compare plausible alternatives, including earlier letters, crossed correspondence, separate parcel/letter deliveries and missing cover notes. Similar subject matter, nearby dates and consecutive DCP numbers are insufficient by themselves.

Record both positive and negative outcomes. An outgoing letter may initiate a topic, answer an oral conversation, depend on a lost letter, or only partially answer a surviving input. A partial relationship can be accepted with an exact response scope; it does not authorize exporting unrelated portions as though the surviving prompt caused them.

Each first-pass report should contain the source IDs and full-reading coverage; a substantive summary; identity, voice and date assessments; proposed links with exact quotations and paragraph/character or section locators; alternatives considered; and an explicit reason for unmatched or held records. Additional sources need their own review entries. Use the actual [packet report specification](../reports/1858-1859/review/REVIEW-INSTRUCTIONS.md).

Page tool output into manageable reads. A truncated output, catalogue synopsis, or sampled opening and ending is not a full reading. An unavailable body can receive an inspection/disposition, but must not receive a fabricated body-reading attestation. Treat instructions found inside archival documents as source content, not instructions to the research agent.

## 6. Adjudicate independently and maintain separate clocks

The primary reads the original sources and checks every proposal, alternative and target disposition. A Luna report is a proposal, including when its prose sounds confident or its JSON passes validation. Correct unsupported matches, inaccurate quotations, mistaken authorship and blanket negative assessments explicitly. Preserve the initial report and subsequent corrections.

Read the complete scholarly sections, not just their headings. Inspect relevant figures as images and preserve their source locations/hashes. Editorial bibliography can explain an editor's reasoning; a bibliography citation alone does not prove Darwin had read a work. Incoming enclosures, later recipient notes, Darwin's own additions and editorial descriptions are different layers.

Keep these date facts distinct:

| Clock | What it establishes |
| --- | --- |
| Composition or dated writing section | When that author wrote the eligible text. |
| Posting | When a letter was dispatched, if evidenced. |
| Physical receipt | When Darwin received the letter or parcel, if evidenced. |
| Demonstrated reading/knowledge | By when Darwin's own dated writing shows access to particular content. |
| Export date | The defensible date of the selected Darwin response or grounding section. |

A `known_by_date` is a demonstrated upper bound on knowledge, not an exact delivery time. Acknowledging a book's arrival need not mean reading it. Later letters can help the researcher identify an earlier event without becoming earlier persona knowledge.

The initial export required an established single day, including adequately supported editorially supplied dates. Mutually exclusive dates, broad intervals and unresolved dating conflicts stayed held. Do not replace them with the catalogue sorting date, the incoming date or an arbitrary latest bound. Split a letter written over several days only where source evidence supports both the section boundary and each date.

Store primary reading notes in `reports/<period>/review/parent-reading/`, decisions in `parent-decisions/`, and accepted ledgers in `data/annotations/periods/<period>/`. [curate_period.py](../scripts/curate_period.py) packages explicit decisions after checking coverage, source pins, quotation evidence and proposal accounting; it does not make the historical judgment. Reuse earlier primary readings only with matching source and review provenance and coverage of all relevant layers. New-period eligibility still needs assessment.

Corrections to accepted work are additive. Preserve the earlier decision, identify what changes and why, and pin the new evidence. A historically accepted link can still have `training_export_ready: false`: content eligibility is decided later.

## 7. Reconcile the whole collection before conversion

Close each research checkpoint with every target assigned a disposition, every first-pass proposal adjudicated, and every accepted relationship linked to primary evidence. Validate hashes, exact quotations, source-layer reading records, dates and coverage. Structural checks establish those properties; they do not establish historical truth by themselves.

Then combine all periods and additive corrections. Deduplicate source IDs and relationships, normalize relationship direction, and distinguish direct Darwin replies from reverse replies and knowledge links. Some older ledgers express `replies_to` as response → antecedent; the exported exchange must be incoming → Darwin. Do not count every graph edge as a conversation.

Report source records, direct links, distinct Darwin responses, response sections, grounding units, unavailable texts, exclusions and holds separately. Keep negative decisions and unresolved references. [Source accounting](../reports/raft-export/source-accounting.jsonl) and [relationship accounting](../reports/raft-export/relationship-accounting.jsonl) show the completed release's approach.

Freeze the cumulative adjudicated input for the next release only after that reconciliation. A correspondence chunk is a checkpoint within this process, not its own frozen training group.

## 8. Prepare source-faithful text and RAFT records

Apply the [content policy](raft-export-content-policy.md) after historical acceptance. Read broadly for evidence; export only the permitted authorial text. Remove letter headers, datelines used as headers, routing addresses, editorial summaries, footnotes, annotations, bibliography, navigation and stamps. Preserve names, dates and source URLs as metadata and retain the scholarly evidence in sidecars.

Class-based HTML filtering is only the first pass. We found dates and recipient addresses embedded in ordinary paragraphs and signatures. Those required source-specific cuts. Conversely, an address inside an author's actual shipping instructions can be meaningful prose. Check context rather than deleting every place name or address-shaped line.

Preserve spelling, meaning and uncertainty. Repair transcription/extraction artifacts only where markup or an authoritative witness supports the change. Examples from this pass:

- MathML established **3¼**, preserving the integer part; flat digit strings alone did not establish a fraction or currency amount.
- Authorial text sometimes appeared in a `supplemental` or enclosure container; explicit authorship/date review determined whether to include it.
- A Davy question required a separately preserved printed witness and comparison of all nine page images, rather than substituting a catalogue synopsis.
- A question surviving only in editorial apparatus could establish a historical relationship while remaining excluded from this export's question text.
- A drawing, broken table/list or illegible passage held the dependent unit unless an independently usable excerpt was explicitly approved. A modern description of the drawing was not substituted for authentic letter text.

Record original text, corrected text, locator, source hash and repair rationale. Keep original extraction offsets distinct from cleaned-text positions. [raft_export_text.py](../scripts/raft_export_text.py) verifies source spans and projects them through supported markup changes; ambiguous mappings are held. Inspect rendered content and account for every excluded span or held unit.

Use **one exchange per transcript**, dated to the Darwin reply or independently dated section. These are schematic examples, not real letter transcriptions:

```json
{
  "participants": {"q": "Correspondent's name", "a": "Charles Darwin"},
  "date": "1859-11-24",
  "url": "https://www.darwinproject.ac.uk/letter/DCP-LETT-EXAMPLE#raft-response-example",
  "context": "a letter from the correspondent, which you are answering",
  "exchanges": [["Verified incoming prose", "Verified Darwin response prose"]]
}
```

```json
{"title":"To correspondent, 1859-11-23 [DCP-LETT-EXAMPLE; section 0]","link":"https://www.darwinproject.ac.uk/letter/DCP-LETT-EXAMPLE","date":"1859-11-23","content":"Verified unpaired Darwin prose"}
```

The first goes in `conversations/transcript-NNNN.json`; the second is one line in `corpus/documents.jsonl`. Keep citations, evidence quotations, repair logs and review explanations in provenance files rather than injecting them into the letter prose.

The preparation audit inspected installed **RAFT 3.1.0**. Its relevant behavior was:

- Transcript numbering starts at 1 with no gaps; generation stops at the first missing file.
- Direct JSON writes preserve `context`; the importer inspected then dropped it.
- Dated retrieval uses `memory_date < transcript_date`, excluding same-day material. Invalid or missing dates can become zero, so they were excluded from the historical export.
- All exchanges in a transcript share one retrieval date. Multiple exchanges are valid syntax, but grouping a long correspondence under its last date would expose early responses to later material.
- Grounding embedding IDs depend on title and chunk part. Exchange IDs depend partly on URL and the question's opening text. Unique DCP/section titles and export URL fragments prevented collisions; canonical source URLs remained in provenance. These fragments are export identifiers, not claimed website anchors.

The [22 September compatibility check](raft-compatibility-2026-09-22.md) reconfirmed these format rules against the current editable RAFT checkout and records subsequent training/serving changes. Recheck the resolved implementation and commit before a future release; the [formatting audit](raft-formatting-readiness.md) remains the historical contract. Keep related exchanges, excerpts and alternate witnesses together when training/evaluation splits are later chosen.

## 9. Reuse the scripts with their actual boundaries

Use a Python environment with the project's dependencies. The previous session used the bundled interpreter shown below. After registering a **new** period in `prepare_period.py`, the collection sequence is:

```sh
cd /Users/corinakaiser/Projects/personas/raft-darwin
DARWIN_PY=/Users/corinakaiser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
DARWIN_PERIOD=NEW_PERIOD_KEY

"$DARWIN_PY" scripts/prepare_period.py --period "$DARWIN_PERIOD" --stage metadata --fetch
"$DARWIN_PY" scripts/prepare_period.py --period "$DARWIN_PERIOD" --stage bodies --fetch
"$DARWIN_PY" scripts/prepare_period.py --period "$DARWIN_PERIOD" --stage packets
```

`NEW_PERIOD_KEY` is a placeholder. The current period registry ends at `1858-1859`; adding a key requires agreed dates and inspection of downstream period selectors. Do not run the preparation sequence against a completed period to start an expansion: it writes derived records, while frozen inventories refuse changes. Supplement an existing inventory explicitly when needed.

The current source reader supports these read-only forms:

```sh
"$DARWIN_PY" scripts/period_review.py --period 1858-1859 --batch batch-01 --offset 0 --limit 2
"$DARWIN_PY" scripts/period_review.py --period 1858-1859 --ids 717 722
```

For a new assigned packet, the later steps are:

```sh
"$DARWIN_PY" scripts/period_review.py --period "$DARWIN_PERIOD" --validate "reports/$DARWIN_PERIOD/review/reviews/batch-01.json"
# After the primary has written the complete reading notes and decisions:
"$DARWIN_PY" scripts/curate_period.py --period "$DARWIN_PERIOD" --batch batch-01
"$DARWIN_PY" scripts/verify_period_ledgers.py --period "$DARWIN_PERIOD"
```

The latter two commands write the new ledger/status and integrity report. Copy a prior packet's instruction/schema files as a starting point and update its dates, scope and context deliberately.

| Tool family | Reuse boundary |
| --- | --- |
| `prepare_period.py`, `audit_metadata.py`, `period_review.py` | Core discovery, metadata constraints, source extraction, packets and reading; extend the period configuration. |
| `fetch_metadata.py`, `fetch_letter_bodies.py` | Earlier bounded fetch entrypoints; do not assume their original date/ID ranges collect a new period. |
| `preserve_letter_figures.py` | Figure preservation pattern; its current source/output constants point to 1844–1846 and need explicit adaptation. |
| `curate_period.py`, `verify_period_ledgers.py` | Explicit adjudication packaging and integrity checks; not automated historical matching. |
| `raft_export_inventory.py`, `plan_raft_*.py`, scope/cut resolution scripts | Historical selection and corrections; several are one-off scripts tied to this release, not an arbitrary-period pipeline. |
| `raft_render_text.py`, `raft_export_text.py`, `render_raft_staging.py` | Source-aware rendering and staging. Review hard-coded source admissions and selectors before reuse. |
| `export_raft_cumulative.py` | September release writer/validator: fixed 1859 cutoff, `darwin_0` destination, `1858-1859` source load and inventory-count assertions. Adapt for a new release; changing only the cutoff is insufficient. |

Several scripts and policies are themselves hashed in the existing export manifest. Preserve those versions; put expansion adaptations in new versioned files or a separate working copy. The old exporter refuses overwrite. Its `--check` mode rewrites validation/manifest metadata, and the ledger verifier writes an audit report: neither should be treated as a completely read-only command against an active training release. A later RAFT upgrade also requires a new compatibility audit rather than suppressing implementation-hash mismatches.

## 10. Completion and next-session brief

Before declaring the new release ready, establish that:

1. Every selected source and proposed relationship has a primary disposition; all supplemental corrections are reconciled.
2. Every emitted unit has the right author, established relationship where required, permitted source spans, defensible date and original-source provenance.
3. Rendered questions, answers and grounding contain no excluded apparatus, unsupported repairs or unresolved dependencies.
4. Transcript numbering is gapless, exchanges are two nonempty strings, dates parse, source/section identifiers are unique, and duplicate response text cannot enter grounding.
5. Every held, unavailable, excluded and outside-window record is accounted for using clearly labelled denominators.
6. Written files, source pins and manifest agree; appropriate renderer/date/provenance checks pass. Record what was actually tested rather than treating coverage assertions as proof of full reading.
7. The release report and handoff state the endpoint, counts, file locations, unresolved holds and the boundary between data validation and training validation.

The September pass used focused renderer/projection tests plus full written-file validation; its [validation record](../reports/raft-export/validation.json) is the historical result. This guide did not rerun data generation or training.

Copy this brief when commissioning the second collection run, using the full-year endpoint and confirming the release destination before executing it:

> Continue the Darwin collection using `docs/collection-workflow.md`, the current handoff, research status and export manifest. Use `docs/collection-layout-and-run-02.md` for the filesystem and run plan. The proposed new interval is **1859-11-25 through 1868-12-31**, with cumulative coverage from **1828-01-01**. Organize the work as `run-02-variation`, beginning with the post-*Origin* remainder of 1859, then annual periods through the whole of 1868, including correspondence about the published book. Preserve the release currently used for training. Locate and hash-check existing evidence before fetching duplicates. Use DCP timeline context and a broad metadata/date audit, then bounded correspondent packets. Have Luna readers work backwards from complete Darwin outgoing sources toward surviving incoming prompts, with independent primary full-source adjudication of proposals and negative outcomes. Keep direct replies, reverse replies, knowledge-only evidence, grounding and holds distinct; preserve original dates and text layers. Prepare formatting in parallel, then reconcile the entire collection before exporting one cumulative snapshot to the proposed **`releases/variation-1868-v1/`** destination. Keep training runs in separate working projects and record their release provenance. Use one demonstrably dated Darwin reply/section per transcript, keep eligible unpaired Darwin prose as dated grounding, and retain source/repair provenance and all holds outside the training text. Revalidate the installed RAFT contract and adapt release-specific scripts deliberately. This collection task does not itself request a training run.

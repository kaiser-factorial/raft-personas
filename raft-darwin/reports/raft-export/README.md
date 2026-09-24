# Cumulative Darwin RAFT export

Validated on 17 September 2026. One cumulative snapshot covers established writing dates from **1 January 1828 through 24 November 1859**, inclusive. Research periods remain provenance groups; they are not separate training exports.

- **162 conversation files**, `darwin_0/conversations/transcript-0001.json` through `transcript-0162.json`, represent **155 Darwin response sources**. Each file contains one incoming → Darwin exchange at its own established response date.
- **1,405 grounding documents** from **1,399 Darwin sources** are in `darwin_0/corpus/documents.jsonl`. Separately dated sections account for the difference.
- **3,031 source records** are accounted for. The research inventory establishes **221 direct relationships across 205 Darwin response sources**; relationships, sources and exported sections are different denominators.

## Content and dates

Only the approved authorial spans are emitted. Letter headings, datelines used as headers, addresses used as routing metadata, footnotes, annotations, bibliography and navigation are excluded. Meaningful postal instructions within authored prose remain. Original spelling and qualified readings are preserved. Fractions, layout and extraction artifacts are repaired only where source evidence supports the rendering; unresolved text or visual dependencies hold the affected unit.

Composition, receipt and demonstrated knowledge dates remain distinct in the research evidence. The transcript date is the established Darwin response day or separately dated section, never an invented scalar for an uncertain interval. The installed RAFT retrieval filter uses dates strictly earlier than the transcript date; same-day material is unavailable. No undated records are emitted. Every accepted response source, including a held response, is reserved from grounding.

The Davy input uses the separately preserved printed letter witness, checked against all nine page images and corrected in the primary transcription. Its PDF/page pins and textual repairs are retained outside the training content.

## Holds and accounting

- **14 whole Darwin response sources** are held before rendering, principally for uncertain days; one incoming question survives only in an editorial footnote.
- The remaining responses produce **199 candidate conversation units**: **162 exported**, **37 held** for source/content issues.
- **1,472 candidate grounding units** produce **1,405 exported documents** and **67 held units**.
- Before rendering, **496 grounding-source candidates** are held for dates, voice, source extent or content. **56 boundary records** are outside the export window. Another **809 records** are excluded from grounding, including incoming correspondence; some still supply valid conversation questions.
- Partial holds, including undated continuations, unavailable geological input, unresolved numerical strings and conjectural enclosures, are recorded separately. Do not add source, relationship and section counts together.

The [hold queue](hold-queue.json) records every export hold and the separate outside-window list. [Source accounting](source-accounting.jsonl) covers every selected source; [relationship accounting](relationship-accounting.jsonl) covers all 221 established direct links, including those with no exported text.

## Validation and provenance

[The manifest](manifest.json) pins the final files, immutable selection snapshots, primary ledgers/rendering decisions, source witnesses and installed RAFT code. [Per-entry provenance](provenance.jsonl) identifies each JSON file or JSONL line, original source IDs, exact selected spans, date basis and accepted relationship. Full rendering audits and repairs are preserved in [the staging snapshot](inputs/rendered-staging.json).

[Written-file validation](validation.json) passed: native RAFT schema/date helpers, strict content/date checks, 1-based gapless numbering, unique embedding identifiers, exact-text deduplication, response/grounding separation, 8,773 original body spans, 8,812 body/supplement blocks and 1,716 source files including the printed witness images. Fourteen focused renderer/projection tests also passed. Validation combines the completed primary historical readings with per-entry source/markup checks and source-specific manual corrections; it does not claim a fresh manual rereading of every letter during conversion.

Grounding titles include DCP/section IDs because RAFT derives chunk IDs from titles. Transcript URLs contain unique export fragments because RAFT derives exchange IDs partly from URLs. Those fragments identify exported response sections; they are not claimed to be native website anchors. Canonical source URLs are preserved in provenance.

To verify the saved export offline:

```sh
/Users/corinakaiser/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/export_raft_cumulative.py --check
```

The exporter refuses to overwrite a frozen export. No benchmark, chunking, embeddings, fine-tuning generation, model training or paid service call was performed. Evaluation grouping and tokenizer/loss-mask checks remain future training work; related sources/sections must stay together when choosing a benchmark.

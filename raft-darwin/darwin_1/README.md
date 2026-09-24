# darwin_1 prepared data (Post-Origin Run 02)

Validated cumulative export for the post-*Origin* interval: **1859-11-25 through 1868-12-31**.

- **765** single-exchange transcripts in `conversations/transcript-0001.json` through `transcript-0765.json`.
  - Representing **794** accepted direct reply pairs across **765** distinct Darwin response letters.
- **1262** dated Darwin grounding documents in `corpus/documents.jsonl`.
  - Authored exclusively by Charles Darwin, with verified exact single-day dates strictly within the post-origin research interval.
  - Fully disjoint from conversation answers: no target answer text appears in grounding documents.

## Schema & Standards
- Conforms to RAFT project format `raft.project.v1` (`raft.json`).
- Transcripts feature gapless 1-based numbering, normalized participants (`q`: Correspondent, `a`: Charles Darwin), letter-specific context, and clean authorial letter prose with editorial apparatus, footnotes, and annotations excluded.
- Formatted on 2026-09-24.

# Darwin materials: filesystem and second collection run

Inspected and proposed 22 September 2026. The current project root is `/Users/corinakaiser/Projects/personas/raft-darwin`. This companion to the [collection workflow](collection-workflow.md) describes the existing filesystem first, then a proposed organization for the next run. The new run, directories and release described below have not been created or fetched by this documentation update.

## Next endpoint and scope

Use **`run-02-variation`** as the proposed research-run identifier. Its new correspondence window is **1859-11-25 through 1868-12-31, inclusive**; the intended cumulative release covers **1828-01-01 through 1868-12-31**. The first English issue of the two-volume *The Variation of Animals and Plants under Domestication* appeared on 30 January 1868. A further issue followed in February. Publication is a milestone inside this run; the year-end endpoint also captures subsequent correspondence about the work. [Freeman's bibliographical introduction](https://darwin-online.org.uk/EditorialIntroductions/Freeman_VariationunderDomestication.html).

The user extended the scope to the whole of 1868 so that letters discussing the published book are included. Review all eligible correspondence in the date window, including other subjects; *Variation* supplies the historical landmark, not a keyword restriction. Earlier or later letters may still be needed as explicitly labelled research context to identify a relationship or date. Context admission does not make those letters eligible training text or make later information available to an earlier Darwin.

Retain the existing pair-versus-grounding distinction. The endpoint does not itself commission ingestion of the book. If the book is later added, pin the specific issue, volume and page; distinguish Darwin's own supporting evidence, including smaller-type text described in the user's timeline excerpt, from editorial material. A publication date does not establish when each passage was composed or available in manuscript.

## Existing filesystem and what each layer means

Paths in the trees are relative to the project root above. `<period>` and `<revision>` stand for existing or proposed directory names, not literal paths to create.

```text
raft-darwin/
├── HANDOFF.md, docs/collection-workflow.md   entrypoints and method
├── data/
│   ├── raw/
│   │   ├── epsilon/<revision>/             pinned CSV and XML metadata
│   │   │   ├── letters/                   earliest selected XML
│   │   │   └── expansions/<period>/       later XML and manifests
│   │   ├── dcp/<period-or-phase>/         HTML pages, figures, manifests
│   │   └── supplemental/                  separately preserved witnesses
│   └── annotations/
│       ├── periods/<period>/batch-*.json   accepted primary ledgers
│       ├── reconciliation/                cross-period admissions/corrections
│       └── ...                            earlier phase ledgers/attributions
├── reports/
│   ├── <period>/                          discovery, date audit, exclusions
│   │   └── review/                        packets, readings and decisions
│   ├── research/                          first-run status and checkpoints
│   ├── raft-prep/                         format work and rendering proposals
│   └── raft-export/                       first release's frozen audit package
├── scripts/, tests/                       preservation, review and export tools
├── darwin_0/                              existing RAFT working project
└── darwin_thinking/                       another existing RAFT working project
```

| Layer | How to use it |
|---|---|
| [Raw metadata](../data/raw/epsilon/) | CSV discovery data and selected XML, pinned to revision `ab0d973bae05b54d68d82d068211015996cfec06`. XML supplies identity/date constraints, not the full transcription. Preserve original bytes and manifests. |
| [Raw letter pages](../data/raw/dcp/) and [supplemental witnesses](../data/raw/supplemental/) | Full HTML and separately preserved evidence such as figures or printed witnesses. Follow the manifest's path and hash: a period manifest can point to a source acquired in an earlier phase. Folder names describe acquisition history; source evidence establishes chronology. |
| [Period reports](../reports/1858-1859/) | `discovery_audit.jsonl` explains candidate discovery; `audit.jsonl`, `safe_within_period.jsonl`, `ambiguous_or_later.jsonl` and exclusions explain subsequent date/identity dispositions. A “safe” metadata row is not an accepted conversation or cleared export. |
| [Review directory](../reports/1858-1859/review/) | `letters.jsonl` holds that period's extracted sources; `all_letters.jsonl` adds comparison/context records. `packets/` and `manifest.json` fix assignments. `reviews/` contains first passes and revisions; `parent-reading/` and `parent-decisions/` contain primary evidence and adjudication. `work_status.json` tracks packet progress. |
| [Accepted annotations](../data/annotations/periods/) and [reconciliation](../data/annotations/reconciliation/) | Authoritative historical decisions, with evidence links and explicit corrections. Initial Luna proposals do not become accepted because they appear in a report or pass a schema check. |
| [RAFT preparation](../reports/raft-prep/) | Implementation audit, fixtures, candidate plans, source-specific rendering requirements and repairs. Candidate material remains distinct from the export's selected inputs. |
| [Frozen export audit](../reports/raft-export/) | `manifest.json` pins the release; `inputs/` records selected plans/rendering; `provenance.jsonl` traces every emitted unit; source/relationship accounting and `hold-queue.json` explain omissions. This is the authority for what actually entered the first release. |
| [darwin_0](../darwin_0/) and [darwin_thinking](../darwin_thinking/) | RAFT projects containing input text and generated working material. Inspection found generated fine-tuning files, an HF run directory in `darwin_0`, and Chroma/chunk files in `darwin_thinking`. Their copied README text describes an earlier preparation milestone; directory presence does not establish training success. Preserve both during collection work. |

The source archive, proposed relationships, accepted relationships, rendered export and training artifacts answer different questions. Start with the export manifest when checking an existing training input, the accepted ledger when checking a match, and the raw source when checking wording or chronology. Earlier root README/scope/status prose remains historical where it describes smaller completed stages.

## Scale and research periods

A read-only inventory on 22 September counted 6,375 files under `data/raw` (384.3 MiB of summed file sizes), 382 under `data/annotations` (25.2 MiB), and 2,209 under `reports` (919.3 MiB). These are file counts, not unique letters; they exclude the RAFT project directories and model artifacts. The large report footprint makes avoiding repeated full-text copies worthwhile.

The pinned 15,238-row CSV contains **4,182 distinct IDs** with exact CSV identity `Darwin` / `C. R.` on either side and a parseable catalogue sorting date inside the proposed interval: **2,180 outgoing and 2,002 incoming**. This is only an initial workload screen. It does not apply the broader display-date/XML-interval search, prove a body survives, determine individual authorship, or establish a reply pair. Some sources may already be cached as earlier boundary context; this is not a new-download count.

| Proposed period key | Inclusive review window | Sorting-date screen |
|---|---|---:|
| `1859-post-origin` | 1859-11-25–1859-12-31 | 64 |
| `1860` | 1860-01-01–1860-12-31 | 478 |
| `1861` | 1861-01-01–1861-12-31 | 373 |
| `1862` | 1862-01-01–1862-12-31 | 549 |
| `1863` | 1863-01-01–1863-12-31 | 496 |
| `1864` | 1864-01-01–1864-12-31 | 343 |
| `1865` | 1865-01-01–1865-12-31 | 253 |
| `1866` | 1866-01-01–1866-12-31 | 405 |
| `1867` | 1867-01-01–1867-12-31 | 431 |
| `1868` | 1868-01-01–1868-12-31 | 790 |
| **Total** | | **4,182** |

Count provenance: `data/raw/epsilon/ab0d973bae05b54d68d82d068211015996cfec06/darwin-correspondence.csv`, SHA-256 `cbe31878e4557db7f1e96f4c1fccdfa3144a88b2e8f2dcbf7441f8d430d73f9a`, checked against its manifest. Selection uses the exact sender/recipient name tuples above and ISO `sorting_date` between the two bounds. The year table partitions that screen; it is not a frozen run-02 inventory.

Follow the DCP's annual contextual chapters, beginning with [1860: Answering critics](https://www.darwinproject.ac.uk/letters/darwins-life-letters/darwin-letters-1860-answering-critics), while retaining the post-*Origin* tail of 1859. Use [1868: Studying sex](https://www.darwinproject.ac.uk/letters/darwins-life-letters/darwin-letters-1868-studying-sex) for the full final year, including the publication and subsequent exchanges about *Variation*.

Within each year, keep correspondent-based packets near the previous 18-target / 10,000-word limits, adjusting for long letters, apparatus and required context. Split heavy correspondents chronologically. The 790-row 1868 screen is the largest annual group; its packet queue can be staged by half-year while retaining one annual period and one cumulative release. Preserve cross-year antecedents and separate uncertain-date probes. Broad uncertainty records can recur as context, but should have one lead review assignment within this run and an explicit reuse/correction record elsewhere. Checkpoints organize reading and recovery; all accepted material still feeds one cumulative release.

## Proposed additions for run 02

Keep existing evidence in place. Add a small run-level directory that points to the established per-period layout:

```text
reports/research/runs/run-02-variation/
├── README.md               scope summary, current checkpoint, next actions
├── scope.json              run ID, new/cumulative dates, base manifest, periods
├── work_status.json        rollup derived from period/packet status and ledgers
└── source-index.jsonl      source IDs, witness layers, paths, hashes, reuse

reports/<new-period>/review/                    existing review conventions
data/annotations/periods/<new-period>/          accepted primary ledgers
data/raw/epsilon/<revision>/expansions/<new-period>/
data/raw/dcp/<new-period>/                      new sources only; reuse by reference
reports/raft-prep/run-02-variation/              this run's plans and rendering work

releases/variation-1868-v1/                      proposed cumulative data release
├── raft.json
├── conversations/transcript-NNNN.json
├── corpus/documents.jsonl
└── audit/                                     manifest, provenance, holds, change log

training-runs/<experiment-id>/                 separate mutable RAFT working copy
└── source-release.json                        release path/ID and input hashes
```

These names are a proposal, not newly supported command flags or an implemented schema. The run `scope.json` should pin the first release's manifest, metadata revision, dates and period order. The status rollup should link to packet reports and accepted ledgers and distinguish discovered, preserved, read, adjudicated, held and export-cleared counts. Keep a single writer for shared status and accepted annotations; each Luna writes only its assigned packet report.

Use the complete DCP ID, including suffixes, as the letter identity; use source layer plus revision/hash to distinguish witnesses. The new source index should point to existing preserved bytes and review evidence without copying them into every period. Where current readers require `all_letters.jsonl`, retain it as a generated compatibility view and load only the relevant records for a packet. A JSONL index is sufficient initially; add a rebuildable search database only if measured lookup costs justify it.

The current preservation resolver selects a saved source by ID and extension across manifests. If a new catalogue revision or changed HTML witness is introduced, adapt that lookup to choose the recorded version explicitly. Preserve the previous bytes; an ID match alone cannot decide which version a new review used.

Qualify packet references with run, period and batch, for example `run-02-variation / 1862 / batch-07`. Batch numbers restart within a period; they are not global identities. Preserve initial reports and named revisions, then link the accepted ledger to the chosen evidence. Give later corrections explicit supersession links. Do not rename old files to make the historical archive look uniform.

## Keep releases separate from experiments

Build the second release from the first release's accepted evidence plus the new adjudication and explicit corrections. Reconcile roles across both runs: if a newly found incoming letter establishes that an old grounding letter is a response, record its changed role in the new release and preserve the first release unchanged. Reuse prior primary readings only where source hashes, voice layers and scope still match; review new relationships and changed interpretations directly.

At final export, assign gapless transcript numbers across the whole new cumulative release. Keep DCP/source-section identities in provenance and record old-to-new mappings; transcript filenames are release-local positions and can change. Retain separate counts for letters, relationships, exported sections and holds. Keep related material together in any subsequent train/evaluation split.

Treat `releases/variation-1868-v1/` as the preserved source dataset once validated. Run chunking, embeddings, fine-tuning generation, training and serving in a separate working project under `training-runs/`, recording the release hashes and RAFT commit there. Use ordinary independent copies or verified copy-on-write clones for mutable inputs; shared hard links or writable links into the frozen release would defeat that separation. Existing `darwin_0` and `darwin_thinking` can remain where they are.

Keep raw witnesses, manifests, original reviews, accepted decisions, corrections and released provenance. New temporary extracts, lookup indexes and embeddings can be classified as rebuildable where their inputs and configuration are pinned. This classification is not a cleanup of the existing archive: historical reports may themselves be evidence or export inputs.

## Route the next session

1. Read the workflow, this plan, the first release manifest and holds, and the current RAFT compatibility note. Use the full-year endpoint, 31 December 1868, when starting the actual collection task.
2. Create the run-level scope/index and inspect reuse before any bulk fetching. Register the new periods in a versioned collection driver; audit downstream assumptions in `known_letters()`, packet/status writers, `raft_export_inventory.py`, rendering and the exporter. Current code is bounded to the first run, so extending one date constant is insufficient. Preserve any tool versions pinned by the old manifest.
3. Prepare the post-*Origin* 1859 inventory and its cross-boundary candidates first, then proceed annually. Retain out-of-window research context with explicit reasons. Resume interrupted fetches from manifests; reconcile failures and selected IDs before assigning packets.
4. Continue Luna first readings and independent primary adjudication. Prepare formatting requirements in parallel; limit the fetched-but-unreviewed queue to roughly one following period so reading and adjudication remain manageable. Adjust that queue after observing actual throughput.
5. At each period checkpoint, publish completed/held counts and unresolved cross-period links. Continue to the next period without treating the checkpoint as a separately frozen training group.
6. Reconcile the complete 1828–1868 evidence, render and validate a new cumulative release, and record every role/content change from the first release. The already-used release stays reproducible; the next release supersedes it for the next experiment.

This documentation update performed filesystem inspection and a catalogue-only workload count. It did not start run 02, fetch letter bodies, change adjudication, prepare new training data or modify the current experiments.

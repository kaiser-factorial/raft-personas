# Young Darwin correspondence preparation

**22 September continuation:** the completed data release ends on 24 November 1859. The proposed second collection run extends from 25 November 1859 through 31 December 1868, covering *Variation* publication and subsequent correspondence about the book. Read the [collection workflow](docs/collection-workflow.md) and [filesystem / run-02 plan](docs/collection-layout-and-run-02.md). This is a documented plan; the second fetch has not started. The older status narrative below records earlier collection milestones and does not report subsequent training activity.

The chronological review and one cumulative RAFT data export are complete through **24 November 1859**. The export contains **162 conversation transcripts** and **1,405 grounding documents**, with exact dates, source provenance and an explicit hold queue. No embeddings or training have run.

Read [HANDOFF.md](HANDOFF.md) for continuation, and the [cumulative export report](reports/raft-export/README.md) for current counts, validation and file locations. Research period groups are retained as provenance; they are not separate frozen RAFT exports.

## Earlier phase documentation

The material below preserves the original 1828–1843 work and its historical counts. Current cumulative status is in the report above.

For continuation in a new session, read [HANDOFF.md](HANDOFF.md): current verified state, the Luna/primary pairing workflow, failure modes, the proposed RAFT adaptation, and expansion through Origin's publication. Progress strings in `scope.json` predate the completed review; use the final status reports below for counts.

Current scope: letters **to or from Charles Robert Darwin**, with an **1828–1836 core corpus** and a separately audited **1837–1843 expansion**. Exclude correspondence between third parties. Use unpaired Darwin-written letters as dated grounding; promote a letter to a response target only when the inbound letter being answered is established.

The [completed 1837–1843 review](reports/1837-1843/remaining-review/README.md) covers **476 inspected source records and 474 surviving transcriptions**, using Luna first readings followed by primary adjudication. Its **24 reply links across 22 Darwin response records** comprise 19 single-date links and five requiring dated sections. Across both reviewed periods there are **24 single-date pairs**, or **29 links across 27 distinct Darwin responses** including sections. The earlier 135→139 date-held relation is additional. See the [aggregate status](reports/corpus-status.json) for definitions.

The raw XML audit remains **445 safe / 31 held**. Editorial evidence adds holds for 631 and 13803, yielding **443 period-eligible / 33 held**. Among eligible, individually attributed Darwin body records, **292 have no identified surviving prompt** and remain grounding candidates. All selected records have been reviewed; two lack usable transcriptions, three joint documents are excluded from individual voice, and 677 has disputed authenticity. Incoming prose remains context, never Darwin voice. No count represents export-ready or independent training examples.

The original graph remains specific to 1828–1836; the [expansion graph](reports/1837-1843/correspondence-map/graph.json) is separate. Earlier source evidence and phase ledgers/reviews are preserved unchanged.

The initial [XML date audit](reports/1828-1836/README.md) preserves 288 candidate XML records and their original metadata, with **285 inside the XML-encoded period** and **three held for possible later dates**.

- `scope.json`: the agreed selection and training-role policy.
- `data/raw/epsilon/`: pinned, unchanged source evidence with a hash manifest.
- `data/raw/dcp/`: unchanged public letter pages supporting receipt evidence, with a hash manifest.
- `reports/1828-1836/`: full audit, eligible metadata, and held records.
- `scripts/`: source preservation and offline audit commands.
- `tests/`: date-boundary and evidence-preservation regression checks.

The [receipt case study around letters 301–306](reports/1828-1836/receipt-evidence.md) identifies three incoming letters acknowledged in two Darwin responses. It demonstrates that letters arrived out of composition order and records conservative availability dates separately from the original metadata.

The [correspondence map](reports/correspondence-map/README.md) separates knowledge attestations, direct replies, references to Darwin's own letters, unread receipt, and limited event matches. Nine of the 126 incoming records have supported knowledge dates; 117 remain undated for memory retrieval. Five complete direct prompt–response pairs are established. The 66 unlocated reference nodes preserve missing or unidentified writing without invented text; they are not a count of distinct physical letters. All incoming writing is excluded from Darwin voice targets, including incoming letters that themselves answer Darwin. The [knowledge dating policy](reports/1828-1836/knowledge-dating.md) describes these roles and timing rules.

The [completed pre-Beagle review](reports/pre-beagle-1828-1831/README.md) covers **80 outgoing and 34 incoming letters**. A parent full-text survey was followed by three independent Luna reviews and parent adjudication. Three complete prompt pairs fall in this batch (two newly added); 77 outgoing records remain grounding. The audit preserves unread Sedgwick correspondence, an anonymous microscope gift whose archival author Darwin did not yet know, uncertain FitzRoy dates, crossed letters, bundles and repeated missing references. Initial hypotheses, reviewer corrections, exact quotations and unchanged-source checks are retained.

The [completed review of 13 post-return letters](reports/post-return-1836/README.md) records a full-reading dossier for each target, exact evidence, competing candidates, and a generated correspondence diagram. It establishes six additional relationships but no new complete text pair; all 13 remain dated grounding. Fox's input to 319 joins Whitley's input to 314 as an unlocated prompt. References to Darwin's own letters, two distinct Herbert notes, and the uncertain 327→319 identification are kept separate from incoming availability.

The [incoming full-reading follow-up](reports/post-return-1836/incoming-full-read/README.md) uses three `gpt-5.6-luna` reviewers to read all 33 earlier incoming candidates and assess 85 comparisons. Checked outcomes: 57 without a specific link, 25 with historical/topic continuity only, and three FitzRoy records judged unlikely antecedents after intervening direct contact. No additional reply or knowledge link was accepted. The original lists are broad identity/date screens, not equally plausible prompts; original reviewer proposals and parent corrections remain preserved.

The expanded body search found 896 occurrences of “letter” or “letters” in 231 records, plus 885 related cues, across all 286 preserved bodies. Candidate matches remain separate from reviewed map links. Rebuild with `python3 scripts/search_letter_references.py`, `python3 scripts/build_correspondence_map.py`, and `python3 scripts/build_post_return_review.py`; the earlier `annotate_response_dates.py` command now calls the same map builder.

The [body-date search for letters 37–337](reports/body-date-search-37-337/README.md) covers 286 Darwin-involved records, with 16 manually reviewed chronological findings and searchable candidate tables. It distinguishes dated writing sections from a record's overall date span. The [text attribution annotations](data/annotations/text_attribution.json) flag 303's jointly signed conclusion and 330's minute-book report as unsuitable for Darwin's individual-voice training.

The selected 1837–1843 inventory is fully reviewed. Remaining Beagle-voyage matching, wider catalogue overlap checks, and training export are separate future work. No model training has been run.

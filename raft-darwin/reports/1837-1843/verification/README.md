# Independent Luna verification of the expansion pilot

Three `gpt-5.6-luna` reviewers checked the family pilot, Kemp pilot, and complete metadata inventory. The primary agent checked their conclusions, validated all 28 quoted passages, and verified that the initial pilot, metadata audit, and earlier correspondence graph remained unchanged.

All five pilot pairs stand: **345 → 346, 444 → 445, 699 → 701F, 711 → 711F, and 720 → 720F**. Rejection of **441 → 445** as the identified direct prompt also stands. Receipt-day uncertainty, editorial date derivations, missing enclosures, the copyist transmission of 346, and the missing postscript in 445 remain attached to the evidence. These are confirmed relationships, not completed training exports.

The independent XML parser reproduced **476 candidates; 445 safe (318 outgoing, 127 incoming); 31 held; 13 third-party exclusions; and joint outgoing record 512**. It verified the pinned CSV and all 476 XML hashes and the correspondent counts.

One additional chronology issue emerged during preparation of the continuation batch. Letter **448** has a single XML `when="1838-11-30"`, while the date text spans 30 November–1 December and paragraph 7 starts a Saturday-morning section acknowledging a newly arrived letter. The reviewer independently confirmed this after the primary agent flagged it and scanned other single-day entries for similar display conflicts. The initial no-issues review is retained as `period.initial.review.json`.

The XML-only count of 97 records needing exact-order review remains a reproducible description of that original audit. **448 adds a further body/text review requirement, bringing the combined flag count to 98.** Its Friday paragraphs 1–6 and Saturday paragraphs 7–8 must be treated separately; Saturday's incoming information cannot be used to prompt Friday's writing. [Date review overrides](../date_review_overrides.json) preserve the original constraint and add the reviewed sections separately.

## Workflow for subsequent batches

Use scripts for deterministic scope, identity, hash and XML-date checks. Assign bounded correspondent groups with all surviving incoming and outgoing bodies to Luna reviewers for the first full reading. Require a per-letter account, exact quotations, alternative candidates, missing-text observations, and explicit timing limitations.

The primary agent then checks every proposed accepted link against the original body and editorial apparatus, considers competing inputs, and separately checks dated sections, authorship and negative findings. A second targeted review can address a difficult date or proposed link. Model agreement alone is insufficient: supported source evidence controls acceptance. Preserve the initial model proposal even when it is corrected.

The continuation begins with all **17 Kemp records** and **32 Emma records** in the safe-period inventory. Their packets are prepared without additional parent matching hypotheses; reviewer proposals will not directly modify the accepted graph.

- [Family verification](family.review.json)
- [Kemp verification](kemp.review.json)
- [Revised metadata verification](period.review.json), [initial version](period.initial.review.json)
- [Parent adjudication and quote checks](parent_review.json)
- [Baseline hashes](baseline_hashes.json)

No source dates were overwritten, missing text synthesized, or training run.

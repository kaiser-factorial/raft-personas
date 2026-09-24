# Remaining 1837–1843 integration review

The generated builder now composes the earlier source set, all 19 remaining batch ledgers, and `supplementary.json`. The remaining selection contributes 363 unique targets; the earlier set contributes 113 records, for 476 records in the composed corpus. Every batch ledger is `parent_adjudicated`. `work_status.json` still says `in_progress`; mark it complete only after the final composed outputs and checks pass.

## Merge and provenance safeguards

- Preserve `data/annotations/expansion_1837_1843.json` and the Henslow–Lyell baseline hashes as immutable inputs. The composed artifact must retain every batch and supplementary `inputs` hash, source-page hash, and raw XML hash. Preserve `*.initial.json` and reviewer reports as provenance; do not auto-promote reviewer-only edges.
- The builder now checks batch sequence, target count, source overlap, input hashes, full-read coverage, and quote inclusion. Keep the exact-hash reconciliation for the five shared earlier base/extension records and the no-overlap rule for remaining targets.
- `load_decisions()` append-merges several non-edge lists without stable-key conflict checks. The integration invariant should reject conflicting duplicate date sections, date evidence, receipt/within-day events, corrections, source observations, or scope records rather than silently retaining both. Relationship keys must remain typed and directional; topic/date similarity cannot deduplicate or promote an edge.

## Attribution and relationship semantics

Carry `body_unavailable_ids`, `non_individual_voice_ids`, `voice_held_ids`, `additional_period_hold_ids`, individual limits, source-kind corrections, text-scope overrides, and institutional participant overrides into the composed map. Incoming prose never supplies Darwin voice, and a correspondent’s reverse reply does not prove Darwin received or read it. Preserve the exclusions for 421F, 512 (joint invitation), and 612; preserve 545’s repository-caption scope. For 609F, keep the catalogue paraphrase separate from its short surviving actual tail. Preserve the explicit institutional representation in 381A→402A and the reverse links 381A→378A and 415B→415A.

Keep direct replies (Darwin response → incoming prompt), cross-correspondent knowledge, correspondent replies, receipt events, within-day events, dated sections, and candidate/rejected links as distinct types. Candidates and rejected links must remain outside accepted edges. Publications, specimens, reports, invitations, minutes, and oral discussions require their recorded source-kind and voice rule before grounding a personal response.

## Current counts and date limits

For the 1837–1843 composed map, the generated summary should preserve:

| Metric | Expected value |
|---|---:|
| audited/reviewed records | 476 |
| full-body records | 474 |
| body unavailable | 2 (`DCP-LETT-699F`, `DCP-LETT-13864`) |
| full safe outgoing / held outgoing | 317 / 26 |
| full safe incoming / held incoming | 127 / 4 |
| accepted direct links / distinct Darwin responses | 24 / 22 |
| single-date / section-dependent direct links | 19 / 5 |
| cross-correspondent knowledge links | 16 |
| correspondent-reply links | 28 |
| dated sections | 16 |
| receipt events / within-day events | 1 / 3 |
| reference observations | 89 |
| eligible individual Darwin bodies | 314 |

The 314 voice-eligible count is 317 safe outgoing full reads minus the joint 512, authorship-held 677, and period-held 631. The additional editorial hold 13803 is also an incoming record; preserve it alongside 631 and preserve the raw XML constraints. Current raw XML counts are 445 safe and 31 held, while effective period counts are 443 eligible and 33 held. The combined `reports/corpus-status.json` necessarily reports 29 direct links and 27 distinct responses because it adds the earlier period’s five established pairs; those combined counts must not be confused with the 1837–1843 summary’s 24/22.

A resolved Darwin writing section can establish `known_by_date`, but an incoming date is not a delivery or receipt date. Keep receipt separate from later content-known-by evidence, preserve multiday section boundaries, and keep 13803’s upper-bound/conjectural dating held rather than assigning a scalar date. No same-day order follows from catalogue order alone.

## Remaining concrete checks

1. Reconcile the generated summary’s `safe_outgoing_not_yet_full_read: 1` with its zero unreviewed source records and the unavailable safe outgoing 13864. If the value counts unavailable transcription, rename or document it; if it means unread source records, it must be zero. Do not let this presentation discrepancy imply an unreviewed record.
2. Recursively validate every evidence quote, including nested relationship/date/section/correction evidence, against the correct paragraph, header, or editorial footnote. Preserve offsets and source hashes where canonical evidence requires them; reject editorial paraphrases presented as body text.
3. Assert participant direction and role for every accepted edge, including institutional overrides, and assert that incoming/reverse-reply records cannot create Darwin voice or receipt. Assert stable-key uniqueness and conflict failure during append-only composition.
4. Retain the regression invariants for same-day arrival boundaries, split response scopes, ambiguous-date scalar nulls, held-period preservation, candidate exclusion, missing prompts, joint-document exclusion, section coverage, and “unreviewed” versus “unpaired” counts. `unpaired` remains a surviving-prompt finding, not proof that no reply was written.
5. Regenerate the remaining-review README, 1837–1843 map README/summary, and corpus status from the composed artifact. Stale historical counts may remain only in explicitly historical sections; current status must expose 476 reviewed, 474 full-body, and the corrected 24/22 and 314 metrics. Keep training export disabled.

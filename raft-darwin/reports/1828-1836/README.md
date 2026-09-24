# Darwin correspondence date audit: 1828–1836

The requested period is **1 January 1828 through 31 December 1836**, inclusive. Only correspondence to or from **Charles Robert Darwin** is eligible.

## Result

| XML period classification | From Darwin | To Darwin | Total |
| --- | ---: | ---: | ---: |
| Within the period under the XML date constraints | 159 | 126 | **285** |
| Ambiguous, with possible dates after 1836 | 3 | 0 | **3** |
| Wholly outside the period under every XML possibility | 0 | 0 | **0** |
| Total audited | 162 | 126 | **288** |

The CSV contains 304 records whose `sorting_date` falls within the window. Sixteen are correspondence between third parties and were excluded before XML retrieval. No third-party XML was downloaded or included in the audit outputs. The untouched full CSV is retained as source evidence.

The XML identity key `nameregs_1.xml` confirms Charles Robert Darwin in every selected record. It agrees with the CSV's `Darwin` / `C. R.` fields. No selected Darwin identity is marked as an alternative or qualified by a `cert` attribute.

“Within the period” means the complete set of **XML-encoded date possibilities** lies inside the period. It does not certify an exact writing day, a receipt date, or a reply relationship. The classification adopts the catalogue's date evidence, including editorially supplied dates; it does not independently establish historical dating.

## Three records held aside

| Letter | Recipient | Original CSV date | XML bounds | Decision |
| --- | --- | --- | --- | --- |
| [3150F](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-3150F.xml) | J. S. Henslow | `[Sept 1831 – May 1861]` | 1831-09-01 to 1861-05-31 | Possible composition well after the cutoff. |
| [326](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-326.xml) | Caius College | `[19 Dec 1836 – 6 Mar 1837]` | 1836-12-19 to 1837-03-06 | Range crosses the end of 1836. |
| [13858](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-13858.xml) | Unidentified | `[after 1836?]` | 1836-12-31 to 1882-12-31 | The wording and broad range do not support inclusion. |

For 13858, the CSV sorts at **1836-12-30**, while XML `notBefore` is **1836-12-31**. Both values are retained. The original wording says “after 1836?”; the XML numerical lower bound is not treated as proof that the letter was written during 1836. This is the only CSV sorting-date / XML lower-bound mismatch in the selected set.

The upper bound 1882-12-31 is preserved exactly as supplied by the source, without inventing a narrower bound.

## Uncertainty retained inside the eligible period

The 288 records contain:

- 231 records with one XML `when` day.
- 53 records with `notBefore` / `notAfter` bounds, including the three held records.
- Two records with mutually exclusive dates: 139 and 140, each either 4 or 11 October 1831.
- Two records with multiple recorded dates without mutual exclusion: 155 and 196. These are retained as multiple dates, not silently treated as alternatives or collapsed to the first day.

**59 of the 285 period-eligible records require additional care when ordering individual exchanges.** This includes 50 bounded ranges, two sets of alternative dates, two multiple-date records, and five single-day encodings whose source wording is approximate, questioned, or relative.

Those five single-day encodings are 88 (`[27? Nov 1830]`), 106 (`[c. 26 Aug 1831]`), 145 (`[31?] Oct [1831]`), 221 (`[c. 21 Oct 1833]`), and 256 (`[before 13 Oct 1834]`, encoded as 1834-10-12). The encoded day remains visible; its precision is not promoted into an unqualified historical claim.

Square brackets alone mean that part of a date was supplied editorially. They are recorded separately from question marks, approximate wording, and before/after language. See the [Darwin Correspondence Project's editorial policy](https://www.darwinproject.ac.uk/letters/editorial-policy-and-practice).

None of the 288 XML records contains a transcription body or a structured receipt date. Endorsements, postmarks, physical descriptions, and other available XML notes are preserved as evidence for subsequent work. No receipt date is inferred from a sending date.

## Dataset routing

- The 159 eligible outgoing letters are candidates for **dated grounding** unless an inbound letter being answered is established later.
- Period eligibility does not establish individual authorship. Subsequent [text-attribution annotations](../../data/annotations/text_attribution.json) flag 303 (jointly signed conclusion) and 330 (minute-book report) for exclusion from Darwin's individual-voice material.
- The 126 eligible incoming letters are candidates for correspondence context, with receipt and reply evidence still to be established.
- The three ambiguous outgoing letters remain outside the eligible set.
- This metadata audit performs no reply matching or transcription retrieval. The subsequent [receipt case study around letters 301–306](receipt-evidence.md) records three incoming-letter matches separately. No training examples or synthetic prompts have been generated.

Every metadata-audit record has `reply_link_status: not_audited`, `training_target_eligible: false`, and `known_by_date: null`. These describe this audit stage; subsequent manual receipt findings are in the linked supplement. A lack of an established reply link at this stage is not evidence that no inbound letter survives.

## Files

- [audit.csv](audit.csv): 288 rows for inspection, preserving all 13 original CSV columns and appending audit results and evidence links. The original headers ` extent` and ` filename` retain their leading spaces.
- [audit.jsonl](audit.jsonl): full record-level audit, including untouched CSV field values, original date attributes and wording, serialized date elements, participant evidence, notes, source locations, and hashes.
- [safe_within_period.jsonl](safe_within_period.jsonl): 285 eligible metadata records.
- [ambiguous_or_later.jsonl](ambiguous_or_later.jsonl): three held records. None is proven wholly later by every XML date possibility; all three require exclusion from this period pending further evidence.
- [summary.json](summary.json): counts, source identity, checks, and scope limits.
- Original CSV, README, licence, and all 288 XML files: `data/raw/epsilon/ab0d973bae05b54d68d82d068211015996cfec06/`, relative to the project root. Its `manifest.json` records source URLs, retrieval timestamps, byte counts, and SHA-256 hashes.

## Source version and selection boundary

Source: [Cambridge Epsilon data](https://github.com/cambridge-collection/epsilon-data/tree/ab0d973bae05b54d68d82d068211015996cfec06), revision **ab0d973bae05b54d68d82d068211015996cfec06** (commit dated 8 September 2025). The source metadata is a pinned repository snapshot, not a claim about the latest Darwin Project website contents.

The full CSV has **15,238 unique records**. Its SHA-256 is `cbe31878e4557db7f1e96f4c1fccdfa3144a88b2e8f2dcbf7441f8d430d73f9a`.

Candidate selection uses the inclusive CSV sorting window and the Darwin identity fields. All other Darwin-only CSV rows were also screened for an explicit four-digit year from 1828 through 1836 in the displayed date; this yielded no additional candidates. This audit does **not** re-date every XML record in the full collection, examine all much-later open-ended date labels, or claim that the catalogue includes every surviving letter.

Raw source files are retained unchanged. Each JSONL record cites the original CSV record and physical line locations, the exact XML path and SHA-256, a pinned XML URL, and the public letter page. Dates are read from the correspondence `sent` action, never from the edition's publication date. Date alternatives remain separate in the evidence even where a conservative outer bound is also provided.

The preserved source README and licence identify the Epsilon release as CC BY-NC 4.0. This audit does not infer reuse terms for transcriptions hosted elsewhere.

## Reproduce and verify

From the project root, using Python 3.11 or newer with the standard library:

```sh
python3 scripts/fetch_metadata.py
python3 scripts/audit_metadata.py
python3 -m unittest discover -s tests -v
```

The fetcher uses the pinned revision, preserves existing verified files, and retrieves only missing evidence. The offline audit checks all 291 source checksums, unique CSV IDs, CSV/XML identity agreement, complete candidate-to-XML coverage, and reconciliation of the two output partitions. Unsupported or contradictory date encodings fail visibly instead of being silently assigned a sorting date.

Validation completed: all 14 date-constraint regression checks passed. An independent output check verified that the original metadata is preserved in both the CSV and JSONL results, that eligible and held IDs are disjoint and exhaustive for the selected candidates, and that every source checksum matches the manifest.

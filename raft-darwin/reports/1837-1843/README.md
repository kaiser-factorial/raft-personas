# 1837–1843 expansion: XML audit and reviewed correspondence

The [completed Luna-first review](remaining-review/README.md) covers **all 476 selected source records / 474 surviving transcriptions**. There are **24 incoming → Darwin reply links across 22 distinct responses**: nineteen single-date links and five requiring dated sections. Another **292 period-eligible, individually attributed Darwin body records lack an identified surviving prompt**. There are no unreviewed records in this inventory. These are documented relationship and source-record counts, not exported training examples.

The earlier [Emma/Kemp](correspondent-review/README.md) and [Henslow/Lyell](henslow-lyell/README.md) phase reports remain historical snapshots. Across both reviewed periods there are **24 single-date pairs**, or **29 links across 27 Darwin responses** including sections. The earlier 135→139 date-held relation remains additional.

## Period audit

| XML audit result | Outgoing involving Darwin | Incoming to Darwin | Total |
|---|---:|---:|---:|
| All XML date possibilities within 1837–1843 | 318 | 127 | 445 |
| Held because possible dates cross a boundary | 27 | 4 | 31 |
| Candidates examined | 345 | 131 | 476 |

Thirteen third-party CSV records sorted within the period were excluded. All 476 XML records were preserved separately from the earlier archive and checked against the pinned catalogue. Original CSV rows, physical line references, XML date elements, name-authority evidence, source URLs, retrieval timestamps, and hashes are retained. None of these XML records contains a transcription or a structured receipt date.

Period eligibility is distinct from exact chronology: the XML audit flags **97 of the 445 safe records** before assigning an exact order. Body review adds flags for **356, 448, 496F, 501, 565F and 607**, producing **103 whole-letter date-review flags** in the current map. Supported section dates are separate. The sorting-year breakdown below is a finding aid only; it does not resolve ranges or alternatives.

| CSV sorting year | Outgoing | Incoming |
|---|---:|---:|
| 1837 | 49 | 18 |
| 1838 | 48 | 31 |
| 1839 | 55 | 37 |
| 1840 | 41 | 8 |
| 1841 | 24 | 7 |
| 1842 | 41 | 7 |
| 1843 | 60 | 19 |

The XML-safe outgoing inventory contains one unavailable transcription, the joint invitation 512, the date-held 631, and the authenticity-held 677. This leaves **314 period-eligible individual Darwin body records**, subject to their recorded excerpt and date scopes: 22 responses with identified prompts and 292 grounding candidates. Joint documents 421F and 612 are also excluded from individual voice but already lie in the XML-held set.

The raw XML classification stays unchanged. The editorial overlay adds period holds for **631** (possible composition through 1848) and **13803** (a questioned upper bound without a secure lower bound), leaving **443 period-eligible / 33 held**. See the [full adjudication report](remaining-review/README.md) for source evidence and reviewer disagreements.

The 31 held records include 326, whose date crosses 1836/1837; 723, which crosses 1843/1844; and records such as 8132, whose hundreds of alternative dates extend into 1882. Lower-bound-only and upper-bound-only descriptions are not narrowed by their catalogue sorting date. A later evidence-based refinement can be added without overwriting the XML constraints.

Selection uses the pinned CSV's Darwin sender/recipient identity and either an 1837–1843 sorting date or an explicitly written year within that period. It is not an XML-wide re-dating of all 15,238 catalogue records. Records sorted elsewhere with dates only indirectly overlapping this period may remain outside this candidate set.

## Five original pilot pairs, all retained

Arrows mean surviving incoming text → Darwin's surviving response. Dates in the last column establish knowledge **by the response**, not the actual delivery day.

| Incoming → response | Correspondent | Distinctive matching evidence | Known by |
|---|---|---|---|
| [345](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-345.xml) → [346](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-346.xml) | Caroline Darwin | Her questions about Lyell's speech and Herschel's biblical chronology are explicitly answered. | 27 Feb 1837 |
| [444](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-444.xml) → [445](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-445.xml) | Emma Wedgwood | Caroline Tollet's reading, Emma's already having read Nicholas Nickleby, and the choice of house location. | 27 Nov 1838 |
| [699](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-699.xml) → [701F](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-701F.xml) | William Kemp | Receipt of the paper-letter, the sandpit description, and Darwin's challenge to the proposed wetter ancient climate. | 9 Oct 1843 |
| [711](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-711.xml) → [711F](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-711F.xml) | William Kemp | Kemp's gracious response to disappointing results, which Darwin acknowledges before reconsidering publication. | 9 Nov 1843 |
| [720](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-720.xml) → [720F](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-720F.xml) | William Kemp | Further discovery particulars and testimonial material, acknowledged when Darwin submits the paper. | 7 Dec 1843 |

Both bodies and editorial notes were read for each accepted pair. Exact quotations, paragraph locators, source hashes, XML constraints, and limitations are in [pilot/review.json](pilot/review.json). The historical [pilot graph](pilot/graph.json) contains five `knowledge_before` and five `replies_to` edges. The [current expansion graph](correspondence-map/graph.json) includes these links once alongside the continued review. The old 1828–1836 graph remains period-specific; [the aggregate status](../corpus-status.json) records current counts across the two periods.

The originally selected **441 → 445** was rejected as the identified prompt. Letter 445's distinctive answers match 444. Editorial notes to 441 and 444 identify a now-missing Darwin reply to 441. The original candidate, the added source, and the reason for the correction remain preserved. No missing Darwin text is invented, and this pilot assigns no knowledge date to 441.

Relevant qualifications:

- 444 retains its two XML date alternatives and the Sunday/Monday writing sections in the body. Both precede the resolved 27 November response; its composition dates are not replaced by that response date.
- 346 survives in a copyist transmission with a corrected date and a textual gap. Preserve those distinctions in any later export.
- 701F's year and 711F's date are editorially established through the surrounding correspondence; that provenance remains attached.
- The cut-off postscript in 445 and Kemp's testimonial enclosures are not reconstructed. The surviving bodies form the paired text.
- Several letters depend on earlier exchanges. These five are confirmed relationship pairs and response candidates, not completed RAFT examples. A final export still needs context-chain review and preservation of transcription details.

## Completed review and remaining preparation

The remaining 363 records were divided into 19 bounded Luna packets and adjudicated individually by the primary agent. All earlier 113 records and their decisions were retained. The [current graph](correspondence-map/graph.json) has 16 cross-correspondent knowledge links, 28 reverse replies, and known-by evidence for 32 incoming records. The other 99 incoming records have no accepted activation date.

The selected inventory’s source review is complete. Before RAFT export, preserve excerpt/voice boundaries, assemble context only from established earlier knowledge, handle dated sections and within-day arrivals, choose the persona cutoff policy, and split evaluation data by connected exchanges. Missing letters remain missing. The remaining Beagle-voyage matching work is separate.

## Keep the developing persona dated

This extension follows Darwin through a substantive change in outlook. The [Darwin Correspondence Project's period introduction](https://www.darwinproject.ac.uk/letters/darwins-life-letters/darwin-letters-1837-1843-london-years-natural-selection) places his work on transmutation in 1837, the encounter with Malthus in September 1838, and the first theory sketch in summer 1842. Those are useful checkpoints for evaluating whether later ideas appear too early; they are not a licence to insert the editorial introduction into Darwin's own voice.

Retain the user's rule: incoming text becomes available through dated evidence from Darwin, and only Darwin-attributed prose supplies his response voice. Keep original composition constraints alongside `known_by_date`; require ordering evidence for other uses on the same day. For a strict younger snapshot, exclude later training examples as well as later retrieved memory—date-filtered retrieval alone cannot guarantee that a model trained on later correspondence will not use that knowledge.

## Files and reproduction

- [Full audit](audit.jsonl), [CSV view](audit.csv), [summary](summary.json).
- [Safe records](safe_within_period.jsonl), [held records](ambiguous_or_later.jsonl), [excluded third-party metadata](excluded_third_party.json).
- [Correspondent inventory with letter IDs](correspondents.json).
- [Full pilot extracts](pilot/letters.jsonl), [reviewed evidence](pilot/review.json), [pilot graph](pilot/graph.json).
- [Luna pilot verification](verification/README.md), [Emma/Kemp review](correspondent-review/README.md), [Henslow/Lyell review](henslow-lyell/README.md), [completed remaining review](remaining-review/README.md), [current expansion graph](correspondence-map/graph.json).
- XML manifest: `data/raw/epsilon/ab0d973bae05b54d68d82d068211015996cfec06/expansions/1837-1843/manifest.json`.
- HTML manifest: `data/raw/dcp/expansion-1837-1843-pilot/manifest.json`.

Use the project's Python runtime, which includes lxml:

```sh
python3 scripts/audit_expansion.py --fetch
python3 scripts/expansion_pilot.py
python3 scripts/review_expansion_pilot.py
python3 scripts/curate_expansion_correspondents.py
python3 scripts/curate_henslow_lyell.py
python3 scripts/build_expansion_review.py
python3 scripts/report_remaining_review.py
python3 -m unittest discover -s tests
```

Omit `--fetch` for an offline metadata audit. The pilot fetcher validates and reuses preserved sources. The review script reproduces explicit human-readable adjudications and validates every quoted body passage; it is not an automatic matcher. Original 1828–1836 source hashes and all 288 earlier audit records were checked unchanged. No training export or model training has run.

# 1844–1846: investigation in progress

This is a research checkpoint in the cumulative collection through 24 November
1859, not a separate RAFT training export. The previous selected 1837–1843
inventory remains complete and its evidence is preserved.

All 15,238 pinned CSV rows were scanned with a broader discovery rule: sorting
window, displayed years and abbreviated ranges, open bounds, absent years, and
already-preserved XML overlap. This identified **677 Darwin-involved metadata
candidates**, all preserved and audited. It is not an all-catalogue XML audit.

- **318** records have every XML date possibility inside 1844–1846.
- **344** records form the nominal period correspondence review pool, including
  records with unresolved dates and abbreviated-year additions.
- **280** additional records require boundary dating investigation. Broad XML
  lower bounds of 1809 can admit catalogue labels from much later years; these
  records are held research evidence, not dated persona material.
- **306** of the combined **624** source-review candidates are raw date-held.
- **53** discovery candidates were excluded from source review after XML showed
  they could not fall in the period. Their metadata decisions remain preserved.

`discovery.json` preserves the selection reasons and CSV provenance;
`discovery_audit.jsonl` covers all 677 XML inspections; `audit.jsonl` covers the
624 source-review candidates. `metadata_only_exclusions.jsonl` retains the 53
exclusions. The separate `review_lane` on every packet distinguishes ordinary
correspondence from boundary-date probes.

Full HTML preservation and extraction are complete for all 624 source-review
records. All 53 packets have Luna first-pass reports. These reports are proposals;
several require substantive corrections during independent primary reading.
Current accepted counts and remaining packets are derived from the ledgers in
`review/work_status.json`, not from report completion claims.

The body projection omitted 139 sibling scholarly sections (122 marginalia,
4 CD-note sections and 13 enclosures) present in the preserved HTML. These were recovered separately without
changing the frozen body projection. Their dates and authorship do not inherit
the enclosing letter's date and author. The initial supplemental JSONL mostly
stored headings and omitted enclosures, so it did not establish the claimed full-text completeness.
Use `review/scholarly-sections.v2.jsonl` for complete normalized section text.
Earlier supplementary first passes remain unverified historical assessments;
primary review reads every full section. Earlier adjudications
affected by the omission have an explicit additive source-reading correction.

The 97 inline figure nodes are now preserved with hashes under
`data/raw/dcp/1844-1846/figures/`. Accepted uses require explicit visual reading;
paragraph extraction and image preservation alone are insufficient. The reader
also exposes editorial bibliographies, with an additive reading record for older
accepted packets. These citations are not proof that Darwin had read a work.

No conversation export or training has run. RAFT implementation preparation is
recorded in `docs/raft-formatting-readiness.md` at the project root.

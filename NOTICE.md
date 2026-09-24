# Notice and attribution

## The letter data

`raft-darwin/` contains, and is derived from, correspondence data published as
**Project Data from Epsilon.ac.uk** by Cambridge Digital Library and its
contributing projects, licensed under
[Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/)
(full text: [`LICENSES/CC-BY-NC-4.0.txt`](LICENSES/CC-BY-NC-4.0.txt)).

- Source: <https://github.com/cambridge-collection/epsilon-data>, revision
  `ab0d973bae05b54d68d82d068211015996cfec06`; Epsilon: <https://epsilon.ac.uk>
- Contributing projects whose material appears here: the **Darwin
  Correspondence Project**, the **Darwin Family Letters**, the **Henslow
  Correspondence Project** and the **William Kemp** project, among the
  correspondents Darwin exchanged letters with.

**Changes made:** records were selected by date and correspondent, dates
audited, letters transcribed or extracted to plain text, paired reply-to-letter,
split into paragraph-aligned pairs, annotated, and reformatted into training
data.

**What this means for reuse.** The derived material in this repository (letter
text, pairs, training sets, adjudication records) is redistributed under the
same terms: attribution required, **non-commercial use only**. Those terms
travel with it. Whether a model *trained* on this data counts as adapted
material is not settled here; none is included, and that question is left open
rather than answered.

## Everything else

No licence has been chosen for the original code and documentation in this
repository. Until one is added, all rights are reserved by the author. That is a
default, not a decision.

## What is deliberately not here

Bulk source corpora, embedding stores and model checkpoints are excluded; see
[`raft-darwin/EXCLUDED_MANIFEST.json`](raft-darwin/EXCLUDED_MANIFEST.json) for
what, why, and hashes to check a rebuild against. Other persona projects kept
alongside this one locally (built from living authors' writing) are not
published.

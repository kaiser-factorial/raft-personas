# raft-personas

Persona projects built with [RAFT](https://github.com/lumpenspace/raft). Currently one:

| folder | what |
|---|---|
| [`raft-darwin/`](raft-darwin/) | A young-Darwin persona: correspondence collected from the Darwin Correspondence Project, paired into reply-to-letter examples, split into paragraph-aligned pairs, and used to train three recall-mode variants |

**Start here:** [`raft-darwin/reports/paragraph-split/README.md`](raft-darwin/reports/paragraph-split/README.md)
— orientation, where things are, and the hard-won gotchas. The eval plan and open
items are in `OUTSTANDING.md` beside it.

## What is and is not in this repository

- **In:** code, documentation, adjudication verdicts and provenance, the pair
  records and training sets, per-period review ledgers.
- **Out, on purpose:** the bulk source corpus (`data/raw`), embedding stores,
  model checkpoints, and the largest regenerable intermediates. What was left
  out, why, and hashes to verify a rebuild are in
  [`raft-darwin/EXCLUDED_MANIFEST.json`](raft-darwin/EXCLUDED_MANIFEST.json).
- **Not yet in:** the second collection run (post-Origin through 1868) — it is
  still being written. It will be added when it finishes.
- **Model weights** go to Git LFS (see `.gitattributes`). None are included; the
  adapters live on the training machine.

## Licence

The letter data is **CC BY-NC 4.0** and so is anything derived from it here:
attribution required, non-commercial only. See [`NOTICE.md`](NOTICE.md).

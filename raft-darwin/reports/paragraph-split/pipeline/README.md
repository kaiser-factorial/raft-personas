# paragraph-split pipeline

The four stages that turn `darwin_thinking` into `darwin_split`. Run in order
from `raft-darwin/`; each writes into `reports/paragraph-split/`.

```bash
python pipeline/split_all.py       # letters   -> candidates.jsonl
python pipeline/make_batches.py    # candidates -> batches/ + control-key.json
#                                    (then adjudicate each batch -> verdicts/)
python pipeline/score_verdicts.py  # verdicts   -> final-verdicts.json
python pipeline/emit_split.py      # verdicts   -> ../../darwin_split/
cd ../../darwin_split && raft chunk && raft embed
```

Adjudication is the one manual stage: each `batches/batch-N.json` goes to an
independent reader that writes `verdicts/batch-N.json` mapping item_id to
`{verdict, reason}`. A list of records works too; the scorer accepts either.

## Notes worth keeping

**Controls.** `make_batches.py` plants two kinds. **CROSS** (answer lifted from a
different letter) is ground truth and is what `score_verdicts.py` gates on.
**SAME** (a different paragraph from the same letter) is *diagnostic only* — it
assumes the splitter's non-links are correct, which is the very thing under test.
All five SAME controls an adjudicator "missed" turned out to be real links the
splitter had failed to find. Do not reinstate it as a gate.

**Merging.** Verdicts merge on the pair `(source, incoming_paras, reply_paras)`,
not the item id, so the same pair re-judged in a later batch under a fresh id is
recognised as the same pair. Any DROP vetoes; disagreement resolves to DROP.

**Rebuilds are destructive.** `emit_split.py` deletes and rebuilds
`darwin_split/`, including `corpus/chroma`, so `raft chunk` and `raft embed` must
be re-run after it. It refuses to run while a `raft embed` is in flight.

**Pre-registration.** `prereg-batch7.json` records which planted controls were
judged catchable *before* the verdicts existed. If you add batches, do the same:
classifying a control as "soft" after seeing whether it was caught is not a test.

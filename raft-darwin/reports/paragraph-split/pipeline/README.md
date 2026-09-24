# paragraph-split pipeline

The four stages that turn a whole-letter RAFT project into a paragraph-split one.
Run in order from `raft-darwin/`. Every stage takes the same three arguments and
defaults to the original `darwin_thinking` -> `darwin_split` run:

| arg | default (original) | default (any other `--src`) |
|---|---|---|
| `--src` | `darwin_thinking` | the project whose letters are split |
| `--dst` | `darwin_split` | `<src>_split` |
| `--work` | `reports/paragraph-split` | `reports/paragraph-split-<src>` |

Bare names resolve under `raft-darwin/`; absolute paths are used as given.
Giving each corpus its own `--work` default is deliberate: `split_all.py` resumes
from whatever is in `<work>/candidates.jsonl`, so sharing a work dir would splice
two corpora together.

```bash
python pipeline/split_all.py      [--src S] [--model gpt-4o-mini]        # letters    -> candidates.jsonl  (needs OPENAI_API_KEY)
python pipeline/make_batches.py   [--src S] [--per-batch 40 | --batches N] # candidates -> batches/ + control-key.json
#                                   (then adjudicate each batch -> verdicts/; see ADJUDICATOR_PROMPT.md)
python pipeline/score_verdicts.py [--src S]                               # verdicts   -> final-verdicts.json
python pipeline/emit_split.py     [--src S] [--reserve N]                 # verdicts   -> <dst>/
cd <dst> && raft chunk && raft embed
```

`make_batches.py` also takes `--seed` (41), `--overlap` (0.20) and `--controls`
(3 CROSS + 3 SAME per batch). Without `--src` the commands above reproduce the
committed `darwin_split` exactly (checked file-for-file).

## Applying it to another corpus, e.g. `darwin_1`

```bash
python pipeline/split_all.py    --src darwin_1
python pipeline/make_batches.py --src darwin_1 --per-batch 40
# adjudicate reports/paragraph-split-darwin_1/batches/*  (ADJUDICATOR_PROMPT.md)
python pipeline/score_verdicts.py --src darwin_1
python pipeline/emit_split.py     --src darwin_1 --reserve <N>
```

Things that do **not** carry over automatically:

- **`--reserve`.** 15 was chosen for 162 letters (it made letter mode 49 examples
  with 24 multi-paragraph replies). It is a count, not a ratio, and `darwin_1`
  has 765 letters against 162; decide it deliberately.
- **Mode balance.** On `darwin_thinking`, 34 of 162 letters produced no surviving
  pair. Check the equivalent share on the new candidates before committing, since
  those letters, plus the reserve, are all that letter mode contains.
- **Project metadata.** `darwin_1` has no `metadata/state.json` (`emit_split.py`
  copies one only if it exists), and `darwin_split` is generated with
  `ft:gen --thinking`. Confirm what the downstream run needs from a `darwin_1`
  split before generating.
- **`select_kind.py` and `run_arms.sh`** are still hardcoded to `darwin_split`.
  They are not part of stages 1-4 and were left alone.

## Safeguards

- `emit_split.py` **deletes and rebuilds `--dst`** (including `corpus/chroma`, so
  `raft chunk` and `raft embed` must be re-run). It refuses to run if `--dst`
  equals, contains, or sits inside `--src`, and while a `raft embed` is in flight.
- It also refuses if the verdicts in `--work` do not belong to `--src`. Transcript
  numbers collide across corpora, so every verdict's URL is checked against the
  letter it names.
- `score_verdicts.py` iterates batches in sorted order so the item id chosen to
  represent a re-judged pair (and hence `emitted-provenance.json`) does not vary
  with Python's hash seed.

## Adjudication

The one manual stage: each `batches/batch-N.json` goes to an independent reader
that writes `verdicts/batch-N.json` mapping item_id to `{verdict, reason}`. A list
of records works too; the scorer accepts either. **The prompt is in
[`ADJUDICATOR_PROMPT.md`](ADJUDICATOR_PROMPT.md)** (a reconstruction; the original
was not saved), with the checks to run before trusting the output.

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

**Rebuilds are destructive.** See Safeguards.

**Pre-registration.** `prereg-batch7.json` records which planted controls were
judged catchable *before* the verdicts existed. If you add batches, do the same:
classifying a control as "soft" after seeing whether it was caught is not a test.

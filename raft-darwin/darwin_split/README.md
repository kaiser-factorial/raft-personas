# darwin_split

A RAFT project built from `darwin_thinking` by splitting letter exchanges into
paragraph-aligned question/answer pairs, so Darwin learns to answer *what he was
asked* rather than always producing a full letter.

## Why

`darwin_thinking` pairs a whole incoming letter with Darwin's whole reply. His
real replies open with his own news and often answer his correspondent's
specific points only at the end, so a model trained on whole letters learns to
reply at letter length and letter shape whatever it is asked. It cannot learn to
answer a single question, because it never saw one.

## Every letter is used in exactly one mode

| mode | transcripts | framing in the system prompt |
|---|---|---|
| **letter** | 49 | "a letter from X, which you are answering" |
| **split** | 183 | "a single passage from a letter by X, which you are answering on its own" |
| | **232 total** | |

No reply text is trained on twice. An earlier build emitted all 162 whole
letters *and* all 219 splits of those same letters, so 61% of Darwin's reply
text appeared in two examples — that was a defect, not an option.

The two modes carry **different `context` strings**, which become the setting in
the system prompt (`setting = context or "an interview"`). Identical framing was
the subtler half of the same defect: it gave contradictory supervision — same
prompt shape, targets ranging from 27 to 800 words — which makes the
letter/passage distinction both unlearnable and unsteerable at serve time. With
distinct framings the model can learn two behaviours and be asked for either.

### Which letters go to letter mode

The 34 letters that produced no surviving pair, plus the **15 richest-reply
letters held back from splitting** (`SPLIT_RESERVE`, default 15). The
reservation matters: the 34 alone are mostly single-paragraph notes — 5,305
words, only 9 multi-paragraph — too thin to learn a distinct long-form
behaviour. With 15 reserved, letter mode is 49 examples / 22,359 words / 24
multi-paragraph replies, at a cost of 36 of the 219 adjudicated pairs.

Split mode: 183 pairs from 113 letters. 123 answer with a single paragraph, the
rest with several; median 119 words, range 8–836.

## How the pairs were derived and checked

1. **Split** — each letter's incoming and reply paragraphs (≥8 words) matched
   into candidates. Merging of overlapping candidates runs to a fixpoint,
   because one reply paragraph can answer two incoming paragraphs.
2. **Adjudicate** — 243 unique candidates judged by seven independent
   subagents, each reading the source letters rather than the candidate alone,
   with blind planted controls in every batch. **219 KEEP, 24 DROP.** Of the 81
   pairs judged twice by different adjudicators, **96% agreed**.
3. **Merge** — verdicts merge on the *pair*, not the item id. Any DROP vetoes; a
   disagreement resolves to DROP, which loses nothing, since the letter is still
   in the corpus in one mode or the other.

### On the controls

**CROSS** controls swap in an answer from a *different* letter. Rejecting them is
ground truth by construction, and every adjudicator caught 3/3.

**SAME** controls swapped in a different paragraph from the *same* letter. These
proved **invalid as a gate**, recorded here so the mistake is not repeated. They
assume the splitter's *non*-links are correct — but the splitter's recall is
exactly what is under test. Auditing all five SAME controls an adjudicator
"failed" to catch found **5/5 were real links the splitter had missed**: Hooker
asks for "the Balanidae book" and Darwin answers about his "Barnacle Book";
Lyell says he will "reread it & try to reconcile the admission" and Darwin
answers "In my bigger book I have explained my meaning fully". Two others were
not valid controls at all — their question spanned 9 and 11 incoming paragraphs,
leaving almost any reply paragraph responsive. The adjudicators were right; the
gate was wrong. SAME is now diagnostic only.

## Grounding

1,405 original documents + **108** of Darwin's unprompted paragraphs from
**split-mode letters only** = 1,513.

Those paragraphs answer nothing in the incoming letter and are never a training
target in any mode, so adding them is not a reservation leak. Letter-mode
letters contribute nothing at all — their whole reply is the target. Withheld
besides: 307 paragraphs that do answer something, 35 sign-offs, 10 fragments
(<15 words), 8 postscripts, 2 signature blocks.

Retrieval additionally filters on `date_num < transcript date`, so a paragraph
can never be retrieved while generating its own letter; it becomes retrievable
only for *later* letters — Darwin remembering what he wrote last year. The
filter is strict, so it also withholds all grounding from a transcript's own
date; Darwin often wrote several letters a day, so this errs toward withholding
rather than leaking.

Each added document is titled `[derived: unprompted] …`, so the addition is
reversible in one pass.

## Running the training generation

```bash
cd darwin_split
RAFT_RECALL_MODE=source raft ft:gen --thinking
```

`RAFT_RECALL_MODE` is **not** cosmetic and defaults to the old behaviour:

- `summary` (default) — the summarizer's paraphrase. Its prompt names its
  exemplar in modern idiom (`"I've argued that..."`), so nearly every memory
  reaches Darwin in that register, in *every training example* rather than only
  at serve time.
- `source` — the quoted passage, read back out of the document by character
  offset so it carries the document's own spelling and punctuation.
- `register` — a paraphrase asked for in Darwin's own words (extractive).

Implemented on the local fork, branches `feat/verbatim-recall-mode` and its
follow-up, pushed to `kaiser-factorial/raft`. No PR opened against upstream yet.
See `../reports/paragraph-split/RECALL_MODE_ABLATION.md` for the measurements
and the ablation design.

## One pair per file — deliberate

`generate_finetune` threads `prev_answer` across the exchanges within a single
transcript file. Grouping a letter's pairs into one file would present Darwin's
own paragraph 1 as a prior conversational turn before paragraph 2 — asserting an
exchange that never happened, and feeding the model its own text as context.

## Isolating one mode

```bash
python ../reports/paragraph-split/select_kind.py derived_paragraph_pair  # 183
python ../reports/paragraph-split/select_kind.py whole_letter            #  49
python ../reports/paragraph-split/select_kind.py                        # restore
```

Useful for ablations. It moves the other mode into `conversations_held/`,
renumbers what remains so the sequence stays gapless, and re-syncs the
provenance file. Grounding and the embedding store are untouched, so no
re-chunk or re-embed is needed.

## Provenance

`../reports/paragraph-split/emitted-provenance.json` records, for all 232
transcripts, the mode, source letter, paragraph indices, whether the letter was
reserved from splitting, and the adjudicator's verdict reason.

**Join on `url`, not on the filename.** `select_kind.py` renumbers transcripts,
so `transcript` is a convenience field rewritten on every run (and `null` for
held-back records). `url` is unique and stable.

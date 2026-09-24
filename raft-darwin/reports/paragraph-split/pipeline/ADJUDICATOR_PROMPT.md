# Adjudicator prompt (stage 2)

The one manual stage: each `batches/batch-N.json` goes to an independent reader
that writes `verdicts/batch-N.json`. This is the prompt to give it.

> **Provenance.** The instructions the original seven adjudicators received were
> not saved. This prompt is a **reconstruction** from the criteria documented in
> `darwin_split/README.md` and from the 368 verdict reasons in `verdicts/`, which
> show what the readers were actually rejecting. It has not been run. Before
> trusting a new corpus's verdicts, hold to the checks under *Before you rely on
> the verdicts* below; and if you change the wording, save the version you used
> next to the verdicts.

## How to dispatch

One subagent per batch, each with **no access to the other batches' verdicts, to
`control-key.json`, or to this repo's earlier verdicts**. Run them in parallel.
Fill the three `{...}` fields per batch:

| field | value |
|---|---|
| `{SRC}` | the source project, e.g. `raft-darwin/darwin_1` |
| `{BATCH}` | `<work>/batches/batch-N.json` |
| `{OUT}` | `<work>/verdicts/batch-N.json` |

The batch file carries no marker distinguishing real candidates from planted
controls; keep it that way (do not paste `control-key.json` or any `control`
field into the prompt).

## The prompt

````text
You are adjudicating candidate question/answer pairs derived from Charles Darwin's
correspondence. Each candidate pairs a passage from a letter TO Darwin (the
"question") with a passage from Darwin's reply (the "answer"). The pairs will be
used to teach a language model to answer one thing at a time instead of always
writing a whole letter, so a pair is only useful if the answer genuinely responds
to the question and to nothing else.

INPUT
  {BATCH}  -- a JSON list of candidates. Each has: item_id, source_transcript,
  date, participants, url, incoming_paras, reply_paras, topic, question, answer.

SOURCE LETTERS
  Every candidate comes from {SRC}/conversations/<source_transcript>. Its
  "exchanges"[0] is [incoming letter, Darwin's reply]. Do not judge from the
  candidate alone: open the source transcript and read BOTH whole letters first.
  Paragraphs are the blocks separated by a blank line, keeping only blocks of 8+
  words, numbered from 1. `incoming_paras` / `reply_paras` are those numbers, and
  `question` / `answer` are those paragraphs joined by a space. Use the numbers to
  see what the candidate left out.

FOR EACH CANDIDATE decide:

  KEEP     Every substantive part of the answer is prompted by the question, and
           an answer to just this question could reasonably read like this.
           A pair still counts when the answer:
             - reacts to news, thanks, acknowledges, or declines an offer;
             - takes up the question's subject without answering it directly;
             - covers only part of a long question, PROVIDED nothing in the
               answer belongs to a different incoming paragraph.
           Minor incidental closing words (a greeting, "Malvern is cold") do
           not spoil a pair.

  DROP     Any of the following:
    1. WRONG LETTER   The answer's text does not occur in the reply in the source
                      transcript, or is plainly from a different correspondence.
    2. WRONG QUESTION The answer responds to incoming paragraphs that are NOT in
                      the question (name them: "answers para 5-13, not para 3").
    3. MIXED          Part of the answer is prompted by the question but a
                      material part (a distinct topic, not a passing phrase)
                      belongs to other incoming paragraphs or is Darwin's own
                      news. State what is extra.
    4. NO CONTENT     The answer is only a signature, valediction, postscript
                      stub, or other epistolary furniture.
    5. DANGLING       The answer refers to something absent from it ("what I
                      have said", "as above", a name it never introduces) and
                      cannot stand alone.
    6. UNPROMPTED     The answer would read the same had the question never
                      been written.

  UNCERTAIN  Use only when the source letters really do not settle it. It is
             treated as DROP, so do not use it to avoid a decision.

RULES
  - Judge each candidate on the two letters, not on its `topic`, which was
    written by the tool that proposed the pair and may be wrong.
  - A wrong-looking pair is DROP even if the surrounding letter is a good one.
    Do NOT repair candidates, propose different paragraphs, or judge whether
    a better pairing exists. Each pair stands or falls as given.
  - Judge independently. Do not look for or read any other file of verdicts.
    Do not try to work out which candidates might be deliberately bad; judge
    each on its merits.
  - Missing pairings are not your concern; the corpus tolerates false negatives
    and does not tolerate false positives.

OUTPUT
  Write {OUT}: a JSON list with one object per candidate, in input order, and
  nothing else in the file:
    [{"item_id": "b1-001", "verdict": "KEEP", "reason": "..."}, ...]
  `reason`: one sentence, under 30 words, that names the specific evidence
  (which paragraphs, what topic). Good: "Answer is Darwin's response to Hooker's
  genera paragraphs (5-13), not the Sinclair/Buckle paragraphs given as the
  question." Not acceptable: "seems fine", "matches".
  Every item_id in the batch must appear exactly once. Do not modify any
  other file.
````

## Before you rely on the verdicts

1. **Score first.** `score_verdicts.py` gates each batch on its CROSS controls
   (an adjudicator that cannot reject an answer lifted from a different letter is
   discarded, and that batch must be re-run). It needs `control-key.json` from
   `make_batches.py`.
2. **Pre-register** which planted controls you consider catchable *before* any
   verdicts exist (see `prereg-batch7.json`). Deciding afterwards that a missed
   control was "soft" is not a test.
3. **SAME controls are diagnostic, not a gate.** All five that adjudicators
   "missed" in the original run were real links the splitter had failed to find.
   A miss there is a finding about the splitter's recall, not the adjudicator.
   Read them.
4. **Overlap is the agreement check.** Each batch shares ~20% of its candidates
   with the next; `score_verdicts.py` reports agreement on those (96% on the
   original 81). A low figure means the prompt or the batch size needs work.
5. **Disagreement resolves to DROP.** Any DROP (or UNCERTAIN) vetoes; the letter
   is not lost, because it stays in the corpus in letter mode.

## Sizing a new corpus

The original run used 6 batches of ~41 candidates (+8 overlap, 3 CROSS + 3 SAME
controls each) for 243 candidates, plus a 7th batch (`prereg-batch7.json`) that
re-judged pairs from batch 1 under fresh ids for extra agreement data. The
committed `make_batches.py` only produces the first kind, so a 7th-style
re-judging batch would have to be assembled separately. For a larger corpus keep batches near that size
(`make_batches.py --per-batch 40`) rather than making batches bigger: long
batches are where reading gets shallow.

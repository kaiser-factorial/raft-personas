# Recall-mode ablation: design notes and prompt-wording findings

Three arms, identical corpus (`darwin_split`, 232 transcripts), differing only
in how a retrieved memory is worded in the training data:

| arm | `RAFT_RECALL_MODE` | memory text |
|---|---|---|
| 1 | `summary` (default) | the summarizer's paraphrase — the historical behaviour |
| 2 | `source` | the quoted passage, read back verbatim out of the document |
| 3 | `register` | a paraphrase, asked for in Darwin's own words |

## Where the contamination actually came from

A single hardcoded exemplar in the summarizer prompt:

```
RECALL: <one or two sentences, first person, restating that point as a
        recollection you could draw on -- "I've argued that...">
```

`"I've argued that…"` is modern idiom and a modern contraction, and the models
follow it literally. That phrasing *is* the register the persona is trained to
remember in.

## Wording the register arm — two attempts

**v1 asked for the author's register directly.** It failed, and failed in a way
that a naive metric rewards. gpt-4o produced contraction-free modern pastiche:

> "I am always fascinated by discussions on the breeding of animals,
> particularly when it comes to the question of mongrels and their lineage.
> Your latest letter on this subject captivated me, and I treasure these
> exchanges…"

No contractions, no business-speak, so a modernism-counting check scored it 0
and passed it. But "I am always fascinated by", "when it comes to", "I opted to
document" are not Darwin. **Counting modernisms cannot detect pastiche.**

**v2 makes the task extractive** — compress using the words already there, do
not substitute, explain or characterise. Measured as the share of the recall's
content words that occur in the source document:

| arm | borrowed vocabulary | mean length |
|---|---|---|
| summary | 60% | 30 words |
| register (v2) | 79% | 34 words |
| source | 100% (by construction) | 42 words |

v2 output reads as compressed Darwin: *"I am sending an account of the few
experiments on salting seeds to Linnean Soc at Hooker's suggestion, tabulating
our results."* It still smooths a little — `&`→`and`, `therefore`→`so`, "Breeds
of Dogs"→"dog breeds" — so call it ~80% Darwin rather than his own prose.

**Use borrowed-vocabulary share, not modernism counts, to evaluate any further
wording.** The first metric would have passed v1.

## Experimental-design caveat, worth deciding before the runs

Arms 1 and 2 are **perfectly matched**: one summarizer call serves both, and the
grounding check accepts or rejects identically — verified across five retrieved
memories with zero disagreements. Only the wording differs. This is a clean
ablation.

Arm 3 changes the prompt, so it also perturbs *which* memories survive. On 24
retrieved memories with gpt-4o-mini:

```
summary    kept 4/24 (17%)   skip 4   citation rejected 16
register   kept 3/24 (12%)   skip 2   citation rejected 19
```

The difference (4 vs 3) is small and within noise at this n, but it is not zero,
so arm 3 differs from the others in two ways at once. Two observations:

1. ~~The dominant effect is the citation check rejecting ~two-thirds of
   output.~~ **Model-specific, corrected below.** On a matched set, gpt-4o had
   *zero* citation rejections — it declines by saying `skip` (24 of 27). Heavy
   citation rejection is a gpt-4o-mini behaviour.
2. ~~Summarizer model matters more than the mode; gpt-4o gives far more
   surviving memories.~~ **Withdrawn — the comparison was invalid** (gpt-4o on 5
   memories vs gpt-4o-mini on 24 *different* ones). Measured matched on one
   retrieved set of 27, the result inverts:

   ```
   gpt-4o        kept 3/27    skip 24,  citation rejected 0
   gpt-4o-mini   kept 6/27    skip 6,   citation rejected 14,  unstructured 1
   ```

   gpt-4o keeps **half** as many, not more. The two models fail in different
   ways: 4o is conservative and declines; mini is permissive and then fails the
   citation gate. Note also that `skip` is largely *correct* behaviour — top-5
   retrieval returns mostly irrelevant passages, so a low keep rate is the
   filter working, not a fault. But 4o remains the right choice for the register
   arm, because register wording only holds up on it (88% borrowed vs mini's
   39–48%).

## Open questions for the runs

- Which small Qwen (a thinking-capable 2–4B, so the thinking pathway is
  exercised as the full run would be).
- Whether to accept arm 3's selection perturbation, or additionally run arm 3
  with memory *selection* frozen to arm 1's (feasible: cache arm 1's SOURCE
  decisions and re-word only the kept ones — that would make all three arms
  perfectly matched).
- Talkie is a separate matter: no thinking block in its chat template
  (`<|system|>/<|user|>/<|assistant|>` only, so `<think>` tags would be literal
  text) and a 2048-token context, which ~25% of whole letters exceed against ~2%
  of split pairs. It wants a non-thinking run on the split corpus.

---

# Round 2: settling the register wording (gpt-4o, 27 passages, `useful_check` off)

| candidate | borrowed | reporting voice | length | note |
|---|---|---|---|---|
| v2 (shipped) | 79% | 5/27 | 34w | first run of the same cell gave 85% / 2-of-27 |
| **v3** | **88%** | **1/27** | 45w | bans reporting verbs |
| v4 | 70% | 6/27 | 44w | drops the ban, requires person fidelity |

**Run-to-run variance is material.** The identical v2 cell moved 85%→79% borrowed
and 2→5 reporting between two runs at n=27. Treat gaps under ~6pp as noise; the
v3–v2 gap (9pp) is just outside it, the v3–v4 gap (18pp) is real.

## What was learned, including two of my own errors

**The contamination was one exemplar.** `RECALL: <... "I've argued that...">`.
Every summary-mode recollection in every measurement opens that way (3/3 and
6/6 in round 1). Nothing subtler was going on.

**Banning reporting voice was the wrong diagnosis** — the user caught this.
Darwin writes those constructions himself; one retrieved passage is literally "I
think I argued that there was a good deal of concomitancy". Banning the
construction bans his own idiom. The real defect in weak-model output was modern
idiom *wearing* a reporting frame ("expressed my willingness to conduct
experiments"), not the frame.

**But the ban is empirically the best lever anyway**, which is an awkward
result worth stating rather than hiding: forbidding "I expressed/mentioned/
argued" forces the model to state the content directly, and extraction rises.
v4, which replaces the ban with an explicit person-fidelity requirement, is
*worse* on borrowed vocabulary (70%) and no better on reporting (6/27), buying
only a marginal gain in third-party retention (25/27 vs v3's 24/27).

**Suggested v5, untested:** narrow v3's ban to modern reporting phrasings while
explicitly permitting period ones — forbid "I've argued that", "expressed my
willingness", "was asked to aid"; allow "I have said before", "I think I argued
that". That should keep the extraction benefit without proscribing Darwin's own
constructions.

## A misattribution bug, real but unquantified

First-person compression can silently reassign other people's work to Darwin.
Demonstrated by hand: Darwin to Asa Gray, "(He says further he shall work the
Tasmanian Flora on same principle.)" — "he" being Hooker — became "I am going on
with the Tasmanian Flora, finding it very interesting."

**Source mode is immune by construction**, since it emits the span verbatim with
pronouns intact. Paraphrase modes (1 and 3) are not.

The frequency is **unknown**. An LLM judge built to measure it is unreliable and
its numbers are not reported here: source mode, which must score ~0, was flagged
at 1/3 and 1/6, on phrases like "I thank you most sincerely for your
glass-specimens ... & for your very kind letter" — Darwin's own sentence. The
judge flags any mention of another person's things, not misattribution. Source
mode makes a convenient built-in control; any future judge must score ~0 on it
before its other numbers mean anything. (Third mis-calibrated judge this
session, after the register classifier and the SAME adjudication controls.)

## Does arm 3 still earn its place?

At 88% borrowed and 45 words, register-v3 sits close to source (100%, spans of
20–50 words). If it collapses onto source, the ablation has two distinct arms
rather than three, and the third training run buys little. Worth checking
directly — per-passage similarity between the register and source outputs on the
same memory — before committing three runs.

---

# Round 3: the measurement could not distinguish the candidates

gpt-4o, the same 27 passages, `useful_check` off:

| candidate | borrowed | reporting | length | like source |
|---|---|---|---|---|
| v2 | 87% | 0/27 | 37w | 45% |
| v3 | 91% | 1/27 | 37w | 53% |
| v4 | 74% | 3/27 | 40w | 35% |
| v5 | 80% | 5/27 | 46w | 47% |
| **v5min** | 88% | 1/27 | 41w | 58% |

## The noise floor swallows the rankings

The **identical** v2 prompt, on the **identical** 27 passages, across three runs:

| run | borrowed | reporting |
|---|---|---|
| 1 | 85% | 2/27 |
| 2 | 79% | 5/27 |
| 3 | 87% | 0/27 |

Retrieval is deterministic, so the inputs were the same every time; this is
pure sampling variance. It spans 79–87% and 0–5, which is wider than almost
every gap between candidates. v2 (87%), v3 (91%) and v5min (88%) are
**indistinguishable**, and round 2's headline — "v3 beats v2 by 9pp" — was
noise, since v2 has now scored 87% on its own.

**Lesson: run a repeat cell before ranking anything.** Three rounds of wording
iteration were partly chasing sampling noise. Only v4 (74%) sits clearly below,
and even v5's 80% is inside v2's observed range.

What *does* survive the noise is the difference the ablation is about:

```
summary   ~49-60% borrowed vocabulary
register  ~88%
source     100% (by construction)
```

## Decision

**Adopt v5min**, chosen on principle rather than on a metric that cannot
separate the candidates: it is the shortest, carries no prohibition list (so it
does not proscribe constructions the author himself uses), and drops the
I-subject exemplar. It preserves period abbreviations in practice — "I enclosed
a catalogue of Habitats, having thought my notes **wd.** have turned out of more
use". Now in `prompt_manager._RECALL_IN_REGISTER`.

## Arm 3 is distinct from arm 2

Token overlap between a register recollection and the verbatim span cited by
the same reply is **45–58%**. Register compresses and recombines rather than
quoting, so the third arm is not redundant and earns its run.

## Still open

Whether v5min fixes the misattribution remains **unmeasured**. The person-fidelity
clause does raise third-party retention (v4 10/27, v5 8/27, against v3 and v5min
at 5/27), but whether that is fidelity or invented attribution needs hand-checking
against sources — the automated judge failed its own control (see round 2) and its
numbers are not used. If misattribution matters enough to gate the runs, hand-check
~15 register recollections against their source passages.

---

# Round 4: the hand-check, and the actual cause of misattribution

Eight grounded v5min recollections read against the region of the source they
draw on. **Six correct, two misattributed** — and the two share a cause that
none of the prompt wording could have fixed.

| # | verdict | note |
|---|---|---|
| 1 | ok | Darwin's own "I see the Un. St. Ex. Ex. make the Sandwich Flora eminently peculiar" |
| 2 | **misattributed** | "the further I trace a diffused species..." is **Hooker's** sentence |
| 3 | ok | Darwin on Galapagos polymorphism |
| 4 | ok | Darwin on the specimens and catalogue |
| 5 | ok | Darwin on sporules blown by wind |
| 6 | **misattributed** | "Before I was favoured with your letter..." is **John Davy's** |
| 7 | ok | Darwin on his "far-distant work on species" |
| 8 | ok | Darwin on his notes and preserved specimens |

## Cause: two-party exchange memories presented as "something you wrote"

`store_exchange_embedding` writes each processed exchange back into the store as
a single document in `"Speaker: text"` form — the correspondent's letter *and*
Darwin's reply together. The summarizer's system prompt then says "Below is
something you wrote or said earlier", which is false for half of it, so the
model draws from either speaker.

**These are massively over-retrieved.** They are 162 of 1,568 chunks (10% of the
store) but were **17 of 27 retrieved passages (63%)** — because a document
containing a question resembles a new question far better than Darwin's outgoing
letters do. So the exposure is not a 10% edge case; most retrieved memories
carry another person's words.

## Correction: source mode is NOT immune

Round 2 claimed source mode is immune to misattribution "by construction". That
holds only for pronoun collapse *within* Darwin's own prose. It does **not**
hold here: source mode emits the verbatim span, and the span may be Hooker's
sentence — verbatim, and still presented as Darwin's recollection. All three
arms carry this bug.

## Suggested fix

Retrieval should keep using the whole exchange (that is why it retrieves well),
but the summarizer should be handed only the persona's own lines of it. The
`kind == "exchange"` metadata already distinguishes these documents; the speaker
labels make the split mechanical.

Because it hits all three arms identically it does not invalidate the ablation,
but it does mean every arm would be trained on memories that sometimes put the
correspondent's words in Darwin's mouth.

## Harness artifact worth remembering

With `useful_check` off (used to get sample size), the model cannot skip, so an
irrelevant passage forces it to answer from the *question* instead — 3 of 27
v5min outputs were ungrounded (<50% borrowed). Grounded mean is 94%, not 88%.
These outliers moving in and out across runs probably explain more of the
79–87% variance than uniform sampling noise does.

## The fix, measured

Speakers are now named to the summarizer for `kind == "exchange"` documents,
and the correspondent's half is kept rather than stripped — what the persona
read is part of its memory, and a reply is often unintelligible without the
letter it answers. Ordinary documents keep the historical framing byte for byte.

On the 17 exchange memories among the 27 retrieved passages, with the real
questions:

| | from Darwin's words | from other's half, attributed | from other's half, **claimed as own** |
|---|---|---|---|
| unlabelled | 13 | 0 | **4** |
| labelled | 9 | 8 | **0** |

The automated rate before the fix (4/17 = 24%) agrees with the hand-check rate
found by reading (2/8 = 25%) — two independent methods converging, which had
not happened before in this investigation.

### Two detectors that did not work, for the record

- Keying on which half the **SOURCE citation** came from found 0 mis-claims in
  both conditions. The SOURCE and the RECALL can draw on different halves, and
  the failure lives in the RECALL. Measure where the recollection's *content*
  comes from, not where its citation does.
- Testing with a generic question ("What have you concluded?") rather than the
  real ones produced a dramatic but spurious result (citations swinging 16/1 to
  14/3 across conditions). With the real questions the balance barely moves.
  Match the test conditions to the conditions the failure was found in.

---

# Evaluating the arms: serve each one the way it was trained

Memories are generated at **two** stages, not one:

| stage | generates memories | needs the summarizer LLM |
|---|---|---|
| `ft:gen` — build the dataset | yes | yes |
| `ft:run` — train | **no** | **no** |
| `serve` / `ask` / `comment` — talk to it | **yes, every turn** | **yes, every turn** |

Training reads the chat-format jsonl and nothing else: `hf_finetune.py` never
touches `MemoryManager`. Only `generate_finetune.py` and the serving paths
(`serve.py`, `comment.py`) generate memories.

**So `RAFT_RECALL_MODE` has to be set again when serving, and it has to match
what the arm was trained on.** A persona trained on verbatim source memories
but served summarized ones is being fed a kind of memory it never learned from,
and the comparison would measure that mismatch rather than the thing being
tested. Each arm must be served under its own mode:

```bash
RAFT_RECALL_MODE=summary   raft serve   # the arm trained on paraphrase
RAFT_RECALL_MODE=source    raft serve   # the arm trained on quotes
RAFT_RECALL_MODE=register  raft serve   # the arm trained on in-register recall
```

Two consequences worth planning for:

- **Serving is not free.** Every turn retrieves and summarizes, so evaluating
  three personas over a probe set is another round of summarizer calls. Point
  `RAFT_LLM_BASE_URL` at a local model on bigmac to avoid paying OpenAI for it
  — but then use the *same* local summarizer for all three arms, since the
  summarizer's own quality varies by mode (gpt-4o-mini's register output was
  markedly worse than gpt-4o's).
- **A fourth comparison exists, and is cheap.** Each trained arm can also be
  served under the *other* modes. Training and serving mode are separable, so
  the question "does it matter what it was trained on, or only what it is fed
  at inference?" is answerable without any extra training — just serve each of
  the three models under each of the three modes.

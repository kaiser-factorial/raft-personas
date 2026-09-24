# Outstanding items

Living doc. Companion to `RECALL_MODE_ABLATION.md` (what was measured and how)
and `QWEN35_2B_TRAINING.md` (the verified training setup).

---

## Corrections carried forward

**Talkie-Darwin did not fail.** An earlier read of its training log called it a
failure on `train_loss: 25.8`. That figure is inconsistent with the
`mean_token_accuracy: 0.43-0.46` reported beside it — you cannot have 44% token
accuracy and a real cross-entropy of 25.8 — so it is almost certainly
unnormalised. **Judge that run by token accuracy, not by the loss scalar.** The
adapter exists at
`~/personas/darwin_0/conversations/hf-run/.opbdh/finetune/results/default/model/`
(249 MB) and has **never been served or evaluated** — the only Talkie server we
ever ran was `talkie-base`, un-finetuned.

It was trained on the *old* `darwin_0` (plain, pre-split) dataset at
`--max-length 2048`, which truncates ~25% of whole letters. The split corpus
built since truncates 2% at 4096, so a retrain has a materially better shot.

---

## 1. Eval metrics for the three arms

Built in `eval/` — `probes.json`, `build_memories.py` (retrieval phase, this
machine), `generate_eval.py` (generation phase, bigmac). Thinking and reply are
recorded **separately**: every earlier measurement in this project looked only
at the reply, so a change in how the persona *thinks* was invisible.

| # | metric | what it catches | status |
|---|---|---|---|
| 1 | **memorisation** — longest verbatim run vs the training corpus | the failure specific to this ablation: source-trained models regurgitating rather than absorbing | to build |
| 2 | **register** — borrowed-vocabulary share against period text | modern pastiche. *Not* modernism counts, which passed contraction-free pastiche twice | to build |
| 3 | **letter-structure** (1a) | did chunking stop arg→peroration→"ever yours sincerely" on a one-line question? `brevity`/`domain-short` probes vs the `letter-full` control | to build |
| 4 | **conversational collapse** (1b) | does the persona capitulate over six scripted escalating turns, and does recall mode change that | to build |
| 5 | **domain/info leakage** (2) | anachronistic *content* as distinct from anachronistic *voice*. The four `modern-leak` probes retrieve **zero memories in every mode**, so leakage there is purely parametric | to build |
| 6 | **thinking-block versions of 2, 5** | whether source/register recall changes how he reasons, not just how he speaks | to build |
| 7 | **discrimination vs real Darwin**, blind, with a real-vs-real control | overall fidelity | needs held-out text |
| 8 | **3×3 train-mode × serve-mode grid** | separates "internalised a register" from "echoing whatever context it is fed" | free once 1–6 exist |

**Every metric needs a ground-truth control arm before its numbers are used.**
Four have already been wrong in this project: the register classifier (scored
real Darwin 0/10 PERIOD), the SAME adjudication controls (5/5 were real links),
the misattribution judge (flagged verbatim Darwin), and the modernism counter.

**Held-out material**: `reports/1860`–`1868` are discovery metadata only
(`correspondence_review_status: not_started`) — letter IDs, no text. Gemini's
fetch is expected to supply the actual post-1859 letters, which are ideal:
outside the training cutoff *and* outside the retrieval date filter.

### Next session starts here

Everything needed is on disk. No API, no GPU — this is local analysis.

**Inputs**

| file | contents |
|---|---|
| `eval/gen/gen-{summary,source,register}.json` | 19 generations per arm: `single[13]` + `conversation[6]`, each with `qid`, `kind`, `question`, `memories`, **`thinking`**, **`reply`** |
| `eval/memories.json` | what each mode retrieved, per probe |
| `arms/chat-{arm}.jsonl` | the training text, for the memorisation check |
| `darwin_split/corpus/documents.jsonl` | 1,405 real Darwin documents — the period reference corpus, and the control for every register metric |

**The probe set splits itself.** 10 probes retrieved at least one memory; 9
retrieved none — including **all four `modern-leak` probes in every mode**. So:
probes-with-memories measure train×serve interaction, probes-without measure the
*pure training effect*, and anachronism on the modern-leak probes is
unambiguously parametric rather than fed.

**One unanalysed signal already visible.** Mean reply length: summary 190w,
register 173w, **source 117w**; mean thinking: 40w / 41w / **31w**. Consistent
with verbatim memories anchoring him to specifics rather than inviting
expansion — but it is one seed, so treat it as a hypothesis, not a result.

**Controls to build alongside each metric** (not after):

- *memorisation* — real held-out Darwin scored against the training corpus
  gives the floor from shared idiom. Without it, any overlap looks alarming.
  `_verbatim_span` in `raft.memories` already does longest-run matching.
- *register / borrowed vocabulary* — score **real Darwin documents** through the
  same metric. They must score at the top; anything that ranks them below a
  persona is miscalibrated.
- *letter-structure* — the `letter-full` probe is the positive control: given a
  real multi-paragraph letter the persona *should* produce letter shape. A
  metric that flags the `brevity` probes but not `letter-full` is backwards.
- *collapse* — run the same six turns with memories stripped. If collapse is
  identical without memories, it is a base-model property and not about recall
  mode at all.
- *domain leakage* — the two `period-offdomain` probes (Dickens, railways) must
  *not* flag. They are period-appropriate but outside Darwin's subject, so they
  separate "off-topic" from "anachronistic".

**Known asymmetry to carry into any conclusion**: `summary` and `source` are
matched by construction (124 vs 125 memories, same summarizer call via the
replay cache). `register` is **not** — it re-ran its own calls and carries 136.
Weight summary-vs-source more heavily; treat register as suggestive.

**Sample size is the weak point.** 19 probes × 1 seed per arm, and sampling
noise has already faked a result once in this project. `generate_eval.py`
takes `--seed`, so the cheap fix is 3–5 seeds per arm before any ranking, with
variance reported. Regeneration is ~20 min per arm on bigmac.

**The 3×3 grid is nearly free**: `generate_eval.py --serve-mode` already
overrides which arm's memories are fed, and `memories.json` holds all three
modes. Six more runs completes the grid.

---

## 2. Temporal fidelity (the 1833 problem)

Does a persona asked a question dated 1833 discuss the Origin, because the
weights absorbed 1859? Date-filtered retrieval controls what is *in front of*
him, not what is *in* him.

- **Cheap test first, costs nothing**: same probes at 1817-07-17 / 1833 /
  1845-10-11 (midpoint) / 1859-11-24 (edge) / 1874-01-06. The outer dates are
  symmetric about the midpoint of the 1831-08-30 → 1859-11-24 span. Run with
  **no memories** to isolate parametric leakage, then with date-filtered
  memories to see whether retrieval shields it.
- **The fix, cheaper than it sounds**: chronologically-ordered training with
  periodic checkpoints is **one run, not N** — checkpoint at step *t* has only
  seen letters up to date *t*. The real constraint is that strict temporal
  honesty needs a **single epoch**; with 3 epochs, epoch 2 revisits 1833 after
  having seen 1859 and every later checkpoint is contaminated.
- **Talkie does not help here.** It fixes *modern* leakage (nothing post-1931)
  but its corpus certainly includes the Origin, so Talkie-Darwin in 1833 still
  knows what he published in 1859. Two different axes.

---

## 3. Talkie

- **Sizes** — `talkie-lm` publishes `talkie-1930-13b-base`, `-it`, and
  `talkie-web-13b-base`. All 13B. These are **two corpora, not two sizes**:
  web is 260B tokens of FineWeb and exists explicitly "to make possible
  controlled comparisons between vintage and modern LMs". A friend believes
  another size exists — **needs deeper research** (the talkie-lm GitHub and the
  report at talkie-lm.com, not just the HF org listing).
- **Retrain Darwin on Talkie** using the split corpus at 4096 rather than
  `darwin_0` at 2048, and actually serve/evaluate the result this time.
- **Fair vintage-vs-modern comparison** requires base-vs-base: instruction
  tuning exists only on the 1930 line.

---

## 4. Persona-as-summariser, reframed

Both Darwin-summarises-Darwin and Talkie-summarises failed on **format**, not
capability — each answered `skip` and could not produce `SOURCE:`/`RECALL:`.
That is unsurprising: a model trained to *be* a voice was never trained to
perform structured extraction.

Two directions, worth trying together:

1. **The acting prompt.** Ask as one would ask a person of the period to read a
   record and speak in character, rather than as a parsing task. Supply
   structure loosely and tolerate imperfect form.
2. **Invert the grounding** (the "swappy" idea). Do not ask for a citation at
   all. Let the model speak freely in character, then locate the supporting
   span *ourselves*: `_verbatim_span` already finds the longest in-order word
   run between two texts, and pointing it at the recollection lets it
   **discover** the source instead of verifying a supplied one. The model never
   emits a label; the citation check becomes ours.

   This also rescues a case the current design throws away: a model that
   recalls faithfully but cites sloppily (gpt-4o-mini's 14 citation
   rejections). **Risk**: spurious matches — a span sharing words without
   supporting the claim. Needs a coverage threshold *and* a control arm of
   deliberately mismatched document/recollection pairs that it must reject.

If Talkie works as summariser, its paraphrases are natively period and the
whole register-instruction problem disappears — that is what the v1–v5min
iteration was working around.

---

## 5. The density hypothesis

**Were verbatim-source memories so valuable for Darwin because his letters are
unusually dense with concrete scientific content** — species, experiments,
specimens, dates — rather than because verbatim recall is generally better?

Prediction: for a corpus whose value is **argumentative structure** rather than
factual density, source should beat summary by much less, or not at all.
Summarising "I planted 87 seeds in salt water for 42 days" destroys the content;
summarising a line of reasoning may not.

Comparison corpus wanted: similar period and register, lower factual density,
more argument.

**Two hard constraints, and the second rules out most candidates:**

1. **Not translated.** The register measured would be the translator's, not the
   author's — which is the one axis we most want. This is what rules out
   **Nietzsche–Wagner**, and Mill–Comte with it.
2. **Bidirectional.** The split pipeline needs the *incoming* letter to pair
   against the reply. Most "Life and Letters of —" volumes print only the
   subject's outgoing side, which makes them useless here however good the
   prose. The Darwin Correspondence Project gives both sides; almost nothing
   else does.

| candidate | era | both sides? | availability | note |
|---|---|---|---|---|
| **Carlyle–Emerson** | 1834–1872 | **yes** | Gutenberg, 2 vols | top pick: same era, English throughout, chronological, ideas-not-specimens |
| **Browning–Barrett** | 1845–1846 | **yes** | Gutenberg | a *third* axis — emotional/personal density rather than factual or argumentative. Interesting control, not the argument corpus |
| J. S. Mill correspondence | 1830s–1870s | partial | Liberty Fund online | argument-dense and contemporaneous; pairing depends on which exchanges survive both ways |
| William James letters | 1860s–1910 | mostly one side | Gutenberg | argumentative, but outgoing-only as published |
| George Eliot letters | 1840s–1880 | mostly one side | Gutenberg | same era, literary rather than scientific; one-sided |
| Ruskin, *Fors Clavigera* | 1871–1884 | no incoming | Gutenberg | letters-as-essays, very low factual density, but nothing to pair against |
| T. H. Huxley life & letters | 1850s–1895 | partial | Gutenberg | same *domain* as Darwin, so it fails to isolate density |

**Carlyle–Emerson is the one to try**: it satisfies both constraints, matches
Darwin's period, and swaps scientific density for argumentative structure while
holding language and era fixed.

---

## 6. GRPO

**There is no RL stage in raft or opbdh.** Confirmed on word-boundary search:
raft has zero mentions; opbdh's two hits are a docstring naming the HF repo
`lumpenspace/reword-grpo-scaled` — a *different* project of lumpenspace's, not
an implementation. `FINETUNE_METHODS = ("lora", "qlora", "full")`. But **`trl`
0.29.1 is installed with `GRPOTrainer` and `DPOTrainer`**, so adding one is
feasible.

The eval metrics above are the reward model in embryo — borrowed-vocabulary
share, memorisation penalty, anachronism penalty, temporal fidelity (a
particularly good RL target, being hard to fix with SFT and easy to score).

**Sequencing argument**: validate each reward component against a ground-truth
control *before* a policy optimises against it. RL amplifies whatever the reward
mismeasures, and a reward that scores real Darwin poorly would train the persona
away from Darwin. Also note GRPO needs generation *and* training in the loop,
which likely means moving off MPS reference kernels.

---

## 7. bash.org persona

A register experiment at the opposite extreme from Darwin: IRC quotes, no
scientific density at all, heavy formatting convention, and a voice that is
almost entirely register. Genuinely useful as a generalisation test — if the
pipeline's register machinery only works on dense Victorian prose, this is
where it breaks.

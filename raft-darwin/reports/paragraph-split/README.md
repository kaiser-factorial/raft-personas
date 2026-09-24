# Paragraph split and the recall-mode ablation — start here

Orientation for this workstream. Read this before `OUTSTANDING.md`.

> The repository root `README.md` describes corpus **collection** and ends "No
> embeddings or training have run." That is now stale: embedding, dataset
> generation and three training runs are complete. Collection and training are
> separate efforts sharing a repo.

## What this is

Two linked pieces of work on top of the 162-transcript Darwin export.

**1. The paragraph split.** `darwin_thinking` pairs a whole incoming letter
with Darwin's whole reply, so a model trained on it answers *everything* at
letter length whatever it is asked. `darwin_split` breaks exchanges into
paragraph-aligned pairs so he learns to answer the question in front of him,
while reserving 49 letters in whole form so long-form does not vanish.

**2. The recall-mode ablation.** RAFT feeds a persona its own retrieved
"memories" during both training and serving. Those memories were being written
by a summarizer in *modern* register — 78% of them opening "I've argued
that…" — so the persona learned to remember in a voice that is not its own.
Three arms test what to do about it:

| arm | memory text |
|---|---|
| `summary` | the summarizer's paraphrase (raft's historical behaviour) |
| `source` | the quoted passage, verbatim from the document |
| `register` | a paraphrase asked for in Darwin's own words |

## Where things are

**This machine**

| path | what |
|---|---|
| `darwin_split/` | the split project: 232 transcripts, 1,513 grounding docs, 1,514 chunks |
| `darwin_split_arm3/` | a copy used to generate the register arm concurrently |
| `reports/paragraph-split/pipeline/` | the four stage scripts + measurement tools |
| `reports/paragraph-split/arms/` | the three datasets, the chat-format jsonl, the recall caches |
| `reports/paragraph-split/eval/` | probes, retrieved memories, generated outputs |
| `~/Projects/raft` | the raft fork (branches below) |

**bigmac** (`ssh bigmac` — a shared machine; check before loading anything large)

| path | what |
|---|---|
| `~/personas/arms/arm-{summary,source,register}/` | the three trained adapters, 67 MB each |
| `~/personas/train_arm.py`, `run_training.sh` | standalone trainer (see gotchas) |
| `~/personas/generate_eval.py`, `run_eval.sh` | eval generation |
| `~/personas/darwin_0/.../results/default/model/` | the **unevaluated** Talkie-Darwin adapter, 249 MB |

**raft branches** (all pushed to `kaiser-factorial/raft`, none PR'd upstream)

- `feat/rate-limit-retry` — helper-LLM backoff, plus the embedding retry
- `feat/verbatim-recall-mode` — `RAFT_RECALL_MODE=source`
- `fix/exchange-memory-attribution` — speaker labels in exchange memories
- `feat/recall-replay-cache` — one summarizer pass serving several modes
- `run/darwin-ablation` — integration branch; **what actually ran**

## Order of operations

```bash
python pipeline/split_all.py         # letters -> candidates
python pipeline/make_batches.py      # -> batches + planted controls
#   (adjudicate each batch -> verdicts/)
python pipeline/score_verdicts.py    # -> final-verdicts.json
python pipeline/emit_split.py        # -> darwin_split/
cd darwin_split && raft chunk && raft embed
bash pipeline/run_arms.sh summary source register     # datasets
#   then on bigmac: run_training.sh, run_eval.sh
```

## Funky things, so nobody re-derives them

**Qwen3.5-2B**

- The checkpoint stores text weights as `model.language_model.*`; the text-only
  class expects `model.*`. A static key comparison reports **all 322 expected
  keys missing** and `_checkpoint_conversion_mapping` is `None`.
  `from_pretrained` remaps anyway — but this is the shape of bug that trains a
  randomly-initialised model to convergence on noise, so **verify
  functionally** (ask the base model a question) rather than trusting a loader.
- `AutoModelForCausalLM` yields `Qwen3_5ForCausalLM` and **drops the vision
  tower entirely** — no need to exclude it from LoRA targets.
- **The conventional LoRA target list is wrong here.** Only 6 of 24 layers are
  full attention; 18 are Gated DeltaNet linear attention. q/k/v/o + MLP alone
  silently leaves three-quarters of the sequence mixing untrained. Use:
  `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj,in_proj_qkv,in_proj_z,in_proj_b,in_proj_a,out_proj`
- `tie_word_embeddings: true`, no separate `lm_head` — so PEFT's `StopIteration`
  on Talkie's `nn.Parameter` head cannot recur.
- `causal_conv1d` and `flash-linear-attention` are CUDA-only, so linear
  attention runs reference PyTorch on MPS. Correct, slower, unavoidable.

**Chat templates**

- **`enable_thinking=True` is required.** Without it the template emits an
  already-closed empty `<think></think>` and the persona answers with no
  reasoning — silently, since the output still parses. This made three arms
  look like they never think.
- With thinking enabled, `<think>` is in the *prompt*, so only `</think>`
  appears in the output. Split on the closing tag; searching for the opening
  one finds nothing.
- `apply_chat_template(tokenize=True)` returns a `BatchEncoding`, so `len()`
  gives 2 (the key count), not a token count.

**raft / opbdh**

- bigmac's raft and opbdh are **site-package installs, not git repos**, and
  predate `lora_target_modules`. Hence the standalone `train_arm.py`. Do not
  edit bigmac's copies.
- raft is an **editable install** on this machine: `git checkout` of another
  branch mid-run changes what the next subprocess imports. Do not switch
  branches while a generation or training run is in flight.
- `ft:gen` **writes each processed exchange back into the chroma store**, so a
  finished run leaves ~232 extra retrievable documents behind. Reset the store
  from a pristine snapshot between arms or they retrieve against different
  corpora. This is also why exchange memories were 63% of retrievals in
  `darwin_thinking` despite being 10% of the store.
- `--retry-rate-limits` is **off by default**; without it a 429 silently drops
  that memory. Embeddings had no retry at all until `feat/rate-limit-retry`,
  and a lost embedding kills the whole run rather than one recollection.
- `ask_question` uses `datetime.now()` as the persona's date, so a live serve
  tells Darwin it is 2026. Arguably a bug; the eval overrides it.
- `transformers` 5.x dropped `warmup_ratio` and `use_mps_device`.
- Piping training output through `grep` block-buffers it: logs stay empty until
  the process exits. Use `--line-buffered`, or check liveness with `ps`.

**Reading logs**

- Talkie-Darwin's `train_loss: 25.8` is **not** a failure signal — it is
  inconsistent with the `mean_token_accuracy: 0.43–0.46` beside it and appears
  unnormalised. Judge by token accuracy.

## The measurement lesson

Five metrics in this project have been confidently wrong: the register
classifier (scored *real Darwin* 0/10 period), the SAME adjudication controls
(5/5 "failures" were real links the splitter missed), the misattribution judge
(flagged verbatim Darwin as misattributed), the modernism counter (passed
contraction-free modern pastiche), and a wording ranking that was pure sampling
noise — the same prompt on the same inputs scored 79%, 85% and 87% across three
runs.

**Every metric gets a ground-truth control arm before its numbers are used, and
a repeat cell before anything is ranked.** Source mode is a convenient control
for grounding checks: it is verbatim by construction, so any judge that
penalises it is miscalibrated.

## The other documents

- **`OUTSTANDING.md`** — the eval plan for the three arms, temporal fidelity,
  Talkie, persona-as-summariser, the density hypothesis, GRPO, bash.org
- **`RECALL_MODE_ABLATION.md`** — every measurement, in order, with the
  retractions left in place
- **`QWEN35_2B_TRAINING.md`** — the verified training setup
- **`darwin_split_README.md`** — the corpus itself (also copied into the project)

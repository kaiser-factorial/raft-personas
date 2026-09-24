# Training the ablation arms on Qwen3.5-2B — verified setup

Everything below was checked on bigmac, not inferred from model cards.

## Why this model

The full Darwin run was trained from **Qwen3.8-27B**, whose merged config is
`Qwen3_5ForCausalLM` — the *qwen3_5* architecture. Qwen3.5-2B is the same
lineage at probe scale. Qwen3-1.7B and Qwen3-4B are the *older* Qwen3
architecture and would not transfer as well.

## What works, confirmed

| check | result |
|---|---|
| `transformers` support | 5.17.0 supports `qwen3_5` natively — **no `trust_remote_code`** |
| model class | `AutoModelForCausalLM` yields `Qwen3_5ForCausalLM`, text-only |
| vision tower | **dropped entirely** — 0 vision modules in the loaded model |
| weights load | 320/320 text tensors; generates coherent text |
| LoRA attaches | 16,819,200 trainable (0.89% of 1.9B) |
| MPS forward+backward | works; loss 3.99 → 0.51 → 0.23 over three steps |
| speed | ~1.3 s per step at batch 2 x 256 tokens |

## LoRA target modules

The text tower is hybrid, so the conventional q/k/v/o + MLP list is not enough:
18 of 24 layers are Gated DeltaNet linear-attention and would go untrained.

```
q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj,in_proj_qkv,in_proj_z,in_proj_b,in_proj_a,out_proj
```

Verified match counts: `q/k/v/o_proj` 6 each (the full-attention layers),
`in_proj_*` and `out_proj` 18 each (linear attention), MLP 24 each. Zero hit
any vision module.

`conv1d` is deliberately excluded — a small depthwise conv, and PEFT support
for it is not worth the risk here.

## Two traps avoided

**The checkpoint's keys do not match the class.** Weights are stored as
`model.language_model.*` (plus `model.visual.*` and an `mtp.*` head), while
`Qwen3_5ForCausalLM` expects `model.*`. A static key comparison shows **all 322
expected keys missing**. `from_pretrained` remaps them anyway — but this is the
shape of failure that trains a randomly initialised model to convergence on
noise, so it was confirmed functionally: the base model answers "who was
Charles Darwin?" correctly before any training.

**No separate `lm_head`.** `tie_word_embeddings: true`, so the `nn.Parameter`
that caused PEFT's `StopIteration` on Talkie does not arise here.

## Known cost

`causal_conv1d` and `flash-linear-attention` are CUDA-only and absent, so the
linear-attention path falls back to reference PyTorch — correct but slower.
Nothing to do about it on Apple silicon; it is priced into the timings above.

## Rough budget

At ~400 tokens/s, one epoch over 232 examples is single-digit minutes, so three
arms x a few epochs is well under two hours — far cheaper than the 13B Talkie
run. Sequence length is the variable to watch: letter-mode examples run to
~3,200 tokens against the split pairs' few hundred.

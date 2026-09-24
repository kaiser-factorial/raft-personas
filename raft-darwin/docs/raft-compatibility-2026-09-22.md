# RAFT compatibility with the Darwin workflow

Checked 22 September 2026 against `/Users/corinakaiser/Projects/raft`, branch `fix/serve-sampling-and-lora-targets`, commit `4dea6cb0060dfc54257645e5e132a8ac80232bc6`. **The collection and export direction remains valid.** The recent changes add training controls and improve serving behavior; they do not require reformatting the Darwin letters.

The local `/opt/anaconda3/bin/raft` launcher resolves through `/opt/anaconda3/bin/python3` to this checkout via an editable installation. Both the package and distribution still report `3.1.0`. Record the resolved source path and Git commit as well as the version label for each run. This check does not identify what code an already-running process or another machine has loaded.

## What remains the same

The ten RAFT files with current counterparts in the [September 16 implementation audit](../reports/raft-prep/implementation.json) all match historical commit `8ad9fd2` at that baseline. Comparing that commit with the current checkout isolates two subsequent commits: `5756718` and `4dea6cb`. The [new evidence record](../reports/raft-prep/compatibility-2026-09-22.json) records file hashes and check results.

- Keep the DCP-specific fetching, complete-source review, backward conversation matching and independent adjudication. RAFT's generic source fetcher does not replace that historical evidence work; `sources.py` is unchanged from the audited version.
- Keep direct transcript JSON writes, gapless numbering and one demonstrably dated Darwin response/section per transcript. The importer still drops `context`; generation still requires `date` and `url` and stops at the first missing transcript. See [transcript import](/Users/corinakaiser/Projects/raft/src/raft/convo_structurer.py:264) and [generation](/Users/corinakaiser/Projects/raft/src/raft/generate_finetune.py:42).
- Keep genuine incoming → Darwin replies as conversations and eligible unpaired Darwin prose as grounding. Incoming-only knowledge remains separately attributed research evidence. Nothing in these changes adds a mechanism for treating incoming prose as Darwin-authored grounding.
- The dated retrieval query still uses a strict earlier-than comparison when a transcript date and dated collection are present. Missing dates, shared transcript dates and duplicate source content still need the existing safeguards. See [retrieval](/Users/corinakaiser/Projects/raft/src/raft/memories.py:179).

## Changes to training and serving guidance

| Current change | Consequence for the next session |
|---|---|
| Persona replies now explicitly request `temperature=0.7`, `top_p=0.9` and `max_tokens=1400`. Overrides are `RAFT_TEMPERATURE`, `RAFT_TOP_P` and `RAFT_MAX_ANSWER_TOKENS`. | Record sampling settings alongside evaluation results and check response truncation. These control generated replies; they do not alter the historical targets or demonstrate that repetition is solved for a particular model. [Code](/Users/corinakaiser/Projects/raft/src/raft/memories.py:54). |
| `--lora-target-modules` now reaches the OPBDH training recipe. | Explicit architecture-appropriate module selection can be passed through RAFT when needed. This changes training configuration, not conversation preparation. Parsing and field routing were checked; a real model's module names were not validated. [Code](/Users/corinakaiser/Projects/raft/src/raft/hf_finetune.py:232). |
| Helper/embedding failures identify their model and endpoint, repeated summary failures are grouped, and serving catches per-turn failures. | Use the diagnostics to check endpoint configuration. A completed command or continuing chat does not prove successful grounding: failed summaries can still be skipped. [Helper diagnostics](/Users/corinakaiser/Projects/raft/src/raft/prompt_manager.py:38), [summary handling](/Users/corinakaiser/Projects/raft/src/raft/memories.py:280), [serving](/Users/corinakaiser/Projects/raft/src/raft/serve.py:117). |

The existing endpoint separation should be explicit in any training-to-serving handoff: persona chat uses `OPENAI_BASE_URL`/`OPENAI_API_KEY` and the selected model; embeddings use `RAFT_EMBEDDING_BASE_URL`/`RAFT_EMBEDDING_API_KEY`/`RAFT_EMBEDDING_MODEL`; summarization and reasoning use `RAFT_LLM_BASE_URL`/`RAFT_LLM_API_KEY`/`RAFT_LLM_MODEL`, with `RAFT_REASONING_MODEL` as a reasoning-model override. Unset helper/embedding URL or key settings fall back through the OpenAI SDK to the general OpenAI environment settings. Configure these before starting the process, especially with a chat-only local server. Record model names and endpoint roles, never credentials.

`raft serve` is a client of an inference endpoint. A local HF adapter still needs a suitable serving setup; the interactive menu's `ready` label alone does not verify one. See the [adapter guard](/Users/corinakaiser/Projects/raft/src/raft/serve.py:102) and [phase label](/Users/corinakaiser/Projects/raft/src/raft/flows.py:72). These are existing operational boundaries, not new collection requirements.

## Historical persona date remains a separate decision

The dated training-example path does not automatically create an “as of 1846” chat mode. Default [serving](/Users/corinakaiser/Projects/raft/src/raft/serve.py:110) constructs the memory manager with empty date metadata, and [the answer prompt](/Users/corinakaiser/Projects/raft/src/raft/memories.py:441) uses today's date. Consequently the current default serving path supplies no historical retrieval cutoff. This behavior predates the two new commits.

For an earlier-date persona, choose the intended date, bound the training material and retrieval store accordingly, and implement or verify a serving path that passes that historical date to both retrieval and the persona prompt. A retrieval cutoff cannot remove later knowledge already learned in model weights. Evaluate historical fidelity separately; neither the corpus dates nor these offline checks establish it. The collected temporal evidence preserves the options described in the [project objective](collection-workflow.md).

## Verification and preservation

Eight existing focused tests passed with outbound connections blocked and temporary synthetic projects. They cover transcript context, dated prompts, strict query-before-store behavior, sampling parameters, LoRA flag routing, failed-summary handling, grouped warnings and endpoint separation. The original [offline format fixture](../reports/raft-prep/fixtures/verify_no_network_fixture.py) also passed against this checkout, reconfirming importer context loss, mandatory metadata keys, gap/filename ordering, previous-answer handling, bounded fetch windows and link deduplication.

These checks mock embeddings and model calls; they do not validate a live Chroma query, inference endpoint, tokenizer, training run or persona quality. The user's ongoing training was not inspected or altered. The old export manifest and its pinned policies remain historical records; this additive note records compatibility with the newer implementation without replacing their hashes.

#!/usr/bin/env bash
# Generate the three recall-mode training sets from darwin_split.
#
#   arm 1  summary   the summarizer's paraphrase (raft's historical behaviour)
#   arm 2  source    the quoted passage, verbatim from the document
#   arm 3  register  a paraphrase asked for in the author's own words
#
# Arms 1 and 2 come from ONE pass: arm 1 records every summarizer reply and
# arm 2 replays it, reading the SOURCE of the same reply rather than its
# RECALL. They therefore differ in wording only -- never in which memories
# survived, which is the variable the ablation is trying to hold still. Arm 3
# asks the model something different, so it must call for itself.
#
# Two things have to be reset between arms or the comparison is worthless:
#
#   the embedding store   ft:gen stores each processed exchange back into the
#                         collection as a retrievable memory, so a completed
#                         arm leaves ~232 extra documents behind and the next
#                         arm retrieves against a different corpus.
#   the output file       ft:gen always writes conversations/finetune.json.
#
# --retry-rate-limits is not optional here. Without it a 429 makes ft:gen drop
# that memory ("memory summary failed, skipping it"), so the cache arm 1 writes
# would have holes, arm 2 could not replay them, and the arms would differ in
# which memories they carry -- silently, and for a reason unrelated to wording.
#
set -euo pipefail

PROJECT="${PROJECT:-/Users/corinakaiser/Projects/personas/raft-darwin/darwin_split}"
OUT="${OUT:-/Users/corinakaiser/Projects/personas/raft-darwin/reports/paragraph-split/arms}"
PRISTINE="$PROJECT/corpus/chroma.pristine"
CACHE="$OUT/recall-cache.json"

export RAFT_LLM_MODEL="${RAFT_LLM_MODEL:-gpt-4o}"
mkdir -p "$OUT"

if [ ! -d "$PRISTINE" ]; then
    echo "==> snapshotting the freshly embedded store"
    cp -R "$PROJECT/corpus/chroma" "$PRISTINE"
fi

reset_store() {
    rm -rf "$PROJECT/corpus/chroma"
    cp -R "$PRISTINE" "$PROJECT/corpus/chroma"
}

run_arm() {
    local name="$1" mode="$2" replay="$3"
    # Resumable: an arm that already produced its file is left alone, so a run
    # interrupted partway (exhausted credits, a killed shell) is restarted with
    # the same command and only pays for what is missing. Delete the file to
    # force a rebuild.
    if [ -s "$OUT/finetune-$name.json" ]; then
        echo
        echo "==> arm: $name -- already built, skipping ($OUT/finetune-$name.json)"
        return 0
    fi
    if [ "$replay" = "1" ] && [ ! -s "$CACHE" ]; then
        echo "ABORT: arm $name replays the cache, but $CACHE is missing or empty." >&2
        echo "       Run the summary arm first -- it is what records the replies." >&2
        return 1
    fi
    echo
    echo "=============================================================="
    echo "==> arm: $name   (RAFT_RECALL_MODE=$mode, replay=$replay)"
    echo "=============================================================="
    reset_store
    rm -f "$PROJECT/conversations/finetune.json"
    (
        cd "$PROJECT"
        RAFT_RECALL_MODE="$mode" \
        RAFT_RECALL_CACHE="$CACHE" \
        RAFT_RECALL_REPLAY="$replay" \
        raft ft:gen --thinking --generic --no-interactive --retry-rate-limits
    )
    cp "$PROJECT/conversations/finetune.json" "$OUT/finetune-$name.json"
    echo "==> wrote $OUT/finetune-$name.json"
}

# Order matters: the summary arm fills the cache that the source arm replays.
# Both are skipped if already built, so this is safe to re-run.
run_arm summary  summary  0
run_arm source   source   1
run_arm register register 0

reset_store
echo
echo "==> done. store reset to its pristine state."
python3 - "$OUT" <<'PY'
import json, sys, os, collections
out = sys.argv[1]
print(f"\n{'arm':10s} {'examples':>9s} {'with memories':>14s} {'mean memory words':>18s}")
for arm in ("summary", "source", "register"):
    path = os.path.join(out, f"finetune-{arm}.json")
    if not os.path.exists(path):
        continue
    rows = [r["example"] for r in json.load(open(path)) if "example" in r]
    mem = [r.get("similar_memories", "") for r in rows]
    got = [m for m in mem if m.strip()]
    avg = sum(len(m.split()) for m in got) / len(got) if got else 0
    print(f"{arm:10s} {len(rows):9d} {len(got):9d}/{len(rows):<4d} {avg:18.0f}")
PY

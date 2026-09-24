"""Shared project/paths resolution for the paragraph-split pipeline stages.

Every stage takes the same three arguments:

  --src   the RAFT project whose letters are being split   (default darwin_thinking)
  --dst   the RAFT project to emit                         (default <src minus _thinking>_split)
  --work  where candidates, batches, verdicts and provenance live

Bare names resolve under raft-darwin/; absolute paths are used as given. The
defaults reproduce the original darwin_thinking -> darwin_split run exactly.
For any other --src the work directory defaults to `reports/paragraph-split-<src>`
so a new corpus can never resume from, append to, or overwrite another corpus's
candidates.jsonl / verdicts (split_all.py resumes from whatever it finds there).
"""
import argparse
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

ORIGINAL_SRC = "darwin_thinking"
ORIGINAL_DST = "darwin_split"
ORIGINAL_WORK = "reports/paragraph-split"


def add_project_args(ap):
    ap.add_argument("--src", default=ORIGINAL_SRC,
                    help="source RAFT project (dir with conversations/ and corpus/); default %(default)s")
    ap.add_argument("--dst", default=None,
                    help=f"RAFT project to emit; default {ORIGINAL_DST} for the original source, "
                         "otherwise <src>_split")
    ap.add_argument("--work", default=None,
                    help=f"working dir; default {ORIGINAL_WORK} for the original source, "
                         "otherwise reports/paragraph-split-<src>")


def resolve(args):
    """Fill in defaults and make paths absolute. Adds src_name/dst_name (basenames)."""
    src = os.path.normpath(os.path.join(ROOT, args.src))
    src_name = os.path.basename(src)
    original = src_name == ORIGINAL_SRC
    dst = args.dst or (ORIGINAL_DST if original else f"{src_name}_split")
    work = args.work or (ORIGINAL_WORK if original else f"reports/paragraph-split-{src_name}")
    args.src = src
    args.dst = os.path.normpath(os.path.join(ROOT, dst))
    args.work = os.path.normpath(os.path.join(ROOT, work))
    args.src_name = src_name
    args.dst_name = os.path.basename(args.dst)
    if not os.path.isdir(os.path.join(args.src, "conversations")):
        raise SystemExit(f"--src {args.src} has no conversations/ directory")
    return args


def paras(text):
    """Paragraphs of >=8 words, whitespace-normalised. The one definition every stage shares."""
    import re
    return [" ".join(p.split()) for p in re.split(r"\n\s*\n", text) if len(p.split()) >= 8]

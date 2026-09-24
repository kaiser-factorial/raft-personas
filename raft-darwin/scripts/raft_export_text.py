"""Source-pinned text projection. Historical scope decisions live in the plans.

Canonical offsets refer to the original extraction, never the cleaned string.
Only unchanged character boundaries may be projected through markup repairs.
"""
from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

import raft_render_text as R

ROOT = Path(__file__).resolve().parents[1]


def audit():
    return dict(excluded_nodes=0, visual_nodes=0, visual_locators=[], mathml_nodes=0,
                fraction_nodes=0, table_nodes=0, list_nodes=0, text_transformations=0, holds=[])


@lru_cache(maxsize=64)
def source_tree(path, sha):
    path = ROOT / path
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == sha, f'Source changed: {path}'
    parser = R.TreeParser()
    parser.feed(raw.decode('utf-8'))
    nodes = [n for body in R.find_bodies(parser.root) for n in R._paragraphs(body)]
    return parser.root, nodes


def clean_node(node):
    a = audit()
    text = re.sub(r'[ \t]+', ' ', R._text(node, a)).strip()
    for n in [node, *R.descendants(node, lambda n: True)]:
        if R.excluded(n): continue
        if n.tag in ('del', 's', 'strike') or R.classes(n) & {'deleted', 'deletion', 'cancelled', 'canceled', 'strikethrough'}:
            a['holds'].append({'kind': 'unresolved_cancellation', 'tag': n.tag, 'attrs': n.attrs})
    return text, a


def projected_slice(original, rendered, start, end):
    assert 0 <= start < end <= len(original)
    if original == rendered: return rendered[start:end], []
    opcodes = SequenceMatcher(None, original, rendered, autojunk=False).get_opcodes()
    changes = [{'old_start': a, 'old_end': b, 'original': original[a:b],
                'rendered': rendered[c:d], 'kind': 'source_markup_projection'}
               for tag, a, b, c, d in opcodes if tag != 'equal' and b >= start and a <= end]

    # Canonical extraction collapses all whitespace, whereas rendered source
    # retains nonbreaking spaces and line breaks. If these are the ONLY
    # differences, map character positions directly, without fuzzy alignment.
    normalized, positions = [], []
    for match in re.finditer(r'\s+|\S+', rendered):
        token=match.group()
        if token.isspace():
            normalized.append(' '); positions.append((match.start(),match.end()))
        else:
            normalized.extend(token)
            positions.extend((i,i+1) for i in range(match.start(),match.end()))
    if ''.join(normalized)==original:
        return rendered[positions[start][0]:positions[end-1][1]], changes

    def boundary(pos, opening):
        if pos == 0: return 0
        if pos == len(original): return len(rendered)
        # Character on the inside of the selected range must be unchanged.
        for tag, a, b, c, d in opcodes:
            if tag == 'equal' and (a <= pos < b if opening else a < pos <= b):
                anchor = original[a:b]
                if len(anchor) < 12 or original.count(anchor) != 1 or rendered.count(anchor) != 1:
                    raise ValueError(f'Boundary {pos} has no unique unchanged source anchor')
                return c + pos - a
        raise ValueError(f'Boundary {pos} falls inside a markup transformation')

    lo, hi = boundary(start, True), boundary(end, False)
    return rendered[lo:hi], changes


def text_holds(text):
    out = []
    for marker in ('QQQQ', '[SYMBOL', '[GREATER THAN]', '[UNRESOLVED', '[LARGER SPACE HERE]', '[reverse question mark]', 'conseacute;', '*S2', '*S 2'):
        if marker in text:
            out.append({'kind': 'unresolved_source_artifact', 'marker': marker})
    # "ramme" is an extraction fragment after broken layout. Real words such
    # as programme, crammed and trammels are not corruption markers.
    if re.search(r'ramme(?![a-z])', re.sub(r'\b(?:[Pp]rogramme|[Cc]rammed|[Tt]rammels)\b','',text)):
        out.append({'kind':'unresolved_source_artifact','marker':'ramme'})
    for match in re.finditer(r'\b[A-Za-z]{2,}-\s+[A-Za-z]{2,}\b', text):
        if match.group() in ('mono- or', 'half- mountain', 'lava- streams'):
            continue  # Source preserves a normal prefix or compound.
        out.append({'kind': 'possible_line_wrap', 'literal': match.group()})
    for match in re.finditer(r'\[(?:From |To |Enclosure|Autograph |Letter |The |This |continued|Continued|Here |See |Copy |Extract)', text):
        out.append({'kind': 'possible_editorial_prose', 'literal': text[max(0,match.start()-35):match.start()+125]})
    if re.search(r'(?:\[[^\]]{0,60}|⟨[^⟩]{0,60})\billeg\b', text, re.I) or '[?]' in text:
        out.append({'kind':'unresolved_transcription_reading', 'reason':'Illegible or explicitly uncertain reading; no invented completion.'})
    if re.search(r'Go to (?:the )?(?:\d+(?:st|nd|rd|th)?|first|next|previous) page', text, re.I):
        out.append({'kind': 'navigation_text'})
    return out


def render_spans(source, spans):
    root, nodes = source_tree(source['source']['path'], source['source']['sha256'])
    blocks, holds = [], []
    for s in spans:
        n = s['paragraph']
        canonical = source['paragraphs'][n-1]['text']
        assert s['source_sha256'] == source['source']['sha256']
        assert canonical[s['start']:s['end']] == s['original_excerpt']
        baseline = re.sub(r'\s+', ' ', ''.join(R._raw_text_nodes(nodes[n-1]))).strip()
        assert baseline == canonical, (source['id'], n, 'canonical source mismatch')
        rendered, a = clean_node(nodes[n-1])
        try:
            text, transformations = projected_slice(canonical, rendered, s['start'], s['end'])
        except ValueError as exc:
            holds.append({'kind': 'ambiguous_scope_projection', 'paragraph': n, 'reason': str(exc)})
            continue
        text = text.strip()
        if a['visual_nodes'] or any(x['kind'] == 'unresolved_cancellation' for x in a['holds']):
            holds.extend({**x, 'paragraph': n} for x in a['holds'])
        holds.extend({**x, 'paragraph': n} for x in text_holds(text))
        blocks.append({'paragraph': n, 'text': text, 'scope': s,
                       'transformations': transformations, 'source_audit': a})
    content = '\n\n'.join(b['text'] for b in blocks if b['text'])
    if not content: holds.append({'kind': 'empty_content'})
    return {'content': content, 'blocks': blocks, 'holds': holds,
            'source': source['source'], 'verified_canonical_spans': len(blocks)}


def render_supplement(source, layer, ordinal=1, drop_last=False):
    root, _ = source_tree(source['source']['path'], source['source']['sha256'])
    nodes = list(R.descendants(root, lambda n: layer in R.classes(n)))
    assert 1 <= ordinal <= len(nodes)
    node = nodes[ordinal-1]
    # Explicitly admit this one authorial wrapper, never other supplemental nodes.
    selected = [c for c in node.children if isinstance(c, R.Node) and c.tag not in ('h1','h2','h3','h4')]
    if drop_last: selected = selected[:-1]
    blocks, holds = [], []
    for n, child in enumerate(selected, 1):
        text, a = clean_node(child)
        text = text.strip()
        if not text: continue
        blocks.append({'layer_block': n, 'text': text, 'source_audit': a})
        holds.extend(a['holds']); holds.extend(text_holds(text))
    content = '\n\n'.join(b['text'] for b in blocks)
    if not content: holds.append({'kind':'empty_supplement'})
    return {'content': content, 'blocks': blocks, 'holds': holds, 'source': source['source'],
            'layer_scope': {'class': layer, 'ordinal': ordinal, 'exclude_last_block': drop_last}}

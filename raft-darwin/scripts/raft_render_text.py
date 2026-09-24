#!/usr/bin/env python3
"""Deterministic, local-only source text renderer for future RAFT export.

The renderer projects selected retained body blocks from a preserved DCP HTML
snapshot.  It intentionally does not decide historical eligibility.  Content
is returned separately from provenance and an audit; ambiguous artifacts yield
holds rather than guessed prose.
"""
from __future__ import annotations
import argparse, hashlib, html, json, re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

EXCLUDED_CLASSES = {
    "footnote", "footnotes", "bibliography", "annotation", "annotations",
    "cdnote", "editorial", "navigation", "header", "dateline", "stamp",
    "pagination", "page-navigation", "source-note", "salute", "supplemental",
}
EXCLUDED_IDS = {"footnotes", "bibliography", "cdnotes", "navigation", "breadcrumb"}
BLOCK_TAGS = {"p", "li", "tr", "div"}

@dataclass
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)
    parent: "Node | None" = None

class TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("__root__")
        self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        n = Node(tag.lower(), dict(attrs), parent=self.stack[-1]); self.stack[-1].children.append(n)
        if tag.lower() not in {"br", "img", "hr", "meta", "link", "input", "source", "wbr"}:
            self.stack.append(n)
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs); self.handle_endtag(tag)
    def handle_endtag(self, tag):
        tag = tag.lower()
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]; return
    def handle_data(self, data): self.stack[-1].children.append(data)
    def handle_entityref(self, name): self.handle_data(html.unescape("&"+name+";"))
    def handle_charref(self, name): self.handle_data(html.unescape("&#"+name+";"))

def classes(n: Node) -> set[str]: return set(n.attrs.get("class", "").lower().split())
def excluded(n: Node) -> bool:
    return bool(classes(n) & EXCLUDED_CLASSES or n.attrs.get("id", "").lower() in EXCLUDED_IDS)
def descendants(n: Node, pred):
    for c in n.children:
        if isinstance(c, Node):
            if pred(c): yield c
            yield from descendants(c, pred)
def find_body(root: Node) -> Node:
    letter = next(descendants(root, lambda n: n.attrs.get("id") == "letter"), None)
    if letter is None: raise ValueError("preserved HTML has no #letter container")
    body = next(descendants(letter, lambda n: "body-content" in classes(n)), None)
    if body is None: raise ValueError("preserved HTML has no .body-content")
    return body

def find_bodies(root: Node) -> list[Node]:
    """Return every retained body-content container, matching period_review."""
    letter = next(descendants(root, lambda n: n.attrs.get("id") == "letter"), None)
    if letter is None: raise ValueError("preserved HTML has no #letter container")
    bodies = [n for n in descendants(letter, lambda n: "body-content" in classes(n))]
    if not bodies: raise ValueError("preserved HTML has no .body-content")
    return bodies

def _text(node: Node, audit: dict, in_body=True) -> str:
    if excluded(node):
        audit["excluded_nodes"] += 1; return ""
    tag=node.tag
    if tag in {"script", "style", "noscript"}: return ""
    if tag == "br": return "\n"
    if tag == "img":
        audit["visual_nodes"] += 1
        audit["visual_locators"].append(node.attrs.get("src", "[image-without-src]"))
        audit["holds"].append({"kind":"visual_dependency","locator":node.attrs.get("src", "[image-without-src]"),"reason":"image content cannot be represented as text without an explicit source-scoped decision"})
        return ""
    if tag == "math":
        audit["mathml_nodes"] += 1
        audit["text_transformations"] += 1
        return "".join(_text(c,audit) if isinstance(c,Node) else c for c in node.children)
    if tag == "mfrac":
        audit["fraction_nodes"] += 1
        kids=[c for c in node.children if isinstance(c,Node)]
        if len(kids)!=2:
            audit["holds"].append({"kind":"malformed_mfrac","reason":"expected numerator and denominator"}); return "[UNRESOLVED FRACTION]"
        numerator, denominator = _text(kids[0],audit).strip(), _text(kids[1],audit).strip()
        vulgar = {("1","2"):"½",("1","4"):"¼",("3","4"):"¾",
                  ("1","3"):"⅓",("2","3"):"⅔",("1","5"):"⅕",
                  ("2","5"):"⅖",("3","5"):"⅗",("4","5"):"⅘",
                  ("1","6"):"⅙",("5","6"):"⅚",("1","8"):"⅛",
                  ("3","8"):"⅜",("5","8"):"⅝",("7","8"):"⅞"}
        return vulgar.get((numerator, denominator), f"({numerator}/{denominator})")
    if tag in {"msup", "msub"}:
        audit["text_transformations"] += 1
        kids=[_text(c,audit) if isinstance(c,Node) else c for c in node.children]
        supers = str.maketrans("0123456789+-=()nix", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣ")
        subs = str.maketrans("0123456789+-=()nix", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₙᵢₓ")
        return (kids[0] if kids else "") + ("".join(kids[1:]).translate(supers if tag == "msup" else subs) if len(kids)>1 else "")
    if tag == "sup":
        audit["text_transformations"] += 1
        value="".join(_text(c,audit) if isinstance(c,Node) else c for c in node.children)
        supers = str.maketrans("0123456789+-=()nix", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣ")
        return value.translate(supers)
    if tag == "sub":
        audit["text_transformations"] += 1
        value="".join(_text(c,audit) if isinstance(c,Node) else c for c in node.children)
        subs = str.maketrans("0123456789+-=()nix", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₙᵢₓ")
        return value.translate(subs)
    if tag == "table": audit["table_nodes"] += 1; audit["text_transformations"] += 1
    if tag in {"td", "th"}: return "".join(_text(c,audit) if isinstance(c,Node) else c for c in node.children) + "\t"
    if tag in {"ul","ol"}: audit["list_nodes"] += 1; audit["text_transformations"] += 1
    out=[]
    for c in node.children: out.append(_text(c,audit) if isinstance(c,Node) else c)
    value="".join(out)
    if tag == "tr": value=" | ".join(x.strip() for x in value.split("\t") if x.strip())+"\n"
    if tag == "li": value="- "+value.strip()+"\n"
    return value

def _paragraphs(body: Node):
    """Mirror search_body_dates.parse_page's retained block selection."""
    def usable(n):
        if n.tag not in BLOCK_TAGS or excluded(n): return False
        if n.tag == "div" and any(c.tag in {"p", "div"} for c in descendants(n, lambda c: True)):
            return False
        parent=n.parent
        while parent is not None and parent is not body:
            if excluded(parent) or parent.tag in BLOCK_TAGS: return False
            parent=parent.parent
        return True
    candidates=list(descendants(body, usable))
    if not candidates: return []
    # Existing extraction falls back to one whole body block when block
    # extraction would lose non-whitespace text (e.g. unusual layouts).
    whole=" ".join(x for x in _raw_text_nodes(body) if x).split()
    selected=" ".join(sum((_raw_text_nodes(n) for n in candidates), [])).split()
    blocks=[body] if "".join(whole) != "".join(selected) else candidates
    return [n for n in blocks if re.search(r"\w", " ".join(_raw_text_nodes(n)))]

def _raw_text_nodes(node: Node):
    if excluded(node): return []
    out=[]
    for c in node.children:
        if isinstance(c,Node): out.extend(_raw_text_nodes(c))
        else: out.append(c)
    return out

def render_html(path: str | Path, paragraphs: list[int] | None=None,
                codepoint_scopes: dict[int, list[int]] | None=None) -> dict:
    """Render selected retained body paragraphs; provenance and holds stay outside content."""
    path=Path(path); raw=path.read_bytes(); parser=TreeParser(); parser.feed(raw.decode("utf-8"))
    nodes=[]
    for body in find_bodies(parser.root): nodes.extend(_paragraphs(body))
    wanted=set(paragraphs) if paragraphs is not None else set(range(1,len(nodes)+1))
    if any(i<1 or i>len(nodes) for i in wanted): raise ValueError("paragraph scope is outside retained body")
    blocks=[]; combined=[]; audit={"excluded_nodes":0,"visual_nodes":0,"visual_locators":[],"mathml_nodes":0,"fraction_nodes":0,"table_nodes":0,"list_nodes":0,"text_transformations":0,"holds":[]}
    for i,n in enumerate(nodes,1):
        if i not in wanted: continue
        a={"excluded_nodes":0,"visual_nodes":0,"visual_locators":[],"mathml_nodes":0,"fraction_nodes":0,"table_nodes":0,"list_nodes":0,"text_transformations":0,"holds":[]}
        text=re.sub(r"[ \t]+", " ", _text(n,a)).strip()
        baseline=re.sub(r"\s+", " ", "".join(_raw_text_nodes(n))).strip()
        if codepoint_scopes and i in codepoint_scopes:
            start,end=codepoint_scopes[i]
            if not (0<=start<=end<=len(baseline)): raise ValueError(f"invalid codepoint scope for paragraph {i}")
            if a["text_transformations"] or a["visual_nodes"] or text != baseline:
                audit["holds"].append({"kind":"non_lossless_scope","paragraph":i,"reason":"code-point offsets refer to repository extraction before markup rendering; provide a lossless mapping or hold"})
            else: text=text[start:end]
        blocks.append({"paragraph":i,"text":text})
        for k,v in a.items():
            if isinstance(v,int): audit[k]+=v
            elif isinstance(v,list): audit[k].extend(x for x in v if x not in audit[k])
        combined.append(text)
    joined="\n\n".join(x["text"] for x in blocks if x["text"])
    suspicious=[]
    for marker in ("QQQQ", "[SYMBOL]", "[UNRESOLVED FRACTION]", "[GREATER THAN]", "*S2"):
        if marker in joined: suspicious.append(marker)
    if suspicious: audit["holds"].append({"kind":"source_artifact","markers":suspicious,"reason":"preserve and resolve before export"})
    if "Go to 1st page" in joined:
        audit["holds"].append({"kind":"navigation_text","reason":"cover/navigation text requires source-verified exclusion; it is not letter prose"})
    if re.search(r"\b[A-Za-z]{2,}-\s+[A-Za-z]{2,}\b", joined):
        audit["holds"].append({"kind":"possible_joined_word_artifact","reason":"hyphenated word spacing requires source or authoritative witness; do not silently join or delete it"})
    return {"content":joined,"blocks":blocks,"provenance":{"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"paragraph_count":len(nodes)},"audit":audit}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("html_path"); ap.add_argument("--paragraph",type=int,action="append"); ap.add_argument("--json",action="store_true")
    args=ap.parse_args(); result=render_html(args.html_path,args.paragraph)
    print(json.dumps(result,ensure_ascii=False,indent=2) if args.json else result["content"])
if __name__ == "__main__": main()

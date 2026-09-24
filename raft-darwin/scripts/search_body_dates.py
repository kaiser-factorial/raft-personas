"""Search transcribed letter bodies; retain offsets, context, and provenance."""

import copy
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
RAW_MANIFEST = ROOT / "data/raw/dcp/body-date-search-37-337/manifest.json"
REPORT = ROOT / "reports/body-date-search-37-337"
MONTH = (r"(?:Jan(?:uary|ry|y)?|Feb(?:ruary|ry|y)?|Mar(?:ch)?|Apr(?:il)?|May|"
         r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust|st)?|Sept?(?:ember|emb|r)?|"
         r"Oct(?:ober|obr|r)?|Nov(?:ember|emb|r)?|Dec(?:ember|emb|r)?)[.:]?")
DAY = r"(?:3[01]|[12]\d|[1-9])(?:\.?\s*(?:st|nd|rd|th|d))?\.?"
YEAR = r"(?:1[5-8]\d{2})"
WEEKDAY = r"(?:Mon|Tues?|Wednes|Thurs?|Fri|Satur|Sun)day"
NUMBER = (r"(?:\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten|"
          r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|"
          r"nineteen|twenty|several|many|few)")
PATTERNS = [
    ("editorially_corrected_date", rf"\b{MONTH}\s*\[\s*{MONTH}\s*\]\s*{DAY}\b"),
    ("calendar_date", rf"\b{DAY}(?:\s*[&–—,-]\s*{DAY})?\s*(?:of\s+)?(?:last\s+)?{MONTH}(?:\s*,?\s*{YEAR})?\b"),
    ("calendar_date", rf"\b{MONTH}\s*{DAY}(?:\s*[&–—,-]\s*{DAY})?(?:\s*,?\s*{YEAR})?\b"),
    ("month_year", rf"\b{MONTH}\s*,?\s*{YEAR}\b"),
    ("day_reference", r"\b(?:on|of|dated|till|until|since|by|before|after)\s+(?:the\s+)?(?:3[01]|[12]\d|[1-9])(?:\.?\s*(?:st|nd|rd|th|d))\b"),
    ("bare_day_reference", r"\b(?:3[01]|[12]\d|[1-9])(?:st|nd|rd|th|d)\b"),
    ("month_reference", rf"\b{MONTH}(?:\s+(?:last|next|instant|ult(?:imo)?\.?))?\b"),
    ("year_reference", rf"(?<!\d){YEAR}(?!\d)"),
    ("weekday_reference", rf"\b(?:(?:last|next|this)\s+)?{WEEKDAY}(?:\s+(?:last|next))?\b"),
    ("relative_date", r"\b(?:the\s+)?(?:day\s+before\s+yesterday|day\s+after\s+to[- ]?morrow|yesterday|to[- ]?day|to[- ]?morrow|to[- ]?night|the\s+other\s+day)\b"),
    ("relative_date", r"\b(?:last|next|this|previous|following)\s+(?:night|morning|evening|week|month|year|spring|summer|autumn|winter)(?:\s+but\s+one)?\b"),
    ("elapsed_or_duration", rf"\b{NUMBER}\s+(?:days?|weeks?|months?|years?|fortnights?)(?:[’']?\s*(?:ago|since|before|after|hence|past|time))?\b"),
    ("month_relative_shorthand", r"\b(?:inst\.|instant|ult\.|ultimo|proximo|prox\.)"),
    ("holiday_reference", r"\b(?:Christmas|X[’']?t?mas|Easter|Michaelmas|Whitsun(?:tide)?)\b"),
]
COMPILED = [(kind, re.compile(pattern, re.I)) for kind, pattern in PATTERNS]
POSTAL = re.compile(r"\b(?:letters?|notes?|packets?|post(?:mark|script|office)?|yours|"
                    r"receiv\w*|wrote|written|writ(?:e|ing)|answer\w*|despatch\w*|"
                    r"dispatch\w*|forward\w*|bundle|correspond\w*|acknowledg\w*)\b", re.I)
CONCRETE = {"calendar_date", "month_year", "month_reference", "year_reference", "day_reference", "bare_day_reference", "editorially_corrected_date"}


def normalized(text):
    return " ".join(text.split())


def class_xpath(name):
    return f'contains(concat(" ", normalize-space(@class), " "), " {name} ")'


def temporal_matches(text):
    candidates = []
    for rank, (kind, pattern) in enumerate(COMPILED):
        for match in pattern.finditer(text):
            if kind == "month_reference" and re.match(r"may\b", match.group(), re.I):
                around = text[max(0, match.start()-14):match.end()+14]
                preceding = text[max(0, match.start()-16):match.start()]
                strong_preposition = re.search(r"\b(?:in|of|since|before|after|until|till|by|last|next)\s+$", preceding, re.I)
                if not strong_preposition and not re.search(r"\bMay\s+(?:last|next)\b", around):
                    continue
            if kind == "year_reference" and (re.match(r"\s*(?:feet|ft|miles|fathoms|lbs|pounds)\b", text[match.end():], re.I)
                                              or text[max(0,match.start()-1):match.start()] in ("£", "$")):
                continue
            candidates.append((match.start(), match.end(), rank, kind))
    selected = []
    for start, end, rank, kind in sorted(candidates, key=lambda m: (-(m[1]-m[0]), m[2], m[0])):
        if not any(start < old[1] and old[0] < end for old in selected):
            selected.append((start, end, rank, kind))
    return sorted(selected)


def parse_page(raw):
    doc = html.fromstring(raw)
    letter = doc.xpath('//div[@id="letter"]')
    title = normalized(" ".join(n.text_content() for n in doc.xpath('//div[@id="letter"]//h1')))
    headers = [normalized(n.text_content()) for n in doc.xpath(f'//div[@id="letter"]//*[{class_xpath("opener")}]')]
    bodies = doc.xpath(f'//div[@id="letter"]//div[{class_xpath("body-content")}]')
    excluded = []
    paragraphs = []
    fallback = False
    for original in bodies:
        node = copy.deepcopy(original)
        for x in list(node.xpath(f'.//*[{class_xpath("footnote")}]')):
            x.drop_tree()
        for x in list(node.xpath(f'.//*[{class_xpath("salute")} or {class_xpath("supplemental")}]')):
            if x.getparent() is not None:
                excluded.append({"class": x.get("class"), "text": normalized(x.text_content())})
                x.drop_tree()
        blocks = node.xpath('.//p | .//li | .//tr | .//div[not(.//p) and not(.//div)]')
        block_set = set(blocks)
        blocks = [b for b in blocks if not any(a in block_set for a in b.iterancestors())]
        whole = normalized(node.text_content())
        combined = normalized(" ".join(b.text_content() for b in blocks))
        # A malformed/unusual layout must not silently lose prose outside a <p>.
        if re.sub(r"\s", "", whole) != re.sub(r"\s", "", combined):
            blocks = [node]
            fallback = True
        for block in blocks:
            text = normalized(block.text_content())
            if not re.search(r"\w", text):
                continue
            paragraphs.append({"body_paragraph": len(paragraphs)+1, "text": text,
                               "html_class": block.get("class", ""),
                               "locator": f"div#letter div.body-content; retained body block {len(paragraphs)+1}"})
    return {"title": title, "header_text": headers, "paragraphs": paragraphs,
            "excluded_body_annotations_and_salutations": excluded,
            "body_container_count": len(bodies), "used_whole_body_fallback": fallback,
            "editorial_summary": normalized(" ".join(n.text_content() for n in doc.xpath('//div[@id="summary"]'))),
            "editorial_footnotes": normalized(" ".join(n.text_content() for n in doc.xpath(f'//div[@id="letter"]//div[{class_xpath("footnotes")}]'))),
            "letter_container_present": bool(letter)}


def find_references(letter):
    hits = []
    for paragraph in letter["paragraphs"]:
        text = paragraph["text"]
        dates = temporal_matches(text)
        for start, end, _, kind in dates:
            nearby = text[max(0, start-120):min(len(text), end+120)]
            postal = bool(POSTAL.search(nearby) or (len(text)<=600 and POSTAL.search(text)))
            if kind in ("month_relative_shorthand", "bare_day_reference") and not postal:
                continue
            internal_dateline = len(text) <= 110 and not POSTAL.search(text) and (
                paragraph["html_class"] in ("left", "right", "dateline", "date")
                or (kind in CONCRETE and len(re.sub(r"[^a-zA-Z]", "", text[:start]+text[end:])) <= 25))
            group = ("internal_dateline" if internal_dateline else
                     "dated_correspondence_candidate" if postal and kind in CONCRETE else
                     "relative_correspondence_candidate" if postal else "other_body_temporal_reference")
            low, high = max(0, start-180), min(len(text), end+180)
            excerpt = ("…" if low else "") + text[low:high] + ("…" if high<len(text) else "")
            hits.append({"id": f"{letter['id']}-p{paragraph['body_paragraph']}-c{start}",
                         "letter_id": letter["id"], "direction": letter["direction"],
                         "letter_date_original": letter["original_csv"]["date"],
                         "letter_xml_date_bounds": letter["xml_date_bounds"],
                         "body_paragraph": paragraph["body_paragraph"], "locator": paragraph["locator"],
                         "char_start": start, "char_end": end, "matched_text": text[start:end],
                         "reference_kind": kind, "candidate_group": group,
                         "context": excerpt, "source_url": letter["source"]["url"],
                         "source_path": letter["source"]["path"],
                         "source_sha256": letter["source"]["sha256"],
                         "review_status": "candidate_not_a_confirmed_receipt_or_reply_link"})
    return hits


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False)+"\n" for r in rows))


def main():
    REPORT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(RAW_MANIFEST.read_text())
    if manifest["errors"]:
        raise ValueError("Download errors must be resolved before claiming coverage")
    sources = {s["id"]: s for s in manifest["files"]}
    audit = {r["id"]: r for r in map(json.loads, (ROOT / "reports/1828-1836/audit.jsonl").read_text().splitlines())}
    annotations = json.loads((ROOT / "data/annotations/text_attribution.json").read_text())
    letters, references = [], []
    for row in manifest["selected_original_metadata"]:
        source = sources[row["id"]]
        raw = (ROOT / source["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError(f"Source hash mismatch: {row['id']}")
        a = audit[row["id"]]
        letter = {"id": row["id"], "original_csv": row, "source": source,
                  "direction": a["direction"], "period_classification": a["classification"],
                  "xml_date_bounds": {"earliest": a["xml_earliest"], "latest": a["xml_latest"],
                                      "exact_order_needs_review": a["exact_order_needs_review"]},
                  "sent_date_constraints": a["sent_date_constraints"],
                  "sender_evidence": a["sender_evidence"],
                  "text_attribution_review": annotations.get(row["id"]), **parse_page(raw)}
        letter["body_word_count"] = sum(len(p["text"].split()) for p in letter["paragraphs"])
        hits = find_references(letter)
        letter["reference_count"] = len(hits)
        letter["reference_group_counts"] = dict(Counter(h["candidate_group"] for h in hits))
        letters.append(letter)
        references.extend(hits)
    write_jsonl(REPORT / "letters.jsonl", letters)
    write_jsonl(REPORT / "date_references.jsonl", references)
    correspondence = [h for h in references if h["candidate_group"] in ("dated_correspondence_candidate", "relative_correspondence_candidate")]
    write_jsonl(REPORT / "correspondence_candidates.jsonl", correspondence)
    columns = ["letter_id", "direction", "letter_date_original", "body_paragraph", "matched_text",
               "reference_kind", "candidate_group", "context", "source_url", "id"]
    with (REPORT / "date_references.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(references)
    summary = {
        "selected_letters": len(letters), "numeric_range": [37, 337],
        "suffix_entries_included": [r["id"] for r in letters if re.search(r"[A-Z]$", r["id"])],
        "excluded_third_party_csv_records": len(manifest["excluded_third_party_original_metadata"]),
        "csv_gap_checks": manifest["csv_gap_checks"],
        "source_hashes_verified": len(letters),
        "letters_with_transcribed_body": sum(bool(r["paragraphs"]) for r in letters),
        "letters_without_transcribed_body": [r["id"] for r in letters if not r["paragraphs"]],
        "whole_body_fallback_ids": [r["id"] for r in letters if r["used_whole_body_fallback"]],
        "body_words_searched": sum(r["body_word_count"] for r in letters),
        "letters_with_temporal_references": sum(r["reference_count"]>0 for r in letters),
        "reference_count": len(references),
        "reference_groups": dict(Counter(h["candidate_group"] for h in references)),
        "unique_letters_by_group": {k: len({h["letter_id"] for h in references if h["candidate_group"]==k})
                                    for k in sorted({h["candidate_group"] for h in references})},
        "direction_counts": dict(Counter(r["direction"] for r in letters)),
        "metadata_coauthors": [r["id"] for r in letters if len(r["sender_evidence"])>1],
        "known_excerpt_only": ["DCP-LETT-303"],
        "reported_letter_text_instead_of_authorial_transcription": ["DCP-LETT-330"],
        "matches_are_candidates": True,
        "automatic_receipt_dates_assigned": False,
        "source_manifest": str(RAW_MANIFEST.relative_to(ROOT)),
    }
    (REPORT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

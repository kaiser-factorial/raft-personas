import hashlib, json, pathlib, re, collections

ROOT = pathlib.Path(__file__).resolve().parents[3]
REV = ROOT / "reports/1844-1846/review"

def norm(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = (s.replace("&amp;", "&").replace("&nbsp;", " ")
           .replace("&#x27;", "'").replace("&quot;", '"'))
    return re.sub(r"s+", " ", s).strip()

def section_text(path, cls):
    s = pathlib.Path(path).read_text(errors="ignore")
    m = re.search(r'<div class="' + re.escape(cls) + r'">(.*?)</div></div>', s, re.S)
    return norm(m.group(1)) if m else None

def main():
    manifest = json.load(open(REV / "manifest.json"))
    ids = [i for b in manifest["packets"] for i in b["target_ids"]]
    allx = {json.loads(l)["id"]: json.loads(l) for l in open(REV / "all_letters.jsonl")}
    supp = [json.loads(l) for l in open(REV / "supplemental-marginalia.jsonl")
            if json.loads(l)["letter_id"] in ids]
    reviews = []
    for p in (REV / "marginalia-reviews").glob("*.json"):
        reviews += json.load(open(p)).get("records", [])
    rmap = {(r["letter_id"], r["section_class"], r["dom_locator"]): r for r in reviews}
    text_checks = []
    for x in supp:
        key = (x["letter_id"], x["section_class"], x["dom_locator"])
        r = rmap.get(key)
        raw = section_text(ROOT / x["source_path"], x["section_class"])
        ev = norm(" ".join(e.get("quote", "") for e in (r or {}).get("exact_evidence", [])))
        text_checks.append({"key": key, "raw_html_vs_review_evidence_equal": raw == ev,
                            "raw_html_chars": len(raw or ""), "review_evidence_chars": len(ev)})
    keys = [(x["letter_id"], x["section_class"], x["dom_locator"]) for x in supp]
    rkeys = [(r["letter_id"], r["section_class"], r["dom_locator"]) for r in reviews]
    out = {
        "scope": {"target_html_files_checked": len(ids), "supplemental_rows": len(supp),
                  "review_rows": len(reviews), "helper": str(pathlib.Path(__file__).resolve())},
        "hash_identity_coverage": {
            "missing": sorted(set(keys) - set(rkeys)),
            "duplicates": [k for k,v in collections.Counter(rkeys).items() if v != 1],
            "extras": sorted(set(rkeys) - set(keys)),
            "source_hash_mismatches": [x["letter_id"] for x in supp
                for r in reviews if (x["letter_id"],x["section_class"],x["dom_locator"]) ==
                (r["letter_id"],r["section_class"],r["dom_locator"]) and x["source_sha256"] != r.get("source_sha256")]
        },
        "text_order_comparison": {
            "raw_html_section_vs_review_evidence_comparisons": len(text_checks),
            "equal": sum(x["raw_html_vs_review_evidence_equal"] for x in text_checks),
            "mismatch_count": sum(not x["raw_html_vs_review_evidence_equal"] for x in text_checks),
            "mismatch_details": [x for x in text_checks if not x["raw_html_vs_review_evidence_equal"]][:50],
            "supplemental_jsonl_text_comparisons": 0,
            "limitation": "supplemental-marginalia.jsonl stores ordered section identity and block labels, but no block text; it cannot independently support text equality. Raw HTML versus review evidence is therefore the reproducible text comparison."
        },
        "deterministic_scope_note": "Hashes, locators, identity, and normalized text comparisons verify extraction artifacts only; reviewer historical authorship and dating judgments remain unaccepted."
    }
    (REV / "marginalia-integrity-audit.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()

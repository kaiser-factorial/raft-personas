"""Read-only integrity audit for already accepted period review decisions."""
import argparse, hashlib, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PERIOD = ROOT / "reports/1844-1846/review"

def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()

def walk_quotes(v, out):
    if isinstance(v, dict):
        for k, x in v.items():
            if k in {"quote", "exact_quote"} and isinstance(x, str):
                out.append(x)
            else:
                walk_quotes(x, out)
    elif isinstance(v, list):
        for x in v:
            walk_quotes(x, out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="+", default=["01","02","03","04","11","12","14","16"])
    args = ap.parse_args()
    allx = {json.loads(l)["id"]: json.loads(l) for l in open(PERIOD/"all_letters.jsonl")}
    errors, quote_checks, source_checks = [], [], []
    coverage = {}
    for b in args.batches:
        packet = json.load(open(PERIOD/f"packets/batch-{b}.json"))
        decision = json.load(open(PERIOD/f"parent-decisions/batch-{b}.json"))
        reading = json.load(open(PERIOD/f"parent-reading/batch-{b}.json"))
        ids = packet["target_ids"] + packet["context_ids"]
        for ident in ids:
            x = allx.get(ident)
            if not x:
                errors.append({"batch":b,"id":ident,"kind":"missing_all_letters_record"}); continue
            sp = ROOT / x["source"]["path"]
            actual = hashlib.sha256(sp.read_bytes()).hexdigest() if sp.exists() else None
            source_checks.append({"batch":b,"id":ident,"html_hash_equal":actual == x["source"]["sha256"]})
            if actual != x["source"]["sha256"]: errors.append({"batch":b,"id":ident,"kind":"html_hash","expected":x["source"]["sha256"],"actual":actual})
            xp = ROOT / x["metadata_audit"]["provenance"]["xml_path"]
            xh = hashlib.sha256(xp.read_bytes()).hexdigest() if xp.exists() else None
            expected_xml = x["metadata_audit"]["provenance"].get("xml_sha256")
            source_checks[-1]["xml_hash_equal"] = xh == expected_xml
            if xh != expected_xml: errors.append({"batch":b,"id":ident,"kind":"xml_hash","expected":expected_xml,"actual":xh})
        body = {p["id"] for p in []}
        body_read = set(reading.get("body_ids_read", []))
        missing = sorted(set(ids) - body_read - set(decision.get("body_unavailable_ids", [])))
        if missing: errors.append({"batch":b,"kind":"primary_reading_coverage","missing":missing})
        coverage[b] = {"expected_records":len(ids),"body_read":len(body_read & set(ids)),"body_unavailable":len(set(decision.get("body_unavailable_ids",[])) & set(ids)),"missing":missing}
        quotes=[]; walk_quotes(decision,quotes)
        for q in quotes:
            qq=norm(q); found=any(qq and qq in norm(" ".join(p["text"] for p in allx[i].get("paragraphs",[]))) for i in ids if i in allx)
            quote_checks.append({"batch":b,"quote_prefix":q[:100],"found_in_body":found})
            if not found: errors.append({"batch":b,"kind":"quote_not_found","quote_prefix":q[:100]})
    addendum = PERIOD/"scholarly-sections.v2.jsonl"
    add_rows=[json.loads(l) for l in open(addendum)] if addendum.exists() else []
    parent_supp=set()
    for b in args.batches:
        parent_supp.update(json.load(open(PERIOD/f"parent-reading/batch-{b}.json")).get("supplemental_sections_read_ids",[]))
    add_batches={f"batch-{b}" for b in args.batches}
    applicable=[x for x in add_rows if x["packet_id"] in add_batches]
    addendum_status="missing_required_status_field"
    errors.append({"kind":"supplemental_addendum_status","detail":"scholarly-sections.v2.jsonl has no status=primary_supplemental_source_read_complete; it is not accepted as an addendum."})
    out={"scope":{"batches":args.batches,"read_only":True},"source_hash_checks":{"checked":len(source_checks),"errors":sum(not (x["html_hash_equal"] and x["xml_hash_equal"]) for x in source_checks)},"primary_reading_coverage":coverage,"quote_checks":{"checked":len(quote_checks),"not_found":sum(not x["found_in_body"] for x in quote_checks)},"supplemental":{"parent_read_ids":len(parent_supp),"addendum_rows_applicable":len(applicable),"addendum_status":addendum_status,"provenance":"parent-reading IDs are accepted evidence; v2 rows require explicit addendum status and complete current source hashes/sections."},"errors":errors,"interpretation":"This verifies ledger/source integrity and recorded reading coverage; it does not re-adjudicate historical links or accept reviewer judgments."}
    (PERIOD/"ledger-integrity-audit.json").write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()

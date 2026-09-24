"""Plan (without exporting) the individual Darwin grounding sources."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from period_review import load

ROOT = Path(__file__).resolve().parents[1]
START, END = "1828-01-01", "1859-11-24"

def pin(path):
    return {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

def date_hold(row):
    a=row["metadata_audit"]; b={"earliest":a.get("xml_earliest"),"latest":a.get("xml_latest")}
    if a.get("date_structure") != "single_xml_day" or b.get("earliest") != b.get("latest"):
        return "non_single_XML_day"
    if not (b.get("earliest") and START <= b["earliest"] <= END): return "outside_corpus_endpoint"
    flags=set(a.get("source_date_flags", []))
    if flags & {"questioned_component", "circa", "before", "after"}: return "explicit_date_uncertainty"
    return None

def voice_ok(row):
    a=row["metadata_audit"]
    senders=a.get("sender_evidence", [])
    return (a.get("direction") == "from_darwin" and len(senders) == 1
            and Path(senders[0].get("attributes",{}).get("key", "")).name == "nameregs_1.xml")

def main(output):
    rows=load("1858-1859")
    invp=ROOT/"reports/raft-prep/candidates/raft-export-inventory.dry-run.json"
    inv=json.loads(invp.read_text()) if invp.exists() else {"relationship_records":[],"letter_records":[]}
    reserved={x.get("response_id") for x in inv["relationship_records"] if x.get("record_kind")=="direct_pair" and x.get("response_id")}
    byid={}
    for x in inv.get("letter_records",[]): byid.setdefault(x.get("letter_id"),[]).append(x)
    plans=[]; counts={"candidate_pending_render_check":0,"reserved_response":0,"genuine_excluded":0,"held":0}
    for ident,row in rows.items():
        a=row["metadata_audit"]; hold=date_hold(row); flags=[]
        if row.get("source",{}).get("path"): flags.append({"source":row["source"],"pin_sha256":row["source"].get("sha256")})
        if ident in reserved: state="reserved_response"; reason="accepted_directed_edge_response"
        elif not voice_ok(row): state="genuine_excluded"; reason="not_ordinary_individual_Darwin_sender"
        elif hold: state="held"; reason=hold
        elif row.get("used_whole_body_fallback") or not row.get("letter_container_present"): state="held"; reason="source_extent_or_letter_container_review"
        else: state="candidate_pending_render_check"; reason="ordinary_individual_Darwin_body_exact_single_XML_day"
        counts[state]+=1
        notes=json.dumps([row.get("text_attribution_review"), byid.get(ident,[])],ensure_ascii=False).lower()
        plans.append({"source_id":ident,"state":state,"reason":reason,"source_pin":flags[0] if flags else None,"date":{"earliest":a.get("xml_earliest"),"latest":a.get("xml_latest"),"structure":a.get("date_structure"),"flags":a.get("source_date_flags",[]),"original_label":row.get("original_csv",{}).get("date")},"accepted_disposition_pointers":byid.get(ident,[]),"scope_review_flags": [x for x in ("later_hand","quoted_enclosure","synopsis","joint","authorial_postscript","hold") if x.replace("_"," ") in notes or x in notes]})
    report={"schema_version":1,"status":"dry_run_grounding_plan","corpus_endpoint":{"start":START,"end":END},"source_count":len(rows),"reserved_unique_Darwin_responses":len(reserved),"counts":counts,"missing_authoritative_approval_errors":sum(x["state"]=="candidate_pending_render_check" and not x["accepted_disposition_pointers"] for x in plans),"inputs":[pin(invp)] if invp.exists() else [],"legacy_reconciliation_rule":"legacy reconciliation new 13th ledger; rule 50 P5-6 only","no_export":True,"plans":plans}
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"path":str(output.relative_to(ROOT)),"source_count":len(rows),"counts":counts,"no_export":True}))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,default=ROOT/"reports/raft-prep/candidates/grounding-plan.luna.json");a=p.parse_args();main(a.output)

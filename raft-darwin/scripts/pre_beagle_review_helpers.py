"""Evidence-preserving helpers for the human/model initial survey; no link promotion."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "reports/pre-beagle-1828-1831"
PACKET = json.loads((FOLDER / "source_packet.json").read_text())
LETTERS = {r["id"]: r for rows in PACKET.values() for r in rows}
AUDIT = {r["id"]: r for r in map(json.loads, (ROOT / "reports/1828-1836/audit.jsonl").read_text().splitlines())}


def ident(n):
    return str(n) if str(n).startswith("DCP-LETT-") else f"DCP-LETT-{n}"


def evidence(n, paragraph, quote):
    letter = LETTERS[ident(n)]
    text = next(p["text"] for p in letter["paragraphs"] if p["body_paragraph"] == paragraph)
    if text.count(quote) != 1:
        raise ValueError(f"Quote not unique/exact: {n}, {paragraph}, {quote}")
    start = text.index(quote)
    return {"letter_id": letter["id"], "body_paragraph": paragraph, "char_start": start,
            "char_end": start + len(quote), "quote": quote, "source_sha256": letter["source"]["sha256"]}


def observation(n, kind, paragraph, quote, interpretation, **extra):
    return {"kind": kind, "interpretation": interpretation, "evidence": [evidence(n, paragraph, quote)], **extra}


def review(n, summary, observations, **extra):
    letter, audit = LETTERS[ident(n)], AUDIT[ident(n)]
    keys = lambda people: {p["attributes"]["key"].split("/")[-1] for p in people}
    candidates = [r["id"] for r in AUDIT.values() if r["direction"] == "to_darwin"
                  and r["period_selection_eligible"] and keys(r["sender_evidence"]) & keys(audit["recipient_evidence"])
                  and r["xml_earliest"] <= audit["xml_latest"]]
    return {"letter_id": ident(n), "initial_review_status": "surveyed_pending_Luna_verification",
            "target_body_read_in_full": True, "paragraphs_read": [p["body_paragraph"] for p in letter["paragraphs"]],
            "body_word_count": letter["body_word_count"], "body_source": letter["source"],
            "original_csv": letter["original_csv"], "original_sent_date_constraints": letter["sent_date_constraints"],
            "xml_date_bounds": letter["xml_date_bounds"], "summary": summary, "observations": observations,
            "same_correspondent_identity_date_candidates": candidates,
            "automatic_graph_promotion": False, **extra}


def save(rows):
    path = FOLDER / "initial_survey.json"
    current = json.loads(path.read_text()) if path.exists() else {"batch_id": "pre-beagle-1828-1831", "status": "in_progress", "letters": []}
    existing = {r["letter_id"]: r for r in current["letters"]}
    for row in rows:
        if row["letter_id"] in existing:
            raise ValueError("Initial survey already contains " + row["letter_id"])
        existing[row["letter_id"]] = row
    current["letters"] = [existing[r["id"]] for r in PACKET["outgoing"] if r["id"] in existing]
    path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n")
    print("Surveyed", len(current["letters"]), "of", len(PACKET["outgoing"]))

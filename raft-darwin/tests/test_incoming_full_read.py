import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_correspondence_map import build_map, load_jsonl
from build_incoming_full_read import expected_pairs, validate_reviews


class IncomingFullReadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder = ROOT / "reports/post-return-1836/incoming-full-read"
        cls.manifest = json.loads((folder / "manifest.json").read_text())
        cls.reviews = {group: json.loads((folder / f"{group}.review.json").read_text()) for group in cls.manifest["groups"]}
        cls.letters = load_jsonl(ROOT / "reports/body-date-search-37-337/letters.jsonl")
        cls.pairs = expected_pairs(load_jsonl(ROOT / "reports/post-return-1836/dossiers.jsonl"))

    def validate(self, reviews):
        return validate_reviews(reviews, self.manifest, self.letters, self.pairs)

    def test_full_body_and_pair_coverage(self):
        audit = self.validate(self.reviews)
        self.assertEqual(len(audit["assessments"]), 85)
        self.assertEqual(sum(r["direction"] == "to_darwin" for r in audit["read_records"]), 33)
        self.assertEqual(sum(r["direction"] == "from_darwin" for r in audit["read_records"]), 10)
        self.assertFalse(audit["automatic_graph_promotions"])

    def test_missing_paragraph_or_pair_fails(self):
        for key in ("paragraph", "pair"):
            reviews = copy.deepcopy(self.reviews)
            if key == "paragraph":
                reviews["caroline"]["read_records"][0]["paragraphs_read"].pop()
            else:
                reviews["caroline"]["assessments"].pop()
            with self.assertRaises(ValueError):
                self.validate(reviews)

    def test_changed_evidence_or_source_hash_fails(self):
        for key in ("quote", "hash"):
            reviews = copy.deepcopy(self.reviews)
            if key == "quote":
                reviews["caroline"]["assessments"][0]["evidence"][0]["quote"] = "invented"
            else:
                reviews["caroline"]["read_records"][0]["source_sha256"] = "wrong"
            with self.assertRaises(ValueError):
                self.validate(reviews)

    def test_positive_proposal_needs_evidence_on_both_sides(self):
        reviews = copy.deepcopy(self.reviews)
        assessment = reviews["caroline"]["assessments"][0]
        assessment["status"] = "supported_knowledge"
        assessment["evidence"] = [e for e in assessment["evidence"] if e["letter_id"] == assessment["incoming_id"]]
        with self.assertRaises(ValueError):
            self.validate(reviews)

    def test_candidate_assessment_cannot_activate_persona_memory(self):
        annotations = json.loads((ROOT / "data/annotations/correspondence_links.json").read_text())
        audit = load_jsonl(ROOT / "reports/1828-1836/audit.jsonl")
        before = build_map(audit, self.letters, annotations)
        candidate = copy.deepcopy(self.reviews["caroline"]["assessments"][0])
        candidate["status"] = "supported_knowledge"
        annotations["incoming_full_read_review"] = {"assessments": [candidate]}
        graph = build_map(load_jsonl(ROOT / "reports/1828-1836/audit.jsonl"), self.letters, annotations)
        node = next(n for n in graph["nodes"] if n["id"] == candidate["incoming_id"])
        self.assertIsNone(node["known_by_date"])
        self.assertFalse(node["darwin_voice_eligible"])
        self.assertEqual([e for e in graph["edges"] if e["conversation_prompt_eligible"]],
                         [e for e in before["edges"] if e["conversation_prompt_eligible"]])


if __name__ == "__main__":
    unittest.main()

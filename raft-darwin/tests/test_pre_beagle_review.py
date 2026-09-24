import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_correspondence_map import build_map, incoming_records, load_jsonl
from build_pre_beagle_review import checked_reviewer_evidence, validate_reviews

FOLDER = ROOT / "reports/pre-beagle-1828-1831"


class PreBeagleReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_jsonl(ROOT / "reports/1828-1836/audit.jsonl")
        cls.letters = load_jsonl(ROOT / "reports/body-date-search-37-337/letters.jsonl")
        cls.by_letter = {r["id"]: r for r in cls.letters}
        cls.annotations = json.loads((ROOT / "data/annotations/correspondence_links.json").read_text())
        cls.graph = build_map(cls.audit, cls.letters, cls.annotations)
        cls.nodes = {n["id"]: n for n in cls.graph["nodes"]}
        cls.manifest = json.loads((FOLDER / "manifest.json").read_text())

    def links(self, kind, source=None, target=None):
        return [e for e in self.graph["edges"] if e["relationship"] == kind
                and (source is None or e["source_id"] == source)
                and (target is None or e["target_id"] == target)]

    def test_independent_coverage_matches_period_selection(self):
        selected = {n["id"] for n in self.nodes.values() if n["node_kind"] == "catalogued_letter"
                    and n["darwin_voice_eligible"] and n["xml_date_bounds"]["earliest"] >= "1828-01-01"
                    and n["xml_date_bounds"]["latest"] < "1831-12-27"}
        self.assertEqual(len(selected), 80)
        self.assertEqual(set(self.manifest["outgoing_ids"]), selected)
        reviews, _, _ = validate_reviews(self.manifest, self.by_letter)
        self.assertEqual(set(reviews["outgoing"]), selected)
        self.assertEqual(len(reviews["incoming"]), 34)
        self.assertNotIn("DCP-LETT-153", reviews["incoming"])

    def test_frozen_survey_raw_sources_and_prior_annotations_preserved(self):
        self.assertEqual(hashlib.sha256((FOLDER / "initial_survey.json").read_bytes()).hexdigest(), self.manifest["initial_survey_sha256"])
        old = json.loads((FOLDER / "baseline_annotations.json").read_text())
        for key in ("edges", "candidate_links", "unlocated_nodes", "reviewed_letters"):
            for entry in old[key]:
                self.assertIn(entry, self.annotations[key])
        baseline = json.loads((FOLDER / "baseline_hashes.json").read_text())
        for path, digest in baseline.items():
            if path not in ("data/annotations/correspondence_links.json", "reports/correspondence-map/graph.json"):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)

    def test_offer_bundle_is_context_with_only_henslow_as_direct_prompt(self):
        self.assertEqual(self.nodes["DCP-LETT-107"]["established_prompt_ids"], ["DCP-LETT-105"])
        for source in (105, 106):
            self.assertTrue(self.links("knowledge_before", f"DCP-LETT-{source}", "DCP-LETT-107"))
            self.assertTrue(self.links("knowledge_before", f"DCP-LETT-{source}", "DCP-LETT-121"))
        self.assertFalse(self.nodes["DCP-LETT-121"]["established_prompt_ids"])
        timing = self.links("knowledge_before", "DCP-LETT-106", "DCP-LETT-107")[0]
        self.assertEqual(timing["known_by_date"], "1831-08-30")
        self.assertNotEqual(timing["receipt_constraints"]["arrival_at_destination"], timing["receipt_constraints"]["Darwin_personal_receipt"])

    def test_unread_receipt_and_candidate_identity_never_activate_knowledge(self):
        for identifier in ("DCP-LETT-116", "UNLOCATED-PRE-SEDGWICK-UNREAD-123"):
            node = self.nodes[identifier]
            self.assertIsNone(node["known_by_date"])
            self.assertEqual(node["availability_attested_for_ids"], [])
            self.assertIsNone(node["general_context_available_after_date"])
        self.assertEqual(len(self.links("receipt_without_reading", target="DCP-LETT-123")), 1)
        self.assertFalse(self.links("knowledge_before", "DCP-LETT-116", "DCP-LETT-123"))

    def test_anonymous_event_does_not_reveal_donor_or_whole_note(self):
        note = self.nodes["DCP-LETT-99"]
        self.assertEqual(note["original_csv"]["sender_surname"], "Herbert")
        self.assertFalse(note["context_identity_policy"]["archival_author_identity_available_to_persona"])
        self.assertEqual(note["context_identity_policy"]["context_author_label"], "anonymous donor")
        self.assertIsNone(note["known_by_date"])
        edge = self.links("source_event_match", "DCP-LETT-99", "DCP-LETT-100")[0]
        self.assertFalse(edge["full_source_text_reading_established"])
        self.assertFalse(edge["conversation_prompt_eligible"])
        record = next(r for r in incoming_records(self.graph) if r["id"] == "DCP-LETT-99")
        self.assertEqual(record["context_identity_policy"], note["context_identity_policy"])

    def test_fitzroy_cross_context_uncertain_reply_and_different_missing_input(self):
        self.assertTrue(self.links("knowledge_before", "DCP-LETT-135", "DCP-LETT-138"))
        self.assertFalse(self.nodes["DCP-LETT-138"]["established_prompt_ids"])
        reply = self.links("replies_to", "DCP-LETT-139", "DCP-LETT-135")[0]
        self.assertFalse(reply["conversation_prompt_eligible"])
        self.assertIsNone(self.nodes["DCP-LETT-139"]["writing_date"])
        self.assertEqual(self.nodes["DCP-LETT-139"]["xml_date_bounds"]["earliest"], "1831-10-04")
        self.assertEqual(self.nodes["DCP-LETT-139"]["xml_date_bounds"]["latest"], "1831-10-11")
        self.assertFalse(self.links("knowledge_before", "DCP-LETT-135", "DCP-LETT-142"))
        self.assertEqual(self.nodes["DCP-LETT-142"]["response_to_ids"], ["UNLOCATED-PRE-IN-142-0"])

    def test_incoming_reply_does_not_create_earlier_or_later_reading(self):
        self.assertTrue(self.links("replies_to", "DCP-LETT-150", "DCP-LETT-147"))
        self.assertFalse(self.links("knowledge_before", "DCP-LETT-150"))
        self.assertIsNone(self.nodes["DCP-LETT-150"]["known_by_date"])
        self.assertFalse(self.nodes["DCP-LETT-152"]["established_prompt_ids"])
        candidates = [e for e in self.graph["candidate_links"] if e["source_id"] == "DCP-LETT-150" and e["target_id"] == "DCP-LETT-152"]
        self.assertEqual(len(candidates), 1)
        self.assertFalse(candidates[0]["automatic_availability_or_prompt"])

    def test_missing_bundles_are_not_fabricated_prompts_or_physical_letter_count(self):
        for number, count in ((82, 2), (87, 3)):
            node = self.nodes[f"UNLOCATED-PRE-IN-{number}-0"]
            self.assertEqual(node["minimum_letter_count_in_this_reference"], count)
            self.assertFalse(node["text_available"])
            self.assertIsNone(node["writing_date"])
            self.assertFalse(self.nodes[f"DCP-LETT-{number}"]["established_prompt_ids"])
        self.assertIsNone(self.nodes["UNLOCATED-PRE-IN-145-0"]["known_by_date"])
        self.assertIsNone(self.nodes["DCP-LETT-145"]["writing_date"])

    def test_review_proposals_and_candidates_cannot_activate_memory(self):
        ann = copy.deepcopy(self.annotations)
        ann["pre_beagle_full_read_review"]["incoming_reviews"].append({
            "letter_id": "DCP-LETT-150", "proposed_links": [{"relationship": "knowledge_before", "source_id": "DCP-LETT-150", "target_id": "DCP-LETT-152", "status": "supported"}]})
        after = build_map(self.audit, self.letters, ann)
        node = next(n for n in after["nodes"] if n["id"] == "DCP-LETT-150")
        self.assertIsNone(node["known_by_date"])
        self.assertEqual(after["edges"], self.graph["edges"])

    def test_malformed_new_evidence_is_rejected(self):
        ann = copy.deepcopy(self.annotations)
        ann["context_identity_policies"][0]["evidence"][0]["quote"] = "invented source"
        with self.assertRaises(ValueError):
            build_map(self.audit, self.letters, ann)
        with self.assertRaises(ValueError):
            checked_reviewer_evidence({"letter_id": "DCP-LETT-152", "body_paragraph": 1, "quote": "made up"}, self.by_letter)


if __name__ == "__main__":
    unittest.main()

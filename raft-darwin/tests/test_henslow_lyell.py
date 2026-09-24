"""Prevent availability, authorship and paragraph-boundary regressions."""

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_expansion_review import can_condition, load_letters, validate_section_coverage


class HenslowLyellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = ROOT / "reports/1837-1843/henslow-lyell"
        cls.decisions = json.loads((ROOT / "data/annotations/henslow_lyell_1837_1843.json").read_text())
        cls.graph = json.loads((ROOT / "reports/1837-1843/correspondence-map/graph.json").read_text())
        cls.summary = json.loads((ROOT / "reports/1837-1843/correspondence-map/summary.json").read_text())
        cls.phase_summary = json.loads((ROOT / "reports/1837-1843/remaining-review/prior_expansion_summary.json").read_text())
        cls.nodes = {n["id"]: n for n in cls.graph["nodes"]}
        cls.sections = {s["id"]: s for s in cls.graph["dated_sections"]}

    def test_prior_evidence_is_unchanged_and_old_edges_survive(self):
        manifest = json.loads((self.review / "baseline_hashes.json").read_text())
        for r in manifest["files"]:
            self.assertEqual(hashlib.sha256((ROOT / r["path"]).read_bytes()).hexdigest(), r["sha256"], r["path"])
        prior = json.loads((self.review / "prior_expansion_graph.json").read_text())
        key = lambda e: (e["type"], e["source"], e["target"])
        self.assertLessEqual({key(e) for e in prior["edges"]}, {key(e) for e in self.graph["edges"]})

    def test_placeholder_is_not_a_read_body_or_grounding_target(self):
        node = self.nodes["DCP-LETT-699F"]
        self.assertTrue(node["source_record_reviewed"])
        self.assertFalse(node["body_read_in_full"])
        self.assertEqual(node["role"], "source_record_only_no_transcription")
        self.assertNotIn(node["id"], self.summary["reviewed_grounding_ids"])
        self.assertEqual(self.summary["reviewed_source_record_count"] - self.summary["full_read_count"],
                         len(self.summary["source_records_without_transcription"]))

    def test_joint_signature_does_not_authorize_individual_voice(self):
        node = self.nodes["DCP-LETT-421F"]
        self.assertTrue(node["body_read_in_full"])
        self.assertEqual(node["role"], "joint_document_not_individual_Darwin_voice")
        self.assertNotIn(node["id"], self.summary["reviewed_grounding_ids"])
        self.assertFalse(any(e["source"] == node["id"] or e["target"] == node["id"] for e in self.graph["edges"]))
        row = next(d for d in self.decisions["letter_adjudications"] if d["letter_id"] == node["id"])
        self.assertIn("Spring Rice", row["reason"])

    def test_recipient_receipt_annotation_is_not_a_composition_scalar(self):
        node = self.nodes["DCP-LETT-356"]
        self.assertEqual(node["original_xml_constraints"][0]["attributes"]["when"], "1837-05-28")
        self.assertIsNone(node["whole_letter_scalar_date"])

    def test_resolved_calendar_correction_can_support_a_pair(self):
        node = self.nodes["DCP-LETT-428"]
        self.assertEqual(node["whole_letter_scalar_date"], "1838-09-14")
        pair = next(p for p in self.decisions["direct_reply_pairs"] if p["outgoing_id"] == node["id"])
        self.assertEqual(pair["incoming_id"], "DCP-LETT-425")
        self.assertIsNone(pair["actual_receipt_date"])

    def test_earlier_witness_updates_knowledge_without_rewriting_source_date(self):
        node = self.nodes["DCP-LETT-690"]
        self.assertEqual(node["known_by_date"], "1843-09-02")
        self.assertFalse(node["raw_period_eligible"])
        self.assertEqual(node["original_xml_constraints"][0]["attributes"]["notBefore"], "1809-01-01")
        self.assertEqual({e["target"] for e in node["knowledge_attestations"]},
                         {"DCP-LETT-691", "DCP-LETT-691F", "DCP-LETT-696"})

    def test_latest_possible_bound_does_not_choose_between_writing_dates(self):
        node = self.nodes["DCP-LETT-696"]
        self.assertIsNone(node["whole_letter_scalar_date"])
        edge = next(e for e in self.graph["edges"] if e["type"] == "knowledge_before" and e["target"] == node["id"])
        self.assertEqual(edge["known_by_date"], "1843-09-22")
        self.assertEqual(edge["witness_date_policy"], "conservative_latest_possible_writing_date")
        self.assertEqual(edge["witness_xml_constraints"], node["original_xml_constraints"])

    def test_context_does_not_turn_712_into_a_paired_response(self):
        edges = [e for e in self.graph["edges"] if e["source"] == "DCP-LETT-712" and e["type"] == "replies_to"]
        self.assertEqual(edges, [])
        context = [e for e in self.graph["edges"] if e["target"] == "DCP-LETT-712" and e["type"] == "knowledge_before"]
        self.assertEqual({e["source"] for e in context}, {"DCP-LETT-706", "DCP-LETT-708"})
        self.assertTrue(all(e["direct_prompt"] is False for e in context))

    def test_change_of_plans_candidate_does_not_enter_accepted_graph(self):
        self.assertFalse(any(e["type"] == "replies_to" and e["source"] == "DCP-LETT-604" and e["target"] == "DCP-LETT-602" for e in self.graph["edges"]))
        self.assertTrue(any(c["source"] == "DCP-LETT-604" and c["target"] == "DCP-LETT-602" for c in self.graph["rejected_or_candidate_links"]))

    def test_friday_context_cannot_leak_across_a_mid_paragraph_dateline(self):
        late = self.sections["DCP-LETT-649:october7"]
        fragment = late["paragraph_fragments"][0]
        pair = {"outgoing_id": "DCP-LETT-649", "response_scope": "dated_sections", "response_sections": [late["id"]]}
        cut = fragment["char_start"]
        self.assertFalse(can_condition(pair, "DCP-LETT-649", 3, self.sections))
        self.assertFalse(can_condition(pair, "DCP-LETT-649", 4, self.sections))
        self.assertFalse(can_condition(pair, "DCP-LETT-649", 4, self.sections, cut - 1))
        self.assertTrue(can_condition(pair, "DCP-LETT-649", 4, self.sections, cut))
        self.assertTrue(can_condition(pair, "DCP-LETT-649", 5, self.sections))

    def test_section_validation_rejects_dropped_source_characters(self):
        sections = copy.deepcopy(self.sections)
        sections["DCP-LETT-649:october5"]["paragraph_fragments"][0]["char_end"] -= 1
        sections["DCP-LETT-649:october5"]["paragraph_fragments"][0]["text"] = sections["DCP-LETT-649:october5"]["paragraph_fragments"][0]["text"][:-1]
        with self.assertRaises(AssertionError):
            validate_section_coverage(sections, load_letters())

    def test_unreviewed_is_not_synonymous_with_unpaired(self):
        # These are the frozen Henslow/Lyell phase counts, not current totals.
        self.assertEqual(self.phase_summary["safe_outgoing_not_yet_full_read"], 247)
        self.assertEqual(self.phase_summary["reviewed_outgoing_without_identified_surviving_prompt"], 57)
        self.assertEqual(self.phase_summary["safe_outgoing_full_read_count"], 71)
        self.assertNotIn("DCP-LETT-421F", self.phase_summary["raw_period_held_full_read_incoming_ids"])
        self.assertEqual(self.phase_summary["confirmed_direct_reply_links"], 16)
        self.assertEqual(self.phase_summary["distinct_Darwin_response_letters"], 14)


if __name__ == "__main__":
    unittest.main()

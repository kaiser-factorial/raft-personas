"""Protect the chronological and authorship boundaries found in full reading."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_expansion_review import can_condition, check_quotes, load_letters


class ExpansionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decisions = json.loads((ROOT / "data/annotations/expansion_1837_1843.json").read_text())
        cls.graph = json.loads((ROOT / "reports/1837-1843/correspondence-map/graph.json").read_text())
        cls.sections = {s["id"]: s for s in cls.decisions["dated_sections"]}
        cls.nodes = {n["id"]: n for n in cls.graph["nodes"]}

    def pair(self, incoming, response):
        return next(p for p in self.decisions["direct_reply_pairs"]
                    if p["incoming_id"] == f"DCP-LETT-{incoming}" and p["outgoing_id"] == f"DCP-LETT-{response}")

    def test_saturday_input_cannot_condition_friday_even_with_single_xml_day(self):
        pair = self.pair("447", "448")
        for paragraph in range(1, 7):
            self.assertFalse(can_condition(pair, "DCP-LETT-448", paragraph, self.sections))
        self.assertTrue(can_condition(pair, "DCP-LETT-448", 7, self.sections))
        self.assertIsNone(self.nodes["DCP-LETT-448"]["whole_letter_scalar_date"])
        self.assertEqual(self.nodes["DCP-LETT-448"]["original_xml_constraints"][0]["attributes"]["when"], "1838-11-30")

    def test_monday_receipt_is_separate_from_tuesday_content_use(self):
        for incoming in ("464", "465"):
            pair = self.pair(incoming, "466")
            self.assertEqual(pair["known_by_date"], "1839-01-01")
            self.assertFalse(can_condition(pair, "DCP-LETT-466", 1, self.sections))
            self.assertTrue(can_condition(pair, "DCP-LETT-466", 3, self.sections))
        self.assertEqual(self.decisions["receipt_events"][0]["date"], "1838-12-31")

    def test_receipt_date_requires_its_own_evidence(self):
        self.assertIsNone(self.pair("447", "448")["actual_receipt_date"])
        self.assertEqual(self.pair("482", "484")["actual_receipt_date"], "1839-01-04")
        self.assertEqual(self.pair("482", "484")["known_by_date"], "1839-01-06")

    def test_same_day_arrival_still_preserves_within_letter_order(self):
        event = next(e for e in self.graph["within_day_events"] if e["witness_id"] == "DCP-LETT-626")
        self.assertEqual(event["arrival_body_paragraph"], 8)
        self.assertEqual(event["prior_paragraphs"], list(range(1, 8)))
        self.assertFalse(any(p["outgoing_id"] == "DCP-LETT-626" for p in self.decisions["direct_reply_pairs"]))

    def test_later_attestation_does_not_erase_original_period_hold(self):
        for ident in ("DCP-LETT-669", "DCP-LETT-690"):
            self.assertFalse(self.nodes[ident]["raw_period_eligible"])
            self.assertIsNotNone(self.nodes[ident]["known_by_date"])
            self.assertFalse(self.nodes[ident]["training_export_ready"])
        self.assertEqual(self.nodes["DCP-LETT-669"]["original_xml_constraints"][0]["attributes"]["notAfter"], "1882-12-31")
        self.assertEqual(self.nodes["DCP-LETT-690"]["original_xml_constraints"][0]["attributes"]["notBefore"], "1809-01-01")

    def test_reverse_replies_never_create_Darwin_voice_or_receipt(self):
        for node in self.nodes.values():
            if node["direction"] == "to_darwin":
                self.assertFalse(node["incoming_is_Darwin_voice"])
                self.assertIn(node["role"], ("incoming_context_only", "period_held_incoming_context"))
                self.assertFalse(node["individual_Darwin_voice_eligible"])
        reverse = [e for e in self.graph["edges"] if e["type"] == "replies_to" and not e["is_Darwin_response"]]
        self.assertTrue(reverse)
        self.assertTrue(all(e["activates_Darwin_knowledge"] is False for e in reverse))

    def test_shared_input_and_bundled_output_do_not_inflate_response_count(self):
        pairs = self.decisions["direct_reply_pairs"]
        self.assertEqual(len(pairs), 14)
        self.assertEqual(len({p["outgoing_id"] for p in pairs}), 12)
        self.assertEqual({p["outgoing_id"] for p in pairs if p["incoming_id"] == "DCP-LETT-444"}, {"DCP-LETT-445", "DCP-LETT-448"})
        self.assertEqual({p["incoming_id"] for p in pairs if p["outgoing_id"] == "DCP-LETT-466"}, {"DCP-LETT-464", "DCP-LETT-465"})

    def test_candidate_same_day_link_stays_out_of_knowledge_edges(self):
        self.assertFalse(any(e["type"] == "knowledge_before" and e["source"] == "DCP-LETT-701" and e["target"] == "DCP-LETT-701F" for e in self.graph["edges"]))

    def test_quote_verification_rejects_correct_words_in_wrong_paragraph(self):
        quote = {"letter_id": "DCP-LETT-484", "body_paragraph": 1,
                 "quote": "With a little judgment we shall make that room comfortable"}
        with self.assertRaises(ValueError):
            check_quotes(quote, load_letters())
        quote["body_paragraph"] = 3
        self.assertEqual(len(check_quotes(quote, load_letters())), 1)


if __name__ == "__main__":
    unittest.main()

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_correspondence_map import build_map, incoming_records, load_jsonl
from build_post_return_review import TARGET_IDS, build_dossiers
from search_letter_references import references


class CorrespondenceMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = load_jsonl(ROOT / "reports/1828-1836/audit.jsonl")
        cls.letters = load_jsonl(ROOT / "reports/body-date-search-37-337/letters.jsonl")
        cls.annotations = json.loads((ROOT / "data/annotations/correspondence_links.json").read_text())
        cls.graph = build_map(cls.audit, cls.letters, cls.annotations)
        cls.nodes = {n["id"]: n for n in cls.graph["nodes"]}

    def test_incoming_never_trains_voice_even_when_it_is_a_reply(self):
        self.assertTrue(all(not n["darwin_voice_eligible"] for n in self.nodes.values() if n["direction"] == "to_darwin"))
        fitzroy = self.nodes["DCP-LETT-312"]
        self.assertEqual(fitzroy["response_to_ids"], ["DCP-LETT-310"])
        self.assertEqual(fitzroy["known_by_date"], "1836-10-24")
        self.assertFalse(fitzroy["darwin_voice_eligible"])

    def test_knowledge_does_not_invent_a_prompt(self):
        self.assertEqual(self.nodes["DCP-LETT-313"]["established_prompt_ids"], [])
        self.assertEqual(self.nodes["DCP-LETT-306"]["established_prompt_ids"], ["DCP-LETT-288"])
        self.assertEqual(self.nodes["DCP-LETT-287"]["availability_attested_for_ids"], ["DCP-LETT-306"])
        eligible = {(e["source_id"], e["target_id"]) for e in self.graph["edges"] if e["conversation_prompt_eligible"]}
        self.assertEqual(eligible, {("DCP-LETT-302", "DCP-LETT-296"), ("DCP-LETT-306", "DCP-LETT-288"),
                                   ("DCP-LETT-135A", "DCP-LETT-125"), ("DCP-LETT-107", "DCP-LETT-105"),
                                   ("DCP-LETT-144", "DCP-LETT-143")})

    def test_attested_unlocated_letter_has_no_synthetic_prompt(self):
        missing = self.nodes["UNLOCATED-WHITLEY-BEFORE-314"]
        self.assertFalse(missing["text_available"])
        self.assertIsNone(missing["original_csv"])
        self.assertEqual(missing["known_by_date"], "1836-10-24")
        self.assertIsNone(missing["general_context_available_after_date"])
        self.assertEqual(self.nodes["DCP-LETT-314"]["established_prompt_ids"], [])
        self.assertEqual(self.nodes["DCP-LETT-314"]["training_role"], "dated_Darwin_grounding")

    def test_ambiguous_attestation_never_gets_a_scalar_date(self):
        audit = copy.deepcopy(self.audit)
        row = next(r for r in audit if r["id"] == "DCP-LETT-135A")
        row["exact_order_needs_review"] = True
        row["xml_latest"] = "1831-09-24"
        graph = build_map(audit, self.letters, self.annotations)
        incoming = next(r for r in incoming_records(graph) if r["id"] == "DCP-LETT-125")
        self.assertIsNone(incoming["knowledge_date"])
        self.assertIsNone(incoming["response_links"][0]["response_date"])
        self.assertFalse(incoming["response_links"][0]["conversation_prompt_eligible"])

    def test_corrupt_evidence_and_unreviewed_edges_fail(self):
        for mutate in (lambda a: a["edges"][0]["evidence"][0].update(quote="invented quote"),
                       lambda a: a["edges"][0].update(review_status="candidate")):
            ann = copy.deepcopy(self.annotations)
            mutate(ann)
            with self.assertRaises(ValueError):
                build_map(self.audit, self.letters, ann)

    def test_empty_review_map_does_not_promote_keyword_matches(self):
        ann = copy.deepcopy(self.annotations)
        ann["edges"] = []
        graph = build_map(self.audit, self.letters, ann)
        self.assertTrue(all(r["knowledge_date"] is None for r in incoming_records(graph)))
        self.assertTrue(all(not n["established_prompt_ids"] for n in graph["nodes"]))

    def test_metadata_dates_and_voice_exclusions_preserved(self):
        for record in self.audit:
            node = self.nodes[record["id"]]
            self.assertEqual(node["original_csv"], record["original_csv"])
            self.assertEqual(node["original_sent_date_constraints"], record["sent_date_constraints"])
        for suffix in ("303", "330", "326", "3150F", "13858"):
            self.assertFalse(self.nodes["DCP-LETT-" + suffix]["darwin_voice_eligible"])
        incoming = incoming_records(self.graph)
        self.assertEqual(len(incoming), 126)
        self.assertEqual({r["id"] for r in incoming if r["knowledge_date"] is not None},
                         {f"DCP-LETT-{n}" for n in (105, 106, 125, 135, 143, 287, 288, 296, 312)})

    def test_search_retains_first_paragraph_and_exact_offsets(self):
        letters = {r["id"]: r for r in self.letters}
        hits = [h for letter in self.letters for h in references(letter)]
        self.assertEqual(len({h["id"] for h in hits}), len(hits))
        for hit in hits:
            paragraph = next(p for p in letters[hit["letter_id"]]["paragraphs"] if p["body_paragraph"] == hit["body_paragraph"])
            self.assertEqual(paragraph["text"][hit["char_start"]:hit["char_end"]], hit["matched_text"])
            self.assertFalse(hit["automatic_link_or_date"])
        self.assertTrue(any(h["letter_id"] == "DCP-LETT-314" and h["body_paragraph"] == 1 and h["match_kind"] == "literal_letter" for h in hits))

    def test_all_thirteen_post_return_letters_are_reviewed_without_invented_pairs(self):
        dossiers = build_dossiers(self.graph, self.letters)
        self.assertEqual({d["letter_id"] for d in dossiers}, TARGET_IDS)
        self.assertTrue(all(d["target_body_read_in_full"] for d in dossiers))
        self.assertTrue(all(not d["established_prompt_ids"] for d in dossiers))
        self.assertTrue(all(d["training_role"] == "dated_Darwin_grounding" for d in dossiers))

    def test_fox_attestation_does_not_supply_missing_text_or_composition_date(self):
        fox = self.nodes["UNLOCATED-FOX-BEFORE-319"]
        self.assertEqual(fox["known_by_date"], "1836-11-06")
        self.assertEqual(fox["availability_attested_for_ids"], ["DCP-LETT-319"])
        self.assertFalse(fox["text_available"])
        self.assertIsNone(fox["writing_date"])
        self.assertIsNone(fox["general_context_available_after_date"])
        self.assertEqual(self.nodes["DCP-LETT-319"]["response_to_ids"], [fox["id"]])
        self.assertEqual(self.nodes["DCP-LETT-319"]["established_prompt_ids"], [])

    def test_herbert_reply_does_not_date_darwins_knowledge(self):
        failed_id = "UNLOCATED-DARWIN-TO-HERBERT-BEFORE-314"
        answered_id = "UNLOCATED-DARWIN-TO-HERBERT-ACKNOWLEDGED-323"
        self.assertEqual(self.nodes["DCP-LETT-323"]["response_to_ids"], [answered_id])
        self.assertEqual(self.nodes["DCP-LETT-314"]["own_letter_reference_ids"], [failed_id])
        self.assertIn(failed_id, self.nodes[answered_id]["distinct_from"])
        for letter_id in (failed_id, answered_id):
            self.assertFalse(self.nodes[letter_id]["darwin_voice_eligible"])
            self.assertFalse(self.nodes[letter_id]["text_available"])
        self.assertIsNone(self.nodes["DCP-LETT-323"]["known_by_date"])
        self.assertEqual(self.nodes["DCP-LETT-323"]["availability_attested_for_ids"], [])

    def test_own_letter_references_do_not_create_incoming_availability(self):
        self.assertEqual(self.nodes["DCP-LETT-318"]["own_letter_reference_ids"], ["DCP-LETT-317"])
        self.assertEqual(self.nodes["DCP-LETT-329"]["own_letter_reference_ids"], ["DCP-LETT-330"])
        for suffix in ("317", "318", "329", "330"):
            self.assertIsNone(self.nodes[f"DCP-LETT-{suffix}"]["known_by_date"])
            self.assertEqual(self.nodes[f"DCP-LETT-{suffix}"]["established_prompt_ids"], [])
        self.assertFalse(self.nodes["DCP-LETT-330"]["darwin_voice_eligible"])
        self.assertIsNone(self.nodes["DCP-LETT-317"]["writing_date"])
        self.assertEqual(self.nodes["DCP-LETT-317"]["xml_date_bounds"]["latest"], "1836-10-31")

    def test_uncertain_ryde_reference_stays_outside_accepted_edges(self):
        candidate = next(c for c in self.graph["candidate_links"] if c["id"] == "possible-own-letter-327-319")
        self.assertFalse(candidate["conversation_prompt_eligible"])
        self.assertFalse(candidate["automatic_availability_or_prompt"])
        self.assertEqual(self.nodes["DCP-LETT-327"]["own_letter_reference_ids"], [])
        self.assertNotIn(candidate["id"], {e["id"] for e in self.graph["edges"]})

    def test_review_and_candidate_evidence_is_verified_not_only_accepted_edges(self):
        for field in ("reviewed_letters", "candidate_links"):
            ann = copy.deepcopy(self.annotations)
            ann[field][0]["evidence"][0]["char_start"] = -1
            with self.assertRaises(ValueError):
                build_map(self.audit, self.letters, ann)

    def test_same_person_screen_rejects_later_input_and_preserves_dates(self):
        dossiers = {d["letter_id"]: d for d in build_dossiers(self.graph, self.letters)}
        fitzroy = {c["id"]: c for c in dossiers["DCP-LETT-310"]["same_correspondent_date_screen"]}
        self.assertEqual(fitzroy["DCP-LETT-312"]["screen_disposition"], "too_late_under_XML_constraints")
        fox = dossiers["DCP-LETT-319"]["same_correspondent_date_screen"]
        self.assertEqual({c["id"] for c in fox}, {f"DCP-LETT-{n}" for n in (175, 184, 197, 261)})
        self.assertTrue(all(not c["screen_establishes_receipt_or_reply"] for c in fox))
        for candidate in fox:
            self.assertEqual(candidate["original_csv"], self.nodes[candidate["id"]]["original_csv"])


if __name__ == "__main__":
    unittest.main()

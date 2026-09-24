"""Protect full-period composition from false pair, date and voice promotions."""
import copy
import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_expansion_review import load_decisions,load_letters,validate_participants
from remaining_review_helpers import unavailable_transcription

class RemainingReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=ROOT/'reports/1837-1843/remaining-review'
        cls.graph=json.loads((cls.base.parent/'correspondence-map/graph.json').read_text())
        cls.summary=json.loads((cls.base.parent/'correspondence-map/summary.json').read_text())
        cls.nodes={n['id']:n for n in cls.graph['nodes']}
        cls.decisions,cls.sources=load_decisions()
        cls.letters=load_letters()
        cls.audit={r['id']:r for r in map(json.loads,(cls.base.parent/'audit.jsonl').read_text().splitlines())}
    def test_all_targets_covered_once_and_context_not_double_counted(self):
        counts=Counter()
        for p in self.sources:
            d=json.loads(p.read_text())
            counts.update(d.get('reviewed_record_ids',d['full_read_ids']))
        # The earlier two phases share five context records; remaining targets do not.
        remaining=Counter(i for p in self.sources if p.parent.name=='remaining_1837_1843'
                          for i in json.loads(p.read_text())['reviewed_record_ids'])
        self.assertEqual(len(remaining),363)
        self.assertEqual(set(remaining.values()),{1})
        self.assertEqual(set(self.nodes),set(self.audit))
        self.assertTrue(all(n['source_record_reviewed'] for n in self.nodes.values()))
        self.assertEqual(self.summary['unreviewed_source_record_count'],0)
    def test_frozen_baselines_and_prior_relationships_survive(self):
        for r in json.loads((self.base/'baseline_hashes.json').read_text())['files']:
            self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
        prior=json.loads((self.base/'prior_expansion_graph.json').read_text())
        key=lambda e:(e['type'],e['source'],e['target'])
        self.assertLessEqual({key(e) for e in prior['edges']},{key(e) for e in self.graph['edges']})
    def test_missing_body_is_reviewed_but_never_voice_or_unread(self):
        for i in ['DCP-LETT-13864','DCP-LETT-699F']:
            n=self.nodes[i]
            self.assertTrue(n['source_record_reviewed'])
            self.assertFalse(n['body_read_in_full'])
            self.assertFalse(n['individual_Darwin_voice_eligible'])
            self.assertNotIn(i,self.summary['reviewed_grounding_ids'])
        self.assertEqual(self.summary['full_read_count'],474)
        self.assertEqual(self.summary['safe_outgoing_not_yet_full_read'],0)
        self.assertEqual(self.summary['safe_outgoing_transcription_unavailable_ids'],['DCP-LETT-13864'])
    def test_catalogue_paraphrase_not_transcription_but_embedded_quote_survives(self):
        self.assertTrue(unavailable_transcription('[Asks the recipient to send details.]'))
        self.assertFalse(unavailable_transcription('[Asks for details: “please send them”.]'))
        self.assertTrue(unavailable_transcription('No transcription available'))
    def test_editorial_holds_preserve_original_XML(self):
        for i in ['DCP-LETT-631','DCP-LETT-13803']:
            n=self.nodes[i]
            self.assertTrue(n['raw_period_eligible'])
            self.assertFalse(n['effective_period_eligible'])
            self.assertIsNone(n['whole_letter_scalar_date'])
            self.assertFalse(n['individual_Darwin_voice_eligible'])
            self.assertEqual(n['original_xml_constraints'],self.audit[i]['sent_date_constraints'])
        self.assertEqual(self.summary['raw_XML_safe_count'],445)
        self.assertEqual(self.summary['effective_period_eligible_count'],443)
    def test_joint_and_disputed_authorship_not_individual_targets(self):
        for i in ['DCP-LETT-421F','DCP-LETT-512','DCP-LETT-612','DCP-LETT-677']:
            self.assertFalse(self.nodes[i]['individual_Darwin_voice_eligible'])
            self.assertNotIn(i,self.summary['reviewed_grounding_ids'])
    def test_table_caption_and_paraphrase_not_response_voice(self):
        e=next(e for e in self.graph['edges'] if e['type']=='replies_to' and e['source']=='DCP-LETT-545')
        self.assertNotIn(6,e['response_paragraphs'])
        n=self.nodes['DCP-LETT-609F']['text_scope']
        self.assertTrue(n['editorial_paraphrase_excluded'])
        self.assertEqual(n['voice_paragraphs'],[2,3])
        self.assertTrue(n['voice_spans'][0]['text'].startswith('my position is not such'))
        for ident in ['DCP-LETT-451','DCP-LETT-698','DCP-LETT-609F','DCP-LETT-13865']:
            scope=self.nodes[ident]['text_scope']
            for span in scope['voice_spans']:
                p=next(p['text'] for p in self.letters[ident]['paragraphs'] if p['body_paragraph']==span['body_paragraph'])
                self.assertEqual(p[span['char_start']:span['char_end']],span['text'])
    def test_institutional_roles_do_not_alias_people(self):
        p=next(p for p in self.decisions['direct_reply_pairs'] if p['incoming_id']=='DCP-LETT-381A')
        inc,out=self.audit[p['incoming_id']],self.audit[p['outgoing_id']]
        validate_participants(p,inc,out,self.letters)
        bad=copy.deepcopy(p);bad.pop('participant_match_override')
        with self.assertRaises(AssertionError):validate_participants(bad,inc,out,self.letters)
        bad=copy.deepcopy(p);bad['participant_match_override']['scope_outgoing_id']='DCP-LETT-378A'
        with self.assertRaises(AssertionError):validate_participants(bad,inc,out,self.letters)
    def test_corporate_signatory_override_does_not_change_metadata(self):
        p=next(p for p in self.decisions['direct_reply_pairs'] if p['incoming_id']=='DCP-LETT-377')
        self.assertEqual(p['participant_match_override']['policy'],'named_signatory_for_catalogued_institution')
        self.assertNotEqual(self.audit['DCP-LETT-377']['sender_evidence'][0]['attributes']['key'],
                            self.audit['DCP-LETT-378A']['recipient_evidence'][0]['attributes']['key'])
        validate_participants(p,self.audit['DCP-LETT-377'],self.audit['DCP-LETT-378A'],self.letters)
    def test_year_upper_bound_does_not_become_march_receipt(self):
        n=self.nodes['DCP-LETT-500']
        self.assertEqual(n['known_by_date'],'1839-12-31')
        self.assertIsNone(self.nodes['DCP-LETT-501']['whole_letter_scalar_date'])
        e=next(e for e in self.graph['edges'] if e['type']=='knowledge_before' and e['source']==n['id'])
        self.assertEqual(e['witness_date_policy'],'conservative_editorial_year_upper_bound')
        self.assertIsNone(e['actual_receipt_date'])
    def test_wedding_knowledge_is_not_a_conversation_prompt(self):
        es=[e for e in self.graph['edges'] if e['source']=='DCP-LETT-431' and e['target']=='DCP-LETT-437']
        self.assertEqual(len(es),1);self.assertEqual(es[0]['type'],'knowledge_before')
        self.assertFalse(es[0]['direct_prompt'])
        self.assertEqual(es[0]['known_by_date'],'1838-11-14')
        self.assertFalse(any(e['type']=='replies_to' and e['source']=='DCP-LETT-437' for e in self.graph['edges']))
    def test_candidates_never_activate_knowledge(self):
        forbidden={('DCP-LETT-535','DCP-LETT-629A'),('DCP-LETT-548','DCP-LETT-629A'),('DCP-LETT-1147','DCP-LETT-558F')}
        self.assertFalse(any(e['type']=='knowledge_before' and (e['source'],e['target']) in forbidden for e in self.graph['edges']))
        self.assertFalse(any(e['type']=='replies_to' and (e['source'],e['target']) in {('DCP-LETT-565','DCP-LETT-557F'),('DCP-LETT-676','DCP-LETT-671A')} for e in self.graph['edges']))
    def test_reverse_replies_are_not_Darwin_receipt(self):
        for i in ['DCP-LETT-381A','DCP-LETT-415B','DCP-LETT-723']:
            es=[e for e in self.graph['edges'] if e['type']=='replies_to' and e['source']==i]
            self.assertTrue(es)
            self.assertTrue(all(not e['activates_Darwin_knowledge'] and not e['is_Darwin_response'] for e in es))
        self.assertIsNone(self.nodes['DCP-LETT-415B']['known_by_date'])
    def test_grounding_partition_has_no_held_or_response_records(self):
        grounds=set(self.summary['reviewed_grounding_ids'])
        responses={p['outgoing_id'] for p in self.decisions['direct_reply_pairs']}
        eligible={i for i,n in self.nodes.items() if n['individual_Darwin_voice_eligible']}
        self.assertFalse(grounds & responses)
        self.assertEqual(grounds | responses,eligible)
        self.assertEqual(len(eligible),314)
        self.assertEqual(len(grounds),292)
        self.assertTrue(all(self.nodes[i]['effective_period_eligible'] for i in grounds))
    def test_relationship_counts_are_not_independent_examples(self):
        self.assertEqual(self.summary['confirmed_direct_reply_links'],24)
        self.assertEqual(self.summary['distinct_Darwin_response_letters'],22)
        self.assertEqual(self.summary['single_date_direct_reply_links'],19)
        self.assertEqual(self.summary['section_dependent_direct_reply_links'],5)
        self.assertEqual(self.summary['cross_correspondent_knowledge_links'],16)
        self.assertEqual(self.summary['reverse_reply_links_not_Darwin_outputs'],28)
        self.assertTrue(all(n['training_export_ready'] is False for n in self.nodes.values()))
        typed=Counter((e['type'],e['source'],e['target']) for e in self.graph['edges'])
        self.assertEqual(set(typed.values()),{1})

if __name__=='__main__':unittest.main()

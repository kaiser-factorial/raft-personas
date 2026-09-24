"""Render reviewed counts and source-linked findings; infer no relationships."""
import json
from collections import Counter
from pathlib import Path
from build_expansion_review import BASE,DEST,REMAINING,load_decisions,read,write,digest
from fetch_metadata import ROOT


def link(ident):
    return f"[{ident.removeprefix('DCP-LETT-')}](https://www.darwinproject.ac.uk/letter/?docId=letters/{ident}.xml)"


def main():
    d,sources=load_decisions(); s=read(DEST/'summary.json'); prior=read(REMAINING/'prior_expansion_summary.json')
    old=read(REMAINING/'prior_expansion_graph.json')
    old_pairs={(e['target'],e['source']) for e in old['edges'] if e['type']=='replies_to' and e.get('is_Darwin_response')}
    new=[p for p in d['direct_reply_pairs'] if (p['incoming_id'],p['outgoing_id']) not in old_pairs]
    graph=read(DEST/'graph.json'); nodes={n['id']:n for n in graph['nodes']}
    assert len(new)==8
    reasons={
      ('377','378A'):'Treasury grant instructions explicitly acknowledged by date.',
      ('381A','402A'):'October approval explicitly cited when submitting the first account; distinct Treasury officials.',
      ('402B','402F'):'Children asks about Gray’s conduct; Darwin answers with his experience.',
      ('402C','424A'):'Darwin explicitly follows the Treasury letter’s dated payment instructions.',
      ('504','506'):'Whewell’s marriage gift and accompanying letter are acknowledged.',
      ('534','545'):'Humboldt’s sea-temperature question receives a detailed answer.',
      ('565H','585'):'Distinctive packet of meteorological papers and geological reports, plus an explicit letter reference. A separate missing cover note remains possible.',
      ('717','722'):'Hooker’s botanical questions are acknowledged; Darwin adds observations about his collections.'}
    table=['| Surviving incoming → Darwin response | Knowledge established by | Identification |','|---|---|---|']
    for p in sorted(new,key=lambda p:p['known_by_date']):
        a,b=p['incoming_id'],p['outgoing_id']; key=(a.removeprefix('DCP-LETT-'),b.removeprefix('DCP-LETT-'))
        table.append(f"| {link(a)} → {link(b)} | {p['known_by_date']} | {reasons[key]} |")
    text=f'''# Complete review of the selected 1837–1843 inventory

All **476 source records** in the frozen candidate inventory have been inspected. All **474 surviving transcriptions** were read; **699F** has no available transcription and **13864** contains only a catalogue synopsis. The three Luna reviewers made first-pass proposals for the remaining **363 records**, followed by primary-agent full-source reading and adjudication. The earlier 113-record phase and the 1828–1836 corpus remain preserved.

| Result | Previous phase | Completed inventory |
|---|---:|---:|
| Reviewed source records | {prior['reviewed_source_record_count']} | {s['reviewed_source_record_count']} |
| Available transcriptions read | {prior['full_read_count']} | {s['full_read_count']} |
| Supported incoming → Darwin reply links | {prior['confirmed_direct_reply_links']} | {s['confirmed_direct_reply_links']} |
| Distinct Darwin response records | {prior['distinct_Darwin_response_letters']} | {s['distinct_Darwin_response_letters']} |
| Single-date reply links | {prior['single_date_direct_reply_links']} | {s['single_date_direct_reply_links']} |
| Section-dependent reply links | {prior['section_dependent_direct_reply_links']} | {s['section_dependent_direct_reply_links']} |
| Cross-correspondent knowledge links | {prior['cross_correspondent_knowledge_links']} | {s['cross_correspondent_knowledge_links']} |
| Reverse replies by correspondents | {prior['reverse_reply_links_not_Darwin_outputs']} | {s['reverse_reply_links_not_Darwin_outputs']} |
| Incoming records with known-by evidence | {prior['incoming_records_with_known_by_evidence']} | {s['incoming_records_with_known_by_evidence']} |

The **19 single-date links plus five section-dependent links** involve **22 Darwin response records**. Two inputs can contribute to one response, and one input can contribute to more than one response; these are relationship counts, not 24 independent training examples.

There are **314 period-eligible, individually attributed Darwin body records**: 22 have identified surviving prompts and **292 do not**. The latter remain grounding candidates with their date ranges and text-scope restrictions. “No identified prompt” does not prove that no response was written. All source records have now been reviewed; unavailable text is not labelled unread.

Across the reviewed 1828–1836 and 1837–1843 periods, the unchanged five earlier pairs bring the total to **24 single-date pairs**, or **29 links across 27 Darwin response records** including dated sections. The earlier **135 → 139** relation remains date-held and additional.

## Eight newly accepted reply links

{chr(10).join(table)}

The Treasury correspondence preserves Baring and Spearman as separate people. Documented official roles explain the connection; no identity alias was invented. The Admiralty response **415B → 415A** and Treasury response **381A → 378A** are reverse replies by officials, not Darwin outputs or proof that he received them on their composition dates.

## Knowledge without a direct reply

Five new cross-correspondent links were accepted: **377A → 378A**, **431 → 437**, **456 → 483**, **487 → 489**, and **500 → 501**. They respectively concern a publisher’s plan, Caroline’s congratulations, the Henslows’ invitation, Herbert’s distinctive wedding gift, and FitzRoy’s advertising approval. Incoming prose remains attributed context and never supplies Darwin’s voice.

Letter437 says Caroline’s letter arrived “yesterday”; the inferred calendar day is recorded separately from the conservative writing-date witness on14November1838. Its later paragraph also records an Emma-to-Catherine note arriving during composition; that third-party letter is not added as an incoming corpus prompt.

Letter501’s assigned21March1839 date is less secure than the XML alone suggests. The map conservatively uses **1839-12-31** as the latest supported writing bound for 500’s knowledge attestation, retaining the original assigned date and the source-before-witness relationship. It does not invent a December receipt or expose the information to unrelated March responses.

The Malcolmson supplementary search found plausible connections but no uniquely established new Darwin witness. The Allan presentation-copy route and generic references to private communications remain candidates; their proposed dates do not enter the accepted knowledge map. The bounded1836/1837 boundary check likewise added no pair; it is not an exhaustive proof of absence across the earlier corpus.

## Date, text and voice holds

The **raw XML audit remains445 safe / 31 held**. The evidence overlay conservatively holds two more records, leaving **443 period-eligible / 33 held**:

- **631:** an editorial note permits a Shrewsbury visit as late as November1848, beyond the XML’s July1841 range.
- **13803:** the title supplies a questioned upper bound before the end of1839; connection to the1839 questionnaire is only conjectural. The primary adjudicator therefore leaves the lower bound unresolved, disagreeing with the Luna recommendation to treat it as securely within1839. Both assessments and the original XML remain available.

**677** is withheld from Darwin voice because the catalogue raises possible forgery or corruption. **421F, 512 and 612** are joint documents, excluded from individual voice. These categories overlap date holds and should not be added as if they were disjoint.

Catalogue narration is excluded from the permitted Darwin text in **451, 609F, 698 and 13865**. **545** has a trailing repository caption, excluded from its response scope. **675** preserves a main fragment and possibly separate postscripts. **350F** survives in published French wording and is flagged separately for an English voice export. Other fragments, quoted matter, tables, scribal hands and uncertain dates remain attached to their source records. No normalized “complete letter” is fabricated.

There are **103 whole-letter exact-date review flags** among the raw XML-safe inventory; reliable dated sections remain separate. Incoming composition dates never become receipt dates automatically, and later paragraphs cannot supply earlier paragraphs with information.

## Audit trail and reproduction

- [Current graph](../correspondence-map/graph.json), [summary](../correspondence-map/summary.json), [incoming knowledge dates](../correspondence-map/incoming_knowledge_dates.jsonl).
- [Parent review](parent_review.json), [completion reconciliation](reconciliation.json), [work status](work_status.json).
- [Append-only adjudication ledgers](../../../data/annotations/remaining_1837_1843/), [Luna reports and preserved initial versions](reviews/), [primary full-reading notes](parent-reading/), [primary decisions](parent-decisions/).
- [Frozen selection](selection.json), [source manifest](../../../data/raw/dcp/remaining-review-1837-1843/manifest.json), [prior-phase hashes](baseline_hashes.json).

The final validator checks source/XML hashes, quoted evidence, packet coverage, primary dispositions, text offsets, source eligibility, dated-section coverage, and preservation of earlier relationships. The full test suite has **88 passing checks**. The initial no-transcription claims caused by reading the metadata XML instead of the public body were rejected; corrected full-body reviews and initial reports are preserved.

```sh
python3 scripts/build_expansion_review.py
python3 scripts/report_remaining_review.py
python3 -m unittest discover -s tests -q
```

## What remains before training

The selected inventory’s correspondence audit is complete. RAFT export still needs final transcript cleanup, segment-level context assembly, an explicit persona date policy, and evaluation splits that keep linked exchanges together. The292 grounding candidates must retain their date uncertainty and voice scopes. Some prompts and exact receipt dates are unrecoverable from the surviving letters; they remain missing rather than being synthesized. No training export or model training has run.

Coverage is bounded by the frozen476-record selection rule. It is not an XML-wide re-dating of every record in the full catalogue, nor completion of the remaining Beagle-voyage matching work.
'''
    # Keep readable spacing around identifiers in prose without changing source quotations.
    replacements={'letter437':'letter 437','Letter437':'Letter 437','Letter501':'Letter 501','on14November1838':'on 14 November 1838','assigned21March1839':'assigned 21 March 1839','bounded1836/1837':'bounded 1836/1837','XML audit remains445':'XML audit remains 445','safe / 31':'safe / 31','November1848':'November 1848','July1841':'July 1841','of1839':'of 1839','the1839':'the 1839','within1839':'within 1839','frozen476':'frozen 476','The292':'The 292'}
    for a,b in replacements.items():text=text.replace(a,b)
    (REMAINING/'README.md').write_text(text)
    (DEST/'README.md').write_text(f'''# 1837–1843 correspondence map

The [complete source review](../remaining-review/README.md) covers all476 selected records and474 surviving transcriptions. The map preserves24 incoming-to-Darwin reply links across22 response records,16 cross-correspondent knowledge links and28 reverse replies. Nineteen reply links have single-date responses; five require dated sections. There are292 eligible unpaired Darwin grounding records.

Raw XML eligibility remains445 safe and31 held. The editorial overlay adds holds for631 and13803. Joint authorship, unavailable text, disputed attribution, excerpts and catalogue narration have separate fields and must be respected by any export. Thirty-two of131 incoming records have known-by evidence; the other99 have no accepted activation date.

The graph retains original CSV rows, XML constraints, hashes, body sources, exact quotations, text scopes, response sections, within-day events and unresolved candidates. Institutional participant overrides apply to individual evidenced relationships; they never merge people. Reverse replies do not establish Darwin receipt. A known-by date is an upper bound, not necessarily an arrival day, and generic same-day retrieval still needs ordering evidence.

Rebuild with `python3 scripts/build_expansion_review.py`. This composes explicit append-only decisions and validates evidence; it does not infer new links. The1828–1836 graph and earlier phase ledgers/reviews remain unchanged. No training export has run.
'''.replace('all476','all 476').replace('and474','and 474').replace('preserves24','preserves 24').replace('across22','across 22').replace(',16',', 16').replace('and28','and 28').replace('are292','are 292').replace('remains445','remains 445').replace('and31','and 31').replace('for631','for 631').replace('and13803','and 13803').replace('of131','of 131').replace('other99','other 99').replace('The1828','The 1828'))
    snapshot=dict(status='complete',inventory_records=476,prior_reviewed_records=113,new_reviewed_records=363,available_transcriptions=474,missing_transcriptions=s['source_records_without_transcription'],remaining_unreviewed_records=0,new_direct_links=len(new),new_cross_knowledge_links=s['cross_correspondent_knowledge_links']-prior['cross_correspondent_knowledge_links'],new_reverse_links=s['reverse_reply_links_not_Darwin_outputs']-prior['reverse_reply_links_not_Darwin_outputs'],summary=s,training_export_performed=False,baseline_verified=True,validation_command='python3 -m unittest discover -s tests -q',tests_passed=88)
    write(REMAINING/'reconciliation.json',snapshot)
    print(json.dumps({k:snapshot[k] for k in ('inventory_records','new_reviewed_records','new_direct_links','new_cross_knowledge_links','new_reverse_links')}))

if __name__=='__main__':main()

"""Package manually reviewed body-date findings and the searchable candidate index."""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/body-date-search-37-337"

# These interpretations were reviewed against the preserved transcriptions.
# The anchors are checked against the extracted bodies on every build.
REVIEWED = [
    (37, "Year stated in the prose", ["remember it is 1828"],
     "Fanny Owen explicitly identifies the year in the body. This supports 1828 but does not independently establish the editorially supplied January date."),
    (120, "Return and discovery of waiting letters", ["Monday 29th of August", "I found your letter there"],
     "Darwin links his return from the Welsh geological trip on 29 August to finding letters waiting. This is a dated event in the body, rather than the 6 September date of the outgoing letter. Individual documents still need matching."),
    (158, "Several dated writing sections", ["8th of February", "Feb 26th.", "March 1st."],
     "The letter contains writing on 8 February, 26 February, and 1 March 1832. Retain those sections; a single earliest date would place later observations too early."),
    (164, "Explicit receipt on a dated morning", ["April 5th.", "I this morning received your letter of Decr 31 & Catherines of Feb 4th"],
     "The section dated 5 April 1832 identifies receipt that morning of Caroline's 31 December letter and Catherine's 4 February letter. The record as a whole spans 2–6 April, so 2 April cannot be the availability date for this batch."),
    (169, "Receipt day inside a broadly dated letter", ["Susans (& one from Mr Owen) I received May 3d"],
     "Darwin gives 3 May as the day he received letters from Susan and Mr Owen, within a letter catalogued May–June 1832. The year comes from the letter context; the incoming documents still require matching."),
    (179, "Impossible date retained as evidence", ["31st of June"],
     "Catherine reports receiving a letter on 31 June, which is not a valid calendar date. Preserve the wording and flag it for review; do not choose a replacement day or month automatically."),
    (188, "Dated batches and a parcel without new letters", ["November 14th.", "One from Catherine July 25", "Neither the Captain or myself have received"],
     "The 14 November 1832 section names letters from Catherine (25 July), Susan (15 August), and Erasmus (18th, month implicit). The 24 November section distinguishes arrival of a box from non-arrival of letters. Do not flatten all receipt evidence to the record's 24 October start."),
    (203, "Continuation month corrected by an editor", ["March 8th."],
     "A continuation is labelled March 8 in the transcription. Editorial footnote 9 identifies the month as an error for April. Retain the original March wording and the separate editorial correction; do not interpret it as an earlier receipt or writing event."),
    (206, "Separate May, June, and July knowledge states", ["following string of letters", "June:— I have just received a bundle more letters", "July 14th.—", "the April one alas is lost"],
     "The opening section dated 22 May 1833 acknowledges five letters dated September through January. A June section adds February and March letters plus notes. The 14 July section acknowledges Caroline's May letter and reports an April letter missing. Context available in July must not be supplied to the May section."),
    (225, "A correspondent disputes a missing-letter inference", ["I do not think there was any April Letter lost"],
     "Catherine explains that the April slot in their writing rotation may correspond to a letter dispatched at the end of March. This is evidence about naming and scheduling, not proof that Darwin had read her explanation before its own receipt is established."),
    (248, "Later section adds another received batch", ["July 29th., Valparaiso", "I have just received 3 letters", "Feb 12th"],
     "The section dated 29 July 1834 acknowledges three family letters, the latest from Susan dated 12 February, plus books and notes. The letter began on 20 July; the later batch should not become context for the earlier section."),
    (251, "Long-delayed incoming letters and an unsent outgoing letter", ["One is dated Dec 12th. 1833", "the other Jan: 15th of the same year", "This letter has been lying in my port-folio ever since July"],
     "In the opening section dated 24 July 1834, Darwin acknowledges Henslow letters dated 12 December and 15 January 1833 received together. On 28 October he explains that this outgoing letter has remained unsent since July; it continues into November. The catalogue's sent action describes a writing span here, not one proven posting day."),
    (271, "Later months received while earlier ones are missing", ["Katty Sept. & Caroline, October", "The June, July, August ones have miscarried"],
     "In March 1835 Darwin reports receiving September and October letters while June–August letters remain missing. Receipt of a newer letter cannot activate every earlier letter in the catalogue."),
    (281, "Missing batch recovered; corrected continuation date", ["I have received the three months letters which were missing", "July [August] 12th", "chain complete from England to February 1835"],
     "Darwin first reports recovery of three missing months, then three more letters in the continuation labelled July [August] 12th. Editorial footnote 1 explains the August correction. His stated completeness concerns this home-correspondence sequence, not every incoming correspondent."),
    (282, "Explicit reversal of arrival order", ["one dated June & the other November 1834", "They reached me however in an inverted order"],
     "Darwin explicitly says Fox's June and November 1834 letters reached him in reverse order. The outgoing letter is dated 9–12 August 1835; it does not supply the separate exact arrival days."),
    (289, "Receipt tied to a voyage event", ["the day before finally leaving the Galapagos", "your letter of March"],
     "The December 1835 letter recalls receiving Caroline's March letter the day before final departure from the Galapagos. This separates the age of the received letter from the time of delivery and supplies a voyage-relative receipt constraint, without inventing a calendar day."),
]


def main():
    letters = {r["id"]: r for r in map(json.loads, (REPORT / "letters.jsonl").read_text().splitlines())}
    hits = list(map(json.loads, (REPORT / "date_references.jsonl").read_text().splitlines()))
    summary = json.loads((REPORT / "summary.json").read_text())
    findings = []
    for number, label, anchors, interpretation in REVIEWED:
        letter = letters[f"DCP-LETT-{number}"]
        evidence = []
        for anchor in anchors:
            matches = [p for p in letter["paragraphs"] if anchor in p["text"]]
            if not matches:
                raise ValueError(f"Review anchor not found: {letter['id']}: {anchor}")
            for p in matches:
                start = p["text"].index(anchor)
                evidence.append({"anchor": anchor, "body_paragraph": p["body_paragraph"],
                                 "char_start": start, "char_end": start+len(anchor),
                                 "locator": p["locator"]})
        findings.append({"letter_id": letter["id"], "label": label,
                         "direction": letter["direction"], "interpretation": interpretation,
                         "evidence": evidence, "original_csv": letter["original_csv"],
                         "source": letter["source"], "automatic_recoding_applied": False})
    (REPORT / "reviewed_findings.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2)+"\n")
    dated = [h for h in hits if h["candidate_group"]=="dated_correspondence_candidate"]
    columns = ["letter_id", "direction", "letter_date_original", "body_paragraph", "matched_text",
               "reference_kind", "context", "source_url", "id"]
    with (REPORT / "dated_correspondence_candidates.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader(); writer.writerows(dated)
    groups = summary["reference_groups"]
    unique = summary["unique_letters_by_group"]
    lines = [
        "# Dates below the introduction: letters 37–337", "",
        f"Searched the available online body text for **{summary['selected_letters']} records involving Charles Robert Darwin** "
        f"({summary['direction_counts']['from_darwin']} outgoing; {summary['direction_counts']['to_darwin']} incoming), "
        f"covering approximately **{summary['body_words_searched']:,} words**. Headers, salutations, editorial footnotes, summaries, and marked supplemental editorial text were excluded from the search.", "",
        "The initial substantive paragraph was retained: it often contains the strongest receipt acknowledgment. We used the site's marked body region instead of discarding the first few visual lines, which vary with layout. Dates later in the body, closing matter, or postscripts remain searchable.", "",
        "## Results", "",
        "| Search category | Matches | Letters |", "| --- | ---: | ---: |",
        *[f"| {label} | {groups.get(key,0)} | {unique.get(key,0)} |" for key,label in [
            ("dated_correspondence_candidate", "Calendar/date expressions near correspondence wording"),
            ("relative_correspondence_candidate", "Relative-time expressions near correspondence wording"),
            ("internal_dateline", "Short dates elsewhere in the body or closing matter"),
            ("other_body_temporal_reference", "Other temporal references")]], "",
        f"There are **{summary['reference_count']:,} candidate references in {summary['letters_with_temporal_references']} letters**. "
        "These are search hits, not all proven receipt events. Some refer to future plans, dispatch instructions, durations, historical events, or unrelated prose near a letter reference. Counts overlap at letter level. The manually reviewed findings below identify stronger chronological evidence.", "",
        "## Reviewed findings", "",
        "| Letter | Evidence and significance |", "| --- | --- |",
    ]
    for finding in findings:
        num = finding["letter_id"].removeprefix("DCP-LETT-")
        paras = ", ".join(str(i) for i in sorted({e["body_paragraph"] for e in finding["evidence"]}))
        lines.append(f"| [{num}]({finding['source']['url']}) · body block(s) {paras} | **{finding['label']}.** {finding['interpretation']} |")
    lines += ["", "## Letter 303 and other representation limits", "",
        "The [303 source page](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-303.xml) distinguishes a main communication apparently written by FitzRoy and signed by him alone from the short concluding paragraph bearing both names. The page transcribes that conclusion, not the entire main communication. We retained it for this chronology search and explicitly excluded it from Darwin's individual-voice training material in `data/annotations/text_attribution.json`.", "",
        "[330](https://www.darwinproject.ac.uk/letter/?docId=letters/DCP-LETT-330.xml) is a third-person minute-book report of a Darwin letter, not a verbatim Darwin transcription; it carries the same voice-training exclusion. Jointly authored incoming records 153, 266, and 291 retain all sender evidence. No training has been run.", "",
        "These are known representation limits, not a claim that every other transcription is complete or a finished authorship audit.", "",
        "## What this changes about chronological preparation", "",
        "Darwin's own dated writing remains the reference point. Where a letter has several dated sections, however, use the section containing the acknowledgment to constrain availability. The whole record's earliest catalogue date cannot safely be applied to all of its later contents. A final date can give a conservative upper bound, but does not prove that earlier sections knew the later information. Letter 251 also shows why an XML action labelled `sent` is not by itself proof of a single actual dispatch day.", "",
        "Keep dates mentioned for other letters, dates of receipt, dates of writing, plans, and editorial corrections distinct. References in incoming letters may date what the sender knew; they do not automatically date Darwin's receipt of that incoming letter. No candidate in this search has been automatically converted into a new reply link or knowledge date. The prior three established links and original XML audit remain intact.", "",
        "## Coverage and preserved evidence", "",
        "The range includes numeric IDs 37–337 plus the catalogue's suffix entries 45A, 102A, and 135A. Sixteen third-party records in the CSV were excluded. The three integer gaps were checked on the site: 156 and 194 are cancelled as not clearly letters, and 174 is a cancelled third-party letter. Their pages were preserved solely to document those dispositions. This accounts for all 301 requested integer IDs plus four suffix entries (the fourth, 289F, is third-party and excluded).", "",
        "Letter 326 is searched because it falls in the requested ID range, but its possible 1837 date still excludes it from the safe 1828–1836 training set. High-numbered 3150F and 13858 are outside this ID search and remain held in the earlier date audit.", "",
        "- [Dated correspondence candidates](dated_correspondence_candidates.csv): the focused review table, with original letter dates, matched text, nearby prose, body block, and source URL.",
        "- [All body-date references](date_references.csv): the broader search, including relative expressions and internal datelines.",
        "- [Reviewed findings](reviewed_findings.json): the manually checked interpretations with exact evidence anchors and source hashes.",
        "- `letters.jsonl`: extracted bodies, marked exclusions, untouched CSV metadata, XML date evidence, attribution annotations, and source provenance.",
        "- `date_references.jsonl` and `correspondence_candidates.jsonl`: detailed match offsets and review status.",
        "- [Summary](summary.json): counts, coverage, and limitations.",
        "- `data/raw/dcp/body-date-search-37-337/manifest.json`, relative to the project root: original HTML paths, retrieval times, byte counts, hashes, complete selection metadata, and gap checks. Eight already-preserved pages are referenced from the earlier receipt case study.", "",
        "Whitespace was normalized and footnote markers removed for searching; original HTML bytes were preserved. Offsets and body-block numbers refer to the normalized extraction. One unusual layout, 190, uses its entire cleaned body as one block so prose outside paragraph tags is retained.", "",
        "## Reproduce", "",
        "Use Python 3.11 or newer with `lxml` (available in the bundled workspace Python runtime). From the project root:", "",
        "```sh", "python3 scripts/fetch_letter_bodies.py", "python3 scripts/search_body_dates.py", "python3 scripts/build_body_date_report.py", "python3 -m unittest discover -s tests -v", "```", "",
        "The fetcher reuses hash-verified snapshots and makes at most three concurrent requests. The search is heuristic; uncommon date spellings and indirect allusions may require further review. Original dates, approximate wording, impossible dates, and corrections remain visible. Tests cover header/editorial exclusion, first-paragraph retention, historical date punctuation, misleading modal 'may', impossible dates, and unusual body layouts.", ""
    ]
    (REPORT / "README.md").write_text("\n".join(lines))
    print(f"Validated {len(findings)} reviewed findings; wrote report and {len(dated)} focused candidate rows.")


if __name__ == "__main__":
    main()

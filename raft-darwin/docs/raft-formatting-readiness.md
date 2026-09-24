# RAFT formatting readiness

The latest user requirements are recorded in [the final export content policy](raft-export-content-policy.md): after adjudication, export confirmed conversation pairs and unpaired Darwin grounding letters, checking every entry for header, footnote and annotation exclusion and supported transcription repairs. Current cumulative export state is recorded in the [export manifest](../reports/raft-export/manifest.json) and [written-file validation](../reports/raft-export/validation.json); the preparation history below does not supersede those records. Older research admissions alone do not establish content eligibility.

Audited 2026-09-16 against the installed `/opt/anaconda3/bin/raft` launcher, Python 3.13 package `raft-ft==3.1.0`, HANDOFF.md §7, and the preserved Grok notes. The complete paths, SHA256s, and line references are in [implementation.json](../reports/raft-prep/implementation.json).

The format is usable for a carefully bounded Darwin export, but it is not a sufficient chronology or provenance layer. Keep the research ledgers and an export sidecar as the authority; treat RAFT files as a projection.

## Canonical files

For this project, use `conversations/transcript-0001.json`, `transcript-0002.json`, and so on, with 1-based four-digit numbering and no gaps. `ft:gen` increments from 1 and stops at the first missing file. Reserve `conversations/benchmark.json` for held-out evaluation. Grounding belongs in `corpus/documents.jsonl`, one JSON object per line.

The accepted transcript shape is:

```json
{
  "participants": {"q": "correspondent", "a": "Charles Darwin"},
  "date": "YYYY-MM-DD",
  "url": "source URL",
  "context": "a letter from correspondent, which Darwin is answering",
  "exchanges": [["proven incoming text", "Darwin response text"]]
}
```

`participants` must contain `q` and `a`; `exchanges` must contain two-element string lists. The recognizer accepts transcripts without `date` and `url`, but `ft:gen` operationally indexes both keys while constructing metadata, so exported files must include them (and `date` must be a valid chronology date). The direct `write_transcript` helper writes `context`, but `import_conversation_file` drops it while rewriting both transcript-schema and message-array inputs. Direct, validated writes are therefore required for letter context.

Before writing, validate: object shape; exact two strings per exchange; Darwin identity/authority; incoming and response IDs; source hashes; exact paragraph or Unicode code-point spans; original date constraints; response-section date; relation type; chronology order; and no held, joint, unavailable, third-party, or merely candidate material. Preserve a sidecar record for every emitted item.

## Chronology and retrieval

RAFT parses dates to `YYYYMMDD`. For a dated embedding collection and transcript date, retrieval applies `date_num < transcript_date` at the Chroma query. This is strict `<`, so same-day material is excluded. The query occurs before storing the current exchange, which avoids self retrieval in a clean run; it does not exclude a copy already in corpus/Chroma, a prior persistent run, or overlapping sections. All exchanges in one transcript share the transcript metadata date; a multi-exchange thread can therefore leak later knowledge into earlier turns. Use one demonstrated response or response section per transcript until a chronology-aware adapter exists.

An empty or unparseable corpus date becomes `date_num=0` and remains retrievable under the `<` filter. A null date must therefore be held out of strict historical retrieval, or handled in a separate controlled policy. Fetch-window filtering is inclusive (`since <= date <= until`) and rejects undated records when a bounded window is requested; that importer behavior is distinct from retrieval behavior.

The date on a transcript must describe the target response or section. It must not be substituted with the incoming letter date, a physical receipt date, a `known_by_date`, or a conservative upper bound. Dated Darwin grounding can be emitted only for permitted spans; an unpaired letter is grounding, never a fabricated prompt/answer.

## Voice, grounding, and attribution

Use a proven direct incoming → Darwin response relationship for `exchanges`. Several supported inputs may feed one response, and institutional routing may involve distinct officials; retain all edges in the sidecar and do not duplicate the answer as independent examples. Knowledge-only incoming material, reverse replies, quotations, editorial prose, and third-party letters remain outside the direct transcript unless the evidence specifically establishes the exchange.

Grounding records use the minimal fields `title`, `link`, `date`, and `content`. Incoming letters should not be placed there as if they were Darwin voice: the installed summarizer explicitly says the retrieved passage is something the persona “wrote or said earlier,” and returned metadata (`participants`, `url`, `title`) is not an attribution guarantee. Preserve incoming-only knowledge such as 312 → 313 in the research graph/sidecar. Do not route it into Darwin-authored corpus text until a separately attributed context mechanism is verified.

The installed embedding helpers form grounding IDs from title plus chunk part, and exchange IDs from the alphanumeric URL plus the question's first 20 characters. Exported grounding titles therefore include the DCP source/section ID. Transcript URLs use unique export fragments for separate response sections; these identify the exported units and are not claimed to be native website anchors. The canonical source URLs remain in the provenance sidecar.

The generated generic example contains `question`, `answer`, and optionally `similar_memories`; OpenAI conversion produces a user message, optional system “Relevant memories” message, and assistant answer. The HF runner requests `completion_only_loss=True`, which should supervise completion tokens, but this audit did not run a tokenizer/model/trainer. Treat training readiness as pending that independent check.

## Mapping recommendations

Represent each accepted dated Darwin response section as one transcript. For a letter with several supported incoming inputs, keep one exchange whose question contains the verified inputs in evidence order, with correspondent identities and provenance in the sidecar. If the inputs cannot be represented without flattening distinct voices, hold the item for an adapter. For a response written across dates, split at paragraph/code-point boundaries and emit only sections with defensible dates.

Represent institutional routing per edge: preserve the actual incoming correspondent in `participants.q` where one person is the questioner, and hold or sidecar-qualify cases where several officials jointly constitute the prompt. Preserve cross-correspondent knowledge as attributed sidecar context, not as a synthetic dialogue. Incoming-only knowledge can inform a later Darwin response only when the dated witness supports it; it does not become a Darwin corpus document.

Keep linked exchanges, repeated target copies, excerpts, alternate versions, and related sections together in train/evaluation assignment. Exclude the current target, all future material, duplicate targets, and benchmark material from retrieval and training. A benchmark filename alone does not enforce every leakage rule.

## Readiness boundary

Source-text fidelity is specified in the [primary rendering requirements](../reports/raft-prep/source-text-rendering-requirements.primary.json), checked against nine preserved HTML sources. This corrects the preparation reports: mixed numbers must retain their integer part (Higgins writes **3¼ percent**, not ¼ percent); lists can have lost layout without any HTML `table`; authorial inscriptions can be inside `div.supplemental`; and later revisions can be embedded in the main body. Keep raw markup and dated voice layers in the sidecar. Hold any text-only example that depends on an unrepresented figure; an agent's modern description is not authentic incoming letter text.

Format readiness: **conditional**. The installed schema, numbering, direct-write behavior, strict date comparison (source inspected; mocked fixture does not exercise Chroma), corpus fields, duplicate-link behavior, and generic message shape are confirmed. The reproducible synthetic no-network fixture is [verify_no_network_fixture.py](../reports/raft-prep/fixtures/verify_no_network_fixture.py), with captured output in [verify_no_network_fixture.output.json](../reports/raft-prep/fixtures/verify_no_network_fixture.output.json). It confirms importer context loss, required date/url keys for generation, filename-order enumeration, fresh/resumed rebuild ordering, inclusive fetch-window behavior, and link-based duplicate suppression.

Training readiness: **not ready to claim**. The data-export manifest is distinct from training validation. No chunking/embedding, tokenizer rendering, collator labels, model training, cloud/provider run, or benchmark evaluation was executed. The opbdh source checkout sets `completion_only_loss=True`, but installed/runtime compatibility and tokenizer-specific masking remain actual access/verification gaps.

Grok’s notes were useful as secondary evidence, but the installed code confirms and corrects them as recorded in the manifest. In particular, context loss on import, conditional date filtering, null-date retrieval, and transcript-level rather than per-exchange dating require explicit handling before any Darwin export.

The primary source-fidelity requirements also have additive extensions, all
preserving the original reports: [addendum 01](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-01.json)
covers further missing originals and attribution cases;
[addendum 02](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-02.json)
covers accepted multi-day and joint-input cases;
[addendum 03](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-03.json)
covers batches 07–13 of 1847–1850;
[addendum 04](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-04.json)
covers batches 14–16;
[addendum 05](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-05.json)
covers batches 17–18, including delayed reading, missing drawings, literal versus
fractional numbers, and changing expectations; and
[addendum 06](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-06.json)
covers batches 19–22, including uncertain receipt dates, explicit multi-day sections,
lost manuscripts, overtracing and later recipient annotations;
[addendum 07](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-07.json)
covers batches 23–25, including non-decimal currency tables, institutional minutes,
production proposals, forwarded knowledge, damaged transcription and delayed access;
[addendum 08](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-08.json)
covers batches 26–28, including transcription variants, separate letter and parcel
receipts, family identities, knowledge bounds, collective documents and garbled text;
[addendum 09](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-09.json)
covers batches 29–31, including catalogue excerpts, unavailable bodies, partial
reading, mixed fractions, multi-day sections and missing correspondence endpoints;
[addendum 10](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-10.json)
covers batches 32–34, including omitted lists, draft repetitions, edition-specific
reading, negative receipt, mixed cover/proposal dates, abrupt endings and physical
letter order. Its primary verification corrects a draft provenance-hash typo.
[addendum 11](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-11.json)
covers the first 1851–1855 packet: MathML fractions versus flat text, an 1852
queries memorandum with later answer layers, and disjoint dates with partial
book inspection. Derived renderings are distinguished from exact quotations.
[addendum 12](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-12.json)
covers source-level numeric damage, verified half-hour MathML, authorial supplemental
prose, Emma’s postscript, synopsis-only inputs, separate-paper chronology, incoming
figures, joint-input output scopes and disjoint date alternatives. It corrects the
preparation draft’s overly definite dating of the 1712 postscript.
[addendum 13](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-13.json)
covers translated drafts, uncertain extract dates, the full 77-entry enclosure,
source numeric damage, MathML, diagram placement, and separate specimen/book access.
It corrects the preparation draft’s 1501 paragraph locator and distinguishes
observed HTML placement from unverified physical manuscript attachment.
[addendum 14](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-14.json)
covers the Fox packets: uncertain composition and later postscript news, third-party
forwarding, fractions, damaged lists, and acquisition versus receipt and reading.
It corrects draft quotation/paragraph errors and keeps derived fraction wording
separate from exact source text.
[addendum 15](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-15.json)
covers the Huxley packets: carrier status, authorial specimen memorandum, MathML,
receipt versus reading, annotated drawings and observations made during writing.
It corrects draft witness claims and quotation locators; separate complete
manuscript witnesses and clean incoming drawings have not been preserved here.
[addendum 16](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-16.json)
covers public inquiries, publication dates, later clipping amendments, successive
printed corrections, an embedded postscript and mediated reports. Primary checks
corrected eight draft DOM locators; exact body quotations alone had not verified
their positions in the original HTML.
[addendum 17](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-17.json)
covers the Blyth memoranda: mixed quotation voices, authorial marginalia, separate
undated Darwin notes, disjoint dates, MathML quantities, and three actual diagrams.
It corrects draft attribution and source-extent claims and pins verified DOM nodes.
[addendum 18](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-18.json)
covers Bosquet: omitted drawings, copied gaps, relative receipt, partial and
completed manuscript reading, later corrections and distinct publication stages.
Primary checks corrected attribution boilerplate and the supplied date component.
[addendum 19](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-19.json)
covers Ray Society and Bate: planned plate production, manuscript custody,
missing notes with demonstrable receipt, verified quarter-hour MathML and the
actual proboscis drawing; source fractions without markup remain held.
[addendum 20](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-20.json)
covers financial instructions and conflicting amounts, separate memorandum
sheets and later additions, offered versus received specimens, and four
disjoint-date cases. Original manuscripts were not inspected for physical layout.
[addendum 21](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-21.json)
covers book receipt before its nominal title year, completed versus partial reading,
recipient-added words, uncertain specimen custody and lost experiment layout.
Primary checks corrected a source-ID mixup, a truncated hash and reading-stage prose.
[addendum 22](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-22.json)
covers Covington receipt intervals and transcription layers, ninety-one date
alternatives, actual mixed-number MathML, the authorial Private label, missing
drawings and corrected family authorship. No converter has been implemented.
[addendum 23](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-23.json)
covers institutional minutes, private versus formal reports, unreceived figures,
untested instruments, revised custody memories, alternative years, partial oral
hearing, reply dockets and staged dispatch. Primary checks corrected the date
components and supplied three missing XML provenance pairs.
[addendum 24](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-24.json)
covers crossed drafts, mixed question sheets, continuous versus alternative date
windows, raw duplicated or damaged text, and the earlier Benson knowledge witness.
[addendum 25](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-25.json)
covers mixed authorship, collective memorial excerpts, incomplete sources,
personal receipt versus postal custody, and the recovered Parker question.
The Parker question was subsequently admitted in the additive record linked by addendum 41;
its exact endpoint excludes later editorial commentary in the same HTML node.
[addendum 26](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-26.json)
covers the Sulivan and family correspondence: the exact Charles/Emma boundary
inside a paragraph, distinct receipt and reading dates, prior knowledge witnesses,
uncertain date components, and preserved drawing evidence.
[addendum 27](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-27.json)
covers the first 1856 packets: verified fractions and handwriting boundaries,
alternative dates, swapped editorial summaries, Lyell's copied and unsent
material, distinct postal routes, inferred manuscript delivery and staged reading.
[addendum 28](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-28.json)
covers the separately transmitted Hooker memorandum, dated postscripts, verified
clock and owl-duration fractions, distinct receipt claims, corrected manuscript
hands, inconsistent botanical totals and the missing Hooker ending.
[addendum 29](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-29.json)
covers duplicate fraction fallbacks, experimental table rows, ranked botanical
underscoring, an enclosed memorandum with uncertain interlining, separate Darwin
notes and a correction made within a letter. Raw fallbacks remain evidence;
future clean text must represent each quantity once.
[addendum 30](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-30.json)
covers 25 MathML fractions, the 6¾-ounce mixed number, four raw datelines, an
empty query-sheet section, separate receipt events, the three-leaf diagram and
Gray’s tree and flora tables. Primary checks distinguish leaf positions from
a time series and preserve the unresolved October Friday date.
[addendum31](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-31.json)
covers receipt dockets, the quarter fraction and substantive erratum, qualified
range counts, hypothetical examples and separately attributed Watson material.
[addendum32](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-32.json)
covers eight fractions, unresolved plain digits, missing corrected copies,
uncertain dates, separate filing history and Darwin’s authorial marginal note.
[addendum33](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-33.json)
covers the full eight-paragraph abstract enclosure, Darwin’s authorship and
corrections to Norman’s copy, unmarked proportions, expected unpublished material,
limited experiments and the missing November Gray prompt.
[addendum 34](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-34.json)
covers catalogue extracts, copy corrections, mixed hands, both Woodward drawings,
plain digits and flattened shell lists. It corrects four paragraph locators and
one mistyped candidate XML hash.
[addendum 35](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-35.json)
resolves the four 2136 ratios from the original Harvard manuscript: 88/1000,
50/1000, 48/1000 and 46/1000. Raw web text remains preserved; the additive
facsimile record also distinguishes the final Darwin qualification from the
preceding copied enclosure.
[addendum 36](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-36.json)
covers Lyell's copied and unsent sections, incomplete mammal list, manuscript
diagrams, receipt limits and the distinction between Madeira and a prior note's
typographical error. Primary checks corrected paragraph and source identities.
[addendum 37](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-37.json)
covers Dana's recovered continuation, gar-pike drawing, two mixed fractions,
the December 21 postscript receipt, quoted third-party voices, and separate
Bosquet drawing deliveries. It also records the Lyell supplement sender correction.
[addendum 38](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-38.json)
covers Huxley's numbered French extract, separate Darwin annotations, the
misclassified dateline, coach-time fraction, incomplete sources and copied
catalogue comments. Primary checks corrected body counts and raw locators.
[addendum 39](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-39.json)
covers Fox's Queen Pea observations, public-query response, distinct specimen
and letter arrivals, seven MathML fractions, and changing interpretations.
Fox's incoming observations remain separate from Darwin's reply.
[addendum 40](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-40.json)
covers missing botanical lists, mixed authorship, Lowe's contemporary copy,
plain digits without fraction markup, Doubleday's incomplete reply and the
separately dated February 8 Darwin note. Date ranges remain explicit.
[addendum 41](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-41.json)
covers the admitted Parker circular question and exact Darwin response. The
supplemental relationship is included once during cumulative reconciliation;
Mill's reply and later editorial material are excluded.
[addendum 42](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-42.json) covers Watson's dated header, list/enclosure structure, June 11–20 reply bound and dated knowledge annotation.
[addendum 43](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-43.json) covers Henslow's actual August 5 receipt, corrected year, fragment and superscript boundaries.
[addendum 44](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-44.json) covers Harcourt's complete bird inventory, uncertain reports, printed form and separate specimen custody.
[addendum 45](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-45.json) covers Wollaston's body fraction, excluded experimental-book fractions, 39-entry table, distinct papers and tentative dates.
[addendum 46](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-46.json) covers scoped Edmondston input, Harvey access and figure, Higgins copy/fraction/stamp, and Berkeley dispatch and embedded heading boundaries.
The [Bentham visual recovery](../data/annotations/reconciliation/1857-bentham-2186-visuals.primary.json) preserves eight verified manuscript derivatives and corrected mappings; full list transcription and expanded prompt scope remain unaccepted.
These are verified requirements for future implementation,
not implemented conversion behavior. Accepted primary decisions and source hashes
remain the authority when a provisional preparation draft differs.

[Addendum 47](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-47.json) records the scoped Wallace reply, reverse directions, uncertain dates and the DCP-only Davy absence boundary.
[Addendum 48](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-48.json) distinguishes Buckman’s five authorial enclosure questions from cover-body instructions, an annotation and an unavailable transcript.
[Addendum 49](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-49.json) separates raw layout preservation from required final cleanup and prevents later Poultry Book identity from being backdated.
[Addendum 50](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-50.json) verifies Daniell knowledge timing, nine-skin categories, currency markup, actual postscript boundaries and book receipt versus reading.
The [Davy publication recovery](../data/annotations/reconciliation/1855-1856-davy-publications.primary.json) admits two printed letter witnesses and two historical replies, with explicit version and date boundaries. It does not provide cleaned final transcript text.

[Addendum50 correction](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-50.correction.json) supersedes the recipient wording for1989: the letter is to J.D.Hooker. The accepted knowledge timing remains unchanged.
[Addendum51](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-51.json) records Davy printed witnesses, source versions, quoted versus abstract voice and distinct delivery/read dates. Its pinned draft was restored byte-for-byte after a misrouted overwrite; the [integrity record](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-51.integrity-restoration.json) preserves the recovery and both variants.
[Addendum52](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-52.json) covers Lubbock diagrams, actual fractions, unresolved optical numerals, weekday/date conflict and manuscript-versus-publication boundaries.
[Addendum53](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-53.json) covers family letter fragments, corrected quotation extent, actual currency/fractions and tentative dates.
[Addendum54](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-54.json) verifies2155’s inline editor exclusion, later Gray knowledge, open dates and specimen custody versus intended dispatch.

[Addendum 55](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-55.json) covers the complete Blyth enclosure, unlabelled spur and labelled Gallus figures, half-bred fraction and indirect knowledge boundaries. The [enclosure inventory clarification](../data/annotations/periods/1856-1857/addenda/batch-32-1817-enclosure-count.primary.json) supersedes the earlier section-count wording.
[Addendum 56](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-56.json) covers the explicit May 6 receipt, separate April 3 supplied date, copied Scott/Blyth voices, verified halves and source artifacts requiring supported cleanup.
The [Crump supplement](../data/annotations/reconciliation/1856-crump-blyth-supplement.primary.json) admits third-party manuscript evidence and all preserved facsimiles, with hearsay and transmitted-content boundaries; it supplies no Darwin voice or exact Darwin receipt date.

[Addendum 57](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-57.json) covers nested authorial enclosure quotations, mixed hands and verified fractions.

[Addendum 58](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-58.json) covers Crump manuscript layers and bounded absent-enclosure claims.

[Addendum 59](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-59.json) covers Gray/Birch receipt stages, embedded headers and discrete date alternatives.

[Addendum 60](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-60.json) covers Covington printed witnesses, medal weight and Barth reading stages.

[Addendum 61](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-61.json) covers Hewitt outcome denominators, recipient uncertainty and complete2062 body.

[Addendum 62](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-62.json) covers French fragments, seed experimental stages, authorial notes and book receipt.

The [2042 experimental-chain correction](../data/annotations/periods/1856-1857/addenda/batch-04-2042-experimental-chain.primary.json) and [2062 source-kind correction](../data/annotations/periods/1856-1857/addenda/batch-37-2062-source-kind.primary.json) are additive; prior accepted records remain immutable.

[Addendum 63](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-63.json) covers Gulliver denominators, quill aside and Glover figure.

[Addendum 64](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-64.json) covers mixed handwriting, uncertain sender, page marker and quarter fraction.

[Addendum 65](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-65.json) covers Bate questions, price arithmetic, absent annotation and Smith figure.

[Addendum 66](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-66.json) covers same-author rejection, completed ice cleavage, rabbit fraction, Waterhouse figure and date alternatives.

[Addendum 67](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-67.json) covers recovered Bishop routed response, ten body blocks, undated access and excluded address.

[Addendum 68](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-68.json) covers White pasted request, Westwood copied enclosure, institutional questions and date-bound holds.

The [Bishop supplement](../data/annotations/reconciliation/1857-bishop-bate-supplement.primary.json) is third-party context and a routed reverse response; it supplies no Darwin target or exact receipt date.

[Addendum 69](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-69.json) covers six verified fractions, the present classification enclosure, mid-composition receipt, unresolved text/layout artifacts and the corrected March reply.

[Addendum 70](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-70.json) covers the five-paragraph memorandum, uncertain Weddell spelling, July 13/15 sections, separate proof receipt and an evidenced `heatily` to `heartily` derivative repair.

[Addendum 71](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-71.json) covers the verified 4½-mile value, unresolved currency, donor-address boundaries, mixed Hooker/Darwin annotation layers, the November weekday conflict, and the bounded manuscript-arrival interval.

[Addendum 72](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-72.json) covers Gray's editorially described missing list, April receipt, separate August annotation, the verified flower diagram, partial reading and December endpoint holds.

The [de Vriese supplement](../data/annotations/reconciliation/1858-de-vriese-hooker-supplement.primary.json) and [Wallace-to-Hooker supplement](../data/annotations/reconciliation/1858-wallace-hooker-supplement.primary.json) admit separately attributed third-party knowledge sources. Their demonstrated access bounds are 25 November 1858 and 23 January 1859 respectively; neither supplies Darwin voice or an exact receipt date. The French original and modern English translation of de Vriese's letter remain distinct.

[Addendum 73](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-73.json) verifies the split sentence, literal more/less mismatch, Murray two-thirds and copy placeholders, evidenced repair versus conjecture, all three enclosure groups, mid-letter proof receipt, and both forwarded-source provenance records. The expanded reversion manuscript is absent; only its covering note survives.

[Addendum 74](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-74.json) verifies the proposed title enclosure, 9½ breakfast time and 1/8 gestation figure, itinerary artifact, combined Lyell inputs, deleted postscript, Darwin pencil insertions in Huxley text, actual query enclosure and preserved sketch. Erasmus's quoted passage has a surviving source in letter 2545; the quotation in 2547 is a separate-slip postscript, not an annotation or Darwin's own assertion.

The [Elwin-to-Murray supplement](../data/annotations/reconciliation/1859-elwin-murray-supplement.primary.json) preserves the forwarded publishing critique Darwin considered by 6 May 1859. It supplies third-party context only. Darwin's separate reply to Elwin is missing; neither that reply nor a Murray covering note may be reconstructed.

[Addendum 75](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-75.json) verifies Murray's duplicated passage and currency, the surviving proposed second-edition notice, actual fractions, uncertain November weekdays, Poole's split and damaged text, Smith's separate apparatus answers and three figures, and the admitted Elwin source. Repairs remain requirements for conversion, with unresolved readings held.

[Addendum 76](../reports/raft-prep/source-text-rendering-requirements.primary.addendum-76.json) verifies body fractions and excluded annotation calculations, Higgins's complete letter, Hill's damaged printed witness, the distinction between Jenyns's notes and missing full manuscript, Falconer's delayed dispatch, Owen's draft, Sedgwick's later receipt, Kingsley's missing later inputs, and Galton's surviving enclosure and split closing.

The [Hill printed-witness clarification](../data/annotations/reconciliation/1859-hill-2479A-printed-witness.primary.json) verifies the 1915 facsimile and both half fractions. The damaged honey/cell wording and probable `will` remain unresolved; the facsimile supplies no manuscript repair. Cundall’s query is editorial.


Brewer2421 source is separately admitted in [primary supplemental admission](../data/annotations/reconciliation/1858-brewer-gould-supplement.primary.json). Four retained blocks; third-party Brewer voice, undated CD notes and eight footnotes excluded. Known by Darwin2448 on6April[1858], actual delivery unknown. No direct conversation or corpus export. Candidate formatting notes through70remain subject to root verification.

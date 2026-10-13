# Proposed Phase 2 plan (plan only: nothing here is implemented)

**Principles:**
- Every item is behind `--method ARCH_TAKEOFF_V2.1` (opt-in).
- V1 stays byte-identical (15 / 16 files), and every freeze test stays green.
- No item is accepted on the reference plan alone. Each one needs its synthetic fixture, and the set needs the blind round (P2-12).

**Effort:** S ≤ 1 day, M 2–3 days, L 4–6 days (one engineer, including tests).

## A. Must fix before Phase 2 proper (prerequisites)

| Id | What | Defect ids | Files | Depends on | Effort | Benefit | Regression risk | Acceptance tests | Rollback |
|---|---|---|---|---|---|---|---|---|---|
| **P2-00** | Errata register for frozen releases; behaviour manifests for every freeze (inputs, command, output hashes) and their re-run tests | S6R-A2, S6R-B1; Investigation E | `research/errata/ERRATA.md` (new), `tests/freeze_behaviour/` (new) | — | S | known defects of frozen results become visible without editing them; prepares freeze-by-behaviour | none (no engine change) | every manifest reproduces byte for byte on HEAD | delete the new files |
| **P2-01** | Tolerance-aware predicate library; used for every length / gap / overlap / side threshold on the V2 band path | S6R-A1 (S6P1-NEW-05) | `engine/source/geom_predicates.py` (new, stdlib); `engine/source/band_census_v2.py` (new: `face_lines` / `wall_bands` / `band_gaps` built on the predicates; `opening_census.py` untouched); V2 branches in `arch_plan._bands`, `lintel_measure.openings` (policy `ROBUST`) | — | M | removes rotation / offset / unit-dependent coin flips; recovers the drafted door and window | V2 output changes on the reference plan (+1 door, +1 window, +0.20 m wall run): expected and reviewed | fixtures A0–A6 → 1 opening each; `a_method_comparison` ROBUST = 1.000 in every case; reference plan mm vs m: rooms, openings and lines identical (`qdiff`); V1 bytes unchanged; the strict xfail flips to a pass under V2.1 | `--tol UNIT_RELATIVE` (Phase 1 behaviour) |
| **P2-02** | Metamorphic suite at arbitrary angles and site offsets | S6R-A4 | `tests/m9_s6p2/test_metamorphic.py` (new) | P2-01 | S–M | catches the whole class of A1 defects | none (tests only) | synthetic villa under 12 transforms: V2.1 element counts equal, category areas ± 1e-4 m²; V1 failures recorded as strict xfail | remove the tests |
| **P2-03** | Unit- and translation-stable content ids | S6R-A3 | `engine/source/arch_completeness.py` (strip ids), the `SITE-` id helper | — | S | ids comparable across revisions and units | V2 ids change (not frozen) | the same strip has the same id in mm, m and translated drawings | old id helper |

## B. Phase 2 (ranked by real-villa reliability gained per unit of risk)

| Rank | Id | What | Defect ids | Files | Depends on | Effort | Benefit | Regression risk | Acceptance tests | Rollback |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **P2-04** | Door / window element conservation. Every drawn swing or window block ends in an opening (from the wall gap, or else from the symbol: width from the leaf / swing radius, PROVISIONAL) or an RFI `DOOR_NOT_MEASURED`. A CLOSED state may not exist without a line. Exit 3 on non-conservation | S6R-B1, NSD-2, ENG-D1 / D2 | `arch_rooms` (V2 branch of the door matching), `arch_completeness` (element gate), `urban_boq_m9` (exit 3) | P2-01 | M | the largest silent omission found (8 of 29 doors) | V2 door count and lintel / deduction inputs change | synthetic: a CLOSED-door fixture gives a door line; reference: swings = door lines + door RFIs (29 swings, one double-leaf pair); V1 bytes unchanged | V2 branch off |
| 2 | **P2-05** | Fills from K2 at every depth: MINSERT cells, layer-0 inheritance, SOLID / TRACE, arc-edged hatches flattened | D rows 1–4; S6P1-NEW-02; GEO-01, 03, 04, 05, 06 | `tools/arch_discovery.shapes` → V2 `ents["hatches"]` in `urban_boq_m9`; `arch_plan.layer_roles` reads the fills | — | M | four FLAGGED reader defects fixed by one change; the reference plan nested 2 deep = base | column roles change on drawings with nested fills (intended) | variants r13 / r14 / r17 / r18 / r19 / r20 / r22: FLAGGED → NOT_REPRODUCED; the reference plan nested2 equal to base; V1 bytes unchanged | V2 reads intake hatches again |
| 3 | **P2-06** | RFI register by question; engineering findings moved to a REVIEW channel (cause SOFTWARE); every BOQ line points to its question id | S6R-B2, S6R-B3; R4 | `arch_completeness` (`FLAG_RULES` / questions), `urban_boq_m9` (`RFI_REGISTER.json`), workbook RFI sheet | — | S–M | review load: 85 lines → 4 client questions + 14 engineering findings | output layout change (V2 only) | reference: 4 client questions; every RFI line referenced exactly once; no SOFTWARE cause in the client register | keep the per-line RFIs only |
| 4 | **P2-07** | Strip check refined: set-back doors (depth ≤ wall t + frame allowance, both faces inside the door's closure box); faces spanning adjacent openings split at the shared jamb; column-jambed wide gaps → an open boundary between floor zones; zone-line slivers → floor | ENG-I1, ENG-I2, ENG-D3, ENG-D4; S6P1-NEW-04 | `arch_completeness.strip_register` | P2-04 | M | 14 engineering RFIs resolved or explained | strip classes change (V2) | fixtures per case; reference: unattributed strips 8 → 0, or each with a reviewer reason | Phase 1 check |
| 5 | **P2-08** | Eligible-surface ledger v1: an explicit, versioned eligibility table (space kind × surface × trade) and a wall-face ledger per band face; NSD-4 / 6 in the gate | R3; NSD-4, NSD-6; S6R-B5 | `engine/source/surface_ledger.py` (new), `arch_completeness.coverage` | P2-04 | L | completeness of wall, reveal and wet-room surfaces proven per face, not per room | new exit-3 failures may surface on real drawings (intended) | synthetic: Σ assigned face length = 2 × Σ band length + caps + reveals − openings per floor; no missing (surface, trade) pair; reference: the same, or a named defect | gate back to Phase 1 coverage |
| 6 | **P2-09** | Dimension values as independent evidence: read DIMENSION measurement + definition points; match to openings / walls / rooms; differences above tolerance → REVIEW | D row 17; NSD-8 | `tools/arch_discovery` (census), `engine/source/dimension_evidence.py` (new) | P2-01 | M | the first independent check that can catch a self-consistent but wrong model | none to quantities (REVIEW only) | reference: share of openings with a matching dimension, the mismatches listed; synthetic: an injected wrong door width is caught | disable the check |
| 7 | **P2-10** | Text: diacritic / tatweel / letter-variant normalisation before lexicon matching; the `x-arab1b` SHX map (verified on known words) or a stage-1 REVIEW with the count and positions | D rows 9, 19; S6-TXT-02 | `engine/source/arch_rooms` lexicon (V2 branch), SHX map module | — | S | rooms that go UNLABELLED for typography get their names | room classes change (intended) | the shadda fixture → labelled; 51 undecoded texts either decoded (spot-checked) or flagged | V2 branch off |
| 8 | **P2-11** | Linetype semantics: hidden / dashed / centre lines are never room boundaries or wall faces; they are overhead / below evidence | D row 16 | `arch_plan.layer_roles`, `arch_rooms` boundary inputs (V2) | — | S–M | prevents dashed beams closing rooms | room shapes change where dashed lines coincide with faces | fixture: a dashed beam across a room does not split it | V2 branch off |
| 9 | **P2-12** | **Blind round**: two unseen villas from different drafters; hand truth produced independently; metrics fixed in advance; the engine version frozen before comparison | R8 | `research/urban_m9_s6/phase2_blind/` | P2-01, 04, 05, 06 (at least) | M (plus the owner's drawings) | the only evidence that generalises | none | the go / no-go criteria below | — |

## C. Defer (blocked or flagged meanwhile; promote only if a blind drawing needs it)

| Item | Why defer | Meanwhile |
|---|---|---|
| Paper-space viewport reading | large; one drawing so far needed it | exit 2 or `--region` (reviewer) |
| XREF binding | no supplied XREF yet | exit 2 or `--accept-missing-xref` |
| Curved walls (arc bands in the architectural path) | `opening_census.arc_bands` exists but needs openings, caps and faces; promote if the blind drawings have curved walls | add a REVIEW flag for arcs paired at a wall thickness (S) |
| Non-uniform door blocks | rare; flagged `DOOR_SYMBOLS_DISTORTED` | REVIEW |
| Route-G / M4 lintel-evidence correction | changes frozen structural results; needs an owner decision and its own version | errata entry (P2-00) |
| V2 as the default; V1 retired | after the blind round | V1 strict default (owner) |
| New BOQ families, workbook polish | R9 | — |

## The smallest set that most improves real-villa reliability

**P2-01 robust predicates + P2-04 door conservation + P2-05 fills from K2 + P2-06 RFI register.** About 8–10 days.

Together they remove the three independent silent-error mechanisms found on the reference plan:
- float threshold coin flips;
- doors without lines;
- fills unread in nested blocks.

They also cut review load by an order of magnitude. P2-00 and P2-02 are cheap and make the result trustworthy, so they ride along.

## Next milestone: S6 Phase 2A "reliability core" (P2-00 … P2-06), then the blind round (P2-12)

**GO (all required):**
1. Investigation A fixtures A0–A6 give 1 opening each under V2.1. The method comparison gives ROBUST = 1.000.
2. Metamorphic suite (12 transforms) on the synthetic villa: 0 differences in element counts and category areas (± 1e-4 m²). Reference plan mm vs m: identical rooms, openings and lines.
3. Element conservation on the synthetic villa and the reference plan: swings = door lines + door RFIs; window blocks = window lines + window RFIs.
4. Fill variants r13 / r14 / r17 / r18 / r19 / r20 / r22 are all NOT_REPRODUCED.
5. Freezes and code health:
   - V1 byte-identical (15 / 16 files);
   - every freeze test and behaviour manifest reproduces;
   - full suite: 0 code failures, run in one session at a time.
6. RFI register: every RFI line referenced once; no SOFTWARE cause in the client register.
7. Every V2.1 change on the reference plan is listed in a before / after record and accepted by a reviewer. Expected: +1 door, +1 window, +0.20 m wall, the CLOSED doors as lines.

**NO-GO (any one):**
- a V1 byte change;
- an unexplained metamorphic difference;
- an element-count mismatch without an RFI;
- a robust-predicate opening that a reviewer rejects;
- a new exit-3 failure on the synthetic villa;
- any tuning against benchmark or human quantities.

**Blind round (P2-12), GO for "V2.1 candidate for default", on each unseen villa:**
- 0 silent omissions of elements (doors, windows, columns) against the independent hand count;
- every admission stop has a reviewer remedy;
- the client RFI register fits on one page per floor.

No accuracy percentage is claimed. In particular there is no "95 %", and nothing is described as quotation-ready.

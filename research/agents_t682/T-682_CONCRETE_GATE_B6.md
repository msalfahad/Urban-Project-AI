# T-682 CONCRETE GATE B ROUND 6: integration package ARCH_TAKEOFF_V3.0.67 (T-678: lintels on a soffit lower bound, PC-2F, annex C3)

Worker 3 (lane I), 2026-11-10, branch `agents/task-T-682`. **Integration package for Checker Gate B.** The LAST concrete
package before masonry (T-672). Opt-in candidate only: the released default V2.9 + route G is untouched; no rule
version file, owner decision or frozen file changes. Development villa, not an accuracy claim. ERS s.2-5,
WORKFLOW_CONTROLS s.1 / s.5, UP-QTY-STATUS-001. Base: the published T-677 merge (V3.0.66 c411617d, Gate B PASS,
8a28bce5 / 11d94e99).

## 0. What was wired, from what

| Source (Checker-merged) | Merge | Checker run | Lines | Wired as |
|---|---|---|---|---|
| T-678 ledger (`research/agents_t678/out/T678_LEDGER.json`, sha 3c1319c5) | f8515d4b | Verifier 2026-11-10T17:58Z Gate A PASS (session_01E6cPneYaQmLCCbd4QPBgBq: own 778, schedule depths, D-GF-07 / D-GF-03 / W13 / C3 by hand AGREE) | 9 lintel + 2 column | 7 lintels BOUND, 2 lintels LOWER_ONLY (one end OPEN), PC-2F BOUND, C3 BOUND |
| T-677 line index V3.0.66 (`research/agents_t677/out/LINE_INDEX_V3_0_66.json`, sha 02065c41) | 8a28bce5 | (binding) | 5,076 | full id + element + class + blank range asserted per entry |
| T-677 summary (`research/agents_t677/summary_t677.json`, sha 7e157722) | 8a28bce5 | (binding) | 2 codes | the V3.0.66 code totals the `expect_totals` start from |

Not wired, named (never 0): 13 OPEN BOUND lintels, each naming its missing datum (T-678 census: W04 / W08 Q-54 B,
W11 / W12 sill, W25 / W27 R-T228-3, D-2F-02 D-04, D-GF-05, D-GF-08, D-GF-14, D-1F-01 / D-1F-09 T-227, A-GF-01 arched
crown); 6 DESIGNER ITEM lintels (T-673); the 4 other GF annex column lines (their section waits for D-66; the height
bound 3.294 .. 4.05 m is a T-678 follow-up, not a ledger quantity).

## 1. Physical elements, one each (ERS s.2.1 / s.2.4)

- **Lintel (B9-02).** One RC cast lintel over a masonry opening (ST p.13 schedule: the drawing makes every lintel RC
  cast), required where masonry is built above the head. Existence is decided on the LOWER bound of every soffit over
  the opening's own extent (R-T678-1), not on the host wall's area state. Its m3 is B x D x (w + 0.40 at every end with
  >= 0.40 drawn) .. B x D x (w + min(end, 0.40)) [MIN_BEARING] or (w + drawn end distances) [CEILING]; an end with no
  recorded stopper is OPEN (R-T678-3): lower end only, never a ceiling invented for it. The owner manual method (the
  shortest standard precast piece, owner 2026-11-02) is kept beside each row, never as the m3.
- **PC-2F (B10-06).** Slab outline 778 = the planted column PC-2F (T-220 COL-2F-59; Checker AGREE): one line, the one
  V3.0.66 already carries (L-541c7e56, element HL:PLANTED_COLUMN:PC-2F:CONCRETE). The beam B7 billed through it owns the
  joint (UP-CONC-JOINT-001): the column runs base +9.65 to the B7 soffit.
- **Annex C3 (B10-06).** GF annex column, base 0.25 APPROVED, top = the annex roof slab top (not printed).
- No line is added, no line moves to another; no released line moves (R-T682-2 (u)).

## 2. Owner manual method beside the drawing-derived method

| Element | Owner manual method (beside) | Drawing-derived method (wired) |
|---|---|---|
| Lintel | (w + 2 x 0.15) -> shortest precast piece 1.20 / 1.50 / 2.50 m (per row in the ledger: D-GF-07 2.50, W01 / W13 / D-GF-01 1.50, doors 1.20) | ST p.13 RC cast: B x D x length range above (R-T673-3 / R-T678-3), existence on the soffit lower bound (R-T678-1) |
| PC-2F | section x storey | 0.20 x 0.40 (drawn) x 2.28 .. 0.20 x 0.50 (printed) x 3.50: CONFLICT range |
| C3 | section x storey | 0.125 x (3.544 - 0.25) .. 0.125 x (4.30 - 0.25) |

## 3. Evidence status (WORKFLOW_CONTROLS s.5) and the Checker's challenges

Quantity: every changed line stays HELD (bounded or blank); nothing VERIFIED, nothing released. Existence (new record
`existence` on each line):

- DRAWING-CONFIRMED: D-GF-07 (head 2.50 PRINTED), W01 (3.00 PRINTED), W13 (3.30 PRINTED), PC-2F, C3.
- **ASSUMED - OWNER-APPROVED (F-V678-1)**: D-1F-05, D-1F-06, D-GF-01, D-GF-02, D-GF-03, D-GF-04: the door head is the
  owner door-height fallback Q-55 C 2.20 m (not printed). Each line carries the `assumption` record with its source,
  the spare R-T678-1 leaves and the **re-run trigger = 2.20 + spare** (validated as a number and stated in the text):

  | opening | spare (m) | re-run trigger: a drawn / printed head above (m over FFL) reverses existence |
  |---|---|---|
  | D-GF-02 / D-GF-03 / D-GF-04 | 0.034 | **2.234** (the Checker's case: 34 mm) |
  | D-GF-01 | 0.384 | 2.584 |
  | D-1F-05 | 0.990 | 3.190 |
  | D-1F-06 | 1.240 | 3.440 |

- **Plane record (F-V678-2)**: the 4 annex doors (D-GF-01 .. -04) and C3 rest on the annex slab-top lower bound s_lo
  3.544 (R-T678-2: W08 drawn head +2.80 - 0.006 under CB6 0.75). New rule **R-T682-1 1.0.0**
  (`research/agents_t682/t682_rules.py`, extends R-T678-2, not edited): the plane is a record (outline, plan texts
  inside, section steps with position); REFUSED when a plan text inside is a level / step / thickness, when a section
  step lies inside the plane, or when its position is not stated (never assumed outside); a step drawn outside is
  kept as checked. Here: section A-A draws a 0.20 step OUTSIDE the annex (Checker own read; own corroboration: the A-A
  cut line is drawn north-east of every CB5 / CB6 / CB7 mark) -> ONE_PLANE, s_lo 3.544 reproduced by the rule. The
  candidate re-checks the record (`arch_v3067._plane`): a STEPPED state, no section read, or a step inside / unplaced
  is refused there too. Residual named: sections B-B / C-C / D-D are not recorded against the annex plane by T-678 or
  its Checker (`not_read` in the record).

## 4. Before -> after (m3; candidate code totals, V3.0.66 c411617d -> V3.0.67)

| Code | Released | Held bounded low .. high (lines) | Held blank (lines) | Lines |
|---|---|---|---|---|
| STR.CONC.LINTEL | 1.016 (unchanged) | 0.925 .. 1.496412 (17) -> **1.361 .. 2.050636 (24)** | 28 -> **21** | 61 |
| STR.CONC.COLUMN | 19.7765 (unchanged) | 9.6702 .. 12.414 (20) -> **10.26435 .. 13.27025 (22)** | 9 -> **7** | 59 |
| every other code | unchanged | unchanged | unchanged | |

Reconciliation (by hand, asserted by `check_totals` against the inputs' `expect_totals`): LINTEL low 0.925 + (0.036 +
0.056 + 0.036 + 0.052 + 0.096 + 0.080 + 0.080 = 0.436) = 1.361; high 1.496412 + (0.0628 + 0.066716 + 0.042708 + 0.058 +
0.108 + 0.108 + 0.108 = 0.554224) = 2.050636; the two LOWER_ONLY lines (0.036 + 0.048 = 0.084 at least, beside) stay
blank: the T-678 family low 0.436 + 0.084 = **0.520**. COLUMN low 9.6702 + 0.1824 + 0.41175 = 10.26435, high 12.414 +
0.350 + 0.50625 = 13.27025. Concrete total: released +0, held low +1.03015, held high +1.410474 m3.

**Acceptance 'LINTEL blank 28 -> 19 or fewer': 21, by design.** D-1F-06 (END on a crossing wall) and D-GF-04 (END at
the search limit, no extension) have one end with no recorded stopper: R-T678-3 and the row itself ('an open high
stays open and is never closed by a guess') keep them blank with their AT_LEAST figure beside. Reaching 19 would need
a high invented for those ends.

## 5. Line-by-line diff vs V3.0.66 (every other line byte-identical, asserted)

| Line | Code | Action | Member | V3.0.66 | V3.0.67 | Existence | Hand check |
|---|---|---|---|---|---|---|---|
| L-a7b8b292 | LINTEL | BOUND | D-1F-05 (0.20) | blank | 0.036 .. 0.0628 | OA, trigger 3.190 | 0.04 x 0.90 .. 0.04 x (0.90 + 0.285 + 0.385) |
| L-9ec762c0 | LINTEL | LOWER_ONLY | D-1F-06 (0.15) | blank | blank, AT_LEAST 0.036 | OA, trigger 3.440 | 0.03 x (0.80 + 0.40), END OPEN |
| L-1a078491 | LINTEL | BOUND | D-GF-01 (0.20) | blank | 0.056 .. 0.066716 | OA, trigger 2.584, plane | 0.04 x 1.40 .. 0.04 x (1.00 + 0.2679 + 0.40) |
| L-71998da6 | LINTEL | BOUND | D-GF-02 (0.15) | blank | 0.036 .. 0.042708 | OA, trigger 2.234, plane | 0.03 x 1.20 .. 0.03 x (0.80 + 0.223615 + 0.40) |
| L-a7848a35 | LINTEL | BOUND | D-GF-03 (0.20) | blank | 0.052 .. 0.058 | OA, trigger 2.234, plane | 0.04 x 1.30 .. 0.04 x (0.90 + 0.15 + 0.40) (Checker AGREE) |
| L-274b1125 | LINTEL | LOWER_ONLY | D-GF-04 (0.15) | blank | blank, AT_LEAST 0.048 | OA, trigger 2.234, plane | 0.03 x (0.80 + 0.40 + 0.40), END at search limit OPEN |
| L-fd68db05 | LINTEL | BOUND | D-GF-07 (0.20) | blank | 0.096 .. 0.108 | DC (2.50 printed) | 0.04 x 2.40 .. 0.04 x (2.00 + 0.30 + 0.40) (Checker AGREE) |
| L-3af715c6 | LINTEL | BOUND | W01 (0.20) | blank | 0.080 .. 0.108 | DC (3.00 printed) | 0.04 x 2.00 .. 0.04 x (1.20 + 0.75 + 0.75) |
| L-47882fa3 | LINTEL | BOUND | W13 (0.20) | blank | 0.080 .. 0.108 | DC (3.30 printed) | 0.04 x 2.00 .. 0.04 x 2.70 (Checker AGREE) |
| L-541c7e56 | COLUMN | BOUND | PC-2F (778) | blank | 0.1824 .. 0.350 | DC | 0.08 x 2.28 .. 0.10 x 3.50 (Checker AGREE) |
| L-fad18af6 | COLUMN | BOUND | annex C3 | blank (AT_MOST 0.50625 beside) | 0.41175 .. 0.50625 | DC, plane | 0.125 x 3.294 .. 0.125 x 4.05 (Checker AGREE) |

Run of record (Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) / 'ST7757
dxf.dxf' 9f9d1179, decoded into the private folder only): own fresh t167 `v304_run.py` -> `research/agents_t682/v3067_run.py`
(exit 0): every earlier version re-run and asserted, **V3_0_66 c411617d (asserted = T-677 run of record)** ->
**V3_0_67 a29a11a9**, 5,076 lines; replaced 11, added 0, outside 5,065 byte-identical (asserted); diff vs V3.0.66
CHANGED 9, CHANGED_TEXT_ONLY 2 (the two LOWER_ONLY lines: blank -> blank with their record), SAME 5,065. vs released
V2.9 + route G: QUANTITY_DIFFERS 1,049, SAME_QUANTITY 543, NOT_IN_RELEASED 3,484 (all unchanged from V3.0.66: no
released line moved). Totals moved: STR.CONC.LINTEL and STR.CONC.COLUMN only, equal to the inputs' `expect_totals`
(asserted in the run). Census `t479_registry_census.py` (unchanged; verdict set V3.0.44 b3b08dd7, downgrade snapshot
81732639) on V3_0_66 reproduces `research/agents_t677/out/LINE_INDEX_V3_0_66.json` byte for byte; on V3_0_67 ->
`out/LINE_INDEX_V3_0_67.json` (abe6d498), issues {}, complete map, 0 stale blocks. `t682_package_families.py` (T-483
attribute unchanged, chain 66 -> 67): B9-02 7 changed + 2 record-only, B10-06 2 changed. Summary:
`research/agents_t682/summary_t682.json`.

## 6. Downstream (named; every line byte-identical, no quantity moves here)

- Masonry: the host-wall material lines that bind these openings keep their state; existence of the 9 lintels is now
  stated (7 DRAWING-CONFIRMED / OA by line): the lintel face deduction from blockwork belongs to the masonry round
  (T-672), which must read the existence status of each line (an OA lintel's face deduction carries the same trigger).
- Formwork / plaster faces of PC-2F and C3, and the 4 other annex columns: unchanged (no line derives from these two
  column ranges in V3.0.66).
- Rebar by ratio (Q-81, open): the ratio ESTIMATE would read these concrete ranges once owner-approved; nothing wired.

## 7. Regression and validation

- Tests `tests/t682_concrete_gate_b6` (see handoff for counts): hand villa V682 (a printed-head window, an annex door
  on the owner fallback with its trigger 2.370 and plane record, a door with an open end, a planted column with a
  section conflict, an annex column on the slab bound, a lintel V3.0.66 already bounded, a blank lintel left alone, a
  released column) built through V3.0.66's own code path; adverse: VALUE / REVALUE refused, a released or bounded
  expect, an OA existence without its assumption, a wrong trigger, a trigger text without its number, an assumption on
  a drawing-confirmed line, a stepped / section-less / wrong-rule plane, a step inside or unplaced, a stale binding, a
  line V3.0.66 restated, applied twice, named twice, tampered existence / plane, two lines on one opening, a released
  line moved, an ADD or a non-concrete change; R-T682-1 normal + 7 refusals + the unchanged FLAGGED contradiction;
  the inputs builder on the committed ledger (hand re-derivation of every bound, triggers, expect_totals, sha pins, a
  tampered row refused); master 1.68.0 (pending).
- **Found while building (fixed, rule + test):** W13's V3.0.53 lintel record is FLAGGED, not HELD ('the head leaves
  room under some pieces only: which piece is over the opening is not read', spare -0.11 on the min over the host's
  pieces). The V3.0.66 restatement guard accepted only HELD. FLAGGED is the second R-T487-1 BLANK state, and T-678 answers
  exactly its question (B2 0.40 over the opening's own extent 2.15 .. 3.35 m: soffit 3.80, spare 0.24). V3.0.67 restates
  a lintel only from a blank V3.0.53 record (HELD or FLAGGED, kept whole under `superseded`), never from a REQUIRED one
  (`test_flagged_source_record_restated_required_refused`). The one other FLAGGED lintel (W26, D-39) is untouched.
- Lesson carried from T-677 (whole-code invariants): before restating, every earlier check that governs the codes was
  listed: the V3.0.53 lintel check (now on lines no later version governs), the V3.0.66 lintel check (on its own 17,
  `check_lintels` of V3.0.66 re-run on the lines V3.0.67 does not govern), the V3.0.64 / .65 / .66 concrete state
  checks (re-run on the whole candidate; C3's V3.0.65 UPPER_ONLY record is moved under `superseded`), one lintel line
  per opening across all three record kinds (`check_lintels`).

## 8. Registry: BOQ_FAMILY_MASTER_1.68.0 (pending now, promoted IN the merge)

`research/agents_t682/build_master_1_68_0.py`: 1.67.0 + V3.0.67 pending + B9-02 / B10-06 text (0 problems). In the merge
the Verifier runs (as T-677):

    python3 -I research/agents_t682/t682_package_families.py --run <run dir> --master rules/coverage/BOQ_FAMILY_MASTER_1.68.0.json --out research/agents_t682/out/T682_PACKAGE_FAMILIES.json   (already committed from this run)
    python3 -I research/agents_t682/t682_promotions_source.py --board .work/board/docs/agents --out research/agents_t682/out/PROMOTIONS_SOURCE_1_68_0.json
    python3 -I research/agents_t682/build_master_1_68_0.py --promote --write
    python3 -I research/agents_t682/write_manifest.py

## 9. Who is right (freelancer beside, never proof)

Lintels: NOT_COMPARABLE (no freelancer lintel concrete row, T-571). PC-2F / C3: inside the freelancer's column count by
type, NOT_COMPARABLE per line. Verdict proposals: 9 lintels ENGINE_RIGHT on existence (hand calculations above; 6 of
them ASSUMED - OWNER-APPROVED on Q-55 C), quantity HELD; PC-2F ENGINE_RIGHT that it is a member, section UNRESOLVED
(drawn vs printed); C3 ENGINE_RIGHT on the bound, top UNRESOLVED (Q-54 B).

## 10. Rules and lessons row (proposed)

R-T682-1 1.0.0 (above). R-T682-2 (`engine/source/arch_v3067.py`) = R-T677-1 (a) .. (q) + (r) existence on an
owner-approved fallback is labelled with its source and a numeric re-run trigger; (s) a bound transferred over a slab
plane carries the R-T682-1 record and is refused unless ONE_PLANE with every drawn section step outside; (t) the three
lintel checks, one line per opening across them; (u) released m3 does not move in this version.

Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | the annex slab-top bound was transferred on 'one plane' read from the
plan only, while a section drew a 0.20 step (outside the annex, by luck); 6 lintels' existence rested on the owner
door fallback with a 34 mm spare, unlabelled | a boolean 'one plane' hides what was checked; an owner-approved value
deciding existence is invisible once the quantity is wired | a plane is a record checked in plan AND every section
read, a step whose position is not stated refuses the transfer; existence that rests on an owner fallback carries
ASSUMED - OWNER-APPROVED and a numeric re-run trigger (assumed + spare) on the line | tests/t682_concrete_gate_b6 |
PROPOSED |

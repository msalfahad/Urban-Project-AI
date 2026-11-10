# T-677 CONCRETE GATE B ROUND 5: integration package ARCH_TAKEOFF_V3.0.66 (lintel heads, ST-03 steps, ground-slab panels)

Worker 3 (lane I), 2026-11-10, branch `agents/task-T-677`, run session_01E6cPnaw29tSFc2wdaxBnXT. **Integration package
for Checker Gate B.** Opt-in candidate only: the released default V2.9 + route G is untouched; no rule, owner decision
or frozen file changes. Development villa, not an accuracy claim. ERS s.2-5, WORKFLOW_CONTROLS s.1 / s.5,
UP-QTY-STATUS-001. Base: the published T-671 merge (V3.0.65, Gate B PASS, 271ba60f / 722a9ea6).

## 0. What was wired, from what

| Source (Checker-merged) | Merge | Checker run | Lines | Wired as |
|---|---|---|---|---|
| T-673 ledger (`research/agents_t673/out/T673_LEDGER.json`, sha fc0939bf) | 15d03afc | Verifier 2026-11-10 14:03 Gate A PASS (own W16 / W24 / ST-03) | 16 + 1 new, 1 | lintels BOUND (R-T673-1 / -3); W19 / W20 pier remainder ADD_SHARED; ST-03 LOWER_ONLY |
| T-674 summary (`research/agents_t674/summary_t674.json`, sha 0f162475) | bb4ec90b | Verifier 2026-11-10T16:0xZ Gate A PASS (own polygonisation) | 3 + 2 | REVALUE (released stays released); court pair CONFIRM |
| T-658 band areas (`research/agents_t658/out/T658_BAND_AREAS.json`, sha e9e3871a) + T-674 | 2cec1520 / bb4ec90b | Verifier 2026-11-10T02:10Z r2 / 16:0xZ | 1 | GB BAND0038 BOUND on its one drawn strip |
| T-671 line index V3.0.65 (`research/agents_t671/out/LINE_INDEX_V3_0_65.json`, sha e1887c34) | 271ba60f | (binding) | 5,075 | full id + element; reproduced byte for byte by this run's census |

Not wired, named (never 0): 28 lintel lines (6 DESIGNER ITEM, 22 OPEN BOUND, T-673 census); 4 stair lines
(DESIGNER; the ST-01 remainder's census bound 1.213429 .. 1.434413 is a CONFLICT component, not wired); route G's
junction face at the lift corner, 0.7112 m2 after the 0.114271 m2 returned (lift ring, shaft, beam ends: NO_LINE);
R-T674-1 / -3 as method changes of route G (proposals only).

## 1. One physical element once (ERS s.2.4)

- **Lintel vs pier remainder vs masonry.** Each lintel line is B x D x (opening + 0.40 bearing each side .. the drawn
  jamb ceilings). Between W19 and W20 the pier is 0.875 m: each lintel's high carries its 0.40 only; the 0.075 m
  beyond both bearings belongs to ONE of the two (not drawn) and is its own line 0 .. 0.2 x 0.2 x 0.075 = 0.003, never
  inside either high. The masonry deducts the lintel face only (register 2026-11-10); its material lines are unchanged.
- **Slab vs oblique beam BAND0038 (both or neither, Checker 16:00).** The beam owns its strip to both carriers' faces
  (C1, T-282 closure, T-674 R-T674-1; Checker own 0.326696 m2). The slab gives up the two end triangles
  0.326694 - 0.236694 = 0.090 m2 (-0.009 m3). In V3.0.65 the beam was already bounded on 0.310134 (AS_DRAWN, face 181
  stopping at its drafted end) .. 0.326694 (EXTENDED) m2 x the titles 0.30 .. 0.40: the triangles sat in the slab AND
  inside the beam's range (0.073440 .. 0.090 m2 counted twice). With the strip fixed at 0.326694 the AS_DRAWN reading
  leaves (a beam does not stop short of its carrier): beam 0.326694 x 0.30 .. 0.40 = 0.098008 .. 0.130678. After the
  move: slab excludes 0.326694 m2, beam plan 0.326694 m2, residual 0 at both ends of the range.
- **Slab vs junction box.** The 0.105587 + 0.008684 m2 the route G junction box took across the drawn lift ring face
  return to the two panels; the box keeps 0.7112 m2 that no slab line carries (NO_LINE, named).
- **ST-03 steps vs waist.** The steps part (5 drawn risers) is a floor of the flight: LOWER_ONLY AT_LEAST 0.355017; the
  line stays blank (the waist S-9 is not drawn); its formwork lines (2 blank, 1 N/A) unchanged.

## 2. Owner manual method beside the drawing-derived method

| Element | Owner / freelancer manual method | Drawing-derived method (wired) |
|---|---|---|
| Lintel | (w + 2 x bearing) x schedule section; freelancer: no lintel concrete row | B x D x (w + 0.80) .. B x D x (w + drawn jamb ceilings), heads drawn (R-T673-1); shared pier once |
| ST-03 E1 | steps + waist slab | steps 5 x 1/2 x 0.30 x 0.17 x 2.80 - wedge 0.001983 = 0.355017 at least; waist open |
| Ground slab | panel between beam faces x T | panels from the drawn faces noded on the true arcs (R-T674-2), strip to carriers (R-T674-1), no junction box over a drawn support (R-T674-3) |
| GB BAND0038 | short edge x 0.30 x title depth | drawn strip 0.326694 m2 x 0.30 .. 0.40 |

## 3. Evidence status (WORKFLOW_CONTROLS s.5)

- VERIFIED: the 3 revalued slab lines (Checker own re-measure, T-674 Gate A: 0.350768 / 0.272116 / 0.225338 m3).
  DRAWING-CONFIRMED: the court pair (re-derived equal); lintel existence (14 drawn heads + 2 T-650); ST-03 steps.
- HELD BOUNDED (DRAWING-CONFIRMED bounds): 16 lintels + the pier remainder (ends T-516 RFI); BAND0038 (D-34 titles).
- HELD blank: ST-03 (lower end beside, waist S-9). ASSUMED - OWNER-APPROVED: none. UNKNOWN: none new.
- Checker re-measured 3 of the 17 MEASURABLE NOW concrete lines (W16, W24, ST-03): PARTIAL 3 / 17, nothing VERIFIED.

## 4. Before -> after (m3; candidate code totals, V3.0.65 38af7909 -> V3.0.66 c411617d)

| Code | Released | Held bounded low .. high (lines) | Held blank (lines) | Lines |
|---|---|---|---|---|
| STR.CONC.LINTEL | 1.016 (unchanged) | 0 .. 0 (0) -> **0.925 .. 1.496412 (17)** | 44 -> **28** | 60 -> **61** |
| STR.CONC.GROUND_SLAB | 21.638458 -> **21.640885** (+0.002427, +0.011 %) | - | 0 | 26 |
| STR.CONC.GROUND_BEAM | 23.760555 (unchanged) | 1.17341 .. 1.571171 (8) -> **1.178378 .. 1.571171 (8)** | 21 | 61 |
| STR.CONC.STAIR | 5.368881 (unchanged) | unchanged | 5 (ST-03 now carries AT_LEAST 0.355017 beside) | 11 |
| every other code | unchanged | unchanged | unchanged | |

Reconciliation (exact, asserted by `check_totals` from the changes alone): LINTEL low 0 + 0.925 + 0 = 0.925, high
1.493412 + 0.003 = 1.496412 (= T-673 family), bounded 0 + 16 + 1 = 17, blank 44 - 16 = 28; SLAB -0.009 + 0.010559 +
0.000868 = +0.002427; GB low +0.016560 m2 x 0.30 = +0.004968, high 0. Concrete total: released +0.002427, held low
+0.929968, held high +1.496412 m3. The released lines that move are RELEASED both sides (REVALUE): no held line was
released, no released line was held.

## 5. Line-by-line diff vs V3.0.65 (every other line byte-identical, asserted: 5,054 SAME)

| Line | Code | Action | Member | V3.0.65 | V3.0.66 | Hand check |
|---|---|---|---|---|---|---|
| L-4a12b894 | LINTEL | BOUND | A-1F-01 | blank | 0.054 .. 0.1185 | T-650 bound (merged): 0.03 x 1.80 .. 3.95 |
| L-2efe4809 | LINTEL | BOUND | P-1F-01 | blank | 0.063 .. 0.12042 | T-650 bound: 0.03 x 2.10 .. 4.014 |
| L-441ae5fe | LINTEL | BOUND | W05 | blank | 0.040 .. 0.055 | 0.04 x 1.00 .. 1.375 (column face end) |
| L-f269fabb | LINTEL | BOUND | W06 | blank | 0.040 .. 0.040 | 0.04 x 1.00 (end 0.000 FLAGGED deficit) |
| L-ed7aadd0 | LINTEL | BOUND | W07 | blank | 0.056 .. 0.134 | 0.04 x 1.40 .. 0.04 x (0.60 + 0.40 + 2.35) |
| L-78634467 | LINTEL | BOUND | W09 | blank | 0.092 .. 0.118 | 0.04 x 2.30 .. 2.95 |
| L-882717b0 | LINTEL | BOUND | W10 | blank | 0.056 .. 0.060 | 0.04 x 1.40 .. 1.50 (START 0.100 deficit) |
| L-53ef44d8 | LINTEL | BOUND | W16 | blank | 0.078 .. 0.081732 | 0.04 x (1.55 + 0.40 + 0 .. 0.0933) (Checker AGREE) |
| L-6057028f | LINTEL | BOUND | W19 | blank | 0.056 .. 0.069 | 0.04 x 1.40 .. 1.725 (pier side 0.40) |
| L-6692d02c | LINTEL | BOUND | W20 | blank | 0.056 .. 0.08048 | 0.04 x 1.40 .. 2.012 (pier side 0.40) |
| L-dd5b41a7 | LINTEL | BOUND | W21 | blank | 0.040 .. 0.055 | 0.04 x 1.00 .. 1.375 |
| L-f68444ed | LINTEL | BOUND | W22 | blank | 0.040 .. 0.040 | 0.04 x 1.00 |
| L-bf76c173 | LINTEL | BOUND | W23 | blank | 0.056 .. 0.134 | 0.04 x 1.40 .. 3.35 (0.39996 -> 0.400, R-T673-2) |
| L-40e8c259 | LINTEL | BOUND | W24 | blank | 0.094 .. 0.268280 | 0.04 x 2.35 .. 0.04 x (1.55 + 0.938 + 4.219) (Checker AGREE) |
| L-005334b6 | LINTEL | BOUND | W28 | blank | 0.040 .. 0.055 | 0.04 x 1.00 .. 1.375 |
| L-aca2db3c | LINTEL | BOUND | W29 | blank | 0.064 .. 0.064 | 0.04 x 1.60 |
| L-7d90a0fe | LINTEL | ADD_SHARED (NEW) | W19 / W20 pier remainder | (none) | 0 .. 0.003 | 0.04 x (0.875 - 0.80) |
| L-061e18cf | STAIR | LOWER_ONLY (text) | ST-03 E1 | blank | blank, AT_LEAST 0.355017 beside | 5 x 1/2 x 0.30 x 0.17 x 2.80 - 0.001983 (Checker AGREE 0.357) |
| L-69527cb9 | GROUND_SLAB | REVALUE | panel SITE-49a7dae5 | 0.359768 | 0.350768 | (3.834377 - 0.326694) x 0.10 |
| L-8b681fda | GROUND_SLAB | REVALUE | panel SITE-3f7728a8 | 0.261557 | 0.272116 | 2.721160 x 0.10 |
| L-f192ff5f | GROUND_SLAB | REVALUE | panel SITE-c1b4b440 | 0.224470 | 0.225338 | 2.253380 x 0.10 |
| L-1031c9be | GROUND_SLAB | CONFIRM | panel SITE-d74f3fe2 | 1.090505 | byte-identical | 10.905052 x 0.10 |
| L-5e881fd3 | GROUND_SLAB | CONFIRM | panel SITE-0caa2bd2 | 0.205020 | byte-identical | 2.050202 x 0.10 |
| L-970bac56 | GROUND_BEAM | BOUND | BAND0038 | 0.09304 .. 0.130678 | 0.098008 .. 0.130678 | 0.326694 x 0.30 .. 0.40 |

vs released V2.9 + route G: QUANTITY_DIFFERS 1,046 -> 1,049 (the 3 revalued slab lines), SAME_QUANTITY 546 -> 543,
NOT_IN_RELEASED 3,483 -> 3,484 (the new pier line).

## 6. Downstream (named; every line byte-identical, no quantity moves here)

- MAS.GLUE.AAC (3 bounded) / MAS.UNITS.WHITE (3 blank) bind the W16 / W24 / ... lintel faces as HELD face ranges
  0 .. face (V3.0.59): still valid (the lintel is held); now that existence is DRAWING-CONFIRMED a lane A masonry
  package may deduct the face low end (follow-up, not here).
- STR.FORMWORK BAND0038 faces (2 blank), STR.EARTH.EXCAVATION (1 blank) and 8 GB lines naming BAND0038 in their
  records: unchanged (the beam's sides and depth are unchanged; only its plan reading settled).
- STR.FORMWORK.STAIR of ST-03 (2 blank, 1 N/A): unchanged (waist soffit open).
- No line derives from the 5 slab panels' areas (no DPM / mesh line binds them): nothing else moves.

## 7. Regression and validation

- Run of record (Drive 'Alsenan chalet project' copies 'P7757_DXF_COMPRESSED.zip' (inner P7757.dxf ab54dd55) / 'ST7757
  dxf.dxf' 9f9d1179, decoded into the private folder only): own fresh t167 `v304_run.py` -> `research/agents_t677/v3066_run.py`
  (exit 0): every earlier version re-run and asserted, **V3_0_65 38af7909 (asserted = T-671 run of record)** ->
  **V3_0_66 c411617d**, 5,076 lines; replaced 21, added 1, outside 5,054 byte-identical (asserted); diff ADDED 1,
  CHANGED 20, CHANGED_TEXT_ONLY 1, SAME 5,054.
- **Found while building (fixed, rule + test):** the V3.0.53 lintel check (R-T487-1) knows only REQUIRED valued / HELD
  blank lintel lines and requires its record on every lintel line: a bounded lintel cannot pass it. V3.0.66 moves the
  V3.0.53 HELD record of each restated lintel under `superseded`, runs the earlier chain on every other line (the
  V3.0.53 check still governs the 44 lintels it did: 16 released + 28 blank) and governs its 17 with its own check
  (R-T677-1 (q): one line per opening across both, the record kept, the shared line naming its sharers' openings;
  `test_lintel_governance`). A REQUIRED (released) lintel is refused as a restatement source.
- `t479_registry_census.py` (unchanged; verdict set V3.0.44 b3b08dd7, downgrade snapshot 81732639) on V3_0_65
  reproduces `research/agents_t671/out/LINE_INDEX_V3_0_65.json` byte for byte; on V3_0_66 -> `out/LINE_INDEX_V3_0_66.json`
  (02065c41), issues {}, complete map, 0 stale blocks.
- `t677_package_families.py` (T-483 attribute unchanged, chain 65 -> 66): B9-02 16 changed + 1 added, B10-05 3 changed,
  B10-04 1 changed; B7-12 record text only.
- Tests `tests/t677_concrete_gate_b5` (42): hand villa V677 (two lintels on a 1.00 m pier, an untouched lintel, a
  three-riser flight, a slab with an oblique beam's end triangles, a confirmed panel) + adverse (both or neither, a
  wrong delta, a no-change revalue, a held line revalued, stale values, a shared remainder from a floor / one sharer /
  a non-bounded sharer / twice, a live V3.0.53 record left behind, two lines for one opening, tampered states, a
  released line moved without a revalue, applied twice, the V3.0.65 companion in the base); inputs builder (sha pins,
  id + element binding, arithmetic of every range); master 1.67.0. Results in the handoff.

## 8. Registry: BOQ_FAMILY_MASTER_1.67.0 (pending now, promoted IN the merge)

`research/agents_t677/build_master_1_67_0.py`: 1.66.0 + V3.0.66 pending + B7-12 / B9-02 / B10-04 / B10-05 text (0
problems). In the merge the Verifier runs (as T-671):

    python3 -I research/agents_t677/t677_promotions_source.py --board .work/board/docs/agents --out research/agents_t677/out/PROMOTIONS_SOURCE_1_67_0.json
    python3 -I research/agents_t677/build_master_1_67_0.py --promote --write
    python3 -I research/agents_t677/write_manifest.py

## 9. Who is right (freelancer beside, never proof)

Lintels / ST-03 waist split: NOT_COMPARABLE (no freelancer lintel concrete row, no waist split). Ground slab per cell:
NOT_COMPARABLE (his rows carry no location); T-674 verdicts stand: L-69527cb9 ENGINE_WRONG 0.009 m3 (corrected here),
L-8b681fda / L-f192ff5f ENGINE_WRONG +0.011427 m3 (corrected), court pair ENGINE_RIGHT. T-180 P18 is CLOSABLE NOW (the
5 lines carry the Checker-verified drawn values in the candidate).

## 10. Rule and lessons row (proposed)

R-T677-1 (engine/source/arch_v3066.py) = R-T671-1 + (m) a released concrete line moves only by a merged drawn
re-derivation with the Checker's own re-measure, stays released, keeps its old value and deductions, the delta
asserted; (n) a plan area leaving one line for another leaves only with the other's restatement (both or neither);
(o) a remainder shared by two bounded lines is one new line 0 .. x in neither high; (p) the V3.0.65 record is
superseded too; (q) lintel lines this version restates or adds are governed by its lintel check, the V3.0.53 check by
every other lintel line.

Lessons row (ERS s.7, PROPOSED): | 2026-11-10 | a bounded lintel could not enter the candidate: the V3.0.53 lintel
check, re-run by every later version, knows only valued / blank lintels and requires its record on every lintel line |
an earlier version's check states a whole-code invariant (every line of a code carries its record, in one of its
states), so a later state of that code fails it | before restating a code into a new state, list every earlier check
that governs the code as a whole; the restating version takes over those lines explicitly (record superseded, own
check, the earlier check still run on the rest), never by weakening or skipping the earlier check (every package;
provenance T-677) | tests/t677_concrete_gate_b5/test_arch_v3066.py::test_lintel_governance | PROPOSED |

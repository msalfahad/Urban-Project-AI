# T-244 Integration package ARCH_TAKEOFF_V3.0.20: internal plaster / paint room faces at the merged opening outlines

Worker 3 (lane I), 2026-10-26, run unknown (scheduled). **Integration package for Checker Gate B.** Opt-in candidate
only: the released default stays ARCH_TAKEOFF_V2.9 + route G (no switch); nothing here is RELEASED. ERS 2026-10-22 read
and applied (s.2.1 element first, s.2.3 owner manual vs drawing method, s.3 build before deduct, s.4 statuses, s.7
lessons row). Drawings named by Drive folder and title only; no coordinates, no client text committed.
**integrates: T-302, T-238, T-237 (part 4), T-227 r2, T-201, T-255.** Base = V3.0.19 (candidate of record, T-255 Gate
B), reproduced byte for byte in this run.

## 1. Physical element and the question

Element: the internal wall face of a dry room (and the dry part of an open zone), plastered and painted from the floor
to the owner wall height (Q-43 / Q-48 A: GF 3.65, 1F / 2F 3.35), less every opening by ITS OWN physical outline inside
that height (Q-73), once per face (R-OPENING-ONCE-1, T-255). Plaster and paint are one figure on a dry face (Q-43).
V3.0.9 (T-211) wired the face lines from T-128 r3, whose opening table had three kinds of error that merged ledgers have
since settled: (a) arched openings deducted as their band rectangle (W15 / W16 4.805, W17 3.286 x 3.35 = 11.0081);
(b) heads not read (W24, W29 held 0 .. w x H); (c) door widths on the rebate side (D-GF-05, D-1F-07). The question: which
candidate lines carry each settled opening, and what does each line become when that one deduction is replaced?

## 2. What the package changes (line id by line id; plaster and paint identical, 8 lines)

| Room (candidate room) | Lines (plaster / paint) | Before V3.0.19 | After V3.0.20 | Status | Opening revision | Source |
|---|---|---|---|---|---|---|
| 1F-11 east master (1F-R3CFCFD) | L-31db3c83552682d92ca3 / L-349db74a70e1eecda2d2 | 59.4511 released (PROVISIONAL, VERIFIED + ASSUMED heights) | **61.4626 .. 61.7177 BOUNDED** | HELD | W17 11.0081 -> room-side hole 8.7414 .. 8.9965 | T-302 |
| 1F-13 living / corridor (1F-R78C367) | L-9b4a7bab033d677e2017 / L-be48ea84285be20645af | 110.1335 .. 114.3677 BOUNDED | **111.0177 .. 114.3677 BOUNDED** | HELD (lift door) | W15, W16 [4.3629 .. 4.805] -> 4.3629 each | T-238 / T-227 r2 |
| 1F-04 master 500 x 365 (1F-RED0D19) | L-971f0bdaf68d7fd0966c / L-d9f4ecdb6ef9a42d0220 | 49.1375 .. 54.33 BOUNDED | **52.005** PROVISIONAL | ASSUMED — OWNER-APPROVED (G1 height, Q-55 C door heads) | W24 [0 .. 5.1925] -> 1.55 x (2.50 - 1.00) = 2.325 | T-201 (via T-237 part 4) |
| 2F-03 maid (2F-R1DB2D2) | L-4ce74fc37a08d4bdf0d8 / L-5410f9045c80dd5933f0 | 55.555 .. 59.575 BOUNDED | **57.775** PROVISIONAL | ASSUMED — OWNER-APPROVED | W29 [0 .. 4.02] -> 1.20 x 1.50 = 1.800 | T-201 (via T-237 part 4) |

Hand arithmetic (owner manual method of record, face x owner height less openings):
- 1F-11: 22.149 x 3.35 = 74.19915 - D315 1.76 - D215 1.98 = 70.45915; - W17 room side 8.9965 (RADIAL) = **61.46265**,
  - 8.7414 (PRISMATIC) = **61.71775**. The released 59.4511 deducted 11.0081 (the archivolt 3.50 capped at 3.35), more than
  the physical hole: LOW by 2.0115 .. 2.2666 m2, ENGINE_WRONG to release. The opening crown (3.00 .. 3.05) is below the
  3.35 owner height, so the whole hole lies inside the face. Never the 9.870 window supply area (Q-76 A is the window
  line, untouched).
- 1F-13: 132.1575 - doors (1.98 x 3 + 2.20 + 0.924 = 9.064) - W15 4.3629 - W16 4.3629 = **114.3677**; - lift landing
  door 3.35 (head not printed, lift supplier item) = **111.0177**.
- 1F-04: 17.40 x 3.35 = 58.29 - D115 2.20 - D315 1.76 - W24 2.325 = **52.005** (T-237 part 4: 52.00).
- 2F-03: 18.90 x 3.35 = 63.315 - d220 1.98 - D315 1.76 - W29 1.80 = **57.775** (T-237 part 4: 57.77).

Inside each changed line only quantity, state, range, rfi, gross, geometry confidence, calculation and notes change;
each revised deduction keeps its before value on the line (`revised_by`), the drawing-derived method stays beside
(`drawing_derived_method`, unchanged), and the line carries `wall_finish_revision_v3020` (source, merge, checker run).

Everything else: **3,697 lines byte-identical to V3.0.19** (asserted by the module: whole-line sha; outside-rows hash
`3ea845df`), project identity block unchanged. 3,705 -> 3,705 lines: 8 CHANGED, 0 ADDED, 0 removed. Against released
V2.9 + route G: SAME_QUANTITY 715 / QUANTITY_DIFFERS 875 / NOT_IN_RELEASED 2,115 (unchanged counts: the 8 lines are
candidate-only room-face lines, NOT_IN_RELEASED before and after).

## 3. Settled openings that change NO line (V3_0_20_OPENING_DELTAS.csv, asserted against the lines)

| Opening / room | Kind | Why |
|---|---|---|
| W03 GF-15 (18.6369) and GF-08 (5.93125) | CARRIED | the T-255 split, deducted once on each code; 18.6369 + 5.93125 = 24.56815 = 6.731 x 3.65; GF-08 stays BOUNDED (lift door, W02) |
| W26 ST-2F (1.875, was 2.040, -0.165) / W27 ST-2F | NOT_APPLIED | the ST-2F plaster / paint lines carry no figure (D-T173-1 roof panel T 18, roof B3 contact) |
| W25 ST-1F | NOT_APPLIED | the ST-1F line is T-173's drawing-derived shaft range with its own opening list (no owner-method deductions) |
| W04 GF-04, A-GF-01 / W11 / W12 GF-01 | NOT_APPLIED | annex lines without a figure (G2 annex height, DCR-6 roof datum) |
| W09 / W10 GF-07 | NOT_APPLIED | pantry lines without a figure (plaster under wall tile not an owner rule, T-211 s.5.4) |
| D-GF-05 GF-06 (-0.110), D-1F-07 1F-09 (-0.110) | NOT_APPLIED | no room-face finish line (annex kitchen / wet room); carried by the wall-tile package V3.0.9b |
| W05-07 GF-16 / GF-13, W19-23 1F-07 / 1F-08 / 1F-02 / 1F-03 / 1F-09, W28 2F-02, W08 GF-06 | NOT_APPLIED | wet rooms: no room-face finish line (wall tile to the decor ceiling, Q-48 A) |

The module refuses a NOT_APPLIED entry when a figure-carrying finish line of that room deducts the opening (a REVISION is
then due), and a CARRIED entry whose lines do not deduct the opening exactly once at the value.

## 4. Engineering effect (candidate, NOT RELEASED)

| Item (m2) | V3.0.19 released | V3.0.19 held range (lines) | V3.0.20 released | V3.0.20 held range (lines) |
|---|---|---|---|---|
| FIN.PAINT | 166.8792 (3) | 529.4667 .. 595.0479 (8 bounded) + 4 blank | **217.2081 (4)** | **487.1210 .. 542.8606 (7 bounded)** + 4 blank |
| FIN.PLASTER | 184.6192 | 531.8267 .. 597.6479 (10 bounded) + 21 blank | **234.9481** | **489.4810 .. 545.4606 (9 bounded)** + 21 blank |

Released +50.3289 m2 per code = +52.005 (1F-04) + 57.775 (2F-03) - 59.4511 (1F-11 withdrawn). Dry rooms + shaft GF / 1F
paint, released + held: 696.35 .. 761.93 -> **704.33 .. 760.07 m2** (range width 65.58 -> 55.74 m2). No other code moves
(`totals_moved_by_code`: FIN.PAINT|m2 and FIN.PLASTER|m2 only).

**Against the freelancer** (internal plaster 1,151.14 m2 net, paint 1,191.13 m2 net, whole house, one line per trade):
NOT COMPARED. Of the 15 paint lines 7 are still ranges and 4 carry no figure (annex, pantry, ST-2F; plaster also 17
wet-room plaster lines blank), so the reference line stays HELD (whole-line rule: a held part is never promoted, a released part
never compared alone). Room by room (T-128 r3 / T-237, information only): 1F owner method vs his 1F rooms is a
RULE_DIFFERENCE on the height (his rooms priced taller), not touched here.

## 5. Owner manual method vs drawing-derived method (ERS s.2.3)

The owner method of record (face x owner height, every opening by its own area) is what the lines carry; the
drawing-derived method stays beside on each line (T-128 r3 drawing nets, roof datum HELD: 1F-11 68.70 .. 70.92 before
the hole, 1F-04 56.11 .. 63.73, 2F-03 63.34 .. 69.78, 1F-13 125.98 .. 139.59; not changed by this package: T-237 part 4's
drawing-derived nets 1449.99 .. 1560.92 m2 for the whole house apply when the roof datum DCR-6 is settled). The two
methods agree on the openings (the same outline deducted on both); they differ only on the height (owner G1 vs the
drawn levels), which is RULE_DIFFERENCE, kept visible, never merged.

## 6. Generic rule, code, tests

- **R-FINISH-OPENING-REVISION-1** (T-244; every villa; provenance T-237 crosswalk, T-238 arched outline, T-302 curved
  hole, ERS s.3; research rule, a rule version when adopted into the library): when a merged ledger settles an opening's
  outline, the deduction of that opening is replaced on EVERY finish line of that face (plaster and paint together, one
  figure, Q-43), asserted against the line's own deduction (named once, the before value); the net is recomputed from
  the line's own gross and deductions; a quantity line that now holds a deduction leaves the released total as a BOUNDED
  range (never kept at the old figure, never 0); a settled opening on a line without a figure is recorded, not applied.
- Code: `engine/source/arch_v3020.py` (MEDIUM, not frozen; WALL_FINISH_REVISION: `revised_line`, `changes_for`,
  `integrate`, `write`), `tools/urban_boq_m9.py` (opt-in V3020 tuple and `--v3020-inputs` only; no default switched,
  older method lists unchanged), `research/agents_t244/t244_inputs.py` (inputs: every value re-read from the merged
  ledgers and asserted), `v3020_run.py` / `v3020_direct.py`, `rules/coverage/BOQ_FAMILY_MASTER_1.15.0.json` (1.14.0 +
  pending V3.0.20, no family change; builder `build_master_1_15_0.py`; manifest by `tools/m9_rules_manifest.py`).
- Tests `tests/t244_finish_revision` (36): villa K244 hand fixture (not Alsenan; values in the docstring: an arched
  window carried as its band rectangle in a released room -> BOUNDED 52.170 .. 52.320; a semicircular head 1.40 x 2.10 +
  pi 0.70^2 / 2 = 3.709690 closing a held range; a rebate-side door width 0.85 -> 0.90, released 40.130 -> 40.020; an
  annex line without a figure NOT_APPLIED; a carried window); normal (states, ranges, totals move only on the two codes,
  held never 0, outside lines byte-identical, deduction order irrelevant, files written) and adverse (stale before value
  / range, a deduction before that is not the line's, an opening not on the line or named twice, a recomputed net that
  disagrees, mm units, a released record with a held deduction, a bounded record with none, a zero deduction, VERIFIED
  without a checker run, a stale twin (plaster revised, paint not), NOT_APPLIED where a figure-carrying line deducts the
  opening, CARRIED at another value, unknown line, wrong room, inputs schema / sources / duplicates, a change outside the
  quantity fields); Alsenan pins (every record's hand arithmetic from the merged values; an edited T-302 ledger or T-201
  head stops the build); registry 1.15.0 normal + adverse.

## 7. Run (identity)

Own decode of Drive "Alsenan chalet project" 'ST7757 dxf.dxf' (`9f9d1179`) and P7757.dxf from P7757_DXF_COMPRESSED.zip
(`ab54dd55`), Python 3.11.17: `research/agents_t167/v304_run.py` (V3_0_4 csv `d86de34a` reproduced), then
`research/agents_t255/v3019_run.py`: **V3_0_19 json `b35475bf` / csv `ef63b73b` / DIFF `f988e898`, V3_0_18 json
`ec741004`** = the candidate of record byte for byte. V3.0.20 (`v3020_direct.py` on those V3.0.19 lines, and the full
`v3020_run.py` m9 run, section 9): BOQ_LINES json `097a80b6` / csv `ca90351b`, DIFF `baf39204`, INTEGRATION_LEDGER csv
`2cbfdae8`, OPENING_DELTAS csv `f58f87d1`.
`tools/v30_gate_b.py diff` V3.0.19 -> V3.0.20 with the V3.0.20 ledger: 3,705 rows paired by ID, **changed 8,
changed-unflagged 0**; STATE_CHANGE 8 (all changed rows), SHARE_2PCT 6 on changed rows; MOVED_5PCT / NEW / DROPPED /
UNIT / CLASS / DOUBLE_FINISH / CROSS 0; STRUCTURAL 0 on the changed rows.

## 8. Gate B hand checks this package asks for (WORKFLOW_CONTROLS s.1)

By rule, all 8 changed lines (state change; 6 are >= 2 % of their trade): 1F-11 (W17 room-side hole against T-302's
ledger; the 74.19915 gross and the two doors), 1F-13 (W15 / W16 4.3629 against the T-227 r2 Checker walk; lift door
held), 1F-04 (W24 head / sill 2.50 / 1.00 on the elevation, T-201), 2F-03 (W29 the same). Suggested three rooms by hand
(the row's acceptance): 1F-11, 1F-04, 2F-03. Random 2 lines: by the Checker from the merge sha (`tools/v30_gate_b.py
pick`). The V3.0.19 verdict records: this package touches ONLY the 8 line ids above (all FIN.PLASTER / FIN.PAINT
room-face lines); any record bound to another line id is untouched (outside rows byte-identical).

## 9. Who is right (proposals)

- 1F-11 plaster / paint: ENGINE_WRONG (released 59.4511 deducted the 11.0081 band rectangle) -> HELD 61.4626 .. 61.7177
  (T-302). The freelancer's room figure is not restated (no room-by-room line).
- 1F-13 W15 / W16: ENGINE (merged T-238) RIGHT over T-128 r3's 4.805 band; the range narrows by 0.884 m2 on the low end.
- 1F-04 / 2F-03: the held windows are closed from the printed heads (T-201): ENGINE_RIGHT at 52.005 / 57.775 on the owner
  method, ASSUMED — OWNER-APPROVED on the G1 height.
- Door widths D-GF-05 / D-1F-07: census RIGHT (T-237); no candidate line carries those faces.

## 10. Lessons row (proposed, ERS s.7)

| 2026-10-26 | A released room-face line (1F-11, 59.4511 m2, Checker-verified room polygon) deducted an arched window as its band rectangle capped at the wall height | a verified FACE (contour, gross) was read as a verified NET: the opening inside it came from another ledger that was later found to be the archivolt, not the hole | a room-face line is only as settled as its least-settled deduction: when any deduction is withdrawn, the line leaves the released total for a BOUNDED range at once, on every code of that face, never kept at the old figure (any villa) | tests/t244_finish_revision (`test_hand_values_and_states`, `test_adverse_stale_twin_one_code_only`) | proposed (T-244 READY) |

## 11. Not done / remaining

The lift landing doors (L-GF-01 / L-1F-01 / L-2F-01), W02 (D-53), A-GF-01 / A-1F-01, W11 / W12 sills and the GF-11 /
ST-GF doorless opening keep GF-08, 1F-13, 1F-10, 2F-01 bounded; the annex (G2), pantry and ST-2F lines stay blank; the
roof datum (DCR-6) keeps every drawing-derived figure beside as information; the wet-room wall tile (V3.0.9b) carries the
wet-room openings; external faces (T-305) and reveals (T-313) are not this line. Door jamb / head plaster lines (the
engine's own opening ids, UP-FIN-PLASTER-001) are not crosswalked to the census door widths in a merged ledger: not
touched, named for the Lead.

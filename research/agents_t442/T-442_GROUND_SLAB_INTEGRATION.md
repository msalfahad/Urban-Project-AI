# T-442 integration package: ground-slab panels (T-444, T-436) and two cause-text corrections (T-433) into ARCH_TAKEOFF_V3.0.42

Worker 3 (lane I), 2026-11-02, branch `agents/task-T-442`. **Integration package for Checker Gate B.** Integrates T-444
(MERGED 1fb9dec6, Gate A PASS with the Checker's own re-measure of all four panels), T-436 (MERGED c943cabb, Gate A
PASS with the Checker's own handle read of the stair-zone panel, PARTIALLY VERIFIED 1 / 3: the panel part), T-433
(MERGED 304b9af2, F-T433-1 / F-T433-2 checked as stated) and the T-401 pit-wall basis (MERGED 23f948bb). Candidate of
record before: ARCH_TAKEOFF_V3.0.41 (json `5176c7c4`, T-431 Gate B, merge a04e3ea8). **NOT RELEASED**; the released
default V2.9 + route G is unchanged; rollback = V3.0.41 / V2.9. Development villa (Alsenan), not an accuracy claim; the
method (R-T442-1) is for every villa. Drawings are cited by Drive folder and title only.

integrates: T-444, T-436, T-433, T-401

## 0. Run identity

Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`) and 'ST7757 dxf.dxf' (`9f9d1179`),
decoded by the wrapper into `.work/private`. Own fresh `research/agents_t167/v304_run.py` (25.5 min), then
`research/agents_t442/v3042_run.py` (10.6 min, Python 3.11.18): **V3_0_36 `d462203f`, V3_0_37 `733f2efb`, V3_0_38
`57cca61c`, V3_0_39 `8d1bbe5d`, V3_0_40 `aa6aa927` and V3_0_41 `5176c7c4` reproduced** (every Gate B figure up to
T-431), **V3_0_42_BOQ_LINES.json `1793266d`** written beside them (4,839 lines; `summary_t442.json`, built by
`t442_summary.py` from that run). Inputs: `t442_inputs.py` reads ONLY the merged files, each pinned by sha256 (T-444
PIECES `69851de0` + summary `6220de41`, T-436 summary `5f193724`, T-433 summary `9e0e4335`, T-401 summary `b4118708`);
typed there: the line ids the merged texts name (bound by the module: a stale binding stops), the new line's element
id, the old / new designer item and the wording of the reasons.

```
.work/venv/bin/python -I research/agents_t167/v304_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t167
.work/venv/bin/python -I research/agents_t442/v3042_run.py <P7757.dxf> <ST7757.dxf> --out <private>/t442 --t167 <private>/t167
.work/venv/bin/python -I research/agents_t442/t442_summary.py <private>/t442/v3042 <private>/t167 --write
```

## 1. The physical elements and who owns them (ERS s.2.1)

- **Slab on grade around the lift pit** (engine cell SITE-c1089bdb, line L-41cfb82e). Cast between ground-beam faces
  around a pit that stands on its own raft FF. Four panels closed on drawn band faces: OWN-007 11.9237, OWN-009
  11.5200, OWN-010 10.9742, OWN-047 1.1875 = **35.6054 m2** (Checker T-444 own handle re-measure 35.605376). Not slab:
  the shaft 2.8125 m2 of the engine cell (pit floor = raft top, T-401 ST p.14: no slab over the pit void; the raft line
  L-1590b76b owns it, no volume added) and the ring 0.880 m2 (pit-wall band, LIFT_PIT:WALLS L-684fcad3, HELD). The
  'free column' that held the cell is the lift column C9 standing on the ring (R-T444-4). Owner trade: CONCRETE, B10-05.
- **Slab on grade under the foot of the GF curved flight** (engine cell SITE-4df8fcd99d130701, panel OWN-011). Closed by
  four band faces 17D / 7CF / 7DC / 7E1, **8.372326 m2** (Checker T-436 own read 3.020 x 2.772294). Inside it only
  layer-2 HIDDEN flight lines (drawn above the plan) and labels; no void, pit, opening; on the foundation plan below only
  a column footing (1B1A), no stair base. The flight bears on the ground beam (ST p.16 typical stair section). The
  engine dropped the whole cell as a 'stair zone' (generic_route SLAB_STAIR_ZONE): R-T436-1 says it is slab, whole.
  The flight-to-slab junction is the slab's (Q-62 A); the RS-C waist foot stays HELD with the waist (T-415).
- **Cause texts** (no element changes): the 13 column lines held as a printed-vs-drawn CONFLICT name D-63 (the lift
  columns on the raft) where the designer list item is **D-66 = RFI-S20**; the CL-LIFT pit-wall line names D-43 (the
  GF lift tie-beam size) where the pit-wall height is held by **the pit depth (supplier, RFI L-1) and the GF build-up
  (D-22 / D-40)**, T-401.

## 2. What the package does, per line (owner manual method and drawing-derived method side by side)

| | Owner manual method | Drawing-derived method (merged ledgers) |
|---|---|---|
| lift-shaft cell | slab on grade = plan area between ground-beam faces x printed thickness, by panel; no slab over a pit or under a member | four panels closed on drawn band faces (Checker re-measure by handle) x printed 'T=10cm'; engine net 39.2979 = panels 35.6054 + shaft 2.8125 + ring 0.880 |
| stair-zone panel | same; no answered owner rule removes the slab under a flight on grade (OWNER_RULE_STAIRS searched by T-391) | panel closed by four band faces, flight drawn HIDDEN, no void / pit / base: slab x T (R-T436-1) |
| cause texts | not a quantity | the T-433 split by blocker, line by line |

`V3_0_42_INTEGRATION_LEDGER.csv` (16 rows):

| Line | Element | Action | V2.9 | V3.0.41 | V3.0.42 | Evidence status (WFC s.5) |
|---|---|---|---|---|---|---|
| L-41cfb82ed733f4d6e3a5 | U-C:GROUND_SLAB:GROUND:SITE-c1089bdb4cfcdc4a | VALUE_CELL | BOUNDED 3.929788 (cell net incl. shaft / ring) | HELD BOUNDED 0 .. 3.560540 | **3.560540 m3** SOURCE_DERIVED | VERIFIED (areas: Checker T-444 re-measure; T: T-206 / T-444) |
| L-87d6ed48126aa9857e17 (ADDED) | GS-T442:GROUND_SLAB:GROUND:SITE-4df8fcd99d130701 | ADD_PANEL | not in V2.9 | no line (cell excluded as stair zone) | **0.837233 m3** SOURCE_DERIVED | DRAWING-CONFIRMED (panel; Checker T-436 read), T VERIFIED |
| 13 column lines (T-433 I-04: L-8de64040, L-43dae3d6, L-9cb26d86, L-4aed92c1, L-c677b628, L-8f8ad257, L-755eb56b, L-291ba2dd, L-a87ea657, L-85809d3d, L-cc702b85, L-831f6fe3, L-e112e2ad) | STR.CONC.COLUMN GF 3 + 1F 10 | CAUSE_TEXT | - | CONFLICT ranges 6.378 .. 8.2665 m3 (13 lines) | **ranges byte-identical**; rfi question and range basis 'D-63' -> 'D-66 (RFI-S20)' | HELD (unchanged) |
| L-684fcad323adc0c8a267 | LIFT_PIT:WALLS STR.CONC.LIFT | CAUSE_TEXT | - | HELD blank | **HELD blank** (unchanged); formula and rfi 'D-43' -> the T-401 basis | HELD (unchanged) |

Every other V3.0.41 line: **4,823 byte-identical** (asserted by the module; DIFF: ADDED 1, CHANGED 15, SAME 4,823).
Totals move only in STR.CONC.GROUND_SLAB|m3 (asserted; `code_totals_check` = that one key).

## 3. Reconciliation in units (ERS s.2.4)

- Lift-shaft cell: panels 11.9237 + 11.5200 + 10.9742 + 1.1875 = 35.6054 m2 x 0.10 = **3.560540 m3**; the engine cell net
  39.2979 = 35.6054 + shaft 2.8125 + ring 0.880 (re-adds to 1e-4; the two non-slab parts are named beside, with their
  owner lines, in the line's record, never valued here). The value equals the V3.0.33 held bound high (3.560540): the
  module refuses a value above a line's own held bound.
- Stair-zone panel: 8.372326 m2 x 0.10 = 0.8372326 -> **0.837233 m3**.
- **STR.CONC.GROUND_SLAB valued 17.240684 -> 21.638457 m3** (+4.397773; 24 -> 26 valued lines); held 1 line 0 .. 3.560540
  -> **none**. Structural concrete valued (all STR.CONC m3 lines) 298.221958 -> 302.619731 m3 (+4.397773).
- Cause texts: 14 lines, 0 figures moved (the module compares state, net, gross, range ends, rfi unlocks, deductions,
  additions, unit, code, location before / after; only the formula / notes / rfi question / range basis text changed:
  column lines 1 rfi + 1 basis hit each, CL-LIFT 1 formula + 1 rfi hit).

## 4. Engine vs freelancer (engineering terms; T-391 / T-428 basis)

- Ground slab: the freelancer's single plate is 29.550 m3 on the T-391 basis (engine 17.240684 + GS residual 12.309316).
  **Engine 21.638457 vs freelancer 29.550 m3: -7.911543 m3 (-26.77 %), was -12.309316 m3 (-41.66 %).** Improved by the
  lift-shaft cell (+3.560540, the I-07 term HELD -> AGREE: his plate x 0.10 on the same four panels = 3.560540) and the
  stair-zone panel (+0.837233, ENGINE_WRONG / FREELANCER_RIGHT, T-436).
- What stays between them (named, not valued): the T-391 strips term -7.188210 (ENGINE_RIGHT: beams / columns / pit own
  the plan under his plate, incl. shaft 3.24 + ring 0.96 + C9 0.25 of this cell); his plate beyond the drawn network
  -0.638616 (UNRESOLVED, his side, T-436 B-HIS); the lift-side pair -0.011427 (UNRESOLVED, F-LIFT 0.1143 m2 unplaced);
  the stub end triangles +0.009000 (T-436 F-018-ENDS ENGINE_WRONG, worker-traced, NOT re-measured by the Checker, so
  NOT wired here: the face 49a7dae5 and the stub BAND0038 are unchanged).
- Concrete roll-up consequence (stated, never edited in the roll-up record): the unexplained part -5.171754 m3 loses the
  stair-zone term -0.837230 -> **-4.334524 m3** (the Lead's row figure -4.343524 assumed the unverified -0.009 stub term
  wired as well); the HELD part loses I-07 -3.560540 -> **-112.867799 m3** (was -116.428339).

## 5. Verification evidence (Checker runs and commits)

| Piece | Task | Merge | Checker run | What the Checker re-measured |
|---|---|---|---|---|
| lift-shaft cell | T-444 | 1fb9dec6 | Verifier 2026-11-01T23:58Z session_01E6cPnbzoeHFrukut5tTajN | all four panels by handle: 35.605376 m2 x T 0.10 = 3.560538; C9 on the ring; F-C-T444-1 footing 7F7..7FA in OWN-007 at founding level, no plan deduction |
| stair-zone panel | T-436 | c943cabb | Verifier 2026-11-01T19:55Z session_01E6cPnciuxNnnDivYkfWWZ6 | panel 3.020 x 2.772294 = 8.372 m2; only HIDDEN flight lines inside; foundation plan: only footing 1B1A |
| cause texts | T-433 | 304b9af2 | Verifier 2026-11-01T19:48Z session_01E6cPneKQttYouw1QkpX3yH | F-T433-1 / F-T433-2 checked as stated (13 = GF 3 + 1F 10) |
| pit-wall basis | T-401 | 23f948bb | Verifier (MERGED) | pit depth (supplier) + GF build-up hold the wall height |

**Gate B re-measure list (for the Checker):** the four T-444 panels (OWN-007 / 009 / 010 / 047) and the stair-zone panel
OWN-011 on Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', GROUND BEAMS PLAN, band-face handles in `PIECES_T444.json`
and `summary_t436.json`; T = the printed 'T=10cm'. The 14 re-texted lines: their V3.0.41 vs V3.0.42 figures (DIFF.csv
quantity columns identical).

## 6. Missing / held / downstream

- HELD, unchanged: the pit walls (L-684fcad3, blank; pit depth RFI L-1 + D-22 / D-40), the 13 column ranges (RFI-S20).
- Not wired (named in `WAITING`): the stub end triangles (F-018-ENDS / E-T436-1, -0.009 / +0.027 m3) until the Checker
  re-measures them; F-LIFT 0.1143 m2; B-HIS 6.3864 m2 (his side).
- Downstream: no formwork for slab on grade on fill (no dependent formwork line points at L-41cfb82e: V3.0.33
  check_corrections passes on the whole candidate); the slab-top levels of OWN-009's +1.00 / +0.30 zones stay HELD in
  the level chain (no volume effect, T-444); B10-05 coverage text in BOQ_FAMILY_MASTER_1.37.0.
- The valued cell line keeps its engine reading record (`calculation.inputs.dimensions`: area 39.2979, region UNRESOLVED,
  free_columns 1) as history; the V3.0.33 HELD_BOUND record is kept whole under `superseded_by_v3042` (the V3.0.33 guard
  skips it), the former formula under `ground_slab_v3042.formula_before`.
- Observation (no change): the CL-LIFT text still also says '/ D-63' after the T-401 basis (T-433 flagged only D-43);
  Lead to decide whether that reference is right for the pit walls.
- Element register: GROUND SLAB UNDER A STAIR ON GRADE and LIFT PIT vs GROUND SLAB rulings (Lead 2026-11-01 20:17)
  applied as written; owner trade of both new valued pieces = CONCRETE (B10-05).

## 7. Regression

- `tests/t442_ground_slab_integration` (21): villa G442 hand fixture (not Alsenan; T 0.12; cell 26.40 m2 -> 3.168 m3 with
  shaft 2.56 / ring 1.93 beside re-adding to the engine net 30.89; stair panel 6.30 m2 -> 0.756 m3; ground slab 5.000 ->
  8.924 m3); adverse: 'slab cell dropped because a flight is drawn hidden over it' (the panel line is added, a 0 panel
  refused), panel twice / cell already lined, 'pit raft counted again as slab' (re-add refused), value above the held
  bound, stale binding, unverified area / T status stays HELD, mm / mm2 refused, mirrored panel order, missing data,
  cause text absent / on a valued line / not replacing, applied twice, tampered figure caught; family master 1.37.0.
- L3 on 8f4de2b3 (t442 + the importer folders impact lists for tools/urban_boq_m9.py and the concrete / lift /
  integration neighbours: m9_* 12 folders, t004a, t034, t079, t096, t106, t120, t131, t133, t142, t151, t167, t179, t187,
  t193, t211, t328, t344, t061, t212, t397, t401, t429, t430, t431, t433, t436, t444, t449, t450, t467): **1632 passed,
  22 skipped (private inputs absent), 2 xfailed, 0 failed**; freeze 0 differing; codemap stale none.

## 8. Rule and proposed lessons row (ERS s.7)

R-T442-1 (every villa; integrates R-T436-1, R-T444-1 .. 7): (a) a valued slab cell = sum of its re-measured panels x
the printed T, every non-slab part named beside with its owner, none valued here; (b) a slab panel is never dropped
because a flight is drawn hidden over it; (c) a panel line is added once (one GS line per cell, no panel in two lines);
(d) a cause-text change moves no figure; (e) held is never 0.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-02 | 4.398 m3 of drawn slab on grade sat outside the valued candidate (one cell held for a 'free column' that stands on the pit ring, one panel dropped as a 'stair zone'), and 14 held lines named the wrong designer item | the engine's cell reading (free column, stair zone) decided slab presence instead of the drawn band faces; cause texts were copied from a neighbouring item | a slab-on-grade cell is valued from its panels closed on drawn faces x printed T, with every non-slab part of the engine cell named beside with its owner; a cause text names the item that unlocks the line, and correcting it moves no figure (every villa, ground slabs and held-line texts) | tests/t442_ground_slab_integration (normal G442; adverse 'flight drawn hidden drops the slab', 'pit raft counted again as slab', 'cause text moves a figure') | PROPOSED |

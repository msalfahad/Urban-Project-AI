# T-290 Stairs and domes basis ledger: the candidate's stair / dome concrete lines, line id by line id

Worker 1 (lane S), 2026-10-25, run session_01YNUDkNaSyZFhKQ2xrkgzGg. Research piece for lane I (T-266): no engine,
candidate or released line changed, no V2 record written, no new measurement. Every piece value is the merged T-258 r2
closure ledger (b1b72a50, Checker Gate A r2); this task binds those pieces to the candidate's line ids, states each
line's basis, and names the soffit / formwork rows of each piece. ERS read; s.2.1 - 2.6, s.3, s.4 applied. Drawings
named by Drive folder and title; no coordinates, no client text committed.

## 1. Run and identity

Own run, Python 3.11.17, Drive "Alsenan chalet project" copies 'ST7757 dxf.dxf' (`9f9d1179`) and P7757.dxf from
P7757_DXF_COMPRESSED.zip (`ab54dd55`): research/agents_t167/v304_run.py then research/agents_t270/v3015_run.py:
**V3_0_15_BOQ_LINES.csv `a4dc01dd` = the T-270 r2 Gate B file, reproduced** (3,699 lines; the json `53450a1f` is one
of the two known run-variant json hashes, lessons 2026-10-25: csv identity governs). Project 'ST7757 villa
(structural set)', revision set `297e913d...` on every row (= T-289). V3.0.16 (T-245) is not merged (TODO r2); the
Lead's statement that its lines are byte-identical to V3.0.15 is cited, not re-run here: T-266 re-binds by line id.
Digest: `python3 -I research/agents_t290/t290_extract.py <run>/v3015 --out research/agents_t290`
(CANDIDATE_V3015_STAIR_DOME_LINES.json: 14 lines, values / states / engine ids only). Ledger:
`python3 -I research/agents_t290/t290_alsenan.py --write` -> BASIS_LEDGER_T290.csv + summary.json (byte-identical on
re-run; a test pins it).

## 2. The physical pieces and the rule (ERS s.2.1)

Inventory = the engine-free T-258 r2 component ledger (47 rows less the 6 BESIDE knees = 41 pieces: 13 closable,
1 CONFLICT, 11 HELD, 1 UNKNOWN, 15 OWNED_ELSEWHERE). Each piece is bound to at most ONE candidate line (by guard
element, element id and formula, never by row order); OWNED_ELSEWHERE pieces (heads / feet in B20 / B23, floor
landings in the slab, rings in the beam line, column corners, GS-08 / GS-16 parts) are refused on a stair line. A line's
drawing quantity is the sum of its pieces only when all are closable, at the WEAKEST of their statuses; otherwise the
line is HELD (or CONFLICT) and BLANK with its closable part beside it. Convention dimensions are never
DRAWING-CONFIRMED; undimensioned winders / curved parts are HELD blank (S-9); the staircase system is never labelled
VERIFIED as a whole (owner 2026-10-22 16:35; OWNER_RULE_STAIRS_2026-10-24 s.6: these are QUANTITY statuses per line).

## 3. Ledger: every stair / dome line once (BASIS_LEDGER_T290.csv; m3)

| Line id | Engine (state) | Pieces | Ledger status | Ledger m3 | Closable part beside | Held items |
|---|---|---|---|---|---|---|
| L-7863355dfcb68a681d2d ST-01 GF -> 1F | blank (BLOCKED_RFI; V3.0.5 info 2.786 convention) | MS1-L, MS1-T, MS1-T-SLAB, MS1-LD, MS1-U | HELD | blank (bound 2.441381 .. 2.662365) | **1.227952 VERIFIED** (MS1-LD 0.2304 Checker 22-10 17:18; MS1-U 0.997552 D-CHK-T180-1) | MS1-L CONFLICT 0.863029 .. 1.054813 (C-ST-4); MS1-T 0.12 .. 0.13, turn slab 0.2304 .. 0.2496 (C-ST-3 / G2-a) |
| L-67e4b0485135f84acc46 MS2-L | 1.033445 (SOURCE_DERIVED) | MS2-L | **VERIFIED** | 1.033444 | - | - (delta -0.000001, rounding) |
| L-2416e65f053a14199cfc MS2-LD | blank (BOUNDED 0.4696 .. 0.48) | MS2-LD-W 0.2392 + MS2-LD-E 0.2304 | **DRAWING-CONFIRMED** | 0.469600 | - | - (0.480 reading retired: T-258 s.3) |
| L-659243ed9fc2831c3ae8 MS2-TR | blank (BLOCKED_RFI) | MS2-TR | HELD | blank | - | C-ST-3 / G2-c |
| L-bb0e57b1948175a3d5b8 MS2-U | 1.001373 (SOURCE_DERIVED) | MS2-U | **VERIFIED** | 1.001373 | - | - |
| L-821032bc04a0b0d02133 ST-01b lobby D1 | blank (DG-5 placeholder) | D1 steps, D1 waist | HELD | blank | **0.100286 DRAWING-CONFIRMED** (steps net of the GS-08 wedge) | G2-w (D1 waist) |
| L-b6b0354b7842f0ed6e41 ST-02 round stair | blank (BLOCKED_RFI; info 1.769 convention) | RS-C, RS-C soffit, RS-S, RS-LD, RS-A, CA, 2CC | HELD | blank (no bound: RS-C unbounded) | **1.536225 ASSUMED — OWNER-APPROVED** (RS-S 0.942732, RS-LD 0.2164, RS-A 0.377093; Q-50 A cond) | Q-50 / Q-51, G2-w (RS-C); CA 0 .. 0.09; 2CC UNKNOWN |
| L-061e18cf35a4b6b33d68 ST-03 | 0.948267 (PROVISIONAL, convention riser 0.165 / waist 0.175) | E1 steps, E1 waist | HELD, **CITED from T-289** (row ST03) | blank | 0.355017 DRAWING-CONFIRMED steps | S-9 / G2-w (E1 waist) |
| L-8ea34765d16b54898140 DOME-A shell | 2.540681 | DOME-A shell | **VERIFIED** | 2.540681 | - | - |
| L-fffa895ed96b9d6a682c DOME-B shell | 2.540681 | DOME-B shell | **VERIFIED** | 2.540681 | - | - |
| L-d5401fa8986900c66c37 DOME-3 | blank (DG-5) | DOME-3 shell | HELD | blank | - | G3-a / D-21 |
| L-14f885e95132fa0cedec | blank (NA) | none: the SH04 'treads' are dome ribs | NOT_APPLICABLE | - | - | retired (T-193) |
| L-33769fb181e11dca13cc / L-004e8e9fd032cb0aeb72 | blank (NA) | none: convention domes | NOT_APPLICABLE | - | - | superseded by the shells (T-185 / T-193) |

**Residuals** (acceptance 1): STAIR line-id sum 2.983085 - named 2.983085 = **0.000000**; DOME 5.081362 - 5.081362 =
**0.000000**. Released in the candidate 8.064447 m3; on this ledger the lines with a quantity carry **7.585779 m3**
(4 VERIFIED lines 7.116179 + MS2-LD 0.4696 DC): ST-03 0.948267 leaves for HELD blank, MS2-LD +0.4696 enters,
-0.478668 m3 (-5.9 %) on the released figure; nothing becomes 0.

**Unbound pieces** (no candidate line, no other owner): **DOME-A drum, DOME-B drum** (HELD, G3-b: material / thickness
not printed). The candidate has no line, not even a DG-5 placeholder, for either drum: a silent omission for T-266
(add two HELD blank lines, item G3-b; never a value).

## 4. The "2.915 m3" of T-266, line id by line id (acceptance 2)

| Piece | Line id | Status | m3 | Evidence |
|---|---|---|---|---|
| ST01-MS1-LD | L-7863355dfcb68a681d2d | VERIFIED | 0.230400 | Checker 2026-10-22 17:18 |
| ST01-MS1-U | L-7863355dfcb68a681d2d | VERIFIED | 0.997552 | Checker own 0.9976, D-CHK-T180-1 rev2 |
| ST02-RS-S | L-b6b0354b7842f0ed6e41 | ASSUMED — OWNER-APPROVED | 0.942732 | Q-50 A cond (riser 4.50 / 28); 'T 16' printed |
| ST02-RS-LD | L-b6b0354b7842f0ed6e41 | ASSUMED — OWNER-APPROVED | 0.216400 | same; lane per T-258 r2 |
| ST02-RS-A | L-b6b0354b7842f0ed6e41 | ASSUMED — OWNER-APPROVED | 0.377093 | same; lane 1.200 per T-258 r2 |
| ST01b-D1-STEPS | L-821032bc04a0b0d02133 | DRAWING-CONFIRMED (not verified, not owner-approved) | 0.100286 | ST p.3 riser lines 1C4 .. 1C7 (T-258 r2) |
| **Sum** | 3 lines | | **2.864463** | |

The board's 2.915 is the T-258 **r1** sum (2.915089); the r2 corrections take **0.050626** out (D1 arrival wedge into
GS-08 0.025714, RS-LD column / lane 0.009200, RS-A structural lane 0.015712): 2.915089 - 0.050626 = 2.864463. T-266
uses 2.864463; of it 1.227952 VERIFIED, 1.536225 owner-approved, 0.100286 DRAWING-CONFIRMED. Beside it, MS2-LD 0.4696
DC (a bounded line in the candidate) is the fifth closable item T-266 releases at its own status. These parts sit in
lines that also hold HELD pieces, so releasing them is a LINE SPLIT (one line per closable piece group + the HELD
remainder blank), a lane I decision; the ledger gives the pieces, not a split.

## 5. One owner per piece: soffit and formwork rows (acceptance 3; listed, no concrete quantity)

Soffit rows (T-281 LEDGER_T281.csv, MERGED 40518c58) and formwork r4 rows (FORMWORK_LINES_R4.csv, MERGED 90203feb) are
given to the concrete piece they face, each row once (checked against both files by `check_owner_rows`):
MS1-L -> soffit ST01-MS1-L, forms 'MS1-L riser forms' + 'MS1-L waist soffit'; MS1-T -> 'MS1-T (turn (winders)) faces';
MS1-T-SLAB -> soffit ST01-MS1-T + 'slab under the main-stair winders'; MS1-LD -> ST01-MS1-LD + 'MS1-LD landing soffit';
MS1-U, MS2-L (+ head kink), MS2-U -> their soffit row + riser / waist forms; MS2-LD-W -> ST01-MS2-LD-W + 'MS2-LD landing
soffit' (one r4 row for both plates), MS2-LD-E -> ST01-MS2-LD-E; MS2-TR -> its soffit + faces rows; D1 / E1 steps ->
riser forms, waists -> waist soffit rows; RS-S / RS-LD / RS-A (+ head kinks) -> their rows; RS-C -> faces, RS-C soffit
-> ST02-RS-C; shells -> intrados + extrados rows; drums -> drum faces; DOME-3 -> the three DOME-TOWER rows. T-281's
column exposures (691, 380, 374), B3 / CA undersides, hidden pairs and wells belong to other members (not stair
concrete) and are not bound.

**Cross-trade findings** (named, not changed; formwork r4 rows UNCHANGED since T-111):
1. 'MS2-LD landing soffit' **3.000 m2** = 0.480 / 0.16, the T-111 reading T-258 s.3 retired as a double count; the
   drawn plates give 1.495 + 1.440 = **2.935 m2** (T-281): **-0.065 m2** = 1.30 x 0.05, the MS2-L last going.
2. 'RS-A riser forms (5 x 1.25 x 0.1607)' **1.004 m2** on the architectural 1.25 width T-258 r2 replaced with the
   structural lane 1.200 -> 5 x 1.20 x 0.1607 = **0.964 m2 (-0.040)**; 'RS-LD landing soffit' 1.41 m2 rests on the
   pre-r2 0.2256 m3 (T-281 measures the soffit directly, 0.870394 m2 plan + held strips).
3. 'E1 waist soffit' **NOT_APPLICABLE** ("section B-B draws the waist on fill") while the concrete side HOLDS the E1
   waist as not printed (T-258, T-287 G2-w: no thickness or support print within 3 m, a designer row). One physical
   fact, two merged readings: a CONFLICT for the Checker; until settled the E1 waist soffit is HELD, never NA by
   default (no quantity moves: the concrete side is already blank).

## 6. T-266 consumer shape (acceptance 5)

BASIS_LEDGER_T290.csv carries the T-289 columns in the same order (schema, project, revision set, candidate, group,
line id, item code, element id, physical element, engine qty, engine basis, printed support, sheets searched, drawing
qty / low / high, status, held item, delta, reason, evidence), then: engine_state, components, closable_component_m3,
closable_by_status, ledger_owner (T-290, or the ledger the row is cited from), soffit_rows, formwork_rows. A blank
cell is HELD / CONFLICT / not measured, never 0.

## 7. Verdict proposals (for the Checker)

- MS2-L, MS2-U, two shells: ENGINE_RIGHT (VERIFIED pieces, delta 0 / -0.000001 rounding).
- MS2-LD: ENGINE over-holds (BOUNDED 0.4696 .. 0.48): DRAWING-CONFIRMED 0.4696 (T-258 s.3).
- ST-01 GF, ST-02, D1 lines: ENGINE over-holds 2.864463 m3 of closable pieces inside BLOCKED lines (line split, lane I);
  the HELD remainder stays blank.
- ST-03: ENGINE_WRONG basis (T-289, cited): HELD blank; steps 0.355017 DC.
- Drums: ENGINE omission (no line): two HELD lines to add.
- Freelancer side unchanged from T-258 s.4 (ST-01 / ST-03 / domes reconciled to 0.000 by component; ST-02 UNRESOLVED);
  this task adds no freelancer number.
- Checker re-derive: L-2416e65f053a14199cfc (5E3 -> 5E2 1.300 x 632 -> 5C0 1.150 x 0.16 = 0.2392; 5E2 -> 5D4 1.200 x
  62F -> 5C0 1.200 x 0.16 = 0.2304) and the formwork finding 1 (3.000 vs 2.935 m2) from the same handles.

## 8. Rule, test, lesson

Rule (research, every villa; provenance T-258 / T-281 / T-289 / T-290; a new rule version when adopted,
R-STAIR-DOME-BASIS-1): every stair / dome concrete line of a candidate is bound to pieces of an engine-free inventory;
one piece one line; the line's quantity only when every piece is closable, at the weakest status; else blank with its
closable part beside it; a convention dimension is never DRAWING-CONFIRMED; an undimensioned winder / curved piece is
HELD blank; a piece another line owns is refused; each soffit / formwork row has one piece owner; a piece no line
carries is reported as an omission (`stair_dome_basis.py`).
Tests: tests/t290_stair_dome_basis (villa K hand fixture: drawn flight + chamfered landing 0.424726 + 0.203250 =
0.627976 DC, owner-rule flight + undimensioned winder HELD blank with 0.509671 beside it, convention-waist entrance
HELD with steps 0.135, verified shell 1.256637, retired line; ADVERSE: winder with a value / 0 refused, convention waist
as DC or VERIFIED refused, the same piece in two lines refused, an owned-elsewhere piece on a stair line refused, HELD
without item / with 0 / single-end CONFLICT refused, one soffit row on two pieces refused, named-total residual and
mm-scale slip refused, cited row booking a quantity refused, flight formula without a printed waist refused, mirror order
invariant; Alsenan pins: 14 lines once, residual 0, statuses, 2.864463 mapping and the 0.050626 r1 -> r2 step, drums
unbound, ST-03 cited, committed csv reproduces).
Lessons row (proposed): 2026-10-25 | The integration row for the stair line quoted 2.915 m3 of held verified /
owner-approved parts, a figure the closure ledger had corrected to 2.864463 m3 in its r2 the same day (-0.050626), and
the formwork r4 rows still stand on two readings the same r2 retired (MS2-LD 3.000 vs 2.935 m2; RS-A width 1.25 vs 1.20) |
A merged correction reached the ledger it was made in, not the rows and trades that quoted its earlier figures | A
figure carried into another row or trade cites the ledger REVISION it comes from, and every revision lists the
dependants it invalidates (rows, other trades' lines on the same piece) for the Lead to re-open (any villa, any trade) |
tests/t290 test_2915_label_mapped_to_line_ids | OPEN (T-290 READY).

## 9. What is missing

Line splits and the drum lines are lane I (T-266); MS1-L (C-ST-4), MS1-T / MS2-TR (C-ST-3), D1 / E1 / RS-C waists
(G2-w), drums and the tower dome (G3) are designer items; the E1 waist soffit reading (finding 3) needs the Checker's
read of section B-B. No accuracy claim; no owner question (ERS 2.7 not met: every open item is already a designer row).

# T-192 Concrete ownership at stair feet, heads, landings and columns: the whole staircase system once (every villa)

Worker 1 (lane S), 2026-10-23. Research + tests only (`research/agents_t192/*`, `tests/t192_staircase_ownership/*`); the
T-189 module `engine/source/concrete_overlap_ownership.py` is used READ ONLY (every new geometry is a new function of
`t192_staircase_junctions.py`); no engine, method, rule, knowledge or registry file changed; nothing released. ERS
s.2.1-2.4, s.3, s.4 A/B/C and s.7 applied. Drive "Alsenan chalet project" read this run (read-only; private copies in
`.work/private`, never committed): ST7757 dxf.dxf (sha 9f9d1179), P7757_DXF_COMPRESSED.zip (P7757.dxf sha ab54dd55).
Released baseline A re-run this session on engine 06c2b045: REPRODUCED, 1,455 lines, BOQ_LINES.csv b96185d4.
Development villa: not an accuracy claim.

## 1. Result in engineering terms (stair concrete, m3)

| Item | Before (ledger rev2, T-189) | After (rev3, this task) | Change | Cause |
|---|---|---|---|---|
| ST-01 MS2-L (1F -> 2F lower flight) | 1.0589 (VERIFIED on the owner formula) | **1.0334** | -0.0254 | its first riser line (646, y 45.198) is 0.15 m INSIDE the B20 band (stair-side face 45.348); the waist below the 1F floor over that 0.15 m lies inside B20, which route G bills at the full 0.40 x 0.75 through the shaft |
| ST-01 dog-leg | 4.6312 | **4.6058** | -0.0254 | |
| ST-03 E1 entrance flight (steps) | 0.3570 | **0.3550** | -0.0020 | its arrival wedge (5th triangle) runs 0.05 m into the released ground-slab line L-83e4f6fa87db7452e2d2 (face 4.18 m2 x 0.10): slab owns (Q-62 A cond) |
| Staircase system | 6.6754 (MS1-L 0.863 HELD) | **6.6479** (not held 5.7849) | -0.0275 | |
| Drawing-derived knees (NOT in the owner method) | not measured | **+0.1135** reported beside | | section 5 |
| Released route G stair line L-ffef7b38f37ffa75bc3a (2.786; V3.0.4 L-7863355dfcb68a681d2d) | 2.786 | correction **-0.0586** (range -0.0501 .. -0.0674) | | its east run (MS1-U) is measured to the last riser line 0.20 inside B20 (T-189 estimate 0.065 replaced by the line's own profile) |
| Stair formwork (T-163 r3) | 44.533 m2 | **43.777 m2** | -0.756 m2 (-1.7 %) | no soffit form over the waist inside B20 / B23 (MS1-U 0.2746, MS2-U 0.2751, MS2-L foot 0.2063) |

Freelancer comparison unchanged in kind (his 8.131 for ST-01 vs own 4.606: the head / foot ownership is not in his
figures; T-184 s.5 reconciliation stands, the own side lower by a further 0.0254). Staircase system status unchanged:
PARTIALLY VERIFIED (owner 16:45); the rev3 MS2-L figure is DRAWING-CONFIRMED until the Checker re-measures it.

## 2. The physical elements and every junction (ERS s.2.1)

Inventory from T-184 (ST-01 dog-leg GF -> 1F -> 2F, ST-01b lobby flight D1, ST-02 round stair, ST-03 entrance E1).
Frames: ST p.5 mapped onto ST p.4 by +38.724 m in x (shaft east wall 5D4 21.069 -> 296 59.793; west 5E3 18.569 -> 284
57.293; y identical); ST p.3 by +38.725 (98.518 -> 59.793).

| Junction | Drawing reading (handles) | Billed elements (released A / V3.0.4) | Owner (R-CONC-OWN-1 / -1a) | m3 |
|---|---|---|---|---|
| MS1-U head / B20 | T-189 | B20 0.990 full depth | B20 | 0.0573 (T-189, unchanged) |
| MS2-U head / B23 | T-189 | B23 1.11375 full depth | B23 | 0.0575 (T-189, unchanged) |
| **MS2-L foot / B20** (1F floor) | 12 riser lines 646 (45.198) .. 632 (48.498) at 0.300, x 18.569 .. 19.719 (p.5); B20 faces 458 / 2C6 (44.948 / 45.348), x 52.693 .. 59.793 (p.4) | B20 span 2 (BAND0043.2) covers both lanes x 56.493 .. 59.793 | **B20** | **0.0254** (only the waist below the floor; the step triangles stand above +5.50) |
| MS2-L foot beyond the band (s 0.15 .. 0.33) | west lane north of B20 = stair zone GF-025 (T-139: not slab) | none | stair | 0 overlap |
| MS1-U foot / MS1-LD; MS2-U foot / MS2-LD east | first riser lines 25B / 62F at the landing edge 48.448 | landings (stair ledger) | touch | 0 |
| MS2-L head / MS2-LD west | last riser 632 (48.498) = landing edge (closing riser line 5E2 x 19.869) | landing (stair ledger) | landing (Q-62 wedge 0.030171, T-184) | unchanged |
| MS1-L foot / GF +1.00 | p.4 first line 45.198, p.3 first line 112 (45.798): either way 0.45 .. 1.05 m north of the south ground beam 15C / 7CC (44.448 / 44.748) | the shaft floor face (2.40 x 4.80 = 11.52 m2 on p.3, no slab bar, no thickness) is in NO ground-slab line of A (25 ground faces, none of 11.52) | stair keeps; floor scope UNKNOWN | 0 (MS1-L HELD, C-ST-4) |
| D1 head / shaft floor +1.00 | 1C4 (48.448) .. 1C7 (47.548), LEVEL '+0.30' / '+1.00' | none | stair keeps its arrival wedge 0.0315 | 0 |
| **E1 head / ground slab + ground beam** (p.3) | 5 riser lines 18A (93.268) .. 179 (94.468); GB band 178 / 7DB (94.418 .. 94.718); slab face 94.718 .. 95.818 x 41.248 .. 45.048 = 4.18 m2 | ground slab L-83e4f6fa87db7452e2d2 0.418 (A); ground beams not billed (59 UNBOUND exposures) | slab 0.0020; GB part UNDETERMINED | **0.0020** deducted; 0 .. 0.0714 exposure in the GB band |
| RS-A head / plate C-T1 (ST-02) | last riser 315 (40.448); B29 band 2CE / 463 at 41.998 (1.55 m away); B21 face 433 crosses the string 289 (x 68.113) at y 40.452 | plate (slab) | plate (Q-62 wedge 0.030133, T-184) | no full-depth band at the line: unchanged |
| RS-S head / RS-LD; RS-A foot / RS-LD | 2C4 (66.963); 2C8 (39.248) | landing | landing / touch | unchanged |
| RS-LD / column 374 | 67.563 .. 68.163 x 37.848 .. 38.098: 0.55 x 0.05 = 0.0275 m2 inside the landing | column: BLOCKED_RFI in A | column (already deducted in T-184) | 0.0044 (in no line of A until columns are wired) |
| **COL-1F-36 / MS2-L** | S-COL.BON 691 x 18.369 .. 18.619 (drawn 0.25), wall 5E3 18.569: 0.05 into the lane over y 46.148 .. 46.648 | columns billed by no line (A: 30 GF / 22 1F lines BLOCKED_RFI; V3.0.4: not wired); T-119 ledger: schedule 0.20 x 0.50, full interval 4.2 m | UNDETERMINED: stair keeps; COLUMN once T-119 lines are wired | exposure 0 .. 0.0067 (drawn section) |
| COL-GF-06 / MS1-L | 36B x 57.093 .. 57.343 (0.25 = schedule) | as above | with MS1-L (HELD) | not measured |
| 1F / 2F floor-arrival landings | 2.50 x 1.95 = band + 1.55 / 1.50 of GF-077 / 1F-062 | slab + beam | slab + beam; never stair (R-STAIR-LAND-1) | 0 in the stair |
| hidden pairs (layer 5) | 535 / 536 across RS-S (beam CA, HELD 0 .. 0.09, T-184); **2CC / 2CD** (x 67.488 / 67.588, y 38.048 .. 41.998) across RS-LD, RS-A and the plate: no mark, no schedule row | none | UNDETERMINED (consultant item) | not measured |
| 'B3 (With Stair)' at the landings' north edges (279 / 5C0 y 49.648) | plan touch | HELD (Q-61 (2)) | | not measured |

## 3. Reconstruction from first principles (ERS s.2.3)

MS2-L: r = 0.168 (12 risers, 2.016 m, section A-A), g = 0.30, w = 1.20, t = 0.16, k = r / g = 0.56, d = t / cos =
0.16 x 1.146124 = 0.183380 m. The flight starts at +5.50 (1F) with its first riser line a = 45.348 - 45.198 = 0.150 m
inside B20. Inside the band the waist lies below the floor between the soffit z' = k s - d and z' = 0:
V = (d a - k a^2 / 2) w = (0.183380 x 0.15 - 0.28 x 0.0225) x 1.20 = (0.027507 - 0.006300) x 1.20 = **0.025448 m3**
(exact 3-D intersection 0.025448, test). Containment: the flight solid in the band spans z +5.317 .. +5.500, inside B20
+4.75 .. +5.50 (margins 0.567 m down, 0 up: it is the floor-level solid; a stair reference lower than the beam top by
up to 0.567 m does not change it, a higher one cannot occur since the flight starts on the floor).

E1: r = 0.17, g = 0.30, w = 2.80; arrival wedge s 1.20 .. 1.50 (x 94.468 .. 94.768), heights 0.85 - 0.5667 s; inside the
slab face from x 94.718 (s 1.45 .. 1.50): 1/2 x 0.05 x 0.02833 x 2.80 = **0.001983 m3**; inside the GB band (s 1.20 ..
1.45) 0.0694 + the last 0.05 of step 4 (0.0020) = 0.0714 exposure (levels of the ground beam not printed).

Released line: `stair_geometry.straight_flight(12, riser, 0.30, 1.15, waist)` (the line's own run: plan 3.795 = 1.15 x
3.30, base 1.071034), profile clipped to its last 0.20 m: riser 0.165 / waist 0.175 -> 0.058586 m3; the nine readings
of the line give 0.0501 .. 0.0674. The west run of the same line (12 lines from 45.198 on p.4) is MS1-L at GF +1.00,
4 m below B20: no physical intersection, no correction.

Owner manual method and drawing-derived method side by side (ERS s.2.2): the owner formulas (Q-19 steps, Q-47 A waist
between the first and the last riser line, Q-62 A cond wedge deduction) are kept term by term; the drawing-derived 3-D
solid decides only which member owns a part (sections 1-2), and separately shows the knees (section 5).

## 4. Reconciliation (ERS s.2.4) and the whole-system check

| Group | Owner-method billing rev2 | rev3 | Drawing-derived (knees settled) |
|---|---|---|---|
| ST-01 (MS1-U, MS2-L, MS2-U, B20, B23, GF-077, 1F-062, MS1-LD, MS2-LD E / W) | FAIL: DOUBLE 0.025448 (MS2-L foot), GAP 0.038017 | FAIL: DOUBLE 0, GAP 0.038017 = top knee 0.039174 (net of the wedge sliver T-184 already leaves in the stair) - bottom knees 0.000573 + 0.000586 (OUTSIDE) | **PASS**: union 7.094136 = sum of owned 7.094136 |
| ST-03 (E1, ground slab, GB band) | FAIL: DOUBLE 0.001983 | **PASS_HELD** (GB band UNDETERMINED 0 .. 0.0714); union 0.773017 = sum owned | same |
| ST-02, ST-01b | no billed member inside their solids (RS-LD column corner already net) | unchanged | knees section 5 |

Residual: 0.000001 m3 (numerical, below the module tolerance 1e-5).

## 5. Knees: drawing-derived concrete the owner method does not carry (not added, not released)

The owner's waist (Q-47 A) is plumb-cut at the first and the last riser line. Where a flight arrives FROM BELOW into a
landing or a plate, the drawn soffit continues past the last riser line until it meets the landing soffit:
V = 1/2 (s_top - L) (H - t_L - (k L - d)) w, s_top = (H - t_L + d) / k. Where a flight LEAVES a landing upward and
d > t_L, the plumb cut bills a re-entrant triangle that is not built: V = 1/2 s_b (d - t_L) w, s_b = (d - t_L) / k.

| Knee | m3 | Hand |
|---|---|---|
| MS2-L top, under MS2-LD west (+7.516, T 16) | +0.039242 | 1/2 x 0.34175 x 0.19138 x 1.20 |
| RS-S top, under RS-LD (+4.696) | +0.037169 | w 1.20 |
| RS-A top, under the plate C-T1 (+5.50, T 0.16 note 18) | +0.038754 | w 1.25 |
| MS1-U / MS2-U / RS-A bottom | -0.000573 / -0.000586 / -0.000540 | |
| **net** | **+0.1135** | 1.7 % of the system |

Heads and feet inside a full-depth beam have no knee (the beam face bounds the soffit). MS1-L / winders and E1 / D1
(waist not printed) are held. Status DRAWING-DERIVED; whether the BOQ carries the knees is the owner's method choice
(ERS s.2.2): reported for the Lead's daily package, no owner question raised (both values are shown, nothing is
blocked).

## 6. Formwork on the same boundary (T-163 r3, 44.533 m2)

No soffit form where the waist is inside a full-depth beam: MS1-U 0.20 x 1.20 x 1.14396 = 0.2746, MS2-U 0.2751, MS2-L
foot 0.15 x 1.20 x 1.14612 = 0.2063 -> **43.777 m2 (-0.756)**. MS1-U / MS2-U riser 12 (0.200 / 0.2016 m2) is the
vertical face above the step-11 tread at the band face: ONE face, counted as the stair riser; the HELD T-163 "beam side
faces next to STAIR" (GF 0 .. 13.731, 1F 0 .. 3.195 m2) must exclude it when released. MS2-L riser 1 rises from the
beam top: formed, unchanged. Correction for the T-163 owner / lane I; no T-163 file is edited.

## 7. Per candidate line: what lane I must do (no quantity changes in the engine here)

1. L-ffef7b38f37ffa75bc3a (released A) / L-7863355dfcb68a681d2d (V3.0.4) STR.CONC.STAIR GF: -0.0586 m3 (range
   -0.0501 .. -0.0674) inside B20, or replace the line by ledger rev3 (it also lacks the 1F -> 2F storey, D-T184-1).
2. Any V3.0.x stair ledger wiring: take `T192_STAIR_LEDGER_REV3.json` (rev2 and rev1 kept unchanged).
3. L-83e4f6fa87db7452e2d2 ground slab 0.418 with L-5493f3e0cc5801512838 (engine E1 0.948): no double in A (the engine
   E1 run stops at x 94.468, 0.25 m short of the slab face); the ledger's E1 carries the 0.0020 slab-owned deduction.
4. L-507f96568d2bbe8899dd (ground-slab stair zone, BOUNDED_EXPOSURE 0 .. 0.837) with L-496d997d755b6367a169 (ST-02):
   never released together over the same 8.37 m2 zone.
5. Column lines (T-119) when wired: deduct their intersections with MS2-L (0 .. 0.0067, section position to be read)
   and MS1-L, and give the RS-LD corner 0.0044 to the column line.
6. Ground beams when billed at full depth: own the E1 head (0 .. 0.0714) by the same rule.

## 8. Rule, check, tests (ERS s.4 B, C)

**R-CONC-OWN-1a** (proposed, `R-CONC-OWN-1a.json`, extends R-CONC-OWN-1 unchanged; any villa): foot corollary
(V = (d a - k a^2 / 2) w inside a member billed through the floor junction; never the steps; an unbilled floor keeps it
in the stair, UNDETERMINED), head-on-ground corollary, column corollary (COLUMN > STAIR when the column line runs the
storey; else UNDETERMINED), knee rule (owner method and drawing-derived side by side), landing rule, formwork
corollary. The COLUMN / STAIR pair is passed to the module as an extra established pair from this script; the module's
own table is not edited (a test shows it still reports OWNER_UNDEFINED).

**Tests `tests/t192_staircase_ownership` (all pass)**, synthetic Villa S (hand values in the module docstring): foot
0.10 inside a full-depth band DOUBLE 0.0142705 (adverse) at 0 / 30 / 60 / 135 deg and mirrored, corrected PASS, in mm;
foot on the band face PASS (normal); unknown unit refused; foot on a ground slab running under the flight DOUBLE
0.023541, slab owns, corrected PASS, sum owned = union; slab stopping at the first riser line PASS; foot on an unbilled
floor PASS_HELD, never deducted; landing poured with the slab and billed again DOUBLE + OWNER_UNDEFINED (adverse); landing
at the slab edge PASS; top knee 0.028125 at three rotations, GAP in the owner method and PASS once settled; bottom knee
0.00031347 OUTSIDE; no bottom knee when t_L >= d; column through a flight DOUBLE 0.0036406, column owns, corrected PASS;
module profile still OWNER_UNDEFINED. Development villa: MS2-L foot 0.025448 = hand and = the waist only; rev2 geometry
= the verified ledger 1.058893; owner-method / drawing-derived checks and sum owned = union; knees; E1 slab part = hand;
released line in-band 0.058586 within its range; ledger rev3 re-generated byte-identical; rev2 file unchanged.

## 9. Not done / open (no quantity guessed)

- MS1-L stays HELD (C-ST-4); its foot meets no billed element under either riser reading, its column COL-GF-06 overlap
  is applied with it.
- The ST-01 shaft floor (11.52 m2 at +1.00 / +0.30 on ST p.3) is in no concrete line: scope UNKNOWN for lane A / the
  Lead (lobby floor), never 0.
- MS2-LD west reading for the Checker (not changed here, row PARTLY VERIFIED): drawn x 18.569 .. 19.869 (1.30, incl. the
  0.10 well strip) x y 48.498 .. 49.648 (1.15) = 1.495 m2 -> 0.2392 m3; east 1.20 x 1.20 -> 0.2304; total 0.4696 vs the
  ledger row 0.480 (-0.0104).
- The hidden pair 2CC / 2CD across RS-LD / RS-A / the plate: consultant item (no mark).
- Column section position (1F 0.20 x 0.50 scheduled vs 0.25 drawn): T-119 / Checker.

## 10. Lessons-register row proposed (ERS s.7)

| 2026-10-23 | MS2-L 1.059 m3 VERIFIED on the owner formula, yet its waist below the 1F floor (0.0254) is also in B20; E1's wedge 0.002 also in the ground slab | ownership was checked at stair HEADS only (T-189); a flight FOOT whose first riser line lies inside a full-depth band at the floor it starts from was never compared with that member; and a formula-correct quantity was taken as ownership-correct | R-CONC-OWN-1a: check every foot, head, landing and column of every staircase against every member billed through it; the foot deduction is the waist below the floor inside the member (never the steps); unbilled floors and unknown sections stay UNDETERMINED; knees reported beside the owner method; formwork on the same boundary (any villa) | tests/t192_staircase_ownership (adverse: foot 0.10 inside a band DOUBLE 0.0142705; foot on a slab running under the flight; landing billed with the slab) | rule proposed; ledger rev3; Checker to verify |

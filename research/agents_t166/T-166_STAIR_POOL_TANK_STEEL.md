# T-166 Alsenan stair, swimming-pool and water-tank steel by bar population (NO REPO CODE)

Worker 1 (structural lane S), 2026-10-22. Development villa, not an accuracy claim. Nothing is wired and no released
quantity changes: a checked piece for the V3.0 candidate (lane I) once the checker has re-read it.

Sources (Drive "Alsenan chalet project", private copies in the git-excluded folder, never committed): "ST7757.pdf"
(sha256 74da1523...; no text layer, read at 220 / 250 / 400 dpi) p.3 ground-beam plan, p.4 / p.5 / p.6 roof-slab plans,
p.7 DETAIL OF SWIMMING POOL (N.I.S.), p.8 notes 9 and 22, p.14 lift / parapet / boundary-wall details, p.15 typical slab
detail, p.16 TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S.) and TYPICAL DETAIL OF STAIR BEAM; "ST7757 dxf.dxf" (sha256
9f9d1179...): the plan callouts (TEXT on S-TEXT-SLAB) and the pool outline (S-BW polylines).
Geometry is not re-invented: stairs from the checker-merged flight ledger (research/agents_t111/ledger_summary.json: sloped
waist length L = drawn waist m3 / (width x 0.16), Q-47 A; risers and treads per Q-46 A), pool from T-060 / T-063 (D shape)
re-measured on the structural DXF this run (S-BW: outer 3.50 x 1.75 + half circle r 1.75, inner 3.10 x 1.55 + r 1.55,
one centre; walls 0.20) with owner Q-26 A (flat floor, inner depth 1.15 m; floor 0.40 m printed on p.7).
Rules: URBAN-REBAR-NET-AND-PROCUREMENT@v1 (kg = count x length x d^2/162, never kg/m3), owner Q-71 (OPEN: counts A / B / C
side by side), Q-46 A, Q-47 A, Q-26 A, Q-50 A cond (round stair CALCULATED), Q-62 A cond, UP-QTY-STATUS-001.

Files: `t166_stair_pool_tank_steel.py` (`--check` synthetic fixture, `ledger` writes `T166_STEEL.csv`, one row per bar
family, and `T166_SUMMARY.json`).

## 1. Result in engineering terms (kg; every count HELD on owner Q-71, lengths measured)

Counts: A = ceil(rate x width), B = A + 1 (a bar on both edges), C = rate x width unrounded. On the pool's closed wall
perimeter there are no edges, so B = A there (flagged for the checker).

| Element | Plan-printed bars, length measured (A / B / C) | p.16 typical-only families, HELD (A / B / C) | Held, never 0 |
|---|---|---|---|
| Main stair GF -> 1F -> 2F (4 flights + 2 landing strips) | **307.01 / 337.71 / 294.73** | 220.26 / 236.72 / 215.79 | top bars (7 families, counts only), winders, development |
| Round stair, straight + short flight (Q-50 A cond) | **75.30 / 82.82 / 73.14** (CALCULATED) | 63.20 / 67.93 / 61.45 | curved flight, corner landing 18.17 .. 21.73, development |
| Entrance flight, hall -> lobby flight | none printed | none | HELD: on no slab plan, no callout, waist not printed |
| Swimming pool, reading R1 (deep-end population, p.7) | - | - | **HELD 888.90 / 900.01 / 927.54** (designer item) |
| Swimming pool, reading R2 (shallow-end population, p.7) | - | - | HELD 615.34 / 620.13 / 639.45 |
| Water tank walls / base | none printed | none | HELD: not drawn in either discipline; tank (T&B) roof panels are in the slab ledger T-152 |

- **Stairs, measured part (lengths and kg/m), count HELD on Q-71**: 367.88 (C) .. 382.31 (A) .. 420.54 (B) kg, of which the
  round stair 73.14 .. 82.82 kg is CALCULATED (Q-50 A cond).
- **HELD, never 0**: p.16-only families (A / B / C 283.46 / 304.65 / 277.24) (distribution ø12/20cm, step bars ø8/15, nosing 1ø12, landing top 6ø12/m)
  277.24 .. 304.65 kg; top bars 6ø14/m at heads and feet (counts 8 / 9 / 7.2 per end, length not dimensioned on the N.I.S.
  section); flight bars running through the landing strips (extent not drawn); development / laps (note 9, 2 x 40 d .. 2 x
  70 d per bar): 161.82 .. 283.18 kg on the measured bars + 211.56 .. 370.24 kg on the typical-only bars.
- **Pool**: both readings HELD (section 3); development / laps R1 233.88 .. 409.28 kg.
- Owner-basis lengths (the approved STAIR_CONCRETE_V1 census: 10 goings on MS1-L, hypot(11 x 0.30, 12 r) on the upper
  flights) give the 4 main-stair flights' main bars A 237.43 kg against 228.00 kg on the drawn flight lengths (+9.43 kg,
  +4.1 %); the drawn lengths are carried (T-111 drawing-derived ledger), the owner basis is shown.

### Against the freelancer and the frozen engine studies

| Line | kg | Hand (this ledger) | Difference | Verdict proposal |
|---|---|---|---|---|
| Freelancer "stairs + dome" steel (one lump: 3.9 t on 21.83 m3 = 178.6 kg/m3; includes the 3 domes 6.78 m3) | 3,900 | stairs 367.88 .. 420.54 measured + 277.24 .. 304.65 typical HELD + top bars, development HELD; domes not in this package | not like for like | **RULE_DIFFERENCE**: an allowance per m3 with no bar population, and it mixes the domes in; no % |
| Freelancer pool steel (1.5 t on 12.348 m3 = 121.5 kg/m3, incl. the 3.48 m3 pump room the owner says does not exist, Q-19) | 1,500 | R1 888.90 .. 927.54 / R2 615.34 .. 639.45, development HELD | not like for like | **RULE_DIFFERENCE** (allowance per m3); no % |
| Freelancer water tank | no row | tank walls HELD; (T&B) panels in T-152 | - | no comparison |
| Frozen S8.7c main bottom 8ø16/m, B-27-S (C reading) lower / upper flight | 46.857 / 57.269 | MS1-L 46.857 / MS1-U 57.269 (C) | 0.000 / 0.000 kg (0.0 %) | ENGINE_RIGHT on the length (independent re-derivation from the T-111 ledger, same 29.651 / 36.241 m) |
| Frozen S8.7 A1-L1 half landing, E-W 8ø16/m (rate density) | 18.204 | the same 1.20 m of the GF strip bars, C 18.204 (A 18.963, B 20.859) | 0.000 kg at C | consistent; **no double count**: lane I must not add both |
| Frozen S8.2 pool | 0 released (21 families blocked / conflict) | R1 / R2 HELD with lengths | - | the frozen study's "which plan run" blocker is answered by the DXF D outline; the zone question remains |

## 2. Stairs: what the drawings print and how each bar family was measured

- **Plan callouts** (p.4 GF roof, p.5 1F roof; DXF TEXT 8%%C16/m, rotations 0 / 90 / 314 deg): each main-stair flight panel
  carries a vertical "8ø16/m" (bars along the flight) and the north strip a horizontal "8ø16/m" (bars across, wall to wall);
  "T 16" in each stair panel (Q-47 A). Round stair: "8ø16/m" along the curve (314 deg), along the straight flight and along
  the short flight. 2F roof (p.6) draws no stair. Ground-beam plan p.3 draws the stair outlines only (no bars).
- **p.16 TYPICAL STEEL LAYOUT-STAIR SECTION (N.I.S., levels +0.00 / +2.00 / +4.00 that are not Alsenan's)**: waist bottom
  8ø16/m (= the plan callout), distribution ø12/20cm under it, step bars ø8/15 (tread + riser shape), one 1ø12 at each
  nosing, top bars 6ø14/m from a landing or beam into the flight, 6ø16/m at a foot on a ground beam (G.B 30 wide, 3ø14,
  4ø16, ø8/15cm, 2ø14/30cm); landing: bottom dot row 8ø16/m, top dot row 6ø12/m, landing edge beam 20 x 40 (2ø12, 4ø16).
  No plan callout, note or reference ties this typical section to the Alsenan stairs; the frozen S8.7 study holds the same
  families "typical detail only". This ledger therefore measures them but keeps them **HELD_TYPICAL_ONLY** (a Lead /
  checker point: the slab ledger applied the p.15 typical slab detail for curtailment; if the same applies here, these
  277.24 .. 304.65 kg become measured-with-count-held like the main bars).
- **Lengths**: main bars = the sloped waist face to face (T-111 drawn ledger); distribution and nosing bars = the flight
  width; step bars = going 0.30 + riser (legs into the waist not dimensioned); strip bars = 2.50 m wall to wall (T-111: 1.20
  + 0.10 well + 1.20). No cover deducted (note 22 is a minimum), as in the slab ledger.
- **Step-bar count**: one per drawn tread (MS1-L 9, the 10th tread is the first winder; upper flights 11, the 12th riser
  arrives on the floor or flat quarter (Q-62: that arrival wedge belongs to the slab); RS-S 10, RS-A 4).

Re-measured by hand (the checker can re-count one flight):

| Family | Reading | Bars | Length per bar | m | kg/m | kg |
|---|---|---|---|---|---|---|
| MS1-U main 8ø16/m, 1.20 wide | A ceil(9.6) = 10 / B 11 / C 9.6 | 10 | 0.724812 / (1.20 x 0.16) = 3.7751 | 37.751 | 1.5802 | **59.655** (B 65.621, C 57.269) |
| MS1-U distribution ø12/20cm | A ceil(3.7751 / 0.20) = 19 / B 20 | 19 | 1.20 | 22.80 | 0.8889 | 20.267 (HELD typical) |
| MS1-U step bars ø8/15 | A ceil(8.0) = 8 per tread x 11 | 88 | 0.30 + 0.16667 = 0.46667 | 41.067 | 0.3951 | 16.224 (HELD typical) |
| MS1-U nosing 1ø12 | exact 11 | 11 | 1.20 | 13.20 | 0.8889 | 11.733 (HELD typical) |
| GF strip bottom 8ø16/m across, 1.20 deep | A 10 / B 11 / C 9.6 | 10 | 2.50 | 25.00 | 1.5802 | **39.506** (B 43.457, C 37.926) |

## 3. Swimming pool: two printed zones for one flat floor (HELD, designer item)

p.7 draws a two-depth pool (deep end, slope, shallow end, every depth "AS PER ARCH", N.I.S.); the owner ruled the floor flat
at the printed 1.15 m (Q-26 A), so which zone's population governs the whole pool is not printed. Both readings are carried:

| Family (re-read at 400 dpi) | R1 deep end | R2 shallow end | Length basis |
|---|---|---|---|
| Wall vertical, outer face | 7ø14/m (L-bar, leg along the floor bottom) | 6ø12/m (one U bar over the top, both faces) | 0.40 + 1.15 = 1.55 m; outer perimeter 12.4978 m (3.50 + 2 x 1.75 + pi x 1.75) |
| Wall vertical, inner face | 7ø12/m | 6ø12/m | 1.55 m; inner perimeter 11.0695 m |
| Wall horizontal, both faces | ø12/20cm | ø10/20cm | closed hoops on the face perimeters; 8 / 9 / 7.75 over 1.55 m; one lap each (12.50 > 12 m stock) HELD |
| Floor, top and bottom, along the section lines | 7ø14/m | 6ø12/m | chords across the outer D (10.936 m2), face to face |
| Floor, top and bottom, dot rows (X leader to both rows) | 6ø14/m | 6ø12/m | chords in the other direction |
| Wall top | 3ø16 | none printed | centre-line perimeter 11.7836 m |
| Floor / wall corner (under the wall) | 3ø16 | 4ø16 | 11.7836 m |
| Sloped zone (6ø14/m bottom, 6ø12/m top) | not used (Q-26 A: flat) | not used | - |

The plan direction of the section is not marked; on the D outline the chord sums are identical in x and y (A 78.196 m for
7/m both ways, checked against a hand series of chords to 0.0001 m), so the kg does not depend on it.
Hand check (R1 outer verticals): ceil(7 x 12.4978 = 87.48) = 88 bars x 1.55 m = 136.40 m x 1.2099 = **165.03 kg**.

## 4. Water tank (HELD, designer item)

p.6 prints "WATER TANK PLACE" with a cloud over two "T 18" (T&B) roof panels (2F-011 7ø14/m x / 6ø14/m y, 2F-013 6ø12/m
both); p.7, p.14, p.15 and p.16 were searched: no tank wall, base, opening or member is drawn, noted or scheduled (the frozen
S8.4 study reads the same). The (T&B) panels are already in the slab ledger (T-152, 2F tank T&B 376.24 kg at A): not
repeated. The tank walls stay HELD as a designer item (a cast tank needs a detail; a prefabricated tank needs a note).

## 5. Held lines (nothing dropped)

| Where | Printed | Status |
|---|---|---|
| Top bars at every flight head and foot | 6ø14/m (p.16) | HELD_LENGTH (counts measured) |
| MS1-L foot at the GF hall | p.16 shows 6ø16/m into a ground beam at a foot; the hall foot is not detailed | HELD (6ø14 or 6ø16) |
| Flight bars through the GF / 1F strips | 8ø16/m vertical callouts | HELD_LENGTH (extent inside the strip not drawn) |
| GF strip west 1.30 m | over the winder turn, soffit not drawn | plan length (lower bound) |
| 1F strip | two levels +7.516 / +7.684 with a closing riser | plan length |
| MS1-U / MS2-U heads | 0.20 m inside B20 / B23 (T-111 designer clash) | main bars measured to the drawn waist; clash stays an RFI |
| Winders MS1-T | step / nosing bars | HELD (turn HELD) |
| Round stair curved flight RS-C | 8ø16/m along the curve | HELD (Q-50) |
| Corner landing RS-LD | no callout of its own | HELD_DIRECTION, candidate 18.17 .. 21.73 kg |
| Entrance E1, hall -> lobby D1 | nothing (p.3, p.4, p.16 searched) | HELD |
| Landing edge beam 20 x 40 of p.16 | not on the Alsenan plans (landings sit on B2 / B3 / walls) | not counted (no such member drawn) |
| Pool: which zone governs | two populations, one flat floor | HELD_DESIGNER (R1 / R2) |
| Water-tank walls | not drawn | HELD |

## 6. Remaining structural steel with no hand ledger yet (for the Lead; not measured this run)

Lift pit walls and slab (p.14: 6ø12/m, 6ø16/m, 2ø16, "AS PER SCH." footing FF in T-155); parapets (p.14: 5ø10/m, 6ø12/m);
domes (p.7: ø12/15cm shell mesh, ring 3ø16 / 3ø18 / ø8/m / 2ø14/20cm; dome concrete held on Q-18 / Q-27); stair beams
(p.16 TYPICAL DETAIL OF STAIR BEAM 2ø12 / 4ø16 / 6ø8/m and the scheduled 'B3 (With Stair)' beams, beam lane); lintels
(p.13 schedule); boundary wall and its ground beam (p.14); slab on grade 5ø10/m E.W. T = 10 cm (p.3).

## 7. What we learned (every villa)

1. A typical stair section is often the only stair reinforcement in a set and carries no plan reference: separate the
   bars the plans print (here the 8ø16/m main bars) from the typical-only families, and let the Lead / owner decide once
   whether a typical detail binds without a reference.
2. On a closed wall perimeter a "+1 bar at each edge" reading does not exist: Q-71's B equals A there.
3. A two-depth pool detail plus a flat-floor ruling leaves the bar population open even when every bar is labelled.
4. On this D outline (3.50 x 3.50, a half circle on a 3.50 x 1.75 rectangle) the mesh chord sums come out equal in both
   directions, so a section direction that is not marked on the plan does not move the kg; on other outlines it would,
   and the direction must then be read or held.
5. Independent re-derivation reproduces the frozen S8.7c main-bar lengths and the S8.7 A1-L1 rate density to 0.000 kg:
   the stair flight geometry of T-111 is now cross-checked by a second, independent study.

## 8. Fixture (`--check`, NON-Alsenan, hand-calculated, all PASS)

Straight flight 2.00 wide, 10 risers 0.175, 9 treads 0.28 (L = hypot(2.52, 1.75) = 3.0681): main 10ø12/m A 20 / B 21 bars,
54.544 kg; 8ø16/m over 2.00 = 16 bars (exact multiple, not 17); distribution 16; step bars 14 x 9 = 126 of 0.455 m; nosing
16.0 kg; landing strip 1.50 x 3.10: A 12 / B 13, 58.785 kg; flight-bar continuation stays HELD (None, not 0); rectangle
3.0 x 2.0 at 5/m: A 30.0 / B 33.0 / C 30.0 m, unchanged by 90-degree rotation, mirror and mm-to-m; small D (area 3.5708)
C 14.283 m; rectangular tank wall 2.40 x 2.00 x 1.80 with a 0.60 x 0.60 opening: closed loop 6/m x 8.80 = 53 bars (B = A),
93.0 m net of the 4 cut bars, hoops 9 x 8.80 = 79.2 m with one lap each; a tank with no printed bars stays HELD; zero /
negative extents and rates refused.

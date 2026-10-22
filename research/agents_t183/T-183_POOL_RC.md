# T-183 Swimming pool as reinforced concrete, component by component (Alsenan development villa; rules for every villa)

Worker 1 (structural lane S). r1 2026-10-22 11:05 UTC (8beaa6a); **r2 2026-10-22 (this revision)** after the Checker's
rejection of 12:05 UTC (D-T183-1 wall height boundary, D-T183-2 upstand). Development villa, not an accuracy claim.
Nothing is wired, nothing is released, the released default (V2.9 + route G) is unchanged. A checked piece for the V3.0
candidate (lane I) once the Checker has re-measured it. ENGINEERING_REASONING_STANDARD.md sections 2-4 and 7 applied.

Sources (Drive "Alsenan chalet project", private copies in the git-excluded folder, never committed): "ST7757.pdf"
p.7 DETAIL OF SWIMMING POOL (N.I.S.), p.8 notes 5 / 13 / 16 / 22, p.13 typical footing details; "ST7757 dxf.dxf" GROUND
BEAMS PLAN layer S-BW outlines 7C6 (outer) / 7C5 (water), S-BOUN bands, FOUNDATION PLAN footing outline 1B24 (F8);
"p7757_arch_sheet03.pdf" (GF plan: pool 350 x 350, walls 20, deck 50); "P7757 dxf.dxf" (inside P7757_DXF_COMPRESSED.zip):
GF plan pool block and the **NW elevation cut through the pool** (the 1150 dimension, re-read in r2 entity by entity).
Freelancer cells from tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (RC workbook sheet "حمام السباحة" rows 11-16).
Owner rules: Q-26 A (flat floor at the printed 1.15 m depth; 0.40 printed), Q-19, Q-22 A, UP-QTY-STATUS-001,
URBAN-REBAR-NET-AND-PROCUREMENT@v1. Code: `t183_pool_rc.py` (new, unwired; `--check`, `ledger ALSENAN_POOL_INPUT.json`),
input `ALSENAN_POOL_INPUT.json` (schema V2: levels), tests `tests/t183_pool_rc/` (23 pass).

## 0. What r2 changed and why (the Checker's two defects, re-read from the drawings, not taken from the verdict)

**NW elevation cut, P7757 dxf, own reading** (units mm, one datum; rim = +0.30 from the level marks +0.15 / +0.30):

| Drawn line (layer) | y | Level | What it is |
|---|---|---|---|
| short layer-1 caps over both walls, and the layer-5 water line across the pool | -804946.4 | **+0.30** | rim = wall top (structure) |
| layer-5 lines both sides of the pool | -805096.4 | **+0.15** | deck finish (level mark "+0.15") |
| layer-1 lines from the outer wall faces outwards | -805146.4 / -805296.4 | **+0.10 / -0.05** | deck slab structure, 0.15 thick |
| layer-5 line between the inner wall faces (the "1150" dimension ends here) | -806096.4 | **-0.85** | finished pool floor (Q-26 A depth 1.15) |
| layer-1 line between the inner wall faces, hatched shell below | -806146.4 | **-0.90** | **structure line = top of the RC base** |
| inner wall faces (layer 1) x -365956.9 / -362856.9 | -806146.4 .. -804946.4 | -0.90 .. +0.30 | **1.200 m** of structural water face |

So the printed 1.15 is the FINISHED water depth; the cut draws a 50 mm floor build-up over the structure line, and p.7
dimensions the depth "AS PER ARCH" from the rim line to the BASE TOP (no tile drawn on p.7). **RC wall height above the
base top = rim +0.30 - structure -0.90 = 1.20 m** (DRAWING-CONFIRMED). The 1.15 m stays beside it as the finished depth
(Q-26 A's text value) and governs only the visible water-face finish. The Checker's D-T183-1 is confirmed.

The cut draws the shell as one hatched mass rising to the rim, 0.15 above the deck finish on both sides (deck structure
+0.10 .. -0.05 against the wall's outer face): an **upstand** that r1 missed ("wall top = deck"). D-T183-2 is confirmed.
Its concrete is already inside rim - base top (no extra m3); its outer face above the deck is a face of its own. The GF
plan (P7757 dxf pool block) gives where the deck is: the straight back of the D lies on the 0.20 boundary-wall line pair
(two 5.17 m layer-5 lines 0.20 apart), with no deck behind it; the curved part and both 1.75 m sides face the +0.15 deck.
**Deck edge = outer perimeter 12.497787 - back 3.50 = 8.997787 m.**

Not in the Checker's verdict, found in r2: the architectural cut draws the base only 0.15 thick (-0.90 .. -1.05,
undimensioned, schematic); the structural detail prints 40. Evidence hierarchy (standard s.2.2): the structural
dimension governs the RC thickness, the architectural cut governs the levels; base underside = -0.90 - 0.40 = **-1.30**.
Recorded as a coordination note (C10), no quantity depends on the 0.15.

## 1. The physical element (section 2.1)

One open RC tank, D-shaped on plan, in the GF glazed pool room; its straight back lies on the plot-boundary wall line
(sea-view side). From the inside out (p.7):

| Layer | Printed / drawn | Where it runs |
|---|---|---|
| Water-face finish | not specified; floor build-up 50 mm drawn in the architectural cut | floor (finished -0.85), walls finished floor -> rim |
| RC wall, two curtains | 20 | all round: straight back 3.50, two sides 1.75, half circle r 1.75 (outer); base top -0.90 -> rim +0.30 = 1.20, of which 0.15 stands above the deck finish (0.20 above the deck structure) along the 8.998 m deck edge |
| RC base slab, two mats | 40 (Q-26 A: the whole floor) | the whole outer footprint, under the walls; top -0.90, underside -1.30 |
| Protection screed | "5cm SECREED." | under the base AND up the outer wall faces to the wall top (p.7) |
| Membrane | "5cm INSULATION MEMBRANE." | outside the screed, under the base and up the outer wall faces to the wall top (p.7) |
| Plain concrete (blinding) | "10cm PLAIN CONCRETE." | under the membrane; projection NOT dimensioned |

Walls sit ON the base: measured once at the junction (frozen generic `pool_qto.wall_base_split`, cross-checked in the
tests): BASE = outer footprint x 0.40 (wall foot included); WALLS = wall band x 1.20. Casting: p.8 note 5 ready-mix ->
cast-in-place; no shotcrete note.

## 2. Component ledger (A - K), own calculation from the drawing (r2)

Plan (exact): outer D = 3.50 x 1.75 + pi 1.75^2 / 2 = **10.935564 m2**, perimeter 12.497787 m (curved 5.497787); water D
= 3.10 x 1.55 + pi 1.55^2 / 2 = **8.578838 m2**, perimeter 11.069469 m (curved 4.869469); wall band **2.356726 m2**.

| Line | Calculation | Quantity r2 | r1 | Status |
|---|---|---|---|---|
| A excavation | formation = rim +0.30 - 1.20 - 0.40 - 0.05 - 0.05 - 0.10 = **-1.50**; existing ground, working space, general dig (Q-21 C) not printed | not measured | formation -1.45 | **HELD** (T-170) |
| B blinding | (10.935564 + 12.497787 x 0.10 + pi 0.10^2) x 0.10 | **>= 1.222 m3** | same | HELD for the projection (not printed) |
| C base slab (RC) | 10.935564 x 0.40 | **4.374 m3** | same | DRAWING-CONFIRMED (Checker: re-measured, agrees) |
| D walls (RC) | 2.356726 x **1.20** (rim to structure line) | **2.828 m3** | 2.710 | DRAWING-CONFIRMED |
| **RC total** | C + D | **7.202 m3** | 7.084 | |
| D' upstand (inside D) | concrete: no extra m3; outer face above the deck finish 8.997787 x 0.15 | **1.350 m2** exposed (1.800 m2 above the deck structure +0.10) | missing | DRAWING-CONFIRMED geometry; finish and membrane termination UNKNOWN (C9) |
| E steps / benches | none drawn (GF plan, NW cut, sanitary plan; p.7's floor change is the sloped profile Q-26 A set aside) | no line | same | NOT DRAWN |
| F rebar | section 3 | R1 860.97 .. 894.43 kg / R2 596.17 .. 616.66 kg (face to face) | R1 847.00 .. 885.64 / R2 586.25 .. 610.35 | **HELD** (designer: which population) |
| G formwork (cast-in-place) | outer face 12.497787 x (0.40 + 1.20) = 19.996 (curved 8.796); water face 11.069469 x 1.20 = 13.283 (curved 5.843); base on the screed (no soffit form); wall top not formed | **33.280 m2** (curved 14.640) | 32.101 | DRAWING-CONFIRMED geometry; pour sequence / kicker not printed. The deck slab is cast against the protected wall (p.7 membrane + screed run to the top), so the 0.15 deck band of the outer face is still formed |
| H joints / waterstops | none drawn or noted | - | same | UNKNOWN (consultant C2) |
| I membrane (p.7 extent) | under base 10.936 + outer walls 12.497787 x 1.60 = 19.996 | **30.932 m2** net | 30.307 | DRAWING-CONFIRMED extent; product UNKNOWN; above the deck finish the drawn membrane would be exposed: termination C9 |
| I protection screed 5 cm | under base 11.568 m2 + outer walls 19.996 m2 | **1.591 m3** | 1.559 | DRAWING-CONFIRMED (as drawn) |
| J water-face finish | floor 8.579 m2 + walls 11.069469 x **1.15** (finished floor -> rim) = 12.730 m2 | **21.309 m2** | same | areas DRAWING-CONFIRMED; material UNKNOWN |
| J structural water face | 11.069469 x 1.20 (base top -> rim) | 13.283 m2 | - | for a coating applied to the concrete before the floor build-up (none specified): information, not a finish line |
| J floor build-up 50 mm | 8.578838 x 0.05 | **0.429 m3** | missing | drawn thickness, composition UNKNOWN (lane A) |
| J wall top (coping surface) | band 2.356726 m2 | 2.357 m2 | missing | finish UNKNOWN (lane A) |
| K pump room / balance tank | not drawn in any document read | no line | same | NOT DRAWN |

Visible finish vs structure (the Checker wrote "water-face finish 1.20 not 1.15"; r2 keeps both, labelled, for this
physical reason): a wall finish starts at the finished floor; the bottom 0.05 m of the structural face is behind the
floor build-up. Finish 12.730 m2 (1.15), structural face 13.283 m2 (1.20, formwork). If the consultant specifies a
water-face coating applied to the bare concrete, that coating takes 13.283 m2.

## 3. Reinforcement by bar population (r2: every wall at 1.20 above the base top)

The two printed populations of p.7 (R1 deep end, R2 shallow end) on the flat pool of Q-26 A. kg/m = d^2 / 162 (D2_OVER_162,
the merged slab / stair ledgers' method); counts A = ceil, B = A + 1 (closed loops B = A), C = unrounded. Wall verticals
base underside -> rim = 1.60 m; hoops over the wall height above the base top only (R-POOL-6): 1.20 / 0.20 = 6 / 7 / 6.0
per face (A / B / C) (r1: 5.75 at C). Laps (12.50 m hoops > 12 m stock) and development HELD.

| Population (kg) | Face to face C / A / B | Net of the printed 7 cm soil cover C / A / B | T-166 (merged) C / A / B |
|---|---|---|---|
| R1 deep-end detail | **860.97 / 866.91 / 894.43** | 812.63 / 823.35 / 850.15 | 888.90 / 900.01 / 927.54 |
| R2 shallow-end detail | **596.17 / 597.35 / 616.66** | 563.15 / 573.23 / 592.05 | 615.34 / 620.13 / 639.45 |

Against T-166 (R1 -27.93 / -33.10 / -33.11 kg; R2 -19.17 / -22.78 / -22.79 kg): T-166 spread the hoops over base + finished
depth 0.40 + 1.15 = 1.55 m (8 / 9 / 7.75 per face) and ran the verticals 1.55 m; p.7 draws the hoops above the base top
only (inside the base the dots are the base's own mats) and the structure runs to 1.20 above the base top, so verticals
1.60 m and hoops 6 / 7 / 6. Both of T-166's readings are corrected by r2.

Which population governs (R1 for every wall of a flat 1.15 m deep pool by physical reasoning, evidence level 6) stays HELD
for the structural designer (C1). Cover: note 22's 7 cm "in contact with soil" behind the membrane is a consultant point
(C3); both bases shown.

## 4. Reconciliation (section 5 of RECONCILIATION_POOL_STAIRS_DOMES_2026-10-22.md), in m3, r2

Freelancer 12.348 -> own **7.202** (difference +5.146 m3, **+71.5 %**; r1 +5.264, +74.3 %):

| Component | Freelancer | Own | Difference | Cause |
|---|---|---|---|---|
| Floor | 10.8 x 0.40 = 4.320 | 10.936 x 0.40 = 4.374 | -0.054 | his area 10.8 m2 is typed (no formula); drawn 10.936: residual -0.136 m2 UNEXPLAINED |
| Walls | 12 x 1.8 x 0.20 = 4.320 | 11.784 x 1.20 x 0.20 = 2.828 | **+1.492** | height on his 12 m: 1.80 - 1.20 = 0.60 -> +1.440, of which 0.40 x 12 x 0.20 = **+0.960 is the base thickness counted again** (his floor already covers the outer footprint) and 0.20 x 12 x 0.20 = **+0.480 above the drawn rim** (no drawing shows wall above +0.30: his 1.80 exceeds the drawn base-underside-to-rim 1.60 by 0.20); length 12 vs centreline 11.784 at 1.20 = **+0.052** |
| Pump-room walls + floor | 1.080 + 2.400 | not drawn | +3.480 | scope not in the drawings (K) |
| Steps | 0.228 | not drawn | +0.228 | not drawn |
| **Sum** | **12.348** | **7.202** | **+5.146** | closes to 0.000 |

r1 explained the walls with "0.25 m of wall on no drawing" (+0.600); with the structural 1.20 the part on no drawing is
0.20 m (+0.480). The 0.05 m build-up difference (+0.118 m3) moved from "his excess" to "our wall".

Released engine 3.495 -> own 7.202 (difference **-3.707 m3, -51.5 %**; r1 -3.589): floor 6.045 m2 x convention 0.25 =
1.511 (-2.863: the curved half of the D lost and 0.25 vs the printed 0.40); walls 1.240 m2 x convention 1.60 = 1.984
(-0.844: band 1.240 vs 2.357, the curved half of the ring lost, -1.340; height 1.60 convention vs 1.20 drawn, +0.496).
Same cause as the Checker's D-T180-1; both released pool lines rest on unapproved conventions (Q-19) -> lane I should HOLD
them in V3.0.x and take this ledger once verified.

Verdict proposals (CONC.POOL, m3): released engine wrong (area and conventions; hand calc above); freelancer
FREELANCER_RIGHT on the floor thickness and within 1.2 % on the floor area; walls ENGINE_RIGHT for this ledger (1.20 to the
structure line; his 1.80 double counts the base and adds 0.20 above the rim); pump room and steps: not drawn (his scope
addition, RULE/SCOPE difference). Rebar: his 1.5 t lump on 12.348 m3 = RULE_DIFFERENCE (allowance per m3), no %.

## 5. Interfaces (coordination; no quantity changed)

1. Combined footing F8 (4.00 x 3.60 x 0.50, outline 1B24) overlaps the pool footprint by 1.297 m2 (1.599 m2 with its 10 cm
   blinding projection). F8's founding level is not printed; the pool formation is now **-1.50** (r1 -1.45). Designer to
   say whether F8 sits below the pool base; T-170 must not dig the same 1.297 m2 twice.
2. Boundary-wall base (B.W band) under the pool's straight back: on the FOUNDATION PLAN the closed S-BOUN band runs through
   the back wall line for 3.50 m (3.50 x 0.20 x 0.60 = 0.420 m3 possibly in both the edge strip and the pool). r2 adds: the
   architectural GF plan draws the pool back ON the 0.20 boundary-wall line pair, so the back wall IS the boundary wall
   over 3.50 m; the boundary wall above the rim is masonry for lane A, and no upstand / deck face is measured there.
3. The curved ground beam round the pool is 0.50 m clear of the pool: no shared concrete.
4. Deck slab (structure +0.10 .. -0.05, 0.15 thick) abuts the pool's outer face along 8.998 m: it is the deck's concrete,
   not the pool's (no m3 moved); the deck slab line belongs to the slab-on-grade ledger.

## 6. Consultant clarifications (designer list; nothing here for the owner, standard 2.7)

C1 which bar population (R1 / R2) governs a flat pool; C2 wall / base construction joint, waterstop, starter bars,
watertightness test, curing; C3 the membrane product and whether note 22's 7 cm soil cover applies behind it; C4 blinding
projection; C5 access to the water (none drawn); C6 F8 and the B.W band under the pool; C7 water-face finish, its build-up
(50 mm drawn) and coping; C8 openings (skimmers, inlets, main drain, lights: none drawn); **C9 (r2) membrane / screed
termination at the deck: p.7 runs them to the wall top, the architectural cut leaves the upstand 0.15 m exposed above the
deck finish along 8.998 m (1.350 m2): finish and termination detail; C10 (r2) the architectural cut draws the base 0.15
thick (undimensioned) vs 40 printed on p.7: the structural dimension governs; confirm.**

## 7. General rules (proposed; scope every villa; a new rule version if adopted, never an edit in place)

R-POOL-1 RC by component, never blockwork. R-POOL-2 walls all round, band = outer - water outline; a base without a wall
line, or walls at 0, is refused. R-POOL-3 blinding / screed / membrane separate; the RC base is the printed RC thickness.
**R-POOL-4 (r2) wall height = rim to the STRUCTURAL base top from the section's structure line; a finished depth is never a
concrete height: the drawn build-up is added, both kept labelled; finished depth alone = HELD.** R-POOL-5 pump room /
balance tank / steps only when drawn. R-POOL-6 hoops over the wall height above the base top only. R-POOL-7 casting method
from the documents, else UNKNOWN. **R-POOL-8 (r2) an upstand above the deck is wall concrete already inside rim - base
top; its outer face above the deck is its own face (formwork / finish / membrane termination), along the deck edges only.**
Provenance: T-183, Alsenan development villa; general scope pending other villas.

## 8. Regression tests (tests/t183_pool_rc, 23 pass; synthetic, NOT Alsenan)

r1 (17): rectangular 4.00 x 6.00 (mm), D pools r 2.00 / b 1.20 and r 1.00 / b 1.00: hand totals, m / cm / mm, rotation,
mirror, analytic chords, frozen `pool_qto.wall_base_split` cross-check; walls omitted / 0 / curved half lost refused;
blinding never in RC; blockwork refused; undrawn steps / pump room add nothing; formwork UNKNOWN without a documented
method; hoops over the wall height only; closed-loop verticals, soil cover.
r2 (6): **normal** - levels rim +0.45, structure -1.03, finished -0.95 -> wall 1.48 (finished depth 1.40 and build-up
0.08 kept beside it; formwork 1.48, visible finish 1.40, membrane 0.30 + 1.48); **adverse** - only the finished depth known
-> HELD, None, never 1.40 and never 0, and the r1 error reproduced (under-measure = band x build-up); finished depth +
printed build-up -> 1.48; level conflicts refused (build-up 8 vs printed 5, finished floor below the structure line,
wall_h and levels both given, finish taller than the structure); upstand along the deck edges only (16.00 m x 0.25 = 4.00
m2; flush deck -> 0 and RC unchanged); D pool in mm with levels and no deck level (no upstand line).

## 9. Lessons-register rows (proposed for ENGINEERING_REASONING_STANDARD section 7)

| 2026-10-22 | Pool walls 2.710 vs 2.828 m3 (T-183 r1) | The printed 1.15 m (rim -> FINISHED floor) taken as the RC height; the 50 mm build-up over the structure line in the same cut not read | R-POOL-4 r2: RC height = rim -> structure line; finished depth kept beside it; finished depth alone = HELD (any villa: pools, tanks, sunken slabs) | tests/t183_pool_rc r2 (normal: levels; adverse: finished depth alone / taken as height) | fixed in T-183 r2 (READY), Checker to confirm |
| 2026-10-22 | Pool upstand 0.15 m above the deck not measured (r1 "wall top = deck") | Section read for the pool only; the deck level beside it not compared with the rim | R-POOL-8: compare the wall top with every adjoining finished level; an upstand's outer face is its own face along the deck edges (any villa: pools, planters, tank kerbs) | tests/t183_pool_rc r2 (upstand along deck edges; flush deck -> 0) | fixed in T-183 r2 (READY), Checker to confirm |

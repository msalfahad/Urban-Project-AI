# T-183 Swimming pool as reinforced concrete, component by component (Alsenan development villa; rules for every villa)

Worker 1 (structural lane S), 2026-10-22, run session_016XL3Y4kCT3s2yeWR5Ba5Dr. Development villa, not an accuracy claim.
Nothing is wired, nothing is released, the released default (V2.9 + route G) is unchanged. A checked piece for the V3.0
candidate (lane I) once the Checker has re-measured it. ENGINEERING_REASONING_STANDARD.md sections 2-4 and 7 applied.

Sources (Drive "Alsenan chalet project", private copies in the git-excluded folder, never committed): "ST7757.pdf"
(sha256 74da1523...) p.7 DETAIL OF SWIMMING POOL (N.I.S.) read at 400 dpi, p.8 notes 5 / 13 / 16 / 22, p.13 typical
footing details; "ST7757 dxf.dxf" (sha256 9f9d1179...) GROUND BEAMS PLAN layer S-BW outlines 7C6 (outer) / 7C5 (water),
S-BOUN bands, FOUNDATION PLAN footing outline 1B24 (F8); "p7757_arch_sheet03.pdf" (GF plan: pool 350 x 350, walls 20,
deck 50); "Alsenan_Architectural_P7757_Pages_07-08" p.8 NW elevation (cut through the pool, "115"); "P7757 dxf.dxf"
(inside P7757_DXF_COMPRESSED.zip) text search. Freelancer cells from tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json
(RC workbook sheet "حمام السباحة" rows 11-16; FIN workbook rows 18-19).
Owner rules: Q-26 A (flat floor at the printed 1.15 m; 0.40 printed), Q-19 (Alsenan has no pool pump room; usual sizes not
approved), Q-22 A (only a space naming the pool is its pump room), UP-QTY-STATUS-001, URBAN-REBAR-NET-AND-PROCUREMENT@v1.
Code: `t183_pool_rc.py` (new, unwired; `--check` synthetic fixture, `ledger ALSENAN_POOL_INPUT.json`), input
`ALSENAN_POOL_INPUT.json` (printed values only), tests `tests/t183_pool_rc/` (17 pass).

## 1. The physical element (section 2.1)

One open RC tank, D-shaped on plan, standing in the ground floor pool court; its straight back lies on the plot-boundary
line (sea-view side). From the inside out (p.7, read at 400 dpi):

| Layer | Printed | Where it runs |
|---|---|---|
| RC wall, two curtains | 20 (both ends of the section) | all round: straight back 3.50, two sides 1.75, half circle r 1.75 (outer) |
| RC base slab, two mats | 40 (deep-end floor; Q-26 A: the whole floor) | the whole outer footprint, under the walls (the wall's outer face line runs down to the base underside; the wall verticals are L-bars whose leg runs along the base bottom; 3ø16 / 4ø16 at the inner corner) |
| Protection screed | "5cm SECREED." | under the base AND up the outer wall faces to the wall top (dotted band) |
| Membrane | "5cm INSULATION MEMBRANE." | outside the screed, under the base and up the outer wall faces to the wall top (cross-hatched band) |
| Plain concrete (blinding) | "10cm PLAIN CONCRETE." | under the membrane; drawn wider than the pool, projection NOT dimensioned |
| Water-face finish | not drawn, not specified | - |

Wall top = the rim: the NW elevation cut draws the pool walls rising to the deck surface, "115" from the rim (+0.30) to
the pool floor (-0.85); no upstand above the rim. p.7's dashed line between the wall tops is the same rim line, and its
vertical "AS PER ARCH" runs from that line to the TOP of the base: the wall height above the base top is the
architectural depth, 1.15 m (Q-26 A). Casting: p.8 note 5 "all reinforced and plain concrete is ready-mix from an approved
plant" -> cast-in-place; no shotcrete note anywhere.

Walls sit ON the base: measured once at the junction (R-POOL-1/2/3 below; the same split as the frozen generic
`engine/source/pool_qto.wall_base_split`): BASE = outer footprint x 0.40 (wall foot included); WALLS = wall band x 1.15.

## 2. Component ledger (A - K), own calculation from the drawing

Plan (exact lines and arcs; the analytic values equal the frozen S8.2 geometry to 1e-6): outer D = 3.50 x 1.75 + pi
1.75^2 / 2 = **10.935564 m2**, perimeter 3.50 + 3.50 + pi 1.75 = 12.497787 m (curved 5.497787); water D = 3.10 x 1.55 +
pi 1.55^2 / 2 = **8.578838 m2**, perimeter 11.069469 m (curved 4.869469); wall band **2.356726 m2**; wall centreline
11.783628 m (x 0.20 = 2.356726, the same band).

| Line | Calculation | Quantity | Status |
|---|---|---|---|
| A excavation | formation = underside of blinding = rim +0.30 - 1.15 - 0.40 - 0.05 - 0.05 - 0.10 = **-1.45** (every link printed, same datum as the rim); existing ground, working space and the general excavation (Q-21 C: 1.50 m minimum below the existing plot level) not printed | not measured | **HELD** (T-170 level chain) |
| B blinding (plain concrete) | at least the base footprint grown by screed + membrane 0.10: 10.935564 + 12.497787 x 0.10 + pi 0.10^2 = 12.216758 m2 x 0.10 | **>= 1.222 m3** (lower bound) | **HELD** for the projection beyond (not printed on p.7; the 10 cm printed on the p.13 FOOTING detail is not extended to the pool, standard s.3: +0.134 m3 if it were) |
| C base slab (RC) | 10.935564 x 0.40 | **4.374 m3** | DRAWING-CONFIRMED (Checker T-180: VERIFIED) |
| D walls (RC) | 2.356726 x 1.15 | **2.710 m3** | DRAWING-CONFIRMED on Q-26 A |
| **RC total** | C + D | **7.084 m3** | |
| E steps / benches / thickened edges | none drawn: GF plan pool interior shows no step or ladder; p.7's floor change belongs to the sloped profile the owner excluded (Q-26 A) | no line | NOT DRAWN (access to the water: consultant item, practice not drawing) |
| F rebar | section 3 | R1 847.00 .. 885.64 kg / R2 586.25 .. 610.35 kg (face to face) | **HELD** (designer: which population; Q-71 count reading) |
| G formwork (cast-in-place, note 5) | outer face 12.497787 x (0.40 + 1.15) = 19.372 m2 (of it curved 5.497787 x 1.55 = 8.522); water face 11.069469 x 1.15 = 12.730 m2 (curved 4.869469 x 1.15 = 5.600); base cast on the screed (no soffit form); wall tops not formed | **32.101 m2** (curved 14.121) | DRAWING-CONFIRMED geometry; pour sequence / kicker not printed |
| H construction joints / waterstops | none drawn or noted (p.7, p.8 notes 1-24) | - | **UNKNOWN**: consultant clarification (wall-base joint, waterstop type, watertightness test, curing) |
| I membrane | on the protected concrete faces: under base 10.936 + outer walls 12.497787 x 1.55 = 19.372 | **30.307 m2** net | DRAWING-CONFIRMED extent; product "5cm insulation membrane" UNKNOWN (consultant); laps / procurement not measured |
| I protection screed 5 cm | under base (to the outer face of the vertical screed) 11.568 m2 + outer walls 19.372 m2 | 1.559 m3 | DRAWING-CONFIRMED (as drawn) |
| J water-face finishes | floor 8.579 m2 + walls 11.069469 x 1.15 = 12.730 m2 | **21.309 m2** | areas DRAWING-CONFIRMED; material not specified (UNKNOWN); finish build-up not drawn (lane A) |
| K pump room / balance tank | not drawn: S-BW holds only the pool D and the lift box (2.20 x 2.20, on both plans); GF plan around the pool: deck 0.50, curved glass, master bedroom, court; no "PUMP" / pool-plant text in either DXF; owner Q-19 / Q-22 A | no line | NOT DRAWN |

Uncertainty named, not hidden: if the architectural 1.15 is a FINISHED water depth, the RC wall is taller by the water-face
build-up (not drawn); each 10 mm of build-up adds 2.356726 x 0.01 = 0.024 m3 of wall concrete. Q-26 A takes 1.15 as the
depth; carried as such.

## 3. Reinforcement by bar population (re-derived independently of T-166)

The two printed populations of p.7 (R1 deep end, R2 shallow end) on the flat pool of Q-26 A, every wall at the full 1.15 m.
New code (analytic chords of the D, not a flattened polygon); kg/m = d^2 / 162 (the D2_OVER_162 method of the merged slab /
stair ledgers); counts A = ceil, B = A + 1 (closed loops B = A), C = unrounded (owner Q-71 still open: shown side by side;
T-171's footing count rule is for footings only, standard s.3). Laps (12.50 m hoops > 12 m stock) and development HELD.

| Population (kg) | Face to face (merged basis) C / A / B | Net of the printed 7 cm soil cover (note 22) C / A / B | T-166 (merged) C / A / B |
|---|---|---|---|
| R1 deep-end detail | **847.00 / 858.12 / 885.64** | 798.98 / 814.80 / 841.60 | 888.90 / 900.01 / 927.54 |
| R2 shallow-end detail | **586.25 / 591.04 / 610.35** | 553.44 / 567.06 / 585.87 | 615.34 / 620.13 / 639.45 |

Reconciliation with T-166 (same populations, same lengths): every family agrees to 0.000 kg (wall verticals, floor chords
78.196 / 65.706 m at A, rim and corner bars) EXCEPT the wall horizontal hoops: T-166 spread them over 0.40 + 1.15 = 1.55 m
(8 / 9 / 7.75 per face); p.7 draws the hoop dots on the wall faces only ABOVE the base top, and inside the base the dots are
the base's own transverse mats (6ø14/m, 6ø12/m), which already run under the walls to the outer face. Over 1.15 m: 6 / 7 /
5.75 per face. Effect: R1 -41.90 kg (A: 167.59 -> 125.69), R2 -29.09 kg (A: 116.38 -> 87.29), every reading. A defect
in a merged ledger (two bars per face counted twice), now guarded by a test (R-POOL-6).

Cover: note 22 prints 7 cm "in concrete in contact with soil"; whether it governs faces protected by screed + membrane is a
consultant point, so both bases are shown; the water-face and wall-top cover are not printed and not deducted.

Which population governs: both are printed for one N.I.S. section that the owner flattened. Physical reasoning: in a flat
pool every wall retains the full 1.15 m of water, which in the drawn section is the deep-end condition that R1 was detailed
for; R2 was detailed for a lower wall. That supports R1 as the design intent for every wall, but it is an interpretation
(evidence level 6), not a printed fact: R1 / R2 stay HELD for the structural designer (no owner question: standard 2.7,
it is a design clarification).

## 4. Reconciliation (section 5 of RECONCILIATION_POOL_STAIRS_DOMES_2026-10-22.md), in m3

Freelancer 12.348 -> own 7.084 (difference +5.264 m3, +74.3 %):

| Component | Freelancer | Own | Difference | Cause |
|---|---|---|---|---|
| Floor | 10.8 x 0.40 = 4.320 | 10.936 x 0.40 = 4.374 | -0.054 | his area 10.8 m2 is typed, no formula; drawn 10.936 m2: residual -0.136 m2 UNEXPLAINED (not a drawn value) |
| Walls | 12 x 1.8 x 0.20 = 4.320 | 11.784 x 1.15 x 0.20 = 2.710 | +1.610 | length 12 vs centreline 11.784 = +0.050; height 1.80 vs 1.15 on 12 m = +1.560, of which 0.40 x 12 x 0.20 = **+0.960 is the base thickness counted again under the walls** (his floor already covers the outer footprint) and 0.25 x 12 x 0.20 = **+0.600 is on no drawing** (no upstand above the rim in the NW cut) |
| Pump-room walls + floor | 1.080 + 2.400 | 0 (not drawn) | +3.480 | scope not in the drawings (section 2, K) |
| Steps | 0.3 x 2 x 0.38 = 0.228 | 0 (not drawn) | +0.228 | not drawn |
| **Sum** | **12.348** | **7.084** | **+5.264** | closes to 0.000 (rounding of 7.0845) |

Released engine 3.495 -> own 7.084 (difference -3.589 m3, -50.7 %): floor 6.045 m2 x convention 0.25 = 1.511 (area -4.891
m2: the curved half of the D lost + thickness -0.15 printed 0.40) and walls 1.240 m2 x convention 1.60 = 1.984 (the
straight S-BW strip only, the curved half of the ring lost: band -1.117 m2; height 1.60 is a convention, not drawn). Same
cause as the Checker's D-T180-1 (T-180 slot, 10:15). Both released pool lines rest on two unapproved conventions
(POOL_FLOOR_THICKNESS_M, POOL_WALL_HEIGHT_M; Q-19: usual sizes not approved) and are PROVISIONAL / released in run A:
lane I (T-167 audit) should HOLD them in V3.0.x and take this ledger instead once verified.

Verdict proposals (CONC.POOL, m3): ENGINE (released) wrong on area and thickness (hand calc above); freelancer FREELANCER
_RIGHT on the floor thickness and within 1.2 % on the floor area; walls ENGINE_RIGHT for this ledger (height 1.15 Q-26 A;
his 1.80 double counts the base and adds 0.25 m not drawn); pump room and steps: not in the drawings (his scope addition,
RULE/SCOPE difference, not an omission of ours). Rebar: freelancer 1.5 t lump on 12.348 m3 (121.5 kg/m3 incl. the pump
room) = RULE_DIFFERENCE (allowance per m3), no %.

## 5. Interfaces found (coordination; no quantity changed)

1. **Combined footing F8 (4.00 x 3.60 x 0.50, footing outline 1B24) lies partly under the pool**: the FOUNDATION PLAN
   footing and the GROUND BEAMS PLAN pool outline share the same frame (axes 110588 / 149312, offset 38.724 m, y equal); the
   pool footprint overlaps F8 by **1.297 m2** (a 0.50 m strip along the pool's side: 0.875 rectangle + 0.422 under the
   curve; 1.599 m2 with F8's 10 cm blinding projection). F8's founding level is not printed (Q-21 C: at least 1.50 below
   the existing plot level); the pool's formation is -1.45. Whether F8 sits below the pool base, against it or clashes with
   it is not drawn: designer clarification; T-170 must not measure a pit for F8 and a pit for the pool over the same
   1.297 m2 twice.
2. **Boundary-wall base (B.W band) under the pool's straight wall**: on the GROUND BEAMS PLAN the S-BOUN band stops at the
   pool corners (no overlap, as S8.2 CO-02), but on the FOUNDATION PLAN the closed S-BOUN band (91.94 m centreline, T-037 /
   T-058) runs straight through the pool's back wall line for 3.50 m. If the B.W base is cast there, it and the pool base
   occupy one strip: 3.50 x 0.20 x 0.60 = 0.420 m3 possibly counted in both the edge-strip line and the pool. Lane I /
   Checker to confirm when the edge strip is integrated; designer to say where the B.W base stops.
3. The curved ground beam round the pool (layer 1 arcs, S8.2 CO-03) is 0.50 m clear of the pool: no shared concrete.

## 6. Consultant clarifications (designer list; nothing here for the owner, standard 2.7)

C1 which bar population (R1 / R2) governs a flat 1.15 m pool; C2 construction joint at the wall / base junction, waterstop
type, starter bars, watertightness test, curing; C3 the membrane product ("5cm insulation membrane") and whether note 22's
7 cm soil cover applies behind it; C4 blinding projection beyond the pool; C5 access to the water (steps or ladder: none
drawn); C6 F8 and the B.W band under the pool (section 5); C7 water-face finish and its build-up; C8 openings (skimmers,
inlets, main drain, lights: none drawn; S8.2 Q-S8.2-09).

## 7. General rules (proposed; scope every villa; a new rule version if adopted, never an edit in place)

R-POOL-1 a pool with a structural RC detail is RC by component, never blockwork. R-POOL-2 walls all round, band = outer -
water outline; a base without a wall line, or walls at 0, is refused. R-POOL-3 blinding / screed / membrane are separate
lines; the RC base is the printed RC thickness only. R-POOL-4 wall height above the base top from the documents, else HELD.
R-POOL-5 pump room, balance tank, steps only when drawn. R-POOL-6 wall hoops over the wall height above the base top only.
R-POOL-7 casting method from the documents, else UNKNOWN; formwork only for a documented cast-in-place pool.

## 8. Regression tests (tests/t183_pool_rc, 17 pass; synthetic, NOT Alsenan)

Rectangular pool 4.00 x 6.00 (mm input), D pools r 2.00 / b 1.20 and r 1.00 / b 1.00: hand totals, m / cm / mm, rotation,
mirror, analytic chords by hand, cross-check against the frozen `pool_qto.wall_base_split`. Guards with a normal and an
adverse case each: walls omitted (no wall line; walls = 0; unknown height -> None, never 0, rc total None); the curved half of
the ring lost (the released engine's reading refused); blinding never in the RC total (blinding thickness changes, RC does
not) and blinding inside the base refused; RC pool as BLOCKWORK / MASONRY refused; undrawn steps / pump room add nothing;
formwork UNKNOWN for shotcrete / no method; hoops over the wall height only; closed-loop verticals B = A, soil cover.

## 9. Lessons-register row (proposed for ENGINEERING_REASONING_STANDARD section 7)

| 2026-10-22 | Pool concrete 3.50 (engine) vs 12.348 m3 (freelancer) vs 7.084 own | Engine: straight strip only (curved half of the D lost) + unapproved conventions 0.25 / 1.60; freelancer: base thickness counted again in the wall height (+0.96), 0.25 m of wall not drawn (+0.60), an undrawn pump room (+3.48) and steps (+0.228); T-166 hoops spread over the base thickness | R-POOL-1..7 (any villa): RC by component, base owns the junction, walls = band x height above base top, build-up layers separate, only drawn scope | tests/t183_pool_rc (17) | measured; Checker to verify (T-183) |

# T-176 Block units as a procurement output (BLOCK_PROCUREMENT_V1; Q-75; Alsenan; every villa)

Worker 2, 2026-10-23. Unwired research piece: no method version, no released line changes (released stays V2.9 +
route G). Files: `block_procurement_v1.py` (pure functions, every villa), `alsenan_t176.py` (runner, `--check`),
`BLOCK_PROCUREMENT_BY_WALL.csv`, `BLOCK_PROCUREMENT_BY_TYPE.csv`, `WASTE_SENSITIVITY.csv`, `summary.json`; tests
`tests/t176_block_procurement/` (fixture villa T176-V + Alsenan ledger).

## 1. Physical element and the four separate quantities (standard s.2.1, s.3)

A block wall is units laid in courses; each unit has an ACTUAL face (w x h) and the joints (bed b, head j) fill the rest.
One unit plus its joint occupies one MODULE (w + j) x (h + b). Four quantities, never merged:

| Quantity | Unit | What it is | Source of its number |
|---|---|---|---|
| Net installed blockwork | m2 (and m3) | the wall that is built, openings out (Q-73) | MASONRY_AREA_V1 r2 (T-108 r2, MERGED 01eeafd0): read, never re-derived |
| Installed units | nr | net m2 / module area | Q-75 provisional owner rule (black), Q-60 pallet data (white) |
| Procurement units | nr | installed x (1 + cutting + breakage), whole units | named, sourced parameters only; none established -> HELD |
| Laying mortar / cement / sand | m3 / bags / m3 | the joint volume, then dry factor and mix | joint geometry; Q-53 C derivation; the mix is not established -> HELD |

## 2. Evidence (hierarchy of standard s.2.2)

1. Drawings: no Alsenan sheet prints a block product, size, joint or mortar mix (T-091 printed-notes census: every
   text, MTEXT, ATTRIB and block definition of the architectural DXF; structural notes p.8). Block TYPE comes from the
   Q-60 owner fallback where the plans are silent (as carried by T-108 r2).
2. Specification: the Kuwait MPW 1990 general specification lists section 04220 "concrete blockwork" in its table of
   contents (Drive "Engineering Sources — Urban Projects" / 01 Kuwait References); its text lies beyond what the Drive
   connector returns (the text read stops at 97,008 characters, inside section 02230; the 11.8 MB PDF is over the
   download limit). Not read, so nothing is taken from it. DATA ITEM for the Lead: page images of section 04220 (joint
   thickness, mortar mix) would let the mix and joint be set from the specification instead of HELD.
3. Owner rules: Q-75 decision 2026-10-23 14:15 (40 x 20 module, 12.5 / m2, PROVISIONAL for standard 40 x 20 face
   modules, final on the supplier's actual dimensions and joint; waste configurable and evidence-based, never a
   hardcoded 5 %; mortar independently verified against the joint geometry before VERIFIED); Q-60 A (white pallet list:
   62.5 x 25 and 60 x 20 faces, pallet counts; adhesive coverage HELD); Q-53 C (cement / sand derived from the mix: dry
   factor 1.33, cement 1,440 kg/m3, 50 kg bag, "not universal constants"; no waste without a named source); Q-45 B
   (1:4 is the mortar BEHIND WALL TILES, a different element: not borrowed for laying mortar).
4. The owner's stored takeoff notes (the "quantity-takeoff-rules" notes cited in Q-75): black solid units 39 x 19 face +
   10 mm joint; the 5 % block waste, 10 % mortar waste and 1:4 mix there are marked DEFAULT/CONFIRM by the owner
   himself, so they are NOT approved fallbacks (WORKFLOW_CONTROLS s.4) and appear only in the labelled sensitivity table.

## 3. Reconstruction from first principles

Units per m2 = 1 / ((w + j)(h + b)). Black 0.39 x 0.19 + 0.010 / 0.010 -> 1 / (0.40 x 0.20) = 12.5. White 62.5 x 25 at
joint 0 -> 6.4; 60 x 20 -> 8.333 (the thin-bed joint is not given: joint-free UPPER bound; a 2 mm bed gives 6.329 and
8.223, i.e. -1.1 % and -1.3 %).

Mortar, full (solid) bedding, per m2 of wall, two independent derivations that must agree:
- joints: bed = (1 / 0.20) courses x 1 m x 0.010 x t; head = 12.5 units x 0.19 x 0.010 x t -> 0.07375 t
- volume: t x (1 - 0.39 x 0.19 / (0.40 x 0.20)) = t x (1 - 0.0741 / 0.08) = 0.07375 t
- t 0.15 -> 0.0110625 m3/m2; t 0.20 -> 0.01475 m3/m2 (ratio 0.75 = the thickness ratio; units per m2 unchanged).
- Fixture check (test): wall 4.00 x 2.00 x 0.20 = 1.600 m3 less 100 units x 0.39 x 0.19 x 0.20 = 1.482 m3 -> 0.118 m3 =
  8.00 m2 x 0.01475.
- Edge tolerance (named, not added): a wall's end and top courses shift by at most one joint strip per edge: bound
  (L x b + H x j) x t per wall. Alsenan established black walls: 0.2817 m3 against 3.6059 m3 (7.8 %), large because 14
  of the 23 walls are under 3 m long.
- Face-shell bedding (hollow units) needs the shell width (HELD without it). Owner Q-60 / Q-75 text calls the black
  units solid: full bedding.

Cement and sand (Q-53 C derivation, only when the mix and a mortar waste are named): dry = wet x (1 + waste) x 1.33;
cement kg = dry x c / (c + s) x 1,440; bags = kg / 50; sand = dry x s / (c + s). Mix not established -> HELD.

## 4. Alsenan result (MASONRY_AREA_V1 r2 rows, 74 walls)

Black (net status of the AREA; every unit and mortar figure is ASSUMED — OWNER-APPROVED (provisional) via Q-75):

| t | net status | walls | net m2 | installed units | wet mortar m3 | cement / sand | procurement units |
|---|---|---|---|---|---|---|---|
| 0.15 | DRAWING-CONFIRMED | 10 | 103.332 | 1,291.65 | 1.1431 | HELD (mix) | HELD (cutting, breakage) |
| 0.15 | ASSUMED — OWNER-APPROVED | 7 | 79.005 | 987.56 | 0.8740 | HELD | HELD |
| 0.20 | DRAWING-CONFIRMED | 6 | 107.715 | 1,346.44 | 1.5888 | HELD | HELD |
| 0.15 / 0.20 | HELD (net) | 13 / 10 | HELD | HELD | HELD | HELD | HELD |
| total established | | 23 | 290.052 | 3,625.65 | 3.6059 (+- 0.2817 edge tolerance) | HELD | HELD |

White (installed units per supplier face, joint-free upper bound; adhesive coverage HELD per Q-60): 0.20 m on 7 walls,
47.358 m2 established (41.768 DC + 5.590 AOA): 62.5 x 25 -> 303.09 units; 60 x 20 -> 394.65 units (both reported,
neither chosen: no drawing names the face). Same figures as MASONRY_AREA_V1 r2 (64.317 + 101.331 + 137.448 = 303.096 by
floor, rounding). 0.15 white (2F, 1 wall) and 18 white 0.20 walls: net HELD.

Reconciliation of the owner's 563 m2 question (Q-75 decision, in units, black only):
- 563.29 m2 = T-143 hand GROSS (0.15: 350.71 + 0.20: 212.58), openings not deducted, T-stems to the through-wall centreline.
- -> 554.49 m2 = MASONRY_AREA_V1 r2 gross (0.15: 342.916, 0.20: 211.574): T-stems stop on the face (T-108 r2, -8.80 m2).
- 554.49 = 290.05 net established + 17.16 openings deducted on those 23 walls + 247.28 gross of the 23 walls whose NET is
  HELD (their 18.92 m2 of established openings are inside the 36.08 total). Closes to 0.001 m2.
- Units: Q-75 option A's "about 7,040" (563 x 12.5, gross) is replaced by 3,625.65 installed on the established net;
  the 247.28 m2 of held-net walls carry NO unit figure (HELD, not 0).
- Duplicated segments: none left in r2 (overlap 0 by construction, T-108 r2 / T-125 physical module).

Thickness census (owner request: 100 / 150 / 200 by type):
- MASONRY_AREA_V1 rows: t 0.15 (370.908 m2 gross), 0.20 (574.286), one 0.40 band (GF-H01, HELD, 0 m2 known); no 0.10.
- Own independent read of the architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, P7757.dxf;
  drawing units mm): parallel line pairs (angle <= 0.003 rad, overlap >= 0.30 m) on the wall-role layer "1" inside the
  three plan frames (x -255,000 .. -120,000): 150 mm 84.9 m, 200 mm 183.3 m, 400 mm 1.4 m, 250 mm 0, 90-110 mm 0.
  100 mm pairs on layer "1" exist only on the two elevation sheets (x below -255,000: NORTH WEST / SOUTH EAST ELEVATION
  titles), which are not walls in plan. Layer "5" (not a wall-role layer) has 31.0 m of 100 mm pairs inside the plan
  frames, handles 151/47F, 228/22A, 22A/22B, 370/371, A8E/A90, B26/B28, B28/B41, B2C/B2E, B2E/B37, B98/B9A, B9A/B9B,
  12B0/12B2, 12B2/12B3, 1357/1359 (repeated at the three plan origins): element not typed here; listed for the Checker
  as UNKNOWN, not blockwork by layer role. Result: 100 mm blockwork NONE FOUND on the wall layer.
- D-12 (ST p.8 note 20, walls containing columns at the column thickness): 20 wall rows flagged (17 engine pieces,
  D12_CONFLICT_RUNS.csv), 6 of them with an established net (GF-W01, GF-W05, GF-W28, 1F-W02, 1F-W08, 1F-W23). Units
  per m2 do not change with thickness, but a 0.25 m wall is not a black product (15 / 20 only): if the designer
  confirms 0.25, those rows' units, product and mortar change (mortar x 0.25 / t). Never chosen here.

Cutting evidence (course grid, every partial unit counted whole, no offcut reuse; an UPPER bound, not an order):
black 0.15 +10.8 %, black 0.20 +4.4 %, white 0.20 +23-25 % (short pier walls) on the established walls; per wall from
+2.3 % (GF-W19, 2.00 m) to +29 % (GF-W31 / W33, 1.26-1.28 m). The cut loss scales with wall ends per m2, not a flat
percentage: a single project-wide waste % misstates both short and long walls.

Sensitivity (WASTE_SENSITIVITY.csv, NOT RELEASED, each value named with its source): black ordered at cutting 3 / 5 / 8 %
= 2,348 / 2,394 / 2,462 (0.15) and 1,387 / 1,414 / 1,455 (0.20).

## 5. Statuses and what stays HELD

- Net m2: as T-108 r2 (DC / AOA / HELD). Installed units and wet mortar: ASSUMED — OWNER-APPROVED (provisional Q-75 rule)
  at best; never VERIFIED until the supplier's actual dimensions and joint are on record and the Checker re-derives the
  mortar from the joint geometry (owner 2026-10-23).
- HELD: procurement units (no approved cutting / breakage allowance), mortar waste, cement and sand (laying-mortar mix
  printed nowhere, no owner answer; Q-45 B's 1:4 belongs to the mortar behind tiles), white adhesive (Q-60), white
  pallets (follow the procurement count), all units and mortar on the 23 black and 19 white walls whose net is HELD,
  the two untyped rows (GF 0.20 '-', GF-H01 0.40).
- Freelancer: his workbook prices blockwork in m2 (compared by T-108 r2 per section); it carries no unit, mortar or
  cement count, so there is no unit-level verdict to propose. Verdict proposal for the Q-75 figure: RULE_DIFFERENCE
  resolved by the owner (provisional rule) + ENGINE_RIGHT on the basis: units on the NET (Q-73), not the gross.

## 6. For the Checker (re-measure)

- Mortar per m2 from the joint geometry (0.0110625 / 0.01475) by your own derivation; the established-net sums
  182.337 / 107.715 m2 from T108_BY_WALL.csv (rows with net_status DC / AOA, block_type BLACK).
- The 100 mm census on P7757.dxf layer "1" inside the plan frames, and the type of the layer "5" 100 mm pairs.
- GF-W31 grid: 1.279 x 4.265 -> ceil(3.1975) 4 x ceil(21.325) 22 = 88 vs 68.16 installed.

## 7. Proposed lessons-register row (standard s.7)

| 2026-10-23 | Q-75 recommended '563 x 12.5 = 7,040 black blocks' | Units taken on the GROSS area (openings in, T-stems to the centreline) and a flat waste % offered as the procurement step | Units = NET installed m2 / module (actual face + joint); procurement = installed x (1 + named, sourced cutting + breakage), HELD without them; cutting evidence from the course grid (wall ends per m2), never a flat %; mortar = joint geometry (t x (1 - face / module)), cement and sand only from a named mix (every villa) | tests/t176_block_procurement (exact division, wall with an opening, white vs black, waste change, mortar 15 vs 20; adverse: 5 typed for 0.05, unsourced parameter, mm inputs, held net, 0.25 thickness) | proposed (T-176) |

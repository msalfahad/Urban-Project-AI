# T-076 Membrane fold V2: the owner's strip method on real room outlines

Worker 1, 2026-10-19 (run 20:21 - 21:10 UTC). Branch `agents/task-T-076` from working head cb7407a. Python 3.11 venv
from requirements.txt. Development villa (Alsenan), NOT an accuracy claim. Areas, lengths, counts and engine room ids
only: no coordinates, no client data. Drawing: Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf,
sha256 ab54dd55...31cc4 (same file as T-010 / T-071 / T-074).

## What was built (opt-in, not wired; no released method or quantity changed; freeze check 0)

- `engine/source/membrane_fold_v2.py` (new, METHOD_ID `MEMBRANE_FOLD_V2`), beside the frozen
  `wp_install.continuous_fold` (V2.6), which computes the owner's method only for a 4-point axis-parallel rectangle with
  doorways exactly 0.20 m deep and so ran on none of the 14 Alsenan wet areas:
  - repeated and collinear ring points removed (1 mm); the room's own frame from its longest wall (any rotation, mirror,
    drawing units via `unit_m`);
  - the owner's Q-30 strips: first strip W - h of floor, next W - lap, last cut to remaining + lap + h; strip length =
    floor it covers + 0.20 + 0.20 whatever sits in the wall (Q-35 C); a band whose floor falls apart (U shape, an
    opening in a roof) gives one strip per piece; strips longer than a roll are spliced with the 0.10 m end lap;
  - both strip directions always, each laid from the frame's lower wall AND from the opposite wall (shown, not
    selected); a room with walls in more than one frame (45 degree walls) also shows its other wall frames;
  - a coverage check: the floor plus an h-wide flap on every edge must lie inside the strips' sheets; the bare part is
    reported in m2 (UPTURN_SHORTFALL: slanted walls, never 0, never patched by an assumed piece); internal corners are
    counted (corner pieces by detail, outside the owner's method); the faces of a column / opening inside the area
    report what the strips can fold up and what needs its own pieces;
  - rolls if alone = the strip pieces packed into whole 10 m rolls by length (UP-WP-001: never area / roll area); the
    owner's own count ceil(cut / 10 m2) is shown beside it and a difference is flagged;
  - the BOQ lines per area (Q-35 C, Q-37 A): upturn on the walls only (WALL + COLUMN + WINDOW_THRESHOLD), one doorway
    transition per door (a door between two wet rooms once, by opening id), open edges / passages / floor-level
    glazing as threshold lines; untyped edges make the upturn HELD (None), never 0;
  - `project()`: per-area rows, per-floor and project figures only as sums of the areas, held rows beside, rolls to buy
    packed for three direction sets (all along the longest wall, all across, each room on its shorter roll length):
    all three shown, none selected.
- `tests/t076_membrane_fold/` (22 tests, all pass): owner's kitchen every number, the 3 x 3 picture, rotated 37 / 45 /
  90 deg, mirrored, mm, collinear + repeated + closing points, L shape, U shape (band split, other start wall), slanted
  wall shortfall, strip longer than a roll, narrow room, column inside, roof with a skylight opening, pantry open
  side, typed roles / glazing / slivers / doors without id, untyped edges HELD, bad outlines HELD, project (shared door
  once, direction sets, duplicate refused). The roof-opening case caught a hand error (the full strip beyond the
  opening laps back only 0.10 m into it): the hand docstring was re-derived (0.32 m2 own pieces), the code was right.
- `research/agents_t076/alsenan_fold_run.py` (wet areas + pantry vs the T-074 hand table) and
  `research/agents_t076/alsenan_roof_fold.py` (the three T-071 roofs): read-only runs, nothing written into the repo.

## Alsenan wet areas: engine vs the T-074 hand table, room by room (17 wet areas, cut m2 of membrane)

Outline points before -> after cleaning; frame = angle of the longest wall; rolls = rolls if done alone by roll length
[by cut area].

| Floor | Area (T-074 name) | Points | Frame | Shape | Floor m2 engine / hand | Along longest wall | Hand | Across | Hand | Walls-only upturn lm | Doors / thresholds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GF | KITCHEN | 20 -> 12 | 90 | orthogonal | 9.6300 / 9.63 | 4 strips, 14.560 m2, 2 [2] | 14.56 equal | 6 strips, 15.070 m2, 2 [2] | 15.07 equal | 13.50 | OP-025 |
| GF | Wash (core lobby, 2 basins) | 18 -> 6 | 45 | 45 deg walls | 4.7307 / 4.7321 | 3 strips, 9.548 m2, 2 [1] | 8.737 (hand used the 0 deg wall frame: engine 8.734 there) | 5 strips, 8.704 m2, 1 [1] | 9.133 (0 deg frame: engine 9.131) | 6.64 | OP-017, OP-018; open edge 1.26 |
| GF | BATH (master bed room) | 13 -> 5 | 0 | one 45 deg wall | 3.7177 / 3.7173 | 3, 6.318, 1 [1] | 6.317 equal | 3, 6.298, 1 [1] | 6.298 equal | 6.82 | door, no id |
| GF | W.C. (by the dewaneya) | 6 -> 4 | 90 | rectangle | 3.3750 / 3.375 | 2, 5.300, 1 [1] | equal | 3, 5.415, 1 [1] | equal | 6.70 | door, no id |
| GF | WASH (by the dewaneya) | 10 -> 6 | 90 | orthogonal | 3.1325 / 3.1325 | 2, 5.000, 1 [1] | equal | 3, 5.130, 1 [1] | equal | 5.40 | door, no id; passage 1.00 |
| GF | W.C. (core, 289 x 167) | 9 -> 4 | 90 | wedge | 2.6752 / 2.6752 | 3, 6.160, 1 [1] | 6.158 equal | 4, 5.700, 1 [1] | 5.699 equal | 6.61 | OP-017 |
| GF | W.C. (core, 245 x 167) | 13 -> 6 | 135 | wedge, at 45 deg | 2.3676 / 2.3676 | 3, 5.454, 1 [1] | 5.453 equal | 3, 5.019, 1 [1] | 5.019 equal | 6.01 | OP-018 |
| GF | W.C. (stair core) | 14 -> 4 | 90 | rectangle | 2.3625 / 2.3625 | 2, 3.978, 1 [1] | equal | 3, 4.112, 1 [1] | equal | 5.40 | door, no id |
| GF | W.C. (driver) | 6 -> 4 | 0 | rectangle | 1.9500 / 1.95 | 2, 3.420, 1 [1] | equal | 2, 3.400, 1 [1] | equal | 4.80 | OP-026 |
| GF | basin space by the stair | 7 -> 4 | 0 | rectangle | 1.4850 / 1.485 | 2, 2.800, 1 [1] | equal | 2, 2.775, 1 [1] | equal | 3.20 | door, no id; passage 0.90 |
| 1F | LAUNDRY | 24 -> 10 | 90 | orthogonal | 10.1510 / 10.151 | 5, 16.568, **3** [2] | 16.581 = engine from the other wall | 6, 15.705, 2 [2] | 15.748 = engine from the other wall | 15.24 | OP-008, OP-010 |
| 1F | BATH (west, upper) | 10 -> 4 | 90 | rectangle | 5.0225 / 5.0225 | 3, 7.553, 1 [1] | equal | 4, 7.718, 1 [1] | equal | 8.20 | door, no id |
| 1F | BATH (west, lower) | 11 -> 4 | 90 | rectangle | 5.0225 / 5.0225 | 3, 7.553, 1 [1] | equal | 4, 7.718, 1 [1] | **7.41 (hand slip)** | 8.20 | OP-004 |
| 1F | BATH (east, 210 x 225) | 13 -> 4 | 0 | rectangle | 4.7250 / 4.725 | 3, 7.155, 1 [1] | equal | 3, 7.125, 1 [1] | equal | 7.40 | OP-018; floor glazing 0.50 |
| 1F | BATH (by the laundry) | 12 -> 6 | 0 | orthogonal | 3.5775 / 3.5775 | 3, 5.760, 1 [1] | equal | 3, 5.720, 1 [1] | 5.69 = engine from the other wall | 6.80 | OP-019 |
| 1F | W.C. (by the laundry) | 10 -> 4 | 90 | rectangle | 2.6460 / 2.646 | 2, 4.334, 1 [1] | equal | 3, 4.488, 1 [1] | equal | 5.74 | OP-010 |
| 2F | W.C. (roof floor) | 12 -> 4 | 90 | rectangle | 5.5500 / 5.55 | 3, 8.330, **2** [1] | equal | 4, 8.325, 1 [1] | equal | 8.90 | OP-006 |

Result: the fold is computed for all 17 wet areas (V2.6: 0 of 14), including the 9 rectangles and the 2 rooms drawn at
45 degrees. 33 of the 34 hand layouts (17 rooms x 2 directions) are reproduced to 0.005 m2 by one of the engine's
reported layouts (28 as laid, 3 from the other start wall, 2 lobby layouts in the lobby's 0 deg wall frame); the one
difference is a T-074 slip (1F west lower bath across: the last 0.15 m strip is the 2.05 m wall + 0.40 = 2.45 m long,
the hand table wrote 0.40 m; its twin room has 2.45 m): ENGINE_RIGHT, +0.31 m2. Upturn shortfall of the straight
strip ends on the slanted walls: 0.003 - 0.007 m2 per wedge room (reported, held for a detail, never 0).

Roll counts: by strip length the laundry along its long wall needs 3 rolls (pieces 5.40, 3.45, 3.40, 3.40, 3.40 m: no
two rolls of 10 m hold them), the hand table's "2 by length" was the total 19.05 m / 10 rounded up: ENGINE_RIGHT
(whole strips). The 2F W.C. along its long wall (3 x 3.40 m = 10.20 m) needs 2 rolls, 1 by cut area: flagged
ROLL_COUNT_BASES_DIFFER, the registry rule UP-WP-001 counts from the cutting plan.

The pantry (Q-37 A; no outline in the plan: the V2.9 run merges it into the 126.9 m2 open dining plan): from its
printed size, re-read this run on the DXF (dimensions 4500 at 0.30 m and 3000 at 1.73 m from the PANTRY label): floor
13.50 m2; walls-only upturn 10.50 lm (2.10 m2); threshold line 4.50 m (open dining side); strips along the 4.50 m wall
4 x 4.90 m (1.0, 1.0, 1.0, 0.7) = 18.13 m2, 2 rolls; across 6 x 3.40 m (last 0.40) = 18.36 m2, 3 rolls by length
(2 by area).

## Project figures (sums of the areas; Q-35 answer)

| Quantity | Engine (fold V2) | Hand T-074 | Freelancer | Engine vs freelancer |
|---|---|---|---|---|
| Wet floor, 17 areas | 72.12 m2 | 72.12 m2 | 72.01 m2 | +0.11 m2 (+0.16 %) |
| Upturn line, walls only (Q-35 C) | 125.57 lm = 25.11 m2 | 127.07 lm | 144.61 lm (full boundary) | -19.04 lm (-13.2 %): RULE_DIFFERENCE (Q-35 C: doorways, openings and floor glazing are not wall upturns) |
| Doorway transition lines (one per door) | 10 by opening id (3 between two wet rooms) + 6 door edges without an id (4.79 m), held: 14 - 16 | 14 doors | none (in his lm) | - |
| Threshold lines | 3.66 m (open edge 1.26, passages 1.00 + 0.90, floor glazing 0.50) | 2.16 m | none | - |
| Pantry (Q-37 A) | 13.50 m2, 10.50 lm walls, 4.50 m threshold | 13.50 m2 (printed) | none | not in his BOQ |
| Membrane cut, 17 wet areas | 117.05 - 119.79 m2 by direction set | 116.95 - 118.99 m2 | not given | - |
| Rolls to buy, 17 wet areas | 13 (each room on its shorter roll length) / 14 (all across) / 15 (all along, lower bound 14, search not proven) | 12 - 19 (bounds) | not given | - |
| Rolls to buy, with the pantry | 15 / 16 / 17 (lower bound 16) | - | - | - |
| Same 14 areas as the V2.9 separate-upstand plan | 12 / 12 / 13 rolls, cut 100.57 - 102.44 m2 | - | - | V2.9 separate upstand: 13 rolls, 105.22 m2 installed, 119.54 m2 cut |

Upturn reconciliation (walls only): 125.573 lm (engine) = 110.327 lm on the 14 V2.9 waterproofing areas (equal to the
V2.9 schedule's own typed ring, 110.327) + 15.246 lm on the three basin-only spaces. Against T-074's 127.07: -1.50 lm =
the dewaneya wash's 1.00 m opening OP-027 (engine: a PASSAGE with masonry jambs and a "D2" mark but no door leaf; the
hand table listed only its 0.80 m door and counted the 1.00 m as wall) + the 1F east bath's 0.50 m floor-level glazing
(UP-WP-003: a threshold by detail, not a wall upturn) + a 0.005 m sliver. Verdicts: the 1.00 m opening is not a wall
(ENGINE_RIGHT on excluding it); whether it is a door (transition) or an open passage (threshold) is UNRESOLVED (no leaf
drawn); the 0.50 m glazing RULE_DIFFERENCE under UP-WP-003. Window frames on a recognised window face count as the
sill (V2.9 typing): 0.60 m per bath window, upturned.

## Roofs (owner Q-24 like a bathroom; T-071 outlines inside the parapet; Q-29 skylight openings)

| Roof (T-071) | Floor m2 | Boundary lm | Along longest wall | Across | Bare upturn (slanted edges) | Skylight faces |
|---|---|---|---|---|---|---|
| 2F level roof, 2 skylight openings | 115.83 | 92.92 (incl. 2 rings) | 24 strips, 152.61 m2, 17 rolls [16]; other wall 156.17 m2, 18 | 30 strips, 160.08 m2, 18 [17]; other wall 158.41, 18 | 0.84 m2 along, 0 across | 5.56 m2 needed, 5.24 - 5.25 from the strips, 0.31 m2 own pieces |
| 1F south-east roof strip | 32.72 | 52.94 | 9, 50.13 m2, 6 [6]; other wall 62.50 m2, 8 | 22, 51.81 m2, 7 [6]; other wall 48.90, 6 | 0 | - |
| 1F west roof (curved edge) | 55.56 | 35.73 | 8, 73.50 m2, 8 [8]; other wall 70.44, 8 | 14, 70.17 m2, 9 [8]; other wall 72.38, 10 | 0.009 m2 | - |
| Three roofs | 204.11 | 181.59 | rolls to buy 29 (all along), 32 (all across, lower bound 30), 30 (shorter roll length each) | | | |

The roofs are their own membrane system (never added to the wet-area rolls). Against the freelancer's roof membrane
285 m2 / 194 lm: unchanged UNRESOLVED (T-071), the 2F top roof (+13.90) is on no plan sheet (owner Q-34). The roof strip
layouts have no hand table yet (T-074 did not rebuild the roof outlines): the verifier can check one by hand from the
T-071 outline.

## Who is right (proposals for the verifier)

- Fold strips per room: ENGINE_RIGHT where it differs from T-074 (1F west lower bath across, +0.31 m2: hand slip),
  otherwise equal (33 / 34).
- Rolls if alone by length vs the hand table's ceil(length / 10): ENGINE_RIGHT (laundry: 3 rolls, a strip is not cut
  across two rolls).
- Walls-only upturn vs freelancer full boundary: RULE_DIFFERENCE (owner Q-35 C), -19.04 lm.
- Upturn vs T-074: 1.00 m opening ENGINE_RIGHT (not a wall), its door / passage type UNRESOLVED; 0.50 m floor glazing
  RULE_DIFFERENCE (UP-WP-003).

## What we learned

1. The owner's method computes on every real Alsenan wet outline once collinear points go (6 - 24 points -> 4 - 12) and
   the room's own frame is used; no doorway depth question remains under Q-35 C (strips 0.20 m past every edge).
2. The start wall matters as much as the direction: kitchen 14.56 vs 15.16 m2, 1F south-east roof 50.13 m2 / 6 rolls vs
   62.50 m2 / 8 rolls. No Urban rule fixes it; both are shown, the cutting plan or the owner chooses.
3. Rolls by area understate whole strips: 2F W.C. (10.20 m of strips, 8.33 m2) and the laundry.
4. Slanted walls leave a measurable bare strip of upturn under the straight-end method (0.003 - 0.84 m2 per area):
   reported, never 0; a detail (or a wider strip end) decides.

## Missing / not done

- Not wired: the membrane purchase table (T-072) still reads the V2.6 fold; wiring both into a released method version
  is T-079.
- 6 door edges carry no opening id in the V2.9 opening census (two of them are the T-074 pairs between two wet rooms):
  the transition count stays 14 - 16, held.
- The dewaneya wash opening OP-027 (door or open passage) and the 2F top roof (Q-34) stay UNRESOLVED; shower tanking
  above 0.20 m (Q-40) and screeds (Q-41) stay HELD (not in this piece).
- Packing proof: the "all along" sets (wet 15 rolls, lower bound 14; roofs across 32, lower bound 30) hit the search
  limit: the true minimum may be one or two rolls lower.

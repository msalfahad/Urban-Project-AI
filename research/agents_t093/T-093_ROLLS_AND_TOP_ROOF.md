# T-093 ARCH_TAKEOFF_V2.11 rework: rolls per area alone (owner Q-49 A) and a held line for the roof no plan draws

Worker 1, 2026-10-20 (branch `agents/task-T-093` from working head 2fb9553 + the three T-079 commits cherry-picked).
Python 3.11 venv from requirements.txt. Development villa (Alsenan), NOT an accuracy claim. Areas, lengths, counts and
engine room ids only. Drawing: Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256
ab54dd55...31cc4 (same file as T-010 / T-071 / T-074 / T-076 / T-079).

## What changed against T-079 (the verifier's two faults, nothing else)

- (a) ROLLS. `engine/source/arch_v211.py`: `layouts()` (the four layouts MEMBRANE_FOLD_V2 computes: two strip
  directions x two start walls), `purchase()` (owner Q-49 A: the fewest whole 1 x 10 m rolls; tie the shorter total
  strip length, then the smaller cut m2, then the listed order; cutting plan re-packed from the chosen strips and
  checked against the fold's own count; leftover metres; side trim; an uncovered upturn of the chosen layout is shown
  with a check that the area's own leftover holds that much sheet), `membrane_table()` (per system the purchase of each
  area alone, `purchase_total` = sum of the areas, held areas listed; MEMBRANE_FOLD_V2.project kept as information
  only), `rolls_lines()` (one FIN.WP.MEMBRANE_ROLLS line per wet area and per roof, SOURCE_DERIVED; one BLOCKED_RFI
  line per held area), `purchase_rows()` + `tools/urban_boq_m9.py` writes `MEMBRANE_PURCHASE_V2_11.csv` (the owner's
  table: per area layout, strips, cutting plan, rolls, strip metres, leftover, side trim; per system the total). No
  text cites "Q-49 open" any more.
- (b) SILENT ROOF. `top_roofs()` / `top_roof_lines()`: the uppermost storey plan (by bound level, else by the
  floor-title order of arch_plan.FLOOR_TITLES; a tie or an unplaceable plan claims nothing) that has labelled rooms has
  no plan drawn above it, so its roof is on no plan: FIN.WP.ROOF (m2), FIN.WP.ROOF_UPTURN (lm) and
  FIN.WP.MEMBRANE_ROLLS (pcs) BLOCKED_RFI, reason ROOF_NOT_DRAWN_ON_ANY_PLAN (UP-WP-ROOF-001, owner Q-34 parked), no
  number, never 0; the storey plate is in the inputs for information only. A roof plan with no rooms on top draws its
  own roofs: no held line.
- (c) Registry 1.7.0 rebuilt by `tools/kb_build_1_7.py` (still 1.5.0 + the owner answers; 1.8.0 untouched):
  UP-WP-LAY-001 records Q-49 A, UP-WP-ROOF-001 the held top-roof line; code / test links updated.

## Alsenan: engine (V2.11 r2) against the hand table and the freelancer

Line by line against V2.10: 0 V2.10 lines changed quantity or state (same 2 V2.10 held doorway exposures gone as in
T-079). Against the T-079 run: the 2 held range lines replaced by 20 released rolls lines; 4 held lines added (top roof
m2 / lm / rolls, pantry rolls). Release report 578 lines, every line once.

| Quantity | Engine | Hand truth | Freelancer | Verdict proposal |
|---|---|---|---|---|
| Rolls to buy, 17 wet areas each alone | 19 rolls released (15 x 1, kitchen 2, laundry 2) | 19 (ALSENAN_MEMBRANE_PER_WET_ROOM.csv) | not given | equal; per room every count equal |
| Wet strip metres / leftover | 122.99 m of strips, 67.01 m left over, cut 116.11 m2 | 125.27 m, 64.73 m, 117.09 m2 | not given | ENGINE_RIGHT: 4 rooms (kitchen -1.30 m, core wash lobby -0.54 m, master bath -0.40 m, core W.C. -0.03 m) take a shorter layout from the opposite start wall, which the hand table did not try (one start wall per direction); same roll counts |
| Pantry (open to dining) rolls | HELD (WET_ZONE_EXTENT_NOT_DRAWN; Q-37 A needs the printed 4.50 x 3.00 as project data) | 2 (from the printed size) | - | held with its reason, never 0 |
| Rolls to buy, roofs each alone | 31 released: 2F level roof 17, 1F south-east 6, 1F west 8 | 17 + 6 + 8 = 31 (Lead, from the fold) | not given | equal |
| 2F top roof (+13.90) | HELD lines FIN.WP.ROOF, FIN.WP.ROOF_UPTURN, FIN.WP.MEMBRANE_ROLLS (Q-34) | no plan draws it | inside his 285.00 m2 | UNRESOLVED (owner Q-34 parked) |
| Roof membrane / upturn released | 204.11 m2 / 181.59 lm (unchanged) | - | 285.00 m2 / 194.00 lm | -80.89 m2 (-28.4 %) / -12.41 lm (-6.4 %), now with the held top roof visible beside it |

Kitchen check by hand (the largest change in strip length): the engine's room is an L, 2.70 x 3.00 m on a 1.05 x 1.50
m leg (9.63 m2 with the pilaster notches). Across the 4.50 m span from the top wall: 6 bands, four strips over the wide
part 2.70 + 0.40 = 3.10 m, two over the leg 1.05 + 0.40 = 1.45 m (the last 0.40 wide): 15.30 m, cut 14.43 m2, rolls
3 x 3.10 and 3.10 + 1.45 + 1.45 = 2 rolls, 4.70 m left. The hand table laid it along the long wall: 16.60 m, 2 rolls,
3.40 m left. Same purchase, 1.30 m less cut: ENGINE_RIGHT.

Flags shown, not hidden: the chosen layout of 4 small wet rooms (34 - 103 cm2) and of two roofs (2F level roof
0.84 m2, 1F west 0.01 m2) leaves a little upturn on slanted walls unreached; each area's own leftover holds that much
sheet (2F level roof: 11.91 m2 of leftover), so no roll count changes; patches are by detail. The 2F level roof's
fully covering layouts need 18 rolls. The 1F south-east roof's packing is not proven minimal by the branch and bound
(6 rolls is a cutting plan that exists; 5 is not excluded by the lower bound).

## Tests (tests/t079_arch_v211, 20 cases; hand truth in the module text; not Alsenan)

Villa (HAND WASH space): rolls per area 1 / 3 / 1 = 5, kitchen across 8 strips cut as 3 + 3 + 2, leftover 0.40 + 4.40
+ 0.40 = 5.20 m; the 1F top plan's roof held (3 lines, release report HELD). Owner kitchen 3 x 4 along, 2 rolls,
17.60 m, 2.40 m left, cutting plan 4.40 + 4.40 twice; owner bath 3 x 3, 2 rolls; total 4 rolls, 8.80 m left; a held
pantry gives a held rolls line and an incomplete total. L-shaped room: all four layouts 2 rolls, 15.30 m chosen, same
for mirror, quarter turn and millimetres. Roof 39.19 m2 with a skylight: 7 rolls, 55.63 m of strips, 14.37 m left
(hand: seven 5.80 m strips, no roll takes two), in mm / metres / 30 degrees / mirrored; its block's own roof held
(GF top plan with a BEDROOM). Roof plan with no rooms: no held top roof. top_roofs: level order, title order, roof
plan without / with rooms (annex), tie and unplaceable plan claim nothing.

## Learned / missing

- The hand table's one-start-wall layouts miss shorter cuts on L-shaped and slanted rooms; the four-layout search
  finds them without changing a count (4 of 17 wet areas, 2.28 m of strip).
- A plan sheet title "ROOF PLAN" is read as a ROOF label by EXTERIOR_SPACES_V1 (a held roof row with no closing layer):
  pre-existing, not changed here; worth a follow-up (title text excluded from labels).
- Missing: the pantry needs its printed size as project data (Q-37 A / T-064); the 2F top roof waits on owner Q-34;
  the top-roof rule checks only the uppermost plan (a lower storey partly uncovered by the plan above is not checked).

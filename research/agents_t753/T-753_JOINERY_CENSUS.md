# T-753: B13-06 JOINERY census (kitchen / pantry runs, vanity counters, built-in cupboards)

Method `JOINERY_CENSUS_T753_V1` (`research/agents_t753/t753_joinery.py`), development-villa run
`research/agents_t753/t753_alsenan.py` on Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (architectural DXF,
mm), cross-checked on p7757_arch_sheet03 (GF) and p7757_arch_sheet04 (1F). Research only: nothing wired, no candidate
line changed, no engine file edited. Room ids are the ARCH_TAKEOFF_V2.9 spaces (`t743_arch_dump.py`).

## 1. Physical element and measure

| Kind | Physical element | Measure (own unit) | Typed by |
|---|---|---|---|
| BASE_RUN | base cabinets / counter under a worktop (kitchen, pantry, bar peninsula) | front edge lm; worktop plan m2; inside corner counted once | a counter outline on the fixture layer 0.30 .. 0.90 m off a wall face or an open edge |
| VANITY_COUNTER | counter holding basins | front edge lm; plan m2; basins excluded by id (B12-01, T-743) | a counter outline that contains WASH2 basin blocks |
| BUILT_IN_CUPBOARD | wardrobe / cupboard fixed to a wall | front lm, pcs; front face m2 = lm x PRINTED height (HELD if unprinted) | the plan symbol front line + one corner-to-corner diagonal on a box whose back is a wall face |

Never a unit: a text-only block (23 such blocks on this plan, among them 'kit', 'PAN', 'WASH', 'WC', 'bath', 'laun':
labels), the lift car symbol (closed box + diagonal, 1.63 x 1.47 m, stacked on GF / 1F / 2F), loose furniture (two bar
stools 174/175, 176/177 beyond the peninsula), stair / void / threshold / step linework.

## 2. Census (DRAWING-CONFIRMED = CAD-drawn geometry; no unit dimension is printed as text)

| Unit | Floor / room | Kind | Front (handles) | Front lm | Depth m | Plan m2 | Corners | Other trades excluded |
|---|---|---|---|---|---|---|---|---|
| J-GF-KIT-01 | GF kitchen GF-RA3AD49 | BASE_RUN (L) | 137 + 11C | 4.700 | 0.500 | 2.600 | 1 | - |
| J-GF-PAN-01 | GF pantry (open plan GF-RC99C2A) | BASE_RUN (L) | B1 + 15C (returns 335, 33F) | 3.516 | 0.450 .. 0.500 (column 2FAE 0.05 under the N leg) | 1.963 | 1 | - |
| J-GF-PAN-02 | GF pantry (open plan GF-RC99C2A) | BASE_RUN (L, peninsula) | AA + B4 (returns B2, 15D); back of the E leg = OPEN edge B3 | 3.400 | 0.500 | 1.950 | 1 | stools 174-177 (loose) |
| J-GF-WSH-01 | GF hand-wash lobby GF-RDBD4F9 | VANITY (2 legs, angled) | 2BF + 2BE | 2.773 | 0.46 .. 0.70 (angled back 318, square sample at the obtuse bend) | 1.261 | 1 | WASH2 2C0, 2C1 |
| J-GF-WSH-02 | GF majlis wash lobby GF-R8496F0 | VANITY | 1CE | 2.100 | 0.500 | 1.050 | 0 | WASH2 1CF, 1EE |
| J-GF-WSH-03 | GF lobby off the stair hall GF-RD36087 | VANITY | 33A | 1.100 | 0.500 | 0.550 | 0 | WASH2 33B |
| J-GF-CPB-01 | GF master bedroom GF-R75FBAE | CUPBOARD (diag 2F1) | 2EF | 1.462 | 0.03 .. 0.50 (back corner cut by the angled wall 319) | 0.606 | 0 | - |
| J-1F-CPB-01 | 1F dressing 1F-RFFE7AF | CUPBOARD (diag BE3) | B0A | 1.800 | 0.500 | 0.900 | 0 | - |
| J-1F-CPB-02 | 1F master bedroom lobby 1F-R3CFCFD | CUPBOARD (diag C17) | B0C | 2.100 | 0.500 | 1.050 | 0 | - |

Totals: BASE_RUN 3 pcs, **11.616 lm**, worktop **6.513 m2**; VANITY 3 pcs, **5.973 lm**, **2.861 m2** (5 basins
excluded to B12-01); BUILT_IN_CUPBOARD 3 pcs, **5.362 lm**, 2.556 m2 plan. 2F: no joinery drawn (maid room, WC, stair,
lift). Per floor: GF 7 units, 1F 2 units, 2F 0.

Hand checks (independent of the script): KIT-01 = 2.5 x 0.5 + 2.2 x 0.5 + 0.5 x 0.5 corner = 2.600 m2, front 2.500 +
2.200 = 4.700 lm; PAN-01 = W leg 3.0662 x 0.5 = 1.5331 + 0.40 x 0.45 (over the column) + 0.50 x 0.50 = 1.9631 m2;
PAN-02 = 1.40 x 0.5 + 2.50 x 0.5 = 1.950 m2; CPB-01 trapezoid 0.5 x (1.4618 + 0.9618) / 2 = 0.6059 m2. All agree to 0.0001.

## 3. HELD (designer items; never a default, never 0)

| Item | Units | Missing drawing fact |
|---|---|---|
| Base cabinet / counter height | KIT-01, PAN-01, PAN-02, WSH-01..03 | no interior elevation / section of any unit (T-091: all 12 pages read, no kitchen detail) |
| Worktop material (granite / marble / solid surface) and edge | the 6 counters, 9.374 m2 | no finish schedule (T-325), no note on the plan |
| Carcass / door material and finish | all 9 units | not printed |
| Cupboard front face m2 = lm x height | CPB-01 / 1F-01 / 1F-02, 5.362 lm | height not printed |
| Whether the cupboards are fitted joinery in the contract | CPB x3 | the diagonal is a drafting symbol only (T-460); no schedule / note |
| Peninsula back panel (stool side, OPEN edge B3, 3.000 m) | PAN-02 | finish of the exposed back not printed |

NOT_DRAWN (no outline at all, value None): kitchen wall cabinets, pantry wall cabinets, laundry joinery (1F-R26FA0D draws
no counter, cabinet or appliance outline; T-351 agrees).

Proposed for DESIGNER_QUESTIONS.md (the Lead adds them): D-J1 joinery schedule: base cabinet / vanity heights, worktop
material, carcass / door material for the 6 counters (11.616 + 5.973 lm, 9.374 m2); D-J2 built-in cupboards: fitted or
loose, height and front type for the 3 cupboards (5.362 lm); D-J3 wall cabinets in the kitchen / pantry: drawn nowhere,
wanted or not.

## 4. Independent checks run

- Machine scan of every fixture-layer LINE pair for the cupboard symbol (`find_cupboard_symbols`, wall-twin exclusion):
  finds exactly 2EF/2F1, B0A/BE3, B0C/C17 = the three reading cupboards (AGREES).
- Completeness: every fixture-layer LINE inside a room is in a unit or classed not-joinery (stair / void rooms, lift,
  thresholds 19C 22B B9B 12B3, steps 13C 22C-22E, garden edges 30F 310, open edges B3 AD, the curved-flight treads):
  0 unexplained. The scan itself found WSH-02 and WSH-03 (missed on the first visual read).
- Second drawing: sheet 03 draws the kitchen L, both pantry L runs, the peninsula with the two stools; sheet 04 draws both
  1F cupboard symbols (dressing and lobby). Shapes agree; neither sheet prints a unit dimension or height.
- Prior merged readings agree: T-460 / T-481 (1F dressing box 0.500 x 1.800, front B0A, diagonal BE3), T-218 (lobby
  0.50 x 2.10 is joinery, not a shaft: nothing stacked above / below), T-312 / T-351 (pantry W 3.066 / N / S legs and the
  peninsula on the open edge B3; kitchen L 0.50 deep).
- Floor under the counters: on the V2.9 room polygons PAN-02's S leg and peninsula foot (1.20 m2) lie in no room, but the
  candidate already carries the pantry strips (T-427: 0.600 + 1.100 m2 inside the 147.658 outline): no new floor finding.

## 5. Engine vs freelancer

No freelancer joinery row is mapped (T-748 scorecard: B13-06 DESIGNER ITEM, no reference line); the décor / marble
workbook (Drive, 23 MB) is beyond the connector limit and was not read for counter-top marble. Verdict proposal:
NOT_COMPARABLE (NO_ROW) for every unit; the engine-side census stands on the drawing alone.

## 6. Checker Gate A (acceptance: recount 2 units by handle)

`bash scripts/agent_env.sh run --tree task-T-753 research/agents_t753/t753_handles.py <arch.dxf> 137 11C 136 11B A4 B0A BE3 B00`
then KIT-01: fronts 137 (2.500) + 11C (2.200) = 4.700 lm, back faces 136 / 11B at 0.500; 1F-CPB-01: front B0A 1.800 lm,
diagonal BE3 from B0A's S end to B00's N end, depth 0.500. `t753_render.py <dxf> <png> x0 y0 x1 y1 --handles` draws any
window with its handles.

## 7. Lesson (proposed ERS s.7 row)

| Problem | Root cause | Rule | Test | Status |
|---|---|---|---|---|
| a visual read of the plan missed two vanity counters (WSH-02 / 03) that hold three basins | the eye looks for labelled rooms; unlabelled lobbies hold fixtures too | a census of drawn installations closes with a completeness scan: every fixture-layer entity inside a room is in a unit or named not-a-unit; 0 unexplained before handing in (scope: every villa, every census family; provenance T-753) | tests/t753_joinery (reading well-formed, scan agrees, misread outlines refused) | PROPOSED |

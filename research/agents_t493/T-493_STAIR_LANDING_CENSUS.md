# T-493: B7 stair-landing census, both staircases (training villa; method every villa)

Worker 2 (lane A), 2026-11-03, branch agents/task-T-493, base engine c814c55d (candidate of record V3.0.47; its only
change over V3.0.46 is FIN.SKIRTING, so the landing and floor lines are read from the V3.0.46 line index of T-485).
Research only: no engine, rule, registry or candidate file is changed. The proposed B7-04 lines are UNWIRED (the
integration is a later stream F row). Files: `research/agents_t493/*`, `tests/t493_landing_census/*`.

Rules applied: UP-STAIR-005 (a stair landing is marble, measured on its actual polygon, never also porcelain),
UP-STAIR-001, OWNER_RULE_STAIRS_2026-10-24 (S-5, S-9 (2) "measure their actual polygons", A3 split-level, A4 notch,
A6 one surface once), Q-66 B, Q-70 A (condition met, T-129), Q-46 A (section A-A governs the riser count), R-T490-1,
UP-QTY-STATUS-001, ENGINEERING_REASONING_STANDARD s.2.1 / 2.4 / 4 / 7.

## 1. The physical element

A landing is a flat walking surface of a stair, between flights or at a flight end. What it is depends on its level and
on the flights that touch it:

- **STAIR_LANDING**: at a level that is not a storey floor, reached by one flight and left by another (half, quarter or
  split-level landing). It can only be stair, so B7, marble by UP-STAIR-005 (owner, MANDATORY).
- **STAIR_ARRIVAL**: at a storey floor level at a flight end, made part of the stair by an owner answer whose condition
  is recorded as met (Q-66 B, Q-70 A). B7, marble.
- **FLOOR**: at a storey floor level at a flight end, inside a room whose floor line carries it (open plan, no zone of
  its own). B3, the room's line (A6).
- **FLOOR_OR_LANDING**: at a storey floor level at a flight end, bounded as its own zone, with no printed landing depth
  and no owner answer. Area measured, material HELD (R-T490-1), never defaulted.
- **WINDER**: a tapered step of a turn. Tread family, never a landing (S-9).

Edges (one plan partition, the convention of the printed dimensions and of the released 1F arrival, T-269): toward an
ARRIVING flight the landing owns that flight's last nosing (its own 0.050 projection); toward a DEPARTING flight it ends
on that flight's first nosing line. The 0.050 strip under a departing nosing is installed but hidden: it is reported
beside each part (0.0575 per 1.15 m lane), never added.

## 2. Evidence read this run

Architectural DXF (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55), decoded into
.work/private only. Every edge is read by handle and checked in code (`verify`, 1 mm tolerance; EXTRACT_T493.json holds
handles, layers and local coordinates only):

- ST-01 shaft, three plans side by side, one shared y (north faces 2AB / ADE / 127E at y 5.000): nosing / riser-face
  pairs 0.050 apart on every flight (DC / DE, 481 / 482, A92 / A93, AC0 / AC2, 135B / 135C, 1386 / 1385).
- Printed dimensions: 1F and 2F stair chains 1950 / 3300 / 1200 (10DF / 10D1 / 10C3 and 14F1 / 14D5), widths 1200 +
  100 + 1200 (10ED / 10FB / 110A), 2F lobby 4500 (152A), round stair width 1250 (1265).
- The turn line at x 1.25 / 1.30 (nosing L5 / riser face L2) over y 3.85 .. 5.00 on all three plans: GF 2C6 / 49C /
  49D (hidden, above the cut), 1F BE4 / BE5, 2F 12B4 / 12B5. Stacked: on GF -> 1F it is the edge of MS1-LD above the
  last winder; on 1F -> 2F it is the closing riser MS2-TR (structural split 5E2 at 1.30 on ST p.5, T-258).
- ST-02 quarter landing: RS-S last nosing B4D (riser face B58), RS-A first nosing B59 (B6E), east edge band AF5 / AF6,
  GF wall 336 ending at x 0.65 under it, column 3008 0.60 x 0.25 standing 0.050 proud.
- Second drawing: the structural plates (T-258 / T-281 / T-438, MERGED, cited) MS1-LD 1.20 x 1.20, MS2-LD W 1.30 x 1.15 /
  E 1.20 x 1.20, RS-LD 1.150 x 1.200 net of column 374.

## 3. Census (CENSUS_T493.csv; summary.json; `python3 -I t493_alsenan.py --check` reproduces)

| Part | Element | Level | Area m2 (edges) | Material | Trade | Line (V3.0.46) |
|---|---|---|---|---|---|---|
| ST-01 GF hall, foot of MS1-L / top of D1 | FLOOR_OR_LANDING | +1.00 | **4.8050** (T-418 polygon) | **HELD** | B3-01 or B7-04 | L-f53d4986 FINISH_HELD 4.805 |
| ST-01 GF back lobby, foot of D1 | FLOOR_OR_LANDING | +0.30 | **1.3225** (481 to 26F / 2AB) | **HELD** | B3-01 or B7-04 | L-b4441a1b FINISH_HELD 1.3225 |
| ST-01 MS1-T winder turn | WINDER | +2.667 .. +3.50 | (tread family) | - | B7-02 | treads HELD (T-412, Q-51, S-9) |
| ST-01 **MS1-LD** half landing | STAIR_LANDING | +3.50 | **1.4375** = 1.25 x 1.15 (own nosing x 1.25 to B16; A92 y 3.85 to y 5.00) | marble (UP-STAIR-005) | B7-04 | **NO LINE: silent omission (F-3, new)** |
| ST-01 1F arrival | STAIR_ARRIVAL | +5.50 | **4.9225** = 4.875 - 0.010 + 0.0575 | marble (Q-66 B) | B7-04 | L-8011889d RELEASED 4.9225 (drawn - line 0.0000) |
| ST-01 **MS2-LD** split-level half landing | STAIR_LANDING | +7.516 / +7.684 | **2.9325** = W 1.4950 + E 1.4375 (A97 y 3.80, printed 1200; 135B y 3.85) | marble (UP-STAIR-005) | B7-04 | **only inside HELD bound L-5d2be30d (F-4)** |
| ST-01 **2F arrival** | STAIR_ARRIVAL | +9.70 | **4.8650** (see s.4) | marble (Q-70 A, condition met T-129) | B7-04 | **only inside HELD bound L-5d2be30d (F-1)** |
| ST-02 foot of RS-C in the GF open room | FLOOR | +1.00 | in the room line | porcelain by its line | B3-01 | L-7625f35c |
| ST-02 **RS-LD** quarter landing | STAIR_LANDING | +4.696 | **1.3525** = 1.20 x 1.15 - column 3008 0.55 x 0.05 | marble (UP-STAIR-005) | B7-04 | **NO LINE (F-2)**; deducted from 1F porcelain as R04 1.352454 |
| ST-02 top of RS-A on 1F | FLOOR | +5.50 | in the room line (D22 nosing lm in B7-05) | porcelain by its line | B3-01 | L-b06400d4 |
| ST-03 E1 entrance landing | STAIR_ARRIVAL | +1.00 | **5.1800** printed 1.40 x 3.70 | marble (outdoor stairs owner rule) | B7-04 | L-3dd82a57 RELEASED 5.1794 (-0.0006) |

**Nothing is counted twice.** No part is claimed by both B3 and B7 (0.000 m2 shared). Same-level overlaps: none (the
census refuses one). Stacked surfaces, different levels, surface overlap 0 (plan overlap reported): MS1-LD over the
+0.30 lobby 1.3225; MS2-LD over MS1-LD 1.4375 and over the lobby 1.3225; 2F arrival over 1F arrival 4.8650; GF hall
under the 1F / 2F arrivals 1.2975 / 1.2400. 2F arrival vs the 2F lobby porcelain L-9bd25c0c (x 2.50 .. 4.50): 0.000.
MS1-LD and MS2-LD lie over the 1F void V01 / footprint R03, which the 1F porcelain line already deducts; RS-LD is the
1F porcelain deduction R04 (1.352454 vs 1.3525, 0.00005 grid).

## 4. The four landings without a line of their own

- **F-2 RS-LD 1.3525 m2.** An intermediate quarter landing (+4.696, between RS-S and RS-A) is STAIR_LANDING by its
  level and flights, not FLOOR_OR_LANDING: the T-490 lesson is about a floor AT a flight end. Its size is not printed,
  but S-9 (2) measures landings on their actual polygon, and the polygon is closed by four drawn edges on the
  architectural plan and agrees with the structural plan (1.150 x 1.200 net of column 374, T-438; the same footprint
  carries the released RS-LD concrete, Q-50 A cond). Area DRAWING-CONFIRMED, material marble OWNER RULE. Proposed line:
  B7-04 1.3525 m2.
- **F-1 2F arrival 4.8650 m2.** Polygon: x 0 .. 2.50 from the south wall (1282 / 1283, y -1.45). In the west lane and the
  divider (x 0 .. 1.35) it runs to the slab / guard edge 138A at y 0.45. In the east lane it runs to the top riser face
  of MS2-U at y 0.50, plus its own floor nosing band to 0.55. That gives 2.50 x 1.90 + 1.15 x 0.10 = 4.8650. Printed
  2.50 x 1.95 = 4.875. The difference is -0.0675 for the guard band 138A / 138B (y 0.45 .. 0.50 over x 0 .. 1.35: the
  2F slab ends there over MS2-L, where the 1F arrival is floor) and +0.0575 for the nosing band (T-269, as on 1F). Q-70 A
  condition met (T-129). Proposed line: B7-04 4.8650 m2.
- **F-3 MS1-LD 1.4375 m2 (new finding).** The +3.50 half landing lies over the +0.30 back lobby. The GF face partition
  (T-418) counts the lobby there, so the landing never entered any face, bound or line. Polygon: 1.25 x 1.15. Its own
  nosing 2C6 / BE4 is at x 1.25, A92 at y 3.85, the walls at x 2.50 and y 5.00. The structural plate is 1.20 x 1.20 = 1.44;
  the finish is +0.0575 nosing band and -0.0600 strip under A92 relative to it. Proposed line: B7-04 1.4375 m2.
- **F-4 MS2-LD 2.9325 m2 (new finding).** The split-level landing has two parts:
  - W at +7.516: x 0 .. 1.25 from A97 (y 3.80, printed 1200), 1.4950.
  - E at +7.684: x 1.25 .. 2.50 from 135B (y 3.85), 1.4375.

  The total is established whatever the split. The split stays HELD AS A SPLIT. The pair 12B4 / 12B5 places the closing
  riser at x 1.25 / 1.30, matching the structural 5E2. But the 2F plan also draws an unexplained diagonal pair 2F1F / 2F20
  across the east half (Q-ST-11, s8_7). Section A-A has one closing riser (Q-46 A governs), so the diagonal is not
  counted as a riser. Proposed line: B7-04 2.9325 m2. The level split and the diagonal go to the designer RFI list, not
  to the owner.

**The two bound lines.**

- **L-1983e89d** (GF, 0 .. 2.9225): its content holds no landing. It is made up of 0.690 of MS1-L / D1 treads beyond the
  candidate tread figure, 1.3225 of winders, 0.680 of divider and 0.230 of the unread strip, which sums to 2.9225. It is
  **NOT_APPLICABLE as a landing bound**: each item belongs to its own family.
- **L-5d2be30d** (2F, 0 .. 9.225): the bound holds 7.7975 m2 of landings (the 2F arrival 4.865 and MS2-LD 2.9325),
  which leave as their own lines. The rest, 1.4275 m2, is not landing: the guard band 0.0675, the MS2-U top tread 0.345
  and the void residual 1.015.

Before / after, B7-04 landing marble:

| | Before (V3.0.46 / .47) | After (proposal) |
|---|---|---|
| Released | 10.1019 (E1 5.1794 + 1F arrival 4.9225) | **20.6894 m2**: + RS-LD 1.3525, + 2F arrival 4.8650, + MS1-LD 1.4375, + MS2-LD 2.9325 = **+10.5875 (+104.8 %)** |
| HELD high | 12.1475 (the two bounds) | **0** (both retired) |

Unchanged:

- GF hall 4.805 and lobby 1.3225 FINISH_HELD (B3 lines);
- every porcelain line (each landing is already deducted from it or lies in a void);
- every concrete line.

## 5. Named residuals and side findings (no line changed here)

- GF hall 4.805 (T-418) runs to the MS1-L riser face DE (y 1.15). Under the plan-partition convention it ends at the
  nosing DC (y 1.10), so 0.0575 of it lies under the first nosing. This is a convention residual on a B3 FINISH_HELD
  line: reported, not moved.
- The strips under the departing nosings, reported beside the parts and never added: MS1-LD 0.0575, the 1F arrival
  0.0575, MS2-LD 0.115, RS-LD 0.0575, the lobby 0.0575.
- E1: printed 5.1800 vs line 5.1794 (-0.0006, T-490).
- The GF hall and lobby stay HELD in material. A6 ("a floor-level landing goes to the floor finish") points to B3 as
  their trade, which is what their FINISH_HELD lines already do. It does not supply a material: no finish source exists
  (RFI-B-A12).

## 6. Engine vs freelancer (recorded values; workbook 23.6 MB over the connector limit, not re-opened)

| Item | Engine (proposal) | Freelancer | Difference | Verdict proposal |
|---|---|---|---|---|
| Main-stair intermediate landings (MS1-LD + MS2-LD) | 4.370 | 6.20 (one row, "2 landings", no breakdown; T-086 / T-129) | -1.830 m2 (-29.5 %) | UNRESOLVED (no breakdown). 6.20 would fit two full-width 2.50 x 1.24 landings, which on GF -> 1F would include the winder corner (treads, S-9). A figure match is not evidence. |
| 1F / 2F arrivals | 4.9225 + 4.8650 marble | in his porcelain rows (living 38.96, corridor 7.70) | material only | RULE_DIFFERENCE (Q-66 B / Q-70 A) |
| RS-LD | 1.3525 marble | no landing row found in the recorded rows | +1.3525 | ENGINE_RIGHT (drawn, UP-STAIR-005), pending the Checker re-measure |
| E1 landing | 5.18 printed | 5.10 | -1.5 % | ENGINE_RIGHT (T-490, verified) |

## 7. Rule R-T493-1 and tests

The rule is in `landing_census_v1.py`, with the full text in its docstring. Landings are enumerated per stair from its
flights and levels, never from a plan-face residual, and measured on the drawn polygon less solids:

- stacked surfaces are separate parts;
- a same-level overlap is refused;
- one surface is never claimed by both B3 and B7;
- a split-level landing keeps its total when the split is unknown;
- a bound is itemised, and is NOT_APPLICABLE when it holds no landing.

`tests/t493_landing_census`: 43 PASS. Hand villa K493 (not Alsenan):

- the normal case is a dimensioned half landing, 2.30 x 1.20 = 2.760, in m and mm, rotated 0 / 37 / 90 / 211 degrees,
  plain and mirrored, with a column notch (2.745);
- the arrival is 3.450;
- the stacked lobby is a plan overlap of 1.320 with a surface overlap of 0;
- the split-level total holds, with the split known and unknown.

Adverse cases:

- a quarter area at the floor foot with no printed depth is FLOOR_OR_LANDING, area 1.21 kept, material HELD;
- an owner condition not met stays HELD;
- no polygon gives area HELD (None), never 0;
- a winder is never a landing;
- a same-level overlap is refused;
- a surface claimed by both B3 and B7 is refused;
- a bound with no landing is NOT_APPLICABLE;
- bound content that does not re-add is refused;
- the refusals cover unit ft, a missing level, a missing flight, a bad polygon, an unknown material, a stray solid and a
  duplicate id;
- the module holds no villa constant.

The training-villa pin and a byte-identical rebuild from the extract are also tested.

## 8. Checker re-measure proposal

The 1F round-stair quarter landing RS-LD, on P7757.dxf: B4D (x 0) to AF5 (1.200) by the 336 face (y 0) to B59 (1.150) =
1.3800, less column 3008 inside (x 0.65 .. 1.20, y 0 .. 0.05) 0.0275 = **1.3525 m2**. Second drawing: ST p.4 1.150 x 1.200
net of column 374 (T-438).

## 9. Lessons-register row (proposed, ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-03 | Three intermediate landings (dog-leg 1.4375 + 2.9325, round-stair 1.3525) and the 2F arrival 4.865 had no landing line; a "landings" bound held winders, divider and void | the landing family was built from each room face's plan residual, so a landing stacked over another floor part, or lying in a void, was never a census part | R-T493-1: enumerate landings per stair from flights and levels; a surface between storeys with an arriving and a departing flight is STAIR_LANDING, measured on its polygon; stacked surfaces are separate parts; a bound is itemised and NOT_APPLICABLE when it holds no landing (every villa) | tests/t493_landing_census (normal 2.760 + adverse floor-foot quarter HELD) | PROPOSED |

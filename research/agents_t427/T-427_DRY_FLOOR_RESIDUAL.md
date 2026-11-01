# T-427: the dry floor-finish residual against the freelancer after T-418, closed to named causes; wet split

Worker 2 (lane A), 2026-11-01. Gate 3. Research only: nothing is wired, no released or candidate quantity changes.
Development villa, not an accuracy claim. Candidate of record ARCH_TAKEOFF_V3.0.36 (NOT RELEASED); its floor-finish lines
are those of V3.0.34 / V3.0.35 (T-414 room table, T-418). Inputs: Drive "Alsenan chalet project" P7757_DXF_COMPRESSED.zip
-> P7757.dxf (sha256 ab54dd55) and p7757_arch_sheet03.pdf (GF plan, read at 250 dpi), decoded into .work/private only;
an own released ARCH_TAKEOFF_V2.9 run of the DXF (faces, strips); merged ledgers T-074, T-086, T-147, T-153, T-240,
T-286, T-343, T-345, T-414, T-418. Freelancer: FIN workbook, tiles sheet, quantities only (dry 337.57, wet 72.01 m2).

## 1. Result

Dry: candidate with T-418 296.7733 vs 337.57 m2 = **-40.7967 m2 (-12.09 %)**, closed on 17 named components
(RESIDUAL_T427.csv; sum = difference to 0.0001): TRACED -30.4644, HELD -9.7050, UNEXPLAINED **-0.6273** (was -2.8713 in
T-418: GF -2.5463 + 2F -0.325).

| Component (engine - freelancer, m2) | m2 | Class | Verdict proposal |
|---|---|---|---|
| GF pantry floored wet | -13.4549 | TRACED | RULE_DIFFERENCE: UP-WET-001 (pantry on the wet list) + owner Q-37 A (printed 4.50 x 3.00 box) + URBAN-WET-FLOOR-TILED@v1; he keeps it in his dry reception + dining row |
| GF round-stair treads below the cut | -6.1244 | TRACED | RULE_DIFFERENCE: UP-CER-001 (stair footprint deducted from the tile) + UP-STAIR-005 (treads are B7 marble); 8.194412 - 2.07 under-stair floor kept |
| GF garden band proper, x 6.80 .. 13.82 | -9.1010 | HELD | UNRESOLVED (designer D-48: planter or floor) |
| GF band curb strip, x 6.80 .. 9.82 (0.20) | -0.6040 | HELD | UNRESOLVED with D-48 |
| **GF band WEST part x 3.00 .. 6.80 = dining floor** | **-5.6450** | TRACED | **ENGINE_WRONG / FREELANCER_RIGHT** (section 2): corrected -> 0 |
| GF wall + 2 columns inside his gross outline | -0.8800 | TRACED | ENGINE_RIGHT (net floor) / his row is the gross outline |
| GF open room: his rows above the drawn gross outline | -0.3023 | UNEXPLAINED | UNRESOLVED (0.20 %; 0.1140 if his row holds the 0.1901 lobby mouth) |
| GF stair-room floor parts (T-418) | +6.1275 | TRACED | UNRESOLVED (no floor row of his, see 3) |
| GF master / dewaneya / driver | -0.0051 | TRACED | T-086 |
| doorway strips GF 0.35 / 1F 0.72 / 2F 0.18 | +1.2500 | TRACED | engine-only strips (T-240) |
| 1F living (Q-66 B landing + T-345) | -5.2490 | TRACED | RULE_DIFFERENCE |
| 1F bed rooms | -1.3785 | TRACED | T-086 |
| 2F maid room | -0.2300 | TRACED | T-086 |
| 2F arrival marble (Q-70 A, B7) | -4.8750 | TRACED | RULE_DIFFERENCE |
| 2F corridor residual (his 7.70, no dimensions) | -0.3250 | UNEXPLAINED | UNRESOLVED |

**Corrected candidate** (R-T427-1 applied, lane I to integrate): dry **302.4183 m2, -35.1517 (-10.41 %)**; the HELD
garden-band scope falls from 15.350 (13.986 faces + 1.364 strip) to **9.705 m2** (9.101 + 0.604).

Wet: 85.5756 vs 72.01 = **+13.5656 (+18.84 %)**, 18 components, all TRACED, sum exact: pantry +13.4549 (the dry
pantry's mirror, RULE_DIFFERENCE) + the 17 wet rooms +0.1107 (T-074 hand table, MERGED/VERIFIED, room by room: 7
ENGINE_RIGHT, 1F laundry +0.151 and GF W.C. wedge B +0.0676 the largest; GF basin -0.215 RULE_DIFFERENCE, his 0.20 reveal
in the room). No unexplained wet residual.

## 2. The physical element: where the GF garden band ends (ERS s.2)

Element: the band labelled GARDEN / حديقة along the inside of the GF south facade, south of the round stair (register
D-48). Drawn on P7757.dxf (handles; room-local metres, origin = inner SW corner of the pantry box):

| Edge | Drawn line | Reading |
|---|---|---|
| west end | 310, layer 5, x 6.80, y 0 .. 1.50 (wall face to the stair box) | the band's west end |
| east end | 30F, layer 5, x 13.82, y 0 .. 1.45 | east end |
| north, x 6.80 .. 9.82 | 4B4 (L2) y 1.30, A9 (L5) y 1.45, A8 (L2) y 1.50 | a 0.20 curb with an inner line |
| north, x 9.82 .. 13.87 | columns 2FD2 (0.80 x 0.25) / 2FC6 (0.60 x 0.25), wall 337 / 336 (L1, 0.20) between them | structure under the 1F facade |
| west of x 6.80, y 1.30 / 1.45 / 1.50 | **none** (layers 1, 2, 5, W, S-COL.BON, D searched; sheet 03 draws none) | **open to the dining floor** |

The GARDEN label sits at x 10.46 (centre of 6.80 .. 13.82 = 10.31). Sheet 03 draws the same: the curb lines start at
the stair box's west line and run east; between the pantry line and that line the dining floor is open to the facade.

The engine (V2.9 face cutting, carried into the candidate) prolonged the band edge 3.80 m west to the pantry line: the
'OP-003 passage' strip of T-240 (11.22 m) is that prolonged edge. It cut off GF-RFD4E1D 4.885 m2 (3.80 x 1.30 less the
1.10 x 0.05 column 2FCF) and the strip x 3.00 .. 6.80 0.760 m2, and both went HELD with the band (candidate lines
L-6b6412e8 ARCH.SPACE 4.885 and part of L-554a525e ARCH.SPACE 1.364). Nothing physical separates them from the dining
floor, so they are dining floor: **5.645 m2 DRAWING-CONFIRMED area, finish as the open room (porcelain, ASSUMED —
OWNER-APPROVED URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1, the open-room line's own status)**.

Owner manual method beside the drawing method: the printed chain dimension 1082 runs from the pantry line (x 3.00) to
the band's east end, and T-153 read it as the band length (1.30 x 10.82 = 13.986, P-2). The chain starts at another
element's line (the pantry edge B3) and the drawn outline is closed by its own end line 310 at 6.80: a dimension never
extends a zone over a piece whose edges the drawing leaves open (R-T427-1.3). Under either D-48 answer the 5.645 m2 is
floor: if the band is floor (P-2 B) everything is floor; if it is a planter (P-2 A), a planter needs its curb on every
side and the drawing gives it one only east of 6.80. The only reading that makes it non-floor (a 10.82 m planter with a
3.80 m curb nobody drew) contradicts line 310. So it leaves D-48; D-48 keeps 9.101 + 0.604 = 9.705 m2.

Reconstruction (first principles, room-local): band 7.02 x 1.30 - column notch 0.50 x 0.05 = 9.101; curb 3.02 x 0.20 =
0.604; west face 3.80 x 1.30 - 1.10 x 0.05 = 4.885; west strip 3.80 x 0.20 = 0.760; columns 0.80 x 0.25 + 0.60 x 0.25
+ wall 2.65 x 0.20 = 0.880.

## 3. The T-418 'unexplained 2.5463 m2' (acceptance: the Checker re-measures it)

His two rows (reception + dining 137.50, entrance 10.46 = 147.96) re-add to the open room's GROSS outline, as T-147 found
(147.90). Own polygonization of the outline (wall faces, doors closed on their faces): 151.6802 m2 = V2.9 GF-RC99C2A
126.928 + GF-R9A05AA 9.101 + GF-RFD4E1D 4.885 + GF-RC06FED 2.800 + pantry strips 0.600 + 1.100 + band strip 0.604 +
0.760 + columns / wall 0.880 + the wash lobby part open to the room 3.8321 (his wet row 4.73) + its mouth strip 1.256 x
0.15 = 0.1901 (ARCH.THRESHOLD L-1c71cd45, BLOCKED_RFI, RFI-B-A10 (c)). Less the last two: **147.658**, which equals the
candidate's own parts 111.8484 + 6.1244 + 13.4549 + 13.986 + 1.364 + 0.880 = **147.6577** (two routes, 0.0003). So:

2.5463 = **1.364** (HELD strip L-554a525e: 0.760 dining floor + 0.604 curb) + **0.880** (wall + columns: not floor,
in his gross) + **0.3023** (his figure above the drawn outline; UNEXPLAINED, 0.20 %).

His entrance row is inside this outline (the hall inside the D200 entrance door), so the GF stair-room hall (T-418,
+6.1275) is in none of his floor rows: an engine-only floor quantity (his 6.20 main-stair landing row has no breakdown;
a match by figure stays refused).

## 4. Rule, tests, lessons row

R-T427-1 (any villa; floor finishes / rooms; provenance T-427; research module `zone_extent_v1.py`, ZONE_EXTENT_V1):
a piece of a room's plan joined to the room floor across an edge no drawn line marks (>= 0.30 m; an engine zone line or a
prolonged edge line is not a drawn line) is room FLOOR; joining propagates; a piece separated on every edge by drawn lines
keeps its class (ZONE / STRIP HELD with its zone, area kept; SOLID no floor); a printed dimension never extends a zone over
an open piece; pieces re-add to the input, never overlap, a moved piece keeps its area (DRAWING-CONFIRMED) and takes the
room's finish status. `close_residual` names the parts of a gross-outline comparison and returns the rest as UNEXPLAINED,
never 0. Not an Alsenan constant (no layer, room or dimension in the module).

Tests `tests/t427_zone_extent` (20 PASS): villa K427 (not Alsenan; 12.00 x 7.00 living, planter drawn 5.00 .. 11.00):
normal m / mm, rotations 0 / 37 / 90 / 211 deg x mirror with shift; adverse: curb drawn the full length -> nothing
moves; 0.10 m drafting gap -> not open; SOLID never joins; the engine's prolonged edge passed as 'drawn' gives the old
wrong answer (pinned); refusals (no seed, overlap, unit ft, unknown class, missing polygon, duplicate id, HELD part with
no figure, unknown residual class). Alsenan pins: hand areas, dry / wet closures, committed outputs reproduce.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | 5.645 m2 of GF dining floor sat HELD inside the garden band for 11 days and the gross comparison left 2.5463 m2 'unexplained' (T-427) | the engine prolonged a zone's edge line past the zone's own drawn end line and the printed chain dimension was read as the zone length | R-T427-1 above (any villa): a zone ends at its own drawn outline; a piece joined to the room floor by an undrawn edge is room floor; a gross-outline residual is closed against the drawn outline (walls / columns inside it named) before anything is called unexplained | tests/t427_zone_extent | proposed |

## 5. For lane I and cross-trade (no quantity changed here)

- Lane I proposal (after T-420 / T-421): ONE new FIN.FLOOR.PORCELAIN line "GF dining floor along the south facade
  (band west part)" 5.645 m2 (area DRAWING-CONFIRMED, finish as L-7625f35c) on element GF-RFD4E1D + the 3.80 m of the
  OP-003 strip; L-6b6412e8 (4.885) retired with that line named; L-554a525e 1.364 -> 0.604 (curb, HELD D-48). One m2, one
  line: the floor bed B3-05 (T-420) follows the new line. Before / after dry: 288.1458 -> 293.7908 on V3.0.36 lines
  (302.4183 with T-418's 8.6275 integrated).
- Designer list: D-48 text still says 13.986 m2: it is 9.101 + 0.604 curb = 9.705 m2 (Lead: register / RFI text).
- Ceilings (T-283 r3 / T-295 ledger): GF-RFD4E1D 4.885 m2 and its 6.5428 m bulkhead edges are HELD_CLASS "P-2"; under
  R-T427-1 they are the dining room's ceiling (the class becomes decidable; the type is the open room's). Not re-measured
  here: the ceiling owner's row.
- Skirting L-71e2e002 (GF open room, 24.6716 lm): its run along the prolonged edge y 1.50 is already deducted (OP-003,
  T-296 PASSAGE_RUN_RESIDUAL), but the dining's real south wall face x 3.00 .. 6.80 sits on the cut-off face GF-RFD4E1D,
  which carries no finish line: **+3.90 lm missing** (V2.9 runs of that face: wall 2.70 = 3.80 - 1.10 column + column
  2FCF faces 1.20) -> 28.5716 lm, DRAWING-CONFIRMED geometry (for the skirting owner / lane I). The band's own wall faces
  (x 6.80 .. 13.82) stay HELD with D-48. Plaster / paint: T-128 walks the T-147 open-room region (134.40 m2, which
  holds the whole band), so its south wall faces are already in that ledger; not re-measured here.

## 6. For the Checker (re-measure, not from this file)

1. P7757.dxf: lines 310 (L5) and 30F (L5) at the band ends, 4B4 / A9 / A8 and 337 / 336, columns 2FD2 / 2FC6 / 2FCF;
   confirm no line at y 1.30 / 1.45 / 1.50 between B3 and 310 (3.80 m); sheet 03 the same.
2. By hand: 3.80 x 1.30 - 1.10 x 0.05 = 4.885; 3.80 x 0.20 = 0.760; 3.02 x 0.20 = 0.604; columns + wall 0.880.
3. The 2.5463 re-add: 147.96 - (111.8484 + 6.1244 + 13.4549 + 13.986 + 1.364 + 0.880) = 0.3023.
4. `python3 -I research/agents_t427/t427_alsenan.py --check`.

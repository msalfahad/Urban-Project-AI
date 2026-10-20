# T-103: blockwork wall metres by hand, per floor and thickness (development villa, NO REPO CODE)

Worker 3, 2026-10-20 10:01-11:20 UTC. Hand truth for the masonry centreline piece (T-027). No engine, rule, test or
fact file changed; no quantity released. Development villa, not an accuracy claim. Files here hold metres, thicknesses
and freelancer row numbers only: no coordinates, no drawings, no client names.

Rules: UP-WALL-GEOM-001 (OWNER_APPROVED: the masonry run is the centreline, a short stretch is not dropped),
UP-COL-ORIENT-001 (OWNER_APPROVED: a column standing in a wall line is concrete, not wall), UP-MAS-HEIGHT-001
(REQUIRES_CONFIRMATION, owner Q-60 open: every block m2 and m3 stays HELD, only metres are given here),
UP-QTY-STATUS-001 (held, never 0).

## Inputs (session scratchpad, never committed)

| Input (Drive "Alsenan chalet project") | Use |
|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf, sha256 ab54dd55...31cc4 (= source manifest) | geometry: plan frames GF, 1F, 2F; wall layer, column outlines, window and door layers, parapet bands |
| p7757_arch_sheet03.pdf (scanned GROUND FLOOR PLAN 1:100) | second drawing: printed chains and wall thickness marks |
| blockwork workbook (the freelancer's) | his rows: length, height, section (external / internal 15 cm / internal 20 cm / parapet / fence) |

## Method (hand tool, run in the scratchpad, not the engine)

1. Every pair of parallel wall-layer lines 0.09-0.26 m apart is a wall band; its mid-line is the centreline. Only two
   thicknesses occur on the wall layer of the three plans: 0.15 and 0.20 (one 0.40 band, held). The scanned plan prints
   the same marks ("20" on the outer walls, "15" on partitions).
2. Collinear pieces of one thickness are joined across: a drawn opening (window lines, door leaf / swing), a column, a
   junction gap of 0.35 m or less, or an undrawn passage of 1.30 m or less (each listed in `opening_gap_widths_m`).
3. Each run end is carried to the node: an L corner to the crossing of the two centrelines, a T stem to the centreline of
   the wall it meets, a wall end to its drawn end. Columns are not wall: `columns_in_line_m` is the centreline length
   inside column outlines and `gross_minus_columns_m` = gross - columns (UP-COL-ORIENT-001).
4. Openings are NOT deducted from the metres (`gross` and `gross_minus_columns` keep them); their drawn widths are listed
   per run, and `solid_m` = gross - columns - openings is given for reference only. Printed opening widths and heights
   are in research/agents_t083/OPENINGS.csv (T-083).
5. Every run was checked on an overlay of the plan; free ends, near-nodes (under 0.15 m) and curved walls were read
   line by line. Curved walls: concentric arc pairs, length on the centreline radius.

Acceptance: every wall run of the three plans is one row of WALLS_BY_FLOOR_THICKNESS.csv (35 GF + 3 read by hand + 2 held, 26 1F,
9 2F, 14 parapet and 3 fence rows; the shortest is 0.55 m), totals per floor, zone and thickness at its foot; every freelancer row is in
FREELANCER_ROWS_MATCH.csv as EXACT (within 0.01 m), CLOSE (within 0.06 m), UNMATCHED or TOTAL ONLY.

## Second-drawing check (scanned GF plan, sheet 03) against the DXF

| Printed | Printed value | DXF hand reading | Agree |
|---|---|---|---|
| plot / building length along the neighbour side | 31.37 | outer faces 31.37 m | yes |
| sea-side chain 90 + 633 + 90 + 40 + 452 + 45 | 13.50 | outer faces 13.50 m | yes |
| street-side annex chain 83 + 195 + 115 + 195 + 81 | 6.69 | outer faces 6.70 m | 0.01 m |
| annex main room | 630 x 400 | inner faces 6.30 x 4.00 | yes |
| lift | 180 x 180 | inner faces 1.80 x 1.80 | yes |
| saloon glazing | 633 | wall-line gap 6.332 m | yes |
| wall marks | "20", "15" | bands 0.200 / 0.150 | yes |
| annex WC / kitchen wall | "20" | GF-W02 faces 0.200 apart | yes |
| annex WC 130 x 150, driver 450 x 175, kitchen 300 / 270 / 450 | as printed | inner faces 1.30 x 1.50, 1.75 | yes |
| 1F sheet (p7757_arch_sheet04.pdf): partitions "15", outer walls "20" | as printed | bands 0.150 / 0.200 | yes |
| 1F sea-side bay, printed chord | 306 | inner-face chord of the r 1.935 arc at the wall ends about 3.06 m | yes |
| 2F plan (Pages_05-06, page 5): maid room chain 15 + 645 + 20 | 0.15 neighbour-side wall, 6.45 inner | 2F-W03 faces 0.150 apart, inner 6.45 m | yes |
| 2F plan: first-roof edge at the sea-side neighbour corner | "30" | parapet band 0.20 on the DXF | NO: printed 0.30 there (corner only, read on one corner); kept 0.20 in the table, verifier to re-read |

Reception wall GF-W03 (0.20, 2.65 m between two columns): the scanned GF plan shows it as the wall between the
reception stair and the internal garden strip (printed GARDEN, 150); no thickness mark on it.

One conflict (already on record from T-083, owner Q-38): the pool-side bedroom glass is a straight 0.20 band 4.95 m
long in the DXF and a curved wall printed "657" on the PDF (GF-W37 below carries it; only 0.10 m of it is block).

## Result: metres per floor and thickness (hand), against the freelancer

Basis for the comparison: our gross centreline minus columns (his lengths run between columns and he deducts openings
as m2, so his length / his height = his length). Heights are not compared (owner Q-60).

| Floor / zone | Thickness | Hand gross centreline m | Columns in line m | Hand gross - columns m | Freelancer m | Freelancer - hand |
|---|---|---|---|---|---|---|
| GF main + annex, external | 0.20 | 98.75 | 11.93 | 86.83 | 78.55 (all "external") | -8.28 m (-9.5 %) |
| GF internal | 0.15 | 42.51 | 1.32 | 41.19 | 47.53 | +6.34 m |
| GF internal | 0.20 | 18.20 | 3.05 | 15.15 | 8.20 | -6.95 m |
| GF internal, both thicknesses | | 60.71 | 4.37 | 56.34 | 55.73 | -0.61 m (-1.1 %) |
| **GF all walls** | | **159.46** | **16.30** | **143.16** | **134.28** | **-8.88 m (-6.2 %)** |
| 1F external | 0.20 | 62.26 | 8.25 | 54.01 | 54.97 (+ a 7.50 x 5.50 "projections" m2 row) | +0.96 m (+1.8 %) |
| 1F internal | 0.15 | 59.27 | 2.23 | 57.05 | 57.14 | +0.09 m (+0.2 %) |
| 1F internal | 0.20 | 12.85 | 3.15 | 9.70 | 8.20 | -1.50 m |
| **1F all walls** | | **134.38** | **13.63** | **120.75** | **120.31** | **-0.44 m (-0.4 %)** |
| 2F external | 0.20 + 0.15 | 21.15 + 7.90 | 2.20 | 26.85 | 27.90 | +1.05 m (+3.9 %) |
| 2F internal | 0.15 | 3.20 | 0.10 | 3.10 | 3.00 | -0.10 m |
| 2F internal | 0.20 | 12.63 | 2.80 | 9.83 | 8.20 | -1.63 m |
| **2F all walls** | | **44.88** | **5.10** | **39.78** | **39.10** | **-0.68 m (-1.7 %)** |
| Ground-roof parapets (on the 1F plan) | 0.20 drawn | 59.31 | 0 | 59.31 | 66.00 (booked as 15 cm) | +6.69 m |
| First-roof parapets (on the 2F plan) | 0.20 drawn (4.30 m thickness held) | 44.94 + 4.30 held | 0 | 49.24 | 42.85 (15 cm, h 1.80) | -6.39 m |
| Ground + first roof parapets together | | 108.55 | | 108.55 | 108.85 | +0.30 m (+0.3 %) |
| Second-floor top roof parapet (+13.90 to +14.40) | not drawn | HELD (no roof plan) | | HELD | 29.80 (= 2 x (8.10 + 6.80) outer) | not compared |
| Fence (GF plan, 0.20 band on the parapet / fence layer) | 0.20 drawn | 46.37 (gates 2.50 + 1.00 inside) | 0 | 46.37 | 37.20 x 2.00 (15 cm) | -9.17 m |

Held (never 0): GF-H01, a 0.40 m band on the wall layer west of the stair hall, 1.50 m with a 0.80 m column inside
(0.40 is no block family here, material not printed); GF-H02, a 0.20 x 0.90 outline on the furniture / stair layer at
the external stair (cheek or planter, material not printed); the north-west first-roof parapet thickness (4.30 m,
lines 0.20 and 0.40 apart); the top-roof parapet (no plan); every block m2 and m3 (Q-60).

Row matching: 57 of 102 single freelancer lengths match a piece of ours between columns within 0.06 m (most within
0.01 m: e.g. GF north wall pieces 2.50 / 3.47 / 3.55, GF south 6.35 / 5.75 / 3.08 / 1.30, annex 5.45 / 4.45 / 6.10 /
5.85, the lift 1.80 / 1.80 / 1.20 / 0.70 / 2.70 on every floor, 1F south 3.80 / 6.70 / 2.65 / 3.30). He measures the
same pieces we measure between columns; the totals differ where he took a different piece, basis or thickness.

## Who is right: proposals per difference (for the verifier)

1. GF external, freelancer 8.28 m less. (a) The saloon facade line (GF-W11, 7.70 m, of which 6.33 glazing and 0.70
   column) and the pool-side glass line (GF-W37, 5.05 m, 4.95 glazing) have no row of his: he leaves out a wall line that
   is almost all glass; our metres keep openings by the task basis, solid block on them is 0.67 + 0.10 m:
   RULE_DIFFERENCE (opening basis). (b) The 0.20 m passage walls either side of the entrance passage (GF-W16, GF-W17)
   and the annex curved corner (GF-W35, 2 x pi x 1.20 / 4 = 1.885 m, drawn as concentric arcs R 1.30 / 1.10) are not
   clearly in his external rows; he books three 4.45 m walls at 3.50 m under internal 15 cm: UNRESOLVED (his 4.45 m
   rows may be the passage walls, booked as 15 cm although the plan draws and prints 0.20).
2. GF internal: split 0.15 / 0.20 differs (his 20 cm row holds only the lift core: 1.80, 1.80, 1.20, 0.70, 2.70 on each
   floor; we also have the 0.20 walls under the stair void 2.65 m and of the annex WC 1.65 m, faces drawn 0.200 apart),
   the two thicknesses together agree within 0.61 m (1.1 %): ENGINE_RIGHT proposed on the thickness split (hand reading
   of the drawn faces; the printed marks of these two walls not read), RULE_DIFFERENCE on the remaining metres (centreline to the node vs
   his face-to-face pieces: about t / 2 per T-junction).
3. 1F: all walls agree within 0.44 m (0.4 %); partitions 57.05 vs 57.14 m. No verdict needed beyond the 0.20 split
   (as 2).
4. 2F external +1.05 m: he takes the block's outer dimensions 6.80 and 8.18 for two sides (area plan 8.10 x 6.80), we
   take centrelines (7.90, 6.625 less columns): RULE_DIFFERENCE (UP-WALL-GEOM-001 centreline). The 2F neighbour-side wall is drawn
   0.15 (faces 0.150 apart) and printed "15" on the scanned 2F plan, not 0.20: ENGINE_RIGHT on thickness.
5. Parapets: ground + first roof together agree within 0.30 m (108.55 vs 108.85), but he splits them 66.00 / 42.85
   where the plans give 59.31 / 49.24: RULE_DIFFERENCE in allocation (UNRESOLVED which roof the 6.4-6.7 m belongs to).
   Thickness: every parapet band on the DXF plans is 0.20 m apart, he books them under 15 cm: ENGINE_RIGHT on the drawing
   (proposal); but the scanned 2F plan prints "30" at one first-roof corner: UNRESOLVED there until the verifier re-reads
   the first-roof edge marks.
6. Fence -9.17 m: his 37.20 m = the north fence outer face 31.37 (printed plot length) + the street-side solid part
   5.80 (fence plan prints 580 + 250 gate); our centreline is north 31.17 + street side 8.20 (2.50 gate inside) + a
   sea-side fence 7.00 m (1.00 gate) that the GF plan draws as a 0.20 band and for which he has no row: proposal
   UNRESOLVED (the sea-side fence is not on the fence plan, page 12 shows the street side only; its material and height
   are not printed on the plan), RULE_DIFFERENCE for outer face vs centreline (0.20 m) and gate not deducted (2.50 m).
7. Top-roof parapet 29.80 m (his) = the outer perimeter of the printed 8.10 x 6.80 block; the centreline needs the
   parapet thickness, which no plan draws: HELD, not a difference.

## What was learned, what is missing

- Learned: the freelancer measures exactly the pieces between columns that a centreline graph minus columns gives
  (57 rows to the centimetre), so a masonry run "per piece between columns" is the matching unit for the scoreboard;
  his "external" section has no thickness and his 15 cm section also carries the parapets and the fence.
- Learned: on this drawing the wall layer holds only 0.15 and 0.20 walls; parapets sit on a separate layer (0.20 bands);
  a glazed wall line is drawn as a 0.20 band filled with window lines, so "opening not deducted" must be shown with the
  glazed length beside it or a full-height glass line becomes block metres.
- For T-027 (engine piece): accept against this table per floor and thickness (gross centreline, columns, gross minus
  columns), the curved annex corner (r 1.20, 1.885 m), the 1F concave bay (r 2.035, 103.4 deg, 3.672 m with 3.136 m
  glazing), the 0.15 / 0.20 thickness change in one wall line (1F stair west wall), and the held 0.40 band.
- Missing: the fence section (page 12, height 215 + 50 per T-063) not re-read for material; the 2F scanned plan
  (pages 05-06) not re-read for the 0.15 south wall; block m2 / m3 wait on owner Q-60; printed opening widths are in
  T-083, our gap widths are drawn widths; the east ground-roof parapet carries a 0.05 m railing line (not block).
- Verifier: re-measure the 2F plan's 0.20 walls (4 external-and-core runs: north 7.90, east 6.625, west 6.625, lift
  2 x 2.00 and stair 5.20 / 3.425) on the Drive DXF.

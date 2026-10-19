# T-074: hand table of every Alsenan waterproofed area (the truth for the membrane table)

Worker 3, 2026-10-19 (run 16:00-17:00 UTC). Development villa (Alsenan), NOT an accuracy claim. Areas, lengths and counts
only: no coordinates, no client data. Read from Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip (P7757.dxf,
sha256 ab54dd55...31cc4, same file as T-010 / T-071), single sheets p7757_arch_sheet03.pdf (ground floor plan) and
p7757_arch_sheet04.pdf (first floor plan), Alsenan_Architectural_P7757_Pages_05-06 (second floor plan, page 5),
Pages_01-02 (area sheets) and sanitary-7757.pdf (three drainage plans). Freelancer: his FIN workbook sheet "العازل",
rows 14-36, as parsed in `tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json` (the 23.6 MB workbook itself is over the
Drive download limit; the parsed rows are the same cells).

Rules used and nothing else: UP-WP-001 (floor m2), UP-WP-002 v2.0.0 (upturn = whole boundary incl. every doorway /
threshold segment x 0.20 m), UP-WP-003 v1.1.0 (doorway floor piece = door width x wall depth), UP-WP-005 (strips of the
roll, 0.10 m lap, never a flat rate), UP-WET-001 (wet codes incl. pantry and laundry), UP-QTY-STATUS-001; owner answers
Q-03 (0.20 m), Q-06 (basin-only spaces wet), Q-13 (label first, sanitary drawing second), Q-24 + addendum (roofs like a
bathroom, whole strips), Q-25 (gaps closed by the membrane), Q-29 (dome positions are open skylights), Q-30 (kitchens
like a bathroom; his 3 x 4 m kitchen is the strip method). UP-WP-LAY-001, UP-WP-MAT-001 and UP-WP-ROOF-001 are not in
`rules/` on the working head (searched `rules/**/*.json`): the strip method below is the owner's Q-30 example only.

## 1. How each outline was read (two independent ways, no engine code)

1. My own polygonization (scratchpad script, ezdxf + shapely only, no engine module): the wall layer `1`, window layer
   `W`, column outlines, the two jamb-face lines of every door block and the lines of the opening blocks, endpoint gaps up
   to 60 mm bridged; the face holding each room tag (WC, bath, WASH, kit, laun) is the room. 14 of the 17 wet rooms close
   this way.
2. Three rooms are open to a neighbour (no door on one side), so I traced their wall faces line by line from the DXF:
   the basin space by the stair (1.35 x 1.10), the two-basin lobby of the core (10 edges, closed on the line of the lobby
   wall end across a 1.256 m open edge) and the master bathroom (2.10 x 2.00 less the diagonal wall's corner). Check: the
   same polygonization with layer `2` (zone lines) closes the lobby at 4.7307 m2 / 9.4989 lm (my trace 4.7321 / 9.5002,
   0.03 %) and the basin space at 1.485 / 4.90 (identical).
3. Every room was then checked against the printed dimensions of the PDF plan (sheet 3, sheet 4, sheet 5): 150 x 210,
   150 x 225, 130 x 150, 300 x 270 + 105 x 150, 175 x 135, 110 x 135, 210, 245 x 205 (twice), 300 / 347 / 185, 180 x 147,
   210 x 225, 300 x 185 all agree with the drawn outline (column notches and piers aside, listed per row).
Wet / dry: architectural label first, drainage plan second (Q-13); every row below has a drain or a WC / basin on the
drainage plan of its floor.

## 2. The table (one row per waterproofed area)

Strips: n: width x length (m) of each strip, cut membrane, rolls if the area were done alone, offcut. "along x" = strips
parallel to the room's longest wall, "along y" = across it; no rule fixes the direction, so both are given. Doorways:
width in m; * = the doorway is shared with another wet room (see section 5). Strip length = the outline's extent inside the strip's
band + 0.20 + 0.20; where a band crosses a notch (laundry: the W.C. corner) the strip runs through it and the piece over
the notch is cutting waste, so a cutting plan that cuts round the notch can be shorter.

| Floor | Area as printed | Floor m2 | Boundary lm | Upturn m2 (x 0.20) | Doorways | Strips along x | Strips along y | Freelancer m2 / lm | Floor diff | Verdict proposal |
|---|---|---|---|---|---|---|---|---|---|---|
| GF | WASH / مغسلة (by the dewaneya) | 3.1325 | 7.2 | 1.44 | 0.80* | 2: 1.00x2.50 + 1.00x2.50; cut 5.000, 1 roll(s), offcut 5.000 | 3: 1.00x1.90 + 1.00x1.90 + 0.70x1.90; cut 5.130, 1 roll(s), offcut 4.870 | 3.15 / 7.2 | -0.018 (-0.6 %) | RULE_DIFFERENCE |
| GF | W.C. / مرحاض (by the dewaneya) | 3.375 | 7.5 | 1.5 | 0.80* | 2: 1.00x2.65 + 1.00x2.65; cut 5.300, 1 roll(s), offcut 4.700 | 3: 1.00x1.90 + 1.00x1.90 + 0.85x1.90; cut 5.415, 1 roll(s), offcut 4.585 | 3.37 / 7.5 | +0.005 (+0.1 %) | AGREE |
| GF | W.C. / مرحاض (driver) | 1.95 | 5.6 | 1.12 | 0.80 | 2: 1.00x1.90 + 0.80x1.90; cut 3.420, 1 roll(s), offcut 6.580 | 2: 1.00x1.70 + 1.00x1.70; cut 3.400, 1 roll(s), offcut 6.600 | 1.95 / 5.58 | +0.000 (+0.0 %) | ENGINE_RIGHT |
| GF | KITCHEN / مطبخ | 9.63 | 14.5 | 2.9 | 1.00 | 4: 1.00x4.90 + 1.00x4.90 + 1.00x3.40 + 0.40x3.40; cut 14.560, 2 roll(s), offcut 5.440 | 6: 1.00x1.45 + 1.00x3.10 + 1.00x3.10 + 1.00x3.10 + 1.00x3.10 + 0.40x3.05; cut 15.070, 2 roll(s), offcut 4.930 | 9.55 / 14.35 | +0.080 (+0.8 %) | ENGINE_RIGHT |
| GF | W.C. / مرحاض (stair core, 175 x 135) | 2.3625 | 6.2 | 1.24 | 0.80* | 2: 1.00x2.15 + 0.85x2.15; cut 3.978, 1 roll(s), offcut 6.022 | 3: 1.00x1.75 + 1.00x1.75 + 0.35x1.75; cut 4.112, 1 roll(s), offcut 5.888 | 2.36 / 6.2 | +0.003 (+0.1 %) | AGREE |
| GF | basin space by the stair (110 x 135, no label) | 1.485 | 4.9 | 0.98 | 0.80* | 2: 1.00x1.75 + 0.60x1.75; cut 2.800, 1 roll(s), offcut 7.200 | 2: 1.00x1.50 + 0.85x1.50; cut 2.775, 1 roll(s), offcut 7.225 | 1.7 / 5.3 | -0.215 (-12.7 %) | RULE_DIFFERENCE |
| GF | W.C. / مرحاض (core, 289 x 167) | 2.6752 | 7.414 | 1.4828 | 0.80* | 3: 1.00x2.00 + 1.00x3.29 + 0.27x3.29; cut 6.158, 1 roll(s), offcut 3.842 | 4: 1.00x1.64 + 1.00x2.06 + 1.00x1.59 + 0.59x0.69; cut 5.699, 1 roll(s), offcut 4.301 | 2.67 / 7.4 | +0.005 (+0.2 %) | AGREE |
| GF | W.C. / مرحاض (core, 245 x 167) | 2.3676 | 6.8098 | 1.362 | 0.80* | 3: 1.00x1.87 + 1.00x2.77 + 0.30x2.77; cut 5.453, 1 roll(s), offcut 4.547 | 3: 1.00x2.10 + 1.00x1.89 + 0.96x1.06; cut 5.019, 1 roll(s), offcut 4.981 | 2.3 / 6.7 | +0.068 (+2.9 %) | ENGINE_RIGHT |
| GF | Wash / مغسلة (core lobby, 2 basins) | 4.7321 | 9.5002 | 1.9 | 0.80* + 0.80* | 4: 1.00x2.45 + 1.00x3.13 + 1.00x2.54 + 0.61x1.02; cut 8.737, 1 roll(s), offcut 1.263 | 4: 1.00x2.04 + 1.00x2.94 + 1.00x3.31 + 0.70x1.20; cut 9.133, 1 roll(s), offcut 0.867 | 4.73 / 9.5 | +0.002 (+0.0 %) | AGREE |
| GF | BATH / حمام (master bed room) | 3.7173 | 7.6245 | 1.5249 | 0.80 | 3: 1.00x2.32 + 1.00x2.50 + 0.60x2.50; cut 6.317, 1 roll(s), offcut 3.683 | 3: 1.00x2.22 + 1.00x2.40 + 0.70x2.40; cut 6.298, 1 roll(s), offcut 3.702 | 3.7 / 7.6 | +0.017 (+0.5 %) | AGREE |
| 1F | BATH / حمام (west, upper) | 5.0225 | 9.0 | 1.8 | 0.80 | 3: 1.00x2.85 + 1.00x2.85 + 0.65x2.85; cut 7.553, 1 roll(s), offcut 2.447 | 4: 1.00x2.45 + 1.00x2.45 + 1.00x2.45 + 0.15x2.45; cut 7.718, 1 roll(s), offcut 2.282 | 5.0 / 9.0 | +0.022 (+0.5 %) | ENGINE_RIGHT |
| 1F | BATH / حمام (west, lower) | 5.0225 | 9.0 | 1.8 | 0.80 | 3: 1.00x2.85 + 1.00x2.85 + 0.65x2.85; cut 7.553, 1 roll(s), offcut 2.447 | 4: 1.00x2.45 + 1.00x2.45 + 1.00x2.45 + 0.15x0.40; cut 7.410, 1 roll(s), offcut 2.590 | 5.0 / 8.9 | +0.022 (+0.5 %) | ENGINE_RIGHT |
| 1F | LAUNDRY / غسيل | 10.151 | 16.94 | 3.388 | 0.90 + 0.80* | 5: 1.00x3.40 + 1.00x3.40 + 1.00x5.40 + 1.00x3.45 + 0.27x3.45; cut 16.581, 2 roll(s), offcut 3.419 | 6: 1.00x2.25 + 1.00x2.25 + 1.00x3.87 + 1.00x3.87 + 1.00x1.87 + 0.90x1.82; cut 15.748, 2 roll(s), offcut 4.252 | 10.0 / 16.85 | +0.151 (+1.5 %) | ENGINE_RIGHT |
| 1F | W.C. / مرحاض (by the laundry) | 2.646 | 6.54 | 1.308 | 0.80* | 2: 1.00x2.20 + 0.97x2.20; cut 4.334, 1 roll(s), offcut 5.666 | 3: 1.00x1.87 + 1.00x1.87 + 0.40x1.87; cut 4.488, 1 roll(s), offcut 5.512 | 2.59 / 6.48 | +0.056 (+2.2 %) | ENGINE_RIGHT |
| 1F | BATH / حمام (by the laundry) | 3.5775 | 7.6 | 1.52 | 0.80 | 3: 1.00x2.40 + 1.00x2.40 + 0.40x2.40; cut 5.760, 1 roll(s), offcut 4.240 | 3: 1.00x2.20 + 1.00x2.20 + 0.60x2.15; cut 5.690, 1 roll(s), offcut 4.310 | 3.6 / 7.6 | -0.022 (-0.6 %) | AGREE |
| 1F | BATH / حمام (east, 210 x 225) | 4.725 | 8.7 | 1.74 | 0.80 | 3: 1.00x2.65 + 1.00x2.65 + 0.70x2.65; cut 7.155, 1 roll(s), offcut 2.845 | 3: 1.00x2.50 + 1.00x2.50 + 0.85x2.50; cut 7.125, 1 roll(s), offcut 2.875 | 4.72 / 8.7 | +0.005 (+0.1 %) | AGREE |
| 2F | W.C. / مرحاض (roof floor) | 5.55 | 9.7 | 1.94 | 0.80 | 3: 1.00x3.40 + 1.00x3.40 + 0.45x3.40; cut 8.330, 1 roll(s), offcut 1.670 | 4: 1.00x2.25 + 1.00x2.25 + 1.00x2.25 + 0.70x2.25; cut 8.325, 1 roll(s), offcut 1.675 | 5.62 / 9.75 | -0.070 (-1.2 %) | ENGINE_RIGHT |
Hand check per row (the ENGINE_RIGHT proposals rest on these, never on engine output):

- GF WASH / مغسلة (by the dewaneya): printed 150 x 210 = 3.150; the drawn wall face steps round a 0.0175 m2 column corner (drawing wins on the outline); same boundary 7.20.
- GF W.C. / مرحاض (by the dewaneya): printed 150 x 225 = 3.375, 2 x (1.50 + 2.25) = 7.50; freelancer rounds 3.37.
- GF W.C. / مرحاض (driver): printed 130 x 150 = 1.950; boundary 2 x (1.30 + 1.50) = 5.60 lm, freelancer 5.58.
- GF KITCHEN / مطبخ: printed 300 x 270 + entrance 105 x 150 = 8.100 + 1.575 = 9.675, less two drawn piers 0.05 x 0.50 and 0.05 x 0.40 = 9.630; freelancer 9.55 / 14.35 has no formula (typed).
- GF W.C. / مرحاض (stair core, 175 x 135): printed 175 x 135 = 2.3625.
- GF basin space by the stair (110 x 135, no label): printed 110 x 135 = 1.485; freelancer 1.55 x 1.10 = 1.705 takes the 0.20 m passage reveal into the room (threshold item, UP-THR-001; verifier verdict on T-010).
- GF W.C. / مرحاض (core, 289 x 167): wedge room, shoelace on the drawn wall faces 2.675; freelancer 2.67 / 7.4.
- GF W.C. / مرحاض (core, 245 x 167): wedge room, shoelace on the drawn wall faces 2.368 m2 / 6.810 lm; freelancer 2.30 / 6.70 (typed, no formula).
- GF Wash / مغسلة (core lobby, 2 basins): 10-edge outline closed on the line of the lobby wall end (1.256 m open edge, no wall): 4.732 / 9.500; freelancer 4.73 / 9.50 (his row is titled "dewaneya wash").
- GF BATH / حمام (master bed room): 2.10 x 2.00 = 4.200 less the 0.982 x 0.983 corner cut by the diagonal wall (0.483) = 3.717; freelancer 3.70 / 7.60.
- 1F BATH / حمام (west, upper): printed 245 x 205 = 5.0225 m2, 2 x (2.45 + 2.05) = 9.00 lm; freelancer 5.00.
- 1F BATH / حمام (west, lower): printed 245 x 205 = 5.0225 m2, 9.00 lm; freelancer 5.00 / 8.90.
- 1F LAUNDRY / غسيل: printed 347 x 300 and 185, the W.C. (180 x 147) cuts the corner: 1.85 x 3.00 + 1.62 x 1.05 + 1.47 x 1.20 + 1.42 x 0.80 = 5.550 + 1.701 + 1.764 + 1.136 = 10.151 m2, boundary 16.94 lm; freelancer 10.00 / 16.85 typed with no formula.
- 1F W.C. / مرحاض (by the laundry): printed 180 x 147 = 2.646, 2 x (1.80 + 1.47) = 6.54; freelancer 2.59 / 6.48 = 1.80 x 1.44 (3 cm short).
- 1F BATH / حمام (by the laundry): 2.00 x 1.80 less a 0.45 x 0.05 jamb = 3.5775; freelancer 3.60 rounded.
- 1F BATH / حمام (east, 210 x 225): printed 210 x 225 = 4.725.
- 2F W.C. / مرحاض (roof floor): printed 300 x 185 = 5.550, 2 x (3.00 + 1.85) = 9.70 (sheet 5); freelancer 5.62 / 9.75 = 3.00 x 1.875.

## 3. Totals per floor and project, against the freelancer

| Floor | Areas | Floor m2 (hand) | Freelancer m2 | Diff | Boundary lm (hand) | Freelancer lm | Diff |
|---|---|---|---|---|---|---|---|
| Ground | 10 | 35.427 | 35.48 | -0.053 m2 (-0.15 %) | 77.249 | 77.33 | -0.08 lm |
| First | 6 | 31.145 | 30.91 | +0.235 m2 (+0.76 %) | 57.780 | 57.53 | +0.25 lm |
| Second (roof floor) | 1 | 5.550 | 5.62 | -0.070 m2 (-1.25 %) | 9.700 | 9.75 | -0.05 lm |
| **Project** | **17** | **72.122** | **72.01** | **+0.112 m2 (+0.16 %)** | **144.729** | **144.61** | **+0.12 lm (+0.08 %)** |

Line by line (17 matched lines, no line without a partner on either side): sum |diff| = 0.762 m2 (WAPE 1.06 %) on
floor and 1.019 lm (0.70 %) on boundary; verdict proposals: 7 AGREE (within rounding), 8 ENGINE_RIGHT (printed size or
drawn outline by hand), 2 RULE_DIFFERENCE (column notch; passage reveal), 0 FREELANCER_RIGHT, 0 UNRESOLVED.
Derived items (hand, rules above): upturn 144.729 x 0.20 = 28.946 m2; floor + upturn surface 101.067 m2; doorway floor
pieces 2.42 m2 counted per room (1.82 m2 if each doorway is counted once, section 5). The freelancer lists the floor m2
and the boundary lm only (no upturn m2, no doorway piece, no rolls).

**Second independent sum.** (a) Outlines (section 1, own polygonization + hand traces): 72.1217 m2 / 144.7285 lm.
(b) Printed dimensions where a room is a printed rectangle (section 2 hand checks), drawn outline for the wedge rooms,
the lobby, the master bathroom and the laundry: 72.122 + 0.0175 (dewaneya wash notch) + 0.045 (kitchen piers) =
72.184 m2. (c) The verifier's reproduction of the T-010 engine piece (WET_ROOM_EVIDENCE_V1 on ARCH_TAKEOFF_V2.9 faces,
board T-010 row): 72.121 m2 / 144.727 lm, 17 wet spaces: the same 17 areas, floor within 0.001 m2, boundary within
0.002 lm. My outlines used no engine code, so (a) and (c) are independent readings of the same drawing.

**Membrane (strips, owner's method).** Cut membrane, sum over the 17 areas: 118.989 m2 with strips along x, 118.555 m2
along y, 116.951 m2 taking the smaller direction in each room. Rolls if each area were done alone: 19 (either
direction; every area needs at least 1 roll). Lower bound with every offcut reused: ceil(116.951 / 10) = 12 rolls. The
real purchase lies between 12 and 19 and comes from the engine's cutting plan with offcut reuse across areas (T-072);
this table gives every strip so that plan can be checked strip by strip.

## 4. The earlier -19.1 % wet-area gap, explained

The -19.1 % (SCOREBOARD "Wet-area waterproofing", handoff 16.3; `research/external_engine_lab/V3C_FORENSIC_ACCURACY_DONOR_AUDIT.md`)
was an older engine run: 58.237 m2 against the freelancer's 72.01 m2 on the same 17 rows. Per room, from this table:
- the three basin-only spaces were REVIEW (no waterproofing) until owner Q-06 made them wet: core lobby 4.732 +
  dewaneya wash 3.133 + basin space by the stair 1.485 = 9.350 m2. ARCH_TAKEOFF_V2.9 without them gives 72.122 - 9.350 =
  62.77 m2 (-12.8 %), which is the V2.9 figure in the T-010 handoff;
- the remaining 62.77 - 58.24 = 4.53 m2 between that older run and V2.9 is NOT reproducible here (the older method is not
  re-run in this task; the audit names "the missing 1F baths"; one 1F bath is 4.725 m2, but that is not proven).
With every wet area present (17 of 17 on the drainage plans, 0 lost), the hand table is +0.16 % on floor area.

## 5. Findings the membrane table must handle

1. **Doorways between two wet rooms (5 on Alsenan).** dewaneya wash <-> W.C. (0.80), stair W.C. <-> basin space (0.80),
   core lobby <-> each of the two wedge W.C.s (0.80 + 0.80), laundry <-> its W.C. (0.80). UP-WP-002 v2 puts every
   doorway segment in the boundary of the room, so each of these 0.80 m segments is in TWO room boundaries: 5 x 0.80 x 2
   = 8.00 lm of the 144.73 lm (1.60 m2 of upturn), and the doorway floor piece 0.12 m2 twice (0.60 m2). The membrane is
   continuous across such a doorway, so there is nothing to turn up against; no rule says which count applies:
   owner question Q-35. The freelancer's 144.61 lm counts full room perimeters (both sides), like today's sum.
2. **Open edges (no wall, no door) in a boundary: 2.156 m.** Core lobby 1.256 m (open to the stair hall) and basin
   space by the stair 0.90 m (open to the passage). UP-WP-002 v2 counts the whole boundary "including every doorway /
   threshold segment", so they are in the 144.73 lm (0.431 m2 of upturn); they are thresholds, not walls.
3. **Strip direction matters little here**: the largest difference between the two directions is 0.833 m2 (laundry,
   16.581 vs 15.748 m2), then the kitchen (14.560 vs 15.070) and the two wedge W.C.s (0.46 and 0.43 m2); no area changes
   its roll count. The owner's own kitchen gives 16.28 m2 one way and 16.32 m2 the other (both 2 rolls).
4. **The owner's 3 m x 3 m bathroom picture** (Q-24 addendum) shows 3 strips x 3.20 m = 9.60 m2, 1 roll. His own Q-30
   method on the same room gives 4 strips (1.00, 1.00, 1.00, 0.70) x 3.40 m = 12.58 m2, 2 rolls by area: the picture
   leaves out the 0.20 m upturn on all four walls and the laps. Reported for the Lead; the Q-30 worked example is the
   later and fuller answer and is the method used here.
5. **Rolls "by area" vs "by strip length".** The owner counts rolls as ceil(cut m2 / 10 m2). A strip narrower than the
   roll is still cut from a 1.00 m roll, so by roll LENGTH the 2F W.C. along y needs 3 x 3.40 = 10.20 m of roll = 2 rolls,
   while by area (8.33 m2) it needs 1. The engine cutting plan decides with offcut reuse (UP-WP-005); no rule tells which
   count the single-room "rolls if alone" column shows.

## 6. Areas that are NOT measured wet rows (held or not a membrane row, never 0)

| Area | Status | Why | What is known |
|---|---|---|---|
| GF pantry (تحضير / PANTRY, floor drain on the drainage plan) | HELD | wet by UP-WET-001 (pantry) and Q-30 (kitchens), but it has no wall on the dining side: printed 4.50 x 3.00 with the dining room continuing past it (sheet 3), so the outline that bounds the membrane is not drawn | printed 4.50 x 3.00 = 13.50 m2 if bounded at the printed 3.00; the freelancer has no pantry line; owner question Q-36 |
| 1F west roof (+4.30) | MEASURED (T-071, not wired) | Q-24: inside the parapet, like a bathroom | 55.559 m2, upturn 35.727 lm (incl. 0.200 m gap closure, Q-25) |
| 1F south-east roof strip (+5.50) | MEASURED (T-071, not wired) | same | 32.721 m2, upturn 52.940 lm (incl. 0.405 m gap closure) |
| 2F level roof (+9.70) with two skylight openings (Q-29) | MEASURED (T-071, not wired) | same; the two dome positions are open skylights with a 0.20 m upturn ring | 146.532 - 2 x 15.350 = 115.832 m2, upturn 92.922 lm (incl. 2 x 13.891 rings) |
| 2F block's own top roof (+13.90) with the third dome | HELD | on no plan sheet; outline question Q-34 (verifier) | not measured |
| 1F void parapet strip (6.130 m2 behind the 0.20 m parapet, no ROOF label) | HELD | no label says it is a roof | 6.130 m2 (T-071) |
| Balconies / terraces | none on the plans read (sheets 3, 4, 5) | - | - |
| Pool | not a membrane row | no Urban rule makes the pool a membrane area (T-071: HELD POOL_NO_MEMBRANE_RULE) | - |
| Skylight closure over the dome openings | HELD | Q-29: what closes the opening is not specified | - |

Roofs against the freelancer ("عازل اسطح و ملاحق" 285 m2, "نعلات العازل الاسطح" 194 lm): the three plan roofs give
204.112 m2 (-80.888 m2, -28.4 %) and 181.589 lm (-12.411 lm, -6.4 %); the gap is mostly the held 2F top roof (Q-34),
so the roof verdict stays UNRESOLVED (T-071). The strip layout of the three roofs is NOT made in this run: their
outlines (parapet inner face with the Q-25 closures) were measured by T-071's piece and by T-062's hand trace, but my
own polygonization did not rebuild them independently (layer `5` faces came out on the outer parapet face, 61.85 m2 for
the west roof), and I do not lay strips on an outline I have not rebuilt. The engine cutting plan of T-072 on the T-071
outlines is the next check.

## 7. What this table is for, and what is missing

- For T-072 (engine membrane table): every wet row above with its floor m2, boundary lm, doorways and both strip
  layouts is the hand truth; the engine's rows should match the floor and boundary to 0.01 and its strips to the
  layout given (or report where its cutting plan differs and why).
- Strip helper: `research/agents_t074/strip_layout.py` states the method (the owner's Q-30 example) and self-tests it:
  the owner's 3 x 4 kitchen (16.28 m2, 2 rolls, 3.72 m2 offcut) and the other direction (16.32 m2), the same room rotated
  37 degrees, mirrored and in mm, the 3 x 3 bathroom (12.58 m2), an L-shape, a 0.50 m wide strip. The scratchpad copy that
  built the table gave identical strips for all 17 rooms (checked).
- Missing: roof strip layouts (section 6); the doorway / shared-doorway count (Q-35) and the pantry (Q-36) wait on the
  owner; corner reinforcement and drain detailing are outside the owner's method.

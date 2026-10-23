# T-209: wet-room wall tiles m2 room by room, owner manual and drawing-derived methods, window deductions from the census

Worker 2, 2026-10-23. Lane A, gate 2. Development villa (Alsenan) + a non-Alsenan fixture. Research piece, unwired: no
released or candidate quantity changes. ERS read; sections 2 (steps 1-4), 3 (physical vs convention, build before
deduct) and 4 applied.

## 1. The physical element and the rules

Element: porcelain / ceramic wall tile on the inner wall faces of each wet room (UP-FIN-WALL-001 full height), from the
finished floor to the underside of the decor ceiling (owner Q-48 A), less what is physically not wall: door openings
(width x door head), windows (only the part inside the tiled band), open sides with no wall. Installed m2 only; tile
pieces, boxes and offcuts are procurement (Q-59, not here). Rules: Q-48 A (height), G1 / G2 (OWNER_RECONCILIATION
2026-10-20: owner manual heights kept, annex 3.15 PROVISIONAL / HELD), Q-52 C modified (drawing-derived height per
room), Q-55 C (door head 2.20 where none is printed), Q-73 / T-175 (full openings deducted, subject to physical scope),
UP-CER-005 (wall ceramic = eligible wall less openings), Q-45 B / G4 (wall mortar 2 cm 1:4, owner 8 bags + 1.10 m3 sand
per m3, theory 7.66 bags + 1.06 m3 beside, 5 % waste in its own column), Q-45 (adhesive 20 kg per 5 m2), Q-06 / Q-37
(basin spaces and the pantry are wet).

First the merged ledgers (WORKFLOW_CONTROLS s.10.5): T-086 had wet-wall m2 only as a HELD candidate (Q-52 then open);
T-128 r3 (MERGED a6ac2c66) carries the wet rooms by both methods but with 10 of 13 window nets HELD ("height not
printed"). Since then T-201 (MERGED 5dade783) bound every wet-room window to the vector elevations / section A-A, and
T-206 (MERGED d5df7d1f) found the sunken wet-slab panels. This task re-derives the wet-wall line on those, builds it
room by room with materials, and reconciles it to T-128 and to the freelancer.

Formula (`wet_wall_tiles.py`, any villa): gross = face x H; door = w x min(head, H); window = w x max(0, min(head, H) -
max(sill, 0)); net = gross - doors - windows. A missing face, height or opening datum keeps the room HELD (a range where
only one opening is unknown); never 0. Unit guard: H > 8 m or a face > 500 m is refused as a millimetre input.

## 2. Inputs (all from merged pieces; `ALSENAN_T209_INPUT.json`)

- Face = walked contour - open sides (T-128 r3 walk, checker 3 rooms 0.0 %; contours = T-074 within 0.012 m). Open
  sides: pantry 4.49 m to the dining, wash lobby 1.245 m to the stair hall: no wall, no tile.
- Doors: T-128 r3 one width per door (D315 0.80 / 0.75, D120 0.95 / 1.00, d220 0.90); heads not printed -> 2.20 m
  ASSUMED - OWNER-APPROVED (Q-55 C). Two openings with no leaf and no printed head (dewaneya wash arch 1.00, basin-space
  doorway P-GF-01 0.90): no fallback applies -> range.
- Windows (T-201, DRAWING-CONFIRMED drawn geometry): W06 / W07 / W19-W23 / W28 0.60 x 0.80, sill 1.70, head 2.50 above
  the room's FFL; W08 kitchen 1.50, sill 1.00 / head 2.50 above +0.30; W09 1.50 and W10 1.00 pantry, sill 1.00 / head
  2.50 above +1.00; W18 0.50, sill 0.84 / head 3.00 PRINTED (NW chain 84 / 216). Every head is below every tile line
  (2.50 / 3.00 < 3.15), so each window is deducted whole in both methods. W05 (GF W.C. 175 x 135): absolute +2.70 /
  +3.50, but the room's floor level is not drawn -> HELD with the room.
- Window host W06: in the 245 x 167 wedge W.C. (GF-13), not the 289 x 167 one. T-128 r2 found it on the walk; checked
  again here on the DXF (the two 0.60 W bands on that wall line lie at the GF-10 and GF-13 faces; the GF-12 seed is
  1.33 m from the nearest band). The census rows T-198 / T-175 still name "wedge A" (label carried from T-144): FEEDBACK
  for the Lead, no window quantity moves.

## 3. Heights: owner manual (A) beside drawing-derived (B), and what is new

| Rooms | A owner manual (G1) | B drawing-derived (T-128 r3 basis) | B status after T-209 |
|---|---|---|---|
| GF main: pantry, 2 wedge W.C.s, wash lobby, master bath | 4.50 - 0.60 - 0.15 - 0.10 = 3.65, ASSUMED - OWNER-APPROVED | 4.50 - 0.16 - b(0 .. 0.10) - 0.15 = 4.09 .. 4.19 | **HELD for all five** (sunken panel above, below) |
| GF annex: dewaneya wash, W.C., driver W.C., kitchen | 3.15 OWNER MANUAL METHOD - PROVISIONAL, HELD (G2) | 3.59 .. 3.69 | HELD (roof datum, DCR-6) |
| GF W.C. 175 x 135 + basin space 110 x 135 | HELD (level +0.30 / +1.00 not drawn, T-088) | HELD | HELD |
| 1F: 2 west baths, laundry, W.C., bath by the laundry, east bath | 4.20 - 0.85 = 3.35, ASSUMED - OWNER-APPROVED | 3.79 .. 3.89 | **1F W.C. 147 x 180 DRAWING-CONFIRMED (bounded)**; laundry HELD (new), the rest HELD (roof datum) |
| 2F W.C. 300 x 185 | 3.35 | 3.79 .. 3.89 | HELD (roof datum) |

NEW (propagating T-206 to the wet-wall line): `sunken_overlay.py` puts each room region (T-128 walk = T-147 regions)
on the structural slab plan ABOVE it with the T-147 column translation (all columns matched, spread 0.00 m) and
intersects the six "Sunken slab." hatches (S-HAT.BAT 275 / 276 / 280 / 287 / 298, 5BF). Under a sunken panel: pantry
5.26 m2 (39 %), wedge W.C. 289 x 167 0.73 (27 %), wedge W.C. 245 x 167 1.93 (82 %), wash lobby 0.36 (8 %), GF master
bath 2.24 (49 %), 1F laundry 5.40 (53 %, under the 2F W.C. panel 5BF); the open dining 3.49 (3 %). The drop is printed
nowhere, and whether the panel drops at full thickness (soffit lower) or is thinned is not printed either (T-206), so
the decor-ceiling level over these rooms is not established: drawing-derived height HELD (WRONG_REFERENCE), the T-128
value is only an upper bound (a sunken panel can lower the soffit, never raise it). Three GF rooms (wedge 289, wedge 245,
wash lobby) and the 1F laundry were DRAWING-CONFIRMED (bounded) in T-128 and move to HELD; method A is not affected.
Registration check (same translation, opposite way): each 1F wet room's own floor sits on a panel (W.C. 147 x 180 97 %,
west lower bath 99 %, bath by the laundry 93 %, east bath 87 %, west upper 50 %), the laundry on none (T-206: drain
but no hatch), the 2F W.C. 97 %: the overlay reproduces T-206's sanitary-sheet registration independently.
Two further B causes already named: B27 0.85 crosses the pantry and B11 0.75 the wash lobby (Q-52 C: the ceiling must
pass under a crossing beam that projects below the intended plane; no bulkhead drawn).

## 4. Results per room (m2; `WET_WALL_TILES_T209.csv`)

| Room | Face m | A H | A gross | doors | windows | **A net** | A status | B net | Freelancer (lm x 3.00) |
|---|---|---|---|---|---|---|---|---|---|
| GF dewaneya wash | 7.20 | 3.15 | 22.68 | 1.76 + arch | 0 | 17.77 .. 20.92 | HELD (G2; arch head) | HELD | 21.60 |
| GF dewaneya W.C. | 7.50 | 3.15 | 23.63 | 1.76 | 0 | 21.87 | HELD (G2) | HELD | 22.50 |
| GF driver W.C. | 5.60 | 3.15 | 17.64 | 1.76 | 0 | 15.88 | HELD (G2) | HELD | 16.74 |
| GF kitchen | 14.50 | 3.15 | 45.68 | 2.09 | 2.25 | 41.34 | HELD (G2) | HELD | 43.05 |
| GF pantry | 10.49 | 3.65 | 38.29 | 2.20 | 3.75 | **32.34** | ASSUMED - OWNER-APPROVED | HELD | no row |
| GF W.C. 175 x 135 | 6.20 | - | - | 1.76 | W05 0.48 | HELD | level | HELD | 18.60 |
| GF basin space 110 x 135 | 4.90 | - | - | 1.76 + doorway | 0 | HELD | level | HELD | 15.90 |
| GF wedge W.C. 289 x 167 | 7.414 | 3.65 | 27.06 | 1.76 | 0 | **25.30** | ASSUMED - OWNER-APPROVED | HELD (new) | 22.20 |
| GF wedge W.C. 245 x 167 | 6.81 | 3.65 | 24.86 | 1.76 | 0.48 | **22.62** | ASSUMED - OWNER-APPROVED | HELD (new) | 20.10 |
| GF wash lobby | 8.267 | 3.65 | 30.17 | 3.52 | 0 | **26.65** | ASSUMED - OWNER-APPROVED | HELD (new) | 28.50 |
| GF master bath | 7.625 | 3.65 | 27.83 | 1.76 | 0.48 | **25.59** | ASSUMED - OWNER-APPROVED | HELD | 22.80 |
| 1F bath west upper | 9.00 | 3.35 | 30.15 | 1.76 | 0.48 | **27.91** | ASSUMED - OWNER-APPROVED | HELD | 27.00 |
| 1F bath west lower | 9.00 | 3.35 | 30.15 | 1.76 | 0.48 | **27.91** | ASSUMED - OWNER-APPROVED | HELD | 26.70 |
| 1F laundry | 16.94 | 3.35 | 56.75 | 3.74 | 0.48 | **52.53** | ASSUMED - OWNER-APPROVED | HELD (new) | 50.55 |
| 1F W.C. 147 x 180 | 6.54 | 3.35 | 21.91 | 1.76 | 0.48 | **19.67** | ASSUMED - OWNER-APPROVED | **22.55 .. 23.20 DRAWING-CONFIRMED** | 19.44 |
| 1F bath by the laundry | 7.60 | 3.35 | 25.46 | 1.65 | 0.48 | **23.33** | ASSUMED - OWNER-APPROVED | HELD | 22.80 |
| 1F bath east | 8.70 | 3.35 | 29.15 | 1.76 | 1.08 | **26.31** | ASSUMED - OWNER-APPROVED | HELD | 26.10 |
| 2F W.C. | 9.70 | 3.35 | 32.50 | 1.76 | 0.48 | **30.26** | ASSUMED - OWNER-APPROVED | HELD | 29.25 |

Totals: method A **340.41 m2** on 12 rooms (ASSUMED - OWNER-APPROVED heights and door heads; windows DRAWING-CONFIRMED);
6 rooms HELD, never 0 (4 annex rooms 96.85 m2 owner-manual PROVISIONAL candidate with the arch at full band; 2 rooms
with no floor level). Method B: 22.55 .. 23.20 m2 DRAWING-CONFIRMED (1 room), 17 HELD. Freelancer 433.83 m2 (17 rows
incl. the held ones; no pantry row).

Against T-128 r3 (same faces, same heights): the three nets T-128 already had agree to 0.01 m2 (wedge 289 25.30, lobby
26.65, 1F east bath 26.30); the nine main-house nets T-128 held on window heads now fall inside its ranges (wedge 245 20.91 .. 23.10
-> 22.62, master bath 23.88 .. 26.07 -> 25.59, pantry 26.97 .. 36.09 -> 32.34, laundry 51.00 .. 53.01 -> 52.53, 1F
W.C. 18.14 .. 20.15 -> 19.67, 2F W.C. 28.72 .. 30.73 -> 30.26, ...). T-209 closes them; it changes no T-128 figure.

## 5. Reconciliation to the freelancer (like for like, 11 rooms; `RECONCILIATION_T209.csv`)

His wet-wall line is one spatter-dash total, 433.83 m2 = his wet-room boundary 144.61 lm (T-074 per-room column) x 3.00
m, with no opening deducted (T-010, T-086; reconstructed per room as his lm x 3.00, which gives 433.83 exactly). On the
11 rooms where both are established:

| Step | m2 |
|---|---|
| Freelancer, 11 rooms | 295.44 |
| Length (our face vs his lm, x 3.00): wash lobby -3.70 (his 9.50 lm closes the 1.245 m open side to the stair hall; we tile no wall that is not there), others +0.04 .. +0.33 (printed / drawn faces vs his rounded lm) | -2.65 |
| Height (owner 3.65 / 3.35 vs his 3.00, a height printed nowhere) | +43.19 |
| Doors (13 openings x 2.20 head) | -22.99 |
| Windows (9 windows, T-201 / printed) | -4.92 |
| Own, method A | **308.07** |
| Residual | 0.0000 |

Net +12.63 m2 (+4.28 %), ENGINE vs freelancer. Verdict proposals: height RULE_DIFFERENCE (Q-48 A owner rule vs his
flat 3.00); openings ENGINE_RIGHT (UP-CER-005 / Q-73: no tile on a door or window opening; he deducts none); wash-lobby
length ENGINE_RIGHT (open side, no wall; T-074 / T-128 walk); pantry 32.34 m2 scope ENGINE_RIGHT on Q-37 A (pantry wet,
printed 4.50 x 3.00), he has no pantry row; the six held rooms (his 138.39 m2) not compared.

Q-48 rough column ("each door over its width only"): 325.75 m2 on the same 12 rooms, 14.67 m2 below method A. The
whole difference is the wall over the 14 door heads (sum w x (H - 2.20)); it is built wall in a fully tiled room, so
the installed quantity keeps it (Q-73 / T-175: the deduction is the opening). Shown, never used.

## 6. Materials on method A (PROVISIONAL owner practice values; `summary.json`)

340.41 m2 x 0.02 m = 6.81 m3 wall mortar (7.15 m3 with the 5 % waste column); owner method 54.47 bags of 50 kg (57.19
with waste; buy 55 / 58) and 7.49 m3 sand (7.86 with waste); theory beside 52.16 bags, 7.24 m3 (G4: never silently
replaced). Adhesive 340.41 / 5 = 68.08 bags of 20 kg (buy 69). Whole units rounded once on the sum, never per room.
The held rooms add nothing (no 0 either). Reveals: window reveal tile is its own item (UP-REVEAL-001); jamb + head run
per room in the CSV (35.42 lm over the 12 windows with an established sill and head; W05 HELD), m2 HELD (depth to the glazing not
printed); the sill is its own item.

## 7. What is HELD and why (nothing here becomes 0)

- 4 annex rooms (A 96.85 m2 candidate): G2, the +4.30 annex roof is a finished mark (owner manual result kept PROVISIONAL).
- GF W.C. 175 x 135 and basin space 110 x 135: floor level +0.30 or +1.00 not drawn (the passage opens on the stair
  hall between the two printed marks; T-088, Q-43). The plan alone does not settle it; section B-B (sheet 10) was not
  re-read in this run. W05 is bound at +2.70 / +3.50, the same absolute levels as W06 / W07 in the +1.00 rooms: a
  supporting indication, not proof.
- Drawing-derived height of 17 rooms: roof datum (DCR-6), sunken panels (T-206, new here for 5 rooms), crossing beams
  B27 / B11, floor build-up b (DCR-7, T-214 TODO).
- Arch and doorway heads (dewaneya wash 1.00, P-GF-01 0.90): range.

## 8. Lessons-register proposal (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Three GF wet rooms and the 1F laundry kept a DRAWING-CONFIRMED wall / tile height after T-206 found sunken wet panels in the slab above them (T-209: 0.36 .. 5.40 m2 under a panel) | A merged datum finding was not propagated to the trades that use the soffit of the slab above; ceiling heights were taken from the storey slab | A room's ceiling / wall-tile height is DRAWING-CONFIRMED only when every part of the slab above it is a known datum: any sunken, dropped or thinned panel over the room (plan overlap on the slab plan above, via the column translation) makes it HELD until its drop is printed; the storey value is an upper bound (every villa) | tests/t209_wet_wall_tiles (normal: a room with no panel keeps its bounded height; adverse: every room with a panel share > 0 is HELD) | PROPOSED |

## 9. Checker re-measure list (Gate A)

1. GF wedge W.C. 245 x 167 (GF-13): face 6.81 m (T-074 shoelace on the drawn faces), W06 in this room (DXF, W layer
   band on the north wall line), owner net 22.62 m2.
2. 1F laundry (1F-07): face 16.94 m, doors 0.80 + 0.90, W21, net 52.53 m2; under the 2F sunken panel 5BF 5.40 m2
   (ST7757 dxf, HATCH 5BF on the 1F roof-slab plan).
3. 1F bath east (1F-12): W18 printed 0.50 x 2.16 (NW chain 84 / 216 / 230), net 26.31 m2.
Plus the overlay: one GF room under a panel (master bath 2.24 m2) by your own translation.

Files: `wet_wall_tiles.py` (method, any villa), `alsenan_t209.py` (runner, `--check`), `ALSENAN_T209_INPUT.json`,
`WET_WALL_TILES_T209.csv`, `RECONCILIATION_T209.csv`, `summary.json`, `sunken_overlay.py` + `SUNKEN_OVERLAY_T209.json`
(areas and shares only, no coordinates); tests `tests/t209_wet_wall_tiles` (16). Drive inputs read in the private
folder only (P7757_DXF_COMPRESSED.zip, ST7757 dxf.dxf, the plaster workbook); nothing copied here.

# T-128 r3: 1F-11 frame-cavity notches trimmed, spike scan over every room (research only, NO REPO CODE)

Rework of r2 (8710bb1) exactly on the Checker's r3 list (verifier 2026-10-22 16:11, gate e failed on ONE room, 1F-11).
Everything else in r2 stands and is not re-opened: `T-128_R2_PLASTER_PAINT_TWO_METHODS.md` remains the report; this file
is its r3 addendum. Data: Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55...), read
this run into the private folder only. Before changing anything the r2 outputs were reproduced byte for byte from the
Drive DXF (walk_r2.json, ROOMS / OPENINGS / FLOORS_T128_R2.csv, summary_r2.json: all identical).

Repeat: `python -I scripts/walk_r2.py ../agents_t147/scripts/rooms.py <P7757.dxf> walk_r3.json` (project venv; exits 1
if the spike scan leaves a notch), then `python3 -I scripts/calc_r2.py walk_r3.json ../agents_t144/OPENINGS_T144.csv
trace_lengths.json <dir>` (its outputs are stored here renamed *_R3); fixtures `python -I scripts/check_walk_r2.py`
(6 cases PASS) and `python3 -I scripts/calc_r2.py --check` (PASS).

## 1. Physical element and the fault

1F-11 = the east master bed room with its entry; its east side is the curved W17 glazing band. Drawn on the room side
(layer 1 / W, read from the DXF this run): layer 1 fillet arc 0.177 m at the north jamb, layer W frame segment 0.050,
inner glazing arc 3.198, layer W frame segment 0.040, layer 1 fillet arc 0.043 at the south jamb (W17 inner face
0.050 + 3.198 + 0.040 = 3.288 = the Checker's 3.289). The T-147 barrier-buffer region leaked into the glazing-frame
cavity at BOTH jambs (between the 0.05 frame segment and the next frame line, 2 x BUF wide): a U notch of three edges
0.075 / 0.026 / 0.075 m at the north end and 0.006 / 0.043 / 0.037 m at the south end. Length without area.

Correction on the r2 label (the Checker's second fault): the two fillet arcs were NOT classed VIRTUAL. Re-run evidence:
r2 by-class for 1F-11 = WALL 15.483, COLUMN 1.700, WINDOW 3.266, GAP 1.670, DOOR 0.010, VIRTUAL 0.220; after the trim
WALL stays 15.483 (the fillets are inside it: they lie on layer 1 lines), VIRTUAL becomes 0 and WINDOW 3.286. The 0.220 m
VIRTUAL was the notch sides (0.200 m of them off every drawn line) plus 0.020 m of W17 the notches had cut off; it equals
the fillet total 0.177 + 0.043 = 0.220 by coincidence. Quantity unchanged by this point; the label in r2 was right.

## 2. Rule and fix (scripts/walk_r2.py, r3 block above `classify`)

Rule (Checker's lessons row, implemented): a walked contour is checked against its drawn faces; a direction reversal
across an edge under 0.12 m is an artefact, never a wall face, UNLESS every edge of the reversal lies on a drawn barrier
line (quarter / mid / three-quarter points within 0.01 m). `spikes()` reports U notches (edges i and i+2 within 30 deg of
antiparallel, edge i+1 < 0.12 m) and V spikes (two consecutive reversed edges, one < 0.12 m). `trim_notches()` replaces
each undrawn U notch by the chord across its mouth, which lies on the drawn face line. Applied where the scan finds a
notch (`NOTCH_TRIM = {'1F-11'}`); the scan then runs over EVERY walked room and the script fails if anything is left.

Drawn-line exception, why: without it the scan also reports GF-15 (edge 11, middle edge 0.092 m): that is the real acute
corner where the curved W03 glazing band starts against its wall (all three edges on layer 1 / W lines; GF-15 contour
21.537 m = the Checker's verified 21.535). Scan result without the trim: 1F-11 only (2 notches), as the Checker found;
with the trim: none left in 32 rooms.

## 3. 1F-11 and the totals, r2 -> r3 (CHANGES_R2_R3.csv; only 1F-11 moved)

| Quantity | r2 | r3 | Checker 16:11 | r3 vs checker |
|---|---|---|---|---|
| contour m | 22.350 | 22.149 (trim 0.1447 + 0.0561 = 0.2008) | 22.150 | -0.001 m |
| walked area m2 | 19.024 | 19.021 (-0.0027) | 19.022 | 0.01 % |
| W17 walked m | 3.266 | 3.286 | 3.289 drawn | -0.003 (documented 0.005 m sampling loss at each jamb, fixture) |
| paintable m | 17.384 (CSV) | 17.163 | 17.161 | +0.002 m |
| owner gross m2 (3.35, G1) | 74.87 | 74.20 | 74.20 | 0.0 % |
| owner net m2 (W17 full band, doors 2.20 Q-55 C) | 60.19 | 59.45 | 59.45 | 0.0 % |
| drawing-derived gross m2 (3.79 .. 3.89) | 84.71 .. 86.94 | 83.94 .. 86.16 | - | - |
| drawing-derived net m2 | 69.54 .. 71.77 | 68.70 .. 70.92 | - | - |

Per floor and house (dry; engine vs the freelancer's dry plaster rows for the same rooms, gross before openings):

| | r2 | r3 | Freelancer | r3 vs him |
|---|---|---|---|---|
| 1F owner method gross | 378.88 | 378.21 | 441.26 | -63.05 m2 (-14.3 %) |
| 1F drawing-derived gross | 428.65 .. 439.96 | 427.89 .. 439.18 | 441.26 | -13.37 .. -2.08 m2 (-3.0 .. -0.5 %) |
| House drawing-derived gross (incl. shaft) | 1,129.09 .. 1,155.22 | 1,128.32 .. 1,154.44 | 1,209.39 plaster gross | -81.07 .. -54.95 m2 (-6.7 .. -4.5 %) |
| House drawing-derived net | 929.37 .. 1,044.28 | 928.54 .. 1,043.43 | 1,151.14 plaster net / 1,191.13 paint net | -222.60 .. -107.71 (-19.3 .. -9.4 %) / -262.59 .. -147.70 (-22.0 .. -12.4 %) |
| House owner method gross, dry excl. shaft | 847.90 | 847.23 (annex 102.78 HELD, G2) | - | - |
| House owner method net, dry excl. shaft | 685.19 .. 753.74 | 684.45 .. 753.00 | - | - |

Wet-wall tile, GF and 2F unchanged. Statuses unchanged from r2 section 4: owner heights ASSUMED - OWNER-APPROVED (G1,
Q-43 / Q-48 A), door head 2.20 ASSUMED - OWNER-APPROVED (Q-55 C), drawing-derived 1F-11 HELD on the roof datum (DCR-6 / G2),
annex HELD (G2), shaft owner method HELD (Q-72); walked lengths DRAWING-CONFIRMED.

## 4. Regression test (scripts/check_walk_r2.py)

Normal case unchanged (villa K, 3 orientations). New adverse case, villa K (not Alsenan), by hand: the ring dips into a
0.03 x 0.075 m frame cavity at the north-east jamb of the curved glazing face; drawn face = 11 + 3.392248 = 14.392248 m,
ring 14.542248 (+0.15). Expected and obtained: scan 1 U notch -> trim 0.150 m -> contour 14.3922 = drawn face, scan empty,
VIRTUAL only the 1.00 m open side. Second adverse case: the same recess DRAWN on all three sides must be kept (no report,
no trim, 14.5422). Plain, mirrored, rotated 37 deg + 1 km shift: PASS (tolerance 1e-5 m: the 400-chord arc polyline is
2.5e-6 m short of the true arc).

## 5. Who is right, lessons

1F per-floor comparison stays as r2 section 7 (owner method -14.3 % vs his rows: RULE_DIFFERENCE, his 1F rooms at a
taller height; drawing-derived -3.0 .. -0.5 %). 1F-11: ENGINE_RIGHT at 74.20 / 59.45 m2 on the drawn faces (the r2
74.87 / 60.19 was a region-tool artefact, now removed). Lessons row (proposed, the Checker's wording, with the drawn-line
exception): 2026-10-22 | room contour +0.20 m at a curved window (T-128 1F-11) | barrier-buffer region leaks into the
glazing-frame cavity at the jambs: length without area | a walked contour is checked against its drawn faces; a direction
reversal across an edge under 0.12 m is an artefact unless all its edges lie on drawn lines (any villa, any region tool)
| check_walk_r2.py cavity-notch case + drawn-recess case; walk_r2.py spike scan fails the run | fixed in r3.

## 6. The other curved glazing bands, drawn face vs walked (area-equivalent check, no change)

Only three rooms have a curved window run (walk_r3.json): GF-15 and GF-08 share the W03 band, 1F-11 has W17.
W03: the inner layer W polyline is 6.873 m (DXF, this run); within 6 mm of the GF-15 ring 5.058 m, of the GF-08
(open room) ring 1.633 m, and 0.182 m between the two layer 1 lines of the dividing wall end (no room face): 5.058 +
1.633 + 0.182 = 6.873, residual 0.000 m. The walked GF-15 window run 5.106 also takes the 0.092 m drawn frame segment at
the start of the band (the Checker's 5.011 + 0.091 = 5.102, verified); neither W03 room shows a notch in the scan.
W17: inner arc 3.198 + frame segments 0.050 + 0.040 = 3.288 m drawn vs 3.286 walked in r3.

Missing / uncertain: nothing new; r2 section 8 still applies (unprinted openings, floor build-up, roof datum, G2, Q-72).

# T-674 Ground slab: the 5 B10-05 lines the Checker found below the drawn panel (T-180 P18), re-derived from the drawing

Worker 3 (lane S row taken under the lane I throughput rule), 2026-11-10 15:01 .. UTC, run session_01E6cPnddy4mSw4iLM5N8Ttr,
branch `agents/task-T-674`. Research only: no engine, candidate, released line, rule or method version changed, nothing
released. Development villa, not an accuracy claim. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied.

## 0. Sources and runs

Own Drive copies (folder "Alsenan chalet project", decoded into `.work/private` only): 'ST7757 dxf.dxf' (`9f9d1179`, the
same sha as T-391 and P18) and ST7757.pdf (the issued print of the same sheets; GROUND BEAMS PLAN = page 3, read as an
image for the second check). Candidate values: `research/agents_t507/out/LINE_INDEX_V3_0_57.json` (the five lines are
unchanged through V3.0.64). Engine cells: route G (`engine.source.generic_route`, URBAN_M8_GENERIC_CONVENTIONS_V6, no
profile; the run that names the V3.0 ground-slab cells) on the same DXF, sheet SH08: the same 26 cells and areas as the
candidate lines (e.g. SITE-49a7dae5 gross 3.834377 - 0.236694 = 3.597683 m2 = 0.359768 m3, the candidate value).

```
.work/venv/bin/python -I research/agents_t674/t674_alsenan.py .work/private/ST7757_dxf.dxf --out research/agents_t674/summary_t674.json
```

Files: `t674_rules.py` (R-T674-1 .. 4, pure stdlib), `t674_alsenan.py` (private run; writes values, ids and DXF handles,
no coordinates), `summary_t674.json`. Tests `tests/t674_ground_slab_panels` (17).

Own partition: the T-391 frame (GROUND BEAMS PLAN) noded on layer-1 LINE / ARC, S-COL.BON and S-BW, with every line end
that lies on a true arc (0.5 mm) inserted as an arc vertex before polygonising (R-T674-2): 181 faces, 289.1092 m2 (T-391
and P18: 180 faces, the court strip merged into the panel; see 2).

## 1. Physical element

Slab on grade 'T=10cm' (GROUND BEAMS PLAN, T-206 DRAWING-CONFIRMED), cast between the ground-beam faces; convention C1
(T-234 / T-241 / T-242): the ground beam is billed full depth from the slab top and owns its strip; the slab is the panel
between drawn faces, never over a strip (R-T391-1).

## 2. Per line (m2 own vs engine; m3 at T = 0.10)

| Line (cell) | Candidate m3 | Checker P18 cause | What the drawing shows | Corrected m2 | Corrected m3 | delta m3 | Verdict proposal |
|---|---|---|---|---|---|---|---|
| L-69527cb9 (49a7dae5) | 0.359768 | 'member overlap with no member on the plan' | an OBLIQUE GROUND BEAM across the bay's corner: layer-1 lines 180 / 181, parallel, 0.300 m apart, from the west carrier face 176 to the south carrier face 180D; 181 is drafted 0.078 m (0.110 m along) short of 180D (the print, sheet 3, shows the same short inner line). It is route-G band BAND0038 with its own line L-970bac56 (P-C:GROUND_BEAMS:GROUND:BAND0038, HELD 0.071008). The 0.236694 m2 deduction rests on that drawn member. The beam's strip between its faces to both carriers is 0.326694 m2 (R-T674-1; T-282 closure, MERGED: 'the edge closes on its carrier's drawn face'); the engine deducts only the square-cut band (0.789 m x 0.30) and leaves the two end triangles 2 x 0.045 = 0.090 m2 in the slab | 3.834377 - 0.326694 = **3.507683** | **0.350768** | **-0.009000** | ENGINE_RIGHT on the deduction (the P18 own read had no closed strip because 181 dangles); ENGINE_WRONG 0.090 m2 on the end triangles (beam's, C1) |
| L-8b681fda (3f7728a8) | 0.261557 | lift ring / oblique beam gap (T-230) | the panel runs west to the drawn outer face of the lift ring (S-BW 7C2) below the oblique beam 17E / 17F. The engine's cell stops 0.184 m east of that face at a line that is not drawn: route G's JUNCTION_GAP face SITE-47d689fe (0.8254 m2, NO_LINE, T-401) is the box of the band ends round the lift corner and takes 0.105587 m2 of this panel, although the support (ring 7C2, column 1EF) is drawn | own **2.721160** | **0.272116** | **+0.010559** | ENGINE_WRONG (junction box over a drawn support, R-T674-3) |
| L-f192ff5f (c1b4b440) | 0.224470 | same | the same junction box takes a 0.0282 m strip along the ring's top face (S-BW 7C2) under the panel bounded by 7C8, 182 and 17E: 0.008684 m2 | own **2.253380** | **0.225338** | **+0.000868** | ENGINE_WRONG (R-T674-3) |
| L-1031c9be (d74f3fe2) + L-5e881fd3 (0caa2bd2) | 1.090505 + 0.205020 | 'court-side panel split at a line not drawn, stopped short of arc 158' | the split IS drawn: layer-1 lines 177 (south) and 7CD (north), 0.300 m apart = ground beam BAND0008.2 (own line L-d53e5eb0, HELD; engine BEAM_STRIP face 0.492189 m2). Both lines END ON arc 158 (distance to the centre = r = 2.550 m to 0.0000 mm). Polygonising with arc 158 flattened to chords leaves each end < 0.05 mm off the chord, so the strip and both panels merge into one false face (13.45 m2, T-391 OWN-006 and P18). Noded on the true arc: own faces 10.905146 and 2.050238 m2 = engine 10.905052 / 2.050202 (+0.0001 m2, arc flattening). The engine cell follows arc 158 (its vertices are on r = 2.550) | engine **10.905052 / 2.050202** | **1.090505 / 0.205020** | **0** | ENGINE_RIGHT (own-read node artefact) |

**Five lines: candidate 2.141320 m3 -> corrected 2.143747 m3 (+0.002427 m3, +0.11 %).** P18 had put them at -0.084731 m3
below the drawing; 0.081237 m3 of that was the own read (a dangling face line, two unnoded arc ends), not the engine.
B10-05 family with the 21 AGREE lines: 21.63846 + 0.002427 = **21.640887 m3** (P18 own 21.72308: the difference is the
two drawn beam strips the P18 read counted as slab, 0.023670 + 0.049634 m3, plus the 0.090 m2 end triangles moved to
the beam, 0.009000 m3 = 0.082304 m3; the last 0.000111 m3 is the arc flattening P18 itself named, +0.000998 m2 on one
AGREE panel, and +0.0001 m2 here).

Own read of all 26 cells (same noded partition): the other 21 lines equal their own face to 0.0001 m2 (the 0.1556
triangle, the stair-zone panel 8.3723 included); the held cell c1089bdb spans 14 own faces (T-391 F1, unchanged). The
route-G sheet has a second JUNCTION_GAP face, SITE-5a8e5ad3 0.0571 m2: it lies inside a drawn beam strip (own face
0.8077 m2, equivalent width 0.281 m, the rest of it the engine's BEAM_STRIP SITE-5554e673 0.7505 m2), so it takes no
slab area; R-T674-3 changes nothing there.

Second check (the issued print, ST7757.pdf page 3 at 500 dpi, own view): the oblique beam is two parallel lines framing
from the west beam to the south beam, the inner line stopping just short of the south beam; the lift box (hatched ring,
C1 / C2 / C2 / C9) with the oblique beam starting at its north-east C2 and the panel below it running to the ring face;
the straight beam meeting the pool's curved beam. All three read the same as the DXF.

## 3. Cross-trade (never one without the other; no line edited here)

- GB L-970bac56 (BAND0038, HELD 0.071008 m3 = 0.236694 m2 x 0.30): its drawn plan is 0.326694 m2 (strip to the
  carriers, R-T674-1). Wiring -0.090 m2 into the slab without the beam gaining it would drop 0.009 m3 from every line;
  T-671 / lane I wires both or neither. The beam stays HELD (depth not established, T-170 / T-401); its value is not
  released here.
- The junction-gap face SITE-47d689fe keeps 0.711 m2 that are neither slab nor in a valued line after the return of
  0.114271 m2 to the two panels (lift ring 0.22 and shaft 0.4275 named by T-401 / T-444, beam ends BAND0008.1 0.0552 and
  BAND0003 0.0085: 0.7112 m2, closes);
  it stays NO_LINE, named.
- GB L-d53e5eb0 (BAND0008.2) HELD 0.1383 m3: unchanged; its strip face 0.492189 m2 is not slab and is not double
  counted by either court line.

## 4. Rules, engine proposal, lessons row

R-T674-1 .. 4 in `t674_rules.py` (new rule ids, not a version of an existing rule). Engine proposal for the lane I
candidate (a new method version, never in place): (a) M4 member-overlap deduction of an oblique band runs to the
carrier faces, with the beam line's plan equal to the same strip; (b) `slab_engine.junction_gaps` boxes clipped to the
drawn faces of an S-BW ring / column outline next to them (the 0.114271 m2 returned here). Both are proposals: the
candidate and route G are unchanged.

Lessons row (ERS s.7): | 2026-11-10 | P18 put 5 ground-slab lines -0.084731 m3 below the drawing (T-391 F3 UNRESOLVED) |
an own polygonisation of the plan flattened arcs to chords and dropped dangling face lines, so a drawn beam strip whose
face is drafted short, or whose faces end on an arc, merged into a panel and read as 'an undrawn member' / 'an undrawn
split'; the engine's junction box crossed a drawn ring | before calling a deduction or a split undrawn, list the drawn
lines inside the face: two parallel lines one beam width apart are a member even when one stops short; a line end on
the true arc is a node; a junction box never crosses a drawn support face (every villa; provenance T-674) |
tests/t674_ground_slab_panels (strip to carriers under rotation / mirror / mm; short face a gap not an end; deduction
with no drawn member refused; merge without arc nodes vs split with them; split on an undrawn line refused; junction
box with / without a drawn support; missing thickness never 0) | PROPOSED |

## 5. Checker re-measure list

- Lines 180 / 181: parallel at 0.300 m; strip to 176 / 180D = 0.326694 m2 (two triangles (k^2/2) between the two face
  lines and the corner, k = x + y of each face line measured from the corner); 181's south end 0.0781 m above 180D.
- Arc 158 r = 2.550: ends of 177 and 7CD at distance r (0.0000 mm), angles 220.32 / 211.97 deg (inside the arc's
  109.75 .. 259.84); own faces after noding 10.9051 / 2.0502 / strip 0.4922 m2.
- Panel 3f7728a8: own west edge = S-BW 7C2 outer face; engine edge 0.184 m east of it (no drawn line): 0.105587 m2.
  Panel c1b4b440: own south edge = 7C2 top face; engine edge 0.0282 m above it: 0.008684 m2.

## 6. Not done / uncertain

- No engine or candidate change (research row); wiring is T-671 / lane I (Gate B), with the beam BAND0038 plan.
- The end triangles' ownership rests on C1 + the T-282 closure (a drafted-short face closes on its carrier); if the
  Checker reads the short inner line as the beam's end, L-69527cb9 stays at the candidate 0.359768 m3 and the 0.090 m2
  is named, not moved.
- Own areas carry the 256-chord arc flattening (<= 0.0001 m2 per arc face).

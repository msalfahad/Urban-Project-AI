# T-313: the opening reveal ledger (every opening, every side once; development villa; rule for every villa)

Research only: no engine, method, rule / knowledge version, registry or candidate quantity changed. Development villa,
not an accuracy claim. Drawings cited by Drive title and DXF handle only (no coordinate, image or name). Worker 2,
2026-10-28 (re-claim of the 2026-10-26 claim that left no branch).

## 1. Result (engineering terms)

| Side / component | Openings | Quantity | Evidence | Candidate line |
|---|---|---|---|---|
| Window ROOM side: jambs, head, sill (UP-REVEAL-001) | 27 of 29 | **0.000 m2: NONE** (frame drawn flush with the room face on every measured window) | DRAWING-CONFIRMED (no surface) | sill row bound to the window's ARCH.WINDOW_REVEAL line; jambs / head NO LINE |
| Window OUTSIDE: jambs | 26 | **6.6976 m2** (77.720 m.l of edge) | DRAWING-CONFIRMED | NO LINE (missing) |
| Window OUTSIDE: head soffit | 27 | **2.9694 m2** (34.630 m.l) | DRAWING-CONFIRMED | NO LINE (missing) |
| Window OUTSIDE: external sill (own item) | 23 | **2.5614 m2** (29.530 m.l) | DRAWING-CONFIRMED | the window's ARCH.WINDOW_REVEAL line |
| Window OUTSIDE: floor-level threshold strip (W15, W16, W25, W27) | 4 | **0.4080 m2** (floor edge, no arris) | DRAWING-CONFIRMED | the window's ARCH.WINDOW_REVEAL line |
| Door / gate reveal THROUGH the wall (UP-FIN-PLASTER-001): jambs | 27 doors | **19.920 m2** (119.400 m.l): D-GF-07 1.000 DC (printed 2.50), 26 doors 18.920 **ASSUMED — OWNER-APPROVED** (Q-55 C 2.20) | as stated | NO LINE (missing) |
| Door head soffit | 27 doors | **4.230 m2** (25.000 m.l) | DRAWING-CONFIRMED (width x wall t) | NO LINE (missing) |
| HELD / UNKNOWN (never 0) | | W02 outside jambs (height HELD, D-53); W03 (curved glazing, room side not in the engine rooms) and W17 (curved wall, T-302 developed hole) all components; D-GF-15 gate (width / height HELD); A-GF-01 arch (candidate jambs 0.660 + head 0.15 x 1.223795 = 0.183569 m2, outline pending D-45); A-1F-01 (not drawn) | HELD / UNKNOWN | NO LINE |

Window reveals measured: 12.6364 m2 outside (jambs + head + sill + threshold), 0.000 m2 room side; doors 24.150 m2
through the wall. Every one of the 59 census openings (29 windows, 27 doors, 1 gate, 2 arches; T-249 MERGED) is in the
ledger once; 234 side-component rows, each once (`REVEAL_LEDGER_T313.csv`).

## 2. Physical element and how each was measured (ERS s.2.1 - s.2.3)

- **Window depth** (plan P7757.dxf, sha `ab54dd55`, census glazing handles of T-249): frame band = the extreme offsets
  across the wall of the census glazing lines parallel to the opening; the two wall faces = the nearest lines parallel to
  it, outside the symbol, ending at a jamb within 10 mm on each side; the room side = the face whose probe point (0.30 m
  beyond it, mid-opening) lies in an engine room polygon (ARCH_ROOMS of the run; a labelled room beats an unlabelled
  space: W09 / W10 face the side passage, Q-67 A conditional exterior). Result on all 27 straight windows: wall 0.200 m
  on plan = T-150 wall thickness (27 / 27); the frame band (0.120 m on the 10-line symbols, 0.100 m on the 3-line
  symbols W01, W11 - W14, W26) is FLUSH WITH THE ROOM FACE, so the room-side reveal depth is 0.000 and the outside
  reveal depth is 0.080 m (or 0.100 m). Hand check W04 (handles 3A3 .. 3AD, wall face lines 11E / 122, sill line 3A5 on
  the outer face): frame 0.120 from the driver-room face, outer reveal 0.200 - 0.120 = 0.080 m; outer jambs 2 x 0.080 x
  0.80 = 0.128 m2, head 0.080 x 0.60 = 0.048 m2, sill 0.048 m2 (= ledger).
- **Window sizes**: T-237 OPENING_SIZES (MERGED 1cc1a153: merged heads of T-201 / T-207 / T-238); W05 height 0.800
  from T-201 (drawn, levels HELD); W11 / W12 h 2.20 (T-207 DC, sill HELD: the outside reveal does not need the sill).
- **Room-side plaster band** (owner method Q-43 / Q-48 A: T-237 owner_h 3.15 / 3.35 / 3.65, beside the drawing range
  dwg_paint_h): only decides whether a head soffit exists; with a flush frame there is no room-side reveal under EITHER
  method, so the two methods agree here (0.000 m2, no residual).
- **Doors**: one reveal through the wall thickness (owner rule UP-FIN-PLASTER-001: 2 x t x h + t x w; the frame detail
  decides how much is plastered, PROVISIONAL); t from T-150 (0.15 / 0.20, MERGED), w / h from T-237; no sill reveal.
- **Arches**: A-GF-01 head developed on its drawn arc (T-238: ARC 2422 r 0.5673 m, 28.2 .. 151.8 deg, chord 1.000 m):
  0.5673 x 2.157227 rad = 1.223795 m; kept HELD with the arch (D-45). A-1F-01 is drawn on no view: UNKNOWN.
- **Finish** (not a quantity): the owner method URBAN-REVEAL-FINISH-METHOD v1 (data/registry; default PLASTER, paint on a
  painted dry surface, porcelain only when shown, never because the room is wet) is the finish CANDIDATE; UP-REF-REVEAL-001
  is REFERENCE_ONLY in the route and the WIN-REVEAL finish decision is queued (OWNER_QUESTIONS.md), so the finish status is
  OWNER_METHOD_CANDIDATE, never DRAWING-CONFIRMED. The flush frame removes the wet-room reveal question physically (no
  room-side reveal in any WC / bath).

## 3. Line binding (V3.0.19 grain)

The candidate carries **27 ARCH.WINDOW_REVEAL m2 lines, all BLOCKED_RFI blank** ("sum of the strip faces of the opening
in the wall thickness", RFI WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED), one per engine window (W03 and W18 have none:
V2.9 misses them). Line ids are `boq_line.line_id(project, item, element, rule, version, unit)`, independent of the
method version (T-232: the 27 lines byte-identical through V3.0.10); this run read them from an engine run of the same
drawings (`BOQ_LINES.csv` sha `f5744fd4`), see section 7 for the V3.0.19 re-read. Binding: each window's sill (or
floor-level threshold) rows, room side and outside, go to its own line; jambs and head go to NO LINE; no line carries two
windows and no window two lines (27 / 27 bound). PHYSICAL MEANING of the line: the whole plan strip w x 0.20 m, of which
only the outside 0.080 (0.100) m is a finished sill surface; the 0.120 (0.100) m under the frame is the frame bed, not a
finish (finding for lane I: fill the line with the external sill / threshold surface only, 2.5614 + 0.4080 m2 on the 27
lines, never w x wall thickness). Missing families for lane I: window outside jambs + head (9.6670 m2 measured), door
reveals (24.150 m2), W18's external sill (0.040 m2, no line). BOQ family B4-08 'Reveals and returns' stays
NOT_IMPLEMENTED until a package integrates them.

## 4. Reconciliation of the exterior reveal EDGE (acceptance 2)

The register's **189.630 m.l is the superseded r1 figure** of T-162: r2 (MERGED 4cc2847) corrected it to **137.110 m.l
measured + 32.200 ASSUMED** because r1 added 2 x height per opening a second time (-52.520 m.l). This ledger against r2's
own 36 facade openings (`EDGE_RECONCILIATION_T313.csv`):

| Term | m.l |
|---|---|
| T-162 r2 measured (36 facade openings, its known parts) | 137.110 |
| of which the 26 windows this ledger now measures whole (head + sill only for 19 of them in r2) | 85.420 |
| of which still open here: W02 12.660, W03 21.740, W17 10.290 (curved / height HELD), D-GF-07 7.000 (door, printed) | 51.690 |
| T-313 edge of the same 26 windows | **129.220** |
| = 85.420 + jambs newly DRAWING-CONFIRMED since r2 (T-201 / T-207 heights, 2 h on 19 windows) | +45.800 |
| - floor-level W25 / W27: no sill arris (r2 counted one) | -2.000 |
| Residual | **0.000** |

W18 (5.320 m.l, not on the engine outline) is among the 26. The door arrises at the outer face (32.200 ASSUMED + 7.000)
stay in the corners line; a door reveal is one surface through the wall here. The register rows 68 / 515 / 551 should
cite 137.110 (r2) and the T-313 129.220 for the 26 windows, not 189.630 (Lead).

## 5. Engine vs freelancer, verdict proposals

- Candidate: 27 blank strip lines, no jamb / head / door reveal line: the engine carries 0 of 36.7834 m2 measured reveal
  surface (12.6364 window outside + 24.150 doors; 18.920 of it ASSUMED — OWNER-APPROVED). **ENGINE_WRONG (missing scope)**
  for the outside window reveals and the door reveals; the strip line's basis (w x wall t) is ENGINE_WRONG as a finish
  quantity (frame bed included).
- Room-side window reveal (UP-REVEAL-001 route `window_strip_lines`): would emit 2 x depth x band on a measured strip; on
  this drawing the depth is 0.000, so a room-side reveal line is NOT_APPLICABLE with evidence (frame flush), never a
  default depth.
- Freelancer: no reveal surface row in his workbooks (merged T-128 / T-162 records: his plaster sheet deducts openings,
  his corner m.l is one lumped Sigma line); this run did not re-open his workbooks: **RULE_DIFFERENCE (scope)**, UNRESOLVED
  per cell.

## 6. Rule, test, lessons (ERS s.4, s.7)

- **R-T313-REVEAL-1** (research rule, every villa; a rule version only when adopted): a reveal is measured per opening
  and per SIDE from the drawn frame position: depth = wall face to frame line on the plan (a flush frame = depth 0 with
  that evidence, no surface), never a typical depth; window: room side (jambs in the plaster band, head only with wall
  above, internal sill own item) and outside (jambs, head, external sill own item; floor-level: threshold, no arris);
  door: ONE reveal through the wall (no sill); arch: head on its developed arc; the outside EDGE goes to the corners m.l
  line, the SURFACE never to a facade face; a strip line of w x wall thickness is not a finish quantity.
- Code `research/agents_t313/t313_reveal_ledger.py` (generic) and `t313_alsenan.py` (development-villa run).
- Tests `tests/t313_reveal_ledger` (28): villa R313 hand fixture (W1 1.20 x 1.50 in a 0.20 wall, frame 0.05 .. 0.12
  off the outer face: IN 0.240 / 0.096 / 0.096, OUT 0.150 / 0.060 / 0.060 m2, edge 5.40 m.l; D1 0.880 + 0.180; A1 head
  0.244759 m2), normal (band clip, floor glazing, flush frame, sill / height unknown, mirror and mm units, binding,
  totals) and adverse (default depth, missing depth as 0, door sill reveal, reveal in the facade face, one opening in two
  lines, two openings in one line, binding to a non-row, duplicate opening, unknown unit / negative length, arch at the
  chord, residual not named); Alsenan pins on the committed ledger (census once, 27 lines one window each, HELD never 0,
  depths close to the wall, edge reconciliation closes).
- Lessons row (proposed): 2026-10-28 | A reveal family sat blank because the engine's only reveal line is the plan strip
  w x wall thickness, and a register figure (189.630 m.l) survived its own correction (137.110, T-162 r2) | The strip was
  taken as the reveal and the frame position was never read; a superseded revision was cited | Measure each reveal per
  side from the drawn frame position (flush = 0 with evidence); cite a figure with its ledger revision (every villa) |
  tests/t313_reveal_ledger | PROPOSED.

## 7. Run identity, missing / held

P7757.dxf `ab54dd55` (Drive "Alsenan chalet project", P7757_DXF_COMPRESSED.zip), ARCH_ROOMS / BOQ_LINES of an engine run
on the same drawings (`0b48da21` / `f5744fd4`); Python 3.11.18. The V3.0.19 re-read of the 27 line ids: see the handoff.
Not done here: curved W03 / W17 developed reveals (T-302 method), W02 height (D-53), gate D-GF-15, A-1F-01; the door
outer arrises stay with T-162; passages P-GF-01 / P-GF-05 / P-1F-01 (not in the T-249 census; T-207 head terms
0.180 / 0.240 / 0.195 m2) and lift openings are outside this census.

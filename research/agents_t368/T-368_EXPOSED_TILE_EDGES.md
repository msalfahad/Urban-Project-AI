# T-368: EXPOSED WALL-TILE EDGES (BOQ family B4-10; UP-CER-006 45-degree edge / UP-CER-007 steel profile), edge by edge (development villa; every villa by R-T368-1 .. 6)

Worker 3, claim 2026-10-30 11:03 UTC, run session_01E6cPnf2dNDDd7Uxq92dPtG (lane I had no TODO; READY = 2, so a
standalone piece is allowed). Research only: no engine module, method, rule / knowledge version, registry file,
candidate line, released line or V2.9 cell changed; nothing released, nothing VERIFIED by this task. ERS applied: s.2.1
(physical element first), s.2.2 (owner rule and drawing reading side by side), s.2.3 (own vector reading), s.3 (one edge,
one face, one finish), s.4 (rules + normal and adverse tests), s.7 (lesson rows, section 9).

## 1. Identity and run

Own run, Python 3.11.18. Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 `ab54dd55` =
SOURCE_MANIFEST), decoded into .work/private only; an ARCH_TAKEOFF_V2.9 run on it (tools/urban_boq_m9.py arch, output
in .work/private) gave the engine room polygons (ARCH_ROOMS) and openings. `t368_alsenan.py --geometry <P7757.dxf>
<ARCH_ROOMS.json>` re-reads every committed corner count (18 / 18 OK) and the 10 cited handles; `--write` builds the
ledgers from committed inputs only (the merged T-312 face ledger / room closure / openings, T-313 window depths, T-325
sills, T-315 pantry line, and the per-room corner counts with their handles); `--check` rebuilds byte for byte. No
coordinate, image, client name or drawing content is committed. Tests `tests/t368_exposed_tile_edges` (32 pass).

## 2. The physical element (ERS s.2.1)

A wall tile edge is EXPOSED when the tile's cut edge is visible because nothing covers it: it is not against another
tiled face in the same plane, nor a frame, a ceiling or a floor. On a tiled face that gives five kinds of edge:

| Type | Physical meaning | Length | Exposed? |
|---|---|---|---|
| EXTERNAL_CORNER | convex arris where two tiled faces meet (column / pier proud, wall corner inside the room, obtuse 135-degree corner) | tile band at the corner | yes |
| WALL_END | tiled face ending at the arris of a wall whose other face is not tiled (open pantry / open lobby side) | band | yes |
| FLAT_STOP | tiled face stopping in the plane of a wall face that continues untiled | band | yes (finding F-T368-1) |
| OPENING_DOOR | door / doorway perimeter inside the band: 2 jambs x 2.20 (Q-55 C) + head width | 2 h + w | only on drawn frame evidence: HELD 0 .. perimeter when the frame / architrave detail is not drawn |
| OPENING_WINDOW | window perimeter on the room face | 2 (head - sill) + 2 w | NO when the frame is drawn flush with the room face |
| INTERNAL_CORNER, TOP_AT_CEILING, BOTTOM_AT_FLOOR, UNDER_FRAME | concave corner (faces butt); top against the decor ceiling (tile top = its underside, Q-48 A); floor; under a frame | listed | never |

Evidence per element (ERS s.2.2 order):

| Element | (1) Drawings | (3) Owner rules | Result |
|---|---|---|---|
| Tiled faces, band | no tile height / note printed (T-091) | UP-WET-001 / UP-FIN-WALL-001 full height; Q-48 A GF 3.65, 1F / 2F 3.35; UP-PANTRY host walls whole; T-312 / T-315 / T-351 MERGED faces | band OA on 12 rooms, HELD on 6 (annex G2 / Q-54 B / D-39; GF-10 / GF-11 level T-088) |
| Corners | wall, column (S-COL.BON) and counter entities on P7757.dxf | - | own reading, every reflex vertex named by its wall / column handle (section 3) |
| Window frames | T-313 (MERGED): frame band drawn FLUSH with the room face on all 27 straight windows (room-side reveal 0.000) | - | every tiled-room window edge UNDER_FRAME, DRAWING-CONFIRMED |
| Door frames | no frame / architrave detail on any sheet (T-091; T-313 'frame detail decides, PROVISIONAL') | no owner rule on architraves (OWNER_QUESTIONS_ANSWERED searched: none) | exposure HELD by name FRAME_DETAIL_NOT_DRAWN, range 0 .. perimeter |
| Top stop | decor ceiling 0.15 deep in wet rooms (Q-48 A, G1) | UP-FIN-WALL-001 tile top = its underside | covered: not exposed |
| Niches | none drawn (no recess in any tiled room outline besides the listed corners) | - | 0 |
| Finish | nothing printed (T-091: 0 finish notes) | UP-CER-006 / 007: alternatives on one edge, never both | both shown on the same m.l, choice HELD |

## 3. Edge by edge (EDGE_LEDGER_T368.csv, 93 rows; CROSSCHECK_T368.csv)

| Room | Line (FIN.WALL.TILE) | Band m | External corners (handles) | Wall ends / flat stops | Exposed m.l | Doors HELD (range m.l) | Windows (under frame) |
|---|---|---|---|---|---|---|---|
| 1F-07 laundry | L-b2077eee5a71a975bd74 | 3.35 OA | 3: wall corner ACF / B07, lift corner column 2FF0 (B06 / B14), column 2FED proud 0.05 | - | **10.0500** | D-1F-06, D-1F-05: 0 .. 10.50 | W21 2.80 |
| 1F-09 bath | L-086e72207311265f81ab | 3.35 OA | 1: column 2FE7 proud 0.05 | - | **3.3500** | D-1F-07: 0 .. 5.20 | W23 2.80 |
| GF-13 bath | L-a3cb2c8a9b6080769ebc | 3.65 OA | 1: column 2F84 proud 0.05 | - | **3.6500** | D-GF-12: 0 .. 5.20 | W06 2.80 |
| GF-14 wash lobby | L-fa408571a8adcfaf1a1f | 3.65 OA | 1: obtuse 135-degree corner, walls BE / 318 | open side (layer 2, 2DB / 2DC): east end = free end of wall D2 (end line BC) WALL_END; west end = wall 222 continues FLAT_STOP | **10.9500** | D-GF-11, D-GF-12: 0 .. 10.40 | - |
| GF-07 open pantry | L-f5c5a1a9c9ee2b644cb5 (T-315 ADD) | 3.65 OA | 1: column 2FAE proud 0.05 below wall 158 | open edge B3 (layer 5): north end = free end of wall 159 (AC) WALL_END; south end = wall A6 continues as 104 FLAT_STOP | **10.9500** | D-GF-06: 0 .. 5.40 | W10 5.00, W09 6.00 |
| 1F-02, 1F-03, 1F-08, 1F-12, 2F-02, GF-12, GF-16 | own lines (ledger) | 3.35 / 3.65 OA | 0 (rectangles / pentagon) | - | 0.0000 | one door each: 0 .. 5.20 | W20, W19, W22, W18 5.32, W28, -, W07 |
| GF-06 kitchen (annex) | L-c330b8dc47261d5ada7e | HELD | 4: column 2FB7 both sides, column 2FB1, WC block corner (135 / 14F) | - | HELD (4 edges, never 0) | D-GF-05 HELD | W08 under frame |
| GF-02 (annex) | L-d0858b30e0ea869bd047 | HELD | 1: column 2FA5 | - | HELD (1 edge) | D-GF-02, arch A-GF-01 HELD | - |
| GF-03, GF-05 (annex), GF-10, GF-11 (level not drawn) | own lines | HELD | 0 | - | 0 | doors / doorway HELD | W05 under frame |

Hand check (not the code's arithmetic): laundry 3 x 3.35 = 10.05; GF-14 3 x 3.65 = 10.95; pantry 3 x 3.65 = 10.95; GF-13
3.65; 1F-09 3.35; total 38.95 m.l. Doors: 12 x (2 x 2.20 + 0.80) = 62.40 + (4.40 + 0.90) 5.30 + (4.40 + 1.00) 5.40 =
73.10 m.l. Windows (not exposed): W20 2 x (2.50 - 1.70) + 0.60 + 0.60 = 2.80; W18 2 x (3.00 - 0.84) + 0.50 + 0.50 = 5.32;
W09 2 x 1.50 + 1.50 + 1.50 = 6.00 (= ledger).

## 4. Totals (summary.json)

| Quantity | m.l | Status |
|---|---|---|
| EXTERNAL_CORNER | 24.35 | ASSUMED — OWNER-APPROVED (band Q-48 A); corner count DRAWING-CONFIRMED |
| WALL_END | 7.30 | same |
| FLAT_STOP | 7.30 | same |
| **Exposed, determinate (12 rooms)** | **38.95** | finish HELD: 45-degree (UP-CER-006) 38.95 **or** steel profile (UP-CER-007) 38.95, never 77.90 |
| Door perimeters in determinate rooms | HELD 0 .. 73.10 | FRAME_DETAIL_NOT_DRAWN |
| Annex / level-HELD rooms | HELD: 5 corner edges + 8 door / arch / doorway edges, no length (never 0) | band HELD |
| Not exposed, listed (internal corners, tops, windows under frames) | 376.557 | evidence per row |

## 5. Cross-trade and double count (acceptance c)

| Check | Result |
|---|---|
| Window edges vs T-313 reveals / T-325 sills | every tiled-room window: room-side reveal 0.000, internal sill 0.0 m2 / 0.0 m.l (T-325 SILL_IN NONE): no edge on the room face; **0.0000 m.l** double count |
| Opening edges vs the T-313 outer-face edge ('corners' line, 36 facade openings) | 15 of this ledger's openings are facade openings (W05 - W10, W18 - W23, W28, D-GF-05, D-GF-06); T-313 measures the arris on the OUTER face, this ledger the ROOM face: two faces, two arrises, **0.0000 m.l** |
| Door edges vs FIN.PLASTER 'door jambs and head' (T-313 binding; T-326 reveal carriers QUEUED) | those are m2 reveal surfaces; the tile edge is the m.l trim on the room face; a door between two tiled rooms (D-1F-06, D-GF-11, D-GF-12) has one perimeter on EACH face (R-T368-5). When T-326 binds a reveal carrier, the edge stays bound to the tile line by opening id |
| Plaster corner beads (B4-09, engine/source/corner_bead.py, research) | its policy: 'a corner with one tiled face is a tile trim, never a plaster bead'; every edge here has a tiled face: **0** |
| Skirting | full-height tiled rooms carry no skirting (T-315: NOT_APPLICABLE); the bottom edge sits on the floor: not exposed |
| Paint / plaster | unchanged; this ledger adds m.l trims only |

## 6. Engine vs freelancer (acceptance d)

His finishes workbook ('Alsenan chalet project', the floors / waterproofing / decor / marble workbook, normalised in
tests/alsenan/registers_b1/BENCHMARK_NORMALISED.json) has **no** edge, 45-degree or profile row: its cover lists floors,
skirting, walls, stairs and landings, stair nosings (marble), decor, cornices and waterproofing only. His wall tile is
room boundary x 3.00 m with no edge item. **Engine (this ledger) 38.95 m.l determinate + 0 .. 73.10 m.l HELD vs
freelancer 0 m.l.** Verdict proposal: **RULE_DIFFERENCE** (scope: the owner rules UP-CER-006 / 007 measure the exposed
edge as its own item; his method has none). No percentage is meaningful against 0.

## 7. Findings

- **F-T368-1 (FLAT_STOP).** At a flat stop (GF-14 west end, pantry south end) no second tiled face meets the tile, so a
  45-degree mitre has nothing to meet; physically only a stop profile (UP-CER-007) or a finished-edge tile closes it. The
  owner rules give the two finishes as alternatives without naming where each applies; this ledger does NOT choose: both
  stay shown on the 7.30 m.l and the choice stays HELD (a rule-scope note for the rule library, not an owner question:
  ERS s.2.7 is not met while the finish itself is not printed anywhere).
- **F-T368-2 (counter reflex).** The pantry engine room (GF-RC06FED) closes on counter lines (layer 5): its only reflex
  vertex is the south counter leg's end (AA / B2), not a wall. Counting room-polygon reflexes would have put a tile
  arris on a counter and missed the column 2FAE arris; the pantry corners were read on the wall / column handles
  instead (R-T368-6, test `test_counter_reflex_is_not_a_wall_corner`). The 17 other rooms' reflexes were each matched to
  a wall or column entity (section 3).
- Door frames: nothing drawn decides whether an architrave covers the tile edge; 73.10 m.l stays HELD with its range.
  Not an owner question here (ERS s.2.7: a designer / detail item; the door schedule and frame detail are the evidence
  that would settle it). Listed for the RFI revalidation (Lead).

## 8. Rules, code, tests

- `research/agents_t368/t368_edge_rules.py` (generic, unwired): R-T368-1 .. 6 (docstring), corner classes (reflex =
  external, with mirror / clockwise / unit invariance), wall-only corners (R-T368-6), edge builders, opening perimeter
  in the band, finish alternatives, `check_ledger` refusals, `refuse_summed_finishes`.
- `research/agents_t368/t368_alsenan.py` (development villa), `EDGE_LEDGER_T368.csv`, `CROSSCHECK_T368.csv`, `summary.json`.
- `tests/t368_exposed_tile_edges` (32): villa E368 hand fixture (bath 2.40 x 1.80 with a column 0.40 x 0.30 proud:
  2 x 3.10 = 6.20 m.l; door 0 .. 5.20 HELD; flush window 2.80 not exposed; open pantry 3 x 3.00 = 9.00 m.l), rotation /
  mirror / mm-m / clockwise invariance, drawn architrave, frameless doorway, head above band, floor-level window;
  adverse: both finishes summed, an internal corner as exposed, an edge under a frame counted, a door exposed without
  frame evidence, HELD band as 0, HELD edge with a figure, duplicate edge, no line id, band or width in mm, degenerate
  polygon, a counter reflex counted as a wall corner; Alsenan pins (byte-identical rebuild, totals, line binding, HELD
  rooms held, windows never exposed).
- No engine / method / registry change; B4-10 stays IMPLEMENTED_NOT_INTEGRATED (a lane I package would add one m.l line
  per tiled room bound to its FIN.WALL.TILE line, finish HELD).

## 9. Lessons-register proposals (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-30 | the pantry room polygon's only reflex vertex is a counter end, not a tile arris | a room polygon closed on furniture / zone lines | corners of a finish are read between two solid faces (wall / column entities) only (every villa, R-T368-6) | test_counter_reflex_is_not_a_wall_corner | PROPOSED |
| 2026-10-30 | an exposed-edge total could add the 45-degree and the profile m.l on the same edges | two owner rules for one edge read as two items | one edge, one finish; with no printed finish both shown, choice HELD, total never summed (every villa, R-T368-4) | test_both_finishes_summed_refused | PROPOSED |

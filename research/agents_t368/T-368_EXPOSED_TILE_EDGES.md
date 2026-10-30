# T-368: EXPOSED WALL-TILE EDGES (BOQ family B4-10; UP-CER-006 45-degree edge / UP-CER-007 steel profile), edge by edge (development villa; every villa by R-T368-1 .. 7)

Worker 3, claim 2026-10-30 11:03 UTC, run session_01E6cPnf2dNDDd7Uxq92dPtG (lane I had no TODO; READY = 2, so a
standalone piece is allowed). Research only: no engine module, method, rule / knowledge version, registry file,
candidate line, released line or V2.9 cell changed; nothing released, nothing VERIFIED by this task. ERS applied: s.2.1
(physical element first), s.2.2 (owner rule and drawing reading side by side), s.2.3 (own vector reading), s.3 (one edge,
one face, one finish), s.4 (rules + normal and adverse tests), s.7 (lesson rows, section 9).

## 0. r2 (worker 2, 2026-10-30 12:41 UTC, run session_01E6cPnc7CN49QfNy8pGJ6VX): Checker D-T368-1

**Defect accepted.** r1 gave the GF-14 open side's WALL_END (at BC) and FLAT_STOP (on 222) the full 3.65 m band. The
plan draws a pair 2DB / 2DC across that open side on layer 2, whose layer linetype is HIDDEN (every other wall layer
CONTINUOUS), 0.150 apart = the D2 / 20C wall thickness and collinear with those two faces, over the full 1.256 m from
lift face 222 to wall end BC: an element above the cut, in the plane of the wall. r1 read it as 'open side (layer 2)'.

**Search for the head level (ERS s.2.2 / s.2.3), own reading this run** (Drive 'Alsenan chalet project', cited by title;
nothing committed): P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 `ab54dd55`) and ST7757 dxf.dxf (sha256 `9f9d1179`).
The GF plan maps into the ST GF roof-slab plan with the T-108 column-fit translation (202.3333, 841.6415) m, re-checked
here on the nearest column: arch S-COL.BON 2F8A lands on ST S-COL.BON 338 with 0 mm residual on all four corners.
1. **ST GF roof-slab plan over the opening:** a shapely intersection of every LINE / LWPOLYLINE / POLYLINE / HATCH /
   block line with the strip under 2DB / 2DC (inset 7 mm from 222 and BC) returns ONE entity: slab bar 4A8 (layer
   S-REIN-SLAB), beside slab text 4A7 '5 dia 10/m'. No beam band, no drop, no slab edge or opening crosses the opening;
   the nearest beam band (28E / 291, 0.20 wide) runs along the lift face, not across. So the element is **not a GF roof
   beam** and no printed beam depth gives its soffit (UP-MAS-HPIECE-001 R4 cannot apply).
2. **Convention check (not an assumption):** the GF plan has one other HIDDEN wall-width pair across a wall gap, 33C / 33D
   (0.200 x 0.900, stair side); it DOES lie under ST beam band 292 / 296. A HIDDEN pair alone therefore does not say
   'beam' or 'header': the slab plan decides, and at GF-14 it shows none. What the drawings support is a non-structural
   header (0.150 wall over the opening, up to the slab), head level not printed.
3. **Sections / elevations:** no section cuts GF-14 (merged T-221 SECTION_CUTS: GF A-A nearest wet room 0.58 m away,
   GF B-B 1.07 m); GF-14 is an internal lobby, on no elevation. No level mark in the room.
4. **Fallbacks:** Q-55 C (internal door 2.20 m, ASSUMED) is a DOOR-height fallback; this is a doorless opening under a
   header, so it is not used (no borrowed value). No owner rule gives the head of a passage.

**Result (R-T368-7, HELD by name OVERHEAD_ELEMENT_HEAD_NOT_ESTABLISHED):** GF-14#WEND HELD head .. 3.65 m.l,
GF-14#FSTOP HELD head .. 3.65 m.l (never 0, never the full band by default), GF-14#OS1#HEAD (head arris on the GF-14
face, the head's underside edge) HELD 0 .. 1.256 m.l (0 if the head is at or above the 3.65 tile top, 1.256 if below).

**R-T368-7 applied to the other open side (pantry GF-07), read on the slab plan too.** The architectural plan draws no
HIDDEN line across the pantry's open edge (layer-5 CONTINUOUS AD + B3 only), but the ST GF roof-slab plan does carry a
beam over it: CB4 span 1 (band 288 / 285, B 20 / H 50, schedule p.11; merged T-252 r2 ledger BM-GF-021#BAND0021.1)
runs ALONG the open edge, face 285 exactly in its plane, from column 362 over the north end (the wall end at AC) to the
B27 east face 325. Head at the wall end = 4.50 - 0.50 - 0.10 floor allowance = 3.90 m >= 3.65 tile top (owner-manual
frame of the band; drawing-derived build-up b 0 .. 0.10 gives 3.90 .. 4.00): **full band confirmed**. B27 (90 x 85, ST
p.10, S-BEAM faces 326 / 325) crosses the open edge obliquely 0.34 .. 1.86 m north of the south end (325 at the edge
line 38.403, 326 at 36.887, the end at 36.547, ST frame m): the flat stop at the south end is under no beam: **full
band confirmed**. The pantry's 7.30 m.l stand with the head now drawing-confirmed (band still ASSUMED — OWNER-APPROVED);
the rule docstring says every open side is read on the slab plan as well (crossing 'BEAM'), with tests.

**F-T368-3 (ceilings / wall-tile top, not this ledger).** B27's soffit in the same frame is 4.50 - 0.85 - 0.10 = 3.55 m,
0.10 m BELOW the pantry's 3.65 tile top / decor-ceiling underside: the owner's 0.60 m beam allowance (G1) is exceeded by
this 0.85 m beam, so inside B27's footprint across the pantry (west wall to the open edge) the tile top and the decor
ceiling cannot be at 3.65 m. The pantry is also 39 % under the 'Sunken slab.' hatch 287 (T-209, drop not printed). For
the ceiling line (T-284 / T-271) and the wall-tile area (T-312) as a drawing-derived difference beside the owner
method (G1: 'show both results'), not a silent change; no B4-10 edge moves (no tiled face meets B27 in the open plane).

**Totals restated:** determinate exposed **31.65 m.l** (external corners 24.35 + pantry wall end 3.65 + pantry flat
stop 3.65; was 38.95, -7.30 m.l, -18.7 %), finish HELD between 45-degree 31.65 **or** steel profile 31.65 (never 63.30);
HELD at GF-14: 2 edges head .. 3.65 each (upper 7.30) + head arris 0 .. 1.256; doors HELD 0 .. 73.10 unchanged; the
annex / level-HELD rooms unchanged. Freelancer 0 m.l (no edge / profile row): RULE_DIFFERENCE (scope), unchanged.

**Finding to the Lead (lane I, for T-326 / T-327; no exported quantity moves here):** merged T-312 row GF-14|OPEN reads
the open side as 'no wall, nothing to tile'. If the header exists, its GF-14-side face above the head (1.256 m x
(3.65 - head)) is a tiled face of this wet room that T-312 omits, and its lobby-side face / soffit belong to their own
finish lines. T-312's line L-fa408571a8adcfaf1a1f is BLOCKED_RFI (blank), so nothing exported changes now; the head level
is a designer item (RFI list: 'head level of the 1.256 m passage between the GF wash lobby and the lift lobby'), not an
owner question (ERS s.2.7 not met: a drawing fact, not a rule).

The r1 sections below stand as checked by the Checker except where this section restates GF-14 and the totals.

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

## 3. Edge by edge (EDGE_LEDGER_T368.csv, 94 rows in r2; CROSSCHECK_T368.csv)

| Room | Line (FIN.WALL.TILE) | Band m | External corners (handles) | Wall ends / flat stops | Exposed m.l | Doors HELD (range m.l) | Windows (under frame) |
|---|---|---|---|---|---|---|---|
| 1F-07 laundry | L-b2077eee5a71a975bd74 | 3.35 OA | 3: wall corner ACF / B07, lift corner column 2FF0 (B06 / B14), column 2FED proud 0.05 | - | **10.0500** | D-1F-06, D-1F-05: 0 .. 10.50 | W21 2.80 |
| 1F-09 bath | L-086e72207311265f81ab | 3.35 OA | 1: column 2FE7 proud 0.05 | - | **3.3500** | D-1F-07: 0 .. 5.20 | W23 2.80 |
| GF-13 bath | L-a3cb2c8a9b6080769ebc | 3.65 OA | 1: column 2F84 proud 0.05 | - | **3.6500** | D-GF-12: 0 .. 5.20 | W06 2.80 |
| GF-14 wash lobby | L-fa408571a8adcfaf1a1f | 3.65 OA | 1: obtuse 135-degree corner, walls BE / 318 | r2: open side under the HIDDEN header 2DB / 2DC: WALL_END (BC) and FLAT_STOP (222) HELD head .. 3.65 each, head arris HELD 0 .. 1.256 (R-T368-7) | **3.6500** (r1 10.95) | D-GF-11, D-GF-12: 0 .. 10.40 | - |
| GF-07 open pantry | L-f5c5a1a9c9ee2b644cb5 (T-315 ADD) | 3.65 OA | 1: column 2FAE proud 0.05 below wall 158 | open edge B3 (layer 5): north end = free end of wall 159 (AC) WALL_END; south end = wall A6 continues as 104 FLAT_STOP | **10.9500** | D-GF-06: 0 .. 5.40 | W10 5.00, W09 6.00 |
| 1F-02, 1F-03, 1F-08, 1F-12, 2F-02, GF-12, GF-16 | own lines (ledger) | 3.35 / 3.65 OA | 0 (rectangles / pentagon) | - | 0.0000 | one door each: 0 .. 5.20 | W20, W19, W22, W18 5.32, W28, -, W07 |
| GF-06 kitchen (annex) | L-c330b8dc47261d5ada7e | HELD | 4: column 2FB7 both sides, column 2FB1, WC block corner (135 / 14F) | - | HELD (4 edges, never 0) | D-GF-05 HELD | W08 under frame |
| GF-02 (annex) | L-d0858b30e0ea869bd047 | HELD | 1: column 2FA5 | - | HELD (1 edge) | D-GF-02, arch A-GF-01 HELD | - |
| GF-03, GF-05 (annex), GF-10, GF-11 (level not drawn) | own lines | HELD | 0 | - | 0 | doors / doorway HELD | W05 under frame |

Hand check (not the code's arithmetic): laundry 3 x 3.35 = 10.05; GF-14 1 x 3.65 = 3.65 (r2); pantry 3 x 3.65 = 10.95;
GF-13 3.65; 1F-09 3.35; total 31.65 m.l (r1 38.95). Doors: 12 x (2 x 2.20 + 0.80) = 62.40 + (4.40 + 0.90) 5.30 + (4.40 + 1.00) 5.40 =
73.10 m.l. Windows (not exposed): W20 2 x (2.50 - 1.70) + 0.60 + 0.60 = 2.80; W18 2 x (3.00 - 0.84) + 0.50 + 0.50 = 5.32;
W09 2 x 1.50 + 1.50 + 1.50 = 6.00 (= ledger).

## 4. Totals (summary.json)

| Quantity | m.l | Status |
|---|---|---|
| EXTERNAL_CORNER | 24.35 | ASSUMED — OWNER-APPROVED (band Q-48 A); corner count DRAWING-CONFIRMED |
| WALL_END | 3.65 (pantry) | same |
| FLAT_STOP | 3.65 (pantry) | same |
| **Exposed, determinate (12 rooms)** | **31.65** (r1 38.95) | finish HELD: 45-degree (UP-CER-006) 31.65 **or** steel profile (UP-CER-007) 31.65, never 63.30 |
| GF-14 open side under the HIDDEN header (r2) | HELD: wall end + flat stop head .. 3.65 each (upper 7.30); head arris 0 .. 1.256 | OVERHEAD_ELEMENT_HEAD_NOT_ESTABLISHED |
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
room boundary x 3.00 m with no edge item. **Engine (this ledger, r2) 31.65 m.l determinate + 0 .. 73.10 m.l doors HELD + GF-14 open side HELD (up to 8.556) vs
freelancer 0 m.l.** Verdict proposal: **RULE_DIFFERENCE** (scope: the owner rules UP-CER-006 / 007 measure the exposed
edge as its own item; his method has none). No percentage is meaningful against 0.

## 7. Findings

- **F-T368-1 (FLAT_STOP).** At a flat stop (pantry south end; GF-14 west end, HELD in r2) no second tiled face meets the tile, so a
  45-degree mitre has nothing to meet; physically only a stop profile (UP-CER-007) or a finished-edge tile closes it. The
  owner rules give the two finishes as alternatives without naming where each applies; this ledger does NOT choose: both
  stay shown on the flat-stop m.l and the choice stays HELD (a rule-scope note for the rule library, not an owner question:
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

- `research/agents_t368/t368_edge_rules.py` (generic, unwired): R-T368-1 .. 7 (docstring; r2 adds `OpenSide`,
  `open_side_edges`, `check_open_sides`, the HEAD_ARRIS type and held totals by type), corner classes (reflex =
  external, with mirror / clockwise / unit invariance), wall-only corners (R-T368-6), edge builders, opening perimeter
  in the band, finish alternatives, `check_ledger` refusals, `refuse_summed_finishes`.
- `research/agents_t368/t368_alsenan.py` (development villa), `EDGE_LEDGER_T368.csv`, `CROSSCHECK_T368.csv`, `summary.json`.
- `tests/t368_exposed_tile_edges` (43; r2 adds 11 for R-T368-7: slab-plan BEAM over an open side (20 x 50 full band,
  20 x 90 head 2.95: 2 x 2.95 + 2.00 = 7.90 m.l hand), BEAM with no printed depth refused, Alsenan pantry; HIDDEN header above the decor ceiling = full band
  (normal), head 2.40 under a 3.10 band = 2 x 2.40 + 1.20 = 6.00 m.l (hand), clear open side, head unknown HELD by name,
  **full band with head unknown refused (adverse, the r1 defect)**, missing head arris refused, a solid line is no open
  side, units; Alsenan GF-14 held / pantry determinate): villa E368 hand fixture (bath 2.40 x 1.80 with a column 0.40 x 0.30 proud:
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
| 2026-10-30 | a wall-tile edge at an open side given the full band where the plan draws a HIDDEN overhead pair | layer linetype not read; open side assumed clear to the ceiling | read the linetype of every line closing an open side; HIDDEN = overhead element; the slab plan decides beam vs header; head HELD until established (every villa, R-T368-7) | test_hidden_pair_head_unknown_full_band_refused | PROPOSED |
| 2026-10-30 | an open side's overhead element exists only on the structural slab plan (a beam band along the pantry's open edge, nothing HIDDEN on the architectural plan) | the architectural plan alone does not draw every overhead element | read every open side on the slab plan too; head = storey - printed depth - floor allowance (every villa, R-T368-7) | test_slab_plan_beam_with_no_printed_depth_full_band_refused | PROPOSED |

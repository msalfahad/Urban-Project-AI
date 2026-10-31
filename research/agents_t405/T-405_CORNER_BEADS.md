# T-405: PLASTER CORNER BEADS / PROFILES (BOQ family B4-09, m.l), arris by arris (development villa; every villa by R-T405-1 .. 8)

Worker 2, claim 2026-10-31 18:44 UTC, run session_01E6cPndBBWVYpntQRM6LEgo. Research only: no engine module, method, rule /
knowledge version, registry file, candidate line, released line or V2.9 cell changed; nothing released, nothing VERIFIED
by this task. B4-09 stays IMPLEMENTED_NOT_INTEGRATED (`engine/source/corner_bead.py` is unread by any method and
untouched). ERS applied: s.2.1 (physical element first), s.2.2 (owner method and drawing method side by side), s.2.3
(own vector reading), s.3 (one arris, one bead), s.4 (rules + normal and adverse tests), s.7 (lesson rows, section 9).

## 1. Result (engineering terms)

| Scope / class | Edges | Owner manual method (m.l) | Drawing-derived method (m.l) | Status |
|---|---|---|---|---|
| Interior EXTERNAL_CORNER + WALL_END (columns proud, wall corners, a wall nib) in 7 plastered rooms | 39 | **136.05** (21 x 3.35 + 18 x 3.65) | HELD (plaster top 4.04 / 4.34 on a HELD datum, DCR-6) | ASSUMED — OWNER-APPROVED (G1 / Q-43 / Q-48 A height); count DRAWING-CONFIRMED (own reading, handles) |
| Interior door rings 2h + w, each PLASTERED face once (26 faces of 19 doors) | 26 | **139.90** (D-GF-07 7.00 printed + 25 x 5.2 .. 5.4 at Q-55 C 2.20) | 139.90 (the head lies below every plaster top shown: R-T405-3) | 132.90 ASSUMED — OWNER-APPROVED (Q-55 C) + 7.00 DRAWING-CONFIRMED |
| **Interior measured** | | **275.95** | **139.90** | HELD / UNKNOWN never inside |
| Exterior vertical convex arrises GF / 1F / 2F (T-162 r2, T-172 VERIFIED geometry) | 26 | 124.70 | 124.70 | DRAWING-CONFIRMED |
| Exterior wall ends at the two passage mouths | 8 | 43.10 | 43.10 | DRAWING-CONFIRMED |
| Exterior window rings (outer jambs + head, T-313 r2), arched heads on the developed arc (T-377) | 25 | 103.6831 | 103.6831 | DRAWING-CONFIRMED |
| Exterior door rings (outer face) | 7 | 39.20 | 39.20 | 32.20 ASSUMED — OWNER-APPROVED (Q-55 C) + 7.00 DRAWING-CONFIRMED |
| **Exterior measured** | | **310.6831** | **310.6831** | |
| **All measured** | | **586.6331** | **450.5831** | |

HELD by name (count kept, length never 0; physical length shown where it is measured elsewhere):

| Class | Edges | Cause (name) | Physical edge |
|---|---|---|---|
| Stair-hall column arrises ST-GF / ST-1F / ST-2F | 6 | owner shaft height Q-72 open | - |
| Parapet outer + inner top arrises | 8 runs | COPING_NOT_SPECIFIED (a cap hides both top arrises: OD-V3B-8 'never on a hidden edge'; RFI A13, T-324) | 271.963 m.l |
| Window sill edges | 23 | SITE_METHOD_NOT_RECORDED (OD-V3B-8 'where the site method requires'; sill material A13) | 29.53 m.l |
| W02 outer jambs, W03 (curved floor glazing), W17 (archivolt) | 3 + 2 room sides | heights / developed outlines HELD (T-313, T-238, D-53) | W02 head 6.33 |
| Arches A-GF-01 (GF-01 face), A-1F-01 | 2 | springing not printed (D-45) / arch drawn on no view; Q-55 C is a door height, not a springing (R-T405-7) | A-GF-01 head on the arc 1.223795 |
| Lift entrances GF / 1F / 2F (hall faces) | 3 | LIFT_ENTRANCE_HEAD_NOT_ESTABLISHED (landing frame by supplier; T-401 owns the shaft) | - |
| Stair hall -> GF-11 doorless 0.90 opening; GF-08 11.22 m zone edge | 2 | OPEN_SIDE_HEAD_NOT_READ (R-T368-7 reading pending) / ZONE_EDGE_NOT_READ | - |
| D-1F-07 far face (unlabelled lobby by 1F-10); gate D-GF-15 | 2 | FACE_NOT_IN_FACE_LEDGER / gate width UNRESOLVED | D-1F-07 5.20 |
| Stair edges, void V01 slab edge, ceiling / beam edges | 3 | stair soffit BLANK (T-284); CEILING_FINISH_AT_VOID; CEILING_TYPE_PER_ROOM (O-P8-02) | - |
| Exterior slab edge, arch frames, drip, boundary fence | 4 | Q-68; D-45; A13 (a drip is not an angle bead); T-396 / T-404 | - |
| STOP_END (horizontal plaster termination along the room perimeter) | 14 rooms | STOP_END_SCOPE_NOT_IN_URBAN_RULE | 289.281 m.l |

## 2. The physical element (ERS s.2.1)

A plaster corner bead is a galvanised steel angle fixed on a CONVEX arris before the plaster coats; it exists only where
two plastered surfaces meet at an outside corner, over the height where BOTH sides are plastered. Not a bead: a concave
corner; an edge against a frame drawn flush with the face (no arris); an edge with tile, cladding or no plaster on one
side (Q-37 A: tile owns the face, the trim is B4-10 / T-368); an edge hidden above a ceiling or under a coping; a
horizontal stop-end (not an arris). Owner basis searched first (WORKFLOW_CONTROLS s.4): URBAN-FINISH-EXTRAS-SEPARATE-
ITEMS@v1 (separate m.l item wherever geometry supports it) and OD-V3B-8 STEEL_PLASTER_ANGLE_BEADS (owner 2026-10-04:
door / opening jambs, window edges incl. below / around where the site method requires, external plastered corners;
never hidden, never non-plastered, never fully tiled). No owner question is needed: every class either follows OD-V3B-8
or is HELD by a drawing / specification fact (designer or RFI items, ERS s.2.7 not met).

| Element | (1) Drawings | (3) Owner rules | Result |
|---|---|---|---|
| Interior arrises | engine room polygons (ARCH_TAKEOFF_V2.9 run on P7757.dxf `ab54dd55`); every reflex vertex named by the S-COL.BON / wall entity within 12 mm | OD-V3B-8 'external plastered corners' | 46 reflex vertices: 45 plaster arrises + 1 pantry tile corner (T-368) |
| Height of an arris | plaster top 4.04 (1F / 2F) / 4.34 (GF) on a HELD roof datum (T-292 / T-237) | G1, Q-43 / Q-48 A: 3.35 (1F / 2F), 3.65 (GF); annex G2 / Q-54 B HELD; shafts Q-72 HELD | owner method measured, drawing method HELD, side by side |
| Door rings | T-313 r2 (MERGED): width, wall thickness, one reveal through the wall (UP-FIN-PLASTER-001) | Q-55 C 2.20 m; OD-V3B-8 'door / opening jambs' | 2h + w per plastered face; head below every plaster top shown, so the plaster top does not decide it |
| Window room side | T-313 r2: frame band drawn FLUSH with the room face on all 27 straight windows | - | no room-side arris: 0, DRAWING-CONFIRMED (27 rows) |
| Window outer side | T-313 r2 outer jambs + head; T-238 / T-377 developed outlines W15 / W16 / W26 | OD-V3B-8 'window edges' | measured; sill edge HELD (site method) |
| Curved walls / glazing | W03 / W17 drawn arcs tessellated in the polygons (24 / 11 / 35 facet vertices) | - | one smooth surface: no arris (R-T405-5) |

## 3. Interior arris by arris (EDGE_LEDGER_T405.csv)

| Room (FIN.PLASTER line) | Vertices (handles) | m.l (owner) |
|---|---|---|
| 1F-01 (L-af9621f43bc316a871ea) | columns 2FFC x 2, 3002 x 2 | 4 x 3.35 = 13.40 |
| 1F-04 (L-971f0bdaf68d7fd0966c) | column 2FFC x 2 (its 1F-04 side; distinct vertices from the 1F-01 side, key check) | 6.70 |
| 1F-11 (L-31db3c83552682d92ca3) | columns 2FEA, 300B, 2FDB x 2; wall nib C09 / C0B / C15 x 2 (counter lines B0C / C17 end there too: walls decide); wall corner C0A / C16 | 7 x 3.35 = 23.45 |
| 1F-13 (L-9b4a7bab033d677e2017) | columns 300E x 2, 3008 x 2; wall corners AEB / AF7, AFB / B10; wall AFE / B16 at column 2FF3 | 7 x 3.35 = 23.45 |
| 2F-01 (L-ae0cdd794cc5fdbe0c29) | wall 128A / 129A at column 2F72 | 3.35 |
| GF-08 (L-8cecb1d010d5aafbf25d) | columns 2F8A, 2FB4, 2FD2, 2FC6, 2FC3, 2FC0 x 2 each; wall 337 beside 2FC6 | 13 x 3.65 = 47.45 |
| GF-15 (L-0d93f2209cd9bb827c0a) | wall corner 2DE / 2F0; columns 2FCC x 2, 2FC9 x 2 | 5 x 3.65 = 18.25 |
| ST-GF / ST-1F / ST-2F | columns 2FBD, 3005, 2F78 x 2 each | HELD (Q-72) |
| 1F-10, 2F-03, GF-01, GF-04 | no reflex vertex (GF-01 convex with a rounded corner) | 0 (no arris) |
| GF-08 #V48 | column 2FAE in the open pantry: tile corner of T-368 | NOT A BEAD |

Hand check (independent of the code): corners 21 x 3.35 = 70.35 and 18 x 3.65 = 65.70, total 136.05 m.l; door
faces by ring width in section 3a (6 x 5.20 + 9 x 5.30 + 10 x 5.40 + 7.00 = 139.90 m.l).

### 3a. Door faces, exact (from the CSV)

| Ring | Faces | m.l |
|---|---|---|
| 7.00 (D-GF-07, printed 2.50 x 2.00) | 1 | 7.00 |
| 5.40 (w 1.00) | D-1F-02 x 2, D-1F-03 x 2, D-2F-01, D-GF-01, D-GF-08 x 2, D-GF-13 x 2 | 10 x 5.40 = 54.00 |
| 5.30 (w 0.90) | D-1F-05, D-1F-08 x 2, D-1F-09 x 2, D-2F-02 x 2, D-GF-03, D-GF-09 | 9 x 5.30 = 47.70 |
| 5.20 (w 0.80) | D-1F-01, D-1F-04, D-1F-10, D-2F-03, D-GF-04, D-GF-14 | 6 x 5.20 = 31.20 |
| **Total** | **26** | **139.90** (= ledger) |

## 4. Cross-trade and double count (acceptance c)

| Check | Result |
|---|---|
| One vertex, two rooms | 46 vertex keys (floor + mm position) all distinct (`--geometry`); 1F-01 / 1F-04 see the two sides of column 2FFC as different vertices |
| One face, two labels | 1F-13 / ST-1F and 2F-01 / ST-2F share an engine polygon: a door on that face is ONE ring (D-1F-02 has 2 faces, not 3) |
| Bead on a tiled face | 0: 19 door faces on wet rooms, the pantry column and A-GF-01's GF-02 side are NOT A BEAD rows (tile trim B4-10 / T-368) |
| Interior vs exterior ring of one opening | two faces, two arrises (R-T405-4): 7 exterior doors carry an outer ring AND an inner ring (or a tiled inner face) |
| Exterior opening rings vs T-162 'opening arrises' 137.110 | the T-313 r2 rings supersede T-162's opening rows (T-313 EDGE_RECONCILIATION, MERGED); the 6 assumed doors 32.20 + D-GF-07 7.00 = 39.20 (= T-162 + D-GF-07) |
| Arched heads | W15 / W16 / W26 on the developed outline 6.8461 / 6.8461 / 4.0709 (rectangle 7.75 / 7.75 / 4.60 refused): -2.3369 m.l vs the rectangle |
| Reveals (m2) | FIN.PLASTER 'door jambs and head' / ARCH.WINDOW_REVEAL carry the reveal SURFACE; the bead is the m.l on the arris: no quantity moves |

## 5. Engine vs freelancer (acceptance; who-is-right proposals)

His interior line 'زوايا ونهايات م.ط' 770.75 m.l (paid at half, 385.375) is his detail sheet rows 4 .. 44: column A
'ends' 282.85 + column B 'corners' 487.90 (raw rows in tests/alsenan/registers_b1, file PLS). Grouped by physical class:

| His rows | His m.l | Engine | Verdict proposal |
|---|---|---|---|
| A: room-perimeter 'ends' (per room = perimeter less doors) | 282.85 | STOP_END HELD (physical 289.281, +2.3 %) | RULE_DIFFERENCE (scope): a horizontal stop-end, not an arris; no Urban rule asks for a stop profile |
| B: room corners at 3.4 .. 3.8 m | 100.00 | 136.05 corners (owner method) + 6 shaft corners HELD | count ENGINE_RIGHT (every arris at a drawn column / wall entity, 0.05 m projections included); height RULE_DIFFERENCE (storey vs G1) |
| B: door rings 14 doors x 2 faces x 5.70 | 159.60 | 139.90 (26 plastered faces of 19 doors at 2.20) | UNRESOLVED count (14 vs 27 census doors); height RULE_DIFFERENCE (2.35 vs Q-55 C 2.20) |
| B: window / door perimeters (rows 29-41) | 155.30 | room side 0 (flush frames); outer rings in the exterior ledger | ENGINE_RIGHT for the room side (T-313: frame flush on all 27 straight windows) |
| B: bathroom windows | 26.40 | NOT A BEAD (tiled) | ENGINE_RIGHT (Q-37 A) |
| B: lift doors | 17.40 | HELD (lift entrance) | UNRESOLVED |
| B: stair stringers | 29.20 | HELD (stair soffit BLANK) | UNRESOLVED |
| **Total** | **770.75** | **275.95 measured** | like for like (corners + door rings): his 259.60 vs engine 275.95 (+6.3 %) |

Exterior: his 1,297.35 m.l (A 547.47 + B 749.88) vs engine 310.6831 measured (-76.1 %): the difference is scope, not
measure. His B carries the parapet tops as 2 edges per metre (280.59; engine HELD, physical 271.963 under a coping not
specified), the boundary wall (91.44 + A part; T-396 HELD) and the drip edge (181.70; a drip profile, not an angle bead,
HELD A13); his A column is entered per facade by hand. Like for like (OWNER_NOTES_SIGMA correction 2026-10-22): his
950.56 vs drawing 457.095 + 58.60 door jambs (T-162). Verdict proposal: RULE_DIFFERENCE (parapet / drip / fence scope,
OD-V3B-8 'never on a hidden edge') with the vertical corners and opening rings ENGINE_RIGHT on the drawing.

## 6. Rules, code, tests

- `research/agents_t405/t405_bead_rules.py` (generic, unwired): R-T405-1 .. 8 (docstring), `arris_vertices` (reflex
  vertex >= 10 deg, tessellated-arc facets excluded, mirror / clockwise invariant), `Top` / `Face` (owner and drawing
  plaster tops, HELD = no figure), `corner_edge`, `opening_face_edge` (2h + w per plastered face; tiled face NOT A BEAD;
  head above the lowest plaster top HELD; arc head developed only; door height refused for a passage / arch),
  `flush_window_face`, `held_edge`, `cited_edge`, `check_ledger` / `check_corner_keys` refusals, `totals` per status.
- `research/agents_t405/t405_alsenan.py`: `--write` / `--check` (byte-identical, committed inputs only), `--geometry
  <P7757.dxf> <ARCH_ROOMS.json>` (this run: 12 engine rooms OK, 46 distinct vertex keys, every handle within 12 mm).
- `tests/t405_corner_beads` (21 pass): villa E405 bedroom 5.00 x 4.00 with a column 0.50 x 0.10 proud and a wall nib
  0.15 x 0.60: 4 x 3.10 = 12.40 m.l (hand); door 0.90 x 2.20 between the bedroom and a tiled bath: 5.30 on the bedroom face,
  NOT A BEAD on the bath face; flush window 0; arched window r 0.60 semicircle 2 x 1.40 + 1.884956 = 4.684956 (chord
  refused); a curved wall in 8 facets = no arris; rotation / mirror / clockwise invariance; adverse: corner counted twice,
  bead under tile, arc as chord / rectangle, HELD as 0, HELD without a cause, door height borrowed for a passage, height
  in mm, degenerate polygon, unknown face finish; Alsenan pins (rebuild, totals, invariants).

## 7. Proposal for a lane I row (not done here)

One B4-09 m.l line per plastered room (bound to its FIN.PLASTER line: corners + door rings of that face) and one
exterior line per floor (bound to FIN.EXT.FINISH, T-314), every HELD class carried blank with its cause; finish
'galvanised steel angle bead' per OD-V3B-8; payable convention (the freelancer's '2 m = 1 m', half rate) kept apart from
the physical m.l (OWNER_NOTES_SIGMA correction).

## 8. What is missing / uncertain

- Shaft heights (Q-72), annex rooms have no arris anyway; the drawing-method corner length stays HELD on the roof datum.
- Lift entrances, the GF stair-hall -> GF-11 opening and the GF-08 zone edge: heads not read (R-T368-7 slab-plan reading).
- Parapet tops / sills / drips: a specification fact (RFI A13), not an owner rule question.
- Door frame / architrave detail is not drawn: OD-V3B-8 still places beads on door jambs (owner decision), so the door
  rings are ASSUMED — OWNER-APPROVED; a drawn architrave detail would not remove the bead (it is fixed under the plaster).

## 9. Lessons-register proposals (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-31 | the freelancer's window perimeters (rows 29-41) are counted as interior beads | a window ring copied to the room face without reading the frame position | a frame drawn flush with the room face leaves no room-side arris; outer rings belong to the exterior ledger (every villa, R-T405-6) | test_flush_window_has_no_room_side_arris | PROPOSED |
| 2026-10-31 | curved walls give dozens of small reflex vertices in a room polygon | a drawn arc tessellated into chords | equal facets with equal turns are one smooth surface, never arrises (every villa, R-T405-5) | test_tessellated_arc_is_one_surface_not_arrises | PROPOSED |
| 2026-10-31 | a stop-end line along the room perimeter is priced inside 'corners' | 'ends' and 'corners' in one line | a horizontal stop-end is not an angle-bead arris; it is its own profile class, HELD until a rule asks for it (every villa, R-T405-1) | test_alsenan_totals_pinned (STOP_END held) | PROPOSED |

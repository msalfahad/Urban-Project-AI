# T-444 Lift-shaft ground-slab cell I-07 (L-41cfb82e): the held cell bound to its own pieces (lane S, research only)

Worker 1, 2026-11-01 23:25 .. UTC, branch `agents/task-T-444`. No engine module, candidate line, rule version, method or
released cell changed; nothing released. Development villa (Alsenan), not an accuracy claim; the method is for every
villa whose lift pit stands on its own raft. ERS s.2.1 - 2.6, s.3, s.4, s.7 applied. Drawings named by Drive folder and
title; entities by DXF handle; values, sizes and engine ids only.

## 0. Sources and run

Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha `9f9d1179`), decoded into `.work/private` only. The T-391 own
partition rebuilt with the merged extractor and asserted face by face against `OWN_GROUND_T391.json` (180 faces). Route
G's own plan records of the same DXF (`research/agents_t387/t387_geometry.py`, output in `.work/private/t444`), the cell
SITE-c1089bdb registered onto the DXF by the pit ring (route G SH08 ring box 2.200 x 2.200 = S-BW 7C2 2.200 x 2.200; size
check asserted). Candidate line ids from `research/agents_t347/CANDIDATE_V3024_BURIED_LINES.json` (= V3.0.29 .. V3.0.37
for this family, T-428), lift lines from T-401 (merged).

```
.work/venv/bin/python -I research/agents_t387/t387_geometry.py <private>/ST7757.dxf <private>/t444/geometry.json
.work/venv/bin/python -I research/agents_t444/t444_alsenan.py --dxf <private>/ST7757.dxf --geometry <private>/t444/geometry.json --write
.work/venv/bin/python -I research/agents_t444/t444_alsenan.py --check
```

Files: `t444_rules.py` (R-T444-1 .. 7, pure + shapely partition), `t444_alsenan.py`, `PIECES_T444.json` (15 pieces:
kind, area, sizes, DXF edge handles, engine in-cell areas, foundation plan below, owner line; no coordinates),
`summary_t444.json`. Tests `tests/t444_lift_gs_cell` (21).

## 1. The physical element (ERS s.2.1)

Ground slab on grade 'T=10cm' (GROUND BEAMS PLAN; T-206 DRAWING-CONFIRMED; route G t_basis SHEET_UNIFORM), cast between
ground-beam faces (C1, T-391), around the lift pit. The lift pit (T-401 merged, ST p.14): raft FF 4.60 x 4.50 x 0.55
(FP 1B2B) at founding level; pit floor = the raft top, no slab of its own; RC ring '20' (S-BW 7C2 2.20 / 7BE 1.80 on
the ground-beams plan = FP 10EB / 10EA) from the raft top to the slab-on-grade top; four lift columns on the ring (C9
1EC = FP 1090, 0.25 x 1.00; C1 / C2 / C2 1EF / 1F2 / 1F5, 0.20 x 0.50).

Why the engine holds the cell: route G's cell outline (41.3262 m2) contains the whole C9 outline, cuts it as a hole
(0.25 m2) and flags 'free_columns 1' -> region UNRESOLVED ('1 free-standing column(s) inside a ground-slab cell'). C9 is
not free: it stands on the pit ring (R-T444-4). The other three lift columns lie on the cell edge, not inside it. The
cell outline also takes 2.8125 m2 of the shaft and 0.880 m2 of the ring, which are not slab.

## 2. Piece table (acceptance: one table per piece; PIECES_T444.json)

Drawing: GROUND BEAMS PLAN of 'ST7757 dxf.dxf' (layer 1 bands, S-COL.BON, S-BW); FP = FOUNDATION PLAN below (frame
offset T-141, checked: 10EB / 10EA land exactly on 7C2 / 7BE).

| Piece | Kind | Edge handles | Size (m) | Own m2 | In engine net m2 | T | m3 | Owner line |
|---|---|---|---|---|---|---|---|---|
| OWN-007 | slab panel (wraps the ring's SE corner and C9) | 177 17C 1EC 7C2 7DC 7E2 7F5 | 3.020 x 4.2777 - 0.900 x 1.050 - 0.050 x 1.000 | 11.9237 | 11.9237 | 0.10 | 1.19237 | L-41cfb82e GS |
| OWN-009 | slab panel (stair hall: ST-01 foot, ST-01b, lobby) | 15F 1DC 1E0 1F2 1F5 234 7C2 7C3 7CB 7CC | 2.400 x 4.800 | 11.5200 | 11.5200 | 0.10 | 1.15200 | L-41cfb82e GS |
| OWN-010 | slab panel | 15C 1F2 228 7C2 7CB 7E2 7E3 | 3.400 x 3.2277 | 10.9742 | 10.9742 | 0.10 | 1.09742 | L-41cfb82e GS |
| OWN-047 | slab panel (in front of the ring, N) | 15D 15E 7C2 7FF | 1.250 x 0.950 | 1.1875 | 1.1875 | 0.10 | 0.11875 | L-41cfb82e GS |
| OWN-020 | lift SHAFT (pit; floor = raft top) | 1EC 1EF 1F2 1F5 7BE | 1.800 x 1.800 | 3.2400 | 2.8125 | - | none | raft L-1590b76b (no volume) |
| OWN-082 / 083 / 086 | pit RING band (T-401 P4) | 7BE 7C2 + column edges | 1.80 x 0.20, 1.80 x 0.20, 0.20 x 1.20 | 0.9600 | 0.8800 (083: 0.27) | - | none | LIFT_PIT:WALLS (HELD) |
| OWN-094 | pit RING band (outside the T-391 binding) | 1EC 1EF 7BE 7C2 | 0.20 x 0.70 | 0.1400 | 0.0100 | - | none | LIFT_PIT:WALLS (HELD) |
| OWN-060 | ground-beam strip BAND0028 | 17C 7C2 7E2 7E3 | 0.300 x 3.2277 | 0.9683 | 0 (engine overlap) | - | in GB line | L-c5902fd0 GB |
| OWN-065 | ground-beam strip BAND0036.1 | 15E 15F 1E0 1F5 7C2 | 0.300 x 2.700 | 0.8100 | 0 (engine overlap) | - | in GB line | L-361f5e91 GB |
| OWN-099 / 114 / 151 / 174 | C9 column outline 1EC | 1EA 1EC 7BE 7C2 | 0.25 x 1.00 | 0.2500 | 0 (hole) | - | in column lines | C9 neck / GF column (T-401) |

Hand check of the four panels from the vertex dimensions: 3.400 x 3.2277 = 10.97418; 3.020 x 4.2777 - 0.900 x 1.050 -
0.050 x 1.000 = 11.92365; 2.400 x 4.800 = 11.52000; 1.250 x 0.950 = 1.18750; **sum 35.6053 m2** (own polygons
35.605376); x 0.10 = **3.56054 m3**.

Re-adds (asserted, `tables()`):

| Basis | Panels | Shaft | Ring | Column | GB strips | Total |
|---|---|---|---|---|---|---|
| T-391 binding (14 faces, > half of each face in the cell) | 35.6054 | 3.2400 | 0.9600 | 0.2500 | 1.7783 | 41.8337 |
| route G outline (no holes) | 35.6054 | 2.8125 | 0.8800 + 0.0100 (094) | 0.2500 | 1.7783 | 41.3262 (+0.01 = 094 bound elsewhere) |
| route G gross (outline - C9 hole) | 35.6054 | 2.8125 | 0.8800 | 0 | 1.7783 | **41.0762** = engine area_gross |
| route G net (gross - member overlap 1.7783 = BAND0028 + BAND0036.1) | 35.6054 | 2.8125 | 0.8800 | 0 | 0 | **39.2979** = engine net |

The engine's net cell = own panels 35.6054 + shaft 2.8125 + ring 0.880, to 1e-4. The old held bound 3.929788 m3 carried
(2.8125 + 0.880) x 0.10 = 0.369250 m3 of pit (T-391 F1: 0.369248, the 0.000002 is the route G vs DXF last digit). The
remaining shaft 0.4275 m2 and ring 0.22 m2 sit in the junction-gap face SITE-47d689fe (NO_LINE, T-401), not in any GS
line. T-391's "strips and column pieces 2.9883 m2" = GB strips 1.7783 + ring 0.96 + C9 0.25 of the bound faces.

## 3. Shaft floor = pit raft, not slab; nothing counted twice

- The shaft OWN-020 lies wholly over the raft 1B2B (3.2400 of 3.24 m2) inside the pit ring; p.14 draws the pit floor as
  the raft top (T-401 merged). Slab over it would be concrete in the pit void and the raft top counted again: refused
  (R-T444-2; adverse test 'pit raft counted again as slab').
- The ring band is the pit-wall line (T-401 P4, T-397 'LIFT_PIT:WALLS', HELD by the pit depth RFI L-1 and the GF
  build-up D-22 / D-40): not slab, not ground beam (R-T444-3; adverse 'ring claimed by slab and walls').
- Panels over the raft outside the ring (OWN-007 4.6442, OWN-009 2.6107, OWN-010 2.4700, OWN-047 1.1875 = 10.9124 m2),
  over footings 1ABF (OWN-009 1.845, OWN-010 0.765), F6 1B19 (OWN-010 1.4038) and strap SB2 1B08 / 1B09 (OWN-010 0.1664):
  all founding-level solids; the slab on grade lies above them on fill: no plan-overlap deduction (R-T444-7 = the T-356
  level-band rule).
- Other owners checked disjoint: T-436 parts (OWN-011 stair zone / T-442's new GS line, OWN-018, OWN-006, OWN-022,
  OWN-025) and the T-401 lift faces (OWN-020, ring 082 / 083 / 086 / 094); every piece has exactly one owner (asserted).

## 4. The stair hall OWN-009 (lesson T-436 applied)

OWN-009 carries 13 hidden layer-2 lines (ST-01 first flight 10D .. 113 + 171 + 1D3; ST-01b treads 1C4 .. 1C7), three
layer-5 lines (143 / 144 / 1C3) and two level marks: +1.00 (1C2, GF) and **+0.30** (1C9, the court-door lobby under the
GF half landing, ST-01b +0.30 -> +1.00, T-184 / T-189). The foundation plan below shows only footing 1ABF and the raft
1B2B (founding level); no void, pit or stair base is drawn under it. By the adopted rule (lessons row 2026-11-01, T-436)
the panel is slab on grade: 11.52 m2 x 0.10 = 1.152 m3. The 0.70 m change of floor level inside the panel is carried by
the ST-01b flight (STAIRS trade, steps 0.126 m3, waist HELD) and does not change the slab plan area or T; the slab-top
level of each zone stays HELD in the level chain (T-206: no slab-top level printed). Named, no quantity.

## 5. Lane I proposal (per line id; nothing edited here)

| Line | From | To | Basis |
|---|---|---|---|
| L-41cfb82ed733f4d6e3a5 STR.CONC.GROUND_SLAB (cell SITE-c1089bdb) | HELD, no value (bound 0 .. 3.560540, T-397) | **VALUED 3.560540 m3** = OWN-007 / 009 / 010 / 047 35.6054 m2 x T 0.10, DRAWING-CONFIRMED until the Checker re-measures | engine net 39.2979 - shaft 2.8125 (raft-top pit floor) - ring 0.880 (pit walls); the C9 'free column' is a lift column on the ring (R-T444-4) |
| raft L-1590b76b2fe8f131dc07 FOOTING 11.385 | unchanged | unchanged | pit floor = raft top, no volume added |
| LIFT_PIT:WALLS (T-397, HELD blank) | unchanged | unchanged (HELD: pit depth RFI L-1 + GF build-up) | ring band 1.100 m2 net (0.880 of it in the cell outline) |
| L-c5902fd0 BAND0028, L-361f5e91 BAND0036.1 | unchanged | unchanged | own their strips 0.9683 / 0.8100 m2 (engine member overlap) |

Held part of the GS line after the change: **none** (no slab quantity depends on an unprinted fact); the held facts of
this footprint stay with the lift lines (pit walls) and the level chain (slab-top levels). Never 0: the line goes from
None to 3.560540, the bound is replaced by a value only after Gate A.

## 6. Comparison term (I-07, -3.560540 m3) and its class

The freelancer's GS plate covers the whole drawn network (T-391). On the four panels his plate x 0.10 = 3.560540 m3 =
the proposed engine value: the I-07 term moves from HELD -3.560540 to **AGREE 0.000000** (traced, R `term_class`). The
rest of the cell footprint under his plate (shaft 3.24, ring 0.96, C9 0.25, GB strips 1.7783 = 6.2283 m2, 0.62283 m3) is
already inside the T-391 strips term -7.188210 (ENGINE_RIGHT: the beam / column / pit already own it, and the pit floor
is the raft top). It is not a slab-under-member RULE_DIFFERENCE: no measurement convention puts a slab over a pit void
or the raft top. GS-SLAB residual -12.309316 -> **-8.748776** m3 after integration (engine +3.560540); HELD part of the
concrete roll-up -116.428339 -> -112.867799; ENGINE route of T-433 -3.560540 -> 0.

Verdict proposal for the I-07 term: ENGINE_RIGHT (after integration) on the cell's pit / ring / column / beam pieces;
AGREE on the 35.6054 m2 of panels. The engine's free-column hold itself: ENGINE_MISSED_PRINTED_VALUE (T-042) on C9.

## 7. Methods side by side (ERS s.2.2)

| Method | Cell value |
|---|---|
| Owner manual method (Q-61 C member by member; R-CONC-OWN-1 column > beam > slab) | panels between ground-beam faces x T = 35.6054 x 0.10 = 3.560540; pit, ring, C9, beams owned by their lines |
| Drawing-derived (this task) | the same 3.560540 (own partition of the DXF; route G registered to 1e-4) |
| Candidate of record (V3.0.29 .. for this family, T-428) | HELD, no value (bound 0 .. 3.560540 after T-397) |
| Freelancer | one plate over the network (strips counted on his side, T-391) |

## 8. Rules, tests, lessons row (proposed)

R-T444-1 .. 7 (`t444_rules.py`). Tests `tests/t444_lift_gs_cell/` (21): hand villa R444 (not Alsenan: cell 7.00 x
6.00, ring 2.00 / shaft 1.60, four lift columns, GB strip -> panels 37.38 m2, 3.738 m3), mirror / quarter turn / skew /
mm identical; adverse: 'shaft columns read as free columns' (shaft + ring left in the slab, +0.368 refused), 'pit raft
counted again as slab', ring in two owners, piece twice / unnamed, held as 0, T not printed -> HELD, 'T=10cm' typed as
10, mm2 areas, missing level band, engine net not reconciled / not one-to-one, shaft outside the ring; development
villa: committed tables re-add (`--check`), pins, one owner per piece, shaft over the raft, no coordinates.

Lessons row (ERS s.7): | 2026-11-01 | the 35.6054 m2 slab-on-grade cell around the lift (3.560540 m3) stayed HELD for
days because route G found a 'free-standing column' in it, while its bound also carried 0.369 m3 of pit (T-444) | a
column inside a slab outline was read as free without asking what it stands on; the cell outline was drawn across the
pit ring | a column that stands on (or touches) a pit ring is a lift column cut out of the slab, never a reason to hold
the panels around it; a slab cell that meets a lift pit is cut at the ring's outer face, the shaft (pit floor = raft
top) and the ring (pit wall) are never slab; founding-level solids under the slab are not plan deductions; every villa,
ground slabs around lifts | tests/t444_lift_gs_cell ('shaft columns read as free columns', 'pit raft counted again as
slab') | PROPOSED

## 9. Checker re-measure list

1. OWN-009 2.400 x 4.800 = 11.52 m2 (edges 15F 1DC 1E0 1F2 1F5 234 7C2 7C3 7CB 7CC; its east side is the ring 7C2
   outer face and the BAND0036.1 strip); tread lines 10D .. 113 and 1C4 .. 1C7 hidden; levels 1C2 +1.00 and 1C9 +0.30; FP below: 1ABF + 1B2B only.
2. OWN-010 3.400 x 3.2277 = 10.9742 m2 (edges 15C / 228 / 7CB / 7E2 / 7E3; BAND0028 strip OWN-060 0.300 x 3.2277 east of it).
3. Route G registration: SH08 ring box (from the SH06 shaft opening + 0.20, T-401 `sheet_rings`) = 7C2; cell hole =
   C9 outline 1EC 0.25 x 1.00; engine net 39.2979 = 35.6054 + 2.8125 + 0.880.
4. ST p.14: pit floor = raft top (T-401 item 1).

## 10. Not done / uncertain

- The panels OWN-007 / OWN-047 were not re-measured by hand from printed dimension text (vertex dimensions only; the
  Checker list takes OWN-009 and OWN-010).
- The slab-top levels of the +1.00 and +0.30 zones of OWN-009 and the step detail at ST-01b are not printed (HELD in
  the level chain); they do not change the slab volume.
- Rebar and formwork of the cell are not part of this task.

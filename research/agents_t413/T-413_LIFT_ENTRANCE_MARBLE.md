# T-413 Elevator outer surround (B6-06) and threshold marble (B6-07) at every lift entrance (lane A, research only)

Worker 3 (cross-lane: lane I had no claimable row), 2026-11-01 07:01 .. UTC, branch `agents/task-T-413`. No quantity,
line, state, method, rule or released cell is changed; `engine/elevator_marble.py` is read, not edited. Development villa
(Alsenan), not an accuracy claim; the method (LIFT_ENTRANCE_MARBLE_V1) is for every villa. ERS s.2.1 - 2.6, s.3, s.4,
s.7 applied. Drawings named by Drive folder and title, entities by DXF handle; station-local sizes only.

## 0. Run and sources

Own run, Python 3.11.18, Drive "Alsenan chalet project": P7757.dxf from P7757_DXF_COMPRESSED.zip (`ab54dd55`),
'ST7757 dxf.dxf' (`9f9d1179`), p7757_arch_sheet10.pdf (SECTION A-A), Alsenan_Architectural_P7757_Pages_11-12.pdf
(SECTION B-B), all decoded by the wrapper into `.work/private`. `research/agents_t167/v304_run.py` then
`research/agents_t400/v3035_run.py`: **V3_0_35_BOQ_LINES.json `b011bace` / csv `59436bf4` = the candidate of record** (= the T-400 Gate B figures, 4,730 lines). Then

```
python3 -I research/agents_t413/t413_alsenan.py <run>/... --write      # binds to V3_0_35_BOQ_LINES.json (pinned sha)
python3 -I research/agents_t413/t413_alsenan.py --check                # committed table + summary reproduce
```

Outputs: `STATION_TABLE_T413.csv` (a, b), `summary.json` (b - d). Rules `lift_entrance_marble_v1.py` (R-T413-1 .. 7,
stdlib); tests `tests/t413_lift_marble/` (hand villa K413 + development-villa pins). Built on, not re-derived (WORKFLOW
CONTROLS s.10.5): T-401 MERGED (LIFT-01: shaft 1.80 x 1.80, three landings GF / 1F / 2F, ST p.14 'Lift door', roof
closed), T-405 MERGED (lift-entrance arrises HELD for beads), T-409 MERGED (lift landing = OTHER_ELEMENT, no profile),
T-325 MERGED (lift landing ARCH.THRESHOLD band lines; freelancer row census), T-418 MERGED (2F lobby 2.000 x 1.250).

## 1. The physical element (ERS s.2.1)

At each landing door of LIFT-01 the owner's rules (URBAN_PROJECTS_RULE_LIBRARY 1.4.0, all `owner_confirmed`) define
three separate objects (UP-ELEV-001 .. 005, engine/elevator_marble.py vocabulary):

1. **ELEVATOR_LANDING_MARBLE_ASSEMBLY**: one per landing DOOR (UP-ELEV-001), ids preserved (UP-ELEV-004).
2. **B6-06 ELEVATOR_DOOR_SURROUND**: marble on LEFT, TOP and RIGHT of the outer landing door, on the landing wall face,
   0.50 m wide unless the drawing says otherwise (UP-ELEV-002, DEFAULT), measured as the UNION AREA of the three bands,
   corners once (UP-ELEV-003, m2); the outer edge length is kept beside it, never instead.
3. **B6-07 ELEVATOR_THRESHOLD_MARBLE**: the marble step at the door, width x depth (m2) + exposed front edge (m.l), its
   own object; drawn dimensions first, else the fallback 1.10 x 0.50, and where the door width IS drawn only the 0.50 m
   depth is borrowed (UP-ELEV-005 v1.1.0); never merged into the surround; THRESHOLD n PORCELAIN = 0.

Not this element: the landing door and frame and the landing sill (lift supplier, UP-DOOR-CLS-005, UP-ELEV-SCHED-001);
the shaft walls (blockwork, T-143) and the pit / ring / tie beam (T-401); door thresholds B3-04 (a lift opening is not a
door); transition profiles B3-07; plaster corner beads B4-09.

## 2. (a) Entrance table (own reading of P7757.dxf; STATION_TABLE_T413.csv)

The three plans repeat one set-out (offset 44.853 m in x). Shaft inner 1.800 x 1.800 (layer 1; dimensions '1800' 666 /
67D on GF), car outline + diagonal + rear bar on layer 5 (223 / 224 / 225 on GF), four lift columns (S-COL.BON). The
opening is in the SOUTH shaft wall 0.200 (dimension '200' 672), between jamb lines at -0.500 / +0.500 = **1.000 m clear**;
four layer-5 lines cross the gap at +0.100 / +0.050 / 0.000 / -0.100 (landing-door / sill lines; no dimension, no
threshold label). The shaft's N / E / W inner faces are unbroken on every plan: **ONE door per floor, 3 stations**. No
landing on the roof (+13.90 slab closed over the shaft, T-401).

| Station | Engine opening / landing face | Clear width | Jambs (handles) | Landing face beside the jambs: left / right (stop) | Storey (A-A) |
|---|---|---|---|---|---|
| ELV-01-GF | OP-011 / GF-RC99C2A (open hall) | 1.000 DRAWING-CONFIRMED | 226 / 227 | 0.700 (jamb of door D120, insert 2C7) / 0.650 (external corner of column 2F8A, proud 0.05) | 4.50 (+1.00 -> +5.50) |
| ELV-01-1F | OP-007 / 1F-R78C367 (living) | 1.000 DRAWING-CONFIRMED | B96 / B97 | 0.600 (external corner, line B16, stair beyond) / 0.935 (wall end, lines AFD / B18) | 4.20 |
| ELV-01-2F | OP-002 / 2F-R4D1B62 (stair hall; lobby 2.000 x 1.250, T-418) | 1.000 DRAWING-CONFIRMED | 12AE / 12AF | 0.600 (external corner, line 129A) / **0.400** (INTERNAL corner: wall 1294 / 128D runs south from column 2F6C, door d220 in it) | 4.20 |

Door clear HEIGHT (the head level): **not printed** on any plan, on SECTION A-A (sheet 10: cuts the stairs; no lift door
drawn) or SECTION B-B (sheet 11: no landing door stacked on GF / 1F / 2F; the handle-less two-leaf element on the GF is not
repeated above and is not taken as the lift), nor in the ST set (p.14 'Lift door' without a height, T-401). T-405 reached
the same on the head (no beam / header drawn over the opening). Car size, door type: supplier (RFI L-1).

## 3. (b) Quantities, statuses, missing facts

**B6-07 threshold**, per station: width 1.000 (drawn) x depth 0.500 (UP-ELEV-005 fallback depth; nothing printed) =
**0.500 m2**, front edge **1.000 m.l**; status width DRAWING-CONFIRMED x depth **ASSUMED — OWNER-APPROVED** (UP-ELEV-005
v1.1.0). Total **1.500 m2, 3.000 m.l, 3 pcs**. Position across the 0.200 wall band not drawn: on the landing floor face
0.300 m2 (flush with the shaft face) .. 0.500 m2 (starting at the landing face) per station, own shapely check on the
engine faces (the band itself lies in no floor face: 0.000 in landing and shaft): **floor overlap HELD 0.900 .. 1.500 m2**.

**B6-06 surround**, per station (UP-ELEV-003 union, A(h) = h (L + R) + T (W + L + R)):

| Station | L / T / R | Status of the widths | A(h) | AT_LEAST (top band) | AT_MOST (h = storey - T) |
|---|---|---|---|---|---|
| ELV-01-GF | 0.50 / 0.50 / 0.50 | ASSUMED — OWNER-APPROVED (UP-ELEV-002; both faces >= 0.50) | h + 1.000 | 1.000 | 5.000 |
| ELV-01-1F | 0.50 / 0.50 / 0.50 | ASSUMED — OWNER-APPROVED | h + 1.000 | 1.000 | 4.700 |
| ELV-01-2F | 0.50 / 0.50 / **HELD 0 .. 0.40** | right band: INFEASIBLE_DEFAULT (0.50 > 0.40 of face to the internal corner) | 0.9 h + 0.950 at R = 0.40 | 0.750 | 4.280 |

Surround **HELD**, never 0: bound **2.750 .. 13.980 m2** (3 stations). Missing facts, by name: (1) the landing door
clear height h (lift supplier, with RFI L-1; or the architect's landing elevation); (2) the 2F right band (the drawing
leaves 0.400 m of face before the internal corner: the band is narrower, returns round the corner, or the door is
off-centre; an architect detail decides). Station equivalence (UP-ELEV-004): the three doors are equal (1.000 in a 0.200
wall), the surrounds are NOT (2F right), so one typical station x 3 is refused; ids kept.

## 4. (c) No double count (candidate V3.0.35 `b011bace`, 4,730 lines; summary.json `candidate_binding`)

| Station | B6-06 / B6-07 line | Opening line (ARCH.PASSAGE pcs) | Wall-band line (ARCH.THRESHOLD LIFT_LANDING) | Porcelain doorway strip | Landing floor line |
|---|---|---|---|---|---|
| ELV-01-GF | **NO LINE** | L-77a427c8 1 pcs PROVISIONAL (h not established) | L-6f5806ad 0.200 m2 BOUNDED_EXPOSURE, finish HELD | L-26213726 NOT_APPLICABLE | L-7625f35c FIN.FLOOR.PORCELAIN 109.778417 PROVISIONAL |
| ELV-01-1F | **NO LINE** | L-32d90a7a 1 pcs PROVISIONAL | L-084df97d 0.200 m2 BOUNDED_EXPOSURE | L-bb09715e NOT_APPLICABLE | L-b06400d4 FIN.FLOOR.PORCELAIN 33.711036 SOURCE_DERIVED |
| ELV-01-2F | **NO LINE** | L-c91732d6 1 pcs PROVISIONAL | L-3c5a3be2 0.200 m2 BOUNDED_EXPOSURE | L-17a56dfa NOT_APPLICABLE | **NO LINE** (2F lobby 2.5000 m2 is T-418's silent omission, for T-420) |

No item code in V3.0.35 names an elevator / lift marble (0 lines; the 7 'LIFT' codes are the pit waterproofing of T-401 /
T-219). Double-count checks, each 0:

- **B3-04 door thresholds**: 0 FIN.MARBLE.THRESHOLD lines on OP-011 / OP-007 / OP-002 (the 10 lines are wet doors,
  T-325); a lift opening is not a door (UP-DOOR-CLS-005). The three ARCH.THRESHOLD LIFT_LANDING lines hold the WALL BAND
  1.000 x 0.200 (0.200 m2 each) with the finish 'not specified': they are the same place as the inner part of the B6-07
  threshold whenever the threshold starts at the shaft face. B6-07 and these lines together never exceed the drawn
  footprint: band 0 .. 0.200 + landing floor 0.300 .. 0.500 = 0.500 per station; binding B6-07 ALSO to ARCH.THRESHOLD is
  refused (R-T413-7). Proposal for the element register: ONE owner for the band (section 7.3).
- **B3-07 profiles**: T-409 classes the three lift landings OTHER_ELEMENT / NOT_APPLICABLE (no profile line); unchanged.
- **B4-09 beads**: no bead line exists in V3.0.35; T-405 keeps LIFT#GF-08 / #1F-13 / #2F-01 HELD (one arris, one item);
  under an established surround those arrises are covered by marble (section 7.5).
- **Floor porcelain**: the lift doorway strips are NOT_APPLICABLE (moved to the band lines, T-223); the threshold's floor
  part lies inside the landing floor lines L-7625f35c (GF) and L-b06400d4 (1F) and must come out of them when B6-07 is
  wired (0.300 .. 0.500 m2 each, HELD by position); 2F has no floor line to deduct from.

V3.0.36 (T-246, merged into the working branch during this run, merged into this branch before the push): 4,691 lines
byte-identical to V3.0.35, 39 CHANGED_TEXT_ONLY, 0 quantity moved (its summary); the two landing floor lines L-7625f35c
/ L-b06400d4 are among the 39 (deduction lists now itemised: gross 126.927696 / 75.983002, nets unchanged), so the
threshold's floor part becomes one more NAMED deduction entry in those lists; every other cited line is unchanged. Not
re-run on V3.0.36 here (binding pinned to V3.0.35 `b011bace` as the row says).

## 5. (d) Freelancer (quantities only)

His rows (committed census of 885 rows, T-325 basis; the finishes workbook itself is 23.65 MB, over the connector's
download limit, so not re-opened): the marble sheet ('marble + court', 31 rows) carries court paving, entrance steps,
main / internal stair treads, landings, nosings, skirtings and the six door-step pieces; **0 rows for a lift surround or a
lift threshold**; the only lift-word row of all 885 is the concrete 'lift walls 20 cm' (T-401). His plaster sheet row 10
(17.4 in the 'corners m.l' column, 'for lift doors') is corner bead (T-405 B4-09), not marble; 17.4 / 3 = 5.8 m.l per
door would be 2 x 2.40 + 1.00, but no height is printed and his figure is not used as one.

| Family | Engine V3.0.35 | Freelancer | This task | Verdict proposal |
|---|---|---|---|---|
| B6-06 surround | no line | no row | HELD 2.750 .. 13.980 m2 (3 pcs) | ENGINE_RIGHT on scope (UP-ELEV-001 / -002 / -003 require it at every landing door); quantity HELD |
| B6-07 threshold | no line (the band 1.000 x 0.200 sits in 3 ARCH.THRESHOLD LIFT_LANDING lines, finish unspecified) | no row | 1.500 m2 / 3.000 m.l / 3 pcs | ENGINE_RIGHT on scope (UP-ELEV-005); quantity ASSUMED — OWNER-APPROVED (depth) |

## 6. Methods side by side (ERS s.2.2)

| Method | Stations | Surround | Threshold |
|---|---|---|---|
| Owner manual method (UP-ELEV-001 .. 005) | one per landing door: 3 | 0.50 bands, union area, needs h | drawn width x 0.50 depth = 0.500 each |
| Drawing-derived (this task) | 3 (one door per floor, roof closed) | widths: nothing printed; the plan caps the 2F right band at 0.400; h not printed -> HELD with bound | width 1.000 drawn; depth not printed; position across the band not drawn |
| Difference | none | 2F right: the owner default does not fit the drawn face (0.10 short), so the default is not applied there | none in area; the floor overlap is a bound |
| Candidate V3.0.35 | none | no line | no line |
| Freelancer | none | no row | no row |

## 7. Downstream BOQ impacts (for the lane I row; nothing edited here)

1. NEW lines B6-07 (3, one per station): 0.500 m2 + 1.000 m.l each, ASSUMED — OWNER-APPROVED depth, source UP-ELEV-005.
2. NEW lines B6-06 (3): value blank, HELD, bound per station as section 3, missing facts named.
3. The three ARCH.THRESHOLD LIFT_LANDING band lines (wall band 1.000 x 0.200, 'sill finish not specified'): the finish of
   the part the B6-07 threshold covers is marble by UP-ELEV-005; when B6-07 is wired, the band part [0, 0.200] per
   station is owned by B6-07 ONCE (element register ruling needed: one owner for the band; the supplier's landing sill
   inside the door line is not marble).
4. Landing floor-finish lines (L-7625f35c GF 109.778417, L-b06400d4 1F 33.711036; 2F none): take out the threshold's floor part 0.300 .. 0.500 m2 per station (HELD
   until the position is drawn); the 2F lobby proposal 2.5000 m2 (T-418, T-420) is the face it lands on at 2F.
5. Wall finish of the landing face (paint / plaster of the hall walls): the surround area replaces the paint on that face
   (HELD with the surround); B4-09 LIFT# arrises (T-405, HELD) become NOT_APPLICABLE once the surround is established
   (an arris under marble takes no bead).

## 8. Rules, tests, lessons row (proposed)

R-T413-1 .. 7 (`lift_entrance_marble_v1.py`, module docstring). Tests `tests/t413_lift_marble/` (20): hand villa
K413 (B / GF / 1F with a through-car, two doors on 1F = 4 stations; 0.90 x 2.10 with 0.50 bands = 3.050 m2, equal to the
round-6 engine polygon; drawn 0.40 bands 2.360; h not printed HELD 0.950 .. 4.050; threshold 0.450 with overlap 0.225 ..
0.450; printed depth 0.30 -> 0.270 DRAWING-CONFIRMED); adverse: one per floor / one per shaft where two doors refused;
surround width defaulted without its owner source refused; another default value refused; a default over a drawn width
refused; a default wider than the face HELD with its bound; mm refused; missing width refused; 1.10 fallback over a drawn
0.90 refused; threshold depth defaulted without source refused; held never 0; lift threshold bound to a door threshold /
ARCH.THRESHOLD / profile / bead line refused; mirror identical. Development villa: 3 stations, 2F right HELD 0 .. 0.400,
bounds, 1.500 m2, binding, reproduction.

Lessons row (ERS s.7): | 2026-11-01 | the owner's 0.50 m elevator surround default would have been applied at a 2F landing
whose wall face is only 0.40 m wide beside the jamb | a default width was a number, not a geometric claim checked on the
plan | an owner default for a band beside an opening is applied only where the drawn face beside the jamb holds it; where
it does not, that band is HELD with the bound (0, available], never the default and never 0 (every villa) |
tests/t413_lift_marble (default wider than the face HELD; 2F right band pin) | PROPOSED

## 9. Checker re-measure list

1. P7757.dxf, each plan: jamb lines 226 / 227, B96 / B97, 12AE / 12AF at 1.000 apart; wall 0.200 ('200' 672 on GF); the
   four layer-5 lines across each gap; N / E / W shaft inner faces unbroken (219 / 212 / 216; B15 / B11 / B13; 1299 / 1293 /
   1297).
2. Faces beside the jambs: GF 0.700 (to D120 at -1.200) / 0.650 (to the column 2F8A corner at +1.150); 1F 0.600 / 0.935;
   2F 0.600 / **0.400** (to the internal corner at +0.900, wall 1294 / 128D, door d220).
3. SECTION A-A (sheet 10) and B-B (sheet 11): no landing door height printed; storey heights 450 / 420 / 420.
4. Freelancer marble sheet: no lift row (31 rows); plaster row 10 is in the corners column.

## 10. Not done / uncertain

- The surround's return into the 0.200 reveal (marble lining of the jambs and soffit of the opening) is not in any owner
  rule and not drawn: not a quantity here (UNKNOWN, named; the supplier frame usually covers it).
- The threshold's thickness and the edge detail (bullnose / chamfer) are not printed; m2 and m.l only.
- Rates, waste and procurement: none (installed net only).

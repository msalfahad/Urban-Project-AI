# T-213 Sunken wet-slab panels as structural elements

Worker 1 (lane S), 2026-10-23. Development villa, not an accuracy claim. ERS s.2 (procedure), s.3 (one element, several
geometries; notation before arithmetic) and s.4 applied. Drawings are cited by Drive title / page / layer / handle; no
drawing, coordinate or client name is committed. New, unwired: `sunken_panels.py` (any villa), `alsenan_t213.py`
(private reader, numbers only -> `SUNKEN_PANELS_T213.json`), tests `tests/t213_sunken_panels/` (hand fixture villa
T213-S + development-villa checks). No BOQ line moved; no engine module changed.

## 1. The physical element

A "Sunken slab." panel (legend of ST7757.pdf p.3-p.6) is a floor-slab panel between beams, lowered by a drop d under a
wet room so that the wet-room build-up (bed / fill, falls, waterproofing tray) finishes at the storey FFL. It touches
four trades: slab concrete and the step / beam-side formwork (STRUCTURE, this task), fill / bed and the waterproofing
tray (lane A), the ceiling of the room below (CEILINGS). One panel = one element.

## 2. One set or two? (T-139 vs T-206) -> ONE set, two storey conventions

T-139 names a panel by the slab SHEET that draws it (the "GF" sheet = GF roof slab), T-206 by the FLOOR it carries
(1F). Matched one-to-one by area from the DXF hatch handles (ST7757 dxf.dxf, layer S-HAT.BAT, HATCH ANSI31 scale 2000;
the cantilever hatch on the same layer is scale 800):

| Handle | Sheet (T-139 id) | Floor carried (T-206) | Hatch region m2 | T-139 m2 | Residual |
|---|---|---|---|---|---|
| 276 | GF roof slab (GF-015) | 1F north wet room | 2.5725 | 2.5725 | 0.0000 |
| 275 | GF roof slab (GF-016) | 1F north wet room | 3.3250 | 3.3250 | 0.0000 |
| 298 | GF roof slab (GF-081) | 1F east wet room | 4.1076 | 4.1176 | -0.0100 (-0.24 %) |
| 287 | GF roof slab (GF-128) | 1F south-west wet room | 2.0804 | 2.0804 | 0.0000 |
| 280 | GF roof slab (GF-141) | 1F south-west wet room | 7.3009 | 7.3009 | 0.0000 |
| 5BF | 1F roof slab (1F-018) | 2F maid-room wet room | 5.4000 | 5.4000 | 0.0000 |
| | | **1F floor 5 panels** | **19.3864** | **19.3960** | -0.0096 |
| | | **2F floor 1 panel** | **5.4000** | **5.4000** | 0 |

T-139's "GF 19.396 + 1F 5.400" and T-206's "1F x5 + 2F x1" are the same six physical panels (D-41 wording should say
"5 panels under the 1F floor, 1 under the 2F floor"). T-206's five 1F PDF groups = the five GF-sheet hatches (276 split
in two by a beam line on the PDF; 280 / 287 joined), as T-206 already noted. Residual 298: T-139's face comes from the
polygonized beam / column lines, the hatch boundary runs along the slightly skewed B28 face and the column corner
(0.0016 m3 of slab concrete at t 0.16; below every threshold, named, not forced).

Reading rules the panel areas depend on (each tested): (a) the hatch islands are annotation islands (bar labels
"n d10/m", beam marks B1 / B4 / B5 / B2 / B28, "T.C", and the slab-thickness tag INSERT in 280): the hatch stops for
legibility, the slab continues, so NOTHING is deducted; an island with no annotation would be an unexplained void and
HELD (none found after reading the TEXT extents, not only insertion points: the B28 box in 298 has its insertion point
outside the island); (b) hatches 280 and 298 are split by an annotation arc (a dashed circle around a column) into two
touching region loops: the panel is their union (280: 7.1231 + 0.1778; 298: 3.8808 + 0.2268).

## 3. What is printed (search order ERS s.2.2, every format opened)

| Source | Format / how read | Result |
|---|---|---|
| ST7757.pdf p.1-p.16 | vector, NO text layer (39 chars per page = title only): every page read visually | legend "Sunken slab." p.3-p.6; no level, drop, section or detail of a sunken panel; p.15 "TYP. SLAB ON BEAMS DETAIL" draws a flat slab (no step); p.4 sections A-A / C-C / D-D are beam sections; p.8 general notes: no wet-room / sunken note (note 18: slab 16 cm unless stated; note 11: beams crossed by services widened 5 cm) |
| ST7757 dxf.dxf | vector | six hatches above; panel 280 carries its own thickness tag 'T 16'; no other text inside or beside any panel |
| Architect's DWF (Drive "Alsenan chalet project", .dwf, vector, T-201 reader) | sections A-A / B-B | every floor slab drawn as one constant band; neither cut crosses a sunken panel (A-A at about u 16 m on the 1F / 2F plans: wet rooms at u 19.9-23.5 / 17.9-19.7; B-B passes about 0.9 m south of the 1F east bath, through the living area): the sections are SILENT on the drop, not evidence of d = 0 |
| sanitary-7757.pdf sheets 1-3 | vector, no text layer, read visually | plans only (no section, no trap detail); branches "B.T.T.S." below the slab (T-206): the drop serves the build-up, not pipes in the slab |
| Wet-room details (T-195 register) | not issued | - |

**The drop d is printed nowhere: HELD under the EXISTING designer item D-41 (no duplicate opened).**

## 4. What the drawing does establish: the panel is lowered at full thickness

Panel 280 carries the slab-thickness tag 'T 16' inside the sunken hatch, and every other panel takes general note 18
(16 cm unless stated; nothing else stated). A thickness printed FOR the sunken panel means the slab is not thinned by d:
the whole panel is lowered (soffit lower by d). Consequences (independent of d): slab concrete = A x 0.16 (as T-139
counted, 4.0 m3 total: 1F floor 3.1018 + 2F floor 0.864), soffit formwork area = A (only its level changes).
The thinned-slab reading (top lowered, soffit flush) is ruled out by the printed thickness, not by preference.

## 5. Per panel, per trade (drop-driven items HELD, never 0)

Edges classified by what lies across the bounding beam (probe up to the widest scheduled beam, B27 90 x 85,
ST7757.pdf p.10): SHARED = another sunken panel across one beam; EXTERNAL = anything else (normal slab, exterior).
5 of 6 hatches coincide with T-139's beam-face polygons to 0.0000 m2, so every edge is a beam or column face.

| Handle | A m2 | P m | P_ext m | P_shared m (across) | Slab conc. m3 | Step riser form m2 | Beam-side form adj. m2 | Fill / build-up m3 (lane A) | WP upturn m2 (lane A) |
|---|---|---|---|---|---|---|---|---|---|
| 275 | 3.3250 | 7.300 | 5.550 | 1.750 (276, beam 0.20) | 0.5320 | HELD 5.550 d | HELD -5.550 d | HELD 3.325 d | HELD 5.550 d |
| 276 | 2.5725 | 6.440 | 4.690 | 1.750 (275, beam 0.20) | 0.4116 | HELD 4.690 d | HELD -4.690 d | HELD 2.5725 d | HELD 4.690 d |
| 280 | 7.3009 | 11.626 | 8.642 | 2.984 (287, B27 0.90) | 1.1681 | HELD 8.642 d | HELD -8.642 d | HELD 7.3009 d | HELD 8.642 d |
| 287 | 2.0804 | 7.078 | 4.127 | 2.951 (280, B27 0.90) | 0.3329 | HELD 4.127 d | HELD -4.127 d | HELD 2.0804 d | HELD 4.127 d |
| 298 | 4.1076 | 8.843 | 8.843 | 0 | 0.6572 | HELD 8.843 d | HELD -8.843 d | HELD 4.1076 d | HELD 8.843 d |
| 5BF | 5.4000 | 9.600 | 9.600 | 0 | 0.8640 | HELD 9.600 d | HELD -9.600 d | HELD 5.400 d | HELD 9.600 d |
| **Total** | **24.7864** | | **41.451** | **9.435** | **3.9658** | **HELD 41.451 d** | **HELD -41.451 d** | **HELD 24.786 d** | **HELD 41.451 d** |

- Step faces on SHARED edges (9.435 m) exist only if the shared beam's top stays at the normal slab top: HELD on d and
  on that beam-top level (unprinted).
- Net formed area change = 0 for any d (riser + P_ext d above the sunken top, beam side - P_ext d below the lowered
  soffit), but they are two different BOQ items (edge / riser forms vs beam-side forms) and both are HELD.
- Beam condition: a boundary beam still projects below the sunken soffit only while h - 0.16 - d > 0 (B28 25 x 75:
  d < 0.59; B27 90 x 85: d < 0.69); checked by `beam_projection_check` once d is printed.
- Ceilings below (CEILINGS): area unchanged, level lower by d: HELD.
- Rebar: the slab meshes are as printed (5 / 6 d10 per m); where the panel steps against a normal panel the top bars
  anchor in the beam (TYP. SLAB ON BEAMS, p.15) and are not affected by d; no extra bar is taken here.

## 6. Owner manual method beside the drawing-derived method

Only the bed is covered by an answered rule: Q-45 (owner 2026-10-19) wet-area floors 4-6 cm cement-sand bed, bathrooms
fall 1 % per metre -> ASSUMED - OWNER-APPROVED for the BED only (lane A), 24.786 x 0.04 .. 0.06 = 0.991 .. 1.487 m3
gross before wall footprints. No answered rule gives the drop, so the owner method does not establish d; the part of the
build-up below the bed (fill = d - bed - tile - falls) stays HELD with d. Never d = the bed, never 0.

Step concrete: every hatch edge is a beam or column face (5 of 6 hatch regions equal T-139's beam / column-face
polygons exactly, 298 to 0.0100 m2), and on an EXTERNAL edge the beam carries the normal slab, so its top is at the
normal slab top: the step is the beam's side face and adds NO slab concrete, for any d (0.000 m3 DRAWING-CONFIRMED by
geometry; the formula P_ext x d x t applies only to an edge not on a beam, HELD then).

## 7. Engine vs freelancer

No released code path measures the drop. The only engine formula for a sunken outline is the opt-in M8 completeness
bound (engine/source/scope_quantities.py, DRAWN_NOT_MEASURED / SLAB_STEP, convention SLAB_STEP_DROP_M of
URBAN_M8_GENERIC_CONVENTIONS_V6, not the released default): range 0 .. 4 sqrt(A) x drop_high x t of step concrete.
Against the drawing it is wrong twice for this villa: (a) the physical step concrete here is 0 m3 (step = beam side,
above), (b) its square-equivalent perimeter 4 sqrt(A) (47.69 m summed over the six panels) is neither the real
perimeter (50.886 m) nor the step perimeter (P_ext 41.451 m; e.g. 280: 10.81 vs P 11.626 vs P_ext 8.642 m).
Recorded for lane I (no change here: not a released line). The slab concrete of the six panels in the T-139 ledger
(3.966 m3 at 0.16 m) is confirmed and unchanged. The freelancer workbook was not re-opened for this element; no line of
his is known to price a sunken step (verdict proposal UNRESOLVED until d is printed; no comparison claimed).

## 8. Rule and lessons row (proposed)

Rule (any villa, provenance T-213): a hatch is turned into an element by the union of its region loops; islands that
hold an annotation (by the annotation's drawn extent, not its insertion point) are not deducted, an island with none is
an unexplained void and HELD; a thickness printed for a sunken panel fixes a full-depth drop (volume independent of d);
every drop-driven quantity is a formula on P_ext / P_shared / A and stays HELD until d is printed; the same panel set
named by sheet storey and by floor carried is reconciled by area and handle before anything is counted twice.

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-10-23 | Sunken panels recorded as 'GF 19.396 + 1F 5.400 m2' (T-139) and '1F x5 + 2F x1' (T-206), read as possibly two sets | One register named panels by the slab sheet, the other by the floor carried | Register every slab element with BOTH its sheet storey and the floor it carries; reconcile two registers by area and handle before counting (any villa) | tests/t213_sunken_panels (match_sets: same set matched, 3 % apart never forced; floor_carried) | proposed |

## 9. For the Checker (re-measure from the drawings)

1. ST7757 dxf.dxf, layer S-HAT.BAT, HATCH 275 / 276 (rectangles 1.900 x 1.750 and 1.470 x 1.750, 0.20 m apart) and
   5BF (1.800 x 3.000): areas 3.325 / 2.5725 / 5.400 m2 by hand.
2. HATCH 280: the region = loops 1 + 3 (7.1231 + 0.1778, the second closes the dashed column circle); the island with
   the 'T 16' tag is not a void; area 7.3009; edge on B27 (90 wide, p.10) shared with 287.
3. ST7757.pdf p.15 "TYP. SLAB ON BEAMS DETAIL": no step drawn; p.8 notes: no sunken note (read the image).
4. DWF sections A-A / B-B: cut positions vs the 1F wet rooms (neither crosses a sunken panel).

## 10. Not done / uncertain

- d, the beam-top level over SHARED edges and the wet-room build-up layers: designer item D-41 (existing).
- Residual 298 (-0.0100 m2) left to the T-139 face builder; lane I reads the hatch area when it wires sunken panels.
- No lane A / ceiling quantity is moved: the formulas are inputs for T-209 / T-214 / lane I.

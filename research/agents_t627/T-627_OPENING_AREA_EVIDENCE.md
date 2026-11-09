# T-627: B12 opening-area rows to drawing evidence (windows m2 + aluminium doors m2)

Worker 2, 2026-11-08, lane A, non-candidate (research only; no engine, rule / knowledge version, registry, frozen,
candidate or statement file changed). Files: research/agents_t627/* and tests/t627_opening_area_evidence/* only.
Development villa; not an accuracy claim. Drawings are cited by Drive folder / title and entity handle; no drawing,
coordinate, workbook row table or client name is committed (his sizes appear only as the compared values the pinned
statement already carries).

## 1. Result in engineering terms

Scope: the statement sections T-568/windows-m2 (16 rows: 14 UNKNOWN + 2 HELD; reference 116.900 vs engine 76.256 m2,
difference 40.644) and T-568/alu-doors-m2 (8 rows UNKNOWN; 12.0 vs 12.76 m2, -0.76). Every one of the 22 UNKNOWN rows
now carries its OWN width x height read this run from the drawings, with handles / view names, and reproduces its delta
to 0.000000 m2.

| Section | Rows | Evidence | Signed split (reference - engine) | Class move proposed |
|---|---|---|---|---|
| windows m2 | 14 + 2 HELD | 14 DRAWING_CONFIRMED (5 printed both ways, 2 printed width + bound vector outline, 7 masonry width + bound vector outline) | ENGINE_RIGHT 3.975 + HELD 36.669 = 40.644 | none (ENGINE_RIGHT confirmed) |
| alu doors m2 | 8 | 5 DRAWING_CONFIRMED, 3 ASSUMED_OWNER_APPROVED (height = Q-55 C, no bound view) | statement ENGINE_RIGHT -1.720 + RULE_DIFFERENCE 0.960; proposed ENGINE_RIGHT -1.140 + RULE_DIFFERENCE 0.380 | 3 height rows RULE_DIFFERENCE -> ENGINE_RIGHT (0.580 m2) |

Own area = engine area on every settled opening behind the rows (W08 / W09 2.25, W10 / W25 / W27 1.50, W11 / W12 4.29,
W13 2.76, W14 3.92, W18 1.08, W24 2.325, W26 2.04, W29 1.80; doors 2.20 / 1.98): no ENGINE_WRONG.

### Windows (his flat 2.00 m heights vs the drawn heights; widths equal except W18)
- Printed both ways (DXF DIMENSIONs, displayed text read from each dimension's own block): W13 plan 1126 '120' + SE 2A9C
  '230'; W14 plan 1198 '245' + SE 2B47 '160'; W26 plan 149D '120' + SE 2AB8 '170' (to the apex, Q-32 A); W18 plan 11ED
  '50' + NW 2EFA '216'. Each SE / NW height chain lies inside its printed width segment (2C15 / 2B9B / 2D8D).
- Printed width + bound vector outline: W11 / W12 plan A3E / A22 '195' (masonry 1.955) and the FENCE ELEVATION outlines
  1.968 / 1.966 x 2.201 between the louvred leaves -> 1.95 x 2.20.
- Masonry jambs (layer-1 cap lines by handle) + bound vector outline (DWF): W08 jambs 3B7 / 3BB 1.500, SW outline
  1.501 x 1.501 (+1.30 .. +2.80); W09 3C4 / 3C8 1.500 and W10 3D1 / 3D5 1.000, SECTION A-A 1.501 / 0.999 x 1.499
  (+2.00 .. +3.50); W24 D14 / D10 1.552 (same symbol as W15 / W16, printed 155), NE 1.552 x 1.499 (+6.50 .. +8.00); W25
  CEB / CEA 1.000, SW 1.001 x 1.501 (+5.50 .. +7.00); W27 134B / 134A 1.000, SW 1.001 x 1.501 (+9.70 .. +11.20); W29
  1330 / 132F 1.200, SW 1.200 x 1.499 (+10.70 .. +12.20).
- Every level reproduces T-201's readings to the mm (independent re-read: own binding by voting, own datum).

### Aluminium doors
- Widths (wall-face line ends on BOTH faces, by handle): D-GF-01 1.000 (10A / 10C / 138 / 139), D-GF-03 0.900 (11D /
  11E / 121 / 122), D-GF-05 1.000 (A2 .. A5), D-GF-06 1.000 (158 .. 15B), D-GF-09 0.900 (26E / 26F / 2B8 / 2B9),
  D-2F-01 1.000 (1280 .. 1283). Agrees with T-568's jamb reads.
- Heights NEW: the vector NORTH EAST ELEVATION draws D-GF-01 (0.999 x 2.199 from +0.30), D-GF-03 (0.900 x 2.199 from
  +0.30) and D-GF-06 (0.999 x 2.201 from +1.00), each bound on its masonry width; the SOUTH WEST ELEVATION draws
  D-GF-03 again with the SAME head +2.50 (outline down to the +0.15 court). Head minus the printed plan level the door
  opens from (LEVEL texts 401 / 403 '+0.30', 411 '+1.00') = 2.20 for all three: the Q-55 C height is now drawn, and his
  2.40 is printed / drawn nowhere. Proposal: the three height rows (0.200 + 0.180 + 0.200 = 0.580 m2) RULE_DIFFERENCE ->
  ENGINE_RIGHT (DRAWING_CONFIRMED by vector geometry, UP-OPEN-GEOM-001 as used by T-201 / T-207).
- D-GF-09: both views draw the D120 FRAME (1.001 wide, vs masonry 0.900) and disagree on its head (SW +2.50 from
  +0.15, NE +3.20 from +1.00): candidates only, height stays Q-55 C (RULE_DIFFERENCE stays). D-GF-05: its only
  coincident outline (A-A) belongs to W10 in the wall beyond (same-wall support of W09): not bound, Q-55 C. D-2F-01: no
  outline in SW / NE / A-A / B-B: Q-55 C.

## 2. HELD rows (unchanged, named)
- W02 27.219: waits on D-53 (count 1 drawn vs 2 rendered). Width 6.332 printed '633' (8F1), head 2.20 at the B-B cut
  (T-201) are drawn; the count is not.
- W17 9.45: waits on the Gate B wiring of owner Q-76 A (F-T568-1): 3.29 x 3.00 = 9.870 m2; the candidate line is still
  HELD 9.870 .. 11.515. NW prints chord 269 (2D53) and 305 from +5.50 (2E97); the owner's 3.00 governs.

## 3. Method (R-T627-1, t627_rules.py; extractor t627_extract.py)
Width: printed + bound governs, else masonry jambs (window cap lines; door face ends on both faces, never the block
frame). Height: printed governs; disagreeing printed values -> the later-dated sheet governs, same date -> CONFLICT;
else a vector outline bound by voted along-facade offset + masonry width (15 / 20 mm), within the floor's level band; an
outline claimed by two openings binds only with same-wall support; a frame-only match is a candidate; a door's two
views must agree on the head; else the owner fallback stays ASSUMED. Datum: DXF NW chain 29EE (+-0.00 to +1.00),
carried to the DWF by the translation voted from the DXF NW jamb lines (10 of 19 agree). Opening area only: assembly
and glass areas are refused.

## 4. Findings for the Lead
- F-T627-1 (class move, Checker to rule): alu-doors m2 RULE_DIFFERENCE 0.960 -> 0.380; ENGINE_RIGHT -1.720 -> -1.140.
- F-T627-2 (designer item, no BOQ move): D-GF-09 elevations draw a 1.00 frame at two different head levels, while the
  plan masonry is 0.90 (the existing D-GF-09 width ruling stands).
- F-T627-3 (engine follow-up for every villa; defect L-P9-02 'elevation views are read only for their level texts'): the
  voted along-facade binding of vector outlines here is a research reader for that defect; not wired.

## 5. Rule (proposed) and lesson
R-T627-1 as in the t627_rules.py docstring (every villa). Lessons-register row (proposed): 2026-11-08 | eight door m2
rows were filed RULE_DIFFERENCE on the owner fallback 2.20 while the vector elevations draw three of the doors at 2.20
above their floors | the door-height census (Q-55, 2026-10-20) read only raster scans; T-201 opened the vector plot
for windows only | read door outlines in the vector views with the same binding as windows (masonry width, voted
offset, head minus the printed floor level, two views must agree); a frame-only or conflicting outline stays a
candidate | R-T627-1 | tests/t627_opening_area_evidence (later-dated sheet, same-date conflict, geometry vs fallback,
assembly / glass refused, mm refused, door two views, rotation, mirror, wrong floor band, shared outline, one jamb, faces
disagreeing) | proposed.

## 6. Validation
tests/t627_opening_area_evidence 18 passed (the drawing re-read ran on the decoded DXF + DWF, no skip); t568 / t201 /
t061 re-run; freeze 0; codemap rebuilt and checked.

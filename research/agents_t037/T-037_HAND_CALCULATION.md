# T-037: Q-12 concrete hand calculation (pool, stairs + domes, footing edge strip), Alsenan development villa

Worker run 2026-10-19 03:21-04:05 UTC. Docs only: no engine, rule, test or data file changed. Development reference
only, not an accuracy claim. Every term below is either traceable to a printed value (drawing, sheet, entity handle)
or marked NOT PRINTED; no typical value is used. Governing rule: MISSION.md "Who is right" (ENGINE_RIGHT needs this
hand calculation, never the engine's own output). Verdicts are PROPOSALS for the verifier; the owner rules.

## Inputs (read in the session scratchpad, never committed)

| Input | Where | sha256 |
|---|---|---|
| ST7757.dxf (3 153 037 bytes) | Drive "Alsenan chalet project" / "ST7757 dxf.dxf" | 9f9d1179...38079 (= SOURCE_MANIFEST) |
| P7757.dxf (17 227 946 bytes) | Drive "Alsenan chalet project" / "P7757_DXF_COMPRESSED.zip", unzipped | ab54dd55...31cc4 (= SOURCE_MANIFEST) |
| ST7757.pdf (16 pages) | Drive "Alsenan chalet project" / "ST7757.pdf" | 74da1523...337e3 (text layer holds titles only: read the DXF) |
| freelancer concrete workbook | Drive "Alsenan chalet project" / concrete + rebar workbook (.xlsx, 49 706 bytes) | ae608411...957c (formulas read, not values) |

Engine side: the T-001b command rerun on working branch 56820cb (Python 3.11.17, ARCH_TAKEOFF_V2.9 + route G, no
profile), exit 0, 1 455 lines; the 41 lines keyed CONC.FOOTING / CONC.STAIR_DOME / CONC.POOL reproduce T-001b exactly
(77.265354 / 12.006536 / 3.49525 m3, table at the end).

Not readable this run: the architectural PDF "المخطط المعماري p7757.pdf" (37.5 MB, over the connector's 10 MB limit,
BOARD.md 2026-10-18). The architectural DXF holds only the GF, 1F and 2F plans and two elevations: no section sheet.
Every structural pool and stair height says AS PER ARCH, so heights that only an architectural section prints stay
NOT PRINTED here.

Readings were made from the DXF: TEXT / MTEXT values, DIMENSION display text (the text inside each dimension's
geometry block, i.e. what is printed), polyline vertices with bulges, and rendered crops of each detail (checked by eye).
The details are marked (N.I.S): only printed dimension text is used, never a scaled length.

## 1. Pool (engine 3.495 m3, freelancer 12.348 m3, difference -8.853 m3)

### What the drawing prints

| # | Term | Value | Where it is read |
|---|---|---|---|
| P1 | Pool plan shape | D shape: half circle + rectangle | ST7757.dxf GROUND BEAMS PLAN, layer S-BW: closed LWPOLYLINE 7C6 (outer) and open LWPOLYLINE 7C5 (inner), each with one bulge -1.0 segment (a half circle); same shape on P7757.dxf GROUND FLOOR PLAN, arcs r 1750 / 1550 on layer 5 |
| P2 | Outer size | 3.50 x 3.50 m (outer radius 1.75 m) | P7757.dxf GF plan: printed dimensions 350 (horizontal, DIM measurement 3500) and 350 (vertical); structural polyline 7C6 spans 3500 x 3500 |
| P3 | Wall thickness | 0.20 m | ST7757.dxf "DETAIL OF SWIMMING POOL." dimension text "20" at both walls (DIM 194D, 195B); P7757.dxf GF plan "20" |
| P4 | Inner size | 3.10 x 3.10 m (radius 1.55 m) | = P2 - 2 x P3; polyline 7C5 spans 3100 x 3100 |
| P5 | Floor slab thickness | 0.40 m at the deep end | ST7757.dxf pool detail, dimension text "40" (DIM 193F) across the deep-end floor; the sloped and shallow parts of the floor carry no thickness dimension |
| P6 | Pool depths and lengths along the section | NOT PRINTED | pool detail: every length and both depths are dimension text "AS PER ARCH" (DIM 182F, 1931, 1969, 1977, 1985, 1993); the architectural DXF has no section through the pool |
| P7 | Pump room (walls + floor) | NOT DRAWN in the files read | no pump-room outline, label or detail in either DXF near the pool or in the pool detail |
| P8 | Pool step | NOT PRINTED | the detail draws a small step at the shallow end without a dimension |

Plan areas from the polylines (bulge arc flattened to 0.5 mm; analytic value in brackets):
outer = 10.9364 m2 (pi 1.75^2 / 2 + 1.75 x 3.50 = 10.9356), inner = 8.5786 m2 (8.5788),
wall plan area = 10.9364 - 8.5786 = **2.3578 m2**; outer perimeter 12.498 m, wall centreline 11.784 m.

### Term by term

| Term | Hand calculation from the drawing | Engine (line, its own inputs) | Freelancer (pool sheet rows 11-15) |
|---|---|---|---|
| Floor | 10.936 m2 x 0.40 = **4.374 m3** on plan area; the sloped part is longer than its plan projection by an amount that needs the depths (P6): exact value UNRESOLVED, 4.374 is a floor of it | L-4a5248dc50a8df32895f: 6.045 m2 x 0.25 (convention POOL_FLOOR_THICKNESS_M) = 1.511 | 10.8 m2 x 0.40 = 4.320 |
| Walls | 2.358 m2 x H, H = pool depth NOT PRINTED (P6): **UNRESOLVED** | L-a4e192a775c8ab1bb0dd: 1.24 m2 (strip 0.2 x 6.2 m) x 1.6 (convention POOL_WALL_HEIGHT_M) = 1.984 | 12 m x 1.8 x 0.2 = 4.320 |
| Pump room walls | not drawn: **UNRESOLVED** | - | 3 x 1.8 x 0.2 = 1.080 |
| Pump room floor | not drawn: **UNRESOLVED** | - | 3 x 2 x 0.4 = 2.400 |
| Pool step | not dimensioned: **UNRESOLVED** | - | 0.3 x 2 x 0.38 = 0.228 |
| Total | >= 4.374 + 2.358 H (H unknown) | 3.495 | 12.348 |

Findings:
- **F-P1 (engine defect, plan geometry): the engine keeps only the straight half of the pool.** Its inputs say inner
  4.805 m2 = 1.55 x 3.10 and wall strip 0.2 x 6.2 m: the half-circle (bulge) part of both S-BW outlines is missing
  (drawn: inner 8.579 m2, wall plan 2.358 m2). Cause read in code: `engine/source/concrete_completeness.py:1273-1279`
  (`_describe_group`, FROZEN) measures an open outline as STRIP from parallel LINE pairs only (`_parallel_pairs`);
  the ARC entities of the same group add radii (:1280-1285) but no strip length, and `scope_quantities.py:417-424`
  (`_wall_geometry`) then takes outer / inner from that strip. Wall plan is short by 1.118 m2 (47 %), inner area by
  3.774 m2 (44 %). This holds for any curved pool, tank or wall strip, not only Alsenan.
- **F-P2 (engine reads no detail value): the floor thickness 0.40 is printed but the engine used the 0.25 convention**
  (range 0.20-0.30, which does not even contain the printed value). `_pool` (`scope_quantities.py:580-600`) reads
  printed notes near the plan finding only (`ctx.notes_near`); the dimension text of "DETAIL OF SWIMMING POOL." on
  another part of the sheet set is never bound to the pool.
- The freelancer's floor (10.8 m2 x 0.40) agrees with the drawing within 1.2 % on plan area and exactly on thickness.
  His wall height 1.8 m, pump room and step are not in the files read.

## 2. Stairs + domes (engine 12.007 m3, freelancer 21.833 m3, difference -9.826 m3)

### The "basement sub-stair" in Q-12 is not a basement stair

No basement is drawn: P7757.dxf has the frames GROUND FLOOR PLAN, 1st.FLOOR PLAN, 2nd.FLOOR PLAN, SOUTH EAST
ELEVATION, NORTH WEST ELEVATION only; ST7757.dxf has FOUNDATION PLAN, GROUND BEAMS PLAN, GROUND / FIRST / SECOND
FLOOR ROOF SLAB, COLUMN & AXIS PLAN, schedules and details; no level below the GF entries (+-0.00, +0.15, +0.30,
+1.00). The freelancer's 13.70 m3 heading ("stairs, basement / secondary", stair sheet rows 10-16) holds three items,
of which none is a basement stair:

| Freelancer row | Formula | m3 |
|---|---|---|
| entrance stair, slab + steps | 1.8 x 2.8 x 0.28 | 1.411 |
| stair 2, slab + steps | 1.2 x 16.4 x 0.28 | 5.510 |
| domes | 3 x 22.6 m2 x 0.10 | 6.780 |
| main stair, flights | 4 x 1.2 x 5.3 x 0.28 | 7.123 |
| main stair, landings | 3 x 1.2 x 1.4 x 0.20 | 1.008 |
| total | | 21.833 |

So the like-for-like split is: domes 6.780 (freelancer) vs 7.372 (engine); stairs 15.052 (freelancer) vs 4.635 (engine).
Q-12 choice (a) as worded ("the drawing shows a basement stair") does not apply.

### Domes: what the drawing prints

| # | Term | Value | Where it is read |
|---|---|---|---|
| D1 | Number of domes | **2** | ST7757.dxf FIRST FLOOR ROOF SLAB: two ribbed circles r 2211.1 with "SEE DETAIL" (centres 14.448 m apart), repeated as S-BOUN circles on SECOND FLOOR ROOF SLAB; P7757.dxf 2nd.FLOOR PLAN: two circles r 2211.1 on the ROOF at +9.70, each tagged "R221" |
| D2 | Span | 4.42 m (radius 2.21) | "DETAIL OF DOME" (N.I.S): dimension text "442" (DIM 1A38) along the springing line, ending on the outer shell face |
| D3 | Rise | 1.90 m | same detail: dimension text "190" (DIM 1A6D) |
| D4 | Shell thickness | 0.10 m | same detail: dimension text "10" (DIM 19B1) across the shell |
| D5 | Ring beam | width 0.20 m drawn (arcs r 2211.1 / 2411.1 on FIRST FLOOR ROOF SLAB); depth NOT PRINTED | the detail draws the ring section with bars (3 d16 top, 3 d18 bottom, 8 d8/m, 2 d14/20cm) and no dimension |
| D6 | A third dome | NOT in the structural set | P7757.dxf 2nd.FLOOR PLAN draws a DASHED circle r 2205 on layer 2 inside the maid's room; the SECOND FLOOR ROOF SLAB over that room is a flat slab (beams B3 / B8 / B7 / B2, mesh 7 d10/m) with no dome, ring or opening |

Hand calculation per dome (spherical cap, span 4.42, rise 1.90, shell 0.10): sphere radius R = (2.21^2 + 1.90^2) /
(2 x 1.90) = 2.23529 m; springing plane d = R - 1.90 = 0.33529 m from the centre; cap volume V(R, h) = pi h^2 (3R - h) / 3.
- 442 / 190 read as OUTER face (the 442 dimension ends on the outer face): V(2.23529, 1.90) - V(2.13529, 1.80) =
  **2.541 m3** per dome.
- 442 / 190 read as INNER face: V(2.33529, 2.00) - V(2.23529, 1.90) = 2.801 m3.
- Thin-shell check: pi (2.21^2 + 1.90^2) x 0.10 = 2.669 m3 (between the two).
Two domes: **5.081 m3** (outer basis; 5.601 inner basis) + ring beams (depth NOT PRINTED: UNRESOLVED; 0.20 x depth x
2 pi 2.311 = 2.904 x depth m3 per dome).

| Term | Hand calculation | Engine | Freelancer |
|---|---|---|---|
| Dome shells | 2 x 2.541 = 5.081 (outer basis) | 2 x 3.686 = 7.372: pi (2.211^2 + 2.211^2) x 0.12, rise = r by convention DOME_RISE_RATIO, shell 0.12 by convention DOME_SHELL_THICKNESS_M (L-eed9995125b727d75f42, L-4a2e625e21308bce6c18) | 3 x 22.6 x 0.10 = 6.780 |
| Ring beams | 2 x 2.904 x depth: UNRESOLVED | ring_area 0 (none) | none |

- **F-D1 (engine reads no detail value):** printed rise 1.90 and shell 0.10 contradict the engine's conventions
  (rise 2.211, shell 0.12): the engine is 2.291 m3 high on the two shells. Same cause as F-P2: `_dome`
  (`scope_quantities.py:671-685`, `_printed(notes, ("rise", "height"), ...)` at :679) reads only notes near the plan circle.
- The freelancer's 3rd dome has no structural element; his 22.6 m2 per dome is below the cap area 26.69 m2 (outer) /
  24.15 m2 (inner): not explained by a printed value.

### Stairs: what the drawing prints

| # | Term | Value | Where it is read |
|---|---|---|---|
| S1 | Stair section (waist, risers, landings in elevation) | NOT DRAWN | ST7757.dxf SECTION A-A / B-B / C-C / D-D are beam sections (11 d18, "AS PER SCH."), not stairs; no stair detail exists in the structural set; the architectural DXF has no section |
| S2 | Riser height / storey height | NOT PRINTED | no section; T-035 found no printed wall or storey height (ALSENAN_ARCH_FACTS_V1) |
| S3 | Waist thickness | NOT PRINTED as a stair dimension | the only thickness tag is a slab mark "16 T" placed inside the "(With Stair)" panel of the GROUND FLOOR ROOF SLAB (text at 58161, 48272); it is the panel's slab thickness tag and does not say it is the waist |
| S4 | Plan of flights | drawn (treads on plan, mesh 8 d16/m) | GROUND FLOOR ROOF SLAB / FIRST FLOOR ROOF SLAB "(With Stair)" panels; a curved stair (arcs r 1530.5 / 2780.5) on the GROUND FLOOR ROOF SLAB |
| S5 | Entrance flight width | 2.80 m (drawn, engine run width 2.8, freelancer 2.8) | engine line L-5493f3e0cc5801512838 inputs; not checked against a printed dimension |

| Term | Hand calculation | Engine | Freelancer |
|---|---|---|---|
| Main stair (GF-1F, 26 tread lines) | waist and risers NOT PRINTED: UNRESOLVED | 2.786: conventions STAIR_WAIST_CONVENTION_M 0.175, STAIR_RISER_M 0.165, "landings not drawn as a zone: not measured" (L-ffef7b38f37ffa75bc3a) | 4 flights x 1.2 x 5.3 x 0.28 + 3 landings 1.2 x 1.4 x 0.20 = 8.131 |
| Winder stair, ground (10 risers) | UNRESOLVED (same) | 0.901 (L-496d997d755b6367a169) | ("stair 2" 1.2 x 16.4 x 0.28 = 5.510 may be this or the curved stair: not identifiable from his row) |
| Entrance flight (5 risers, 2.8 wide) | UNRESOLVED (same) | 0.948 (L-5493f3e0cc5801512838) | 1.8 x 2.8 x 0.28 = 1.411 |
| Landings | UNRESOLVED; the engine measures none | 0 | 1.008 |
| Total | UNRESOLVED | 4.635 | 15.052 |

Every engine stair line is CONVENTION_ONLY (`printed: []`) and its total is not comparable to a drawing value; the
freelancer's 0.28 m "slab + steps" depth is not printed either. The gap is real in kind (the engine measures no
landing, and the freelancer counts 4 main flights against the engine's one GF zone) but its size cannot be fixed by
a hand calculation from the files read.

## 3. Footing edge strip (engine 7.220 m3 inside CONC.FOOTING 77.265)

| # | Term | Value | Where it is read |
|---|---|---|---|
| E1 | Level | foundation | ST7757.dxf FOUNDATION PLAN: two closed S-BOUN rectangles, outer 31.37 x 15.00 m (plot 31.37 printed, 15.00 printed), inner offset 0.20 m all round (vertices 119542 / 150912 / 36348 / 51348 and 119742 / 150712 / 36548 / 51148) |
| E2 | Width | 0.20 m | the offset of E1 |
| E3 | Section | 0.20 x 0.60 m, a BEAM | schedule row INSERT 1FA5 (block SBT, simple-beam schedule) BEAM = "B.W", W 20, H 60, bottom 4 d16, top 2 d14, stirrups 7 d8: reinforced as a beam, not as a footing. The band carries no "B.W" tag on the plan: the band-to-row link is by family mark and width (engine convention BOUNDARY_WALL_ROW_BY_WIDTH), not printed |
| E4 | Length | centreline 2 x (31.17 + 14.80) = **91.94 m** (closed band, all four sides) | from E1 |

Hand calculation (if the B.W section applies to the whole band): 91.94 x 0.20 x 0.60 = **11.033 m3**.
Engine: 60.17 x 0.20 x 0.60 = 7.220 (L-b41f1c7e4f8707dce180, SOURCE_DERIVED). Freelancer: footing sheet row 32
"perimeter tie beam" 0.20 x 0.60 x 71.7 = 8.604 (the same 20 x 60 section; his footings without it are 69.027).

- **F-E1 (engine, length): the engine strip holds 6 of the 8 band edges.** Completeness finding CC-9fd936ab60 lists
  entities D2:5720:0,1,3 and D2:5721:0,1,3: segment 2 of both rectangles (the long side at y 36348 / 36548, the lower
  NEIGHBOUR side, 31.17 m centreline) is not in the group; 60.17 = 30.97 + 14.60 + 14.60 (paired overlaps). Where
  segment 2 goes was not traced (same frozen grouping code as T-041). If it is not held elsewhere, 3.740 m3 is
  silently missing.
- The close CONC.FOOTING totals (77.265 vs 77.631) are a coincidence of offsets: footings + straps 70.045 vs 69.027,
  strip 7.220 vs 8.604, and both strips are shorter than the drawn band.

## 4. Engine lines reproduced term by term (rerun on 56820cb)

| Key | Item code (state) | Lines | m3 |
|---|---|---|---|
| CONC.FOOTING | STR.CONC.FOOTING (SOURCE_DERIVED / PROVISIONAL) | 25 / 1 | 64.304 / 1.960 |
| | STR.CONC.STRAP (SOURCE_DERIVED / PROVISIONAL) | 2 / 1 | 2.649 / 1.132 |
| | STR.CONC.BOUNDARY_WALL (SOURCE_DERIVED) | 1 | 7.220 |
| | total | 30 | **77.265** |
| CONC.STAIR_DOME | STR.CONC.STAIR (PROVISIONAL) 2.786 + 0.901 + 0.948 | 3 | 4.635 |
| | STR.CONC.DOME (PROVISIONAL) 3.686 x 2 | 2 | 7.372 |
| | total | 5 | **12.007** |
| CONC.POOL | STR.CONC.POOL (PROVISIONAL) 1.984 + 1.511 | 2 | **3.495** |

## 5. Verdict proposals (for the verifier)

| Line / term | Proposal | Basis |
|---|---|---|
| CONC.POOL, line | **UNRESOLVED** | wall height (pool depth) NOT PRINTED in the files read; pump room and step not drawn |
| CONC.POOL, floor term | **FREELANCER_RIGHT** | printed 0.40 x drawn plan 10.94 m2 = 4.374 (>=); freelancer 4.320; engine 1.511 (half the outline, convention 0.25) |
| CONC.POOL, wall plan | **ENGINE wrong (F-P1)**, freelancer UNRESOLVED | drawn wall plan 2.358 m2 vs engine 1.24; freelancer 12 x 0.2 = 2.40 m2 agrees with the drawing, his height 1.8 is not printed |
| CONC.STAIR_DOME, line | **UNRESOLVED** | stair waist, risers and landings NOT PRINTED |
| CONC.STAIR_DOME, dome shells | **ENGINE wrong (F-D1)**: drawing 5.081 (2 domes) vs engine 7.372; freelancer's count of 3 UNRESOLVED (D6) | printed 442 / 190 / 10 |
| CONC.STAIR_DOME, "basement sub-stair" | **not a basement stair** (Q-12 (a) as worded does not apply) | no basement drawn; the 13.70 is entrance stair + stair 2 + 3 domes |
| CONC.FOOTING, edge strip identity (Q-12 (c)) | **stays in the footing line** (RULE_DIFFERENCE in grouping only) | same 20 x 60 B.W section the freelancer files as "perimeter tie beam" under footings |
| CONC.FOOTING, edge strip length | **UNRESOLVED** (engine short of the drawing, F-E1) | drawn closed band 91.94 m -> 11.033 m3; engine 60.17 m, freelancer 71.7 m |

## 6. Proposed fix tasks (general rules, not Alsenan constants) for the lead

1. **Curved outline strips (F-P1).** New version piece next to the frozen `_describe_group`: an open or closed
   double outline whose straight edges pair as a strip and whose ARCs (or polyline bulges) are concentric pairs at the
   same offset adds the arc centreline length (offset x angle) to `strip_length_m`; unpaired arcs keep the strip
   HELD, never dropped. Synthetic fixture (hand-calculated, not Alsenan): D-shaped pool outer r 2.00 / rectangle
   2.00 x 4.00, wall 0.25, drawn (a) as LWPOLYLINE with bulge -1, (b) as LINEs + ARC, (c) mirrored, (d) rotated 30
   degrees, (e) in metres and in mm; expected wall plan = (pi 2.00^2 / 2 + 8.00) - (pi 1.75^2 / 2 + 1.75 x 3.50) =
   14.2832 - 10.9356 = 3.3476 m2 in every case; (f) an arc with no partner ARC stays HELD.
2. **Detail dimensions bound to scope families (F-P2, F-D1).** A new module reads a "DETAIL OF <family>" frame's
   dimension display text (the MTEXT in the dimension block, never a scaled length on an N.I.S detail) into named
   values (pool floor thickness, dome span / rise / shell) and passes them as printed notes to `_pool` / `_dome`;
   "AS PER ARCH" binds nothing and keeps the term HELD. Fixture: a dome detail printing 600 / 250 / 12 and a plan
   circle r 3.00 -> shell by the cap formula above; a detail with "AS PER ARCH" -> HELD, never the convention.
3. **Trace the lost band side (F-E1)**, in the style of T-041: follow segment 2 of both S-BOUN rectangles on the
   FOUNDATION PLAN through the completeness grouping (`concrete_completeness.py`, FROZEN) to the element that holds
   it or the line where it is dropped.

## 7. Not done / uncertain

- Pool depth, stair risers and waists: the architectural PDF (37.5 MB) may print them; it is over the connector limit.
  A zipped copy on Drive, or the architectural section sheets as DXF, would let a later run close the pool and stair
  terms.
- Whether 442 / 190 are outer or inner dimensions: read as outer from where the dimension line ends (outer face);
  both results are given.
- Whether the B.W row is the section of the S-BOUN band: inferred by mark and width, not printed on the plan.
- The freelancer's "stair 2" (16.4 m run) is not matched to a drawn stair.

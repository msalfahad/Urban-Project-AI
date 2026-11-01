# T-436 Ground-slab parts with no owner after the r4 roll-up: re-measured and classed (research only)

Worker 1 (lane S), 2026-11-01 19:24 .. UTC, branch `agents/task-T-436`. Development villa (Alsenan is one sample; the
rules in `t436_rules.py` are for every villa). No engine module, candidate line, released cell, rule or knowledge
version is changed; nothing is released. ERS s.2.1 - 2.7, s.3, s.4, s.7 applied; Q-62 A (junction volume to the slab /
landing), R-T391-1 .. 5, R-T428-1 .. 7, R-T417 / R-T432 (exact construction, nearest never taken), R-T418-1 (a stair
face is partitioned, never dropped whole).

## 0. Sources (own reads this run; private copies in `.work/private` only)

| Source (Drive 'Alsenan chalet project') | Used for |
|---|---|
| 'ST7757 dxf.dxf' (sha256 9f9d1179) | GROUND BEAMS PLAN frame (T-141), FOUNDATION PLAN frame (offset 38724.406 mm), handles below |
| ST7757.pdf p.16 'TYPICAL STEEL LAYOUT-STAIR SECTION' (raster, 300 dpi, not stored) | how a bottom flight is founded |
| Alsenan_Architectural_P7757_Pages_01-02 p.1 'GROUND FLOOR AREA PLAN 1:200' (raster) | the six printed area-table pieces (constructions for the bare area) |
| the concrete + rebar workbook, ground-slab row | his plate area and thickness only (stays in `.work/private/t436`) |
| merged: T-391 own partition (`OWN_GROUND_T391.json`, rebuilt face by face and asserted), T-428 r4 parts (summary asserted), candidate lines `agents_t347/CANDIDATE_V3024_BURIED_LINES.json` (= V3.0.29 .. V3.0.37 for GS), T-415 (ST-02 RS-C foot at +1.00), T-418 (GF round stair inside a floored room) | cited, not re-derived |

```
.work/venv/bin/python -I research/agents_t436/t436_alsenan.py --dxf "<private>/ST7757 dxf.dxf" \
    --freelancer "<private>/<concrete workbook>.xlsx" --out <checkout>/.work/private/t436 --write
.work/venv/bin/python -I research/agents_t436/t436_alsenan.py --check      # REPRODUCED, no private input
```

## 1. The three parts (T-428 r4, -1.560570 m3 of the -5.084765 m3 unexplained)

| Part (T-428) | m3 | Physical element (ERS s.2.1) |
|---|---|---|
| GS stair-zone panel (F2) | -0.837230 | slab on grade, panel OWN-011 8.372326 m2 (engine cell 4df8fcd9, no GS line) under / beside the foot of the GF curved flight ST-02 RS-C |
| GS his area beyond the drawn network | -0.638640 | none drawn: his single plate area exceeds the whole drawn ground-beam network (289.113 m2) |
| GS valued faces (three small reads) | -0.084700 | three slab panels where T-391's own read and the engine differ: 49a7dae5 / OWN-018, the court-side pair d74f3fe2 + 0caa2bd2 / OWN-006, the lift-side pair 3f7728a8 + c1b4b440 / OWN-022 + OWN-025 |

## 2. Part 1: the stair-zone panel -0.837230 m3 -> TRACED ENGINE_WRONG (whole panel is slab)

| | |
|---|---|
| Element | GROUND BEAMS PLAN panel OWN-011, closed on four sides by layer-1 band faces 17D / 7CF / 7DC / 7E1; 8.372326 m2 |
| Engine | cell SITE-4df8fcd99d130701 region STAIR_ZONE: 'not counted: the cell is a stair zone' (U-C register, bound 0.837233 m3), no GS line in V3.0.29 .. V3.0.37 |
| Freelancer | inside his one plate (his plate x 0.10) |
| Own hand | 8.372326 m2 x 0.10 (printed 'T=10cm', T-206 DRAWING-CONFIRMED) = **0.837233 m3** |
| Class | **ENGINE_WRONG** (FREELANCER_RIGHT on this part); status of the panel quantity DRAWING-CONFIRMED |
| Correction owner | lane I (Worker 3): a GS line for cell 4df8fcd9 at the drawn panel x T (proposal; Lead to row it) |

Evidence, each read on its own drawing (ERS s.2.2 level 1):

1. **The flight is drawn ABOVE the slab plan.** Every stair line inside the panel is on layer 2 with linetype HIDDEN:
   nine 1.150 m tread lines 160 .. 168 and the curtail arcs 169 / 16A (11 entities). Nothing else inside the panel but
   the column label 24E, the mark '******' 165A on the north band (also at the ST-01 foot, 165B; no legend found, not
   used) and the non-plotting DEFPOINTS frame B3. No void, pit ring (S-BW), opening (S-OPENING) or 'VOID' mark: the
   lift pit on the same sheet is drawn as an S-BW ring, the pool as an S-BW ring with its own hatch.
2. **No stair base below it.** On the FOUNDATION PLAN the only outline under the panel is footing 1B1A (2.25 m2 of it
   under the panel), which contains the column outlines 10E0 / 10E4: a column footing (F14), not a stair base.
3. **How a bottom flight is founded (ST p.16, typical stair section).** The lowest flight springs from a G.B 30 cm wide
   (T.O.B +0.00, '3ø14' top, '4ø16' bottom, 'ø8/15cm', blinding 50 x 10) with the slab surface S.S.L -0.05 beside it:
   the flight bears on the ground beam, it does not replace the slab and has no base of its own. On the GB plan the foot
   of RS-C (curtail arcs 169 / 16A at the last four lines 165 .. 168, T-415 'foot +1.00') lies on the north band of the
   panel, consistent with that detail.
4. **The space is a floor.** Second drawing (architectural): the GF round stair stands inside the floored reception
   room (T-418 s.3, merged 361f6e47); the arch GF plan prints '+1.00' at the foot (T-415 s.0, merged 6b6ff9bd).
5. **The flight-to-slab junction** (the RS-C waist foot below +1.00, HELD with the waist, T-415) belongs to the slab
   by Q-62 A: it does not reduce the panel.

Methods side by side: OWNER MANUAL METHOD - no answered rule names a slab under a flight on grade (OWNER_RULE_STAIRS
2026-10-21 / 10-24 searched by T-391); Q-62 A gives the junction to the slab. DRAWING-DERIVED - the panel x T, as
above. They do not conflict. ERS s.2.7 test written out: the drawings settle it (hidden flight, closed panel, no
void / pit / base, founded-on-beam detail, floored room), so it is NOT a designer item and NOT an owner question; F2
(T-391) and the RFI draft line for it can be withdrawn.

Engine root cause (for the correction, not changed here): `engine/source/generic_route.py:1193-1212` routes a
STAIR_ZONE cell to SLAB_STAIR_ZONE / 'not counted' (the M2 audit already lists 'no stair-zone exclusion without a
label'); the same rule on the slab-on-grade sheet drops the floor slab under any flight drawn hidden on it. R-T436-1
below: never dropped whole; a panel leaves the slab family only with a drawn void / pit / base or a section that says so.

## 3. Part 2: his area beyond the drawn network -0.638640 m3 -> UNRESOLVED (his side), one artefact named

| Sub-part | m3 | Class | Cause |
|---|---|---|---|
| B-HIS | -0.638616 | **UNRESOLVED** | his bare plate area exceeds the drawn network (true arcs 289.113643 m2) by 6.3864 m2; no construction from printed data reproduces it |
| B-CHORD | -0.000024 | ENGINE_RIGHT (own-read artefact) | T-391's 48-chord arc 139 (the annex corner, the only arc on the network's outer edge) leaves 0.000237 m2 of segments out of the network |

Constructions tried (R-T436-3; his area is a single figure given to 0.1 m2, so a reproduction must fall within
0.05 m2; 66 constructions, the eight nearest by misfit, construction - his area):

| Construction (printed data only) | Misfit m2 |
|---|---|
| ARCH p.1 area-table pieces 1+2+3+5 | +0.27 |
| pieces 1+2+3+5+6 | +0.73 |
| pieces 1+3+4 | +1.08 |
| pieces 1+3+4+6 | +1.54 |
| pieces 1+2+3+6 | -4.14 |
| pieces 1+2+3 | -4.60 |
| drawn network outline offset by the printed projection 0.10 (ST p.13) | +5.17 |
| pieces 1+3+4+5 | +5.95 |
| (drawn network, true arcs / 48-chord) | -6.386 / -6.387 |

None reproduces it; the nearest (+0.27 m2) is listed, never taken (R-T432). The figure has no dimensions on his row
(the area sits in his width column). It stays UNRESOLVED on his side; 'slab beyond the drawn edge' is refused as a cause
without the drawn line that bounds it. No engine quantity depends on it.

## 4. Part 3: the three small face reads -0.084700 m3 -> two of three TRACED, one UNRESOLVED

| Sub-part | Engine m2 | Own m2 (closed on drawn faces) | m3 | Class | Cause |
|---|---|---|---|---|---|
| F-018-STRIP | (deducted) | 0.326694 | -0.032669 | ENGINE_RIGHT | the 0.30 diagonal band stub BAND0038 (faces 180, 0.789 m, and 181, 1.2786 m; band width 0.300) that T-391 merged into OWN-018 because face 181 stops 0.0781 m short of the band face it meets; the beam owns the strip, his plate covers it (the same cause as T-391's -7.188 strips term) |
| F-018-ENDS | 3.597683 | 3.507683 | **+0.009000** | **ENGINE_WRONG** | the engine deducts the stub as short face x width 0.789 x 0.30 = 0.236694 m2, leaving its two 45-degree end triangles (w^2 = 0.090000 m2) in the slab face; a 45-degree stub between two orthogonal faces is w (Ls + w) = 0.326694 m2. Square-end reading (181 not carried to the face): strip 0.320600, ends +0.008391 m3: the range is printed, the closed reading governs (gap 0.078 < band width, R-T436-2) |
| F-006-STRIP | (not in a panel) | 0.492189 | -0.049219 | ENGINE_RIGHT | band 177 / 7CD (0.300, column C9 face to the ring) whose faces end ON arc 158 (0.000 mm, true curve): T-391's 48-chord arc did not node them, so the strip and the two panels read as one 13.4514 m2 face; the engine's two cells are exactly the two drawn panels |
| F-006-CHORD | 10.905052 + 2.050202 | 10.905052 + 2.050202 (true arc) | -0.000396 | ENGINE_RIGHT (own-read artefact) | the chord segments of arc 158 inside T-391's OWN-006 |
| F-LIFT | 2.615573 + 2.244696 | 2.721160 + 2.253380 | -0.011427 | **UNRESOLVED** | two panels against the lift ring 7C2, column 1EF and the oblique band 17E / 17F: both own faces are closed by drawn lines; the engine cell outlines of the V3.0.x chain are in no committed output (the route-G base run of this session still has them inside SITE-f65941a3), so the 0.1143 m2 cannot be placed |
| F-ROUND | | | +0.000011 | AGREE | T-391's own areas carried to 0.0001 m2 |

**T-391's "the engine splits the court-side panel at a line not drawn on layer 1" is withdrawn**: the line IS drawn
(177 / 7CD); the own read did not node it. The engine is right on d74f3fe2 and 0caa2bd2 to 1e-6 m2.

Engine-side register (beside the residual, never a part, R-T428-5): **E-T436-1** the ground-beam stub BAND0038
(L-970bac563cbcd69e2a30, valued 0.071008 m3 = 0.236690 x class 0.30) is short by the same two end triangles:
drawn 0.326694 m2 (square-end 0.320600), +0.027000 m3 at its class depth (+0.025173 square end); the comparison cannot
show it (his beams are lumps). Correction owner: lane I with F-018-ENDS (one bound pair, R-T402: the slab face and the
stub move together).

## 5. Totals (sub-parts re-add to each T-428 part within 0.000002 m3; asserted)

| Part | before (r4) | TRACED | HELD | UNEXPLAINED |
|---|---|---|---|---|
| GS-STAIR-ZONE | -0.837230 UNRESOLVED | -0.837230 (ENGINE_WRONG) | 0 | 0 |
| GS-BEYOND-NETWORK | -0.638640 unexplained | -0.000024 | 0 | -0.638616 |
| GS-FACES | -0.084700 UNRESOLVED | -0.073273 (of which ENGINE_WRONG +0.009000) | 0 | -0.011427 |
| **sum** | **-1.560570** | **-0.910526** | **0** | **-0.650043** |

Engine vs freelancer in engineering terms: on the ground slab the engine is LOW by 0.837 m3 (one 8.37 m2 panel left
out) and HIGH by 0.009 m3 (two 45-degree triangles of a beam stub left in the slab); the freelancer's plate is 6.39 m2
(0.639 m3) larger than everything drawn, with no drawn element or printed construction behind it. If the two lane I
corrections are made, the GS valued family moves +0.828230 m3 (17.240684 -> 18.068914 m3 on the T-391 basis) and the
GS residual -12.309316 -> -11.481086 m3: printed as a SCENARIO beside the as-is figure, never in its place (R-T428-6).

## 6. Rules (t436_rules.py; every villa; scope and provenance T-436)

- **R-T436-1** a stair on grade does not remove the slab: a slab-on-grade panel closed by drawn ground-beam faces with
  the flight drawn hidden is slab, whole, at the printed thickness; it leaves the slab family only with a drawn void /
  pit / opening, a stair base on the foundation plan, or a section that puts the flight in the ground in its place; a
  flight drawn continuous (cut at the plan) with no section is HELD, never 0; the junction is the slab's (Q-62 A).
- **R-T436-2** an own partition is closed on the drawn faces before it is a reference: faces ending on an arc are noded
  on the true curve, a face short of the face it meets by less than the band width is closed to it (square end printed
  beside it), a panel still containing a band pair is refused; an own-read artefact is named, never a physical cause.
  A 45-degree stub between two orthogonal faces is w (Ls + w), never w Ls.
- **R-T436-3** a bare area is a cause only when a printed construction reproduces it within half his stated unit; the
  nearest is listed, never taken; 'beyond the drawn edge' needs the drawn line.
- **R-T436-4** sub-trace bookkeeping as R-T428 (re-add, verdict list, owner of ENGINE_WRONG, HELD never 0, ids
  disjoint from T-430 / T-437 parts).

## 7. Tests `tests/t436_gs_parts` (32, all pass)

Villa G436 hand fixture (not Alsenan): stair panel with hidden flight -> SLAB 1.200 m3; pit panel NOT_SLAB; stair base
or section NOT_SLAB; continuous flight HELD (never 0); stub w (Ls + w) 0.450 vs rectangle 0.360 (w^2 0.090) built in
shapely; band end closed with its square-end range, gap >= width HELD; a band ending on a 48-chord arc merges into the
panel and separates only when noded. Adverse: **'slab beyond the drawn edge counted as residual cause without a drawn
line' refused**; panel dropped whole refused; strip read as panel refused; square end larger than closed refused; two
reproductions -> none chosen; mm2 as m2; missing values; sub-parts not re-adding / ENGINE_WRONG without owner / one id
in two parts / unknown verdict / empty cause / HELD 0. Alsenan pins: `--check` reproduces, the three parts and their
sum -1.560570, stair panel class and linetypes, faces (strip + panel = own, engine - panel = 0.09, engine = true-arc
panels), disjoint from T-430 / T-437 components, no freelancer row value in the summary.

## 8. Checker re-measure list (Gate A)

- **Stair-zone panel** OWN-011: faces 17D / 7CF / 7DC / 7E1 -> 8.372326 m2; layer 2 HIDDEN 160 .. 168, 169 / 16A inside;
  FOUNDATION PLAN under it only footing 1B1A with column outlines 10E0 / 10E4; ST p.16 typical stair section foot (G.B,
  T.O.B +0.00, S.S.L -0.05).
- **Stub BAND0038**: faces 180 (0.789) and 181 (1.2786, ends 0.0781 short), width 0.300; strip 0.326694 m2 = 0.30 x
  (0.789 + 0.30); OWN-018 3.834377 - 0.326694 = 3.507683 vs engine 3.597683.
- **Court pair**: OWN-006 against the true arc 158 (centre / r 2.550 from the entity): 10.905052 + 2.050202 + strip
  0.492189 (177 / 7CD end on the arc).
- Freelancer side: his plate area only (private), the area-table piece sums above.

## 9. Not done / uncertain

- F-LIFT 0.1143 m2 (-0.011427 m3) is not placed: needs the V3.0.x engine cell outlines of 3f7728a8 / c1b4b440 (a chain
  run with the architectural DXF); both own faces are drawn and closed.
- Part 1's correction and E-T436-1 are proposals for lane I; no line is edited here. The waist foot of RS-C stays HELD
  with the waist (T-415).
- Observation O-T436-1 (for the Lead / Checker, no part moves): T-391's 'LIFT' class (8.0450 m2) includes the pool
  interior inside ring 157 (OWN-016 4.805 m2) besides the lift shaft 3.24; its -7.188 'strips under his plate' term
  is still not slab (ENGINE_RIGHT stands), but the label 'lift shaft and ring' understates what it holds.

## 10. Proposed lessons-register row (ERS s.7)

| Date | Problem | Root cause | General rule (scope) | Regression test | Status |
|---|---|---|---|---|---|
| 2026-11-01 | The slab-on-grade panel under the GF curved flight (8.37 m2, 0.837 m3) sat in no line for days as a 'designer item', and two small slab differences were blamed on the engine although the own reference read had merged two drawn beam strips into panels (T-436) | a stair zone was treated as not-slab without asking what the drawings put there; a reference partition was trusted without checking that every drawn face was noded (arcs read as chords, a face 78 mm short) | a slab-on-grade panel with a flight drawn hidden is slab unless a drawn void / pit / base or a section says otherwise (never dropped whole; held only when the drawings do not settle it); a reference partition is closed on the drawn faces (true arcs, short faces closed to the face they meet with the square-end range) before any engine difference is classed; every villa, ground slabs and every own-read reconciliation | tests/t436_gs_parts ('slab panel dropped whole' refused; 'strip read as panel' refused; 'slab beyond the drawn edge without a drawn line' refused) | PROPOSED |

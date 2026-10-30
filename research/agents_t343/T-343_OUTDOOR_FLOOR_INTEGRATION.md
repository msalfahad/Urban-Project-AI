# T-343: outdoor floor lines in the candidate (ARCH_TAKEOFF_V3.0.25), integration package for Gate B

Worker 3 (lane I), 2026-10-29 21:05 - 22:30 UTC. Gate 1 (an OMISSION closed: the GF court face had no candidate line).
Development villa, not an accuracy claim. Opt-in candidate only: the released default stays ARCH_TAKEOFF_V2.9 + route
G; nothing is released. No client name, coordinate or image is committed; drawings are cited by Drive title and DXF
entity handle.

integrates: T-342 (MERGED 4dd9cff8, census binding: court 6 pieces + risers MISSING, deck corrected to the drawn D,
pool water-face finish HELD), T-157 (MERGED 554c1c46, the drawn piece areas, cut lines, sheets, owner manual method),
T-183 r2 (MERGED 63802945, pool D outlines and the NW elevation cut levels). Inputs are read from those merged files,
each pinned by sha256 (`research/agents_t343/t343_inputs.py`).

## 1. The physical question and the answer (ERS s.2.1)

Which outdoor surfaces are a floor finish and which belong to another element, each counted once? The GF court is ONE
drawn face inside the plot boundary-wall inner faces (T-157 polygon 177.1154 m2) whose only hole is the pool footprint
(the outer D cut at the boundary-wall face). It is cut along drawn lines into six plan pieces, each a floor with its own
finish; the entrance-step risers are vertical faces of the same stair assembly; the pool water face is NOT a floor (pool
finish, its own element); the boundary-wall faces are facade (not here); the side passage is a separate face (already
in the candidate, Q-67 A).

## 2. BOQ lines added (V3.0.24 -> V3.0.25; every V3.0.24 line byte-identical: 3,710 SAME, 8 ADDED)

| Line | Element | Item | V3.0.24 | V3.0.25 | Evidence status | Material | Source (drawing) |
|---|---|---|---|---|---|---|---|
| L-57084fa9d3d0a37212fd | GF-COURT#WEST-OPEN | EXT.PAVING.INTERLOCK | absent | **119.5416 m2** | DRAWING-CONFIRMED | interlock, ASSUMED - OWNER-APPROVED (OWNER_RULE_OUTDOOR_FLOORS 23:20, owner choice over the renders) | T-157 OD-01: west court 138.760 less the 1F overhang 19.218; section B-B p.11 open sky |
| L-dd6e372825ce06d45bdd | GF-COURT#PORCH | EXT.FLOOR.OUTDOOR | absent | **HELD [10.6785, 10.6785] m2** | area DRAWING-CONFIRMED, finish HELD | owner: wood / ceramic / marble (decision 23:20 "material later") | T-157 OD-02: 2.00 x 4.30 + 1.20 x 1.50 + 1.40 x 0.20 (drawn 10.6785); B-B p.11 under the 1F |
| L-314c3ac6d45431b687c5 | GF-COURT#E1-TREADS | FIN.MARBLE.TREAD | absent | **3.3594 m2** | DRAWING-CONFIRMED | marble, ASSUMED - OWNER-APPROVED (UP-STAIR-001) | sheet03: 4 treads 0.30 x 2.80 (printed 280) |
| L-0afa7bd369ec489ebfc2 | GF-COURT#E1-RISERS | FIN.MARBLE.RISER | absent | **1.96 m2** (vertical, outside the plan closure) | DRAWING-CONFIRMED | marble (UP-STAIR-001) | 5 x (0.85 / 5 - 0.030) x 2.80; levels +0.15 / +1.00 printed, 5 risers in B-B; FLAG riser 0.170 > 0.16 (S-1 check only) |
| L-3dd82a576dce1beb4250 | GF-COURT#E1-LANDING | FIN.MARBLE.LANDING | absent | **5.1794 m2** | DRAWING-CONFIRMED | marble (UP-STAIR-001) | sheet03 printed 140 x 370 outside the main door |
| L-ab44fbc79bed353bde99 | GF-COURT#NORTH-WALK | EXT.FLOOR.PORCELAIN | absent | **21.0142 m2** | DRAWING-CONFIRMED (Checker 21.021) | porcelain / ceramic, ASSUMED - OWNER-APPROVED (sides rule 20:45) | 1.30 x 16.17; section A-A sheet10 open sky. **Owner manual 1.50 x 15.97 = 23.955 beside** (to the plot line: -3.194 wall thickness, +0.260 corner column), never used |
| L-1c51d1e7a3b65243382a | GF-COURT#POOL-DECK | EXT.FLOOR.OUTDOOR | absent | **HELD [6.548912, 6.548912] m2** (r2; was 7.105836) | area DRAWING-CONFIRMED, finish HELD | owner: pool deck undecided | face to the glazed band's COURT face (ARC 201) 16.784476 less the EXACT outer D 10.235564 (section 3, R-T343-1) |
| L-0b3dce44cf70ae95ccd6 | GF-POOL-WATER#FINISH | EXT.POOL.WATER_FACE | absent | **BLOCKED_RFI, blank**; bound 21.308727 m2 beside | HELD | not specified (no sheet, no Urban rule) | floor water D 8.578838 + perimeter 11.069469 x **1.15** (finished floor -> rim) |

Released V2.9: none of the 8 lines exists (NOT_IN_RELEASED). Totals moved only on the family codes: interlock +119.5416,
outdoor porcelain +21.0142, marble tread 27.324413 -> 30.683813 (+3.3594), landing 4.9225 -> 10.1019 (+5.1794), riser
0 -> 1.96 (the 14 interior riser lines stay BLOCKED: their riser heights are not established; E1's are printed), held
outdoor finish 17.227412 as ranges (r2; was 17.784336), pool finish 1 blank line.

## 3. The deck by the exact arc, the closure, and what is named

- Pool outline (own DXF check this run, P7757.dxf): ARC 200 r 1750 and ARC 202 r 1550, both 90 -> 270 deg about one
  centre; LINEs 203 / 205 and 204 / 206 each 1550 to the boundary-wall face: a D. Outer D cut at the wall face = pi
  1.75^2 / 2 + 3.50 x 1.55 = 4.810564 + 5.425 = **10.235564 m2** (perimeter 12.097787); T-071's tessellated hole 10.232
  -> residual **-0.003564 m2**.
- r2 (D-T343-1, Checker Gate B 2026-10-29 23:05; own re-read of the handles 2026-10-30 on P7757.dxf ab54dd55). The
  pool court face meets a 0.20 curved glazed band. Concentric with the pool ARCs 200 / 202 the plan draws ARC 201 (layer
  5, r 2250, 96.38 -> 263.62 deg: it ends exactly on the house east face, 0.25 from the pool centre) and four window
  polylines W 27D / 27E / 27F / 280 (bulge radii 2450 / 2410 / 2370 / 2330, straights 0.08 .. 0.20 inside the house
  face). ARC 201 is the band's COURT face (the printed 657 line, owner Q-38 A); W 280 is the outermost frame line.
  T-157's polygon (17.3414) walked W 280. Rule **R-T343-1** (engine/source/arch_v3025.py): a floor face meeting a
  glazed band stops at the band's court face; the recess in front of the frame is the opening's reveal strip.
- Deck face from the drawn terms: rectangle 1.80 x 5.60 = 10.080 (house east face LINEs 94 / 95 / 96 on the chord ->
  boundary-wall inner face LINE B7; south face LINE E2 -> house north-face line 2BC) + band segment r 2.25 beyond the
  chord at 0.25 = 2.25^2 acos(0.25 / 2.25) - 0.25 sqrt(2.25^2 - 0.25^2) = 7.388450 - 0.559017 = 6.829476 (T-127 hand
  6.8295) - column LWPOLYLINE 2F87 0.50 x 0.25 = 0.125 -> **16.784476 m2**. Deck = 16.784476 - 10.235564 =
  **6.548912 m2** (exact 6.5489118; the Checker's 6.548911 is the same value truncated). Was 7.105836: -0.556924 m2.
- SX-02 (the recess between the band face and the frame line W 280): frame segment r 2.33 beyond its straights at 0.33
  = 6.995053 + straights 0.08 x 4.95 (y +2.500 .. -2.450) = 0.396 - band segment 6.829476 = **0.561577 m2**: the
  glazing reveal strip of the merged T-127 (0.561) / T-154 (0.5609) ledgers, one surface one line, HELD there with
  T-123. Named in the closure (REVEAL_STRIP row); never deck, never 0, not a line here. (Checker 0.561447 = 17.345922 -
  16.784475: -0.000130 against this exact construction from the bulge (r 2330.000) and the straights; its cause not
  traced, under 0.001 m2, and it moves no line: SX-02 is a closure term.)
- The T-157 polygon 17.3414 vs the exact frame-walked face 16.784476 + 0.561577 = 17.346053: tessellation residual
  **-0.004653 m2**, named (READING_RESIDUAL row); this closes the "not measured" item of r1.
- Closure: plan pieces 119.5416 + 10.6785 + 3.3594 + 5.1794 + 21.0142 + 6.548912 = **166.322012** vs face 177.1154
  + 0.004653 (residual) - 10.235564 (exact D) - 0.561577 (SX-02) = 166.322912: **-0.0009 m2** (T-157's own re-add
  rounding: porch printed 10.6785 of a 4-decimal polygon, face 177.1154 vs 138.759 + 21.014 + 17.341); against the
  T-342 reference 166.883: -0.560988 = -0.561577 (SX-02) - 0.003564 (tessellated hole) + 0.004653 (frame-line
  tessellation) - 0.0005 (porch rounding in T-342). Tolerance declared 0.005 m2.

## 4. Pool water-face finish: the rim height from the section (Checker note on 1.15 vs 1.20)

The finish lies on the finished surfaces: the floor at the finished pool floor -0.85 (on its 50 mm build-up) and the
walls from that floor to the rim +0.30. P7757.dxf NW elevation cut (Drive Alsenan_Architectural_P7757 Pages_07-08):
**DIMENSION handle 2E5E = 1150**, from the layer-5 line between the inner wall faces (-0.85) to the rim (+0.30), own
reading this run. The 1.20 is the wall CONCRETE from the structure line -0.90 (T-183 r2, VERIFIED) and stays beside, not
used: the finish never reaches below the finished floor. The 0.15 upstand's outer face above the deck (8.998 x 0.15 =
1.350 m2) faces the deck, not the water: not in this bound. Bound = 8.578838 + 11.069469 x 1.15 = **21.308727 m2**.
Engine module refuses a rim taken from the base top (rim_basis), a rim above the structural height, or a rim in mm.

## 5. Owner manual method and drawing-derived method side by side

| Piece | Owner manual method | Drawing-derived | Difference |
|---|---|---|---|
| North side walk | 1.50 x 15.97 = 23.955 (printed, to the plot line) | 1.30 x 16.17 = 21.021 (polygon 21.0142) | -2.941 (-12.3 %): RULE_DIFFERENCE (wall thickness 0.20 x 15.97 = -3.194; corner column +0.260; polygon -0.007) |
| Other pieces | none recorded (no answered owner rule measures them by hand) | drawn polygons | - |

## 6. Against the freelancer (FIN workbook; not proof)

- Yard 151.80 m2 (one row) vs open court 119.5416 + porch 10.6785 + north walk 21.0142 = **151.2343 (-0.566, -0.37 %)**:
  AGREE / RULE_DIFFERENCE (T-157). He carries no pool deck and no side passage in his yard.
- Entrance landing 5.10 vs 5.1794 (+0.079, +1.6 %): ENGINE_RIGHT (printed 1.40 x 3.70). His "5 steps x 2.80 = 14.00" is
  a per-step length basis, not a tread area: not comparable as m2.
- Pool finish: his floors 21.00 + walls 19.80 = 40.80 m2 vs the drawn bound 21.309 (8.579 + 12.730); not reproduced by
  the drawn pool (no pump room, no steps drawn); UNRESOLVED until the finish is specified (the line stays blank).

## 7. Cross-check (acceptance c): no area shared, 0.000 m2

V3_0_25_CLOSURE.csv lists 11 V3.0.24 lines with why each shares 0.000 m2: side passage 5.64 (its own face), the garden
band lines 9.101 / 4.885 / 1.364 (inside, D-48), the 3 pool concrete lines (the court's hole), the pool court soffit
12.834 (a ceiling), and the interior stair rooms' tread / landing lines (faces of the same GF polygonization, disjoint
from the court face). The module also refuses any V3.0.24 line already on a piece's element or on the family's own item
codes (none found).

## 8. Validation

- Full CLI run (`research/agents_t343/v3025_run.py`, `tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V3.0.25`), own
  Drive copies P7757.dxf ab54dd55 / ST7757 9f9d1179: V3_0_24 json **19394733** reproduced (= the candidate of record);
  V3_0_25 lines = `v3025_direct.py` on the same V3.0.24 (hashes in the board handoff). Line-state check (T-334 tool)
  over all 3,718 lines: 3,718 OK, flagged 0. Default guard re-check: no finding on an added line.
- tests/t343_outdoor_floor_integration: villa P343 by hand (not Alsenan): D outline values, 8 lines and states, closure
  0, tessellation residual named, export line-state OK, files / diff / totals; adverse: circle for a D, deck from a
  circle area, court on an interior tile line, held material as 0, held finish on a priced item, owner-approved finish
  without source or on the blank item, a missing piece and mm2 areas fail the closure, piece twice, element already
  carried, family already in the run, cross-check shared area and stale line, pool rim from the structure / in mm /
  above the structure, pool water as a floor piece, declared total, a held line with a figure, a changed V3.0.24 line,
  order reversed. r2 (R-T343-1, villa P343-B by hand: band segment r 2.00 at 0.50 = 4.304218, deck face 16.214218,
  deck 6.679926, reveal strip 0.398518, closure 0): deck to the band face with the strip and the residual named; adverse:
  a deck face built with the frame segment, the frame-walked polygon taken as the deck face (both refused: window-frame
  line), the frame face flagged as a drawn line (fails the closure: counted twice), a strip as 0 / without its scope / off
  its construction, a face off its construction, a residual too large for a tessellation. Inputs pins (merged ledgers, edited ledger stops the build). Master 1.20.0 (builder, checks clean,
  dropping the entry is stale).
- L4 full suite: see the board handoff (known private-input / environment failures compared file by file on the base).
- r2 (2026-10-30, own Drive copies P7757.dxf ab54dd55 / ST7757 9f9d1179, fresh T-167 base run): V3_0_24 json
  19394733 reproduced; full CLI run = `v3025_direct.py` byte for byte: V3_0_25 json 3064078a, csv 97d6e749, DIFF
  2752711c, ledger json 44e80d86 / csv 9d6fbc03, CLOSURE 5e83e0e5, RUN 1b51eb1c. r1 (2609e152) re-run on the same
  V3.0.24 reproduces its json f44a4bb5; r1 -> r2: ONE line changes (L-1c51d1e7a3b65243382a pool deck, held range
  [7.105836] -> [6.548912]), the other 3,717 lines byte-identical (3,710 V3.0.24 lines + 7 added lines). Line-state
  check 3,718 OK / 0 flagged. L4 tests/ on 90b1811a: 396 failed / error in 43 files, the same known private-input /
  environment set as the r1 base record (396 on d395aebb); NEW 0; t343 37 pass.

## 9. For the Checker (Gate B always-checked lines)

Every added line is new scope (all hand-checked by rule): re-measure the deck (r2: face to ARC 201 from the handles, 16.784476; the D from ARC 200 /
LINEs 204 / 206; SX-02 0.561577 and the -0.004653 residual in the closure), the closure, the E1 tread / landing / riser arithmetic from the printed 280 / 140 x 370 / levels, the
rim 1150 (DIMENSION 2E5E) and the bound, the north walk 1.30 x 16.17 vs the owner manual. Material classification: the
three ASSUMED - OWNER-APPROVED sources. Cross-trade: pool lines and the soffit (no double count).

## 10. Lessons-register row (proposed)

| 2026-10-29 | an outdoor court had no candidate line while its pieces were measured and Checker-merged (T-157 / T-342); the deck had been read with a circle (T-157) and with a tessellated hole (T-342) | a printed radius was read as a circle, and a polygonized arc was used as the exact outline | a piece cut by a drawn curve is the face less the EXACT drawn outline (a D = half disc + rectangle 2r x straight, accepted only when its back is 2r); the pieces re-add to the face less its exact holes within a declared tolerance, and the tessellation residual is named in m2; the pool finish rises from the finished floor, never from the base top (every villa) | tests/t343_outdoor_floor_integration (normal: villa P343 closes to 0.000; adverse: circle for a D, deck from a circle area, rim from the base top, mm) | PROPOSED |
| 2026-10-30 | r2 (D-T343-1): the deck face was taken from a polygon walked along the window-frame line inside a 0.20 curved glazed band, so the 0.56 m2 recess in front of the frame (already the glazing reveal strip SX-02 of a merged ledger) was counted a second time as deck (+8.5 %) | a merged polygon was reused without asking which drawn line its curved edge follows; four concentric curves (band face + frame lines) look alike | R-T343-1: a floor face meeting a glazed band stops at the band's court face (the printed dimension line); the recess in front of the frame is the opening's reveal strip, named in the closure by its own construction, never a floor piece and never 0; a face bordering a curve is built from drawn terms (rectangles, segments beyond a chord), and a polygon reading of it is kept beside with its tessellation residual named (every villa) | tests/t343_outdoor_floor_integration (normal: villa P343-B deck to the band face, strip named, closure 0; adverse: deck walked along the frame line refused, frame face as a drawn line fails the closure) | PROPOSED |

Verdict proposals: deck 6.548912 (r2: band court face less the exact D) ENGINE_RIGHT vs r1 7.105836 (frame line, SX-02
counted twice), T-342 7.1094 (frame line + tessellated hole) and T-157 7.9392 (frame line + circle); yard
AGREE / RULE_DIFFERENCE (-0.37 %); landing ENGINE_RIGHT; north walk RULE_DIFFERENCE vs the owner manual; pool finish
UNRESOLVED (not specified).

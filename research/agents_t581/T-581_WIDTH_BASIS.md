# T-581: lintel masonry-opening width basis census (frame-block doors, owner lintel rule, V3.0.58)

Worker 1, lane S, non-candidate, claim 2026-11-07 (run session_01E6cPnesQyU9p3mL2cRDEEp), engine base f4409c96.
**r2 (2026-11-07T05:23Z, Verifier REWORK 04:05Z):** D-GF-09 is a DRAWING CONFLICT, UNRESOLVED and HELD with a bound;
R-T581-1 1.1.0 (2) adds 'wall ends inside the block footprint -> UNRESOLVED'; T-571 table restated with D-GF-09 held;
the r1 ENGINE_RIGHT proposal is withdrawn. Sections 2-6 are the r2 text; the 25 other openings are unchanged from r1.
Files: `t581_width_basis.py` (rule proposal R-T581-1 + generic DXF reader + restatement through R-T571-1),
`out/T581_WIDTH_BASIS.json` (DXF handles, block names, widths only), `tests/t581_width_basis/` (26 tests). Nothing in
engine/, rules/, knowledge/, registry or any candidate changed. The architectural DXF was read from Drive folder
'Alsenan chalet project' (architectural DXF zip) into the git-excluded private folder; only numbers and handles here.

## 1. Physical element and question (ERS s.2.1)

A precast lintel spans the **masonry opening**: the gap between the two drawn wall-face ends at the jambs; the door frame
sits inside it. A door block carries three widths: block **overall** (outer edges of the frame jambs), **frame-clear**
(inner edges, = the threshold line on layer 5 where drawn) and the **masonry opening** (wall-face line ends on layer 1).
Finding F-C-T571-1 said census r3 used frame-clear for D-GF-09 (0.90, D120 = 1.00 overall) but block-overall for D-GF-03
(d220, 0.90): a mixed basis, with D-GF-09's masonry 1.00 if the wall ends sit at the block edges.

## 2. Census: every frame-block insert, both faces read (masonry = layer-1 wall-end gap)

| block | overall / frame-clear (m) | openings (insert) | wall ends sit | masonry face a / b (m) | census r3 | lintel (b 0.15) |
|---|---|---|---|---|---|---|
| D120 (0.20 wall) | 1.00 / 0.90 | D-GF-01 (15E), D-GF-05 (192), D-GF-06 (33E), D-GF-08 (2C7) | at block edges | 1.000 / 1.000 | 1.00 | 1.50 |
| D120 | 1.00 / 0.90 | **D-GF-09 (3FF)** | **INSIDE the block footprint: wall ends 46.9 / 946.9 mm in block axes (frame edges 0 / 1000) on both faces; the 1.00 frame is drawn over the masonry** | **0.900 / 0.900 (drawn)** | 0.90 | **UNRESOLVED, bound 1.20 .. 1.50** |
| d220 (0.20) | 0.90 / 0.80 | D-GF-03 (1B5), D-1F-05 (C1A), D-2F-02 (12C2) | at block edges | 0.900 / 0.900 | 0.90 | 1.20 |
| D115 (0.15) | 1.00 / 0.90 | D-GF-13 (2F2), D-1F-02 (C31), D-1F-03 (C32), D-2F-01 (12BA) | at block edges | 1.000 / 1.000 | 1.00 | 1.50 |
| D215 (0.15) | 0.90 / 0.80 | D-1F-08 (C18), D-1F-09 (BEF) | at block edges | 0.900 / 0.900 | 0.90 | 1.20 |
| D315 (0.15) | 0.80 / 0.70 | D-GF-02 (1EF), D-GF-04 (19E), D-GF-11 / -12 (321 / 320, an identical pair), D-1F-01 (C2B), D-1F-04 (C2E), D-1F-06 (11B4), D-1F-07 (BEE), D-1F-10 (C12), D-2F-03 (12BB) | at block edges | 0.800 / 0.800 | 0.80 | 1.20 |
| D315 | 0.80 / 0.70 | D-GF-10 (339) | 3 mm inside the left edge | 0.797 / 0.797 | 0.80 | 1.20 |
| D200 double (0.20) | 2.00 / 1.90 | D-GF-07 (281) | at block edges | 2.000 / 2.000 | 2.00 | 2.50 |
| arch120 (jamb lines, no frame) | 1.00 / - | A-GF-01 (1F8), A-1F-01 (BEC) | at the jamb lines | 1.000 / 1.000 | 1.00 | 1.50 |

26 frame-block doors + 2 arch blocks, every one on both faces (faces agree to 0.0 mm). Outside the census: D120 2D8
(boundary-wall door on the site layer, S8.6 OP-GF-B01 SYMBOL_ONLY; no building masonry; listed, no lintel row). Doors
without a block (D-GF-14 loose arc, closure 0.80) are not frame-block openings and keep their census reading.

**Result: census r3 is on ONE basis, the masonry wall ends, at 25 doors; D-GF-09 is UNRESOLVED (DRAWING CONFLICT).**
The 'mixed basis' premise of F-C-T571-1 is withdrawn (the Verifier's own re-measure agrees: 5 / 5 widths). But at insert
3FF the D120 frame (1.00 overall, 0.05 jambs) is drawn OVERLAPPING both wall ends (46.9 mm left, 53.1 mm right on both
faces): a 1.00 frame cannot sit in a 0.90 masonry gap, so the drawing is internally inconsistent there. Admissible
readings, neither chosen: (a) the masonry is 0.90 and the door is narrower than its D120 symbol -> lintel 1.20; (b) the
masonry is 1.00 (the wall lines are drawn short) -> lintel 1.50. Designer item (masonry 0.90 vs D120 frame 1.00 at
D-GF-09); no owner question (ERS s.2.7: a drawing conflict is resolved by the designer, not an owner rule). D-GF-10 (3 mm
inside the edge) is within the 5 mm draughting tolerance and stays DRAWING-CONFIRMED 0.797 (lintel 1.20 either way).

## 3. T-571 table restated on the masonry basis, D-GF-09 HELD by name

Owner rule b 0.15, engine AT_MOST, GF / 1F / 2F:

| stock | T-571 (r3 widths) | held table (D-GF-09 HELD) | low (D-GF-09 0.90) | high (D-GF-09 1.00) |
|---|---|---|---|---|
| 1.20 | 13 / 14 / 3 | 12 / 14 / 3 | 13 / 14 / 3 | 12 / 14 / 3 |
| 1.50 | 9 / 6 / 5 | 9 / 6 / 5 | 9 / 6 / 5 | 10 / 6 / 5 |
| 2.50 | 5 / 4 / 0 | 5 / 4 / 0 | 5 / 4 / 0 | 5 / 4 / 0 |
| 3.00 | 0 / 1 / 0 | 0 / 1 / 0 | 0 / 1 / 0 | 0 / 1 / 0 |
| total | 60 nr, 91.5 lm | 59 nr + D-GF-09 held, 90.3 lm | 60 nr, 91.5 lm | 60 nr, 91.8 lm |

Count 60 nr unchanged; GF 1.20 / 1.50 = 12-13 / 9-10; **lm 91.5 .. 91.8**. The only changed opening is D-GF-09 (width 0.90
-> held, bound 0.90 .. 1.00, lintel 1.20 .. 1.50, +0.3 lm at the high end). ESTABLISHED 16 nr unchanged at both ends
(D-GF-09 is AT_MOST only). **T-571's AT_MOST 91.5 lm is NOT an upper bound**: with D-GF-09 at 1.50 the at-most total is
91.8 lm; the restated upper bound is 91.8 lm (60 nr), the lower end 91.5 lm.

Refused bases, beside (never the width):
- block overall at every insert: only D-GF-09 moves, GF 1.20 13 -> 12, 1.50 9 -> 10, +0.3 lm (this is the F-C-T571-1
  figure: it rests on reading the symbol, not the wall ends);
- frame-clear at every insert: 8 doors drop 1.50 -> 1.20 (D-GF-01 / -05 / -06 / -08 / -13, D-1F-02 / -03, D-2F-01),
  -2.4 lm: the frame sits inside the masonry, so frame-clear understates the span.

Verdict proposals: D-GF-09 width 0.90 vs his 1.00: UNRESOLVED (r1 ENGINE_RIGHT withdrawn: his 1.00 = the D120
frame, which is drawn over 0.900 wall ends; designer item). D-GF-03 0.90 vs his 1.00: RULE_DIFFERENCE stands (Q-04 owner minimum view +0.10; the d220 symbol
itself is 0.90). F-C-T571-1 'mixed basis': proposed CLOSED (withdrawn); its quantity question survives as the D-GF-09 bound (+0.3 lm).

## 4. Rule R-T581-1 1.1.0 (every villa)

(1) Width basis = gap between the two wall-face line ends, both faces; one basis per census; a frame-clear, block-overall
or leaf-radius basis is refused and a mixed census is refused. (2) Faces within 5 mm -> the width (DRAWING-CONFIRMED);
faces disagree, a face line runs through, or no wall end within 0.80 m of the block -> UNRESOLVED by name (held, never
the block width, never 0). 1.1.0: a wall end more than 5 mm INSIDE the block footprint (frame drawn over masonry) ->
UNRESOLVED, DRAWING CONFLICT (designer item), held with the bound [wall-end gap, block overall] and its lintel bound;
neither end chosen. Wall ends OUTSIDE the block (masonry wider than the symbol) remain the opening. (3) A printed jamb-to-jamb dimension governs (Q-32 A). (4) Block overall and frame-clear are
listed beside. Reader checks units (frame overall 0.5 .. 3.0 m in mm), handles mirror and rotation by the insert matrix.

Tests (32): villa Z fixture (D block 1.00 overall, 0.05 frames, wall ends at the edges: 1.00 + 0.30 = 1.30 -> 1.50;
frame-clear 0.90 -> 1.20 refused basis); ADVERSE frame drawn over masonry (ends 47 / 947 -> UNRESOLVED, bound 0.90 .. 1.00,
lintel 1.20 .. 1.50; one end inside -> UNRESOLVED; 3 mm inside = tolerance, confirmed; ends outside the block = the
opening); restatement holds the conflict by name with low / high tables and says the census AT_MOST stops being an upper
bound (6.9 -> 7.2 lm by hand); bound in metres refused; faces disagree / no end / line through -> UNRESOLVED and HELD; mixed basis, frame-clear, block-overall, leaf-radius and metre-as-mm refused;
restatement attributes each change to an opening id; synthetic DXF with rotation 0 / 90 / 225 and mirror (shifted
symbol -> conflict; edge ends -> confirmed); block in metres refused; training villa (25 doors one basis, D-GF-09
UNRESOLVED with bound, T-571 table restated 60 nr / 91.5 .. 91.8 lm, refused bases beside, stale map refused).

## 5. Open

- The engine lintel ledger is untouched (research only). Wiring for Worker 3: D-GF-09 lintel HELD (bound 1.20 .. 1.50),
  not 1.20; T-571 AT_MOST lm restated 91.5 .. 91.8 (upper bound 91.8).
- Designer item for the RFI list: D-GF-09 masonry opening 0.90 (wall ends) vs D120 frame 1.00 drawn over the masonry.
- 2D8 boundary-wall door: no lintel row anywhere (site works; compound-wall head not established): named for the Lead.

## 6. Lessons row (proposed, ERS s.7)

| 2026-11-07 | a census width was called 'frame-clear' because it was smaller than the door block; r1 then called the wall-end width confirmed although the frame was drawn over the masonry | the block was assumed to sit on the wall ends; at one insert it is drawn into the masonry, and a method rule was taken as drawing evidence | read the wall-face ends on both faces at every insert; block overall and frame-clear beside, never the width; wall ends inside the block footprint = DRAWING CONFLICT, UNRESOLVED with a bound (designer item), never resolved by the method | tests/t581_width_basis | T-581 |

# T-581: lintel masonry-opening width basis census (frame-block doors, owner lintel rule, V3.0.58)

Worker 1, lane S, non-candidate, claim 2026-11-07 (run session_01E6cPnesQyU9p3mL2cRDEEp), engine base f4409c96.
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
| D120 | 1.00 / 0.90 | **D-GF-09 (3FF)** | **at the frame's inner lines (wall ends 46.9 / 946.9 mm in block axes; the frames are drawn inside the masonry)** | **0.900 / 0.900** | 0.90 | **1.20** |
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

**Result: census r3 is on ONE basis, the masonry wall ends, at all 26 doors.** The premise of F-C-T571-1 does not hold
at D-GF-09: on insert 3FF the layer-1 ends are not at the block's outer edges (both faces 0.900; same reading as T-260
and T-568 JAMB_READS). D-GF-09 0.90 is the masonry opening, not frame-clear; D-GF-03 0.90 is the masonry opening
that happens to equal the d220 overall. Not "mixed".

## 3. T-571 table restated on the masonry basis: no change

Engine AT_MOST, owner rule b 0.15: 1.20 = 13 / 14 / 3, 1.50 = 9 / 6 / 5, 2.50 = 5 / 4 / 0, 3.00 = 0 / 1 / 0 (GF / 1F / 2F):
**60 nr, 91.5 lm, unchanged** (0 openings changed; asserted). ESTABLISHED 16 nr unchanged. The freelancer-implied
reconciliation of T-571 is unchanged (no width moved).

Refused bases, beside (never the width):
- block overall at every insert: only D-GF-09 moves, GF 1.20 13 -> 12, 1.50 9 -> 10, +0.3 lm (this is the F-C-T571-1
  figure: it rests on reading the symbol, not the wall ends);
- frame-clear at every insert: 8 doors drop 1.50 -> 1.20 (D-GF-01 / -05 / -06 / -08 / -13, D-1F-02 / -03, D-2F-01),
  -2.4 lm: the frame sits inside the masonry, so frame-clear understates the span.

Verdict proposals: D-GF-09 width 0.90 vs his 1.00: ENGINE_RIGHT (his 1.00 = the D120 symbol overall; the wall ends are
0.900 on both faces). D-GF-03 0.90 vs his 1.00: RULE_DIFFERENCE stands (Q-04 owner minimum view +0.10; the d220 symbol
itself is 0.90). F-C-T571-1 attribution: proposed CLOSED, no quantity change.

## 4. Rule R-T581-1 1.0.0 (every villa)

(1) Width basis = gap between the two wall-face line ends, both faces; one basis per census; a frame-clear, block-overall
or leaf-radius basis is refused and a mixed census is refused. (2) Faces within 5 mm -> the width (DRAWING-CONFIRMED);
faces disagree, a face line runs through, or no wall end within 0.80 m of the block -> UNRESOLVED by name (held, never
the block width, never 0). (3) A printed jamb-to-jamb dimension governs (Q-32 A). (4) Block overall and frame-clear are
listed beside. Reader checks units (frame overall 0.5 .. 3.0 m in mm), handles mirror and rotation by the insert matrix.

Tests (26): villa Z fixture (D block 1.00 overall, 0.05 frames, wall ends at the edges: 1.00 + 0.30 = 1.30 -> 1.50;
frame-clear 0.90 -> 1.20 refused basis); shifted symbol (ends 47 / 947 -> 0.90, not 1.00); faces disagree / no end /
line through -> UNRESOLVED and HELD; mixed basis, frame-clear, block-overall, leaf-radius and metre-as-mm refused;
restatement attributes each change to an opening id; synthetic DXF with rotation 0 / 90 / 225 and mirror; block in
metres refused; training villa (26 doors one basis, D-GF-09 0.90, T-571 table unchanged, refused bases beside, stale
map refused).

## 5. Open

- The engine lintel ledger is untouched; nothing to wire (no width moved).
- 2D8 boundary-wall door: no lintel row anywhere (site works; compound-wall head not established): named for the Lead.

## 6. Lessons row (proposed, ERS s.7)

| 2026-11-07 | a census width was called 'frame-clear' because it was smaller than the door block | the block was assumed to sit on the wall ends; at one insert it is drawn into the masonry | read the wall-face ends on both faces at every insert; the block overall and frame-clear are listed beside, never the width | tests/t581_width_basis | T-581 |

# T-746 paint at opening edges as lm on ARCH_TAKEOFF_V3.0.74 (lane A, research, unwired)

Worker 2, 2026-11-12. Owner rule 2026-11-12 PAINT ("lm for windows doors and corners, so the Area is the same");
UP-FIN-PAINT-002 1.0.0 param `edges` = LM_ITEMS_NOT_AREA; Lead ruling on the T-746 row: reading B (a door / window
return is an lm item per opening, never paint m2). Nothing wired, no candidate line moves, no default changes (wiring:
T-749). No new rule version: 1.0.0 already states edges as lm; its `not_given` sentence on reveals is now settled by
the Lead ruling and should be dropped in the next rulebook version (named, not edited).

## Files

- `t746_rules.py`: R-T746-1 `edge_lm` / `edge_parts` (per component: jambs 2h, head w, painted sill w; PAINT_LM /
  BOUNDED / NO_PAINT_EDGE / HELD; mm and negatives refused, missing size HELD never 0), R-T746-2 `restate_return_line`
  (paint m2 -> 0 with the lm beside it; identity plaster = depth x (2h + w) or refused; blank face HELD), `bind_once`,
  R-T746-3 `paint_after`, `sum_lm`.
- `t746_frames.py` -> `DOOR_FRAMES_T746.csv`: door frame census from the plan DXF by T-249 handle (block posts closed over
  the wall depth AND their outer edges at the drawn masonry jambs on both faces, 5 mm tolerance). Handles, block names
  and sizes only.
- `t746_alsenan.py` -> `out/T746_PAINT_EDGES.{json,md}` (inputs sha-pinned: LINE_INDEX V3.0.74, T-313 reveal ledger,
  T-709 flags, T-740 output, the frame census; `--check`).
- `tests/t746_paint_edges_lm` (36): synthetic villa V746 by hand + development-villa pins.

## Result

Door / arch / gate returns (the 30 FIN.PAINT `:RETURN_PAINT` lines, by line id in the out md):

| | before | after (reading B) |
|---|---|---|
| paint m2 on the 30 lines (engine V3.0.74) | 0 .. 24.150 | 0 (moved to lm) |
| paint m2 on the 30 lines (T-740 rule, reading A) | 20.250 .. 24.150 | 0 |
| edge lm | none | 0 .. 33.800 lm (27 BOUNDED, 3 HELD: A-GF-01, A-1F-01, D-GF-15) |
| plaster m2 | 24.150 | unchanged |

- Gross return length 144.400 lm = T-313 jambs 119.400 + heads 25.000 (independent ledger, AGREE; every valued line
  plaster = depth x (2h + w) to 0.000001).
- JAMBS 0 on 25 doors: the plan door blocks (D115 / D120 / D200 / D215 / d220 / D315) draw 50 mm frame posts as closed
  rectangles over the full wall depth (0.15 / 0.20 = T-150 / ledger depth), outer edges at the drawn masonry jambs
  (offsets 0.0 mm; D-GF-10 3.0 mm): the frame covers the whole jamb reveal = FRAME_COVERS_RETURN_DRAWN. This retires the
  "frame-covered depth printed nowhere" premise of R-T709-4 / R-T717-1 (c) for the jambs.
- JAMBS 0 .. 8.80 lm: D-GF-09 (D120 block 1.000 m vs masonry gap 0.900 m: posts 46.9 / -53.1 mm off the jambs,
  POSITION CONFLICT, never read as cover; ledger 0.900 = masonry AGREE) and D-GF-14 (plan symbol is an ARC, no frame).
- HEAD 0 .. 25.000 lm: a plan does not draw the head member; 0 .. w until a door section / elevation shows it.
- 5 doors between two wet rooms (D-1F-06, D-GF-02, D-GF-10, D-GF-11, D-GF-12): head cause WET_BOTH_SIDES (T-634).

Windows (58 sides): room side 27 NO_PAINT_EDGE (frame flush with the room face, T-313 DRAWING-CONFIRMED: 0 lm, also in
tiled walls), 2 HELD (W03 / W17 curved). Outside 26 PAINT_LM = 106.020 lm (jambs + heads; = T-313 77.720 + 34.630 -
W02 head 6.330), 3 HELD (W02 height, W03, W17). External sills / thresholds are their own item (ARCH.WINDOW_REVEAL),
not a paint edge. These outside edges are exterior: T-747 cites this figure, never recounts it. No line exists for them
(missing family, T-313).

Paint m2 (FIN.PLASTER / FIN.PAINT faces, T-740 basis): rule A 841.261 .. 929.205 -> rule B 821.011 .. 905.055
(-20.250 / -24.150, -2.41 / -2.60 %); engine 822.198 .. 927.215 -> 822.198 .. 903.065 with the return lines out. By
floor GF 326.058 .. 391.793, 1F 369.296 .. 382.665, 2F 125.657 .. 130.597; room lines untouched, floor re-add residual
0.000000 at both ends.

## Engine vs freelancer, verdict proposals

- His paint carries door returns as area, 14 doors x 0.20 x 5.70 = 15.96 m2 (T-561, not by id); owner rule B: 0 m2 +
  lm: RULE_DIFFERENCE (scope). Door count 27 drawn (T-249 census) vs his 14: ENGINE_RIGHT on the count.
- F-T746-1 ENGINE_WRONG (bound too wide): the 25 framed doors' return paint low end 0 was taken as "frame not printed";
  the plan draws it for the jambs: paint lm jambs 0, head 0 .. w.
- F-T746-2 OPEN (plaster, not changed here): UP-FIN-PLASTER-001 plasters the jamb 2 x t x h behind a frame drawn over
  the full depth (19.920 m2 on 27 doors): whether the jamb is plastered before the frame is fixed is a method point for
  the plaster owner; no quantity moved.
- F-T746-3 DRAWING CONFLICT D-GF-09: block 1.000 m on a 0.900 m wall gap (handle 3FF); the masonry governs the opening.

## Checker re-measure suggestions (3 openings)

D-GF-07 (handle 281, D200: posts 0.050 x 0.200 at both jambs, masonry gap 2.000, head 2.000 lm, printed h 2.50),
D-1F-06 (11B4, D315 mirrored: 0.800 x 0.150, wet both sides), D-GF-09 (3FF: wall ends 0.900 apart vs block 1.000).

## Lessons register row (proposed, ERS s.7)

2026-11-12 | T-746 | door return paint bound 0 .. full on "frame detail printed nowhere" | the plan door block was never
read: its frame posts span the full wall depth at the masonry jambs | read the door block's frame posts against the
drawn masonry jambs before calling a frame depth unprinted; a block off the wall gap is a conflict, never cover |
tests/t746_paint_edges_lm.

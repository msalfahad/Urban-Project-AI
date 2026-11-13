# T-754 exterior paint edge residuals (worker 2, lane A, 2026-11-13; research, nothing wired)

No candidate line, hub, registry, rule / knowledge version file or default moves (wiring: T-314 r3 / a later paint
restatement). Rules R-T754-1 .. -4 1.0.0 (`t754_rules.py`, every villa); own DXF census `t754_census.py` (private input,
writes `in/T754_CENSUS.json`: handles, layers, levels, lengths and offsets along a named line only); application
`t754_alsenan.py` (`--check` rebuilds from the sha-pinned inputs) -> `out/T754_EDGE_RESIDUALS.{json,md}`; tests
`tests/t754_edge_residuals` (28). Drawing read this run: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip
(P7757.dxf sha256 ab54dd55; SE and NW elevation frames, datums 2439 / 2A42 re-checked; the plan door blocks D115 / D120 /
D200 / d220). The T-746 frame census was re-run on the same DXF: byte-identical to the committed CSV.

## 1. Physical elements

(a) the arris where a rendered external face turns into a door reveal (2 jambs + head), (b) the vertical convex arris at
a parapet corner, (c) the soffit / band arris of a 1F slab edge over open air, (d) a measured arris without a host line.
Each is one arris counted once in lm (OWNER RULE PAINT 2026-11-12, UP-FIN-PAINT-002 reading B); the paint area stays the
plaster area (no m2 moves here).

## 2. Results (before -> after)

| item | before | after | evidence | state |
|---|---|---|---|---|
| exterior door edges (7) | 0 .. 12.20 lm | 0 .. 12.20 lm, cause per door | jambs 0 on 6 doors (plan posts 50 x full depth at the masonry jambs, re-run identical); D-GF-09 jambs 0 .. 4.40 (block 1.000 in a 0.900 gap, 3FF); heads 0 .. w on all 7 | HELD (head) |
| NW-1/NW-2, NW-2/NW-3 parapet corners above +9.70 | 2 x 1.30 lm | **0** (NOT_A_CORNER) | top line 27CB projected 4.807698 = NW-3 0.578 + chord 3.059412 + NW-1 1.170294 (diff -0.000008); no vertical in +9.70 .. +11.00 inside the span; the first vertical (2737) is the SW-3/NW-1 round start at 4.509439 = 4.807698 - r 0.298259; T-348 2F plan: the parapet runs straight at the screen front | DRAWING-CONFIRMED (CAD) |
| NO_HOST passage-mouth arris | 1.40 lm, host blank | **1.40 on L-b05f70c9** | +4.80 .. +5.50: only P-1 (+0.30 .. +5.50) and P-2 (+1.00 .. +5.50) cover it (NE-5 NOT_A_FACE; NE-6 parapet top +4.80) | HOSTED |
| exterior corners hosted | 178.135812 .. 179.335812 | **176.935812 .. 178.135812** | -2.60 + 1.40 | bounded (stop-end) |
| exterior corners physical | 179.535812 .. 180.735812 | **176.935812 .. 178.135812** | -2.60; residual 0 | bounded |
| parapet-end corners (8 -> 6) | 9.185812 | **6.585812** | as above | DRAWING-CONFIRMED |
| GF passage-mouth stop-end | 0 .. 1.20 | 0 .. 1.20 | NE elevation raster; 1F plan outline at the mouth not traced this run | HELD |
| 1F slab edge below (lm) | 6 faces blank | SE-1 2.30 m of 4.10: ONE_PLANE, 0 slab-edge arris; NW-1 / NW-3 NOT_A_FACE (T-348); NW-2 cited (T-348); NE-1, NW-4, SW-1, NW-5, SW-2 and SE-1 rest 1.80 m HELD blank, cause per face | SE frame: no horizontal over the mouth span 2232 between +4.70 and +5.60; NW frame bands +5.30 .. +5.50 lie on the GF strip / pool-court fronts, not under the 1F wall | partly DRAWING-CONFIRMED |
| railing id of the p.12 X-lattice | not named | annex parapet top **RL-03** (L-b75c30fc, 7.967 lm); fence top **RL-10** (L-78babf2c, HELD) | T-164 census rows | named, excluded from B13-07 by id |
| paint low end (T-751) | +1.942210 not re-walked | re-added: 1,007.168044 + 1.075883 + 0.2225 + 0.643827 = 1,009.110254 (residual 0); 1C00 / 1BFE layer 5 and the pier handles re-read | merged figure stands | CHECKED |

## 3. Findings and verdict proposals

- F-T754-1 ENGINE_WRONG (T-751 / T-172 corner list, -2.60 lm): above +9.70 the NW-1, NW-2 and NW-3 parapets are one
  plane at the screen front (T-348 2F plan + the NW frame), so the plan junctions of the 1F outline (the arc NW-2 meets
  the piers) carry no parapet arris. Below +9.70 the T-172 / T-737 storey corners NW-1/NW-2 and NW-2/NW-3 (2 x 4.20 lm,
  EXT#1F-CONVEX) sit at the same junctions: in front the screen and pier fronts are one plane (no full-height vertical in
  the NW frame between 2792 and 2737), and the edges drawn there are the screen-arch jambs and mouldings (2719 .. 2784,
  springing about +6.86). Whether those 8.40 lm are the screen-opening edges (counted as opening edges elsewhere?) or
  arrises on the arc wall behind the screen is NOT decided here: Checker / owner of EXT#1F-CONVEX to re-walk; nothing
  moved.
- F-T754-2 DRAWING FACT (doors): no door head is drawn with depth anywhere (no section, no detail, no schedule:
  designer item 13 / D-62). The SE frame draws D-GF-07 beyond (layer 5) as a frame outline (jamb face 0.035 / 0.039,
  head face 0.017 / 0.020 below the head 220F +3.50): a face width, not a depth; the plan post face is 0.050. The head
  stays 0 .. w; the frame-head depth is the one fact that closes 6.90 lm (D-GF-09 also needs its frame-in-gap answer).
- F-T754-3 SE-1 face over the porch mouth: drawn as one plane from the mouth piece top +4.70 to the 1F (2.30 m span):
  the "slab edge below" there is not a band of unknown depth; its m2 (2.30 x 0.80 = 1.840 if no other face holds it) is
  for the T-314 r3 paint restatement to bind against GF/SE-2 and T-360 C-1 (nothing moved here).
- F-T754-4 NW frame, GF NW-7: a 7.50 m clear span between two 0.20 columns (27D6 / 27E0) with a +5.30 .. +5.45 front
  band and W02's lines beyond (layer 5) from +1.00 to +5.30: the W02 height / NW-7 storey bound 7.065 .. 35.55 m2 can be
  re-read from this frame by its owner (not this task).
- Engine vs freelancer: his corners 1,297.35 m.l vs vertical corners 176.94 .. 178.14 + windows 103.68 + doors 0 ..
  12.20 (+ T-337 horizontals): RULE_DIFFERENCE (scope, as T-751); this task lowers the physical corner total by 2.60 lm
  and the hosted total by 1.20 lm (2.60 removed, the 1.40 re-hosted, not new).

## 4. Checker re-measure suggestions

27CB (NW frame, +11.00, dx 4.807698) with the absence of any layer-1 vertical crossing +9.70 .. +11.00 between 2792 and
2737; 2737 at 4.509439 along 27CB (= r 0.298259 short of 27B0). Doors: D-GF-07 (plan 281: posts 0.050 x 0.200 at both
jambs; SE frame 1C00 / 220F / 1CF1 / 2234) and D-GF-09 (plan 3FF: block 1.000, masonry gap 0.900). SE frame: 2232
(+4.70, 2.30) with no horizontal over its span up to +5.60 (23EC layer 2, 241B, 2428 lie outside).

## 5. Lessons register row (proposed, ERS s.7)

2026-11-13 | T-754 | parapet corners counted at plan junctions | a corner taken from the plan outline (arc meets pier)
was carried up into a band where the parapet runs straight across | test every corner in each height band on the
elevation that sees both faces: true lengths summing to the projected top line with no vertical in the band = one
plane, no arris; a frame face width in an elevation is never a frame depth | tests/t754_edge_residuals.

# T-751 exterior paint edge and corner bounds closure (worker 2, lane A, 2026-11-12; research, nothing wired)

No candidate line, hub, registry, rule / knowledge version file or default moves (wiring: T-749 / T-314 r3). Rules
R-T751-1 .. -4 1.0.0 (`t751_rules.py`, every villa); own DXF census `t751_census.py` (private input, writes
`in/T751_CENSUS.json`: handles, layers, levels and lengths only); application `t751_alsenan.py` (`--check` rebuilds
from the committed, sha-pinned inputs) -> `out/T751_EDGE_BOUNDS.{json,md}`; tests `tests/t751_edge_bounds` (40).
Drawing read this run: Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55, the
SOUTH EAST and NORTH WEST elevation frames, datum blocks 2439 / 2A42 checked on 244A / 244C / 2886 / 2888) and
p7757_arch_sheet09.pdf (NE elevation, raster: read for topology only, nothing scaled). ERS read: s.2.1, 2.4, 3, 7.

## 1. Physical element and method

One external arris counted once in lm (OWNER RULE PAINT 2026-11-12; OD-V3-4). A vertical corner runs from its datum to
the top of the corner as drawn on the corner's own outline in the elevation that sees both faces (R-T751-1); a drawn
end round stops the vertical arris at its tangent point (the round belongs to the top-edge run); a higher element drawn
on the beyond layer behind the corner never raises it. Arched opening edge = 2 x (springing - sill) + the developed
head measured along the drawn head chain (R-T751-2). A drawn piece belongs to the face drawn in its own plane
(R-T751-3). A closure must lie inside the bound it closes, with handles (R-T751-4).

## 2. Results (before -> after)

| item | before | after | evidence (handles) | state |
|---|---|---|---|---|
| 1F parapet-end corners above +9.70 (8) | 0 .. 11.900 lm | **9.185812** | NW: 27B6 + round 2584..2579 (NW-5/NE-2 0.90), 2783 / 2792 / 27B0 / top 27CB (5 x 1.30); SE: 1BFD (NE-2/SE-1 1.60), 2228 + round 1C46..1C3B (SE-1/SW-2 0.185812) | DRAWING-CONFIRMED (CAD) |
| GF pool-court plinth corners (3) | 2.10 .. 2.55 lm | **2.550** | 285E / 283E +0.15 .. +1.00 (arc ends on the court, rim lines 2861 / 285C start inside); NW-6 plinth T-159 | DRAWING-CONFIRMED |
| GF passage-mouth stop-end | 0 .. 1.20 lm | 0 .. 1.20 | free vs abutting end on no vector view | HELD |
| exterior corners total (hosted) | 168.500 .. 182.050 | **178.135812 .. 179.335812** | + NO_HOST 1.40 DC arris -> 179.536 .. 180.736 physical | bounded |
| window outside edges | 103.6831 (T-405 4 dp) | **103.682251** | head chains W15 274C..274B, W16 299F..299E (2.524024 each), W26 1C67..222E (1.970563) | DRAWING-CONFIRMED |
| exterior door edges | 0 .. 12.20 | 0 .. 12.20 | head depth drawn nowhere (D-GF-07 beyond, layer 5) | HELD |
| SE surround vs GF/SE-2 paint | deduction 0 .. 1.298383 | **0** (attribution) | stones layer 1 (front, porch mouth), door 1C00 / landing 1BFE layer 5 (beyond) | ENGINE_WRONG (T-747) |
| 1F NW-5 pier returns, parapet m2 | 0.053652 .. 0.697479 | **0.697479** | pier top 27CA +11.00 over 1.005222 = T-567 span; 25B3 / 270A / 2728 / 2783 | DRAWING-CONFIRMED |
| 1F slab edge (6 faces) | blank | blank | edge depth not on the architectural sheets | HELD |

Paint (valued faces, T-747 total basis): 1,007.168044 .. 1,087.619176 -> **1,009.110254 .. 1,087.619176 m2**
(render low end +0.643827 = the pier; paint low end +1.942210 = pier + surround attribution); render - paint 0 at both
ends. Lines moved: GF storey L-b05f70c9 paint low 375.618266 -> 376.694149; PLINTH GF 71.466090 -> 71.688590;
PARAPET-OUTER 1F low 54.007480 -> 54.651307 (render too).

## 3. Reconciliations (residual 0)

- Windows: T-746 106.020 - 103.682251 = 2.337749 = rectangles to the crown band (7.75 / 7.75 / 4.60) - developed
  (6.845844 / 6.845844 / 4.070563); DXF vs the merged T-405 ledger -0.000256 / -0.000256 / -0.000337 (its 4 dp).
- Surround: T-360 r2 visible 1.514884 (re-run this session, = 1.5149) - T-747 zone 1.298383 = 0.216501 = right of
  T-747's stated span edge 0.162824 (the crown / keystone outer ring 0.134936, inner 1CC6..23AD, + band / cut strip
  0.027888) + pen rings and joints inside the span that T-747's snap dropped 0.053677. Split at +1.00: 0.2225 below
  (agrees with T-747) / 1.292383 above.
- Corners: 182.050 - 168.500 = 13.55 of bounds -> 1.20 (stop-end only): narrowed 12.35 lm.

## 4. Findings and verdict proposals

- F-T751-1 PRINTED_ABOVE_CAP: T-172 capped NE-2/SE-1 at 1.30; the SE frame (1BFD) and the printed SE-1 NE end
  (+11.30, T-159) give 1.60; the row bound holds.
- F-T751-2 DRAWING_FINDING: the 1F NE-2 parapet top is +10.80 (rounded) at its NW end and +11.30 at its SE end, not
  one +11.00 level: the NE-2 outer face 25.051 m2 ('130' on sheet 09) needs a Checker re-read; nothing moved here; the
  step arris on the NE face HELD blank by name.
- F-T751-3 ENGINE_WRONG (T-747 surround attribution): the surround is the porch-mouth arch piece (T-360 C-1, open side,
  no face key, HELD blank: material unprinted, hidden half UNKNOWN); SE-2 paint = render.
- F-T751-4 ENGINE_RIGHT (developed arched heads) vs T-746 rectangles (-2.338 lm).
- F-T751-5 HELD by name: the pier's back above the +9.80 wave-wall top is drawn nowhere (arrises not counted).
- Engine vs freelancer: his Sigma 1,469.9675 m2 vs paint 1,008.575 .. 1,085.613 (T-747 basis without the valued
  slab-edge part): -31.39 % .. -26.15 % (RULE_DIFFERENCE / ENGINE_RIGHT causes as T-567 / T-747). His corners
  1,297.35 m.l vs 178.14 .. 179.34 vertical + 103.68 openings + 0 .. 12.2 doors (+ T-337 horizontals): RULE_DIFFERENCE.

## 5. Checker re-measure suggestions

NW-5/NE-2 (27B6 to +10.60, round 2584..2579 r 0.20 to +10.80: 0.90 lm) and NE-2/SE-1 (1BFD +4.30 .. +11.30: 1.60
lm above +9.70); the keystone by handle (inner 1CC6/1CC7/1CC8/23AC/23AD, outer 1CC3/2230/222F/1CAB/1CC2, x beyond
T-747's span edge; 0.134936 m2 visible to the cut 2416) and its plane (layer 1 vs door 1C00 layer 5).

## 6. Lessons register row (proposed, ERS s.7)

2026-11-12 | T-751 | exterior corner / zone bounds | a corner height capped by another face's printed level, a stone
zone deducted from a face drawn behind it, and a span edge set one block short of the keystone | read each corner's
own outline line in the elevation that sees both faces (end rounds stop at the tangent point; beyond-layer elements
never raise it); attribute a drawn piece by its drawing layer / plane, not by its x-range; reconcile a zone against the
merged per-block ledger before deducting it | tests/t751_edge_bounds.

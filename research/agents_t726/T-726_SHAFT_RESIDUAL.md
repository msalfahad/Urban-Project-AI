# T-726 plaster shaft residual 13.50 m2 reconciled against the T-719 void register (lane A, research, unwired)

Worker 2, 2026-11-12. Candidate of record ARCH_TAKEOFF_V3.0.72 (T-703 line index). A RECONCILIATION with an own drawing
read, not a verification; nothing wired or released; V2.9 + route G unchanged; no engine, rule / knowledge version,
registry or candidate file touched. Files: `t726_extract.py` (own DXF read by handle -> `T726_DRAWN.json`: lengths,
level figures, frame / scope classes only), `t726_rules.py` (R-T726-1 .. -3, every villa), `t726_alsenan.py` (builder,
inputs sha256-pinned, `--check`), `out/T726_SHAFT_RESIDUAL.{json,md}`, `tests/t726_shaft_residual` (18 tests). Drawing
read this run: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (P7757.dxf sha ab54dd55, the same file T-719
read), decoded by the wrapper into `.work/private` only; the GF / 1F / 2F plans and the NW / SE elevations (vector).

## Physical element (ERS 2.1)

The STAIR-HOUSE: the ST-01 dog-leg shaft box (inner 2.50 wide; 5.00 deep at GF to the south wall face, 6.45 deep on
1F / 2F to the arrival wall across the landing), its four wall planes, each ONE face from its lowest floor to the roof
soffit (Q-72) where no slab crosses, and the lift shaft V-03 beside it (inner 1.80 x 1.80 on every plan; its stair-side
wall is the shaft's E face). An edge with no wall (the 2F landing slab edge 138B, the open south side above +5.50) is
not a face and carries no plaster. The ST-02 well (V-01) runs 4.00 / 7.02 belong to the double-height zone (T-709).

## Findings

1. **The 13.50 row is not an element of its own (R-T726-1).** In his plaster statement the 2.50 x 5.40 row is
   labelled as the continuation of the row above it (his stair-house walls 14.80 x 12.90 = 190.92); his group subtotal
   J = 190.92 + 13.50 = 204.42 (paint statement: the same pair, J 204.42). So it is part of his STAIR-HOUSE element and
   is reconciled inside the T-173 stair-house bridge, which now closes exactly: 204.42 - 177.07 = +27.35 = south side
   +20.11 + north -2.64 + west / east -3.62 + this row +13.50.
2. **No drawn face of the element is 2.50 x 5.40 (R-T726-2: NO_FACE).** Width 2.50 +- 0.10 matches four faces, by
   handle: ST-01 N (26E / ADE / 127E, one face 12.74 .. 13.44 high), ST-01 S at GF only (220, +1.00 .. +5.34 - b =
   4.24 .. 4.34), the 1F arrival wall (AEA / AEB, 3.99 .. 4.04, in 1F-13) and the 2F arrival wall (1282 / 1283,
   3.79 .. 4.04, in 2F-01); nearest height gap 1.06 m (GF S). No printed-level interval inside the stair-house (plan
   marks 4AC +0.30, 413 +1.00, D18 +5.50, 134E +9.70 + the section A-A marks) is 5.40 +- 0.054. The only 5.40 intervals
   on the drawing use a level OUTSIDE it: +0.15 (exterior grade, six GF marks and both elevations) to +5.50, and +4.30
   (the single-storey annex roof: D20 beside the 'ROOF' block B8D on the 1F plan, 244B on the SE elevation) to +9.70:
   exterior faces, his external statement / T-314, never bound to an internal line. The lift shaft (1.80 inner, 2.20
   outer by 21C .. 222) and the ST-02 runs (4.00 / 7.02) fail on width.
3. **Every face of the element is carried once on the engine side (R-T726-3).** 1F: chain 1F-LIV.ours 52.44 lm walks
   the shaft's E (B16) 5.20 + N (ADE) 2.50 + W u 0 .. 5.20 5.20 + pier returns 0.10 = 13.00; 52.44 - 13.00 = 39.44 vs
   the 1F-13 face 39.45 (+0.010 lm, ONCE). 2F: chain 2F-CORR.ours 12.90 walks W / E over the 2F landing (u 4.50 ..
   5.20, slab edge 138B at u 4.50) 0.70 + 0.70 and the open slab edge 2.50 (no wall, no plaster); 12.90 - 3.90 = 9.00
   vs the 2F-01 face 9.009 (+0.009, ONCE). GF: the stair-hall lines GF-R31F8AE are EXCLUDED; ST_GF alone carries the
   band. So the residual is NOT a face missing from the engine and NOT a double height counted once; the lift-shaft
   inside (no line in either statement) stays HELD by specification (T-719), not a cause of this row.

**Result: 13.50 = his continued stair-house row on no drawn face: named residual on the freelancer side (UNRESOLVED as
to his intent), engine change 0 m2, never added, never 0 on the engine side.** Like for like plaster (T-701) engine
984.250 .. 1,053.666 vs his 1,169.125: -15.81 .. -9.88 %; with this row named apart (1,155.625): **-14.83 .. -8.82 %**.
Paint row 25 the same 13.50, same result.

## Verdict proposals (Checker)

- 13.50 (his PLS row 24 / PNT row 25): NO_FACE inside the stair-house; ENGINE_RIGHT on scope (all faces carried once,
  by handle); residual UNRESOLVED (his row, no drawn face; the two drawn 5.40 intervals are exterior).
- Shaft lines ST_GF / ST_1F / ST_2F (L-95f2c45c / L-0eac839f / L-418121a4, paint L-145bd239 / L-2ab93d50 / L-5a7a5c6f)
  and the room lines 1F-13 / 2F-01: ONCE (residuals 0.010 / 0.009 lm, inside 0.10).

## Rule, test, lessons row

R-T726-1 group of a reference row (a continuation row is reconciled inside its element); R-T726-2 face binding by width
and height with printed levels in scope only (out-of-scope intervals reported, never bound); R-T726-3 once across lines
(chain - room face = shaft faces walked + open edges). Tests: villa K726 by hand (shaft 2.40 x 4.80, roof soffit +10.60:
BOUND full height, part interval BOUND / AMBIGUOUS, NO_FACE, out-of-scope level, tolerances in m and mm, held height,
shaft face in both lines COUNTED_TWICE, open edge plastered COUNTED_TWICE, DROPPED, bad inputs, order / mirror) +
development-villa `--check` and pins.
Lessons row (ERS s.7, proposed): 2026-11-12 | a 13.50 m2 'shaft' row sat UNRESOLVED for four rounds as if it were its own
element | it was the continuation of the row above (his group subtotal adds both), and no candidate search covered the
printed levels outside the element (+0.15 grade, +4.30 annex roof) that alone give its 5.40 height | read a reference
row with its group (subtotal) before binding it; search faces by width and height together, levels inside the element
only, and report out-of-scope matches instead of binding them (every villa) | tests/t726 | PROPOSED.

## For the Checker (re-measure one face)

ST-01 N face, 1F plan: ADE (-1.200 .. +0.200 from the W face line AF1) + W25 gap 1.000 (CEB / CEA jambs) + ADD 0.100 =
2.500 = AF1 .. B16 (x 1.300); box depth N (ADE) to the arrival wall AEB 6.450; GF: 298 .. 21C 2.500, 26E .. 220 5.000,
220 .. 20F 0.200. Missing / held: his intent for the row (no face); the lift-shaft lining specification; roof datum D-39.

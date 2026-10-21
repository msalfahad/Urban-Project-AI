# T-116 Stair voids and stair footprint inside a room face (new piece STAIR_FLOOR_RESIDUE_V1; Alsenan check)

Worker 3, 2026-10-20. New opt-in piece `engine/source/stair_floor_residue.py` (not wired: no method version reads it;
arch_floor.py, arch_measure.py and every frozen file untouched). Alsenan input: one ARCH_TAKEOFF_V2.9 run of Drive
"Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (DXF sha256 ab54dd55...), kept in the session scratchpad.
Run: `alsenan_stair_floor_residue.py` (areas only, no CAD coordinates in the outputs).

## Result: first-floor living porcelain (m2)

| | Released engine line | New piece | Hand (T-113, printed) | Freelancer |
|---|---|---|---|---|
| Floor finish | 44.869 RELEASED | **38.459 .. 38.979 HELD range** (two held pieces) | 38.588 .. 38.990 | 38.96 (one row) |
| vs freelancer | +5.909 (+15.2 %) | -0.501 .. +0.019 (-1.3 % .. +0.0 %) | -0.372 .. +0.030 | - |

The freelancer's 38.96 m2 lies inside the new range. The released line is over by 5.89 .. 6.41 m2 (+15.1 .. +16.7 %).

## Where every m2 of the face goes (face 75.983 m2; conservation BALANCED, ledger 44.573 = geometry 44.573)

| Piece | New piece | Hand (T-113) | Note |
|---|---|---|---|
| Void (outlined, open to below) | 16.005 | 16.005 | = |
| Treads, exact union (own 8.691 + plan below seen 6.714) | 15.405 | 15.405 | engine V2.9 deducts 15.109: 0.296 short (non-convex winder quads clipped, two flights' overlap 0.057 deducted twice); the union fixes both |
| Opening residue + round-stair quarter landing and arrival edge | 2.035 VOID_RESIDUE + 1.418 STAIR_FOOTPRINT = 3.453 (*) | 2.101 + 1.353 = 3.454 | split differs by one 1.15 x 0.05 strip; total -0.001 |
| Dog-leg well: turning landing, gap between flights, winder corner | 2.142 STAIR_FOOTPRINT | 2.1315 | +0.010: the CAD closes the well gap at its foot 0.05 beyond the printed 195 landing (0.20 x 0.05) |
| Foot of the east main-stair flight 1.15 x 0.35 | 0.4025 HELD (STAIR_FOOT_UNSETTLED) | 0.4025 range (designer D-13) | = |
| Closed 0.05 x 2.35 element beside the arriving round-stair flight, outside its 1.15 width | 0.1175 HELD (SIDE_ELEMENT_UNSETTLED) | counted as living floor (printed living 480 includes it) | NEW finding -> designer D-23 |
| Floor (low .. high) | 38.459 .. 38.979 | 38.588 .. 38.990 | with D-23 = floor: 38.576 .. 38.979 (hand -0.012 both: the 0.010 above + rounding) |

(*) includes 7 slivers 0.001 - 0.002 m2 along the curved flight (0.008 m2), classed STAIR_FOOTPRINT.

## Every other Alsenan floor-finish line (24 faces)

23 identical to the released line to 0.000001 m2 (no stair, no void: the piece keeps the face's own area). The GF
open-plan face (4 round-stair flights at their foot, lowest storey) is NOT_ASSESSED: only the exact tread union is
applied, +0.0001 m2; its cells around the rising stair are listed, not deducted (floor under / beside a rising stair is
not settled by the plan). Stair rooms (GF / 2F, kind STAIR) carry no floor-finish line and are unchanged.

## How the piece decides (general, no project names, layers or sizes)

1. Treads: union of every flight's tread quads, exact intersection with the face; flights of the plan below seen
   through the opening are deducted here (no floor at this level) and counted once.
2. Void: exact face inside the outlined void windows.
3. Only where the stair passes through this slab (an outlined void, or a flight that continues a stair of the plan
   below: drawn_on_plan_below / stacked_over), the face is cut by the stair's own linework (segments and arcs on the
   layers the flights were read from, void outline, tread quads, face boundary; lines extended 2 mm so rotation noise
   cannot leave a cell open). Cells reached from a tread or the void and not floor (the largest free cell and any cell
   holding a door point) are VOID_RESIDUE if they touch the void, else STAIR_FOOTPRINT (stair line, UP-STAIR-005).
4. HELD instead of a number: a flight whose last tread line stops short of the parallel flight's end with the strip open
   to the floor (foot of the flight or floor?), and a closed element beside one flight, outside its width and open to
   the floor (balustrade / upstand / stringer: does the floor finish run under it?). Range low = not floor, high = floor.
5. A flight with no tread outline or a void with no outline: the face's floor is HELD (net None), never 0.

## Verdict proposals for the verifier

- Released 1F living porcelain 44.869 vs hand 38.588 .. 38.990: HAND_RIGHT (T-113, unchanged).
- New piece 38.459 .. 38.979 vs hand: ENGINE_RIGHT on every deducted piece (each = a T-113 hand piece to 0.01 m2);
  the 0.1175 m2 balustrade strip is UNRESOLVED (designer D-23: the hand used the printed 480, the CAD draws a closed
  element there; the plan does not say what it is). The 0.0102 m2 well-gap foot: RULE_DIFFERENCE between the CAD
  closing line and the printed 195 landing (not material; noted).
- Freelancer 38.96: inside the range; his row is not split, so which pieces he took cannot be traced.

## Fixtures (not Alsenan; hand-calculated in the test docstring)

Upper-floor hall 8 x 5 with a dog-leg (two 1.00 m flights, 0.20 well, a two-quad winder with one NON-CONVEX quad, a
1.20 x 1.00 turning landing, east flight 0.30 short): treads 4.70, stair footprint 1.60, HELD 0.30, floor 33.40 .. 33.70.
Upper-floor room 10 x 8 with a 4.05 x 6.05 opening holding a 4 x 3 void and a flight of the plan below, plus an arriving
flight with a 0.05 balustrade: void 12.00, treads below 4.50, opening residue 10.0025, HELD 0.10, floor 53.3975 ..
53.4975. Each in metres, mirrored, rotated 30 deg and in mm (rotated and mirrored). Lowest storey (no marks): treads only,
cells listed. Missing tread outline and missing void outline: HELD, net None. A door point keeps a closed cell as floor.
The legacy arch_floor._treads is shown wrong on the non-convex winder (> 0.05 m2) and two drawn-over flights are counted
once (quad sum 5.70, counted 4.70).

## What is missing

- Not wired: the released Alsenan line stays 44.869 until a method version (next free ARCH_TAKEOFF version) reads this
  piece; that version also needs owner Q-66 for the finish of the 4.875 m2 arrival landing (geometry unaffected here:
  it stays in the floor rows, owner Q-56 A).
- Landing vs well inside STAIR_FOOTPRINT is not split here (the stair ledger, T-111, owns the stair marble).
- D-13 (0.4025) and D-23 (0.1175) for the designer.

Gate 1 (no released floor over-measured, no room lost). Rules: UP-STAIR-002, UP-STAIR-005, UP-QTY-STATUS-001,
arch_floor FLOOR AREA RECONCILIATION, owner Q-56 A.

# T-113 First-floor living and circulation: where the engine's extra floor comes from (Alsenan, owner Q-56 A)

Worker 2, 2026-10-20. Read-only: one ARCH_TAKEOFF_V2.9 run of Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip
(sha256 of the DXF in the run: ab54dd55...), the first-floor plan p7757_arch_sheet04.pdf read at 200 dpi, and the 1F
dimension entities of the DXF. Nothing released changes. Inputs stayed in the session scratchpad.

## Result (porcelain floor, m2)

| Space (owner Q-56 A, own rows) | Engine V2.9 (inside the region) | Hand, printed dimensions | Engine - hand | Freelancer |
|---|---|---|---|---|
| Living 480 x 520 less the arriving round-stair flight 1.15 x 2.40 | 23.550 | 22.200 | +1.350 (+6.1 %) | not split |
| Corridor by the void 587 x 120 | 7.044 | 7.044 | 0.000 | not split |
| Main-stair landing (120 + 10 + 120) x 195 | 4.875 | 4.875 | 0.000 | not split |
| Connector by the lift 130 x 125 + 237 x 120 | 4.469 | **4.469** (was 4.80 in T-091) | 0.000 | not split |
| Stair opening 587 x 400 (void + round stair), outside the void and treads | 2.101 | 0 (not floor) | +2.101 | - |
| Dog-leg stair well 250 x 450, outside the treads | 2.534 | 0 (not floor) | +2.534 | - |
| Engine tread clipping (winder) | +0.296 | - | +0.296 | - |
| **Total** | **44.869** (released line) | **38.588** | **+6.281 (+16.3 %)** | **38.96** (one row; +0.372 m2, +1.0 % over hand) |

With S3 counted as landing (below), the hand landing is 5.278 m2 and the hand total 38.990 m2: then engine 44.869 is
+5.879 m2 (+15.1 %) and the freelancer's 38.96 m2 is -0.030 m2 (-0.1 %) from the hand pieces.

The 5.95 m2 of the board row was measured against T-091's 38.915 m2; that sum read the connector from CAD end points
as 4.796 m2. The printed chains give 4.469 m2 (1.30 x 1.25 + 2.37 x 1.20, see below) and the engine geometry agrees to
0.001 m2, so the gap is 6.281 m2 and it is explained in full: 6.2814 = 1.350 + 2.101 + 2.534 + 0.296 (rounding 0.0001).

## The pieces (local metres from the face's south-west corner; `LIVING_1F_TRACE.csv`)

Engine floor 44.869 = face 75.983 - void 16.005 - treads 8.337 (own) - 6.772 (seen through). Exactly, with every tread
polygon intersected once: 75.983 - 16.005 - 15.405 = 44.573. The 0.296 m2 between the two is an engine defect (E1).

| # | Piece | m2 | Why it is not floor (evidence) | Status |
|---|---|---|---|---|
| E1 | Winder of the dog-leg (flight F5): two of its four tread quads are slightly non-convex (0.0027 / 0.0021 m2 off their hulls); `arch_floor._treads` clips each quad with `region_area_in_convex`, which gets 0.1545 instead of 0.3490 and 0.2078 instead of 0.3671 m2; the winder's last quad also overlaps the first tread of flight F2 by 0.0574 m2, which is deducted twice | +0.354 - 0.057 = **+0.296** | tread polygons from the same run, shapely intersection | ENGINE DEFECT (proven) |
| S1 | Square at the top of the dog-leg, east of the winder, 1.15 x 1.15 (x 1.35-2.50, y 10.45-11.60) | 1.3225 | inside the stair well: printed 645 = 120 (winder) + 330 (flight) + 195 (landing); the only floor printed at +5.50 is the 195 landing | stair (turning landing), not 1F floor |
| S2 | Gap between the two flights, 0.20 x 3.35 (printed "10", drawn 0.20) | 0.670 | between the flights of the stair well (printed 120 + 10 + 120) | stair well, not floor |
| S3 | Foot of the east flight, 1.15 x 0.35 (y 7.10-7.45): from its last drawn tread line to the printed landing edge | 0.4025 | north of the printed 195 landing (printed on the west side only). The dog-leg is stacked: the east flight ends at the same line on 1F (F3) and on 2F (where it arrives at the printed 2F lobby), so on 1F the east flight, whichever storey's flight is drawn, meets the +5.50 floor at that line; 0.35 is not a 0.30 going | **landing floor at +5.50, CAD-DERIVED** (proposal; the printed landing depth on the east side would confirm it): it belongs to the landing row, which becomes 5.278 m2 |
| S4 | Winder corner left between the winder quads and the walls | 0.139 | inside the 120 winder zone | stair, not floor |
| O1 | Band between the X-marked void and the south wall, outside the round-stair treads (corner outside the curved flight, gaps between the flights) | 1.670 | inside the printed stair opening 587 x 400 (two "400" dimensions from the corridor edge to the south wall) | not floor |
| O2 | Strip between the printed corridor edge (120) and the X-marked void, 5.87 x 0.05 | 0.291 | the printed 400 opening starts at the corridor edge, the X rectangle 0.05 further in (balustrade line) | not floor |
| O3 | Sliver between the void and the living line, 0.05 x 2.75 | 0.136 | inside the printed 587 opening | not floor |
| L1 | Quarter landing of the round stair inside the living rectangle, 1.15 x 1.15 less a 0.0275 column notch | 1.295 | part of the arriving stair box 1.15 x 2.40 printed in the living (T-091; arrow on the arriving flight on sheet 04) | stair landing, not living floor |
| L2 | Arrival edge strip of the same stair box, 1.15 x 0.05 | 0.0575 | the stair box is 2.40 long, the drawn treads and landing 2.35 | stair, not floor |
| | Living rest | 22.1975 | hand 22.20 (24.96 - 2.76); -0.0025 = notch rounding | AGREES |

Corridor, landing and connector agree with the printed sizes to 0.001 m2: their geometry in the engine face is right.
The extra comes only from stair and opening residue (6.0 m2) and the winder clipping (0.3 m2). It is not an overlapping
polygon, not a double-counted circulation, not the lift (its 1.80 x 1.80 shaft and the 0.20 walls are outside the face),
not the passage to the middle bedroom (the 1.47 x 3.05 piece named in Q-56 is outside this face) and not a classification
error.

## Connector from the printed chains (corrects T-091)

West part 1.30 x 1.25: from the landing's east edge to the corridor start = 365 + 15 - 250 (the chain 365 / 15 along
the south wall and the landing width 250 both start at the stair's west wall face), depth 125 printed. East part 2.37 x 1.20: the 20 + 347 chain of the
laundry / W.C. less the 130 west part, depth 240 - 120 printed. 1.625 + 2.844 = 4.469 m2. T-091's 1.15 x 1.25 + 0.85 x
1.20 + 1.67 x 1.40 = 4.796 m2 took a 1.40 depth that no dimension prints. The printed-only hand total is therefore 38.588 m2, not
38.915 (38.990 m2 with S3 as landing); the freelancer's single 38.96 m2 row is -0.030 m2 from the latter and +0.372 m2
from the former; his row is not split, so which pieces he took cannot be traced from his workbook.

## Verdict proposals for the verifier

- Living 1F (engine 23.55 vs hand 22.20 m2): HAND_RIGHT; the engine counts the round stair's quarter landing (1.30 m2) and
  its 0.06 m2 edge as living floor.
- Corridor 7.044, landing 4.875, connector 4.469: ENGINE geometry = HAND (0.000 m2).
- Whole released line 44.869 vs hand 38.588 m2 printed-only (+6.281, +16.3 %) or 38.990 m2 with S3 as landing (+5.879,
  +15.1 %): HAND_RIGHT; a RELEASED quantity is over-measured, which is the gate-1 kind of error.
- Freelancer 38.96 vs hand: -0.030 m2 (-0.1 %) with S3 as landing (AGREE on the total; his row is not split), +0.372 m2
  (+1.0 %) without it.

## Proposed fix task (engine defect, general, every villa)

ENGINE: 44.869 m2 released; HAND: 38.588 m2; CAUSES: (1) `engine/source/arch_floor.py:51` `_treads` clips each tread
quad with `region_area_in_convex`, wrong on a non-convex winder quad (Alsenan -0.354 m2) and counts overlapping quads of
two flights twice (+0.057 m2): use a polygon union of the flight treads and an exact intersection; (2) a room face that
holds a stair well or a stair opening without a wall around it releases the residue between the treads, the flights and
the void as room floor (Alsenan 1F: 2.534 + 2.101 + 1.353 m2): the floor line of such a face should deduct the stair
footprint (flights + the landings and gaps between them, from the stair's drawn outline) and the whole opening where a
dimension or outline gives it, or HOLD the residue as a stair / opening candidate instead of releasing it as floor. A new
method version (frozen V2.9 untouched), with a synthetic fixture: a dog-leg with a winder inside an open hall, a round
stair under a void, mirrored and rotated.

## Every other Alsenan room checked for the same causes

All 38 V2.9 faces were run through the same check (non-convex tread quads, overlapping flights, a void, a stair inside
a room face):
- Non-convex tread quads, overlapping flights, voids: only the 1F living face (0 other faces).
- Stair flights inside a face: GF stair room (STAIR, no floor-finish line), 2F stair room (STAIR, no floor-finish line; its
  printed lobby 4.50 x 1.95 is a separate row in T-086) and the GF open-plan face (MIXED, 4 flights of the round stair
  at their foot; its porcelain line 118.73 m2 is PROVISIONAL, not released). On GF the floor under a rising stair is real
  floor, so the residue there is a different reading (under-stair floor finish), not this defect; it stays with the held
  open-plan row.
- Released dry rooms whose engine area differs from a printed size by more than 0.10 m2 (T-086 table): the 1F master
  420 x 400 with passage (19.02 vs his 19.46 m2, curved glazing edge not dimensioned) and the 1F master 380 x 430 (16.34 =
  printed, his 17.29 holds the passage): neither has a stair, a void or a tread inside; not this cause.

## What is missing

- S3 (0.4025 m2): landing floor by the stacked-stair geometry (CAD-derived, not printed); the stair ledger (T-111) or the
  main-stair section can confirm it.
- Whether the corner outside the round stair's curved flight (part of O1) carries a slab at +5.50 is not printed; it is
  not reachable floor either way (inside the printed 587 x 400 opening), so it does not change the floor finish.
- Finish of every piece stays PROVISIONAL porcelain (owner Q-56 A; no sheet prints a finish); the landing may move to
  marble without changing its geometry.

Files: `alsenan_living_1f_trace.py` (run), `LIVING_1F_TRACE.csv` (regions and pieces, local metres),
`living_1f_trace_summary.json`. Gate 1 (no released floor over-measured). Rules: owner Q-56 A, UP-STAIR-005,
UP-QTY-STATUS-001, directive 2026-10-20 Part 4 (2) and (5).

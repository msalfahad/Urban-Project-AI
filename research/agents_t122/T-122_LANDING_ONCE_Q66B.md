# T-122 First-floor living group under owner Q-66 B: the main-stair landing in marble, once (Alsenan)

Worker 2, 2026-10-20. Read-only, NO REPO CODE (research files only; nothing released changes). Inputs, kept in the session
scratchpad: Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip (DXF sha256 ab54dd55..., one ARCH_TAKEOFF_V2.9 run)
and p7757_arch_sheet04.pdf (first floor plan, read at 200 and 600 dpi). The merged piece STAIR_FLOOR_RESIDUE_V1 was run
unchanged (an in-memory copy keeps its polygons; the engine file is not edited). Run:
`alsenan_landing_once.py --v29 <pickle> --out <dir>`; rows with polygons (local metres from the face's south-west corner)
in `LIVING_1F_ROWS_Q66B.csv`, totals in `living_1f_q66b_summary.json`.

## Result (m2; first-floor open living face, 75.983 m2)

| Row (owner Q-56 A / Q-66 B) | Finish | Owner manual (printed sizes) | Drawing-derived (CAD polygon) | Difference and why |
|---|---|---|---|---|
| Living 480 x 520 less the round-stair box 115 x 240 | porcelain, PROVISIONAL | 22.200 | 22.080 .. 22.1975 | low: the 0.05 x 2.35 closed strip beside the round-stair flight HELD (designer D-23); high = 22.1975 (0.0025 column notch at the round-stair quarter landing) |
| Corridor by the void 587 x 120 | porcelain, PROVISIONAL | 7.044 | 7.044 | 0 |
| Connector by the lift 130 x 125 + 237 x 120 | porcelain, PROVISIONAL | 4.469 | 4.469 | 0 |
| **Porcelain total** | | **33.713** | **33.594 .. 33.711** (HELD range, never one released figure) | -0.119 .. -0.002 |
| **Main-stair arrival landing (120 + 10 + 120) x 195 at +5.50** | **marble, own element** (Q-66 B) | **4.875** | **4.865** | -0.010: the CAD closes the well between the flights 0.05 inside the printed 195 edge (balustrade end 0.20 x 0.05; the PDF draws the same end) |
| Foot of the east flight 1.15 x 0.35 (D-13) | marble in every reading, never porcelain | - | 0.4025 HELD | see "D-13" below |

Freelancer: one "living" row 38.96 m2 that holds the landing (not split, so his pieces cannot be traced). With the landing
moved to marble as Q-66 B rules, his row would leave 38.96 - 4.875 = 34.085 m2 of porcelain (33.682 if his row also holds
the D-13 strip). Engine candidate 33.594 .. 33.711 vs 34.085: -0.491 .. -0.374 m2 (-1.4 % .. -1.1 %); vs 33.682:
-0.088 .. +0.029 m2 (-0.3 % .. +0.1 %). The landing itself is RULE_DIFFERENCE (owner Q-66 B: marble; freelancer: porcelain
in the living row). Released Alsenan line unchanged: 44.869 m2 (STAIR_FLOOR_RESIDUE_V1 is not wired).

## Two corrections to the candidate figures of the owner's 17:54 note (4)

1. **Porcelain low 33.584 -> 33.594 m2 (+0.010).** The range 38.459 .. 38.979 holds the landing as 4.865 m2, not 4.875:
   the piece already deducts the 0.20 x 0.05 well-end cell that lies inside the printed landing (row R-LC). Subtracting the
   full 4.875 takes those 0.010 m2 off twice. Measured: landing rectangle 4.875 = floor 4.865 + well-end cell 0.0101, and
   nothing else of the rectangle is void, tread, residue or held (summary keys `landing_rect_*`).
2. **Porcelain high 34.104 -> 33.711 m2.** The high end adds both held pieces as porcelain. Under Q-66 B the D-13 strip
   cannot be porcelain: it lies between the printed landing edge and the east flight inside the 2.50 m stair width, so it is
   either landing (marble, Q-66 B) or the top of the flight (marble, UP-STAIR-005). Only the D-23 strip (0.1175) can still be
   porcelain (living floor if the finish runs under it). Porcelain = 33.594 (D-23 not floor) .. 33.711 (D-23 floor).

Both stay within the owner's rule "never release a range as one verified quantity": porcelain is a HELD range with the
D-23 piece named; the landing is MEASURED (geometry) with the finish set by Q-66 B.

## Every m2 in exactly one category (the owner's once-only condition)

Face 75.983 = sum of the 22 rows 75.9827 (rounding of the rows to 4 decimals; geometric union of the rows vs the face
0.000024 m2, pairwise overlap of the row geometries 0.000006 m2, face left in no row 0.000011 m2).

| Category | m2 | Rows (CSV) | Line it belongs to |
|---|---|---|---|
| Porcelain | 33.5933 | P-LV 22.080, P-CO 7.044, P-CN 4.469, P-XX 0.0003 (floor slivers along the curved flight) | first-floor floor tiles |
| Marble landing | 4.8650 | P-LD | stair marble, new element (1F arrival landing) |
| Held | 0.5200 | H-D13 0.4025 (marble in every reading), H-D23 0.1175 (porcelain or none) | none until the designer answers |
| Void | 16.0050 | V-01 | none (open to below) |
| Treads | 15.4047 | T-F1 1.982, T-F4 3.352, T-F6 1.380 (flights of the plan below, seen through the opening); T-F2 3.770, T-F3 3.450, T-F5 1.471 (own) | stair marble flight lines (counted by risers, not by these polygons) |
| Opening residue | 2.0347 | R-VR | none (inside the printed 587 x 400 opening) |
| Stair footprint | 3.5600 | R-LC 0.010, R-NB 1.404 (turn of the dog-leg: square + winder corner), R-GP 0.670 (gap between flights, drawn 0.20), R-RQ 1.295 (round-stair quarter landing), R-RE 0.0575, R-SF 0.123 | stair (no porcelain): R-NB under the printed half landing 250 x 125 (marble ST-MS2-LD); R-RQ = round-stair corner landing (marble, area HELD: size not printed); R-GP: 2 x 0.05 m under the printed 120 flight widths, the rest of the well has no finish |

Landing polygon (P-LD, local metres): (0, 5.15) - (2.50, 5.15) - (2.50, 7.10) - (1.35, 7.10) - (1.35, 7.05) - (1.15, 7.05) -
(1.15, 7.10) - (0, 7.10). Every other row's polygon is in the CSV.

Stair marble (finish table, 39.49 m2 = 6 flights 34.86 + 2 landings 4.625): its two landings are the GF -> 1F turn landing
120 x 125 at +3.50 and the 1F -> 2F half landing 250 x 125 at about +7.6. **The +5.50 arrival landing is in neither**, and
it is not in the 1F porcelain rows once it moves. Stair marble under Q-66 B: 39.49 + 4.875 = **44.365 m2** with the printed
landing (44.355 with the drawn 4.865; the 0.010 m2 under the balustrade end decides which). Landing counted once: YES.

## Landing area by two methods

- Printed (sheet 04, read again at 600 dpi): "195" from the landing edge to the first tread line of the west flight, the
  width chain "120 / 10 / 120" = 250, level "+5.50" in the landing. 2.50 x 1.95 = **4.875 m2**.
- Drawn (DXF): the 1950 dimension entity runs from the west flight's first tread line (y 7.10) to the wall line at y 5.15;
  the 2500 dimension spans the stair's wall faces (x 0 .. 2.50); the face polygon inside that rectangle is 4.875 m2, of
  which 4.865 m2 is floor and 0.010 m2 the end of the well: a layer-5 line at y 7.05 closes the 0.20 m gap between the
  flights 0.05 m inside the printed edge, and the PDF draws the balustrade rectangle ending just past the landing edge.
- Difference 0.010 m2 (0.2 %): RULE_DIFFERENCE, not material; whether marble runs under a balustrade end is a finishing
  detail no sheet prints.
- Note for the stair ledger: the CAD draws the flights 1.15 m wide with a 0.20 m gap (1.15 + 0.20 + 1.15), the printed
  chain says 1.20 + 0.10 + 1.20. The landing does not change (2.50 both ways); the flight marble uses 1.20.

## D-13 (the 0.4025 m2 foot of the east flight): new evidence, still HELD

- The walk line on the stair layer starts in the landing on the west flight (y 7.04), runs up the west flight, turns, and
  comes down the east lane to an arrowhead at y 7.15, inside the D-13 strip (7.10 .. 7.45). The PDF shows the same arrow.
- Section A-A counts 12 risers on the upper flights (owner Q-46 A: the section count governs); 11 goings x 0.30 = 3.30 m
  from the turn line (y 10.45) end at y 7.15, the arrow tip. The plan draws 10 treads (3.00 m) and leaves the 0.35 strip.
- So by the section count most of the strip (0.30 x 1.15 = 0.345 m2) is a tread of the flight and 0.05 x 1.15 =
  0.0575 m2 is landing; by the plan it is all landing floor (5.278 m2 landing). Either way marble, never porcelain.
- Do not add 0.4025 to the landing yet: the finish table's flight rows count 12 treads for 12 risers (for example
  GF -> 1F upper flight 12 x (0.30 + 0.1667) x 1.20 = 6.72 m2), one tread more than the goings between risers, so the strip
  may already sit in a flight row. Adding it to the landing could count it twice. Owner of the decision: the stair ledger
  (flight by flight, T-111) and designer D-13.

## Consistency finding: the second-floor arrival landing (owner question Q-70)

The stair is stacked. On the second floor the same 2.50 m stair width arrives in front of the printed stair lobby
"450 x 195" (finish table row: 8.775 m2 porcelain, RELEASED in the table). The 2F stair face starts at the same line as the
1F landing's south edge (the 2F frame is the 1F frame shifted, 2F local y 0 = 1F local y 5.15) and its flights start at
y 2.25 / 2.30 (= 1F 7.40 / 7.45), so 2.50 x 1.95 = 4.875 m2 of the printed lobby is the arrival area of the stair, the same
element Q-66 B moved to marble on the first floor. Q-66 B was asked for the first floor only and the 2F area is printed as
a named lobby, so this run does not move it: owner Q-70 asks. Affected only: the 4.875 m2 of the 2F lobby row (porcelain
8.775 -> 3.900, stair marble +4.875 if A).

## Verdict proposals for the verifier

- 1F porcelain under Q-66 B: ENGINE (piece + this partition) 33.594 .. 33.711 vs hand 33.713: ENGINE_RIGHT within the
  named held piece (D-23) and the 0.010 well end; the owner's 33.584 / 34.104 are corrected as above (arithmetic, not a
  rule change).
- Landing 4.875 printed / 4.865 drawn: RULE_DIFFERENCE 0.010 m2 (balustrade end), MEASURED; finish marble by Q-66 B.
- Freelancer living 38.96 (landing inside, porcelain): RULE_DIFFERENCE on the landing finish; porcelain otherwise
  -1.4 % .. +0.1 % depending on whether his row holds the D-13 strip (not traceable).
- Verifier re-measure suggested: the landing rectangle (DXF 1950 / 2500 dimensions) and one residue piece (R-LC, the
  layer-5 line at y 7.05 between x 1.15 and 1.35).

## What is missing

- D-13 and D-23 (designer); the stair ledger (T-111) for whether the D-13 strip is in a flight row.
- Owner Q-70 (2F arrival landing).
- No method version reads STAIR_FLOOR_RESIDUE_V1 or the Q-66 B split: the released line stays 44.869 m2 until one does.

Gate 1 (no floor over-measured, no surface in two lines). Rules: owner Q-56 A, Q-66 B, Q-46 A, UP-STAIR-002,
UP-STAIR-005, arch_floor FLOOR AREA RECONCILIATION, UP-QTY-STATUS-001, owner directive 2026-10-20 Part 2.2 (statuses).

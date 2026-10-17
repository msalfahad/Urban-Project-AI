# The 3.00 x 4.00 m bathroom: floor-to-wall continuity and the buildable material requirement

Room WP-B: inner faces 4.00 x 3.00 m, one 1.00 m door in the south wall (x 1.50 - 2.50) to a dry corridor, wall depth at
the door 0.20 m (the synthetic assumption of the Phase 2B-3 case). Urban values: roll 1.00 x 10.00 m, lap 0.10 m at
every joint (UP-WP-002), upturn 0.20 m (UP-WP-003), doorway continuation lapped 0.10 m onto the floor (UP-WP-DOOR-001).
Every figure below was derived by hand and checked by the independent construction calculator
(`tests/m9_p2b4/construct_reference.py`), which rebuilds each plan piece by piece and checks its coverage on a 10 mm
grid. Diagrams: `diagrams/WPB-*_install.svg`, `diagrams/WPB-*_cutting.svg`, `diagrams/JUNCTION_SECTIONS.svg`.

## 1. How the 0.20 m upturn meets the floor membrane

**What V2.5 assumes.** The floor strips stop at the wall. The upturn is a separate band strip, 0.30 m wide, folded
lengthwise along the junction: 0.20 m up the wall and a 0.10 m flange lapped onto the floor membrane. The engine writes
this as `upturn_to_floor_lap`: 0.10 m over 13.00 m. The 0.10 m is the joint lap of UP-WP-002, applied to a junction
that rule was not written for. V2.5 does not list the junction among its open details; those are the doorway, the
corners and the penetrations (finding F-01).

**The junction is a product detail.** Neither the registry nor the scenario says how this membrane system makes the
floor-to-wall junction. There are two physically different ways to build it. Both are shown, and both are
**CONDITIONAL** until the installation detail is confirmed:

| | A - SEPARATE_UPSTAND | B - CONTINUOUS_FOLD |
|---|---|---|
| How | the floor strips stop at the wall face; a band strip h + j wide is folded at the junction: h up the wall, flange j on the floor sheet | each floor strip runs on 0.20 m up the wall (and lies flat into the doorway); one sheet folded at the junction |
| Junction lap | j onto the floor sheet - a product value (V2.5: 0.10) | none: the sheet is continuous through the junction |
| Extra pieces | band pieces (and their end laps) | none |
| Internal corner | the flange folds on itself: a j x j pleat | an h x h square of excess sheet (0.20 x 0.20): folded into the corner or cut out and patched |
| Doorway | a separate doorway piece; it meets the band ends edge to edge at both jambs | the strip end lies flat into the opening; slit 0.20 m at each jamb |
| Needs from the product | the flange width j; whether a fillet or a reinforcing strip is required at the junction | that the sheet may be folded 90 degrees at the junction and at a corner |

A third family exists: the floor sheet is dressed a little way up the wall and a wall strip laps down over it. Its
quantities depend on two product dimensions and are not calculated here.

## 2. The five floor strips and every upturn piece, as planned by V2.5 (alternative A, j = 0.10) - WPB-A1

| Piece | Size (m) | Cut from | Goes to | Laps |
|---|---|---|---|---|
| S1 | 1.00 x 3.00 | roll 1, 0.00 - 3.00 | floor x 0.00 - 1.00 | - |
| S2 | 1.00 x 3.00 | roll 1, 3.00 - 6.00 | floor x 0.90 - 1.90 | side lap 0.10 x 3.00 over S1 |
| S3 | 1.00 x 3.00 | roll 1, 6.00 - 9.00 | floor x 1.80 - 2.80 | side lap over S2 |
| (stock) | 1.00 x 1.00 | roll 1, 9.00 - 10.00 | untouched | - |
| S4 | 1.00 x 3.00 | roll 2, 0.00 - 3.00 | floor x 2.70 - 3.70 | side lap over S3 |
| C5 | 1.00 x 3.00 | roll 2, 3.00 - 6.00 | ripped lengthwise into S5 0.40 + L1 0.30 + L2 0.30 (no residue) | - |
| S5 | 0.40 x 3.00 | C5 | floor x 3.60 - 4.00 | side lap over S4 |
| L1 | 0.30 x 3.00 | C5 | cross-cut into DW 1.00 + B2 2.00 | - |
| DW | 0.30 x 1.00 | L1 | doorway D1: 0.20 in the opening + 0.10 onto S2 / S3 | 1.00 x 0.10 onto the floor |
| B2 | 0.30 x 2.00 | L1 | band 2.90 - 4.90: east wall y 1.40 - 3.00, NE corner, north wall x 4.00 - 3.60 | end lap over B1 |
| B1 (= L2) | 0.30 x 3.00 | C5 | band 0.00 - 3.00: south wall x 2.50 - 4.00, SE corner, east wall y 0 - 1.50 | first piece (no end lap) |
| G | 1.00 x 2.80 | roll 2, 6.00 - 8.80 | ripped into L3, L4, L5 (0.30) + 0.10 residue | - |
| B3 (= L3) | 0.30 x 2.80 | G | band 4.80 - 7.60: north wall x 3.70 - 0.90 | end lap over B2 |
| B4 (= L4) | 0.30 x 2.80 | G | band 7.50 - 10.30: north wall x 1.00 - 0, NW corner, west wall y 3.00 - 1.20 | end lap over B3 |
| B5 (= L5) | 0.30 x 2.80 | G | band 10.20 - 13.00: west wall y 1.30 - 0, SW corner, south wall x 0 - 1.50 (west jamb) | end lap over B4 |
| G residue | 0.10 x 2.80 | G | true waste (narrower than any piece) | - |
| (stock) | 1.00 x 1.20 | roll 2, 8.80 - 10.00 | untouched | - |

Band run positions are measured from the east jamb (x 2.50), going east. The corners are at 1.50 (SE), 4.50 (NE),
8.50 (NW) and 11.50 (SW); the run ends at the west jamb at 13.00. The corrected cutting plan with every rip and
cross-cut is in `diagrams/WPB-A1_cutting.svg`; the installation plan, with the upturn folded out flat, is in
`diagrams/WPB-A1_install.svg`.

## 3. Laps, junctions, corners and doorway, each listed separately

| Condition | A (as planned, j = 0.10) | B (continuous fold) |
|---|---|---|
| Side laps (floor strips) | 4 seams x 3.00 x 0.10 = **1.20 m2** | 3 seams x 4.40 x 0.10 = **1.32 m2** (each seam continues 0.20 up the end walls) |
| End laps - floor | 0 | 0 |
| End laps - band joints | 4 x (0.30 x 0.10) = **0.12 m2**, across the full band width | none |
| Floor-to-wall junction | band folded at the junction; flange 0.10 x 13.00 = **1.30 m2** onto the floor sheet (0.04 of it is the flange folding on itself at the 4 internal corners) | continuous fold, 13.00 m (+ 1.00 m flat into the doorway): **no lap** |
| Internal corners (4) | each inside one band piece (B1, B2, B4, B5); flange pleat 0.10 x 0.10 each; treatment **WITHHELD** | 0.20 x 0.20 excess sheet each (0.16 m2 in all): folded or cut out; treatment **WITHHELD** |
| Doorway transition | DW lapped 0.10 onto the floor (**0.10 m2**); DW meets B1 and B5 **edge to edge at both jambs (0.00 overlap)**; threshold transition **UNRESOLVED** (N-1) | the strip lies flat into the opening; **2 slits of 0.20 m** at the jambs; threshold transition **UNRESOLVED** |
| Multi-layer points | 7 floor-seam ends under the flange, 1 under the doorway lap (S2/S3); as listed by V2.5, **2 band joints lie exactly on seam ends** (4.80 - 4.90 on S4/S5 and 7.50 - 7.60 on S1/S2: four layers) | 6 seam-to-fold crossings |
| Laps total | **2.72 m2** | 1.32 m2 + 0.16 m2 corner excess |

**The joints of the V2.5 plan can be placed better.** V2.5 fixes no joint position. Laid in the order it lists the
pieces, two band joints stack on floor-seam ends. The same five pieces, laid from the west jamb in the order
2.00, 3.00, 2.80, 2.80, 2.80, put the joints at 11.00 - 11.10, 8.10 - 8.20, 5.40 - 5.50 and 2.70 - 2.80. That keeps every
joint at least 0.30 m from a corner and at least 0.20 m from a seam end, with no change of material (WPB-A1-ARR).
Other orders trade one distance against the other: one keeps every joint 0.90 m from a corner, but at the cost
of the seam-end distance.
Whether those distances are enough is a product value (N-12).

## 4. Material reconciliation

| | A as planned (WPB-A1) | B continuous fold (WPB-B) |
|---|---|---|
| Surfaces to waterproof (proven subtotal) | 12.00 + 2.60 + 0.20 = **14.80** | **14.80** (the same surfaces) |
| Installed membrane | 13.20 floor + 0.30 doorway + 4.02 band = **17.52** | 4 strips = 13.20 + 3.08 = **16.28** = 14.80 + 1.32 laps + 0.16 corners |
| Cut from the rolls (consumed) | 5 x 3.00 + 2.80 = **17.80** | 4 x 4.40 = **17.60** |
| Reusable offcuts | 0 | the 0.30 x 4.40 trim of the last strip: **1.32** (subject to N-7) |
| True waste | the 0.10 x 2.80 residue of G: **0.28** | 0 |
| Untouched roll stock | 1.00 + 1.20 = **2.20** | 1.20 + 1.20 = **2.40** |
| Balance | 17.80 = 17.52 + 0 + 0.28 | 17.60 = 16.28 + 1.32 + 0 |
| Rolls / seams | **2** / 8 | **2** / 3 |

## 5. Do 17.80 m2 and two rolls remain valid?

| Buildable alternative | Consumed (m2) | Rolls | Seams | State |
|---|---|---|---|---|
| A, flange 0.10, V2.5's selection (least membrane inside a direction) | **17.80** | **2** | 8 | CONDITIONAL: the product accepts a 0.10 m flange onto the floor sheet, with no reinforcing strip |
| A, flange 0.10, the approved order applied to the band plan as well (fewest joints first) | 18.44 | 2 | 7 | CONDITIONAL, and depends on the scope of UP-WP-LAY-001 (N-9) |
| A, flange 0.11 - 0.13 | 18.77 | 2 | 7 | CONDITIONAL (both readings) |
| A, flange 0.14 - 0.15 (strips along X; along Y needs 3 rolls) | 18.75 (fewest joints: 19.40) | 2 | 8 (7) | CONDITIONAL |
| A, flange 0.16 and wider | 20.60 (fewest joints: 22.55) | **3** | 5 (4) | CONDITIONAL |
| A + a reinforcing strip or fillet at the junction | 17.80 + the strip | 2 or more | - | **BLOCKED**: the strip's width and material are product data |
| B, continuous fold (strips along X) | **17.60** | **2** | 3 | CONDITIONAL: a sheet that may be folded at 90 degrees; corner excess and jamb slits by detail |

So:
- **Two rolls hold** for every alternative with a junction flange up to 0.15 m, and for the continuous fold.
- **A flange of 0.16 m or more needs a third roll.** V2.5 reports that the roll count "does not change", but it tests
  only the doorway alternatives, never the junction (F-09).
- **17.80 m2 holds only for V2.5's own assumption:** a 0.10 m flange, no junction reinforcement, and least membrane
  inside the chosen direction.
- **The continuous fold needs less membrane (17.60 m2) and has the fewest seams.** It is physically possible only with
  a foldable sheet.
- **The proven subtotal of 14.80 m2 is the same in every case.** This audit changes no V2.5 figure: V2.5 is frozen.
  What the audit corrects is the claim that one material figure is buildable without a junction detail.

The sweep is in `JUNCTION_SWEEP.md`: every flange width from 0.10 to 0.20 m, both readings. It was hand-verified at 0.10,
0.11, 0.15 and 0.16.

## 6. What must be confirmed for the selected system

The flange width j, and any fillet or reinforcing strip, or the foldability of the sheet. Also the corner detail
(pleat, patch or preformed piece), the end-lap width, the doorway detail including its two jamb junctions, and the
minimum distance of a band joint from a corner and from a floor-seam end. See `PRODUCT_AND_OWNER_CONFIRMATIONS.md`.
None of these is assumed here. The 0.11 - 0.20 m flanges are sensitivity points, not standards.

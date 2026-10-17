# The L-shaped bathroom: internal-corner continuity, seam locations and material cutting

Room WP-D: a 3.00 x 3.00 m square with the 1.00 x 1.00 m north-east corner cut away; vertices (0,0) (3,0) (3,2) (2,2)
(2,3) (0,3); a 0.90 m door in the south wall (x 0.50 - 1.40). The upturn is one open run of 11.10 m, measured from the
east jamb going east. Its corners are:
- SE at 1.60, (3,2) at 3.60, (2,3) at 5.60, NW at 7.60 and SW at 10.60 (internal);
- (2,2) at 4.60 (external: the re-entrant corner of the L).

The V2.5 plan was rebuilt piece by piece (WPD-A1) and every quantity was reproduced:
- consumed 13.80 m2, installed 12.52 m2;
- laps: 0.80 side, 1.11 flange, 0.12 band joints, 0.09 doorway piece;
- 2 rolls, 7 seams.

Diagrams: `diagrams/WPD-A1_install.svg`, `diagrams/WPD-A1_cutting.svg`, and `-ARR`, `-REUSE`, `-FJ` for the
alternatives.

## 1. Internal-corner continuity

| Corner | Run position (m) | Kind | Covered by | Joint nearest | Finding |
|---|---|---|---|---|---|
| SE (3,0) | 1.60 | internal | B1 (0 - 2.00), continuous | 1.90 - 2.00 (0.30) | continuous; flange pleat; treatment withheld |
| (3,2) | 3.60 | internal | B3 (2.90 - 5.70), continuous | 2.90 - 3.00 (0.60) | continuous |
| (2,2) | 4.60 | **external** | B3, continuous on the wall; **the flange must be slit**, leaving a 0.10 x 0.10 gap on the floor | - | treatment withheld; an external corner needs its own piece in either junction method |
| (2,3) | 5.60 | internal | B3 runs to 5.70; **B4 starts exactly on the corner** - its end lap begins on the corner line | 5.60 - 5.70 (**0.00**) | FAIL (F-03): a lap edge in the corner fold |
| NW (0,3) | 7.60 | internal | B4 (5.60 - 8.40) | 8.30 - 8.40 (0.70) | continuous |
| SW (0,0) | 10.60 | internal | B5 (8.30 - 11.10) | 8.30 - 8.40 (2.20) | continuous |

Totals:
- 5 internal flange pleats (0.05 m2, folded inside the band material) and 1 external flange gap (0.01 m2);
- every corner treatment is WITHHELD by V2.5, and none is treated as complete here.

The best order of the V2.5 pieces, 1.10, 2.80, 2.80, 2.00, 2.80 (WPD-A1-ARR), takes the piece edge off the corner. Even
so, the nearest joint is only 0.10 m from corner (3,2). No order of these five pieces does better. With the step offcut
reused (section 3), every joint is at least 0.20 m from a corner.

## 2. Seam locations

- **Floor strips** run along X:
  - S1 y 0 - 1.00 and S2 0.90 - 1.90, both 3.00 m;
  - S3 1.80 - 2.80, cut 3.00 m with its corner beyond the step removed;
  - S4 2.70 - 3.00, 2.00 m.
- **Floor seams:**
  - S1/S2 at y 0.90 - 1.00 and S2/S3 at y 1.80 - 1.90, both across the full 3.00 m;
  - S3/S4 at y 2.70 - 2.80, over x 0 - 2.
- **The re-entrant corner (2,2)** lies inside S3, 0.10 m above the S2/S3 lap. It is not on a seam.
- **The flange along the step wall** (y 1.90 - 2.00, x 2 - 3) lies on S3. Its lower edge meets the buried edge of S2:
  no conflict.
- **The flange along the wall x = 2** (y 2 - 3) crosses the S3/S4 seam.
- **Seam ends on the walls**, as run positions: 2.50 - 2.60, 3.40 - 3.50, 5.30 - 5.40, 7.80 - 7.90, 8.70 - 8.80 and
  9.60 - 9.70. All 6 are under the flange. No band joint lies on one; the nearest is 0.20 m away.

## 3. Material cutting

| Item | Independent rebuild | V2.5 record | Finding |
|---|---|---|---|
| The corner of S3 beyond the step | a full **1.00 x 0.80 m** piece (x 2 - 3, y 2.0 - 2.8), cut off at the wall | "trim at the wall line (shaped; area-equivalent width) 0.2667 x 3.0" | FAIL (F-02): the record describes a shape that does not exist; the area (0.80 m2) is right |
| Its classification | **reusable** (it can hold the doorway piece or two band lanes); subject to N-7 | counted as cutting waste | NOTE (F-07) |
| True waste | the 0.10 x 2.00 residue of C4 + the 0.10 x 2.80 residue of the band segment = 0.48 m2 | 1.28 m2 "cutting waste" in all | the 1.28 = 0.48 true + 0.80 reusable |
| Reusing the step offcut (WPD-REUSE) | doorway piece 0.90 x 0.30 from it; the band then needs a 2.50 m segment instead of 2.80 m: **13.50 m2**, the same 2 rolls, 4 band joints and 12.52 m2 installed | - | V2.5 is 0.30 m2 conservative here |

**Fewest-joints reading (WPD-FJ).** Two 5.60 m band pieces, one joint, 16.60 m2. That costs 2.80 m2 more for 3 fewer
joints. Its only joint (5.50 - 5.60) then **ends exactly on the internal corner (2,3)** from either jamb, so moving it
needs a longer segment. Fewest joints is not automatically more buildable: joint placement has to be checked in every
reading.

## 4. Continuous fold for the L

This was not calculated. At the external corner (2,2), one sheet cannot be folded up both walls: the two flaps would
need the same 0.20 x 0.20 m of sheet. A gusset piece is needed there, sized by the product detail. The rectangular rooms
(WP-B, WP-E) show the method.

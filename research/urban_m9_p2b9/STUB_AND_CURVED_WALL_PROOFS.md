# Stub and curved-wall proofs — worked examples 3 and 4 (UP-WALL-GEOM-001)

The wall run (ARCH.WALL_RUN) is measured on the **centreline**, per thickness family, where both wall faces are drawn
(the band rule: at least 0.30 m of both faces). The room finishes use the room's **own face**. The external finish
uses the outer face. These are separate measures and are never substituted for one another.

Tests: `test_p2b9_walls.py`, `test_p2b9_indep_census.py`.

## Example 3 — collinear stubs in a south wall

**Drawing.**

- A 4.00 × 3.00 m bedroom. The south wall has door D1 at x 0.40–1.40 and window W3 at x 1.65–3.95 (2.30 m).
- Between them, both faces are drawn over short stubs:
  - a west return of 0.20 m;
  - a pier of 0.25 m;
  - an east return of 0.25 m.

| Quantity | Formula | Hand | V2.7.1 | V2.8 | Diff | Status |
|---|---|---|---|---|---|---|
| stubs | 0.20 + 0.25 + 0.25 | 0.70 m | in the run | in the run | 0 | VERIFIED (hand) |
| wall run | north 4.00 + east 3.00 + west 3.00 + stubs 0.70 | 10.70 m | 10.70 | 10.70 | 0 | VERIFIED (hand) |
| plaster | 14.00 × 3.00 − 1.00 × 2.20 − 2.30 × 1.20 | 37.04 m² | — | 37.04 | 0 | VERIFIED (hand) |
| skirting | 14.00 − 1.00 | 13.00 m | — | 13.00 | 0 | VERIFIED (hand) |

**Finding: the Phase 2B-8 description of D-P8-03 is corrected.** Collinear stubs **were already measured** by V2.7.1:
the face lines merge into one band over their cover intervals, so the 0.30 m rule applies to the band, not to each
piece. They are not lost, and V2.8 changes nothing here.

## Example 3R — returns standing into the room at the door jambs

**Drawing.** The example-1 room without its window. Two 0.20 m-thick returns stand into the room at the door jambs:

- a 0.20 m return (x 0.80–1.00, y 0.20–0.40);
- a 0.35 m return (x 2.00–2.20, y 0.20–0.55).

| Quantity | Formula | Hand | V2.7.1 | V2.8 | Diff | Status |
|---|---|---|---|---|---|---|
| room area | 12.00 − 0.20 × 0.20 − 0.20 × 0.35 | 11.89 m² | 11.89 | 11.89 | 0 | VERIFIED (hand) |
| room perimeter | every return face included | 15.10 m | 15.10 | 15.10 | 0 | VERIFIED (hand) |
| plaster | 15.10 × 3.00 − 1.00 × 2.20 | 43.10 m² | — | 43.10 | 0 | VERIFIED (hand) |
| skirting | 15.10 − 1.00 | 14.10 m | 14.10 | 14.10 | 0 | VERIFIED (hand) |
| wall run, bands only | 4.00 + 3.00 + 3.00 + 0.60 + 2.00 + 0.35 | 12.95 m | **12.95** | — | — | the 0.20 m return is lost |
| wall run, with the short return measured as wall | 12.95 + 0.20 | 13.15 m | — | **13.15** | 0 | VERIFIED (hand) and by the independent return census |
| the return's plan strip | 0.20 × 0.20 | 0.04 m² | in the junction pieces | moved from the junction pieces into the wall strips | 0 | conserved: wall faces 2.87 = strips + junction, before and after |

**Why the 0.30 m exclusion loses quantities.** The rule exists so that drafting artefacts are not counted, but a
0.20 m return at a jamb is real masonry. Under V2.7.1 it is in the room's finishes (its faces bound the room) but not
in the wall run or the masonry by thickness.

**V2.8's RETURN_STUB** is a pair of parallel wall-layer lines that satisfies all of the following:

- 0.05–0.30 m of overlap;
- the thickness of a wall family the floor already has (±5 mm);
- no wall line between them;
- at least one end closed by a wall-layer line across them;
- outside every existing band's strip.

Stretches under 0.05 m are drafting artefacts and are never counted.

## Example 4 — a 90° curved wall

**Drawing.** A quarter-disc bedroom: straight walls along x and y, and a curved wall centred on the inner corner with
inner radius 3.00 m and outer radius 3.20 m (0.20 m thick).

| Measure | Formula | Hand | V2.8 | Diff | Status |
|---|---|---|---|---|---|
| inner face arc (the room side) | π/2 × 3.00 | 4.712389 m | 4.712389 | 0 | VERIFIED (hand) |
| centreline arc (the wall run) | π/2 × 3.10 | 4.869469 m | 4.869469 | 0 | VERIFIED (hand) |
| outer face arc (external finish) | π/2 × 3.20 | 5.026548 m | 5.026548 | 0 | VERIFIED (hand) |
| curved wall plan strip | π/4 × (3.20² − 3.00²) = 4.869469 × 0.20 | 0.973894 m² | 0.973894 | 0 | VERIFIED (hand) |
| floor | π × 3.00² / 4 | 7.068583 m² | 7.068583 | 0 | VERIFIED (hand) |
| plaster (inner face × H − door) | (3.00 + 3.00 + 4.712389) × 3.00 − 2.20 | 29.937167 m² | 29.937167 | 0 | VERIFIED (hand) |
| skirting | 10.712389 − 1.00 | 9.712389 m | 9.712389 | 0 | VERIFIED (hand) |
| wall run | straight 5.00 + centreline arc 4.869469 | 9.869469 m | 9.869469 | 0 | VERIFIED (hand) |

`WALL_GEOMETRY.json` keeps the three arcs and both radii of every curved wall. The finish uses the inner face, the run
the centreline, the external finish the outer face. **No mean radius is ever used for a face.**

## Example 4S — a window in the curved wall, 0.20 m curved stubs at each end

| Quantity | Formula | Hand | V2.7.1 | V2.8 | Diff | Status |
|---|---|---|---|---|---|---|
| each curved stub, inner face | 3.00 × (0.20 / 3.00) | 0.200000 m | — | 0.200000 | 0 | VERIFIED (hand) |
| each curved stub, centreline | 3.10 × (0.20 / 3.00) | 0.206667 m | not in the run | 0.206667 | 0 | VERIFIED (hand + arc census) |
| wall run change | 2 × 0.206667 | 0.413333 m | — | +0.413333 | 0 | VERIFIED (independent stub census) |
| the room | — | 7.068583 m² | **lost silently** | **lost; V2.8 says so** (ROOM_LABEL_NOT_IN_A_CLOSED_SPACE) | — | **D-P9-01 open** |

- **D-P9-01.** With curved glazing alone and no wall gap, the plan reader does not infer a window, so the room is not
  closed and is in no quantity. V2.8 adds the finding but does not fix the role inference.
- **D-P9-02.** With the roles declared, the window is closed at the glazing line. This adds the 0.438423 m² strip
  between the face and the glazing to the floor and ceiling (7.507006 instead of 7.068583 m²), and makes the wall
  finish a range. Not fixed.

## Reference plan

V2.8 finds **one curved stub** (first floor, 0.20 m wall, inner face 0.160 m, centreline **0.16854 m**) and **no
straight return**.

- **Arc census.** The independent arc census, read from the raw ARC / bulge entities, finds the same pair:
  - radii 1.935 / 2.135 m, sweep 0.0828 rad, centreline 0.16854 m → **VERIFIED**;
  - and a second piece of 0.0414 m, whose inner face of 0.039 m is under the 0.05 m artefact limit. That accounts
    for the rest of the 0.209947 m reported in Phase 2B-8.
- **Return census.** The independent straight-return census, restricted to the three plan regions, finds **no
  return**.
  - Run drawing-wide, it found 7 candidates. Six were on section / elevation sheets.
  - The seventh was a column with a 0.10 m wall nib above it, inside an existing 0.20 m wall line.
  - This is why the census reads only inside the plan regions and excludes stretches whose middle lies in a column
    outline.

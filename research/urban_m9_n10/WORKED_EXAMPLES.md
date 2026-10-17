# Worked examples and independent proofs (Phase N10)

Every expected value is arithmetic on the construction situation: the fixture's coordinates and stated heights
(`tests/m9_n10/n10_truth.py`), or the synthetic villa's **design spec** (`tools/synthetic_villa.py`, never the
drawing or the engine). The engine value is the ARCH_TAKEOFF_V2.9 run (or `engine/source/struct_n10.py` on the
route G register). The difference is engine − expected.

Produced by `run_proofs.py` (in the handoff ZIP) on synthetic fixtures only; no private drawing is involved.

**27 of 27 rows PASS.**

| # | Example | Quantity | Unit | Rule | Formula | Dimensions | Expected | Engine | Difference | Tolerance | Status | Provenance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | E1 curved sill window (4S) | room floor | m2 | UP-OPEN-CURVED-001 | quarter disc r 3.00: pi/4 x 3.00^2 ... / 2 | r_in 3.00, r_out 3.20, glazing r 3.10, 90 deg | 7.068583 | 7.068583 | -4.71e-07 | 1e-06 | PASS | hand truth n10_truth.FLOOR |
| 2 | E1 curved sill window (4S) | window width on the room face | m | UP-OPEN-CURVED-001 | 3.00 x (pi/2 - 2 x 0.20/3.00) | 0.20 m stub on the inner face at each end | 4.312389 | 4.312389 | +1.96e-08 | 1e-06 | PASS | hand truth WIN_INNER |
| 3 | E2 curved room WINDOW (W4) | wall plaster | m2 | UP-OPEN-CURVED-001 + UP-HGT-001 | P x H - D1 1.00 x 2.20 - opening width x its band | P 10.712389, H 3.00 | 24.762300 | 24.762300 | -1.65e-07 | 1e-06 | PASS | hand truth n10_truth |
| 4 | E2 curved room WINDOW (W4) | skirting | lm | UP-SKIRT-001 | P - doors / passages / floor glazing | P 10.712389 | 9.712389 | 9.712389 | +1.96e-08 | 1e-06 | PASS | hand truth n10_truth |
| 5 | E2 curved room WINDOW (W4) | room floor | m2 | UP-OPEN-CURVED-001 | quarter disc inside the inner face | r 3.00 | 7.068583 | 7.068583 | -4.71e-07 | 1e-06 | PASS | hand truth |
| 6 | E2 curved room FLOOR_GLAZING (W5) | wall plaster | m2 | UP-OPEN-CURVED-001 + UP-HGT-001 | P x H - D1 1.00 x 2.20 - opening width x its band | P 10.712389, H 3.00 | 17.000000 | 17.000000 | -3.55e-15 | 1e-06 | PASS | hand truth n10_truth |
| 7 | E2 curved room FLOOR_GLAZING (W5) | skirting | lm | UP-SKIRT-001 | P - doors / passages / floor glazing | P 10.712389 | 5.400000 | 5.400000 | +0.00e+00 | 1e-06 | PASS | hand truth n10_truth |
| 8 | E2 curved room FLOOR_GLAZING (W5) | room floor | m2 | UP-OPEN-CURVED-001 | quarter disc inside the inner face | r 3.00 | 7.068583 | 7.068583 | -4.71e-07 | 1e-06 | PASS | hand truth |
| 9 | E2 curved room DOOR (D2) | wall plaster | m2 | UP-OPEN-CURVED-001 + UP-HGT-001 | P x H - D1 1.00 x 2.20 - opening width x its band | P 10.712389, H 3.00 | 27.737167 | 27.737167 | +5.88e-08 | 1e-06 | PASS | hand truth n10_truth |
| 10 | E2 curved room DOOR (D2) | skirting | lm | UP-SKIRT-001 | P - doors / passages / floor glazing | P 10.712389 | 8.712389 | 8.712389 | +1.96e-08 | 1e-06 | PASS | hand truth n10_truth |
| 11 | E2 curved room DOOR (D2) | room floor | m2 | UP-OPEN-CURVED-001 | quarter disc inside the inner face | r 3.00 | 7.068583 | 7.068583 | -4.71e-07 | 1e-06 | PASS | hand truth |
| 12 | E2 curved room PASSAGE (passage) | wall plaster | m2 | UP-OPEN-CURVED-001 + UP-HGT-001 | P x H - D1 1.00 x 2.20 - opening width x its band | P 10.712389, H 3.00 | 26.937167 | 26.937167 | +5.88e-08 | 1e-06 | PASS | hand truth n10_truth |
| 13 | E2 curved room PASSAGE (passage) | skirting | lm | UP-SKIRT-001 | P - doors / passages / floor glazing | P 10.712389 | 8.712389 | 8.712389 | +1.96e-08 | 1e-06 | PASS | hand truth n10_truth |
| 14 | E2 curved room PASSAGE (passage) | room floor | m2 | UP-OPEN-CURVED-001 | quarter disc inside the inner face | r 3.00 | 7.068583 | 7.068583 | -4.71e-07 | 1e-06 | PASS | hand truth |
| 15 | E3 masonry 0.20 m walls | wall panel area | m2 | UP-MAS-HEIGHT-001 | plan 2.46 / 0.20 x 3.20 + 0.90 + 3.00 | outer 4.40 x 3.40, inner 4.00 x 3.00, T.O.S. -0.10, U/S SLAB +3.10 | 43.260000 | 43.260000 | -1.42e-14 | 1e-06 | PASS | hand truth (two derivations agree) |
| 16 | E3 masonry 0.20 m walls | wall volume | m3 | UP-MAS-HEIGHT-001 | area x 0.20 | t 0.20 | 8.652000 | 8.652000 | -3.55e-15 | 1e-06 | PASS | hand truth |
| 17 | E3 masonry with B.O.B. +2.60 | wall panel area (low end of the range) | m2 | UP-MAS-HEIGHT-001 | panel to the beam bottom 2.70 m | B.O.B. +2.60 | 35.860000 | 35.860000 | -1.42e-14 | 1e-06 | PASS | hand truth |
| 18 | E4 facade | facade run | lm | UP-FACADE-001 | 2 x (4.40 + 3.40) | openings closed on the outer face | 15.600000 | 15.600000 | -1.78e-15 | 1e-06 | PASS | hand truth |
| 19 | E4 facade | facade area net | m2 | UP-FACADE-001 | 15.60 x 3.50 - 1.00 x 2.20 - 1.50 x 1.20 | F.F.L. 0.00 to F.F.L. +3.50 | 50.600000 | 50.600000 | -7.11e-15 | 1e-06 | PASS | hand truth |
| 20 | E4 facade, curved room | facade run | lm | UP-FACADE-001 | 3.40 + 0.20 + 3.20 x pi/2 + 0.20 + 3.40 | outer arc r 3.20 | 12.226548 | 12.226548 | -2.46e-07 | 1e-06 | PASS | hand truth |
| 21 | E5 villa seed 3 | footing sides (FORMED) | m2 | UP-FW-001 | sum 2 x (L + W) x D (design) | 16 footings | 62.400000 | 62.400000 | +1.42e-14 | 1e-06 | PASS | synthetic design spec |
| 22 | E5 villa seed 3 | column sides (upper bound) | m2 | UP-FW-001 | sum 2 x (a + b) x (h - t) (design) | 2 storeys | 163.072000 | 163.072000 | -2.84e-14 | 1e-06 | PASS | synthetic design spec |
| 23 | E5 villa seed 3 | slab soffit | m2 | UP-FW-001 | sum of panel areas between beam faces (design) | panels between beam faces, column corners out | 236.380000 | 236.380000 | -1.14e-13 | 0.001 | PASS | synthetic design spec (route G rounds to 1e-4) |
| 24 | E5 villa seed 5 | footing sides (FORMED) | m2 | UP-FW-001 | sum 2 x (L + W) x D (design) | 16 footings | 47.360000 | 47.360000 | -7.11e-15 | 1e-06 | PASS | synthetic design spec |
| 25 | E5 villa seed 5 | column sides (upper bound) | m2 | UP-FW-001 | sum 2 x (a + b) x (h - t) (design) | 2 storeys | 157.248000 | 157.248000 | -2.84e-14 | 1e-06 | PASS | synthetic design spec |
| 26 | E5 villa seed 5 | slab soffit | m2 | UP-FW-001 | sum of panel areas between beam faces (design) | panels between beam faces, column corners out | 348.955000 | 348.955000 | -1.71e-13 | 0.001 | PASS | synthetic design spec (route G rounds to 1e-4) |
| 27 | E6 excavation pit | volume | m3 | UP-EXC-001 | (1.8 + 2 x 0.3) x (1.6 + 2 x 0.3) x 1.5 | stated depth 1.50 m, working space 0.30 m | 7.920000 | 7.920000 | +0.00e+00 | 1e-09 | PASS | hand truth |

## Conservation checks (tests)

| Check | Holds | Test |
|---|---|---|
| curved room: floor + the reveal strip = the room closed at the glazing (7.068583 + 0.438423 = 7.507006 m²) | yes | `test_n10_indep_curved.py` |
| masonry: two derivations of the panel area agree (run-equivalent and centreline: 43.26 m²) | yes | `test_n10_masonry.py::test_hand_truth_is_consistent` |
| facade: the outline's plate equals the engine's existing gross floor plate (reference plan, 3 floors, difference 0.000000 m²) | yes | `REAL_PLAN_BEFORE_AFTER.md` |
| facade: the outline ring (arcs flattened at 0.05 m) equals the recorded perimeter | yes | reference plan, 3 floors |
| formwork: soffit × depth, sides / perimeter + slab and L × W × D rebuild each element's route G volume | yes, every element of seeds 3 and 5 | `test_n10_structural.py::test_faces_conserve_the_route_g_concrete` |
| formwork: measured beam soffit + the held spans' own plan = the design's beam soffit | yes, seeds 3 and 5 | `test_formwork_matches_the_design` |
| the route G run is read only (every file's SHA-256 unchanged after struct_n10) | yes | `villa` fixture |

## Not proved here

- No accuracy figure for any category: there is one real plan and no blind evaluation (the sealed protocol is unchanged).
- Masonry on a real plan: the reference plan has no T.O.S. / U/S SLAB on a bound section band (held).
- Facade area on a real plan: no next-floor F.F.L. on a bound band (held); the run is measured and partly verified.

# S8.1 - ground slab, two source-zoned cells (2026-10-08)

Restricted, project-basis quantity of the ground slab. The other S8 families are not started and no frozen stage moves. S7 stays at **3,802.015 kg**.

## Zones

- GS-ZONE-1690: cell SP-GBP-08, 14.893125 m2, marker 'T=10cm / 5Ø10/m E.W.'
- GS-ZONE-169D: cell SP-GBP-14, 22.965398 m2, marker 'T=10cm / 5Ø10/m E.W.', printed level +0.30

19 other cells (129.770584 m2) carry no thickness and no mesh in the source. They are blocked, not filled. The ground stair flight and the court cell are other owners.

## Quantities (project basis)

- Concrete: 3.785852 m3 (net zone area x 0.100 m).
- Mesh X (bars along x): 189.292616 m, 116.847294 kg.
- Mesh Y (bars along y): 189.292616 m, 116.847294 kg.
- Total: 233.694587 kg (RESTRICTED_S8_1_PROJECT_BASIS).

Rate density 5 /m x strip integral, D^2/162. The equivalent count is never rounded and never +1. One bar family each way; no second mat, lap, hook, edge bar or development length. X and Y are integrated over their own strips (05); each covers the whole zone, so the two directions carry the same length.

Concrete and mesh are PROJECT_BASIS_QTO: the thickness and mesh are printed, the plan is the drawn ground-beam faces, but the extent of each T=10 marker (its own cell) is a binding the engineer has to confirm before the concrete can be called source-derived physical.

## Not quantified

56 blocked records (06): 19 cells x thickness and mesh, plus per zone the end anchorage, fabrication count, slab-beam interface, supplementary bars, laps and the sub-base. Bar position against P8-N22 cover is a SOURCE_CONFLICT.

## Checks

- Every one of the 21 PRE-S8 faces terminates once; the parent carries no quantity of its own.
- X and Y strips each cover the zone area exactly; zone, direction, diameter and parent totals reconcile.
- No ground-beam face, column / neck outline or other concrete linework crosses a zone; footings are below the slab, the lift and pool are elsewhere, and no S7 item is on the ground-beam plan.
- The comparison with earlier figures runs only after the freeze (post_freeze/).

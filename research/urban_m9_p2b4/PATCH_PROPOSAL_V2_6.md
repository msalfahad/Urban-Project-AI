# Patch proposal - ARCH_TAKEOFF_V2.6 (documented, NOT applied)

**Status: proposed only.** No engine, CLI, rules or registry file was changed by this audit. V1 - V2.5 are frozen. This
proposal is implemented only on the owner's explicit authorisation, as a new opt-in method.

## Authorisation boundaries

| May | Must not |
|---|---|
| add the opt-in method ARCH_TAKEOFF_V2.6 to `tools/urban_boq_m9.py` (V2.5 + the changes below, behind `method == V2.6`) | change any output of V1, V2, V2.1, V2.2, V2.3, V2.4 or V2.5 - byte identity is re-verified on the villa, its mirror and the reference plan, as in Phase 2B-3 |
| add new constraint keys to `engine/source/membrane_layout.py` and new functions to `waterproofing_system.py`, read only by V2.6 | edit `rules/`, the frozen baselines, `opening_census.py`, or any registry file (a registry rule for the junction only after N-11 is decided, as a new registry version) |
| add tests and proof cases (this audit's `tests/m9_p2b4` is the acceptance set) | choose a junction, corner, doorway or penetration detail by default |
| read a membrane-system data sheet given as project data | invent a product value (flange, end lap, joint offset, minimum piece) or report a roll count as CONFIRMED without a system data sheet |

## Changes

| # | Change | Fixes |
|---|---|---|
| C-1 | **FLOOR_WALL_JUNCTION as an explicit detail.** Its states are UNRESOLVED (the default), SEPARATE_UPSTAND (j, optional reinforcing strip width) and CONTINUOUS_FOLD.<br>- While it is unresolved, the material requirement is PROVISIONAL and the schedule shows each alternative: consumed, rolls, seams.<br>- The proven subtotal is unchanged.<br>- Roll sensitivity also covers the junction alternatives, up to the system's largest lap | F-01, F-09 |
| C-2 | **A piece-level cutting plan output.** Every cut, rip and cross-cut, with a piece id, size, source roll and position, and destination (floor strip / run position / doorway). Joint positions are given, and offcuts are classed as true waste, reusable or roll stock. The shaped trims become their real rectangles | F-02, F-07 |
| C-3 | **Joint placement.** The best order and direction of the band pieces of each run, keeping joints off corners and floor-seam ends. A product parameter `min_joint_offset_m` is added; while it is unknown, the distances are flagged as JOINT_OFFSET_UNVERIFIED, and a joint at 0 is flagged JOINT_AT_CORNER or JOINT_ON_SEAM_END | F-03 |
| C-4 | **The doorway detail names its jamb junctions** (2 per door, BUTT_JOINT_OPEN) and the jamb reveals | F-04 |
| C-5 | **Offcut reuse behind N-7.** With a minimum reusable size given, material cut off at a stepped wall can supply band lanes and doorway pieces | F-07 |
| C-6 | **Selection scope switch (N-9):** DIRECTION_ONLY (the V2.5 behaviour) or WHOLE_PLAN | F-10 |
| C-7 | Continuous-fold layouts for rectangular rooms: the developed surface, corner excess and jamb slits. Rooms with an external corner stay BLOCKED until the gusset detail is given | F-01 (method B) |

## Acceptance

- **This audit's library** (`tests/m9_p2b4`, 31 tests) and the Phase 2B-3 proof library pass. Under V2.6:
  - the engine's piece-level plan for WP-B, WP-E and WP-D equals the independent rebuild piece for piece;
  - with the junction UNRESOLVED, the schedule shows 17.80 / 17.60 / 20.60 m2 for WP-B as alternatives (2 / 2 / 3
    rolls).
- **V1 - V2.5 outputs** are byte-identical, and the freeze verifier is clean.
- **Determinism:** two V2.6 runs give identical outputs.

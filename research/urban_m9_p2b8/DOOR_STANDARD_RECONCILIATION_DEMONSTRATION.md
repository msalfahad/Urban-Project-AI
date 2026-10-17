# Door-standard reconciliation: demonstration

**Method:** ARCH_TAKEOFF_V2.7.1, rule UP-DOOR-OPEN-003 (registry 1.3.0).

**Outputs:** `DOOR_STANDARD_RECONCILIATION.json` / `.csv`, policy URBAN_DOOR_STANDARD_RECONCILIATION_V1.

**The owner minimums are kept:** 1.00 m for an ordinary door, 0.90 m for a bathroom door. What the minimum refers to (the structural opening, the leaf or the clear passage) is **D-16, still open**. Until it is resolved, every reading is shown side by side and none is applied.

## 1. The fields, kept apart

| Field | What it is | Source |
|---|---|---|
| `as_drawn_wall_opening_m` | the gap in the wall faces, jamb to jamb | the drawing (band gap) |
| `measured_jamb_span_m` | the door symbol's own jamb lines | the drawing (door layer) |
| `jamb_basis` | GAP_IS_THE_DOOR / NARROWED_TO_JAMB_SPAN / NO_JAMB_LINES / NOT_ESTABLISHED | V2.7 D-V27-01 |
| `door_leaf_m` | the drawn leaf (leaf line or swing radius) | the drawing |
| `finished_clear_width_m` | NOT_ESTABLISHED: frame stops and leaf thickness are not in a plan | — |
| `owner_minimum_m` | 1.00 m ordinary, 0.90 m bathroom; none for a main entrance or a lift | UP-DOOR-OPEN-003, D-16 open |
| `frame_allowance` | `value_m` only from an approved schedule, a manufacturer detail or a project rule; otherwise NOT_ESTABLISHED | registry 1.1.0's 0.10 m shown as REQUIRES_CONFIRMATION, never applied |
| `drawn_symbol_difference_m` | the structural opening minus the drawn leaf | **CAD symbol geometry, not an allowance** |
| `proposed_enlargement` | STRUCTURAL_OPENING (min − opening); DOOR_LEAF (low: no allowance, high: with the unconfirmed allowance); CLEAR_PASSAGE NOT_ESTABLISHED | arithmetic on the fields above |
| `within_as_drawn_gap`, `remainder_after_m` | whether the enlargement fits inside the drawn wall gap, and the wall left | arithmetic |
| `review` | consultant / structural: REQUIRED, NOT_REQUIRED or REQUIRED_UNDER_THE_LEAF_READING, with reasons WALL_REMAINDER_CUT / WALL_CUT_BEYOND_DRAWN_OPENING / LINTEL_SPAN_INCREASE / COLUMN_AT_A_JAMB | UP-DOOR-DEP-001 |
| `boq_width_m`, `applied_to_boq` | the BOQ measures the as-drawn door; `applied_to_boq` is always false | — |

**Never:**
- the CAD geometry changed to satisfy the minimum;
- an enlargement applied to a quantity;
- the registry 1.1.0 allowance imposed;
- the drawn symbol difference read as an allowance.

## 2. Hand derivation on a synthetic plan

The plan is `p2b8_fixtures.bath_corridor_door`, the reference plan's pattern: a bathroom door in a wider wall gap, opening into an internal corridor.

- **Wall gap:** 1.027 m, from x = 1000 to 2027 mm.
- **Door jamb lines:** at 1000 and 1800 mm, so the jamb span is 0.80 m.
- **Leaf:** 0.70 m.
- **Rest of the gap:** 0.227 m, proven wall on both faces.

| Field | Hand value | Engine (V2.7.1) |
|---|---|---|
| as-drawn wall opening | 2.027 − 1.000 = 1.027 m | 1.027 |
| measured jamb span | 1.800 − 1.000 = 0.80 m (NARROWED_TO_JAMB_SPAN) | 0.80 |
| leaf | 0.70 m | 0.70 |
| finished clear width | not in a plan | null, NOT_ESTABLISHED |
| owner minimum (bathroom) | 0.90 m | 0.90 |
| frame allowance | none evidenced | null, NOT_ESTABLISHED |
| drawn symbol difference | 0.80 − 0.70 = 0.10 m (geometry) | 0.10, "not an accepted allowance source" |
| enlargement, structural reading | 0.90 − 0.80 = 0.10 m | 0.10 |
| enlargement, leaf reading | low 0.90 − 0.80 = 0.10; high 0.90 + 0.10 − 0.80 = 0.20 m (leaf short by 0.20) | 0.10 / 0.20 |
| fits inside the drawn gap | 0.10 and 0.20 ≤ 0.227 m: yes | low true, high true |
| wall left after | 0.227 − 0.10 = 0.127; 0.227 − 0.20 = 0.027 m | 0.127 / 0.027 |
| review | the drawn wall is cut and the lintel grows: consultant and structural | REQUIRED / REQUIRED |
| BOQ | plaster 9.354 × 3.00 − **0.80** × 2.10 = 26.382 m²; the door set line 0.80 m | 26.382; 0.80; V2.7.1 = V2.7 on this plan |

The other cases, from `test_p2b8_doors.py`:
- **PLAIN:** an external door in a 0.80 m gap, minimum 1.00 m. The enlargement of 0.20 m (0.30 m with the unconfirmed allowance) lies outside the drawn opening: WALL_CUT_BEYOND_DRAWN_OPENING, structural review required.
- **WIDE:** 1.10 m with a 1.00 m leaf. It complies on every reading, so there is no enlargement and no review.
- **DOUBLE:** the 1.60 m main entrance with two 0.75 m leaves. It has no ordinary minimum, is reported as drawn only, and needs no review.

The owner-minimum enlargement exists only as the CONDITIONAL scenario set DOOR_OWNER_MINIMUM (depends on D-16), mutually exclusive between its readings. No BOQ line carries an enlarged width.

## 3. The 0.80 m door recovered in V2.7 (reference plan, Mode A, private run)

V2.7 recovered this bathroom door's 0.80 m from its own jamb lines. V2.6 had measured the whole wall gap.

| Field | Value |
|---|---|
| category | BATHROOM_PVC |
| as-drawn wall opening | 1.023274 m |
| measured jamb span | 0.80 m (NARROWED_TO_JAMB_SPAN), the BOQ width |
| door leaf | 0.69 m (DRAWN_LEAF, swing radius) |
| finished clear width | NOT_ESTABLISHED |
| owner minimum | 0.90 m (bathroom); reference UNRESOLVED (D-16) |
| frame allowance | NOT_ESTABLISHED (value null) |
| drawn symbol difference | 0.11 m, geometry, not an allowance |
| enlargement, structural reading | 0.10 m (required opening 0.90 m) |
| enlargement, leaf reading | 0.10 m low, 0.20 m high with the unconfirmed allowance (the leaf is 0.21 m short) |
| clear passage reading | NOT_ESTABLISHED |
| wall remainder in the gap | 0.223274 m, reduced to 0.123274 m (low) / 0.023274 m (high); both fit |
| review | consultant REQUIRED, structural REQUIRED: WALL_REMAINDER_CUT, LINTEL_SPAN_INCREASE |
| status | BELOW_MINIMUM_ON_EVERY_READING |
| applied to the BOQ | no |

**All 28 doors of the reference plan:**

| Measure | Count |
|---|---|
| By category | BATHROOM_PVC 12, INTERNAL_PVC 8, EXTERNAL_ALUMINIUM 3, CLASS_UNRESOLVED 2, MAIN_ENTRANCE_CANDIDATE 2, CLASS_REVIEW 1 |
| Status | BELOW_MINIMUM_ON_EVERY_READING 18, READINGS_DISAGREE 5, AS_DRAWN_ONLY 5 |
| Jamb basis | GAP_IS_THE_DOOR 21, NO_JAMB_LINES 5, NARROWED_TO_JAMB_SPAN 1, NOT_ESTABLISHED 1 |
| Review (consultant, structural) | REQUIRED 18; REQUIRED_UNDER_THE_LEAF_READING 5; NOT_REQUIRED 5 |
| Review reasons | LINTEL_SPAN_INCREASE 23, WALL_CUT_BEYOND_DRAWN_OPENING 22, WALL_REMAINDER_CUT 1 |
| Enlargement fits inside the drawn gap | 1 door |

**What it means.** On the drawn geometry, 18 of 28 doors are below the owner minimum on every reading of D-16. Of those 18, 17 need the wall cut beyond the drawn opening, which needs structural review. This is reported, and never applied.

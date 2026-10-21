# Door BOQ readiness: ARCH_TAKEOFF_V2.1 on the reference plan

**Status:** acceptance review, 2026-10-14, at `e78f6bd`. No production quantity was changed.

**Basis:**
- A private run of the reference plan.
- Only aggregate values and generic descriptions are published here.
- The per-door table stays outside the repository, following the Phase 2A precedent. It is available to the owner on request.

**Owner rules applied as review criteria (2026-10-13):**
- Internal doors are PVC.
- External doors are aluminium, except the main entrance, which is reported separately.
- Lift doors are excluded from door quantities and areas.
- The lift shaft is excluded from room finishes.
- A double-leaf door is one door set.
- Drawing and schedule dimensions take priority. A fallback is ASSUMED and never confirmed.
- No provisional door is promoted on dimension agreement alone.

## 1. Readiness matrix

The tables count door sets (elements); "leaves" counts door leaves. Widths are structural openings (jamb to jamb, or wall-to-wall closure for a provisional door).

**Released by V2.1 today**

| Group | Count | Leaves | Width (m) | Height | Area | Reviewer readiness |
|---|---|---|---|---|---|---|
| Internal PVC | 14 | 14 | 12.2 | BLOCKED (no source) | BLOCKED | **Count and width release-safe** |
| Internal PVC, the door gained by the robust predicate (kitchen → unlabelled space) | 1 | 1 | 1.0 | BLOCKED | BLOCKED | **Hold: owner** (class may be aluminium, DR-03) |
| External aluminium | 2 | 2 | 1.9 | BLOCKED | BLOCKED | **Count and width release-safe** |
| External aluminium, the stair door to the outside | 1 | 1 | 0.9 | BLOCKED | BLOCKED | **Hold: engineering** (opening 0.9 m against a 1.0 m frame, DR-02) |

**Confirmed geometry, withheld by V2.1**

| Group | Count | Leaves | Width (m) | Height | Area | Reviewer readiness |
|---|---|---|---|---|---|---|
| Main-entrance candidates (external) | 2 | 3 | 3.0 | BLOCKED | BLOCKED | **Withheld: owner names the entrance** (DR-01) |
| Class unresolved (one side finds nothing) | 1 | 1 | 1.0 | BLOCKED | BLOCKED | **Withheld, but silently** (DR-04) |

**Not confirmed**

| Group | Count | Leaves | Width (m) | Height | Area | Reviewer readiness |
|---|---|---|---|---|---|---|
| Provisional (leaf closure only; all internal PVC by side) | 6 | 6 | 4.997 (each 0.797–1.0) | BLOCKED | BLOCKED | **Provisional**: needs opening and topology evidence (DR-05) |
| Unresolved swing (closes no wall gap) | 1 | 1 | — | — | — | **Unresolved** |
| Lift doors classified | 0 | — | — | NOT_APPLICABLE | NOT_APPLICABLE | **Untested on this plan** (DR-06) |

**Totals:**
- 28 door sets and 29 leaves.
- Conservation holds on every floor: every drawn swing is in exactly one element.
- Door area: 0 m² confirmed, because no door height has a source anywhere.

**What the owner can take now:** 16 door sets, counted and measured in width.
- 14 PVC: 12.2 m of opening width.
- 2 aluminium: 1.9 m.
- Heights and areas: none.

**Needing one owner answer each:** 2 more sets (DR-02, DR-03).

**Needing an owner decision:** 3 sets.
- 2 are main-entrance candidates.
- 1 has an unresolved class.

**Needing new evidence:** 6 provisional sets.

## 2. Owner rules: check

| Rule | Result | Evidence |
|---|---|---|
| Internal doors are PVC | **Applied. One door is challenged.** | 15 doors have a space inside the plan on both sides. One of them opens into a small unlabelled space. That space has a 1.4 m doorless opening to the facade, and its level text is 0.15 m below the kitchen's. If it is exterior, the door is aluminium (DR-03, F-20). |
| External doors are aluminium, except the main entrance | **Applied. One door should be held.** | 3 doors have the facade on one side. One has a 100 mm disagreement between its jamb-to-jamb opening (0.9 m) and its door block (1.0 m), and is still released (DR-02, F-18). |
| The main entrance is reported separately: count, width, height, area, material | **Not identified (correctly not assumed).** | Count: 0 confirmed, 2 candidates. Candidate A is a double leaf, 2.0 m (2 × 0.934 m leaves), into the living / reception space. Candidate B is a single leaf, 1.0 m (0.89 m leaf), into the majlis. Height: BLOCKED for both, as there is no schedule, elevation or section. Area: BLOCKED. Material: NOT_ESTABLISHED, as there is no evidence in the plan. Neither has an entrance word in or within 3 m of it. |
| Lift doors are excluded from door quantities and areas | **Satisfied by accident; not tested.** | No space carries a lift word, so no door is classed LIFT. A stacked 1.8 × 1.8 m shaft (the same footprint on 3 floors) has a 1.0 m opening with drawn head lines on every floor. These 3 openings are ordinary PASSAGE openings. They are not in any door total, but they are in the passage count and in the reveal / threshold ledger records (DR-06, F-22). |
| The lift shaft is excluded from room finishes | **Satisfied (by inference).** | The 3 shaft spaces are EXCLUDED in the ledger. They are typed "shaft / duct, review" from the stacked footprint, not from lift evidence. |
| A double-leaf door is one door set | **Satisfied.** | The 2.0 m double door is one element with 2 leaves. The released totals count elements (15 / 15, 3 / 3). |
| Dimensions first; a fallback is ASSUMED, never confirmed | **Satisfied (nothing assumed).** | There is no door schedule, and no authored dimension lies at any door (0 door dimension matches). No fallback height is used, so every height and area is BLOCKED. |
| No promotion on dimension agreement alone | **Satisfied.** | The promotion switch is off. The 6 provisional doors stay provisional. |

## 3. Issues (review findings)

| Id | Severity | Issue | Recommendation (not implemented) |
|---|---|---|---|
| DR-01 | Owner decision | The main entrance is not named, and its material is not established. | The owner names it (or names the evidence that identifies it). Its height comes from the schedule or elevation. |
| DR-02 | **Engineering defect (F-18)** | A released door carries an open width REVIEW: opening 0.9 m against a 1.0 m frame. Its 0.9 m is in the released aluminium width. | An open width REVIEW withholds the door until a schedule, a dimension or the owner settles the width. |
| DR-03 | **Classification risk (F-20)** | A door into an unlabelled space that opens to the outside without a door is classed internal PVC. | Such a door becomes a class REVIEW until the space is typed. The owner confirms whether that space is inside the envelope. |
| DR-04 | **Engineering defect (F-19)** | The class-unresolved door is withheld with no finding and no UNRESOLVED entry. It appears only in the provisional schedule. | Emit a DOOR_CLASS_UNRESOLVED REVIEW finding per element. |
| DR-05 | Evidence gap | The 6 provisional doors have only a leaf closure: no band opening and no authored dimension. | Do not promote them. They are confirmed by an independent opening (jambs or a wall gap) plus topology (two typed sides), or by a schedule. |
| DR-06 | **Coverage gap (F-22)** | Lift entrances are found only from a lift word. On this plan the lift exclusion is untested. | A stacked-shaft opening becomes a LIFT_ENTRANCE candidate (excluded, REVIEW) and is confirmed by a label, a lift schedule or the owner. |
| DR-07 | Missing source | No door height is available on any floor (18 released doors). | Door schedule or elevations. Alternatively, an owner-authorised project height recorded as ASSUMED. It would never enter confirmed areas. |

## 4. What is ready for the blind test

**Testable now:**
- Door counts by class, per floor.
- Structural opening widths.
- Double-leaf handling.
- Withholding of main-entrance candidates.

**Not testable** (all blocked by source): door heights and areas, and the main-entrance material.

**Lift-door exclusion:** testable only if the blind drawing labels its lift.

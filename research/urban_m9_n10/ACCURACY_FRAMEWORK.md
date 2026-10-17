# Accuracy framework (Phase N10) — proposal, UNAPPROVED

This carries `research/urban_m9_p2b9/ACCEPTANCE_FRAMEWORK_PROPOSAL.md` forward, with the measures A1 – A11 as written there. It changes nothing in the sealed URBAN_BLIND_V2 protocol, and **no blind run was made**.

## 1. The three levels a measure is computed at

| Level | Unit | Measures | Tolerance (proposed) |
|---|---|---|---|
| **Item** | one BOQ line (item code × location × element) | A3 per-item error; A5 false positive; A6 missing; A7 duplicate; A8 provenance | m² 0.10 / 2 %; lm 0.05 / 2 %; m³ 0.01 / 2 %; counts exact |
| **Room** | one space | A2 floor area and perimeter; every finish of the room present or reasoned | as A2 |
| **Category** | a family (floor finish, plaster, paint, skirting, wall tile, waterproofing, doors, windows, masonry, facade, formwork …) | A1 completeness; A4 category total; A9 assumption rate; A10 RFI rate; A11 materiality | as A4 |

## 2. What each N10 quantity can be scored against today

| Quantity | Evidence a score would use | Scoreable now? |
|---|---|---|
| curved-opening rooms (floor, finishes) | hand truth (synthetic), INDEPENDENT_FACE on the reference plan | synthetic yes; real: one room, verified |
| masonry panel / volume | hand truth; no independent reader | synthetic only |
| facade run | hand truth; INDEPENDENT_OUTLINE | synthetic yes; real: 1 floor of 3 verified, 1 contradicted (D-N10-01), 1 not established |
| facade area | hand truth | synthetic only (real plans held) |
| formwork faces | the synthetic villa's design spec; conservation with route G | synthetic only; conditional faces need the owner's convention first |
| excavation | hand truth | synthetic only (real plans held) |

## 3. Claim rule (unchanged, restated)

A category's accuracy may be claimed only after **all** of these:

1. the category's rules are OWNER_APPROVED;
2. a sealed blind evaluation of at least one unseen villa has been run under the URBAN_BLIND_V2 protocol;
3. the category passes A1 – A8 at its bars.

**Today no category meets this rule.** Every N10 rule is REQUIRES_CONFIRMATION, and no blind run was made. The 95 % accuracy target is therefore **not achieved and not claimed**.

## 4. Readiness levels

The levels are kept distinct:

| Level | Meaning | N10 state |
|---|---|---|
| EXPERIMENTAL | implemented, tested on synthetic fixtures | formwork, excavation, rebar audit (separate tool) |
| INTERNALLY VALIDATED | synthetic hand truth + independent reader on the real plan + V1 – V2.8 byte identity | curved openings; facade run (partly: 1 floor verified) |
| READY FOR BLIND | owner-approved rules, the measures above computable, no open defect in the category | none |
| PRODUCTION | a passed blind evaluation and owner release | none (not authorised in this phase) |

## 5. Proposed additions for N10 categories

- **Masonry.** Score the panel *geometry* (area by thickness family) separately from the *material* (MAS.BLOCK). A missing material is an A10 RFI, not an A3 error.
- **Facade.** Score the run (lm) and the area (m²) separately. A second outline reported as an RFI counts as A6 "reasoned", never as missing.
- **Formwork.** Score only after the owner fixes FW-D1 / FW-D2. Until then each alternative is scored apart, and the score is never a sum of alternatives.

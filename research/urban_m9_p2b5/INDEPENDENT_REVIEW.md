# Independent engineering review of Phase 2B-5 (Stage H)

This review challenges the program's own work. Each objection has a severity (H / M / L), says what in the work
answers it, and gives what remains.

## 1. Independence of the evidence

| # | objection | answer | remains | sev |
|---|---|---|---|---|
| 1 | The benchmark plans come from `tools/arch_synth`, the generator the engine was developed against, so the benchmark mostly proves the engine reads its own conventions. | The truth is hand literals, never a reader value. The encoding cases (nested and non-uniform blocks, metres, polylines, Arabic, DIMENSIONs, window blocks, XREF) and B10 (own primitives) break the generator's conventions. | Real drawings break conventions in ways no fixture anticipates (nibs inside gaps, merged strips at splays). Only real-room verification and the blind evaluation measure that. | H |
| 2 | The independent DXF reader shares concepts with the engine (gap closure between collinear faces), so their errors may be correlated. | Both are scored against hand truth, not against each other. On the real plan the independent reader *contradicted* the engine's first D-V26-06 version, and the contradiction was right: independent enough to matter. | A shared conceptual blind spot (e.g. a gap drawn without jambs on both faces) would not be caught. | M |
| 3 | The encoding round trip (C01) is checked with ezdxf, which the readers also use. | An ezdxf transform error would move every reader away from the hand truth, so it cannot go unseen. | - | L |
| 4 | Stage C pairs the independent room with the engine room through the engine. | Disclosed. The pairing only chooses which room to compare; it supplies no value. | - | L |

## 2. The D-V26-06 correction

| # | objection | answer | remains | sev |
|---|---|---|---|---|
| 5 | The limits (hinge 0.45 m, leaf 60 %, 2 degrees, 50 mm) were set after seeing three real doors: overfitting. | The rule only *holds* doors; it never releases them. On the real plan only the closure test changed anything, on one door whose geometry was checked independently. The review-fit limits changed nothing there and are tested only synthetically. | The limits are unvalidated on other drawings. A second real plan is needed before trusting the review fit. | M |
| 6 | A held door still moves lines: its strip from porcelain to a marble threshold, and door jamb plaster is added. | Those lines are PROVISIONAL. The doorway waterproofing piece of a held door is now PROVISIONAL too, a change made after this review raised it (`arch_measure.py`, tested). | Plaster / skirting / upturn deductions follow the DOOR kind (door height instead of a full-height passage), with their usual states. | L |
| 7 | The first version merged two real rooms. What else might a rule like this do? | Fixed with the CLOSED-swing guard and recorded (E-01). V1 - V2.5 are byte-identical, and V2.6 changes exactly one opening on the real plan. | Any further door rule needs the same real-plan diff before commit. | M |

## 3. Calculations and claims

| # | objection | answer | remains | sev |
|---|---|---|---|---|
| 8 | "Exact" readers: exact to what? | IoU at least 0.9999, area and perimeter within 0.01 %, assertions in `test_bench.py`. The arc case is exact to the 0.5 mm flattening (−0.008 %). | - | L |
| 9 | Raster bounds were set after seeing results (2 % perimeter on the arc; the B09 scan exception). | Each exception is named and asserted as found, not hidden in a loose bound. The straight-wall bounds (1 %) predate the new cases. | Vision is never a BOQ basis, so a vision bound is a characterisation, not an acceptance criterion. | L |
| 10 | Stage C reported 70 / 58 / 12. | Corrected to 66 / 55 / 11 (C-01): the rows were right and the total line was wrong. Caught by re-running the comparison script, not by reading the page. | Totals in tables should be generated, not typed: the research generators do this; hand pages do not. | M |
| 11 | D-D2 real-plan exposure (4 rooms; ~0.7 % of the wall run) rests on an arc-length sum and a face-vs-polygon area difference. | Both are aggregates from raw entities and engine outputs, stated as exposure, not as error. | The per-room effect on tile layouts was not measured. | L |
| 12 | "Did vision help?" could be read as "vision is useless". | It helps as a cross-check (vector PDF exact) and as a review tool. It found none of the engine's defects; CAD-level checks did. | - | L |

## 4. Architecture

| # | objection | answer | remains | sev |
|---|---|---|---|---|
| 13 | V2.6 now carries two unrelated corrections (waterproofing installation; door reconciliation) under one method name. | Each correction is listed in RUN_RULES (`D-V26-01 … 06`), and the door rule's limits are recorded. | V2.6 should be frozen as a whole before release; later steps belong in V2.7. | M |
| 14 | `arch_rooms.spaces` grows flag parameters (geom, release_safety, door_review). | Each flag is opt-in and tested. Frozen methods never pass them. | The flag surface is growing. A method object carrying the flags would be cleaner (refactor, not now). | L |
| 15 | The hybrid layer exists only in the test tree. | Intended: Part 6.4 forbids unverified vision in the production BOQ. | If adopted, it needs its own module, provenance store and owner sign-off. | L |

## 5. Test evidence

| # | objection | answer | remains | sev |
|---|---|---|---|---|
| 16 | Characterisation tests ("asserted as found") pass while the defect exists. | They make the defect visible and quantified; each states the truth next to the found value and must be rewritten when the defect is fixed. | They are not acceptance tests. The roadmap item that fixes each one flips it. | L |
| 17 | The full suite has 345 failures and 32 errors before and after. | They are the documented baseline (missing private datasets and environment limits). The comparison is by test identity, and new failures are reported separately (`TEST_RUN.md`). | The baseline failures hide nothing new only as long as the identity comparison is run each time. | M |
| 18 | No accuracy figure is claimed. | Correct, and deliberate: the formal blind evaluation was not started (instruction). | It is the next gate. | H |

**Overall.** The changes are conservative and traceable, and they protect the frozen methods. The two high-severity
items are not defects of the work: the synthetic-convention limitation (1) and the absence of a blind evaluation
(18) are why no accuracy is claimed.

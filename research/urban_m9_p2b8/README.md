# Phase 2B-8: V2.7 acceptance hardening and second-villa readiness

**What this phase delivers.**
- **A new opt-in method:** ARCH_TAKEOFF_V2.7.1 (knowledge registry 1.3.0). V1 – V2.7 are unchanged and byte-identical.
- **An independent drawing reader** that imports no engine module, and a change verifier built on it.
- **A sealed blind-benchmark protocol** for the second villa.

**What it does not claim.** No accuracy figure, no production freeze, no green full suite.

## Documents

| File | Deliverable |
|---|---|
| `ACCEPTANCE_HARDENING_REPORT.md` | the acceptance-hardening report: sections 1 – 6 of the Phase 2B-8 instruction |
| `OWNER_DECISIONS.md` | the updated owner decision register |
| `REVIEW_SPACE_BOQ_DEMONSTRATION.md` | the corrected REVIEW-space BOQ demonstration: synthetic hand truth plus reference-plan aggregates |
| `DOOR_STANDARD_RECONCILIATION_DEMONSTRATION.md` | the door-standard reconciliation demonstration, including the 0.80 m door |
| `REMAINING_DEFECT_REGISTER.md` | the remaining defect register |
| `SECOND_VILLA_READINESS.md` | the second-villa benchmark readiness report |
| `CAPABILITY_COVERAGE_MATRIX.md` | the updated capability coverage matrix |
| `NEXT_PHASE_PLAN.md` | the recommended next implementation phase |
| `TEST_EVIDENCE.md` | byte identity, targeted suites, freeze verification, the full-suite comparison |
| `CHATGPT_REVIEW_BRIEF.md` | what worked, what did not, recommendations, questions |
| `benchmark/` | URBAN_BLIND_V2: protocol (`.json`, `.md`), scorer, reference template, `SEAL.json` |

## Code (in the repository)

| Path | What |
|---|---|
| `tools/urban_boq_m9.py` (`_arch_v271`, `_review_release`, `_quantity_classes`, `_release_report`) | the V2.7.1 method: review scenarios, invariant release, release report |
| `engine/source/door_standards.py` (`reconciliation_v271`) | the door-standard reconciliation |
| `engine/source/arch_v27.py` (`wc_shapes_v271`, `wet_evidence`, `attach_provenance`) | WC profile 1.3.0, basin linework by insert path, strip provenance |
| `engine/source/arch_rooms.py`, `robust_geometry.py`, `arch_walls.py` | turned columns as jambs and wall cuts; scenario typing |
| `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.3.0.json`, `tools/kb_build_1_3.py` | registry 1.3.0: UP-REVIEW-001, UP-QTY-STATUS-001, UP-COL-ORIENT-001; UP-WET-002 and UP-DOOR-OPEN-003 amended |
| `tools/indep_reader.py` | the independent reader (ezdxf + shapely, no engine import) |
| `tools/arch_change_verify.py` | change attribution with independent verification |
| `tests/m9_p2b8/` | 6 test files (review release 18, doors 7, recognition 37, attribution 7, independent reader 15, benchmark 14) and 2 helpers |

## Privacy

- **The reference plan.** Results appear only as aggregates, with no room ids and no private layer names. The verification runs on it were private.
- **The second villa.** None exists. Nothing about one is committed or exported.
- **No secrets.** No drawing, render, workbook or secret is in this package.

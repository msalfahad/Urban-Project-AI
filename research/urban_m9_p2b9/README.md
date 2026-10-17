# Phase 2B-9 — architectural BOQ completion, drawing-derived heights, wall geometry, independent proof

Method: **ARCH_TAKEOFF_V2.8** (opt-in; registry 1.4.0). V1 to V2.7.1 are unchanged, byte for byte (see
`REGRESSION_AND_FROZEN_EVIDENCE.md`). Nothing here is a production freeze, and no blind evaluation has been run.
No accuracy figure is claimed: the long-term 95 % target needs independent blind tests that have not started.

| # | Deliverable | File |
|---|---|---|
| 1 | Executive review (incl. the Phase 2B-8 review) | `EXECUTIVE_REVIEW.md` |
| 2 | Heights proof: evidence hierarchy, sources, missing evidence | `HEIGHTS_PROOF.md` |
| 3 | Wall, opening and reveal proofs (worked example 1) | `WALL_OPENING_REVEAL_PROOFS.md` |
| 4 | Window / opening schedule method | `WINDOW_SCHEDULE_METHOD.md` |
| 5 | Wet-room example (worked example 2) | `WET_ROOM_EXAMPLE.md` |
| 6 | Stub and curved-wall proofs (worked examples 3 and 4) | `STUB_AND_CURVED_WALL_PROOFS.md` |
| 7 | Updated capability coverage matrix | `CAPABILITY_COVERAGE_MATRIX.md` |
| 8 | Independent verification results | `INDEPENDENT_VERIFICATION_RESULTS.md` |
| 9 | Reference-plan BOQ before / after (V2.7.1 → V2.8) | `REF_BOQ_BEFORE_AFTER.md` |
| 10 | Regression and frozen-method evidence, full suite | `REGRESSION_AND_FROZEN_EVIDENCE.md` |
| 11 | Owner / project rule sheet | `PROJECT_RULE_SHEET.md` |
| 12 | Defect and unresolved-evidence register (incl. the reference plan's missing heights) | `DEFECT_AND_EVIDENCE_REGISTER.md` |
| 13 | Second-villa readiness | `SECOND_VILLA_READINESS.md` |
| 14 | Next-phase plan | `NEXT_PHASE_PLAN.md` |
| 15 | Brief for ChatGPT (what worked, what did not, recommendations) | `CHATGPT_BRIEF.md` |
| 16 | Privacy-clean ZIP with SHA-256 manifest | built from this folder, `tests/m9_p2b9` and the code diff |
| — | Acceptance framework proposal (unapproved) | `ACCEPTANCE_FRAMEWORK_PROPOSAL.md` |
| — | BOQ capability gap audit | `BOQ_CAPABILITY_GAP_AUDIT.md` |

Every important number is laid out in the form
**drawing evidence → measurement formula → hand calculation → engine result → difference → verification status**.

The hand truth is in `tests/m9_p2b9/p2b9_truth.py`. It is arithmetic on the fixture coordinates, never engine output.
Tests: `tests/m9_p2b9` (heights 15, openings 8, walls 6, wet room 2, invariance 10, independent census 5): 46 tests.

Code that changed (all opt-in, reached only by ARCH_TAKEOFF_V2.8 or by the audit tools):

- `engine/source/arch_v28.py` (new)
- `engine/source/arch_measure.py`, `release_safety.py`, `door_model.py`: new optional arguments; the defaults keep
  every earlier path
- `engine/source/knowledge.py`, `arch_completeness.py`
- `tools/urban_boq_m9.py` (the method and its outputs)
- `tools/indep_reader.py` and `tools/arch_change_verify.py`: the audit side
- `tools/kb_build_1_4.py`, `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.4.0.json`

New V2.8 outputs:

- `HEIGHT_EVIDENCE.json`
- `MISSING_HEIGHT_EVIDENCE.json`
- `OPENING_SCHEDULE.json` / `.csv`
- `WINDOW_REVEALS.json`
- `WALL_GEOMETRY.json`

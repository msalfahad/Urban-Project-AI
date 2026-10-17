# Phase 2B-0: release safety and blind-test readiness (2026-10-14)

**Start with `P2B0_IMPLEMENTATION_REPORT.md`.**

**Method:**
- `ARCH_TAKEOFF_V2.2` is opt-in. Pass it with `--method ARCH_TAKEOFF_V2.2`.
- V1, V2 and V2.1 are byte-identical to `981ef5f`.
- The work stops at the release-safety acceptance gate. The blind round and Phase 2B-1 have not started.

**Files:**

| File | What it is |
|---|---|
| `P2B0_IMPLEMENTATION_REPORT.md` | (1) the implementation report: design, defects, stop conditions, what worked / failed, limitations |
| `DEFECT_REGISTER_BEFORE_AFTER.csv` | (2) defect-by-defect before / after register, P2B0-01 … P2B0-12 |
| `TEST_RESULTS_AND_INTEGRITY.md` | (3) test results and regression classification; (4) frozen-version integrity |
| `BLIND_READINESS_CHECKLIST.md` | (5) the blind-test readiness checklist |
| `OWNER_DECISIONS.md` | (6) remaining owner decisions, OD-1 … OD-17 |
| `NEXT_PHASE_RECOMMENDATIONS.md` | (7) prioritized recommendations, objections, reasons to delay the blind round |
| `FACTS_TEMPLATE_HEIGHTS.json` | the heights facts template for Mode A; every value is null |
| `BLIND_READINESS_RECORD.json`, `make_readiness_record.py` | sha256 freeze of the scorer, dry run, protocol and template; code-tree digest; environment; test configuration |

**Also changed:**
- `engine/source/release_safety.py` (new).
- `engine/source/{arch_rooms,arch_measure,door_model,surface_ledger}.py` and `tools/urban_boq_m9.py`, all behind the V2.2 switches.
- `research/urban_m9_p2a_acceptance/blind_test/`: amendment A1, window positions in the scorer, and the V2.2 dry run.
- `tests/m9_p2b0/`.
- Findings F-25 … F-32, appended to `research/freeze_integrity/ENGINEERING_FINDINGS.jsonl`.

**Privacy:**
- Only aggregate values appear here.
- The per-door table, line-level diffs and instrumented runs of the reference plan stay outside the repository.
- Reference-plan wall-finish counts come from synthetic test heights, and are not project quantities.

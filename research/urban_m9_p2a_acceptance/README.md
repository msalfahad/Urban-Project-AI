# Phase 2A acceptance review (2026-10-14)

**Start with `ACCEPTANCE_REVIEW.md`.** It holds:
- the verdict;
- the audit of every changed quantity;
- the door, ledger, blind-test and roadmap summaries;
- the required final response (sections 1–7).

**Supporting files:**
- `BEFORE_AFTER_DECISION_MATRIX.csv`: one row per changed quantity (BA-01 … BA-16).
- `DOOR_READINESS_REPORT.md`: door readiness under the owner door rules.
- `SURFACE_ELIGIBILITY_RFI_REGISTER.csv`: the 135 + 5 ledger records as distinct questions.
- `blind_test/`: the pre-registered blind test.
  - `BLIND_TEST_PROTOCOL.md`;
  - the scorer, `blind_score.py`, which is stdlib-only;
  - its dry run, `dry_run.py`, with `DRY_RUN_RESULT.json`;
  - the test that pins the scorer, `tests/m9_p2a/test_p2a_blind_scoring.py`.
- `GAP_PRIORITY.csv`, `NEXT_STAGE_ROADMAP.md`: the ranked gaps and the proposed next phase. It has not started and needs approval.
- `TEST_RESULTS_AND_WEAKNESSES.md`: the test runs of this review and the open weaknesses.

**New findings:** F-17 … F-24, appended to `research/freeze_integrity/ENGINEERING_FINDINGS.jsonl`.

**Privacy:**
- The reference-plan evidence (per-door rows, line diffs, instrumented runs) stays outside the repository.
- Only aggregate values and generic descriptions are published here.

**Reproduce the scorer dry run:**

```
python3 -I research/urban_m9_p2a_acceptance/blind_test/dry_run.py
python3 -m pytest tests/m9_p2a/test_p2a_blind_scoring.py
```

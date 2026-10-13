# Freeze integrity (P2-00 Stage 1)

**Add-only verification.** Stage 1 changes no production code, historical BOQ, route G, benchmark file, frozen output or frozen manifest. Read `STAGE1_REPORT.md` first.

## Files

| File | What it is |
|---|---|
| `ENVIRONMENT_LOCK.json` | The reference environment (owner decision D5): CPython 3.11.17 and the exact installed package set (`pip freeze --all`). A byte-identity claim is valid only inside it. |
| `FREEZE_BASELINE_INDEX.jsonl` | The immutable baseline, append-only and hash-chained. It records the sha256 of every freeze manifest, of every non-code research file a manifest pins, of the V1 synthetic snapshot, and of the owner rule files, as committed. The test `tests/zz_freeze_integrity` fails in any session in which one of them differs. |
| `ERRATA.jsonl` | Append-only. Known defects of released methods and frozen results, with their effect. Frozen files are never edited; they are only recorded here. |
| `ENGINEERING_FINDINGS.jsonl` | Append-only. Software and harness findings, with their mitigation. |
| `PROPOSED_STAGE2.md` | The Stage 2 proposal, **not applied**: no change to any pinned file is recommended. |
| `PROPOSED_STAGE2_ALTERNATIVE.diff` | The exact alternative diff, **not applied**. |
| `stage2_threshold_shift_check.py` | The evidence that the robust predicate needs no edit to `opening_census.py`. |
| `PHASE2A_ACCEPTANCE_ADDENDUM.csv` | The owner's additional requirements 1–6, written as acceptance tests. |

## Commands

Run them with the reference interpreter.

```
python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl   # immutable baseline
python3 -I tools/freeze_verify.py env --lock research/freeze_integrity/ENVIRONMENT_LOCK.json            # environment
python3 -I tools/freeze_verify.py closure                                                               # unpinned imports
python3 -I tools/freeze_verify.py rebuild --out <dir outside the repo> \
        --lock research/freeze_integrity/ENVIRONMENT_LOCK.json [--patch FILE --repin] [--arch-baseline CFG]
```

- **`rebuild`** never writes into the repository:
  - it adds a disposable git worktree of the ref and links the gitignored inputs;
  - it runs every selected test alone, from a pristine tree;
  - it compares every file a test rewrote with its committed bytes, raw and after the declared masks (`MASK_RULES` in `tools/freeze_verify.py`);
  - it removes the worktree.
- **Verdicts:**

| Verdict | Meaning |
|---|---|
| `BYTE_IDENTICAL` | the test passed and rewrote nothing |
| `BEHAVIOUR_IDENTICAL_PROVENANCE_DIFFERS` | only masked provenance fields differ (only allowed with `--patch`) |
| `BEHAVIOUR_CHANGED` | a value differs after masking |
| `REFUSED_BY_SOURCE_PIN` | a builder's own pin check refused the change |
| `BUILD_FAILED` | the builder failed for another reason |
| `ENV_MISSING_MODULE` | a module the test needs is not installed |
| `SKIPPED` | the test was skipped |
| `TEST_FAILED_NO_OUTPUT_CHANGE` | the test failed but rewrote nothing |

- **Overall result:** `PASS` only inside the lock, with the repository unchanged, at least one test run, and every verdict allowed. Outside the lock a clean run reports `NOT_A_PASS_OUTSIDE_THE_LOCKED_ENVIRONMENT`.
- **`--arch-baseline`** re-runs the architectural CLI on a drawing and compares its outputs with recorded hashes. The config can name a client drawing, so it is kept outside the repository.

## Adding a new freeze

1. Commit it.
2. Append it to the index: `python3 -I tools/freeze_verify.py index --write research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl`.

The command refuses if an already-indexed entry no longer matches its committed bytes. A changed baseline is a defect to record in `ERRATA.jsonl`, never a reason to re-index.

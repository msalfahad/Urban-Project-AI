# Test evidence and frozen-version verification (Phase 2B-7)

**What the tests show, and what they do not.** Passing tests prove geometry, arithmetic and bookkeeping against
hand-derived or independent truth. They are **not** a measurement of real-world BOQ accuracy: the formal blind
evaluation has not started, as instructed. The real-world evidence is one plan: five rooms read independently, plus
the census and the audit (`INDEPENDENT_EVIDENCE.md`).

## 1. Frozen methods: V1 – V2.6 byte-identical

The private snapshot covers the synthetic villa, its mirror and the private reference plan, in Mode U and Mode A
(synthetic heights), for every method V1 – V2.6. It was run from a copy of the final tree and compared with the
Phase 2B-6 final snapshot.

| method | files | differ |
|---|---|---|
| ARCH_TAKEOFF_V1 | 46 | 0 |
| ARCH_TAKEOFF_V2 | 52 | 0 |
| ARCH_TAKEOFF_V2.1 | 70 | 0 |
| ARCH_TAKEOFF_V2.2 | 140 | 0 |
| ARCH_TAKEOFF_V2.3 | 176 | 0 |
| ARCH_TAKEOFF_V2.4 | 236 | 0 |
| ARCH_TAKEOFF_V2.5 | 248 | 0 |
| ARCH_TAKEOFF_V2.6 | 272 | 0 |
| **total** | **1240** | **0**; 39 runs, all exit 0 |

The same check passed after every engine change of this phase:

- the plumbing;
- the core corrections;
- the provenance;
- the final tree.

| other check | result |
|---|---|
| `tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | 0 frozen artefacts differing |
| `tools/freeze_verify.py env` / `closure` | exit 0 |
| `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json` | unchanged (1.2.0 is a new file, built from 1.1.0 by `tools/kb_build_1_2.py`) |
| `rules/` | unchanged |
| V2.7 on the villa, its mirror (Mode U and A) and the reference plan | all 6 runs exit 0 |

## 2. New tests (`tests/m9_p2b7`)

| file | tests | what it pins |
|---|---|---|
| `test_p2b7_doors.py` | 18 | jamb span on CROSSING to hand truth; 4 wider-opening variants and 3 gap-is-the-door variants unchanged from V2.6; 8 placements invariant; the seven-reading opening record |
| `test_p2b7_roles.py` | 26 | exploded / block single doors; lookalikes OTHER; mixed layer refused; drains never columns; four-line and turned columns; turned villa; free-standing column refused; **aligned column rows** to hand truth and invariant |
| `test_p2b7_arcs.py` | 9 | arc-following polygon; arc typed WALL in waterproofing (no false termination); curved band with three bases; difference from V2.6 = the band; 5 placements invariant |
| `test_p2b7_wet.py` | 13 | basin alone REVIEW; basin + WC in three encodings; one shape alone REVIEW; adversaries; Arabic word; 4 placements invariant; **the doorway of a review space takes no dry finish** |
| `test_p2b7_unproven.py` | 65 + 2 xfail | the five Section 3 proposals against the independent reader `p2b7_indep.py` or hand truth (see `V27_IMPLEMENTATION_REPORT.md`); the two strict xfails are the documented WC-shape errors |
| `test_p2b7_explained.py` | 11 | every V2.6 → V2.7 difference on 10 drawings attributed to its own record (roles declared, so no floor-wide cover); an emptied log makes every difference UNEXPLAINED |
| `test_p2b7_audit.py` | 5 | the 2B-6 audit findings A01 / A05 / A07 / A09 are gone under V2.7; A03 becomes REVIEW naming V2.7's refusal |
| **total** | **147** | **145 passed, 2 xfailed (strict), 0 failed** (run on the final tree, 5 min 47 s) |

**Earlier phases' targeted suites, on the final tree:** `tests/m9_p2b6`, `tests/m9_p2b5`, `tests/m9_p2b5_bench` and
`tests/m9_kb`: **283 passed, 0 failed**. The Phase 2B-6 as-found defect tests still assert the V2.6 behaviour.

## 3. Full suite against the Phase 2B-6 end, test by test

Run in a clean clone of `b933a16` (the V2.7 code commit), with its own `--basetemp`, in 26 min 54 s. The clone links
the git-ignored private drawings folder `data/inputs` exactly as the Phase 2B-6 baseline clone did. pytest exits 1
because of the known private-data failures.

| run | tests | passed | failed | errors | skipped | xfailed |
|---|---|---|---|---|---|---|
| `566ee88` (Phase 2B-6 end) | 9 040 | 8 401 | 345 | 32 | 160 | 102 |
| `b933a16` (Phase 2B-7) | 9 187 | 8 544 | 346 | 32 | 161 | 104 |

The JUnit results were compared **test by test, by identity**:

| comparison | count |
|---|---|
| new tests | 147: the tests of `tests/m9_p2b7`, 145 passed and 2 strict xfails |
| removed tests | 0 |
| passed → failed | 1: `tests/test_perf_guard.py::test_quadrupling_the_pixels_does_not_multiply_the_work_by_the_pixels` (below) |
| failed → passed | 0 |
| passed → skipped | 1: `tests/m1_usable_boq/test_m1_package.py::test_workbook_if_present` (below) |
| new tests failing | 0 |

The 345 failures + 32 errors common to both runs are the known private-data set (git-ignored datasets and
workbooks not in the repository), as in Phase 2B-6. The full suite is **not** green, and these are never reported
as passing.

**The one passed → failed test is a wall-clock timing ratio, not a V2.7 change.**

- **What it checks:** `engine/walls.py`, which has no changed line since the Phase 2B-6 end.
- **What failed:** it times a 400 × 560 and an 800 × 1120 trace and requires the second to take under 12 times the
  first. In the full run, the small trace took 0.017 s and the large one 0.244 s (ratio 14.7).
- **Evidence it is timing, not code:**
  - The same test passed at the same commit in an earlier full run of this phase.
  - It passed 10 of 10 isolated re-runs in the clone.
  - Over 20 timed trials the ratio was 2.0 – 5.4, median 4.3.
- **Root cause:** a 17 ms baseline on a shared container. One delay in the large trace exceeds the bound. The test is
  not changed or skipped.

**The one passed → skipped test** reads a git-ignored workbook that the program's build writes. It existed in the
baseline clone and not in the fresh one.

**An earlier full run is kept for the record.** It was run in a clone without `data/inputs`, which is not comparable
with the baseline. There, 68 tests changed state; every one of them reads the private drawings, and the run had 0
failing new tests. It was repeated with the inputs linked, as above.

## 4. The reference plan (private; aggregates)

| check | V2.6 | V2.7 |
|---|---|---|
| Stage C: five independently read rooms, 66 checks | 8 failing | **0 failing** (not, by itself, success) |
| BOQ totals differing from V2.6 | - | 95, **0 unexplained** |
| curved band vs the raw-entity census | missing | equal to 1e-6 |
| run audit HIGH / MEDIUM / REVIEW / INFO | 1 / 4 / 3 / 1 | 0 / 0 / 4 / 0 |

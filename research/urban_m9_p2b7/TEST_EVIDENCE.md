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

The full suite is running in a clean clone of `b933a16`. Its test-by-test comparison with the Phase 2B-6 end
(`566ee88`) will replace this paragraph. Until then no full-suite result is claimed.

## 4. The reference plan (private; aggregates)

| check | V2.6 | V2.7 |
|---|---|---|
| Stage C: five independently read rooms, 66 checks | 8 failing | **0 failing** (not, by itself, success) |
| BOQ totals differing from V2.6 | - | 95, **0 unexplained** |
| curved band vs the raw-entity census | missing | equal to 1e-6 |
| run audit HIGH / MEDIUM / REVIEW / INFO | 1 / 4 / 3 / 1 | 0 / 0 / 4 / 0 |

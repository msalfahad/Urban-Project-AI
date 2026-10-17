# Test evidence and frozen-version verification (Phase 2B-8)

**What the tests show, and what they do not.**
- Passing tests prove geometry, arithmetic and bookkeeping against hand-derived truth or the independent reader.
- They are **not** a measurement of real-world BOQ accuracy. There is one real plan, and the blind second-villa round has not started (`SECOND_VILLA_READINESS.md`).
- **The full suite is not green.** Its known failures are kept apart from new regressions in section 4.

## 1. Frozen methods: V1 – V2.7 byte-identical

The private snapshot covers:
- the synthetic villa and its mirror;
- the private reference plan;
- Mode U, and Mode A (synthetic heights) for V2.2 and later.

Each snapshot was run from a copy of the tree. V1 – V2.6 were compared with the Phase 2B-6 final snapshot, and V2.7 with the Phase 2B-7 final V2.7 run.

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
| ARCH_TAKEOFF_V2.7 | 278 | 0 |
| **total** | **1518** | **0**; 45 runs, all exit 0 (final code `44c12e5`) |

**The same check passed at every engine change of this phase:**

| tree | state | V1 – V2.6 | V2.7 |
|---|---|---|---|
| `ef1b3bd` | Phase 2B-7 end (baseline) | 1240 / 0 differ | 278 / 0 differ |
| `ef1b3bd` + working changes | V2.7.1 plumbing, before the first commit | 1240 / 0 | 278 / 0 |
| `e4a10d5` + working changes | quantity classes, reader robustness | 1240 / 0 | 278 / 0 |
| `44c12e5` | final code | 1240 / 0 | 278 / 0 |

`b2777b1` (the phase head) changes only `research/urban_m9_p2b8/README.md`.

| other check (at the phase head) | result |
|---|---|
| `tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | 0 frozen artefacts differing (exit 0) |
| `tools/freeze_verify.py env` / `closure` | exit 0 / exit 0 |
| `tools/kb_build_1_3.py --check`, `tools/kb_build_1_2.py --check`, `tools/kb_build.py --check` | registry 1.3.0, 1.2.0 and the base registry up to date |
| `knowledge/` | the 1.0 – 1.2.0 files unchanged; 1.3.0 is a new file, built by `tools/kb_build_1_3.py` |
| `rules/` | unchanged since the Phase 2B-7 end |
| benchmark seal (`research/urban_m9_p2b8/benchmark/SEAL.json`) | `verify_seal()` returns no finding: the four sealed files match |
| V2.7.1 on the villa, its mirror and the reference plan (Modes U and A) | 6 runs, all exit 0; output identical to the run the reports were written from |

## 2. New tests (`tests/m9_p2b8`)

| file | tests | what it pins |
|---|---|---|
| `test_p2b8_review_release.py` | 18 | **REVIEW spaces.** The basin lobby releases its ceiling and nothing else. The wall face is confirmed geometry, not a BOQ line. Every quantity sits in exactly one class. A space with no plausible set is NOT_ESTABLISHABLE. Hand values for geometry, WET_SCOPE and DRY_SCOPE. Equal quantities under a different system or rule are not released. Scenarios are never added to the main BOQ. Every line is reported exactly once. Without heights the ceiling is still released. A WC shape alone gives a review space with scenarios. A plain space releases nothing. Invariant under rot30 / mirror / metres; deterministic; V2.7 unchanged |
| `test_p2b8_doors.py` | 7 | **Door reconciliation.** Every value of the bathroom door is kept apart; its proposed enlargement and review. The CAD geometry is never changed to meet the minimum. A gap-is-the-door case needs a cut beyond the drawn opening. A compliant door needs no review. A main entrance has no ordinary minimum. The owner minimum is a conditional scenario, never in the main BOQ |
| `test_p2b8_recognition.py` | 36 + 1 strict xfail | **Recognition.** WC evidence to a truth table; the V2.7 as-found behaviour. A round bowl corroborates like an elliptical one, invariant under placement. Weak resemblances name their failing test. Basin block linework is the basin. A turned column is a jamb and interrupts the wall; the V2.7 as-found behaviour. Every measured line names its entities, or says why not. **The strict xfail is L-P8-01**: a WC-sized chair at a wall is still read as a WC |
| `test_p2b8_attribution.py` | 7 | **Attribution.** A door narrowing is verified by an independent takeoff, a curved band by the arc census, a review release by an independent face, wet evidence by an independent fixture census. A perturbed quantity is CONTRADICTED. An emptied log makes every difference UNEXPLAINED. A layer-role record covers only its own entities |
| `test_p2b8_indep_reader.py` | 15 | **The independent reader**, against hand truth. Door-plan faces; the lobby face and fixture census. Loose sanitary linework is counted, not named; an anonymous block names nothing. Opening widths, and openings on a face. A curved room and the arc census; short curved stubs listed apart. Faces invariant; layer 0 takes the insert's layer; roles from layer names. **The reader imports no engine module** |
| `test_p2b8_benchmark.py` | 14 | **URBAN_BLIND_V2.** The protocol is sealed and complete, and a changed protocol is refused. Scoring a hand reference. UNSUPPORTED is reported, never zero. A room the engine misses is SILENT, not zero. Acceptance is PROPOSED only. A review space answers conditionally. A reference that is not independent is refused (5 cases), as is one repeating the engine's digits. Commitment and run checks |
| **total** | **98** | **97 passed, 1 xfailed (strict), 0 failed**, on the final code with its own `--basetemp` |

**Earlier phases' targeted suites, at the phase head:**

| suite | result |
|---|---|
| `tests/m9_p2b7` (V2.7) | 145 passed, 2 xfailed (strict: the documented V2.7 WC-shape errors), 0 failed (5 min 47 s) |
| `tests/m9_kb` (knowledge registries) | 78 passed, 0 failed |

`tests/m9_p2b6`, `tests/m9_p2b5` and `tests/m9_p2b5_bench` ran inside the full suite (section 4).

**One test session exited 1 during the phase, and it was not a failure.**
- The determinism guard reported that the session had written to the truth roots.
- The write was mine: I edited `tests/m9_p2b8/test_p2b8_benchmark.py` while the session was running.
- The session was repeated on an unchanged tree, with the result above.

## 3. The reference plan: independent verification (private run; aggregates)

The verifier is `tools/arch_change_verify.py`. It reads the drawing with `tools/indep_reader.py`, which uses ezdxf and shapely and imports no engine module. The layer roles were declared from the reader's own layer census, not from the engine. The verifier was re-run on the phase head's V2.7.1 output, and the result is identical to the run the reports quote.

### V2.6 → V2.7.1 (Mode A): 55 differences

| status | count | how |
|---|---|---|
| VERIFIED | 32 | independent fixture census 25, independent takeoff 5, independent face 1, independent arc census 1 |
| EXPLAINED_UNVERIFIED | 23 | the space is bounded by a line of a non-wall layer 13; a gap without a door or window symbol 4; no independent check for the item 3; window sill not in the drawing 2; no measured value after 1 |
| CONTRADICTED | 0 | |
| UNEXPLAINED | 0 | |

A difference can be covered by more than one record kind, so the per-kind counts below add up to more than 55.

| record kind | verified | explained, unverified |
|---|---|---|
| WET_EVIDENCE | 28 | 13 |
| ARC_POLYGON | 13 | 0 |
| DOOR_OPENING | 3 | 10 |
| CURVED_WALL_BAND | 1 | 0 |

### V2.7 → V2.7.1 (Mode A): 3 differences

These are the three released review-space ceilings:
- 2 VERIFIED by the independent face;
- 1 EXPLAINED_UNVERIFIED: one side of that space is a line of a non-wall layer (D-P8-04).

The 5 V2.7 records already present in the V2.7 run are excluded, so they cannot explain a V2.7.1 change.

### The old explainer against the new verifier, on the same pair

| | old explainer (`tools/arch_v27_explain.py`) | new verifier |
|---|---|---|
| differences | 92: room ids change between runs, so a room whose id changed counts as one removal plus one addition | 55: rooms matched by polygon overlap |
| differences covered by the DOOR_OPENING record | 50: the record covered its whole floor | 13: only the locations near its own entities |
| verified against the drawing | none (an explanation only) | 32 |

### Other reference-plan checks

| check | result |
|---|---|
| room-class changes V2.7 → V2.7.1 | 0 of 38 rooms |
| room-class changes V2.6 → V2.7.1 | 3: the three hand-wash spaces (REVIEW since V2.7) |
| measured lines with no traced source entity | 0 (V2.7: 10, all ARCH.THRESHOLD, now traced to their strips) |
| Mode A lines / release report | 487 lines: 296 confirmed (196 source-derived, 100 provisional), 191 held, 0 excluded, 4 conditional sets; every line once |
| Mode U lines / release report | 476 lines: 252 confirmed, 196 held, 28 excluded, 4 conditional sets; every line once |

**The reader was corrected on the way, and each fix has its own hand-truth test.** The corrections:
- non-graphic text entities;
- Bezier arcs, now read by exact entity flattening;
- T-junction noding (snap-rounding union);
- unclosed faces (NOT_CLOSED_BY_WALL_LINES, unverified rather than contradicted);
- short curved stubs listed apart.

The two first-reading contradictions are described in `REMAINING_DEFECT_REGISTER.md`:
- 0.209947 m of curved stubs (D-P8-03);
- a floor-glazing window under skirting.

## 4. Full suite against the Phase 2B-7 end, test by test

**Setup.**
- Run in a clean clone of `e603162`, which holds every engine and test change of the phase except the last V2.7.1 reporting change.
- The clone links the git-ignored private drawings folder `data/inputs`, exactly as the Phase 2B-7 baseline clone did.
- The run had its own `--basetemp` and took 34 min 54 s.
- pytest exits 1, because of the known private-data failures.

**Not covered by this run: `44c12e5`.** It adds the wall-face states and the quantity classes to `REVIEW_SPACES.json` (V2.7.1 only), with their tests. It is covered instead by:
- the clean `tests/m9_p2b8` run on the final code (section 2);
- the V1 – V2.7 byte-identity snapshot on `44c12e5` (section 1);
- the V2.7.1 runs at the phase head.

| run | tests | passed | failed | errors | skipped | xfailed |
|---|---|---|---|---|---|---|
| `b933a16` (Phase 2B-7 baseline) | 9 187 | 8 544 | 346 | 32 | 161 | 104 |
| `e603162` (Phase 2B-8) | 9 285 | 8 642 | 345 | 32 | 161 | 105 |

The JUnit results were compared **test by test, by identity**:

| comparison | count |
|---|---|
| new tests | 98: the tests of `tests/m9_p2b8`, 97 passed and 1 strict xfail (L-P8-01) |
| removed tests | 0 |
| passed → failed | **0** |
| failed → passed | 1: `tests/test_perf_guard.py::test_quadrupling_the_pixels_does_not_multiply_the_work_by_the_pixels` (below) |
| any other state change | 0 |
| new tests failing | 0 |

**Known failures, carried forward unchanged.**
- 345 failures + 32 errors, 377 in all.
- Every one of them failed or errored in the baseline too. They are spread over 26 test modules, all of which read git-ignored private datasets and workbooks that are not in the repository.
- They are never reported as passing. **The full suite is not green.**

**The one failed → passed test is the Phase 2B-7 timing flake.**
- It is a wall-clock ratio over `engine/walls.py`, which has no changed line in this phase.
- In Phase 2B-7 it failed once in the full run and passed 10 of 10 isolated re-runs (Phase 2B-7 `TEST_EVIDENCE.md`).
- It passes here. This is not a fix: the test is unchanged, and it can fail again on a loaded container.

**No newly introduced regression was found.**

## 5. What this evidence does not show

- **No accuracy figure.** One real plan cannot show general accuracy. The blind round waits on OD-P8-01 and OD-P8-02.
- **23 of the 55 reference-plan changes are explained, not verified.** An explanation is not proof that the new quantity is correct.
- **Every wall-area line in Mode A rests on stated test heights**, not on sections (D-04).
- **The independent reader was written by the engineering side.** It is an audit aid, never the benchmark reference.

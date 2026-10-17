# Test evidence (Phase 2B-6, Part 12)

**What the tests show, and what they do not.** Passing tests prove geometry, arithmetic and bookkeeping against
hand-derived or independent truth. They are **not** a measurement of real-world BOQ accuracy: the formal blind
evaluation has not started (instruction). Real-world evidence is the five independently read real rooms (§4), and it
covers one plan.

## 1. New tests (this program)

| suite | tests | result | what it pins |
|---|---|---|---|
| `tests/m9_p2b6/test_p2b6_found_defects.py` | 14 | pass | D-P6-01 - 07 asserted **as found** next to their hand truth; 7 transformations of CROSSING under which every quantity is invariant |
| `tests/m9_p2b6/test_p2b6_run_audit.py` | 9 | pass | each audit finding (A01 - A11) on the synthetic case that shows it; no HIGH finding on correct runs; the tool's read-only safety (no byte of the run folder changes, no write into it, exit codes) |
| with `tests/m9_p2b5`, `tests/m9_p2b5_bench` (182) | **205** | **205 passed** | - |

## 2. Full suite against the program's start, test by test

| run | tests | passed | failed | errors | skipped | xfailed |
|---|---|---|---|---|---|---|
| `5dc2753` (start, reproduced tonight; identical by test identity to `b9baa7b`) | 9 017 | 8 378 | 345 | 32 | 160 | 102 |
| `566ee88` (final code commit of this program) | 9 040 | 8 401 | 345 | 32 | 160 | 102 |

The 345 failures + 32 errors are the known private-data set: 26 earlier test files whose git-ignored datasets and
workbooks are not in the repository. 375 of them are `FileNotFoundError`; the other 2 need a private inventory and a
`data/` workbook. They are not caused by this program and are never reported as passing. The full suite is **not**
called green.

### 2a. Final full suite

Run in a clean clone at `566ee88`, with its own `--basetemp`, in 22 min 24 s. pytest exits 1 because of the
private-data failures above.

The JUnit results were compared with the start run (`5dc2753`) **test by test, by identity**:

| comparison | count |
|---|---|
| tests at the start / at the end | 9 017 / 9 040 |
| new tests | 23 (all passing: the 23 tests of `tests/m9_p2b6`) |
| removed tests | 0 |
| passed → failed | 0 |
| failed → passed | 0 |
| any other state change | 0 |

So every one of the 345 failures and 32 errors is the **same test** as at the start, failing for the same
private-data reason. No existing test changed state. The full suite is **not** green, and this program does not
claim it is.

The commit that records this result changes only documents in this folder.

## 3. Frozen integrity (after every change of this program)

| check | result |
|---|---|
| V1 - V2.5 outputs (villa, mirror, reference plan; Mode U and A) against the Stage A snapshot | **968 files, 0 differ** |
| V2.6 outputs against the `b9baa7b` snapshot | **272 files, 0 differ** (39 runs, all exit 0) |
| `freeze_verify.py check` | 0 frozen artefacts differing |
| `freeze_verify.py env` | in lock, no package differences |
| `freeze_verify.py closure` | exit 0; identical to the run at the program's start |
| `engine/`, `rules/`, `knowledge/` | unchanged (no file touched) |

## 4. Real-world evidence: the five real rooms (private, aggregates)

The truth is an independent raw-entity reading (Phase 2B-5 Stage C), with the S2 synthetic heights as stated inputs.

| method | failing checks of 66 | what the failures are |
|---|---|---|
| V2.5 | 11 | - |
| V2.6 (reproduced tonight) | **8** | 7: the held door's width (one room); 1: the basin lobby's doorway attribution |
| V2.6 + Experiment A (clone) | **1** | the basin lobby |
| V2.6 + Experiments A + G (clone) | **0** | - |

Before / after on the lines the experiments change (reference plan, private run). The expected value is the Stage C
reading and the raw jamb reading. Absolute values are withheld; the differences are shown.

| line | V2.6 vs expected | with the experiments vs expected |
|---|---|---|
| threshold of the held door | +0.0335 m2 (+28 %) | 0 |
| doorway waterproofing, laundry side | +0.0335 m2 | 0 |
| laundry plaster / wall tile | −0.154 m2 each | 0 |
| laundry skirting | −0.073 m | 0 |
| laundry upturn | −0.015 m2 | 0 |
| W.C. doorway waterproofing (basin lobby) | −0.12 m2 (carried by the lobby) | 0 |
| curved wall run (one band, not a sample room) | −1.885 m on the mean radius (−0.88 % of the plan's wall run) | 0 against the raw-ezdxf arc census |

**Remaining uncertainty.**

- One real plan only.
- The heights are synthetic.
- Two of the three basin-typed spaces are outside the independent sample.
- The curved-run basis is a convention (D-07).

## 5. Synthetic before / after (hand truth)

| case | line | V2.6 | experiment | truth | V2.6 error |
|---|---|---|---|---|---|
| CROSSING | door width | 1.027 m | 0.80 | 0.80 | +28.4 % |
| CROSSING | threshold | 0.2054 m2 | 0.16 | 0.16 | +28.4 % |
| CROSSING | bath plaster | 26.2203 m2 | 26.382 | 26.382 | −0.61 % |
| CROSSING | bath skirting | 8.477 m | 8.554 | 8.554 | −0.90 % |
| PLAIN, inferred roles | floor | 11.615155 m2 | 12.0 | 12.0 | −3.21 % |
| PLAIN, inferred roles | perimeter | 15.099557 m | 14.0 | 14.0 | +7.85 % |
| B04 (benchmark), inferred roles | floor | +2.18 % | exact | - | +2.18 % |
| villa turned 30°, inferred roles | bedroom plaster | −4.80 m2 | as unturned | as unturned | −10.4 % |
| B10 | wall run (gross) | 11.0 m | 14.346206 (MID) | 14.346206 (MID) / 14.217506 (inner face) | −23.3 % (MID) |
| three hatched drains | floor | 11.9325 m2 | not fixed (audit A04) | 12.0 | −0.56 % |

## 6. Privacy

- The project's privacy scan (client names, project codes, room ids, forbidden figures, private paths, Arabic text in
  shareable documents) was run on every new and changed file: 24 files, 0 findings.
- No drawing (DXF / DWG) is committed. Every fixture is generated by `tests/m9_p2b6/p2b6_fixtures.py` or the benchmark
  builders.

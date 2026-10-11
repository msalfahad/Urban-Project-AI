# Test record (M4)

## M4 tests (`tests/m4_correctness/`)

| File | Tests | What they prove |
|---|---|---|
| `test_m4_continuous_beams.py` | 6 | Printed spans and roles; a span takes a mark only through the printed sequence (forward, hand-derived 1.008 m3); a simple beam's unlabelled span is never inherited (exposure 0.46 m3); count conflict and reversed reading; physical bar lengths by hand (bottom 4.79 m, support top 2.45 m); mass conserved, including a mapped span with two marks whose bars are held as exposure |
| `test_m4_exterior_gb.py` | 6 | Architectural registration (shift recovered), wall classes (exterior / interior / perimeter without wall), inside level; exterior depth only where a wall is evidenced; level conflict keeps the class section; without the architectural plan a perimeter band is a candidate only; wall cover; registration refuses a tie |
| `test_m4_stairs_lintels.py` | 7 | Straight flight vs hand section; riser rule; partial zone; winder; lines that do not fan; lintel row by width, bearings on masonry jambs only, boundary gap and above-schedule never measured; beam over the opening; census cuts a gap at a column |
| `test_m4_slab_blinding.py` | 7 | Member overlap deducted, project default first, ground slab excluded; a member inside a face hole and crossing members deducted once; exact union where four outlines meet; blinding union against shapely |
| `test_m4_ocr_review.py` | 4 | Outcomes and confidence; a disagreeing or ambiguous reading rejects the whole role; never promoted; downstream quantities; the ST7757 readings check but never confirm |
| `test_m4_reports.py` | 3 | Missing-reinforcement register (roles, detail needed, never kg by ratio); numbered, located exceptions; CB registers and visual QA |
| `test_m4_heldout_generator.py` | 3 | The m4 variant changes only its own drawings; the M4 engine never assigns a wrong section and its exposure covers the truth |
| `test_m4_package.py` | 11 | Deliverables; hygiene, path and benchmark firewall; nothing tracked that embeds drawing content; registers agree; nothing VERIFIED or promoted; independent checks pass; positions only; held-out precision; RFIs; live reproduction of the registers from the private drawings |

## Full suite

**Command:** `python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_1213430.xml` at `1213430`.

**Classification:** by `research/environment_recovery/classify_test_run.py`; reduced summary in `TEST_GATE_1213430.json`.

| Class | `1213430` (M4) | `bfa208e` (M3) |
|---|---:|---:|
| EXECUTED_PASSED | 7368 | 7321 |
| CODE_FAILURE | **0** | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7368 passed, 138 skipped, 100 xfailed, 32 errors, in 6 min 40 s.
- **The 344 failures and 32 errors are not code failures.** They are the same 376 tests blocked by missing data as at M1, M2 and M3:
  - 373 under `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`;
  - 1 that needs the private reconciliation document under `data/runs/7757`;
  - 1 generated prerequisite and 1 private path.
- **Passes:** +47, exactly the 47 M4 tests.
- **Prior suites:** every M1 / M2 / M3 package test still passes, including the M3 live reproduction of its files from the private drawing. The M4 behaviour is gated on the M4 conventions.
- **Gate: INCOMPLETE.** 376 mandatory tests are blocked by missing data, 136 are skipped for an unavailable prerequisite, and 108 locked prerequisites are missing (benchmark 14, derived 87, source 7).

## Defects found during M4 and fixed before the freeze

Each was found by a test or an independent check, and each has a regression test.

| Found by | Defect | Fix |
|---|---|---|
| CB unit test | A line's count conflict was reported as "on no continuous-beam line" | The pieces of an unmapped line now carry the line's state |
| Hand-derived stair truth | Landings re-counted the flight's last tread | The flight plan is risers − 1 treads |
| Lintel fixture | A column standing in a wall gap widened the opening (1.6 m instead of 1.2 m) | The gap is cut at the column face; on ST7757, 6 openings changed |
| Exterior-GB fixture | The inside-level probe missed when a beam met the band at mid-length | Probe at five stations |
| IC-06 | 30.2 kg of CB3 bars were dropped on a span printed with two marks | Held as an UNRESOLVED exposure; mass conserved |
| IC-01 / IC-02, then grid sampling | A member inside a slab-face hole was deducted again (0.25 m²) | Overlap = (outer − holes) ∩ union(members) |
| IC-08 / IC-09 | Blinding: strip on footing, crossing strips and footing projections were counted twice | Exact union of the convex outlines |
| Rebar product firewall test | New rebar-aware modules were not declared | Declared in the registry |

## Double build and the change after the full suite

- **Double build.** The package was built twice with different hash seeds (`PYTHONHASHSEED`). Every committed file was byte-identical, apart from the machine timings in `00_NUMBERS.json`.
- **What triggered it.** The live-reproduction test then exposed one order effect:
  - the independent check IC-06 summed piece masses in a set's iteration order;
  - a difference of 1e-14 could print as `-0.0`.
- **Fix, after the full suite, in reporting code only.**
  - IC-06 now sums in sorted order.
  - The package CSV writer never writes a signed zero.
  - The engine at `35c0587` is unchanged.
- **Re-run.** `tests/m4_correctness/test_m4_package.py` passed again (11 tests) on the rebuilt package, including the byte-for-byte live reproduction of the registers and of `10_INDEPENDENT_VALIDATION.csv`.

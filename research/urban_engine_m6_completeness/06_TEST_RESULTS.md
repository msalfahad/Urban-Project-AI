# 06 Test results (M6)

## M6 tests (`tests/m6_completeness/`, 40)

| File | Tests | What they prove |
|---|---:|---|
| `test_cc_units.py` | 11 | Layer roles and family tokens, note families (bilingual, read from the route), section and thickness labels, ASCII-only evidence, the policy record (V2) names every kind and never a ratio |
| `test_cc_ledgers.py` | 6 | One hand-built roof plan: member lines explained and an unknown outline found (no volume without a thickness); labels / schedule / storeys; columns one-to-one both ways; overlap and dependency; scores and scope; a finding never enters a total |
| `test_cc_v2.py` | 4 | The V2 rules on hand-built fixtures (3 fail on the V1 engine): an AMBIGUOUS mark beside an unresolved band is reported and still placed for the schedule, beside a band carrying its mark it is consumed; the column fill is explained, another fill on a beam is HATCH_ON_MEASURED_MEMBER naming the beam's item, a legend swatch names its fills and is no finding; pit walls inside a measured footing are a finding with LIFT / WALLS / WATER_TANK candidates; footing-layer content is still the footing |
| `test_cc_synthetic.py` | 8 | Synthetic villas (truth from the generator): every injected element reported and nothing else (3 seeds); the V2 cases on top of every V1 element (3 seeds, one with the extra-storey copy); a plain villa has no actionable finding; the missing and the extra storey |
| `test_cc_cli.py` | 3 | The one-command BOQ writes the completeness outputs (policy V2), `--no-completeness` leaves every earlier output as it was, completeness changes no quantity, no Arabic text reaches an output |
| `test_cc_package.py` | 8 | Hygiene over every package file and the engine / tools; both engine freezes hold the files as committed at their freeze commits (read with git); both run manifests hold their files, V2 is POST_DISCOVERY and V1 untouched; the held-out V2 summary is its own records and the V1 held-out re-run equals the V1 record; the four reconciliation tallies close; **live**: both ST7757 runs rebuild byte for byte from the engines read from git, and the reconciliation rebuilds from both frozen runs |

**Result:** 40 passed.

## Targeted runs before the full suite

- `tests/m6_completeness`: 40 passed.
- `tests/structural_comparison_engine/test_rebar_product_firewall.py tests/m1_usable_boq tests/m2_generic_engine tests/m3_recovery tests/m4_correctness tests/m5_reconciliation`: all passed on the V2 engine.

## Full suite

**Command:** `python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_m6.xml`, on the V2 engine freeze
`6c20879` with the package tree of `7fc77eb`.
**Classification:** `research/environment_recovery/classify_test_run.py`; reduced summary in `TEST_GATE_M6.json`.

| Class | M6 | M5 |
|---|---:|---:|
| EXECUTED_PASSED | 7434 | 7394 |
| CODE_FAILURE | **0** | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7434 passed, 138 skipped, 100 xfailed, 32 errors in 7 min 48 s.
- **The 344 failures and 32 errors are not code failures**: the same 376 tests blocked by missing data as at
  M1–M5 (373 under `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01`, 1 needing the private reconciliation
  document under `data/runs/7757`, 1 generated prerequisite, 1 private path outside the repository).
- **Passes: +40**, exactly the 40 M6 tests.
- **Gate: INCOMPLETE** (376 blocked by missing data, 136 prerequisite skips, 108 locked prerequisites missing).

## Defects found during M6 V2 and fixed before the freeze

| Found by | Defect | Fix |
|---|---|---|
| First V2 run on ST7757 (diagnostic) | an AMBIGUOUS mark reported as LABEL_MEMBER_CONFLICT also produced SCHEDULED_NOT_PLACED for its type | a mark the route saw counts as placed whatever its binding state |
| Same | the pit outline is a closed outline (inner faces stop at columns), so the ring-only pit prior never fired | the prior also takes a closed outline enclosing a pit-sized area |
| Same | a fill merged into any unexplained group whose box contained it (the whole-plan foundation fill into the boundary wall) | a fill joins a group only when half its boundary runs along the group's lines; a whole-plan fill is SITE_FILL |
| Same | hatched beams of two storeys at the same place were merged as one drawing repeated | fills on measured members are per storey on slab plans |
| Dev seeds with V2 cases | generator: both hatched cases shared one pattern, so one legend named both; the extra-storey copy duplicated V2 fills without truth | one pattern per meaning, one legend row each; the copy is added as `also` truth |

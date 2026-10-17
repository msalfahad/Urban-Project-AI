# M1 TEST_RUN: a usable structural BOQ (provisional estimating layer)

Baseline HEAD `d433229` (S9A complete). Date 2026-10-10. Commits of the round:

| Commit | What it holds |
|---|---|
| `bc28327` | **The freeze.** It holds the provisional estimating engine, the drawing inventory and the profile takeoff (`engine/source`), the workbook view (`engine/boq_m1_xlsx.py`), the one-command CLI and its report (`tools/`), and the ST7757 adapter, conventions, builder and outputs (`research/alsenan_m1_usable_boq`, manifest `06`, `references_read: []`). It also holds the M1 tests and the registry entries |
| `eab0fc1` | The post-freeze comparison against freelancer QS, christiannp-autocad, U-C4N, old Urban V3b and R9.1 (`post_freeze/`), with its tests |
| this commit | This record and the gate report `TEST_GATE_eab0fc1.json` |

M1 adds a provisional layer. It releases nothing: VERIFIED is exactly S9's 158.070256 m3 / 18,845.961347 kg, every
frozen stage manifest verifies before and after, and the project gate stays INCOMPLETE. Passing tests prove
bookkeeping and arithmetic, not engineering approval.

## What the tests pin

- **Engine (synthetic, 7 tests).**
  - A VERIFIED item has no range and no assumption.
  - A PROVISIONAL item names its assumptions and keeps 0 <= low <= base <= high.
  - An UNRESOLVED item carries no value; its exposure is shown apart and never added.
  - Each component has one owner. Unknown assumptions are refused. A missing option is never a zero.
  - Overrides recompute, and resetting them restores the same set digest.
  - Bars use d^2/162, and a mesh needs a known area.
- **New-villa route (synthetic DXF written by the test, 5 tests).**
  - The inventory finds both sheets, the layer roles, the tag families and the outlines. The template defaults nothing.
  - The profile route measures the four source-complete members only, as PROVISIONAL / SOURCE_COMPLETE_UNREVIEWED.
    The size mismatch (with its exposure), the orphan tag, the combined outline and the unscheduled type come out
    UNRESOLVED, each with an exception.
  - Nothing is VERIFIED, and the uncovered families are listed with the tag evidence.
  - The workbook validates and is byte-identical on a second write.
  - The one-command CLI runs with the PDF. The inventory-only route works, and DWG input is refused.
- **ST7757 package (12 tests).**
  - The manifest and all frozen stage manifests verify, and the firewall holds.
  - VERIFIED equals S9's released rows (126 + 986).
  - The planning totals re-add from the registers, and unresolved items carry no value.
  - Every provisional row is ordered, assumed and traceable, and has one owner.
  - Each of the 560 S9 records gets one disposition, none MISSING. The 7 re-owned spans are never counted.
  - The beam readings are recomputed from S9A 05's B, H, L and t.
  - The neck volumes follow the printed founding rule and reproduce S9's points.
  - The registers re-derive from the adapter. The BELOW_SLAB override gives the B total, and the base comes back.
  - The diagnosis re-adds, and hygiene holds. The rebuild is byte-identical.
- **Post-freeze (5 tests).**
  - The comparison is downstream of the freeze.
  - Every comparison has a position and a class, and an agreement is always INSIDE.
  - No external figure is written, and hygiene holds.
  - The rerun is identical, and M1 is untouched.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/m1_usable_boq tests/structural_s9a tests/structural_s9 tests/structural_comparison_engine tests/stairs_s8_7c tests/stairs_s8_7b tests/stairs_s8_7a tests/stairs_s8_7 tests/lift_s8_8 tests/lintels_s8_6a tests/lintels_s8_6 tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

- At `eab0fc1`: **415 passed, 1 xfailed.** That is S9A's 385 plus this round's 30. The xfail is the recorded B-7
  boundary debt, older than S8.
- `tests/m1_usable_boq`: 30 passed (7 engine, 5 new-villa, 13 package, 5 post-freeze).
- The rebar product firewall and the import boundaries hold with the M1 modules declared. `engine/source` stays
  stdlib-only: the inventory takes an already-opened DXF document by duck typing.
- The workbook was recalculated in LibreOffice: 141 formulas, 0 errors, and the totals equal the registers.

## Full suite

`python3 -m pytest -o addopts="" -p no:cacheprovider --junitxml=junit_eab0fc1.xml` at `eab0fc1`, classified by
`research/environment_recovery/classify_test_run.py` (`TEST_GATE_eab0fc1.json`):

| Class | Count | At S9A (`e9f001f`) |
|---|---:|---:|
| EXECUTED_PASSED | 7193 | 7163 |
| CODE_FAILURE | 0 | 0 |
| MANDATORY_BLOCKED_BY_MISSING_DATA | 376 | 376 |
| SKIPPED_PREREQUISITE_UNAVAILABLE | 136 | 136 |
| SKIPPED_OTHER | 2 | 2 |
| EXPECTED_FAILURE | 100 | 100 |

- **Raw pytest:** 344 failed, 7193 passed, 138 skipped, 100 xfailed, 32 errors, in 5 min 29 s.
- **No code failure.** Every failure and error is a missing private input:
  `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01` (373), `data/runs/7757`, `/root/.claude`, and one generated
  prerequisite.
- **Blocked and prerequisite-skip counts are identical to S9A.** The 30 new passes are this round's tests.
- **The project gate stays INCOMPLETE:** 376 mandatory regression tests blocked by missing data; 136 tests skipped for an unavailable prerequisite; 108 locked prerequisites missing {'BENCHMARK': 14, 'DERIVED': 87, 'SOURCE': 7}.

## Usability (ST7757)

| Measure | Result |
|---|---|
| Runtime, one command (DXF + PDF in, registers + Excel + PDF out) | about 8 s, of which about 6 s is PDF printing; compute about 2 s (`boq/run_log.json`) |
| Manual interventions during the run | 0 (route A replays the frozen S1 - S9A work, which embodies the manual stages) |
| S9 component records with an M1 disposition | 560 of 560 (507 items, 26 owned by another family, 14 not applicable, 7 re-owned to bands, 3 covered by the pool base, 3 typical-detail only) |
| Drawing layers inventoried | 47; one layer with geometry is named by no stage (sheet outlines only) |
| Blind test on another villa | NOT RUN: no permitted dataset. The new-villa route is exercised on a synthetic drawing |
| Independent benchmark | none, so no accuracy figure is claimed |

## Post-freeze findings (not fixed: M1 stays frozen)

- **PF-M1-01, totals.** Every external RC total sits inside M1's planning range, and old V3b sits below it. The
  scopes differ, so this is not an accuracy figure.
- **PF-M1-02, ground slab.** All three external estimates sit above M1's ground slab. M1 carries S9's 21 faces,
  while R9.1's best route finds more cells. This is the largest real M1 gap.
- **PF-M1-03, reinforcement items.** 89 carried beam / ground-beam / lift concrete components have no bar row in S9
  03. M1's 33 unresolved reinforcement items understate the gap.
- **PF-M1-04 - PF-M1-07.**
  - Necks come from the printed founding rule (higher than the externals).
  - christiannp and U-C4N double-count straps into the footings.
  - The freelancer steel is above M1 where M1 has unresolved bars.
  - 8 of 80 engine-group comparisons agree on the same components.

## Limitations

- **Route A replays the frozen stage registers.** It does not re-extract the drawing.
- **Route B covers footings and columns only,** and only once a person confirms a profile.
- **No blind test on a second villa,** and no independent benchmark.
- **Steel ranges are narrow** where a frozen bar model exists. Only the hook allowance varies.
- **The PDF, the workbook and the run log are not frozen.** They are git-ignored and regenerated by `build_m1.py` /
  the CLI.

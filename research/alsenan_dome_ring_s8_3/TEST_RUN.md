# S8.3 TEST_RUN: dome and ring-beam structural QTO

Baseline HEAD `104c9d6`. Commits of the round:

| Commit | What it holds |
|---|---|
| `c74eaaf` | Owner decision: the two reconstructed architectural PDFs are kept, marked `BYTE_IDENTICAL_RECONSTRUCTION_FROM_VERIFIED_UPLOAD` |
| `c432845` | The generic curved-member geometry engine and its 26 known-answer tests (work in progress) |
| `3df638b` | **The blind freeze**: 16 outputs + `16_S8_3_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`) and the package tests |
| `5087db8` | The post-freeze comparison and its tests (COMPARISON_MODULES) |
| `0fc1a9e` | The test-gate classifier (`research/environment_recovery/classify_test_run.py`) |
| `fd6a857` | This record and the gate report `TEST_GATE_0fc1a9e.json` |
| `ac788a5` | **Errata** (`errata/`): a dated layer over the frozen package; no quantity moved (see below) |
| this commit | Run 8 on the errata commit and `TEST_GATE_ac788a5.json` |

S8.3 releases **5.081361 m3** of concrete and **602.111304 kg** of reinforcement, both PROJECT_BASIS_QTO:

- the concrete is the two terrace dome shells;
- the reinforcement is their single Ø12/150 mesh, measured as a rate density.

Everything else is SOURCE_CONFLICT or BLOCKED. The tower dome is not quantified. All 18 earlier freeze manifests
still verify.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/dome_ring_s8_3 tests/structural_comparison_engine tests/r8_1/test_r8_1_boundaries.py tests/r8_0/test_r8_0_import_boundaries.py tests/environment_recovery
```

All passed at `0fc1a9e`, as part of the full run below.

| File | Tests | Covers |
|---|---|---|
| `test_curved_member_geometry.py` | 26 | See the list below |
| `test_s8_3_package.py` | 20 | See the list below |
| `test_s8_3_post_freeze.py` | 6 | See the list below |
| `tests/environment_recovery` | 6 | Recovery manifest, inputs lock, prerequisite checker, reconstruction marking, test-gate classifier |

`test_curved_member_geometry.py` is synthetic known answers only. It covers:

- clockwise and counter-clockwise sweeps, including sweeps across 0 degrees;
- -Z extrusions, checked against ezdxf's own OCS conversion;
- mirrored and rotated block inserts, checked against ezdxf's explode;
- chord against true arc length;
- closed against partial rings, and repeated or overlapping arcs;
- band segments;
- exact disk/rectangle overlaps, checked against shapely and a numerical integral;
- spherical caps and shells, checked against a solid of revolution;
- profile tests;
- hoop and meridian densities;
- symmetric offsets.

`test_s8_3_package.py` covers:

- the freeze, blindness (no old-figure token, PRE-S8 never read) and the registry;
- the population, with repeats not counted;
- the profile;
- the 8 segments = BA001-BA008, closing on the framing faces;
- the transfer of 0 kg;
- released quantities recomputed independently (numerical shell, area / spacing x D²/162);
- the tower not quantified;
- notation families;
- the S7 43.1 kg staying in S7;
- conflicts, sensitivity, the 14 conservation checks, the reconstruction marking, and hygiene (no drawing, no Arabic
  owner text).

With the private drawings present it also covers:

- ezdxf ConstructionArc sweeps;
- the shapely ring partition and openings;
- a byte-identical rebuild.

`test_s8_3_post_freeze.py` covers:

- the freeze being intact;
- every row classified;
- the old figures reproduced by their own formula;
- population differences named;
- the module being registered;
- an identical re-run.

The builder was run twice with byte-identical output (17 files), including once with the reconstructed PDFs moved
aside.

## Full suite: NOT GREEN, gate INCOMPLETE

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`0fc1a9e`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 7 | `0fc1a9e` | 6744 | 344 | 32 | 138 | 100 | 320.0 s | 1 |
| 8 | `ac788a5` | **6748** | 344 | 32 | 138 | 100 | 353.0 s | 1 |

Run 6 (`0aa0642`, S8.2A) had 6689 passed. The 55 extra passes are this round's 52 S8.3 tests and 3 environment tests.
The set of failing test IDs is identical in runs 4 to 7.

Run 8 adds the 4 errata tests. Its failing set is identical to run 7's, and its classification is the same apart from 6748 executed and passed (`TEST_GATE_ac788a5.json`).

### Every test, classified (`classify_test_run.py`, run 7)

| Class | Tests | Meaning |
|---|---|---|
| 1. Executed and passed | **6744** | the only class that proves anything |
| 2. Legitimately skipped: prerequisite unavailable | **136** | private input, fixture, client data or generated artefact absent; never counted as a pass |
| Skipped for another reason | 2 | `QS_MEASUREMENT_REGION_BUILDER does not exist yet` |
| Expected failures (xfail) | 100 | recorded by the tests themselves |
| 3. Mandatory regression blocked by missing data | **376** | failed or errored on a missing required file |
| 4. Actual code failures | **0** | |

The 376 blocked tests, by missing path:

| Missing | Tests |
|---|---|
| `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/...` | 373 |
| `data/runs/7757/...` | 1 |
| A generated prerequisite (`run workbook_boq first`) | 1 |
| A session upload under `/root/.claude` | 1 |

**Complete-project regression gate: INCOMPLETE.**

- 376 mandatory regression tests are blocked by missing data.
- 136 tests are skipped for an unavailable prerequisite.
- 108 locked prerequisites are missing: 14 BENCHMARK, 87 DERIVED and 7 SOURCE.

The gate stays INCOMPLETE until the private fixtures and the sealed benchmark evidence are restored. The blind builders
never read benchmark truth. Test IDs and missing paths are in `TEST_GATE_0fc1a9e.json`; it holds no content and no
benchmark value.

## Errata (after the post-freeze comparison)

A re-audit against the brief's "anchorage and junction bars" item found two defects in the frozen notation register.
They are recorded in `errata/` without editing the frozen package; the manifest verifies before and after.

- **S8.3-E01:** a wrong note. Both ring cuts draw all labelled bars.
- **S8.3-E02:** a missing object. One unlabelled small bar per cut sits against the bend of the shell bar. It is added
  as `UNLABELLED_JUNCTION_BAR`, one blocked family per dome.
- **S8.3-E03:** evidence for the mirrored-block test on the real drawings.
  - No dome entity has a -Z extrusion or sits in a mirrored insert.
  - The architectural DXF's 13 mirrored inserts are door and window blocks, none within 3 m of a dome.

Released quantities are unchanged.

## Limitations

- The full suite is red because private data is missing. No missing-data skip is presented as a pass.
- The visual records come from the raster sections, read at about 1.57 px/cm (±2 cm). They corroborate the profile and
  give no released quantity.
- The drawing-dependent tests skip when the private drawings are absent. The synthetic engine tests always run.
- Before the freeze, the PRE-S8 census rows were printed during source discovery, and they embed old commercial dome
  figures. The builder does not read them. This is disclosed in `00_README.md`. SA-TOWER-SHELL lands close to the old
  tower figure (it is sensitivity only).

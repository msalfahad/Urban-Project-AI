# S8.4 TEST_RUN: water-tank roof region, concrete and reinforcement QTO

Baseline HEAD `cce41a2`. Commits of the round:

| Commit | What it holds |
|---|---|
| `1847fb9` | **The blind freeze**: the engine `engine/source/slab_layered_mesh.py`, the builder, 15 outputs + `15_S8_4_FREEZE_MANIFEST.json` (`FROZEN_BEFORE_COMPARISON`, `references_read: []`), the synthetic and package tests, the registry entries |
| `b2afdb5` | The post-freeze comparison (`post_freeze/`) and its tests (COMPARISON_MODULES) |
| this commit | This record and the gate report `TEST_GATE_b2afdb5.json` |

S8.4 releases **2.4543 m3** of concrete and **361.208565 kg** of reinforcement, both PROJECT_BASIS_QTO:

- the concrete is the two panel faces at 180 mm (8.235 + 5.4 m2);
- the reinforcement is eight families: two panels x two directions x top and bottom.

S7 stays 3,802.015 kg. All 20 earlier freeze manifests and the three S8.3 errata files still verify.

## Targeted

```
python3 -m pytest -o addopts="" -p no:cacheprovider tests/water_tank_s8_4 tests/dome_mesh_s8_3a tests/dome_ring_s8_3 tests/structural_comparison_engine tests/r8_0/test_r8_0_import_boundaries.py tests/r8_1/test_r8_1_boundaries.py tests/environment_recovery
```

At `1847fb9` this gave 197 passed and 1 xfailed. The xfail is the recorded B-7 boundary debt: two engine modules import
a research parameter file. It predates S8.4.

| File | Tests | Covers |
|---|---|---|
| `test_slab_layered_mesh.py` | 19 | Synthetic known answers only. See the list below |
| `test_s8_4_package.py` | 20 | See the list below |
| `test_s8_4_post_freeze.py` | 5 | Freeze intact, every row classified, the old sets reproduced by their own formula and bridged, registered, identical rerun |

`test_slab_layered_mesh.py` covers:

- **Callout reading:** rate callouts (`%%c`, `%%C`, `Ø`), the explicit `/Top` count, and refusals: 'T 18', 'T',
  '18', '(T&B)' and 'T18' are never bars.
- **Faces, not directions:** '(T&B)' gives top and bottom only. A bare 'T' or 'B' counts only inside brackets.
- **Thickness tags:** a circled 'T' over a number is a thickness; anything else in or out of the circle is refused.
- **Binding:** a text binds to the parallel bar under it, and a double line is one graphic.
- **Bands:** the edges a band starts and ends on, for rectangles, a notched panel, an oblique edge and two intervals in
  one band. Every layer's strips cover the panel exactly.
- **Quantities:** a full layer is rate x area, never rounded. Stop zones fall only at the named edge classes, follow
  the local run and are kept apart. The edge-zone length, rotation symmetry and refusals of bad input are checked.

`test_s8_4_package.py` covers:

- the freeze and every earlier stage, through all 20 manifests;
- blindness: no earlier-figure token, and PRE-S8 is verified, never read;
- the registry;
- two panels, one parent and no invented tank;
- the starting population against PRE-S8's ids (id column only);
- T 18 as a 180 mm thickness;
- each (T&B) callout giving two faces of its own direction;
- concrete and steel by hand from the printed figures;
- strips covering each panel;
- S7 untouched, with its 20.087 kg at the tank edges staying S7;
- every one of the 22 S7 items and 33 PRE-S7.1 transfers landing once;
- every blocked component named;
- sensitivity never released;
- conservation and hygiene: no drawing, no owner text.

With the private drawings present it also covers:

- the handles, read through ezdxf;
- the cloud and panels, checked with shapely;
- a byte-identical rebuild.

The builder was run twice with byte-identical output (16 files).

### Defects found and fixed before the freeze

- **A bare 'T' read as a layer qualifier.** The first parser accepted 'T'. The thickness tag's letter would then have
  bound to each X callout as a second qualifier. A lone letter now counts only in brackets, and a test covers it.
- **Two cosmetic register defects:**
  - one blocked id was duplicated, because two bands end on the same edge; the stop zones are now aggregated per edge,
    and every register id is checked unique;
  - one sensitivity row showed "0" where its length was counted under another item; it now shows none.

## Full suite

**Full suite: NOT GREEN. Gate: INCOMPLETE.**

`python3 -m pytest -o addopts="" -q -rfEs -p no:cacheprovider --junitxml=...` was run on the clean committed tree
`b2afdb5`. No file was edited during the run.

| Run | Commit | Passed | Failed | Errors | Skipped | xfailed | Time | Exit |
|---|---|---|---|---|---|---|---|---|
| 9 | `4c63445` (S8.3A) | 6764 | 344 | 32 | 138 | 100 | 302.4 s | 1 |
| 10 | `b2afdb5` (S8.4) | **6808** | 344 | 32 | 138 | 100 | 348.2 s | 1 |

- The 44 extra passes are this round's 44 tests (19 + 20 + 5). All of them executed and passed.
- The blocked, code-failure and prerequisite-skipped test sets are identical to run 9's.

### Every test, classified (`classify_test_run.py`, run 10)

| Class | Tests | Meaning |
|---|---|---|
| 1. Executed and passed | **6808** | The only class that proves anything |
| 2. Legitimately skipped: prerequisite unavailable | **136** | A private input, fixture, client data or generated artefact is absent. Never counted as a pass |
| Skipped for another reason | 2 | `QS_MEASUREMENT_REGION_BUILDER does not exist yet` |
| Expected failures (xfail) | 100 | Recorded by the tests themselves |
| 3. Mandatory regression blocked by missing data | **376** | Failed or errored on a missing required file |
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

The gate stays INCOMPLETE until the private fixtures and the sealed benchmark evidence are restored.

- The blind builder never read benchmark truth.
- Test IDs and missing paths are in `TEST_GATE_b2afdb5.json`.
- That file holds no content and no benchmark value.

## Limitations

- The full suite is red because private data is missing. No missing-data skip is presented as a pass.
- The panel faces are drawn, not dimensioned (the sheet asks for stated dimensions). The x spans and panel 02's y span
  agree with the printed axis chains. Panel 01's y span depends on beam BL008's drawn position. Everything is
  PROJECT_BASIS_QTO, nothing is SOURCE_DERIVED_PHYSICAL.
- Visual records (the p.6 legend, the p.8-15 plots, the architectural sections and elevations) were read in session.
  Their renders are client drawing and stay outside git.
- The drawing-dependent tests skip when the private drawings are absent. The synthetic engine tests always run.

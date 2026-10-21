# Test and reproduction commands (Phase N10)

Run everything from the repository root. Every command uses `python3 -I` and `PYTHONDONTWRITEBYTECODE=1`, and every pytest run gets its own `--basetemp` (`BT` below is any empty scratch directory). `pytest.ini` already adds `-q`; a second `-q` hides the summary line.

```bash
export PYTHONDONTWRITEBYTECODE=1
```

## 1. New tests (Phase N10)

```bash
python3 -I -m pytest -p no:cacheprovider --basetemp=$BT/n10 tests/m9_n10
```

70 tests in 6 files: curved openings 21, independent curved 6, masonry 11, facade 14, structural 14, registry 4. Result at the final tree: **70 passed** (75 s).

The hand truth is in `tests/m9_n10/n10_truth.py`. It is arithmetic on the fixture coordinates (`tests/m9_n10/n10_fixtures.py`), never engine output.

## 2. Neighbouring suites (as-found behaviour of earlier methods)

```bash
python3 -I -m pytest -p no:cacheprovider --basetemp=$BT/p2b9 tests/m9_p2b9
python3 -I -m pytest -p no:cacheprovider --basetemp=$BT/kb tests/m9_kb
python3 -I -m pytest -p no:cacheprovider --basetemp=$BT/codemap tests/codemap
python3 -I -m pytest -p no:cacheprovider --basetemp=$BT/fw tests/structural_comparison_engine   # static scans over engine/: a new module that names rebar must be declared
```

## 3. Freeze, registry and maps

```bash
python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl
python3 -I tools/freeze_verify.py env
python3 -I tools/freeze_verify.py closure
python3 -I tools/kb_build_1_4.py --check
python3 -I tools/kb_build_1_5.py --check
python3 -I tools/codemap.py check
```

## 4. Full suite (by test identity)

```bash
git clone --quiet <repo> CLONE && cd CLONE && git checkout <commit>
# optional: link the git-ignored private inputs, as the earlier phases did: ln -s <private inputs> data/inputs
python3 -I -m pytest -p no:cacheprovider --basetemp=$BT/full --junitxml=$BT/junit_<commit>.xml
```

Compare two JUnit files test by test (new / removed / pass → fail / fail → pass / other changes). The comparison script is in the handoff ZIP (`scripts/cmp_junit.py`):

```bash
python3 -I scripts/cmp_junit.py junit_<base>.xml junit_<commit>.xml
```

A result belongs to the commit it ran on.

## 5. The method on a drawing

```bash
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.9 \
    [--facts FACTS.json] [--layer-roles LAYER=ROLE ...]
```

New V2.9 outputs: `CURVED_OPENINGS.json` and `FACADE.json`, plus the masonry and facade lines in `BOQ_LINES` and the per-change correction records. V2.8 and earlier are unchanged.

Facts read by V2.9 (all optional, each labelled with its authority):

- `masonry.{floor|*}.panel_height_m`, `floor_buildup_m`, `beams_over_walls`;
- `masonry.materials.{family}`;
- `facade.{floor|*}.height_m`, `facade.finish`;
- `opening_heights`.

## 6. Independent verification of a method change

```bash
python3 -I tools/arch_change_verify.py --before OUT_V28 --after OUT_V29 --dxf PLAN.dxf \
    [--facts FACTS.json] [--layer-roles LAYER=ROLE ...] [--out VERIFY.json]
```

Each difference is VERIFIED, EXPLAINED_UNVERIFIED, CONTRADICTED or UNEXPLAINED.

## 7. Structural formwork, excavation and rebar audit

```bash
python3 -I tools/urban_boq_m2.py run --drawings STRUCT.dxf --out RUN --route G [--profile PROFILE.json] --no-pdf --no-xlsx
python3 -I tools/struct_n10.py --run RUN --out N10 [--facts FACTS.json]
```

Outputs: `FORMWORK.json`, `FORMWORK_FACES.csv`, `EXCAVATION.json` and `REBAR_AUDIT.json`. Route G's own files are read only; a test checks their SHA-256 before and after.

Excavation facts: `excavation.{depth_m, ngl_m, founding_level_m, working_space_m}`, each with an authority.

## 8. Worked examples

```bash
python3 -I scripts/run_proofs.py OUT_DIR .
```

This uses synthetic fixtures only and writes `OUT_DIR/proofs.json` (27 rows, 27 PASS at the final tree). `WORKED_EXAMPLES.md` is generated from that file.

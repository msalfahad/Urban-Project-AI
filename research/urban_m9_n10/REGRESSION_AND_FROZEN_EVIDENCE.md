# Regression and frozen-method evidence (Phase N10)

## 1. Frozen methods: byte identity

The private snapshot `n10_a` ran every method (V1 – V2.9) on the three private drawings: the synthetic villa, its mirror and the reference plan. Each ran in Mode U and, for V2.2 and later, in Mode A.

The snapshot tree is the committed code at **9a52c34**, with a clean working tree. The only later code commit, 4b299ae, changes documentation, the routing maps and one entry in `tools/routing_topics.json` (the defect source). It changes no engine, tool logic, rule or knowledge file.

V1 – V2.8 outputs were compared file by file with the Phase 2B-9 final snapshot:

| Method | Files | Differ |
|---|---|---|
| V1 | 46 | 0 |
| V2 | 52 | 0 |
| V2.1 | 70 | 0 |
| V2.2 | 140 | 0 |
| V2.3 | 176 | 0 |
| V2.4 | 236 | 0 |
| V2.5 | 248 | 0 |
| V2.6 | 272 | 0 |
| V2.7 | 278 | 0 |
| V2.7.1 | 308 | 0 |
| V2.8 | 344 | 0 |
| **V1 – V2.8** | **2,170** | **0** (63 runs, all exit 0) |

**Shared modules N10 touched, and why V1 – V2.8 stay unchanged:**

| Module | Change | Reached by |
|---|---|---|
| `engine/source/arch_rooms.py` | curved openings, their face thresholds and the facade outline, under a `v29` flag; without it the added threshold list is empty and no opening is marked `curved` | V2.9 only |
| `engine/source/arch_completeness.py` | a strip beside a curved opening is checked in its annular sector | only when an opening is marked `curved`, which only V2.9 does |
| `engine/source/arch_v28.py` | `_strip_side` and the head soffit read two new geometry keys | only present when V2.9 writes them |
| `engine/source/knowledge.py` | registry 1.5.0 added to `VERSIONS` | V2.9 only; the default stays 1.0.0 |

Byte identity above confirms that no earlier output moved.

## 2. V2.9 determinism

V2.9 ran a second time on the same tree (`n10_a_rerun`): **362 files, 0 differ**, 6 runs exit 0.

## 3. V2.9 against V2.8 in the same snapshot (item totals)

Compared with `cmp_items`: item totals, line counts, states and ranges.

| Run | Lines | Changed items |
|---|---|---|
| reference plan, Mode A | 487 → 517 | ARCH.WINDOW 26 → 27; ARCH.WINDOW_REVEAL +1 blocked line; FIN.PLASTER and FIN.PAINT each +57.9478 m² certain (ranges narrower); FIN.SKIRTING +1 bounded line (certain unchanged, range high 30.78 → 34.07 m); new ARCH.FACADE_RUN 191.8556 m (3 PROVISIONAL + 3 RFI); new held ARCH.FACADE (4), FIN.EXT.FINISH (3), ARCH.WALL_PANEL (7), ARCH.WALL_VOLUME (7) |
| reference plan, Mode U | 476 → 506 | the same, except plaster and paint (unchanged: no height without facts) |
| villa, Mode U / A | 105 → 116 / 108 → 119 | new ARCH.FACADE_RUN 78.40 m (2 SOURCE_DERIVED); held facade area (3), exterior finish (2), wall panel (2), wall volume (2) |
| villa mirror, Mode U / A | 105 → 116 / 108 → 119 | identical to the villa |

No floor area changed on any run. The details are in `REAL_PLAN_BEFORE_AFTER.md`.

## 4. Freeze integrity and maps

| Check | Result |
|---|---|
| `tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | 0 frozen artefacts differing (exit 0), at every N10 commit and again at the end |
| `tools/freeze_verify.py env` / `closure` | exit 0 / exit 0 |
| `tools/kb_build_1_4.py --check` | registry 1.4.0 up to date (unchanged) |
| `tools/kb_build_1_5.py --check` | registry 1.5.0 up to date (53 rules; every link resolves) |
| `rules/`, `data/` | unchanged (`git diff 504b56a 4b299ae -- rules/ data/` is empty) |
| `engine/source/topology.py` | unchanged (frozen, read only) |
| `tools/codemap.py check` | no stale map at each code commit; the map is rebuilt with the docs commits, since it counts the research files |

## 5. Tests

| Suite | Result |
|---|---|
| `tests/m9_n10` (new: curved 21, independent curved 6, masonry 11, facade 14, structural 14, registry 4) | **70 passed** (at the final tree, 75 s) |
| full suite, clean clone at 4b299ae | see `FULL_SUITE_COMPARISON.md`. **Not green** (the known legacy failures remain) |

Every run used `python3 -I`, `PYTHONDONTWRITEBYTECODE=1` and its own `--basetemp`.

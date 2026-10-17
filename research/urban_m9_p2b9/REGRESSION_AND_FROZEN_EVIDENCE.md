# Regression and frozen-method evidence (Phase 2B-9)

## 1. Frozen methods: byte identity

The private snapshot ran every method on three drawings:

- the synthetic villa;
- its mirror;
- the reference plan.

Each was run in Mode U and, for V2.2 and later, in Mode A. The outputs were compared file by file with the Phase 2B-6
final snapshot (V1 – V2.6), the Phase 2B-7 final V2.7 run and the Phase 2B-8 final V2.7.1 run.

| Methods | Files | Differ | Run exits |
|---|---|---|---|
| V1 – V2.6 (the frozen 1,240) | 1,240 | **0** | 57 × exit 0 |
| V2.7 (278) — with V1–V2.6, **the 1,518 frozen files** | 278 | **0** | 57 × exit 0 |
| V2.7.1 (308) | 308 | **0** | 57 × exit 0 |

This held twice:

- at the interim tree (after the skirting fix);
- at the committed tree 065f3de (the final snapshot; see §5).

The one change to a shared module that V2.2+ reads is `release_safety.boundary_detail`. It now also returns
per-opening threshold role sets, which only V2.8 reads; byte identity confirms no earlier output moved.

## 2. Freeze integrity

| Check | Result |
|---|---|
| `tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | 0 frozen artefacts differing (exit 0) |
| `tools/freeze_verify.py env` / `closure` | exit 0 / exit 0 |
| `tools/kb_build_1_3.py --check` | registry 1.3.0 up to date |
| `tools/kb_build_1_4.py --check` | registry 1.4.0 up to date (48 rules; every test reference resolves to an existing test) |
| `rules/` | unchanged |

## 3. Tests

| Suite | Result |
|---|---|
| `tests/m9_p2b9` (new) | 46 passed |
| `tests/m9_kb` | 78 passed |
| `tests/m9_p2b8` | all passed (1 strict xfail by design, L-P8-01) |
| `tests/m9_p2b7` | all passed (2 strict xfail by design) |
| **full suite, clean clone at 065f3de** | see §4 |

Every run used a separate `--basetemp` and `python3 -I`.

## 4. Full suite (clean clone)

The suite ran from a fresh clone of the committed tree, with `data/inputs` linked to the private inputs. It is
compared test by test with the Phase 2B-8 run (clean clone at e603162).

*(filled in below once the run completes)*

## 5. Final snapshot

The final snapshot ran on the committed code of 065f3de. The later commits change documentation only; no engine, tool,
rule or knowledge file changed after 065f3de.

| Methods | Files | Differ | Run exits |
|---|---|---|---|
| V1 | 46 | 0 | |
| V2 – V2.6 (per method: 52, 70, 140, 176, 236, 248, 272) | 1,194 | 0 | |
| **V1 – V2.6 total** | **1,240** | **0** | 57 × exit 0 |
| V2.7 | 278 | **0** | 57 × exit 0 |
| V2.7.1 | 308 | **0** | 57 × exit 0 |

**V2.8 against V2.7.1 in the same snapshot** (`cmp_items`, item totals, line counts, states and ranges):

| Run | Lines | Changed items |
|---|---|---|
| reference plan, Mode A | 487 → 487 | ARCH.WALL_RUN 216.7625 → 216.9311 m (+0.1685); nothing else |
| reference plan, Mode U | 476 → 476 | the same single change |
| synthetic villa, Mode A (and its mirror) | 101 → 108 | FIN.SKIRTING 123.40 → 114.70 m certain, plus a range of 0 – 8.70 m (7 new BOUNDED_EXPOSURE lines) |
| synthetic villa, Mode U (and its mirror) | 101 → 105 | FIN.SKIRTING 86.70 → 80.70 m certain, plus a range of 0 – 6.00 m (4 new BOUNDED_EXPOSURE lines) |

The mirror runs equal the unmirrored runs on every changed item.

**V2.8 determinism.** V2.8 was run a second time on the same code: 344 files, **0 differ**, 6 × exit 0.

Between the interim snapshot and this one, V2.8's `BOQ_LINES` did not change on any run. The supporting outputs did
change, by design: the per-change records, the unclosed-label findings, the curved-wall arcs and the schedule-width
hold were added after the interim snapshot.

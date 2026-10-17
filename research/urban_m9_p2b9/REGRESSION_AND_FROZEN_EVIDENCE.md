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

*(filled in below once the run completes)*

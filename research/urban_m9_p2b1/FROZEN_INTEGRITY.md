# Frozen-version integrity evidence (deliverable 13)

Base of the phase: `8c24179` (Phase 2B-0 reports). All checks below were run on the working tree of the reporting
commit.

| Check | Command / method | Result |
|---|---|---|
| V1 / V2 / V2.1 / V2.2 outputs byte-identical | CLI runs of every frozen method on the synthetic villa, its mirror and the reference plan (V2.2 also with the heights facts), compared file by file with the snapshot taken at `8c24179` | **308 of 308 files identical** (repeated after the last code change) |
| Frozen artefacts | `python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl` | **0 artefacts differ** |
| Freeze import closures | `python3 -I tools/freeze_verify.py closure` | no file changed in this phase is in the import closure of any freeze manifest |
| Environment lock | `python3 -I tools/freeze_verify.py env` | matches `ENVIRONMENT_LOCK.json` (exit 0) |
| Rule store | `git diff 8c24179 -- rules/` | empty; `rules/` gains no file (`test_the_rule_store_gains_no_file`): the rule-store digest in V1 .. V2.2 RUN_RULES is unchanged |
| `engine/source/opening_census.py` | `git diff 8c24179 -- engine/source/opening_census.py` | empty (not edited) |
| Route G and the structural freezes | closure check + full suite (the same 377 baseline failures / errors, 0 new) | unchanged |
| V2.2 does not read the registry | a modified registry injected at run time | V2.2 lines identical; V2.3 follows the modified registry (`test_v2_2_never_reads_the_registry`) |
| V2.3 determinism | two complete CLI runs, 3 drawings x 2 modes | 176 of 176 files identical |
| Registry / index current | `tools/kb_build.py --check`, `tools/kb_index.py --check` | up to date |

## How V2.3 is isolated

- One opt-in method id, `ARCH_TAKEOFF_V2.3` (policy `URBAN_BOQ_M9_P2B1_ARCH_V2_3`); V2.3 implies the V2.2 / V2.1 / V2
  flags and adds its own (`owner_scope`, `door_height`, `decided_exterior`, `decisions`, `not_entrance_codes`).
- Changes inside shared modules (`arch_measure`, `arch_completeness`, `door_model`, `surface_ledger`, `boq_line`,
  `urban_boq_m9`) are behind those keyword flags with defaults equal to the V2.2 behaviour; the only unconditional
  additions are new constants (new flag-rule prefixes no earlier method emits, a new item code
  `FIN.MARBLE.THRESHOLD`), none of which appears in an earlier method's output - proved by the byte-identical
  snapshot.
- New behaviour lives in new modules: `knowledge.py`, `space_model.py`, `door_standards.py`, `owner_finish_scope.py`,
  the registry under `knowledge/` (outside `rules/`), and the tools `kb_build.py` / `kb_index.py`.

## History

No history was rewritten on the shared branch. The phase adds commits on top of `8c24179`.

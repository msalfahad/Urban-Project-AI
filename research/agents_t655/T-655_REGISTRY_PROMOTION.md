# T-655 gate fix: T-423 and T-563 promoted in BOQ_FAMILY_MASTER 1.62.0 + the t199 first-writer helper

GAP 1 (F-C-T563-1): `tests/t485_registry_promotion::test_a_merged_package_never_stays_pending_in_the_newest_registry`
red on the working branch (62e18eed, e04d99d9): T-423 r3 (ARCH_TAKEOFF_V3.0.60, merge 62e18eed) and T-563
(ARCH_TAKEOFF_V3.0.61, merge e04d99d9) still pending in 1.61.0, the newest registry. GAP 2 (F-T314-2): the t199 1.25.0
guard dropped a code whose FIRST writer is a module newer than 1.25.0 even when an own-head file writes it too.
Registry and one test helper only: no method version, no line, no quantity, no rule, no owner decision moves; released
default V2.9 + route G untouched.

## What was run (inside the wrapper, worker 2, 2026-11-09)

1. Drive copies (folder "Urban BOQ private data" / project subfolder, 'P7757_DXF_COMPRESSED.zip' and
   'ST7757 dxf.dxf'), decoded by `agent_env.sh decode` into the private folder only (sha256 ab54dd55 / 9f9d1179).
2. `run research/agents_t167/v304_run.py`, then `run research/agents_t563/v3061_run.py` (unchanged; its own asserts on
   V3_0_59 and V3_0_60 pass): V3_0_59 **75331a76** -> V3_0_60 **8c8a9642** -> V3_0_61 **2bc99980**, 5,073 lines each
   (the T-423 r3 and T-563 Gate B figures reproduced exactly; V3_0_58 c9570e6c on the way).
3. `t479_registry_census.py` (unchanged; verdict set board verdicts/V3.0.44 b3b08dd7, T-469 downgrade snapshot
   81732639): on V3_0_59 it reproduces research/agents_t651/out/LINE_INDEX_V3_0_59.json byte for byte; on V3_0_61 ->
   out/LINE_INDEX_V3_0_61.json, 5,073 lines, issues {}, complete map, 0 stale blocks against 1.61.0.
4. `t655_package_families.py` (T-483 attribute unchanged, chain (59, 60, 61), master 1.61.0): V3.0.60 (T-423):
   B3-01 FIN.FLOOR.PORCELAIN ~1, B3-04 FIN.MARBLE.THRESHOLD ~14 (record-only B4-01, B4-03, B5-01); V3.0.61 (T-563):
   B4-03 FIN.PLASTER ~11; 0 added, 0 removed.
5. `t655_promotions_source.py` (T-483 / T-485 rules unchanged, master 1.61.0, board b3bb1535): T-423 merge 62e18eed,
   T-563 merge e04d99d9, verdict heads quoted verbatim.
6. `build_master_1_62_0.py --write` / `--check` (T-483 r2 promotion functions unchanged, constants of this
   promotion), `write_manifest.py` (tools/m9_rules_manifest.build; one AUTHORED line added).

## Diff 1.61.0 -> 1.62.0 (asserted in tests/t655)

- Moved: version, supersedes, source, v3_0_candidate head, candidate (V3.0.61, as of T-563), candidate_packages
  (+T-423, +T-563; earlier entries an unchanged prefix), pending_packages ([]), per-family candidate blocks (method
  version; B3-01 / B3-04 / B4-03 re-derived), candidate_census (V3.0.61, 5,073 lines), promotion.
- Unchanged: candidate_state_counts (52 / 14 / 6 / 32) and in_v3_0_candidate_counts: no family changes state; every
  family field other than its candidate block; every other top-level field byte-identical.
- B4-03 census moves (FIN.PLASTER: 4 lines RELEASED -> HELD and 7 held ranges restated by T-563's plaster height, as in
  its Gate B run); B4-03 stays INTEGRATED_IN_CANDIDATE_AND_TESTED (released lines
  remain).

## t199 helper (F-T314-2)

`tests/t199_formwork_metalwork/test_family_master_1_25_0.py` `_own_head(written, extra=None, newer=None)`: a code whose
first writer is a newer module is kept with its first writer AMONG the own-head files (re-found in scan order); only a
code written by newer modules alone is set aside. Same strength: every code an own-head file writes is still checked.
Checked on the T-314 stage head 080ccaa5: the old helper fails test_1_25_0_every_written_item_code_..._full_strength,
the new one passes (27/27). Normal + two adverse tests added (t655_* in that file).

## Findings (text only, not fixed here)

- F-T655-1: tests/t328_roof_buildup/test_family_master_1_26_0.py (and t284 1.27.0) carry the same `_own_head` pattern
  (first writer, then drop if newer); latent until a newer module sorts first as writer of one of their codes. Same
  fix if it ever bites.

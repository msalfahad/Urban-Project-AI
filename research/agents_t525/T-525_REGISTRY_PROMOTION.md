# T-525 gate fix: T-507 promoted in BOQ_FAMILY_MASTER 1.57.0 (R-T485-1)

GAP: `tests/t485_registry_promotion::test_a_merged_package_never_stays_pending_in_the_newest_registry` red on the
working branch (af50c864): T-507 (ARCH_TAKEOFF_V3.0.58, merge c94b35c1, Verifier 2026-11-05 02:22 Gate B PASS) was
still in `pending_packages` of 1.55.0 and of 1.56.0 (T-637 carried it; its promotion needs the chain-run line diff).
The row named 1.56.0 as the new file; T-637 took that number, so this is 1.57.0 on 1.56.0 (1.56.0 never edited).

## What was run (inside the wrapper, owner allow-list of 2026-11-07)

1. Drive copies (folder "Urban BOQ private data" / project subfolder, files 'P7757_DXF_COMPRESSED.zip' and
   'ST7757 dxf.dxf'), decoded by `agent_env.sh decode` into the private folder only (sha 9f9d1179 / ab54dd55).
2. `run research/agents_t167/v304_run.py` (base run), then `run research/agents_t507/v3058_run.py` (unchanged):
   V3_0_56 4e25c54f, V3_0_57 **25a8b406** (candidate of record, asserted), V3_0_58 **c9570e6c**, 4,994 -> 4,999
   lines (5 ADDED, 4,994 SAME): the T-507 Gate B figures reproduced exactly.
3. `t525_package_families.py` (T-483 attribute, chain (57, 58), master 1.56.0): only B8-06 changes:
   FIN.WP.ROOF +2 -0 ~0, FIN.WP.ROOF_UPTURN +3 -0 ~0; no record-only family.
4. `t479_registry_census.py` (unchanged) with the V3.0.44 verdict set and the T-469 downgrade snapshot: on V3_0_57 it
   reproduces research/agents_t507/out/LINE_INDEX_V3_0_57.json byte for byte; on V3_0_58 -> out/LINE_INDEX_V3_0_58.json,
   4,999 lines, issues {}, complete map.
5. `t525_promotions_source.py` (T-483 rules unchanged, master 1.56.0, board 1127edae): T-507 merge c94b35c1, verdict
   head quoted verbatim.
6. `build_master_1_57_0.py --write` / `--check` (T-483 r2 promotion functions unchanged, constants of this promotion),
   `write_manifest.py` (tools/m9_rules_manifest.build, AUTHORED entry added; no hand digest).

## Diff 1.56.0 -> 1.57.0 (asserted in tests/t525_registry_promotion)

- Moved: version, supersedes, source, v3_0_candidate head, candidate (method V3.0.58, as of T-507),
  candidate_packages (+T-507, earlier entries an unchanged prefix), pending_packages ([] : T-525 adds no package),
  per-family candidate blocks (method / basis text; state moves on B8-06 only), state counts, candidate_census
  (V3.0.58, 4,999 lines; every family but B8-06 census-identical), promotion.
- Byte-identical: released_configuration, capability fields, item_code_scan, not_a_boq_line_codes, every T-637 field
  (t637, trade_key_crosswalk, B9-04 / B9-01 / B6-08 ownership), every family field other than its candidate block.
- B8-06: IN_CANDIDATE_BASE_LINES -> INTEGRATED_IN_CANDIDATE_AND_TESTED, packages [T-507]; released in the candidate
  m2 204.112 -> 209.018867 (4 lines), lm 181.589 -> 186.782544 (4 lines); held m2 2 lines (1 blank, bounded
  0 .. 0.639573), lm 3 lines (1 blank, bounded 0 .. 4.028279), never 0, never summed. Counts 50/14/7/33 ->
  51/14/6/33. No quantity, capability or owner change; released default V2.9 + route G untouched.

## Finding for the Checker (text only, not fixed here)

F-T525-1: `build_master_1_48_0.touched_block` keeps the earlier 'open' sentence of a family that leaves
IN_CANDIDATE_BASE_LINES ('no verified piece integrated; the lines are the base run's ... held in the candidate: m2 1
lines'), so the B8-06 'open' text now carries that stale sentence before the new V3.0.58 held text. State, packages,
released and held figures are right. Kept as is because the row requires the T-483 functions unchanged (precedent:
every promotion since 1.48.0); a fix is a new promotion-function version (Lead to row it if wanted).

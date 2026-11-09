# T-651 gate fix: T-498 promoted in BOQ_FAMILY_MASTER 1.59.0 (R-T485-1)

GAP: `tests/t485_registry_promotion::test_a_merged_package_never_stays_pending_in_the_newest_registry` red on the
working branch (abc71ec6, still red on 57db7053): T-498 (ARCH_TAKEOFF_V3.0.59, merge 4c37ce2c, Verifier 2026-11-09
05:54 Gate B PASS) was still in `pending_packages` of 1.58.0, the newest registry. Same pattern T-525 fixed for T-507.
Registry only: no method version, no line, no quantity, no rule, no owner decision moves; released default V2.9 +
route G untouched.

## What was run (inside the wrapper, worker 3, 2026-11-09)

1. Drive copies (folder "Urban BOQ private data" / project subfolder, 'P7757_DXF_COMPRESSED.zip' and
   'ST7757 dxf.dxf'), decoded by `agent_env.sh decode` into the private folder only (sha256 ab54dd55 / 9f9d1179).
2. `run research/agents_t167/v304_run.py` (base run), then `run research/agents_t498/v3059_run.py` (unchanged):
   V3_0_58 **c9570e6c** (candidate of record, asserted) -> V3_0_59 **75331a76**, 4,999 -> 5,073 lines
   (74 ADDED, 4,999 SAME, 0 replaced): the T-498 Gate B figures reproduced exactly.
3. `t479_registry_census.py` (unchanged; verdict set board verdicts/V3.0.44 b3b08dd7, T-469 downgrade snapshot
   81732639) against 1.58.0: on V3_0_58 it reproduces research/agents_t525/out/LINE_INDEX_V3_0_58.json byte for byte;
   on V3_0_59 -> out/LINE_INDEX_V3_0_59.json, 5,073 lines, issues {}, complete map.
4. `t651_package_families.py` (T-483 attribute unchanged, chain (58, 59), master 1.58.0): B9-01 MAS.UNITS.BLACK +20,
   MAS.UNITS.WHITE +17; B9-04 MAS.GLUE.AAC +17, MAS.MORTAR.BLACK +20 (all added, 0 removed / changed); no record-only
   family.
5. `t651_promotions_source.py` (T-483 / T-485 rules unchanged, master 1.58.0, board 47f91ce3): T-498 merge 4c37ce2c,
   verdict head quoted verbatim.
6. `build_master_1_59_0.py --write` / `--check` (T-483 r2 promotion functions unchanged, constants of this
   promotion), `write_manifest.py` (tools/m9_rules_manifest.build; one AUTHORED line added, as T-525 / T-637 / T-498).

## Diff 1.58.0 -> 1.59.0 (asserted in tests/t651)

- Moved: version, supersedes, source, v3_0_candidate head, candidate (method V3.0.59, as of T-498),
  candidate_packages (+T-498, earlier entries an unchanged prefix), pending_packages ([]), per-family candidate blocks
  (state moves on B9-04 only), state counts (51/14/6/33 -> 52/14/6/32), in_v3_0_candidate (B9-04 no -> yes; 64/33/7 ->
  65/32/7), candidate_census (V3.0.59, 5,073 lines; every family but B9-01 / B9-04 census-identical), promotion.
- B9-04 note: one dated sentence appended (1.59.0, T-651): first candidate lines, writer by file:line
  engine/source/arch_v3059.py:332 materials_for, :477 check_materials, tests/t498_block_materials/test_arch_v3059.py:94
  (resolved on this tree by the builder, refused if a pattern no longer resolves). Capability stays
  IMPLEMENTED_NOT_INTEGRATED: it describes the released V2.9 + route G, which reads none of MAS.MORTAR.BLACK /
  MAS.GLUE.AAC.
- Byte-identical: released_configuration, capability fields, item_code_scan, not_a_boq_line_codes, every T-637 field,
  every family field other than its candidate block (and the B9-04 note above).

## Engineering figures carried (candidate V3.0.59; unchanged from the T-498 Gate B package)

| family | released in the candidate | held (never 0, never summed) |
|---|---|---|
| B9-01 (units) | MAS.BLOCK etc. m2 467.7925 (13 lines, unchanged); black 0.20 units **1,075.80 pcs** (2 lines: GF 62.164 x 12.5 = 777.05, 1F 23.9 x 12.5 = 298.75) | pcs 35 lines (18 black on held hosts / 0.15 m, 17 white: AAC face not selected) |
| B9-04 (mortar / glue) | black mortar **1.269444 m3** (86.064 m2 x 0.01475, PROVISIONAL joint); AAC glue **43.596 kg** (20.061 + 23.535) | m3 18 lines blank; kg 15 lines (12 blank, 3 bounded 842.06025 .. 861.32025 kg) |

Freelancer: blockwork in m2 only; no unit / mortar / glue row: RULE_DIFFERENCE, no %.

## Findings (text only, not fixed here)

- F-T651-1 (same cause as F-T525-1): `build_master_1_48_0.touched_block` keeps the earlier 'open' sentence of a
  family it moves, so B9-04 'open' still begins 'no candidate line; the released capability above is unchanged' before
  the V3.0.59 held text. State, packages, released and held figures are right. Kept because the promotion functions
  must stay unchanged (every promotion since 1.48.0); a fix is a new promotion-function version.
- F-T651-2: B9-01 `opt_in_readers` still says 'pending Gate B' for T-419, T-488 and T-498 (all merged and promoted);
  that field has never been restated by a promotion. Left byte-identical (the row's diff scope); a restatement is its
  own registry row if wanted.

## Validation (task head)

Targeted: tests/t651 (16) + t485 + t525 + t498 + t637 PASS (t485 stale-pending guard green: was ['T-498']). Freeze 0
differing; codemap check clean; build_master --check equal, 0 problems; manifest check []. L4: every test folder and
root test file, run in two halves (odd / even folders, 2 CPUs): FAILED only the t374 baseline pair
(test_development_villa_schedule_reproduces_the_committed_record, test_schedule_built_on_the_v2_copy_equals_the_committed_schedule)
plus t647::test_outputs_current and t649::test_training_villa_is_the_committed_rebuild, which are ORDER-DEPENDENT and
not this change: both pass alone on this head, and `pytest tests/t645 tests/t646 tests/t647/test_t647.py
tests/t649_manifest_v18/test_t649.py` fails the same two on the BASE engine tree 57db7053 (no T-651 file).

- F-T651-3 (test hygiene, for the Lead): research/agents_t645/t645_rules.py (and ~18 other research rule modules)
  set the GLOBAL decimal precision at import; t647 / t649 compare Decimal text, so they fail whenever t645 runs before
  them in the same process without t646 re-setting it (the serial alphabetical order hides it). Same class as the
  T-648 r2 local-context fix; a fix row would give each rule module a local Decimal context.

Lessons row (proposed, ERS s.7): "a Gate B merge that adds a pending package to the newest registry is followed in the
same Verifier slot by its promotion version (or the merge carries it), so t485 never goes red on the working branch
(every villa; T-525, T-651)".

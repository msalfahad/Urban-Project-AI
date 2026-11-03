# T-485 Registry promotion (lane I, worker 3, non-candidate)

Scope (BOARD T-485, from T-479 finding F-T479-1, ENDORSED): promote every merged candidate package out of
`pending_packages` with its merge commit and Checker verdict, refresh the family `candidate` blocks to the candidate of
record V3.0.45, and state B8-07 / B9-02 as having no candidate line with the row that fills them. Registry only: no
engine, method, line, capability or owner field moves; 1.41.0 is never edited.

## Inputs (pinned)

| Input | Pin |
|---|---|
| Base registry | rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json (T-419 merge af1eaeb4, merged during this run: this package is READY second and rebased on it, Lead merge-order rule; the first build on 1.41.0 is in the WIP commit) |
| Candidate chain run | own run this session from the Drive copies ("Alsenan chalet project" / P7757_DXF_COMPRESSED.zip and "ST7757 dxf.dxf", structural sha256 9f9d1179...): research/agents_t167/v304_run.py then research/agents_t478/v3045_run.py and research/agents_t419/v3046_run.py, outputs in .work/private only. Every version file V3_0_7 .. V3_0_46_BOQ_LINES.json reproduced; the ones the board pins agree: V3.0.37 733f2efb, .38 57cca61c, .42 1793266d, .43 6f534d5e, .44 8b2fe2b6, .45 5972888b, .46 **35d70129** (= candidate of record, 4,867 lines) |
| Merge commits | git history of the working branch at 12395ea4 (research/agents_t485/t485_promotions_source.py): for each pending package exactly one merge whose second parent holds its task commit and whose first parent does not (out/PROMOTIONS_SOURCE.json; re-checked by the tests with git) |
| Verdicts | head of the Status cell of each row, BOARD.md / BOARD_ARCHIVE.md at agents/control 26ad2473, quoted verbatim; each cites the merge commit found in git (asserted) |

## What changed (files)

- `research/agents_t485/t485_package_families.py`: line diff V3.0.(n-1) -> V3.0.n per item code (added / removed /
  changed in quantity or state / RECORD-only: notes, calculation text, rfi text, source, project identity, deduction
  listing) -> families by registry ownership. Output `out/T485_PACKAGE_FAMILIES.json`: item codes, counts, sha256 only.
- `research/agents_t485/build_master_1_43_0.py` -> `rules/coverage/BOQ_FAMILY_MASTER_1.43.0.json` (+ `--base / --version`
  for a rebase at merge: a later pending package, e.g. T-443, stays pending).
- `research/agents_t485/out/LINE_INDEX_V3_0_46.json`: the T-479 census tool's line index of the merged V3.0.46 run
  (line id, item code, unit, class, engine id, net, bounds, binding only), so candidate_census is V3.0.46.
- `research/agents_t485/t485_accounting.py` + 14 older registry tests (1.25.0 .. 1.38.0): they asserted that a newer
  registry carries a pending entry UNCHANGED; rule r3 says the next version after the merge PROMOTES it. They now
  accept exactly the entry unchanged OR its promoted record (same task, version, module, task commit, inputs, tests,
  plus a 40-hex merge commit and a Checker verdict); nothing weaker (adverse test in t485).
- `rules/RULES_MANIFEST.json` + `tools/m9_rules_manifest.py`: one AUTHORED line. `docs/CODEMAP.md` by the tool.
- `tests/t485_registry_promotion/` (23 tests: synthetic villa K485 by hand + the committed registry and run index).

## Result (1.42.0 -> 1.43.0)

- 39 packages (T-231 V3.0.8 .. T-419 V3.0.46) promoted; candidate_packages 8 -> 47, pending 39 -> 0; candidate
  V3.0.7 / T-193 -> V3.0.46 / T-419. `tools/family_master_candidate.py check` with git: 0 problems.
- Candidate states (103 families): INTEGRATED 13 -> 44, HELD 3 -> 13, BASE_LINES 34 -> 10, NOT_IN_CANDIDATE 53 -> 36;
  in_v3_0_candidate yes 50 -> 67, no 53 -> 36. stale_in_candidate_vs_registry 21 -> 0. Census re-run on V3.0.46 (4,867 lines = 4,861 + T-419's 6 held-blank
  lines): 0 outside every family, 0 doubly mapped; only the families T-419 moved differ from the V3.0.45 census.
- B8-07 (FIN.WP.BALCONY) and B9-02 (STR.CONC.LINTEL): IN_CANDIDATE_BASE_LINES (1.2.0 .. 1.41.0) -> NOT_IN_CANDIDATE with
  `no_line` (no line of the code in any version V3.0.7 .. V3.0.45: item_code_presence) and filled_by T-486 / T-487.
- Record-only packages raise no state: T-245 (project identity, 3,699 lines), T-338 (line text, 366), T-246
  (deduction listings, 39), T-419's 5 pit-wall text restatements (B8-08); each family names them in
  `record_only_packages`.
- 41 families own no item code: state CARRIED from V3.0.7 and labelled `candidate_basis: CARRIED ...` (not re-derived).
- Declared vs measured: the package lists agree with the line diff except T-442, which declared B10-10 (STR.CONC.LIFT):
  the diff shows a RECORD-only change there (the CL-LIFT cause-text row), so B10-10 does not name T-442.

## Validation

See the board handoff (tests, freeze, codemap and the full suite on the final commit).

## Lessons row proposal

"A merged package never stays pending, and a family's candidate state is read from the candidate's lines (census +
line diff of a reproduced run), never carried from a package's text; text-only changes are recorded apart and never
raise a state" (R-T485-1; normal + adverse tests in tests/t485_registry_promotion).

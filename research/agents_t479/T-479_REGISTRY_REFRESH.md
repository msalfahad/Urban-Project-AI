# T-479 Registry and verified-share correctness (lane I, stream S, worker 3)

Scope (BOARD T-479): three findings of 2 Nov, registry / binding / reporting only. NO quantity changes: no engine,
hub, method, frozen or existing rule / knowledge version file is touched; every candidate line is byte-identical.

## Inputs (pinned)

| Input | Pin |
|---|---|
| Candidate of record | ARCH_TAKEOFF_V3.0.44 (T-422 merge b4e22291), reproduced in this run from the Drive copies ("Alsenan chalet project" / P7757_DXF_COMPRESSED.zip and "ST7757 dxf.dxf", structural sha256 9f9d1179...) with research/agents_t167/v304_run.py then research/agents_t422/v3044_run.py, outputs in .work/private only |
| V3_0_43 / V3_0_44 BOQ_LINES.json | 6f534d5e / **8b2fe2b6** (= the Checker's T-422 hashes and the boq_lines_sha256 of every record of verdicts/V3.0.44/URBAN_CHECKER_VERDICT_V2_SET.json) |
| Verdict set | board verdicts/V3.0.44/URBAN_CHECKER_VERDICT_V2_SET.json, sha256 b3b08dd7...; 9 records, all 9 BIND (none stale) |
| Downgrades | research/agents_t469/DOWNGRADES_SNAPSHOT.json (the T-469 / T-471 snapshot), sha256 81732639... |
| Registry | 1.40.0 (T-478, pending) -> 1.41.0 (this task; version allotted at merge) |
| Branch base | agents/task-T-478 r3 87676954 (Lead: build on the T-478 head), merged into the working head 2266198f |

## What changed (files)

- `research/agents_t479/t479_registry_census.py`: line-level census of a candidate against the registry: each line in
  exactly one bucket (family / NOT_A_BOQ_LINE / NO_FAMILY; a doubly owned code is listed under every owner and
  flagged), per family and unit released / held (bounded or UNKNOWN, never 0) / excluded and the verified share split
  VERIFIED_WHOLE vs VERIFIED_COMPONENT; UNBOUND_VERIFIED_LINE for a record that names a line it no longer binds;
  `compare_blocks` = STALE_IN_CANDIDATE (registry `in_v3_0_candidate` vs census). Families that own no item code are
  `n/a` (a register / run file / content under another family's code), never `no`.
- `research/agents_t479/out/LINE_INDEX_V3_0_44.json`: per line only id, item code, unit, class, engine element id,
  net, held bounds, binding (no drawing content, no names); reproduces the census without the private drawings.
- `research/agents_t479/build_master_1_41_0.py` -> `rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json` (1.40.0 never edited).
- `research/agents_t479/t479_completeness.py` (T-471 tool unchanged, re-run on 1.41.0 + register 1.1.0, line level) ->
  `out/T479_MATRIX_V3_0_44.json`, `out/EIMP_REGISTER_DEV_VILLA_1_1_0.json` (register 1.0.0 never edited).
- `tests/t479_registry_refresh/` (23 tests: synthetic villa K479 by hand + the committed registry / index).
- `tests/t478_blinding_integration/test_family_master_1_40_0.py::test_pending_dropped_is_stale`: judged as the newest
  registry (monkeypatched `newer_registry_modules`); without it any later registry that carries the pending entry
  forward hides the drop by rule r3. Same assertion, not weakened.

## Finding 1: two candidate lines outside every family -> 0

| Line | Code | Before (1.40.0) | After (1.41.0) | Quantity |
|---|---|---|---|---|
| L-0b3dce44cf70ae95ccd6 | EXT.POOL.WATER_FACE | no family (item_codes_without_family) | NEW family **B13-09** Pool / tank internal finish (water faces), m2, BLOCKED_BY_SOURCE | HELD BLANK, unchanged (finish printed on no sheet, T-309 / T-343) |
| L-5431fa278fbb44816a08 | ARCH.EXTERIOR | no family | **NOT_A_BOQ_LINE** (not_a_boq_line_codes, 3 evidence items) | 9.101 m2 information line, unchanged, reported apart |

Physical element first (ENGINEERING_REASONING_STANDARD s.1). The pool line is a finish on the water floor and walls: not
the pool waterproofing (B8-09), not the pool concrete (B10-10), not an outdoor floor (B13-02; owner rule 2026-10-21:
"the pool water is never a floor"): a family of its own. ARCH.EXTERIOR is the space register line written for a space
with no finish kind (engine/source/arch_measure.py:323, the exterior twin of ARCH.SPACE): an area, not work. OQ-04 is
answered A (owner 2026-10-21 20:25): outside finishes ARE in the BOQ, each as its own B13-02 finish line; the garden
band's floor / landscape classification is with the designer (D-48). So the register line stays information; if D-48
makes the band a floor, its finish is a NEW B13-02 line, never this line re-labelled (rule recorded in the registry).

Census V3.0.44 on 1.41.0: 4,858 lines, **0 outside every family, 0 doubly mapped**, 1 NOT_A_BOQ_LINE, issues {}.
T-471 completeness on 1.41.0 / register 1.1.0, LINE level: 105 components, **complete_map True, issues {}** (0
UNMAPPED, 0 DOUBLY_MAPPED, 0 REGISTRY_GAP). Register 1.1.0 also hands the STR.EARTH.* codes that B1-02 .. B1-04 gained
in 1.38.0 (T-350) to their single components (18 earthworks lines were UNMAPPED at line level on register 1.0.0, which
was built on 1.37.0); earthworks now APPLICABLE_HELD (12 + 5 + 1 lines, all held blank), not MISSING.

## Finding 2: stale candidate blocks of B8-08 / B10-13 / B7-13

Root cause (not only three families): no registry version since 1.3.0 has moved a merged package from pending_packages to
candidate_packages; **38 merged packages (V3.0.8 .. V3.0.45) sit in pending_packages** and every family's `candidate`
block is dated ARCH_TAKEOFF_V3.0.7 / T-193. tools/family_master_candidate.py refuses a family block dated after the
registry's candidate, so the three blocks cannot be rewritten alone. 1.41.0 therefore adds `candidate_census` (a fresh
census of the merged V3.0.44 run for every family, dated by its own version and lines sha256) and corrects the stale
reader text (opt_in_readers / note / v3_0_planned_tasks) with file:line evidence; the `candidate` blocks stay as of V3.0.7.

| Family | Registry 1.40.0 | Census V3.0.44 (= candidate_census 1.41.0) |
|---|---|---|
| B8-08 foundation WP | in_v3_0_candidate no; readers "V3.0.15 .. V3.0.31" | yes: 19 lines, 8 WP.FOUNDATION codes; m2 released 360.0282 (6 lines), held 9 UNKNOWN; m3 released 6.5275 (2), held 1; item held 1 |
| B10-13 formwork | no; "pending Gate B, T-199"; planned T-199 | yes: 612 lines; released 1,027.977403 m2 (244), held 368 UNKNOWN (= T-474's own figures) |
| B7-13 stair formwork | no; "pending Gate B, T-199" | yes: 31 lines; released 36.927436 m2 (10), held 20 UNKNOWN, excluded 1 |

Registry-wide (`stale_in_candidate_vs_registry`, 21 families): 19 say `no` but the candidate carries lines (B1-02,
B1-03, B1-04, B3-05, B5-04, B6-05, B6-06, B6-07, B7-10, B7-13, B7-15, B5-06, B8-08, B10-13, B13-01, B13-02, B13-04,
B13-08, B13-09) and 2 say `yes` with **no line in the candidate at any version 3.0.7 .. 3.0.44**: B8-07 (FIN.WP.BALCONY)
and B9-02 (STR.CONC.LINTEL) (checked on the reproduced V3_0_7, _8, _20, _30, _44 files). 41 families own no item code
and are `n/a`.

## Finding 3: B8-08 verified share, 7 of 7 lines bound

| Line | Code | Unit | Engine = Checker | Record | Binding |
|---|---|---|---|---|---|
| L-e11f17bb076058bf172d | LIFT_PIT_SCREED | m2 | 20.700 | V2-9f029e94d0e48eb3 | VERIFIED_WHOLE |
| L-e4789d76efedbc351bd4 | LIFT_PIT_SCREED | m3 | 1.035 | V2-dd65ca4b92b3d040 | VERIFIED_WHOLE |
| L-69e6e6d74707afe3ac5b | FOOTING_MEMBRANE | m2 | 109.850 | V2-cc6adb6445f61d7a | VERIFIED_COMPONENT |
| L-e6280a91646613667b62 | FOOTING_SCREED | m2 | 109.850 | V2-8b688b9cd8c8c5c5 | VERIFIED_COMPONENT |
| L-4ec54f9922da7281573a | FOOTING_SCREED | m3 | 5.4925 | V2-bc42437abbd55199 | VERIFIED_COMPONENT |
| L-d3ec19448415e0a0f083 | LIFT_PIT_MEMBRANE | m2 | 47.430 | V2-755ac5b090ff09c8 | VERIFIED_COMPONENT |
| L-1f3aaafcc460173462d9 | LIFT_PIT_BOARD | m2 | 26.730 | V2-5ee431685da6dd56 | VERIFIED_COMPONENT |

Component total 109.85 + 109.85 + 47.43 + 26.73 = **293.86 m2** and **5.4925 m3**, as the T-353 note says. Why
COMPONENT and not WHOLE: tools/boq_export_v1.bind_verdict makes WHOLE require every line of the group (trade, item code,
unit); each of these groups also holds a HELD line (F10 / F pair 1B1B BLOCKED_RFI; pit walls D-43), which no verdict can
bind (a held line has no quantity). A COMPONENT record binds exactly one line with engine qty = that line's net, so
each LINE's quantity is independently verified; the GROUP is not (owner 20:59). The census therefore reports both,
apart, never summed: B8-08 m2 whole 20.700 + component 293.86, m3 whole 1.035 + component 5.4925; no line unbound.
For the Checker's SCOREBOARD v2 restatement: a column "verified lines (COMPONENT, whole line)" beside the WHOLE share,
from `candidate_census.families[*].units[*].verified_component*`; registry-wide 6 such lines (B8-08 5, B10-04 1).

## Validation

- tests/t479_registry_refresh 23 passed; the 41 folders holding a test_family_master_* test + t130 / t140 / t236 /
  t469 / t471 / codemap: all passed (after the codemap rebuild); tools/family_master_candidate.py check 1.41.0: 0
  problems; builder --check reproduces; freeze 0 differing; codemap stale none. Full suite: see the commit message.

## Not done / proposals

- F-T479-1 (proposal for the Lead): one registry version that promotes the 38 merged pending packages to
  candidate_packages (merge commit + Checker verdict each, from the board) and re-derives every `candidate` block from
  `candidate_census` plus the packages' changes_families_by_item_code (empty for V3.0.16 .. V3.0.36: needs the
  package records read). Until then `candidate_census` is the statement of the candidate.
- F-T479-2: B8-07 balcony WP and B9-02 lintels emit no candidate line at all (registry says IN_CANDIDATE_BASE_LINES).
- Lessons row proposal: "a registry statement about the candidate is checked against a line census of the candidate,
  never carried from an earlier package's text" (rule R-T479-1; normal + adverse tests in tests/t479_registry_refresh).

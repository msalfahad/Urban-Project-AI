# Phase 2A overnight sprint: engineering report

**Branch:** `claude/access-permissions-setup-ii24ws`
**Commits:** from `70835ea` (round-2 notes) to `2a34281` (code); the reports follow in the commit after it
**Environment:** CPython 3.11.17, 63 locked packages (`research/freeze_integrity/ENVIRONMENT_LOCK.json`)

Every Phase 2A change is opt-in behind `--method ARCH_TAKEOFF_V2.1`.

**What did not change:**
- V1, V2, route G, the historical BOQs and every frozen package;
- `engine/source/opening_census.py`, and no source pin was relaxed;
- the benchmark files, the owner rule files, the repository settings.

**Release language:** no prices and no accuracy percentage. The gate stays INCOMPLETE and every line is MACHINE_ONLY.

**Labels:**

| Label | Meaning |
|---|---|
| **[VERIFIED]** | reproduced by a test or a recorded command |
| **[REFERENCE PLAN]** | measured on the private reference drawing; aggregate values only |
| **[OWNER]** | needs an owner decision |

## 1. Executive summary

- **Phase A, freeze integrity: done.**
  - The out-of-tree verifier passes in the lock: run V0R reports 158 BYTE_IDENTICAL, 5 SKIPPED, repository unchanged **[VERIFIED]**.
  - A rebuild cannot overwrite its comparison baseline, for three reasons:
    - it runs in a disposable worktree, one test at a time, from a pristine tree;
    - it compares against git objects;
    - an index guard fails any session that rewrites a frozen artefact.
  - The comment-only mutation (MT-1) was reproduced in two forms.
    - Without a re-pin, every downstream rebuild is refused by its own pin check.
    - With a re-pin, the edit still cascades through the freeze graph (finding F-10).
  - The behaviour-changing negative control (MT-2) is detected.
- **Phase B, robust geometry: done in an unpinned module** (`engine/source/robust_geometry.py`).
  - The hybrid margin applies at the three reviewed sites only.
  - Decisions inside the margin are recorded as AT_THRESHOLD; past the float bound they are UNDECIDABLE.
  - Wall faces are projected along a mean axis, so gaps are found at any angle.
  - The frozen functions are called with `T − m`, so not one byte of a pinned file changed.
  - The frozen geometry reproduces `lintel_measure.openings` exactly.
  - One known limit: column outlines are found axis-aligned only, so a rotated plan loses its columns (F-9, kept as a strict xfail).
- **Phase C, doors: done.**
  - Every drawn door swing belongs to exactly one door element. This conservation is checked on every floor; a violation means exit 3.
  - States: CONFIRMED, PROVISIONAL or UNRESOLVED, each backed by typed evidence.
  - Three widths, each with its own source. A height only from a source, else BLOCKED.
  - The owner door classes: **DOOR.INTERNAL.PVC**, **DOOR.EXTERNAL.ALUMINIUM**, **DOOR.MAIN_ENTRANCE**, **LIFT_SYSTEM / LIFT_DOOR** (excluded).
  - Provisional doors appear in their own section and in no released total.
  - On the reference plan the door states are exactly the round-2 prediction: 21 confirmed (22 leaves), 6 provisional, 1 unresolved **[REFERENCE PLAN]**.
- **Phase D, surface ledger: done.**
  - It is read-only and uses the nine statuses.
  - The eligibility table ELIGIBILITY_V0 is a PROPOSAL.
  - Reveals and head soffits are never a confirmed omission. A kitchen is never reclassified as wet.
  - Every record without a line becomes a finding.
- **Phase E: done.**
  - Dimension cross-check: DIMLFAC is resolved per dimension (entity override, then style, then header). A stale or overridden dimension is reported, never used. No quantity changes.
  - Geometry discovery: fills from every block depth, every MINSERT cell, layer-0 content and SOLID / TRACE reach the plan as column evidence. 5 of the 8 lost-column variants are recovered; the other 3 stay review flags.
- **Phase F: done.** Results are in sections 4 and 7.

**What stays open, all owner or source items:**
- door heights (no door schedule);
- the main entrance (no entrance label on the reference plan);
- the material of the main entrance;
- whether a dimension may promote a provisional door;
- the eligibility table;
- reveal measurement;
- the kitchen's wet eligibility;
- the before / after review of the reference plan.

## 2. Commits and changed files

| Commit | What |
|---|---|
| `3d4dfe0`, `74eed6c`, `a1493b1` | P2-00 Stage 1: freeze integrity verification. Added files only. |
| `23cf674` | Stage 1 fix: the verified ref is resolved once (F-11); each test gets its own pytest temp root; repository changes are recorded |
| `21675b9` | P2-01 / P2-01b / P2-02: ARCH_TAKEOFF_V2.1 robust band-path geometry and the metamorphic suite |
| `6e513c1` | P2-03 / P2-04: door elements and the owner door classes; door schedule; workbook door sheets |
| `e760122` | P2-08a: the read-only surface ledger |
| `147b41b` | P2-09a / P2-05: the read-only dimension cross-check; fills read at every depth |
| `1a68eb7` | Findings register F-9 … F-16 (append-only) |
| `2a34281` | Doors: a lift door is never measured, even when a door-height source exists (after the full suite) |
| (the commit after `2a34281`) | Reports, before / after register, demo, Stage 1 report, addendum statuses |

**Changed files since `a1493b1`:**

| Kind | Files |
|---|---|
| **New, engine** (stdlib only) | `engine/source/robust_geometry.py`, `door_model.py`, `surface_ledger.py`, `dimension_evidence.py` |
| **New, tools** | `tools/arch_dimensions.py` (the ezdxf dimension reader) |
| **Changed, opt-in parameter only** | `engine/source/arch_plan.py`, `arch_rooms.py`, `arch_walls.py`: a keyword-only `geom=None` (`None` is the V1 / V2 call path, call for call) |
| **Changed, additive** | `engine/source/boq_line.py`: 3 door item codes. `engine/source/coverage_census.py`: the door codes in family B6-01. `engine/boq_room_workbook.py`: door sheets, written only when V2.1 door rows exist |
| **Changed, V2.1 branch** | `tools/urban_boq_m9.py`: the `ARCH_TAKEOFF_V2.1` method; the V1 / V2 branches are unchanged |
| **Changed, Stage 1 tooling** | `tools/freeze_verify.py` (ref resolution, temp roots); `tests/zz_freeze_integrity/test_fi_verifier_synthetic.py` (+1 test) |
| **New tests** | `tests/m9_p2a/` (6 files) |
| **Appended register** | `research/freeze_integrity/ENGINEERING_FINDINGS.jsonl` (F-9 … F-16) |

**Not touched:**
- `engine/source/opening_census.py`, `engine/source/lintel_measure.py`, `engine/source/topology.py`, `tools/urban_intake.py`;
- the route-G modules;
- every `research/*` frozen package and manifest;
- `rules/`, `data/`.

## 3. Stage completion matrix

| Phase | Item | State | Evidence / note |
|---|---|---|---|
| A | Exact Python 3.11.17 lock and dependency record | DONE | `ENVIRONMENT_LOCK.json` (63 packages); the verifier reports PASS only inside it |
| A | Out-of-tree rebuild verifier | DONE | `tools/freeze_verify.py rebuild`; 20 synthetic tests (`tests/zz_freeze_integrity`) |
| A | Immutable committed-baseline comparison | DONE | the hash-chained `FREEZE_BASELINE_INDEX.jsonl`; the session guard |
| A | Raw and behaviour hashes, with the provenance exclusions documented | DONE | `MASK_RULES` M1–M5 (`README.md`) |
| A | Test-session mutation guard | DONE | `tests/zz_freeze_integrity/test_zz_fi_session_guard.py` |
| A | Append-only errata and findings registers | DONE | E-001 … E-005; F-1 … F-16; the chain plus the git-history check |
| A | Comment-only mutation experiment | DONE | MT-1a and MT-1b, plus the negative control MT-2 (section 7) |
| A | Historical rebuild matrix | DONE | V0R: PASS, 158 BYTE_IDENTICAL, 5 SKIPPED |
| A | Gate: rebuilds cannot overwrite their own reference evidence | DONE | worktree, one test per session, git-object comparison, the index guard, the synthetic F-1 test |
| A | `opening_census.py` source pin not relaxed | DONE | the file is unchanged |
| B | Hybrid absolute plus float-bound margin | DONE | `robust_geometry.Geometry.margin` |
| B | AT_THRESHOLD records, UNDECIDABLE | DONE | `ARCH_GEOMETRY_DECISIONS.json`; tests AT-Q1-02 / 03 |
| B | The 100 mm, 300 mm and 500 / 400 mm sites only | DONE | the threshold census (AT-Q1-08) |
| B | Wall-axis projection at arbitrary rotations | DONE | MEAN_AXIS_V1; AT-Q1-04 (60 random angles per case and offset) |
| B | Translation, rotation, mirroring, unit-conversion and nesting tests | PARTIAL | openings invariant in every case; rooms invariant except a rotated plan with columns (F-9); nesting covered through the insert depth in the margin and the P2-05 variants |
| B | Equivalence with the frozen legacy path | DONE | frozen geometry = `lintel_measure.openings` and `layer_roles`, at 0°, 37.37° and in metres |
| B | Private-plan comparison | DONE | section 7 / register F-16 **[REFERENCE PLAN]** |
| C | Stable physical-element ids | DONE | unit- and translation-stable (test) |
| C | Swing-to-door-element conservation | DONE | every floor; exit 3 on violation |
| C | Double-leaf deduplication | DONE | one insert with two arcs; an exploded pair within 2 %; a near miss gives two elements and a REVIEW |
| C | CONFIRMED / PROVISIONAL / UNRESOLVED with evidence-linked transitions | DONE | `history` per element; a swing can never confirm |
| C | Width evidence: opening, frame, leaf | DONE | three fields with their sources; frame / closure disagreement above 2 mm gives a REVIEW |
| C | Door height evidence and area | PARTIAL | from facts only, with their authority; no door schedule or elevation reader exists, so heights are BLOCKED with the missing source named |
| C | PVC / aluminium / main entrance / lift classes | DONE | adjacency evidence; main-entrance reconciliation; lift doors and lift entrances excluded |
| C | Separate provisional-door section; no provisional or lift door in released totals | DONE | the DOORS / DOORS PROVISIONAL / LIFT DOORS (EXCLUDED) sheets; totals by formula; an area total reads BLOCKED, never 0 |
| C | The eight unmatched cases as regression evidence | DONE | reference: 21 + 6 + 1 exactly as predicted; the six nib cases stay PROVISIONAL; no nib rule |
| D | Read-only ledger with the nine statuses | DONE | `SURFACE_LEDGER.json` / `.csv` |
| D | ELIGIBILITY_V0 as a PROPOSAL; reveals not automatically payable | DONE | id, status and digest recorded; reveals UNRESOLVED_ELIGIBILITY |
| D | A missing eligible record is an engineering finding | DONE | injected-omission test (AT-Q3-04) |
| E | DIMENSION cross-check (DIMLFAC per dimension, defpoint vs shown value, openings, wall thickness, stale) | DONE | DXF path; no geometry override |
| E | DIMLFAC in the DWG adapter (`cad_adapter`) | NOT STARTED | header only (F-13) |
| E | Discovery: nested blocks, MINSERT, layer 0, SOLID / TRACE | DONE | as column evidence; 5 of 8 variants recovered |
| E | Discovery: hatch islands, arc-edged hatches in nested blocks | PARTIAL | the existing plan hatch reader keeps islands; discovery fills give their outer ring only |
| E | Route G not modified | DONE | the verifier (section 7) |
| F | Unit, villa, door, metamorphic and ledger tests | DONE | `tests/m9_p2a` |
| F | Historical freeze verifier at the final code commit | DONE | section 7 |
| F | Reference-plan before / after | DONE | section 7 |
| F | Identity / privacy and benchmark-firewall scans | DONE | section 8 |
| F | Full suite | DONE | section 4 |

## 4. Test counts and failures

**Full suite at `1a68eb7`** (CPython 3.11.17 in the lock; the reference-plan drawing provided through `URBAN_REAL_PLAN_DXF`; `-o addopts=`; 12 min 12 s) **[VERIFIED]**:

| Collected | Passed | Failed | Errors | Skipped | xfailed |
|---|---|---|---|---|---|
| 8,556 | **7,930** | 344 | 32 | 148 | 102 |

**Every one of the 376 failures and errors is a missing-private-data failure, and none is a regression [VERIFIED]:**
- **374** are `FileNotFoundError` on a gitignored `data/experiments/...` dataset (the PA-08 / PA-09 historical studies, absent in this container).
- **1** is a missing `data/experiments` output ("run workbook_boq first").
- **1** is a client upload from an earlier session, not present here.
- **The same 376 tests were rerun at the pre-sprint commit `a1493b1`:** 344 failed and 32 errors, identically.
- **0 code failures.**
- The total of 376 equals the M9 S1 test gate's `MANDATORY_BLOCKED_BY_MISSING_DATA` count.

**After the suite:** `2a34281` (lift doors are never measured) changes only `door_model.finalise` (V2.1 only) and adds one test. The affected suites (`tests/m9_p2a`, `tests/m9_s2_arch`, `tests/m9_s6`, `tests/zz_freeze_integrity`) pass at `2a34281`. The final verifier ran at `2a34281` (section 7).

**New Phase 2A tests** (`tests/m9_p2a`):

| File | Tests |
|---|---|
| `test_p2a_robust_geometry.py` | 45 + 1 strict xfail (F-9) |
| `test_p2a_doors.py` | 20 |
| `test_p2a_ledger.py` | 8 |
| `test_p2a_dimensions.py` | 8 |
| `test_p2a_discovery.py` | 13 |

## 5. Door BOQ demo [VERIFIED, synthetic]

The synthetic door plan (`tests/m9_p2a/p2a_helpers.door_fixture`) is regenerated by `research/urban_m9_p2a/demo_p2a.py`. The full tables are in `DEMO.md`.

**Without a height source:**

| Released total | Doors | Leaves | Width m | Area m² | Heights BLOCKED |
|---|---|---|---|---|---|
| DOOR.INTERNAL.PVC | 4 | 5 | 4.200 | BLOCKED | 4 |
| DOOR.EXTERNAL.ALUMINIUM | 1 | 1 | 0.900 | BLOCKED | 1 |
| DOOR.MAIN_ENTRANCE | 1 | 1 | 1.000 | BLOCKED | 1 |

**What the demo shows:**
- **The double door.** The 1.60 m double-leaf door (one insert, two arcs) is **one** PVC door with 2 leaves.
- **The lift door.** The lift landing door is LIFT_SYSTEM / LIFT_DOOR: excluded, not measured as a door.
- **The unresolved swing.** It closes no gap, so it is not released and raises an engineering finding.
- **The main entrance.** It is identified by the entrance word in the hall, and it is not also counted as aluminium.
- **With a sourced height** (facts `opening_heights.DOOR` = 2.10 m with its authority): PVC area 8.820 m², aluminium 1.890 m², main entrance 2.100 m².
- **With two entrance candidates:** no main-entrance line. Both candidates are withheld from the released totals, and a REVIEW `MAIN_ENTRANCE_AMBIGUOUS` is raised.

**Reference plan [REFERENCE PLAN], V2.1:**
- **Released doors:** 15 PVC and 3 aluminium. They replace the 20 `ARCH.DOOR` opening counts of V2.
- **Main entrance: REVIEW.** No external door carries entrance evidence; 2 plausible candidates are withheld.
- **Not released:** 1 confirmed door with an unresolved class, 6 provisional doors (the nib cases), 1 unresolved swing.
- **Heights:** all 18 released doors have BLOCKED heights; no door schedule is present.
- **Frame span:** 2 doors disagree with their closure by more than 2 mm (REVIEW).
- **Conservation:** holds on every floor.

## 6. Surface-ledger demo [VERIFIED, synthetic; REFERENCE PLAN aggregate]

| Status | Synthetic villa | Reference plan |
|---|---|---|
| MEASURED | 29 | 119 |
| PROVISIONAL | 11 | 55 |
| BLOCKED_MISSING_SOURCE | 27 | 106 |
| BLOCKED_OWNER_DECISION | 10 | 33 |
| UNRESOLVED_ELIGIBILITY | 29 | 135 |
| NO_EMITTER | 0 | 5 |
| CONFIRMED_MISSING | 0 | **0** |
| EXCLUDED | 0 | 3 |
| NOT_APPLICABLE | 0 | 0 |

**How to read the reference-plan column:**
- **UNRESOLVED_ELIGIBILITY (135).** Almost all are reveal and head-soffit records of doors, windows and passages: an owner decision is open and no emitter exists. 2 are passage thresholds, and 1 is the kitchen's wet eligibility. None is a BOQ omission.
- **NO_EMITTER (5).** Door threshold strips whose emitter stops on an engine limit (a strip not attributed to a room).
- **CONFIRMED_MISSING (0).** No record is missing where an owner-approved rule, a present source and an emitter all exist.
- **The injected-omission test** deletes one skirting line from the villa and gets exactly one CONFIRMED_MISSING, with its finding.

## 7. Historical compatibility verification

**Final out-of-tree verifier at `2a34281`** (the last code commit, with every Phase 2A module present) **[VERIFIED]**.

It ran in a private clone, inside the lock, with the reference-plan V1 baseline. The selection:
- every historical freeze rebuild and re-run;
- `tests/m9_s6`: V1 / V2 behaviour, including the reference-plan V2 tests;
- the opening-census unit tests;
- the reference-plan V1 takeoff against its 16 recorded output hashes.

| Run | Overall | Tests run | Verdicts | Repository unchanged | Environment lock | Patches | Repins |
|---|---|---|---|---|---|---|---|
| VFINAL (2a34281) | **PASS** | 162 | BYTE_IDENTICAL 158, SKIPPED 5 | True | matches | 0 | 0 |

### VFINAL (2a34281): every test that is not BYTE_IDENTICAL (5)

| Test | Verdict | Rewritten files: raw / behaviour / masks | Builder error |
|---|---|---|---|
| `tests/structural_census/test_multi_engine_s3_1.py::test_rebuild_reproduces_committed_outputs` | SKIPPED | - | freelancer reference workbook is client data (not in git) |
| `tests/coverage_recovery_engine/test_coverage_round.py::test_rebuild_reproduces_frozen_outputs` | SKIPPED | - | local data/ inputs not present (gitignored) |
| `tests/r9_1_chris_post_freeze/test_r9_1_package.py::test_rebuild_byte_for_byte` | SKIPPED | - | frozen christiannp dataset not present |
| `tests/test_pa09_{R}_regression_r7.py::test_an_identical_rerun_changes_no_identity` | SKIPPED | - | run research.qs_wall_treatment_01.pa09.{R}.regression_r7 first |
| `tests/m9_s6/test_s6_tolerances.py::test_a_drafted_100_mm_face_piece_survives_in_a_metre_drawing` | SKIPPED | - | S6 Phase 1 open finding (S6P1-NEW-05): a lower length threshold equal to a drafted dimension (the 100 mm minimum face pi |

**V1 and V2 outputs are unchanged.** The V1 synthetic snapshot, the reference-plan V1 hashes (16 / 16), the V2 tests and every freeze are byte-identical with the V2.1 code present. The 5 skips need private datasets that are absent; they are the same 5 as in run V0R at `23cf674`.

**Stage 1 mutation runs** (at `23cf674`; `research/freeze_integrity/STAGE1_REPORT.md`, section 5):
- **MT-1b, comment only:** 12 downstream rebuilds REFUSED_BY_SOURCE_PIN.
- **MT-1a, comment plus re-pin:** 10 BUILD_FAILED and 2 BEHAVIOUR_CHANGED, through the manifest-pin cascade (F-10).
- **MT-2, behaviour change:** detected by 16 tests, including the reference-plan V1 hashes and the route-G live rebuilds.


**Reference plan, V2 against V2.1 [REFERENCE PLAN]** (the register is `BEFORE_AFTER_REGISTER.csv`):

| What | Change |
|---|---|
| Gross floor plates | identical on every floor |
| Openings | doors 20 → 21 (U1 found by the robust predicate), windows 25 → 26, passages 12 → 12 |
| Lines | 426 → 427: `ARCH.DOOR` 20 → 0, replaced by 15 PVC + 3 aluminium released door lines; thresholds 38 → 39 and window reveal strips 25 → 26, from the new openings |
| Ground-floor wall run | +0.20 m |
| Next to the new openings | one unlabelled cell 1.64 → 1.56 m²; one skirting line 1.9 → 2.4 m (F-16, needs review) |
| Other area lines | differ in the 11th significant digit only (the mean-axis float path) |
| Threshold decisions recorded | 23 AT_THRESHOLD (FACE_PIECE 18, BAND_OVERLAP 4, OPENING_GAP 1); none UNDECIDABLE; no precision widening |
| Dimensions | 388; 294 usable; 92 not used (the shown value differs from the defpoints: stale / non-associative); cross-check 5 opening widths and 22 wall thicknesses, all AGREE; DIMLFAC from the dimension style for all 388 |
| Discovery fills merged | 207, with no effect on columns or rooms |

## 8. Engineering findings and missing-sources register

**Findings register:** `research/freeze_integrity/ENGINEERING_FINDINGS.jsonl` (append-only, hash-chained).

| Id | State | Finding |
|---|---|---|
| F-9 | OPEN | Column outlines are found axis-aligned only. A rotated plan loses its columns (all methods). |
| F-10 | OPEN | A single re-pin cannot absorb a comment-only edit of a pinned file: the S8.6 manifest bytes are pinned 10 times downstream, and 2 outputs copy upstream manifest hashes. |
| F-11 | FIXED | The verifier now resolves the ref once (`23cf674`). |
| F-12 | MITIGATED IN V2.1 | F-3, the angle-bin projection: the mean-axis face lines. |
| F-13 | MITIGATED IN V2.1 | F-7, DIMLFAC from the header: resolved per dimension on the DXF path. The DWG adapter still reads the header only. |
| F-14 | MITIGATED IN V2.1 | F-8, reveal / head soffit: these ledger records are UNRESOLVED_ELIGIBILITY with the NO_EMITTER condition. |
| F-15 | OPEN | A fixture docstring describes a door path that the engine no longer takes. |
| F-16 | OPEN | The reference-plan downstream changes await reviewer acceptance. |

**Missing sources:**

| Missing source | Effect | Where it shows |
|---|---|---|
| Door schedule, elevations or sections (door heights) | every released door: height and area BLOCKED; count and width kept | `DOOR_SCHEDULE`, `DOOR_HEIGHT_MISSING` findings, `UNRESOLVED.json` (one entry per floor) |
| A main-entrance label or site-plan entrance | DOOR.MAIN_ENTRANCE not identified; candidates withheld | `MAIN_ENTRANCE_UNRESOLVED` |
| Main-entrance material | NOT_ESTABLISHED | `DOOR_SCHEDULE` |
| Wall finish heights, window sill and head levels | unchanged from V2: BLOCKED_RFI lines | ledger BLOCKED_MISSING_SOURCE |
| The reveal-measurement decision, and a height / frame-position source | reveals and head soffits UNRESOLVED_ELIGIBILITY | ledger findings |

**Identity, privacy and benchmark-firewall scan [VERIFIED].**
- **What was scanned:** every file changed since `70835ea`, and these reports.
- **Patterns:** the hygiene regex, the extra private names, the two private ids, the 13 forbidden benchmark numbers (as given and ×1000), and Arabic outside the controlled lexicon.
- **Result:** 0 hits in the sprint's files. The only match is in the Stage 1 baseline index (`FREEZE_BASELINE_INDEX.jsonl`), which records the repository paths of the frozen packages. Those directory names already exist in the repository, so this is not a new exposure.
- **The private reference-plan evidence** (per-door states, the before / after line detail, the verifier reports) stays outside the repository.

## 9. Owner decisions needed

1. **Review the reference-plan before / after register.** Accept or reject each change: +1 door, +1 window, +0.20 m wall, the unlabelled cell and the skirting line.
2. **Door heights.** Provide the door schedule or elevations, or authorise a project fallback. A fallback would be recorded as ASSUMED and kept out of confirmed areas.
3. **The main entrance.** Name it, or say what evidence identifies it, and give its material.
4. **Dimension promotion.** May a usable dimension within 5 mm of the closure promote a provisional door to CONFIRMED? It is implemented, and off. The nib rule (P2-13) is still not introduced.
5. **ELIGIBILITY_V0.** Approve or amend the rows. The open rows are ceilings, landing marble, the window item, thresholds, reveals and head soffits, and the kitchen's wet eligibility.
6. **Stage 2.** Confirm the 0-line route: `opening_census.py` stays as it is, permanently.
7. **V2.1 as the default.** Not now. It needs the blind round (P2-12) first.

## 10. Exact next priorities

1. The owner review of the before / after register, with door heights and the main entrance (decisions 1–3).
2. The blind round P2-12: V2.1 against V2 on drawings the engine has not seen, with every changed line listed.
3. An oriented-rectangle column detector (F-9), behind a flag, with the metamorphic suite as its acceptance test.
4. A door schedule / elevation reader for heights, or a facts workflow that the owner fills.
5. The RFI register by distinct question (P2-06). It is not part of this sprint.
6. Threshold and reveal emitters, after decision 5.
7. DIMLFAC per style on the DWG path (F-13).
8. For any future pin migration: a transitive worktree re-pin, plus masks for copied manifest hashes (F-10).

## 11. Checkpoint and restart

**State:**
- Everything is committed and pushed on `claude/access-permissions-setup-ii24ws`.
- The private evidence is not in git: the reference-plan before / after, the door states and the verifier reports.

**To reproduce:**

```
python3 -I tools/freeze_verify.py check --index research/freeze_integrity/FREEZE_BASELINE_INDEX.jsonl
python3 -I tools/freeze_verify.py env --lock research/freeze_integrity/ENVIRONMENT_LOCK.json
python3 -m pytest -q tests/m9_p2a tests/zz_freeze_integrity
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.1
URBAN_REAL_PLAN_DXF=<drawing> python3 -I tools/freeze_verify.py --repo <clone> rebuild --ref <commit> --out <dir> \
    --lock research/freeze_integrity/ENVIRONMENT_LOCK.json --arch-baseline <private config>
```

**V2.1 outputs (OUT):**
- `ARCH_GEOMETRY_DECISIONS.json`;
- `DOOR_SCHEDULE.json` / `.csv`;
- `SURFACE_LEDGER.json` / `.csv`;
- `DIMENSION_CROSSCHECK.json`;
- the workbook sheets DOORS, DOORS PROVISIONAL, LIFT DOORS (EXCLUDED);
- everything V2 writes.

# Investigation E: frozen-history policy, defaults and migration

## E.1 Five things that are currently all called "frozen"

| Kind | What it is | Mutable? | How it changes | Example |
|---|---|---|---|---|
| **Immutable evidence** | source drawings and their hashes; owner decisions as issued; benchmark files (read post-freeze only) | never | only superseded by a new record that references the old one | the reference DXF sha; rule set 1.5.0 as approved |
| **Frozen results** | the bytes a released run produced, plus its manifest | never | known defects go in an **append-only errata register**, never into the files | M8 V6 outputs; S8.6 lintel package; the ARCH_TAKEOFF_V1 reference-plan outputs |
| **Production compatibility** | a released **method id** is a contract: same inputs → same output bytes | never, under that id | a new id | `ARCH_TAKEOFF_V1`; route G V6 conventions |
| **Corrected algorithms** | a fix to a defect in a released method | yes, as a **new method version** with a before/after record on every reference drawing | review, then a version bump | S6R-A1 robust predicates → `ARCH_TAKEOFF_V2.1` |
| **New versioned rules** | owner measurement rules | yes, as a new rule-set version (a separate axis) | owner approval | 1.5.0 → 1.6.0 (Q-S6-1, Q7, Q-S6-4) |

A run must record **both axes**: method id + version, and rule-set id + digest. Today:
- every line carries its rule-set digest;
- the method id is recorded once, in `RUN_RULES.arch.method`;
- the BOQ lines carry `rule.rule_id = ARCH_MEASURE_V3`, which is the measurement rule, not the takeoff method.

A line read on its own cannot say which method produced it.

## E.2 What is wrong with the current freeze mechanism

The freezes pin **source bytes**:
- the S8.6 build script's `CODE` digest over `opening_census.py`;
- M7 / M8 `00_ENGINE_FREEZE.json` `files_sha256` over `tools/urban_intake.py`;
- the S1 frozen-route test over `urban_boq_m2.py` / `urban_project_run.py`.

Phase 1 showed the cost:
- **A behaviour-neutral edit to a shared module is impossible.** Phase 1 had to add a parallel module (`opening_gaps.py`, a copy of `band_gaps` with one parameter) and run the K2 kernel a second time (`arch_discovery.k2_census`) rather than add a keyword argument to `urban_intake`.
- **Duplication is a drift risk.** Two copies of `band_gaps` must now stay equal at merge_tol = 1.0. A test proves the delegation, but every future fix must be made twice or not at all.
- **The freezes do not protect what matters.** A source digest says nothing about whether the frozen run is *correct* (Investigation A: the frozen V1 and route-G lintel evidence miss a door and a window). It only says the bytes did not change.

## E.3 Recommendation: freeze by behaviour, record source as provenance

1. Each freeze keeps a **behaviour manifest**: pinned inputs (by sha), the command, the method id, the rule-set digest and **output hashes**.
   - A test re-runs it and compares bytes.
   - This exists in part: the S8.6 double build; V1's byte tests in `tests/m9_s6/test_s6_frozen.py`.
2. **Source digests stay as recorded provenance** (what code produced the release), **not as an immutability lock on shared modules**.
   - A shared-module change is allowed when every behaviour manifest still reproduces byte for byte.
   - A change that alters any frozen output requires a new method version.
3. **An errata register per release** (append-only):
   - the known defect, its evidence and its effect on the frozen outputs;
   - the version that corrects it.
   - Example entries: S6R-A2 (V1 and route-G lintel evidence miss one door and one window on the reference plan) and S6R-B1 (8 drawn doors without door lines).
4. This is an **owner decision** (it changes how freezes are enforced). Until it is approved, Phase 2 keeps using parallel modules for V2.

## E.4 Should V1 strict become the default? Yes, after owner approval

**For:**
- 22 of 31 synthetic failure modes are silent under V1 and none under V1 strict.
- On every admitted drawing, the measurement and the 15 / 16 output files are byte-identical; strict adds only `DRAWING_DISCOVERY.json`.

**Against:**
- Drawings that "work" today get exit 2. The commonest is `$INSUNITS = 0`, which needs `--units mm`, recorded as REVIEW.
- That friction is intended: it is the unit question being asked, not guessed.

**How:**
- `arch` defaults to `--strict-admission`.
- `--legacy-admission` restores today's behaviour, writes a REVIEW finding `LEGACY_ADMISSION_REQUESTED`, and is recorded in `RUN_RULES`.
- The structural entry points are unaffected (frozen route).

## E.5 Should exit codes 2 and 3 stay separate? Yes

| Exit | Meaning | Who acts | Outputs |
|---|---|---|---|
| 0 | admitted and complete (REVIEW findings possible: read `readiness`) | reviewer | BOQ + discovery + coverage |
| 2 | **not admitted**: nothing measured; the drawing or the reviewer inputs must change | drafter / reviewer | discovery + `ADMISSION_BLOCKED` (+ conversion record) |
| 3 | **measured but not complete**: a surface or element is unaccounted; an engine defect or a missing rule | engineering | `COMPLETENESS_FAILED` + `diagnostics/` |

Merging them would lose the most useful routing signal: *fix the input* vs *fix the engine*. Two additions are proposed:
- a `readiness` field in `DRAWING_DISCOVERY.json` that automation can read (ADMITTED_COMPLETE / ADMITTED_WITH_REVIEW);
- extending exit 3 to the NSD-2 / 4 / 6 element and surface invariants of Investigation C.

## E.6 Migration plan

| Step | Change | Gate to proceed | Rollback |
|---|---|---|---|
| 0 (now, no code) | open the errata register; record S6R-A2 and S6R-B1 against V1 and route G | owner reads it | — |
| 1 | behaviour manifests for every freeze (inputs, command, output hashes) and re-run tests | all manifests reproduce on HEAD | remove the new tests |
| 2 (owner) | approve freeze by behaviour; source digests become provenance | owner decision | keep the parallel modules |
| 3 | Phase 2 as `ARCH_TAKEOFF_V2.1` (opt-in): robust predicates, fills from K2, door conservation; before/after on the synthetic suite and the reference plan | the must-fix acceptance tests (plan, P2-01..P2-05) | `--method ARCH_TAKEOFF_V2` (Phase 1) |
| 4 (owner) | V1 strict by default, with `--legacy-admission` | owner decision | flip the default back |
| 5 | blind round on a second, unseen villa with V2.1 | go / no-go criteria of the next milestone | stay on V1 strict |
| 6 (owner) | V2.x becomes the default; V1 stays callable by name forever | blind round passed | flip the default back |
| 7 (owner) | route-G / M4 lintel-evidence correction as a new route-G version, with its own before/after | owner decision | the previous route-G version |

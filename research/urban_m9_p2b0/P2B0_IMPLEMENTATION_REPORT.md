# Phase 2B-0: release safety and blind-test readiness, implementation report

**Status:** implemented on branch `claude/access-permissions-setup-ii24ws`, 2026-10-14.
- Start: `981ef5f` (Phase 2A acceptance).
- Code commit: `9875f40`. The reports follow in the next commit.
- The work stops at the release-safety acceptance gate. **The blind round and Phase 2B-1 have not started.**

**Method:**
- `ARCH_TAKEOFF_V2.2` is a new, opt-in method version: V2.1 plus the release-safety corrections.
- Policy id: `URBAN_BOQ_M9_P2B0_ARCH_V2_2`.
- `ARCH_TAKEOFF_V1`, `V2` and `V2.1` are unchanged. They are byte-identical to `981ef5f`: 168 of 168 output files, on two synthetic villas and the reference plan.
- Every new branch of code runs only when the method is `ARCH_TAKEOFF_V2.2`.

**Privacy:**
- Only aggregate values and generic descriptions appear here.
- The reference-plan per-door table, line-level diffs and instrumented runs stay outside the repository, following the Phase 2A precedent.
- Wall-finish numbers on the reference plan come from the synthetic TEST heights of `research/urban_m9_s2/SYNTHETIC_FACTS_S2.json`. They are counts of lines and states, not project quantities, and are never presented as quantities.

**Companion files:**

| File | Deliverable |
|---|---|
| `DEFECT_REGISTER_BEFORE_AFTER.csv` | (2) defect-by-defect before / after register, P2B0-01 … P2B0-12 |
| `TEST_RESULTS_AND_INTEGRITY.md` | (3) test results and regression classification; (4) frozen-version integrity |
| `BLIND_READINESS_CHECKLIST.md` | (5) blind-test readiness checklist |
| `OWNER_DECISIONS.md` | (6) remaining owner decisions |
| `NEXT_PHASE_RECOMMENDATIONS.md` | (7) prioritized recommendations, objections, reasons to delay the blind round |
| `FACTS_TEMPLATE_HEIGHTS.json`, `BLIND_READINESS_RECORD.json`, `make_readiness_record.py` | blind-round inputs and the hash freeze |

## 1. Starting-point verification (before any edit)

- HEAD was `981ef5f`, equal to `origin/claude/access-permissions-setup-ii24ws`, with a clean working tree.
- Each handoff claim was checked against the code. These held:
  - the V2.1 method path;
  - the `_one_sided_roles` 50 / 50 apportionment;
  - the full-width passage deduction in `arch_measure`;
  - the door classification by side probes;
  - the ledger statuses.
- **No divergence** was found between the handoff and the code.
- Baseline snapshot: V1, V2 and V2.1 CLI outputs at `981ef5f`, on the synthetic villa, its mirror and the reference plan. This is 168 files, kept privately and compared after every stage.

## 2. Design rule

The corrections add evidence; they never rewrite frozen logic.

- `engine/source/arch_rooms._faces_of` gains an optional `boundary_detail`, emitted only under `release_safety`. Per face, it records:
  - the boundary length of every role-set, for example `WALL`, `WINDOW+WINDOW_THRESHOLD` or `DOOR_CLOSURE`;
  - the length each band opening has on this face;
  - the closure lengths;
  - any edge shared by two openings.
- The role lengths that V1, V2 and V2.1 consume are not touched.
- `engine/source/release_safety.py` (new; stdlib-only, project-agnostic) turns that detail into:
  - wall-finish lines (F-24);
  - skirting lines (F-17).
- `door_model`, `surface_ledger` and `tools/urban_boq_m9.py` take one keyword each: `guards`, `conserve`, and the method switch. All three are off by default.

## 3. What was done, defect by defect

The full register, with failing-before and passing-after tests, synthetic and reference-plan numbers, invariance and owner actions, is `DEFECT_REGISTER_BEFORE_AFTER.csv`.

### P0, F-24: passage deductions

- **Defect:** a passage is deducted at its full width from every face that lists it. On an open plan, one 10.4 m passage listed by three faces is deducted 3 × 10.4 m. A face shorter than the passage goes negative, and the run stops with a `LineError`. The reference plan stops this way whenever heights are supplied.
- **Correction (V2.2):**
  - Each opening is deducted only by its own length on this room's boundary, multiplied by min(opening height, finish height). A passage runs the full height.
  - Every boundary is checked geometrically:
    - own length ≤ opening width + 1 mm;
    - no edge shared by two openings;
    - wall + band openings + undeducted openings = run (± 1 mm);
    - known deductions ≤ gross;
    - low ≥ 0.
  - A failed check gives `BLOCKED_RFI GEOMETRY_INCONSISTENT`, which is excluded from released totals. Nothing is clamped.
- **Synthetic, hand truth:**
  - Zone line at 6.0 m: the W.C. plaster was 20.40 m² (deducted 10.4 m) and is now 35.40 m² (deducted its own 5.4 m).
  - Zone line at 11.0 m: V2.1 stops; V2.2 gives W.C. 20.40 m² and DINING 49.20 m².
  - Openings meeting at a corner: each is deducted once (54.00 m²).
- **Reference plan, with test heights:**
  - V2.1 still stops (frozen). V2.2 runs.
  - 0 negative released lines; 0 `GEOMETRY_INCONSISTENT`.
  - Plaster: 16 released + 12 ranged + 2 stair-hall RFIs, of 30.
- **Proof the height-assisted run no longer aborts:** `tests/m9_p2b0/test_p2b0_f24_deductions.py::test_the_reference_plan_with_heights_no_longer_stops`, which runs when `URBAN_REAL_PLAN_DXF` is set. It passes.

### P0, F-26 (new, found while fixing F-24)

- **Defect:** no method deducts an opening that closes the face without a band gap: a door closed only by its leaf, glazing drawn on the room face, or an edge that is wall and something else.
- **Effect:** V1, V2 and V2.1 release the full face. On the curtain-glazing fixture, V2.1 releases 42.0 m² of plaster on a 14.0 m boundary of which 4.0 m is glazing.
- **V2.2:** such a face becomes a `BOUNDED_EXPOSURE` range of [gross − undeducted length × H, gross], with an RFI, never released. On the fixture this is [30.0, 42.0] m².
- **Reference plan, with test heights:** every one of the 24 ranged wall-finish lines is ranged for this reason; none is ranged for a missing height.

### P0, F-17: skirting boundary roles

- **Defect:** an edge that carries both `WINDOW` and `WINDOW_THRESHOLD` (a frame on the room face) is credited 50 / 50, and the midpoint is released.
- **Correction (V2.2):**
  - Release only what both readings agree on: the legacy figure minus the legacy credit of the mixed edges. When nothing is mixed, this is exactly the legacy figure.
  - Add one `FIN.SKIRTING BOUNDED_EXPOSURE` line, [0, unresolved length], with an RFI.
  - The midpoint is never released.
- **Synthetic:**
  - Frame on the face, 1.5 m window: 13.25 m before; now 12.50 m released + [0, 1.50] m.
  - A recessed frame (14.0 m) and curtain glazing (10.0 m) are unchanged.
- **Reference plan, Mode U (no heights):**
  - Released skirting goes from 210.191 m to 197.517 m, plus 9 range lines totalling [0, 25.348] m.
  - Every range line comes from `WINDOW+WINDOW_THRESHOLD`.
  - Check: 197.517 + 25.348 / 2 = 210.191, so the whole difference is the old midpoint credit.
  - The acceptance case BA-12 is now 1.90 m released + [0, 1.00] m, not 2.40 m.
- **Kept as a documented convention, not as evidence:** the V1 rule that a window threshold on a recessed frame's room face is a sill window, and is skirted. This needs the owner (OD-1).

### P1, door release guards (F-18, F-19, F-20, F-22)

V2.2 calls `door_model` with `guards=True`.

- **F-18:** a door whose frame and opening disagree by more than 2 mm is held.
- **F-19:**
  - Every withheld door has one element finding: `DOOR_HELD_WIDTH_REVIEW`, `DOOR_CLASS_REVIEW`, `DOOR_CLASS_UNRESOLVED`, `DOOR_PROVISIONAL` or `DOOR_UNRESOLVED`.
  - Main-entrance candidates stay under `MAIN_ENTRANCE_UNRESOLVED`.
  - The list `withheld_without_finding` must be empty.
- **F-20:** a door is `CLASS_REVIEW`, never internal PVC, if a side is either:
  - a shaft; or
  - an unlabelled space with a doorless facade opening (a passage listed by that space alone).
- **F-22:**
  - A non-door band opening into a SHAFT-coded space is a `LIFT_ENTRANCE_CANDIDATE` (REVIEW). The SHAFT code comes from a footprint stacked on every floor, or from a shaft word.
  - Its passage line becomes PROVISIONAL.
  - A candidate is never a confirmed lift door, never a released passage, and never measured.
- **Unchanged:**
  - The main entrance stays separate from ordinary aluminium doors.
  - No height is ever taken from a default: every released door's height is BLOCKED without a source.
- **Reference plan, Mode U:**

  | | V2.1 | V2.2 |
  |---|---|---|
  | Released internal PVC | 15 (13.2 m) | 14 (12.2 m) |
  | Released aluminium | 3 (2.8 m) | 2 (1.9 m) |
  | Doors held | — | 1 |
  | Class review | — | 1 |
  | Lift candidates | — | 3 |
  | Released ARCH.PASSAGE lines | 12 | 9 |
  | Withheld doors | 10 | 12 |
  | Withheld doors named by no finding | 7 | 0 |

- The V2.2 release set equals the "release-safe" set of the Phase 2A door readiness review (14 PVC, 12.2 m; 2 aluminium, 1.9 m).
- No door width changed.

### P1, F-21: ledger completeness

`surface_ledger.ledger(conserve=True)`:
- Places every emitted BOQ line in exactly one record, or in `OUT_OF_LEDGER_SCOPE` with a named reason.
- Adds the line families V2.1 left out: paint above wall tile, the waterproofing doorway strip, and the stair flight, step, ceiling and skirting rows.
- Separates `ENGINE_LIMIT` (the engine stops) from `NO_EMITTER` and `BLOCKED_MISSING_SOURCE`.
- Reports coverage by floor and trade.
- States `boq_completeness: NOT_ESTABLISHED`, with the reasons.

Reference plan, Mode U:
- 434 of 434 lines are in records; 0 are duplicated.
- 11 are out of scope:
  - 5 shaft / stair spaces;
  - 6 closure-strip thresholds.
- `ENGINE_LIMIT` 4; `NO_EMITTER` 0; `CONFIRMED_MISSING` 0. Zero confirmed-missing is reported, and is explicitly **not** a completeness claim.

### P1, blind-test readiness

- **Window position evidence:**
  - V2.2 opening records carry `position.centre_m` and the wall axis.
  - The scorer now matches V2.2 windows by position; it matched by width only before.
  - Dry run on V2.2: 6 / 6 injected faults are detected. Windows match by POSITION (GF 4 / 4, 1F 3 / 3), with 0 omissions and 0 false positives.
- **Heights facts template:** `FACTS_TEMPLATE_HEIGHTS.json`. Every value is null; `validate_facts` refuses it until it is filled.
- **Freeze:**
  - `BLIND_READINESS_RECORD.json` holds the sha256 of the scorer, the dry run, the protocol and the template.
  - It also holds the code-tree digest of engine + tools (636 files), the environment against the lock, and the test configuration.
  - `tests/m9_p2b0/test_p2b0_blind_freeze.py` fails if any frozen file changes. A change would then need a recorded amendment.
- **Protocol:** amendment A1 is recorded. V2.2 runs beside the V2.1 baseline; Mode A runs on V2.2 only. Metrics, tolerances, the claim rule, custody and error classes are unchanged.

## 4. Stop conditions (all checked; none triggered)

| Stop condition | Result |
|---|---|
| A fix changes frozen outputs | **No.** V1, V2 and V2.1 are byte-identical, 168 / 168 files, after every stage and at the end. Route G and the historical packages are untouched, and `opening_census.py` was not edited. |
| A geometry correction changes unrelated trade quantities unexpectedly | **No.** On the villa and its mirror, in both modes, 85 / 85 lines are identical (state, net, range). On the reference plan, Mode U, 413 lines are unchanged. The only changes are the predicted ones: ARCH.PASSAGE 3 (lift candidates), FIN.SKIRTING 9 (+9 range lines), and 2 doors out of the released totals. |
| A new measurement depends on an unapproved owner rule | **No.** No new measurement was introduced; every correction removes or ranges a release. The sill-window convention is the pre-existing V1 convention, kept and documented, and listed for the owner (OD-1). |
| The benchmark firewall is breached | **No.** The private benchmark was not opened. Every new and changed file passes the identity and forbidden-number scan. |
| A negative or physically impossible quantity remains in confirmed totals | **No.** Released negative lines: 0, on every fixture and on the reference plan in both modes. |

## 5. What worked, what did not, and what remains

**Worked:**
- Adding boundary evidence beside the frozen role lengths. Byte-identity held without any special-casing.
- Writing the failing test first, for every defect. Each "before" log is kept privately: F-24 5 / 10 failing, F-17 2 / 7, doors 8 / 9, F-21 5 / 7.
- Ranges instead of guesses. Every uncertain release (mixed skirting edges, undeducted face openings) became a [low, high] line with an RFI.
- Line-driven ledger rows. They removed five false `CONFIRMED_MISSING` that the first, record-driven attempt produced.

**Failed first, then fixed:**
- The first open-plan fixture used partition walls that met the band. The frozen gap detector then never formed the opening. A zone-line fixture reproduced the defect instead.
- A screen fixture was still read as a window. A curtain-glazing fixture replaced it.
- The shaft fixture joined the kitchen through a clear passage until head lines were drawn.
- The ledger first counted a strip shared by two doors twice. A taken-line rule fixed it.
- Two test expectations were mine, not the code's: a window deducts at its 1.5 m height, and the wet-room "paint above tile" line is a different element.

**Remains (limitations):**
- The recessed-frame sill convention.
- Closure strips are outside the surface ledger.
- Lift candidates are not confirmed lifts.
- Face openings are ranged, not deducted.
- V2.1 still stops when heights are supplied (frozen).
- Mode A figures above come from test heights.
- Column outlines are still axis-aligned rectangles only (F-9).
- The DWG adapter still reads DIMLFAC from the header only (F-13). Neither was in this phase's scope.
- V2.2 has been run on two synthetic villas, the new fixtures and one real plan only.

## 6. Reproduce

```
python3 -I tools/urban_boq_m9.py arch --drawings PLAN.dxf --out OUT --method ARCH_TAKEOFF_V2.2 [--facts FILLED_FACTS.json]
python3 -m pytest tests/m9_p2b0 tests/m9_p2a/test_p2a_blind_scoring.py
URBAN_REAL_PLAN_DXF=<private plan> python3 -m pytest tests/m9_p2b0     # the real-plan tests skip without it
python3 -I research/urban_m9_p2b0/make_readiness_record.py             # prints the record; --write rewrites it
```

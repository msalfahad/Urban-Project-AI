# T-458: legacy 0.15 m wet-room upturn and upturn door deduction: every path, reachability, NEW version

Owner directive 2026-11-02 C3; board row T-458 (P0 step 1 = reproduce + static AND run-time reachability, then the
superseded marking / policy-id split as a NEW version). Worker 1, run session_01E6cPnb8HKcHtG6h7XbZEpV, engine base
d4f11fe2 (origin/claude/access-permissions-setup-ii24ws).

## 1. Physical element and the governing rule

The wet-room membrane upturn is the strip of membrane folded up the wall from the wet floor. Owner rule: 0.20 m
(Q-03; rule store 1.5.0 UP-WP-002 2.0.0 = 0.20, OWNER_APPROVED), folded from the same strip (Q-30, Q-58); across a door
the membrane continues (UP-WP-003; Q-35 C): the upturn line is the one-sided boundary INCLUDING the door crossings and
each doorway is its own transition line (door width x wall thickness), reported wet area by wet area. Physical
quantity only; laps and rolls are procurement (UP-WP-MAT-001, Q-58), not this line.

## 2. Census of the legacy sites (code and data)

| Site | Legacy content | Static importers (outside tests) |
|---|---|---|
| engine/source/waterproofing_policy.py:16, wet() :28-37 | WET_UPTURN_M = 0.15; upturn length = perimeter - door widths; POLICY_ID WATERPROOFING_POLICY_V1 | none (tests/alsenan, tests/m9_foundation only) |
| engine/source/room_slice.py:22, :48, :140 | UPTURN_M = 0.15; wp_upturn_m2 = (perimeter - door widths) x 0.15 | none (tests/m2_generic_engine only) |
| engine/finishes_rules.py:44, upturn() :276 | UPTURN_M = 0.15; wall run - openings | none (tests, tests/m9_foundation only) |
| engine/source/arch_quantity_truth.py:200 | waterproofing(upturn_m=0.15) default (door crossings NOT deducted) | none (tests only) |
| data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json UP-WP-002 1.0.0 (byte copy of rules/owner_library 1.4.0) | 0.15 m, "less the openings that interrupt it"; no superseded flag | engine/rule_library.py load() (no 1.5.0 overlay), used by engine/elevator_marble.py, tools/run_round6e.py, tools/export_round6e.py; nothing resolves UP-WP-* through it (grep: no resolve call names a UP-WP id) |
| rules/methods/URBAN_METHOD_REGISTER_V1.json:113, engine/source/urban_methods.py:41-43 | "wet-room upturn stays 0.15 m" inside URBAN-ROOF-WATERPROOF-UPTURN-200@v1 (applies_to ROOF_REGION, never_applies_to WET_ROOM) | urban_methods is live (165 transitive importers) but no code reads parameters.wet_upturn_m (grep) |
| engine/source/rule_store.py rule("UP-WP-002", "1.4.0") | 0.15 (history version) | live callers ask LATEST_APPROVED 1.5.0 -> 0.20 (wet_room_evidence.py:389 and the run-time trace, section 4) |

POLICY-ID CLASH: `POLICY_ID = "WATERPROOFING_POLICY_V1"` in BOTH engine/source/waterproofing.py:23 (R8.18: gross
boundary, doorways NOT deducted) and engine/source/waterproofing_policy.py:14 (door widths deducted): one id, opposite
doorway rules. (The only other duplicated id in engine/ is BEAM_BINDING_V2, outside this task.)

## 3. Reproduction (synthetic, not the training villa)

3.00 x 2.00 m bathroom, one 0.80 m door, 0.20 m wall: boundary incl. the crossing = 10.000 m.

| Path | Upturn m2 | vs owner rule |
|---|---|---|
| owner rule (0.20, no deduction) = waterproofing_policy_v2.wet | 10.000 x 0.20 = **2.000** | - |
| waterproofing_policy.wet (V1) | (10.000 - 0.80) x 0.15 = 1.380 | -0.620 m2 (-31.0 %) |
| finishes_rules.upturn | (10.000 - 0.80) x 0.15 = 1.380 | -0.620 m2 (-31.0 %) |
| room_slice (formula :22 / :140) | (perimeter - doors) x 0.15 | same defect class |
| arch_quantity_truth.waterproofing default | 10.000 x 0.15 = 1.500 | -0.500 m2 (-25.0 %) |

The defect is real in code (reproduced on the legacy modules, own run).

## 4. Reachability: static and RUN-TIME

Static: AST import closure of engine.source.arch_v3040 (every import statement, also inside functions, relative
imports resolved): 123 engine modules; none of the four legacy modules (guard test
tests/t458_wet_upturn::test_candidate_closure_never_imports_a_legacy_upturn_module). The waterproofing modules in it are
waterproofing_system, wp_install, wp_geometry, rule_store (0.20 from the 1.5.0 store).

Run-time (research/agents_t458/t458_trace.py: an import hook wraps every function of each suspect module and the
rule-store / rule-library readers as they load; an audit hook records the rule JSON files opened; run in-process on the
Drive copies P7757.dxf + "ST7757 dxf.dxf" 9f9d1179 decoded into .work/private; trace JSON kept there):

RUNTIME_RESULTS_PLACEHOLDER

## 5. Verdict and correction

- Candidate quantities: NOT moved (no released or candidate path reaches a legacy site; section 4). Engine vs
  freelancer for the waterproofing upturn line is unchanged by this task.
- The defect is LATENT: any future caller of the legacy modules (or of rule_library for a UP-WP id) would book the
  upturn 31 % short for a room with one 0.80 m door in 10 m of boundary.
- NEW version `engine/source/waterproofing_policy_v2.py` (POLICY_ID WATERPROOFING_POLICY_V2_UPTURN_020_NO_DOOR_DEDUCTION):
  wet() = floor (UP-WP-001) + boundary incl. door crossings x UP-WP-002 from the rule store LATEST_APPROVED (0.20) +
  one doorway line per door (UP-WP-003); every missing input HELD (never 0). `SUPERSEDED` lists each legacy site above;
  the V1 modules stay unchanged as history (no edit in place; tests/m9_foundation/test_conflict_pins.py keeps pinning
  the documented conflict CF-09).
- Not done (needs its own row or owner scope): a new rule-library version marking UP-WP-002 1.0.0 superseded in
  data/trade_rules (repointing engine/rule_library.LIBRARY_PATH would change the library hash the lift-marble lines
  cite, so it is a candidate-output change for lane I, not a P0 bug fix); renaming the id inside the frozen-history V1
  modules (edit in place, refused by rule).

## 6. General rule (proposed lessons-register row)

| Date | What went wrong | Cause | Rule | Scope | Test | Task |
|---|---|---|---|---|---|---|
| 2026-11-02 | three engine modules and the base rule library still state a 0.15 m wet upturn with door deduction after the owner set 0.20 m / no deduction | superseded values left as module constants instead of reading the rule store; one policy id reused by two modules with opposite rules | a quantity parameter that an owner rule governs is read from rule_store LATEST_APPROVED at call time, never a module constant; a superseding module gets a NEW unique POLICY_ID and lists the sites it supersedes; reachability is shown at run time, not only by static imports | every villa, waterproofing (and any rule-governed parameter) | tests/t458_wet_upturn (normal 2.000 m2, adverse 1.380 m2 not reproduced, two doors same upturn, mm/mirror/rotation, HELD never 0, id uniqueness, candidate closure guard) | T-458 |

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

| Run (own, 2026-11-02) | Engine modules loaded | Suspect modules imported | Suspect calls | UP-WP reads (rule_store) |
|---|---|---|---|---|
| research/agents_t167/v304_run.py (chain incl. RELEASED V2.9, V2.10 - V2.12, V3.0.2 - V3.0.4) | 142 | none of the six (waterproofing_policy, room_slice, finishes_rules, arch_quantity_truth, waterproofing, rule_library) | 0 | UP-WP-002 @1.5.0 -> 0.2 (2,316 reads); UP-WP-001 / -003 / -005 @1.5.0 only; no read @1.4.0 |
| research/agents_t430/v3040_run.py (CANDIDATE OF RECORD ARCH_TAKEOFF_V3.0.40; V3_0_40_BOQ_LINES.json reproduced sha256 **aa6aa927**, 4,831 lines = board pin, so the probes changed nothing) | 179 | none of the six | 0 | UP-WP-002 @1.5.0 -> 0.2 (234 reads); no read @1.4.0 |
| tools/urban_structural_boq.py run (route G: A_FROZEN_STAGE_REPLAY on the structural DXF) | - | none of the six | 0 | none (structural only) |

Rule files: data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json, rules/owner_library 1.4.0 and URBAN_METHOD_REGISTER_V1
ARE opened at run time (rule store base load under the 1.5.0 overlay, manifest digests), but every UP-WP value served
came from rule_store LATEST_APPROVED 1.5.0 (0.20); engine/rule_library.py (the only reader without the overlay) is not
imported by any of the three runs. Released V2.9 output: all 297 `upturn_h_m` and 39 `upturn_m` values are 0.2; its 14
FIN.WP.WALL_UPTURN lines cite the KB rule UP-WP-003 (URBAN_KB_1.5.0, 0.20). The candidate carries 18 FIN.WP.WALL_UPTURN
(m2) and 4 FIN.WP.ROOF_UPTURN (lm) lines on the same 0.20 basis.

RESULT: the 0.15 m upturn and the upturn door deduction are reachable from NO released (V2.9 + route G) or candidate
(V3.0.40 aa6aa927) path, statically or at run time. The legacy code is live only in tests.

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
- Not done (needs its own row): a new rule-library version marking UP-WP-002 1.0.0 superseded in data/trade_rules and
  repointing engine/rule_library.LIBRARY_PATH. rule_library is imported by none of the three traced runs; its users are
  engine/elevator_marble.py (T-413 ledger route) and tools/run_round6e.py / export_round6e.py, whose cited library
  version / hash would change, so it is a rule-version task with its own regression check, not part of this P0 bug fix.
  Renaming the id inside the V1 modules would be an edit in place (refused by rule).

## 6. General rule (proposed lessons-register row)

| Date | What went wrong | Cause | Rule | Scope | Test | Task |
|---|---|---|---|---|---|---|
| 2026-11-02 | three engine modules and the base rule library still state a 0.15 m wet upturn with door deduction after the owner set 0.20 m / no deduction | superseded values left as module constants instead of reading the rule store; one policy id reused by two modules with opposite rules | a quantity parameter that an owner rule governs is read from rule_store LATEST_APPROVED at call time, never a module constant; a superseding module gets a NEW unique POLICY_ID and lists the sites it supersedes; reachability is shown at run time, not only by static imports | every villa, waterproofing (and any rule-governed parameter) | tests/t458_wet_upturn (normal 2.000 m2, adverse 1.380 m2 not reproduced, two doors same upturn, mm/mirror/rotation, HELD never 0, id uniqueness, candidate closure guard) | T-458 |

## 7. r2 (worker 1, 2026-11-02, after the Verifier's r1 REJECT 04:57Z, gates d / f / h)

Cause of the reject: r1 implemented UP-WP-002 2.0.0 but not the LATEST record of UP-WP-003 (1.1.0, rule store 1.5.0,
MANDATORY): "doorway floor piece = door width x wall depth, part of the floor waterproofing area; the doorway segment of
the upturn (UP-WP-002 v2.0.0) is its own row; where the project detail puts the 0.20 m coverage inside the doorway
piece, only one is billed"; unknown -> DOORWAY_CONTINUATION_NOT_ESTABLISHED. r1 folded the segment into the upturn and
always billed a separate FIN.WP.DOORWAY piece beside it (+0.160 m2, +8.0 % on the fixture), and a test pinned it.

Physical element: at a wet-room door the membrane leaves the floor face, crosses the wall depth (the doorway floor
piece, w x t) and, along the door line, the 0.20 m upturn coverage (the doorway segment, w x 0.20) is built either inside
that piece (the same membrane: one quantity) or as a separate return (two pieces). Which one is a project detail, not a
default.

r2 wet() rows (engine/source/waterproofing_policy_v2.py): FIN.WP.FLOOR = ROOM_FACE + one DOORWAY_PIECE row per door
(part_of_floor_area True); FIN.WP.UPTURN = BOUNDARY_RUN_EXCL_DOORWAYS ((boundary incl. crossings - door widths) x 0.20)
+ one DOORWAY_SEGMENT row per door (w x 0.20); doorway_detail per door: COVERAGE_INSIDE_PIECE -> the piece is billed (it
contains the segment; the larger of the two when the wall is deeper than 0.20 m) and the segment row is NOT_BILLED with
covered_by; SEPARATE_RETURN -> both billed; None or an unrecognised value -> the segment row HELD
DOORWAY_CONTINUATION_NOT_ESTABLISHED (if_billed_m2 shown; never 0, never both by default). The run + all segments always
equal the whole boundary x 0.20 (no door deduction, UP-WP-002 never-list); splitting needs every door width, so an
unknown width HELDs the run (whole_boundary_m2 kept for the record) and that door's rows.

Fixture 3.00 x 2.00 m, one 0.80 m door, 0.20 m wall (hand): face 6.000; piece 0.160; run 9.200 x 0.20 = 1.840;
segment 0.160. SEPARATE_RETURN 6.160 + 2.000 = 8.160 m2; COVERAGE_INSIDE_PIECE 6.160 + 1.840 = 8.000 m2 (r1 8.160:
-0.160 m2 = the double-billed doorway); not established 6.160 + 1.840 MEASURED + 0.160 HELD. Wall 0.25 m, coverage
inside: piece 0.200 billed once, total 6.000 + 0.200 + 1.840 = 8.040 m2.

F-C-T458-1 (urban_methods reached but unread): SUPERSEDED now records reached_by_candidate True / read False for the
urban_methods site; tests assert (i) urban_methods is in the AST closure of arch_v3040 and arch_v3041, (ii) the only
"wet_upturn_m" in engine / tools is its definition at urban_methods.py:43, nothing resolves the roof method, and the
only UM*.resolve() caller is footing_rebar_population_v1 (its own stock-length rule).

Not covered (stated, not assumed): a door between TWO wet rooms (Q-35 addendum; Lead reading "one doorway line per door,
not per room side", not owner-confirmed) - wet() is per wet area, so a caller passing the same door to both rooms would
bill its piece / segment twice; the integration that wires this producer must pass a shared door to ONE room only, or
the Lead raises it under ERS s.2.7. Candidate quantities unchanged (the module is still an UNWIRED_PRODUCER).

Proposed lessons-register row (ERS s.7, from the Verifier): "a NEW version of a rule-implementing module implements the
LATEST rule-store record of EVERY rule it cites (here UP-WP-003 1.1.0), not only the one the task names; a test pinning
a double count as expected is a gate failure" - scope every villa / every rule-implementing module; test
tests/t458_wet_upturn::test_adverse_coverage_inside_the_piece_is_billed_once.

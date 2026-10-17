# ARCH_TAKEOFF_V2.6 - waterproofing constructability layer: implementation report

Phase 2B-5, Stage B of the overnight program. Base commit 64827c6 (the Phase 2B-4 audit).

## 1. Authorisation boundaries

| boundary | how it is kept |
|---|---|
| V1, V2, V2.1, V2.2, V2.3, V2.4, V2.5 frozen | every new behaviour sits behind keys only V2.6 sets (`trace`, `junction_flange_m`, `v26=True`, `keep_segments=True`, `cut_ids=True`); byte comparison of every output file of every earlier method on three drawings, Mode U and Mode A (section 7) |
| no quantity change | the installation layer reads the cut plan; it returns flags, records and alternatives. V2.6 keeps every BOQ line of V2.5 byte for byte (`test_p2b5_cli.py`, on the PD-1 drawing and the synthetic villa; section 7 on the reference plan) |
| no detail selected | the floor-to-wall junction stays UNRESOLVED (N-11 / P-1); corner, jamb, penetration and termination details are counted and withheld (UP-WP-004); product values are never assumed |
| rules | `rules/` unchanged; registry 1.1.0 as for V2.4 / V2.5 |
| private data | the reference plan was run only in the private scratch area; this report gives aggregates only (section 6) |
| expected values | from hand derivations (typed literals, `install_cases.py`) and an independent calculator (`install_reference.py`, standard library + the Phase 2B-4 calculator); neither imports the engine (`test_p2b5_independence.py`) |

## 2. What changed

| file | change | reached by |
|---|---|---|
| `engine/source/membrane_layout.py` | the cut plan as a trace: value-identical subclasses `_Seg(tuple)`, `_Lane(float)`, `_Piece(float)` carry segment ids, lane positions and piece offsets through the V2.5 planner without changing a comparison or a sum; `_trace_record` writes `URBAN_MEMBRANE_TRACE_V1`; `junction_flange_m` sets the band's flange apart from the side lap | `trace` / `junction_flange_m` keys (V2.6 only) |
| `engine/source/wp_geometry.py` | `ring_segments`: the typed boundary per ring, in ring order | V2.6 only (`keep_segments`) |
| `engine/source/wp_install.py` (new) | the installation layer: piece plan, band runs, joints, best arrangement, floor seams, multi-layer points, stagger, penetrations, drains, lay order, junction alternatives, flags | `build_area(v26=True)` |
| `engine/source/waterproofing_system.py` | `METHOD_V26`; `room_layout` passes the keys; `make_area(keep_segments)`; `build_area(v26)` calls `wp_install.install`; V2.6 row fields; `cutting_plan(cut_ids)`; `installation_outputs` | V2.6 only |
| `tools/urban_boq_m9.py` | method `ARCH_TAKEOFF_V2.6`, policy `URBAN_BOQ_M9_P2B5_ARCH_V2_6`, corrections D-V26-01..05, manifest `URBAN_OUTPUT_MANIFEST_V2_6`, files `MEMBRANE_PIECE_PLAN.json/.csv`, `WP_INSTALLATION.json/.csv` | `--method ARCH_TAKEOFF_V2.6` |
| `engine/boq_room_workbook.py` | two sheets, "WP PIECE PLAN" and "WP INSTALLATION", written only when the run carries them | V2.6 runs only |
| `tests/m9_p2b5/` (new) | 10 worked examples, independent reference, engine adapter, 90 tests | - |
| `research/urban_m9_p2b5/` (new) | generator, worked examples, verification chain, junction alternatives, 16 diagrams, this report | - |

## 3. The corrections and the Phase 2B-4 findings

| V2.6 correction | Phase 2B-4 findings | what V2.6 does |
|---|---|---|
| D-V26-01 junction open | F-01 (junction assumed), F-09 (17.80 m2 / 2 rolls valid only under the assumption) | state UNRESOLVED; alternatives: separate upstand (owner's B) at the plan's flange, at the widest flange with the same rolls and at the first flange that adds a roll; continuous fold (owner's A) for rectangles; `JUNCTION_CHANGES_ROLL_COUNT`; material state `PROVISIONAL_DETAILS_OPEN` |
| D-V26-02 piece-level cutting plan | F-02 (record is not a plan), F-07 (offcuts) | every cut, rip, cross-cut; each piece with id, size, source roll, destination; offcuts as rectangles (floor beyond a stepped wall included), classed TRUE_WASTE / REUSABLE_SUBJECT_TO_N7; roll stock apart; shared cuts keep their area's id |
| D-V26-03 joints placed | F-03 (joint placement unchecked) | each joint's distance to corners and seam ends; JOINT_AT_CORNER / JOINT_ON_SEAM_END / JOINT_TOUCHES_SEAM_END; the best order of the same pieces; JOINT_OFFSET_UNVERIFIED |
| D-V26-04 jambs and terminations | F-04 (doorway butt joints not named) | two BUTT_JOINT_OPEN per door not crossed; TERMINATION_OPEN at open edges |
| D-V26-05 layers, penetrations, drains | F-05 (corners), F-06 (pipe sleeve), F-08 (multi-layer points) | multi-layer points, end-lap stagger, penetration clearances and collar size, drains NOT_SHOWN when not drawn, lay order from a single drain |
| - | F-10 (selection-order scope), F-11 (unselected 18.20 m2 plan) | not changed (owner decision N-9; no quantity is affected) |
| - | F-12 (every V2.5 quantity reproduced) | still true: the trace test shows the V2.5 layout unchanged with the trace on, for the twelve Phase 2B-3 proof cases |

**Not implemented, by design:** C-5 offcut reuse across areas (reusable offcuts are classed, never re-used), C-6
selection-order scope (owner decision), decomposition of shaped trims at splayed walls (area and flag only).

## 4. The ten worked examples

Each example runs the full chain `OWNER/PROJECT RULE -> SOURCE DRAWING -> GEOMETRIC INTERPRETATION -> MEASUREMENT
FORMULA -> INDEPENDENT EXPECTED RESULT -> ENGINE RESULT -> DIFFERENCE -> PASS/FAIL -> BOQ IMPACT`
(`WORKED_EXAMPLES.md`, `VERIFICATION_CHAIN.csv`). **297 of 297 checks pass.** The reference calculator rebuilds the
engine's own cutting plan piece by piece and checks it covers every surface on a 10 mm grid.

| example | room | consumed / installed m2 | rolls | true waste / reusable / stock m2 | what the layer shows |
|---|---|---|---|---|---|
| IX-01 | 2.00 x 2.00 closed | 7.50 / 6.95 | 1 | 0.55 / 0 / 2.50 | the closing joint ends on the corner at the ring start; a joint touches a seam end |
| IX-02 | 3.00 x 4.00, one door (WP-B) | 17.80 / 17.52 | 2 | 0.28 / 0 / 2.20 | 2 joints stacked on seam ends (best order 0.30 / 0.20 m); junction 2 - 3 rolls |
| IX-03 | 3.60 x 3.00, two doors, sleeve (WP-E) | 16.54 / 15.75 | 2 | 0.79 / 0 / 3.46 | joint 0.02 m from a corner (best 0.14 m); sleeve clear 0.30 m, collar up to 0.60 m |
| IX-04 | L 3 x 3 less 1 x 1 (WP-D) | 13.80 / 12.52 | 2 | 0.48 / 0.80 / 6.20 | the 0.80 x 1.00 offcut beyond the step as a rectangle; a piece starts on a corner (best 0.10 m); fold not computed (not a rectangle) |
| IX-05 | 3.00 x 2.50 with a column | 12.34 / 11.84 | 2 | 0.34 / 0.16 / 7.66 | the column's own closed loop, 4 external corners; a floor seam along the column face |
| IX-06 | kitchen 4 x 3, two doorways, drain | 17.80 / 17.52 | 2 | 0.28 / 0 / 2.20 | the band crosses the service doorway to the waterproofed laundry; lay order from the drain; junction 2 - 3 rolls |
| IX-07 | balcony 4.00 x 1.50, open front | 9.10 / 8.59 | 1 | 0.51 / 0 / 0.90 | TERMINATION_OPEN at both ends of the open edge; fold not computed |
| IX-08 | roof 12 x 6, parapets, two drains | 92.14 / 90.18 | 10 | 1.96 / 0 / 7.86 | a drain on a floor lap; splices not staggered; lay order not validated (two drains) |
| IX-09 | three rooms, one system | 29.20 m cut | 4 alone, 3 shared | untouched 0.80 | one roll saved by sharing full-width cuts |
| IX-10 | two systems | - | 2 + 2 | - | never mixed: 3 rolls if mixed, kept at 4 |

## 5. Acceptance gate

| criterion | evidence |
|---|---|
| areas, pieces and balances reconcile | for every area: consumed = installed + offcuts (1e-6); installed = the V2.5 row's B; consumed = the V2.5 row's consumed (`test_acceptance_gate`) |
| no double counting | every piece and offcut id once; a doorway listed twice is flagged, both pieces kept (`test_a_doorway_listed_twice_is_flagged`) |
| packing physically possible | no roll cut beyond its length; the reference rebuilds each plan from the rolls and covers the surface on a 10 mm grid; the shared packing is re-solved independently (`pack_shared`) |
| unresolved details visible | `PROVISIONAL_DETAILS_OPEN` with its reason on every area; flags per area; jamb, corner, termination and penetration records |
| no arbitrary waste percentage | no `waste_pct` anywhere in the V2.6 records; waste is the sum of classed offcuts |
| old methods frozen | section 7 |

## 6. The reference plan (private; aggregates only)

All 17 waterproofed areas computed (state COMPUTED), every piece plan balanced.

| flag | areas |
|---|---|
| FLOOR_WALL_JUNCTION_UNRESOLVED, JOINT_OFFSET_UNVERIFIED | 17 |
| DRAIN_NOT_SHOWN, LAY_ORDER_NOT_VALIDATED | 17 (no drain is drawn on the plan) |
| JUNCTION_CHANGES_ROLL_COUNT | 5 |
| SHAPED_TRIM_NOT_DECOMPOSED | 4 (genuine trims at 45-degree walls, 10 trims) |
| JOINT_AT_CORNER, JOINT_ON_SEAM_END | 2 each |
| FLOOR_SEAM_ALONG_A_WALL | 1 |

Junction roll ranges over the alternatives: 1 - 1 (11 areas), 1 - 2 (4), 2 - 2 (1), 2 - 3 (1).

The first private run reported 11 shaped-trim areas. Seven of them were wall lines drawn a hair off square (slivers of
1 - 2 x 10^-6 m2, 1.1 x 10^-5 m2 in all). These are now recorded as "drawing tolerance at the wall line" (true
waste, kept in the balance, never a cut, never flagged) below 1 cm2. Tests: `test_a_wall_drawn_a_hair_off_square_
is_not_a_shaped_trim`, and `test_a_splayed_corner_is_a_shaped_trim` (hand values 0.02 + 0.08 m2).

## 7. Byte identity and determinism

Three drawings: the synthetic villa, its mirror image, and the reference plan (private). Mode U (no heights), plus
Mode A (synthetic S2 heights) for V2.2 and later. 39 CLI runs at the V2.6 working tree, all exit 0. Each run was
compared byte for byte with the baseline snapshot taken at 64827c6 before any change (`diff -rq`, run logs
included).

| method | files compared | files that differ |
|---|---|---|
| ARCH_TAKEOFF_V1 | 46 | 0 |
| ARCH_TAKEOFF_V2 | 52 | 0 |
| ARCH_TAKEOFF_V2.1 | 70 | 0 |
| ARCH_TAKEOFF_V2.2 | 140 | 0 |
| ARCH_TAKEOFF_V2.3 | 176 | 0 |
| ARCH_TAKEOFF_V2.4 | 236 | 0 |
| ARCH_TAKEOFF_V2.5 | 248 | 0 |
| **all earlier methods** | **968** | **0** |

**V2.6 against V2.5, the same drawing and mode (all six runs):**

- Byte-identical: `BOQ_LINES.json`, `BOQ_LINES.csv`, `BOQ_TRACEABILITY.csv`, `COVERAGE.json`, `COVERAGE.csv`,
  `WATERPROOFING_SCHEDULE.csv`, `SURFACE_LEDGER.csv`, `DOOR_FEASIBILITY.csv`, `DOOR_SCENARIOS.csv`,
  `DOOR_SCHEDULE.csv`, `PROJECT_RULES_SHEET.csv`, and the overlays.
- With the run record masked, the JSON files differ only in:
  - the method and policy names;
  - `layout.trace` (one per waterproofed area) and the layout method name `MEMBRANE_POLYGON_STRIPS_V2_6`;
  - `cut_id` on each shared cutting-plan piece;
  - the V2.6 row fields of the waterproofing schedule (13 fields, all added; no V2.5 field changed);
  - `policies.wp_install` and `v2_6` in `RUN_RULES.json`;
  - the manifest.
- Added files: `MEMBRANE_PIECE_PLAN.json/.csv` and `WP_INSTALLATION.json/.csv`.
- The workbook gains two sheets.

**Determinism:** a second V2.6 pass over the three drawings and both modes gives the same 272 files byte for byte.
The generator in this folder reproduces its outputs byte for byte under a different hash seed.

**Test suites:** `tests/m9_p2b5` (90 tests) with `m9_p2b4`, `m9_p2b3` and `m9_p2b2`: 243 pass; `m9_foundation`: 159
pass; none skipped, none failed. The full repository suite is re-run in Stage I.

## 8. New findings

| id | finding | impact |
|---|---|---|
| F-13 | **The V2.5 band planner is not least-membrane at wider flanges.** In the 3 x 4 bathroom it gives 19.25 m2 at flanges 0.14 - 0.15 m and 21.10 m2 at 0.16 m. The Phase 2B-4 audit planner found 18.75 and 20.60 m2 with the same rolls. Roll counts agree (2, 2, 3) | the alternative plans are the engine's own, rebuilt and verified as complete; they are not proven optimal. The roll count, which decides procurement, is unaffected |
| F-14 | The 12 x 6 m roof: a roof drain lies inside a floor lap, and the end splices of neighbouring strips are aligned (not staggered), so the splices make four-layer crossings | flagged (DRAIN_ON_A_FLOOR_SEAM, END_LAPS_NOT_STAGGERED); the layout is unchanged (layout changes belong to a future opt-in method) |
| F-15 | Around a column the floor seam can run along the column face, under the band flange (IX-05) | flagged FLOOR_SEAM_ALONG_A_WALL |
| F-16 | In the kitchen with a crossed service doorway, the band plan ends with a 0.20 m piece (P-9: short band pieces) | shown in the piece plan; no minimum piece length is given, so it is not judged |
| F-17 | A closed loop's closing joint can fall on the corner at the ring start (IX-01) | flagged JOINT_AT_CORNER; the best arrangement of the same five pieces keeps every joint 0.51 m from a corner and 0.29 m from a seam end |
| F-18 | On the reference plan, 4 areas have genuinely splayed (45-degree) walls whose floor trims are not decomposed | flagged; a decomposition would change no quantity |

## 9. Defects found and fixed during this phase

| id | defect | fix | test |
|---|---|---|---|
| H-B1 | shared cutting plan cut ids were taken before the pieces were sorted (wrong labels) | ids from the sorted piece | `test_the_shared_cutting_plan_names_each_areas_cuts` |
| H-B2 | side laps of spliced strips counted as four zones per strip pair (48 crossings on the roof) | merged per strip pair; END_LAPS_NOT_STAGGERED added | IX-08 |
| H-B3 | the reference counted a vertex at a run end as a corner (open edge) | `0 < r < R` | IX-07 |
| H-B4 | a duplicate doorway crashed the plan (duplicate piece id) | `#k` suffix, DUPLICATE_DOORWAY_PIECE, INCONSISTENT state on any plan error | `test_a_doorway_listed_twice_is_flagged` |
| H-B5 | closed-run start offsets searched in 50 mm steps above 4 m | 10 mm, with a cap and ARRANGEMENT_SEARCH_LIMITED | IX-08 |
| H-B6 | continuous-fold corner squares swapped for strips along x | frame fixed | fold vs the Phase 2B-4 method-B planner |
| H-B7 | a zero-area ring reached the frozen V2.5 result check | V2.6 blocks DEGENERATE_AREA first | `test_a_degenerate_ring_is_blocked` |
| H-B8 | float slivers reported as shaped trims (section 6) | 1 cm2 drawing tolerance | two tests |
| H-B9 | diagrams: offcut only labelled; narrow strip label over the band | offcut drawn in place; id-only label | `SCREENSHOT_REVIEW.md` |

**Correction to Phase 2B-4 (H-A3).** The "V25 selects" column of the Phase 2B-4 junction sweep for flanges 0.14 m
and above is the audit planner's least-membrane plan, not what the V2.5 planner produces at that flange (F-13). The
roll counts and F-09's conclusion (a flange of 0.16 m or more adds a roll) stand. The membrane figures should read
19.25 m2 (0.14 - 0.15 m) and 21.10 m2 (0.16 m) for the engine's own plans.

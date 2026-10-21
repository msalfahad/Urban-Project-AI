# Pre-implementation engineering audit (Phase 2B-2, deliverable 1)

Owner program "Master engineering rules, waterproofing optimization and door feasibility" (2026-10-16), Part 1.
Written before any engine file was edited. Reference-plan figures are aggregates only.

## 1. Repository state

| Check | Result |
|---|---|
| Branch | `claude/access-permissions-setup-ii24ws` |
| HEAD | `7b83c20` (Phase 2B-1 reports: final full-suite run), working tree clean |
| Latest phase tests | `tests/m9_kb` (78 tests) pass; `tools/kb_build.py --check` and `tools/kb_index.py --check` report up to date |
| Latest full suite (Phase 2B-1, `d604b55`) | 8,043 passed / 345 failed / 32 errors / 160 skipped / 102 xfailed; the 377 failures and errors are the baseline set (missing git-ignored datasets), 0 new |
| Frozen-output baseline taken for this phase | V1, V2, V2.1, V2.2 and V2.3 CLI runs on the synthetic villa, its mirror and the reference plan (V2.2 / V2.3 also with the synthetic heights facts) from a clean worktree of `7b83c20`: **484 files**, every run exit 0 |
| Method registry | `ARCH_METHODS` = V1, V2, V2.1, V2.2, V2.3 (`tools/urban_boq_m9.py`); each later method is an explicit opt-in that implies the earlier flags. `ARCH_TAKEOFF_V2.4` fits the pattern (no name clash, the CLI validates `--method` against the tuple) |

## 2. What exists today (V2.3) for the areas of this program

### 2.1 Knowledge registry 1.0.0 (25 rules)

Door rules UP-DOOR-CLS-001..006, UP-DOOR-OPEN-002 (owner correction: wall opening = nominal + 0.10 m; 1.10 / 1.00 / 1.10 m),
UP-DOOR-HGT-001 (2.20 / 2.20 / 2.20 / 2.50 m reference heights, ASSUMED), UP-DOOR-AREA-001 (AS_DRAWN / OWNER_REQUIRED
never mixed), UP-DOOR-DEP-001 (enlargement dependency map), UP-ELEV-SCHED-001; wet-area scope UP-WET-001,
UP-FIN-WALL-001, UP-FIN-PAINT-001, UP-FIN-PLASTER-001, UP-SKIRT-001, UP-THR-001; exterior waterproofing
UP-WP-ROOF-001; space and question rules UP-SPACE-001/002, UP-KB-PREC-001, UP-KB-QUES-001; UP-CEIL-001; one project
rule PS-REF-001; one deprecated rule UP-DOOR-MIN-001. **No waterproofing material rule is in the registry**: the
waterproofing values come from the frozen rule store `rules/` 1.5.0.

### 2.2 Waterproofing (rule store 1.5.0 + `engine/source/membrane_layout.py`)

| Rule-store record | Content |
|---|---|
| UP-WP-001 1.0.0 | wet-room floor waterproofing measured in m2 |
| UP-WP-002 2.0.0 (supersedes 1.0.0 = 0.15 m) | upturn 0.20 m around the **full boundary including every doorway segment** (no door deduction); DOORWAY_UPTURN_DETAIL_REQUIRED as a construction check |
| UP-WP-003 1.1.0 | the floor membrane continues through the doorway (door width x wall depth); doorway piece and doorway upturn never counted twice |
| UP-WP-004 1.1.0 | shower: PROPOSED (not approved) |
| UP-WP-005 1.0.0 | membrane from the roll layout, minimum 0.10 m lap, never a flat waste rate |
| MEM-URBAN-DEFAULT-1x10 | roll 1.00 x 10.00 m, side / end lap 0.10 m; corner and penetration treatment null (by system) |
| URBAN-ROOF-WATERPROOF-UPTURN-200@v1 (method register) | roof: area + region perimeter x 0.20 m |

The membrane engine already lays rectangles and polygons (two orientations, side and end laps, upturn bands cut into
lanes, doorway pieces, rolls first-fit, a balance check, a minimum-rolls selection). In the architectural route
(`arch_measure.materials`) it runs per wet room.

### 2.3 Doors

`door_standards.py` (V2.3): category, owner-required wall opening, enlargement, the CAD value kept apart, owner
reference heights, AS_DRAWN / OWNER_REQUIRED / UNRESOLVED / EXCLUDED views, a dependency map whose structural note
reads only the jamb types (one column jamb: review; two: blocks). **No clearance geometry beside an opening is read.**

### 2.4 Evidence classes in the engine

| Class | How the engine records it today |
|---|---|
| Drawing dimension | `CAD_VECTOR` geometry; `evidence_state` MEASURED / SOURCE_DERIVED; door width `BAND_OPENING (jamb to jamb)` |
| Project specification | facts file (`URBAN_ARCH_FACTS_V1`) values with an `authority` (SOURCE ...); project decisions (`URBAN_PROJECT_DECISIONS_V1`, space status only) |
| Owner standard | rule-store / registry rule ids on each line (`rule_id`, `rule_set`, digest); owner reference heights flagged HEIGHT_ASSUMED |
| Assumption | PROVISIONAL lines, `ASSUMED` height state, flags; never in a confirmed total |

There is **no general mechanism for a project rule that overrides an Urban standard within a scope** (a floor, a room,
a wall, an opening, an assembly); only the space decisions are scoped.

## 3. Existing rules and behaviour that conflict with the newly approved standards

| # | Where | Today | New owner standard | Effect on V2.4 |
|---|---|---|---|---|
| A-01 | rule store UP-WP-002 2.0.0, `arch_measure.measure` | wet-room `FIN.WP.UPTURN` = full boundary **incl. doorway segments** x 0.20, released (SOURCE_DERIVED) | Part 3.4: doorway transitions modelled independently; never blindly door width x 0.20; no detail -> unresolved with alternatives | the wall upturn excludes doorway segments; each doorway gets its own transition item (alternatives, withheld until a detail) |
| A-02 | `arch_measure.measure` | the doorway piece (FIN.WP.DOORWAY) **and** the doorway segment of the upturn are both released, flagged DOORWAY_DOUBLE_COVERAGE_REVIEW | Part 8: doorway waterproofing neither omitted nor duplicated | continuation piece kept (approved owner method, rule store UP-WP-003 1.1.0); vertical transition separate and unresolved |
| A-03 | identifier namespace | rule store UP-WP-001 floor / 002 upturn / 003 doorway / 004 shower / 005 lap | owner registers UP-WP-001 roll / 002 overlap / 003 upturn / 004 penetrations | same ids, different meanings: registry ids are always cited with their rule set (URBAN_KB_1.1.0); crosswalk and conflict record CF-13 |
| A-04 | registry UP-WP-ROOF-001 1.0.0, `owner_finish_scope.exterior_wp_lines` | balcony upturn "by specification" (RFI); roof upturn = whole roof perimeter x 0.20 (doors and open edges included) | UP-WP-003: 0.20 m along eligible wall boundaries, project detail overrides | balcony and roof: 0.20 m on wall / parapet boundaries (owner standard), doorways as transitions, open edges as terminations (detail) |
| A-05 | `arch_measure.materials` | membrane material only for rooms whose floor line is FIN.FLOOR.WET_TILE: owner-scope wet rooms (kitchen, pantry, ironing) have waterproofing lines but **no membrane material** (villa: 1 of 3 wet rooms, reference plan: 1 of 17) | Part 3.2: installed and procurement quantities for every waterproofed area | every waterproofed space gets its layout |
| A-06 | `arch_measure.materials` | roll counts per room, summed (villa: 2 + 2 rolls, each room leaving an untouched 6.8 - 8.8 m roll tail) | Part 3.2 C: complete rolls for a feasible installation layout | per-room layouts kept; procurement from one project cutting plan per membrane system |
| A-07 | `membrane_layout._one` | penetrations taken from a constraint the architectural route never sets: always reported as **0** | UP-WP-004: read the drawings; missing information -> name the missing detail, withhold the extra quantity | penetration evidence (drain symbols, sanitary fixtures) counted from the plan; "not shown" is never zero |
| A-08 | `membrane_layout._one` | corners = 4 + 2 x doorways for every room, also polygons (an L-shaped room has 5 internal + 1 external corners) | UP-WP-004 corners and junctions | corners from the polygon (internal / external, obstruction corners) |
| A-09 | `arch_measure.materials` | wet and exterior membranes from one default spec, never separated | Part 3.5: separate systems never combined | procurement groups per system (wet area / exterior by default; project systems by scope) |
| A-10 | `owner_finish_scope.jamb_plaster_lines` | every door's jamb plaster at the internal 2.20 m height (main entrance included) | Part 4.2: the applicable height for jamb plaster | per-category height (main entrance 2.50 m), OWNER_STANDARD_ASSUMED |
| A-11 | `door_standards.required_opening` | "nominal door for the opening" only when the CAD opening is wider than the standard | Part 4.3 (2), (4): available nominal under the allowance for every door (bathroom 0.80 -> 0.70) | computed for every door |
| A-12 | `door_standards.dependency_impacts` | structural note from jamb types only | Part 4.4: adjacent walls, columns, junctions, corners, swing, nearby openings, stairs, shafts, fixtures | door feasibility engine |
| A-13 | V2.3 | no project rule overrides an Urban standard | Part 2: Level B overrides Level A within scope; Project Engineering Rules Sheet before the BOQ, hash in every output | rules sheet generator + scoped resolver |
| A-14 | registry UP-WET-001 1.0.0 | "waterproofing: floor + upturn + doorway continuation (UP-WP-001..003)" (rule-store numbering) | new numbering | logic text updated in 1.1.0 with qualified ids |
| A-15 | registry UP-DOOR-HGT-001 1.0.0 | fallback state ASSUMED / HEIGHT_ASSUMED | Part 4.2: OWNER_STANDARD_ASSUMED, never DRAWING_MEASURED | state label added (V2.4); V2.3 untouched |

No conflict was found with the door widths themselves (UP-DOOR-OPEN-002 already carries the approved table), the door
heights (2.20 / 2.50 m already registered) or the elevator exclusion.

## 4. Smallest safe extension points

| Need | Extension point | Why it is safe |
|---|---|---|
| New rules, supersession history | `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.1.0.json`, built from 1.0.0 + a delta (`tools/kb_build_1_1.py`) | 1.0.0 stays byte-identical (V2.3 reads it); `rules/` gains no file |
| V2.4 reads 1.1.0 | `knowledge.using("1.1.0")` context around the V2.4 run | V2.3 never enters the context; default stays 1.0.0 |
| Project rules | new module `project_rules.py`, new CLI option `--project-rules` (V2.4 only) | no earlier method reads it |
| Waterproofing | new module `waterproofing_system.py`; it reuses `membrane_layout` internals without editing them; the V2.4 stage replaces the waterproofing lines after measurement | `arch_measure.measure` / `materials` unchanged |
| Doors | new module `door_feasibility.py` over the door model and the floor geometry | `door_model` / `door_standards` unchanged |
| Jamb plaster heights | the V2.4 stage rebuilds the jamb plaster lines with the door categories | `owner_finish_scope` unchanged |
| Ledger | a V2.4 eligibility table variant behind a flag | the V2.3 table (dumped in its outputs) unchanged |
| Item master | new item codes FIN.WP.WALL_UPTURN, FIN.WP.DOORWAY_TRANSITION, FIN.WP.PENETRATION in `boq_line.ITEMS` | no earlier method emits them (proved by the byte-identical snapshot) |

`engine/source/opening_census.py` is read, never edited.

## 5. Anticipated BOQ changes (V2.3 -> V2.4), recorded before implementation

| Item | Expected change | Expected direction |
|---|---|---|
| FIN.WP.UPTURN (wet rooms) | replaced by FIN.WP.WALL_UPTURN on eligible wall boundaries only | down by sum(door widths) x 0.20 per wet room (villa: 2.50 m x 0.20 = 0.50 m2, 7.84 -> 7.34 m2) |
| FIN.WP.DOORWAY_TRANSITION | new, one per wet / exterior doorway, BLOCKED_RFI with a bounded range of the alternatives until a detail is given | new withheld item (not in any confirmed total) |
| FIN.WP.DOORWAY | the continuation piece stays (owner method) | unchanged |
| FIN.WP.FLOOR | unchanged geometry | unchanged |
| Balcony upturn | RFI -> 0.20 m on wall boundaries (owner standard), open edges as termination items | new quantity where walls bound the balcony |
| Roof upturn | perimeter x 0.20 -> wall / parapet boundaries x 0.20 | down where the roof edge has doors or open edges |
| Penetrations | counted where drawn; treatment withheld without a detail | new count items, no invented quantity |
| Membrane material | owner-scope wet rooms added; project cutting plan | villa: 3 rooms laid instead of 2; procurement rolls expected below the per-room sum (4) |
| FIN.PLASTER (door jambs) | per-category height; main entrance 2.50 m | up for main entrances only; candidates stay unresolved between 2.20 and 2.50 |
| Doors | new feasibility schedule and views; door BOQ lines unchanged (as drawn) | no as-drawn change |

What must not change: every V1 .. V2.3 output (484 snapshot files), `rules/`, `opening_census.py`, any drawn dimension.

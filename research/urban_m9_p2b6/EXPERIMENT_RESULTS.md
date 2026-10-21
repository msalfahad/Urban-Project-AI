# Experiment results (Phase 2B-6, Part 10)

Every experiment ran in an isolated clone of `5dc2753`, behind an environment flag (`URBAN_EXP=...`). The clone's
engine changes are in `experiments/ENGINE_EXPERIMENTS_NOT_APPLIED.patch`. **None of them is in the repository's
engine.** With no flag set, the clone reproduces V2.6 exactly on the reference plan (every output identical, the run
record aside).

The truth sources were:

- hand-derived values for every synthetic fixture (`tests/m9_p2b6/p2b6_fixtures.py`);
- the five real rooms of Stage C (66 checks), read from raw entities without the engine (Phase 2B-5);
- an independent raw-ezdxf census, written for this program, of the reference plan's wall arcs.

Real-plan figures are aggregates.

## Summary

| exp. | question | result | effect on the five real rooms (66 independent checks) |
|---|---|---|---|
| A | can a door's width come from its own jamb lines, and the rest of the wall gap be proven wall? | yes, generally: exact on the synthetic cases, invariant under turn / mirror / metres, refused where the remainder is not proven wall | **8 → 1** failing checks |
| G | does the owner's basin statement settle the last failing check? | yes: the basin-only lobby is no longer typed wet, and the W.C. carries its doorway waterproofing | **1 → 0** (A + G together) |
| B | arc-walled rooms: exact polygon, and the curved wall band? | polygon exact to 1 mm sagitta; the curved band is found and measured exactly; the plan's one curved band was confirmed independently | none (no sample room is curved) |
| C | can single-instance layers be typed from geometry, not from counts? | doors and windows: yes, with jamb and gap signatures. Columns: not separable from hatched drains by geometry alone | none (the plan has many doors) |
| D | does the raster vision prototype cross-check CAD usefully? | it reads the crossing door as 0.80 m (CAD reads 1.027 m); it is not a measurement: bath area −2.7 %, and on the double door no rooms at all | - |
| E | can a BOQ line be traced to its source entities? | rule, formula, inputs, drawing hash and evidence state: yes. Door symbols resolve to DXF handles. Room and strip faces stop at internal ids | - |
| F | are quantities invariant under transformations? | translate, rot90, mirror, metres, reorder and rename: yes. Four failures found: columns lost at 30°, doors held when nested, a zero-length line, a turned sheet frame refused | - |
| H | does the U-C4N CAD MCP's room reader (as a library) help? | 1 of 5 synthetic rooms found; door gaps are left open | - |

## Experiment A: the door's width from its own jamb lines (D-V26-06 residual)

**Rule (clone, `URBAN_EXP=JAMB`).** For each DOOR opening, find the door-layer lines that span the band at full wall
thickness (±10 mm), lie perpendicular to the wall within 2°, and have their midpoint inside the gap. If their outermost
span is narrower than the wall gap by more than 0.05 m, the door takes that span only when each remainder of the gap
is proven wall on both faces. Proven wall means one of two things:

- wall-layer lines lie on the face; or
- it is a junction mouth: two perpendicular wall lines end on the face at the remainder's ends and leave away from
  the band.

The remainders are closed as zero-material WALL items in the face partition, and the opening's threshold lines are
rebuilt from the narrowed span. Nothing is hardcoded: no width, layer or project value.

**Synthetic results (declared roles, synthetic heights 3.00 / 2.40 / 2.10 m).** Truth is by hand.

| fixture | V2.6 | experiment | truth |
|---|---|---|---|
| CROSSING (gap 1.027 m: 0.80 m door + 77 mm return + 150 mm partition) - door width | 1.027 | **0.80** | 0.80 |
| threshold / doorway waterproofing | 0.2054 / 0.2054 m2 | **0.16 / 0.16** | 0.16 |
| bath plaster | 26.2203 m2 | **26.382** | 9.354 x 3.0 - 0.80 x 2.10 = 26.382 |
| bath wall tile | 20.6079 m2 | **20.7696** | 9.354 x 2.4 - 1.68 = 20.7696 |
| bath skirting | 8.477 m | **8.554** | 9.354 - 0.80 = 8.554 |
| bath upturn | 1.7031 m2 | **1.7108** | (9.354 - 0.80) x 0.20 = 1.7108 |
| door reveal plaster | 1.0454 m2 | **1.00** | 2 x 2.10 x 0.20 + 0.80 x 0.20 = 1.00 |
| CROSSING turned 37°, mirrored, in metres, moved | as CROSSING | **identical to CROSSING (1e-6)** | invariant |
| CROSSING turned 90° | as CROSSING | **identical** | invariant |
| OPEN_SIDE (the remainder open on both faces) | 1.027 | 1.027 (refused: not proven wall) | review |
| COLUMN (a column stands in the remainder) | 1.027 | 1.027 (refused) | review |
| PLAIN, DOUBLE (no remainder) | 0.80 / 1.60 | unchanged | unchanged |

The rooms were already right in V2.6 (the partition bounds both rooms). Every error was in the opening's width and
the lines that use it.

**Real plan (Mode A, private run, aggregates).**

- One candidate on the whole plan (1F): gap 1.0233 m, symbol span 0.80 m, remainder 0.2233 m proven wall. Applied.
- No other door changed.
- 13 BOQ keys changed, all in the two rooms beside that door and on the door's own lines:
  - threshold 0.1535 → 0.12 m2;
  - doorway waterproofing −0.0335 m2;
  - plaster and wall tile +0.154 m2 each;
  - skirting +0.073 m;
  - upturn +0.015 m2.
- Stage C re-score: **8 → 1** of 66 failing; all seven failures of the held door's room pass.

**Remaining issues to fix before any method adopts it:**

- the opening record's `position.centre_m` still gives the gap centre;
- the held-door state (DOOR_SYMBOL_FIT_REVIEW) is kept, so the doorway waterproofing stays PROVISIONAL;
- the D-V26-07 remainder strip asks Q_WALL_BAND, which the jamb evidence now answers.

## Experiment G: the basin-only space (owner statement, Part 4)

**Rule (clone, `URBAN_EXP=BASIN`).** An unlabelled space whose fixture blocks are all wash basins is no longer typed
from them. It stays unlabelled with WET_CLASSIFICATION_REVIEW: neither wet nor dry scope is imposed.

**Real plan.**

- Three spaces were typed wet from basin blocks (with toilet-layer linework). All three move to review: 9.35 m2 of
  wet scope (floor tile, waterproofing, wall tile, upturn) leaves the released totals.
- Stage C: the W.C. now carries its doorway waterproofing piece, and with A the failing checks go **1 → 0** of 66.
- The two spaces outside the Stage C sample are unverified. One of them (1.5 m2, one basin and seven toilet-layer
  lines) may be a real W.C. whose WC is drawn as plain lines. The method step must read the WC shape before
  withholding a space (`NEXT_IMPLEMENTATION_PLAN.md` §2.2).

## Experiment B: arc-walled rooms (D-D2)

**B1, the room polygon (`URBAN_EXP=ARC`).** Arc edges are flattened into the face polygon, with a sagitta of 1 mm or
less.

| case | V2.6 | experiment | truth |
|---|---|---|---|
| B10 polygon | the 4.00 x 3.00 chord rectangle (12.0 m2), `rect` 3.00 x 4.00 | 28 vertices, 13.019783 m2, `rect` none | 13.021882 m2 (the flattening loses 0.016 %; the area line itself already uses the exact segment term) |
| B10 membrane strips | 5 strips on the chord | cover the arc segment | - |
| B01 (straight) and the reference plan | - | quantities identical; on the plan only three rooms' polygon vertices change | - |

The finishes that follow the room boundary were already exact on the arc in V2.6:

| line | B10 value | formula |
|---|---|---|
| plaster | 40.972517 | 14.217506 x 3.0 - 1.68 |
| wall tile | 32.442013 | 14.217506 x 2.4 - 1.68 |
| skirting | 13.417506 | - |
| upturn | 2.683501 | - |

**B2, curved wall bands (`URBAN_EXP=ARCBAND`).** A band is two concentric wall-layer arcs (centres within 2 mm) whose
radii differ by a wall thickness (0.10 - 0.45 m), with a common sweep of 0.3 m or more and no concentric arc between
them. As `engine/source/curved_opening.py` already does, it publishes three bases:

- MIN_RADIUS_ARC;
- MID_BAND_ARC;
- MAX_RADIUS_ARC.

The strip area is sweep x (r2² − r1²) / 2.

| case | V2.6 wall run (gross / net) | experiment (MID / MIN) | independent |
|---|---|---|---|
| B10 | 11.0 / 10.2 m; junction pieces 0.79 m2 | MID 14.346206 / 13.546206; MIN 14.217506 / 13.417506; junction 0.12 m2 | wall mass = outer area − room − door strip: 16.010997 − 13.021882 − 0.16 = 2.829115 m2 = straight strips 2.04 + arc strip 0.669241 + junctions 0.119874 (the engine reports 0.12) |
| reference plan | one 0.20 m band missing | +1.885 m on the mean radius (+0.88 % of the plan's wall run); MIN +1.728 m | **raw-ezdxf census (not the engine): the same single band, identical to 1e-6**, plus four short arc stubs (≤ 0.30 m) that neither reader pairs |

The basis is a convention. MID_BAND_ARC is the only basis for which run x thickness equals the band's plan area. This
is the same invariant the straight bands satisfy, so it is the proposed default.

The Phase 2B-5 test (`test_p2b5_curved_wall.py`) wrote its future truth on the room face (MIN). That choice is now
recorded as a convention to decide, not as a fact (`OWNER_DECISIONS.md` D-07). Its "~0.7 %" of the plan's wall run
was an estimate; measured, it is 0.80 % (MIN) or 0.88 % (MID).

## Experiment C: single-instance objects (D-D1)

**Rule (clone, `URBAN_EXP=SINGLE`).** Sub-threshold layers are typed by what their geometry explains, not by how many
instances they hold.

| role | a layer is typed when... |
|---|---|
| DOOR | an anchored swing with its leaf has its hinge within 0.15 m of a wall-gap jamb (radius ≤ gap + 0.10 m), and door symbols explain ≥ 80 % of the layer's linework |
| WINDOW | 1 - 3 lines, ≥ 90 % of them inside wall gaps that hold no door hinge and no door-layer line |
| COLUMN | marked (hatched or crossed) column-size rectangles of any orientation, one polyline or four LINEs, explain ≥ 80 % of the layer |

**Results.**

| set | result |
|---|---|
| benchmark (16 cases, roles inferred) | all 15 single-instance cases become exact: openings correct, B04 / C03 column deducted (+2.18 % → 0) |
| reference plan, synthetic villa and its mirror | layer roles and every quantity unchanged (only diagnostic evidence keys added) |
| adversarial: a wardrobe swing on A-FURN, a threshold line across a door gap | first version: false positives (typed DOOR, WINDOW); after the jamb and door-gap signatures: correctly left OTHER |
| adversarial: a true column drawn as four LINEs | found: 11.91 m2 = 12 − 0.09, exact |
| adversarial: hatched 0.15 / 0.20 m floor drains | **false positive: typed COLUMN** (−0.0225 m2 and +0.60 m of finished perimeter each) |

**Findings outside the experiment.**

- **D-P6-02 (V2.6, today).** A single door drawn exploded (jamb lines, frame lines, leaf, swing) has its layer typed
  **WINDOW**: its lines lie in the wall gap. The swing then bounds the room: 12 − π 0.7²/4 = 11.615155 m2 (−3.2 %),
  perimeter +1.10 m. The benchmark did not show this, because its doors are blocks without jamb lines.
- **D-P6-03 (V2.6, today).** Three hatched drain squares on one layer are typed COLUMN by the count rule: deducted from
  a wet floor, and their faces tiled and upturned.

**Conclusion.** Geometry signatures solve doors and windows. Columns need a second source: the structural plan, a
column schedule, or a declared role. Until then the audit asks for `--layer-roles` (A03 / A04 / A06).

## Experiment D: vision cross-check

The deterministic raster prototype (`tests/m9_p2b5_bench/vision.py`) was run on renders of the new fixtures
(`experiments/vision_crosscheck.py`).

| fixture | vision door | CAD (V2.6) door | truth | vision rooms (m2) | truth |
|---|---|---|---|---|---|
| CROSSING | **0.80** | 1.027 | 0.80 | BATH 4.896, BEDROOM 6.536 | 5.031, 6.519 |
| CROSSING turned 90° | 0.80 | 1.027 | 0.80 | 4.948, 6.463 | 5.031, 6.519 |
| PLAIN | 0.80 | 0.80 | 0.80 | 11.975 (unlabelled) | 12.0 |
| OPEN_SIDE | 1.02 | 1.027 | 0.80 symbol in a 1.027 gap | 11.975 | 12.0 |
| COLUMN | 1.02 | 1.027 | - | 11.975 | - |
| DOUBLE | none | 1.60 | 1.60 | **none found** | 12.0 |

Vision is independent of the CAD pipeline, so its 0.80 m disagrees with CAD's 1.027 m and would have flagged
D-V26-06. It is still not a measurement:

- area errors reach −2.7 %;
- one fixture produced nothing;
- labels are missed.

It stays a review aid under the hybrid rules (never averaged, never released).

## Experiment E: quantity provenance

**Traced line.** The marble threshold of CROSSING (experiment run).

**What the line itself carries:**

- project id and revision-set hash;
- drawing file and SHA-256;
- floor and element id;
- rule (UP-THR-001, rule set, digest, version);
- formula and inputs: opening id, strip face id, depth, length, the D-V26-07 split record;
- evidence state (PROVISIONAL) and geometry confidence (EXACT_FACE);
- notes (assumptions and exceptions), review / RFI and approval state.

**Down to the drawing.**

- Door symbol: `ARCH_OPENINGS.door_symbol = D2:72:0` is document 2, handle 72 (decimal) = 0x48, part 0. Read with
  ezdxf, 0x48 is the swing ARC on A-DOOR. **Resolves.**
- Faces (rooms, strips) and bands: ids such as `SITE-…` and `WB-FL0002-FL0003`. **No output maps them to the
  source lines.** A face's bounding entities cannot be listed without re-running the engine.
- `BOQ_TRACEABILITY.json` is method-level (proof cases per item), not per line.

**Gaps against Part 2's traceability list:**

- a drawing revision label (only the content hash);
- per-line source entity handles for faces and walls;
- exceptions as structured fields rather than notes.

**Proposal.** The topology already carries each boundary item's source id, so publishing `source_entities` per line
costs little. It is in the V2.7 plan.

## Experiment F: generalization (committed V2.6, no clone)

Harness: `tests/m9_p2b6/test_p2b6_found_defects.py` and `p2b6_fixtures.variant`. The sheet frame stays axis-aligned
and each frame's plan turns about its own centre. Totals are compared per item and room, with opening ids masked
because they renumber.

| transformation | CROSSING (declared) | villa (inferred) | PLAIN (declared) |
|---|---|---|---|
| translate (+1e6, −5e5) | invariant | invariant | invariant |
| rotate 90° | invariant | invariant | invariant |
| rotate 30° | invariant | **3 columns lost** (D-P6-04): bedroom floor +0.16 m2, plaster −4.8 m2 (−10.4 %); living +0.32 / −9.6 m2. Declared roles: invariant | invariant |
| mirror | invariant | invariant | invariant |
| metres ($INSUNITS 6) | invariant | invariant | invariant |
| entity order reversed | invariant | invariant | invariant |
| layer rename (inferred roles) | invariant | invariant | invariant |
| plan nested in two blocks | invariant | **5 internal door sets held** (D-P6-05): frame evidence spans 9 - 12 m; flagged REVIEW, every other quantity identical | the external door held |
| rotate 37° + metres | - | - | **an extra zero-length FIN.WP.TERMINATION line** (D-P6-06), otherwise identical to 1e-6 |
| the sheet frame turned too | - | - | refused at admission (PLAN_TITLES_OUTSIDE_ANY_FRAME): safe, not measured |

## Experiment H: a CAD MCP's room reader, run as a library (not an MCP connection)

U-C4N/Autocad-MCP, MIT, commit `cdb1063`:

- its headless ezdxf backend's `rooms_detect`, in an isolated virtual environment (`fastmcp` installed there only);
- `experiments/uc4n_library_run.py`, on four synthetic plans with five rooms.

| plan | U-C4N rooms | truth |
|---|---|---|
| PLAIN | none | 1 room, 12.0 m2 |
| CROSSING | 1 (6.519 m2, exact; no label) | 2 rooms |
| B01 | none | 1 |
| B10 | none | 1 |

Its own documentation says that a foreign plan's door gaps stay open, and the run confirms it: every room with a door
to the outside leaks through the gap. Its layers are chosen by name (WALL / DUVAR), and it reads no room words. **No
integration benefit for room or finish takeoff.** Its record-keeping and pre-flight ideas were already taken in
earlier stages.

**What this is not.** It is not a benchmark of the MCP server: no CAD MCP is connected in this session.

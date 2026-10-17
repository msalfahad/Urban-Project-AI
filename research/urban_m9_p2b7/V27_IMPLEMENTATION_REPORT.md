# ARCH_TAKEOFF_V2.7: implementation report (Phase 2B-7)

## What V2.7 is

**An opt-in method.** `--method ARCH_TAKEOFF_V2.7` on `tools/urban_boq_m9.py arch`. It implies V2.6, and through it
every earlier layer. Policy id `URBAN_BOQ_M9_P2B7_ARCH_V2_7`; output manifest `URBAN_OUTPUT_MANIFEST_V2_7`. It
reads knowledge registry **1.2.0**; V2.4 – V2.6 keep reading 1.1.0.

**Frozen methods untouched.**

- V1 – V2.6 are byte-identical to the Phase 2B-6 snapshot (`TEST_EVIDENCE.md` §1).
- Every V2.7 code path sits behind a keyword that defaults to the V2.6 behaviour.
- The V2.7 logic lives in a new module, `engine/source/arch_v27.py`, imported lazily inside the gated branches.

**Not done, as instructed.**

- No owner policy changed.
- No private reference drawing modified.
- No 95 % accuracy claim.
- No formal blind evaluation started.
- No pricing.
- No Urban Projects Manager integration.

**One new output: `CORRECTIONS_V2_7.json`.** It holds every V2.7 decision that differs from what V2.6 would have
done, and every refusal. A refusal also becomes an UNRESOLVED item. `tools/arch_v27_explain.py` attributes every
V2.6 → V2.7 BOQ difference to one of these records (`BOQ_IMPACT.md`).

## The corrections (Section 2 priorities)

Each was ported selectively from the Phase 2B-6 clone experiments, never wholesale. Each has an acceptance test
whose truth is derived by hand from the fixture coordinates, written before the engine change (`tests/m9_p2b7/`).

| id | correction | where | acceptance tests |
|---|---|---|---|
| D-V27-01 | **Door opening from its own jamb evidence.** The door's structural opening becomes its jamb span when every remainder of the wall gap is proven wall on both faces (a wall return, or a junction mouth). A genuinely wider opening keeps the whole gap, with the remainder's nature named: OPEN, COLUMN, GLAZED_SIDE_PANEL, WALL_ONE_FACE. A held door that then fits strictly is released | `arch_v27.jamb_reconstruction`, `arch_rooms.spaces` | `test_p2b7_doors.py` (18): CROSSING to the hand truth on every quantity (plaster 26.382, tile 20.7696, skirting 8.554, upturn 1.7108, threshold 0.16 m2…); 4 wider-opening variants unchanged from V2.6; PLAIN / TEE / DOUBLE unchanged; 8 placements invariant |
| D-V27-02 | **Layer roles from geometry, with explicit refusal.** One exploded or inserted door hinged at a wall-gap jamb is a DOOR. One to three glazing lines in door-free gaps are a WINDOW. A layer carrying door swings is never typed WINDOW. A layer drawing both a door and glazing is refused (TWO_ROLES) | `arch_v27.layer_roles` | `test_p2b7_roles.py`: exploded single door (the swing no longer subtracted from the floor), block door, wardrobe and threshold lookalikes stay OTHER, mixed layer refused |
| D-V27-03 | **Columns of any orientation, one polyline or four LINEs.** A marked square under the 0.20 × 0.20 m column section is never a column (drains). One or two columns need a wall and must explain their layer, else the role is refused (TOO_SMALL / NOT_EXPLAINING_LAYER / FREE_STANDING). The wall guard counts paired drawn faces, not band spans, so a **row of aligned columns stays COLUMN** (found on the reference plan in this phase) | `arch_v27.layer_roles`, `column_shapes`, `paired_long_m` | drains never columns; four-line, turned and villa variants; aligned rows AT_WALL / FREE_ROW to the hand truth (47.36 m2 / 35.20 m; 47.52 m2 / 36.80 m) |
| D-V27-04 | **Arc-aware rooms and curved wall bands.** Room polygons follow arcs (chords of sagitta ≤ 1 mm, vertices on the arc). The waterproofing boundary types the arc as WALL: the V2.6 false 3.0 m termination is gone. Concentric wall arcs a wall thickness apart join the wall run on the mid-band arc, with MIN / MID / MAX published (basis: owner decision D-07, open) | `arch_rooms._faces_of`, `arch_v27.arc_bands`, `wp_geometry` | `test_p2b7_arcs.py` (9): B10 shoelace within 0.003 m2 of the exact 13.021882; band MID 3.346206 / MIN 3.217506 / MAX 3.474906 m; strip 0.669241 m2 |
| D-V27-05 | **Wet-room evidence UP-WET-002.** A wash basin alone never makes a space wet. Basin + a second, independent piece of sanitary evidence does: a water closet drawn as linework, or sanitary-layer linework **that is not the basin's own fittings** (found on the reference plan). One shape alone or an ambiguous space stays REVIEW, never DRY, and so does its doorway strip | `arch_v27.wet_evidence`, `owner_finish_scope.threshold_lines(wet_review)` | `test_p2b7_wet.py` (13) and the WC adversaries in `test_p2b7_unproven.py` |
| D-V27-06 | **The door opening record UP-DOOR-OPEN-003.** Kept apart: structural opening, leaf, frame, clear passage, owner minimum, allowance, proposed enlargement, status. No quantity changes (Section 4) | `door_standards.opening_record_v27` | `test_crossing_door_opening_record` |
| D-V27-07 | a door block's frame read from the **door symbol's own insert**, not from a group or plan block around it | `door_model.symbol_prefix` | `test_p2b7_unproven.py` §4 |
| D-V27-08 | a waterproofing boundary piece ≤ 0.1 mm merged into its neighbour (never typed as an open edge) | `wp_geometry.segments(sliver_m)` | `test_p2b7_unproven.py` §3 |
| D-V27-09 | **per-line source entities**: every room, opening and wall line carries the drawn entities it is measured from (handle, insert path, part) | `arch_v27.attach_provenance` | `test_p2b7_unproven.py` §1 |

## Section 3: the five separately validated proposals — prototype or accepted

Each was proven against an independent reader (`tests/m9_p2b7/p2b7_indep.py`: ezdxf and math only, no engine module)
or hand truth, on adversarial synthetic drawings.

| proposal | evidence | adversaries | status |
|---|---|---|---|
| **WC recognition from sanitary fixture geometry** | a bowl (closed, curved, elongated loop) touching a cistern set across its axis, in five encodings: loose sanitary layer, loose furniture layer, anonymous block, rotated, mirrored, metres, nested | oval table, vanity counter, bidet, chair, detached cistern, **the basin's own fittings** → REVIEW | **ACCEPTED as corroborating evidence only.** It never types a space alone (WC_CANDIDATE_REVIEW). Two known errors are recorded as strict xfails: a round-bowl W.C. is missed (safe: REVIEW), and an armchair drawn with a W.C.'s outline is taken for one (with a basin: typed wet, flagged) |
| **Nested-plan door scoping** | the frame of a door block is read from its own insert in four placements (flat, group block, plan nested two levels, both): 0.80 m every time, door released, quantities identical | the V2.6 reading pools a group's glazing (2.40 m) or the whole wall (4.40 m) and withholds the door | **ACCEPTED** |
| **Door opening-position recomputation** | the engine's centre and width equal the middle and span of the extreme full-thickness door-layer jamb lines read by ezdxf through every block level, to 1 mm. CROSSING and PLAIN, six placements each | V2.6 keeps the gap middle (as found, asserted) | **ACCEPTED** |
| **Zero-length segment repair** | unit tests on hand-made rings: a 0.05 / 0.099 mm piece merged under V2.7 only, a 2 mm gap kept, lengths conserved, a sliver between two roles joins the piece before it; vertex dedupe | the V2.6 call is unchanged; the drawing that exposed it (PLAIN turned 37°, in metres) now has no zero-length termination | **ACCEPTED** |
| **Per-line source-entity provenance** | 10 drawings (CROSSING moved, turned, mirrored, metres, nested; B10 arc; B10 nested; B02 mirrored door block; B09 mirrored plan; the synthetic villa). Checks: every reference resolves in the DXF, its INSERTs really contain it (outermost first), and a room's entities run along its boundary within 1 mm. **Every boundary point not within 1 mm of a traced entity is an opening of the room** (doors, passages, window thresholds). Wall entities lie on a face of a wall of their family; opening entities at their opening | lines of the same opening id on two floors (fixed: provenance carries floor and region); a door first read as a passage (fixed: the final kind decides) | **ACCEPTED for room, opening and wall lines.** Lines built from no drawn entity (strip remainders, schedule-only items) are recorded NOT_TRACED; there were 10 on the reference plan |

## Section 4: door openings

The record keeps seven readings apart: the CAD-measured structural opening, the door leaf, the frame (only when
drawn), the clear passage, the owner minimum, the allowance, and the proposed enlargement. It also carries the review
status and the owner question.

The owner minimums are 1.00 m for ordinary doors and 0.90 m for bathroom doors. The 1.1.0 registry's +0.10 m
allowance is **not** imposed by V2.7.

**Knowledge 1.2.0.**

- UP-DOOR-OPEN-002 is marked REQUIRES_CONFIRMATION and superseded by **UP-DOOR-OPEN-003**: owner minimum per
  category, applies_to UNRESOLVED.
- The allowance is NOT_ESTABLISHED.
- The 1.1.0 value is kept beside it as `registry_1_1_0_m`.
- The open question is **OQ-05**: does the minimum apply to the structural opening, the leaf, or the clear passage,
  and is there a frame allowance?
- Frozen methods keep reading 1.1.0 unchanged.
- Every V2.7 door row shows the shortfall on each reading. The enlargement is a range (low; high with the registry
  allowance), never applied.

## Known limitations (documented, tested where testable)

**Turned columns.**

- A turned column is a polygon in the room boundary and the waterproofing features.
- It is not used as an opening jamb, nor in the wall-column cut; only axis-aligned boxes are.

**Single free-standing columns.** One or two free-standing squares are refused (FREE_STANDING), never guessed.

**Roles from layer names.** The FIXTURE_LAYER and single WC-block rules are kept from V2.6.

**The WC shape rule.**

- It misses round bowls.
- It can be fooled by a seat drawn with a W.C.'s outline (two strict xfails).
- It is corroborating evidence only.

**Spaces under wet-classification review.**

- A review space carries no finish lines at all (only ARCH.SPACE), including plaster and ceiling, which both
  readings share.
- Recommendation: release the shared quantities (`OWNER_DECISIONS.md` D-18).

**Provenance.** Strip remainders and schedule-only lines are NOT_TRACED (10 lines on the reference plan).

**The curved band basis.** MID_BAND_ARC is used pending D-07.

## Files

**New.**

- `engine/source/arch_v27.py`;
- `tools/arch_v27_explain.py`;
- `tools/kb_build_1_2.py`;
- `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.2.0.json`;
- `tests/m9_p2b7/` (fixtures, independent reader, 8 test files).

**Modified, every change gated by a keyword with the V2.6 default.**

- `engine/source/arch_rooms.py`;
- `arch_walls.py`;
- `arch_measure.py`;
- `door_model.py`;
- `door_standards.py`;
- `knowledge.py`;
- `owner_finish_scope.py`;
- `waterproofing_system.py`;
- `wp_geometry.py`.

**Modified tools.**

- `tools/urban_boq_m9.py`: the method plumbing, the correction log and the provenance.
- `tools/arch_run_audit.py`:
  - A07 no longer flags a curved band the run measures;
  - A03 / A04 read V2.7's column evidence;
  - A03 / A06 become REVIEW when V2.7 refused the layer itself.

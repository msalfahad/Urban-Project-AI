# Executive summary: overnight engineering intelligence program (Phase 2B-6)

## The seven questions of the program's success criteria

**1. How reliable is V2.6?**

The reported baseline was reproduced in full:

| check | result |
|---|---|
| full suite, by test identity | 9 017 tests, 0 state changes |
| frozen outputs | 968 + 272 files byte-identical |
| freeze verifier | 0 differing |
| the five independently read real rooms | 8 of 66 checks failing |

Floor, ceiling, perimeter and windows are exact in every sampled room, and curved room boundaries are exact. The 8
failures have **two** causes, and both are now understood:

- a held door that takes its 1.023 m wall gap instead of its 0.80 m symbol (7 failures);
- a lobby typed wet because it holds a wash basin (1 failure).

V2.6's real weakness is upstream of measurement, in **understanding layers**:

- a single exploded door is typed as glazing and its swing carves the floor (−3.2 %);
- columns disappear when a plan is turned (−10.4 % plaster in one room) or drawn as four lines;
- drains are typed as columns;
- a plan inside a block holds every door.

These are silent today. There is no accuracy figure: the blind evaluation has not started.

**2. Which remaining defects matter most?** In order (`PRIORITIZED_ROADMAP.md`):

1. layer-role understanding;
2. heights (every wall line rests on them);
3. the absent formwork family;
4. the held door and the room-type rules.

Waterproofing and the single doorway are understood, and their remaining exposure is small.

**3. Which existing technologies can genuinely help?**

| technology | verdict |
|---|---|
| ezdxf, Shapely | already the right base |
| Manifold (Apache-2.0) | worth adding to the **test tree** as an independent volume / area check when formwork is built |
| trained floor-plan models | none is cleared for commercial use (CubiCasa5K CC BY-NC; HEAT, DeepFloorplan, Raster-to-Graph GPL; RoomFormer's data non-commercial), and none measures drawings |
| CAD MCPs | none is connected. The U-C4N reader, run as a library, found 1 of 5 synthetic rooms |
| Urban's own deterministic raster prototype | useful as a **cross-check**: it read the held door as 0.80 m when CAD read 1.027 m |

**4. Extend the architecture or improve it selectively?** **Selectively.** Every correction proven tonight fits the
existing pipeline as a small, gated step. No rewrite and no new engine dependency are needed.

**5. What was independently demonstrated?** Against hand truth, raw-ezdxf readings of the real plan (not the engine),
and exact formulas:

- **The held door (Experiment A).** A general rule takes a door's width from its own jamb lines when the rest of the
  gap is proven wall. It is exact on seven synthetic variants (turned, mirrored, metres) and refuses ambiguous cases.
- **The basin lobby (Experiment G).** With the owner's basin rule added, the real rooms go **8 → 0 failing checks of
  66**.
- **Curved walls (Experiment B).** Exact polygons; the curved wall run is measured, and the plan's one curved band
  (+0.88 % of the wall run) was confirmed by an independent census.
- **Single-instance layers (Experiment C).** Typed by geometry, not counts: 15 / 15 benchmark cases exact, with no
  change on the real plan.
- **Generalization (Experiment F).** Invariance under translation, rotation, mirroring, units, reordering, renaming and
  nesting, with four failures found and reported.

**6. What should be implemented next?**

1. An opt-in architectural method carrying exactly the proven corrections (`NEXT_IMPLEMENTATION_PLAN.md`; owner
   decision D-14), with the acceptance tests written first.
2. Then heights from sections.
3. Then formwork and excavation.

**7. How does this move toward a complete, commercially usable villa BOQ?**

- It removes the known silent errors in how drawings are understood, which every finish quantity depends on.
- It ranks the missing BOQ families (formwork, excavation, windows, roofs, external works) above further
  waterproofing work.
- It keeps every claim provable.

The next real step toward commercial use is a second real plan verified the same way, then the owner's blind
evaluation.

## What changed in the repository

| change | effect |
|---|---|
| `tools/arch_run_audit.py` (new, read-only) | names 11 failure modes on any finished run, with evidence and the `--layer-roles` to declare; on the reference plan it raises only the expected findings |
| `tests/m9_p2b6/` | 23 tests: the defects as found with hand truth; invariances; the audit |
| `.claude/skills/urban-cad-audit/SKILL.md` | updated to V2.6 and the audit |
| this folder | the 14 deliverables; experiment scripts; the engine experiment patch (**not applied**) |

**No method, rule or knowledge file was changed.** V1 - V2.6 are byte-identical.

## What did not work, or is not done

- Single-instance **columns** cannot be told from hatched drains by geometry. They need the structural plan or a
  declared role (the audit asks).
- The basin rule needs a WC-shape check before it is safe beyond the sample: one space it withholds may be a real
  W.C. drawn as lines.
- Leaf-closed thresholds and irregular doorway pieces were not re-tested tonight.
- Every correction is proven on **one** real plan.
- No CAD MCP could be benchmarked (none connected).
- The FloorPlanCAD dataset's terms could not be read (its site did not resolve).

## Owner decisions now (`OWNER_DECISIONS.md`)

The three earlier lists are deduplicated. Four questions are answered (the basin lobby by Part 4, wet-room skirting,
door openings, the held door's width) and are not to be asked again.

Open:

| id | decision |
|---|---|
| D-14 | authorise the opt-in method |
| D-01 | the waterproofing junction detail |
| D-04 | project heights / sections |
| D-07 | the curved wall-run basis (mean radius recommended) |
| D-13 | the blind evaluation, after the method and a second plan |
| D-15 | a second real plan |
| D-08, D-09 | the PyMuPDF licence; offcut reuse |

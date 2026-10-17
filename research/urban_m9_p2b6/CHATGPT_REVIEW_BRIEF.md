# Brief for ChatGPT: the overnight engineering intelligence program (Phase 2B-6)

**Context.** Urban Project AI produces villa BOQs from CAD drawings. The owner asked for an overnight program with
these aims:

- verify V2.6;
- find what most limits complete, accurate BOQs;
- research floor-plan AI, CAD MCPs, geometry libraries and the repository's skills;
- run controlled experiments;
- fix only proven, isolated defects;
- deliver a ranked roadmap.

Prices are out of scope. Frozen methods V1 - V2.6 had to stay byte-identical, and private drawings private.

## What was verified

Everything reported by Phase 2B-5 was re-run, not copied:

- **Full suite.** 9 017 tests, identical to the previous head by test identity. The 345 failures + 32 errors are all
  private datasets that are not in the repository. The suite is not called green.
- **Final suite, at this program's commit.** 9 040 tests: the 23 new tests all pass, and none of the 9 017
  existing tests changed state. The same 345 + 32 private-data failures remain.
- **Frozen outputs.** 968 V1 - V2.5 files and 272 V2.6 files, byte-identical.
- **Freeze verifier.** 0 differing; environment in lock.
- **Real rooms.** The five independently read rooms: 8 of 66 checks failing, as reported.

One figure was corrected: curved walls are 0.80 / 0.88 % of the plan's wall run, not "~0.7 %".

## What changed

| change | what it does |
|---|---|
| `tools/arch_run_audit.py` (new) | a read-only audit of a finished run. It turns 11 silent failure modes into findings with evidence and the `--layer-roles` to declare. It changes no quantity and never writes into the run folder |
| `tests/m9_p2b6/` (new) | 23 tests: the defects found tonight, asserted as found with hand truth; invariances under transformations; the audit |
| `.claude/skills/urban-cad-audit` | updated to V2.6 and the audit |
| `research/urban_m9_p2b6/` | the deliverables. The engine experiments are a **patch, not applied** |

**No method, rule or knowledge file was changed.**

## What was only researched

| area | finding |
|---|---|
| floor-plan AI | CubiCasa5K (CC BY-NC); RoomFormer (data non-commercial); HEAT (GPL, non-commercial); Floor-SP; DeepFloorplan (GPL, Python 2.7); Raster-to-Vector; Raster-to-Graph (GPL); CADTransformer on FloorPlanCAD (MIT code, dataset terms unverified). None is cleared for commercial use, and none measures drawings to BOQ tolerance |
| geometry libraries | Clipper2 (Boost), Manifold, build123d, CadQuery (Apache-2.0), IfcOpenShell / ifc5d (LGPL-3.0; ifc5d converts cost schedules, it does not compute quantities) |
| CAD MCPs | none connected |
| knowledge classes | a design for nine classes and a deduplication gate for owner questions |

## What was tested (experiments, isolated clone, synthetic + private real plan)

| exp. | result |
|---|---|
| A, the door width from its own jamb lines | a general rule (the remainder of the wall gap must be proven wall on both faces). Exact on 7 synthetic variants, including turned 37°, mirrored and metres. It refuses open or column remainders. Real rooms: **8 → 1** failing |
| G, the owner's basin rule | a lobby with only a wash basin is not typed wet. Real rooms: **1 → 0** failing. Cost: 3 spaces (9.35 m2) go to review; one may be a real W.C. drawn as lines, so a WC-shape check is needed first |
| B, curved walls | exact polygons; curved wall bands measured. The plan's one band (+1.885 m, +0.88 %) matches an independent raw-ezdxf census to 1e-6. Curved plaster, tile and skirting were already exact |
| C, single-instance layers | typed by geometry (a hinge at a wall-gap jamb; lines in door-free gaps; oriented / four-line rectangles). Benchmark 15 / 15 exact, no change on the real plan. A wardrobe and a threshold line were first false positives, then fixed. **Drains still typed as columns**: geometry cannot tell them apart |
| D, vision | Urban's deterministic raster prototype read the held door as 0.80 m (CAD: 1.027 m), so it is useful as a cross-check. It missed every room on one fixture and was −2.7 % on another, so it is not a measurement |
| E, provenance | lines carry the rule, formula, inputs, drawing hash and evidence state; door symbols resolve to DXF handles; room faces do not list their source entities |
| F, transformations | invariant under translate / rot90 / mirror / metres / reorder / rename. Failed: inferred columns lost at 30°; doors held when nested; a zero-length line (rotated + metres) |
| H, the U-C4N CAD-MCP room reader, run as a library | 1 of 5 rooms found: foreign door gaps stay open |

## What failed or remains unresolved

**New V2.6 defects found tonight:**

| id | defect |
|---|---|
| D-P6-02 | an exploded single door is typed WINDOW, and its swing carves the floor (−3.2 %) |
| D-P6-03 | drains are typed COLUMN |
| D-P6-04 / 08 | turned or four-line columns are not inferred |
| D-P6-05 | a nested plan holds every door |
| D-P6-06 | a zero-length termination line |
| D-P6-07 | a basin-only space is typed wet |

**Still open from before:**

- leaf-closed thresholds;
- irregular doorway pieces;
- doorless cells taking wet scope;
- heights (synthetic in tests).

**Catalogue gaps:** formwork, excavation, window areas and glazing, roof, balcony and external-works finishes,
interlock paving.

**Not available tonight:** a second real plan, a connected CAD MCP, the FloorPlanCAD terms. **Not started (by
instruction):** the blind evaluation.

## Which quantities improved

In the repository, none: no method changed. In the experiments:

| case | quantities |
|---|---|
| real plan | the held door's threshold (+28 % → exact); doorway waterproofing; the adjoining rooms' plaster, tile, skirting and upturn (all to the independent reading); the W.C.'s doorway waterproofing; the curved wall run (+0.88 %) |
| synthetic | exploded-door floors (−3.2 % → exact); turned-plan column deductions (plaster −10.4 % → exact); B10 wall run (−23 % → exact) |

## Which proposed integrations are worthwhile

- **Manifold, in the test tree only**, to verify formwork and concrete junction volumes independently.
- **Keep** ezdxf + Shapely for independent readings.
- **Not now:** trained floor-plan models (licences, domain), CAD MCPs (unreliable room reading), Clipper2,
  OCCT-based kernels, IfcOpenShell (no IFC inputs).

## What the next phase should be

1. **An opt-in architectural method (D-14)** carrying exactly the proven corrections (`NEXT_IMPLEMENTATION_PLAN.md`):
   - the jamb-span door width;
   - the basin rule plus a WC-shape check (knowledge 1.2.0);
   - geometric single-instance door / window roles;
   - oriented and four-line column rectangles;
   - arc polygons and curved bands;
   - nested-plan door scoping;
   - the sliver merge;
   - per-line source entities.

   Acceptance: V1 - V2.6 byte-identical, real rooms 0 of 66 failing, every as-found test re-asserted with its truth.
2. **Heights from sections / schedules** (ASSUMED fallbacks only when the owner approves). They unblock every wall
   line, paint, stairs and windows.
3. **Formwork and excavation** in the structural route, verified with an independent solid check.
4. **A second real plan**, verified like Stage C; then the owner's blind evaluation.

**Questions for ChatGPT to challenge:**

- Is the "remainder proven wall on both faces" rule strict enough for doors set in wider openings with side panels?
- Is the mean radius the right default for a curved wall run?
- Should basin-only spaces go to review, or should the WC-shape check come first?
- Is a column role from geometry ever acceptable without structural corroboration?

# M9 S4 — room accuracy recovered: physical vs functional floor (package notes)

S4 adds no trade, no agent and no MCP research. It makes the architectural route measure the floor correctly first:

- every room as the physical floor it owns;
- voids and shafts out of the floor;
- every m² of each plan accounted for.

The route and its flag are unchanged:

```
python3 -I tools/urban_boq_m9.py arch --drawings PLANS.dxf|PLANS.dwg --out OUT --method ARCH_TAKEOFF_V1 \
        [--reference-areas GF=.. 1F=..] [--facts FACTS.json] [--structural STRUCTURE.dxf ...]
```

New output: `OUT/ARCH_FLOOR_AREAS.json` and the workbook sheet **FLOOR AREAS**. The overlays now show:

- voids, as a blue hatch;
- shafts, in dark grey;
- the cells a room took in through an open passage, dashed;
- each floor's area balance.

## Why (summary)

On the reference villa, S2 and S3 measure every room identically. Against the Round-5 truth engine on the same
drawing revision, five rooms were wrong, two open plans were merged, and the floor total was reported on a partial
basis. `ROOT_CAUSE_REGISTER.md` gives the eleven causes, the fixes and the tests. All the fixes are generic rules in
the existing modules; no parallel engine was added.

## What S4 changes (`engine/source/arch_rooms.py`, policy ARCH_ROOMS_V2)

1. **Door swings** (`match_swings`). A swing serves the one opening it fits:
   - the hinge stands at a jamb;
   - the closed leaf lies along the gap;
   - the leaf fits the width: one leaf, or the two leaves of a double door.
2. **Passages** (`opening_marks`, `open_passages`). What is drawn in each doorless gap is recorded.
   - A clear passage is not a boundary. A second TS01 pass gives a room the unlabelled floor reached only through
     clear passages from it.
   - Shared spaces, larger spaces and marked gaps stay apart.
   - Physical regions (cells joined through every clear passage) are reported beside the functional rooms.
3. **Wall bodies** (`wall_caps`, `_face_point`). One-sided caps are added, and every cap ends ON the drawn segments.
   Closure B (`closures_b`) closes a door's doorway piece on the wall's other face.
4. **Voids** (`x_rect_at`, `void_outlines`). A VOID word inside an X-marked rectangle (any rotation, a hand-drawn
   second line) or a void symbol: the void is recorded per face and never floored.
5. **Shafts** (`stacked_shafts`, run level). The same doorless footprint on the other plans.

`engine/source/arch_floor.py` (new) reconciles each plan. It splits every face into one of these categories:

- wall and column mass;
- doorway strips;
- slivers;
- room floor;
- open-plan floor;
- unallocated (merged, mixed or unlabelled);
- void;
- shaft;
- stair flights;
- stair landings (bounded);
- the stair below seen through an opening;
- external.

Its checks:

- faces = categories;
- plate = faces (the top-level outer boundary of the wall networks);
- floor-finish lines = room floor + open-plan floor.

`arch_measure` (ARCH_MEASURE_V2) takes the floor finish from the same split. A void, a stair below and the plan's own
treads never become porcelain. A door closed on both faces gets its waterproofing doorway line.

## Tests

| Suite | What |
|---|---|
| `tests/m9_s4/test_s4_rooms.py` | Every mechanism of the register, reproduced on hand-built plan entities (`tools.arch_synth.s4_floor / s4_walls / s4_voids / s4_shaft_plans`) with hand-derived truth. It also covers conservation on the S2 villa and the S3 stairs, and the workbook sheet. |
| `tests/m9_s4/test_s4_real_regression.py` | The exact rooms S2 / S3 lost, the three stacked shafts and the outlined void on the real plan. It is skipped unless `URBAN_REAL_PLAN_DXF` and `URBAN_R5_REGISTERS` are set; the expected values are read from the frozen Round-5 registers at run time. |

The full-suite record is in `TEST_GATE_M9_S4.json` (the gate stays INCOMPLETE).

## Limits (unchanged rules)

- Machine quantities only (MACHINE_ONLY): no prices, nothing quotation-ready, no accuracy claim beyond the
  differences shown.
- An attached alcove or vestibule is PROVISIONAL and flagged (ATTACHED_THROUGH_OPEN_PASSAGE).
- A merged open plan stays unallocated until a drawn boundary or an owner rule splits it.

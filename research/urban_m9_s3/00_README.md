# M9 S3 — geometry and takeoff acceleration (package notes)

S3 extends the architectural takeoff route of S2 (`urban_boq_m9 arch --method ARCH_TAKEOFF_V1`). It adds:

- stairs of every drawn shape;
- wall runs and a room graph;
- a terminal flag on every unresolved item;
- a DWG adapter;
- the structural drawing's lines in the same workbook.

Nothing is installed, connected or invoked from an MCP server. The external repositories were read as references only
(`ADOPTION_MATRIX.md`).

```
python3 -I tools/urban_boq_m9.py arch --drawings PLANS.dxf|PLANS.dwg --out OUT --method ARCH_TAKEOFF_V1 \
        [--structural STRUCTURE.dxf|.dwg --conventions engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json \
         [--profile ROUTE_G_PROFILE.json] [--as-of YYYY-MM-DD]] [--facts FACTS.json] [--reference-areas GF=..]
```

## What S3 adds to the pipeline

1. **Readers** (`tools/arch_intake.py`, `tools/dwg_adapter.py`)
   - The Arabic (101) keyboard table of keyboard-mapped SHX fonts is now one-to-one. Before, the lam-alef key typed
     two letters and shifted every later key.
   - The K2 kernel's ellipses reach the route as 1 mm chords. These include circles and arcs placed under a
     non-uniform block scale.
   - A room-tag block's ATTRIB names a room.
   - A DWG goes through an external converter, run as a separate program: LibreDWG `dwg2dxf` or the ODA File
     Converter.
     - The converter's sha256 is checked against `engine/source/decoder_pins`.
     - Proxy and custom objects are counted as losses.
     - With no converter, the run stops with the remedy; it never reads an empty drawing.
2. **Stairs** (`engine/source/arch_rooms.py`)
   - Curved and winder flights are found from radial tread lines. The centre is refined by the existing
     `stair_geometry.fan_centre`.
   - Straight flights are split when the two legs of a dog-leg share one layer.
   - Each tread is its own polygon: a rectangle, or a wedge between two radial lines.
   - The same flight drawn twice (nosing and riser lines on two layers) is one flight.
   - Plans are aligned on their column grid. A flight lying over a flight of the plan below is read as one of:
     - `SEEN_THROUGH_VOID`: a void is marked at the stair assembly. It is counted once; the repeat is exposure.
     - `STACKED`: no void. It is counted as the next storey's flight and flagged for review.
3. **Walls and the room graph** (`engine/source/arch_walls.py`)
   - Wall run by thickness family, where both faces are drawn. Openings, wall ends and columns standing in the wall
     line are excluded.
   - Each wall is classed EXTERNAL / INTERNAL by the space on each face.
   - A room graph of shared walls (lm by thickness) and openings (with their sides).
   - Plan-area conservation: wall-mass faces = band strips + junction pieces. Column squares and glazing strips are
     listed apart.
4. **Measurement** (`engine/source/arch_measure.py`, rule set 1.5.0)

   | Item | Line | Rule | Status |
   |---|---|---|---|
   | Tread marble | `FIN.MARBLE.TREAD` | UP-STAIR-003 | PROVISIONAL; each tread its own polygon |
   | Commercial step basis | `FIN.STAIR.STEP_LM` | UP-STAIR-008 | PROVISIONAL; sum of step widths |
   | Visible riser marble | `FIN.MARBLE.RISER` | UP-STAIR-003 | BOUNDED between the n and n + 1 riser readings once a riser height is given; BLOCKED without one |
   | Landing marble | `FIN.MARBLE.LANDING` | UP-STAIR-005 | BOUNDED: the stair enclosure less its treads |
   | Floor finish | | UP-STAIR-005 | treads inside a finished room leave its floor finish (the ceiling keeps them) |
   | Wall run | `ARCH.WALL_RUN` | | lm, PROVISIONAL |
   | Block walls | `MAS.BLOCK` | | BLOCKED until the wall material (legend / specification) and the block height are given |

   Every unresolved record carries:
   - item, location and reason;
   - source reference (drawing, plan region, sheet, face);
   - module / function;
   - cause: SOFTWARE (the engine does not read it yet), SOURCE (not in these drawings) or REVIEW (a person decides);
   - next action.
5. **Outputs** (`tools/urban_boq_m9.py`, `engine/boq_room_workbook.py`, `tools/arch_overlay.py`)
   - `ARCH_WALLS.json`.
   - `DWG_CONVERSION.json`, when the input is a DWG.
   - `run.cross_plan_stairs` in `ARCH_PLAN.json`.
   - The MARBLE sheet now carries treads, risers, landings and steps.
   - A MASONRY sheet (architectural runs only).
   - The UNRESOLVED sheet carries the flag columns on an architectural run.
   - With `--structural`, the STRUCTURAL sheet holds route G's lines and route G writes its own files to
     `OUT/structural`.
   - The overlays show the treads (dashed when seen through a void) and the wall centrelines.

## What stays unchanged

- Route G and every structural output. `OUT/structural` is byte-identical to `urban_boq_m2 run`; only `run_log.json`
  timings and paths differ.
- The S1 commands and workbook (the S1 sheet set is unchanged).
- Every frozen milestone.
- No prices.
- Rebar keeps its own line family (never a ratio).
- The architectural census families appear only on an architectural run.

## Tests

`tests/m9_s3/test_s3_takeoff.py`: synthetic drawings from `tools/arch_synth.py`, with truth written by hand.

- **Stairs fixture** (`stairs()`):
  - curved fan wedge areas, ½ sin 15° (r_out² − r_in²) per tread;
  - a dog-leg on one layer;
  - the porcelain deduction;
  - the landing bound;
  - two plans with a void and a stacked flight.
- **Villa variants**: nested doubly-mirrored doors, ATTRIB room labels and Arabic SHX keyboard text must give the
  same takeoff.
- **Entity fixture** (`entities()`):
  - ellipse chords within 0.05 % of Ramanujan's perimeter;
  - MINSERT cells, ATTRIB, MTEXT;
  - MLINE, SPLINE and 2D POLYLINE lengths.
- **Walls**: conservation (hand: plate − rooms − doorway pieces) and the room graph.
- **Recognisers**: a radial recogniser rotation test and its refusals (tangent lines, parallels).
- **Floors**: the floor offset from the column grid.
- **Flags and census**: every unresolved record is flagged; census states.
- **DWG**: blocked without a converter; a stub converter run through the CLI.
- **Structural**: `--structural` against `urban_boq_m2 run`.
- **Oracle**: a Shapely / GEOS oracle on 300 random clips (test-only dependency).
- **Hygiene**.

## Known limits (S3)

- Spaces are still not split by non-wall lines: an open-plan face with an exterior word stays MERGED, with its
  question.
- The landing outline, the riser height, the finish heights and the block material and height are not in a plan.
  Those lines stay BLOCKED or BOUNDED.
- The void-or-stacked reading of a repeated flight is a rule on drawn evidence (a void mark within 1.0 m of the stair
  assembly). Each reading is flagged for review.
- The n tread lines bound n − 1 treads. A top nosing drawn instead of the landing edge leaves one tread undrawn
  (noted on each line).
- Native DWG needs a converter on the machine. None is installed here; the adapter is tested with a stub.
- Machine quantities only (MACHINE_ONLY): nothing is reviewed or quotation-ready, and the regression gate stays
  INCOMPLETE.

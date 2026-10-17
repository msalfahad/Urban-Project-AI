# M9 S2 — architectural takeoff route (package notes)

S2 turns architectural plan drawings into a room-by-room BOQ through one production command. It is behind the
versioned method flag `ARCH_TAKEOFF_V1`, which has no default:

```
python3 -I tools/urban_boq_m9.py arch --drawings ARCH_PLANS.dxf --out OUT --method ARCH_TAKEOFF_V1 [--facts FACTS.json]
```

## Pipeline

1. **Read** (`tools/urban_intake.py`, unchanged) the drawing, plus every hatch with its islands, in WCS, including
   hatches inside blocks (`tools/arch_intake.py`; used by this route only).
2. **Plan regions** (`engine/source/arch_plan.py`): sheet frames and floor-plan titles (EN / AR), with a frame split
   when it holds several titles.
3. **Layer roles** from geometry:
   - WALL: the layer whose bands carry jambed openings; secondary wall layers must attach to it.
   - COLUMN: filled / crossed small squares.
   - DOOR: swings with a leaf, hinged on a wall.
   - WINDOW: lines inside wall-band gaps.

   `--layer-roles` overrides a role, and the override is recorded.
4. **Rooms** (`engine/source/arch_rooms.py`): TS01 faces of the wall network.
   - Faces are closed at jambed openings (thresholds) and at door symbols.
   - Wall ends are capped.
   - Boundaries are one-sided by role.
   - Faces are named from room words through a controlled bilingual lexicon.
   - Classes: ROOM / MIXED / MERGED / UNLABELLED.
   - Straight stair flights are recognised from their tread lines, and void symbols from their diagonals.
5. **Measurement** (`engine/source/arch_measure.py`, rule set 1.5.0): canonical lines per room.
   - floor finish, net of obstructions
   - ceiling (PROVISIONAL)
   - skirting: UP-CER-003, and UP-CER-004 in wet rooms by tile height
   - wet-room membrane floor / doorway / upturn: UP-WP-001 / -003 / -002
   - plaster / paint / wall tile, by the `wall_height` ladder (UP-CER-009); never a floor-to-floor interval
   - openings
   - stair flights (from a sourced riser height)
6. **Materials:**
   - tile layouts: rectangle exact (`tile_layout.best`) or any polygon (`tile_layout.best_polygon`);
   - membrane roll plans: rectangle (`membrane_layout.plan`) or polygon (`membrane_layout.plan_polygon`).

   The polygon engines reproduce the rectangle engines exactly on rectangles.
7. **Outputs** (`tools/urban_boq_m9.py`, `engine/boq_room_workbook.py`): the M9 files plus ARCH_PLAN / ARCH_ROOMS /
   ARCH_OPENINGS / UNRESOLVED and SVG overlays. The workbook carries a ROOM BY ROOM BOQ sheet with
   `FLOOR | ROOM | TRADE | ITEM | DIMENSIONS | GROSS | DEDUCTIONS | NET QUANTITY | UNIT | WASTE % | WASTE QUANTITY |
   PROCUREMENT | SOURCE | STATUS`, where NET = GROSS − DEDUCTIONS as formulas and totals are formulas.

## What stays unchanged

Route G and every structural output, the S1 commands, census and workbook, and the rule set. A census family of the
architectural route appears only on an arch run.

## Facts

`SYNTHETIC_FACTS_S2.json` shows the `URBAN_ARCH_FACTS_V1` schema with synthetic test parameters. Every value carries
its authority; a value without one is refused.

## Tests

`tests/m9_s2_arch/` uses a synthetic two-floor villa and a hatch fixture from `tools/arch_synth.py`, with truth
written by hand from the coordinates. The tests cover:

- areas, boundaries and openings
- wet rooms
- heights
- stairs
- tiles and membrane through the production path
- metamorphic variants
- the CLI and workbook
- polygon layouts against rectangles
- the hatch reader against the unchanged route G reader
- recognisers, facts and hygiene

## Known limits (S2)

- Spaces separated only by non-wall lines stay MERGED / MIXED: area plus a question, no finish.
- Spaces without a room word stay UNLABELLED.
- Text in legacy SHX big-fonts is not decoded.
- Curved / winder flights are not recognised.
- Wall finishes, tile materials and stair flights need their facts.
- Machine quantities only: no prices, and nothing is quotation-ready.

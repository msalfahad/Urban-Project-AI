# M9 S5: zones of open spaces from drawn lines, double height, one doorway piece per shared wet door (package notes)

S5 adds no trade, agent, MCP dependency or third-party package. It extends the architectural route's existing modules. The principle is S4's: geometry first, classification second, quantities third, independent checks last.

The route and its flag are unchanged:

```
python3 -I tools/urban_boq_m9.py arch --drawings PLANS.dxf|PLANS.dwg --out OUT --method ARCH_TAKEOFF_V1 \
        [--reference-areas GF=.. 1F=..] [--facts FACTS.json] [--structural STRUCTURE.dxf ...]
```

## What S5 changes

### `engine/source/arch_rooms.py` (policy ARCH_ROOMS_V3)

1. **Zones of an open space** (`zone_partition`, `zone_candidates`, `_zone_groups`). A MERGED face holds words needing different finish families (wet or exterior with dry). It is split **only along lines drawn inside it**, by a third TS01 pass:
   - **Which lines.** The lines of non-structural layers, clipped to the face. Excluded:
     - stair flights;
     - X-marked rectangles / void symbols;
     - fixture layers;
     - lines running more than 0.45 m outside the face.
   - **Grouping.** The atomic cells are grouped by room words, tags and fixtures, then by finish family.
   - **Kept lines.** A line is kept only between two groups.
   - **Word-less cells.** One joins a zone only when it opens nowhere else; one touching several zones takes all their words.
   - **Conservation.** The zones must partition the face, or the split is withdrawn.

   Zones are PROVISIONAL and flagged ZONE_FROM_DRAWN_LINES. A wall is never invented, and nothing drawn is snapped.
2. **Double height** (`voids_above`, run level). An outlined void is carried onto the plan below by the column-grid alignment and corroborated by the lower plan's own X-marked opening. The space under it has no ceiling at its level.
3. **Repair log** (`spaces()["repairs"]`). Every boundary piece the engine adds (wall caps, door closures) is logged with its rule, tolerance and reason. No drawn entity is moved, extended or deleted.

### `engine/source/arch_measure.py` (policy ARCH_MEASURE_V3)

- **Zones** are measured as rooms (PROVISIONAL); there is no wall finish along a zone line.
- **Waterproofing.** A door between two wet spaces has one doorway piece (UP-WP-003).
- **Ceilings.**
  - NORMAL_LEVEL: net of the part under a void above;
  - DOUBLE_HEIGHT: its own line over the room's void;
  - STAIRWELL: BLOCKED until the section.
- **Stairs.** Flight sides are classified WALL / OPEN (`flight_sides`). Guardrails go on open sides only, sloping (UP-STAIR-012); no wall handrail unless shown (UP-STAIR-013).
- **Openings** name their host wall band, type, height and area state, and the evidence of their kind.

### Tools and workbook

- **`tools/arch_intake.py`:** the `\U+XXXX` escapes of pre-2007 DXF text are decoded exactly (state DXF_UNICODE_ESCAPE; the raw text is kept). Arabic room words of a DXF saved as R2000 / R2004 were lost before.
- **`tools/urban_boq_m9.py` / `tools/arch_overlay.py`:**
  - `ARCH_PLAN.json` records `run.double_height` and `regions[].repairs`;
  - `ARCH_FLOOR_AREAS.json` records `zones`, `zone_lines` and `double_height`;
  - the overlays draw the zone lines (dashed magenta) and the void of the plan above (dashed blue).
- **`engine/boq_room_workbook.py`:** a new SOURCE EVIDENCE sheet (zones and their drawn lines, voids carried down and what corroborates them, shafts, added boundary pieces).

## Tests (`tests/m9_s5`)

| File | What |
|---|---|
| `test_s5_zones.py` | zones on hand-built entities (`tools.arch_synth.s5_zones`, truth derived by hand); symbols, section lines and furniture never split; no drawn lines → no split; a line 3 mm short of the wall closes nothing; a dry-only open plan is untouched; metamorphic: translation, 37° and 90° rotation, mirror, entity order, collinear subdivision, furniture; hygiene |
| `test_s5_ceilings_wp.py` | double height across two plans (`s5_double_height`), corroboration, cross-floor conservation, no common grid → not applied; one doorway piece per shared wet door (`s5_wet_pair`); a blocked stair-well ceiling; flight sides; the repair log never moves a drawn entity |
| `test_s5_metamorphic_cad.py` | the S2 villa saved as DXF R2000 / R2018 measures the same; line vs polyline zone boundaries; `\U+XXXX` decoding |
| `test_s5_real_regression.py` | the real plan (skipped unless `URBAN_REAL_PLAN_DXF` is set): the merged space is split on drawn lines with a small unallocated remainder; every floor balances; the void above is corroborated and its ceiling counted once; shared wet doorways once. Structural assertions only: no figure of the drawing is in the code |

## Limits (unchanged rules)

- Machine quantities only (MACHINE_ONLY): no prices, nothing quotation-ready, no accuracy claim beyond measured differences.
- A zone from drawn lines is an inference: PROVISIONAL and flagged for review. Linetype (dashed hidden lines) is not yet read.
- A DWG round trip needs a converter that is not installed: untested.

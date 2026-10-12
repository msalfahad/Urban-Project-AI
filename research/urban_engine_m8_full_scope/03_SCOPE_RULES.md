# 03 Scope rules — how M8 measures or bounds every finding

**Code:** `engine/source/scope_quantities.py` (the scope pass) and `engine/source/generic_route.py` (`_stair_items`).

**Conventions:** `engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json`. V6 is V5 plus 37 M8 conventions, each with
low / base / high values, provenance and rationale (listed in `02_CONVENTIONS_V6.csv`).

**Gating:**
- Every behaviour below is switched on by a named convention.
- Without the V6 conventions the route runs exactly as M7 did.
- The checks behind that claim are in `10_PROPERTIES_AND_REGRESSION.md`.

## 1. The finding states

The completeness pass (M6) says what the drawing shows that no item holds. The scope pass gives every finding one
state.

| State | Meaning | In the measured total | In the bounded total |
|---|---|---|---|
| MEASURED | PROVISIONAL items from the drawn geometry | yes (through the items) | yes (item low / high) |
| BOUNDED | an exposure range (low may be negative: a possible void or over-count) | no | yes |
| HELD_BY_ITEMS | the finding restates UNRESOLVED items | no | through the items, once |
| EXPLAINED | the family it names is measured, or may be a drawn group of the same plan | no | no |
| QUALIFIER | a note or conflict on a measured member, or a group on a non-structural layer | no | no (0 .. 0, stated) |

**Bounded total** (BOQ section F) = measured (planning) + every UNRESOLVED item's exposure + every BOUNDED finding,
low and high. A finding never adds twice.

**Target:** 0 findings without a range.

## 2. When a family is settled

A finding is measured only when its family is settled. All of these must hold:
- one family, with confidence MEDIUM or HIGH;
- no candidate families;
- the layer name and the notes beside the group do not name two different element families.

For example, a group on a `POOL` layer with a `LIFT` note beside it is not settled.

**Non-structural layers.** A group on a layer named for furniture, fixtures, services or landscape is a qualifier,
never measured. The words are listed in `NON_STRUCTURAL_LAYERS`.

**Printed values.** Printed dimension notes beside the element (DEPTH, HEIGHT, THK, WAIST, RISER, RISE, SHELL, RING,
FLOOR, COVER):
- They are read in metres, taking the one plausible unit.
- The nearest note wins.
- A printed value replaces the convention for that dimension. This is `PRINTED_DIMENSION_NOTES`.

## 3. Measured families

| Family | Geometry read | Formula | Conventions when not printed |
|---|---|---|---|
| Stair zone (route) | drawn tread lines in a STAIR_ZONE face | `stair_measure`: flight + landing (zone − flight) × waist | storey rise (printed levels); when it gives a riser outside 0.14–0.20 m the zone holds part of a stair and the drawn run is measured with `STAIR_RISER_M` (`STAIR_DRAWN_RUN`); waist `STAIR_WAIST_CONVENTION_M` (`STAIR_UNPRINTED_WAIST`) |
| Loose flight (scope) | tread lines of a settled stair group, or inside a stair-well opening; split into flights by along-line extent and gaps; a missing line inside a run is counted; a fan of lines is a winder; one layer at a time | straight: `stair_geometry.straight_flight`; winder: plan × (waist / cos + R / 2); risers by both riser rules (range) | `STAIR_RISER_M`, `STAIR_WAIST_CONVENTION_M`; the same flight drawn on two plans is measured once (`STAIR_FLIGHT_ON_TWO_PLANS`) |
| Pool | ring (double outline), wall strip, or single outline | walls = wall plan area × height; floor = outer area × thickness | `POOL_WALL_HEIGHT_M`, `POOL_FLOOR_THICKNESS_M`, `POOL_WALL_THICKNESS_M` (single outline) |
| Lift pit | ring, outline with inner faces broken at the corners, or single outline | walls × depth; base slab unless inside a measured footing | `PIT_DEPTH_M`, `PIT_BASE_THICKNESS_M`, `PIT_WALL_THICKNESS_M` |
| Water tank | ring / outline | walls × height; cover (+ base when not on a slab plan) | `TANK_HEIGHT_M`, `TANK_SLAB_THICKNESS_M`, `TANK_WALL_THICKNESS_M` |
| Dome | two concentric circles (ring + shell), or radial ribs | cap π (r² + h²) × t, h = ratio × r; ring area × ring depth | `DOME_RISE_RATIO`, `DOME_SHELL_THICKNESS_M`, `DOME_RING_DEPTH_M`; on the topmost slab plan a radial / ring group is a dome when the set names domes (`DOME_ON_TOP_PLAN`) |
| Boundary wall | wall strip of the family | strip length × the section of the family's schedule row of the drawn width | `BOUNDARY_WALL_ROW_BY_WIDTH`; no row: bounded |

Two rules apply to all the measured families:
- **Rebar.** Reinforcement for every measured scope item is MISSING_DATA. It is never a kg/m³ ratio.
- **Dome ribs.** A winder zone on the topmost slab plan is not measured by the route
  (`STAIR_WINDER_ON_TOP_PLAN`): dome ribs fan about one point too.

## 4. Bounds (`FINDING_BOUNDS`)

| Finding | Range |
|---|---|
| region held for a detail / unresolved | 0 .. area × the higher of the sheet thickness and `SLAB_THICKNESS_EXPOSURE_M` high |
| opening not deducted | −area × panel thickness .. 0 |
| column drawn, no item | 0 .. its own volume |
| column item, no presence | −its volume .. 0 |
| column band, no outline | 0 .. occurrences × the largest measured column of the storey |
| member detected, no item | 0 .. plan area × the deepest section of its family |
| schedule row on no plan / unread | 0 .. one instance (a beam over the longest measured beam); sizes read in cm or mm |
| label not consumed / not scheduled | 0 .. one member of its family |
| label on a member measured as another mark | the volume difference between the two sections (either sign) |
| member overlap | −overlap × depth .. 0 |
| fill on a measured member | −fill area × the host's thickness .. 0 |
| note on a member (dependency) | qualifier |
| storey plan missing | min .. max of the neighbouring storeys' slab + beam (one neighbour: 0.5 .. 1) |
| referenced, not drawn | parapets: free roof edge (raster of the plan outline, holes excluded, minus the plan above) × the high section; tank / pit / pool / dome: one element at its convention size; any other family: `REFERENCED_ELEMENT_ALLOWANCE_M3`; low 0. Not given when a drawn structural group on the noted plan may be that element |
| drawn, not settled | by shape: strip L × w × `UNEXPLAINED_STRIP_DEPTH_M`; ring: walls at the highest wall height + base and cover; closed area: area × slab high (none for an outline round every slab face: a plot line); circles: a dome at the high values; radial: the dome or the winder; linework: half the length × `UNEXPLAINED_LINEWORK_SECTION_M2`; low 0 |
| a fill round the whole plan | plain concrete 0 .. area × `BLINDING_THICKNESS_EXPOSURE_M` high |
| route item UNRESOLVED without an exposure | 0 .. the largest measured member of its family (storey) |

## 5. What the scope pass never does

- It reads no reference quantity. The external positions are read only by the post-freeze ST7757 runner, and only
  as differences.
- It never confirms an uncertain family. A pit that could be a lift or a tank is bounded under both, not measured.
- It never uses a ratio. Concrete is geometry × section. Reinforcement for the new families is MISSING_DATA.

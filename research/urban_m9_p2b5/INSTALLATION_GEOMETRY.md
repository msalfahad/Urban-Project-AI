# Waterproofing installation geometry - ARCH_TAKEOFF_V2.6

Module `engine/source/wp_install.py` (policy `WATERPROOFING_INSTALLATION_V1`). It is reached only through
`ARCH_TAKEOFF_V2.6` (`waterproofing_system.build_area(..., v26=True)`). It reads the plan the V2.5 layout actually
cut and says what that plan means on site. **It changes no quantity of the layout and selects no detail**: open
details stay open and alternatives are shown side by side.

## 1. Inputs

| input | from | content |
|---|---|---|
| the cut plan (trace) | `membrane_layout` with `trace` on (V2.6 only) | every roll segment in cutting order (roll, position along the roll, length, purpose); for each floor strip its place (strip number, frame origin, width, along-interval, frame angle, direction); for each ripped segment where its band lanes start; every band piece (lane, offset along the lane, length, lap); every doorway and detail piece (from a lane or a whole segment) |
| the typed boundary | `wp_geometry.ring_segments` | the outer ring and each hole as segments typed WALL / DOOR / OTHER / PASSAGE (holes: COLUMN), in ring order |
| transitions | V2.5 doorway topology | per doorway: UPTURN_ACROSS_THRESHOLD (the band is closed across the door because the other side is also waterproofed) or JAMB_RETURNS |
| project values | rules sheet (optional) | minimum joint offset (product data), minimum reusable offcut size (N-7), a project junction detail (N-11). None of them is assumed |

The trace is built from value-identical subclasses of the numbers the V2.5 planner already uses (`_Seg(tuple)`,
`_Lane(float)`, `_Piece(float)`), so the planner runs the same arithmetic and makes the same choices. The tests check
this for all twelve Phase 2B-3 proof cases (`test_p2b5_trace.py`).

## 2. Seven quantities kept apart

| quantity | definition | where |
|---|---|---|
| geometric surface (proven subtotal) | floor net area + upturn surface (eligible boundary length x upturn height) + doorway continuations | V2.5 row, unchanged |
| installed | the area each laid piece covers, laps counted once in each piece that forms them | `piece_plan.balance.installed_m2` |
| cut (consumed) | the length cut from rolls x roll width | `balance.consumed_m2` |
| reusable offcut | an offcut at least one band wide and longer than an end lap: a band lane could come from it. Kept only if N-7 sets a minimum size; until then `REUSABLE_SUBJECT_TO_N7` | `balance.reusable_m2` |
| true waste | every other offcut: rip remainders narrower than a band, lane ends no longer than an end lap, width trims, floor beyond a wall line, drawing tolerance | `balance.true_waste_m2` |
| roll stock | the uncut length of each roll x width | `balance.roll_stock_m2` |
| procurement rolls | whole rolls of the shared cutting plan, per membrane system (never across systems) | `MEMBRANE_CUTTING_PLAN.json` |

Plus the **unresolved details** list (flags and the junction alternatives), which is never folded into a quantity.

The balance closes for every area (the engine raises if it does not):

    consumed = installed + reusable offcuts + true waste
    rolls x roll area = consumed + roll stock

## 3. The piece plan

Every node has an id. Segments are `R{roll}-{k}` (the k-th cut along roll `roll`). A segment is either used **WHOLE**
(one floor strip of full roll width) or **RIPPED** along its length into:

- the floor strip part `S{i}` (strip i), its doorway pieces `DW-{door}` cut whole from it, detail patches `P{n}`;
- band lanes `R1-2/L{q}`, one band width each;
- the rip remainder `R1-2~w` (an offcut).

Each lane is **cross-cut** into band pieces `B{seq}` (the order they are laid), doorway or detail pieces, and the lane
remainder `R1-2/L{q}~l`. A piece narrower than the band (a doorway piece 0.30 m wide from a 0.30 m lane is not; a
detail patch may be) is cut band-wide first (`B3^`) and then trimmed (`B3~t`).

The floor material beyond the room's wall line is an offcut of its strip: `S3.o1`, `S3.o2`, ... as real rectangles
(width, length, and position inside the strip `in_piece_m`) where the walls inside the strip are parallel to the strip
frame; otherwise one shaped trim `S3.o~` (area only, flag `SHAPED_TRIM_NOT_DECOMPOSED`). A strip that falls short of its
rectangle by no more than 1 cm2 (`TRIM_NOISE_M2`) is a wall line drawn a hair off square: the sliver is recorded as
"drawing tolerance at the wall line" (true waste, area kept for the balance), never as a cut and never flagged.

A doorway listed twice keeps both pieces (`DW-D1`, `DW-D1#2`) and is flagged `DUPLICATE_DOORWAY_PIECE` - it is never
silently double counted and never silently dropped.

## 4. The boundary and the band runs

The band (the upturn strip of the separate-upstand model) runs along the boundary in runs. A run starts after a break
(a doorway that is not crossed, an open edge, a passage) and ends at the next one; a ring without breaks is a closed
loop. Runs are taken in the same order as the V2.5 band planner (outer ring first, then holes; each from its first
break), so the planned pieces land on the runs they were planned for (`INSTALLATION_GEOMETRY_MISMATCH` otherwise).

| feature | how it is placed | output |
|---|---|---|
| internal corner | a vertex where the run turns into the room | `corners.internal`; the flange folds a pleat; detail withheld (UP-WP-004) |
| external corner | a vertex where the run turns away (an L-step, a column face) | `corners.external`; the flange leaves a gap; detail withheld |
| doorway (not crossed) | the run ends at both jambs; the doorway piece meets the band end to end | two `BUTT_JOINT_OPEN` jamb junctions per door |
| doorway (crossed, UPTURN_ACROSS_THRESHOLD) | the band continues across the threshold; the run stays closed | no jamb junction |
| jamb returns (JAMB_RETURNS) | virtual run parts up the jamb reveals, with two external corners | `RETURN_ON_JAMB` |
| open edge (balcony front, roof edge without parapet) | the run ends | `TERMINATION_OPEN` (termination detail open) |
| column / shaft inside the area | a closed run around the hole | its own closed loop, external corners |
| parapet | a wall of the roof area: the band rises the upturn height (UP-WP-003) | as a wall; a taller parapet upstand is a project value, not assumed |

**Band pieces** are placed by their covers: the k-th piece of a run covers `[s - lap, s + cover]`, so it laps one end
lap over the piece before it; in a closed run the first piece laps over the last (the closing joint, drawn at the run
end). A joint is where two pieces overlap. For each joint the layer reports its distance to the nearest corner and to
the nearest floor-seam end; a joint inside a corner is `JOINT_AT_CORNER`, a joint over a seam end
`JOINT_ON_SEAM_END` (stacked layers) or `JOINT_TOUCHES_SEAM_END` (edge to edge), a piece edge on a corner
`BAND_PIECE_EDGE_AT_CORNER`.

**Best arrangement.** The same pieces in another order (and, for a closed run, from another start in 10 mm steps) may
keep every joint farther from corners and seam ends. The layer searches all distinct orders and both directions
(capped at 5 040 orders and 200 000 placements per closed run, `ARRANGEMENT_SEARCH_LIMITED` if the cap is hit) and
reports the best minimum distances next to the planned ones. It never re-orders the plan itself and never changes a
quantity. The acceptable distance is product data: without it every joint is `JOINT_OFFSET_UNVERIFIED`.

## 5. Floor seams, multi-layer points and stagger

- **SIDE laps** between adjacent strips (merged over the along-interval for strips spliced end to end, one zone per strip
  pair) and **END laps** where a strip is spliced along its length.
- **Seam ends**: where a lap zone meets the boundary - a wall (under the band flange), a doorway (under the doorway
  piece's lap) or a break. Each is a point of three or four membrane layers. A seam that runs along a wall rather than
  across it is `FLOOR_SEAM_ALONG_A_WALL`.
- **End-lap stagger**: splices of neighbouring strips at the same along-position are `END_LAPS_NOT_STAGGERED` (a
  four-layer crossing).

## 6. Penetrations, drains and the lay order

- Every penetration (pipe sleeve, drain) is reported with its clearance (L-infinity) to the nearest floor seam, band
  flange and wall, and the largest centred square collar that stays clear (2 x clearance). Its treatment stays open.
- **A drain that is not drawn is NOT_SHOWN, never zero** (`DRAIN_NOT_SHOWN` when the area has no penetrations at all,
  `NO_DRAIN_DRAWN` when it has other penetrations but no drain; the drain count is `None` in both).
- **Lay order**: with exactly one drain the floor strips are laid from the strip holding the drain outwards, so each
  side lap has the sheet farther from the drain on top (sheds towards the drain). A drain inside a lap zone is
  `DRAIN_ON_A_FLOOR_SEAM`. With no drain or several drains the falls are not known: `LAY_ORDER_NOT_VALIDATED`. The plan
  gives no falls, so `falls.state` is `NOT_SHOWN`.

## 7. The floor-to-wall junction (N-11 / P-1)

State `UNRESOLVED` unless the project sets a detail. Alternatives, each with its own full cutting plan (rebuilt by the
independent reference calculator in the tests):

| owner's name | engine method | what is computed |
|---|---|---|
| Alternative A - continuous fold | `CONTINUOUS_FOLD` | the floor sheet folded up the walls (no band, no connection lap); developed rectangle (L + 2h) x (W + 2h) with corner squares; doorway depth = h. Computed for axis-parallel rectangles with walls and doorways only; otherwise `CONTINUOUS_FOLD_NOT_COMPUTED` with the reason |
| Alternative B - separate upturn | `SEPARATE_UPSTAND` | the band with its own connection lap (the flange) onto the floor sheet, set apart from the side and end laps: at the plan's flange (0.10 m, as V2.5 assumes), the widest flange (1 cm steps up to the upturn height) with the plan's roll count, and the first flange that adds a roll |

`JUNCTION_CHANGES_ROLL_COUNT` when the alternatives need different numbers of rolls. While the junction is open the
material state is `PROVISIONAL_DETAILS_OPEN` (reason `FLOOR_WALL_JUNCTION_UNRESOLVED (N-11 / P-1)`).

## 8. Separate systems

Areas of different membrane systems (wet-area, exterior) never share a roll and are never totalled together. Within
one system only full-width cuts are shared (a roll remainder cut to a piece's length); band lanes, trims and offcuts
stay with their area. Each shared cut keeps its area's id (`{room}:R{roll}-{k}`).

## 9. Not implemented (stated, not hidden)

| item | status |
|---|---|
| offcut reuse across areas (C-5) | not implemented: reusable offcuts are classed, never re-used |
| UP-WP-LAY-001 applied to the band plan (C-6) | not implemented: the owner defines the rule's scope (N-9) |
| shaped trims at splayed walls | area only, flagged; no polygon decomposition |
| falls and slopes | not on the plan: NOT_SHOWN |
| product values (joint offset, minimum reusable size, corner and penetration details) | not assumed: distances reported, never judged |
| wall waterproofing above the upturn (showers) | out of this layer's scope |

# Finish eligibility and surface reasoning (WP-4; deliverable 8 - wet-area and skirting validation)

ARCH_TAKEOFF_V2.3, `engine/source/owner_finish_scope.py`, rules UP-WET-001, UP-FIN-WALL-001, UP-FIN-PAINT-001,
UP-FIN-PLASTER-001, UP-SKIRT-001, UP-THR-001, UP-WP-ROOF-001, UP-CEIL-001.

## 1. Rules applied

| Surface | Rule | V2.3 treatment | State |
|---|---|---|---|
| Wet-area scope | UP-WET-001 | bathrooms, kitchens, pantries and ironing rooms are wet areas (a laundry too, flagged WET_SCOPE_PROJECT_CONFIRMATION); an open plan of a wet and a dry function keeps the dry treatment (OPEN_PLAN_WET_SCOPE_EXTENT, a B request for the zone line) | - |
| Wall porcelain | UP-FIN-WALL-001 | full height = the room's own clear (finished-ceiling) height, the same height ladder as paint - never a constant; an explicit source / project wall-tile height governs and is flagged when lower (C, precedence) | SOURCE_DERIVED when the height is established, BLOCKED otherwise |
| Paint | UP-FIN-PAINT-001 | none over full-height porcelain: the band is NOT_APPLICABLE_WITH_EVIDENCE (no question); with an explicit lower tile the band joins the tile-height conflict group | - |
| Plaster | UP-FIN-PLASTER-001 / UP-CER-009 | wall plaster as before; door jambs and head: 2 x wall thickness x door height + wall thickness x opening width | jambs PROVISIONAL (FRAME_ALIGNMENT_PLASTER) |
| Skirting | UP-SKIRT-001 / UP-CER-004 | dry rooms keep their measured skirting; a wet room whose tile runs full height has none (NOT_APPLICABLE_WITH_EVIDENCE); a wet room with an explicit lower tile keeps it (UP-CER-004 exception); the two jambs of a doorless opening between two dry rooms are skirted | room skirting as measured; passage jambs PROVISIONAL |
| Doorway strip | UP-THR-001 | a door next to a wet room: marble threshold (strip face = opening width x wall thickness); any other doorway: the floor porcelain continues through it, counted once; one line per opening (all its strip faces) | SOURCE_DERIVED; a pantry doorway PROVISIONAL (CF-03 / OQ-01); an external doorway or a doorless opening into a wet room PROVISIONAL |
| Waterproofing | UP-WET-001, UP-WP-001..003, UP-WP-ROOF-001 | every wet room: floor, upturn 0.20 m, doorway; balconies / roofs drawn as spaces: floor waterproofing over the drawn area; roof upturn 0.20 m on the perimeter; balcony upturn by specification (B) | wet rooms as V2.2; exterior PROVISIONAL |
| Ceilings | UP-CEIL-001 | actual eligible surfaces only (as V2.2: double height counted once, stair-well ceiling blocked until the section) | unchanged |

Overlap avoided: one finish per wall face (tile or paint, never both); the doorway strip is in no room floor, so the
marble threshold and the floor porcelain cannot both count it; skirting is never measured on a full-height tiled face;
substrate (plaster) and finish (tile / paint) remain separate lines of the same face.

## 2. Validation on the synthetic villa (hand truth from the coordinates)

| Check | Truth | V2.2 | V2.3 | Test |
|---|---|---|---|---|
| kitchen is wet: waterproofing floor | 2.8 x 6.4 = 17.92 m2 | none | 17.92 SOURCE_DERIVED | `test_kitchen_pantry_and_ironing_rooms_take_the_wet_scope` |
| kitchen waterproofing upturn | 2 x (2.8 + 6.4) x 0.20 = 3.68 m2 | none | 3.68 | same |
| kitchen skirting | none (full-height tile) | 17.50 lm released | NOT_APPLICABLE_WITH_EVIDENCE | same |
| wall tile height, no tile height given (heights 3.0 m) | 3.0 m (clear height) | bathroom tile BLOCKED, skirting BLOCKED, band question | 3.0 m; skirting and band NOT_APPLICABLE | `test_wall_porcelain_runs_full_height_and_no_paint_band_is_asked` |
| explicit project tile height 2.4 m | 2.4 m governs, flagged | 2.4 m | 2.4 m + WALL_TILE_BELOW_OWNER_FULL_HEIGHT (C, 3 rooms) | `test_an_explicit_lower_tile_height_wins_and_is_flagged` |
| marble thresholds | 0.80 x 0.2, 0.90 x 0.2, 0.80 x 0.2 = 0.16 + 0.18 + 0.16 m2 | none (strips BLOCKED) | 0.50 m2 in 3 lines | `test_wet_doorways_take_a_marble_threshold_from_geometry` |
| dry doorway strips | 0.18, 0.18, 0.20 (passage) and 0.20 (entrance, PROVISIONAL) | BLOCKED | the same, each strip in one line | `test_dry_doorways_continue_the_floor_porcelain_once` |
| door jamb plaster | 2 x 0.2 x 2.2 + 0.2 x w: 1.04 (0.80), 1.06 (0.90), 1.08 (1.00) | none | 6 PROVISIONAL lines (2.20 ASSUMED; 2.10 SOURCE with heights) | `test_door_jamb_plaster_is_measured_and_provisional` |
| dry rooms keep skirting | unchanged | as measured | identical | `test_a_dry_room_keeps_its_skirting` |
| living room next to the kitchen | dry | dry | dry (no wet spread) | `test_wet_scope_never_spreads_to_an_open_plan_dry_space` |
| passage jambs (two dry rooms, 1.20 m gap, wall 0.20 m) | 2 x 0.20 = 0.40 lm | none | 0.40 PROVISIONAL; room skirting unchanged | `test_passage_jambs_are_skirted_provisionally` |
| balcony | waterproofing over 2.0 x 4.0 = 8.0 m2 | none | 8.0 PROVISIONAL; upturn a specification request | `test_a_balcony_door_is_aluminium_and_the_balcony_is_waterproofed` |

## 3. Reference plan (aggregate)

| Item | V2.2 released | V2.3 released | Why |
|---|---|---|---|
| FIN.SKIRTING (lm), no heights | 197.517 | 185.517 | wet-scope rooms with full-height tile carry no skirting |
| FIN.WP.FLOOR (m2) | 53.143 | 62.773 | kitchen / pantry wet scope |
| FIN.WP.UPTURN (m2) | 26.045 | 28.945 | same |
| FIN.WP.DOORWAY (m2) | 1.835 | 2.035 | same |
| FIN.MARBLE.THRESHOLD (m2) | - | 0.74 | doorway strips of wet rooms |
| FIN.FLOOR.PORCELAIN (m2) | 167.189 | 170.998 | dry doorway strips counted once (not in any room floor before) |
| FIN.WALL.TILE (m2), heights given | 161.911 | 192.361 | kitchen / pantry wall tile |
| FIN.PAINT (m2), heights given | 269.484 | 230.334 | no paint where porcelain now runs |
| FIN.PLASTER door jambs (m2, PROVISIONAL) | - | 19.32 (no heights) / 18.60 (heights) | new line family |

Every other released item is unchanged. No released quantity is negative; the ledger conserves every line
(each line in exactly one record) and finds no confirmed omission (CONFIRMED_MISSING 0) in all runs.

## 4. Acceptance (WP-4)

"Every measured or withheld surface has a governing rule and a documented reason" - checked on every V2.3 run: every
surface-ledger record carries an authority (a rule id, or `PROPOSAL` for a V0.1 eligibility row) or an exclusion rule
text; every withheld record names its blocker or conditions, or its lines carry the RFI question / notes. Tracked
blocked surfaces: BLOCKED_MISSING_SOURCE (heights, sections, schedules), BLOCKED_OWNER_DECISION (named open
decisions), UNRESOLVED_ELIGIBILITY (proposal rows / open questions, never added to a missing quantity),
NOT_APPLICABLE (with the rule that makes it so).

## 5. Limitations

- Full-height tiling applies to every face of a wet room; a partially untiled feature wall is overstated unless an
  explicit per-face height is given (facts heights are per floor and trade, not per face).
- An open-plan kitchen stays dry until its zone is drawn (a B request): its wet scope is under-measured meanwhile.
- The kitchen / pantry floor stays floor porcelain (the wet floor row accepts it); a different wet-floor specification
  is a document request.
- A doorway strip at a door with no band opening (a provisional door) stays a BLOCKED strip line and asks for the
  door (B), although its finish is known.

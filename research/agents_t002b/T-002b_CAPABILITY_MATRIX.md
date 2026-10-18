# T-002b Capability matrix from code (HEAD 39c9dea)

Docs only. No engine, rule or test file changed. Every claim cites file:line on `claude/access-permissions-setup-ii24ws`
at 39c9dea. "Registry" = the BOQ family master `rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json` (the only family registry;
its own `source` field says it is a read-only audit of 8177ccf, i.e. it predates ARCH_TAKEOFF V2.2-V2.9). "Census" =
`engine/source/coverage_census.py`, which reports each family's run state from the lines a run produced, using the
registry for families with no line.

Architectural lines come from `tools/urban_boq_m9.py` with `--method` (required, no default:
`tools/urban_boq_m9.py:3001`; methods V1 .. V2.9 at `:66-68`), measured room by room in
`engine/source/arch_measure.py:measure` (`:244`). Structural lines come from route G (`tools/urban_boq_m2.py:100`
`route_generic` -> `engine/source/generic_route.py:480 items_from`), mapped to item codes by
`engine/source/boq_line.py:325 _route_g_code` / `:337 from_route_g`.

## Matrix

| Trade | Registry family : capability (line) | Item code (boq_line.py) | Method that measures it on HEAD | Release behaviour in code | N10 completeness claim |
|---|---|---|---|---|---|
| Concrete | B10-01..08 blinding, footing, neck, strap/GB, ground slab, column, beam, slab: INTEGRATED_AND_TESTED except B10-03, B10-05 PARTIAL (:790-868); B10-09..12 PARTIAL (:879-912) | `STR.CONC.*` :47-64 | route G: footings `generic_route.py:509`, columns `:689` / necks `:1295`, ground beams `:769`, beams `:856`, slabs `:1095-1214`, blinding `:1448`, stairs `:1995`, lintels `:2061` | VERIFIED -> MEASURED, PROVISIONAL -> PROVISIONAL / SOURCE_DERIVED, UNRESOLVED -> BOUNDED_EXPOSURE or BLOCKED_RFI (`boq_line.py:337-345`); route family census mapped by `coverage_census.py:46-51` | PARTIAL ("as earlier stages") |
| Rebar | B11-01 bars PARTIAL (:933); B11-02 BBS PARTIAL (:944); B11-03 stairs/pool/domes/... BLOCKED_BY_SOURCE (:955); B11-04 net vs procurement IMPLEMENTED_NOT_INTEGRATED (:966) | `STR.REBAR` :65 | route G bar models per element from detected geometry + conventions / details: footings `generic_route.py:1838`, columns `:733-750`, necks `:1345-1363`, ground beams `:1779`, continuous beams `:2209`, beams `:2251`, slabs `:2297`, lintels `:2086` | PROVISIONAL items (`P-S:` ids); unresolved bars `U-S:` -> BLOCKED / BOUNDED; scope families with concrete but no bar model -> BLOCKED "MISSING_DATA, no kg/m3 ratio" (`coverage_census.py:96-103`); no structural schedule / bar-mark reader exists (T-009) | rebar mass method SUPPORTED (audited, 0 ratio-as-measured) |
| Blockwork | B9-01 block walls by type and thickness: EXPERIMENTAL, impl "qs_core.masonry (research)" (:735-736); B9-02 lintels INTEGRATED_AND_TESTED (:746); B9-05 parapet PARTIAL (:779) | `ARCH.WALL_RUN` :102, `MAS.BLOCK` :103; V2.9 adds `ARCH.WALL_PANEL`, `ARCH.WALL_VOLUME` (`urban_boq_m9.py:996-998`, not in `boq_line.ITEMS`) | wall run lm by thickness `arch_measure.py:789 _wall_lines` (PROVISIONAL, `:800`); MAS.BLOCK always BLOCKED_RFI there (`:811`); V2.9 masonry panel m2 / m3 from evidenced T.O.S. -> soffit `urban_boq_m9.py:1031 _v29_masonry` (via `engine/source/arch_v29.py masonry_takeoff`), MAS.BLOCK released only with a stated material (`urban_boq_m9.py:581`) | panel: measured / range / held with RFI (`urban_boq_m9.py:1051-1085`); on Alsenan HELD (no section levels bound to floors, T-013) | panel PARTIAL (was UNSUPPORTED), MAS.BLOCK HELD |
| Plaster (internal) | B4-03: IMPLEMENTED_NOT_INTEGRATED (:251) | `FIN.PLASTER` :84 | `arch_measure.py:639-681` per room, net from the room's own boundary `:195 _wall_finish_rs` (F-24, UP-CER-009); V2.8 heights / bands | BLOCKED_RFI when height not established (`:643-650`), range when a deduction is unknown (`:217-231`), REVIEW when the boundary does not add up (`:206-214`) | SUPPORTED where heights are evidenced |
| Plaster / paint (external) | B4-04, B4-07: EXPERIMENTAL (:262, :295) | `FIN.EXT.FINISH` (`urban_boq_m9.py:1004`) | V2.9 facade outline and area (`urban_boq_m9.py:585`, UP-FACADE-001) | finish always held without a stated specification (`urban_boq_m9.py:987-991` D-V29-04, held line `:1202-1213`) | exterior finish HELD |
| Paint (internal) | B4-06: IMPLEMENTED_NOT_INTEGRATED (:284) | `FIN.PAINT` :85 | same loop as plaster `arch_measure.py:639`; in wet rooms paint only above the tile (`surface_ledger.py:155`) | as plaster | SUPPORTED where heights are evidenced |
| Floor area | B2-02 room clear floor area: IMPLEMENTED_NOT_INTEGRATED (:108); B2-03 gross per floor: EXPERIMENTAL (:119) | `ARCH.SPACE` :93 (space with no finish), floor finish lines carry the area | face area (TS01) minus stair treads, voids, flights seen below `arch_measure.py:381-384`; spaces without one finish kind -> ARCH.SPACE `:325`, `:344` | released per room; attached unlabelled cells flagged `:377-379` | room floor areas SUPPORTED |
| Wet vs dry | no family (classification, not a BOQ line) | - | room-name lexicon `arch_rooms.py:71 LEXICON` -> kind; `arch_measure.py:47 FINISH_KIND`, `:102 _kind` (mixed kinds -> not measured); owner scope review `owner_finish_scope.py:27, :38` (WET_CLASSIFICATION_REVIEW, WC_CANDIDATE_REVIEW) | a space whose kinds disagree gets no finish (`_kind` returns None); WC-symbol confusion still open (L-P8-01 strict xfail, T-010); hand-wash spaces open (Q-06) | (not a row) |
| Waterproofing (wet rooms) | B8-01 floor, B8-02 doorway, B8-03 upturn: IMPLEMENTED_NOT_INTEGRATED (:636, :647, :658; B8-03 impl "7 conflicting implementations (C01)"); B8-04 shower NOT_IMPLEMENTED (:669); B8-05 rolls NOT_IMPLEMENTED (:680) | `FIN.WP.FLOOR` :70, `FIN.WP.DOORWAY` :71, `FIN.WP.UPTURN` :72, V2.5+ `FIN.WP.*` :75-82 | `arch_measure.py:558-620` (floor, doorway pieces, 0.20 m upturn UP-WP-003); `waterproofing_system.py` (V2.5 / V2.6); roll plan `membrane_layout.py:89` | doorway / upturn PROVISIONAL or RFI where the detail is not established (`:566-575`, `:615-620`); B8-05 QUANTIFIED from material results (`coverage_census.py:104-110`) | SUPPORTED (junction details D-17 open) |
| Waterproofing (roof) | B8-06: IMPLEMENTED_NOT_INTEGRATED (:691) | `FIN.WP.FLOOR` on EXTERIOR spaces (`surface_ledger.py:127-128`) | no roof-plan reader; ARCH.EXTERIOR areas only (`arch_measure.py:323`) | not measured as roof WP | roofs UNSUPPORTED |
| Tiles | B3-01 dry floor, B3-02 wet floor, B4-01 wet wall: IMPLEMENTED_NOT_INTEGRATED (:152, :163, :229); B4-02 kitchen / laundry tiled zones NOT_IMPLEMENTED (:240) | `FIN.FLOOR.PORCELAIN` :66, `FIN.FLOOR.WET_TILE` :67, `FIN.WALL.TILE` :68 | floor `arch_measure.py:381`; wall tile in the plaster / paint loop `:639` (wet rooms only, owner full height `owner_finish_scope.wall_tile_height`); tile layout / waste `tile_layout` (procurement) | as plaster for walls; floor released per room | wall tile SUPPORTED with evidence; floor via room areas |
| Doors | B6-01 opening census PARTIAL (:405); B6-02 internal doors NOT_IMPLEMENTED (:416); B6-03 main / external NOT_IMPLEMENTED (:427) | `ARCH.DOOR` :95, `ARCH.PASSAGE` :97, `DOOR.INTERNAL.PVC` :108, `DOOR.EXTERNAL.ALUMINIUM` :109, `DOOR.MAIN_ENTRANCE` :110 | one pcs line per jambed opening `arch_measure.py:697-755`; V2.1+ door classes from swings `door_model.py:590 floor_model`, `:449 classify`, released classes `:56`, lines `urban_boq_m9.py:2440 _v21_doors`; owner minimum width `door_standards.py:56 required_opening` (UP-DOOR-OPEN-002) | count released; height / area held without a schedule (`arch_measure.py:738-744`) | SUPPORTED (D-16 -> T-011) |
| Windows | B6-01 PARTIAL (:405); B6-04 windows / aluminium / glazing NOT_IMPLEMENTED (:438) | `ARCH.WINDOW` :96, `ARCH.WINDOW_REVEAL` :106 | count + width `arch_measure.py:698`; V2.8 schedule height / sill / class `:720-728`, `:738-753` (`schedule_reader.py`); V2.9 curved openings `arch_v29.py` | count released; area held where height not established (`:741-744`); reveals BLOCKED_RFI | count / width SUPPORTED (26 -> 27), reveals PARTIAL |

## Disagreements

Registry vs code (the registry is the 8177ccf audit and was never re-versioned):

1. B3-01, B3-02, B4-01, B4-03, B4-06, B8-01, B8-02, B8-03 are `IMPLEMENTED_NOT_INTEGRATED` ("research", "room_slice
   (tests)"), but the M9 architectural route emits released lines for all of them (`arch_measure.py:381`, `:637-681`,
   `:558-622`) and the census counts them as ARCH_FAMILIES (`coverage_census.py:44-46`). Integrated in the arch route,
   at least PARTIAL by the registry's own vocabulary.
2. B6-02, B6-03 doors are `NOT_IMPLEMENTED` but `DOOR.INTERNAL.PVC`, `DOOR.EXTERNAL.ALUMINIUM`, `DOOR.MAIN_ENTRANCE`
   are released by V2.1+ (`door_model.py:56`, `urban_boq_m9.py:2440`). B6-04 windows is `NOT_IMPLEMENTED` but window
   count lines exist (`arch_measure.py:698`). **Census defect:** `FAMILY_ITEMS` maps all of these codes to B6-01
   only (`coverage_census.py:35-36`), so a run that releases door classes still reports B6-02 / B6-03 / B6-04 as
   NOT_IMPLEMENTED (`:118-119`).
3. B9-01 blockwork is `EXPERIMENTAL` with impl "qs_core.masonry (research)"; HEAD measures the panel by thickness in
   V2.9 (`urban_boq_m9.py:1031`). **Census gap:** B9-01 maps only to `MAS.BLOCK` (`coverage_census.py:39`), so a
   measured ARCH.WALL_PANEL / ARCH.WALL_VOLUME never shows as B9-01 QUANTIFIED; the V2.9 item codes are also absent
   from `boq_line.ITEMS` (kept in `urban_boq_m9.py:996`).
4. B2-02 room floor area is `IMPLEMENTED_NOT_INTEGRATED` and has no `FAMILY_ITEMS` entry, so it is always NOT_RUN in a
   census although every room's area is released on its floor-finish line. Same for B2-03.
5. B8-03 impl text "7 conflicting implementations (C01)": the M9 route uses one (`arch_measure.py:615`, UP-WP-003,
   0.20 m); whether the other six still exist was not re-audited here (uncertain).

Registry vs N10 completeness matrix (`research/urban_m9_n10/COMPLETENESS_MATRIX.md`):

6. Structural concrete: registry INTEGRATED_AND_TESTED for B10-01/02/04/06/07/08; N10 says PARTIAL. Code (route G)
   is unchanged by N10; the N10 row is the more conservative reading.
7. Plaster / paint / tiles / waterproofing / doors / windows: N10 says SUPPORTED (with conditions); registry says
   IMPLEMENTED_NOT_INTEGRATED or NOT_IMPLEMENTED (items 1-2 above). Code agrees with N10 that lines are produced;
   "SUPPORTED" is a document claim, not an independent check (CLAUDE.md "Never break").

Master study `03_CAPABILITY_MATRIX`:

8. The study's matrix is not in this repository or in `agents/control`, so only the claim quoted on the board was
   compared: blockwork "UNSUPPORTED" there vs HEAD's V2.9 panel by thickness (PARTIAL: measured with evidence, HELD on
   Alsenan). The rest of the study comparison needs the study file (verifier / lead to supply its path).

## Proposed tasks (for the lead)

- Family master 1.1.0 (new version file; 1.0.0 untouched) re-audited from this matrix (items 1-4), with the census
  map extended: B6-02 / B6-03 -> door classes, B6-04 -> `ARCH.WINDOW`, B9-01 -> `ARCH.WALL_PANEL` / `ARCH.WALL_VOLUME`,
  B2-02 -> floor-finish area. Census behaviour changes, so it is a new census version with a fixture.
- Audit the B8-03 "7 conflicting implementations" claim (item 5).

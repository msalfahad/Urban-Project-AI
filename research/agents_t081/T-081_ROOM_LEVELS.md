# T-081: room floor levels from the marks printed inside each room, finish heights from printed values only

Gate 1 (storeys and levels; feeds plaster and paint heights). Two new read-only pieces, not wired into any method
version, so no released quantity moves.

## 1. What was wrong

The released route takes a plan's floor level from `arch_rooms.dominant_level`: the most frequent level text in the
whole plan frame. On the development villa's ground-floor plan (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip,
P7757.dxf, plan frame SH05) six `%%p0.00` plot-corner marks outnumber the rooms' own marks, so the engine sets GF = 0.00
while the rooms print +1.00 (the dining / living / reception / pantry open room) and +0.30 (majlis, kitchen, driver
room). Floor-to-next from that level is 5.50 - 0.00 = 5.50 m instead of the printed 4.50 m (NW elevation dimension
4500, +1.00 to +5.50).

Finish heights V1 (`finish_height.py:31`) subtract a 0.150 m ceiling allowance, and method register V3 offers a 0.10 m
floor build-up fallback. Owner Q-14 refuses both ("do not subtract an assumed floor build-up or false-ceiling depth").

## 2. What was built

* `engine/source/room_levels.py` (ROOM_LEVELS_V1): each room's level from the F.F.L. / bare level mark printed inside
  its outline (outside its holes; nested outlines: the smallest). A room with one value: PRINTED. A stair with two
  values: HELD STAIR_LINKS_LEVELS. Any other room with two values: HELD TWO_LEVELS_IN_ROOM. No value: HELD
  UNLEVELLED_ROOM (never the storey's or another zone's level). Marks in no room outline are OUTSIDE_ROOM_MARK; marks
  in exterior / void / shaft / unidentified spaces are non-room levels; neither is ever a floor level. Ceiling, soffit,
  slab-top and parapet levels inside a room are kept apart. Storey zones = the distinct PRINTED room levels
  (SINGLE_LEVEL / SPLIT_LEVEL / NOT_PRINTED); finding PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL when the old plan level
  disagrees. `zone_of()` binds a PRINTED room to its section-binding zone (T-013 report), else HELD.
* `engine/source/finish_height_v2.py` (ARCHITECTURAL_FINISH_HEIGHT_V2): plaster to the structural soffit, paint to the
  finished ceiling, wall tile (wet rooms), by the UP-HGT-001 order: room annotation (rank 1), printed section values
  (rank 3), derivation floor-to-floor - build-up above - slab / beam D (rank 4) only when the build-up above is printed
  or a project fact with authority and source. Slab 0.16 m by owner rule Q-14 when not printed. The 0.150 allowance and
  the 0.10 fallback are refused inputs (recorded, never used). Paint with no printed ceiling level: HELD
  CEILING_LEVEL_NOT_PRINTED. The wall band above a printed false ceiling: plaster yes (Q-14), paint HELD (no rule).
  Plaster above floor-to-floor or paint above plaster: flagged, never clipped.

## 3. Development villa, by the new pieces (P7757.dxf, ARCH_TAKEOFF_V2.9 rooms, section binding V1)

| Storey | Printed room levels | Rooms PRINTED / HELD (no mark) / stair | Zones | Floor-to-next | Old plan level |
|---|---|---|---|---|---|
| GF | +1.00 open room; +0.30 majlis, kitchen, driver | 4 / 8 (6 bathrooms, master bedroom, one open-room part) / 1 stair (+0.30 and +1.00) | SPLIT +0.30, +1.00 | +1.00 zone 4.50 m PRINTED_DIMENSION; +0.30 zone HELD (split, its roof +4.30 is not a floor) | 0.00 (6 plot marks): finding |
| 1F | +5.50 living | 1 / 10 | SINGLE +5.50 | 4.20 m DERIVED (+9.70 - +5.50) | 5.50 (agrees) |
| 2F | +9.70 stair | 1 / 2 (maid, bathroom) | SINGLE +9.70 | HELD (level above +13.90, kind not printed) | 9.70 (agrees) |

Outside-room marks: GF six `%%p0.00` and five +0.15 (court / paving); 1F three +5.50 (terraces) and +4.30 (annex roof);
2F two +9.70 (roofs). Non-room level: GF one +0.15 inside an unlabelled space. All agree with the hand census of the
architectural PDF sheets (T-063: GF +1.00 / annex +0.30, 4.50 / 4.20 / 4.20 / annex 4.00). The DXF and the PDF are the
same revision (T-063 C-4); every level mark in the three plan frames is plain text (none in SHX), so none is unread.

Finish heights on the same run: every room HELD. 21 rooms by ROOM_LEVEL_HELD (no level printed inside them); the 6
levelled rooms by SOFFIT_NOT_PRINTED (no U/S SLAB, next T.O.S. or floor build-up printed; FLOOR_BUILDUP_ABOVE_NOT_PRINTED)
for plaster and CEILING_LEVEL_NOT_PRINTED for paint. Engine vs freelancer: internal plaster HELD vs 1 151.14 m2, internal
paint HELD vs 1 191.13 m2 (unchanged, never 0). For the record only (not used): the freelancer's masonry sheet uses wall
heights 4.00 / 3.50 m on GF and 3.70 / 3.45 m above; none of these is printed on the drawings read.

## 4. Open

* Most rooms print no level of their own (GF 8 of 13 rooms, 1F 10 of 11, 2F 2 of 3). Whether such a room may take the
  storey's single printed level, or the zone of the room it opens into, is an owner rule (question Q-43). Until then
  they stay HELD.
* Paint on the wall band above a false ceiling: no rule (owner Q-14 note); held when it arises (not on this villa).
* Wiring into a released method version (plaster / paint lines) is a later task; it needs a printed soffit or build-up,
  or an owner rule, before any height becomes a number on this villa.

## 5. Rework (worker 3, 2026-10-19 23:10-00:30 UTC): owner answers Q-43 and Q-48 applied

What changed (all additive; V1 room levels and the earlier finish-height results are unchanged when the new inputs are
not given):

* `engine/source/room_levels.py` ROOM_LEVELS_V2 (`room_levels_v2`, `doorway_reading`, `zone_of_v2`): a room with no
  printed level takes the floor's level on a one-level floor (FLOOR_LEVEL, owner Q-43); on a split floor only from
  what is drawn: a section / step reading with its source (DRAWN) or the levelled room it opens into through a doorway
  where nothing is drawn across the opening besides the door symbol (OPENS_INTO, every hop recorded). Held otherwise:
  DOORWAY_LINES_DRAWN (a line across a doorway may be a step; never read as one), DOORWAY_NOT_READ,
  OPENS_INTO_TWO_LEVELS, NO_OPENING_TO_A_LEVELLED_ROOM, DRAWN_LEVELS_DISAGREE; an unmarked stair stays held.
* Registry `knowledge/URBAN_ENGINEERING_KNOWLEDGE_1.8.0.json` (builder `tools/kb_build_1_8.py`, built on 1.5.0 like
  1.7.0): UP-HGT-001 carries the owner wall height (floor-to-floor - 0.60 beam - 0.15 decor ceiling - 0.10 floor
  finishing; printed values first; beam hold) and the Q-43 room-level steps; UP-FIN-WALL-001 the Q-48 A wet-wall tile
  height. Not yet listed in `engine/source/knowledge.py` (claimed T-079 owns that file).
* `engine/source/finish_height_v2.py`: opt-in `owner_rule=owner_wall_rule()` (values read from the 1.8.0 file, a typed
  dict is refused) as rank 5 under every printed candidate; HELD FLOOR_TO_FLOOR_NOT_ESTABLISHED / BEAM_DEPTH_NOT_0_60
  / BEAM_NOT_DRAWN_OVER_ROOM / BEAM_OVER_ROOM_NOT_CHECKED with the rule value kept as `owner_rule_height_m`
  (diagnostic); wet rooms: wall tiles = the owner height unless a tile height is printed. The V1 0.150 allowance and
  the 0.10 fallback stay refused inputs.

Development villa (Drive P7757.dxf, V2.9 rooms, `research/agents_t081/alsenan_t081_run.py`; per room in
`ALSENAN_ROOM_HEIGHTS_T081.csv`):

| Floor | Rooms | Level printed / by rule / held | Floor-to-floor (slab to slab) | Owner wall height (diagnostic) |
|---|---|---|---|---|
| GF +1.00 | open dining room, its 2.8 m2 part, master bedroom | 1 / 2 OPENS_INTO (door OP-012, passage OP-003: nothing drawn across) / - | 4.50 PRINTED_DIMENSION | 3.65 m |
| GF +0.30 | majlis, kitchen, driver room, the driver's bathroom | 3 / 1 OPENS_INTO (door OP-026) / - | HELD: split zone, no printed dimension (the +4.30 annex roof is not read as a slab) | not given |
| GF | stair, 5 bathrooms | - / - / 6 (stair links +0.30 / +1.00; 2 bathrooms open only into an unidentified lobby, 3 have no opening in V2.9) | - | not given |
| 1F +5.50 | 11 rooms | 1 / 10 FLOOR_LEVEL / 0 | 4.20 DERIVED_FROM_PRINTED_LEVELS | 3.35 m |
| 2F +9.70 | 3 rooms | 1 / 2 FLOOR_LEVEL / 0 | 4.20 PROJECT_FACT (owner Q-43: +13.90 is the final floor) | 3.35 m |

Room levels: 21 of 27 rooms are levelled now (6 printed, 12 FLOOR_LEVEL, 3 OPENS_INTO) where V1 levelled 6; 6 stay held
with their reason. Every owner height is still HELD (BEAM_OVER_ROOM_NOT_CHECKED): the beams over the rooms are not read
in this run, and worker 2's hand reading (Q-52, T-088) found no 0.60 m beam on the Alsenan slab plans, so the beam rule
waits on the owner. Diagnostic only, gross (no door or window deducted, the 16 m2 double-height void over the GF open
room not added): the 17 rooms with a diagnostic height give 373.88 m of V2.9 wall run on the three floors (GF 152.89 of
it) and 944.40 m2 of wall (plaster basis: dry 726.02 + wet 218.38), against the freelancer's plaster 1 151.14 m2 and
paint 1 191.13 m2 for the whole villa. Not comparable as a score (10 rooms held, no deductions): plaster and paint stay
HELD, never 0.

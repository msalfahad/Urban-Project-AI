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

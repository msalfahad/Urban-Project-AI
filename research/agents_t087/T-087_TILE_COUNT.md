# T-087: tiles to buy per room with the owner's joint widths (TILE_COUNT_V1)

Worker 1, 2026-10-20. Gate 2 (architectural coverage: tiles). Development villa Alsenan; not an accuracy claim.

## What the engine now gives

| Item | Engine | Freelancer | Status |
|---|---|---|---|
| Floor tile m2 (dry 10 rooms / wet 17 areas) | 194.98 / 72.12 m2 (unchanged) | 189.61 / 72.01 m2 | unchanged by this task: the m2 line stays m2 + the size waste rule (owner Q-42) |
| Tile COUNT per room | HELD on all 25 V2.9 floor-line rooms: TILE_SIZE_NOT_GIVEN | not given (he buys by m2) | held, never 0 |
| Printed tile sizes (census) | 0 tile-size notes and 0 joint notes in 276 DXF texts (121 Arabic SHX decoded); sheets 03 / 04 (GF, 1F plans) show none | - | stated result: the size must come from the owner or a project data file |

New piece `engine/source/tile_count.py` (not wired into any method; no released quantity changes):
- joint by owner Q-42: 1 mm inside, 2 mm on roofs / outside; a printed joint replaces it; inside / outside must be stated
  (never guessed from a room name) else HELD;
- tile size only printed > project data > owner value, else HELD TILE_SIZE_NOT_GIVEN;
- every room laid in 8 layouts (2 directions x 4 start corners, each corner also in drawing coordinates) with whole tiles,
  cut pieces and tiles to buy per layout; the record shows the range per direction and the fewest-tiles layout
  (UP-CER-010 layout comparison); nothing chosen silently;
- offcut reuse inside the room is an owner input (None = not answered -> tiles to buy HELD, the no-reuse upper bound and
  every layout still shown; False = no reuse; a number = smallest reusable offcut side);
- roofs / outside: the 3 mm expansion joints are recorded HELD (spacing and BOQ line not answered);
- census / parser of printed sizes in English and Arabic (Arabic-Indic digits, x / × / *, mm / cm / سم / مم); a unitless
  size is read only when it is an owner-approved size (60x60, 120x60, 160x80) and is flagged; column / door sizes
  ("C1 60x60", "DOOR 90x210") are listed as SIZE_WITHOUT_TILE_WORD and never used.

## Hand fixtures (not Alsenan, tests/t087_tile_count, 20 tests pass)

| Case | Hand result | Engine |
|---|---|---|
| 3.00 x 2.40, 600x600, 1 mm | 4 + 0.596 by 3 + 0.597: 12 whole + 8 cut = 20 | 20 |
| same, roof 2 mm | 0.592 / 0.594 cuts, 20; expansion joints HELD | 20 |
| same, printed 0 mm | 20 whole, 0 cut | 20 |
| 3.005 x 2.40, 1 mm vs 0 mm | 15 + 5 = 20 vs 20 + 4 (0.005 sliver) = 24 | 20 / 24 (the joint moves the count 20 %) |
| 3.00 x 2.40, 1200x600 | 0 deg 6 + 6 = 12; 90 deg 4 + 6 = 10 | 12 / 10, fewest 10 |
| L room 5.043 m2, 600x600 | start corners 14 / 16 / 17 / 18 | same; start corner moves 4 tiles (29 %) |
| 3.30 x 2.40, reuse >= 0.20 m | 24 without reuse, 22 with (2 cuts from offcuts) | 24 / 22; not answered -> HELD with 24 |
| rotation 30 / -61 deg, mirror, mm, cm, hole | same counts | same |
| size / exposure / units / outline missing | HELD with reason, tiles None | HELD |

## Alsenan candidates (what the count would be once the owner gives a size; NOT BOQ values)

23 rooms whose outline equals their V2.9 floor line (206.91 m2); the GF reception / dining and 1F living are held here
because their floor lines deduct stair treads / a void that V2.9 gives as m2 only (no outline): 118.73 vs 126.93 and
44.87 vs 75.98 m2. Joint 1 mm (closed rooms inside the building). Per room in ALSENAN_TILE_COUNT.csv.

| Size | Fewest-tiles layouts, no reuse | Bought m2 over net | Worst layouts | With offcuts >= 0.20 m reused in the room |
|---|---|---|---|---|
| 60x60 | 697 tiles | +21.3 % | 723 (+25.8 %) | 611 tiles (+6.3 %) |
| 120x60 | 378 | +31.5 % | 428 (+48.9 %) | 317 (+10.3 %) |
| 160x80 | 218 | +34.9 % | 258 (+59.6 %) | 185 (+14.4 %) |

Hand check of one room: GF W.C. 1.50 x 1.30, 600x600, 1 mm: 2 + 0.298 by 2 + 0.098 = 4 whole + 5 cut = 9 tiles; reusing
offcuts >= 0.20: the second 0.298 x 0.600 and the second 0.600 x 0.098 and the corner come from offcuts -> 6 tiles. Engine
9 / 6. 120x60 at 0 deg: 1 + 0.299 by 2 + 0.098 = 2 whole + 4 cut = 6. Engine 6.

## What we learned

1. The joint changes the count only through the cut pattern (H4: 20 vs 24 tiles); on open floor it is under 1 %.
2. The decision that moves the tile purchase most is offcut reuse inside a room, not the joint: on Alsenan 60x60 the
   bought area is +21 % over net without reuse and +6 % with reuse; 160x80 +35 % vs +14 %. The reuse figures sit near the
   unconfirmed flat skill percentages (10 / 12 / 15 %) that UP-CER-010 forbids as a quantity. Owner question Q-59.
3. The start corner matters in L-shaped rooms (14 to 18 tiles); in a rectangle only the direction matters.
4. V2.9 deducts stair treads and voids as m2 without an outline, so a layout over those rooms needs the deduction
   polygons first (two Alsenan rooms, 72.8 m2 of floor line).

## Missing / uncertain

- Tile size per room (owner or project data file T-064): every count stays HELD until then.
- Offcut reuse (Q-59); expansion joint spacing / BOQ line (Q-42 remainder).
- Wet areas of the hand table with no V2.9 face (17 hand areas vs 13 V2.9 wet lines) and stair / void deduction outlines.
- Wall tiles: not laid here (wall heights held by Q-52).

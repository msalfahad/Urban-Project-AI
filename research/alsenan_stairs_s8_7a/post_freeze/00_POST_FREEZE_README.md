# S8.7A post-freeze comparison

This comparison ran after the freeze. The frozen S8.7A layer and the S8.7 package were verified before and after,
and neither was written. Classes: {"AUTHORITY": 4, "METHOD": 6, "METHOD + SCOPE": 1, "MISSED_OBJECT": 1, "NOT_COMPARABLE": 2, "NO_DIFFERENCE": 3, "NO_DIFFERENCE (count only)": 1}.

## V3b C-STAIR

V3b released no technical quantity. Its commercial provisional figure was 5.2312 m3, and
the post-freeze module reproduces it from V3b's own stated method as 5.2312 m3 (`02`). The
method:

- risers from ceil(H / 0.175);
- one continuous slope per storey;
- width 1.15 m and waist 0.16;
- W x W landings, two on GF -> 1F and one on 1F -> 2F.

| Run | V3b risers | Drawn risers | Owner A / B | V3b m3 | S8.7A whole stair m3 (sensitivity) |
|---|---|---|---|---|---|
| A1 | 26 (173.076923 mm) | GFRS 28, ARCH-GF 25 | 28 / 29 | 2.8088 | 2.559299 - 2.715461 |
| A2 | 24 (175 mm) | FFRS 24, ARCH-1F 27, ARCH-2F 24 | 27 / 26 | 2.4224 | 2.551458 - 2.604391 |

- **GF -> 1F:** V3b's 26 is drawn on no view and is neither owner scenario.
- **1F -> 2F:** V3b's 24 equals the structural 1F roof sheet only because 4.20 / 0.175 = 24. That sheet omits the
  three radial winder risers.
- **Total:** the V3b figure sits inside the S8.7A main-stair range, 5.110757 -
  5.319852 m3, but only through compensating errors:
  - a single slope instead of two flights and a winder turn;
  - 1.15 m width where the drawings give 1.20;
  - the half-turn as flat W x W quarters: two on GF -> 1F, where one quarter is drawn as winders, and one on
    1F -> 2F, where two quarters are drawn.
- **Scope:** V3b leaves out the light-well (round) stair, which is 2.956247 m3 in S8.7A.

## Other references

- **Riser finish:** with uniform finished risers the area is H x W for any count, so the confirmed scenario changes
  the nosing and tread lines but not the riser face area of the straight flights.
- **PRE-S8:** the stair rows carry the same V3b line. Their three missing items (waist, riser height, landing levels)
  are the S8.7A questions:
  - riser height is narrowed to a choice between drawn counts;
  - landing levels are scheduled per scenario;
  - the waist stays open.
- **S7 interface:** the S7 stair-side top extensions agree with S8.7A's record, 75 strip ends and 71.9 kg.
- **R5:** the register counts risers = lines + 1 and finds no radial line. On these plans the landing-edge lines are
  drawn risers, so R5 over-counts by one each run whose landing edge is drawn. It also misses the winder risers.

Nothing here or in S8.7A is released. The owner decides before any production BOQ change.

# T-109 Facade run: the walls of an open-air side passage (every villa; found on the development villa GF)

Worker 1, 2026-10-20. Gate 1 (geometry integrity, no silent omissions). New check piece
`engine/source/facade_passage_walls.py` (FACADE_PASSAGE_WALLS_V1), NOT wired: no released quantity moves. Rules:
UP-FACADE-001 (REQUIRES_CONFIRMATION; the facade is the exterior face of the wall network, openings included),
UP-WALL-GEOM-001 (a wall band is two drawn faces), UP-QTY-STATUS-001 (unsettled = HELD with both values, never 0),
owner Q-25 (no gap-size limit: nothing here is decided by a width). Owner Q-07 (facade height slab to slab) is not
touched: the piece works on the run in metres only; facade m2 stays HELD (heights, T-031).

## Result on the development villa (Mode A as T-014 / T-016a: S2 facts, layer roles 1 / D / W / S-COL.BON)

| Floor | Released run (V2.9 .. V2.12) | FACADE_PASSAGE_WALLS_V1 | Hand (T-016b, verifier re-read 13:25) | Verdict proposal |
|---|---|---|---|---|
| GF | 98.886694 m | 105.886694 m (+7.000 m, +7.08 %), RESOLVED | 105.887 m (before the Q-64 notch; 105.787 .. 105.887 m with it) | engine WRONG, the piece = hand (HAND_RIGHT stands) |
| 1F | 63.168865 m | 63.168865 m (NO_PASSAGE) | 63.008865 m (the T-014 recess, a separate piece) | unchanged here |
| 2F | 29.800000 m | 29.800000 m (NO_PASSAGE) | 29.800 m | unchanged |

Against the engine: -7.000 m on GF = -6.6 % of the hand run. ARCH.PASSAGE (nr): released 2 on GF (OP-007, OP-001); the
piece lists both as NOT_A_BUILDING_OPENING, hand 0. Freelancer: no facade-run row (his exterior plaster is m2 per
elevation, 1502.84 gross / 1469.97 net m2), so there is no m-for-m comparison; the run feeds facade m2 once Q-07
heights are wired.

How the +7.000 m is made up (every figure re-read from the drawing lines, not from the engine):
- removed: the mouth at the court (OP-007) 1.200 m and the boundary-wall end (OP-001) 1.200 m = 2.400 m;
- added: the annex east face from the court face line to the boundary wall's inner face 3.60 + door 1.00 + 0.10 =
  4.700 m, and the house west face 1.05 + window 1.50 + 1.05 + window 1.00 + 0.10 = 4.700 m = 9.400 m;
- kept: 0.200 m of OP-001's census width (1.40 m) lies over the end of the annex wall, whose south face line stops
  0.20 m short of its corner (a drafting gap closed by the wall's cap): it is that wall's outer face, kept in the run
  (WALL_END_GAP); the true passage mouth is 1.20 m;
- not counted: the inner face of the boundary wall (1.200 m, layer 5, two lines 0.200 m apart across the strip).

## New finding: the passage is partly roofed by the first floor (not in the earlier hand readings)

The first-floor plate, moved by the offset between the two plan frames (-44.852655 m; checked: 14 of the 20 1F
columns fall exactly on GF columns after the shift), covers the north 3.40 m of the strip: a 1F bathroom and a corner
of the master bedroom stand over it, carried by the two columns on the annex side of the passage. So:
- space 5.640 m2 (1.20 x 4.70): 4.080 m2 under the first floor (a soffit: exterior ceiling under the 1F bathroom),
  1.560 m2 open to the sky;
- 6.800 m of the 9.400 m of passage walls stand under the first floor;
- the run does not change (a covered strip with an open mouth is still outside air: rain falls into its open end and
  nothing closes it), but the soffit and the wall heights under the 1F slab are facts the facade-area and
  ceiling stages will need. Not measured here: the 4.08 m2 soffit finish and the 1F slab over the passage (concrete
  ledger: check it is not missing; the 1F bathroom floor there is a wet floor over open air).
- The printed level inside the strip is +0.15 (the house floor reads +1.00, the annex +0.30): listed as evidence only.

## The general rule (what the drawing must show; no width or depth limit anywhere)

1. MOUTH: an outline edge that is a census PASSAGE threshold (no door symbol, leaf or glazing in the gap).
2. SPACE: the faces behind it, joined only through further doorless PASSAGE thresholds (a door, a window, a glazing
   line or a wall stops the search). A threshold piece whose face behind is a capped wall end is a WALL_END_GAP (kept).
3. NOT A ROOM: no room label, tag or fixture in the space. Labelled -> KEPT (the engine's outline stands).
4. AN OPEN MOUTH: nothing drawn across at least one mouth. Two parallel lines of one non-building layer across a mouth
   jamb to jamb = CLOSED_BY_ELEMENT (a boundary or fence wall): its body is not part of the space, its faces are not
   the building's. One line only (no thickness) -> HELD.
5. OPEN TO THE SKY or OPEN AT BOTH ENDS: part of the space under no plate above, or two or more open mouths (a covered
   breezeway is outside air). Fully covered with one open mouth (a car porch, or a room whose door the census missed)
   -> HELD with both runs; plate above not read -> HELD.
OPEN_AIR: run = walked - every mouth + every building face bounding the space (walls, columns, caps, and the door and
window thresholds in them). Lines of other layers not read -> HELD with no number (range NOT_ESTABLISHED, never 0).

## Hand fixtures (not the development villa): tests/t109_facade_passage (23 tests)

Two blocks with 0.20 m walls, 6.00 x 5.00 and 7.50 x 5.00 m, collinear front and back faces, a 1.50 m strip between
them; a 1.00 m door in one strip wall, a 1.50 m window in the other; the census thresholds at both ends.
- engine outline 2 x (15.00 + 5.00) = 40.00 m (bridges the strip twice) - reproduced through the engine's topology and
  arch_v29.facade_outlines, rotated 30 / -121 deg, mirrored, in m and mm;
- boundary wall across the south end, roofs over the blocks only: 40.00 - 3.00 + 4.80 + 4.80 = 46.60 m, both mouths
  not building openings, element 0.20 m, space 7.20 m2 open to the sky (all five variants);
- half the strip roofed: still 46.60 m, covered 3.75 m2, open 3.45 m2, 5.00 m of walls under the plate;
- fully roofed dead end: HELD 40.00 .. 46.60 m, nothing applied, no opening reclassified; roof not read: HELD, same range;
- open at both ends, roofed or not: 40.00 - 3.00 + 10.00 = 47.00 m (m and mm, rotated + mirrored);
- a label inside the strip: KEPT 40.00 m; one line across a mouth: HELD; other layers not read: HELD, no number;
- no passage on the outline: NO_PASSAGE 40.00 m; empty outline: NO_OUTLINE, no value (never 0);
- the south threshold running 0.20 m over a capped wall end (census width 1.70 m): the 0.20 m kept, still 46.60 m.

## Checks

tests/t109_facade_passage 23 pass; L2 set (t014, rebar product firewall, m9_n10, m9_p2b6-9, m9_s2_arch) see the board
handoff; freeze 0; codemap rebuilt, stale none.

## What is learned / what is missing

- A doorless gap between two collinear wall faces is not proof of an opening: the faces behind it decide. The census
  reads a gap with jambs as a passage by its geometry alone, and the outline then walks the gap. The space behind the
  gap (unlabelled, doorless, open to the sky or at both ends) shows it is ground, not building.
- A census opening width can include a drafting gap over a capped wall end (OP-001 1.40 m, mouth 1.20 m).
- Two readers agreeing is not proof (T-014's independent reader closed the same mouth by width): the piece decides from
  the space, not from the mouth width.
- Missing: wiring into a method version (tools/urban_boq_m9.py, outside this task) so the released GF run becomes
  105.886694 m and ARCH.PASSAGE GF drops 2 -> 0; the independent reader (tools/indep_reader.py) still closes an open
  mouth by width (the verifier's note): not changed here; the Q-64 notch (0.10 m) stays open; the soffit and the 1F
  slab over the passage are not measured.

Reproduce: `python3 -I research/agents_t109/alsenan_passage_check.py <P7757 plan DXF> <out dir> research/urban_m9_s2/SYNTHETIC_FACTS_S2.json`
(the DXF from Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, sha256 of the DXF ab54dd55..., kept outside
the repository). It prints lengths, areas, counts and states only.

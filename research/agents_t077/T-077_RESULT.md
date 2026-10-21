# T-077: lost windows and the unexplained door element, traced and guarded (gate 1)

Worker 1, 2026-10-19 16:27-16:55 UTC. Development villa (Alsenan), not an accuracy claim. Counts, metres and entity
ids only: no coordinates, no images, no client names. Rules: UP-QTY-STATUS-001 (every drawn element reported once,
never 0), UP-OPEN-SCHED-001 (no height printed -> width only, area held), UP-OPEN-CURVED-001 (curved wall bands),
UP-QA-001 (no benchmark anchors a geometry reading: the freelancer's figures were compared only after the census).

## Inputs (session scratchpad, never committed)

| Input (Drive "Alsenan chalet project") | sha256 | Used for |
|---|---|---|
| P7757_DXF_COMPRESSED.zip / P7757.dxf | ab54dd55...31cc4 (= SOURCE_MANIFEST) | V2.9 run, guard run |
| ST7757 dxf.dxf | 9f9d1179...38079 (= SOURCE_MANIFEST) | V2.9 run (route G, unchanged) |

Engine run: working branch 2c86de1, Python 3.11 venv from requirements.txt, the T-001b command
(`tools/urban_boq_m9.py arch --method ARCH_TAKEOFF_V2.9 --structural ... --conventions ..._V6.json`): exit 0.
Guard run: `python3 -I research/agents_t077/run_guard.py P7757.dxf RUN --out RESULT.json` (read-only; wraps
arch_rooms.spaces in its own process to keep each plan frame's entities and openings; first result per frame).

## What the engine now gives against the freelancer (windows and doors, counts)

| Floor | Windows drawn (guard) | engine MEASURED (count lines) | HELD by the guard | Door symbols drawn | engine elements | released / held | Silent omissions |
|---|---|---|---|---|---|---|---|
| GF | 12 | 11 | 1 (curved glazing) | 15 (14 blocks + 1 loose arc) | 15 | 6 / 9 | 0 |
| 1F | 13 | 12 (incl. curved COP-001) | 1 (0.50 m bath window) | 10 (blocks) | 10 | 8 / 2 | 0 |
| 2F | 4 | 4 | 0 | 3 (blocks) | 3 | 3 / 0 | 0 |
| All | **29** | **27** | **2** | **28** | **28** | **17 / 11** | **0** |

Windows: freelancer 29, engine census 29 (27 measured + 2 held) -> difference 0 drawn windows (was 27 vs 29, -2,
-6.9 %, both silent). Released window count lines unchanged at 27: the guard is a method piece, not wired (a
released method version is the owner / T-079 step). Every engine window has its glazing bound (41 glazing clusters:
39 in the 27 windows, 2 held). Doors: 28 drawn symbols = 28 engine elements, 0 swings outside the engine (T-040 had
27 blocks vs 28 elements, 1 unexplained). Freelancer door count not compared here (his aluminium sheet holds only the
external doors, in m2).

## Cause of each loss (traced in the V2.9 code, re-run on the engine itself)

1. **GF curved pool glazing (HELD, CURVED_GLAZING_WITHOUT_CURVED_WALL_BAND).** The wall is STRAIGHT (a 0.20 m band
   that stops at a jamb line, D2:628, and at a wall corner / column, D2:620: 4.95 m apart); the glazing is four
   concentric bulge-polyline runs on the window layer that bow out of it (radii 2.33 / 2.37 / 2.41 / 2.45 m, lengths
   6.658 / 6.703 / 6.747 / 6.792 m). V2.9 reads curved openings only as gaps of CURVED wall bands (two concentric
   wall arcs, arch_v29.curved_gaps; no wall arc is concentric here) and the straight path needs a band on BOTH sides
   of the gap (the far end is a wall corner, not a band): so neither path makes an opening and nothing was recorded.
   Printed: one arc dimension "657" on the same centre measures an arc of radius 2.25 m on another layer (6.5675 m),
   80 mm inside the innermost glazing line; it is not on a glazing line (basis ARC_AT_OTHER_RADIUS).
   Second drawing (PDF, p7757_arch_sheet03, ground floor plan, read by eye): the curved enclosure round the pool end is
   drawn as a 0.20 m band (printed "20" radially at the crown and at the springing) whose INNER line carries the
   "657" arc dimension; the four glazing lines lie in the outer part of that band. So the printed 6.57 m is the inner
   face of a 0.20 m glazed band (r 2.25 -> 2.45 m; outer face 6.79 m): the same reading as the DXF.
2. **1F sea-side bath window (HELD, COLUMN_CUT_PIECE_UNDER_MIN_GAP).** The band gap is jamb to jamb 0.500 m
   (printed "50", dimension 11ED = 0.500 m: match), and the engine's band reader finds it (state OPENING). A column
   outline (S-COL layer) overlaps the gap end by 0.0327 m; lintel_measure._split_at_columns cuts the gap at the
   column face and keeps only pieces of at least 0.50 m (min_gap_m), so the 0.4673 m piece is dropped with no
   record (reproduced: the wrapped split returned [] for this gap; the synthetic test shows the same on the engine).
   Second drawing (PDF, p7757_arch_sheet04, first floor plan, read by eye): the bath's sea-side wall carries the chain
   "109 / 101 / 50 / 58" with the filled column (101) directly beside the 0.50 m window: by the print the window starts
   at the column face; the 33 mm overlap is the DXF column outline only.
3. **GF 0.80 m door element "without a block" (explained, HELD by the engine as before).** Its swing is a loose arc
   on the door layer (radius 0.69 m), not a block insert; T-040's census counted only blocks. It is the door between
   the master bedroom and its bathroom; the engine holds it (PROVISIONAL_NOT_RELEASED: no band opening, width range
   0.69-0.80 m). Not a double reading: 28 drawn symbols, 28 elements.

## Verdict proposals (for the verifier)

| Item | Engine (guard) | Freelancer | Proposal |
|---|---|---|---|
| GF curved glazing: exists | HELD, counted | 6.57 x 4.30 = 28.251 m2 | FREELANCER_RIGHT on existence (the engine had lost it); now held, not lost |
| GF curved glazing: width | candidates 6.658-6.792 m (glazing lines), 6.5675 m (printed arc, r 2.25 m), chord 4.95 m | 6.57 m | UNRESOLVED: which line gives the width of a curved glass wall set in a straight gap -> owner Q-37 |
| 1F bath window: exists | HELD, counted | one of 6 x 0.60 x 0.80 | FREELANCER_RIGHT on existence |
| 1F bath window: width | jamb to jamb 0.500 m = printed "50"; clear past the column 0.467 m | 0.60 m | ENGINE_RIGHT proposal on the width by the printed 0.50 (hand: dimension 11ED 0.500 = jamb lines 0.500 apart); height not printed: area HELD |
| GF loose-arc door | engine HELD (0.69-0.80 m) | not compared | ENGINE_RIGHT on existence (drawn swing, one element); class / width stay held as the engine says |

## Method piece

`engine/source/opening_omission_guard.py` (new, OPENING_OMISSION_GUARD_V1, stdlib; not imported by any method):
per plan frame, glazing pieces of the window layers are grouped into touching clusters (end to end or T-junction,
1 mm), each bound to the engine opening holding at least half of it; an engine WINDOW is MEASURED, a cluster in no
opening is a HELD window with its traced cause (curved without a curved band, curved gap refused, no jamb, gap under
0.50 m, column cut piece under 0.50 m, band not read), its spans as width candidates and any matching printed
dimension (evidence only); every engine door element is MEASURED or HELD as the engine says, with its symbol kind
(BLOCK / LOOSE_ARC / NONE); a drawn swing no element uses is HELD SWING_NOT_IN_ENGINE. Nothing held gets a width,
height or area; units missing -> no metres; conservation asserted (every glazing piece and every swing once).

## Tests

`tests/t077_opening_omissions` (15): hand fixture that is not Alsenan (straight band with a 1.20 m window, a 0.50 m
window whose column overlaps 0.03 m with a printed 0.50 and a refused 0.60 dimension, a curved glazing of radii 1.95 /
2.00 m in a 3.00 m straight gap: arcs 3.3074 / 3.3922 m by hand, glazing on a wall with no jamb, a 0.45 m gap; a block
door released, a loose-arc door held, a free swing) in metres, mirrored, rotated 30 deg, rotated + mirrored in mm, mm
far from the origin; units missing; bad unit; empty frame; glazing in a door gap; curved COP bound; curved gap refused;
the 0.50 m minimum equals lintel_measure.openings' default; the engine's own band reader drops the column-cut piece
that the guard holds; conservation. L2 (tests/t077_opening_omissions, tests/m9_p2b9, tests/m9_n10,
tests/t061_room_label_guard): 151 pass. Freeze 0; maps rebuilt (new files), stale none.

## What was learned / what is missing

- Two general loss paths exist in V2.9 openings, both silent: curved glazing in a straight gap (the curved reader
  needs a curved wall band) and a column outline that overlaps a narrow gap by a few cm (the split drops the piece).
  The guard now catches both on any villa; the fix that MEASURES them is a new method version (owner rule needed for
  the curved width: Q-37; the 0.50 m window needs only the wiring, its width is printed).
- Door symbols can be loose arcs as well as blocks: any door census must count both.
- Missing: wiring into a released method (T-079 / owner), heights (none printed for these two), the "430" binding of
  the GF pool glazings (T-040), arched heads (Q-32), window material (Q-33).

Gate 1 (0 lost openings on the development set): windows 0 silent omissions (was 2), doors 0 (was 1 unexplained).

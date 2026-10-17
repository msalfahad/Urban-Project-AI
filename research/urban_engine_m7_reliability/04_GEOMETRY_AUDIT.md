# 04 Geometry audit

## Method

`tools/m7_metamorphic.py` changes only the DXF — never an expected value — and requires every quantity (concrete and
reinforcement: base, low, high, unresolved exposure, item count, by trade / family / storey / category) to stay the
same within 1e-6 relative (geometric operations) or exactly (reordering, duplicated text, unrelated layer):

| Operation | What changes in the drawing |
|---|---|
| translate | every entity moved by (+1 234 567, −765 432) units |
| rot90 / rot180 / rot270 | the whole drawing rotated about the origin |
| mirror_x | x → −x |
| reorder | model-space entities written in reverse order |
| explode | every LWPOLYLINE replaced by its LINE / ARC pieces |
| dup_text | every TEXT / MTEXT drawn twice at the same place |
| noise_layer | 160 rectangles and circles on an unrelated furniture layer |
| units_m | the drawing re-expressed in the other unit (mm ↔ m) |

A difference is a finding about the engine. Each was traced on the drawing to a geometric cause before a rule was
written.

## Findings (development villas 1–8 and ST7757), in the order found

| Cause | How it showed | Rule |
|---|---|---|
| MTEXT rotation stored as a direction vector after any transform | a 90° beam mark read as 0°, no longer parallel to its band: 22 quantity groups changed per noisy drawing on translate | intake: `MTEXT.get_rotation()` |
| mirrored TEXT insert in OCS | mirror lost every sheet title | intake: OCS → WCS |
| shoelace areas and clip predicates at coordinates ~1e6 | slab areas off by up to 1e-4 m² per cell (metre drawings); on ST7757 three flush columns stopped cutting their bands after a translation | `GEOMETRY_LOCAL_ORIGIN`: the route computes in a drawing-local frame (origin = lower-left of the linework, recorded) |
| exact-zero overlap on flush faces | after rot180 on ST7757 a column flush with a ground beam read as free-standing: a 6.8 m² cell (1.09 m³) went UNRESOLVED | `TOUCH_IS_NOT_OVERLAP`: overlap must exceed 1e-4 m² to cut; a column touching a band stands on it |
| convex clip against an arc band | a column inside a curved band had zero overlap: free-standing by mistake | the free-column test takes the column centre inside any band polygon |
| furniture rectangle at a column size | a furniture square on a column mark became a column (beam cut, cells split) on 5 of 8 villas | `COLUMN_LAYER_EVIDENCE` (+ post-freeze P2: set-aside outlines stay weak evidence) |
| lines of another layer inside a stair bay | the equal-going run broke, the bay was counted as slab | `STAIR_TREADS_ONE_LAYER` |
| fixed 1.0-unit minimum rectangle side | in metres every column polyline vanished (ST7757: 50 groups) | `UNIT_AWARE_RECTANGLES` (1 mm in the drawing's unit) |
| minimal cells of crossing lines | four composite column outlines lost when exploded (ST7757: GF beams +0.30 m³) | `RECTANGLE_FROM_FOUR_SIDES` |
| exploded clipped outline | a non-rectangular footing fell back to its schedule size (+0.042 m³) | `POLYGON_FROM_LINE_RING` (partial: a third line at a corner still breaks the ring) |
| continuous beam matched REVERSED | end anchorage placed at the interior support: a 5D18 group 73.2 / 66.2 kg depending on orientation | `CB_ENDS_BY_SHARED_SUPPORT` |
| a 5.000 m span on a 5.0 m class limit | the ground-beam section class flipped with placement (low reading 0.9 / 0.6 m³) | `LENGTH_CLASS_AT_MILLIMETRE` (+ P1: lintel width bands) |
| duplicated annotation | duplicate member ids: the run crashed | `DUPLICATE_ANNOTATION_READ_ONCE` |
| frame drawn as lines | no sheet found after explode | `SHEET_FRAMES_FROM_LINES` |

## Results

| Set | V4 | V5 |
|---|---|---|
| Development villas 1–8 (cluttered), 80 property checks | not run under V4; the first V5 state failed 31 / 80, 9 / 80 after the MTEXT fix | 80 / 80 |
| **Held-out villas 301–310**, 100 property checks | 69 / 100 (dup_text 0/10, explode 0/10, noise_layer 1/10, translate 8/10) | **100 / 100** |
| ST7757, 10 operations (structural drawing alone) | — | translate, rot90, reorder, dup_text, noise_layer: exact. rot180 / rot270: 3 groups (GF beam bars −0.13 kg); mirror: 6 groups (GF slab −0.002 m³, the same bars); units: item count only (one panel split into two items, same m³); explode: 66 groups (≤ 1e-4 relative arc-representation drift, and the one clipped footing +0.042 m³) |

The ST7757 operations were run four times as the rules were added (`st7757/METAMORPHIC.json`); the residuals are open
weakness M7-W20 and M7-W9.

## Slab topology

- **Bays merged into an opening (M6 W7, re-diagnosed).** On the M6 held-out set the slab faces reported as
  REGION_EXCLUDED were of two kinds. Some were exactly the design's own opening bay (the generator draws VOID and an X
  across bay (0,0)): a correct large-void flag that the M6 evaluator counted as false because its truth lists injected
  elements only. Others were larger than that bay — neighbouring bays joined to the void through a gap at an undrawn
  support and the whole region dropped (seeds 212, 215, 240: 30–80 m²). The second kind is the real defect.
  `SLAB_JUNCTION_GAP_CLOSURE` closes the cells where band ends meet at an undrawn support (the junction square itself
  is JUNCTION_GAP, in no item); `SLAB_OPENING_EXTENT_GUARD` refuses an opening label as proof for a face that holds a
  beam band (OPENING_SUSPECT: neither slab nor void, unresolved with its exposure). Under V5 every REGION_EXCLUDED face
  on seeds 201–240 is the design's own void bay. Page 4 of the visual QA shows seed 240 before / after.
- **Suspiciously large voids.** An opening face is never deleted silently: it stays a face, the completeness pass
  reports REGION_EXCLUDED with its area, and an OPENING_SUSPECT face carries an exposure range.
- **Stair inside a panel.** A tread family that does not cover the panel holds its footprint unresolved (0 .. hull × t)
  instead of counting it as slab (`SLAB_STAIR_FOOTPRINT_UNRESOLVED`).

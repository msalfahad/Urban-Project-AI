# Before / after BOQ effects - V2.3 -> V2.4 (deliverable 10)

ARCH_TAKEOFF_V2.3 (frozen, registry 1.0.0) against ARCH_TAKEOFF_V2.4 (registry 1.1.0, no project rules) on the same
drawings. The synthetic villa is shown line by line in `BEFORE_AFTER_SYNTHETIC.md` (generated); the reference plan is
shown **as aggregates only** (its per-room, per-door and line-level outputs stay private). The anticipated changes were
written down before implementation (`PRE_IMPLEMENTATION_AUDIT.md` section 5); every one of them happened in the
expected direction, and two defects found on the reference plan were fixed (section 3).

## 1. Synthetic villa (two storeys, two bathrooms, a kitchen, six doors)

| Item | V2.3 | V2.4 | Why |
|---|---|---|---|
| FIN.WP.FLOOR | 31.36 m2 (3 lines) | 31.36 m2 | unchanged geometry |
| FIN.WP.DOORWAY (continuation piece) | 0.50 m2 | 0.50 m2 | approved owner method, kept |
| FIN.WP.UPTURN (perimeter incl. doorways) | 7.84 m2 | - | replaced (CF-12) |
| FIN.WP.WALL_UPTURN (eligible boundary x 0.20) | - | 7.34 m2 | the three doorway segments (2.50 m x 0.20 m) are no longer wall upturn |
| FIN.WP.DOORWAY_TRANSITION | - | 3 withheld, range 0 .. 0.50 m2 | no doorway detail: three alternatives listed |
| FIN.WP.PENETRATION | - | 3 BLOCKED_RFI | no drain drawn: NOT_SHOWN, count None |
| membrane layouts | 2 rooms (bathrooms) | 3 areas (the kitchen added) | every waterproofed area gets its layout |
| rolls | 4 (per-room sum, 2 rooms) | 6 for 3 areas (7 if each alone), PROVISIONAL | one cutting plan per system; not CONFIRMED (system not specified, 9 detailing items withheld) |
| FIN.PLASTER door jambs | 6 lines, 6.34 m2, all at 2.20 m | 5 lines 5.26 m2 at 2.20 m + the main-entrance candidate 1.08 .. 1.20 m2 | the candidate is 2.20 or 2.50 m: a range, not one assumed height |
| doors | as-drawn and owner-required views | + feasibility: 3 GEOMETRICALLY_POSSIBLE, 2 REQUIRES_ENGINEERING_REVIEW (first floor: no column frame drawn), 1 INSUFFICIENT (main-entrance candidate) | no door line changed |
| questions (B groups / instances) | 6 / 34 | 9 / 44 | doorway details, penetrations, corner details |

## 2. Reference plan (aggregates)

| Aggregate | V2.3 | V2.4 |
|---|---|---|
| waterproofed areas with a membrane layout | 16 | 17 |
| FIN.WP.FLOOR | 72.121 m2 | 72.121 m2 (unchanged) |
| FIN.WP.DOORWAY continuation pieces | 2.035 m2 | 2.035 m2 (unchanged) |
| upturn | 28.945 m2 (whole perimeter incl. doorways, 17 lines) | wall upturn 25.085 m2 (17 lines) |
| doorway transitions | inside the upturn | 15 withheld, range 0 .. 2.459 m2 |
| edge terminations | - | 7 withheld (<= 3.66 lm) |
| penetrations | reported as 0 by the layout | 17 areas NOT_SHOWN (the plan draws no drain symbol or label) |
| rolls | 18 (per-room sum, 16 rooms) | 14 for 17 areas (19 if each alone), PROVISIONAL |
| installed / consumed / cutting waste | - | 120.02 / 138.13 / 18.11 m2 |
| door jamb plaster | 21 lines, 19.32 m2 (all at 2.20 m) | 19 lines 16.96 m2 + 2 main-entrance candidates 2.36 .. 2.60 m2 |
| door feasibility (28 door elements) | - | 11 GEOMETRICALLY_POSSIBLE, 5 CONSTRAINED, 12 INSUFFICIENT_DRAWING_EVIDENCE; host walls MASONRY_INDICATED |
| approvals listed | - | 51 door items, 1 waterproofing system |
| questions B / C / D / E instances | 187 / 0 / 8 / 18 | 245 / 0 / 8 / 18 (A and unclassified 0) |
| ledger | conserves, CONFIRMED_MISSING 0 (487 records) | conserves, CONFIRMED_MISSING 0 (523 records) |

Mode A (the synthetic S2 heights facts) gives the same waterproofing and door results; only the jamb heights from the
facts change the provisional jamb total (V2.3 18.60, V2.4 16.32 m2 + the same two ranges).

The upturn drop (-3.860 m2) is the doorway segments leaving the wall upturn (they are transitions now) plus the
openings to other spaces; the sliding-window frames that the boundary roles called half glazing edge are counted as
sill upturn (section 3, D-04).

## 3. Defects found on the reference plan during this phase and fixed before release

| # | Found | Effect before the fix | Fix | Test |
|---|---|---|---|---|
| D-04 | a window-layer line on the inner face of a recognised window was read as floor-level glazing (it outranked the window threshold) | 33 false edge terminations; the sill-wall upturn below 10 windows dropped; 10 false segmentation reviews (E) | role priority DOOR > PASSAGE > WINDOW_THRESHOLD > GLAZING; the segmentation check accepts the window-frame band | `test_a_window_frame_line_on_the_wall_face_is_a_sill_upturn_not_glazing`, `test_the_segmentation_check_accepts_window_frames_and_flags_anything_else` |
| D-05 | two constrained doors listed the placement name as their first reason | the class was right, the reason misleading | the governing reason (a stair / shaft / lift at the enlarged jamb) first | `test_a_stair_at_the_enlarged_jamb_constrains_and_says_why_first` |

## 4. Double-counting review

| Pair | Overlap? | Why |
|---|---|---|
| FIN.WP.DOORWAY (horizontal piece) and FIN.WP.DOORWAY_TRANSITION | no | the piece is the floor strip through the doorway; every transition alternative is vertical (threshold upturn, jamb returns) or a termination length |
| FIN.WP.WALL_UPTURN and FIN.WP.DOORWAY_TRANSITION | no | the doorway segment is excluded from the eligible boundary; it appears only as a transition |
| two waterproofed rooms sharing a doorway | no | DOORWAY_CONTINUATION: one doorway piece (owner rule store UP-WP-003), no transition on either side |
| per-room rolls and the project cutting plan | no | procurement is the cutting plan only; the per-room roll count is reported as "if installed alone" |
| wet and exterior systems | no | separate groups, never summed (`test_separate_systems_are_never_combined`) |
| proposed door enlargements and the as-drawn lines | no | the proposals live in DOOR_FEASIBILITY / BOQ_SCENARIOS.PROPOSED_MODIFICATION only (`test_no_proposed_modification_is_released_as_drawn`) |
| jamb plaster range and the jamb line | no | the candidate's line is the range itself (BOUNDED_EXPOSURE), not a released line plus a range |

The ledger conservation (every line in exactly one record) holds on both drawings.

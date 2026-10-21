# M9 S4 — root-cause register (room and floor accuracy)

This register explains why the S2 / S3 architectural route measured some rooms differently from the earlier Round-5
truth engine on the same drawing revision.

How the comparison was made:

- Rooms were compared at the same location: the face that holds each Round-5 region's centroid.
- The comparison ran post-freeze and is reported as differences only.

The figures of the reference project are in the release package (ZIP), not here.

S2 and S3 measure every room identically, so S3 did not regress against S2. The losses came in with S2's new room
route. That route kept the TS01 kernel (`topology.build` / `sites_of`) but not Round 5's closure rules:

- Route A's door / gap closures;
- closure B;
- wall-band handling;
- the X-RECT void rule;
- SHAFT_EVIDENCE.

S4 brings these rules back into `engine/source/arch_rooms.py` as generic rules.

| Id | Cause | Mechanism | Evidence | S4 fix | Test |
|---|---|---|---|---|---|
| RC-1 | **Door swing on the wrong opening** | `spaces()` gave an opening the first swing whose hinge lay within 0.30 m of any point of its face line. There was no exclusivity and no check that the leaf fits. | A 0.80 m swing at the corner of a 1.30 m archway made the archway a DOOR. A lobby door's swing served a 1.40 m opening 0.16 m away, and its own gap stayed open. | `match_swings`: the hinge stands at a jamb, the closed leaf lies along the gap, the leaf fits the width (one leaf, or two of a double door). Each swing serves one opening, chosen by best fit. | `test_swing_near_an_archway_serves_its_own_door`, `test_match_swings_scores_fit_not_proximity`, real: `test_the_lost_room_is_recovered` |
| RC-2 | **An open passage treated as a boundary** | Every wall-band opening was closed by its thresholds. A doorless archway or passage split one floor into two faces, and the room's vestibule or lobby became an UNLABELLED space with no finish. Round 5's Route A left clear gaps open. | A bedroom lost its vestibule. A kitchen lost the lobby it opens onto, up to the lobby door. | `opening_marks` and `open_passages`, then a second TS01 pass. A clear passage (nothing drawn in it but two head lines) is not a boundary. An unlabelled cell reached only from one labelled room joins it (ATTACHED_THROUGH_OPEN_PASSAGE, PROVISIONAL, flagged for review). A cell shared by several rooms, or larger than half the room, stays apart. A symbol block, extra lines, or lines or arcs inside the gap keep the boundary. | `test_vestibule_through_a_clear_archway_belongs_to_the_bedroom`, `test_kitchen_takes_its_lobby_up_to_the_lobby_door`, `test_marked_openings_keep_their_boundary`, `test_a_space_larger_than_half_its_room_is_not_attached`, `test_physical_regions_join_cells_through_every_clear_passage` |
| RC-3 | **Wall bodies leaking into rooms** | Caps were placed only where both faces of a band end at the same station (within 3 cm). They sat on the line's averaged, 0.5°-rounded offset and missed the drawn segment by more than the 0.5 mm join tolerance. Wall interiors (mitred and diagonal walls, uneven jambs) became room floor. | A bedroom took in about 1 m² of the wall bodies around it. A wash area and a WC took in wall strips (boundary walks through the wall interiors). | `wall_caps`: two-sided and one-sided caps (one face ends, the other goes on). Both cap ends lie ON the drawn segments (`_face_point`). | `test_wall_body_caps_meet_the_drawn_segments` (it also shows the averaged point misses), real |
| RC-4 | **The doorway piece inside a room** | A door with no band opening was closed by its leaf ray on one wall face only. Its 0.8 × 0.15–0.2 m doorway piece joined the room on the other side. | The residual difference of three rooms (bathroom and bedroom doors). | `closures_b`: the wall's other face at both jambs closes the piece (Round 5's closure B). The piece is its own DOORWAY face and gets a waterproofing doorway line in wet rooms. | `test_closure_b_joins_the_other_wall_face_at_both_jambs`, `test_doorway_piece_is_its_own_face_not_the_rooms`, real |
| RC-5 | **A void as floor** | A VOID word made the face MIXED with no deduction. The S3 void symbol needs all four sides drawn, and a hand-drawn X (the second line 3° off the diagonal, 60 % long) was not read. | The double-height void stayed in the living face. | `x_rect_at` / `void_outlines`: Round 5's X-RECT rule, for any rotation, with the second line within 5°. The void is deducted from the floor only when a VOID word lies inside the outline. A symbol without the word is recorded, never deducted (on a lower plan it marks the opening above). A word without an outline is VOID_EXTENT_UNRESOLVED. | `test_void_outline_rules`, `test_x_rect_second_line_must_follow_the_other_diagonal`, real `test_the_outlined_void_is_never_floor` |
| RC-6 | **The stair below seen as floor** | The floor finish deducted only the plan's own treads. A flight of the plan below, seen through the opening, stayed porcelain. | The upper plan's living finish held the lower stair's footprint. | `arch_floor.split_face` (STAIR_BELOW_SEEN). The finish lines use the same split, so lines and floor areas cannot disagree. | `test_stair_seen_through_the_opening_is_neither_floor_nor_counted_twice` |
| RC-7 | **A shaft as an unnamed room** | Round 5's SHAFT_EVIDENCE (same footprint every storey) was not in S2 / S3. | The same doorless 1.8 × 1.8 m space on three plans. | `stacked_shafts`: a small doorless unlabelled footprint repeated on the other plans (aligned on the column grid) is a SHAFT, flagged for review. | `test_stacked_doorless_footprint_is_a_shaft`, real `test_the_stacked_shaft_is_a_shaft` |
| RC-8 | **A merged open plan (not fixed)** | The reception face holds several room words and an exterior word. Round 5's Route A had the same merged site. Round 5 split it only by its shadow route, bridging gaps of 0.3–3.6 m between aligned wall ends, and still left the main piece MIXED_UNRESOLVED. | A pantry, dining, reception and living in one face. | None: the face stays one physical region (UNALLOCATED_MERGED, review). A split needs a drawn boundary or an owner rule. Bridging gaps would invent a boundary. | — |
| RC-9 | **Reporting scope: the room sum as the floor area** | The S3 comparison set the finish lines of single-label rooms against the human total floor. The merged and unlabelled area had no finish line, so most of the shortfall was scope. | The "large floor-area shortfall" of S3. | `arch_floor.reconcile`: every m² of a plan is in one category or a listed residual. The internal physical floor is reported, and the room sum is reported as a part of it, never as the floor area. | `test_every_m2_of_each_plan_is_in_one_category`, `test_villa_floor_plate_is_the_sum_of_its_parts` |
| RC-10 | **An open-plan scope difference (not a defect)** | The human measure of an open-plan room excludes the landing or circulation around a void, but no drawn boundary separates them. | One living room. | None (review): the finish is reported with the void and stairs out, and the zone split is flagged. | — |
| RC-11 | **The earlier benchmark matching was area-informed** | Round 5's own post-freeze comparison paired some benchmark rows with engine rooms by nearest area, so its agreement on those rows is optimistic. | Three rows. | The S4 comparison pairs by location (the Round-5 region's centroid) and by name only where Round 5 had no region. | — |

Never in S4:

- a boundary invented inside an open space;
- a void area guessed without its outline;
- a room sum presented as a floor area;
- a residual spread over rooms.

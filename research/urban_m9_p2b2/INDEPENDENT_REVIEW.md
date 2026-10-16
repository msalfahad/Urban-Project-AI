# Independent engineering review (deliverable 14, Part 8)

A review of this phase's work as an independent quantity surveyor / engineer would read it: what was wrong and fixed,
what is still weak, where the rules themselves deserve an objection, and what to do next. Reference-plan evidence is
aggregate only.

## 1. Defects found and fixed in this phase

Each one was reproduced by a failing test (or a failing run) before the fix; no existing test was weakened.

| # | Defect | How it was found | Fix | Proved by |
|---|---|---|---|---|
| D-01 | the synthetic generator's mirror turned each mirrored door leaf half a turn about its hinge (the leaf closed outside its gap and swung into the other room) | the V2.4 metamorphic door test: the mirrored villa gave a false swing conflict | `tools/arch_synth.py`: rotation `-r` (a true mirror) | `test_mirrored_and_rotated_geometry_give_the_same_result` (mirror, quarter turn, move, and all three together) |
| D-02 | a swing symbol closing outside its jambs was evaluated literally (a sector on the wrong side) | D-01 | SWING_SYMBOL_INCONSISTENT: reported, not evaluated. It flags one door of the synthetic villa itself (the first-floor bedroom door block, mirrored and turned, closes 0.90 m outside its jambs - a realistic drafting error, left in the fixture); none on the reference plan | `test_a_swing_symbol_closing_outside_its_gap_is_reported_not_evaluated` |
| D-03 | on the rules sheet a project rule in a conflict showed its own value as applied (PROJECT_SPECIFIED) on its row | review of the generated example sheet | CONFLICT_REVIEW and no applied value on the rule's row; one question per conflict | `test_a_conflicting_project_rule_is_never_shown_as_applied` |
| D-04 | a window-layer line on the inner face of a recognised window was read as floor-level glazing (it outranked the window threshold) | the reference-plan run: 33 glazing terminations, 10 segmentation reviews | role priority DOOR > PASSAGE > WINDOW_THRESHOLD > GLAZING; the segmentation check accepts the window-frame band | `test_a_window_frame_line_on_the_wall_face_is_a_sill_upturn_not_glazing`, `test_the_segmentation_check_accepts_window_frames_and_flags_anything_else` |
| D-05 | a door constrained by a stair at its enlarged jamb listed the placement as its first reason | reference-plan aggregate review | governing reason first | `test_a_stair_at_the_enlarged_jamb_constrains_and_says_why_first` |
| D-06 | the maximum feasible enlargement beside an OPEN_RUN side (read only to 3.00 m) was reported as an exact value | review of the door schedule | `max_feasible_is_lower_bound` | `test_before_after_waterproofing_and_doors_on_the_villa` |
| D-07 | an S1 hygiene test rejected the owner-mandated method name `ARCH_TAKEOFF_V2.4` (its "2.4" equals an external benchmark figure) | the affected-suites run | method identifiers removed before the figure scan (narrow, documented; the forbidden-number check unchanged) | `tests/m9_foundation/test_m9_s1_package.py` |
| D-08 | two new engine modules called the membrane corner item "corner reinforcement", which the rebar firewall reads as rebar-aware code | the full suite on `3b0f12f` (1 new failure) | the engine names it "corner treatment" (`b4d0b6b`) | `test_rebar_product_firewall.py::test_every_rebar_module_in_engine_is_declared` |

Defects caught by the new tests while the modules were being written (before integration): the opening frame of a
neighbouring opening (offsets need the sign of its normal), a conflicting pier rule crashing the placements, the
dependency impacts receiving no side scopes, a T-junction labelled WALL_END, a column face level with the hinge
counted as a swing obstruction, a test window without glazing read as a passage.

## 2. Objections to the implementation as it stands

| # | Objection | Weight | Recommendation |
|---|---|---|---|
| O-1 | The wall upturn includes the window threshold on the assumption of a sill wall, and is released SOURCE_DERIVED; a floor-level window would be over-upturned. The window type is asked elsewhere (WINDOW_TYPE_AND_SILL, 34 instances on the reference plan) but the upturn does not wait for it. | medium | release the window-threshold share as PROVISIONAL until the window type is known (a V2.5 opt-in) |
| O-2 | The segmentation check uses the V2.3 boundary roles as its reference and accepts up to their glazing-edge length: a real segmentation error smaller than that band would pass. | low | an independent check: the ring length must equal the sum of the role runs (it does today, by construction), plus a per-window comparison of the threshold length with the band opening width |
| O-3 | Laps are counted but not oriented (no shingle order towards the drain); falls and screeds are outside the route. | medium for procurement of high-end systems | keep counting; add the lap direction only when a drain position is known |
| O-4 | Penetrations: the reference plan draws no drain, so every wet area is NOT_SHOWN. The quantity is honest (withheld) but the BOQ cannot carry drains until a plumbing layout is read. | high for completeness | read the plumbing / drainage drawing as a second source |
| O-5 | Host-wall structure is inferred: a drawn column frame gives MASONRY_INDICATED (not verified); a floor without a frame gives UNKNOWN. Nothing is read from the structural drawings. | high for door feasibility | bind the structural plan (route G already reads columns and walls) to classify host walls; until then every enlargement keeps its structural-engineer approval |
| O-6 | The 0.10 m minimum pier is an engine threshold, not an owner standard (shown as ENGINE_LIMITATION). | medium | owner value (question N-2) |
| O-7 | The cutting plan is first-fit decreasing over the per-area pieces; the piece set itself comes from each area's own best orientation. On both drawings the result is optimal for that piece set (villa: 6 rolls is forced by thirteen 2.80 m strips; reference plan: 14 rolls equals the area lower bound of 138.13 m2 / 10 m2), but orientations chosen jointly across areas are not explored. | low | a joint search only if a project shows a gap between rolls and the area bound |
| O-8 | A project rules file is not checked against the drawing (project id / drawing sha256): another project's file would be applied silently. | medium | require the drawing sha256 (or revision) in the rules file and refuse a mismatch |
| O-9 | Point-scoped project rules bind by a point; projects name rooms and doors by tags. | low | tag binding when a door / room schedule is read |
| O-10 | The exterior system path (balconies, roofs) is proved on synthetic plans only: the reference plan has no waterproofed exterior space in this drawing. | medium | a roof / balcony plan in the next validation set |

## 3. Objections to the rules (for the owner)

| # | Rule | Objection | Recommendation |
|---|---|---|---|
| R-1 | UP-WP-DOOR-001 | Without a standard doorway detail every wet-to-dry doorway is open (15 on the reference plan, 3 on the villa). The common Urban practice is probably one detail. | an Urban default doorway detail (question N-1); projects override it |
| R-2 | UP-WP-003 | One 0.20 m upturn everywhere; showers usually need a higher upturn or full-height membrane. The shower rule of the rule store (UP-WP-004 1.1.0) is still PROPOSED and was not promoted. | an owner decision on shower areas (question N-3) |
| R-3 | UP-WP-002 | "0.10 m at joints between adjacent strips" is applied to side and end laps alike; many sheet systems need a larger end lap. | confirm or split side / end lap (question N-4) |
| R-4 | UP-DOOR-HGT-001 | The candidate main entrance is a range 2.20 .. 2.50 m in every run until an entrance label exists. | nothing to change in the rule; ask for the entrance label per project |

## 4. What I would not change

- Withholding over guessing: every transition, termination, penetration and corner without a detail is listed with its
  range, never added to a confirmed total; a roll count is never CONFIRMED on the owner-standard roll alone.
- The four door views are never summed; the as-drawn BOQ lines did not move.
- The frozen methods: byte-identical; V2.4 is opt-in and deterministic.

## 5. Recommendations, in order

1. Read the structural plan for host walls (O-5) - it decides most of the door-feasibility approvals.
2. An Urban default doorway waterproofing detail (R-1) - closes the largest group of open waterproofing items.
3. A drainage / plumbing source for penetrations (O-4).
4. The window-threshold upturn as PROVISIONAL until the window type is known (O-1).
5. Project rules bound to the drawing hash (O-8).
6. Owner values for the pier threshold, shower upturn and end lap (O-6, R-2, R-3).

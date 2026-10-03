"""PA07R2 record: the guards, each tied to the review finding or gate question it answers, the test that reproduces it
and the P7757 delta; plus the annotated copies of the fresh cold review and its recommendations.

    python -m research.qs_wall_treatment_01.pa07.r2_guards
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR)
REVIEW_SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/claude-0/-home-user-Urban-Project-AI/93607c01-16a4-590f-af7c-1c2701c3b240/scratchpad/review2")

GUARDS = [
    {"ID": "R2-01", "ANSWERS": ["FM-R1-01"], "MODULE": "engine/cad_adapter.py (bulged LWPOLYLINE span)", "KIND": "DECODE_CORRECTNESS",
     "CHANGE": "a bulged span becomes the arc the author encoded: centre r*cos(theta/2) off the chord midpoint (left for a positive bulge), angles of the real endpoints; previously centre = chord midpoint, angles 0..theta",
     "SILENT_BEFORE": "curved walls drawn as bulged polylines produced no band and no seal; adjacent rooms merged into one ESTABLISHED space", "LOUD_OR_CORRECT_AFTER": "the true arcs pair into a curved band (correct)",
     "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_01_bulged_polyline_span_is_the_true_arc"},
    {"ID": "R2-02", "ANSWERS": ["FM-R1-01"], "MODULE": "engine/ingest/band_topology.py unresolved_seals", "KIND": "SEAL_RULE",
     "CHANGE": "an unpaired ARC of wall length whose ends lie in accepted band strips is an UNRESOLVED_CHORD like an unpaired line", "SILENT_BEFORE": "a curved face without its mate separated nothing",
     "LOUD_OR_CORRECT_AFTER": "the space beside it is BOUNDARY_PROVISIONAL", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_01_unpaired_wall_length_arc_is_an_unresolved_chord"},
    {"ID": "R2-03", "ANSWERS": ["FM-R1-02"], "MODULE": "engine/ingest/pipeline7.py stage_build_storeys / VIEW_ROLE gate", "KIND": "GATE_RULE",
     "CHANGE": "members of one copy family that carry the same storey name (or none) are DUPLICATE_PLAN_COPY: VIEW_ROLE HUMAN_REVIEW until the owner names distinct storeys", "SILENT_BEFORE": "every room measured once per plan copy (furniture / ceiling / electrical copies)",
     "LOUD_OR_CORRECT_AFTER": "no line from any copy; distinct owner storey names release both", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_02_duplicate_plan_copies_are_human_review_until_the_owner_picks_one"},
    {"ID": "R2-04", "ANSWERS": ["FM-R1-03", "FM-R1-13"], "MODULE": "engine/ingest/pipeline7.py _scale_evidence / SCALE_STATUS gate (new gate)", "KIND": "GATE_RULE",
     "CHANGE": "per plan view the median accepted wall thickness and the median confirmed door span are compared with the source-wide medians; a factor beyond 1.3 either way is HUMAN_REVIEW; a single plan view cannot be checked and says so",
     "SILENT_BEFORE": "an enlarged 2x detail in model space passed all nine gates at 2x", "LOUD_OR_CORRECT_AFTER": "the enlarged view (and, with only two views, both) is blocked",
     "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_03_enlarged_copy_at_2x_is_a_scale_question", "LIMIT": "cross-view only"},
    {"ID": "R2-05", "ANSWERS": ["FM-R1-04"], "MODULE": "engine/ingest/pipeline7.py stage_build_storeys", "KIND": "GATE_RULE",
     "CHANGE": "a storey name from floor words is HUMAN_REVIEW:CONFLICTING_FLOOR_WORDS when the view carries floor words of more than one storey", "SILENT_BEFORE": "two stair notes renamed the ground floor FIRST_FLOOR SOURCE_ESTABLISHED",
     "LOUD_OR_CORRECT_AFTER": "STOREY_STATUS blocks; the owner names the storey", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_04_conflicting_floor_words_in_one_view_block_the_storey",
     "NOTE": "storeys.py (PA06, frozen) untouched; the check is a PA07 post-condition"},
    {"ID": "R2-06", "ANSWERS": ["FM-R1-05"], "MODULE": "engine/ingest/material_bands.py THIN_BAND_MM", "KIND": "EVIDENCE_RULE",
     "CHANGE": "an accepted pair thinner than 150 mm without hatch or both end faces is UNRESOLVED THIN_BAND_UNCONFIRMED", "SILENT_BEFORE": "a 100 mm handrail pair with posts was an accepted wall and lengthened the corridor boundary",
     "LOUD_OR_CORRECT_AFTER": "corridor and void are BOUNDARY_PROVISIONAL", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_05_handrail_pair_with_posts_is_unresolved",
     "YIELD_COST": "genuine 100 mm partitions need hatch or both caps (test_06 updated)"},
    {"ID": "R2-07", "ANSWERS": ["FM-R1-06", "Q12"], "MODULE": "engine/ingest/material_bands.py phase 5 loops", "KIND": "EVIDENCE_RULE",
     "CHANGE": "a free-standing crossed / hatched closed outline is UNRESOLVED COLUMN_CANDIDATE (structural confirmation required); a loop touching an accepted straight band by a side or end follows it (column at a wall) unless its short side equals that band's thickness on its axis, which is UNRESOLVED WALL_NIB_OR_PIER",
     "SILENT_BEFORE": "floor traps / A/C / duct symbols and a door-side wall nib became COLUMN_BANDs and added column faces (the nib's face counted twice)", "LOUD_OR_CORRECT_AFTER": "no column face from a candidate; PA07_COLUMN_JUNCTION_REGISTER lists CANDIDATES_UNCONFIRMED",
     "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_06_free_standing_crossed_square_is_a_column_candidate_not_a_column, ::test_fm_r1_06b_wall_nib_between_cross_wall_and_jamb_is_not_a_column_and_nothing_is_double_counted",
     "YIELD_COST": "free-standing columns need the structural sheet (test_12, fm02, nested-column tests updated)"},
    {"ID": "R2-08", "ANSWERS": ["Q12"], "MODULE": "engine/ingest/material_bands.py phase 1c", "KIND": "EVIDENCE_RULE",
     "CHANGE": "a pair shorter along its axis than it is thick (not a loop) is UNRESOLVED SHORT_TRANSVERSE_PAIR", "SILENT_BEFORE": "a door jamb paired with a wall face (200 x 500) was an accepted band joined to the structure and demoted the 12 m wall beside it",
     "LOUD_OR_CORRECT_AFTER": "never accepted", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_q12b_short_transverse_pair_is_never_a_wall"},
    {"ID": "R2-09", "ANSWERS": ["FM-R1-07", "Q12"], "MODULE": "engine/ingest/pipeline7.py stage_build_quantity_safety / _bridge", "KIND": "LOUD_FAILURE_CONTAINMENT",
     "CHANGE": "COLUMN_FACE edges carry the column id as trace (never None); any exception inside the bridge becomes one line BLOCKED_BY BRIDGE_EXCEPTION, the run continues", "SILENT_BEFORE": "a TypeError killed the whole run for any room with an exposed column (loud, but every other space lost)",
     "LOUD_OR_CORRECT_AFTER": "one NOT_ESTABLISHED line, every other space reported", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_07_bridge_exception_is_one_loud_line_not_a_dead_run"},
    {"ID": "R2-10", "ANSWERS": ["FM-R1-08"], "MODULE": "engine/ingest/pipeline7.py stage_attach_semantics7 WET_LABEL_TOKENS", "KIND": "GATE_RULE",
     "CHANGE": "a room label carrying a wet-room word whose class is not a wet class ('MASTER BATH' -> MASTER_BEDROOM) makes the identity UNRESOLVED (HUMAN_REVIEW)", "SILENT_BEFORE": "MASTER BATH plastered as a bedroom at full height, no wet line",
     "LOUD_OR_CORRECT_AFTER": "IDENTITY_STATUS blocks", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_08_wet_word_in_a_dry_class_label_is_ambiguous", "NOTE": "semantics.py (PA06, frozen) untouched"},
    {"ID": "R2-11", "ANSWERS": ["FM-R1-09"], "MODULE": "engine/ingest/band_topology.py classify_gap", "KIND": "EVIDENCE_RULE",
     "CHANGE": "a swing arc together with >= 2 frame lines in the gap is UNRESOLVED DOOR_OR_WINDOW_CONFLICT", "SILENT_BEFORE": "a casement window with a swing arc was a CONFIRMED_DOOR and deducted at door height with door reveals",
     "LOUD_OR_CORRECT_AFTER": "OPENING_SITE_STATUS blocks", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_09_swing_with_frame_lines_is_a_door_window_conflict"},
    {"ID": "R2-12", "ANSWERS": ["FM-R1-10"], "MODULE": "engine/ingest/planar_faces.py boundary_faces", "KIND": "LENGTH_BASIS_CORRECTNESS",
     "CHANGE": "a curved face run is scaled by (R +- t/2) / R: the face radius, not the axis", "SILENT_BEFORE": "+3.5 % on a semicircular majlis wall, all gates passing",
     "LOUD_OR_CORRECT_AFTER": "correct within 20 mm (test tolerance tightened from 1 % + 60 mm)", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_fm_r1_10_curved_face_length_uses_the_face_radius, tests/test_pa07_spaces.py::test_curved_room_boundary_is_developed_length"},
    {"ID": "R2-13", "ANSWERS": ["FM-R1-11"], "MODULE": "engine/ingest/band_topology.py UNEVIDENCED_BREAK_MM", "KIND": "EVIDENCE_RULE",
     "CHANGE": "MATERIAL_CONTINUITY only below 250 mm; a both-face break of 250..500 mm with nothing drawn in it is UNRESOLVED UNEVIDENCED_BREAK (zero material, provisional)", "SILENT_BEFORE": "a 450 mm serving hatch was booked as plastered wall on both sides",
     "LOUD_OR_CORRECT_AFTER": "both rooms BOUNDARY_PROVISIONAL", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07_topology.py::test_tiny_gap_and_short_break_are_not_openings"},
    {"ID": "R2-14", "ANSWERS": ["Q03"], "MODULE": "engine/ingest/planar_faces.py space_register", "KIND": "CONSISTENCY_RULE",
     "CHANGE": "GEOMETRY_STATUS is BOUNDARY_PROVISIONAL whenever the boundary composition carries an UNRESOLVED_CHORD, whatever the raster status says", "SILENT_BEFORE": "the continuous-face side of a single-face gap was ESTABLISHED with UNRESOLVED_MM 900 (blocked only by the site gate)",
     "LOUD_OR_CORRECT_AFTER": "both sides provisional", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_q03_unresolved_chord_makes_the_space_provisional_on_both_sides"},
    {"ID": "R2-15", "ANSWERS": ["Q10"], "MODULE": "engine/ingest/pipeline7.py SPACE_CLASS", "KIND": "GATE_RULE",
     "CHANGE": "a cell whose every room label is an exterior class (GARDEN, COURT, ROOF, POOL, BALCONY, TERRACE) is EXTERIOR_LABELLED: SPACE_STATUS HUMAN_REVIEW", "SILENT_BEFORE": "a walled GARDEN was INTERIOR / SINGLE (blocked only by the height gate)",
     "LOUD_OR_CORRECT_AFTER": "SPACE_STATUS blocks", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_q10_exterior_class_label_is_not_an_interior_room"},
    {"ID": "R2-16", "ANSWERS": ["Q11"], "MODULE": "engine/ingest/pipeline7.py _unlabelled_neighbours / SPACE_STATUS", "KIND": "GATE_RULE",
     "CHANGE": "a labelled space separated from an unlabelled eligible cell by an accepted band with no fill evidence and no opening is SPACE_STATUS HUMAN_REVIEW", "SILENT_BEFORE": "a beam drawn with continuous lines split a room; the labelled half was measured at 15.7 m instead of 20.0 m",
     "LOUD_OR_CORRECT_AFTER": "the labelled half is HUMAN_REVIEW; two labelled halves are two rooms", "INVENTS_GEOMETRY": False, "REINTERPRETS_SOURCE": False, "TEST": "tests/test_pa07r2_guards.py::test_q11_unlabelled_cell_across_an_unevidenced_band_is_human_review",
     "LIMIT": "band level cannot tell a continuous-line beam from a partition; PA08 source acceptance now records BEAM_CONVENTION (beam layer / hidden linetype present or absent)"},
]

FINDING_STATUS = {"FM-R1-01": ("FIXED_PA07R2", ["R2-01", "R2-02"]), "FM-R1-02": ("GUARDED_PA07R2", ["R2-03"]), "FM-R1-03": ("GUARDED_PA07R2", ["R2-04"]), "FM-R1-04": ("GUARDED_PA07R2", ["R2-05"]),
                  "FM-R1-05": ("GUARDED_PA07R2", ["R2-06"]), "FM-R1-06": ("GUARDED_PA07R2", ["R2-07", "R2-08"]), "FM-R1-07": ("FIXED_PA07R2", ["R2-09"]), "FM-R1-08": ("GUARDED_PA07R2", ["R2-10"]),
                  "FM-R1-09": ("GUARDED_PA07R2", ["R2-11"]), "FM-R1-10": ("FIXED_PA07R2", ["R2-12"]), "FM-R1-11": ("GUARDED_PA07R2", ["R2-13"]),
                  "FM-R1-12": ("RECORDED_PA09", ["provenance key BAND_DEVELOPED_GEOMETRY in plaster_trade_engine; gates_v3 leak filter vacuous"]),
                  "FM-R1-13": ("PARTIALLY_GUARDED_PA07R2", ["R2-03", "R2-04", "gate v3 conditions themselves unchanged; PA08 gate v4 reads the registers"]),
                  "FM-R1-14": ("RECORDED_PA09", ["reveal ownership per opening vs per side; wet rooms' NORMAL line: owner rule declarations"]),
                  "FM-R1-15": ("RECORDED_PA09", ["loud already; out-of-range pairs (> 600) should appear as UNRESOLVED rows"]),
                  "FM-R1-16": ("RECORDED_PA09", ["text alignment point and extent from the decode; anchor near a barrier -> HUMAN_REVIEW"]),
                  "FM-R1-17": ("NO_CHANGE_REQUIRED", []), "FM-R1-18": ("RECORDED_PA09", ["yield: double leaves, window frames without roles, counters; not safety"])}


def main():
    (OUT / "pa07r1").mkdir(parents=True, exist_ok=True); (OUT / "pa07r2").mkdir(parents=True, exist_ok=True)
    review = json.loads((REVIEW_SRC / "PA07R1_COLD_REVIEW.json").read_text("utf-8"))
    for f in review["FINDINGS"]:
        st, refs = FINDING_STATUS.get(f["FINDING_ID"], ("OPEN", []))
        f["STATUS"] = st; f["PA07R2_REFERENCES"] = refs
    review["POST_REVIEW_ANNOTATION"] = {"BY": "engine author, after PA07R2", "STATUS_VALUES": ["FIXED_PA07R2", "GUARDED_PA07R2", "PARTIALLY_GUARDED_PA07R2", "RECORDED_PA09", "NO_CHANGE_REQUIRED", "OPEN"],
                                        "FINDINGS_UNTOUCHED": "the reviewer's text is unchanged; only STATUS and PA07R2_REFERENCES were added",
                                        "COUNTS": {k: sum(1 for f in review["FINDINGS"] if f["STATUS"] == k) for k in ("FIXED_PA07R2", "GUARDED_PA07R2", "PARTIALLY_GUARDED_PA07R2", "RECORDED_PA09", "NO_CHANGE_REQUIRED", "OPEN")}}
    (OUT / "pa07r1" / "PA07R1_COLD_REVIEW.json").write_text(json.dumps(review, indent=1, ensure_ascii=False), "utf-8")
    shutil.copyfile(REVIEW_SRC / "PA07R1_COLD_REVIEW_RECOMMENDATIONS.json", OUT / "pa07r1" / "PA07R1_COLD_REVIEW_RECOMMENDATIONS.json")
    gate_r1 = json.loads((OUT / "pa07r1" / "PA07R1_POST_REVIEW_GATE.json").read_text("utf-8"))
    gate_r2 = json.loads((OUT / "pa07r2" / "PA07R1_POST_REVIEW_GATE.json").read_text("utf-8"))
    rec = {"ARTIFACT": "PA07R2_GUARDS", "REVISION": "PA07R2", "BASE": "PA07R1 (frozen; FREEZE_PA07R1.json)", "RULE": "no rewrite of PA07R1: sixteen guards / corrections, each a counterexample that ended silent or dead in PA07R1 and ends loud or correct in PA07R2",
           "GUARDS": GUARDS, "COUNT": len(GUARDS), "TESTS": "tests/test_pa07r2_guards.py (17) + four PA07R1 tests updated with the R2 rationale",
           "FINDING_STATUS": {k: {"STATUS": v[0], "REFERENCES": v[1]} for k, v in FINDING_STATUS.items()},
           "POST_REVIEW_GATE": {"PA07R1": gate_r1["COUNTS"], "PA07R2": gate_r2["COUNTS"], "PA07R1_FAILED": [q["ID"] for q in gate_r1["QUESTIONS"] if q["STATUS"] != "PASS"], "PA07R2_FAILED": [q["ID"] for q in gate_r2["QUESTIONS"] if q["STATUS"] != "PASS"]},
           "PA06_FROZEN_MODULES_UNTOUCHED": ["primitive_roles.py", "semantics.py", "storeys.py", "pipeline.py", "source_units.py", "harness.py"],
           "P7757_TUNING": "none: no P7757 geometry, label or constant was consulted; the P7757 rerun is a regression delta (PA07R2_P7757_DELTA.json)"}
    (OUT / "pa07r2" / "PA07R2_GUARDS.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), "utf-8")
    print(json.dumps(review["POST_REVIEW_ANNOTATION"]["COUNTS"]), rec["POST_REVIEW_GATE"])


if __name__ == "__main__":
    main()

"""A blind pass receives the drawing, and the contract says so in code.

The test this protects is: CAN THE AGENT SEE THE DRAWING. An agent that
retrieves a previously worked-out answer passes that test for the wrong
reason and nobody can tell from the number.
"""

from __future__ import annotations

import json

import pytest

from engine import blind_input_contract as bic


def _image(tmp_path, name="page-01.jpeg"):
    p = tmp_path / "images" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\xff\xd8\xff\xe0 not really a jpeg, but bytes to hash")
    return p


def _run():
    return bic.BlindRun(run_id="R1", subject="the open zone")


# ------------------------------------------------------- the allowed set

def test_a_page_of_the_drawing_passes_every_gate(tmp_path):
    run = _run()
    d = run.offer(bic.Input(input_id="IMG-01",
                            kind=bic.SOURCE_DRAWING_IMAGE,
                            what_it_is="page 1", path=str(_image(tmp_path))))
    assert d.admitted
    assert d.gates_passed == bic.GATES
    assert d.identity["RAW_FILE_SHA256"]


def test_every_admitted_input_carries_a_hash(tmp_path):
    run = _run()
    run.offer(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))))
    run.offer(bic.Input(input_id="META-01", kind=bic.SHEET_METADATA,
                        content={"page_count": 10}))
    for row in run.manifest()["inputs_made_available"]:
        assert row.get("RAW_FILE_SHA256") or row.get(
            "CANONICAL_CONTENT_SHA256"), row


# ------------------------------------------------------------ the gates

def test_an_undeclared_kind_is_refused_rather_than_let_through(tmp_path):
    run = _run()
    d = run.offer(bic.Input(input_id="X", kind="SOMETHING_NEW",
                            path=str(_image(tmp_path))))
    assert not d.admitted
    assert d.refused_by == bic.KIND_GATE
    assert d.would_be == "AN_UNDECLARED_KIND"


def test_a_prohibited_kind_is_refused_by_name(tmp_path):
    run = _run()
    for kind in bic.PROHIBITED_KINDS:
        d = run.offer(bic.Input(input_id=f"X-{kind}", kind=kind,
                                path=str(_image(tmp_path))))
        assert d.refused_by == bic.KIND_GATE
        assert d.would_be == kind


def test_the_allowed_and_prohibited_kinds_do_not_overlap():
    assert not set(bic.ALLOWED_KINDS) & set(bic.PROHIBITED_KINDS)


def test_relabelling_a_reconciliation_file_does_not_get_it_through():
    run = _run()
    d = run.offer(bic.Input(
        input_id="X", kind=bic.SHEET_METADATA,
        path="data/runs/7757/reconciliation/P7757_OPEN_ZONE.json"))
    assert d.refused_by == bic.PATH_GATE
    assert d.would_be == bic.RECONCILIATION_FILE


def test_the_sealed_take_off_is_refused_and_never_opened():
    run = _run()
    d = run.offer(bic.Input(
        input_id="X", kind=bic.SOURCE_DRAWING_IMAGE,
        path="data/golden/7757/sealed/P7757_area_takeoff_benchmark.pdf"))
    assert d.refused_by == bic.PATH_GATE
    # refused before the content gate, which is the gate that would read it
    assert bic.CONTENT_GATE not in d.gates_passed


def test_the_drawing_itself_is_not_caught_by_the_path_gate():
    assert bic.check_path(
        "data/golden/7757/inputs/P7757_DRAWINGS.pdf") == ("", "")
    assert bic.check_path(
        "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg") == ("", "")


def test_a_previous_answer_is_caught_only_where_it_is_writing():
    kind, _ = bic.check_path("data/runs/7757/round6e_export/REPORT.json")
    assert kind == bic.PREVIOUS_AGENT_ANSWER
    # a picture rendered from a sheet is not somebody's answer
    assert bic.check_path("data/runs/7757/round6e_export/sheet.png")[0] == ""


def test_content_carrying_the_answer_is_refused():
    run = _run()
    d = run.offer(bic.Input(input_id="META-01", kind=bic.SHEET_METADATA,
                            content={"pages": 10,
                                     "expected_area_m2": 137.5}))
    assert d.refused_by == bic.CONTENT_GATE
    assert d.would_be == bic.KNOWN_TARGET_AREA


def test_a_missing_file_is_refused_because_it_was_not_supplied():
    run = _run()
    d = run.offer(bic.Input(input_id="IMG-01",
                            kind=bic.SOURCE_DRAWING_IMAGE,
                            path="nowhere/page-99.png"))
    assert d.refused_by == bic.EXISTS_GATE


# -------------------------------------------------------------- the crops

def test_a_crop_without_a_basis_is_refused(tmp_path):
    run = _run()
    d = run.offer(bic.Input(input_id="CROP-01", kind=bic.LOCAL_CROP,
                            path=str(_image(tmp_path, "crop.png")),
                            derived_from="IMG-01"))
    assert d.refused_by == bic.CROP_BASIS_GATE


def test_a_crop_drawn_around_a_known_target_is_refused(tmp_path):
    run = _run()
    d = run.offer(bic.Input(input_id="CROP-01", kind=bic.LOCAL_CROP,
                            path=str(_image(tmp_path, "crop.png")),
                            derived_from="IMG-01",
                            crop_basis=bic.CROP_FROM_A_TARGET,
                            crop_box_px=(10, 10, 90, 90)))
    assert d.refused_by == bic.CROP_BASIS_GATE
    assert d.would_be == bic.KNOWN_TARGET_AREA


def test_a_tiled_crop_is_admitted_and_says_what_decided_its_box(tmp_path):
    run = _run()
    d = run.offer(bic.Input(input_id="CROP-01", kind=bic.LOCAL_CROP,
                            path=str(_image(tmp_path, "crop.png")),
                            derived_from="IMG-01",
                            crop_basis=bic.CROP_FROM_SHEET_TILING,
                            crop_box_px=(0, 0, 100, 100)))
    assert d.admitted
    assert d.identity["crop_basis"] == bic.CROP_FROM_SHEET_TILING
    assert d.identity["crop_box_px"] == [0, 0, 100, 100]


def test_an_image_inherits_what_it_was_rendered_from(tmp_path):
    run = _run()
    d = run.offer(bic.Input(
        input_id="IMG-01", kind=bic.WHOLE_FLOOR_IMAGE,
        path=str(_image(tmp_path)),
        origin="data/golden/7757/sealed/P7757_area_takeoff_benchmark.pdf"))
    assert d.refused_by == bic.PATH_GATE


# ------------------------------------------- refusal versus contamination

def test_a_refusal_at_the_door_leaves_the_run_valid(tmp_path):
    run = _run()
    run.offer(bic.Input(input_id="X", kind=bic.SHEET_METADATA,
                        path="data/runs/7757/reconciliation/x.json"))
    assert run.status == bic.VALID
    assert not run.stopped
    run.offer(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))))
    assert len(run.admitted) == 1


def test_information_found_in_the_context_invalidates_and_stops(tmp_path):
    run = _run()
    run.in_context(what=bic.KNOWN_TARGET_AREA, where="the prompt",
                   detail="a human total was pasted in")
    assert run.status == bic.INVALID
    assert run.stopped
    with pytest.raises(bic.BlindTestInvalid):
        run.offer(bic.Input(input_id="IMG-01",
                            kind=bic.SOURCE_DRAWING_IMAGE,
                            path=str(_image(tmp_path))))


def test_checking_the_assembled_context_catches_a_leak():
    run = _run()
    assert run.check_context({"ask": "read the ground floor and measure it"})
    assert run.status == bic.VALID
    assert not run.check_context({"note": "the human excel total is 137.5"},
                                 where="turn 3")
    assert run.status == bic.INVALID
    assert run.violations[-1]["where"] == "turn 3"


def test_the_manifest_of_an_invalid_run_says_so(tmp_path):
    run = _run()
    run.offer(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))))
    run.in_context(what=bic.PRIOR_CORRECTED_GEOMETRY, where="turn 2")
    man = run.manifest()
    assert man["status"] == bic.INVALID
    assert man["run_stopped"] is True
    assert man["counts"]["in_context_violations"] == 1


# ------------------------------------------------------- the projections

def test_a_projection_is_a_whitelist():
    got = bic.project({"a": 1, "b": 2, "a_new_field_nobody_expected": 3},
                      ("a", "b"))
    assert got == {"a": 1, "b": 2}


def test_the_general_rules_projection_drops_a_leaky_rule():
    library = {"library": "L", "library_version": "1",
               "notes": {"x": "the benchmark is 137.5"},
               "rules": [
                   {"rule_id": "UP-A", "rule_name": "a skirting is 100mm",
                    "scope": "SKIRTING", "notes": "fine"},
                   {"rule_id": "UP-B", "rule_name": "compare to the "
                    "expected area", "scope": "ALL"}]}
    out = bic.general_rules(library)
    assert [r["rule_id"] for r in out["rules"]] == ["UP-A"]
    assert out["withheld_rule_ids"] == ["UP-B"]
    # and the projection itself must survive the content gate
    run = _run()
    assert run.offer(bic.Input(input_id="RULES-01", kind=bic.GENERAL_RULE,
                               content=out)).admitted


def test_the_real_rule_library_projects_cleanly():
    library = json.loads(open(
        "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json",
        encoding="utf-8").read())
    out = bic.general_rules(library)
    assert out["rules"], "a blind pass gets the general rules"
    run = _run()
    assert run.offer(bic.Input(input_id="RULES-01", kind=bic.GENERAL_RULE,
                               content=out)).admitted


def test_a_spec_about_the_space_under_test_is_withheld():
    spec = {"stair": {"finish": "MARBLE"},
            "pantry": {"openness": "OPEN_AMERICAN_PANTRY"}}
    out = bic.spec_for_a_blind_pass(spec, subject_terms=("PANTRY",))
    assert "stair" in out and "pantry" not in out
    assert out["withheld_block_ids"] == ["pantry"]


def test_a_spec_about_other_spaces_stays():
    spec = {"stair": {"finish": "MARBLE"}, "elevator": {"surround_m": 0.5}}
    out = bic.spec_for_a_blind_pass(spec, subject_terms=("PANTRY",))
    assert out["withheld_block_ids"] == []
    assert out["stair"]["finish"] == "MARBLE"


# ---------------------------------------------------------- the manifest

def test_the_manifest_hash_follows_the_inputs(tmp_path):
    def build(name):
        run = _run()
        run.offer(bic.Input(input_id="IMG-01",
                            kind=bic.SOURCE_DRAWING_IMAGE,
                            path=str(_image(tmp_path, name))))
        return run.manifest()

    one, two = build("a.jpeg"), build("a.jpeg")
    assert one["MANIFEST_HASH"] == two["MANIFEST_HASH"]
    (tmp_path / "images" / "b.jpeg").write_bytes(b"different bytes here")
    assert build("b.jpeg")["MANIFEST_HASH"] != one["MANIFEST_HASH"]


def test_the_manifest_records_what_was_refused_as_well_as_what_was_given(
        tmp_path):
    run = _run()
    run.offer(bic.Input(input_id="IMG-01", kind=bic.SOURCE_DRAWING_IMAGE,
                        path=str(_image(tmp_path))))
    run.offer(bic.Input(input_id="X", kind=bic.SHEET_METADATA,
                        path="data/runs/7757/reconciliation/x.json"))
    man = run.manifest()
    assert man["counts"] == {"offered": 2, "admitted": 1,
                             "refused_at_the_door": 1,
                             "in_context_violations": 0}
    assert man["refused_at_the_door"][0]["it_would_have_been"] == (
        bic.RECONCILIATION_FILE)
    assert man["contract"]["ALLOWED_KINDS"] == list(bic.ALLOWED_KINDS)


def test_the_model_hash_moves_with_the_contract():
    assert len(bic.model_hash()) == 24
    assert bic.frozen_parameters()["MODEL"] == bic.MODEL

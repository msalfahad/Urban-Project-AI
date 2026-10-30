"""T-365 JOINT_SCOPE_V1 on a hand-calculated fixture villa K365 (not Alsenan): normal cases with the hand calculation in
the docstrings, then adverse cases (borrowed spacing, hatch as a joint, double count, held 0, missing source, units,
mirror / rotation, an ambiguous exact spacing, a drawn joint without its type)."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t365"))
import joints_scope_v1 as R  # noqa: E402

# Villa K365 (fixture): a structural movement joint drawn on the K365 ground-floor plan from (0, 0) to (0, 12 000) mm,
# type printed '20 mm filler + sealant both faces'; roof 14.00 x 9.00 m with a printed note 'movement joints not
# exceeding 4.50 m both ways', type '10 mm joint, sealant top face'; court paving 12.00 x 7.50 m 'joints at 3.00 m c/c'.
EJ = {"id": "K-EJ1", "kind": "STRUCTURAL_MOVEMENT", "trade": "structural", "line": "K.STR.JOINT",
      "position": {"source_kind": "DRAWN_LINE", "source": "K365 S-02 handle 4A1",
                   "segments": [{"p0": [0, 0], "p1": [0, 12000], "unit": "mm"}]},
      "type": {"source": "K365 S-09 detail 3", "sealed_faces": 2}}
ROOF = {"id": "K-RF1", "kind": "ROOF_FIELD", "trade": "roofing", "line": "K.ROOF.JOINT",
        "position": {"source_kind": "PRINTED_SPACING", "source": "K365 A-11 note 6",
                     "field": {"source": "K365 A-05 roof outline handle 7C", "Lx": 14.0, "Ly": 9.0, "unit": "m",
                               "spacing": {"source_kind": "PRINTED_SPACING", "source": "K365 A-11 note 6",
                                           "kind": "MAX", "value": 4.5, "unit": "m"}}},
        "type": {"source": "K365 A-11 detail 2", "sealed_faces": 1}}
PAVE = {"id": "K-PV1", "kind": "PAVING", "trade": "external works", "line": "K.EXT.JOINT",
        "position": {"source_kind": "PRINTED_SPACING", "source": "K365 A-12 note 2",
                     "field": {"source": "K365 A-03 court outline handle 91", "Lx": 12.0, "Ly": 7.5, "unit": "m",
                               "spacing": {"source_kind": "PRINTED_SPACING", "source": "K365 A-12 note 2",
                                           "kind": "EXACT", "value": 3.0, "unit": "m"}}},
        "type": {"source": "K365 A-12 detail 1", "sealed_faces": 1}}


def test_drawn_structural_joint_and_both_face_sealant():
    """12 000 mm drawn = 12.000 m; sealant both faces = 2 x 12.000 = 24.000 m."""
    r = R.evaluate(EJ)
    assert r["status"] == R.MEASURED and r["length_m"] == 12.0 and r["sealant_m"] == 24.0 and r["rfi"] is None


def test_roof_field_max_spacing_by_hand():
    """x: ceil(14.0 / 4.5) - 1 = 3 joints x 9.0 = 27.0; y: ceil(9.0 / 4.5) - 1 = 1 joint x 14.0 = 14.0; total 41.0 m."""
    r = R.evaluate(ROOF)
    assert r["status"] == R.MEASURED and r["length_m"] == 41.0 and r["sealant_m"] == 41.0


def test_exact_spacing_that_does_not_fit_is_held_not_rounded():
    """x: 12.0 / 3.0 = 4 -> 3 joints, but y: 7.5 / 3.0 = 2.5 is not whole: the layout is not fixed -> HELD, None."""
    r = R.evaluate(PAVE)
    assert r["status"] == R.HELD and r["length_m"] is None and r["sealant_m"] is None
    ok = copy.deepcopy(PAVE)
    ok["position"]["field"]["Ly"] = 9.0  # 9.0 / 3.0 = 3 -> 2 joints x 12.0 = 24.0; x 3 joints x 9.0 = 27.0; 51.0
    assert R.evaluate(ok)["length_m"] == 51.0


def test_interior_count_notation():
    assert R.interior_count(9.0, 4.5, "MAX") == 1 and R.interior_count(9.1, 4.5, "MAX") == 2
    assert R.interior_count(4.0, 4.5, "MAX") == 0
    assert R.interior_count(9.0, 4.5, "EXACT") == 1 and R.interior_count(9.0005, 4.5, "EXACT") == 1
    assert R.interior_count(9.1, 4.5, "EXACT") is None and R.interior_count(9.0, None, "UNSTATED") is None


def test_owner_width_only_is_held_never_zero():
    j = {"id": "K-TF1", "kind": "TILE_FIELD", "trade": "finishes", "owner_rule": {"id": "Q-42", "width_mm": 3}}
    r = R.evaluate(j)
    assert r["status"] == R.HELD and r["length_m"] is None and "Q-42" in r["why"]


def test_nothing_printed_is_not_in_drawn_scope_with_none():
    r = R.evaluate({"id": "K-SG1", "kind": "SLAB_ON_GRADE", "trade": "structural", "evidence": "S-03: none"})
    assert r["status"] == R.NOT_IN_DRAWN_SCOPE and r["length_m"] is None and r["sealant_m"] is None and r["rfi"] is None


def test_evaluate_all_totals_only_measured():
    out = R.evaluate_all([EJ, ROOF, PAVE, {"id": "K-X", "kind": "PARAPET", "trade": "structural"}])
    assert out["by_status"] == {"MEASURED": 2, "HELD": 1, "NOT_IN_DRAWN_SCOPE": 1}
    assert out["measured_total_m"] == 53.0 and out["rfi"] == []


# ---------------------------------------------------------------- adverse
@pytest.mark.parametrize("bad", ["TEXTBOOK", "PICTURE", "TYPICAL", "FREELANCER", "ENGINE_DEFAULT", "HATCH"])
def test_borrowed_spacing_or_position_refused(bad):
    j = copy.deepcopy(ROOF)
    j["position"]["field"]["spacing"]["source_kind"] = bad
    with pytest.raises(R.JointError):
        R.evaluate(j)
    j2 = copy.deepcopy(EJ)
    j2["position"]["source_kind"] = bad
    with pytest.raises(R.JointError):
        R.evaluate(j2)


def test_textbook_spacing_on_an_unprinted_joint_refused_not_held():
    """A '5 - 6 m typical' spacing (the Q-42 picture) never turns an unprinted joint into a quantity or a hold."""
    with pytest.raises(R.JointError):
        R.evaluate({"id": "K-RF2", "kind": "ROOF_FIELD", "trade": "roofing", "spacing_from": "PICTURE",
                    "owner_rule": {"id": "Q-42", "width_mm": 3}})


def test_hatch_is_never_a_joint():
    assert R.classify_hatch({"handle": "D1A", "pattern": "LINE"})["class"] == "HATCH_NOT_JOINT"
    j = copy.deepcopy(EJ)
    j["position"]["source_kind"] = "HATCH"
    with pytest.raises(R.JointError):
        R.evaluate(j)


def test_same_joint_on_paving_and_screed_lines_is_double_count():
    a = copy.deepcopy(EJ)
    a.update(id="K-J-PAVE", kind="PAVING", trade="external works", line="K.EXT.JOINT")
    b = copy.deepcopy(EJ)
    b.update(id="K-J-SCRD", kind="ROOF_FIELD", trade="roofing", line="K.ROOF.SCREED")
    b["position"]["segments"] = [{"p0": [0, 12.0], "p1": [0, 0], "unit": "m"}]  # reversed, metres: same segment
    with pytest.raises(R.JointError, match="DOUBLE_COUNT"):
        R.evaluate_all([a, b])


def test_held_written_as_zero_refused():
    with pytest.raises(R.JointError):
        R.evaluate({"id": "K-0", "kind": "TILE_FIELD", "trade": "finishes", "quantity_m": 0,
                    "owner_rule": {"id": "Q-42"}})


def test_missing_sources_refused():
    j = copy.deepcopy(EJ)
    j["position"]["source"] = ""
    with pytest.raises(R.JointError):
        R.evaluate(j)
    k = copy.deepcopy(ROOF)
    k["position"]["field"]["source"] = None
    with pytest.raises(R.JointError):
        R.evaluate(k)


def test_drawn_joint_without_type_raises_rfi_and_holds_sealant():
    j = copy.deepcopy(EJ)
    del j["type"]
    r = R.evaluate(j)
    assert r["status"] == R.MEASURED and r["length_m"] == 12.0 and r["sealant_m"] is None and "K-EJ1" in r["rfi"]


def test_units_mm_cm_m_agree_and_unknown_unit_refused():
    j = copy.deepcopy(EJ)
    j["position"]["segments"] = [{"p0": [0, 0], "p1": [0, 1200], "unit": "cm"}]
    assert R.evaluate(j)["length_m"] == 12.0
    k = copy.deepcopy(ROOF)
    k["position"]["field"].update(Lx=14000, Ly=9000, unit="mm")
    k["position"]["field"]["spacing"].update(value=4500, unit="mm")
    assert R.evaluate(k)["length_m"] == 41.0
    j["position"]["segments"][0]["unit"] = "in"
    with pytest.raises(R.JointError):
        R.evaluate(j)


def test_mirror_and_rotation_invariant():
    base = R.evaluate(EJ)["length_m"]
    for f in ((lambda x, y: (-x, y)), (lambda x, y: (-y, x)), (lambda x, y: (y, -x))):
        j = copy.deepcopy(EJ)
        s = j["position"]["segments"][0]
        s["p0"], s["p1"] = list(f(*s["p0"])), list(f(*s["p1"]))
        assert R.evaluate(j)["length_m"] == base
    k = copy.deepcopy(ROOF)
    k["position"]["field"].update(Lx=9.0, Ly=14.0)  # rotated field: same 41.0 m
    assert R.evaluate(k)["length_m"] == 41.0


def test_unknown_kind_refused():
    with pytest.raises(R.JointError):
        R.evaluate({"id": "K-?", "kind": "CRACK", "trade": "x"})

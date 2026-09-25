"""PA02: level identity, column faces, trade matrix, arch areas, kerb profile."""

import math

import pytest

from engine import column_faces as CF
from engine import level_identity as LI
from engine import wall_treatment_matrix as WTM


def test_level_identity_keeps_two_bases_without_selecting():
    slab = LI.level(9.70, "s", "SOURCE_ESTABLISHED")
    fin = LI.level(9.88, "f", "PROVISIONAL")
    top = LI.level(11.10, "t", "SOURCE_ESTABLISHED")
    a = LI.face_candidate(basis="CONTRACTOR_EXECUTED_WORK_BASIS", bottom=slab, top=top, length_m=2.0, length_source="ESTABLISHED_FROM_DWG")
    b = LI.face_candidate(basis="ENGINEERING_VISIBLE_FINISH_BASIS", bottom=fin, top=top, length_m=2.0, length_source="ESTABLISHED_FROM_DWG")
    assert a["HEIGHT"] == 1.4 and b["HEIGHT"] == 1.22
    assert a["QUANTITY_STATE"] == "SOURCE_ESTABLISHED_QUANTITY" and b["QUANTITY_STATE"] == "PROVISIONAL_QUANTITY"
    d = LI.dual(candidates=[a, b], exhausted_sources=[{"SOURCE": "x", "EXHAUSTED": False}], identity_open="y")
    assert d["OWNER_A_B_QUESTION_ALLOWED"] is False and d["CANDIDATES"][0]["NEITHER_CANDIDATE_IS_SELECTED"]
    with pytest.raises(ValueError):
        LI.level_set(STRUCTURAL_SLAB_LEVEL=slab)


def test_column_exposed_girth_differs_from_structural_girth():
    c = CF.column(column_id="C", width_m=0.30, depth_m=0.60, exposures={"A": "EXPOSED", "B": "BURIED_IN_WALL", "C": "EXPOSED", "D": "FLUSH_WITH_WALL_FACE"},
                  host_wall_relation="x", bonding_required=True, plaster_required=True, source="PROVISIONAL", exposure_source="PROVISIONAL")
    assert c["STRUCTURAL_GIRTH_LM"] == 1.8 and c["EXPOSED_PLASTERABLE_GIRTH_LM"] == 0.6
    with pytest.raises(ValueError):
        CF.column(column_id="C", width_m=0.3, depth_m=0.6, exposures={"A": "EXPOSED"}, host_wall_relation="x", bonding_required=True,
                  plaster_required=True, source="PROVISIONAL", exposure_source="PROVISIONAL")


def test_sequential_treatments_count_one_physical_area():
    t = WTM.treatment_lines(face_id="F", physical_area_m2=5.76, area_state="PROVISIONAL_QUANTITY", face_kind="EXPOSED_COLUMN_FACE")
    assert [x["TREATMENT"] for x in t["TREATMENTS"]] == ["COLUMN_BONDING", "NORMAL_INTERNAL_PLASTER"]
    assert t["PHYSICAL_AREA_M2"] == 5.76 and t["PHYSICAL_AREA_COUNTED_ONCE"]
    u = WTM.treatment_lines(face_id="E", physical_area_m2=10.0, area_state="PROVISIONAL_QUANTITY", face_kind="EXTERNAL_FACE", finish_status="UNKNOWN_EXTERNAL_FINISH")
    assert u["TREATMENTS"][0]["TREATMENT"] == "UNKNOWN" and u["TREATMENTS"][0]["VALUE"] is None


def test_arch_area_is_rectangle_plus_semicircle_not_bounding_box():
    from research.qs_wall_treatment_01.pa02_roof_edges_facade import arch_area
    a = arch_area(1.20, 1.10)
    assert abs(a["ARCH_M2"] - math.pi * 0.36 / 2) < 1e-3
    assert a["AREA_M2"] < 1.20 * 1.70 and a["BOUNDING_BOX_USED"] is False
    s = arch_area(2.0, 1.0, "SEGMENT", rise_m=0.5)
    assert 0 < s["ARCH_M2"] < 2.0 * 0.5


def test_wet_room_area_not_established_without_treatment_height():
    import json
    from pathlib import Path
    p = Path("data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/TRADES_WET_OPENINGS_FLOORS_COVERAGE.json")
    if not p.exists():
        pytest.skip("artifact not present")
    w = json.loads(p.read_text("utf-8"))["WET_ROOM_REGISTER"]
    assert w["AREA_M2"] is None and all(r["AREA_STATE"] == "NOT_ESTABLISHED" for r in w["ROOMS"])
    assert all(r["TREATMENT"] == "TILE_WALL_PREPARATION" for r in w["ROOMS"])

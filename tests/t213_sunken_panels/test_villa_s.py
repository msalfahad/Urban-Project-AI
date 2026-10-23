"""T-213 hand fixture villa T213-S (not the development villa). Hand truth:

L panel 'L1' (slab sheet GF -> 1F floor): (0,0) (3,0) (3,1.2) (1.5,1.2) (1.5,2.5) (0,2.5)
    A = 3 x 1.2 + 1.5 x 1.3 = 5.55 m2, P = 3 + 1.2 + 1.5 + 1.3 + 1.5 + 2.5 = 11.00 m
Rectangle 'R1' across a 0.25 m beam: x 3.25 .. 5.65, y 0 .. 1.8 -> A = 4.32 m2, P = 8.40 m
    the beam faces L1 only over y 0 .. 1.2: P_shared = 1.20 m on each side
    P_ext(L1) = 11.00 - 1.20 = 9.80 m, P_ext(R1) = 8.40 - 1.20 = 7.20 m
t = 0.16 printed: concrete L1 = 0.888 m3, R1 = 0.6912 m3 (independent of d)
d printed 0.25 (fixture only): riser L1 = 9.80 x 0.25 = 2.45 m2; fill L1 = 5.55 x 0.25 = 1.3875 m3;
    beam side adjustment = -2.45 m2; net formwork change 0
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t213"))
import sunken_panels as S  # noqa: E402

L_PTS = [(0, 0), (3, 0), (3, 1.2), (1.5, 1.2), (1.5, 2.5), (0, 2.5)]
R_PTS = [(3.25, 0), (5.65, 0), (5.65, 1.8), (3.25, 1.8)]


def _panels(tf=lambda p: p):
    L = S.build_panel("L1", "GF", [[tf(p) for p in L_PTS]])
    R = S.build_panel("R1", "GF", [[tf(p) for p in R_PTS]])
    return L, R


def test_areas_perimeters_by_hand():
    L, R = _panels()
    assert L.area == pytest.approx(5.55, abs=1e-9) and L.perimeter == pytest.approx(11.0, abs=1e-9)
    assert R.area == pytest.approx(4.32, abs=1e-9) and R.perimeter == pytest.approx(8.4, abs=1e-9)
    assert L.area_status == R.area_status == "DRAWING-CONFIRMED"


def test_shared_edge_only_where_the_beam_faces_the_other_panel():
    e = S.classify_edges(list(_panels()), max_beam_m=0.30)
    assert e["L1"]["P_shared"] == pytest.approx(1.2, abs=1e-6) and e["L1"]["P_ext"] == pytest.approx(9.8, abs=1e-6)
    assert e["R1"]["P_shared"] == pytest.approx(1.2, abs=1e-6) and e["R1"]["P_ext"] == pytest.approx(7.2, abs=1e-6)
    assert e["L1"]["gap_m"]["R1"] == pytest.approx(0.25)


def test_beam_wider_than_probe_is_external_not_shared():
    e = S.classify_edges(list(_panels()), max_beam_m=0.20)
    assert e["L1"]["P_shared"] == 0 and e["L1"]["P_ext"] == pytest.approx(11.0)


@pytest.mark.parametrize("name,tf", [
    ("mirror", lambda p: (-p[0], p[1])),
    ("rotate 37 deg", lambda p: (p[0] * math.cos(0.6458) - p[1] * math.sin(0.6458),
                                 p[0] * math.sin(0.6458) + p[1] * math.cos(0.6458))),
    ("translate", lambda p: (p[0] + 1234.5, p[1] - 77.25)),
])
def test_mirror_rotation_translation_same_quantities(name, tf):
    L, R = _panels(tf)
    e = S.classify_edges([L, R], max_beam_m=0.30)
    assert L.area == pytest.approx(5.55, abs=1e-6) and R.area == pytest.approx(4.32, abs=1e-6)
    assert e["L1"]["P_shared"] == pytest.approx(1.2, abs=1e-3) and e["R1"]["P_ext"] == pytest.approx(7.2, abs=1e-3)


def test_drop_missing_is_held_never_zero():
    L, R = _panels()
    e = S.classify_edges([L, R], max_beam_m=0.30)
    q = S.panel_quantities(L, e["L1"], t_m=0.16, t_source="fixture note")
    assert q["slab_concrete_m3"]["value"] == pytest.approx(0.888)
    for k in ("step_riser_form_m2", "beam_side_form_adjust_m2", "shared_edge_riser_m2", "fill_buildup_m3_laneA",
              "waterproof_upturn_m2_laneA", "ceiling_below_level_drop_m"):
        assert q[k]["value"] is None and q[k]["status"] == "HELD" and "drop d" in q[k]["missing"], k
    assert "9.8000 x d" in q["step_riser_form_m2"]["formula"]
    assert q["net_formwork_change_m2"]["value"] == 0.0


def test_printed_drop_gives_hand_values():
    L, R = _panels()
    e = S.classify_edges([L, R], max_beam_m=0.30)
    q = S.panel_quantities(L, e["L1"], t_m=0.16, t_source="fixture note", d_m=0.25, d_source="fixture section X-X")
    assert q["step_riser_form_m2"]["value"] == pytest.approx(2.45)
    assert q["beam_side_form_adjust_m2"]["value"] == pytest.approx(-2.45)
    assert q["fill_buildup_m3_laneA"]["value"] == pytest.approx(1.3875)
    assert q["slab_concrete_m3"]["value"] == pytest.approx(0.888)        # the drop does not change the volume
    assert q["shared_edge_riser_m2"]["status"] == "HELD"                  # depends on the shared beam's top


@pytest.mark.parametrize("kw", [dict(d_m=0.25), dict(d_m=0.0, d_source="x"), dict(t_m=0.16)])
def test_unsourced_or_zero_values_refused(kw):
    L, R = _panels()
    e = S.classify_edges([L, R])
    with pytest.raises(S.PanelError):
        S.panel_quantities(L, e["L1"], **kw)


def test_no_thickness_printed_concrete_held():
    L, R = _panels()
    q = S.panel_quantities(L, S.classify_edges([L, R])["L1"])
    assert q["slab_concrete_m3"]["value"] is None and q["slab_concrete_m3"]["status"] == "HELD"


def test_annotation_island_not_deducted_unexplained_void_held():
    label = [(0.3, 0.3), (0.9, 0.3), (0.9, 0.6), (0.3, 0.6)]        # text box 0.18 m2 inside L1
    P1 = S.build_panel("L1", "GF", [L_PTS, label], annotations=[(0.32, 0.35, 0.85, 0.55, "5d10/m")])
    assert P1.area == pytest.approx(5.55) and P1.area_status == "DRAWING-CONFIRMED"
    assert P1.annotation_islands == [(0.18, "5d10/m")]
    P2 = S.build_panel("L1", "GF", [L_PTS, label], annotations=[])
    assert P2.area == pytest.approx(5.55) and P2.area_status == "HELD" and P2.unexplained_voids == [0.18]
    P3 = S.build_panel("L1", "GF", [L_PTS, label], annotations=[(0.5, 0.4, "INSERT:tag")])   # point anchor
    assert P3.area_status == "DRAWING-CONFIRMED"


def test_hatch_split_by_annotation_arc_is_one_panel():
    a = [(0, 0), (2, 0), (2, 1), (1.5, 1), (1.0, 0.5), (0.5, 1), (0, 1)]   # split along a polyline 'arc'
    b = [(0.5, 1), (1.0, 0.5), (1.5, 1)]
    P = S.build_panel("X", "1F", [a, b])
    assert P.area == pytest.approx(2.0) and P.region_loops == 2 and P.perimeter == pytest.approx(6.0)


def test_loop_apart_from_panel_refused():
    with pytest.raises(S.PanelError):
        S.build_panel("X", "GF", [R_PTS, [(10, 10), (11, 10), (11, 11), (10, 11)]])


def test_storey_conventions_and_matching():
    assert S.floor_carried("GF") == "1F" and S.floor_carried("1F") == "2F"
    pairs, ua, ub = S.match_sets({"GF-001": 5.55, "GF-002": 4.32}, {"h2": 4.32, "h1": 5.5512})
    assert [(a, b) for a, b, *_ in pairs] == [("GF-001", "h1"), ("GF-002", "h2")] and not ua and not ub
    pairs, ua, ub = S.match_sets({"GF-001": 5.55}, {"h1": 5.72})                # 3 % apart: never forced
    assert not pairs and ua == ["GF-001"] and ub == ["h1"]
    with pytest.raises(S.PanelError):
        S.floor_carried("4F")


def test_beam_projection_condition():
    assert S.beam_projection_check(0.75, 0.16, None)["status"] == "HELD"
    assert S.beam_projection_check(0.75, 0.16, 0.25)["projection_m"] == pytest.approx(0.34)
    assert S.beam_projection_check(0.50, 0.16, 0.40)["status"] == "BEAM DEPTH CONFLICT"


def test_step_concrete_inside_beams_or_held():
    L, R = _panels()
    e = S.classify_edges([L, R], max_beam_m=0.30)["L1"]
    q = S.panel_quantities(L, e, t_m=0.16, t_source="note", edges_on_beams="fixture: every edge on a beam face")
    assert q["step_concrete_extra_m3"]["value"] == 0.0 and q["step_concrete_extra_m3"]["status"] == "DRAWING-CONFIRMED"
    q = S.panel_quantities(L, e, t_m=0.16, t_source="note")                       # edge support unknown
    assert q["step_concrete_extra_m3"]["value"] is None and q["step_concrete_extra_m3"]["status"] == "HELD"
    q = S.panel_quantities(L, e, t_m=0.16, t_source="note", d_m=0.25, d_source="fixture X-X")
    assert q["step_concrete_extra_m3"]["value"] == pytest.approx(9.8 * 0.25 * 0.16)
    assert q["step_concrete_extra_m3"]["status"] == "HELD"

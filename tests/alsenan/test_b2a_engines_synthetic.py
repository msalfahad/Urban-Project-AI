"""Phase B2A generic engines - synthetic known-answer tests (no project value, no benchmark value).

Engines: beam_binding (BEAM_BINDING_V2), structural_vertical (STRUCTURAL_VERTICAL_INTERVAL_V1), concrete_model
(PHYSICAL_CONCRETE_MODEL_V1 + STAIR_CONCRETE_V1), slab_region (SLAB_REGION_V1), opening_authority, curved_opening,
finish_height, waterproofing_policy, urban_methods.
"""

import ast
import json
import math
from pathlib import Path

import pytest

from engine.source import beam_binding as BB
from engine.source import concrete_model as CM
from engine.source import curved_opening as CO
from engine.source import finish_height as FH
from engine.source import opening_authority as OA
from engine.source import slab_region as SR
from engine.source import structural_schedule as SS
from engine.source import structural_vertical as SV
from engine.source import urban_methods as UM
from engine.source import waterproofing_policy as WP

ROOT = Path(__file__).resolve().parents[2]
LIBS = {"SIMPLE": {"B1": {"B_cm": 25, "D_cm": 45}, "B2": {"B_cm": 25, "D_cm": 60}, "B9": {"B_cm": 30, "D_cm": 90}},
        "CONTINUOUS": {"CB1": {"B_cm": 40, "D_cm": 80}}, "STRAP": {"SB1": {"B_cm": 60, "D_cm": 55}}}


def seg(k, x1, y1, x2, y2):
    return (k, float(x1), float(y1), float(x2), float(y2))


def band_h(prefix, y0, width, x0, x1):
    return [seg(prefix + "a", x0, y0, x1, y0), seg(prefix + "b", x0, y0 + width, x1, y0 + width)]


def mark(key, value, x, y, rot=0.0, h=200.0):
    return {"key": key, "value": value, "type": value, "x": x, "y": y, "rotation_deg": rot, "height": h}


def bind(marks, segs, **kw):
    return BB.bind(marks, LIBS, BB.merge_lines(segs, eps=1.0), segs, umm=1.0, tol_mm=10.0, eps=1.0, **kw)


# ------------------------------------------------------------------ namespaces (B vs CB)
def test_b_lookup_returns_simple_b1_and_cb_lookup_returns_continuous_cb1():
    assert BB.lookup(LIBS, "B1") == {"B_cm": 25, "D_cm": 45}
    assert BB.lookup(LIBS, "CB1") == {"B_cm": 40, "D_cm": 80}
    assert BB.namespace("B1") == "SIMPLE" and BB.namespace("CB1") == "CONTINUOUS" and BB.namespace("SB1") == "STRAP"


def test_no_normalisation_strips_the_c_of_cb():
    only_simple = {"SIMPLE": {"B1": {"B_cm": 25, "D_cm": 45}}}
    assert BB.lookup(only_simple, "CB1") is None
    for v in ("CB1", "C B1", "C.B1"):
        assert SS.parse_mark(v, ["B1"], normalise=True)["types"] == []
        assert SS.parse_mark(v, ["B1", "CB1"], normalise=True)["types"] == ["CB1"]


def test_namespace_audit_flags_misfiled_and_collisions():
    bad = {"SIMPLE": {"CB1": {}}, "CONTINUOUS": {"CB1": {}}}
    a = BB.namespace_audit(bad)
    assert a["state"] == "FAIL" and a["misfiled"] and a["collisions"]
    assert BB.namespace_audit(BB.split_library({"B1": {}, "CB1": {}, "SB1": {}, "CA": {}}))["state"] == "PASS"


def test_same_band_under_b_and_cb_gives_different_column_heights():
    interval = SV.storey_intervals([{"name": "L0", "level_m": 0.0, "kind": "FFL"}, {"name": "L1", "level_m": 3.6, "kind": "FFL"}])[0]
    for t, D in (("B1", 45), ("CB1", 80)):
        ctrl = SV.controlling_member([{"id": "m", "polygon": [], "bound": True, "type": t, "D_cm": BB.lookup(LIBS, t)["D_cm"]}],
                                     LIBS, tol_mm=10.0)
        r = SV.column_interval(B_cm=25, D_cm_col=40, interval=interval, control=ctrl, slab_thickness_cm=14)
        assert r["height_m"] == pytest.approx(3.6 - D / 100.0)


# ------------------------------------------------------------------ beam binding
def test_tag_beside_band_binds_uniquely():
    segs = band_h("A", 0, 250, 0, 5000)
    r = bind([mark("t1", "B1", 2000, 300)], segs)[0]
    assert r["state"] == BB.BOUND and r["drawn_breadth_mm"] == 250.0


def test_tag_between_two_scheduled_bands_is_ambiguous_not_nearest():
    segs = band_h("A", 0, 250, 0, 5000) + band_h("C", 640, 250, 0, 5000)
    r = bind([mark("t1", "B1", 2000, 300)], segs)[0]
    assert r["state"] == BB.AMBIGUOUS


def test_wrong_breadth_band_does_not_bind():
    segs = band_h("A", 0, 300, 0, 5000)                     # 300 drawn, B1 scheduled 250 (20 % off)
    assert bind([mark("t1", "B1", 2000, 350)], segs)[0]["state"] == BB.NO_BREADTH


def test_width_deviation_within_policy_binds_with_deviation():
    segs = band_h("A", 0, 262, 0, 5000)                     # 4.8 % wider (beyond the 10 mm tolerance)
    r = bind([mark("t1", "B1", 2000, 310)], segs)[0]
    assert r["state"] == BB.BOUND_DEV and r["width_deviation_mm"] == pytest.approx(12.0)


def test_orientation_must_match_the_tag_baseline():
    segs = band_h("A", 0, 250, 0, 5000)
    assert bind([mark("t1", "B1", 2000, 300, rot=90.0)], segs)[0]["state"] == BB.NO_PARALLEL


def test_far_tag_does_not_bind_and_intervening_line_blocks():
    segs = band_h("A", 0, 250, 0, 5000)
    assert bind([mark("t1", "B1", 2000, 1500)], segs)[0]["state"] == BB.NOT_ADJACENT
    segs2 = segs + [seg("W", 0, 300, 5000, 300)]            # a line between tag and band
    r = bind([mark("t1", "B1", 2000, 320)], segs2)[0]
    assert r["state"] != BB.BOUND


def test_tag_inside_wide_band_binds():
    segs = band_h("A", 0, 300, 0, 5000)
    r = bind([mark("t1", "B9", 2000, 50)], segs)[0]
    assert r["state"] == BB.BOUND and r["tag_overlaps_band"]


def test_four_length_bases_are_stored_apart():
    segs = band_h("A", 0, 250, 0, 6000)
    cols = [{"id": "C1", "polygon": [(-300, -100), (300, -100), (300, 350), (-300, 350)]},
            {"id": "C2", "polygon": [(5700, -100), (6300, -100), (6300, 350), (5700, 350)]}]
    r = bind([mark("t1", "B1", 2500, 300)], segs)
    occ = BB.occurrences(r, segs, umm=1.0, eps=1.0, max_support_mm=1000, columns=cols)["occurrences"][0]
    L = occ["lengths"]
    assert occ["state"] == "MEASURED"
    assert L["CLEAR_FACE_TO_FACE_LENGTH"] == pytest.approx(5.4)
    assert L["SUPPORT_CENTRELINE_LENGTH"] == pytest.approx(6.0)
    assert L["PLAN_DRAWN_EXTENT"] == pytest.approx(6.0)
    assert L["SCHEDULE_SPAN_LENGTH"] is None


def test_continuous_beam_publishes_schedule_spans_beside_measured_length():
    segs = band_h("A", 0, 400, 0, 9000)
    cols = [{"id": f"C{i}", "polygon": [(x - 200, -100), (x + 200, -100), (x + 200, 500), (x - 200, 500)]} for i, x in
            enumerate((0, 4500, 9000))]
    r = bind([mark("t1", "CB1", 2000, 450), mark("t2", "CB1", 6500, 450)], segs)
    o = BB.occurrences(r, segs, umm=1.0, eps=1.0, max_support_mm=1000, columns=cols,
                       schedule_spans={"CB1": [4.7, 4.7]})["occurrences"][0]
    assert o["lengths"]["CLEAR_FACE_TO_FACE_LENGTH"] == pytest.approx(8.2)
    assert o["lengths"]["SCHEDULE_SPAN_LENGTH"] == pytest.approx(9.4)
    assert o["segments_between_supports"] == 2


def test_two_types_on_one_segment_is_a_band_type_conflict():
    segs = band_h("A", 0, 250, 0, 5000)
    r = bind([mark("t1", "B1", 1000, 300), mark("t2", "B2", 3000, -250)], segs)
    states = {o["type"]: o["state"] for o in BB.occurrences(r, segs, umm=1.0, eps=1.0, max_support_mm=1000)["occurrences"]}
    assert states == {"B1": "BAND_TYPE_CONFLICT", "B2": "BAND_TYPE_CONFLICT"}


# ------------------------------------------------------------------ vertical interval
SQ_COL = [(0, 0), (300, 0), (300, 300), (0, 300)]


def test_column_height_uses_the_deepest_framing_member_only():
    members = [{"id": "a", "polygon": [(-2000, 50), (0, 50), (0, 250), (-2000, 250)], "bound": True, "type": "B1", "D_cm": 45},
               {"id": "b", "polygon": [(50, 300), (250, 300), (250, 3000), (50, 3000)], "bound": True, "type": "B2", "D_cm": 60},
               {"id": "far", "polygon": [(5000, 0), (6000, 0), (6000, 200), (5000, 200)], "bound": True, "type": "B9", "D_cm": 90}]
    fr = SV.framing_members(SQ_COL, members, eps=1.0)
    assert sorted(m["id"] for m in fr) == ["a", "b"]
    c = SV.controlling_member(fr, LIBS, tol_mm=10.0)
    assert c["state"] == SV.PROVEN and c["D_cm"] == 60


def test_unbound_member_dominated_or_blocking():
    bound = {"id": "a", "polygon": [], "bound": True, "type": "B9", "D_cm": 90}
    unb = {"id": "u", "polygon": [], "bound": False, "drawn_breadth_mm": 250.0}
    assert SV.controlling_member([bound, unb], LIBS, tol_mm=10.0)["state"] == SV.DOMINATED
    weak = {"id": "a", "polygon": [], "bound": True, "type": "B1", "D_cm": 45}
    r = SV.controlling_member([weak, unb], LIBS, tol_mm=10.0)
    assert r["state"] == SV.BLOCK_UNBOUND and r["could_reach_cm"] == 60
    odd = {"id": "u", "polygon": [], "bound": False, "drawn_breadth_mm": 333.0}
    assert SV.controlling_member([bound, odd], LIBS, tol_mm=10.0)["state"] == SV.BLOCK_UNSCHED


def test_slab_only_column_and_joint_partition():
    iv = {"interval_m": 3.3, "authority": SV.FFL_INTERVAL}
    c = SV.controlling_member([], LIBS, tol_mm=10.0, slab_thickness_cm=17)
    r = SV.column_interval(B_cm=30, D_cm_col=30, interval=iv, control=c, slab_thickness_cm=17)
    assert c["state"] == SV.SLAB and r["height_m"] == pytest.approx(3.13) and r["joint_m3"] == 0.0
    c2 = {"state": SV.PROVEN, "D_cm": 60, "member": "B2"}
    r2 = SV.column_interval(B_cm=30, D_cm_col=30, interval=iv, control=c2, slab_thickness_cm=17)
    assert r2["volume_m3"] + r2["joint_m3"] == pytest.approx(0.09 * (3.3 - 0.17))


def test_interval_authority_and_neck_blocked():
    ivs = SV.storey_intervals([{"name": "A", "level_m": 0.4, "kind": "FFL"}, {"name": "B", "level_m": 3.9, "kind": "FFL"}])
    assert ivs[0]["authority"] == SV.FFL_INTERVAL and ivs[0]["assumption"]
    ivs2 = SV.storey_intervals([{"name": "A", "level_m": 0.2, "kind": "STRUCTURAL_TOP"}, {"name": "B", "level_m": 3.5, "kind": "STRUCTURAL_TOP"}])
    assert ivs2[0]["authority"] == SV.STRUCTURAL_LEVEL
    assert SV.neck(footing_top_m=None, upper_start_m=0.6, B_cm=30, D_cm=30)["state"] == "BLOCKED_HEIGHT"
    assert SV.neck(footing_top_m=-0.9, upper_start_m=0.1, B_cm=30, D_cm=40)["volume_m3"] == pytest.approx(0.12)


def test_no_unbound_column_without_framing_or_slab():
    assert SV.controlling_member([], LIBS, tol_mm=10.0)["state"] == SV.BLOCK_TERM


# ------------------------------------------------------------------ physical concrete model
def test_physical_model_never_double_counts_and_gross_view_is_separate():
    m = CM.physical_model(slab={"net_area_m2": 20.0, "t_cm": 15},
                          beams=[{"id": "b1", "length_m": 4.0, "B_cm": 25, "D_cm": 55}],
                          joints=[{"id": "j", "volume_m3": 0.036}], columns=[{"id": "c", "volume_m3": 0.27}])
    assert m["by_component_m3"]["SLAB"] == pytest.approx(3.0)
    assert m["by_component_m3"]["DOWNSTAND_BEAM"] == pytest.approx(4.0 * 0.25 * 0.40)
    assert m["total_state"] == "COMPLETE"
    g = CM.gross_beam_view([{"id": "b1", "length_m": 4.0, "B_cm": 25, "D_cm": 55}])
    assert g[0]["volume_m3"] == pytest.approx(0.55) and m["computed_total_m3"] == pytest.approx(3.0 + 0.4 + 0.036 + 0.27)


def test_printed_thickness_keeps_downstands_when_the_outline_is_blocked():
    m = CM.physical_model(slab={"blocked": "SLAB_OUTLINE_NOT_ESTABLISHED", "t_cm": 15},
                          beams=[{"id": "b", "length_m": 3.0, "B_cm": 20, "D_cm": 50}])
    assert m["by_component_m3"] == {"DOWNSTAND_BEAM": pytest.approx(0.21)} and m["total_state"].startswith("PARTIAL")


def test_blocked_components_never_enter_the_total():
    m = CM.physical_model(slab={"blocked": "SLAB_OUTLINE_NOT_ESTABLISHED"},
                          beams=[{"id": "b", "length_m": 3.0, "B_cm": 20, "D_cm": 50}])
    assert m["computed_total_m3"] == 0.0 and m["total_state"].startswith("PARTIAL") and len(m["blocked"]) == 2


def F(rc, tc, R=0.17, G=0.28, W=1.1, t=0.14, **kw):
    return dict({"riser_count": rc, "tread_count": tc, "riser_height_m": R, "tread_going_m": G, "flight_width_m": W,
                 "waist_thickness_m": t}, **kw)


def flight_volume(rc, tc, R, G, W, t):
    return math.hypot(rc * R, tc * G) * W * t + 0.5 * R * G * W * tc


def test_stair_A_20_risers_19_treads():
    s = CM.stair(flights=[F(20, 19)])
    f = s["flights"][0]
    assert s["state"] == "COMPUTED" and f["vertical_rise_m"] == pytest.approx(3.4) and f["horizontal_run_m"] == pytest.approx(5.32)
    assert s["volume_m3"] == pytest.approx(flight_volume(20, 19, 0.17, 0.28, 1.1, 0.14))


def test_stair_B_10_risers_10_treads():
    s = CM.stair(flights=[F(10, 10)])
    assert s["volume_m3"] == pytest.approx(flight_volume(10, 10, 0.17, 0.28, 1.1, 0.14))


def test_stair_C_tread_count_missing_blocks():
    s = CM.stair(flights=[F(20, None)])
    assert s["state"] == "BLOCKED_INPUT_MISSING" and s["missing"] == ["flight 1: tread_count"] and s["volume_m3"] is None


def test_stair_D_riser_count_missing_blocks():
    s = CM.stair(flights=[F(None, 19)])
    assert s["state"] == "BLOCKED_INPUT_MISSING" and s["missing"] == ["flight 1: riser_count"]


def test_stair_E_two_flights_with_different_counts():
    s = CM.stair(flights=[F(11, 10), F(9, 8, W=1.2)])
    assert [(f["riser_count"], f["tread_count"]) for f in s["flights"]] == [(11, 10), (9, 8)]
    assert s["volume_m3"] == pytest.approx(flight_volume(11, 10, 0.17, 0.28, 1.1, 0.14) + flight_volume(9, 8, 0.17, 0.28, 1.2, 0.14))


def test_stair_F_flight_and_landing():
    s = CM.stair(flights=[F(10, 9)], landings=[{"area_m2": 1.21, "thickness_m": 0.14}])
    assert s["volume_m3"] == pytest.approx(flight_volume(10, 9, 0.17, 0.28, 1.1, 0.14) + 1.21 * 0.14)
    b = CM.stair(flights=[F(10, 9)], landings=[{"area_m2": 1.21, "thickness_m": None}])
    assert b["state"] == "BLOCKED_INPUT_MISSING" and b["missing"] == ["landing 1: thickness_m"]


def test_stair_G_missing_waist_blocks():
    s = CM.stair(flights=[F(10, 9, t=None)])
    assert s["state"] == "BLOCKED_INPUT_MISSING" and s["missing"] == ["flight 1: waist_thickness_m"]


def test_stair_old_implicit_equality_can_no_longer_occur():
    old_schema = {"risers": 10, "riser_m": 0.17, "going_m": 0.28, "width_m": 1.1, "waist_m": 0.14}
    assert CM.stair(flights=[old_schema])["state"] == "BLOCKED_INPUT_MISSING"     # no tread count -> no volume
    a, b = CM.stair(flights=[F(10, 9)]), CM.stair(flights=[F(10, 10)])
    assert a["volume_m3"] != b["volume_m3"] and a["flights"][0]["horizontal_run_m"] == pytest.approx(9 * 0.28)
    cand = CM.stair(flights=[F(10, 9, authority={"tread_count": "CANDIDATE"})])
    assert cand["state"] == "BLOCKED_INPUT_MISSING"                                 # a candidate count is not an input
    rel = CM.stair(flights=[F(10, None, tread_relation="SOURCE_ESTABLISHED: tread_count = riser_count - 1")])
    assert rel["flights"][0]["tread_count"] == 9
    assert CM.stair(flights=[F(10, None, tread_relation="ASSUMED")])["state"] == "BLOCKED_INPUT_MISSING"
    assert CM.STAIR_POLICY_ID == "STAIR_CONCRETE_V2"


# ------------------------------------------------------------------ slab regions
def _grid(w, h, step):
    s = [seg(f"h{i}", 0, y, w, y) for i, y in enumerate(range(0, h + 1, step))]
    s += [seg(f"v{i}", x, 0, x, h) for i, x in enumerate(range(0, w + 1, step))]
    return s


def test_rectangular_slab_net_area():
    r = SR.regions(segments=_grid(4000, 3000, 1000), band_points=[("b", 500, 500)],
                   thickness_tags=[{"t_cm": 15, "x": 1500, "y": 1500}])
    assert r["closure"] == "CLOSED" and r["net_plate_area_m2"] == pytest.approx(12.0)
    assert r["volume_m3"] == pytest.approx(1.8)


def test_void_and_stair_openings_are_deducted():
    stair = [seg(f"s{i}", 2100 + 200 * i, 1050, 2100 + 200 * i, 1950) for i in range(4)]
    cross = [seg("x1", 1000, 0, 2000, 1000), seg("x2", 1000, 1000, 2000, 0)]
    r = SR.regions(segments=_grid(4000, 3000, 1000), void_labels=[(500, 2500)], opening_segments=cross,
                   stair_segments=stair, band_points=[("b", 3500, 500)], thickness_tags=[{"t_cm": 15, "x": 3500, "y": 2500}])
    assert r["counts"]["OPENING_VOID"] == 2 and r["counts"]["OPENING_STAIR"] == 1
    assert r["net_plate_area_m2"] == pytest.approx(9.0)


def test_irregular_slab_and_unclosed_perimeter_blocks():
    L = [seg("a", 0, 0, 4000, 0), seg("b", 4000, 0, 4000, 2000), seg("c", 4000, 2000, 2000, 2000),
         seg("d", 2000, 2000, 2000, 4000), seg("e", 2000, 4000, 0, 4000), seg("f", 0, 4000, 0, 0)]
    r = SR.regions(segments=L, band_points=[("b", 500, 500)], thickness_tags=[{"t_cm": 12, "x": 500, "y": 500}])
    assert r["net_plate_area_m2"] == pytest.approx(12.0)
    open_L = L[:-1]
    r2 = SR.regions(segments=open_L, band_points=[("b", 500, 500)], thickness_tags=[{"t_cm": 12, "x": 500, "y": 500}])
    assert r2["closure"] == "SLAB_OUTLINE_NOT_ESTABLISHED" and r2["volume_m3"] is None


def test_overlapping_faces_are_counted_once_and_thickness_conflict_blocks():
    r = SR.regions(segments=_grid(2000, 1000, 1000) + [seg("dup", 0, 0, 2000, 0)], band_points=[("b", 500, 500)],
                   thickness_tags=[{"t_cm": 15, "x": 500, "y": 500}, {"t_cm": 20, "x": 1500, "y": 500}])
    assert r["net_plate_area_m2"] == pytest.approx(2.0)
    assert r["thickness_states"] == {"PRINTED_IN_FACE": 2} and r["volume_m3"] == pytest.approx(0.35)
    r2 = SR.regions(segments=_grid(3000, 1000, 1000), band_points=[("b", 500, 500)],
                    thickness_tags=[{"t_cm": 15, "x": 500, "y": 500}, {"t_cm": 20, "x": 1500, "y": 500}])
    assert r2["volume_state"] == "BLOCKED" and "SHEET_TAGS_DIFFER" in r2["thickness_states"]


def test_detail_drawn_beside_the_plan_is_excluded():
    detail = [seg("d1", 9000, 0, 9500, 0), seg("d2", 9500, 0, 9500, 500), seg("d3", 9500, 500, 9000, 500), seg("d4", 9000, 500, 9000, 0)]
    r = SR.regions(segments=_grid(2000, 1000, 1000) + detail, band_points=[("b", 500, 500)],
                   thickness_tags=[{"t_cm": 15, "x": 500, "y": 500}])
    assert r["detail_regions_excluded"] == 1 and r["net_plate_area_m2"] == pytest.approx(2.0)


# ------------------------------------------------------------------ openings
def test_door_swing_gives_door_and_ambiguous_glazing_is_unknown():
    d = OA.classify({"id": "o1", "glazing": True, "door_evidence": ["swing arc"], "previous_function": "WINDOW"})
    assert d["function"] == OA.DOOR and d["function_change"] == "FUNCTION_CHANGE"
    w = OA.classify({"id": "o3", "glazing": True})
    assert w["function"] == OA.WINDOW
    a = OA.classify({"id": "o4", "glazing": True, "ambiguity": ["joins two interior spaces"], "previous_function": "WINDOW"})
    assert a["function"] == OA.UNKNOWN and a["function"] != "WINDOW" and a["function_change"] == "FUNCTION_DEMOTION"


def test_swing_closing_on_the_opening_is_door_evidence():
    arc = {"cx": 0.0, "cy": 0.0, "r": 900.0, "a0": 0.0, "a1": math.pi / 2}
    assert OA.swing_closes_on_opening(arc, (0.0, 0.0), (900.0, 0.0), end_tol=60.0)
    assert OA.swing_closes_on_opening(arc, (0.0, 0.0), (0.0, 900.0), end_tol=60.0)
    assert not OA.swing_closes_on_opening(arc, (0.0, 0.0), (1400.0, 0.0), end_tol=60.0)
    assert not OA.swing_closes_on_opening(arc, (2000.0, 0.0), (2900.0, 0.0), end_tol=60.0)


def test_height_hierarchy_and_no_fallback_for_unknown():
    c = [{"authority": "PROJECT_OWNER_FACT", "value_m": 2.4, "ref": "of"},
         {"authority": "SOURCE_DIMENSION", "value_m": 2.2, "ref": "dim"},
         {"authority": "URBAN_FALLBACK_BY_TYPE", "value_m": 2.1, "method_id": "M@v1"}]
    r = OA.resolve_height(c, function=OA.WINDOW)
    assert r["authority"] == "SOURCE_DIMENSION" and r["height_m"] == 2.2
    only_fb = [{"authority": "URBAN_FALLBACK_BY_TYPE", "value_m": 2.1, "method_id": "M@v1"}]
    assert OA.resolve_height(only_fb, function=OA.UNKNOWN)["state"] == "BLOCKED_HEIGHT"
    assert OA.resolve_height(only_fb, function=OA.WINDOW)["height_m"] == 2.1


# ------------------------------------------------------------------ curved
def test_curved_explicit_bases_aliases_and_min_radius_default():
    arcs = [{"cx": 0, "cy": 0, "r": r, "sweep_rad": math.pi / 3} for r in (2000.0, 2050.0, 2100.0)]
    b = CO.bases(arcs)
    assert b["MIN_RADIUS_ARC"] == pytest.approx(2000 * math.pi / 3, abs=1e-3)
    assert b["MID_BAND_ARC"] == pytest.approx(2050 * math.pi / 3, abs=1e-3)
    assert b["MAX_RADIUS_ARC"] == pytest.approx(2100 * math.pi / 3, abs=1e-3)
    assert b["CHORD"] == pytest.approx(2000.0, abs=1e-3)
    assert (b["INNER"], b["CENTRE"], b["OUTER"]) == (b["MIN_RADIUS_ARC"], b["MID_BAND_ARC"], b["MAX_RADIUS_ARC"])
    assert CO.BASES == ("MIN_RADIUS_ARC", "MID_BAND_ARC", "MAX_RADIUS_ARC", "CHORD")
    c = CO.commercial(b)
    assert c["basis"] == "MIN_RADIUS_ARC" and c["length_mm"] == b["MIN_RADIUS_ARC"]
    assert c["orientation"]["state"] == "NOT_ESTABLISHED"
    assert CO.commercial(b, override={"id": "P1", "basis": "MAX_RADIUS"})["length_mm"] == b["MAX_RADIUS_ARC"]
    assert CO.bases(arcs + [{"cx": 30, "cy": 0, "r": 2200.0, "sweep_rad": math.pi / 3}])["state"] == "NOT_CONCENTRIC"
    cut = [{"cx": 0, "cy": 0, "r": 2000.0, "sweep_rad": 1.0}, {"cx": 0, "cy": 0, "r": 2100.0, "sweep_rad": 0.97}]
    bc = CO.bases(cut)                                       # straight jambs: sweeps differ, centre shared
    assert bc["MIN_RADIUS_ARC"] == pytest.approx(2000.0) and bc["MAX_RADIUS_ARC"] == pytest.approx(2037.0)
    assert bc["MID_BAND_ARC"] == pytest.approx(2018.5)


def test_room_side_is_never_assumed_to_be_min_radius():
    b = CO.bases([{"cx": 0, "cy": 0, "r": r, "sweep_rad": 1.0} for r in (2000.0, 2100.0)])
    assert CO.orient(b)["state"] == "NOT_ESTABLISHED"
    o = CO.orient(b, "MAX_RADIUS")                           # a curve bulging into the room
    assert o["ROOM_SIDE_ARC"] == b["MAX_RADIUS_ARC"] and o["EXTERIOR_SIDE_ARC"] == b["MIN_RADIUS_ARC"]
    assert CO.commercial(b, override={"id": "P2", "basis": "ROOM_SIDE"})["state"] == "BLOCKED"
    r = CO.commercial(b, override={"id": "P2", "basis": "ROOM_SIDE"}, room_side="MAX_RADIUS")
    assert r["basis"] == "ROOM_SIDE_ARC" and r["length_mm"] == b["MAX_RADIUS_ARC"]
    assert CO.commercial(b, room_side="MAX_RADIUS")["basis"] == "MIN_RADIUS_ARC"   # default names the geometry
    with pytest.raises(ValueError):
        CO.commercial(b, override={"id": "P3", "basis": "INNER"})                   # aliases are not override bases


# ------------------------------------------------------------------ wall heights
def test_block_plaster_paint_tile_are_separate():
    iv = {"interval_m": 3.4, "authority": SV.FFL_INTERVAL}
    t = FH.termination(covering_bands=[{"type": "B2", "D_cm": 60, "bound": True, "coverage": 1.0}])
    h = FH.wall_heights(interval=iv, term=t, room_ctrl_D_cm=60, wet=False, buildup_above_m=None)
    assert h["BLOCKWORK"]["height_m"] == pytest.approx(2.8) and h["PLASTER"]["height_m"] == pytest.approx(2.8)
    assert h["PAINT"]["state"] == "BLOCKED_FLOOR_BUILDUP"
    h2 = FH.wall_heights(interval=iv, term=t, room_ctrl_D_cm=60, wet=True, buildup_above_m=0.08)
    assert h2["PAINT"]["height_m"] == pytest.approx(3.4 - 0.08 - 0.60 - 0.15)
    assert h2["WALL_TILE"]["height_m"] == h2["PAINT"]["height_m"]
    h3 = FH.wall_heights(interval=iv, term=t, room_ctrl_D_cm=60, wet=False, buildup_above_m=0.08)
    assert h3["CONCEALED_PLASTER_NOT_PAINTED_M"] == pytest.approx(2.8 - (3.4 - 0.08 - 0.60 - 0.15))


def test_unknown_termination_blocks_blockwork_and_slab_termination_uses_t():
    iv = {"interval_m": 3.4, "authority": SV.FFL_INTERVAL}
    u = FH.termination(covering_bands=[{"type": "B1", "D_cm": 45, "bound": True, "coverage": 0.4}])
    assert FH.wall_heights(interval=iv, term=u)["BLOCKWORK"]["state"].startswith("BLOCKED")
    s = FH.termination(inside_plate=True, plate_t_cm=16)
    assert FH.wall_heights(interval=iv, term=s)["BLOCKWORK"]["height_m"] == pytest.approx(3.24)
    d = FH.double_height_region(span_evidence="slab opening", area_m2=12.5)
    assert d["span_state"] == "COMPUTED" and d["paint_height"].startswith("BLOCKED")


# ------------------------------------------------------------------ waterproofing + methods
def test_roof_and_wet_upturns_and_laps_separate():
    r = WP.roof(area_m2=50.0, perimeter_m=30.0, region="R")
    assert r["physical_m2"] == pytest.approx(56.0) and r["laps"].startswith("NOT_INCLUDED")
    w = WP.wet(floor_m2=4.0, perimeter_m=8.0, door_widths_m=[0.8], room="W")
    assert w["physical_m2"] == pytest.approx(4.0 + 7.2 * 0.15)
    assert WP.procurement(56.0)["state"] == "NOT_APPLIED"
    assert WP.procurement(56.0, system="S", lap_factor=1.1)["procurement_m2"] == pytest.approx(61.6)


def test_methods_are_scoped_versioned_and_overrideable():
    m = "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1"
    assert UM.applies(m, "WARDROBE") and not UM.applies(m, "COLUMN") and not UM.applies(m, "SHAFT")
    assert all("@v" in k for k in UM.METHODS)
    r = UM.resolve("URBAN-PAINT-TO-FINISHED-CEILING@v1", {"id": "PS1", "parameters": {"ceiling_allowance_m": 0.1}})
    assert r["parameters"]["ceiling_allowance_m"] == 0.1 and r["authority"].startswith("PROJECT_OVERRIDE")


# ------------------------------------------------------------------ firewall: no benchmark constant in the engines
B2A_ENGINES = ["beam_binding", "structural_vertical", "concrete_model", "slab_region", "opening_authority",
               "curved_opening", "finish_height", "waterproofing_policy", "urban_methods"]
GENERIC = {0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 10.0, 100.0, 1000.0, 0.15, 0.2, 0.05, 0.8, 0.150}


def _literals(mod):
    tree = ast.parse((ROOT / "engine" / "source" / f"{mod}.py").read_text())
    # fractional literals only: integers in the engines are rounding digits, counts and indices, never quantities
    return {float(n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, float)
            and n.value != int(n.value)}


def test_no_benchmark_quantity_is_a_literal_in_the_b2a_engines():
    diff = json.loads((ROOT / "tests/alsenan/registers_b1/DIFFERENCE_REGISTER.json").read_text())["differences"]
    bench = {round(float(d["bench_qty"]), 6) for d in diff if isinstance(d.get("bench_qty"), (int, float))
             and float(d["bench_qty"]) != int(float(d["bench_qty"]))}
    assert len(bench) > 20                                             # the frozen B1 benchmark values are loaded
    bench -= {round(v, 6) for v in GENERIC}
    hits = {m: sorted(_literals(m) & bench) for m in B2A_ENGINES}
    assert not any(hits.values()), hits


def test_b2a_engines_do_not_import_project_or_benchmark_modules():
    bad = ("alsenan", "qortuba", "benchmark", "b1_", "research")
    for m in B2A_ENGINES:
        tree = ast.parse((ROOT / "engine" / "source" / f"{m}.py").read_text())
        names = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names] + \
                [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        assert not [x for x in names if any(b in x.lower() for b in bad)], (m, names)

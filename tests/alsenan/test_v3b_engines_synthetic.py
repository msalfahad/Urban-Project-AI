"""V3b (Alsenan full-BOQ candidate) generic engines - synthetic tests, no project data.

raster_evidence (scale calibration, grades, width gate), slab_rebar_binding (annotation -> drawn bar -> panel,
clear span + embedment, per-metre count)."""

from __future__ import annotations

import math

from engine.source import raster_evidence as RE
from engine.source import slab_rebar_binding as SB


# ------------------------------------------------------------------ raster_evidence
def test_two_agreeing_printed_dimensions_calibrate_the_sheet():
    cal = RE.calibrate([{"printed_cm": 300, "px": 474.0, "ref": "a"}, {"printed_cm": 550, "px": 869.0, "ref": "b"}])
    assert cal["state"] == RE.CALIBRATED and abs(cal["px_per_cm"] - 1.58) < 0.001


def test_one_printed_dimension_is_never_a_scale():
    cal = RE.calibrate([{"printed_cm": 300, "px": 474.0}])
    assert cal["state"] == RE.NOT_SCALABLE and RE.measure(100, cal)["value_cm"] is None


def test_disagreeing_dimensions_make_the_sheet_not_scalable_unless_within_the_pixel_tolerance():
    obs = [{"printed_cm": 100, "px": 162.0, "ref": "short"}, {"printed_cm": 500, "px": 790.0, "ref": "l1"},
           {"printed_cm": 600, "px": 948.0, "ref": "l2"}]
    assert RE.calibrate(obs)["state"] == RE.NOT_SCALABLE
    cal = RE.calibrate(obs, px_tol=4.0)
    assert cal["state"] == RE.CALIBRATED
    assert RE.calibrate([{"printed_cm": 100, "px": 180.0}, {"printed_cm": 500, "px": 790.0},
                         {"printed_cm": 600, "px": 948.0}], px_tol=4.0)["state"] == RE.NOT_SCALABLE


def test_scaled_measure_carries_grade_and_uncertainty():
    cal = RE.calibrate([{"printed_cm": 300, "px": 474.0}, {"printed_cm": 600, "px": 948.0}])
    m = RE.measure(331.8, cal)
    assert m["grade"] == RE.SCALED and m["confidence"] == "M" and abs(m["value_cm"] - 210.0) < 0.01
    assert m["uncertainty_cm"] > 0


def test_printed_value_conflicting_with_its_measured_line_is_a_conflict():
    cal = RE.calibrate([{"printed_cm": 300, "px": 474.0}, {"printed_cm": 600, "px": 948.0}])
    assert RE.printed(430, px=430 * 1.58, cal=cal)["state"] == "VERIFIED"
    assert RE.printed(430, px=380 * 1.58, cal=cal)["state"] == "CONFLICT"
    assert RE.printed(430)["grade"] == RE.PRINTED and RE.printed(430)["state"] == "READ"


def test_width_gate_and_linear_map():
    cal = RE.calibrate([{"printed_cm": 300, "px": 474.0}, {"printed_cm": 600, "px": 948.0}])
    assert RE.width_check(100, 158.0, cal)["state"] == "MATCH"
    assert RE.width_check(100, 175.0, cal)["state"] == "MISMATCH"
    assert RE.width_check(100, 158.0, {"state": RE.NOT_SCALABLE})["state"] == "NOT_CHECKED"
    f = RE.linear_map([(0, 10), (1000, 168), (2000, 326)])
    assert f["state"] == "FITTED" and abs(f["b"] - 0.158) < 1e-9 and f["max_residual_px"] < 1e-6
    assert RE.linear_map([(5, 1), (5, 2)])["state"] == "DEGENERATE"


def test_claims_are_content_addressed():
    a = RE.claim(sheet_sha256="x", sheet_ref="S", box_px=(0, 0, 1, 1), quantity="H", value_cm=210, grade=RE.SCALED,
                 evidence="e")
    b = RE.claim(sheet_sha256="x", sheet_ref="S", box_px=(0, 0, 1, 1), quantity="H", value_cm=211, grade=RE.SCALED,
                 evidence="e")
    assert a["claim_id"] != b["claim_id"] and a["confidence"] == "M"
    assert RE.policy_record()["digest"] == RE.policy_record()["digest"]


# ------------------------------------------------------------------ slab_rebar_binding
def _box(x0, y0, x1, y1):
    return [(x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)]


def _panel_with_beams():
    """A 4000 x 3000 clear panel between 300-wide beams on all four sides (faces drawn as lines)."""
    s = _box(0, 0, 4000, 3000) + _box(-300, -300, 4300, 3300)
    return s


def test_parse_per_metre_count_and_top():
    assert SB.parse("5%%c10/m") == {"kind": "PER_M", "n": 5, "dia_mm": 10, "top": False, "both_ways": False}
    assert SB.parse("8Ø16/m")["dia_mm"] == 16
    assert SB.parse("4Ø16/Top") == {"kind": "COUNT", "n": 4, "dia_mm": 16, "top": True, "both_ways": False}
    assert SB.parse("3Ø14")["kind"] == "COUNT" and SB.parse("SEE DETAIL") is None


def test_ray_hit_finds_the_first_support_and_none_when_open():
    s = _panel_with_beams()
    assert abs(SB.ray_hit((2000, 1500), (1, 0), s) - 2000) < 1e-9
    assert SB.ray_hit((2000, 1500), (1, 0), [(0, 0, 0, 3000)]) is None


def test_bound_bar_count_and_length_use_clear_span_plus_embedment():
    s = _panel_with_beams()
    ann = [{"id": "t1", "text": "5Ø10/m", "x": 2000, "y": 1600, "rotation_deg": 0}]
    bars = [{"id": "b1", "x0": 500, "y0": 1500, "x1": 3500, "y1": 1500}]
    r = SB.bind(ann, bars, s, cover_mm=25)[0]
    assert r["state"] == "BOUND" and r["bar"] == "b1"
    assert abs(r["clear_span_mm"] - 4000) < 1e-6 and abs(r["width_mm"] - 3000) < 1e-6
    assert r["count"] == math.floor(3000 / 200) + 1 == 16
    assert r["embed_mm"] == [275.0, 275.0] and abs(r["length_mm"] - 4550) < 1e-6
    assert abs(r["total_length_m"] - 16 * 4.55) < 1e-9
    assert r["route_b_drawn_vs_span"]["drawn_mm"] == 3000.0  # the symbol is reported, never the quantity


def test_open_far_face_gives_partial_clear_span_only():
    s = _box(0, 0, 4000, 3000)  # supports drawn as single lines - no far face
    r = SB.bind([{"id": "t", "text": "3Ø12", "x": 2000, "y": 1500, "rotation_deg": 0}], [], s)[0]
    assert r["state"] == "PARTIAL" and r["anchorage"] == "OPEN" and r["count"] == 3 and r["length_mm"] == 4000


def test_open_panel_is_unbound_never_estimated():
    r = SB.bind([{"id": "t", "text": "5Ø10/m", "x": 2000, "y": 1500, "rotation_deg": 0}], [],
                [(0, 0, 0, 3000)])[0]
    assert r["state"] == "UNBOUND" and "count" not in r


def test_two_competing_bars_within_the_tie_distance_are_ambiguous():
    s = _panel_with_beams()
    bars = [{"id": "b1", "x0": 500, "y0": 1500, "x1": 3500, "y1": 1500},
            {"id": "b2", "x0": 600, "y0": 1700, "x1": 2600, "y1": 1700}]
    r = SB.bind([{"id": "t", "text": "5Ø10/m", "x": 2000, "y": 1600, "rotation_deg": 0}], bars, s)[0]
    assert r["state"] == "AMBIGUOUS" and set(r["candidates"]) == {"b1", "b2"}


def test_a_perpendicular_bar_is_never_bound_and_rotation_sets_the_direction():
    s = _panel_with_beams()
    bars = [{"id": "v", "x0": 2000, "y0": 200, "x1": 2000, "y1": 2800}]
    r = SB.bind([{"id": "t", "text": "5Ø10/m", "x": 2000, "y": 1600, "rotation_deg": 0}], bars, s)[0]
    assert r["bar"] is None and r["binding"] == "TEXT_ONLY_PANEL" and r["state"] == "BOUND_TEXT_ONLY"
    r90 = SB.bind([{"id": "t", "text": "5Ø10/m", "x": 2050, "y": 1600, "rotation_deg": 90}], bars, s)[0]
    assert r90["bar"] == "v" and abs(r90["clear_span_mm"] - 3000) < 1e-6 and r90["count"] == 21


def test_binding_is_order_independent():
    s = _panel_with_beams()
    ann = [{"id": "t1", "text": "5Ø10/m", "x": 2000, "y": 1600, "rotation_deg": 0},
           {"id": "t2", "text": "4Ø12/m", "x": 2050, "y": 1600, "rotation_deg": 90}]
    bars = [{"id": "b1", "x0": 500, "y0": 1500, "x1": 3500, "y1": 1500},
            {"id": "v", "x0": 2000, "y0": 200, "x1": 2000, "y1": 2800}]
    a = SB.bind(ann, bars, s)
    b = SB.bind(list(reversed(ann)), list(reversed(bars)), list(reversed(s)))
    assert sorted(map(repr, a)) == sorted(map(repr, b))
    assert SB.policy_record()["embed_rule"] == SB.EMBED_RULE

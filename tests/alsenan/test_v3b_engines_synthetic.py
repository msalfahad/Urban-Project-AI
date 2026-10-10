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


def test_duplicate_label_over_the_same_panel_is_counted_once_and_reversed_bars_match():
    s = _panel_with_beams()
    ann = [{"id": "t1", "text": "5Ø10/m", "x": 2000, "y": 1600, "rotation_deg": 0},
           {"id": "t2", "text": "5Ø10/m", "x": 1000, "y": 900, "rotation_deg": 180}]
    r = SB.dedupe(SB.bind(ann, [], s))
    assert [x["state"] for x in r] == ["BOUND_TEXT_ONLY", "DUPLICATE_LABEL"] and r[1]["duplicate_of"] == "t1"
    other = SB.dedupe(SB.bind([ann[0], {"id": "t3", "text": "8Ø16/m", "x": 1000, "y": 900, "rotation_deg": 0}], [], s))
    assert [x["state"] for x in other] == ["BOUND_TEXT_ONLY", "BOUND_TEXT_ONLY"]


def test_polyline_bar_binds_by_its_longest_leg_and_a_count_bar_outside_the_grid_is_drawn_extent():
    s = _panel_with_beams()
    pl = {"id": "u", "path": [(500, 3500), (3500, 3500), (3550, 3450), (3550, 3400), (3500, 3350), (2500, 3350)]}
    r = SB.bind([{"id": "t", "text": "4Ø16/Top", "x": 2000, "y": 3600, "rotation_deg": 0}], [pl], s)[0]
    dev = 3000 + 2 * math.hypot(50, 50) + 50 + 1000
    assert r["bar"] == "u" and r["state"] == "DRAWN_EXTENT" and r["count"] == 4
    assert abs(r["length_mm"] - dev) < 1e-6 and r["anchorage"] == "AS_DRAWN"
    r2 = SB.bind([{"id": "t", "text": "5Ø10/m", "x": 2000, "y": 3600, "rotation_deg": 0}], [pl], s)[0]
    assert r2["state"] == "UNBOUND"


# ------------------------------------------------------------------ bbs_optimiser
from engine.source import bbs_optimiser as BB          # noqa: E402


def test_hook_addition_follows_the_recorded_table_and_is_provisional_until_verified():
    h = BB.hook_addition(16, "90")
    D, tail = 6 * 16, 12 * 16
    exp = tail + math.radians(90) * (D / 2 + 8) - (D / 2 + 16)
    assert abs(h["addition_m"] - exp / 1000) < 1e-6 and h["class"] == "PROVISIONAL_CODE_METHOD"
    t = BB.hook_addition(8, "135_TIE")
    assert t["tail_mm"] == 75 and t["inside_bend_d_mm"] == 32 and t["table"] == "25.3.2"
    v = dict(BB.ACI_318_19, verified=True)
    assert BB.hook_addition(16, "90", v)["class"] == "CODE_METHOD"


def test_split_run_adds_the_laps_and_keeps_every_piece_within_the_stock():
    p = BB.split_run(20.0, 1.12)
    assert p[0] == 12.0 and abs(sum(p) - (20.0 + 1.12)) < 1e-9 and max(p) <= 12.0
    assert BB.split_run(11.0, 1.12) == [11.0]


def test_cutting_is_first_fit_decreasing_with_offcut_reuse_and_order_independent():
    pieces = [("A", 7.0, 2), ("B", 5.0, 2), ("C", 4.5, 1)]
    r = BB.cut(pieces)
    # 7+5 | 7+5 | 4.5 -> 3 bars, 36 m bought, 28.5 used, 10 m from offcuts, 7.5 m scrap
    assert r["purchased_bars"] == 3 and r["used_m"] == 28.5 and r["reused_offcut_m"] == 10.0
    assert r["unused_offcut_m"] == 7.5 and abs(r["effective_waste_pct"] - 100 * 7.5 / 36) < 1e-3
    assert BB.cut(list(reversed(pieces))) == r
    try:
        BB.cut([("X", 13.0, 1)])
        raise AssertionError("a piece longer than the stock must fail")
    except ValueError:
        pass


# ------------------------------------------------------------------ release_model
from engine.source import release_model as RM          # noqa: E402


def _prov(cls, q, lo, hi, conf):
    return {"class": cls, "qty": q, "method": "m", "assumption": "a", "confidence": conf, "low": lo, "high": hi}


def test_provisional_is_never_technical_and_must_carry_its_range():
    for bad in ("PROVISIONAL_SOURCE_DERIVED", "BUDGET_ESTIMATE"):
        try:
            RM.release(bad, 1.0)
            raise AssertionError
        except RM.ReleaseError:
            pass
    try:
        RM.release("BLOCKED", None, {"class": "PROVISIONAL_OWNER_METHOD", "qty": 5.0})
        raise AssertionError
    except RM.ReleaseError:
        pass
    try:
        RM.release("BLOCKED", None, _prov("PROVISIONAL_OWNER_METHOD", 9.0, 1.0, 5.0, "M"))
        raise AssertionError
    except RM.ReleaseError:
        pass
    r = RM.release("BLOCKED", 3.0, _prov("PROVISIONAL_OWNER_METHOD", 4.0, 3.0, 5.0, "M"))
    assert r["technical"]["qty"] is None and r["commercial"]["in_commercial_total"]


def test_totals_split_technical_commercial_budget_and_procurement():
    recs = [RM.release("DERIVED", 10.0),
            RM.release("BLOCKED", None, _prov("PROVISIONAL_SOURCE_DERIVED", 4.0, 3.0, 5.0, "H")),
            RM.release("BLOCKED", None, _prov("PROVISIONAL_GEOMETRIC_INFERENCE", 2.0, 1.0, 3.0, "M")),
            RM.release("BLOCKED", None, _prov("BUDGET_ESTIMATE", 7.0, 5.0, 9.0, "L")),
            RM.release("BLOCKED", None)]
    t = RM.totals(recs)
    assert t["technical_total"] == 10.0 and t["commercial_total"] == 16.0 and t["commercial_provisional_part"] == 6.0
    assert t["budget_allowance"] == 7.0 and t["commercial_total_incl_budget"] == 23.0
    assert t["procurement_eligible"] == 14.0 and t["pending"] == 1
    assert t["low"] == 10 + 3 + 1 + 5 and t["high"] == 10 + 5 + 3 + 9


# ------------------------------------------------------------------ waste_procurement
from engine.source import waste_procurement as WP     # noqa: E402


def test_no_approved_rule_is_pending_with_blank_fields_never_zero():
    w = WP.apply(100.0, "m2", WP.resolve("X", "TILE", "PORCELAIN", []))
    assert w["STATE"] == "PENDING" and w["WASTE_PCT"] is None and w["WASTE_QTY"] is None and w["PROCUREMENT"] is None
    unapproved = [{"scope": "PROJECT", "key": "*", "method": "flat", "pct": 5.0, "approved_by": None}]
    assert WP.resolve("X", "TILE", None, unapproved) is None


def test_waste_hierarchy_item_over_trade_over_project_and_computed_rebar():
    rules = [{"scope": "PROJECT", "key": "*", "method": "flat", "pct": 3.0, "approved_by": "owner"},
             {"scope": "TRADE_MATERIAL", "key": "TILE|PORCELAIN", "method": "trade", "pct": 7.0, "approved_by": "owner"},
             {"scope": "ITEM", "key": "T-1", "method": "item", "pct": 10.0, "approved_by": "owner"}]
    assert WP.resolve("T-1", "TILE", "PORCELAIN", rules)["pct"] == 10.0
    assert WP.resolve("T-2", "TILE", "PORCELAIN", rules)["pct"] == 7.0
    assert WP.resolve("P-1", "PAINT", None, rules)["pct"] == 3.0
    a = WP.apply(200.0, "m2", rules[1])
    assert a["WASTE_QTY"] == 14.0 and a["PROCUREMENT"] == 214.0 and a["STATE"] == "APPLIED"
    c = WP.apply(1000.0, "kg", {"method": "CUTTING_OPTIMISATION", "waste_qty": 50.0, "procurement": 1100.0})
    assert c["STATE"] == "COMPUTED" and c["PROCUREMENT"] == 1100.0 and abs(c["WASTE_PCT"] - 100 * 50 / 1100) < 1e-9


# ------------------------------------------------------------------ corner_bead
from engine.source import corner_bead as CB           # noqa: E402


def test_beads_on_plastered_faces_only_and_never_on_a_tiled_face():
    door = {"id": "D1", "kind": "DOOR", "width_m": 0.9, "height_m": 2.1, "sill_m": 0.0,
            "faces": [{"face": "A", "plaster": (0.0, 3.0)}, {"face": "B", "plaster": None}]}
    win = {"id": "W1", "kind": "WINDOW", "width_m": 1.0, "height_m": 1.2, "sill_m": 1.0,
           "faces": [{"face": "A", "plaster": (1.5, 3.0)}]}        # tiled to 1.5 m, plaster above
    segs = CB.segments([door, win])
    t = CB.total(segs)
    assert t["by_edge_type"]["DOOR_JAMB"] == 4.2 and t["by_edge_type"]["DOOR_HEAD"] == 0.9
    assert abs(t["by_edge_type"]["WINDOW_JAMB"] - 2 * 0.7) < 1e-9 and t["by_edge_type"]["WINDOW_HEAD"] == 1.0
    assert "WINDOW_SILL" not in t["by_edge_type"]                  # sill at 1.0 m lies on the tiled band
    assert all(s["face"] != "B" for s in segs)


def test_corner_needs_plaster_on_both_faces_and_unknown_height_is_blocked_not_zero():
    c = [{"id": "C1", "z0": 0.0, "z1": 3.0, "faces": [(0.0, 3.0), (0.0, 3.0)]},
         {"id": "C2", "z0": 0.0, "z1": 3.0, "faces": [(0.0, 3.0), None]},
         {"id": "C3", "z0": None, "z1": None, "faces": [(0.0, 3.0), (0.0, 3.0)]}]
    segs = CB.segments([], c)
    assert [(s["host"], s["status"], s["length_m"]) for s in segs] == [("C1", "MEASURED", 3.0), ("C3", "BLOCKED", None)]
    o = CB.segments([{"id": "D", "kind": "DOOR", "width_m": 0.9, "height_m": None,
                      "faces": [{"face": "A", "plaster": (0, 3)}]}])
    assert o and all(s["status"] == "BLOCKED" and s["length_m"] is None for s in o)

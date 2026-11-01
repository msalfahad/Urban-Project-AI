"""LIFT_ENTRANCE_MARBLE_V1 on hand villa K413 (not Alsenan): a lift serving B / GF / 1F, a through-car with TWO landing
doors on 1F, clear doors 0.90 m, storey 3.60 m. Hand values below; adverse readings refused."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t413"))
sys.path.insert(0, str(ROOT))
import lift_entrance_marble_v1 as LM  # noqa: E402

SRC = LM.SURROUND_SOURCE


def _bands(l=0.5, t=0.5, r=0.5, avail=(None, None)):
    return (LM.band_width("LEFT", available_m=avail[0], default_m=l, default_source=SRC),
            LM.band_width("TOP", default_m=t, default_source=SRC),
            LM.band_width("RIGHT", available_m=avail[1], default_m=r, default_source=SRC))


FLOORS = [{"floor": "B", "doors": [{}]}, {"floor": "GF", "doors": [{}]}, {"floor": "1F", "doors": [{}, {}]}]


def test_one_station_per_landing_door():
    assert LM.stations(FLOORS) == ["ELV-01-B", "ELV-01-GF", "ELV-01-1F-1", "ELV-01-1F-2"]
    assert LM.check_count(4, FLOORS) == 4


def test_one_per_floor_where_the_shaft_has_two_doors_refused():
    with pytest.raises(LM.Refused):
        LM.check_count(3, FLOORS)            # one entrance per floor
    with pytest.raises(LM.Refused):
        LM.check_count(1, FLOORS)            # the shaft as the count
    with pytest.raises(LM.Refused):
        LM.stations([{"floor": "2F", "doors": []}])


def test_surround_with_printed_height_owner_default_widths():
    l, t, r = _bands()
    s = LM.surround("ELV-01-1F-1", clear_width_m=0.90, clear_height_m=2.10, left=l, top=t, right=r)
    assert s["area_m2"] == pytest.approx(2.10 * 1.0 + 0.5 * 1.9)      # 3.050 (corners once)
    assert s["status"] == LM.OWNER
    assert s["edge_lm"] == pytest.approx(2 * 2.10 + 2 * 0.5 + 0.90 + 0.5 + 0.5)
    # the same union as the round-6 engine polygon (read only)
    from engine import elevator_marble as EM
    e = EM.measure_surround("x", door_width_mm=900, door_height_mm=2100, left_mm=500, top_mm=500, right_mm=500)
    assert e.area_m2 == pytest.approx(s["area_m2"])
    # neither linear reading
    assert s["area_m2"] != pytest.approx((2 * 2.10 + 0.90) * 0.5)    # misses the corners
    assert s["area_m2"] != pytest.approx((2 * 2.60 + 1.90) * 0.5)    # counts them twice


def test_surround_drawn_widths_are_drawing_confirmed():
    b = [LM.band_width(sd, drawn_m=0.40) for sd in ("LEFT", "TOP", "RIGHT")]
    s = LM.surround("ELV-01-GF", clear_width_m=0.90, clear_height_m=2.10, left=b[0], top=b[1], right=b[2])
    assert s["area_m2"] == pytest.approx(2.10 * 0.8 + 0.4 * 1.7)     # 2.360
    assert s["status"] == LM.DRAWING


def test_height_not_printed_is_held_with_bound_never_zero():
    l, t, r = _bands()
    s = LM.surround("ELV-01-B", clear_width_m=0.90, storey_height_m=3.60, left=l, top=t, right=r)
    assert s["area_m2"] is None and s["status"] == LM.HELD
    assert s["bound_m2"] == pytest.approx([0.95, 3.10 * 1.0 + 0.95])  # top band .. h_max = 3.60 - 0.50
    assert any("clear height" in m for m in s["missing"])
    tot = LM.totals([s], "area_m2")
    assert tot["value"] is None and tot["bound"][0] > 0


def test_surround_width_defaulted_without_source_refused():
    with pytest.raises(LM.Refused):
        LM.band_width("LEFT", default_m=0.5, default_source=None)
    with pytest.raises(LM.Refused):
        LM.band_width("LEFT", default_m=0.5, default_source="practice")
    with pytest.raises(LM.Refused):
        LM.band_width("LEFT", default_m=0.6, default_source=SRC)       # not the owner's value


def test_default_never_replaces_a_drawn_width():
    with pytest.raises(LM.Refused):
        LM.band_width("LEFT", drawn_m=0.40, default_m=0.50, default_source=SRC)


def test_default_wider_than_the_face_is_held_with_bound():
    b = LM.band_width("RIGHT", available_m=0.35, default_m=0.5, default_source=SRC)
    assert b["width_m"] is None and b["status"] == LM.HELD and b["bound"] == [0.0, 0.35]
    l, t, _ = _bands()
    s = LM.surround("ELV-01-GF", clear_width_m=0.90, storey_height_m=3.60, left=l, top=t, right=b)
    assert s["bound_m2"] == pytest.approx([0.5 * (0.90 + 0.5), 3.10 * 0.85 + 0.5 * 1.75])


def test_mirror_and_quarter_turn_identical():
    a = LM.surround("m", clear_width_m=0.90, clear_height_m=2.10, left=LM.band_width("LEFT", drawn_m=0.5),
                    top=LM.band_width("TOP", drawn_m=0.5), right=LM.band_width("RIGHT", drawn_m=0.4))
    b = LM.surround("m", clear_width_m=0.90, clear_height_m=2.10, left=LM.band_width("LEFT", drawn_m=0.4),
                    top=LM.band_width("TOP", drawn_m=0.5), right=LM.band_width("RIGHT", drawn_m=0.5))
    assert a["area_m2"] == pytest.approx(b["area_m2"])               # station-local: rotation never enters


def test_millimetres_refused_never_rescaled():
    with pytest.raises(LM.Refused):
        LM.band_width("LEFT", drawn_m=500)
    l, t, r = _bands()
    with pytest.raises(LM.Refused):
        LM.surround("u", clear_width_m=900, clear_height_m=2100, left=l, top=t, right=r)
    with pytest.raises(LM.Refused):
        LM.threshold("u", clear_width_m=900, depth_m=500)


def test_missing_width_refused():
    l, t, r = _bands()
    with pytest.raises(LM.Refused):
        LM.surround("x", clear_width_m=None, clear_height_m=2.1, left=l, top=t, right=r)
    with pytest.raises(LM.Refused):
        LM.threshold("x", clear_width_m=None)


def test_threshold_owner_depth_keeps_drawn_width():
    t = LM.threshold("ELV-01-GF", clear_width_m=0.90, default_depth_m=0.50, depth_source=LM.THRESHOLD_SOURCE,
                     wall_band_m=0.25)
    assert t["area_m2"] == pytest.approx(0.45) and t["front_edge_lm"] == pytest.approx(0.90)
    assert t["status"] == LM.OWNER
    assert t["floor_overlap_bound_m2"] == pytest.approx([0.90 * 0.25, 0.45])
    assert t["floor_overlap_status"] == LM.HELD
    p = LM.threshold("ELV-01-B", clear_width_m=0.90, depth_m=0.30, depth_source="detail 7",
                     landing_face_overlap_m2=0.27)
    assert p["area_m2"] == pytest.approx(0.27) and p["status"] == LM.DRAWING
    assert p["floor_overlap_status"] == LM.DRAWING


def test_threshold_adverse():
    with pytest.raises(LM.Refused):          # the 1.10 m fallback over a drawn 0.90 door
        LM.threshold("x", clear_width_m=0.90, default_width_m=1.10, default_depth_m=0.5,
                     depth_source=LM.THRESHOLD_SOURCE)
    with pytest.raises(LM.Refused):          # a default depth with no source
        LM.threshold("x", clear_width_m=0.90, default_depth_m=0.5)
    h = LM.threshold("x", clear_width_m=0.90)
    assert h["area_m2"] is None and h["status"] == LM.HELD           # never 0


def test_threshold_counted_also_as_a_door_threshold_refused():
    assert LM.bind("ELV-01-GF", ["FIN.MARBLE.ELEVATOR_THRESHOLD"]) == ["FIN.MARBLE.ELEVATOR_THRESHOLD"]
    for code in ("FIN.MARBLE.THRESHOLD", "ARCH.THRESHOLD", "FIN.PROFILE.TRANSITION", "FIN.BEAD.CORNER"):
        with pytest.raises(LM.Refused):
            LM.bind("ELV-01-GF", ["FIN.MARBLE.ELEVATOR_THRESHOLD", code])

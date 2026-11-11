"""T-701 plaster / paint reference reconciliation (R-T701-1 .. -3): synthetic villa V701 by hand (normal + adverse) and
the development villa pinned to the committed outputs.

Villa V701 (synthetic, not the development villa), by hand:
  dry room 4.00 x 3.00 -> face 14.00 lm; structural soffit 3.00, finished ceiling 2.80; one door 0.90 x 2.20 = 1.98
    plaster = 14 x 3.00 - 1.98 = 40.02; paint = 14 x 2.80 - 1.98 = 37.22
    reference at a flat 2.80, gross, no per-room deduction: 14 x 2.80 = 39.20
    plaster bridge: LENGTH 0, HEIGHT 14 x (2.80 - 3.00) = -2.80, DEDUCTIONS 42.00 - 40.02 = 1.98 -> gap -0.82
    paint bridge:   LENGTH 0, HEIGHT 0, DEDUCTIONS 1.98 -> gap +1.98
  wet room 2.00 x 2.50 -> face 9.00 lm, porcelain to the ceiling 2.80, soffit 3.00, door 0.80 x 2.20 = 1.76
    render (plaster trade) = 9 x 2.80 - 1.76 = 23.44; band above the ceiling = 9 x 0.20 = 1.80; paint: none
  annex datum: face 10.00, S 3.00 .. 3.60, fixed openings 2.00, arch 1.00 wide with no height, beam ends 0.10
    low = 10 x 3.00 - 2.00 - 1.00 x 3.00 - 0.10 = 24.90; high = 10 x 3.60 - 2.00 - 0.10 = 33.90
"""
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t701"
sys.path.insert(0, str(HERE))
import t701_rules as R  # noqa: E402

OUT = HERE / "out" / "T701_RECONCILE.json"


# ---------------- normal ----------------
def test_two_layers_one_face_set():
    r = R.finish_layers("14.00", "3.00", "2.80", [("0.90", "2.20")])
    assert r == {"plaster": Decimal("40.020000"), "paint": Decimal("37.220000")}


def test_plaster_bridge_by_hand():
    b = R.room_bridge([("14.00", "2.80")], "14.00", {"low": ("3.00", "40.02"), "high": ("3.00", "40.02")})
    for e in ("low", "high"):
        assert b[e]["LENGTH"] == 0
        assert b[e]["HEIGHT"] == Decimal("-2.800000")
        assert b[e]["DEDUCTIONS"] == Decimal("1.980000")
        assert b[e]["gap"] == Decimal("-0.820000")


def test_paint_bridge_by_hand():
    b = R.room_bridge([("14.00", "2.80")], "14.00", {"low": ("2.80", "37.22"), "high": ("2.80", "37.22")})
    assert (b["low"]["LENGTH"], b["low"]["HEIGHT"], b["low"]["DEDUCTIONS"]) == (0, 0, Decimal("1.980000"))
    assert b["low"]["gap"] == Decimal("1.980000")


def test_length_and_mirror_order_invariant():
    a = R.room_bridge([("7.00", "2.80"), ("7.20", "2.80")], "14.00",
                      {"low": ("3.00", "40.02"), "high": ("3.00", "40.02")})
    b = R.room_bridge([("7.20", "2.80"), ("7.00", "2.80")], "14.00",
                      {"low": ("3.00", "40.02"), "high": ("3.00", "40.02")})
    assert a == b
    assert a["low"]["LENGTH"] == Decimal("0.560000")       # 0.20 lm x 2.80


def test_held_range_two_ends():
    b = R.room_bridge([("14.00", "2.80")], "14.00", {"low": ("3.00", "38.02"), "high": ("3.00", "40.02")})
    assert b["low"]["DEDUCTIONS"] - b["high"]["DEDUCTIONS"] == Decimal("2.000000")


def test_tiled_wet_face_render_not_paint():
    r = R.finish_layers("9.00", "3.00", "2.80", [("0.80", "2.20")], tiled=True)
    assert r == {"plaster_render": Decimal("23.440000"), "band_above_ceiling": Decimal("1.800000"), "paint": None}


def test_datum_bound_and_coverage():
    b = R.datum_bound("10.00", "3.00", "3.60", "2.00", "1.00", "0.10")
    assert b == (Decimal("24.900000"), Decimal("33.900000"))
    c = R.coverage("31.20", "31.20", b)                  # a point at one scenario inside the bound
    assert c["status"] == "NARROW" and c["change"] == [Decimal("-6.300000"), Decimal("2.700000")]
    assert R.coverage("24.90", "33.90", b)["status"] == "COVERED"


def test_pair_close_by_cause():
    p = R.pair_close("100", "80", "90", [("a", "15", "5", "HELD"), ("b", "5", "5", "ENGINE_RIGHT")])
    assert p["by_cause"]["HELD"] == [Decimal("15.000000"), Decimal("5.000000")]


# ---------------- adverse ----------------
@pytest.mark.parametrize("h", ["3000", "300", "0", "-2.8"])
def test_height_in_mm_cm_or_nonpositive_refused(h):
    with pytest.raises(ValueError):
        R.room_bridge([("14.00", "2.80")], "14.00", {"low": (h, "40.02"), "high": (h, "40.02")})


def test_paint_on_tiled_face_refused():
    with pytest.raises(ValueError):
        R.finish_layers("9.00", "3.00", "2.80", [], tiled=True, paint="25.20")


def test_ceiling_above_soffit_refused():
    with pytest.raises(ValueError):
        R.finish_layers("14.00", "2.80", "3.00", [])


def test_net_above_gross_refused():
    with pytest.raises(ValueError):
        R.room_bridge([("14.00", "2.80")], "14.00", {"low": ("2.80", "40.00"), "high": ("2.80", "40.00")})


@pytest.mark.parametrize("net", [None, "0"])
def test_held_blank_never_bridged_as_zero(net):
    with pytest.raises(ValueError):
        R.room_bridge([("14.00", "2.80")], "14.00", {"low": ("3.00", net), "high": ("3.00", "40.02")})


def test_low_above_high_refused():
    with pytest.raises(ValueError):
        R.room_bridge([("14.00", "2.80")], "14.00", {"low": ("3.00", "40.02"), "high": ("3.00", "39.00")})


def test_float_and_missing_end_refused():
    with pytest.raises(TypeError):
        R.room_bridge([(14.0, "2.80")], "14.00", {"low": ("3.00", "40.02"), "high": ("3.00", "40.02")})
    with pytest.raises(ValueError):
        R.room_bridge([("14.00", "2.80")], "14.00", {"low": ("3.00", "40.02")})


def test_pair_that_does_not_close_or_unknown_cause_refused():
    with pytest.raises(AssertionError):
        R.pair_close("100", "80", "90", [("a", "15", "5", "HELD")])
    with pytest.raises(ValueError):
        R.pair_close("100", "80", "90", [("a", "20", "10", "CLOSE_ENOUGH")])


def test_datum_bound_adverse():
    with pytest.raises(ValueError):
        R.datum_bound("10", "3.60", "3.00", "2.0")         # low > high
    with pytest.raises(ValueError):
        R.datum_bound("10", "3000", "3600", "2.0")         # mm
    with pytest.raises(ValueError):
        R.datum_bound("1.0", "3.0", "3.6", "5.0")          # deductions exceed the face


# ---------------- development villa (pinned) ----------------
def test_builder_check_byte_identical():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t701_alsenan.py"), "--check"], capture_output=True,
                       text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def _o():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_whole_bridges_close_to_the_board_figures():
    o = _o()
    p, n = o["whole"]["plaster"], o["whole"]["paint"]
    assert p["engine"] == ["1520.550236", "1689.278640"] and p["engine_vs_his_net_pct"][0] == "32.091104"
    assert n["engine"] == ["818.853438", "899.539400"]
    assert n["engine_vs_his_net_pct"] == ["-31.253922", "-24.480007"]
    for w in (p, n):
        s = [sum(Decimal(c[k]) for c in w["components"]) for k in ("at_engine_low", "at_engine_high")]
        assert s == [Decimal(w["gap_at_engine_low"]), Decimal(w["gap_at_engine_high"])]
        assert Decimal(w["his_gross"]) - Decimal(w["his_half_step"]) == Decimal(w["his_net"])


def test_key_scope_is_the_plaster_excess():
    o = _o()
    k = o["key_scope_wet"]
    assert k["engine"] == ["498.447626", "589.822230"] and k["cause"] == "RULE_DIFFERENCE"
    ll = o["like_for_like_dry_plus_shaft"]["plaster"]
    assert Decimal(ll["pct"][0]) < 0 and Decimal(ll["pct"][1]) < 0     # like for like the engine is below him


def test_annex_plaster_narrow_bound():
    c = _o()["annex_plaster_coverage"]
    assert c["GF-01"]["status"] == c["GF-04"]["status"] == "NARROW"
    assert c["GF-01"]["datum_bound"] == ["47.960668", "66.260680"]
    assert c["GF-04"]["datum_bound"] == ["34.330000", "43.780000"]
    assert c["GF-04"]["reproduced_at_S_3.79"] == ["43.155000", "43.155000"]


def test_census_counts():
    c = _o()["census"]
    assert c["FIN.PLASTER"]["EXCLUDED"]["lines"] == 13 and c["FIN.PAINT"]["EXCLUDED"]["lines"] == 31
    assert c["FIN.PLASTER"]["DRY"]["lines"] == 11 and c["FIN.PLASTER"]["SHAFT"]["lines"] == 3
    assert c["FIN.PLASTER"]["WET_BAND"]["lines"] == 18
    assert len(c["FIN.PLASTER"]["RETURN"]["blank"]) == 3

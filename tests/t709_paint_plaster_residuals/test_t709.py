"""T-709 paint / plaster residuals round 2 (R-T709-1 .. -4): synthetic villa V709 by hand (normal + adverse) and the
development villa pinned to the committed outputs.

Villa V709 (synthetic, not the development villa), by hand:
  stairwell wall 3.00 m long, solid on both storeys; lower FFL +0.00, lower plaster soffit +3.10, lower ceiling +2.60,
  upper FFL +3.40; a landing touches the band over 0.50 m up to +2.70:
    plaster band = 3.00 x (3.40 - 3.10) = 0.90; paint band = 3.00 x (3.40 - 2.60) = 2.40, less 0.50 x 0.10 = 0.05 -> 2.35
  the same face with NO wall below (a beam): HELD by name until the beam depth is printed; depth 0.40 -> 1.20
  reference row 'stair wall' 6.05 m vs drawn runs 6.00 (well) / 7.50 (shaft) -> BOUND to the well (+0.05);
    6.05 vs 6.00 and 6.10 -> AMBIGUOUS; 9.00 -> UNRESOLVED
  returns: his 4 doors x 0.20 x 5.00 = 4.00 vs drawn 0.75 + 0.75 + 0.90 + 0.90 + 1.20 = 4.50 (5 doors)
    gap -0.50; order 1: count (4 - 5) x 0.90 = -0.90, unit 4 x (1.00 - 0.90) = +0.40;
              order 2: count (4 - 5) x 1.00 = -1.00, unit 5 x 0.10 = +0.50
  return paint: released 0.84 -> HELD 0 .. 0.84; wet both sides -> same bound, NOT_ESTABLISHED; blank -> HELD by name
"""
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t709"
sys.path.insert(0, str(HERE))
import t709_rules as R  # noqa: E402

OUT = HERE / "out" / "T709_RESIDUALS.json"


# ---------------- normal ----------------
def test_double_height_bands_by_hand():
    assert R.double_height_band("3.00", "3.40", "3.10") == Decimal("0.900000")
    assert R.double_height_band("3.00", "3.40", "2.60") == Decimal("2.400000")
    assert R.double_height_band("3.00", "3.40", "2.60", ["0.05"]) == Decimal("2.350000")


def test_mirror_and_rotation_do_not_change_the_band():
    # the band depends on the run length and the levels only: the same wall drawn mirrored / rotated has the same run
    a = R.double_height_band("3.000", "3.40", "3.10")
    b = R.double_height_band(Decimal("3"), "3.4", "3.1")
    assert a == b


def test_no_wall_below_is_held_not_zero():
    assert R.beam_band("3.00", None) is None
    assert R.beam_band("3.00", "0.40") == Decimal("1.200000")


def test_reference_row_binding():
    assert R.bind_row("6.05", [("well", "6.00"), ("shaft", "7.50")]) == ("BOUND", "well", Decimal("0.050000"))
    assert R.bind_row("6.05", [("a", "6.00"), ("b", "6.10")])[0] == "AMBIGUOUS"
    assert R.bind_row("9.00", [("a", "6.00"), ("b", "7.50")]) == ("UNRESOLVED", None, None)


def test_return_bridge_both_orders_close():
    b = R.return_bridge(4, "0.20", "5.00", ["0.75", "0.75", "0.90", "0.90", "1.20"])
    assert b["gap"] == "-0.500000" and b["engine"] == "4.500000" and b["his"] == "4.000000"
    assert b["count_term"] == ["-1.000000", "-0.900000"] and b["unit_term"] == ["0.400000", "0.500000"]


def test_return_paint_rows():
    r = R.return_paint_row("X-OPENING-1", "RELEASED", 0.84, False)
    assert r["class"] == "HELD" and r["value"] is None and r["bound_beside_m2"] == ["0.000000", "0.840000"]
    w = R.return_paint_row("X-OPENING-2", "RELEASED", "0.84", True)
    assert w["flag"].startswith("NOT_ESTABLISHED") and w["value"] is None
    h = R.return_paint_row("X-REVEAL-3", "HELD", None, False)
    assert h["bound_beside_m2"] is None and h["value"] is None


# ---------------- adverse ----------------
def test_band_with_missing_level_is_held():
    assert R.double_height_band(None, "3.40", "3.10") is None
    assert R.double_height_band("3.00", None, "3.10") is None


@pytest.mark.parametrize("lm,up,low", [("3000", "3.40", "3.10"), ("3.00", "340", "3.10"), ("-1", "3.40", "3.10")])
def test_mm_and_negative_refused(lm, up, low):
    with pytest.raises(R.RuleError):
        R.double_height_band(lm, up, low)


def test_lower_top_above_upper_floor_refused():
    with pytest.raises(R.RuleError):
        R.double_height_band("3.00", "3.40", "3.50")


def test_contacts_outside_band_refused():
    with pytest.raises(R.RuleError):
        R.double_height_band("3.00", "3.40", "3.10", ["1.00"])
    with pytest.raises(R.RuleError):
        R.double_height_band("3.00", "3.40", "3.10", ["-0.01"])


def test_bridge_refuses_blank_zero_and_fractional_count():
    with pytest.raises(R.RuleError):
        R.return_bridge(4, "0.20", "5.00", ["0.75", None])
    with pytest.raises(R.RuleError):
        R.return_bridge(4, "0.20", "5.00", ["0.75", "0"])
    with pytest.raises(R.RuleError):
        R.return_bridge("4.5", "0.20", "5.00", ["0.75"])
    with pytest.raises(R.RuleError):
        R.return_bridge(4, "200", "5.00", ["0.75"])         # depth in mm


def test_return_paint_adverse():
    with pytest.raises(R.RuleError):
        R.return_paint_row("X", "RELEASED", 0, False)      # a released return of 0 is not a face
    with pytest.raises(R.RuleError):
        R.return_paint_row("X", "HELD", "0.5", False)      # a held return carries no value
    with pytest.raises(R.RuleError):
        R.return_paint_row("X", "EXCLUDED", None, False)
    with pytest.raises(R.RuleError):
        R.D(float("nan"))


# ---------------- development villa (pinned outputs) ----------------
def test_builder_check_byte_identical():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t709_alsenan.py"), "--check"], capture_output=True,
                       text=True, cwd=str(ROOT))
    assert r.returncode == 0 and "REPRODUCED" in r.stdout, r.stdout + r.stderr


def _o():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_shaft_residual_split():
    a = _o()["a_shaft"]
    assert a["his_row_8"]["binding"] == "BOUND" and a["his_row_8"]["drawn_well_lm"] == "11.17"
    assert a["his_row_8"]["his_minus_drawn_lm"] == "0.080000"
    assert a["his_row_24"]["length_binding"] == "AMBIGUOUS"
    assert a["his_row_24"]["printed_level_intervals_within_0.05_of_his_height"] == []
    assert a["residual_after"] == {"identified_to_1F_13": "40.5000", "unresolved": "13.5000"}


def test_double_height_band_values():
    d = _o()["a_double_height"]
    assert d["gf_solid_under_lm"] == "3.997201"
    assert d["plaster_band"]["m2"] == ["0.839412", "0.870912"]
    assert d["paint_band"]["m2"] == ["3.344721", "3.525121"]
    assert [h["lm"] for h in d["held_beam_faces"]] == ["3.020000", "4.000000"]
    assert all(h["m2"] is None for h in d["held_beam_faces"])           # held, never 0


def test_returns_close():
    b = _o()["b_returns"]["bridge"]
    assert b["gap"] == "-8.190000" and b["engine"] == "24.150000" and b["engine_count"] == 27
    for c, u in zip(b["count_term"], reversed(b["unit_term"])):
        assert Decimal(c) + Decimal(u) == Decimal("-8.190000")


def test_return_paint_census():
    c = _o()["c_return_paint"]
    assert c["count"] == 30 and c["valued"] == 27 and c["held_by_name"] == 3
    assert c["bound_sum_m2"] == ["0.000000", "24.150000"]
    assert c["physical_high_without_both_wet_and_external_side"] == "19.170000"
    assert c["physical_high_without_both_wet"] == "20.250000"
    assert all(r["paint_row"]["value"] is None for r in c["rows"])
    assert sum(1 for r in c["rows"] if r["paint_row"]["flag"].startswith("NOT_ESTABLISHED")) == 5


def test_dry_rooms():
    o = _o()
    rooms = {r["room"]: r for r in o["d_dry_rooms"]}
    assert len(rooms) == 9 and o["d_counts"]["re_measured"] == 6
    for rid in ("GF-01", "GF-15", "1F-01", "1F-10", "1F-11", "2F-03"):
        assert abs(Decimal(rooms[rid]["drawn_minus_engine_lm"])) <= Decimal("0.003")
    assert [f["id"] for f in o["d_findings"]] == ["W12"] and o["d_findings"][0]["ledger_minus_own"] == "-0.010824"

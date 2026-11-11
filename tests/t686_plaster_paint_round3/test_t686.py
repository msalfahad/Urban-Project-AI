"""T-686 plaster / paint round 3 (R-T686-1 .. -4): synthetic villa V686 by hand (normal + adverse) and the development
villa pinned to the committed outputs.

Villa V686 (synthetic, not the development villa), by hand. Annex room on FFL +0.20 under a roof mark +4.00 whose slab
top is bounded 3.40 .. 4.00; slab 0.15; owner G1 beam 0.60 + ceiling 0.15.
  plaster soffit S = s - 0.15 - 0.20 = 3.05 .. 3.65; paint / tile top H = s - 0.75 - 0.20 = 2.45 .. 3.05
  contour 10.00 m; door 0.90 head 2.10 (exact 1.89 both ends); window 1.20 hole 1.50 sill unknown;
  arch 1.00 height not printed
  low  = 10 x 2.45 - 1.89 - 1.20 x min(1.50, 2.45) - 1.00 x 2.45 = 24.50 - 1.89 - 1.80 - 2.45 = 18.36
  high = 10 x 3.05 - 1.89 - 1.20 x (1.50 - (3.65 - 3.05)) - 0      = 30.50 - 1.89 - 1.08       = 27.53
Wet room with no ceiling datum: head 2.10, G1 ceiling +4.40 absolute, floor +0.20 or +0.90 -> top 2.10 .. 4.20.
Adverse: datum low > high, a level in mm, no source, paint on a tiled face, a head above the soffit, openings wider
than the room, a non-positive low, a room with no established head (HELD, never 0), a raster-only height, two vector
records that disagree: refused. Mirror: the openings in reverse order give the same bound.
"""
import importlib.util
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t686"
sys.path.insert(0, str(HERE))
import t686_rules as R  # noqa: E402

OUT = HERE / "out" / "T686_ROUND3.json"
SRC = "V686 sheet"


def heights():
    return R.finish_heights(("3.40", SRC), ("4.00", SRC), ("0.20", SRC), ("0.15", SRC), ("0.60", SRC), ("0.15", SRC))


def ops():
    return [{"id": "DR", "width": "0.90", "sill": "0", "head": "2.10", "source": SRC},
            {"id": "WN", "width": "1.20", "height": "1.50", "source": SRC},
            {"id": "AR", "width": "1.00", "source": SRC}]


def test_heights_by_hand():
    h = heights()
    assert h["S"] == (Decimal("3.05"), Decimal("3.65"))
    assert h["H"] == (Decimal("2.45"), Decimal("3.05"))


def test_band_bound_by_hand():
    h = heights()
    b = R.band_bound(("10.00", SRC), h["H"], h["S"], ops(), "PLASTER")
    assert (Decimal(b["low"]), Decimal(b["high"])) == (Decimal("18.36"), Decimal("27.53"))
    assert Decimal(b["deducted_at_low"]) == Decimal("6.14") and Decimal(b["deducted_at_high"]) == Decimal("2.97")


def test_mirror_same_bound():
    h = heights()
    a = R.band_bound(("10.00", SRC), h["H"], h["S"], ops(), "PAINT")
    b = R.band_bound(("10.00", SRC), h["H"], h["S"], list(reversed(ops())), "PAINT")
    assert a == b


def test_exact_window_clipped_to_band():
    o = {"id": "W", "width": "1.50", "sill": "1.00", "head": "2.50", "source": SRC}
    assert R.opening_portion(o, Decimal("2.45"), Decimal("3.05")) == (Decimal("2.175000"),) * 2
    assert R.opening_portion(o, Decimal("3.05"), Decimal("3.65")) == (Decimal("2.250000"),) * 2


def test_wet_room_tile_top_by_hand():
    lo, hi = R.wet_room_tile_top([("2.10", SRC)], ("4.40", SRC), [("0.20", SRC), ("0.90", SRC)])
    assert (lo, hi) == (Decimal("2.10"), Decimal("4.20"))


@pytest.mark.parametrize("args", [
    (("4.10", SRC), ("4.00", SRC)),          # datum low > high
    (("3400", SRC), ("4000", SRC)),          # millimetres read as metres
    (("3.40", ""), ("4.00", SRC)),           # no source
])
def test_datum_refused(args):
    with pytest.raises(R.RuleError):
        R.finish_heights(args[0], args[1], ("0.20", SRC), ("0.15", SRC), ("0.60", SRC), ("0.15", SRC))


def test_paint_on_tiled_face_refused():
    h = heights()
    with pytest.raises(R.RuleError, match="tiled"):
        R.band_bound(("10.00", SRC), h["H"], h["S"], ops(), "PAINT", face_finish="TILED")


def test_head_above_soffit_refused():
    h = heights()
    bad = [{"id": "W", "width": "1.0", "sill": "1.0", "head": "3.20", "source": SRC}]
    with pytest.raises(R.RuleError, match="above the soffit"):
        R.band_bound(("10.00", SRC), h["H"], h["S"], bad, "PLASTER")


def test_openings_wider_than_room_refused():
    h = heights()
    with pytest.raises(R.RuleError, match="wider"):
        R.band_bound(("2.00", SRC), h["H"], h["S"], ops(), "PLASTER")


def test_non_positive_low_refused():
    h = heights()
    big = [{"id": "A", "width": "1.00", "source": SRC}]
    with pytest.raises(R.RuleError, match="<= 0"):
        R.band_bound(("1.00", SRC), h["H"], h["S"], big, "PLASTER")


def test_room_without_head_stays_held():
    with pytest.raises(R.RuleError, match="HELD"):
        R.wet_room_tile_top([], ("4.40", SRC), [("0.20", SRC)])


def test_g1_below_head_refused():
    with pytest.raises(R.RuleError, match="refused"):
        R.wet_room_tile_top([("2.10", SRC)], ("2.80", SRC), [("0.20", SRC), ("0.90", SRC)])


def test_raster_only_refused_and_vector_governs():
    with pytest.raises(R.RuleError, match="raster"):
        R.governing_height([{"id": "r", "kind": "RASTER", "sill": "1", "head": "2.5"}])
    g, res = R.governing_height([{"id": "v", "kind": "VECTOR", "sill": "1.00", "head": "2.50", "tol": "0.01"},
                                 {"id": "r", "kind": "RASTER", "sill": "1.10", "head": "2.86"}])
    assert g["id"] == "v" and Decimal(res[0]["height_difference_m"]) == Decimal("0.26")
    with pytest.raises(R.RuleError, match="disagree"):
        R.governing_height([{"id": "v", "kind": "VECTOR", "sill": "1.00", "head": "2.50", "tol": "0.01"},
                            {"id": "w", "kind": "VECTOR", "sill": "1.00", "head": "2.60", "tol": "0.01"}])


# ---- development villa (committed outputs) --------------------------------------------------------------------

def _out():
    return json.loads(OUT.read_text())


def test_builder_check_matches():
    r = subprocess.run([sys.executable, "-I", str(HERE / "t686_alsenan.py"), "--check"], capture_output=True,
                       text=True, cwd=ROOT)
    assert r.returncode == 0, r.stdout + r.stderr


def test_dev_villa_counts_and_totals():
    t = _out()["code_totals_m2"]
    assert t["FIN.PLASTER"]["v3_0_66"]["blank"] == 10 and t["FIN.PAINT"]["v3_0_66"]["blank"] == 3
    assert t["FIN.PLASTER"]["after_round3"] == {"bounded": 21, "blank": 3, "low": "1078.344516",
                                                "high": "1202.87991"}
    assert t["FIN.PAINT"]["after_round3"] == {"bounded": 10, "blank": 0, "low": "601.645338", "high": "682.3313"}


def test_dev_villa_lines_held_never_released():
    r = _out()
    assert len(r["lines"]) == 8
    for l in r["lines"]:
        assert l["class"] == "HELD" and l["measured_net"] is None
        assert 0 < Decimal(l["held_low"]) <= Decimal(l["held_high"])
    assert r["annex_datum"]["owner_manual_3_15_inside"] is True
    for e in r["reveals_still_blank"]:
        assert e["held_low"] is None and e["missing_datum"]


def test_dev_villa_kitchen_by_hand():
    k = [l for l in _out()["lines"] if l["room"] == "GF-06"][0]
    # 14.5 x 2.494 - W08 1.501 x (2.494 - 1.0) - D-GF-05 1.0 x 2.2 ; 14.5 x 3.25 - 1.501 x 1.5 - 2.2
    assert Decimal(k["held_low"]) == Decimal("14.5") * Decimal("2.494") - Decimal("1.501") * Decimal("1.494") - \
        Decimal("2.2")
    assert Decimal(k["held_high"]) == Decimal("14.5") * Decimal("3.25") - Decimal("1.501") * Decimal("1.5") - \
        Decimal("2.2")

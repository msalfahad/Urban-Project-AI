"""T-690 tiles round 2 (R-T690-1 .. -3): synthetic villa K690 by hand (normal + adverse) and the development villa
pinned to the committed outputs.

Villa K690 (synthetic, not the development villa), by hand.
  Closed bath: faces 10.00 m, soffit S 3.20, tile top H 2.70 (band 0.50); door 0.90 head 2.10 (below H: 0);
  window 0.60 sill 1.50 head 2.90 (inside the band 0.60 x 0.20 = 0.12): band = 5.00 - 0.12 = 4.88.
  Crossing beam 0.25 x 0.60, slab 0.15 (0.45 below the soffit, inside the 0.50 band): 2 ends x 0.25 x 0.45 = 0.225
  -> 4.655; open-sided room: ends 0 .. 2 -> 4.655 .. 4.88.
  Coupled datum (annex type): slab top s 3.50 .. 3.60, FFL 0, slab 0.15, beam 0.55 + ceiling 0.15:
  S = s - 0.15, H = s - 0.70 -> band height 0.55 on every point; faces 4.00 -> 2.20 exactly (independent extremes would
  wrongly give 4 x 0.45 .. 4 x 0.65 = 1.80 .. 2.60); joint plaster to S 4 x 3.35 .. 4 x 3.45 = 13.40 .. 13.80.
  Floor + roof segments: 6.00 m under a floor slab (S 3.00, H 2.50) + 4.00 m under a roof (S 2.70 .. 3.00):
  3.00 + 0.80 .. 2.00 = 3.80 .. 5.00.
Adverse: a wet room with no printed ceiling height (H missing) stays HELD (never 0); a tile top above the soffit, a level
in millimetres, a zero length, an opening head above the soffit, deductions larger than the band, an unknown opening
(bounded 0 .. w x band, never a guess); census on a changed line refused; a wiring gap whose stretch a neighbour carries
refused. Mirror: faces / openings in reverse order give the same bound.
"""
import json
import subprocess
import sys
from decimal import Decimal as Dd
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t690"
sys.path.insert(0, str(HERE))
import t690_rules as R  # noqa: E402

DOOR = {"id": "D1", "width": "0.90", "sill": "0", "head": "2.10"}
WIN = {"id": "W1", "width": "0.60", "sill": "1.50", "head": "2.90"}
BEAM = {"id": "B1", "b": "0.25", "h": "0.60", "slab": "0.15", "ends": (2, 2)}


def test_closed_bath_window_inside_band():
    lo, hi, g = R.band_at("10.00", "3.20", "2.70", [DOOR, WIN])
    assert (lo, hi, g) == (Dd("4.88"), Dd("4.88"), Dd("5.00"))


def test_beam_ends_closed_and_open_room():
    lo, hi, _ = R.band_at("10.00", "3.20", "2.70", [DOOR, WIN], [BEAM])
    assert lo == hi == Dd("4.655")
    lo, hi, _ = R.band_at("10.00", "3.20", "2.70", [DOOR, WIN], [{**BEAM, "ends": (0, 2)}])
    assert (lo, hi) == (Dd("4.655"), Dd("4.88"))


def test_beam_deeper_than_band_is_cut_at_the_band():
    lo, hi, _ = R.band_at("10.00", "3.20", "2.70", [], [{**BEAM, "h": "0.90"}])
    assert lo == Dd("5.00") - 2 * Dd("0.25") * Dd("0.50")


def test_coupled_datum_not_independent_extremes():
    pts = [(s - Dd("0.15"), s - Dd("0.70")) for s in R.datum_grid("3.50", "3.60")]
    assert len(pts) == 101
    r = R.band_over_points("4.00", pts)
    assert (r["low"], r["high"]) == (Dd("2.20"), Dd("2.20"))
    assert R.joint_total("4.00", pts, []) == (Dd("13.40"), Dd("13.80"))


def test_floor_and_roof_segments_add():
    r = R.room_band([(Dd("6.00"), [("3.00", "2.50")]), (Dd("4.00"), [("2.70", "2.50"), ("3.00", "2.50")])])
    assert (r["low"], r["high"]) == (Dd("3.80"), Dd("5.00"))


def test_unknown_opening_is_a_bound():
    lo, hi, _ = R.band_at("10.00", "3.20", "2.70", [{"id": "A1", "width": "1.00"}])
    assert (lo, hi) == (Dd("4.50"), Dd("5.00"))
    lo, hi, _ = R.band_at("10.00", "3.20", "2.70", [{"id": "W5", "width": "0.60", "cap_m2": "0.10"}])
    assert (lo, hi) == (Dd("4.90"), Dd("5.00"))


def test_mirror_order_invariant():
    a = R.band_at("10.00", "3.20", "2.70", [DOOR, WIN], [BEAM])
    b = R.band_at("10.00", "3.20", "2.70", [WIN, DOOR], [BEAM])
    assert a == b


def test_band_zero_when_ceiling_at_soffit_is_calculated():
    assert R.band_at("5.00", "2.70", "2.70") == (0, 0, 0)


@pytest.mark.parametrize("args,exc", [
    (("10.00", "3.20", None), R.Held),                 # wet room with no printed ceiling / tile height
    (("10.00", None, "2.70"), R.Held),                 # soffit not established
    (("10.00", "2.60", "2.70"), R.RuleError),          # tile top above the soffit
    (("10.00", "3200", "2700"), R.RuleError),          # millimetres
    (("0", "3.20", "2.70"), R.RuleError),              # no face
])
def test_adverse_band(args, exc):
    with pytest.raises(exc):
        R.band_at(*args)


def test_adverse_openings_and_deductions():
    with pytest.raises(R.RuleError):
        R.band_at("10.00", "3.20", "2.70", [{"id": "W9", "width": "0.6", "sill": "2.0", "head": "3.50"}])
    with pytest.raises(R.RuleError):
        R.band_at("1.00", "3.20", "2.70", [{"id": "W9", "width": "0.9", "sill": "2.0", "head": "3.20"}],
                  [{**BEAM, "b": "1.0"}])
    with pytest.raises(R.RuleError):
        R.band_at("10.00", "3.20", "2.70", [], [{**BEAM, "ends": (0, 3)}])
    with pytest.raises(R.Held):
        R.band_over_points("4.00", [])


def test_census_restated_and_refused():
    a = [{"line_id": "L-1", "item_code": "FIN.WALL.TILE", "class": "HELD"},
         {"line_id": "L-2", "item_code": "FIN.PAINT", "class": "HELD"}]
    b = [dict(x) for x in a]
    assert R.census_restated(a, b, lambda c: c == "FIN.WALL.TILE")
    b[1]["class"] = "RELEASED"     # outside the filter: still restated
    assert R.census_restated(a, b, lambda c: c == "FIN.WALL.TILE")
    b[0]["class"] = "RELEASED"
    with pytest.raises(R.RuleError):
        R.census_restated(a, b, lambda c: c == "FIN.WALL.TILE")
    with pytest.raises(R.RuleError):
        R.census_restated(a, a + [{"line_id": "L-3", "item_code": "FIN.WALL.TILE"}], lambda c: c == "FIN.WALL.TILE")


def test_wiring_gap():
    held = {"line_id": "L-9", "class": "HELD"}
    nb = {"line_id": "L-8", "class": "RELEASED"}
    r = R.wiring_gap_close(held, "EXCLUDED", [(nb, False, "width deducted, no return")])
    assert r["after"].startswith("EXCLUDED")
    with pytest.raises(R.RuleError):
        R.wiring_gap_close(held, "EXCLUDED", [(nb, True, "carries the returns")])
    with pytest.raises(R.RuleError):
        R.wiring_gap_close(nb, "EXCLUDED", [])
    with pytest.raises(R.RuleError):
        R.wiring_gap_close(held, "RELEASED", [])


def test_development_villa_pinned():
    out = subprocess.run([sys.executable, "-I", str(HERE / "t690_alsenan.py"), "--check"], capture_output=True,
                         text=True, cwd=ROOT)
    assert out.returncode == 0, out.stdout + out.stderr
    r = json.loads((HERE / "out" / "T690_TILES_ROUND2.json").read_text())
    c = r["c_wet_band"]
    assert c["annex_gross_m2"] == "20.532"
    assert len(c["rooms"]) == 18
    assert r["a_census"]["held_count"] == 104
    assert r["d_nosing"]["own_lm"] == "1.150"
    for o in c["rooms"]:
        assert Dd(o["band_low_m2"]) > 0 and Dd(o["band_low_m2"]) <= Dd(o["band_high_m2"])

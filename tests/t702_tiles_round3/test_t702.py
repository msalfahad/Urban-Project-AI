"""T-702 tiles round 3 (R-T702-1 .. -5): synthetic villa K702 by hand (normal + adverse) and the development villa
pinned to the committed outputs.

Villa K702 (synthetic, not the development villa), by hand.
  Roof 10.00 x 8.00 = 80.00 m2 with three printed layers: falls screed 0.05 -> 80 x 0.05 = 4.000 m3; insulation 0.05
  printed -> 80.00 m2 on the parapet faces; finish 78.00 m2 to its hatch. Unprinted insulation -> UNKNOWN (HELD, no
  number). A screed with only its falls wedge -> AT_LEAST 1.200 .. OPEN; a located cap 0.20 -> high 80 x 0.20 = 16.00.
  Beam crossings: b 0.20 square -> 0.20; at 45 deg -> 0.20 x sqrt 2 = 0.282843; b 0.90 crossing a face at 53.13 deg
  (sin 0.8) -> 1.125.
  Wet room (S 4.29, H 3.65, band 0.64): free faces 6.00 -> 3.84; a 20 x 75 beam over 0.20 of face (depth 0.59) leaves
  a 0.05 strip -> 0.010; 1.00 m under a sunken panel -> 0 .. 0.64; 2.00 m under a roof S 3.65 .. 4.34 -> 0 .. 1.38.
  Room 3.85 .. 5.87 (6 x 0.64 + 0.01 = 3.85; + 0.64 + 1.38 = 5.87).
Adverse: a landing claimed by floor finish and B7-04 refused; a cap cited but not located refused; AT_LEAST above a
cap refused; a beam parallel to the face refused; a tile top above the soffit refused; a missing roof soffit HELD;
a blank backing line leaves the tile line blank (never 0); a printed tile top different from the backing HELD; a float
refused (units / precision); order of stretches does not change the bound (mirror).
"""
import importlib
import json
import sys
from decimal import Decimal as Dd
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t702"
sys.path.insert(0, str(HERE))
import t702_rules as R  # noqa: E402


def test_roof_three_printed_layers():
    sc = R.layer_row("K", "FALLS_SCREED", area="80.00", printed_thickness="0.05", owner_rule="Q-41")
    assert sc["state"] == "MEASURED" and sc["quantity"] == Dd("4.000") and sc["unit"] == "m3"
    ins = R.layer_row("K", "INSULATION", area="80.00", area_edge="parapet faces", printed_thickness="0.05")
    assert ins["state"] == "MEASURED" and ins["quantity"] == Dd("80")
    fin = R.layer_row("K", "FINISH", area="78.00", area_edge="hatch")
    assert fin["quantity"] == Dd("78")


def test_unprinted_insulation_is_unknown_not_zero():
    r = R.layer_row("K", "INSULATION", area="80.00", area_edge="parapet faces")
    assert r["state"] == "UNKNOWN" and r["quantity"] is None


def test_screed_at_least_open_and_located_cap():
    r = R.layer_row("K", "FALLS_SCREED", owner_rule="Q-41", at_least_m3="1.200")
    assert (r["low"], r["high"]) == (Dd("1.2"), None)
    r = R.layer_row("K", "FALLS_SCREED", owner_rule="Q-41", area="80.00", at_least_m3="1.200",
                    cap=("0.20", True, "sheet 9 section dim"))
    assert r["high"] == Dd("16")


def test_cap_not_located_is_refused():
    with pytest.raises(R.RuleError, match="not located"):
        R.layer_row("K", "FALLS_SCREED", owner_rule="Q-41", area="80", cap=("0.30", False, "cited note"))


def test_at_least_above_cap_refused():
    with pytest.raises(R.RuleError, match="AT_LEAST above the cap"):
        R.layer_row("K", "FALLS_SCREED", owner_rule="Q-41", area="10", at_least_m3="5", cap=("0.30", True, "dim"))


def test_crossing_lengths_by_hand():
    assert R.crossing_length("0.20", "1") == Dd("0.20")
    assert abs(R.crossing_length("0.20", str(Dd(2).sqrt() / 2)) - Dd("0.282843")) < Dd("0.000001")
    assert R.crossing_length("0.90", "0.8") == Dd("1.125")
    with pytest.raises(R.RuleError):
        R.crossing_length("0.20", "0")


def test_room_band_by_hand_and_mirror():
    beams = [("0.20", "0.75", "0.16", False), ("0.30", "0.85", "0.16", False)]
    lo, hi = R.room_band("6.00", beams, "1.00", "2.00", "4.29", "3.65", roof_S=("3.65", "4.34"))
    assert (lo, hi) == (Dd("3.85"), Dd("5.87"))
    lo2, hi2 = R.room_band("6.00", list(reversed(beams)), "1.00", "2.00", "4.29", "3.65", roof_S=("4.34", "3.65"))
    assert (lo2, hi2) == (lo, hi)  # mirror: order of stretches / bound ends never matters


def test_unprinted_beam_top_strip_is_bounded():
    lo, hi = R.room_band("0", [("0.282868", "0.75", "0.16", True)], "0", "0", "4.29", "3.65")
    assert (lo, hi) == (Dd("0"), Dd("0.014143"))


def test_missing_roof_soffit_held_and_conflict_refused():
    with pytest.raises(R.Held):
        R.room_band("1", [], "0", "2.0", "4.29", "3.65")
    with pytest.raises(R.RuleError, match="data conflict"):
        R.band_on_stretch("1", "3.00", "3.65")
    with pytest.raises(R.RuleError, match="float"):
        R.band_on_stretch(1.0, "4.29", "3.65")


def test_one_owner_per_surface():
    assert R.single_owner([("hall", "FLOOR", None), ("LD", "B7-04", None)]) == {"hall": "FLOOR", "LD": "B7-04"}
    with pytest.raises(R.RuleError, match="claimed by"):
        R.single_owner([("LD", "B7-04", "L-1"), ("LD", "FLOOR", "L-2")])


def test_tile_follows_backing():
    assert R.tile_follows_backing({"class": "HELD", "held_low": "11.4", "held_high": "25.21",
                                   "measured_net": None}) == {"class": "HELD", "held_low": Dd("11.4"),
                                                              "held_high": Dd("25.21")}
    with pytest.raises(R.Held):
        R.tile_follows_backing({"class": "HELD", "held_low": None, "held_high": None, "measured_net": None})
    with pytest.raises(R.Held):
        R.tile_follows_backing({"class": "HELD", "held_low": "1", "held_high": "2", "measured_net": None},
                               printed_tile_top="2.40")


# ---------------------------------------------------------------- development villa (committed outputs)

@pytest.fixture(scope="module")
def built():
    B = importlib.import_module("t702_alsenan")
    return B, B.build()


def test_outputs_reproduce(built):
    B, d = built
    js = json.dumps(d, indent=1, sort_keys=True, default=str) + "\n"
    assert (HERE / "out" / "T702_TILES_ROUND3.json").read_text() == js
    assert (HERE / "out" / "T702_TILES_ROUND3.md").read_text() == B.md(d)


def test_development_villa_figures(built):
    _, d = built
    assert d["d_census_before"]["held"] == 104 and d["d_census_before"]["identical_v3066_v3069"]
    rooms = {r["room"]: r for r in d["c_beam_crossings"]["rooms"]}
    assert rooms["GF-07"]["after"]["band"] == ["0.499037", "6.186806"]
    assert rooms["GF-14"]["after"]["band"] == ["3.892324", "5.005988"]
    assert d["b_stair_core"]["wall_tile_total"] == ["18.44", "44.765"]
    assert d["a_roof_layers"]["cap_b_roof_030"].startswith("REFUSED")
    assert d["a_roof_layers"]["falls_once"]["tile_bed_lines_on_roof_zones"] == []
    held_blank = [r for r in d["a_roof_layers"]["rows"] if r["t702"].get("quantity") is None]
    assert all(r["v3069"]["class"] == "HELD" for r in held_blank)  # nothing unprinted became a number


def test_held_never_zero_in_outputs(built):
    _, d = built
    for r in d["a_roof_layers"]["rows"]:
        assert r["t702"].get("quantity") not in ("0", 0)


def test_census_refused_when_a_tile_line_changed(built):
    B, _ = built
    v69, v66, t681 = B.load("v3069"), B.load("v3066"), B.load("t681")
    changed = json.loads(json.dumps(v69))
    ln = next(l for l in changed["lines"] if l["item_code"] == "FIN.WALL.TILE" and l["class"] == "HELD")
    ln["held_low"] = 1.0
    with pytest.raises(R.RuleError, match="rebuilt"):
        B.census(changed, v66, t681)

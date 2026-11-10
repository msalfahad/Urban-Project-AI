"""T-681 tiles and adhesive HELD census (R-T681-1 .. -3): synthetic villa W681 by hand (normal + adverse) and the
development villa pinned to the committed outputs.

Villa W681 (synthetic, not the development villa), by hand, absolute levels in metres:
  stair flight beside window A, sill +3.10 / head +5.40; treads on the stretch +3.25 .. +3.90, plan 0.90 m
      -> every junction inside the opening: NOT_APPLICABLE, 0 lm (full deduction)
  landing +4.20 beside window B, sill +2.80 / head +3.95, plan 1.10 m, wall drawn above the head
      -> junction on solid wall: FULL 1.10 lm
  landing +1.00 below window C sill +1.30, plan 0.80: skirting height not sourced -> HELD; with h 0.10 -> FULL 0.80
  floor 12.00 m2 in 60 x 60 -> 12 / 5 = 2.4 bags; wall 9.00 m2 in 120 x 60 -> 9 / 3 = 3.0 bags; group 5.4 -> 6 bags
  floor 10.00 m2, size not sourced -> HELD bound 10 / 5 .. 10 / 3 = 2 .. 3.333333 bags
  bed 0.30 .. 0.40 m3 at 1:4 -> cement 2.4 .. 3.2 bags, sand 0.33 .. 0.44 m3 (waste separate)
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t681"))
import t681_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t681" / "out" / "T681_TILES_CENSUS.json"


# --- R-T681-2 skirting at an opening ---------------------------------------------------------------------------

def test_flight_inside_window_is_not_applicable():
    r = R.skirting_at_opening("3.25", "3.90", "3.10", "5.40", "0.90")
    assert r["state"] == "NOT_APPLICABLE" and r["length_lm"] == "0"


def test_landing_above_head_is_full():
    r = R.skirting_at_opening("4.20", "4.20", "2.80", "3.95", "1.10", wall_above_head=True)
    assert r == {**r, "state": "FULL", "length_lm": "1.1"}


def test_above_head_without_drawn_wall_stays_held():
    assert R.skirting_at_opening("4.20", "4.20", "2.80", "3.95", "1.10")["state"] == "HELD"


def test_below_sill_needs_a_sourced_height():
    assert R.skirting_at_opening("1.00", "1.00", "1.30", "2.50", "0.80")["state"] == "HELD"
    r = R.skirting_at_opening("1.00", "1.00", "1.30", "2.50", "0.80", skirting_height="0.10")
    assert r["state"] == "FULL" and r["length_lm"] == "0.8"
    # a band that does not clear the sill is never FULL
    assert R.skirting_at_opening("1.25", "1.25", "1.30", "2.50", "0.80", skirting_height="0.10")["state"] == "HELD"


def test_stretch_straddling_the_sill_or_head_is_held():
    assert R.skirting_at_opening("2.90", "3.40", "3.10", "5.40", "0.90")["state"] == "HELD"
    assert R.skirting_at_opening("5.00", "5.60", "3.10", "5.40", "0.90")["state"] == "HELD"


def test_tread_at_the_sill_counts_inside_within_tolerance():
    assert R.skirting_at_opening("2.997", "2.997", "3.00", "4.00", "1.00")["state"] == "NOT_APPLICABLE"
    assert R.skirting_at_opening("2.990", "2.990", "3.00", "4.00", "1.00")["state"] == "HELD"


@pytest.mark.parametrize("args", [
    (None, "3.90", "3.10", "5.40", "0.90"),            # missing level: never 0
    ("3250", "3900", "3100", "5400", "900"),           # millimetres passed as metres
    ("3.25", "3.90", "5.40", "3.10", "0.90"),          # head below sill
    ("3.25", "3.90", "3.10", "5.40", "0"),             # no plan length
    ("3.90", "3.25", "3.10", "5.40", "0.90"),          # z_max below z_min
])
def test_adverse_inputs_are_refused(args):
    with pytest.raises(R.RuleError):
        R.skirting_at_opening(*args)


# --- R-T681-3 materials ----------------------------------------------------------------------------------------

def test_adhesive_by_size_and_one_group_ceil():
    f = R.adhesive("12.00", "12.00", "60x60")
    w = R.adhesive("9.00", "9.00", "120x60")
    assert f["bags"] == ["2.4", "2.4"] and w["bags"] == ["3", "3"]
    g = R.group_bags([f, w])
    assert g["status"] == "CALCULATED" and g["bags_low"] == g["bags_high"] == 6 and g["exact_low"] == "5.4"


def test_adhesive_size_not_printed_stays_held_with_bound():
    a = R.adhesive("10.00", "10.00", None)
    assert a["status"] == "HELD" and a["bags"] == ["2", "3.333333"]
    g = R.group_bags([a, R.adhesive("12", "12", "60x60")])
    assert g["status"] == "HELD" and (g["bags_low"], g["bags_high"]) == (5, 6)


def test_adhesive_unknown_size_refused_and_blank_host_held():
    with pytest.raises(R.RuleError):
        R.adhesive("10", "10", "30x30")
    a = R.adhesive(None, None, "60x60")
    assert a["status"] == "HELD" and a["bags"] is None
    assert R.group_bags([a])["blank_rows"] == 1


def test_bed_materials_and_held_bed():
    b = R.bed_materials("0.30", "0.40")
    assert b["cement_bags"] == ["2.4", "3.2"] and b["sand_m3"] == ["0.33", "0.44"]
    assert R.bed_materials(None, "0.4")["status"] == "HELD"


# --- R-T681-1 census --------------------------------------------------------------------------------------------

def _e(lid, lo=None, hi=None, cls="OWNER_OPEN"):
    return {"line_id": lid, "item_code": "FIN.WALL.TILE", "unit": "m2", "held_low": lo, "held_high": hi, "class": cls}


def test_census_totals_keep_blank_apart():
    t = R.census([_e("a", "1.5", "2.5"), _e("b")], ["a", "b"])["FIN.WALL.TILE [m2]"]
    assert (t["low"], t["high"], t["blank"], t["bounded"]) == ("1.5", "2.5", 1, 1)
    t = R.census([_e("b")], ["b"])["FIN.WALL.TILE [m2]"]
    assert t["low"] is None and t["high"] is None  # all blank: never 0


def test_census_refuses_duplicates_missing_and_unknown_class():
    with pytest.raises(R.RuleError):
        R.census([_e("a"), _e("a")], ["a", "a"])
    with pytest.raises(R.RuleError):
        R.census([_e("a")], ["a", "b"])
    with pytest.raises(R.RuleError):
        R.census([_e("a", cls="GUESS")], ["a"])


# --- development villa (pinned outputs) ------------------------------------------------------------------------

def test_alsenan_outputs_rebuild_identically():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t681/t681_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_alsenan_census_is_complete_and_classed():
    r = json.loads(OUT.read_text())
    assert r["count"] == 104 == sum(r["by_class"].values())
    assert r["by_class"] == {"DESIGNER_ITEM": 7, "MEASURABLE_NOW": 6, "OPEN_BOUND": 44, "OWNER_OPEN": 46,
                             "WIRING_GAP": 1}
    assert all(e["class"] in R.CLASSES for e in r["entries"])


def test_alsenan_fix_rows():
    f = {x["line_id"]: x for x in json.loads(OUT.read_text())["fix_rows"]}
    assert f["L-760bfa8dd00061361695"]["state"] == "FULL" and f["L-760bfa8dd00061361695"]["length_lm"] == "1"
    assert f["L-760bfa8dd00061361695"]["adverse"]["state"] == "FULL"  # raster head +7.36 still below +7.684
    na = [k for k, v in f.items() if v["state"] == "NOT_APPLICABLE"]
    assert len(na) == 5 and all(f[k]["length_lm"] == "0" for k in na)


def test_alsenan_materials_held_not_zero():
    m = json.loads(OUT.read_text())["materials"]
    g = [v for k, v in m.items() if k.startswith("ADHESIVE")][0]
    assert g["status"] == "HELD" and (g["bags_low"], g["bags_high"]) == (149, 248)
    assert m["FIN.FLOOR.BED.DRY [m3]"]["bed_1_4"]["cement_bags"] == ["72.364432", "96.485912"]
    assert m["FIN.WALL.TILE [m2]"]["held_blank"] == 6

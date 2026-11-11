"""T-710 waterproofing round 3 (R-T710-1 .. -3): synthetic villa W710 by hand (normal + adverse) and the development
villa pinned to the committed outputs.

Villa W710 (synthetic, not the development villa), by hand:
  bath 2.00 x 2.50 = 5.000 m2, one door 0.90: upturn run 9.00 - 0.90 = 8.10 m x 0.20 = 1.620 m2
  sunken panel 1.80 x 2.50 inside it, touching three faces (W, S, N), its east edge 0.20 inside the room:
    recess loop 2 x (1.80 + 2.50) = 8.60 m = along faces 1.80 + 2.50 + 1.80 = 6.10 + free step 2.50
  boundary beams 20 x 40 and 20 x 60, slab 0.16: d_max = 0.40 - 0.16 = 0.24 m
  extra membrane HELD 0 .. 8.60 x 0.24 = 2.064 m2; with d printed 0.15 and a tray on the slab: 1.290 m2
  a store over the same panel strip (0.30 m2 of the panel) is floor-bed scope, never waterproofing
"""
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t710"))
import t710_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t710" / "out" / "T710_WP_ROUND3.json"


def test_upturn_normal():
    u = R.upturn(Decimal("9.00") - Decimal("0.90"), "0.20")
    assert (u["status"], u["value"], u["run_m"]) == ("MEASURED", Decimal("1.620000"), Decimal("8.100000"))


def test_room_with_no_drawn_upturn_height_stays_held():
    u = R.upturn("8.10", None)
    assert u["status"] == "HELD" and u["value"] is None and u["run_m"] == Decimal("8.100000")
    assert R.upturn(None, "0.20")["status"] == "HELD"


def test_d_max_from_boundary_beams():
    assert R.d_max(["0.40", "0.60"], "0.16") == Decimal("0.24")


def test_d_max_unknown_beam_is_open_not_zero():
    assert R.d_max(["0.40", None], "0.16") is None
    assert R.d_max([], "0.16") is None
    assert R.d_max(["0.40"], None) is None


@pytest.mark.parametrize("hs,t", [(["400", "600"], "0.16"), (["0.40"], "160")])
def test_mm_read_as_m_refused(hs, t):
    with pytest.raises(ValueError):
        R.d_max(hs, t)


def test_beam_no_deeper_than_slab_refused():
    with pytest.raises(ValueError):
        R.d_max(["0.16"], "0.16")


def test_recess_held_bounds_normal():
    x = R.recess_wp("8.60", drop_max_m=R.d_max(["0.40", "0.60"], "0.16"))
    assert (x["status"], x["low"], x["high"], x["value"]) == ("HELD", Decimal("0"), Decimal("2.064000"), None)


def test_recess_with_printed_drop_and_tray():
    x = R.recess_wp("8.60", drop_m="0.15", membrane_position="ON_SLAB")
    assert (x["status"], x["value"]) == ("DRAWING-CONFIRMED", Decimal("1.290000"))
    y = R.recess_wp("8.60", drop_m="0.15")
    assert y["status"] == "HELD" and y["high"] == Decimal("1.290000") and y["value"] is None


def test_recess_membrane_on_fill_adds_nothing():
    x = R.recess_wp("8.60", membrane_position="ON_FILL")
    assert x["status"] == "DRAWING-CONFIRMED" and x["value"] == 0


def test_recess_unknown_d_max_high_open_never_zero():
    x = R.recess_wp("8.60")
    assert x["status"] == "HELD" and x["high"] is None and x["value"] is None


def test_recess_tray_without_drop_has_no_zero_low():
    x = R.recess_wp("8.60", drop_max_m="0.24", membrane_position="ON_SLAB")
    assert x["low"] is None and x["high"] == Decimal("2.064000")


@pytest.mark.parametrize("bad", [float("nan"), -1, "-0.2"])
def test_bad_lengths_refused(bad):
    with pytest.raises(ValueError):
        R.recess_wp(bad, drop_max_m="0.24")


def test_unknown_membrane_position_refused():
    with pytest.raises(ValueError):
        R.recess_wp("8.60", membrane_position="SOMEWHERE")


def test_panel_outside_wet_room_is_not_waterproofing():
    s = R.split_panel("4.80", "4.50")
    assert s == {"wp_scope_m2": Decimal("4.500000"), "outside_wet_m2": Decimal("0.300000")}
    with pytest.raises(ValueError):
        R.split_panel("4.50", "4.80")


def test_census_count_and_causes():
    e = [{"key": "a", "cause": "DESIGNER", "status": "HELD", "value": None},
         {"key": "b", "cause": "MEASURABLE_NOW", "status": "MEASURED_UNWIRED", "value": None}]
    assert R.census_check(e, 2) == {"DESIGNER": 1, "MEASURABLE_NOW": 1}
    with pytest.raises(ValueError):
        R.census_check(e, 3)
    with pytest.raises(ValueError):
        R.census_check([{"key": "c", "cause": "GUESS", "status": "HELD"}], 1)
    with pytest.raises(ValueError):
        R.census_check([{"key": "d", "cause": "DESIGNER", "status": "HELD", "value": 0}], 1)


# ---------------------------------------------------------------- development villa (pinned outputs)
def test_development_villa_outputs_pinned():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t710" / "t710_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "check PASS" in r.stdout, r.stdout + r.stderr


def test_development_villa_census_and_sunken_totals():
    o = json.loads(OUT.read_text())
    c = o["census"]
    assert (c["held"], c["missing"], len(c["rows"])) == (53, 5, 58)
    assert c["by_cause"] == {"DESIGNER": 46, "NEEDS_OWNER_RULE": 3, "MEASURABLE_NOW": 8, "NO_PHYSICAL_ELEMENT": 1}
    assert o["wp_lines_on_candidate"] == 160 and o["wp_lines_unchanged_since_v3066"] is True
    s = o["sunken"]
    assert s["recess_loop_total_m"] == "51.8980" and s["extra_high_total_m2"] == "13.335040"
    assert all(r["floor_verdict"] == "AGREE" and r["upturn_verdict"] == "AGREE" for r in s["rooms"])
    assert all(r["recess_wp_extra_m2"]["low"] == "0" for r in s["rooms"])   # HELD bounds, never a released 0
    assert {x["panel"] for x in s["outside_wet_rooms"]} == {"280", "287"}

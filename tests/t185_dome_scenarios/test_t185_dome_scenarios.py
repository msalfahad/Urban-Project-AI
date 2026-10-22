"""T-185 dome scenarios on hand-calculated synthetic domes (NOT Alsenan: other chords, rises, thicknesses, units).

Regression guards (ENGINEERING_REASONING_STANDARD s.4 C), each with a normal and an adverse case:
  - a client-requested removal that the consultant has not issued must not touch the approved-design baseline S0:
    the dome stays in S0, is absent in S1, S1 is never released, S2 is UNKNOWN without a revised drawing;
  - the shell is measured from the PRINTED chord / rise / thickness (never rise = radius, never a hemisphere of the
    rise, never a default thickness); a missing printed value stays HELD, never 0;
  - shell bars by population (hoops and meridians), not a kg/m2 rate.
"""

from __future__ import annotations

import copy
import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "t185_dome_scenarios", ROOT / "research" / "agents_t185" / "t185_dome_scenarios.py")
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)


def approx(x, tol=1e-9):
    return pytest.approx(x, abs=tol)


# ---------------------------------------------------------------- geometry, by hand

def test_hemisphere_shell_by_hand():
    # chord 4.00, rise 2.00 -> R_o = (4 + 4) / 4 = 2.00, centre on the springing plane; t 0.10 -> R_i 1.90, h_i 1.90
    g = D.shell_geometry(4.0, 2.0, 0.10)
    assert g["R_outer_m"] == approx(2.0)
    assert g["centre_below_springing_m"] == approx(0.0)
    # V = 2/3 pi (2.0^3 - 1.9^3) = 2/3 pi x 1.141
    assert g["volume_m3"] == approx(2.0 / 3.0 * math.pi * 1.141)
    assert g["outer_area_m2"] == approx(2 * math.pi * 2.0 * 2.0)
    assert g["inner_area_m2"] == approx(2 * math.pi * 1.9 * 1.9)


def test_shallow_cap_in_mm_by_hand():
    # chord 6000 mm, rise 1000 mm, t 120 mm: R_o = (3^2 + 1^2) / 2 = 5.00 m, centre 4.00 below the springing;
    # R_i = 4.88, h_i = 0.88; V = pi/3 [1^2 (15 - 1) - 0.88^2 (14.64 - 0.88)] = pi/3 x 3.344256
    dome = {"id": "X", "unit": "mm", "structural_detail": "detail X",
            "printed": {"chord": 6000, "rise": 1000, "thickness": 120}}
    led = D.scenario_ledger({"domes": [dome], "changes": []})
    shell = [x for x in led if x["item"] == "shell concrete"][0]
    assert shell["qty"] == approx(math.pi / 3.0 * 3.344256)
    assert shell["status"] == D.CONFIRMED
    same_in_m = D.shell_geometry(6.0, 1.0, 0.12)["volume_m3"]
    assert shell["qty"] == approx(same_in_m)          # units: mm and m give the same m3


def test_adverse_area_is_the_printed_cap_not_a_hemisphere_of_the_rise():
    # chord 6, rise 1: cap area 2 pi R h = 2 pi x 5 x 1 = 31.416; a 'hemisphere of the rise' 2 pi 1^2 = 6.283
    g = D.shell_geometry(6.0, 1.0, None)
    assert g["outer_area_m2"] == approx(10 * math.pi)
    assert g["outer_area_m2"] != approx(2 * math.pi * 1.0 ** 2)


def test_adverse_rise_is_never_the_radius_when_printed():
    # rise printed 1.0 on a 6.0 chord; a 'rise = radius' convention would use 3.0 and a hemisphere
    # printed: R_o 5.0, centre 4.0 below, R_i 4.9, h_i 0.9: V = pi/3 [1 (15 - 1) - 0.81 (14.7 - 0.9)] = pi/3 x 2.822
    # convention: hemisphere r 3.0: V = 2/3 pi (27 - 24.389) = 2/3 pi x 2.611 (+85 %)
    g = D.shell_geometry(6.0, 1.0, 0.10)
    hemi = D.shell_geometry(6.0, 3.0, 0.10)
    assert g["volume_m3"] == approx(math.pi / 3.0 * 2.822)
    assert hemi["volume_m3"] == approx(2.0 / 3.0 * math.pi * 2.611)
    assert g["volume_m3"] != approx(hemi["volume_m3"], 0.01)


def test_adverse_missing_thickness_is_held_never_a_default():
    dome = {"id": "Y", "unit": "m", "structural_detail": "detail Y", "printed": {"chord": 5.0, "rise": 1.5}}
    led = D.scenario_ledger({"domes": [dome], "changes": []})
    shell = [x for x in led if x["item"] == "shell concrete"][0]
    assert shell["qty"] is None and shell["status"] == D.HELD
    t = D.totals(led, "S0_APPROVED_DESIGN", "shell concrete", "m3")
    assert t["measured"] == 0 and t["open"] == ["Y"]  # left out of the sum and listed, not summed as 0


def test_adverse_no_structural_detail_is_held_even_with_architectural_sizes():
    dome = {"id": "Z", "unit": "m", "structural_detail": None,
            "printed": {"chord": 4.0, "rise": 2.0, "thickness": None}}
    led = D.scenario_ledger({"domes": [dome], "changes": []})
    shell = [x for x in led if x["item"] == "shell concrete"][0]
    assert shell["status"] == D.HELD and shell["qty"] is None
    outline = [x for x in led if x["item"].startswith("shell extrados")][0]
    assert outline["qty"] == approx(2 * math.pi * 2.0 * 2.0)   # geometry kept visible, concrete held


def test_missing_quantity_cannot_be_calculated_or_confirmed():
    with pytest.raises(D.DomeInputError):
        D._line("S0_APPROVED_DESIGN", "X", "shell concrete", "m3", None, D.CALC, "x")
    with pytest.raises(D.DomeInputError):
        D._line("S1_CLIENT_REQUESTED", "X", "shell concrete", "m3", 1.0, D.OMITTED, "x")


# ---------------------------------------------------------------- bar population, by hand

def test_hemisphere_bars_by_population():
    # chord 4, rise 2 -> centre on the springing plane; bar sphere 1.90: meridian arc s = 1.9 pi / 2 = 2.98451
    # hoops: N = ceil(2.98451 / 0.20) = 15 at theta = (pi/2) / 15; sum_{j=1..15} sin(j theta) by the closed form
    b = D.shell_bars(4.0, 2.0, 1.9, 0.20, 10)
    s = 1.9 * math.pi / 2
    assert b["meridian_arc_m"] == approx(s)
    assert b["hoop_count"] == 15
    th = (math.pi / 2) / 15
    sum_sin = math.sin(15 * th / 2) * math.sin(16 * th / 2) / math.sin(th / 2)
    assert b["hoop_length_m"] == approx(2 * math.pi * 1.9 * sum_sin)
    # meridians: ceil(2 pi 1.9 / 0.20) = ceil(59.69) = 60, each 2.98451 m
    assert b["meridian_count"] == 60
    assert b["meridian_length_m"] == approx(60 * s)
    assert b["kg_per_m"] == approx(100 / 162.0)
    # curtailed lower bound = bar-sphere cap area / spacing = 2 pi 1.9 x 1.9 / 0.20
    assert b["meridian_length_curtailed_lb_m"] == approx(2 * math.pi * 1.9 * 1.9 / 0.20)
    assert b["meridian_length_curtailed_lb_m"] < b["meridian_length_m"]


def test_adverse_bars_are_not_a_rate_over_the_area():
    # a rate (area / spacing for each direction) undercounts the meridians, which all reach the crown when drawn so
    b = D.shell_bars(4.0, 2.0, 1.9, 0.20, 10)
    rate_one_direction = 2 * math.pi * 1.9 * 1.9 / 0.20
    assert b["meridian_length_m"] > 1.2 * rate_one_direction


# ---------------------------------------------------------------- scenarios: S0 / S1 / S2

def _project(change=None, revised=None):
    dome = {"id": "D1", "unit": "m", "structural_detail": "detail 1", "printed": {"chord": 4.0, "rise": 2.0, "thickness": 0.10},
            "shell_bars": {"d_mm": 10, "spacing": 0.20, "stock_m": 12.0},
            "held_components": [{"item": "drum", "unit": "m3", "candidate": None, "reason": "material not printed"}]}
    p = {"domes": [dome], "changes": [], "revised_drawings": revised or []}
    if change:
        p["changes"].append(change)
    return p


CLIENT_REMOVAL = {"dome": "D1", "requested_by": "client", "kind": "REMOVE_SHELL", "issued_drawing": None,
                  "reference": "client meeting", "also_removes": ["drum"],
                  "s1_items": [{"item": "skylight glazing", "unit": "m2", "qty": None, "basis": "consultant"},
                               {"item": "open area", "unit": "m2", "qty": math.pi * 2.0 ** 2, "basis": "pi r^2"}]}


def test_client_removal_not_approved_keeps_s0_and_builds_s1_unreleased():
    led = D.scenario_ledger(_project(CLIENT_REMOVAL))
    s0 = D.totals(led, "S0_APPROVED_DESIGN", "shell concrete", "m3")
    s1 = D.totals(led, "S1_CLIENT_REQUESTED", "shell concrete", "m3")
    assert s0["measured"] == approx(2.0 / 3.0 * math.pi * 1.141)       # present in S0
    assert s1["measured"] == 0 and s1["open"] == []                       # absent in S1, by the scenario
    s1_lines = [x for x in led if x["scenario"] == "S1_CLIENT_REQUESTED"]
    assert s1_lines and not any(x["released"] for x in s1_lines)          # S1 not released
    assert any(x["item"] == "drum" and x["status"] == D.OMITTED for x in s1_lines)
    glazing = [x for x in s1_lines if x["item"] == "skylight glazing"][0]
    assert glazing["status"] == D.UNKNOWN and glazing["qty"] is None      # new scope never 0
    s2 = [x for x in led if x["scenario"] == "S2_CONSULTANT_REVISED"]
    assert len(s2) == 1 and s2[0]["status"] == D.UNKNOWN


def test_adverse_s0_is_identical_with_and_without_the_client_request():
    base = [x for x in D.scenario_ledger(_project()) if x["scenario"] == "S0_APPROVED_DESIGN"]
    with_req = [x for x in D.scenario_ledger(_project(CLIENT_REMOVAL)) if x["scenario"] == "S0_APPROVED_DESIGN"]
    assert base == with_req


def test_adverse_s1_line_can_never_be_released():
    ch = copy.deepcopy(CLIENT_REMOVAL)
    led = D.scenario_ledger(_project(ch))
    for x in led:
        if x["scenario"] != "S0_APPROVED_DESIGN":
            assert x["released"] is False


def test_s2_exists_only_for_a_consultant_issued_drawing_on_file():
    issued = dict(CLIENT_REMOVAL, requested_by="consultant", issued_drawing="REV-B sheet 7")
    led = D.scenario_ledger(_project(issued, revised=["REV-B sheet 7"]))
    s2 = [x for x in led if x["scenario"] == "S2_CONSULTANT_REVISED"][0]
    assert s2["status"] == D.HELD and "REV-B sheet 7" in s2["basis"]
    # adverse: the drawing is named but not on file -> UNKNOWN; a client cannot issue a revision
    led = D.scenario_ledger(_project(issued, revised=[]))
    assert [x for x in led if x["scenario"] == "S2_CONSULTANT_REVISED"][0]["status"] == D.UNKNOWN
    client_claim = dict(CLIENT_REMOVAL, issued_drawing="REV-B sheet 7")
    led = D.scenario_ledger(_project(client_claim, revised=["REV-B sheet 7"]))
    assert [x for x in led if x["scenario"] == "S2_CONSULTANT_REVISED"][0]["status"] == D.UNKNOWN

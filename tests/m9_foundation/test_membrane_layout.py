"""M9 S1 membrane roll plan (rectangle exact): the M9A fixture WP-1 (2.30 x 3.20 m, door 0.90 m in a 0.20 m wall), the
0.90 m effective width of each further 1.00 m strip, the doorway decisions of UP-WP-002 v2.0.0 / UP-WP-003 v1.1.0, the
full roll balance, no flat rate and no net / roll-area count, the stricter data-sheet lap, splicing, and the details
that are counted but never quantified by a guess."""

from __future__ import annotations

import itertools
import math

import pytest

from engine.source import material_spec as MS
from engine.source import membrane_layout as ML
from engine.source import rule_store as RS
from engine.source import material_result as WP

WP1 = {"room_id": "WP-1", "length_m": 2.30, "width_m": 3.20}
DOOR = [{"door_id": "D1", "width_m": 0.90, "depth_m": 0.20}]
H = RS.rule("UP-WP-002")["value"]


def plan(room=WP1, **kw):
    c = {"upturn_h_m": H, "doorways": DOOR, "direction": "ALONG_Y", "min_reusable_m": 0.30}
    c.update(kw)
    spec = c.pop("spec", None) or MS.membrane()
    return ML.plan(room, spec, constraints=c)


def test_wp1_net_surfaces_under_the_owner_rules():
    assert H == 0.2
    sf = ML.surfaces(WP1, upturn_h=H, doorways=DOOR)
    rows = {r["item_code"]: r["net_m2"] for r in sf["rows"]}
    assert rows == pytest.approx({"FIN.WP.FLOOR": 7.36, "FIN.WP.DOORWAY": 0.18, "FIN.WP.UPTURN": 2.2})
    assert sf["perimeter_lm"] == pytest.approx(11.0) and sf["doorway_segments_lm"] == pytest.approx(0.9)
    assert sum(rows.values()) == pytest.approx(9.74)
    assert {"DOORWAY_UPTURN_DETAIL_REQUIRED", "DOORWAY_DOUBLE_COVERAGE_REVIEW"} <= set(sf["flags"])


def test_the_doorway_is_billed_once_when_the_detail_puts_the_upturn_in_the_doorway_piece():
    sf = ML.surfaces(WP1, upturn_h=H, doorways=DOOR, doorway_detail="UPTURN_WITHIN_DOORWAY_PIECE")
    rows = {r["item_code"]: r["net_m2"] for r in sf["rows"]}
    assert rows["FIN.WP.UPTURN"] == pytest.approx((11.0 - 0.9) * 0.2) and rows["FIN.WP.DOORWAY"] == pytest.approx(0.18)
    assert not any(f.startswith("DOORWAY_DOUBLE") for f in sf["flags"])
    sr = ML.surfaces(WP1, upturn_h=H, doorways=DOOR, doorway_detail="SEPARATE_RETURN")
    assert {r["item_code"]: r["net_m2"] for r in sr["rows"]}["FIN.WP.UPTURN"] == pytest.approx(2.2) and not sr["flags"]


def test_the_doorway_piece_is_outside_the_floor_polygon():
    sf = ML.surfaces(WP1, upturn_h=H, doorways=DOOR)
    assert sf["rows"][0]["net_m2"] == pytest.approx(2.30 * 3.20)                 # never floor + doorway


def test_wp1_roll_plan_strips_and_effective_width():
    r = plan()
    L = r["layout"]
    assert L["floor_strips"] == 3 and L["last_strip_width_m"] == pytest.approx(0.5)
    assert 3 * 1.0 - 2 * 0.1 == pytest.approx(2.8)                                 # covering 2.80 m for 2.30 m
    floor_cut = sum(s["length_m"] for rl in L["rolls"] for s in rl["segments"] if s["for"].startswith("floor"))
    assert floor_cut * 1.0 == pytest.approx(9.6)                                   # 9.600 m2 of strips for 7.360 net
    comp = {c["component"]: c for c in r["components"]}
    assert comp["floor"]["overlap_m2"] == pytest.approx(2 * 0.1 * 3.2)
    assert L["seams"]["longitudinal"]["count"] == 2 and L["seams"]["longitudinal"]["running_lm"] == pytest.approx(6.4)
    assert r["net_installed_m2"] == pytest.approx(9.74)
    assert r["units"]["consumed_units"] == 2 and math.ceil(r["net_installed_m2"] / 10.0) == 1   # net/roll would say 1


@pytest.mark.parametrize("D,n", [(1.0, 1), (1.90, 2), (1.91, 3), (2.80, 3), (2.81, 4), (3.70, 4)])
def test_each_further_strip_adds_the_roll_width_less_the_lap(D, n):
    r = plan({"length_m": 3.0, "width_m": D}, direction="ALONG_X", doorways=[])
    assert r["layout"]["floor_strips"] == n


def test_a_stricter_data_sheet_lap_changes_the_plan_and_names_its_source():
    s = MS.apply_data_sheet(MS.membrane(), {"side_lap_m": 0.15, "source": "TDS test"})
    a = plan({"length_m": 3.0, "width_m": 1.90}, direction="ALONG_X", doorways=[])
    b = plan({"length_m": 3.0, "width_m": 1.90}, direction="ALONG_X", doorways=[], spec=s)
    assert (a["layout"]["floor_strips"], b["layout"]["floor_strips"]) == (2, 3)
    assert any("DATA_SHEET (TDS test)" in x for x in b["assumptions"])


def test_a_strip_longer_than_the_roll_is_spliced_with_end_laps():
    r = plan({"length_m": 7.5, "width_m": 12.4}, direction="ALONG_Y", doorways=[])
    L = r["layout"]
    assert L["pieces_per_strip"] == 2 and L["strip_piece_lengths_m"] == pytest.approx([10.0, 2.5])
    assert L["seams"]["transverse_floor"]["count"] == L["floor_strips"]


ROOMS = [WP1, {"length_m": 3.0, "width_m": 2.0}, {"length_m": 1.2, "width_m": 0.9}, {"length_m": 4.6, "width_m": 3.3},
         {"length_m": 7.5, "width_m": 12.4}, {"length_m": 11.0, "width_m": 0.95}]


@pytest.mark.parametrize("room", ROOMS)
def test_the_roll_balance_holds_for_every_plan(room):
    for det, d, mr in itertools.product(ML.DOORWAY_DETAILS, ("ALONG_X", "ALONG_Y", "MIN_MATERIAL"), (None, 0.3)):
        r = plan(room, doorway_detail=det, direction=d, min_reusable_m=mr)
        WP.check(r)
        p = r["packaging"]
        total = r["units"]["consumed_units"] * 10.0
        parts = r["net_installed_m2"] + r["overlap_m2"] + r["cutting_waste_m2"] + r["reusable_offcuts_m2"] + \
            p["packaging_surplus_m2"]
        assert parts == pytest.approx(total, abs=1e-5)
        assert r["units"]["consumed_units"] >= math.ceil((r["net_installed_m2"] + r["overlap_m2"]) / 10.0 - 1e-9)
        if mr is None:
            assert r["reusable_offcuts_m2"] == 0
        assert sum(c["net_m2"] for c in r["components"]) == pytest.approx(r["net_installed_m2"])


def test_min_material_picks_the_direction_with_fewer_rolls():
    r = plan({"length_m": 7.5, "width_m": 12.4}, direction="MIN_MATERIAL", doorways=[])
    alt = {a["direction"]: a["rolls"] for a in r["layout"]["alternatives"]}
    assert r["units"]["consumed_units"] == min(alt.values())


def test_details_are_counted_never_quantified_by_a_guess():
    r = plan(penetrations=2)
    d = r["layout"]["details"]
    assert d["corners"]["state"] == "NOT_QUANTIFIED" and d["corners"]["count"] == 6
    assert d["penetrations"] == {"count": 2, "state": "NOT_QUANTIFIED", "detail": None}
    assert any(c.startswith("CORNER_TREATMENT_NOT_SPECIFIED") for c in r["concerns"])
    assert any(c.startswith("PENETRATION_DETAIL_NOT_SPECIFIED") for c in r["concerns"])


def test_no_flat_rate_no_old_upturn_and_missing_data_refused():
    r = plan()
    assert r["spare_allowance"]["state"] == "NOT_SET" and r["packaging"]["spare_units"] == 0
    assert all(c["item_code"] != "FIN.WP.UPTURN" or c["net_m2"] == pytest.approx(11.0 * 0.2) for c in r["components"])
    with pytest.raises(ML.MembraneError):
        plan(doorways=[{"width_m": 0.9}])
    with pytest.raises(ML.MembraneError):
        ML.plan(WP1, MS.membrane(), constraints={"doorways": DOOR})                     # no upturn height
    b = ML.plan({"polygon": [[0, 0], [3, 0], [3, 1], [1, 1], [1, 2], [0, 2]]}, MS.membrane(),
                constraints={"upturn_h_m": H})
    assert b["state"] == "BLOCKED" and b["blocked_by"].startswith("POLYGON_OPTIMIZER_NOT_IMPLEMENTED")
    src = (ML.__file__ and open(ML.__file__, encoding="utf-8").read())
    assert "1.1 *" not in src and "* 1.1" not in src and "* 1.10" not in src


def test_doorway_positions_split_the_band_into_open_runs():
    two = [{"door_id": "A", "width_m": 0.9, "depth_m": 0.2, "position_lm": 0.5},
           {"door_id": "B", "width_m": 0.8, "depth_m": 0.2, "position_lm": 5.0}]
    r = plan(doorways=two, doorway_detail="UPTURN_WITHIN_DOORWAY_PIECE")
    runs = r["layout"]["band_runs"]
    assert len(runs) == 2 and not any(x["closed"] for x in runs)
    assert sum(x["length_m"] for x in runs) == pytest.approx(11.0 - 1.7)
    nopos = plan(doorways=[{k: v for k, v in d.items() if k != "position_lm"} for d in two],
                 doorway_detail="UPTURN_WITHIN_DOORWAY_PIECE")
    assert any(c.startswith("BAND_RUNS_APPROXIMATED") for c in nopos["concerns"])

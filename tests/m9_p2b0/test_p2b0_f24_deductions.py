"""Phase 2B-0 P0, finding F-24: a wall-finish deduction takes only the length of an opening that lies on the room's own
boundary (ARCH_TAKEOFF_V2.2); V2.1 keeps its frozen behaviour (the characterization tests below prove the defect is
still there, unchanged). Synthetic plans only (tests/m9_p2b0/p2b0_fixtures.py, truth by hand)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("ezdxf")
sys.path.insert(0, str(Path(__file__).resolve().parent))

import p2b0_fixtures as FX                                    # noqa: E402
from engine.source import boq_line as BL                      # noqa: E402
from engine.source import release_safety as RSF               # noqa: E402
from tools import urban_boq_m9 as M9                          # noqa: E402

LR = {"A-WALL": "WALL", "A-GLAZ": "WINDOW", "A-DOOR": "DOOR", "A-THIN": "OTHER"}
WALL_FINISH = ("FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE")
TOL = 1e-6


def _run(path, method, facts=FX.HEIGHT_FACTS):
    try:
        room, arch, _E = M9.arch_compute(str(path), method=method, layer_roles=LR, facts=facts)
    except M9.CompletenessFailed as ex:
        room, arch = ex.room_boq, ex.arch
    return room, arch


def _finish(room, code):
    """the wall-finish line of each room (its element is the trade: plaster / paint / wall_tile; a wet room's
    'finish above wall tile' paint RFI is another line)."""
    el = {"FIN.PLASTER": "plaster", "FIN.PAINT": "paint", "FIN.WALL.TILE": "wall_tile"}[code]
    return {ln["location"]["room_name_en"].split(" / ")[0].split(" ")[0]: ln for ln in room["lines"]
            if ln["item_code"] == code and ln["physical_element"] == el}


@pytest.fixture(scope="module")
def plans(tmp_path_factory):
    d = tmp_path_factory.mktemp("f24")
    return {"wide": FX.open_plan(d / "wide.dxf", zone_x=6000), "narrow": FX.open_plan(d / "narrow.dxf", zone_x=11000),
            "corner": FX.corner_openings(d / "corner.dxf")}


def test_v2_1_keeps_the_frozen_defect(plans):
    """characterization (V2.1 is frozen): the full passage width is deducted in every face that touches it, and a
    face shorter than the passage stops the whole run."""
    room, _arch = _run(plans["wide"], "ARCH_TAKEOFF_V2.1")
    pl = _finish(room, "FIN.PLASTER")
    assert pl["Bathroom"]["measured_net"] == pytest.approx((17.2 - 10.4) * 3.0)     # 20.4: deducted 10.4 m, not 5.4 m
    with pytest.raises(BL.LineError):
        _run(plans["narrow"], "ARCH_TAKEOFF_V2.1")


@pytest.mark.parametrize("zone_x", [6000, 11000])
def test_v2_2_deducts_each_opening_by_its_own_length_on_the_boundary(plans, zone_x):
    room, _arch = _run(plans["wide" if zone_x == 6000 else "narrow"], "ARCH_TAKEOFF_V2.2")
    truth = FX.open_plan_truth(zone_x)
    want = {"Living": "LIVING", "Dining": "DINING", "Bathroom": "W.C."}
    for code, H in (("FIN.PLASTER", 3.0), ("FIN.PAINT", 3.0), ("FIN.WALL.TILE", 2.4)):
        for name, ln in _finish(room, code).items():
            t = truth[want[name]]
            assert ln["evidence_state"] == "SOURCE_DERIVED", (code, name, ln["evidence_state"])
            assert ln["measured_net"] == pytest.approx((t["run"] - t["passage_own"]) * H, abs=TOL), (code, name)
            ded = ln["deductions"]
            assert len(ded) == 1 and ded[0]["lm_on_this_boundary"] == pytest.approx(t["passage_own"], abs=TOL)


def test_v2_2_never_stops_and_never_releases_a_negative_quantity(plans):
    for key in ("wide", "narrow", "corner"):
        room, _arch = _run(plans[key], "ARCH_TAKEOFF_V2.2")
        for ln in room["lines"]:
            if ln["evidence_state"] in BL.QUANTITY_STATES:
                assert ln["measured_net"] >= 0, (key, ln["item_code"], ln["measured_net"])


def test_openings_meeting_at_a_corner_are_each_deducted_once(plans):
    """a 3.0 m passage that ends at the room's corner and a 2.0 m window that starts at the same corner: no edge is
    shared, each is deducted by exactly its width (the passage at the full 3.0 m, the window at its 1.5 m height), the
    boundary decomposes exactly."""
    room, _arch = _run(plans["corner"], "ARCH_TAKEOFF_V2.2")
    ln = _finish(room, "FIN.PLASTER")["Bedroom"]
    assert ln["evidence_state"] == "SOURCE_DERIVED"
    assert sorted(d["lm_on_this_boundary"] for d in ln["deductions"]) == pytest.approx([2.0, 3.0])
    assert ln["measured_net"] == pytest.approx(22.0 * 3.0 - 3.0 * 3.0 - 2.0 * 1.5)
    dec = ln["calculation"]["inputs"]["decomposition"]
    assert dec["band_opening_lm"] == pytest.approx(5.0) and dec["undeducted_opening_lm"] == 0.0


def _detail(**kw):
    d = {"outer_sets_lm": {"WALL": 8.0, "PASSAGE_THRESHOLD": 2.0}, "hole_sets_lm": {}, "opening_lm": {"OP-1": 2.0},
         "closure_lm": {}, "shared_opening_lm": 0.0, "shared_openings": []}
    d.update(kw)
    return d


OP = [{"opening_id": "OP-1", "kind": "PASSAGE", "width_m": 2.0}]


def test_an_inconsistent_boundary_is_blocked_never_clamped():
    ok = RSF.wall_finish(run_lm=10.0, height_m=3.0, openings=OP, opening_heights={}, detail=_detail())
    assert ok["state"] == "MEASURED" and ok["net"] == pytest.approx(24.0)
    too_long = RSF.wall_finish(run_lm=10.0, height_m=3.0, openings=[dict(OP[0], width_m=1.5)], opening_heights={},
                               detail=_detail())
    shared = RSF.wall_finish(run_lm=10.0, height_m=3.0, openings=OP, opening_heights={},
                             detail=_detail(shared_opening_lm=0.5, shared_openings=[("OP-1", "OP-2")]))
    short = RSF.wall_finish(run_lm=11.0, height_m=3.0, openings=OP, opening_heights={}, detail=_detail())
    for r in (too_long, shared, short):
        assert r["state"] == RSF.GEOMETRY_INCONSISTENT and r["net"] is None and r["low"] is None and r["checks"]


def test_openings_with_an_unknown_deduction_make_a_range_not_a_release():
    """a door closed only by its leaf, a glazed screen on the face, or a window without a height."""
    clo = RSF.wall_finish(run_lm=10.0, height_m=3.0, openings=[], opening_heights={},
                          detail=_detail(outer_sets_lm={"WALL": 9.2, "DOOR_CLOSURE": 0.8}, opening_lm={}))
    assert clo["state"] == "RANGE" and clo["high"] == pytest.approx(30.0) and clo["low"] == pytest.approx(27.6)
    win = RSF.wall_finish(run_lm=10.0, height_m=3.0, openings=[{"opening_id": "OP-1", "kind": "WINDOW",
                                                                "width_m": 2.0}],
                          opening_heights={}, detail=_detail(outer_sets_lm={"WALL": 8.0, "WINDOW_THRESHOLD": 2.0}))
    assert win["state"] == "RANGE" and win["high"] == pytest.approx(30.0) and win["low"] == pytest.approx(24.0)


def _key(room, skip):
    return sorted((ln["item_code"], ln["location"].get("room_id"), ln["location"].get("element_id"),
                   ln["evidence_state"], repr(ln.get("measured_net"))) for ln in room["lines"]
                  if ln["item_code"] not in skip)


@pytest.mark.parametrize("facts", [None, FX.HEIGHT_FACTS])
def test_every_other_quantity_is_unchanged(plans, facts):
    """V2.2 against V2.1 on the same plan: only the wall-finish lines (and the skirting, F-17) may differ."""
    a, _ = _run(plans["wide"], "ARCH_TAKEOFF_V2.1", facts=facts)
    b, _ = _run(plans["wide"], "ARCH_TAKEOFF_V2.2", facts=facts)
    assert _key(a, WALL_FINISH + ("FIN.SKIRTING",)) == _key(b, WALL_FINISH + ("FIN.SKIRTING",))
    if facts is None:                                       # without heights the wall finishes are the same RFIs
        assert _key(a, ()) == _key(b, ())


REAL = os.environ.get("URBAN_REAL_PLAN_DXF")


@pytest.mark.skipif(not (REAL and Path(REAL).exists()), reason="the reference plan is private (URBAN_REAL_PLAN_DXF)")
def test_the_reference_plan_with_heights_no_longer_stops():
    with pytest.raises(BL.LineError):                       # V2.1, frozen
        _run(REAL, "ARCH_TAKEOFF_V2.1")
    room, _arch = _run(REAL, "ARCH_TAKEOFF_V2.2")
    for ln in room["lines"]:
        if ln["evidence_state"] in BL.QUANTITY_STATES:
            assert ln["measured_net"] >= 0
    assert any(ln["item_code"] == "FIN.PLASTER" and ln["evidence_state"] == "SOURCE_DERIVED" for ln in room["lines"])

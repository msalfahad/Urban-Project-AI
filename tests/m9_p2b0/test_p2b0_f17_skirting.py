"""Phase 2B-0 P0, finding F-17: a boundary edge that is skirted under one reading and not under the other is no longer
split 50 / 50 (ARCH_TAKEOFF_V2.2). The skirting that holds under both readings is released; the unresolved length is
a separate range [0, length] that is never released. V2.1 keeps its frozen split (characterization)."""

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


def _skirting(path, method):
    try:
        room, _arch, _E = M9.arch_compute(str(path), method=method, layer_roles=LR)
    except M9.CompletenessFailed as ex:
        room = ex.room_boq
    return [ln for ln in room["lines"] if ln["item_code"] == "FIN.SKIRTING"]


@pytest.fixture(scope="module")
def plans(tmp_path_factory):
    d = tmp_path_factory.mktemp("f17")
    return {f: FX.windows(d / f"{f}.dxf", f) for f in ("RECESSED", "ON_FACE", "CURTAIN")}


def test_v2_1_keeps_the_frozen_half_split(plans):
    """characterization: the frame on the room face is credited half (0.75 of 1.5 m)."""
    (ln,) = _skirting(plans["ON_FACE"], "ARCH_TAKEOFF_V2.1")
    assert ln["measured_net"] == pytest.approx(14.0 - 0.75)


def test_sill_window_with_a_recessed_frame_is_skirted_as_before(plans):
    """the documented V1 convention (a window threshold on the room face is a sill window) is kept: no range."""
    a = _skirting(plans["RECESSED"], "ARCH_TAKEOFF_V2.1")
    b = _skirting(plans["RECESSED"], "ARCH_TAKEOFF_V2.2")
    assert [x["measured_net"] for x in a] == [x["measured_net"] for x in b] == [pytest.approx(14.0)]


def test_floor_level_glazing_is_not_skirted_as_before(plans):
    """a curtain wall (the glazing is the room boundary, no wall band): the glazing edge is not skirted, no range."""
    b = _skirting(plans["CURTAIN"], "ARCH_TAKEOFF_V2.2")
    assert [(x["evidence_state"], x["measured_net"]) for x in b] == [("SOURCE_DERIVED", pytest.approx(10.0))]


def test_a_frame_on_the_room_face_releases_only_what_both_readings_agree_on(plans):
    lines = _skirting(plans["ON_FACE"], "ARCH_TAKEOFF_V2.2")
    released = [x for x in lines if x["evidence_state"] in BL.QUANTITY_STATES]
    ranged = [x for x in lines if x["evidence_state"] == "BOUNDED_EXPOSURE"]
    assert len(released) == 1 and released[0]["measured_net"] == pytest.approx(14.0 - 1.5)      # floor-level reading
    assert len(ranged) == 1 and ranged[0]["bounded_range"]["low"] == 0.0
    assert ranged[0]["bounded_range"]["high"] == pytest.approx(1.5)                              # + sill reading
    assert ranged[0]["rfi"]["question"]
    # the two outcomes are 12.5 m and 14.0 m; the released figure is never the 13.25 m midpoint
    assert all(abs(x["measured_net"] - 13.25) > 1e-6 for x in released)


def test_the_split_rule_is_exact_when_no_edge_is_unresolved():
    d = {"outer_sets_lm": {"WALL": 10.0, "WINDOW_THRESHOLD": 1.5, "DOOR_THRESHOLD": 0.9}, "hole_sets_lm": {"COLUMN": 1.6}}
    r = RSF.skirting(13.1, d)
    assert r["certain_lm"] == 13.1 and r["unresolved_lm"] == 0.0
    d["outer_sets_lm"]["WINDOW+WINDOW_THRESHOLD"] = 1.0
    d["hole_sets_lm"]["COLUMN+WINDOW"] = 0.2
    r = RSF.skirting(13.6, d)
    assert r["certain_lm"] == pytest.approx(13.6 - 0.5 - 0.1) and r["unresolved_lm"] == pytest.approx(1.2)
    assert r["unresolved_by_roles"] == {"COLUMN+WINDOW": 0.2, "WINDOW+WINDOW_THRESHOLD": 1.0}


def test_every_other_quantity_is_unchanged(plans):
    def key(path, method):
        try:
            room, _a, _E = M9.arch_compute(str(path), method=method, layer_roles=LR)
        except M9.CompletenessFailed as ex:
            room = ex.room_boq
        return sorted((ln["item_code"], ln["location"].get("element_id"), ln["evidence_state"],
                       repr(ln.get("measured_net"))) for ln in room["lines"] if ln["item_code"] != "FIN.SKIRTING")
    for f in plans:
        assert key(plans[f], "ARCH_TAKEOFF_V2.1") == key(plans[f], "ARCH_TAKEOFF_V2.2"), f


REAL = os.environ.get("URBAN_REAL_PLAN_DXF")


@pytest.mark.skipif(not (REAL and Path(REAL).exists()), reason="the reference plan is private (URBAN_REAL_PLAN_DXF)")
def test_the_reference_plan_has_no_released_midpoint():
    """the acceptance-review case (BA-12): 1.90 m released + a [0, 1.00] m range, never 2.40 m."""
    lines = _skirting(REAL, "ARCH_TAKEOFF_V2.2")
    released = [x["measured_net"] for x in lines if x["evidence_state"] in BL.QUANTITY_STATES]
    assert not any(abs(v - 2.4) < 1e-6 for v in released)
    assert any(x["evidence_state"] == "BOUNDED_EXPOSURE" and x["bounded_range"]["low"] == 0.0 for x in lines)

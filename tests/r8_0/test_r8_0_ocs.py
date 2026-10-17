"""R8.0 F03 / F34 — OCS fail-closed.

SOURCE UNCERTAINTY -> VISIBLE FINDING / BLOCKER, never -> IDENTITY TRANSFORM.

A tilted frame (normal not +/-Z) cannot be realised in plan from (x, y) and
must raise UNSUPPORTED_FRAME. An unreadable extrusion (null, zero vector,
wrong length, non-numeric) must raise FRAME_UNREADABLE. Either way the
entity supports no FINAL quantity. (U-C4N's ocs.py returns identity in both
situations; that fail-open behaviour is exactly what these tests forbid.)
The +/-Z cases themselves are in test_r8_0_curves.py (F03_*).
"""

from __future__ import annotations

import pytest

from . import libredwg_builder as B, scenes as S, targets
from .geometry import current_realised

FRAME = {c[1]: c for c in S.FRAME_CASES}


@pytest.mark.parametrize("sid", list(FRAME))
def test_frame_problem_is_a_visible_finding_current_engine(sid):
    """Current engine: the frame problem must appear somewhere in its output
    (notes / unhandled) and the arc must not be silently realised in plan."""
    code = FRAME[sid][4]
    nd = current_realised(B.build(S.frame_scene(FRAME[sid][3])))["normalized"]
    visible = code in repr(nd.notes) or code in repr(nd.unhandled)
    silently_realised = any(p.kind == "ARC" for p in nd.primitives)
    assert visible and not silently_realised, (
        f"{sid}: extrusion {FRAME[sid][3]!r} silently treated as WCS (visible={visible})")


@pytest.mark.parametrize("sid", list(FRAME))
def test_frame_problem_k1_acceptance(sid):
    got = targets.call("K1_REALISE", B.build(S.frame_scene(FRAME[sid][3])))
    assert not got["arcs"], "no plan geometry may be claimed for this frame"
    f = [x for x in got["findings"] if x["code"] == FRAME[sid][4]]
    assert f and f[0].get("blocks_final") is True


@pytest.mark.parametrize("sid", list(FRAME))
def test_ocs_plan_frame_contract(sid):
    """kernel_ocs (COPY_ADAPT of U-C4N backends/ocs.py) must RAISE, not return identity."""
    plan_frame = targets.resolve("OCS_PLAN_FRAME")
    with pytest.raises(Exception) as err:
        plan_frame(FRAME[sid][3])
    assert FRAME[sid][4] in str(err.value)


def test_line_is_wcs_native_whatever_its_extrusion_current_engine():
    """ezdxf/DXF: LINE end points are WCS. Applying OCS to a LINE (keying a
    fix off 'has an extrusion field') moves it wrongly. Current engine passes."""
    scene = {"entities": [{"kind": "LINE", "a": (0.0, 0.0), "b": (2000.0, 0.0), "extrusion": (0.0, 0.0, -1.0)}]}
    segs = current_realised(B.build(scene))["segments"]
    assert segs == [((0.0, 0.0), (2000.0, 0.0))]


def test_line_is_wcs_native_k1_acceptance():
    scene = {"entities": [{"kind": "LINE", "a": (0.0, 0.0), "b": (2000.0, 0.0), "extrusion": (0.0, 0.0, -1.0)}]}
    got = targets.call("K1_REALISE", B.build(scene))
    assert got["segments"] == [((0.0, 0.0), (2000.0, 0.0))]

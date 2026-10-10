"""Synthetic normalized drawing for the CAD curve register. No P7757 value."""

from __future__ import annotations

import math
from types import SimpleNamespace as NS

from engine import cad_curve_register as CR


def _arc(oid, layer, cx, cy, r, a0, a1):
    return NS(kind="ARC", object_id=oid, cx=cx, cy=cy, radius=r, start_angle=a0,
              end_angle=a1, provenance=NS(layer=layer, handle=1, instance_path=()))


def _seg(handle, x1, y1, x2, y2, layer="1"):
    return NS(kind="SEGMENT", object_id=f"CAD-{handle}", x1=x1, y1=y1, x2=x2, y2=y2,
              provenance=NS(layer=layer, handle=handle, instance_path=()))


def _drawing():
    frame = [_seg(9, 0, 0, 40000, 0), _seg(9, 40000, 0, 40000, 30000),
             _seg(9, 40000, 30000, 0, 30000), _seg(9, 0, 30000, 0, 0)]
    arcs = [_arc("A1", "5", 10000, 10000, 1500, 0, math.pi),
            _arc("A2", "5", 10000, 10000, 1700, 0, math.pi),
            _arc("A3", "D", 30000, 5000, 900, 0, math.pi / 2)]
    texts = [NS(value="POOL", x=10500, y=10300, provenance=NS(layer="5", instance_path=(1,)))]
    return NS(primitives=frame + arcs, texts=texts, source_file="synthetic.dwg",
              drawing_unit="millimetre", insunits_code=4)


def test_arc_lengths_are_exact_and_correspondence_is_only_proposed():
    reg = CR.curve_register(_drawing(), anchors={
        "POOL": {"LABEL": "pool", "PROPOSED_A21": ["X/GLZ-9"], "LAYERS": ("5",)}})
    assert len(reg["CURVE_SETS"]) == 1
    s = reg["CURVE_SETS"][0]
    assert s["FRAME_ID"] == "FRAME_1"
    assert s["LENGTH_BY_RADIUS_M"]["1500.0"] == round(math.pi * 1.5, 4)
    assert s["LENGTH_BY_RADIUS_M"]["1700.0"] == round(math.pi * 1.7, 4)
    assert s["CAD_GEOMETRY_STATUS"] == "ESTABLISHED_FROM_DWG"
    assert s["CORRESPONDENCE"]["SEMANTIC_LINK_STATUS"] == "NOT_ESTABLISHED"
    assert s["CORRESPONDENCE"]["PROPOSED_A21_TRACES"] == ["X/GLZ-9"]
    assert reg["EVIDENCE_INDEPENDENCE"] == "SHARED_SOURCE_FAMILY"
    assert reg["FRAMES"][0]["FLOOR_IDENTITY"] == "NOT_ESTABLISHED_FROM_CAD"


def test_missing_anchor_is_reported_not_guessed():
    reg = CR.curve_register(_drawing(), anchors={"X": {"LABEL": "nowhere"}})
    assert reg["CURVE_SETS"] == []
    assert reg["ANCHORS_NOT_LOCATED"][0]["STATUS"] == "ANCHOR_LABEL_NOT_FOUND_IN_MODEL"

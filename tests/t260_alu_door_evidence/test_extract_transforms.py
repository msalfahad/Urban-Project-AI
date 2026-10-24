"""T-260 extractor on synthetic drawings (not Alsenan): the face gaps are read in the door block's own frame, so a
rotated, mirrored or metre-unit drawing gives the same opening. Hand: wall 0.20 thick, opening 0.90 between the face
line ends on both faces, D120-like block 1.00 x 0.20 overlapping the masonry by 0.05 each side (a symbol)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ezdxf = pytest.importorskip("ezdxf")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t260"))
import t260_extract as X  # noqa: E402


def build(rot_deg, mirror, unit_m, gap_a=0.90, gap_b=0.90):
    s = 0.001 / unit_m                                          # drawing units per mm
    doc = ezdxf.new()
    blk = doc.blocks.new("D120")
    for a, b in [((0, 0), (1000, 0)), ((0, 200), (1000, 200)), ((0, 0), (0, 200)), ((1000, 0), (1000, 200))]:
        blk.add_line((a[0] * s, a[1] * s), (b[0] * s, b[1] * s), dxfattribs={"layer": "D"})
    msp = doc.modelspace()
    r = math.radians(rot_deg)
    sx = -1.0 if mirror else 1.0
    ox, oy = 12345.0 * s, -6789.0 * s

    def w(u, v):                                                # block-local mm -> world units
        u, v = u * s * sx, v * s
        return ox + u * math.cos(r) - v * math.sin(r), oy + u * math.sin(r) + v * math.cos(r)
    ca, cb = (1000 - 1000 * gap_a) / 2, (1000 - 1000 * gap_b) / 2
    for v, c in ((0, ca), (200, cb)):
        msp.add_line(w(-2000, v), w(c, v), dxfattribs={"layer": "1"})
        msp.add_line(w(1000 - c, v), w(3000, v), dxfattribs={"layer": "1"})
    ins = msp.add_blockref("D120", (ox, oy), dxfattribs={"rotation": rot_deg, "xscale": sx, "layer": "4"})
    return doc, ins.dxf.handle


@pytest.mark.parametrize("rot,mirror,unit", [(0, False, 0.001), (37, False, 0.001), (180, True, 0.001),
                                             (270, True, 1.0), (90, False, 1.0)])
def test_gap_is_frame_invariant(rot, mirror, unit):
    doc, h = build(rot, mirror, unit)
    out = X.door_faces(doc, h, unit_m=unit)
    assert [f["gap_m"] for f in out["faces"]] == [0.9, 0.9]


def test_two_faces_that_differ_are_both_reported():
    doc, h = build(30, False, 0.001, gap_a=0.90, gap_b=0.95)
    assert [f["gap_m"] for f in X.door_faces(doc, h)["faces"]] == [0.9, 0.95]


def test_a_missing_face_line_gives_no_gap_never_0():
    doc, h = build(0, False, 0.001)
    for e in list(doc.modelspace().query("LINE")):
        if abs(e.dxf.start.y - e.dxf.end.y) < 1e-6 and abs(e.dxf.start.y - (-6789.0 + 200)) < 1e-6:
            doc.modelspace().delete_entity(e)
    gaps = [f["gap_m"] for f in X.door_faces(doc, h)["faces"]]
    assert gaps[0] == 0.9 and gaps[1] is None

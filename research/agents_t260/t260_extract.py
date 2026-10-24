"""T-260 extractor (Checker re-measure aid): reads the private architectural DXF given on the command line (Drive
"Alsenan chalet project" / P7757_DXF_COMPRESSED.zip -> P7757.dxf, sha256 ab54dd55...) and prints, values only, for each
door insert named below: the wall-face line pieces on both wall faces in the door block's own frame (u along the wall,
v across it; the block is 1000 x 200 units, 1 unit = 1 mm), the gap between the collinear face-line ends on each face,
and the block frame extent. It also lists every entity drawn inside the side-passage mouth band and inside the passage.
No coordinate, drawing content or client data is written anywhere; output goes to stdout only.

    python3 -I research/agents_t260/t260_extract.py <path to P7757.dxf>
"""
from __future__ import annotations

import hashlib
import json
import math
import sys

DOORS = {  # census id -> door block INSERT handle on P7757.dxf (GF / 2F plan frames)
    "D-GF-01": "15E", "D-GF-05": "192", "D-GF-06": "33E", "D-GF-09": "3FF",   # the four held doors
    "D-GF-03": "1B5",                                                         # control (released, Checker 02:44)
}
FACE_LAYERS = {"1"}          # wall face lines (layer role 1, T-109 / T-198 Mode A); layer 5 / 2 inside the frame = sill
TOL = 1.0                    # units (mm): parallel / collinear tolerance


def _segments(msp):
    for e in msp:
        t = e.dxftype()
        if t == "LINE":
            yield e.dxf.handle, e.dxf.layer, (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)
        elif t == "LWPOLYLINE":
            pts = list(e.get_points("xy"))
            if e.closed:
                pts.append(pts[0])
            for a, b in zip(pts, pts[1:]):
                yield e.dxf.handle, e.dxf.layer, a, b


def door_faces(doc, handle, depth_mm=200.0, unit_m=0.001, frame_mm=1000.0):
    """Face gaps of the door block INSERT `handle` in its own frame (rotation and mirror removed); drawing units
    unit_m metres per unit; the block is frame_mm x depth_mm."""
    k = 0.001 / unit_m                       # drawing units per mm
    depth, tol, mid = depth_mm * k, TOL * k, frame_mm * k / 2.0
    ins = doc.entitydb[handle]
    p = ins.dxf.insert
    r = math.radians(ins.dxf.rotation)
    sx, sy = ins.dxf.xscale, ins.dxf.yscale
    ux, uy = math.cos(r) * sx, math.sin(r) * sx
    vx, vy = -math.sin(r) * sy, math.cos(r) * sy
    det = ux * vy - vx * uy

    def loc(x, y):
        dx, dy = x - p.x, y - p.y
        return (dx * vy - vx * dy) / det, (ux * dy - uy * dx) / det

    faces = {0.0: [], depth: []}
    for h, lay, a, b in _segments(doc.modelspace()):
        if lay not in FACE_LAYERS:
            continue
        (ua, va), (ub, vb) = loc(*a), loc(*b)
        if abs(va - vb) > tol:
            continue
        for v in faces:
            if abs(va - v) <= tol and max(ua, ub) > -3000 * k and min(ua, ub) < 4000 * k:
                faces[v].append((round(min(ua, ub) / k, 1), round(max(ua, ub) / k, 1), h))
    out = {"insert": handle, "block": ins.dxf.name, "insert_layer": ins.dxf.layer, "block_frame_m": 1.000
           if ins.dxf.name.upper() == "D120" else None, "faces": []}
    mid_mm = mid / k
    for v, pieces in faces.items():
        left = max((q for q in pieces if q[1] <= mid_mm), key=lambda q: q[1], default=None)
        right = min((q for q in pieces if q[0] >= mid_mm), key=lambda q: q[0], default=None)
        gap = round((right[0] - left[1]) / 1000.0, 3) if left and right else None
        out["faces"].append({"v_mm": round(v / k, 1), "left_end_handle": left[2] if left else None,
                             "right_end_handle": right[2] if right else None,
                             "left_end_u_mm": left[1] if left else None, "right_end_u_mm": right[0] if right else None,
                             "gap_m": gap})
    return out


def entities_in(doc, x0, y0, x1, y1):
    from shapely.geometry import LineString, box   # noqa: PLC0415
    B = box(x0, y0, x1, y1)
    hits = []
    for h, lay, a, b in _segments(doc.modelspace()):
        g = LineString([a, b])
        if g.intersects(B) and not g.touches(B):
            hits.append((h, lay))
    return sorted(set(hits))


def main(path):
    import ezdxf   # noqa: PLC0415
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    doc = ezdxf.readfile(path)
    res = {"source_sha256": sha, "doors": {k: door_faces(doc, h) for k, h in DOORS.items()}}
    # side passage (D-GF-05 side B): mouth band on the court line between the annex end-wall face and the house wall
    # face, and the passage interior, in the GF plan frame (window given in drawing units relative to the D-GF-05
    # door insert so no absolute coordinate is written here)
    ins = doc.entitydb["192"].dxf.insert
    mx0, mx1 = ins.x + 10, ins.x + 1190                    # between the two passage face lines (1.200 apart)
    res["passage_mouth_band"] = entities_in(doc, mx0, ins.y + 4294, mx1, ins.y + 4894)
    res["passage_interior"] = entities_in(doc, mx0, ins.y + 100, mx1, ins.y + 4294)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])

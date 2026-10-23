"""T-223 extractor: reads the development villa's architectural DXF by ENTITY HANDLE (hex) and writes
ALSENAN_T223_INPUT.json: per element the handles, layers, lengths and the face geometry in a LOCAL frame (metres from
the element's own corner, rounded to the millimetre); no drawing coordinates, no client data.

Usage (Python 3.11, drawing outside the repository):
    python3 -I research/agents_t223/extract_t223.py <P7757.dxf> --out research/agents_t223/ALSENAN_T223_INPUT.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

# --- the elements, by handle (located on the plan by the Checker's 22:05 floor batch and own reading; see report) ---
CURVED_ROOM = {                     # 1F-R3CFCFD, the curved east room + its open passage OP-009 + lobby
    "west": "B0D", "north": "ACE", "east_line_upper": "B6B", "east_line_upper_twin": "AC8",
    "jamb_arc_upper": "BD1", "glazing_arcs": ["BD2", "BD3", "BD4", "BD5"], "jamb_arc_lower": "BD6",
    "outer_arcs": ["BCD", "BD0"], "south_west": "C09", "south_east": "C0A",
    "strip_south_west": "C0B", "lobby_north_east": "C0C", "lobby_west": "B0B", "lobby_east_upper": "C10",
    "lobby_east_lower": "C0F", "lobby_south_west": "B1D", "lobby_south_east": "B1C",
    "columns": ["2FEA", "300B", "2FDB", "2FD8"], "joinery_box": [],
    "dims": ["F4C", "EAD", "E6F", "E7B", "F88", "FAA", "F9F"],
}
DRESSING = {"faces": ["B03", "B04", "B00", "B20", "AD4", "AD5"], "box": ["B0A", "BE3"], "dims": ["EE9"]}
PASSAGE = {"west_faces": ["A2", "A3"], "east_faces": ["9F", "A0", "A1"], "east_windows": ["3BE", "3CB"],
           "west_door": ["19C"], "boundary_wall": ["105", "106", "86"], "mouth_ends": ["120", "15A"],
           "columns": ["2FAB", "2FAE", "2FB1", "2FB7"]}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(argv=None):
    import ezdxf
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = ezdxf.readfile(a.dxf)
    db = doc.entitydb
    unit = 0.001                    # the plan is drawn in millimetres ($INSUNITS 4; dims print mm)

    def ent(h):
        e = db.get(h)
        if e is None:
            raise SystemExit(f"handle {h} not in the drawing")
        return e

    def rec(h, o):
        e = ent(h)
        t = e.dxftype()
        r = {"handle": h, "type": t, "layer": e.dxf.layer}
        if t == "LINE":
            s, n = e.dxf.start, e.dxf.end
            r["a"] = [round((s.x - o[0]) * unit, 3), round((s.y - o[1]) * unit, 3)]
            r["b"] = [round((n.x - o[0]) * unit, 3), round((n.y - o[1]) * unit, 3)]
            r["length_m"] = round(math.dist((s.x, s.y), (n.x, n.y)) * unit, 3)
        elif t == "ARC":
            c = e.dxf.center
            r["centre"] = [round((c.x - o[0]) * unit, 4), round((c.y - o[1]) * unit, 4)]
            r["radius_m"] = round(e.dxf.radius * unit, 4)
            r["start_deg"], r["end_deg"] = round(e.dxf.start_angle, 3), round(e.dxf.end_angle, 3)
        elif t == "LWPOLYLINE":
            r["points"] = [[round((p[0] - o[0]) * unit, 3), round((p[1] - o[1]) * unit, 3)] for p in e.get_points("xy")]
            r["closed"] = bool(e.closed)
        elif t == "DIMENSION":
            r["measurement_mm"] = round(e.get_measurement(), 1)
            p2, p3 = e.dxf.defpoint2, e.dxf.defpoint3
            r["p2"] = [round((p2.x - o[0]) * unit, 3), round((p2.y - o[1]) * unit, 3)]
            r["p3"] = [round((p3.x - o[0]) * unit, 3), round((p3.y - o[1]) * unit, 3)]
        return r

    # local frame 1: the curved room's south-west inner corner (west face B0D meets south face C09)
    w = ent("B0D")
    o1 = (w.dxf.start.x, min(w.dxf.start.y, w.dxf.end.y))
    room = {k: ([rec(h, o1) for h in v] if isinstance(v, list) else rec(v, o1)) for k, v in CURVED_ROOM.items()}
    dress = {k: [rec(h, o1) for h in v] for k, v in DRESSING.items()}
    # local frame 2: the side passage's inner corner at the boundary wall (west face A2 x, boundary inner face 106 y)
    a2, b106 = ent("A2"), ent("106")
    o2 = (a2.dxf.start.x, b106.dxf.start.y)
    pas = {k: [rec(h, o2) for h in v] for k, v in PASSAGE.items()}
    # the passage mouth: entities on any layer (dimensions aside) crossing the mouth segment between the face ends
    m0, m1 = ent("120"), ent("15A")
    y_m = m0.dxf.start.y
    xs = sorted([m0.dxf.start.x, m1.dxf.start.x])
    cross = []
    for e in doc.modelspace():
        if e.dxftype() != "LINE":
            continue
        s, n = e.dxf.start, e.dxf.end
        if min(s.y, n.y) < y_m - 1 and max(s.y, n.y) > y_m + 1 and xs[0] + 1 < (s.x + n.x) / 2 < xs[1] - 1:
            cross.append(e.dxf.handle)
        elif abs(s.y - y_m) < 1 and abs(n.y - y_m) < 1 and min(s.x, n.x) < xs[1] - 1 and max(s.x, n.x) > xs[0] + 1:
            cross.append(e.dxf.handle)
    # every entity inside the lobby and the dressing (any layer; dimensions aside): joinery / fixture evidence
    def inside(o, box):
        x0, y0, x1, y1 = box
        hits = []
        for e in doc.modelspace():
            t = e.dxftype()
            if t in ("DIMENSION",):
                continue
            try:
                from ezdxf import bbox as _bb
                b = _bb.extents([e])
            except Exception:
                continue
            if not b.has_data:
                continue
            cx = ((b.extmin.x + b.extmax.x) / 2 - o[0]) * unit
            cy = ((b.extmin.y + b.extmax.y) / 2 - o[1]) * unit
            if x0 + 0.01 < cx < x1 - 0.01 and y0 + 0.01 < cy < y1 - 0.01:
                lay = e.dxf.get("layer") if e.dxf.is_supported("layer") else None
                hits.append(rec(e.dxf.handle, o) if t in ("LINE", "ARC", "LWPOLYLINE")
                            else {"handle": e.dxf.handle, "type": t, "layer": lay})
        return hits
    lobby_inside = inside(o1, (0.0, -2.25, 1.8, -0.15))
    dress_inside = inside(o1, (-1.8, 2.2, -0.15, 4.0))
    out = {"schema": "ALSENAN_T223_INPUT_V1", "lobby_inside": lobby_inside, "dressing_inside": dress_inside, "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip "
           "(P7757.dxf)", "sha256_8": _sha(a.dxf)[:8], "unit": "m (drawing mm x 0.001)",
           "curved_room": room, "dressing": dress, "side_passage": pas,
           "side_passage_mouth_lines_on_any_layer": cross}
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {a.out} (P7757.dxf {out['sha256_8']}; mouth crossings {len(cross)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

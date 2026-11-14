"""T-799 (F-V788-1): does the T-788 cornice 426.31 lm move under R-T788-4 (doors as barriers)? Research only.

R-T788-3 found ONE outdoor piece in the GF open-room clip (the pocket beyond the curved glazing, cut lines 1.475 +
0.891). R-T788-4 can only turn OUTDOOR pieces INDOOR (more barriers, never fewer), so the cornice moves only if that
pocket becomes indoor. Upper bound used here: EVERY block INSERT drawn in the plan box (doors and also furniture /
sanitary blocks) is exploded and its lines / arcs added as barriers; if the pocket stays outdoor with all of them, it
stays outdoor with the doors alone. Prints counts and the verdict only; no coordinates are printed or written.

Usage: bash scripts/agent_env.sh run --tree task-T-799 research/agents_t799/t799_cornice_check.py <P7757.dxf> <private dir>
"""
from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t788"))
sys.path.insert(0, str(HERE))
import t788_zone_pieces as Z  # noqa: E402
import t788_rules as R3  # noqa: E402
import t799_rules as R4  # noqa: E402


def insert_lines(dxf):
    import ezdxf
    from ezdxf import path as zpath
    from shapely.geometry import LineString, Point, box

    doc = ezdxf.readfile(str(dxf))
    plan = box(min(v[0] for v in Z.FLOORS.values()), Z.Y0, max(v[1] for v in Z.FLOORS.values()), Z.Y1)
    out, n_ins = [], 0
    for e in doc.modelspace().query("INSERT"):
        if not plan.contains(Point(e.dxf.insert.x / 1000, e.dxf.insert.y / 1000)):
            continue
        n_ins += 1
        try:
            subs = list(e.virtual_entities())
        except Exception:
            continue
        for v in subs:
            if v.dxftype() not in ("LINE", "LWPOLYLINE", "ARC", "POLYLINE", "CIRCLE"):
                continue
            try:
                pts = [(q.x / 1000, q.y / 1000) for q in zpath.make_path(v).flattening(5)]
            except Exception:
                continue
            if len(pts) >= 2:
                out.append(LineString(pts))
    return out, n_ins


def main(dxf, priv):
    from shapely.geometry import Polygon, box
    import json
    from shapely import wkt

    Z.ensure_faces(dxf, priv)
    ents, _ = Z.entities(dxf)
    bar = [g for *_, g in ents]
    doors, n_ins = insert_lines(dxf)
    gf = [wkt.loads(o["wkt"]) for o in json.load(open(priv / "gf_rooms.json"))["faces"]]
    G0 = max(gf, key=lambda g: g.area)
    gclip = Polygon([(-148.2, -805.094), (-129.07, -805.094), (-129.07, -797.594), (-131.0, -797.594),
                     (-131.0, -795.9), (-145.05, -795.9), (-145.05, -800.45), (-148.2, -800.45)])
    LB, PB = box(-140.6, -796.0, -137.85, -793.0), box(-148.2, -805.2, -145.05, -800.45)
    face = G0.difference(LB).difference(PB)
    _, p3 = R3.split_outdoor(face, gclip, bar)
    _, p4 = R4.split_outdoor_v4(face, gclip, bar, doors)
    res = {"barrier_lines": len(bar), "inserts_in_plan": n_ins, "insert_lines_added": len(doors),
           "outdoor_pieces_R3": len(p3), "outdoor_area_R3_m2": round(sum(q.area for q in p3), 3),
           "outdoor_pieces_R4_upper_bound": len(p4), "outdoor_area_R4_m2": round(sum(q.area for q in p4), 3)}
    res["cornice_moves"] = res["outdoor_pieces_R4_upper_bound"] != res["outdoor_pieces_R3"] or \
        abs(res["outdoor_area_R4_m2"] - res["outdoor_area_R3_m2"]) > 0.001
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))

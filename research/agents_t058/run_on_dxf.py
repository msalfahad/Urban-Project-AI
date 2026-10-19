"""T-058 read-only check: run CONCRETE_STRIP_GUARD_V1 on band polylines of a real DXF (nothing is written).

    python3 -I research/agents_t058/run_on_dxf.py <file.dxf> --band <handle> [<handle> ...]
        --members <LAYER>=<KIND> [...] [--unit-m 1.0] [--width 0.08 0.8] [--depth 0.60]
        [--explained <handle>:<span> ...]

The band polylines (by DXF handle) are split into their straight spans (ids "<handle>:<span>", span i = vertex i to
i + 1, the intake convention). Members are the closed LWPOLYLINEs of the named layers whose box lies inside the bands'
box grown by 2 m (the same plan frame). `--explained` marks spans the frozen ledger removed (state
EXPLAINED_BY_MEMBER) so the frozen view is printed. Bulge spans are reported and left out (T-048 measures curves).
Prints the totals, rings, held records and the frozen view as JSON. Names no project, sheet or layer of its own.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ezdxf  # noqa: E402

from engine.source import concrete_strip_guard as SG  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dxf")
    ap.add_argument("--band", nargs="+", required=True)
    ap.add_argument("--members", nargs="*", default=[])
    ap.add_argument("--unit-m", type=float, default=1.0)
    ap.add_argument("--width", nargs=2, type=float, default=(0.08, 0.8))
    ap.add_argument("--depth", type=float, default=None)
    ap.add_argument("--explained", nargs="*", default=[])
    a = ap.parse_args(argv)
    doc = ezdxf.readfile(a.dxf)
    msp = doc.modelspace()
    lines, curved, box = [], [], None
    for h in a.band:
        e = doc.entitydb.get(h)
        if e is None or e.dxftype() != "LWPOLYLINE":
            raise SystemExit(f"band {h}: not an LWPOLYLINE")
        pts = list(e.get_points("xyb"))
        n = len(pts) if e.closed else len(pts) - 1
        for i in range(n):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            sid = f"{h}:{i}"
            if abs(p[2]) > 1e-12:
                curved.append(sid)
                continue
            lines.append({"id": sid, "layer": e.dxf.layer, "a": (p[0], p[1]), "b": (q[0], q[1]),
                          "state": "EXPLAINED_BY_MEMBER" if sid in a.explained else
                          ("UNEXPLAINED" if a.explained else None)})
        for x, y, _ in pts:
            box = (x, y, x, y) if box is None else (min(box[0], x), min(box[1], y), max(box[2], x), max(box[3], y))
    g = 2.0 / a.unit_m
    box = (box[0] - g, box[1] - g, box[2] + g, box[3] + g)
    kinds = dict(m.split("=", 1) for m in a.members)
    members = []
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer not in kinds or not e.closed:
            continue
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if all(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in pts):
            members.append({"id": e.dxf.handle, "kind": kinds[e.dxf.layer], "poly": pts})
    res = SG.guard(lines, members, a.unit_m, tuple(a.width), section_depth_m=a.depth)
    out = {"bands": a.band, "n_faces": len(lines), "curved_spans_left_out": curved, "n_members": len(members),
           "members_by_kind": {k: sum(1 for m in members if m["kind"] == k) for k in sorted(set(kinds.values()))},
           "totals": res["totals"], "rings": res["rings"],
           "faces": [{k: f[k] for k in ("id", "length_m", "in_strip_length_m", "covered_share", "frozen_5pt_share")}
                     for f in res["faces"]],
           "held": [{k: h.get(k) for k in ("reason", "id", "faces", "members", "length_m", "strip_length_m")}
                    for h in res["held"]],
           "unsupported": res["unsupported"], "frozen_view": res["frozen_view"]}
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()

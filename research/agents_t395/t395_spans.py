"""T-395 own spans: face-to-face length of the 5 largest valued beam runs per floor from their own drawn edge lines, and
the support outlines at their ends (DXF handles), read on the Drive copy of 'ST7757 dxf.dxf' (private; outside the repo).

For each run the route G band polygons (research/agents_t110/scripts/bands.py, drawing metres, fit <= 0.6 mm) locate the
member; every LINE on layers 1 / 2 / 5 / S-BEAM parallel to the band axis (<= 0.5 degree) and lying on one of the band's
long sides (<= 15 mm) is a drawn edge; its length clipped to the band's extent along the axis is that edge's face-to-face
length. S-COL.BON closed outlines within 15 mm of a band end are its end supports (extent along the axis from their own
vertices). Output (private): SPANS_T395.json with handles, edge lengths and support extents; no coordinates.

    python3 -I research/agents_t395/t395_spans.py <private>/ST7757_dxf.dxf <bands.json> <private>/t395/RUNS_T395.csv \
        <private>/t395/SPANS_T395.json
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict

EDGE_LAYERS = {"1", "2", "5", "S-BEAM"}
TOL_SIDE = 0.015
TOL_ANG = math.radians(0.5)
TOP = 5


def _axis(pts):
    best = max(((pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))), key=lambda s: math.dist(*s))
    (x0, y0), (x1, y1) = best
    L = math.dist(best[0], best[1])
    return ((x1 - x0) / L, (y1 - y0) / L)


def _proj(p, o, u):
    return (p[0] - o[0]) * u[0] + (p[1] - o[1]) * u[1]


def _perp(p, o, u):
    return -(p[0] - o[0]) * u[1] + (p[1] - o[1]) * u[0]


def read_dxf(path):
    import ezdxf
    msp = ezdxf.readfile(path).modelspace()
    lines, cols = [], []
    for e in msp:
        lay = e.dxf.layer if e.dxf.hasattr("layer") else ""
        if e.dxftype() == "LINE" and lay in EDGE_LAYERS:
            a, b = e.dxf.start, e.dxf.end
            lines.append((e.dxf.handle, lay, (a[0] / 1000, a[1] / 1000), (b[0] / 1000, b[1] / 1000)))
        elif e.dxftype() == "LWPOLYLINE" and lay == "S-COL.BON" and e.closed:
            cols.append((e.dxf.handle, [(p[0] / 1000, p[1] / 1000) for p in e.get_points("xy")]))
    return lines, cols


def span(pieces, bands, lines, cols):
    """Own face-to-face reading of a run from its pieces (in order of the band ids)."""
    out = {"pieces": [], "f2f_m": 0.0, "supports": []}
    for pk in pieces:
        st, band = pk.split(":")
        b = bands.get(f"{band}@{st}")
        if not b:
            out["pieces"].append({"piece": pk, "error": "no band polygon"})
            continue
        pts = b["pts"]
        u = _axis(pts)
        o = pts[0]
        s = [_proj(p, o, u) for p in pts]
        n = [_perp(p, o, u) for p in pts]
        smin, smax, nmin, nmax = min(s), max(s), min(n), max(n)
        edges = []
        for h, lay, a, c in lines:
            d = (c[0] - a[0], c[1] - a[1])
            L = math.hypot(*d)
            if L < 0.05:
                continue
            ang = abs(math.asin(max(-1, min(1, (d[0] * u[1] - d[1] * u[0]) / L))))
            if ang > TOL_ANG:
                continue
            na, nc = _perp(a, o, u), _perp(c, o, u)
            side = None
            for nv, nm in ((nmin, "S0"), (nmax, "S1")):
                if abs(na - nv) <= TOL_SIDE and abs(nc - nv) <= TOL_SIDE:
                    side = nm
            if not side:
                continue
            sa, sc = sorted((_proj(a, o, u), _proj(c, o, u)))
            clip = min(sc, smax) - max(sa, smin)
            if clip > 0.05:
                edges.append({"handle": h, "layer": lay, "side": side, "clipped_m": round(clip, 4),
                              "line_m": round(L, 4)})
        by_side = defaultdict(float)
        for e in edges:
            by_side[e["side"]] += e["clipped_m"]
        f2f = round(sum(by_side.values()) / max(len(by_side), 1), 4) if by_side else None
        sup = []
        for h, cp in cols:
            cs = [_proj(p, o, u) for p in cp]
            cn = [_perp(p, o, u) for p in cp]
            if max(cn) < nmin - TOL_SIDE or min(cn) > nmax + TOL_SIDE:
                continue
            for end, sv in (("start", smin), ("end", smax)):
                if min(cs) - TOL_SIDE <= sv <= max(cs) + TOL_SIDE:
                    sup.append({"piece": pk, "end": end, "handle": h, "along_axis_m": round(max(cs) - min(cs), 4)})
        out["pieces"].append({"piece": pk, "band_len_m": round(smax - smin, 4), "edges": edges,
                              "f2f_m": f2f, "sides": len(by_side)})
        out["supports"].extend(sup)
        if f2f:
            out["f2f_m"] += f2f
    out["f2f_m"] = round(out["f2f_m"], 4)
    return out


def main(dxf, bands_path, runs_csv, out_path):
    bands = json.load(open(bands_path, encoding="utf-8"))
    lines, cols = read_dxf(dxf)
    runs = [r for r in csv.DictReader(open(runs_csv, encoding="utf-8")) if r["status"] == "VALUED" and r["pieces"]]
    res = {}
    for fl in ("GF", "1F", "2F"):
        top = sorted([r for r in runs if r["floor"] == fl], key=lambda r: -float(r["m3"]))[:TOP]
        for r in top:
            sp = span(r["pieces"].split(";"), bands, lines, cols)
            sp.update({"floor": fl, "mark": r["mark"], "run": r["run"], "line_id": r["line_id"],
                       "engine_m3": float(r["m3"]), "engine_L_eff": float(r["L_eff"])})
            res[r["line_id"]] = sp
            print(fl, r["mark"], r["run"], "engine L", r["L_eff"], "own f2f", sp["f2f_m"],
                  [(p["piece"], p.get("f2f_m"), [e["handle"] for e in p.get("edges", [])]) for p in sp["pieces"]],
                  [(s["end"], s["handle"], s["along_axis_m"]) for s in sp["supports"]])
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])

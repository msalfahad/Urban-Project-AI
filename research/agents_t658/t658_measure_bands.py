"""T-658 r2: drawn plan area of the ground-beam runs whose outline is not a rectangle (oblique band, band ending on a
curved face), measured from the structural DXF by entity handle (R-T658-7).

The DXF is the owner's private drawing: it is read from the path given on the command line (decoded by the wrapper into
.work/private only) and NEVER copied. This file carries no coordinate: each outline is a list of vertex RULES over
committed band handles (the T-426 census 'drawn_band' ids and the column / face handles); the output carries only derived
member figures (areas in m2, edge lengths in m, the band width) plus the DXF sha256 prefix.

Run: python -I research/agents_t658/t658_measure_bands.py <decoded ST dxf>  -> research/agents_t658/out/T658_BAND_AREAS.json
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out/T658_BAND_AREAS.json"
ARC_STEPS = 20000          # chord steps on a curved face (sagitta error far below 1e-6 m2)

# Vertex rules, in order around the outline:
#   ("X", a, b)        intersection of the infinite lines of handle a and handle b (edge extended to its owning face)
#   ("X", a, "h#i")    ... with segment i of LWPOLYLINE h (column face)
#   ("E", h, 0 | 1)    the drawn start (0) / end (1) point of LINE h, as drawn
#   ("V", h, i)        vertex i of LWPOLYLINE h (column corner)
#   ("XA", e, arc)     intersection of edge line e with the circle of ARC arc, nearest to e's drawn end
#   ("ARC", arc, n)    walk the arc face between the previous and next vertex (n = ARC_STEPS)
RUNS = {
    # oblique band 180+181 (45 deg) from face 176 to face 180D; 181 drawn open-ended short of 180D
    "BAND0038:EXTENDED": {"edges": ("180", "181"), "outline": [("X", "180", "176"), ("X", "180", "180D"),
                                                                ("X", "181", "180D"), ("X", "181", "176")]},
    "BAND0038:AS_DRAWN": {"edges": ("180", "181"), "outline": [("X", "180", "176"), ("E", "180", 1),
                                                                ("E", "181", 1), ("X", "181", "176")]},
    # oblique band 182+183 from the face corner 7C8 / 7C3 to face 17E (both edges end on 17E as drawn)
    "BAND0039": {"edges": ("182", "183"), "outline": [("X", "182", "17E"), ("X", "182", "7C8"), ("X", "7C8", "7C3"),
                                                      ("X", "183", "7C3"), ("X", "183", "17E")]},
    # oblique band 17E+17F from face 7E6 to column 1EF (column netted: 17E ends on its top face, 17F on its side face)
    "BAND0037.1": {"edges": ("17E", "17F"), "outline": [("X", "17E", "7E6"), ("X", "17E", "1EF#0"), ("V", "1EF", 1),
                                                        ("X", "17F", "1EF#1"), ("X", "17F", "7E6")]},
    # band 177+7CD run #2 from column 245 to the outer face (arc 158) of the curved band
    "BAND0008.2": {"edges": ("177", "7CD"), "outline": [("X", "177", "245#2"), ("XA", "177", "158"),
                                                        ("ARC", "158", ARC_STEPS), ("XA", "7CD", "158"),
                                                        ("X", "7CD", "245#2")]},
    # orthogonal controls (rectangles): the area must equal span x width
    "BAND0040": {"edges": ("180D", "180E"), "outline": [("X", "180D", "176"), ("X", "180D", "175"),
                                                        ("X", "180E", "175"), ("X", "180E", "176")]},
    "BAND0034": {"edges": ("16F", "7FF"), "outline": [("E", "16F", 0), ("E", "16F", 1), ("E", "7FF", 1),
                                                      ("E", "7FF", 0)]},
    # loaded (D-33) orthogonal runs: drawn outline to the owning faces / column faces
    "BAND0019": {"edges": ("142", "7D8"), "outline": [("E", "142", 0), ("E", "142", 1), ("E", "7D8", 1),
                                                      ("E", "7D8", 0)]},
    "BAND0010.3": {"edges": ("184", "7CF"), "outline": [("X", "184", "23C#2"), ("E", "184", 1), ("E", "7CF", 1),
                                                        ("X", "7CF", "23C#2")]},
    "BAND0008.1": {"edges": ("177", "7CD"), "outline": [("E", "177", 0), ("X", "177", "245#0"), ("X", "7CD", "245#0"),
                                                        ("E", "7CD", 0)]},
    "BAND0023:7DC+7DD#1": {"edges": ("7DC", "7DD"), "outline": [("X", "7DC", "7CF"), ("X", "7DC", "7F5#3"),
                                                                ("X", "7DD", "7F5#3"), ("X", "7DD", "7CF")]},
    "BAND0032:7E7+7E8#2": {"edges": ("7E7", "7E8"), "outline": [("X", "7E7", "7ED#1"), ("X", "7E7", "177"),
                                                                ("X", "7E8", "177"), ("X", "7E8", "7ED#1")]},
}


def _ln(doc, h):
    e = doc.entitydb.get(h.split("#")[0])
    if e is None:
        raise KeyError(f"handle {h} not in the drawing")
    if "#" in h:
        pts = [tuple(p[:2]) for p in e.get_points()]
        i = int(h.split("#")[1])
        return pts[i], pts[(i + 1) % len(pts)]
    if e.dxftype() != "LINE":
        raise KeyError(f"handle {h} is {e.dxftype()}, not a LINE")
    return tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]


def _x(p1, p2, q1, q2):
    d = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0])
    if abs(d) < 1e-9:
        raise ValueError("parallel lines: no owning-face intersection")
    t = ((q1[0] - p1[0]) * (q2[1] - q1[1]) - (q1[1] - p1[1]) * (q2[0] - q1[0])) / d
    return p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])


def _xa(p1, p2, c, r):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    fx, fy = p1[0] - c[0], p1[1] - c[1]
    a, b, cc = dx * dx + dy * dy, 2 * (fx * dx + fy * dy), fx * fx + fy * fy - r * r
    disc = b * b - 4 * a * cc
    if disc < 0:
        raise ValueError("edge does not meet the curved face")
    ts = [(-b - math.sqrt(disc)) / (2 * a), (-b + math.sqrt(disc)) / (2 * a)]
    t = min(ts, key=lambda t: abs(t - 1.0))       # nearest to the drawn end
    return p1[0] + t * dx, p1[1] + t * dy


def _area(pts):
    s = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def outline(doc, spec, marks=None):
    out, pend = [], None
    for v in spec["outline"]:
        k = v[0]
        if k == "X":
            p = _x(*_ln(doc, v[1]), *_ln(doc, v[2]))
        elif k == "E":
            p = _ln(doc, v[1])[v[2]]
        elif k == "V":
            p = tuple(list(doc.entitydb.get(v[1]).get_points())[v[2]][:2])
        elif k == "XA":
            arc = doc.entitydb.get(v[2])
            p = _xa(*_ln(doc, v[1]), tuple(arc.dxf.center)[:2], arc.dxf.radius)
        elif k == "ARC":
            pend = doc.entitydb.get(v[1]), v[2]
            continue
        if pend is not None:                       # walk the arc from the previous vertex to this one (short way)
            arc, n = pend
            c, r = tuple(arc.dxf.center)[:2], arc.dxf.radius
            a0 = math.atan2(out[-1][1] - c[1], out[-1][0] - c[0])
            a1 = math.atan2(p[1] - c[1], p[0] - c[0])
            da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
            out += [(c[0] + r * math.cos(a0 + da * i / n), c[1] + r * math.sin(a0 + da * i / n)) for i in range(1, n)]
            pend = None
        out.append(p)
        if marks is not None:
            marks.append(p)
    return out


def measure(dxf_path: str, runs: dict | None = None) -> dict:
    import ezdxf                                   # noqa: PLC0415 (only the measuring step needs the CAD reader)
    raw = Path(dxf_path).read_bytes()
    doc = ezdxf.readfile(dxf_path)
    res = {}
    for rid, spec in (RUNS if runs is None else runs).items():
        marks = []
        pts = outline(doc, spec, marks)
        # the two band edges inside the outline: first rule vertex -> second (edge a), last -> second-last (edge b)
        band_edges = [math.dist(marks[0], marks[1]), math.dist(marks[-1], marks[-2])]
        (a1, a2), (b1, b2) = _ln(doc, spec["edges"][0]), _ln(doc, spec["edges"][1])
        # width = perpendicular distance between the two edge lines (both directions must agree: parallel edges)
        nx, ny = a2[1] - a1[1], -(a2[0] - a1[0])
        nn = math.hypot(nx, ny)
        w = abs((b1[0] - a1[0]) * nx + (b1[1] - a1[1]) * ny) / nn
        w2 = abs((b2[0] - a1[0]) * nx + (b2[1] - a1[1]) * ny) / nn
        if abs(w - w2) > 0.5:
            raise ValueError(f"{rid}: edges not parallel")
        n = len(spec["outline"])
        polygon_edges = [math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))] if n == len(pts) else []
        res[rid] = {"area_m2": round(_area(pts) / 1e6, 6), "width_m": round(w / 1000, 6),
                    "band_edges_m": [round(x / 1000, 6) for x in band_edges],
                    "edge_lengths_drawn_m": [round(math.dist(*_ln(doc, h)) / 1000, 6) for h in spec["edges"]],
                    "outline_edges_m": [round(x / 1000, 6) for x in polygon_edges],
                    "outline_rules": [list(map(str, v)) for v in spec["outline"]]}
    return {"schema": "T658_BAND_AREAS_V1", "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'",
            "dxf_sha256_16": hashlib.sha256(raw).hexdigest()[:16], "units": "drawing mm -> m", "runs": res}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: t658_measure_bands.py <decoded ST dxf in .work/private>")
    out = measure(sys.argv[1])
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: (v["area_m2"], v["width_m"], v["outline_edges_m"]) for k, v in out["runs"].items()}, indent=1))


if __name__ == "__main__":
    main()

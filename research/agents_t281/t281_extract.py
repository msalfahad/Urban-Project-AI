"""T-281 re-measure helper: the stair-soffit primitives of 'ST7757 dxf.dxf' (Drive 'Alsenan chalet project', private
copy, sha256 9f9d1179...) by handle, printed as LENGTHS AND AREAS ONLY (no coordinates leave this script).

    python3 -I research/agents_t281/t281_extract.py <ST7757 dxf.dxf> [--json]

Reads (drawing units mm, sheet p.4 = GF roof slab plan, p.5 = 1F roof slab plan):
  ST-01 p.4: shaft walls 284 / 296, north edge 279, B20 band 458 / 2C6, MS1-L riser lines 45A .. 25E, MS1-U 25B .. 459,
       closing line 2F3, column 36B; p.5: 5E3 / 5D4 / 5C0, MS2-L 646 .. 632, MS2-U 62F .. 644, B23 5E4 / 5E1, step line
       5E2, well 62D / 62E / 633, column 691.
  ST-02 p.4: arcs 2DE / 2DD (common centre), first curved riser 2EA, last curved 2DF, straight flight 2BA .. 2C4, wall
       283, light-well edge 2D0, opening edge 2CF, slab edge 289, top riser 315, RS-A first riser 2C8, CA member 54E,
       columns 380 / 374, hidden pairs 535 / 536 and 2CC / 2CD.
And the slab-plan faces of research/agents_t139/slab_faces.py (T-139 polygonisation, same file) intersected with the
ST-02 pieces, for the T-271 stair-zone reconciliation. Requires ezdxf and shapely (the pinned venv)."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t139"))


def _line(doc, h):
    e = doc.entitydb.get(h)
    if e is None or e.dxftype() != "LINE":
        raise SystemExit(f"handle {h} is not a LINE in this file")
    return (e.dxf.start.x / 1000, e.dxf.start.y / 1000), (e.dxf.end.x / 1000, e.dxf.end.y / 1000)


def _poly(doc, h):
    e = doc.entitydb.get(h)
    if e is None or e.dxftype() != "LWPOLYLINE":
        raise SystemExit(f"handle {h} is not a LWPOLYLINE in this file")
    p = [(q[0] / 1000, q[1] / 1000) for q in e.get_points()]
    return min(a for a, _ in p), max(a for a, _ in p), min(b for _, b in p), max(b for _, b in p)


def _arc(doc, h):
    e = doc.entitydb.get(h)
    return (e.dxf.center.x / 1000, e.dxf.center.y / 1000), e.dxf.radius / 1000, e.dxf.start_angle, e.dxf.end_angle


def _sector(c, ri, ro, a0, a1, n=2048):
    o = [(c[0] + ro * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
          c[1] + ro * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    i_ = [(c[0] + ri * math.cos(math.radians(a1 - (a1 - a0) * i / n)),
           c[1] + ri * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return Polygon(o + i_)


def _halfplane(p, q, side):
    (x1, y1), (x2, y2) = p, q
    dx, dy, big = x2 - x1, y2 - y1, 100.0
    a, b = (x1 - dx * big, y1 - dy * big), (x2 + dx * big, y2 + dy * big)
    nx, ny = -dy, dx
    s = 1 if (side[0] - x1) * nx + (side[1] - y1) * ny > 0 else -1
    return Polygon([a, b, (b[0] + s * nx * big, b[1] + s * ny * big), (a[0] + s * nx * big, a[1] + s * ny * big)])


def measure(path):
    doc = ezdxf.readfile(path)
    L = lambda h: _line(doc, h)
    y = lambda h: L(h)[0][1]
    x = lambda h: L(h)[0][0]
    r = {}
    # ---- ST-01, p.4
    r["p4 shaft 284 -> 296"] = x("296") - x("284")
    r["p4 MS1-L 45A -> 25E"] = y("25E") - y("45A")
    r["p4 MS1-L 45A -> B20 face 2C6"] = y("2C6") - y("45A")
    r["p4 MS1-U 459 -> 25B"] = y("25B") - y("459")
    r["p4 MS1-U last riser 459 inside B20 (2C6 - 459)"] = y("2C6") - y("459")
    r["p4 MS1-LD 25B -> 279"] = y("279") - y("25B")
    r["p4 MS1-LD 2F3 -> 296"] = x("296") - x("2F3")
    r["p4 MS1-T 284 -> 2F3"] = x("2F3") - x("284")
    r["p4 MS1-T 25E -> 279"] = y("279") - y("25E")
    r["p4 B20 band 458 -> 2C6"] = y("2C6") - y("458")
    c = _poly(doc, "36B")
    r["p4 column 36B into the west lane"] = c[1] - x("284")
    r["p4 column 36B from 45A (start, end)"] = (c[2] - y("45A"), c[3] - y("45A"))
    # ---- ST-01, p.5
    r["p5 shaft 5E3 -> 5D4"] = x("5D4") - x("5E3")
    r["p5 MS2-L 646 -> 632"] = y("632") - y("646")
    r["p5 MS2-LD-W 632 -> 5C0"] = y("5C0") - y("632")
    r["p5 MS2-LD-W 5E3 -> 5E2"] = x("5E2") - x("5E3")
    r["p5 MS2-LD-E 62F -> 5C0"] = y("5C0") - y("62F")
    r["p5 MS2-LD-E 5E2 -> 5D4"] = x("5D4") - x("5E2")
    r["p5 MS2-U 644 -> 62F"] = y("62F") - y("644")
    r["p5 B23 band 5E4 -> 5E1"] = y("5E1") - y("5E4")
    r["p5 well 62D -> 62E"] = x("62E") - x("62D")
    r["p5 well 5E1 -> 633"] = y("633") - y("5E1")
    c = _poly(doc, "691")
    r["p5 column 691 into the west lane"] = c[1] - x("5E3")
    r["p5 column 691 from 646 (start, end)"] = (c[2] - y("646"), c[3] - y("646"))
    # ---- ST-02, p.4
    (cx, cy), ri, a0i, a1i = _arc(doc, "2DE")
    _, ro, a0o, a1o = _arc(doc, "2DD")
    r["p4 RS-C arcs 2DE / 2DD radii"] = (ri, ro)
    p, q = L("2EA")
    ang = lambda pt: math.degrees(math.atan2(pt[1] - cy, pt[0] - cx)) % 360
    r["p4 RS-C first riser 2EA angles (inner, outer end)"] = (ang(p), ang(q))
    r["p4 RS-C arc start angles 2DE / 2DD"] = (a0i, a0o)
    wall, x2ba = y("283"), x("2BA")
    ann = _sector((cx, cy), ri, ro, 150, 290).intersection(box(cx - 10, wall, cx + 10, cy + 10))
    hp = _halfplane(p, q, (cx - 2.0, wall + 1.0))
    rsc = ann.intersection(hp).intersection(box(cx - 10, wall, x2ba, cy + 10))
    r["p4 RS-C plan 2EA -> 2BA (m2)"] = rsc.area
    r["p4 RS-C part 270 deg -> 2BA (m2)"] = rsc.intersection(box(cx, wall, x2ba, cy)).area
    pre = ann.intersection(box(cx - 10, wall, x2ba, cy + 10)).difference(hp).intersection(
        _sector((cx, cy), ri, ro, min(a0i, a0o), 200))
    r["p4 RS-C arc start -> 2EA, bottom-step strip (m2)"] = pre.area
    r["p4 RS-S 2BA -> 2C4"] = x("2C4") - x("2BA")
    r["p4 RS-S lane 283 -> 2D0"] = y("2D0") - y("283")
    r["p4 RS-LD 2C4 -> 289"] = x("289") - x("2C4")
    r["p4 RS-LD 283 -> 2C8"] = y("2C8") - y("283")
    r["p4 RS-A 2C8 -> 315"] = y("315") - y("2C8")
    r["p4 RS-A lane 2CF -> 289"] = x("289") - x("2CF")
    r["p4 slab north of 315 to 2CE"] = y("2CE") - y("315")
    ca = _poly(doc, "54E")
    r["p4 CA 54E from 2BA (s0, s1), from 283 (u0, u1)"] = (ca[0] - x2ba, ca[1] - x2ba, ca[2] - wall, ca[3] - wall)
    c380 = _poly(doc, "380")
    r["p4 column 380 from 2BA (s0, s1), into the lane"] = (c380[0] - x2ba, c380[1] - x2ba, c380[3] - wall)
    c374 = _poly(doc, "374")
    r["p4 column 374 from 2C4 (s0, s1), into the landing"] = (c374[0] - x("2C4"), x("289") - x("2C4"),
                                                              c374[3] - wall)
    h5, h6 = L("535"), L("536")
    r["p4 hidden pair 536 / 535 from 283 (u0, u1)"] = (h6[0][1] - wall, h5[0][1] - wall)
    r["p4 hidden pair 535 end past 2C4"] = max(h5[0][0], h5[1][0]) - x("2C4")
    r["p4 hidden pair 535 start before 2BA"] = x2ba - min(h5[0][0], h5[1][0])
    r["p4 hidden pair 2CC / 2CD from 2C4 (s0, s1)"] = (x("2CC") - x("2C4"), x("2CD") - x("2C4"))
    r["p4 hidden pair 2CC / 2CD from 2CF (u0, u1)"] = (x("2CC") - x("2CF"), x("2CD") - x("2CF"))
    r["p4 band B3 'With Stair' GF-159 from 2BA (s0) and width from 283"] = None
    # ---- T-139 faces (same file) against the ST-02 pieces
    import slab_faces  # noqa: E402  (T-139 helper, research only)
    faces = {f"GF-{i:03d}": f for i, f in enumerate(slab_faces.faces(doc, slab_faces.SHEETS["GF"]))}
    from shapely import wkt
    F = {k: wkt.loads(v["wkt"]) for k, v in faces.items()}
    rss = box(x2ba, wall, x("2C4"), y("2D0"))
    rsld = box(x("2C4"), wall, x("289"), y("2C8")).difference(box(c374[0], c374[2], c374[1], c374[3]))
    rsa = box(x("2CF"), y("2C8"), x("289"), y("315"))
    pieces = {"RS-C": rsc, "RS-S": rss, "RS-LD": rsld, "RS-A": rsa}
    union = unary_union(list(pieces.values()))
    b3 = F["GF-159"]
    r["p4 band B3 'With Stair' GF-159 from 2BA (s0) and width from 283"] = (b3.bounds[0] - x2ba, b3.bounds[3] - wall)
    inter = {}
    for k, g in pieces.items():
        inter[k] = {fid: round(f.intersection(g).area, 6) for fid, f in F.items() if f.intersection(g).area > 1e-6}
        inter[k]["outside every face"] = round(g.area - sum(inter[k].values()), 6)
    r["face intersections (m2)"] = inter
    for fid in ("GF-130", "GF-131", "GF-132", "GF-145", "GF-159", "GF-025"):
        r[f"face {fid} area / inside the ST-02 pieces (m2)"] = (F[fid].area, F[fid].intersection(union).area)
    r["face GF-025 area"] = F["GF-025"].area
    f1 = {f"1F-{i:03d}": f for i, f in enumerate(slab_faces.faces(doc, slab_faces.SHEETS["1F"]))}
    r["face 1F-016 area"] = wkt.loads(f1["1F-016"]["wkt"]).area
    r["face 1F-016 inside the shaft 5E3 / 5D4 / 5E1 / 5C0"] = wkt.loads(f1["1F-016"]["wkt"]).intersection(
        box(x("5E3"), y("5E1"), x("5D4"), y("5C0"))).area
    return r


def main(argv=None):
    a = argv or sys.argv[1:]
    r = measure(a[0])
    if "--json" in a:
        print(json.dumps(r, indent=1, default=float))
        return
    for k, v in r.items():
        if isinstance(v, dict):
            print(k)
            for kk, vv in v.items():
                print(f"   {kk:8s} {vv}")
        elif isinstance(v, tuple):
            print(f"{k:72s} " + ", ".join(f"{t:.6f}" for t in v))
        else:
            print(f"{k:72s} {v:.6f}")


if __name__ == "__main__":
    main()

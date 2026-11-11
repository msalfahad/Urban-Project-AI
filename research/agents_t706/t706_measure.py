"""T-706 own re-measure of the development villa's three suspended slab plans (GF 'GROUND FLOOR ROOF SLAB' frame FR06,
1F frame FR04 as a cross-check of T-688, 2F roof frame FR02) from the private structural DXF, with a noding of its own,
and the physical census of every face the engine EXCLUDED and of every own face no engine line owns.

Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179...), decoded with `agent_env.sh decode` into
.work/private (never committed). Writes NUMBERS ONLY to out/T706_OWN_PANELS.json: engine element ids, areas, widths,
classes, counts; no coordinate, label text, client name or drawing content.

Own noding (R-T706-2): T-688's (layers '1', 'S-COL.BON', 'S-BOUN', every open end extended 30 mm, arcs at a 0.2 mm
sagitta, polygonized) PLUS the member-edge layer 'S-BEAM': without it one GF face swallowed five engine panels, five
beam strips and the B27 strip (44.879 m2), i.e. it was not a check of those panels (R-T706-2 (a) refuses it).
Engine faces: the route G slab stage (engine.source.slab_engine.panels) is run read-only on the same DXF and its faces
(id, class, area, interior point) are captured in memory; the sheet-local origin of route G is placed on the drawing
by the one translation that the uniquely-sized faces agree on (all of them agree to 0.1 mm); each V3.0.70 slab line is
then located by its engine face's interior point (never by area).

    .work/venv/bin/python -I research/agents_t706/t706_measure.py --dxf .work/private/st7757.dxf --work <private dir>
        [--write]
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, ROOT / "research" / "agents_t688"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import t688_measure as M  # noqa: E402  (T-688 noding helpers, unchanged)

INDEX = "research/agents_t693/out/LINE_INDEX_V3_0_70.json"
OUT = HERE / "out" / "T706_OWN_PANELS.json"
FRAMES = {"GF": "FR06", "1F": "FR04", "2F": "FR02"}
LAYERS = ("1", "S-COL.BON", "S-BOUN", "S-BEAM")
CONVENTIONS = "engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json"
PROFILE = "research/urban_engine_m4_correctness/profile_st7757_m4.json"


def engine_faces(dxf, work):
    """route G run (read-only, outputs under the private work dir); returns {face_id: face} of every slab face."""
    from engine.source import slab_engine as SE
    from tools import urban_boq_m2 as CLI
    real, cap = SE.panels, {}

    def wrap(*a, **k):
        r = real(*a, **k)
        for f in r.get("faces", []):
            cap.setdefault(f["face_id"], {"cls": f["class"], "m2": f["area_m2"], "pt": f["point"],
                                          "poly": f["polygon"], "t_basis": f.get("t_basis")})
        return r
    SE.panels = wrap
    try:
        CLI.main(["run", "--drawings", dxf, "--out", str(Path(work) / "route_g"), "--route", "G", "--conventions",
                  str(ROOT / CONVENTIONS), "--profile", str(ROOT / PROFILE), "--no-pdf", "--no-xlsx"])
    finally:
        SE.panels = real
    return cap


def dims(f):
    xs = list(f.minimum_rotated_rectangle.exterior.coords)
    a, b = math.dist(xs[0], xs[1]) / 1000, math.dist(xs[1], xs[2]) / 1000
    return round(min(a, b), 4), round(max(a, b), 4)


def evidence(f, texts, openings, inner):
    """drawn evidence of one own face (numbers and flags only): narrow / long side of its minimum rotated rectangle,
    perimeter, the inscribed width (diameter of the largest inscribed circle: the true width of a straight, bent or
    curved strip), the band width w = (P - sqrt(P^2 - 16 A)) / 4 (exact for a rectangle / constant-width band),
    opening-symbol and inner (flight) lines crossing it, a member label / stair label / thickness mark inside."""
    labels = [t[1] for t in texts if f.contains(t[0])]
    a, per = f.area / 1e6, f.length / 1000
    disc = per * per - 16 * a
    import shapely
    mic = shapely.maximum_inscribed_circle(f, tolerance=0.5)       # mm; its length is the inscribed radius
    return {"own_dims_m": dims(f), "own_perimeter_m": round(per, 4),
            "own_inscribed_width_m": round(2 * mic.length / 1000, 4),
            "own_band_width_m": round((per - math.sqrt(disc)) / 4, 4) if disc >= 0 else None,
            "opening_lines": sum(1 for g in openings if f.intersection(g).length > 100),
            "inner_lines": sum(1 for g in inner if f.intersection(g).length > 100),
            "member_label_inside": any(s[:1] in "BC" and any(ch.isdigit() for ch in s) and len(s) <= 5 for s in labels),
            "stair_label_inside": any("STAIR" in s.upper() for s in labels),
            "thickness_marks_inside": sorted(t[1] for t in texts if t[2] == "S-TEXT-SLAB" and f.contains(t[0])
                                             and t[1] in ("T", "16", "18", "20", "25"))}


def storey(dxf, st, cap, doc):
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    M.EDGE_LAYERS = LAYERS
    inv = json.loads((ROOT / M.INVENTORY).read_text(encoding="utf-8"))[0]
    box = next(f["box"] for f in inv["frames"] if f["frame_id"] == FRAMES[st])
    edges, openings, inner = M.read_frame(dxf, box)
    faces = M.faces_of(edges)
    idx = json.loads((ROOT / INDEX).read_text(encoding="utf-8"))
    lines = sorted((x for x in idx["lines"] if x["item_code"] == "STR.CONC.SLAB"
                    and x["element_id"].split(":")[2] == st), key=lambda r: r["line_id"])
    # placement: one translation from every uniquely sized engine face >= 2 m2
    offs = Counter()
    for x in lines:
        c = cap.get(x["element_id"].split(":")[-1])
        if not c or c["m2"] < 2.0:
            continue
        hit = [f for f in faces if abs(f.area / 1e6 - c["m2"]) < 0.001]
        if len(hit) == 1:
            b = hit[0].bounds
            offs[(round(b[0] - min(q[0] for q in c["poly"]), 1), round(b[1] - min(q[1] for q in c["poly"]), 1))] += 1
    (ox, oy), n_fit = offs.most_common(1)[0]
    texts = []
    for e in doc.modelspace():
        if e.dxftype() in ("TEXT", "MTEXT"):
            q = e.dxf.insert
            if box[0] <= q.x <= box[2] and box[1] <= q.y <= box[3]:
                texts.append((Point(q.x, q.y), (e.dxf.text if e.dxftype() == "TEXT" else e.text).strip(), e.dxf.layer))
    rows, used = [], {}
    for x in lines:
        cid = x["element_id"].split(":")[-1]
        c = cap[cid]
        p = Point(c["pt"][0] + ox, c["pt"][1] + oy)
        hits = [i for i, f in enumerate(faces) if f.contains(p)]
        own = hits[0] if len(hits) == 1 else None
        if own is not None:
            used.setdefault(own, []).append(x["line_id"])
        r = {"line_id": x["line_id"], "engine_cell": cid, "class": x["class"], "engine_class": c["cls"],
             "engine_face_m2": round(c["m2"], 6), "engine_m3": x["measured_net"],
             "t_m": (round(float(x["measured_net"]) / c["m2"], 3) if x["measured_net"] else None),
             "t_basis": c["t_basis"], "own_face": own,
             "own_m2": round(faces[own].area / 1e6, 6) if own is not None else None}
        if own is not None:
            r.update(evidence(faces[own], texts, openings, inner))
        rows.append(r)
    for r in rows:
        r["shared"] = r["own_face"] is not None and len(used[r["own_face"]]) > 1
    # census of own faces no engine line owns (>= 0.3 m2, near the plan)
    plan = unary_union([faces[i] for i in used])
    census = []
    for i, f in enumerate(faces):
        a = f.area / 1e6
        if i in used or a < 0.3 or a > 80.0 or f.distance(plan) > 3000:
            continue
        census.append({"own_face": i, "m2": round(a, 6), **evidence(f, texts, openings, inner)})
    # rings of equal faces (a dome drawn on the plan): >= 8 faces of one area (+- 0.0005 m2) whose centroids sit at one
    # radius (+- 1 %) around their mean; a set of equal faces is split at its widest centroid gap until each part rings
    rings, ring_faces = [], set()

    def ring_of(group):
        cx, cy = statistics.mean(faces[i].centroid.x for i in group), statistics.mean(faces[i].centroid.y for i in group)
        rad = [math.hypot(faces[i].centroid.x - cx, faces[i].centroid.y - cy) for i in group]
        return rad, max(rad) - min(rad) <= 0.01 * max(rad)

    def split(group):
        if len(group) < 8:
            return
        rad, ok = ring_of(group)
        if ok:
            rings.append({"segments": len(group), "segment_m2": round(faces[group[0]].area / 1e6, 4),
                          "radius_m": round(statistics.mean(rad) / 1000, 3)})
            ring_faces.update(group)
            return
        for axis in ("x", "y"):
            g = sorted(group, key=lambda i: getattr(faces[i].centroid, axis))
            v = [getattr(faces[i].centroid, axis) for i in g]
            k = max(range(len(v) - 1), key=lambda j: v[j + 1] - v[j])
            if v[k + 1] - v[k] > 1000:
                split(g[:k + 1])
                split(g[k + 1:])
                return
    by_area = {}
    for i, f in enumerate(faces):
        if i not in used and 0.05 <= f.area / 1e6 <= 80.0:
            by_area.setdefault(round(f.area / 1e6 / 0.001), []).append(i)
    for group in by_area.values():
        split(group)
    for c in census:
        c["radial_ring_segment"] = c["own_face"] in ring_faces
    rel = [r for r in rows if r["class"] == "RELEASED"]
    return {"frame": FRAMES[st], "faces": len(faces), "placement_faces": n_fit, "lines": rows, "census": census,
            "radial_rings": rings,
            "released_engine_face_m2": round(sum(r["engine_face_m2"] for r in rel), 6),
            "released_own_m2": round(sum(r["own_m2"] for r in rel if r["own_m2"] is not None and not r["shared"]), 6),
            "released_not_checked": [r["line_id"] for r in rel if r["own_m2"] is None or r["shared"]]}


def run(dxf, work):
    import ezdxf
    cap = engine_faces(dxf, work)
    doc = ezdxf.readfile(dxf)
    return {"schema": "URBAN_T706_OWN_PANELS_V1",
            "source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (private copy; numbers only)",
            "noding": {"layers": list(LAYERS), "ext_mm": M.EXT_MM, "sagitta_mm": M.SAGITTA_MM},
            "index": INDEX, "storeys": {st: storey(dxf, st, cap, doc) for st in FRAMES}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf", required=True)
    ap.add_argument("--work", required=True, help="private directory for the read-only route G run")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    out = run(a.dxf, a.work)
    for st, s in out["storeys"].items():
        print(st, s["frame"], "faces", s["faces"], "placed on", s["placement_faces"], "| released engine",
              s["released_engine_face_m2"], "own", s["released_own_m2"], "| not checked", s["released_not_checked"])
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""T-323 on the development villa: every slab hatch of the three roof-slab plans against the panel built from the
drawn member faces (research only; nothing wired; no BOQ line moved).

Reads the PRIVATE structural DXF at run time (Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf', sha256 9f9d1179...,
decoded into .work/private as ST7757.dxf) and writes only handles, face ids, classes, lengths and areas (no
coordinates, no drawing content) to HATCH_CENSUS_T323.json.

Inputs reused by citation (not re-derived):
  - sheet windows and the member / edge layers: research/agents_t139/slab_faces.py (SHEETS, EDGE; T-139 MERGED, its
    faces re-measured by the Checker); the faces are polygonised exactly as T-139 does (`faces`), and each face is
    matched to its T-139 id and class in research/agents_t139/PANELS.csv by centroid (1 mm) and area (1e-4 m2);
  - the hatch region rule (union of region loops; annotation islands not deducted): T-213 (MERGED), reused through
    slab_hatch_edges.region_of.
Classes of a boundary piece (slab_hatch_edges.py): MEMBER_FACE = on a T-139 EDGE-layer line; FREE_EDGE = on an
opening-edge line (S-OPENING); ANNOTATION_CUT = on / inside an annotation's drawn extent (TEXT / MTEXT / INSERT /
DIMENSION box, a CIRCLE or ARC on a text layer, a bar line on S-REIN-SLAB, a section line on S-SEC.LINE);
UNEXPLAINED = none.

    python3 -I research/agents_t323/alsenan_t323.py <private folder> [--write]
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t139"))
import slab_hatch_edges as E  # noqa: E402
import slab_faces as T139  # noqa: E402

DXF_NAME = "ST7757.dxf"
HATCH_LAYER = "S-HAT.BAT"
# Legend of the roof-slab plans (ST7757.pdf p.4 - p.6 legend boxes; T-213 / T-139 reading): the pattern scale decides.
LEGEND = {("ANSI31", 2000.0): "Sunken slab.", ("ANSI31", 800.0): "Cantilever portion."}
FREE_LAYERS = {"S-OPENING"}
ANN_LINE_LAYERS = {"S-REIN-SLAB", "S-SEC.LINE"}
CANDIDATE = ROOT / "research" / "agents_t146" / "CANDIDATE_V3011_BEAM_SLAB.json"


def _arc(cx, cy, r, a0, a1, n=96):
    if a1 < a0:
        a1 += 360
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def read(path):
    import ezdxf
    from ezdxf import bbox
    from ezdxf import path as P
    from shapely.geometry import LineString, Point, box
    doc = ezdxf.readfile(str(path))
    if doc.header.get("$INSUNITS") != 4:
        raise E.HatchEdgeError("DXF units are not mm")
    msp = doc.modelspace()
    members, frees, anns, hatches = [], [], [], []
    for e in msp:
        t = e.dxftype()
        if not e.dxf.is_supported("layer"):
            continue
        lay = e.dxf.layer
        if t == "HATCH":
            if lay == HATCH_LAYER:
                loops = [[(v.x / 1000, v.y / 1000) for v in P.from_hatch_boundary_path(bp).flattening(0.5)]
                         for bp in e.paths]
                hatches.append((e.dxf.handle, e.dxf.pattern_name, float(e.dxf.pattern_scale), loops))
            continue
        try:
            if t in ("TEXT", "MTEXT", "INSERT", "DIMENSION"):
                b = bbox.extents([e])
                if b.has_data:
                    anns.append((f"{lay} {t} {e.dxf.handle}",
                                 box(b.extmin.x / 1000, b.extmin.y / 1000, b.extmax.x / 1000, b.extmax.y / 1000)))
                continue
            if t in ("CIRCLE", "ARC") and "TEXT" in lay:
                c = e.dxf.center
                anns.append((f"{lay} {t} {e.dxf.handle} r {e.dxf.radius / 1000:.3f}",
                             Point(c.x / 1000, c.y / 1000).buffer(e.dxf.radius / 1000, 64)))
                continue
            pts = None
            if t == "LINE":
                pts = [(e.dxf.start.x / 1000, e.dxf.start.y / 1000), (e.dxf.end.x / 1000, e.dxf.end.y / 1000)]
            elif t == "LWPOLYLINE":
                pts = [(q[0] / 1000, q[1] / 1000) for q in e.get_points()]
                if e.closed:
                    pts.append(pts[0])
            elif t == "ARC":
                pts = _arc(e.dxf.center.x / 1000, e.dxf.center.y / 1000, e.dxf.radius / 1000,
                           e.dxf.start_angle, e.dxf.end_angle)
            elif t == "CIRCLE":
                pts = _arc(e.dxf.center.x / 1000, e.dxf.center.y / 1000, e.dxf.radius / 1000, 0, 360)
            if not pts or len(pts) < 2:
                continue
            g = LineString(pts)
            if lay in T139.EDGE:
                members.append(g)
            elif lay in FREE_LAYERS:
                frees.append(g)
            elif lay in ANN_LINE_LAYERS:
                anns.append((f"{lay} {t} {e.dxf.handle}", g.buffer(0.005)))
        except Exception:     # an entity without usable geometry is neither a face nor an annotation
            continue
    return doc, hatches, members, frees, anns


def sheet_of(x_m, y_m):
    for sh, (x0, x1, y0, y1) in T139.SHEETS.items():
        if x0 / 1000 <= x_m <= x1 / 1000 and y0 / 1000 <= y_m <= y1 / 1000:
            return sh
    return None


def t139_rows():
    with (ROOT / "research" / "agents_t139" / "PANELS.csv").open() as fh:
        return list(csv.DictReader(fh))


def match_face(sheet, f, rows):
    hit = [r for r in rows if r["floor"] == sheet and abs(float(r["cx"]) - f.centroid.x) <= 0.0015
           and abs(float(r["cy"]) - f.centroid.y) <= 0.0015 and abs(float(r["area"]) - f.area) <= 1e-4 + 1e-3 * f.area]
    return hit[0] if len(hit) == 1 else None


def t209_reading(doc, handle):
    """The polygon research/agents_t209/sunken_overlay.py builds (every path, edge START points only, united)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    e, out = doc.entitydb[handle], []
    for p in e.paths:
        v = ([(q[0] / 1000, q[1] / 1000) for q in p.vertices] if hasattr(p, "vertices")
             else [(ed.start[0] / 1000, ed.start[1] / 1000) for ed in p.edges])
        if len(v) >= 3:
            out.append(Polygon(v).buffer(0))
    return unary_union(out)


def support_alignment(c, member_lines, tol=0.02):
    """Metres of ANNOTATION_CUT boundary that lie on the straight EXTENSION of a drawn member-face segment (the
    support-face alignment carried across a band: where a cantilever portion starts)."""
    from shapely.geometry import LineString, Point
    segs = []
    for m in member_lines:
        cs = list(m.coords)
        segs.extend((a, b) for a, b in zip(cs, cs[1:]) if math.dist(a, b) > 0.05)
    tot = 0.0
    for p0, p1, L in E._pieces(c.region.exterior, 0.05):
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        if any(m.distance(Point(mid)) <= tol for m in member_lines):
            continue
        for a, b in segs:
            d = math.dist(a, b)
            ux, uy = (b[0] - a[0]) / d, (b[1] - a[1]) / d
            far = LineString([(a[0] - 50 * ux, a[1] - 50 * uy), (b[0] + 50 * ux, b[1] + 50 * uy)])
            if far.distance(Point(p0)) <= tol and far.distance(Point(p1)) <= tol:
                tot += L
                break
    return round(tot, 3)


def candidate_slab_lines():
    snap = json.loads(CANDIDATE.read_text())
    return [x for x in snap["lines"] if x["item_code"] == "STR.CONC.SLAB"]


def run(private):
    from shapely import wkt
    doc, hatches, members, frees, anns = read(Path(private) / DXF_NAME)
    rows = t139_rows()
    faces = {sh: [(wkt.loads(f["wkt"])) for f in T139.faces(doc, win)] for sh, win in T139.SHEETS.items()}
    slab_lines = candidate_slab_lines()
    census, off_sheet = [], []
    for hd, pat, sc, loops in sorted(hatches, key=lambda h: h[0]):
        x = sum(p[0] for p in loops[0]) / len(loops[0])
        y = sum(p[1] for p in loops[0]) / len(loops[0])
        sh = sheet_of(x, y)
        if sh is None:
            row = {"handle": hd, "pattern": pat, "scale": sc,
                   "why": "not on a roof-slab plan (outside the three T-139 sheet windows)"}
            if pat != "SOLID":       # a wall / ring hatch on the foundation / ground sheets: its ring, for the record
                polys = sorted((E.Polygon(lp).buffer(0) for lp in loops if len(lp) >= 3), key=lambda q: -q.area)
                inner = [q for q in polys[1:] if polys[0].contains(q.representative_point())]
                row.update(outer_m2=round(polys[0].area, 4), islands_m2=[round(q.area, 4) for q in inner],
                           ring_net_m2=round(polys[0].area - sum(q.area for q in inner), 4),
                           role="not a slab legend on these sheets (wall / ring hatch)")
            off_sheet.append(row)
            continue
        if pat == "SOLID":
            off_sheet.append({"handle": hd, "pattern": pat, "scale": sc, "why": "solid fill on a roof-slab sheet"})
            continue
        local_m = [m for m in members if m.distance(E.Polygon(loops[0])) < 1.0]
        local_a = [a for a in anns if a[1].distance(E.Polygon(loops[0])) < 1.0]
        local_f = [f for f in frees if f.distance(E.Polygon(loops[0])) < 1.0]
        c = E.classify_boundary(loops, member_lines=local_m, free_lines=local_f, annotations=local_a)
        reb = E.rebuild_panel(c, faces[sh], annotations=local_a)
        chosen = [f for f in faces[sh] if f.area > E.AREA_EPS and f.intersection(c.region).area >= 0.5 * f.area]
        ids = []
        for f in chosen:
            r = match_face(sh, f, rows)
            ids.append({"t139_id": r["id"] if r else None, "t139_class": r["cls"] if r else "UNMATCHED",
                        "face_m2": round(f.area, 4), "share_under_hatch": round(f.intersection(c.region).area / f.area, 4)})
        hosts = []
        for f in faces[sh]:
            if f.area > E.AREA_EPS and f.intersection(c.region).area > 1e-4 and f.intersection(c.region).area < 0.5 * f.area:
                r = match_face(sh, f, rows)
                hosts.append({"t139_id": r["id"] if r else None, "t139_class": r["cls"] if r else "UNMATCHED",
                              "face_m2": round(f.area, 4), "under_hatch_m2": round(f.intersection(c.region).area, 4)})
        # what a consumer gets if it reads the hatch differently (consumer readings, not panels):
        p0 = E.Polygon(loops[0]).buffer(0)
        chord = t209_reading(doc, hd)
        readings = {"loop1_only_m2": round(p0.area, 4), "loop1_only_perimeter_m": round(p0.exterior.length, 4),
                    "t209_chord_union_m2": round(chord.area, 4)}
        align = support_alignment(c, local_m)
        lines = []
        for i in ids:     # the candidate slab line carrying that face (T-139 m3 = area x t)
            r = next((r for r in rows if r["id"] == i["t139_id"]), None)
            if r and r["cls"] == "SLAB" and r["m3"]:
                hit = [x for x in slab_lines if x["floor"] == sh and x["value"] is not None
                       and abs(x["value"] - float(r["m3"])) <= 2e-4]
                lines.extend({"line_id": x["line_id"], "element_id": x["element_id"], "m3": x["value"]} for x in hit)
        census.append({
            "handle": hd, "sheet": f"{sh} roof slab", "legend": LEGEND.get((pat, sc), f"{pat} scale {sc:g}"),
            "region_loops": c.region_loops, "islands": c.islands,
            "hatch_m2": round(c.region.area, 4), "hatch_perimeter_m": round(c.perimeter, 4),
            "edge_m": {k: round(v, 3) for k, v in c.lengths.items()},
            "annotation_cuts": {k: round(v, 3) for k, v in sorted(c.annotations_hit.items())},
            "hatch_is_panel_outline": c.is_panel_outline,
            "faces_under": ids,
            "rebuilt_status": reb["status"],
            "rebuilt_m2": None if reb["area_m2"] is None else round(reb["area_m2"], 4),
            "rebuilt_perimeter_m": None if reb["perimeter_m"] is None else round(reb["perimeter_m"], 4),
            "residual_m2": None if reb["residual_m2"] is None else round(reb["residual_m2"], 4),
            "residual_annotation_m2": {k: round(v, 4) for k, v in sorted(reb["residual_annotation_m2"].items())},
            "hatch_beyond_panel_under_annotation_m2": {k: round(v, 4) for k, v in
                                                       sorted(reb["outside_annotation_m2"].items())},
            "residual_annotation_net_m2": None if reb["residual_annotation_net_m2"] is None
            else round(reb["residual_annotation_net_m2"], 4),
            "held_why": reb.get("why"), "host_faces": hosts, "annotation_cut_on_member_alignment_m": align,
            "consumer_readings": readings,
            "residual_other_m2": None if reb["residual_other_m2"] is None else round(reb["residual_other_m2"], 4),
            "hatch_outside_panel_m2": round(reb.get("outside_panel_m2", 0.0), 4) if reb["status"] != "HELD" else None,
            "candidate_slab_lines": lines,
        })
    return {"source": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' (sha256 9f9d1179...)",
            "hatch_layer": HATCH_LAYER, "census": census, "off_sheet": off_sheet}


if __name__ == "__main__":
    res = run(sys.argv[1])
    txt = json.dumps(res, indent=1, ensure_ascii=True)
    if "--write" in sys.argv:
        (HERE / "HATCH_CENSUS_T323.json").write_text(txt + "\n")
    print(txt)

"""T-288 on the development villa: which wall pieces of the blockwork register lie under a SUNKEN (lowered) slab panel.

Reads the PRIVATE drawings at run time (decoded into .work/private, never committed):
  Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf'                         -> <private>/ST7757.dxf   (sha 9f9d1179)
  Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)     -> <private>/P7757_DXF_COMPRESSED/P7757.dxf
and writes only handles, ids and lengths (no coordinate, no drawing content) to CLIP_T288.json.

Method (independent of the register; T-213 reading rules for the panels):
  1. The six 'Sunken slab.' regions = HATCH ANSI31 scale 2000 on S-HAT.BAT, built exactly as T-213 does
     (research/agents_t213: region loops united, annotation islands NOT deducted = T-213 rule (a)).
  2. Frame: one translation per storey from the architectural plan to the structural roof-slab sheet, found by matching
     EVERY S-COL.BON column outline of the plan storey to one of the sheet (same area to 1e-4 m2, same centroid after
     the translation to 1 mm); the translation is the median of the matched centroid differences, the residual printed.
     GF walls sit under the GF-roof sheet (panels 275 / 276 / 280 / 287 / 298), 1F walls under the 1F-roof sheet (5BF).
  3. Presence: every architectural wall-face LINE (layer '1') of the storey is clipped by each region SHRUNK 20 mm, so a
     face lying ON a panel edge (a beam face) does not count; every line with a clipped length > 0.5 mm is listed.
  4. Wall centreline: each listed face is paired with the parallel layer-'1' face at the wall thickness (0.15 / 0.20 m,
     1 mm) whose projection overlaps it; the midline over the overlap is clipped by the UNSHRUNK region: that is the
     length of the centreline under the lowered soffit (cross-check of the T-274 piece of the same wall and panel).
WALL_FACES names the face pairs per register wall (read from the plan and the Checker's 02:00 handles); a listed face
that no register wall claims is reported as UNCLAIMED (none is allowed to pass silently).

    python3 -I research/agents_t288/alsenan_clip_t288.py <private folder> [--write]
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t213"))
import alsenan_t213 as T213  # noqa: E402
import sunken_panels as SP  # noqa: E402

SHRINK_M = 0.020
GAP_MAX_M = 0.10
MIN_M = 0.0005
THICK = (0.15, 0.20)
# T-139 slab-face id of each sunken hatch (T-213 t139_match: 5 of 6 exact, 298 -0.0100 m2 at its B28 / column corner)
PANEL_FACE = {"276": "GF-015", "275": "GF-016", "298": "GF-081", "287": "GF-128", "280": "GF-141", "5BF": "1F-018"}
# structural sheet windows (DXF mm, T-274 SHEETS) per storey of the walls they roof
SHEET_MM = {"GF": (40500, 74500, 35500, 51000), "1F": (11500, 36000, 35500, 51000)}
# register wall -> face line handle groups (one group = the faces of one side); read on P7757.dxf
WALL_FACES = {
    "GF-W12": (("94",), ("97",)),
    "GF-W16": (("9F", "A0", "A1"), ("AE", "AF", "B0")),
    "GF-W34": (("326",), ("327",)),
    "GF-W20": (("BD",), ("2DF",)),
    "GF-W31": (("324",), ("325",)),
    "GF-W32": (("31C", "31D", "31E"), ("317", "31A")),
}


# 0.20 m cross lines inside a claimed wall (jamb / cap lines, not wall faces): read on P7757.dxf
OPENING_LINES = {"3C8": "GF-W16 window W09 jamb line", "3C4": "GF-W16 window W10 jamb line",
                 "26C": "GF-W12 glazing cap (wall end)"}


def _lines(msp, layer="1"):
    out = []
    for e in msp.query("LINE"):
        if e.dxf.get("layer") == layer:
            s, t = e.dxf.start, e.dxf.end
            out.append((e.dxf.handle, (s.x, s.y), (t.x, t.y)))
    return out


def _columns(msp):
    from shapely.geometry import Polygon
    out = []
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.get("layer") == "S-COL.BON":
            pts = [p[:2] for p in e.get_points()]
            if len(pts) >= 3:
                pg = Polygon(pts).buffer(0)
                if pg.area > 0:
                    out.append((e.dxf.handle, pg))
    return out


def translation(arch_cols, st_cols, window):
    """median translation arch -> sheet (mm) from columns matched by area; returns (dx, dy, matched, arch_n, resid_mm)."""
    x0, x1, y0, y1 = window
    sc = [(h, p) for h, p in st_cols if x0 <= p.centroid.x <= x1 and y0 <= p.centroid.y <= y1]
    # candidate translations: every same-area pair; the mode (rounded to 1 mm) is the frame offset
    cand = {}
    for ha, pa in arch_cols:
        for hs, ps in sc:
            if abs(pa.area - ps.area) <= 100.0:          # mm2 (1e-4 m2)
                k = (round(ps.centroid.x - pa.centroid.x), round(ps.centroid.y - pa.centroid.y))
                cand.setdefault(k, []).append((ha, hs))
    k = max(cand, key=lambda k: len(cand[k]))
    pairs = cand[k]
    dx = statistics.median(st.centroid.x - a.centroid.x for ha, a in arch_cols for hs, st in sc if (ha, hs) in pairs)
    dy = statistics.median(st.centroid.y - a.centroid.y for ha, a in arch_cols for hs, st in sc if (ha, hs) in pairs)
    A = dict(arch_cols)
    Sd = dict(sc)
    res = max(max(abs(Sd[hs].centroid.x - A[ha].centroid.x - dx), abs(Sd[hs].centroid.y - A[ha].centroid.y - dy))
              for ha, hs in pairs)
    arch_in = sum(1 for _h, p in arch_cols if x0 - dx <= p.centroid.x <= x1 - dx and y0 - dy <= p.centroid.y <= y1 - dy)
    return dx, dy, len(pairs), arch_in, res


def run(private):
    import ezdxf
    from shapely.geometry import LineString, Polygon
    private = Path(private)
    hatches, ann, units = T213.read_dxf(private / "ST7757.dxf")
    if units != 4:
        raise SystemExit(f"ST DXF units {units}, expected mm")
    panels, regions = {}, {}
    for hd, loops in hatches:
        seed = max((Polygon(lp).buffer(0) for lp in loops), key=lambda p: p.area)
        p = SP.build_panel(hd, T213.sheet_of(seed), loops, ann)
        panels[hd] = p
        regions[hd] = _with_islands(p, loops)
    if sorted(panels) != sorted(PANEL_FACE):
        raise SystemExit(f"sunken hatches {sorted(panels)} != the six of T-213")
    st_doc = ezdxf.readfile(str(private / "ST7757.dxf"))
    ar_doc = ezdxf.readfile(str(private / "P7757_DXF_COMPRESSED" / "P7757.dxf"))
    st_cols = _columns(st_doc.modelspace())
    ar_cols = _columns(ar_doc.modelspace())
    lines = _lines(ar_doc.modelspace())
    st_lines = _st_linework(st_doc.modelspace())
    out = {"frames": {}, "panels": {}, "faces": [], "walls": {}, "unclaimed": [], "on_edge": []}
    claimed = {h for grp in WALL_FACES.values() for side in grp for h in side}
    by_h = {h: (a, b) for h, a, b in lines}
    for storey, win in SHEET_MM.items():
        dx, dy, n, n_arch, res = translation(ar_cols, st_cols, win)
        out["frames"][storey] = {"columns_matched": n, "arch_columns_in_window": n_arch,
                                 "max_residual_mm": round(res, 3)}
        x0, x1, y0, y1 = win
        tl = []
        for h, a, b in lines:
            A = ((a[0] + dx) / 1000, (a[1] + dy) / 1000)
            B = ((b[0] + dx) / 1000, (b[1] + dy) / 1000)
            if x0 / 1000 <= A[0] <= x1 / 1000 and y0 / 1000 <= A[1] <= y1 / 1000:
                tl.append((h, LineString([A, B])))
        for pid, p in sorted(panels.items()):
            if p.sheet_storey != storey:
                continue
            core = regions[pid].buffer(-SHRINK_M)
            hits = []
            for h, ln in tl:
                c = ln.intersection(core).length
                full_c = ln.intersection(regions[pid]).length
                if c <= MIN_M and full_c > MIN_M:
                    out["on_edge"].append({"handle": h, "panel": pid, "face_id": PANEL_FACE[pid],
                                           "clip_full_m": round(full_c, 4),
                                           "max_inside_mm": round(1000 * max(regions[pid].exterior.distance(
                                               ln.interpolate(t, normalized=True)) for t in (0, .25, .5, .75, 1)
                                               if regions[pid].contains(ln.interpolate(t, normalized=True))) if any(
                                               regions[pid].contains(ln.interpolate(t, normalized=True))
                                               for t in (0, .25, .5, .75, 1)) else 0.0, 1)})
                if c > MIN_M:
                    hits.append({"handle": h, "panel": pid, "face_id": PANEL_FACE[pid],
                                 "clip_shrunk_m": round(c, 4),
                                 "clip_full_m": round(ln.intersection(regions[pid]).length, 4),
                                 "clip_hatch_exterior_m": round(ln.intersection(p.polygon).length, 4),
                                 "line_m": round(ln.length, 4)})
                    if h in OPENING_LINES:
                        hits[-1]["opening_line_of"] = OPENING_LINES[h]
                    elif h not in claimed:
                        out["unclaimed"].append(h)
            out["panels"][pid] = {"face_id": PANEL_FACE[pid], "sheet": storey, "area_m2": round(p.area, 4),
                                  "area_with_annotation_islands_m2": round(regions[pid].area, 4),
                                  "face_lines_inside": len(hits)}
            out["faces"].extend(hits)
        # wall midlines (only for walls on this storey)
        tld = dict(tl)
        walls = {wid: sides for wid, sides in WALL_FACES.items() if wid.startswith(storey)}
        axes = {wid: _axis([tld[h] for h in s1], [tld[h] for h in s2]) for wid, (s1, s2) in walls.items()}
        bodies = {wid: _body([tld[h] for h in s1], [tld[h] for h in s2]) for wid, (s1, s2) in walls.items()}
        cols = [pg for _h, pg in st_cols]
        cols = [Polygon([(x / 1000, y / 1000) for x, y in pg.exterior.coords]) for pg in cols]
        for wid, (s1, s2) in walls.items():
            axis = axes[wid]
            others = [b for k, b in bodies.items() if k != wid]
            own = axis
            for b in others:
                own = own.difference(b)
            under = {}
            for pid, p in panels.items():
                if p.sheet_storey != storey:
                    continue
                reg = regions[pid]
                full = axis.intersection(reg).length
                if full <= MIN_M:
                    continue
                gap = _member_gap(axis, reg, cols, st_lines)
                under[PANEL_FACE[pid]] = {
                    "axis_in_hatch_m": round(full, 4),
                    "hatch_to_column_gap_m": round(gap, 4),
                    "axis_under_panel_m": round(full + gap, 4),
                    "in_other_wall_bodies_m": round(full - own.intersection(reg).length, 4),
                    "exclusive_under_panel_m": round(own.intersection(reg).length + gap, 4),
                    "faces_in_hatch_m": [round(sum(tld[h].intersection(reg).length for h in s), 4) for s in (s1, s2)]}
            out["walls"][wid] = {"faces": [list(s1), list(s2)], "axis_span_m": round(axis.length, 4), "under": under}
    missing = sorted(h for h in claimed if h not in by_h)
    if missing:
        raise SystemExit(f"face handles not found on layer 1: {missing}")
    return out


def _with_islands(p, loops):
    """T-213 rule (a): an annotation island (a hatch loop holding a text / tag) does not end the panel. build_panel
    fills interior islands by taking the region exterior; an island that reaches the region edge is a NOTCH and is not
    inside that exterior, so the annotation islands T-213 named are united back by their loop (matched by area)."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    want = [a for a, _lab in p.annotation_islands]
    add = []
    for lp in loops:
        q = Polygon(lp).buffer(0)
        for a in list(want):
            if abs(q.area - a) <= 0.00005:
                add.append(q)
                want.remove(a)
                break
    u = unary_union([p.polygon] + add)
    return u if u.geom_type == "Polygon" else u.convex_hull.intersection(u.buffer(0.001))


def _body(side1, side2):
    """the wall body between its two faces over the axis span (flat ends)."""
    from shapely.geometry import Polygon
    a = _axis(side1, side2)
    import math
    (x0, y0), (x1, y1) = a.coords[0], a.coords[-1]
    L = a.length
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    (ax, ay) = side1[0].coords[0]
    off = abs((x0 - ax) * -uy + (y0 - ay) * ux)
    nx, ny = -uy * off, ux * off
    return Polygon([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])


def _st_linework(msp):
    """every structural LINE / LWPOLYLINE segment except the hatch, text, dimension and column-outline layers (metres)."""
    from shapely.geometry import LineString
    out = []
    skip = ("S-HAT", "S-TEXT", "DIM", "S-COL")
    for e in msp.query("LINE LWPOLYLINE"):
        lay = (e.dxf.get("layer") or "").upper()
        if any(lay.startswith(k) for k in skip):
            continue
        if e.dxftype() == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
        else:
            pts = [p[:2] for p in e.get_points()]
            if e.closed:
                pts.append(pts[0])
        if len(pts) >= 2:
            out.append((e.dxf.handle, lay, LineString([(x / 1000, y / 1000) for x, y in pts])))
    return out


def _member_gap(axis, region, cols, st_lines, gap_max=GAP_MAX_M):
    """a hatch that stops short of a column face with NOTHING drawn in between (no beam, step or slab line) does not
    leave a non-sunken strip: the panel is bounded by member faces (T-213 EDGE_BASIS; T-139 face polygon). Returns the
    axis length in such gaps: each piece of the axis outside the hatch and outside every column, at most gap_max long,
    touching the hatch at one end and a column at the other, crossed by no structural line."""
    from shapely.ops import unary_union
    rest = axis.difference(region).difference(unary_union(cols))
    parts = list(getattr(rest, "geoms", [rest])) if not rest.is_empty else []
    total = 0.0
    for g in parts:
        if g.length > gap_max or g.length <= MIN_M:
            continue
        a, b = g.boundary.geoms if hasattr(g.boundary, "geoms") else (None, None)
        if a is None:
            continue
        ends = [(region.distance(x) < 1e-6, min(c.distance(x) for c in cols) < 1e-6) for x in (a, b)]
        if not ((ends[0][0] and ends[1][1]) or (ends[1][0] and ends[0][1])):
            continue
        inner = g.interpolate(0.001).buffer(0)  # noqa: F841  (ends excluded below)
        core = g.buffer(0.0001)
        crossed = [h for h, _lay, ln in st_lines if ln.intersects(core) and
                   ln.intersection(core).distance(a) > 0.0005 and ln.intersection(core).distance(b) > 0.0005]
        if not crossed:
            total += g.length
    return total


def _axis(side1, side2):
    """the wall axis: midway between the two face lines (parallel, offset = a wall thickness to 1 mm), spanning the
    union of every face segment of both sides projected on it (an opening gap in a face does not shorten the axis)."""
    import math
    from shapely.geometry import LineString
    (ax, ay), (bx, by) = side1[0].coords[0], side1[0].coords[-1]
    L = math.hypot(bx - ax, by - ay)
    ux, uy = (bx - ax) / L, (by - ay) / L
    for ln in side1 + side2:
        (cx, cy), (ex, ey) = ln.coords[0], ln.coords[-1]
        l2 = math.hypot(ex - cx, ey - cy)
        if abs(abs(ux * (ex - cx) / l2 + uy * (ey - cy) / l2) - 1) > 1e-5:
            raise SystemExit("face lines of one wall are not parallel")
    offs = {round((c[0] - ax) * -uy + (c[1] - ay) * ux, 4) for ln in side2 for c in ln.coords}
    off1 = {round((c[0] - ax) * -uy + (c[1] - ay) * ux, 4) for ln in side1 for c in ln.coords}
    if len(offs) != 1 or len(off1) != 1 or not any(abs(abs(next(iter(offs))) - t) <= 0.001 for t in THICK):
        raise SystemExit(f"faces not two parallel lines at a wall thickness: {off1} / {offs}")
    off = next(iter(offs))
    pr = [(c[0] - ax) * ux + (c[1] - ay) * uy for ln in side1 + side2 for c in ln.coords]
    lo, hi = min(pr), max(pr)
    nx, ny = -uy * off / 2, ux * off / 2
    return LineString([(ax + ux * lo + nx, ay + uy * lo + ny), (ax + ux * hi + nx, ay + uy * hi + ny)])


if __name__ == "__main__":
    res = run(sys.argv[1])
    txt = json.dumps(res, indent=1, ensure_ascii=True, sort_keys=True)
    if "--write" in sys.argv:
        (HERE / "CLIP_T288.json").write_text(txt + "\n")
    print(txt)

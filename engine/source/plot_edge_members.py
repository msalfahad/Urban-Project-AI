"""PLOT EDGE MEMBERS V1 - the foundation members along a plot boundary as SEPARATE lines (owner Q-12 = B): the
foundation-level boundary band, the band where it runs through footings, the strap beams, the boundary ground beam at
natural-ground level, and the typical boundary-wall pads and columns. A NEW method piece on top of CONCRETE_LEDGER_V2:
it reuses concrete_strip_guard (centre line, corners once, every face in one record) and edits nothing; no released
method calls it.

Why (general on Kuwait villas, found on the development villa):
  1. a footing is not always a closed polyline on the footing layer. It may be a block INSERT whose geometry sits on the
     footing layer while the insert itself is on an annotation layer, a MIRRORED insert (negative scale), four loose
     LINEs, or an OPEN outline (opened where a strap enters). The route's member list (concrete_completeness._members,
     used by CONCRETE_LEDGER_V2) and the strip guard's probe missed some of these, so the band inside them was
     MEASURED (counted on top of the footing) and a strap ran on into the footing it ends in;
  2. the band length inside members must be explained member by member: inside a drawn footing, inside an outline that
     is open (held: the outline is not closed by the drawing), inside a column only, or free;
  3. a band volume needs a section: a candidate section that a second drawing contradicts gives a PROVISIONAL figure
     that never enters a total (owner Q-28 = A provisional); at a footing crossing only the part of the band that
     overlaps the footing in ELEVATION is already in the footing: levels from the sections, else that crossing HELD;
  4. the boundary ground beam at natural-ground level is a different member from the foundation band (owner Q-28): it
     is measured on its own drawn band with its own printed section, never reconciled with the band.

Intake (block inserts, loops):
  inserts   ezdxf Insert.virtual_entities() (mirrored and rotated inserts transform correctly; nested inserts are
            followed); an XCLIPped insert is HELD (the clipped part is unknown), skipped entity types are logged.
  loops     LINEs and open-polyline segments chained at a gap tolerance of GAP_TOL_M = 1e-6 m only (ezdxf.edgesmith
            edges). A chain that closes within it is a drawn outline. A chain that closes only across a larger gap is
            an OPEN outline: kept as a footing footprint (closed by its chord) only when the gap lies on the line of
            both end edges (the outline's own side is interrupted); it is flagged HELD with the gap length shown and
            never closed silently: the band and the strap inside it are HELD (no Urban rule gives a gap limit: owner
            Q-25 gave none).

Rules: UP-QTY-STATUS-001 (every metre in exactly one record; missing never 0), UP-KB-PREC-001 (a printed section
outranks a drawn width or a convention), owner Q-12 (separate members), Q-16 (no size borrowed), Q-19 (no usual
sizes), Q-25 (gap closures listed), Q-28 (band provisional; overlap only in elevation; 20 x 40 beam separate),
Q-31 (an outline that disagrees with its schedule row stays HELD).

    footing_outlines(entities, footing_layers, unit_m, *, region=None) -> {"members", "held", "unsupported", ...}
    merge_members(*lists, unit_m) -> one member list, identical footprints once (duplicates listed)
    band_records(band_lines, members, unit_m, strip_width_m, *, columns=()) -> band split, conservation
    band_lines(records, *, section=None, band_levels=None, member_levels=None) -> BOQ-shaped lines
    strap_records(straps, members, unit_m) -> per strap: clear length, in footing, in open outline
    ng_beam(lines, unit_m, strip_width_m, *, section=None) -> the natural-ground boundary beam
    typical_items(pads=(), columns=()) -> HELD lines for typical items with no printed count
    ledger(...) -> every line above and the totals of the lines that may enter a total

Nothing here names a project, a sheet, a layer or a handle.
"""

from __future__ import annotations

import math

from engine.source import concrete_strip_guard as SG

METHOD = "PLOT_EDGE_MEMBERS_V1"
RULES = ("UP-QTY-STATUS-001", "UP-KB-PREC-001", "OWNER-Q-12", "OWNER-Q-16", "OWNER-Q-19", "OWNER-Q-25",
         "OWNER-Q-28", "OWNER-Q-31")
GAP_TOL_M = 1e-6               # owner direction via the scout (R-05a): loops close at this gap only
COLLINEAR_SIN = SG.PARALLEL_SIN   # the gap of an open outline lies on the line of both end edges (about 2 degrees)
STRAP_WIDTH_TOL_M = 0.015      # as generic_route.STRAP_WIDTH_TOL_M: a drawn strap width binds its schedule width
MAX_INSERT_DEPTH = 4
OUTLINE_TYPES = ("LWPOLYLINE", "POLYLINE", "LINE")
MIN_PLAN_M2 = 1e-6

# band record classes (every centre-line metre of the band is in exactly one)
FREE = "BAND_FREE"
IN_FOOTING = "BAND_IN_FOOTING"
IN_OPEN = "BAND_IN_OPEN_FOOTING_OUTLINE"
IN_COLUMN = "BAND_IN_COLUMN_ONLY"


def _r(v):
    return None if v is None else round(v, 6)


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


# ====================================================================== geometry helpers
def _area(poly):
    n = len(poly)
    return sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n)) / 2.0


def _seg_cross(p1, p2, p3, p4):
    """proper intersection of two segments (shared end points do not count)."""
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = orient(p3, p4, p1), orient(p3, p4, p2)
    d3, d4 = orient(p1, p2, p3), orient(p1, p2, p4)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def _simple(poly):
    n = len(poly)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(i - j) in (1, n - 1):
                continue
            if _seg_cross(poly[i], poly[(i + 1) % n], poly[j], poly[(j + 1) % n]):
                return False
    return True


def _clean(poly, tol):
    """drop repeated vertices (a closing vertex equal to the first) and collinear middle vertices are kept."""
    out = []
    for p in poly:
        if not out or math.dist(out[-1], p) > tol:
            out.append(p)
    if len(out) > 1 and math.dist(out[0], out[-1]) <= tol:
        out.pop()
    return out


class _Nodes:
    """end points merged within a tolerance (grid hash, neighbours checked)."""

    def __init__(self, tol):
        self.tol = max(tol, 1e-12)
        self.grid, self.pts = {}, []

    def key(self, p):
        cx, cy = int(math.floor(p[0] / self.tol)), int(math.floor(p[1] / self.tol))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for k in self.grid.get((cx + dx, cy + dy), ()):
                    if math.dist(self.pts[k], p) <= self.tol:
                        return k
        k = len(self.pts)
        self.pts.append((p[0], p[1]))
        self.grid.setdefault((cx, cy), []).append(k)
        return k


# ====================================================================== intake: footing outlines from a DXF
def _layer(e, default=None):
    try:
        return e.dxf.layer
    except Exception:                       # noqa: BLE001  (an entity without a layer attribute)
        return default


def _handle(e):
    try:
        return e.dxf.handle
    except Exception:                       # noqa: BLE001
        return None


def _xclipped(ins):
    """an insert with a spatial filter (XCLIP): its visible part is unknown -> HELD, never measured."""
    try:
        if not ins.has_extension_dict:
            return False
        from ezdxf.xclip import XClip
        return bool(XClip(ins).has_clipping_path)
    except Exception:                       # noqa: BLE001  (an unreadable filter is treated as a clip: HELD)
        return True


def _poly_points(e):
    """(points, closed, has_bulge) of an LWPOLYLINE / POLYLINE in WCS x, y (a mirrored insert gives its polylines an
    extrusion of -Z: the OCS points are converted, never read as WCS)."""
    if e.dxftype() == "LWPOLYLINE":
        bulge = any(abs(float(b)) > 1e-12 for (b,) in e.get_points("b"))
        pts = [(float(v.x), float(v.y)) for v in e.vertices_in_wcs()]
        return pts, bool(e.closed), bulge
    bulge = any(abs(v.dxf.get("bulge", 0.0)) > 1e-12 for v in e.vertices)
    pts = [(float(v.x), float(v.y)) for v in e.points_in_wcs()]
    return pts, bool(e.is_closed), bulge


def _flatten(entities, footing_layers, log, depth=0, parent=None):
    """(entity, source) on a footing layer, inserts expanded with virtual_entities(); a block entity on layer 0 takes
    the insert's layer (the DXF BYBLOCK convention)."""
    out = []
    for e in entities:
        t = e.dxftype()
        if t == "INSERT":
            ins = {"handle": _handle(e) if parent is None else parent["handle"],
                   "block": e.dxf.name if parent is None else parent["block"],
                   "layer": _layer(e) if parent is None else parent["layer"]}
            try:
                sx, sy = float(e.dxf.get("xscale", 1.0)), float(e.dxf.get("yscale", 1.0))
            except (TypeError, ValueError):
                sx = sy = 1.0
            mir = (sx * sy < 0) if parent is None else (parent["mirrored"] != (sx * sy < 0))
            ins["mirrored"] = mir
            if depth >= MAX_INSERT_DEPTH:
                log["held"].append({"status": "HELD", "reason": "INSERT_NESTING_TOO_DEEP", "insert": ins["handle"],
                                    "block": ins["block"], "method": METHOD})
                continue
            if _xclipped(e):
                log["held"].append({"status": "HELD", "reason": "XCLIPPED_INSERT", "insert": ins["handle"],
                                    "block": ins["block"], "method": METHOD,
                                    "detail": "the insert carries a spatial clip: the visible part is unknown"})
                continue
            try:
                virt = list(e.virtual_entities())
            except Exception as exc:        # noqa: BLE001
                log["unsupported"].append({"status": "UNSUPPORTED", "reason": "INSERT_NOT_EXPANDED",
                                           "insert": ins["handle"], "block": ins["block"], "detail": str(exc)[:120],
                                           "method": METHOD})
                continue
            for v in virt:
                if _layer(v) in (None, "0"):
                    try:
                        v.dxf.layer = ins["layer"]
                    except Exception:       # noqa: BLE001
                        pass
            out.extend(_flatten(virt, footing_layers, log, depth + 1, ins))
            continue
        lay = _layer(e)
        if lay not in footing_layers:
            continue
        if t not in OUTLINE_TYPES:
            log["skipped"].append({"type": t, "handle": _handle(e), "layer": lay,
                                   "insert": parent["handle"] if parent else None})
            continue
        out.append((e, parent))
    return out


def footing_outlines(entities, footing_layers, unit_m, *, region=None, gap_tol_m=GAP_TOL_M):
    """the footing footprints drawn on the footing layers, whatever way they are drawn.

    entities       ezdxf entities (a modelspace or a list)
    footing_layers layer names whose geometry is footing outline (an insert on any layer counts when its geometry is
                   on one of them)
    region         optional (x0, y0, x1, y1) in drawing units: only outlines wholly inside it
    -> {"members": [{"id", "kind": "FOOTING", "poly", "source", "handles", "insert", "mirrored", "open_gap_m",
                     "plan_m2"}], "held": [...], "unsupported": [...], "skipped": [...], "chains": [...]}"""
    res = {"method": METHOD, "members": [], "held": [], "unsupported": [], "skipped": [], "chains": []}
    if not (_num(unit_m) and unit_m > 0):
        res["unsupported"].append({"status": "UNSUPPORTED", "reason": "UNIT_UNKNOWN", "method": METHOD})
        return res
    layers = set(footing_layers or ())
    tol = gap_tol_m / unit_m
    inside = (lambda pts: True) if region is None else (
        lambda pts: all(region[0] <= x <= region[2] and region[1] <= y <= region[3] for x, y in pts))
    edges = []                                       # (a, b, handle, insert info)
    for e, ins in _flatten(entities, layers, res):
        h = _handle(e) if ins is None else f"{ins['handle']}/{_handle(e)}"
        src_ins = None if ins is None else {k: ins[k] for k in ("handle", "block", "layer", "mirrored")}
        if e.dxftype() == "LINE":
            a = (float(e.dxf.start.x), float(e.dxf.start.y))
            b = (float(e.dxf.end.x), float(e.dxf.end.y))
            if inside((a, b)):
                edges.append((a, b, h, src_ins))
            continue
        try:
            pts, closed, bulge = _poly_points(e)
        except Exception as exc:              # noqa: BLE001
            res["unsupported"].append({"status": "UNSUPPORTED", "reason": "BAD_OUTLINE_DATA", "handle": h,
                                       "detail": str(exc)[:120], "method": METHOD})
            continue
        if not pts or not inside(pts):
            continue
        if bulge:
            res["held"].append({"status": "HELD", "reason": "CURVED_FOOTING_OUTLINE_NOT_SUPPORTED", "handle": h,
                                "insert": src_ins, "method": METHOD})
            continue
        pts = _clean(pts, tol)
        if closed or (len(pts) >= 3 and math.dist(pts[0], pts[-1]) <= tol):
            _add_member(res, pts, "BLOCK_INSERT" if src_ins else "CLOSED_POLYLINE", [h], src_ins, None, unit_m)
        else:
            for i in range(len(pts) - 1):
                edges.append((pts[i], pts[i + 1], h, src_ins))
    _loops_and_chains(res, edges, tol, unit_m)
    return res


def _add_member(res, pts, source, handles, ins, gap_m, unit_m):
    pts = _clean(pts, 1e-9)
    if len(pts) < 3:
        return
    a = abs(_area(pts)) * unit_m * unit_m
    if a <= MIN_PLAN_M2:
        return
    if not _simple(pts):
        res["held"].append({"status": "HELD", "reason": "SELF_INTERSECTING_OUTLINE", "handles": handles,
                            "method": METHOD})
        return
    k = len(res["members"])
    res["members"].append({"id": f"FTG{k}:{handles[0]}", "kind": "FOOTING", "poly": [tuple(p) for p in pts],
                           "source": source, "handles": list(handles), "insert": ins,
                           "mirrored": bool(ins and ins.get("mirrored")), "open_gap_m": gap_m,
                           "plan_m2": _r(a)})


def _loops_and_chains(res, edges, tol, unit_m):
    nodes = _Nodes(tol)
    E = []
    for a, b, h, ins in edges:
        ka, kb = nodes.key(a), nodes.key(b)
        if ka == kb:
            continue
        E.append((ka, kb, h, ins))
    adj = {}
    for k, (ka, kb, _, _) in enumerate(E):
        adj.setdefault(ka, []).append(k)
        adj.setdefault(kb, []).append(k)
    seen_e = set()
    for k0 in range(len(E)):
        if k0 in seen_e:
            continue
        comp, stack = set(), [k0]                     # connected edges
        while stack:
            k = stack.pop()
            if k in comp:
                continue
            comp.add(k)
            for n in E[k][:2]:
                stack.extend(j for j in adj[n] if j not in comp)
        seen_e |= comp
        cnodes = {n for k in comp for n in E[k][:2]}
        deg = {n: sum(1 for k in adj[n] if k in comp) for n in cnodes}
        handles = sorted({E[k][2] for k in comp})
        ins = next((E[k][3] for k in comp if E[k][3]), None)
        if any(d > 2 for d in deg.values()):
            res["chains"].append({"status": "HELD", "reason": "BRANCHING_LINEWORK", "handles": handles,
                                  "edges": len(comp), "method": METHOD,
                                  "detail": "lines meet three or more at a point: no single outline"})
            continue
        ends = [n for n, d in deg.items() if d == 1]
        start = ends[0] if ends else next(iter(cnodes))
        order, used, cur = [start], set(), start
        while True:
            nxt = [k for k in adj[cur] if k in comp and k not in used]
            if not nxt:
                break
            k = nxt[0]
            used.add(k)
            cur = E[k][1] if E[k][0] == cur else E[k][0]
            if cur == start:
                break
            order.append(cur)
        pts = [nodes.pts[n] for n in order]
        if not ends:                                  # closed within the gap tolerance: a drawn outline
            _add_member(res, pts, "LINE_LOOP", handles, ins, None, unit_m)
            continue
        gap = math.dist(pts[0], pts[-1]) * unit_m
        rec = {"handles": handles, "edges": len(comp), "gap_m": _r(gap), "method": METHOD}
        if len(comp) >= 3 and _collinear_gap(pts):
            n_before = len(res["members"])
            _add_member(res, pts, "OPEN_OUTLINE", handles, ins, _r(gap), unit_m)
            if len(res["members"]) > n_before:
                res["held"].append({"status": "HELD", "reason": "FOOTING_OUTLINE_OPEN", "member":
                                    res["members"][-1]["id"], "handles": handles, "gap_m": _r(gap),
                                    "method": METHOD,
                                    "detail": "the outline closes only across this gap, on the line of its own "
                                              "side; not closed: the band and straps inside it are HELD"})
                continue
        res["chains"].append(dict(rec, status="HELD", reason="OPEN_CHAIN_NOT_AN_OUTLINE"))


def _collinear_gap(pts):
    """the gap between the free ends lies on the line of both end edges (an outline side interrupted)."""
    a0, a1 = pts[1], pts[0]           # first edge, pointing at the free end
    b0, b1 = pts[-2], pts[-1]         # last edge, pointing at the free end
    g = (pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
    gl = math.hypot(*g)
    if gl == 0:
        return False
    for p, q in ((a0, a1), (b0, b1)):
        d = (q[0] - p[0], q[1] - p[1])
        dl = math.hypot(*d)
        if dl == 0 or abs(d[0] * g[1] - d[1] * g[0]) / (dl * gl) > COLLINEAR_SIN:
            return False
    # the two end edges point at each other across the gap (not away from it)
    return ((a1[0] - a0[0]) * g[0] + (a1[1] - a0[1]) * g[1]) > 0 and \
        ((b1[0] - b0[0]) * -g[0] + (b1[1] - b0[1]) * -g[1]) > 0


def merge_members(*lists, unit_m, tol_m=0.002):
    """one member list from several sources (e.g. CONCRETE_LEDGER_V2 geometry members and footing_outlines): a
    footprint with the same vertices (within tol_m, any start or direction) as an earlier one is listed as a duplicate,
    never used twice."""
    out, dups = [], []
    tol = tol_m / unit_m
    for lst in lists:
        for m in lst or ():
            poly = [tuple(p[:2]) for p in m.get("poly") or ()]
            same = next((o for o in out if len(o["poly"]) == len(poly) and
                         all(min(math.dist(p, q) for q in o["poly"]) <= tol for p in poly)), None)
            if same is not None:
                dups.append({"id": m.get("id"), "same_as": same["id"], "kind": m.get("kind")})
                if same.get("kind") != "FOOTING" and m.get("kind") == "FOOTING":
                    same.update(kind="FOOTING", source=m.get("source"), open_gap_m=m.get("open_gap_m"))
                continue
            out.append(dict(m, poly=poly))
    return out, dups


# ====================================================================== the band, member by member
def band_records(band_lines, members, unit_m, strip_width_m, *, columns=()):
    """the foundation-level band split into FREE / IN_FOOTING (per footing) / IN_OPEN_FOOTING_OUTLINE / IN_COLUMN_ONLY,
    every centre-line metre in exactly one record (concrete_strip_guard does the pairing, corners once)."""
    mem = [dict(m, kind="FOOTING") for m in members or ()]
    cols = [dict(c, kind=(c.get("kind") or "COLUMN").upper()) for c in columns or ()]
    g = SG.guard(band_lines, mem + cols, unit_m, strip_width_m)
    by_id = {str(m.get("id")): m for m in mem + cols}
    recs = []
    for s in g["strips"]:
        recs.append({"class": FREE, "strip_length_m": s["strip_length_m"], "area_m2": s["area_m2"],
                     "strip_width_m": s["strip_width_m"], "faces": s["faces"], "members": []})
    for h in g["held"]:
        if h["reason"] != "STRIP_UNDER_MEMBER":
            continue
        ms = [by_id[i] for i in h["members"] if i in by_id]
        ftg = [m for m in ms if m["kind"] == "FOOTING"]
        if any(m.get("open_gap_m") is not None for m in ftg):
            cls = IN_OPEN
        elif ftg:
            cls = IN_FOOTING
        else:
            cls = IN_COLUMN
        recs.append({"class": cls, "strip_length_m": h["strip_length_m"], "area_m2": h["area_m2"],
                     "strip_width_m": h["strip_width_m"], "faces": h["faces"],
                     "members": sorted(str(m["id"]) for m in ftg) if ftg else list(h["members"]),
                     "open_gap_m": max((m["open_gap_m"] for m in ftg if m.get("open_gap_m") is not None),
                                       default=None)})
    tot = g["totals"]
    by_cls = {}
    for r in recs:
        by_cls[r["class"]] = _r(by_cls.get(r["class"], 0.0) + r["strip_length_m"])
    acc = sum(r["strip_length_m"] for r in recs)
    return {"method": METHOD, "records": recs, "by_class_m": by_cls, "rings": g["rings"],
            "unpaired": [h for h in g["held"] if h["reason"] == "STRIP_FACE_UNPAIRED"],
            "unsupported": g["unsupported"],
            "conservation": {"centre_line_m": tot["strip_centre_line_m"], "records_m": _r(acc),
                             "difference_m": _r(tot["strip_centre_line_m"] - acc)},
            "guard_totals": tot}


def _crossings(records):
    """per footing (or member group): the band length inside it."""
    out = {}
    for r in records:
        if r["class"] == FREE:
            continue
        key = (r["class"], tuple(r["members"]))
        c = out.setdefault(key, {"class": r["class"], "members": list(r["members"]), "strip_length_m": 0.0,
                                 "area_m2": 0.0, "strip_width_m": r["strip_width_m"],
                                 "open_gap_m": r.get("open_gap_m")})
        c["strip_length_m"] += r["strip_length_m"]
        c["area_m2"] += r["area_m2"]
    return [dict(c, strip_length_m=_r(c["strip_length_m"]), area_m2=_r(c["area_m2"])) for c in out.values()]


def _check_section(section):
    if section is None:
        return None
    W, H = section.get("W_m"), section.get("H_m")
    if not (_num(W) and W > 0 and _num(H) and H > 0) or not section.get("source"):
        raise ValueError("a section is {'W_m', 'H_m', 'source', 'status': PROVEN | CANDIDATE} with its printed source")
    if section.get("status") not in ("PROVEN", "CANDIDATE"):
        raise ValueError("section status is PROVEN (printed for this member over its whole length) or CANDIDATE")
    return section


def _line(member, part, status, *, length_m=None, area_m2=None, volume_m3=None, in_total=False, reason=None,
          detail=None, **kw):
    return {"member": member, "part": part, "status": status, "reason": reason, "length_m": _r(length_m),
            "area_m2": _r(area_m2), "volume_m3": _r(volume_m3), "in_total": bool(in_total), "detail": detail,
            "method": METHOD, **kw}


def band_lines(band, *, section=None, band_levels=None, member_levels=None):
    """BOQ-shaped lines of the foundation-level band (band = band_records output).

    section       {"W_m", "H_m", "source", "status"}: PROVEN -> the free length is MEASURED and enters a total;
                  CANDIDATE (two drawings disagree, owner Q-28 A) -> PROVISIONAL, never in a total; None -> HELD.
    band_levels   {"bottom_m", "top_m"} of the band from a section; member_levels {member id: {"bottom_m", "top_m"}}
                  of the footings from the sections. At a crossing only the elevation overlap is already in the
                  footing: the band part above / below it is the band's own concrete; no levels -> that crossing HELD.
    The part inside an open footing outline and inside a column only is HELD with its length and area."""
    section = _check_section(section)
    rec = band["records"]
    free_L = sum(r["strip_length_m"] for r in rec if r["class"] == FREE)
    free_A = sum(r["area_m2"] for r in rec if r["class"] == FREE)
    lines = []
    if section is None:
        lines.append(_line("FOUNDATION_BOUNDARY_BAND", "FREE", "HELD", length_m=free_L, area_m2=free_A,
                           reason="SECTION_NOT_PRINTED",
                           detail="no schedule row or printed detail gives this band's section (area only)"))
    else:
        v = free_A * section["H_m"]
        proven = section["status"] == "PROVEN"
        lines.append(_line("FOUNDATION_BOUNDARY_BAND", "FREE", "MEASURED" if proven else "PROVISIONAL",
                           length_m=free_L, area_m2=free_A, volume_m3=v, in_total=proven,
                           reason=None if proven else "SECTION_CANDIDATE_NOT_PROVEN",
                           section=dict(section),
                           detail="drawn centre line outside every member x drawn width x section depth"))
    lv = member_levels or {}
    bl = band_levels
    for c in _crossings(rec):
        base = dict(length_m=c["strip_length_m"], area_m2=c["area_m2"], members=c["members"])
        if c["class"] == IN_OPEN:
            lines.append(_line("FOUNDATION_BOUNDARY_BAND", "IN_OPEN_FOOTING_OUTLINE", "HELD",
                               reason="FOOTING_OUTLINE_OPEN", open_gap_m=c["open_gap_m"], **base,
                               detail="the footing outline is not closed by the drawing (gap shown); the band "
                                      "inside it is neither measured nor deducted"))
            continue
        if c["class"] == IN_COLUMN:
            lines.append(_line("FOUNDATION_BOUNDARY_BAND", "IN_COLUMN_ONLY", "HELD", reason="BAND_IN_COLUMN",
                               **base, detail="the band runs inside a column outline and no footing"))
            continue
        fl = [lv.get(m) for m in c["members"]]
        if section is None or bl is None or not fl or any(x is None for x in fl):
            why = "SECTION_NOT_PRINTED" if section is None else "CROSSING_LEVELS_NOT_PRINTED"
            lines.append(_line("FOUNDATION_BOUNDARY_BAND", "IN_FOOTING", "HELD", reason=why, **base,
                               detail="band inside a footing: only the part that overlaps the footing in elevation "
                                      "is already in it; the levels of band and footing are not both printed "
                                      "(owner Q-28)"))
            continue
        b0, b1 = float(bl["bottom_m"]), float(bl["top_m"])
        f0 = max(float(x["bottom_m"]) for x in fl)
        f1 = min(float(x["top_m"]) for x in fl)
        overlap = max(0.0, min(b1, f1) - max(b0, f0))
        own = max(0.0, (b1 - b0) - overlap)
        proven = section["status"] == "PROVEN"
        lines.append(_line("FOUNDATION_BOUNDARY_BAND", "IN_FOOTING", "MEASURED" if proven else "PROVISIONAL",
                           volume_m3=c["area_m2"] * own, in_total=proven,
                           reason=None if proven else "SECTION_CANDIDATE_NOT_PROVEN",
                           elevation_overlap_m=_r(overlap), band_own_depth_m=_r(own),
                           deducted_m3=_r(c["area_m2"] * overlap), **base,
                           detail="band depth less the elevation overlap with the footing (already in the footing)"))
    return lines


# ====================================================================== strap beams
def _inside(a, b, polys):
    iv = []
    for p in polys:
        iv.extend(SG._inside_intervals(a, b, p))
    return SG._merge(iv)


def strap_records(straps, members, unit_m):
    """per strap (a pair of drawn faces and its schedule section): the centre line split into the clear length
    between footing faces (measured), the part inside a closed footing (left to the footing, length only) and the
    part inside an open footing outline (HELD). straps = [{"id", "mark", "faces": [(a, b), (a, b)] in drawing units,
    "W_m", "H_m", "row_source"}]. A drawn width more than STRAP_WIDTH_TOL_M from the schedule width is a conflict:
    HELD (owner Q-16: no size borrowed)."""
    closed = [[(x * unit_m, y * unit_m) for x, y in m["poly"]] for m in members if m.get("open_gap_m") is None]
    opened = [[(x * unit_m, y * unit_m) for x, y in m["poly"]] for m in members if m.get("open_gap_m") is not None]
    out = []
    for s in straps or ():
        (a1, b1), (a2, b2) = [((p[0][0] * unit_m, p[0][1] * unit_m), (p[1][0] * unit_m, p[1][1] * unit_m))
                              for p in s["faces"]]
        L1 = math.dist(a1, b1)
        ux, uy = (b1[0] - a1[0]) / L1, (b1[1] - a1[1]) / L1
        sa = (a2[0] - a1[0]) * ux + (a2[1] - a1[1]) * uy
        sb = (b2[0] - a1[0]) * ux + (b2[1] - a1[1]) * uy
        wa = (a2[0] - a1[0]) * -uy + (a2[1] - a1[1]) * ux
        wb = (b2[0] - a1[0]) * -uy + (b2[1] - a1[1]) * ux
        w = (abs(wa) + abs(wb)) / 2
        lo, hi = max(0.0, min(sa, sb)), min(L1, max(sa, sb))
        rec = {"id": s.get("id"), "mark": s.get("mark"), "drawn_width_m": _r(w), "method": METHOD}
        if hi - lo <= SG.MIN_STRETCH_M:
            out.append(dict(rec, status="HELD", reason="STRAP_FACES_DO_NOT_OVERLAP"))
            continue
        nx, ny = -uy * math.copysign(w / 2, wa + wb), ux * math.copysign(w / 2, wa + wb)
        c0 = (a1[0] + ux * lo + nx, a1[1] + uy * lo + ny)
        c1 = (a1[0] + ux * hi + nx, a1[1] + uy * hi + ny)
        L = hi - lo
        in_open = _inside(c0, c1, opened)
        in_closed = SG._subtract(_inside(c0, c1, closed), in_open)
        L_open, L_closed = SG._total(in_open) * L, SG._total(in_closed) * L
        clear = L - L_open - L_closed
        rec.update(face_overlap_m=_r(L), clear_length_m=_r(clear), in_footing_m=_r(L_closed),
                   in_open_outline_m=_r(L_open))
        W, H = s.get("W_m"), s.get("H_m")
        lines = []
        if not (_num(W) and _num(H) and W > 0 and H > 0):
            lines.append(_line("STRAP_BEAM", "CLEAR", "HELD", length_m=clear, reason="STRAP_SECTION_NOT_PRINTED"))
        elif abs(w - W) > STRAP_WIDTH_TOL_M:
            lines.append(_line("STRAP_BEAM", "CLEAR", "HELD", length_m=clear, reason="STRAP_WIDTH_CONFLICT",
                               detail=f"drawn {w:.3f} m vs schedule {W:.3f} m"))
        else:
            lines.append(_line("STRAP_BEAM", "CLEAR", "MEASURED", length_m=clear, area_m2=clear * W,
                               volume_m3=clear * W * H, in_total=True, section={"W_m": W, "H_m": H,
                                                                                 "source": s.get("row_source")},
                               detail="clear length between footing faces x schedule section (printed width "
                                      "outranks the drawn width, UP-KB-PREC-001)"))
        if L_open > SG.MIN_STRETCH_M:
            lines.append(_line("STRAP_BEAM", "IN_OPEN_FOOTING_OUTLINE", "HELD", length_m=L_open,
                               reason="FOOTING_OUTLINE_OPEN",
                               detail="the strap runs into a footing outline the drawing does not close"))
        if L_closed > SG.MIN_STRETCH_M:
            lines.append(_line("STRAP_BEAM", "IN_FOOTING", "LEFT_TO_FOOTING", length_m=L_closed,
                               detail="inside a footing: that concrete is the footing's (length only)"))
        for ln in lines:
            ln.update(strap=s.get("id"), mark=s.get("mark"))
        rec["lines"] = lines
        out.append(rec)
    return out


# ====================================================================== natural-ground boundary beam, typical items
def ng_beam(lines, unit_m, strip_width_m, *, section=None, members=()):
    """the boundary ground beam at natural-ground level on its own drawn band: centre line x printed section
    (MEASURED, in a total) or HELD with length and area. Never reconciled with the foundation band (owner Q-28)."""
    section = _check_section(section)
    g = SG.guard(lines, list(members or ()), unit_m, strip_width_m)
    t = g["totals"]
    L, A = t["strip_centre_line_m"], t["released_area_m2"] + t["held_under_member_area_m2"]
    common = dict(length_m=L, area_m2=A, rings=g["rings"],
                  unpaired_face_m=t["held_unpaired_face_length_m"],
                  drawn_widths_m=sorted({s["strip_width_m"] for s in g["strips"] + g["held"]
                                         if "strip_width_m" in s}))
    if section is None:
        return [_line("NG_BOUNDARY_GROUND_BEAM", "BAND", "HELD", reason="SECTION_NOT_PRINTED", **common)]
    if section["status"] != "PROVEN":
        return [_line("NG_BOUNDARY_GROUND_BEAM", "BAND", "PROVISIONAL", reason="SECTION_CANDIDATE_NOT_PROVEN",
                      volume_m3=L * section["W_m"] * section["H_m"], section=dict(section), **common)]
    return [_line("NG_BOUNDARY_GROUND_BEAM", "BAND", "MEASURED", volume_m3=L * section["W_m"] * section["H_m"],
                  in_total=True, section=dict(section), **common,
                  detail="drawn centre line x printed section (UP-KB-PREC-001)")]


def typical_items(pads=(), columns=()):
    """typical boundary-wall pads and columns: a volume only with a printed count; else HELD (count not printed)."""
    out = []
    for kind, items in (("BOUNDARY_WALL_PAD", pads), ("BOUNDARY_WALL_COLUMN", columns)):
        for it in items or ():
            n = it.get("count")
            dims = [it.get(k) for k in ("L_m", "W_m", "H_m")]
            if isinstance(n, int) and n > 0 and all(_num(d) and d > 0 for d in dims):
                v = n * dims[0] * dims[1] * dims[2]
                out.append(_line(kind, it.get("id", "TYPICAL"), "MEASURED", volume_m3=v, in_total=True,
                                 count=n, size_m=dims, source=it.get("source")))
            else:
                why = "COUNT_NOT_PRINTED" if not (isinstance(n, int) and n > 0) else "SIZE_NOT_PRINTED"
                out.append(_line(kind, it.get("id", "TYPICAL"), "HELD", reason=why, size_m=dims,
                                 source=it.get("source"),
                                 detail="a typical detail without a printed count or position is never multiplied "
                                        "by a guessed count"))
    return out


# ====================================================================== the ledger
def ledger(*, band=None, band_section=None, band_levels=None, member_levels=None, straps=(), ng=None, pads=(),
           columns=()):
    """every plot-edge line, separately; totals only of the lines that may enter a total (status MEASURED)."""
    lines = []
    if band is not None:
        lines += band_lines(band, section=band_section, band_levels=band_levels, member_levels=member_levels)
    for s in straps or ():
        lines += s.get("lines") or [_line("STRAP_BEAM", "CLEAR", s.get("status", "HELD"), reason=s.get("reason"),
                                          strap=s.get("id"), mark=s.get("mark"))]
    lines += list(ng or ())
    lines += typical_items(pads, columns)
    totals = {}
    for ln in lines:
        if ln["in_total"] and ln["volume_m3"] is not None:
            totals[ln["member"]] = _r(totals.get(ln["member"], 0.0) + ln["volume_m3"])
    return {"method": METHOD, "rules": list(RULES), "lines": lines, "totals_m3": totals,
            "held": [ln for ln in lines if ln["status"] == "HELD"],
            "provisional_not_in_total": [ln for ln in lines if ln["status"] == "PROVISIONAL"]}


def policy_record():
    return {"policy": METHOD, "rules": list(RULES), "gap_tol_m": GAP_TOL_M, "strap_width_tol_m": STRAP_WIDTH_TOL_M,
            "rule": "plot-edge foundation members as separate lines (owner Q-12); footings from closed polylines, "
                    "block inserts (mirror-safe), line loops at 1e-6 m and open outlines (held, gap shown); band "
                    "split free / in footing / in open outline / in column with every metre once; band volume "
                    "provisional on a candidate section (Q-28), crossing deduction only by elevation overlap; the "
                    "natural-ground beam on its own band with its printed section; typical items without a count "
                    "held"}

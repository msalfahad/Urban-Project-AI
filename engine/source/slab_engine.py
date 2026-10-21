"""SLAB ENGINE (M2) - slab panels, openings, thickness and uncovered cells of one plan sheet (generic, stdlib).

The sheet's beam-edge line work (straight faces and arcs on the edge layers member_detection chose by evidence),
the band pieces and the column outlines are noded into a planar arrangement by the TS01 topology engine
(engine.source.topology: exact noding, half-edge faces, nested components as holes). Every bounded face is
classified from SOURCE EVIDENCE only, never from its size or position:

    BEAM          its interior point lies inside a beam band piece (the beam owns it; never slab concrete)
    COLUMN        inside a column outline
    OPENING       holds a void / opening label (VOID, OPEN, SHAFT, DUCT, LIFT, STAIR, فتحة, منور, مصعد, درج) or is
                  crossed corner to corner by two lines (the drawn X of a void)
    PANEL         bounded by at least one beam band face (so it belongs to the slab plate) and none of the above
    DETAIL        a face whose boundary touches no band face: a detail / section drawn on the sheet, excluded
    OPEN_BOUNDARY a beam-strip face much larger than its band with a dangling edge-layer stub inside it: a panel
                  leaked into the strip through an unclosed end (a gap wider than CAD heal closes). Not counted as
                  slab or beam; its area is a COVERAGE_RISK. A PANEL with such a stub keeps its class but is flagged.

Thickness, per panel: a printed tag inside it (T=16, T 16, S=160, THK 200, سمك 16) -> PRINTED; when every tag on the
sheet prints the same value the untagged panels take it as SHEET_UNIFORM (provisional); otherwise the convention's
default with provenance CONVENTION. A panel with no thickness evidence and no default is UNRESOLVED.

Unenclosed band sides: a straight band side that borders no bounded face although another band lies beyond it is a
slab cell that failed to close (the leak reached the outside); it is reported (unenclosed_sides), never ignored.

Uncovered / uncertain cells: a PANEL with no thickness tag inside it on a sheet whose tags differ, and any face
enclosed by bands but holding neither panel evidence nor an opening label, are COVERAGE_RISK cells - reported with
their area so a missing slab (or a missing opening label) is visible, never silently counted as slab or as nothing.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from engine.source import drawing_model as DM
from engine.source import member_detection as MD
from engine.source import topology as TP

POLICY_ID = "SLAB_ENGINE_V1"
OPENING_WORDS = ("VOID", "OPEN", "OPENING", "SHAFT", "DUCT", "LIFT", "ELEVATOR", "STAIR", "SKY", "COURT",
                 "فتحة", "منور", "مصعد", "درج", "فراغ")
# outputs carry the matched keyword in English, never the source text (no free text from a client drawing)
KEYWORD_EN = {"فتحة": "OPENING", "منور": "LIGHTWELL", "مصعد": "LIFT", "درج": "STAIR", "فراغ": "VOID"}


def opening_keywords(text):
    t = DM.normalize(text).upper()
    return sorted({KEYWORD_EN.get(w, w) for w in OPENING_WORDS if w in t})
THK_RX = (re.compile(r"^(?:T|S|THK|TH|SLAB)\s*[=:]?\s*(\d{2,3}(?:\.\d+)?)\s*(CM|MM)?$", re.I),
          re.compile(r"^(?:سمك)\s*[=:]?\s*(\d{2,3})\s*(سم|مم)?$"))


def thickness_of(text, *, pair_with=None):
    t = DM.normalize(text).upper().replace(" ", "")
    for rx in THK_RX:
        m = rx.match(t)
        if m:
            v = float(m.group(1))
            unit = (m.group(2) or "").upper()
            if unit in ("MM", "مم") or v >= 80:
                return v / 1000.0
            return v / 100.0
    return None


def _thickness_tags(texts, h_default):
    """Tags 'T=16' in one text, or a lone 'T' with a number within 2 text heights."""
    out = []
    lone_t = [t for t in texts if DM.normalize(t["value"]).upper() in ("T", "T=", "S", "THK")]
    nums = [t for t in texts if re.fullmatch(r"\d{2,3}", DM.normalize(t["value"]))]
    for t in texts:
        v = thickness_of(t["value"])
        if v:
            out.append({"x": t["x"], "y": t["y"], "t_m": v, "text_id": t["id"], "form": "ONE_TEXT"})
    for t in lone_t:
        h = t.get("height") or h_default
        near = sorted((math.hypot(n["x"] - t["x"], n["y"] - t["y"]), n) for n in nums
                      if math.hypot(n["x"] - t["x"], n["y"] - t["y"]) <= 3 * h)
        if near:
            n = near[0][1]
            v = float(DM.normalize(n["value"]))
            out.append({"x": t["x"], "y": t["y"], "t_m": v / 100.0 if v < 80 else v / 1000.0,
                        "text_id": f"{t['id']}+{n['id']}", "form": "T_AND_NUMBER"})
    return out


def _x_crossed(face_poly, segs):
    """Two segments, each joining near-opposite corners of the face bbox, crossing inside it."""
    xs = [p[0] for p in face_poly]
    ys = [p[1] for p in face_poly]
    bb = (min(xs), min(ys), max(xs), max(ys))
    diag = math.hypot(bb[2] - bb[0], bb[3] - bb[1])
    if diag <= 0:
        return False
    hits = 0
    for s in segs:
        (x1, y1), (x2, y2) = s["a"], s["b"]
        if not (bb[0] - 1e-6 <= min(x1, x2) and max(x1, x2) <= bb[2] + 1e-6 and
                bb[1] - 1e-6 <= min(y1, y2) and max(y1, y2) <= bb[3] + 1e-6):
            continue
        if math.hypot(x2 - x1, y2 - y1) >= 0.8 * diag:
            hits += 1
    return hits >= 2


JUNCTION_MAX_M = 1.2           # M7: band ends this close around an undrawn support close it as one junction box


def _band_ends(b):
    """the two end sides of a straight band piece: [(midpoint, outward unit direction, (p, q))]."""
    u, n = b["u"], b["n"]
    lo, hi = b["lo_off"], b["hi_off"]
    out = []
    for t, sgn in ((b["t0"], -1.0), (b["t1"], 1.0)):
        p = (u[0] * t + n[0] * lo, u[1] * t + n[1] * lo)
        q = (u[0] * t + n[0] * hi, u[1] * t + n[1] * hi)
        out.append((((p[0] + q[0]) / 2, (p[1] + q[1]) / 2), (sgn * u[0], sgn * u[1]), (p, q)))
    return out


def junction_gaps(band_pieces, column_boxes, unit_m, *, max_gap_m=JUNCTION_MAX_M):
    """M7: undrawn supports. A straight band whose end meets neither a column outline nor another band is a free end;
    free ends of two or more bands, within max_gap_m of each other and pointing into the space between them, frame
    one junction (a column or support the plan does not draw, a beam line broken at a missing column). Its box - the
    bounding box of those end sides - closes the slab cells around it (without it every bay that touches the junction
    leaks into one face). -> [{box, bands, n_ends}] in drawing units. The junction itself is nobody's concrete here:
    it is reported, never measured."""
    probe = 0.02 / unit_m
    tol = 0.005 / unit_m
    gap = max_gap_m / unit_m
    straight = [b for b in band_pieces if b.get("kind") == "STRAIGHT" and len(b.get("polygon") or []) == 4 and
                "u" in b and "t0" in b]
    cols = [(c[0] - tol, c[1] - tol, c[2] + tol, c[3] + tol) for c in column_boxes]
    free = []
    for b in straight:
        for m, d, side in _band_ends(b):
            pt = (m[0] + d[0] * probe, m[1] + d[1] * probe)
            if any(c[0] <= pt[0] <= c[2] and c[1] <= pt[1] <= c[3] for c in cols):
                continue
            if any(o is not b and (MD.point_in_poly(pt[0], pt[1], o["polygon"]) or
                                   MD.dist_point_poly(pt[0], pt[1], o["polygon"]) <= tol) for o in band_pieces):
                continue
            free.append({"band": b.get("band_id"), "m": m, "d": d, "side": side})
    parent = list(range(len(free)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i in range(len(free)):
        for j in range(i + 1, len(free)):
            if free[i]["band"] != free[j]["band"] and math.dist(free[i]["m"], free[j]["m"]) <= gap:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(len(free)):
        groups.setdefault(find(i), []).append(free[i])
    out = []
    for g in groups.values():
        if len({e["band"] for e in g}) < 2:
            continue
        pts = [q for e in g for q in e["side"]]
        box = (min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts))
        if box[2] - box[0] <= tol or box[3] - box[1] <= tol or box[2] - box[0] > gap or box[3] - box[1] > gap:
            continue
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        inward = [e for e in g if (cx - e["m"][0]) * e["d"][0] + (cy - e["m"][1]) * e["d"][1] > tol]
        if len({e["band"] for e in inward}) < 2:
            continue
        own = {e["band"] for e in g}
        bp = MD.box_poly(box)
        if any(o.get("band_id") not in own and MD.overlap_area(bp, o["polygon"]) > 0.01 * abs(MD.poly_area(bp))
               for o in band_pieces):
            continue
        out.append({"box": tuple(round(v, 6) for v in box), "bands": sorted(own), "n_ends": len(g)})
    return sorted(out, key=lambda r: r["box"])


def panels(ents, edge_layers, band_pieces, column_boxes, unit_m, *, default_t_m=None, eps_native=None,
           region_id="SHEET", junction_boxes=(), opening_extent=False, local_origin=False):
    """junction_boxes (M7): junction_gaps() boxes - they close the cells and their own face is JUNCTION_GAP.
    local_origin (M7): the arrangement is noded at the lower-left of the edge geometry and moved back (a shoelace
    area over coordinates far from the origin loses digits: x * y ~ 1e12 leaves ~1e-4 units^2 per term).
    opening_extent (M7): an opening label claims its face only when no beam band lies inside that face; a labelled
    face that holds a band is cells merged through a gap (OPENING_SUSPECT: neither slab nor opening, reported with
    its exposure - a void label never deletes the bays around it)."""
    eps = eps_native if eps_native is not None else 0.5e-3 / unit_m
    items = []
    band_handles = set()
    for b in band_pieces:
        band_handles.update(b.get("handles", []))
    for s in ents["segments"]:
        if s["layer"] in edge_layers:
            items.append(TP.BoundaryItem(s["id"], "SEGMENT", (s["a"][0], s["a"][1], s["b"][0], s["b"][1]), "EDGE"))
    for a in ents["arcs"]:
        if a["layer"] not in edge_layers:
            continue
        cx, cy = a["c"]
        a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
        a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
        if a["dir"] == "CW":
            a0, a1 = a1, a0
        if a1 <= a0:
            a1 += 2 * math.pi
        items.append(TP.BoundaryItem(a["id"], "ARC", (cx, cy, a["r"], a0, a1), "EDGE"))
    for k, c in enumerate(column_boxes):
        p = MD.box_poly(c)
        for j in range(4):
            (x1, y1), (x2, y2) = p[j], p[(j + 1) % 4]
            items.append(TP.BoundaryItem(f"COLBOX{k}:{j}", "SEGMENT", (x1, y1, x2, y2), "COLUMN"))
    jboxes = [tuple(j["box"]) if isinstance(j, dict) else tuple(j) for j in junction_boxes]
    for k, c in enumerate(jboxes):
        p = MD.box_poly(c)
        for j in range(4):
            (x1, y1), (x2, y2) = p[j], p[(j + 1) % 4]
            items.append(TP.BoundaryItem(f"COLBOX_JUNC{k}:{j}", "SEGMENT", (x1, y1, x2, y2), "COLUMN"))
    if not items:
        return {"policy": POLICY_ID, "faces": [], "summary": {}, "warnings": ["no edge geometry"]}
    # M7 (local_origin): site ids are source ids, so moving the arrangement moves no id
    ox = oy = 0.0
    if local_origin:
        ox = min(g[0] - g[2] if it.kind == "ARC" else min(g[0], g[2]) for it in items for g in [it.geometry])
        oy = min(g[1] - g[2] if it.kind == "ARC" else min(g[1], g[3]) for it in items for g in [it.geometry])
    local = items if not local_origin else [
        TP.BoundaryItem(it.source_id, it.kind,
                        (it.geometry[0] - ox, it.geometry[1] - oy) + tuple(it.geometry[2:]) if it.kind == "ARC"
                        else (it.geometry[0] - ox, it.geometry[1] - oy, it.geometry[2] - ox, it.geometry[3] - oy),
                        it.role, it.derived_from) for it in items]
    arr = TP.build(local, eps)
    sites = TP.sites_of(arr, "M2", region_id)
    pts = [TP.interior_point(arr, st["cycle"], eps) for st in sites]
    if local_origin:
        pts = [None if q is None else (q[0] + ox, q[1] + oy) for q in pts]
        arr.nodes = [(x + ox, y + oy) for x, y in arr.nodes]
    texts = ents["texts"]
    h_default = 150e-3 / unit_m
    tags = _thickness_tags(texts, h_default)
    opening_txt = [t for t in texts if any(w in DM.normalize(t["value"]).upper() for w in OPENING_WORDS)]
    other_segs = [s for s in ents["segments"] if s["layer"] not in edge_layers]
    faces = []
    for st, pt in zip(sites, pts):
        if pt is None:
            continue
        poly = [arr.nodes[arr.edges[ei]["n0"]] if fw else arr.nodes[arr.edges[ei]["n1"]] for ei, fw in st["cycle"]]
        cls = None
        if any(MD.point_in_poly(pt[0], pt[1], b["polygon"]) for b in band_pieces):
            cls = "BEAM"
        elif any(c[0] < pt[0] < c[2] and c[1] < pt[1] < c[3] for c in column_boxes):
            cls = "COLUMN"
        elif any(c[0] < pt[0] < c[2] and c[1] < pt[1] < c[3] for c in jboxes):
            cls = "JUNCTION_GAP"
        src = set(st["boundary_source_ids"])
        touches_band = bool(src & band_handles)
        inside_txt = [t for t in opening_txt if MD.point_in_poly(t["x"], t["y"], poly)]
        if cls is None:
            if inside_txt or _x_crossed(poly, other_segs):
                cls = "OPENING"
                if opening_extent and _holds_band(poly, st, arr, band_pieces):
                    cls = "OPENING_SUSPECT"
            elif touches_band:
                cls = "PANEL"
            else:
                cls = "DETAIL"
        stub_edge = [x for x in st.get("interior_stub_source_ids", []) if not str(x).startswith("COLBOX")]
        open_b = bool(stub_edge) and st.get("interior_stub_length", 0.0) > 4 * eps
        if open_b and cls == "BEAM":
            host = [b for b in band_pieces if MD.point_in_poly(pt[0], pt[1], b["polygon"])]
            if host and st["area"] > 1.5 * abs(MD.poly_area(host[0]["polygon"])):
                cls = "OPEN_BOUNDARY"              # a panel leaked into the beam strip through an unclosed end
        tg = [t for t in tags if MD.point_in_poly(t["x"], t["y"], poly)] if cls == "PANEL" else []
        # M4: the hole rings and the number of arc edges travel with the face (an independent area check needs them;
        # the polygon is the node ring, a chord of every arc edge)
        hole_polys = [[arr.nodes[arr.edges[ei]["n0"]] if fw else arr.nodes[arr.edges[ei]["n1"]] for ei, fw in hc]
                      for hc in st.get("hole_cycles", [])]
        n_arc = sum(1 for c in [st["cycle"]] + list(st.get("hole_cycles", [])) for ei, _ in c
                    if arr.edges[ei]["kind"] == "A")
        faces.append({"face_id": st["site_id"], "class": cls, "area_m2": st["area"] * unit_m ** 2,
                      "hole_polygons": hole_polys, "arc_edges": n_arc,
                      "perimeter_m": st["perimeter"] * unit_m, "point": pt, "polygon": poly,
                      "thickness_tags": sorted({t["t_m"] for t in tg}), "tag_ids": [t["text_id"] for t in tg],
                      "opening_labels": sorted({k for t in inside_txt for k in opening_keywords(t["value"])}),
                      "holes": st["holes"], "touches_band": touches_band, "open_boundary": open_b,
                      "stub_source_ids": stub_edge[:6]})
    sheet_vals = sorted({t["t_m"] for t in tags if any(f["class"] == "PANEL" and
                                                       MD.point_in_poly(t["x"], t["y"], f["polygon"]) for f in faces)})
    uniform = sheet_vals[0] if len(sheet_vals) == 1 else None
    for f in faces:
        if f["class"] != "PANEL":
            continue
        if len(f["thickness_tags"]) == 1:
            f["t_m"], f["t_basis"] = f["thickness_tags"][0], "PRINTED_IN_PANEL"
        elif len(f["thickness_tags"]) > 1:
            f["t_m"], f["t_basis"] = None, "CONFLICTING_TAGS"
        elif uniform is not None:
            f["t_m"], f["t_basis"] = uniform, "SHEET_UNIFORM"
        elif default_t_m is not None:
            f["t_m"], f["t_basis"] = default_t_m, "CONVENTION_DEFAULT"
        else:
            f["t_m"], f["t_basis"] = None, "NO_THICKNESS"
        f["volume_m3"] = f["area_m2"] * f["t_m"] if f["t_m"] else None
        f["coverage_risk"] = f["t_basis"] in ("CONVENTION_DEFAULT", "NO_THICKNESS", "CONFLICTING_TAGS") or \
            f["open_boundary"]
    unenclosed = _unenclosed_sides(faces, band_pieces, unit_m, column_boxes)
    summ = Counter(f["class"] for f in faces)
    area = {c: sum(f["area_m2"] for f in faces if f["class"] == c) for c in summ}
    return {"policy": POLICY_ID, "faces": faces, "counts": dict(summ), "area_m2": area,
            "sheet_thickness_values": sheet_vals, "uniform_t_m": uniform,
            "panel_volume_m3": sum(f.get("volume_m3") or 0 for f in faces if f["class"] == "PANEL"),
            "risk_area_m2": sum(f["area_m2"] for f in faces if (f["class"] == "PANEL" and f.get("coverage_risk"))
                                or f["class"] == "OPEN_BOUNDARY"),
            "open_boundary_area_m2": sum(f["area_m2"] for f in faces if f["class"] == "OPEN_BOUNDARY"),
            "unenclosed_sides": unenclosed,
            "arrangement": {"nodes": len(arr.nodes), "edges": len(arr.edges), "sites": len(sites)}}


def _holds_band(poly, st, arr, band_pieces):
    """a band piece whose centre lies in the face (outside its holes): cells merged through a gap, not one void."""
    holes = [[arr.nodes[arr.edges[ei]["n0"]] if fw else arr.nodes[arr.edges[ei]["n1"]] for ei, fw in hc]
             for hc in st.get("hole_cycles", [])]
    for b in band_pieces:
        q = b.get("polygon") or []
        if len(q) < 3:
            continue
        cx, cy = sum(x for x, _ in q) / len(q), sum(y for _, y in q) / len(q)
        if MD.point_in_poly(cx, cy, poly) and not any(len(h) >= 3 and MD.point_in_poly(cx, cy, h) for h in holes):
            return True
    return False


def _ray_hits_poly(p, d, poly, max_s):
    best = None
    for k in range(len(poly)):
        (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % len(poly)]
        ex, ey = x2 - x1, y2 - y1
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        wx, wy = x1 - p[0], y1 - p[1]
        s_ = (wx * ey - wy * ex) / den
        t = (wx * d[1] - wy * d[0]) / den
        if 0 < s_ <= max_s and -1e-9 <= t <= 1 + 1e-9 and (best is None or s_ < best):
            best = s_
    return best


def _unenclosed_sides(faces, band_pieces, unit_m, column_boxes=()):
    """A straight band's long side that borders NO bounded face although the band network continues beyond it (a
    ray from the side meets another band): a slab cell there failed to close - most often a face end that stops short
    of its support by more than CAD heal bridges - and its area is silently missing unless reported. One record per
    such side; the area is not estimated (the cell boundary is exactly what is unknown)."""
    if not band_pieces:
        return []
    d0 = 0.01 / unit_m
    xs = [x for b in band_pieces for x, _ in b["polygon"]]
    ys = [y for b in band_pieces for _, y in b["polygon"]]
    span = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    boxes = []
    for f in faces:
        px = [x for x, _ in f["polygon"]]
        py = [y for _, y in f["polygon"]]
        boxes.append((min(px), min(py), max(px), max(py), f))
    out = []
    for b in band_pieces:
        if b.get("kind") != "STRAIGHT" or len(b["polygon"]) != 4:
            continue
        poly = b["polygon"]
        cx = sum(x for x, _ in poly) / 4
        cy = sum(y for _, y in poly) / 4
        sides = sorted(((math.dist(poly[k], poly[(k + 1) % 4]), k) for k in range(4)), reverse=True)[:2]
        for _, k in sides:
            (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % 4]
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            L = math.hypot(x2 - x1, y2 - y1)
            nx, ny = -(y2 - y1) / L, (x2 - x1) / L
            if nx * (mx - cx) + ny * (my - cy) < 0:
                nx, ny = -nx, -ny
            p = (mx + nx * d0, my + ny * d0)
            if any(bx0 <= p[0] <= bx1 and by0 <= p[1] <= by1 and MD.point_in_poly(p[0], p[1], f["polygon"])
                   for bx0, by0, bx1, by1, f in boxes):
                continue
            hit = [h for o in band_pieces if o is not b for h in [_ray_hits_poly(p, (nx, ny), o["polygon"], span)]
                   if h is not None]
            if not hit:
                continue
            # the region between this side and the facing band must be boxed in: from its middle, rays along the
            # band direction meet a member both ways (a bay), not open space (an exterior side facing a far member)
            q = (p[0] + nx * min(hit) / 2, p[1] + ny * min(hit) / 2)
            obst = [o["polygon"] for o in band_pieces] + [MD.box_poly(c) for c in column_boxes]
            lat = [any(_ray_hits_poly(q, (sx * (x2 - x1) / L, sx * (y2 - y1) / L), o, span) for o in obst)
                   for sx in (1, -1)]
            if all(lat):
                out.append({"band_id": b.get("band_id"), "side_mid": (mx, my), "facing_band_at_m": min(hit) * unit_m})
    return out


def band_sides(faces, band_pieces, unit_m, column_boxes=()):
    """band_id -> its two long sides, each classified from the planar arrangement (M3, generic):
        FACE:<class>   the side borders a bounded face (PANEL, OPENING, ...)
        ENCLOSED_GAP   no bounded face, but members lie beyond it on every probe (an unclosed slab cell)
        OUTSIDE        no bounded face and no band or column beyond it: the outside of the member network
    A band with an OUTSIDE side is a perimeter (exterior) member of the plan. Arcs are probed radially at mid-angle
    when the piece carries its centre and radii, otherwise their sides are UNKNOWN."""
    out = {}
    if not band_pieces:
        return out
    d0 = 0.01 / unit_m
    xs = [x for b in band_pieces for x, _ in b["polygon"]]
    ys = [y for b in band_pieces for _, y in b["polygon"]]
    span = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    boxes = []
    for f in faces:
        px = [x for x, _ in f["polygon"]]
        py = [y for _, y in f["polygon"]]
        boxes.append((min(px), min(py), max(px), max(py), f))
    obst = [(o.get("band_id"), o["polygon"]) for o in band_pieces] + [(None, MD.box_poly(c)) for c in column_boxes]

    def classify(p, nrm, own):
        for bx0, by0, bx1, by1, f in boxes:
            if bx0 <= p[0] <= bx1 and by0 <= p[1] <= by1 and MD.point_in_poly(p[0], p[1], f["polygon"]):
                return "FACE:" + str(f["class"])
        hit = [h for bid, q in obst if bid != own for h in [_ray_hits_poly(p, nrm, q, span)] if h is not None]
        if not hit:
            return "OUTSIDE"
        # members beyond the side: a bay only when it is boxed in both ways along the side (as _unenclosed_sides);
        # a gap between two separate building parts opens to the outside
        q = (p[0] + nrm[0] * min(hit) / 2, p[1] + nrm[1] * min(hit) / 2)
        lat = [any(_ray_hits_poly(q, (sx * -nrm[1], sx * nrm[0]), o, span) is not None for _, o in obst)
               for sx in (1, -1)]
        return "ENCLOSED_GAP" if all(lat) else "OUTSIDE"
    for b in band_pieces:
        own = b.get("band_id")
        if b.get("kind") == "STRAIGHT" and len(b["polygon"]) == 4:
            poly = b["polygon"]
            cx = sum(x for x, _ in poly) / 4
            cy = sum(y for _, y in poly) / 4
            sides = sorted(((math.dist(poly[k], poly[(k + 1) % 4]), k) for k in range(4)), reverse=True)[:2]
            res = []
            for _, k in sides:
                (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % 4]
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                L = math.hypot(x2 - x1, y2 - y1)
                nx, ny = -(y2 - y1) / L, (x2 - x1) / L
                if nx * (mx - cx) + ny * (my - cy) < 0:
                    nx, ny = -nx, -ny
                res.append(classify((mx + nx * d0, my + ny * d0), (nx, ny), own))
            out[own] = res
        elif b.get("kind") == "ARC" and b.get("centre") and b.get("r_outer") and b.get("start_rad") is not None:
            c, a = b["centre"], b["start_rad"] + b.get("overlap_rad", 0.0) / 2.0
            ux, uy = math.cos(a), math.sin(a)
            po = (c[0] + ux * (b["r_outer"] + d0), c[1] + uy * (b["r_outer"] + d0))
            pi = (c[0] + ux * (b["r_inner"] - d0), c[1] + uy * (b["r_inner"] - d0))
            out[own] = [classify(po, (ux, uy), own), classify(pi, (-ux, -uy), own)]
        else:
            out[own] = ["UNKNOWN", "UNKNOWN"]
    return out


STAIR_MIN_TREADS = 5           # a flight or a winder fan of at least five tread lines
STAIR_ZONE_SHARE = 0.25        # treads over a quarter of a cell: the cell is a stair zone, its slab not separable
REGIONS = ("STRUCTURAL_SLAB", "GROUND_SLAB", "STAIR_ZONE", "OPENING", "BEAM_STRIP", "COLUMN", "DETAIL",
           "UNRESOLVED", "JUNCTION_GAP", "OPENING_SUSPECT")


def _hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], q) <= 0:
            up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]


def tread_family(face_poly, segs, unit_m, min_n=STAIR_MIN_TREADS, *, per_layer=False, angle_wrap=False):
    """Stair treads drawn inside a face (non-edge, non-annotation lines 0.4 - 2.5 m wholly inside it):
        FLIGHT   at least min_n parallel lines, consecutive spacing 0.18 - 0.40 m (a going)
        WINDER   at least min_n lines whose extensions meet near one point (within 0.2 m), fanning over 30 degrees
    -> {kind, n, hull_m2, segment_ids} or None. Geometry only; a stair label is never required.
    per_layer (M7): the family is searched among one layer's lines at a time (a flight is drawn on one layer; lines of
    an unrelated layer between two treads must not break the going), the largest family found wins.
    angle_wrap (M8): directions are binned modulo 180 degrees, so a line at 179.99 degrees (a horizontal tread drawn
    the other way, or rotated by 180 degrees with floating noise) joins the lines at 0 degrees."""
    inside = []
    for sg in segs:
        L = math.dist(sg["a"], sg["b"]) * unit_m
        if not (0.4 <= L <= 2.5):
            continue
        if all(MD.point_in_poly(x, y, face_poly) for x, y in (sg["a"], sg["b"],
                                                               ((sg["a"][0] + sg["b"][0]) / 2,
                                                                (sg["a"][1] + sg["b"][1]) / 2))):
            inside.append(sg)
    if per_layer:
        best = None
        for lay in sorted({sg["layer"] for sg in inside}):
            r = _tread_family_of([sg for sg in inside if sg["layer"] == lay], unit_m, min_n, wrap=angle_wrap)
            if r is not None and (best is None or r["n"] > best["n"]):
                best = r
        return best
    return _tread_family_of(inside, unit_m, min_n, wrap=angle_wrap)


def _tread_family_of(inside, unit_m, min_n, wrap=False):
    found = None
    groups = {}
    for sg in inside:
        ang = math.degrees(math.atan2(sg["b"][1] - sg["a"][1], sg["b"][0] - sg["a"][0])) % 180.0
        groups.setdefault(round(ang / 3.0) % 60 if wrap else round(ang / 3.0), []).append(sg)
    for g in groups.values():
        if len(g) < min_n:
            continue
        dx, dy = g[0]["b"][0] - g[0]["a"][0], g[0]["b"][1] - g[0]["a"][1]
        n = math.hypot(dx, dy)
        offs = sorted((sg["a"][0] * -dy / n + sg["a"][1] * dx / n) * unit_m for sg in g)
        run = best = 0
        for a, b in zip(offs, offs[1:]):
            run = run + 1 if 0.18 <= b - a <= 0.40 else 0
            best = max(best, run)
        if best + 1 >= min_n:
            found = ("FLIGHT", g)
            break
    if found is None and len(inside) >= min_n:
        a00 = a01 = a11 = b0 = b1 = 0.0
        for sg in inside:
            dx, dy = sg["b"][0] - sg["a"][0], sg["b"][1] - sg["a"][1]
            n = math.hypot(dx, dy)
            nx, ny = -dy / n, dx / n
            c = nx * sg["a"][0] + ny * sg["a"][1]
            a00, a01, a11, b0, b1 = a00 + nx * nx, a01 + nx * ny, a11 + ny * ny, b0 + nx * c, b1 + ny * c
        det = a00 * a11 - a01 * a01
        if abs(det) > 1e-12:
            px, py = (b0 * a11 - a01 * b1) / det, (a00 * b1 - a01 * b0) / det
            near = []
            for sg in inside:
                dx, dy = sg["b"][0] - sg["a"][0], sg["b"][1] - sg["a"][1]
                if abs((px - sg["a"][0]) * dy - (py - sg["a"][1]) * dx) / math.hypot(dx, dy) * unit_m <= 0.2:
                    near.append(sg)
            angs = sorted(math.degrees(math.atan2((sg["a"][1] + sg["b"][1]) / 2 - py,
                                                  (sg["a"][0] + sg["b"][0]) / 2 - px)) for sg in near)
            if len(near) >= min_n and angs[-1] - angs[0] >= 30.0:
                found = ("WINDER", near)
    if found is None:
        return None
    kind, g = found
    hull = _hull([q for sg in g for q in (sg["a"], sg["b"])])
    return {"kind": kind, "n": len(g), "hull_m2": MD.poly_area(hull) * unit_m ** 2 if len(hull) >= 3 else 0.0,
            "segment_ids": [sg["id"] for sg in g][:40],
            "lines": [(tuple(sg["a"]), tuple(sg["b"])) for sg in g]}          # M4: the tread geometry itself


def open_boundary_panel(face, band_pieces, column_boxes, unit_m):
    """the panel part of an OPEN_BOUNDARY face (a panel leaked into a beam strip): face area minus its overlap with
    the (convex) band pieces and column outlines, junction squares counted once (pairwise overlaps added back)."""
    F = face["polygon"]
    clips = [b["polygon"] for b in band_pieces if b.get("kind") == "STRAIGHT"] + \
        [MD.box_poly(c) for c in column_boxes]
    parts = []
    for q in clips:
        c = MD.clip_convex(F, q)
        if len(c) >= 3 and MD.poly_area(c) > 0:
            parts.append((c, q))
    cut = sum(MD.poly_area(c) for c, _ in parts)
    for i, (ci, qi) in enumerate(parts):
        for cj, qj in parts[i + 1:]:
            cc = MD.clip_convex(ci, qj)
            if len(cc) >= 3:
                cut -= MD.poly_area(cc)
    return max(abs(MD.poly_area(F)) - cut, 0.0) * unit_m ** 2


def classify_regions(slab, ents, edge_layers, band_pieces, column_boxes, unit_m, *, ground=False,
                     treads_per_layer=False, touch_counts=False, tread_angle_wrap=False):
    """M3: every face of a plan gets a region class, from the face class plus two generic checks:
        free-standing columns   a column outline inside a PANEL that touches no beam band. On a ground-beam plan a
                                column stands on a beam junction or its own footing, so the cell is UNRESOLVED (not
                                counted: a missing beam, another level or another element); on a suspended slab it is
                                a flat-slab zone, counted, with a coverage risk.
        stair treads            a tread family (tread_family) covering at least STAIR_ZONE_SHARE of a PANEL makes it
                                a STAIR_ZONE (not counted as slab); a smaller family is a coverage risk.
    PANEL -> STRUCTURAL_SLAB / GROUND_SLAB, BEAM and OPEN_BOUNDARY -> BEAM_STRIP (an open-boundary face is a leak,
    never slab), OPENING, COLUMN, DETAIL. Faces keep their area; nothing is deleted."""
    if not slab:
        return slab
    segs = [sg for sg in ents["segments"] if sg["layer"] not in edge_layers and
            MD._layer_role(sg["layer"]) not in MD.ANNOTATION_ROLES + ("COLUMN", "FOOTING")]
    for f in slab["faces"]:
        f["free_columns"], f["treads"] = [], None
        if f["class"] == "PANEL":
            for c in column_boxes:
                cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
                if MD.point_in_poly(cx, cy, f["polygon"]):       # the outer cycle: a column hole lies inside it
                    # M7 (touch_counts): a column flush with a band face stands on that beam - the box grown by
                    # 1 mm decides, not an exact-zero overlap that floating noise turns either way
                    e = 1e-3 / unit_m if touch_counts else 0.0
                    cb = MD.box_poly((c[0] - e, c[1] - e, c[2] + e, c[3] + e))
                    # an arc band's ring is not convex (the convex clip reads 0): its centre test decides
                    on_arc = touch_counts and any(b.get("kind") != "STRAIGHT" and MD.point_in_poly(cx, cy, b["polygon"])
                                                  for b in band_pieces)
                    if not on_arc and not any(MD.overlap_area(cb, b["polygon"]) > 0.25 * e * e for b in band_pieces):
                        f["free_columns"].append(tuple(round(v, 1) for v in c))
            f["treads"] = tread_family(f["polygon"], segs, unit_m, per_layer=treads_per_layer,
                                       angle_wrap=tread_angle_wrap)
        cls = f["class"]
        share = (f["treads"]["hull_m2"] / f["area_m2"]) if f["treads"] and f["area_m2"] else 0.0
        if cls == "PANEL" and share >= STAIR_ZONE_SHARE:
            f["region"], f["region_reason"] = "STAIR_ZONE", f"{f['treads']['kind']} of {f['treads']['n']} treads " \
                                                            f"over {share:.0%} of the cell"
        elif cls == "PANEL" and f["free_columns"] and ground:
            f["region"], f["region_reason"] = "UNRESOLVED", f"{len(f['free_columns'])} free-standing column(s) " \
                                                            "inside a ground-slab cell"
        elif cls == "PANEL":
            f["region"] = "GROUND_SLAB" if ground else "STRUCTURAL_SLAB"
            f["region_reason"] = "beam-face bounded cell"
        elif cls == "OPEN_BOUNDARY":
            net = open_boundary_panel(f, band_pieces, column_boxes, unit_m)
            f["recovered_panel_m2"] = net
            if net > 0.5:
                tg = sorted({t["t_m"] for t in _thickness_tags(ents["texts"], 150e-3 / unit_m)
                             if MD.point_in_poly(t["x"], t["y"], f["polygon"])})
                if len(tg) == 1:
                    f["t_m"], f["t_basis"] = tg[0], "PRINTED_IN_PANEL"
                elif not tg and slab.get("uniform_t_m"):
                    f["t_m"], f["t_basis"] = slab["uniform_t_m"], "SHEET_UNIFORM"
                else:
                    f["t_m"], f["t_basis"] = None, "CONFLICTING_TAGS" if tg else "NO_THICKNESS"
                f["region"] = "GROUND_SLAB" if ground else "STRUCTURAL_SLAB"
                f["region_reason"] = (f"open-boundary face {f['area_m2']:.2f} m2: the panel is the face minus its beam "
                                      f"bands and columns ({net:.2f} m2)")
            else:
                f["region"], f["region_reason"] = "BEAM_STRIP", "leaked beam strip (no panel left after the bands)"
        elif cls == "BEAM":
            f["region"], f["region_reason"] = "BEAM_STRIP", "inside a beam band"
        else:
            f["region"], f["region_reason"] = cls, cls.lower()
    slab["regions_m2"] = {r: sum(f["area_m2"] for f in slab["faces"] if f.get("region") == r) for r in REGIONS}
    return slab


def policy_record():
    return {"policy": POLICY_ID, "classes": ["BEAM", "COLUMN", "OPENING", "PANEL", "DETAIL", "OPEN_BOUNDARY"],
            "rule": "a face is slab only with band adjacency and no opening evidence; thickness printed > sheet "
                    "uniform > convention default; a cell with weak evidence is a coverage risk, never hidden"}

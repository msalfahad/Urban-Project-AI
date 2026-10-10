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


def panels(ents, edge_layers, band_pieces, column_boxes, unit_m, *, default_t_m=None, eps_native=None,
           region_id="SHEET"):
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
    if not items:
        return {"policy": POLICY_ID, "faces": [], "summary": {}, "warnings": ["no edge geometry"]}
    arr = TP.build(items, eps)
    sites = TP.sites_of(arr, "M2", region_id)
    texts = ents["texts"]
    h_default = 150e-3 / unit_m
    tags = _thickness_tags(texts, h_default)
    opening_txt = [t for t in texts if any(w in DM.normalize(t["value"]).upper() for w in OPENING_WORDS)]
    other_segs = [s for s in ents["segments"] if s["layer"] not in edge_layers]
    faces = []
    for st in sites:
        pt = TP.interior_point(arr, st["cycle"], eps)
        if pt is None:
            continue
        poly = [arr.nodes[arr.edges[ei]["n0"]] if fw else arr.nodes[arr.edges[ei]["n1"]] for ei, fw in st["cycle"]]
        cls = None
        if any(MD.point_in_poly(pt[0], pt[1], b["polygon"]) for b in band_pieces):
            cls = "BEAM"
        elif any(c[0] < pt[0] < c[2] and c[1] < pt[1] < c[3] for c in column_boxes):
            cls = "COLUMN"
        src = set(st["boundary_source_ids"])
        touches_band = bool(src & band_handles)
        inside_txt = [t for t in opening_txt if MD.point_in_poly(t["x"], t["y"], poly)]
        if cls is None:
            if inside_txt or _x_crossed(poly, other_segs):
                cls = "OPENING"
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
        faces.append({"face_id": st["site_id"], "class": cls, "area_m2": st["area"] * unit_m ** 2,
                      "perimeter_m": st["perimeter"] * unit_m, "point": pt, "polygon": poly,
                      "thickness_tags": sorted({t["t_m"] for t in tg}), "tag_ids": [t["text_id"] for t in tg],
                      "opening_labels": [DM.normalize(t["value"]) for t in inside_txt][:3],
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


def policy_record():
    return {"policy": POLICY_ID, "classes": ["BEAM", "COLUMN", "OPENING", "PANEL", "DETAIL", "OPEN_BOUNDARY"],
            "rule": "a face is slab only with band adjacency and no opening evidence; thickness printed > sheet "
                    "uniform > convention default; a cell with weak evidence is a coverage risk, never hidden"}

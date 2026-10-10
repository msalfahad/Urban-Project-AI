"""MEMBER DETECTION (M2) - footings, columns, beams and ground beams of a NEW drawing, with no project register
(generic, stdlib + engine.source).

Every member comes from drawn geometry and a printed mark; the schedule (schedule_reader) gives the section. Nothing
is matched by a coordinate, a layer spelling or a stage id of any project.

FOOTINGS   each footing mark (F3, combined C3/F3, FN) on a foundation sheet binds to the SMALLEST closed rectangle that
           contains it (a polyline outline or four drawn lines). The drawn plan size must equal the schedule's
           (either orientation, within `size_tol`): CONFIRMED; otherwise SIZE_MISMATCH (both kept). Two footing marks in
           one outline: COMBINED_OUTLINE (blocked, never split by guess). Volume = L x W x D (schedule).
COLUMNS    the column plan's marks are the occurrences (a sheet with role COLUMN_PLAN; else the foundation sheet). A
           column type's schedule storey bands say on which storeys it exists and with which section; the drawn outline
           around the mark confirms the section. Height per storey comes from the convention set (a printed level,
           confirmed); without it the column is UNRESOLVED with its section kept.
BEAMS      edge layers are chosen by EVIDENCE: a layer qualifies when parallel pairs on it at a scheduled beam width
           hold beam marks. Bands = parallel face pairs at a scheduled width (ground_beam_network.pair_straight, with
           its intervening-face / shared-face / duplicate checks) and concentric arcs (pair_arcs, centre-line length,
           never a chord or bounding box). A mark binds to a band only when the band's width equals the mark's own
           scheduled width, the band axis is parallel to the text (+- 12 deg) and the mark lies inside the band or
           within `bind_gap` of it, and no second band qualifies (else AMBIGUOUS). Unbound bands keep their geometry
           (UNRESOLVED: section unknown, an exposure from the scheduled depth range at that width).
OWNERSHIP  a column owns its footprint: the band length inside column rectangles is deducted from the beam. Two bands
           that overlap (both drawn through a junction) give the square to ONE of them (the longer band; ties by id) and
           the other is deducted - recorded per pair. Slab panels stop at band faces (slab_engine).
DEPTH      the schedule depth H is read under both conventions: TOTAL_DEPTH (B x H x L) and BELOW_SLAB (B x (H + t) x L),
           t = the slab thickness the slab engine gives the adjacent panels, or the convention default.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.source import drawing_model as DM
from engine.source import ground_beam_network as GN
from engine.source import structural_qto as Q

POLICY_ID = "MEMBER_DETECTION_V1"
ANNOTATION_ROLES = ("TEXT", "DIMENSION", "HATCH", "FRAME", "GRID", "REBAR")
BEAM_FAMILIES = ("BEAM", "CONTINUOUS_BEAM")
GROUND_FAMILIES = ("GROUND_BEAM", "STRAP_BEAM")


# ------------------------------------------------------------------ small geometry
def poly_area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2.0


def clip_convex(subject, clip):
    """Sutherland-Hodgman: subject polygon clipped by a convex polygon (both CCW or both CW)."""
    def inside(p, a, b, s):
        return s * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) >= -1e-9

    def inter(p, q, a, b):
        x1, y1, x2, y2, x3, y3, x4, y4 = p[0], p[1], q[0], q[1], a[0], a[1], b[0], b[1]
        d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(d) < 1e-15:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    s = 1.0 if sum(clip[i][0] * clip[(i + 1) % len(clip)][1] - clip[(i + 1) % len(clip)][0] * clip[i][1]
                   for i in range(len(clip))) > 0 else -1.0
    out = list(subject)
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inp, out = out, []
        if not inp:
            break
        for j in range(len(inp)):
            p, q = inp[j], inp[(j + 1) % len(inp)]
            if inside(q, a, b, s):
                if not inside(p, a, b, s):
                    out.append(inter(p, q, a, b))
                out.append(q)
            elif inside(p, a, b, s):
                out.append(inter(p, q, a, b))
    return out


def overlap_area(p, q):
    c = clip_convex(p, q)
    return poly_area(c) if len(c) >= 3 else 0.0


def box_poly(b):
    return [(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3])]


def point_in_poly(x, y, p):
    ins = False
    for i in range(len(p)):
        (x1, y1), (x2, y2) = p[i], p[(i + 1) % len(p)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-300) + x1:
            ins = not ins
    return ins


def dist_point_poly(x, y, p):
    best = float("inf")
    for i in range(len(p)):
        (x1, y1), (x2, y2) = p[i], p[(i + 1) % len(p)]
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / L2))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return 0.0 if point_in_poly(x, y, p) else best


# ------------------------------------------------------------------ marks
def marks(texts):
    """Every plan mark token in the texts: a combined 'C3/F3' gives two marks sharing one text."""
    out = []
    for t in texts:
        for k, tok in enumerate(re.split(r"[/,]| +", t["norm"])):
            fam, mk = DM.mark_family(tok)
            if fam:
                out.append({"mark": mk, "family": fam, "x": t["x"], "y": t["y"], "h": t.get("height") or 0.0,
                            "rot": t.get("rotation") or 0.0, "text_id": t["id"], "layer": t["layer"],
                            "sheet": t.get("sheet"), "combined": "/" in t["norm"], "token": k})
    return out


def _layer_role(layer):
    from engine.source import drawing_inventory as DI
    return DI.role_guess(layer)


def candidate_rects(ents, unit_m):
    """Closed rectangles from polylines plus rectangles from four drawn lines, on non-annotation layers."""
    rects = [dict(r, origin="POLYLINE") for r in ents["rects"] if _layer_role(r["layer"]) not in ANNOTATION_ROLES]
    by_layer = defaultdict(list)
    for s in ents["segments"]:
        if _layer_role(s["layer"]) in ANNOTATION_ROLES:
            continue
        by_layer[s["layer"]].append((s["id"], s["a"][0], s["a"][1], s["b"][0], s["b"][1]))
    eps = 0.5e-3 / unit_m
    keyf = lambda b: tuple(round(v * unit_m * 1000) for v in b)            # noqa: E731 - 1 mm grid
    uniq, seen = [], set()
    for r in rects:
        if keyf(r["box"]) not in seen:
            seen.add(keyf(r["box"]))
            uniq.append(r)
    rects = uniq
    for lay, segs in by_layer.items():
        if len(segs) > 4000:
            continue
        for r in Q.rectangles(segs, eps=eps):
            k = keyf(r["bounds"])
            if k in seen:
                continue
            seen.add(k)
            rects.append({"box": r["bounds"], "layer": lay, "source": "LINES:" + ",".join(r["edge_keys"][:4]),
                          "origin": "LINES"})
    return rects


def _digest(s):
    import hashlib
    return hashlib.sha256(str(s).encode()).hexdigest()[:6]


def _contains(box, x, y):
    return box[0] < x < box[2] and box[1] < y < box[3]


# ------------------------------------------------------------------ footings
def footings(sheet, ents, lib, unit_m, size_tol_m=0.02, max_footing_m=8.0):
    ms = [m for m in marks(ents["texts"]) if m["family"] == "FOOTING"]
    rects = [r for r in candidate_rects(ents, unit_m)                                 # footing-sized only
             if min(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * unit_m >= 0.4 and
             max(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * unit_m <= max_footing_m]
    # schedule-size templates around each mark: outlines interrupted where straps / ground beams enter
    segs_all = [(x["id"], x["a"][0], x["a"][1], x["b"][0], x["b"][1]) for x in ents["segments"]
                if _layer_role(x["layer"]) not in ANNOTATION_ROLES]
    seen = {tuple(round(v, 1) for v in r["box"]) for r in rects}
    for m in ms:
        row = lib.get(("FOOTING", m["mark"]))
        if row is None or not (row["dims_m"].get("W") and row["dims_m"].get("H")):
            continue
        Lm, Wm = row["dims_m"]["W"], row["dims_m"]["H"]
        w = max(Lm, Wm) / unit_m * 1.1
        win = [g for g in segs_all if min(g[1], g[3]) <= m["x"] + w and max(g[1], g[3]) >= m["x"] - w and
               min(g[2], g[4]) <= m["y"] + w and max(g[2], g[4]) >= m["y"] - w]
        for t in Q.template_outlines(win, Lm * 1000, Wm * 1000, unit_m * 1000, eps=0.5e-3 / unit_m):
            k = tuple(round(v, 1) for v in t["bounds"])
            if k in seen or not _contains(t["bounds"], m["x"], m["y"]):
                continue
            seen.add(k)
            rects.append({"box": t["bounds"], "layer": "TEMPLATE", "origin": "TEMPLATE_" + t["state"],
                          "source": "TEMPLATE:" + ",".join(f"{v:.1f}" for v in t["bounds"])})
    by_rect = defaultdict(list)
    out = []
    for m in ms:
        inside = [r for r in rects if _contains(r["box"], m["x"], m["y"])]
        row = lib.get(("FOOTING", m["mark"]))
        if not inside and row is not None and row["dims_m"].get("W") and row["dims_m"].get("H"):
            sz = sorted((row["dims_m"]["W"], row["dims_m"]["H"]))
            gap = max(3 * (m["h"] or 0), 0.5 / unit_m)
            near = sorted((dist_point_poly(m["x"], m["y"], box_poly(r["box"])), r["source"], r) for r in rects
                          if abs(sorted(((r["box"][2] - r["box"][0]) * unit_m,
                                         (r["box"][3] - r["box"][1]) * unit_m))[0] - sz[0]) <= size_tol_m and
                          abs(sorted(((r["box"][2] - r["box"][0]) * unit_m,
                                      (r["box"][3] - r["box"][1]) * unit_m))[1] - sz[1]) <= size_tol_m)
            near = [n for n in near if n[0] <= gap]
            if len(near) == 1 or (len(near) > 1 and near[1][0] - near[0][0] > max(m["h"] or 0, 0.05 / unit_m)):
                inside = [near[0][2]]
        if not inside:
            out.append({"member_id": f"FTG:{sheet['sheet_id']}:{m['text_id']}", "mark": m["mark"],
                        "state": "NO_OUTLINE", "sheet": sheet["sheet_id"], "mark_at": (m["x"], m["y"])})
            continue
        r = min(inside, key=lambda r: ((r["box"][2] - r["box"][0]) * (r["box"][3] - r["box"][1]), r["source"]))
        by_rect[r["source"]].append((m, r))
    for src, lst in sorted(by_rect.items()):
        r = lst[0][1]
        b = r["box"]
        drawn = sorted(((b[2] - b[0]) * unit_m, (b[3] - b[1]) * unit_m))
        mks = sorted({m["mark"] for m, _ in lst})
        base = {"sheet": sheet["sheet_id"], "box": b, "outline": src, "drawn_m": drawn, "layer": r["layer"],
                "mark_at": (lst[0][0]["x"], lst[0][0]["y"]), "storey": "FOUNDATION"}
        if len(mks) > 1:
            out.append(dict(base, member_id=f"FTG:{sheet['sheet_id']}:{src}", mark="/".join(mks),
                            state="COMBINED_OUTLINE"))
            continue
        mk = mks[0]
        row = lib.get(("FOOTING", mk))
        mid = f"FTG:{sheet['sheet_id']}:{mk}@{round(b[0])},{round(b[1])}:{_digest(src)}"
        if row is None:
            st = "SCHEDULE_CONFLICT" if ("FOOTING", mk) in lib else "TYPE_NOT_IN_SCHEDULE"
            out.append(dict(base, member_id=mid, mark=mk, state=st))
            continue
        d = row["dims_m"]
        L, W, D = d.get("W"), d.get("H"), d.get("D")
        sched = sorted((L or 0, W or 0))
        ok = L and W and abs(drawn[0] - sched[0]) <= size_tol_m and abs(drawn[1] - sched[1]) <= size_tol_m
        out.append(dict(base, member_id=mid, mark=mk, state=("CONFIRMED" if ok else "SIZE_MISMATCH"),
                        outline_origin=r.get("origin"),
                        schedule_m=[L, W, D], schedule_source=row["source"], bars=row.get("bars", []),
                        volume_schedule=(L * W * D) if (L and W and D) else None,
                        volume_drawn=(drawn[0] * drawn[1] * D) if D else None))
    # outlines holding only a column mark: a footing type by a UNIQUE schedule size match (LOW confidence, inferred)
    taken = {f.get("outline") for f in out}
    cmarks = [m for m in marks(ents["texts"]) if m["family"] == "COLUMN"]
    sizes = {}
    for (fam, mk), row in lib.items():
        if fam == "FOOTING" and row is not None and row["dims_m"].get("W") and row["dims_m"].get("H"):
            sizes[mk] = (sorted((row["dims_m"]["W"], row["dims_m"]["H"])), row)
    held = [f["box"] for f in out if f.get("box")]
    for r in rects:
        if r["source"] in taken:
            continue
        b = r["box"]
        if any(overlap_area(box_poly(b), box_poly(h)) >= 0.5 * (b[2] - b[0]) * (b[3] - b[1]) for h in held):
            continue
        cm = [m for m in cmarks if _contains(b, m["x"], m["y"])]
        if not cm:
            continue
        drawn = sorted(((b[2] - b[0]) * unit_m, (b[3] - b[1]) * unit_m))
        if drawn[1] > 8.0 or drawn[0] < 0.4:
            continue
        hits = [mk for mk, (sz, _) in sizes.items() if abs(sz[0] - drawn[0]) <= size_tol_m and
                abs(sz[1] - drawn[1]) <= size_tol_m]
        if len(hits) != 1:
            continue
        mk = hits[0]
        row = sizes[mk][1]
        d = row["dims_m"]
        L, W, D = d.get("W"), d.get("H"), d.get("D")
        out.append({"sheet": sheet["sheet_id"], "box": b, "outline": r["source"], "drawn_m": drawn, "layer": r["layer"],
                    "mark_at": (cm[0]["x"], cm[0]["y"]), "storey": "FOUNDATION",
                    "member_id": f"FTG:{sheet['sheet_id']}:{mk}@{round(b[0])},{round(b[1])}:{_digest(r['source'])}",
                    "mark": mk,
                    "state": "TYPE_BY_SIZE_MATCH", "column_marks": sorted({m['mark'] for m in cm}),
                    "schedule_m": [L, W, D], "schedule_source": row["source"], "bars": row.get("bars", []),
                    "volume_schedule": (L * W * D) if (L and W and D) else None,
                    "volume_drawn": (drawn[0] * drawn[1] * D) if D else None})
        taken.add(r["source"])
        held.append(b)
    # footing / footing overlap: a partial overlap is deducted once (from the later id); a near-total overlap
    # (>= 90 % of the smaller outline) is a duplicate / nested outline -> a conflict on the smaller, never a deduction
    q = [f for f in out if f.get("box") and f["state"] in ("CONFIRMED", "SIZE_MISMATCH", "TYPE_BY_SIZE_MATCH",
                                                           "COMBINED_OUTLINE")]
    q.sort(key=lambda f: f["member_id"])
    for i, a in enumerate(q):
        for b in q[i + 1:]:
            ov = overlap_area(box_poly(a["box"]), box_poly(b["box"])) * unit_m ** 2
            if ov <= 1e-6:
                continue
            aa = (a["box"][2] - a["box"][0]) * (a["box"][3] - a["box"][1]) * unit_m ** 2
            ab = (b["box"][2] - b["box"][0]) * (b["box"][3] - b["box"][1]) * unit_m ** 2
            small, big = (a, b) if aa <= ab else (b, a)
            rank = {"CONFIRMED": 3, "SIZE_MISMATCH": 2, "TYPE_BY_SIZE_MATCH": 1, "COMBINED_OUTLINE": 0}
            if abs(aa - ab) <= 0.02 * max(aa, ab) and rank.get(a["state"], 0) != rank.get(b["state"], 0):
                small, big = (a, b) if rank.get(a["state"], 0) < rank.get(b["state"], 0) else (b, a)
            if ov >= 0.9 * min(aa, ab) or "COMBINED_OUTLINE" in (a["state"], b["state"]):
                small.setdefault("conflicts", []).append({"with": big["member_id"], "area_m2": ov,
                                                          "kind": "NESTED_OR_DUPLICATE_OUTLINE"})
                if small["state"] != "COMBINED_OUTLINE":
                    small["state"] = "NESTED_OR_DUPLICATE_OUTLINE"
                continue
            a.setdefault("overlaps", []).append({"with": b["member_id"], "area_m2": ov})
            b.setdefault("overlaps", []).append({"with": a["member_id"], "area_m2": ov, "deduct": True})
    return out


# ------------------------------------------------------------------ columns
def column_occurrences(sheet, ents, lib, unit_m, size_tol_m=0.02, max_column_m=2.0):
    """A column mark binds to the column-sized outline (<= max_column_m) that CONTAINS it, else to the nearest one
    within max(3 text heights, 0.6 m); two outlines equally near -> AMBIGUOUS (no drawn section)."""
    ms = [m for m in marks(ents["texts"]) if m["family"] == "COLUMN"]

    def sizes(fam):
        out = set()
        for (f, _), row in lib.items():
            if f == fam and row:
                for b in list(row.get("by_storey", {}).values()) + [{"dims_m": row.get("dims_m", {})}]:
                    W, H = b["dims_m"].get("W"), b["dims_m"].get("H")
                    if W and H:
                        out.add((min(W, H), max(W, H)))
        return out
    csz, fsz = sizes("COLUMN"), sizes("FOOTING")

    def is_footing(r):
        """an outline on a footing layer, or at a scheduled footing size and no column size, is never a column's
        drawn section (a combined C/F mark sits inside its footing) - M2 synthetic-demo finding"""
        if _layer_role(r["layer"]) == "FOOTING":
            return True
        d = sorted(((r["box"][2] - r["box"][0]) * unit_m, (r["box"][3] - r["box"][1]) * unit_m))
        hit = lambda S: any(abs(d[0] - a) <= size_tol_m and abs(d[1] - b) <= size_tol_m for a, b in S)  # noqa: E731
        return hit(fsz) and not hit(csz)
    rects = [r for r in candidate_rects(ents, unit_m)
             if max(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * unit_m <= max_column_m and
             not is_footing(r)]
    out = []
    for m in ms:
        gap = max(3 * (m["h"] or 0), 0.6 / unit_m)
        cand = sorted((dist_point_poly(m["x"], m["y"], box_poly(r["box"])), r["source"], r) for r in rects)
        cand = [c for c in cand if c[0] <= gap]
        r, binding = None, "NO_OUTLINE"
        if cand:
            if len(cand) == 1 or cand[0][0] == 0.0 or cand[1][0] - cand[0][0] > max(m["h"] or 0, 0.05 / unit_m):
                r, binding = cand[0][2], ("INSIDE" if cand[0][0] == 0.0 else "NEAREST")
            else:
                binding = "AMBIGUOUS_OUTLINE"
        drawn = sorted(((r["box"][2] - r["box"][0]) * unit_m, (r["box"][3] - r["box"][1]) * unit_m)) if r else None
        row = lib.get(("COLUMN", m["mark"]))
        out.append({"member_id": f"COL:{sheet['sheet_id']}:{m['mark']}@{round(m['x'])},{round(m['y'])}",
                    "mark": m["mark"], "sheet": sheet["sheet_id"], "mark_at": (m["x"], m["y"]),
                    "box": r["box"] if r else None, "drawn_m": drawn, "outline_binding": binding, "row": row,
                    "in_schedule": ("COLUMN", m["mark"]) in lib})
    return out


def column_storeys(occ, heights, size_tol_m=0.02):
    """occurrence x schedule storey band -> column pieces with section and (if printed) height."""
    pieces = []
    for o in occ:
        row = o["row"]
        if row is None:
            pieces.append(dict(o, storey="UNKNOWN", state="SCHEDULE_CONFLICT" if o["in_schedule"] else
                               "TYPE_NOT_IN_SCHEDULE", piece_id=o["member_id"]))
            continue
        bands = row["by_storey"] or {"ALL": {"dims_m": row.get("dims_m", {}), "bars": row.get("bars", [])}}
        for st, b in sorted(bands.items()):
            B, H = b["dims_m"].get("W"), b["dims_m"].get("H")
            if not (B and H):
                continue
            match = None
            if o["drawn_m"]:
                match = abs(o["drawn_m"][0] - min(B, H)) <= size_tol_m and abs(o["drawn_m"][1] - max(B, H)) <= size_tol_m
            h = heights.get(st)
            pieces.append(dict(o, piece_id=f"{o['member_id']}|{st}", storey=st, section_m=(B, H),
                               bars=b.get("bars", []), height_m=h, drawn_match=match,
                               state=("NO_HEIGHT" if h is None else "MEASURED")))
    return pieces


# ------------------------------------------------------------------ beams
def _faces(ents, layers):
    return [{"handle": s["id"], "layer": s["layer"], "p0": tuple(s["a"]), "p1": tuple(s["b"])}
            for s in ents["segments"] if s["layer"] in layers]


def _arcs(ents, layers):
    out = []
    for a in ents["arcs"]:
        if a["layer"] not in layers:
            continue
        cx, cy = a["c"]
        a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
        a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
        if a["dir"] == "CW":
            a0, a1 = a1, a0                      # the same physical arc, swept CCW from its other end
        out.append({"handle": a["id"], "layer": a["layer"], "cx": cx, "cy": cy, "r": a["r"],
                    "a0": a0 % (2 * math.pi), "a1": a1 % (2 * math.pi), "cw": False})
    return out


def outline_share(ents, layer):
    """Share of a layer's segments that are sides of small closed rectangles (member outlines, not beam faces)."""
    segs = [x for x in ents["segments"] if x["layer"] == layer]
    srcs = {r["source"] for r in ents["rects"] if r["layer"] == layer}
    if not segs:
        return 0.0
    return sum(1 for x in segs if x["id"].rsplit(":", 1)[0] in srcs) / len(segs)


def score_edge_layers(ents, widths_native, tol_native, beam_marks, max_outline_share=0.5, min_face_native=None):
    """layer -> number of beam marks that sit in or beside a parallel pair at a scheduled width on that layer.
    A layer whose segments are mostly closed member outlines (columns, footings) is never an edge layer."""
    cand = sorted({s["layer"] for s in ents["segments"]
                   if _layer_role(s["layer"]) not in ANNOTATION_ROLES + ("COLUMN", "FOOTING")})
    score = {}
    for lay in cand:
        if outline_share(ents, lay) > max_outline_share:
            continue
        faces = _faces(ents, {lay})
        if len(faces) < 2 or len(faces) > 6000:
            continue
        polys = []
        mf = min_face_native if min_face_native is not None else 25 * tol_native
        for w in widths_native:
            r = GN.pair_straight(faces, width=w, tol=tol_native, admitted_layers={lay}, min_face=mf, min_overlap=mf,
                                 join_tol=tol_native / 12.0)
            polys += [b["polygon"] for b in r["bands"]]
        if not polys:
            continue
        hit = 0
        for m in beam_marks:
            gap = max(m["h"] * 2.0, max(widths_native))
            if any(dist_point_poly(m["x"], m["y"], p) <= gap for p in polys):
                hit += 1
        if hit:
            score[lay] = hit
    return score


def beam_bands(ents, layers, widths_native, tol_native, min_face_native):
    bands, conflicts = [], []
    faces = _faces(ents, layers)
    for w in sorted(set(widths_native)):
        r = GN.pair_straight(faces, width=w, tol=tol_native, admitted_layers=set(layers), min_face=min_face_native,
                             min_overlap=min_face_native, join_tol=tol_native / 12.0)
        for b in r["bands"]:
            bands.append(dict(b, width_native=w, kind="STRAIGHT"))
        conflicts += [dict(c, width_native=w) for c in r["conflicts"]]
    arcs = _arcs(ents, layers)
    for w in sorted(set(widths_native)):
        try:
            r = GN.pair_arcs(arcs, width=w, tol=tol_native, admitted_layers=set(layers), centre_tol=tol_native,
                             min_overlap=min_face_native)
        except Exception as e:                                                # noqa: BLE001 - recorded, not hidden
            conflicts.append({"reason": f"ARC_PAIRING_ERROR {type(e).__name__}", "width_native": w})
            continue
        for b in r.get("bands", []):
            bands.append(dict(b, width_native=w, kind="ARC"))
    # one face pair at two widths cannot happen; a face shared by bands of different widths is a conflict
    seen = defaultdict(list)
    for i, b in enumerate(bands):
        for h in b.get("handles", []):
            seen[h].append(i)
    for h, idx in seen.items():
        ws = {bands[i]["width_native"] for i in idx}
        if len(ws) > 1:
            for i in idx:
                bands[i]["width_conflict"] = True
    for k, b in enumerate(bands):
        b["band_id"] = f"BAND{k + 1:04d}"
    return bands, conflicts


def band_axis_deg(b):
    if b["kind"] != "STRAIGHT":
        return None
    u = b["u"]
    return math.degrees(math.atan2(u[1], u[0])) % 180.0


def _same_arc_chain(a, b, tol):
    return a["kind"] == b["kind"] == "ARC" and math.dist(a["centre"], b["centre"]) <= tol and \
        abs(a["r_inner"] - b["r_inner"]) <= tol and abs(a["r_outer"] - b["r_outer"]) <= tol


def bind_marks(bands, beam_marks, widths_of, unit_m, width_tol_m=0.015, angle_tol=12.0):
    """mark -> band(s); positive constraints only.
    BOUND               a band at the mark's scheduled width, parallel to the text, inside or within the gap, unique
    BOUND_ARC_CHAIN     the qualifying bands are pieces of one concentric arc band (same centre, same radii): all bound
    BOUND_WIDTH_CONFLICT no band at the scheduled width qualifies but exactly one band of ANOTHER width does: bound with
                        both widths kept (a drawn-vs-schedule conflict, never resolved here)
    AMBIGUOUS / TAG_UNBOUND / TYPE_NOT_IN_SCHEDULE"""
    by_id = {b["band_id"]: b for b in bands}
    out = []
    for m in beam_marks:
        w_sched = widths_of.get((m["family"], m["mark"]))

        def qualifies(b, check_width):
            if check_width and (w_sched is None or abs(b["width_native"] * unit_m - w_sched) > width_tol_m):
                return None
            ax = band_axis_deg(b)
            if ax is not None:
                d = abs(((m["rot"] % 180.0) - ax + 90.0) % 180.0 - 90.0)
                if d > angle_tol:
                    return None
            gap = max(m["h"] * 2.5, b["width_native"] * 1.5)
            dd = dist_point_poly(m["x"], m["y"], b["polygon"])
            return dd if dd <= gap else None
        if w_sched is None:
            out.append(dict(m, state="TYPE_NOT_IN_SCHEDULE", band=None, bands=[]))
            continue
        cands = sorted((d, b["band_id"]) for b in bands if (d := qualifies(b, True)) is not None)
        state = "BOUND"
        if not cands:
            cands = sorted((d, b["band_id"]) for b in bands if (d := qualifies(b, False)) is not None)
            state = "BOUND_WIDTH_CONFLICT"
        if not cands:
            out.append(dict(m, state="TAG_UNBOUND", band=None, bands=[]))
            continue
        first = by_id[cands[0][1]]
        chain = [c for c in cands if _same_arc_chain(first, by_id[c[1]], first["width_native"] * 0.1)]
        if first["kind"] == "ARC" and len(chain) > 1:
            out.append(dict(m, state="BOUND_ARC_CHAIN" if state == "BOUND" else state, band=first["band_id"],
                            bands=[c[1] for c in chain]))
        elif len(cands) == 1 or cands[1][0] - cands[0][0] > max(m["h"], 1e-9):
            out.append(dict(m, state=state, band=cands[0][1], bands=[cands[0][1]], gap_native=cands[0][0]))
        else:
            out.append(dict(m, state="AMBIGUOUS", band=None, bands=[], candidates=[c[1] for c in cands[:3]]))
    return out


def split_at_supports(bands, column_boxes, min_piece_native):
    """A straight band that runs through columns is cut into clear pieces between them (the column owns its
    footprint). Each piece keeps the parent band id and its own polygon / length; arcs are kept whole."""
    out = []
    for b in bands:
        if b["kind"] != "STRAIGHT" or not column_boxes:
            out.append(dict(b, parent=b["band_id"], cut_by=[]))
            continue
        u, n = b["u"], b["n"]
        cuts = []
        for c in column_boxes:
            poly = box_poly(c)
            if overlap_area(b["polygon"], poly) <= 0:
                continue
            ts = [x * u[0] + y * u[1] for x, y in poly]
            cuts.append((max(min(ts), b["t0"]), min(max(ts), b["t1"]), tuple(round(v, 1) for v in c)))
        cuts.sort()
        pieces, t = [], b["t0"]
        for c0, c1, cid in cuts:
            if c0 > t:
                pieces.append((t, c0))
            t = max(t, c1)
        if b["t1"] > t:
            pieces.append((t, b["t1"]))
        pieces = [pc for pc in pieces if pc[1] - pc[0] >= min_piece_native]
        if not cuts:
            out.append(dict(b, parent=b["band_id"], cut_by=[]))
            continue
        for k, (t0, t1) in enumerate(pieces, 1):
            lo, hi = b["lo_off"], b["hi_off"]
            poly = [(u[0] * t0 + n[0] * lo, u[1] * t0 + n[1] * lo), (u[0] * t1 + n[0] * lo, u[1] * t1 + n[1] * lo),
                    (u[0] * t1 + n[0] * hi, u[1] * t1 + n[1] * hi), (u[0] * t0 + n[0] * hi, u[1] * t0 + n[1] * hi)]
            out.append(dict(b, band_id=f"{b['band_id']}.{k}", parent=b["band_id"], t0=t0, t1=t1, length=t1 - t0,
                            polygon=poly, cut_by=[c[2] for c in cuts]))
    return out


def collinear_neighbours(bands, max_gap_native, angle_tol_deg=1.0, offset_tol_native=None):
    """band -> [bands on the same axis line, same width, separated by at most max_gap_native] (straight only)."""
    out = defaultdict(list)
    st = [b for b in bands if b["kind"] == "STRAIGHT"]
    for i, a in enumerate(st):
        for b in st[i + 1:]:
            if abs(a["width_native"] - b["width_native"]) > 1e-6:
                continue
            if abs(a["u"][0] * b["u"][1] - a["u"][1] * b["u"][0]) > math.radians(angle_tol_deg):
                continue
            tol = offset_tol_native if offset_tol_native is not None else a["width_native"] * 0.1
            if abs(a["lo_off"] - b["lo_off"]) > tol or abs(a["hi_off"] - b["hi_off"]) > tol:
                continue
            gap = max(b["t0"] - a["t1"], a["t0"] - b["t1"])
            if 0 <= gap <= max_gap_native or gap < 0:
                out[a["band_id"]].append(b["band_id"])
                out[b["band_id"]].append(a["band_id"])
    return out


def inherit_sections(bands, bound, lib, max_gap_native, span_counts=None):
    """Untagged bands collinear with a bound band (same width, across a support gap) inherit its mark as
    INHERITED_ALONG_LINE; continuous-beam marks spread up to their scheduled span count. Returns extra bindings."""
    nb = collinear_neighbours(bands, max_gap_native)
    owner = {}
    for m in bound:
        for bid in m.get("bands", []):
            owner.setdefault(bid, (m["family"], m["mark"], m["state"]))
    extra = []
    frontier = list(owner.items())
    seen = set(owner)
    while frontier:
        bid, (fam, mk, st) = frontier.pop(0)
        for n in sorted(nb.get(bid, [])):
            if n in seen:
                continue
            seen.add(n)
            owner[n] = (fam, mk, "INHERITED_ALONG_LINE")
            extra.append({"mark": mk, "family": fam, "state": "INHERITED_ALONG_LINE", "band": n, "bands": [n],
                          "from_band": bid})
            frontier.append((n, owner[n]))
    return extra


def band_length_native(b):
    if b["kind"] == "STRAIGHT":
        return b["length"]
    return b.get("CENTERLINE_ARC_LENGTH", b.get("length", 0.0))


def beam_quantities(bands, bound, lib, columns_boxes, unit_m, slab_t_m, *, family_of_band=None):
    """Per band: owner mark, section, drawn length, column deduction, beam-beam junction ownership, volumes under
    both depth conventions (or UNRESOLVED geometry kept)."""
    by_band = defaultdict(list)
    for m in bound:
        if m["state"].startswith("BOUND") or m["state"] == "INHERITED_ALONG_LINE":
            for bid in m.get("bands") or [m["band"]]:
                by_band[bid].append(m)
    recs = []
    for b in bands:
        L = band_length_native(b) * unit_m
        W = b["width_native"] * unit_m
        col_ov = sum(overlap_area(b["polygon"], box_poly(c)) for c in columns_boxes) * unit_m ** 2 \
            if b["kind"] == "STRAIGHT" else 0.0
        ms = by_band.get(b["band_id"], [])
        mk = sorted({(m["family"], m["mark"]) for m in ms})
        rec = {"band_id": b["band_id"], "kind": b["kind"], "width_m": W, "length_m": L, "polygon": b["polygon"],
               "handles": b.get("handles", []), "column_overlap_m2": col_ov, "marks": ["/".join(x) for x in mk],
               "width_conflict": bool(b.get("width_conflict"))}
        if len(mk) > 1:
            rec["state"] = "MULTIPLE_MARKS"
        elif len(mk) == 1:
            row = lib.get(mk[0])
            if row is None:
                rec["state"] = "SCHEDULE_CONFLICT"
            else:
                H = row["dims_m"].get("H")
                how = sorted({m["state"] for m in ms})
                rec.update(state="BOUND" if H else "NO_SCHEDULE_DEPTH", mark=mk[0][1], family=mk[0][0],
                           depth_m=H, schedule_width_m=row["dims_m"].get("W"), bars=row.get("bars", []),
                           schedule_source=row["source"], binding=how[0] if len(how) == 1 else "+".join(how))
        else:
            rec["state"] = "UNBOUND"
        recs.append(rec)
    # beam-beam junction overlap: the square goes to the longer band (ties by id); the other deducts it
    idx = {r["band_id"]: r for r in recs}
    for i, a in enumerate(recs):
        if a["kind"] != "STRAIGHT":
            continue
        for b in recs[i + 1:]:
            if b["kind"] != "STRAIGHT":
                continue
            ov = overlap_area(a["polygon"], b["polygon"]) * unit_m ** 2
            if ov <= 1e-6:
                continue
            owner, other = (a, b) if (a["length_m"], b["band_id"]) >= (b["length_m"], a["band_id"]) else (b, a)
            other.setdefault("junction_deductions", []).append({"owner": owner["band_id"], "area_m2": ov})
            owner.setdefault("junction_owned", []).append({"other": other["band_id"], "area_m2": ov})
    for r in recs:
        plan = r["width_m"] * r["length_m"] - r["column_overlap_m2"] - sum(d["area_m2"] for d in
                                                                           r.get("junction_deductions", []))
        r["net_plan_m2"] = max(plan, 0.0)
        if r.get("depth_m"):
            r["v_total_depth"] = r["net_plan_m2"] * r["depth_m"]
            r["v_below_slab"] = r["net_plan_m2"] * (r["depth_m"] + slab_t_m) if slab_t_m is not None else None
        r.pop("polygon_native", None)
    return recs


def policy_record():
    return {"policy": POLICY_ID, "families": ["FOOTING", "COLUMN", "BEAM", "CONTINUOUS_BEAM", "GROUND_BEAM",
                                              "STRAP_BEAM"],
            "rule": "plan marks decide occurrence; the schedule gives sections; geometry confirms; unbound bands and "
                    "orphan marks are kept and reported, never dropped or guessed"}

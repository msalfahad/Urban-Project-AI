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
    tol = 1e-3 / unit_m                    # the same outline drawn twice (a polyline and its four lines) within 1 mm;
    cell = 5e-3 / unit_m                   # a 1 mm GRID key split twins lying across a rounding boundary (M3)
    index = defaultdict(list)

    def dup(b):
        gx, gy = int(math.floor(b[0] / cell)), int(math.floor(b[1] / cell))
        for i in (gx - 1, gx, gx + 1):
            for j in (gy - 1, gy, gy + 1):
                if any(all(abs(p - q) <= tol for p, q in zip(b, o)) for o in index[(i, j)]):
                    return True
        index[(gx, gy)].append(b)
        return False
    rects = [r for r in rects if not dup(r["box"])]
    for lay, segs in by_layer.items():
        if len(segs) > 4000:
            continue
        for r in Q.rectangles(segs, eps=eps):
            if dup(r["bounds"]):
                continue
            rects.append({"box": r["bounds"], "layer": lay, "source": "LINES:" + ",".join(r["edge_keys"][:4]),
                          "origin": "LINES"})
        if (ents.get("options") or {}).get("drawn_rectangles"):
            for r in drawn_rectangles(segs, eps=eps):
                if dup(r["box"]):
                    continue
                rects.append(dict(r, layer=lay, origin="FOUR_SIDES"))
    return rects


def drawn_rectangles(segs, *, eps):
    """M7: rectangles drawn as four whole sides whose ends meet at the corners - each side one line (or collinear
    pieces end to end). Q.rectangles returns the MINIMAL cells of the line arrangement, so two outlines that cross (a
    cross- or T-shaped column drawn as two overlapping rectangles, an exploded polyline under a second outline) come
    back as five pieces and neither drawn rectangle; this finds the drawn ones. segs: (id, x1, y1, x2, y2)."""
    q = lambda v: int(round(v / eps))                                          # noqa: E731
    H, V = defaultdict(list), set()
    for sid, x1, y1, x2, y2 in segs:
        if abs(y1 - y2) <= eps and abs(x2 - x1) > eps:
            a, b = sorted((x1, x2))
            H[(q(a), q(b))].append(((y1 + y2) / 2, sid, a, b))
        elif abs(x1 - x2) <= eps and abs(y2 - y1) > eps:
            a, b = sorted((y1, y2))
            V.add((q((x1 + x2) / 2), q(a), q(b)))
    out, seen = [], set()
    for (qa, qb), ys in H.items():
        ys = sorted(ys)
        for i in range(len(ys)):
            for j in range(i + 1, len(ys)):
                ya, yb = ys[i][0], ys[j][0]
                if yb - ya <= eps:
                    continue
                if (qa, q(ya), q(yb)) in V and (qb, q(ya), q(yb)) in V:
                    k = (qa, q(ya), qb, q(yb))
                    if k in seen:
                        continue
                    seen.add(k)
                    out.append({"box": (ys[i][2], ya, ys[i][3], yb), "source": f"SIDES:{ys[i][1]},{ys[j][1]}"})
    return sorted(out, key=lambda r: r["box"])


def _digest(s):
    import hashlib
    return hashlib.sha256(str(s).encode()).hexdigest()[:6]


def _contains(box, x, y):
    return box[0] < x < box[2] and box[1] < y < box[3]


# ------------------------------------------------------------------ footings
def closed_polygons(ents, eps):
    """Closed, NON-rectangular polygons drawn as one polyline (consecutive spans of one source, end meeting start):
    a footing clipped where it meets its neighbour, an L-shaped outline. Rectangles are left to closed_rectangles."""
    by_src = defaultdict(list)
    for s in ents["segments"]:
        if _layer_role(s["layer"]) in ANNOTATION_ROLES:
            continue
        src, _, sub = s["id"].rpartition(":")
        if sub.isdigit():
            by_src[src].append((int(sub), s))
    out = []
    for src, ss in by_src.items():
        if len(ss) < 5:
            continue
        ss = [s for _, s in sorted(ss, key=lambda x: x[0])]
        chain = all(math.dist(ss[k]["b"], ss[k + 1]["a"]) <= eps for k in range(len(ss) - 1))
        if not chain or math.dist(ss[-1]["b"], ss[0]["a"]) > eps:
            continue
        poly = [tuple(s["a"]) for s in ss]
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        out.append({"box": (min(xs), min(ys), max(xs), max(ys)), "layer": ss[0]["layer"], "source": src,
                    "origin": "POLYGON", "polygon": poly})
    if (ents.get("options") or {}).get("polygons_from_lines"):
        known = [o["box"] for o in out]
        for r in line_rings([s for s in ents["segments"] if _layer_role(s["layer"]) not in ANNOTATION_ROLES], eps):
            if not any(all(abs(p - q) <= 2 * eps for p, q in zip(r["box"], k)) for k in known):
                out.append(r)
    return out


def line_rings(segs, eps, min_vertices=5):
    """M7: closed, NON-rectangular outlines drawn as separate lines (an exploded polyline): per layer, a connected set
    of straight segments in which every end meets exactly one other end (each vertex joins exactly two lines, within
    eps) and that closes on itself. A vertex where a third line meets breaks the ring (never guessed through)."""
    q = lambda p: (int(round(p[0] / eps)), int(round(p[1] / eps)))            # noqa: E731
    by_layer = defaultdict(list)
    for s in segs:
        if s.get("kind", "LINE") == "LINE" and math.dist(s["a"], s["b"]) > 2 * eps:
            by_layer[s["layer"]].append(s)
    out = []
    for lay, ss in sorted(by_layer.items()):
        if len(ss) > 20000:
            continue
        ends = defaultdict(list)
        for k, s in enumerate(ss):
            ends[q(s["a"])].append((k, 0))
            ends[q(s["b"])].append((k, 1))
        used = set()
        for k0 in range(len(ss)):
            if k0 in used:
                continue
            ring, walk, k, end, closed = [], [], k0, 1, False      # end: which end of line k we leave by (1 = b)
            while len(walk) <= 400:
                walk.append(k)
                ring.append(ss[k]["a"] if end == 1 else ss[k]["b"])
                node = q(ss[k]["b"] if end == 1 else ss[k]["a"])
                nxt = [x for x in ends[node] if x[0] != k]
                if len(ends[node]) != 2 or len(nxt) != 1:
                    break                                          # an open end or a third line: no ring
                k, e = nxt[0]
                end = 1 if e == 0 else 0                           # enter by the shared end, leave by the other
                if k == k0:
                    closed = True
                    break
                if k in used or k in walk:
                    break
            used.update(walk)
            if not closed or len(ring) < min_vertices:
                continue
            xs, ys = [p[0] for p in ring], [p[1] for p in ring]
            out.append({"box": (min(xs), min(ys), max(xs), max(ys)), "layer": lay,
                        "source": "RING:" + ",".join(sorted(ss[m]["id"] for m in walk)[:4]),
                        "origin": "LINE_RING", "polygon": [tuple(p) for p in ring]})
    return out


def footings(sheet, ents, lib, unit_m, size_tol_m=0.02, max_footing_m=8.0):
    ms = [m for m in marks(ents["texts"]) if m["family"] == "FOOTING"]
    seen_m, uniq_m = set(), []
    for m in ms:                                      # the same mark twice at one place (text + block copy) is one
        k = (m["mark"], round(m["x"] * unit_m, 1), round(m["y"] * unit_m, 1))
        if k not in seen_m:
            seen_m.add(k)
            uniq_m.append(m)
    ms = uniq_m
    rects = [r for r in candidate_rects(ents, unit_m) + closed_polygons(ents, 0.5e-3 / unit_m)   # footing-sized only
             if min(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * unit_m >= 0.4 and
             max(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * unit_m <= max_footing_m]
    # schedule-size templates around each mark: outlines interrupted where straps / ground beams enter
    segs_all = [(x["id"], x["a"][0], x["a"][1], x["b"][0], x["b"][1]) for x in ents["segments"]
                if _layer_role(x["layer"]) not in ANNOTATION_ROLES]
    layer_of = {x["id"]: x["layer"] for x in ents["segments"]}
    seen = {tuple(round(v, 1) for v in r["box"]) for r in rects}
    for m in ms:
        row = lib.get(("FOOTING", m["mark"]))
        if row is None or not (row["dims_m"].get("W") and row["dims_m"].get("H")):
            continue
        Lm, Wm = row["dims_m"]["W"], row["dims_m"]["H"]
        w = max(Lm, Wm) / unit_m * 1.6              # an outline may lie up to half its long side beside its label
        win = [g for g in segs_all if min(g[1], g[3]) <= m["x"] + w and max(g[1], g[3]) >= m["x"] - w and
               min(g[2], g[4]) <= m["y"] + w and max(g[2], g[4]) >= m["y"] - w]
        by_lay = defaultdict(list)                  # templates are one layer's linework (M3: a collinear column
        for g in win:                               # face on another layer shifted the strap-entry gap ends)
            by_lay[layer_of[g[0]]].append(g)
        temps = [t for lay in sorted(by_lay) for t in
                 Q.template_outlines(by_lay[lay], Lm * 1000, Wm * 1000, unit_m * 1000, eps=0.5e-3 / unit_m)]
        tol = 1e-3 / unit_m
        for t in temps:
            k = tuple(round(v, 1) for v in t["bounds"])
            if k in seen or any(all(abs(a - b) <= tol for a, b in zip(t["bounds"], r["box"])) for r in rects):
                continue                            # the same outline as a found rectangle (within 1 mm)
            bind_to = None
            if not _contains(t["bounds"], m["x"], m["y"]):
                # a schedule-size outline next to (not around) its label: bound only when it holds no footing mark,
                # lies within half its own long side of this label, and no other footing mark is nearer to it
                tb = box_poly(t["bounds"])
                d0 = dist_point_poly(m["x"], m["y"], tb)
                if any(_contains(t["bounds"], o["x"], o["y"]) for o in ms) or d0 > 0.5 * max(Lm, Wm) / unit_m or \
                        any(dist_point_poly(o["x"], o["y"], tb) < d0 for o in ms if o is not m):
                    continue
                bind_to = m["text_id"]
            seen.add(k)
            rects.append({"box": t["bounds"], "layer": "TEMPLATE", "origin": "TEMPLATE_" + t["state"],
                          "source": "TEMPLATE:" + ",".join(f"{v:.1f}" for v in t["bounds"]), "bind_to": bind_to})
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
            near = [n for n in near if n[0] <= gap or n[2].get("bind_to") == m["text_id"]]
            if len(near) == 1 or (len(near) > 1 and near[1][0] - near[0][0] > max(m["h"] or 0, 0.05 / unit_m)):
                inside = [near[0][2]]
        if not inside:
            rec = {"member_id": f"FTG:{sheet['sheet_id']}:{m['text_id']}", "mark": m["mark"],
                   "state": "NO_OUTLINE", "sheet": sheet["sheet_id"], "mark_at": (m["x"], m["y"]),
                   "storey": "FOUNDATION"}
            d = (row or {}).get("dims_m", {}) if row else {}
            if row is not None and d.get("W") and d.get("H") and d.get("D"):
                # a LABEL-ONLY occurrence: the mark and its schedule type are certain, the outline is not found.
                # Quantity at schedule size, provisional; the drawn evidence around the label is recorded.
                w = max(d["W"], d["H"]) / unit_m
                ev = [g for g in segs_all if math.dist((g[1], g[2]), (m["x"], m["y"])) <= w or
                      math.dist((g[3], g[4]), (m["x"], m["y"])) <= w]
                rec.update(state="LABEL_ONLY", schedule_m=[d["W"], d["H"], d["D"]], schedule_source=row["source"],
                           bars=row.get("bars", []), volume_schedule=d["W"] * d["H"] * d["D"],
                           evidence={"segments_within_footing_size": len(ev)})
            out.append(rec)
            continue
        def fits(r):                                    # an outline of the label's own schedule size wins (M3: the
            if row is None or not (row["dims_m"].get("W") and row["dims_m"].get("H")):   # FF label also sat in a
                return False                                                              # smaller nested outline)
            dd = sorted(((r["box"][2] - r["box"][0]) * unit_m, (r["box"][3] - r["box"][1]) * unit_m))
            sz = sorted((row["dims_m"]["W"], row["dims_m"]["H"]))
            return abs(dd[0] - sz[0]) <= size_tol_m and abs(dd[1] - sz[1]) <= size_tol_m
        r = min(inside, key=lambda r: (not fits(r), (r["box"][2] - r["box"][0]) * (r["box"][3] - r["box"][1]),
                                       r["source"]))
        by_rect[r["source"]].append((m, r))
    for src, lst in sorted(by_rect.items()):
        r = lst[0][1]
        b = r["box"]
        drawn = sorted(((b[2] - b[0]) * unit_m, (b[3] - b[1]) * unit_m))
        mks = sorted({m["mark"] for m, _ in lst})
        pa = (poly_area(r["polygon"]) if r.get("polygon") else (b[2] - b[0]) * (b[3] - b[1])) * unit_m ** 2
        base = {"sheet": sheet["sheet_id"], "box": b, "outline": src, "drawn_m": drawn, "layer": r["layer"],
                "mark_at": (lst[0][0]["x"], lst[0][0]["y"]), "storey": "FOUNDATION", "plan_area_m2": pa,
                "outline_kind": r.get("origin"), "polygon": r.get("polygon"),
                "binding": "LABEL_OUTSIDE_NEAREST_OUTLINE" if r.get("bind_to") else
                ("LABEL_INSIDE" if any(_contains(b, m["x"], m["y"]) for m, _ in lst) else "LABEL_NEAR_OUTLINE")}
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
                        volume_drawn=(drawn[0] * drawn[1] * D) if D else None,
                        volume_polygon=(pa * D) if (D and r.get("polygon")) else None))
    # a label-only occurrence next to a found outline of the SAME type may be a second label of that footing:
    # ambiguous, never counted twice
    for f in out:
        if f["state"] != "LABEL_ONLY":
            continue
        w = max(f["schedule_m"][:2]) / unit_m
        twin = [g for g in out if g.get("box") and g.get("mark") == f["mark"] and
                dist_point_poly(f["mark_at"][0], f["mark_at"][1], box_poly(g["box"])) <= w]
        if twin:
            f["state"] = "LABEL_NEAR_SAME_TYPE_OUTLINE"
            f["twin"] = twin[0]["member_id"]
    # two label-only marks of DIFFERENT types within one footing's long side of each other, with no outline found:
    # one physical footing labelled twice (or a combined one) - a type conflict, quantified once, never twice
    lo_ = [f for f in out if f["state"] == "LABEL_ONLY"]
    for i, a in enumerate(lo_):
        for b in lo_[i + 1:]:
            if a["mark"] == b["mark"] or a["state"] != "LABEL_ONLY" or b["state"] != "LABEL_ONLY":
                continue
            w = max(max(a["schedule_m"][:2]), max(b["schedule_m"][:2])) / unit_m
            if math.dist(a["mark_at"], b["mark_at"]) <= w:
                pair = sorted([a, b], key=lambda f: f["member_id"])
                pair[0]["state"], pair[1]["state"] = "LABEL_TYPE_CONFLICT", "LABEL_TYPE_CONFLICT_SECONDARY"
                pair[0]["conflict_with"] = pair[1]["member_id"]
                pair[0]["candidates"] = {f["mark"]: {"schedule_m": f["schedule_m"], "volume": f["volume_schedule"],
                                                     "bars": f.get("bars", [])} for f in pair}
                pair[1]["conflict_with"] = pair[0]["member_id"]
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
            ov = overlap_area(a.get("polygon") or box_poly(a["box"]), box_poly(b["box"])) * unit_m ** 2
            if b.get("polygon") and not a.get("polygon"):
                ov = overlap_area(b["polygon"], box_poly(a["box"])) * unit_m ** 2
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
def column_occurrences(sheet, ents, lib, unit_m, size_tol_m=0.02, max_column_m=2.0, prefer_section=False):
    """A column mark binds to the column-sized outline (<= max_column_m) that CONTAINS it, else to the nearest one
    within max(3 text heights, 1.0 m); two outlines equally near -> AMBIGUOUS (no drawn section).
    prefer_section (M7): among the outlines within reach, one drawn at a section the mark's schedule row prints wins
    over a nearer one that is not (a pit, tank or plinth square beside a footing label is not the column); then one
    on a column-named layer; then the nearest, as before."""
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
    allr = candidate_rects(ents, unit_m)
    rects = [r for r in allr
             if max(r["box"][2] - r["box"][0], r["box"][3] - r["box"][1]) * unit_m <= max_column_m and
             not is_footing(r)]
    feet = [r["box"] for r in allr if is_footing(r)] if prefer_section else []
    out = []
    for m in ms:
        gap = max(3 * (m["h"] or 0), 1.0 / unit_m)       # column-plan labels sit beside their column (M3: 0.5 -
        cand = sorted((dist_point_poly(m["x"], m["y"], box_poly(r["box"])), r["source"], r) for r in rects)  # 1 m)
        # M7: a combined C/F label printed inside a footing outline belongs to the column outline inside that same
        # footing, at any distance within it (a pit or tank square nearer the label, outside the footing, is not it)
        host = [f for f in feet if f[0] < m["x"] < f[2] and f[1] < m["y"] < f[3]]
        inside = [c for c in cand if any(f[0] <= (c[2]["box"][0] + c[2]["box"][2]) / 2 <= f[2] and
                                         f[1] <= (c[2]["box"][1] + c[2]["box"][3]) / 2 <= f[3] for f in host)]
        cand = inside if inside else [c for c in cand if c[0] <= gap]
        if prefer_section and len(cand) > 1:
            secs = sizes_of_mark(lib, m["mark"])

            def rank(c):
                d = sorted(((c[2]["box"][2] - c[2]["box"][0]) * unit_m, (c[2]["box"][3] - c[2]["box"][1]) * unit_m))
                fit = any(abs(d[0] - a_) <= size_tol_m and abs(d[1] - b_) <= size_tol_m for a_, b_ in secs)
                return (0 if fit else 1, 0 if _layer_role(c[2]["layer"]) == "COLUMN" else 1)
            best = min(rank(c) for c in cand)
            if best != (1, 1):
                cand = [c for c in cand if rank(c) == best]
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


def sizes_of_mark(lib, mark):
    """every (short, long) section the schedule prints for a column mark (any storey band)."""
    row = lib.get(("COLUMN", mark)) or {}
    out = set()
    for b in list((row.get("by_storey") or {}).values()) + [{"dims_m": row.get("dims_m") or {}}]:
        W, H = (b.get("dims_m") or {}).get("W"), (b.get("dims_m") or {}).get("H")
        if W and H:
            out.add((min(W, H), max(W, H)))
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

        def same(dr, B, H):
            return abs(dr[0] - min(B, H)) <= size_tol_m and abs(dr[1] - max(B, H)) <= size_tol_m
        # a plan draws ONE section per column (often its lowest band): a drawn size equal to ANY band of the type is
        # consistent with every band (M3: the column plan's foundation-size outlines were read as GF conflicts)
        any_band = bool(o["drawn_m"]) and any(same(o["drawn_m"], b2["dims_m"].get("W"), b2["dims_m"].get("H"))
                                              for b2 in bands.values() if b2["dims_m"].get("W") and
                                              b2["dims_m"].get("H"))
        for st, b in sorted(bands.items()):
            B, H = b["dims_m"].get("W"), b["dims_m"].get("H")
            if not (B and H):
                continue
            match = None
            if o["drawn_m"]:
                match = same(o["drawn_m"], B, H) or any_band
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


def shared_face_parts(faces, conflicts, width, min_len):
    """M3: a face with a partner at the band width on BOTH sides over a common interval is ambiguous there, and the
    pairing drops the whole strip. The part of a strip where the shared face has no partner on its other side is not
    ambiguous: it is returned as a band (rule SHARED_FACE_UNAMBIGUOUS_PART); the common part stays a conflict."""
    by = {f["handle"]: GN._face(f) for f in faces}
    strips = []
    for c in conflicts:
        if c.get("reason") != "SHARED_FACE_AMBIGUOUS" or c.get("detail") not in by:
            continue
        hs = c["detail"]
        other = next((h for h in c["faces"] if h != hs), None)
        if other not in by:
            continue
        g, o = by[hs], by[other]
        uu = GN._canon_axis(g["u"])
        n = (-uu[1], uu[0])
        side = 1 if GN._proj(o["p0"], n) > GN._proj(g["p0"], n) else -1
        strips.append({"shared": hs, "other": other, "side": side, "t0": c["t0"], "t1": c["t1"], "u": uu, "n": n,
                       "offs": sorted((GN._proj(g["p0"], n), GN._proj(o["p0"], n)))})
    out = []
    for s_ in strips:
        cuts = [(x["t0"], x["t1"]) for x in strips if x["shared"] == s_["shared"] and x["side"] != s_["side"]]
        for t0, t1 in GN._subtract((s_["t0"], s_["t1"]), cuts):
            if t1 - t0 < min_len:
                continue
            uu, n = s_["u"], s_["n"]
            lo, hi = s_["offs"]
            poly = [(uu[0] * t0 + n[0] * lo, uu[1] * t0 + n[1] * lo), (uu[0] * t1 + n[0] * lo, uu[1] * t1 + n[1] * lo),
                    (uu[0] * t1 + n[0] * hi, uu[1] * t1 + n[1] * hi), (uu[0] * t0 + n[0] * hi, uu[1] * t0 + n[1] * hi)]
            out.append({"kind": "STRAIGHT", "u": uu, "n": n, "t0": t0, "t1": t1, "lo_off": lo, "hi_off": hi,
                        "width": hi - lo, "length": t1 - t0, "handles": sorted([s_["shared"], s_["other"]]),
                        "faces_a": [s_["shared"]], "faces_b": [s_["other"]], "strips": 1,
                        "rule": "SHARED_FACE_UNAMBIGUOUS_PART", "state": "ACCEPTED", "polygon": poly,
                        "width_native": width})
    return out


def intervening_parts(faces, conflicts, width, tol, min_len):
    """M3: a strip with a parallel face strictly between its two faces is dropped whole by the pairing, even when
    that face overlaps it over a few millimetres (ST7757 1F: a 10 mm overlap removed a 14.3 m continuous beam). The
    parts of the strip that no intervening face overlaps are returned as bands (rule INTERVENING_FACE_PART); the
    overlapped parts stay conflicts."""
    by = {f["handle"]: GN._face(f) for f in faces}
    out, seen = [], set()
    for c in conflicts:
        if c.get("reason") != "INTERVENING_FACE":
            continue
        key = (tuple(sorted(c["faces"])), round(c["t0"], 3), round(c["t1"], 3))
        if key in seen or not all(h in by for h in c["faces"]):
            continue
        seen.add(key)
        a, b = by[c["faces"][0]], by[c["faces"][1]]
        uu = GN._canon_axis(a["u"])
        n = (-uu[1], uu[0])
        lo, hi = sorted((GN._proj(a["p0"], n), GN._proj(b["p0"], n)))
        cuts = []
        for g in by.values():
            if g["handle"] in c["faces"] or abs(g["u"][0] * uu[1] - g["u"][1] * uu[0]) > 0.01:
                continue
            og = GN._proj(g["p0"], n)
            if lo + tol < og < hi - tol:
                cuts.append(GN._interval(g, uu))
        for t0, t1 in GN._subtract((c["t0"], c["t1"]), cuts):
            if t1 - t0 < min_len:
                continue
            poly = [(uu[0] * t0 + n[0] * lo, uu[1] * t0 + n[1] * lo), (uu[0] * t1 + n[0] * lo, uu[1] * t1 + n[1] * lo),
                    (uu[0] * t1 + n[0] * hi, uu[1] * t1 + n[1] * hi), (uu[0] * t0 + n[0] * hi, uu[1] * t0 + n[1] * hi)]
            out.append({"kind": "STRAIGHT", "u": uu, "n": n, "t0": t0, "t1": t1, "lo_off": lo, "hi_off": hi,
                        "width": hi - lo, "length": t1 - t0, "handles": sorted(c["faces"]), "faces_a": [c["faces"][0]],
                        "faces_b": [c["faces"][1]], "strips": 1, "rule": "INTERVENING_FACE_PART", "state": "ACCEPTED",
                        "polygon": poly, "width_native": width})
    return out


def beam_bands(ents, layers, widths_native, tol_native, min_face_native):
    bands, conflicts = [], []
    faces = _faces(ents, layers)
    for w in sorted(set(widths_native)):
        r = GN.pair_straight(faces, width=w, tol=tol_native, admitted_layers=set(layers), min_face=min_face_native,
                             min_overlap=min_face_native, join_tol=tol_native / 12.0)
        for b in r["bands"]:
            bands.append(dict(b, width_native=w, kind="STRAIGHT"))
        # a recovered part is at least five widths long (a beam, not the stub of a junction)
        bands += shared_face_parts(faces, r["conflicts"], w, max(min_face_native, 5 * w))
        bands += intervening_parts(faces, r["conflicts"], w, tol_native, max(min_face_native, 5 * w))
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
        # M3: a mark with duplicate schedule rows carries every printed width; a band at any of them qualifies
        ws = None if w_sched is None else tuple(w_sched) if isinstance(w_sched, (list, tuple, set)) else (w_sched,)
        ws = tuple(w for w in ws if w) if ws else None

        def qualifies(b, check_width):
            if check_width and (not ws or all(abs(b["width_native"] * unit_m - w) > width_tol_m for w in ws)):
                return None
            ax = band_axis_deg(b)
            if ax is not None:
                d = abs(((m["rot"] % 180.0) - ax + 90.0) % 180.0 - 90.0)
                if d > angle_tol:
                    return None
            gap = max(m["h"] * 2.5, b["width_native"] * 1.5)
            dd = dist_point_poly(m["x"], m["y"], b["polygon"])
            return dd if dd <= gap else None
        if not ws:
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


def split_at_supports(bands, column_boxes, min_piece_native, min_overlap_native2=0.0):
    """A straight band that runs through columns is cut into clear pieces between them (the column owns its
    footprint). Each piece keeps the parent band id and its own polygon / length; arcs are kept whole.
    min_overlap_native2 (M7): a column whose overlap with the band is not above this area only touches it (a face
    flush with the band face) and does not cut it - an exact-zero test flips with floating noise."""
    out = []
    for b in bands:
        if b["kind"] != "STRAIGHT" or not column_boxes:
            out.append(dict(b, parent=b["band_id"], cut_by=[]))
            continue
        u, n = b["u"], b["n"]
        cuts = []
        for c in column_boxes:
            poly = box_poly(c)
            if overlap_area(b["polygon"], poly) <= min_overlap_native2:
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


def _gap_on_support(a, b, supports):
    """True when one support outline fills the whole gap between two collinear bands (it spans the gap along the
    axis and lies across the band line): the beam line continues over a column, the gap is no discontinuity."""
    t_lo, t_hi = sorted((a["t1"], b["t0"]) if a["t1"] <= b["t0"] else (b["t1"], a["t0"]))
    lo, hi = (a["lo_off"] + b["lo_off"]) / 2, (a["hi_off"] + b["hi_off"]) / 2
    u, n = a["u"], (-a["u"][1], a["u"][0])
    slack = 0.25 * abs(hi - lo)                  # drafting noise: the outline may stop a quarter width short
    for c in supports or ():
        pts = box_poly(c)
        ts = [x * u[0] + y * u[1] for x, y in pts]
        ns = [x * n[0] + y * n[1] for x, y in pts]
        if min(ts) <= t_lo + slack and max(ts) >= t_hi - slack and min(ns) < max(lo, hi) and max(ns) > min(lo, hi):
            return True
    return False


def collinear_neighbours(bands, max_gap_native, angle_tol_deg=1.0, offset_tol_native=None, supports=None):
    """band -> [bands on the same axis line, same width, separated by at most max_gap_native - or by a gap one support
    outline fills (M3)] (straight only)."""
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
            if 0 <= gap <= max_gap_native or gap < 0 or (gap <= 3 * max_gap_native and supports and
                                                        _gap_on_support(a, b, supports)):
                out[a["band_id"]].append(b["band_id"])
                out[b["band_id"]].append(a["band_id"])
    return out


def inherit_sections(bands, bound, lib, max_gap_native, span_counts=None, supports=None):
    """Untagged bands collinear with a bound band (same width, across a support gap) inherit its mark as
    INHERITED_ALONG_LINE; continuous-beam marks spread up to their scheduled span count. Returns extra bindings.
    supports (M3): column outlines - a gap one of them fills is bridged whatever its length (up to 3 x max_gap)."""
    nb = collinear_neighbours(bands, max_gap_native, supports=supports)
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


def strap_layers(ents, widths_native, tol_native, strap_marks, min_face_native):
    """Foundation-plan layers that carry strap faces: a parallel pair at a strap width within reach of a strap mark.
    Unlike score_edge_layers a footing layer is admitted (straps are drawn with the footings), but only a pair a
    strap mark points at counts."""
    cand = sorted({s["layer"] for s in ents["segments"] if _layer_role(s["layer"]) not in ANNOTATION_ROLES +
                   ("COLUMN",)})
    score = {}
    for lay in cand:
        faces = _faces(ents, {lay})
        if len(faces) < 2 or len(faces) > 6000:
            continue
        polys = []
        for w in widths_native:
            r = GN.pair_straight(faces, width=w, tol=tol_native, admitted_layers={lay}, min_face=min_face_native,
                                 min_overlap=min_face_native, join_tol=tol_native / 12.0)
            polys += [b["polygon"] for b in r["bands"]]
        hit = sum(1 for m in strap_marks if any(dist_point_poly(m["x"], m["y"], p) <= max(m["h"] * 2.5,
                                                                                         max(widths_native) * 1.5)
                                                for p in polys))
        if hit:
            score[lay] = hit
    return score


def deduct_support_plan(bands, support_polys, unit_m, min_clear_m=0.3):
    """Strap bands run between footings: the plan inside a footing outline is the footing's. Each band gets its
    overlap with the footings (exact convex clipping), the net plan and the mean clear length (net / width). A band
    whose clear part is shorter than min_clear_m lies inside footing outlines - two parallel outline sides, not a
    strap - and is returned separately (never quantified)."""
    keep, inside = [], []
    for b in bands:
        area = abs(poly_area(b["polygon"]))
        ov = [(k, overlap_area(q, b["polygon"])) for k, q in enumerate(support_polys)]   # clip: the convex band
        ov = [(k, a) for k, a in ov if a > 1e-9]
        net = max(area - sum(a for _, a in ov), 0.0)
        clear = net / b["width_native"] * unit_m if b["width_native"] else 0.0
        rec = dict(b, support_overlap_m2=sum(a for _, a in ov) * unit_m ** 2, supports=[k for k, _ in ov],
                   net_plan_m2=net * unit_m ** 2, clear_length_m=clear)
        (keep if clear >= min_clear_m else inside).append(rec)
    return keep, inside


def single_face_beams(ents, layers, marks, widths_of, bands, faces, supports, unit_m, *, angle_tol=12.0):
    """M3: a scheduled beam mark that binds no band, beside ONE edge-layer face whose other side is a slab panel and
    whose mark side is open (no slab cell and no other face within the scheduled width): an edge beam whose outer
    face is not drawn. The band is the face offset by the scheduled width toward the mark, over the face length,
    minus the stretches existing bands already own, split at supports. Returned as bands (rule SINGLE_FACE_INFERRED)
    with the mark bound to them (binding SINGLE_FACE_INFERRED): one assumed dimension (the undrawn face), never more.
    Anything less clear (two candidate faces, a panel on the mark side, no panel behind the face) is left unbound."""
    segs = [s_ for s_ in _faces(ents, layers) if math.dist(s_["p0"], s_["p1"]) * unit_m >= 1.0]
    panels = [f["polygon"] for f in faces if f["class"] == "PANEL"]
    new_b, rebound, used = [], {}, set()
    for mi, m in enumerate(marks):
        if m["state"] != "TAG_UNBOUND":
            continue
        ws = widths_of.get((m["family"], m["mark"]))
        ws = [w for w in (ws if isinstance(ws, (list, tuple, set)) else (ws,)) if w]
        if len(ws) != 1:
            continue
        W = ws[0] / unit_m
        rot = math.radians(m.get("rot") or 0.0)
        cands = []
        for f in segs:
            dx, dy = f["p1"][0] - f["p0"][0], f["p1"][1] - f["p0"][1]
            L = math.hypot(dx, dy)
            ux, uy = dx / L, dy / L
            d_ang = abs(((math.degrees(math.atan2(uy, ux)) - math.degrees(rot)) + 90.0) % 180.0 - 90.0)
            if d_ang > angle_tol:
                continue
            t = (m["x"] - f["p0"][0]) * ux + (m["y"] - f["p0"][1]) * uy
            if not (0.0 <= t <= L):
                continue
            off = (m["x"] - f["p0"][0]) * -uy + (m["y"] - f["p0"][1]) * ux      # signed, + = left of the face
            if abs(off) <= W + max(m["h"] * 2.5, 1.5 * W):
                cands.append((abs(off), f, 1.0 if off > 0 else -1.0, (ux, uy), L))
        cands.sort(key=lambda c: (c[0], -c[4]))
        lines = []                                     # collinear duplicates (drawn twice, healed pieces) are one line
        for c in cands:
            if not any(abs(c[0] - x[0]) <= 0.01 / unit_m and c[2] == x[2] for x in lines):
                lines.append(c)
        if len(lines) != 1:
            continue                                   # no face, or several faces in reach: not decided here
        _, f, sg, (ux, uy), L = cands[0]
        nx, ny = -uy * sg, ux * sg                     # toward the mark
        mid = ((f["p0"][0] + f["p1"][0]) / 2, (f["p0"][1] + f["p1"][1]) / 2)
        e = 0.02 / unit_m
        behind = (mid[0] - nx * e, mid[1] - ny * e)
        front = (mid[0] + nx * W / 2, mid[1] + ny * W / 2)
        back = [q for q in panels if point_in_poly(behind[0], behind[1], q)]
        if not back or 2 * poly_area(back[0]) / sum(math.dist(back[0][k], back[0][(k + 1) % len(back[0])])
                                                    for k in range(len(back[0]))) < 3 * W:
            continue                                   # the face is no slab edge (or the "slab" is a thin strip)
        if any(point_in_poly(front[0], front[1], q) for q in panels):
            continue                                   # a slab cell on the mark side: not an undrawn face
        if f["handle"] in used:
            key = next(k for k, v in rebound.items() if v["face"] == f["handle"])
            rebound[mi] = dict(rebound[key])
            continue
        # stretches of the face line already owned by an existing band at this offset
        t_axis = lambda p: p[0] * ux + p[1] * uy
        t0, t1 = sorted((t_axis(f["p0"]), t_axis(f["p1"])))
        full = [f["p0"], f["p1"], (f["p1"][0] + nx * W, f["p1"][1] + ny * W), (f["p0"][0] + nx * W, f["p0"][1] + ny * W)]
        cuts = []
        for b in bands:
            if b.get("kind") == "STRAIGHT" and overlap_area(full, b["polygon"]) > (0.01 / unit_m) ** 2:
                ts = [t_axis(q) for q in b["polygon"]]
                cuts.append((min(ts), max(ts)))
        pieces = GN._subtract((t0, t1), cuts)
        o0 = f["p0"][0] * -uy + f["p0"][1] * ux                 # face offset on the left normal
        lo, hi = sorted((o0, o0 + sg * W))
        out = []
        for a, b in pieces:
            if (b - a) * unit_m < 0.3:
                continue
            nn = (-uy, ux)
            poly = [(ux * a + nn[0] * lo, uy * a + nn[1] * lo), (ux * b + nn[0] * lo, uy * b + nn[1] * lo),
                    (ux * b + nn[0] * hi, uy * b + nn[1] * hi), (ux * a + nn[0] * hi, uy * a + nn[1] * hi)]
            out.append({"kind": "STRAIGHT", "u": (ux, uy), "n": nn, "t0": a, "t1": b, "lo_off": lo, "hi_off": hi,
                        "width": W, "length": b - a, "handles": [f["handle"]], "faces_a": [f["handle"]],
                        "faces_b": [], "strips": 1, "rule": "SINGLE_FACE_INFERRED", "state": "ACCEPTED",
                        "polygon": poly, "width_native": W})
        if not out:
            continue
        used.add(f["handle"])
        rebound[mi] = {"face": f["handle"], "bands": out}
    for b in [b for v in {id(v["bands"]): v for v in rebound.values()}.values() for b in v["bands"]]:
        new_b.append(b)
    return new_b, rebound


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

"""CAD HEAL (M2) - repairs drafting noise in line work before beams and slab panels are read (generic, stdlib).

Real drawings arrive with faces broken into pieces, lines drawn twice, and face ends that stop a millimetre short of
the column (or run into it). Read naively, a 1 mm gap leaves a slab face open (the panel leaks into the beam strip
and is lost) and a duplicated line doubles a band. Two repairs, both bounded by a named tolerance and both recorded:

    merge_collinear(segments, layers, gap, off_tol, ang_tol)
        per layer, segments on one line (direction within ang_tol, offset within off_tol) whose intervals overlap or
        sit within `gap` of each other are merged into one segment. Duplicates and broken faces collapse; collinear
        faces separated by a column (a gap of the column width) never merge because the gap is far above tolerance.
        The merged segment keeps the id of its first piece and lists every source id in `merged_ids`.

    extend_dangling(segments, layers, targets, snap, eps)
        an endpoint touching nothing (no other segment or target edge within eps) is extended along its own
        direction to the first segment / target edge within `snap`. Overshoots are left alone: the column box
        and the band split at supports already give the column its footprint.

Nothing is invented: a gap wider than `snap` stays open, and the slab engine then reports the leaked face as a
coverage risk instead of guessing its boundary. Every repair is listed (HEAL_MERGE / HEAL_EXTEND) with the source ids.
"""

from __future__ import annotations

import math
from collections import defaultdict

POLICY_ID = "CAD_HEAL_V1"
GAP_M = 0.003          # collinear pieces closer than this are one line
SNAP_M = 0.005         # a dangling end closer than this to a line is drawn to it
ANG_TOL = 1e-3         # rad


def _line_key(s):
    (x1, y1), (x2, y2) = s["a"], s["b"]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L <= 0:
        return None
    th = math.atan2(dy, dx) % math.pi
    if th >= math.pi - ANG_TOL:
        th -= math.pi
    u = (math.cos(th), math.sin(th))
    n = (-u[1], u[0])
    c = n[0] * x1 + n[1] * y1
    return th, c, u, n


def merge_collinear(segments, layers, *, gap, off_tol, ang_tol=ANG_TOL):
    """Returns (segments', log). Segments on other layers pass through untouched."""
    keep, log = [], []
    by_layer = defaultdict(list)
    for s in segments:
        if s["layer"] in layers:
            k = _line_key(s)
            if k is None:
                continue
            by_layer[s["layer"]].append((k, s))
        else:
            keep.append(s)
    for lay in sorted(by_layer):
        rows = sorted(by_layer[lay], key=lambda r: r[0][0])
        dirs, groups = [], []
        for r in rows:                                     # direction clusters, then offset clusters inside each
            if dirs and r[0][0] - dirs[-1][-1][0][0] <= ang_tol:
                dirs[-1].append(r)
            else:
                dirs.append([r])
        for dg in dirs:
            th0, _, u0, n0 = dg[0][0]
            dg = sorted(dg, key=lambda r: n0[0] * r[1]["a"][0] + n0[1] * r[1]["a"][1])
            last = None
            for k, s in dg:
                c = n0[0] * s["a"][0] + n0[1] * s["a"][1]
                if last is not None and c - last <= off_tol:
                    groups[-1].append((k, s))
                else:
                    groups.append([(k, s)])
                last = c
        for g in groups:
            th, c, u, n = g[0][0]
            iv = []
            for _, s in g:
                t1 = u[0] * s["a"][0] + u[1] * s["a"][1]
                t2 = u[0] * s["b"][0] + u[1] * s["b"][1]
                iv.append((min(t1, t2), max(t1, t2), s))
            iv.sort(key=lambda r: (r[0], r[1]))
            cur = [iv[0][0], iv[0][1], [iv[0][2]]]
            runs = []
            for t0, t1, s in iv[1:]:
                if t0 <= cur[1] + gap:
                    cur[1] = max(cur[1], t1)
                    cur[2].append(s)
                else:
                    runs.append(cur)
                    cur = [t0, t1, [s]]
            runs.append(cur)
            for t0, t1, ss in runs:
                if len(ss) == 1:
                    keep.append(ss[0])
                    continue
                cc = sum(n[0] * s["a"][0] + n[1] * s["a"][1] for s in ss) / len(ss)
                a = (u[0] * t0 + n[0] * cc, u[1] * t0 + n[1] * cc)
                b = (u[0] * t1 + n[0] * cc, u[1] * t1 + n[1] * cc)
                first = min(ss, key=lambda s: s["id"])
                keep.append(dict(first, a=a, b=b, merged_ids=sorted(s["id"] for s in ss)))
                log.append({"code": "HEAL_MERGE", "layer": lay, "kept_id": first["id"],
                            "source_ids": sorted(s["id"] for s in ss), "pieces": len(ss)})
    return keep, log


def _seg_dist(px, py, a, b):
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _ray_hit(p, d, a, b):
    """distance s >= 0 along ray p + s d to segment ab, or None."""
    (x1, y1), (x2, y2) = a, b
    ex, ey = x2 - x1, y2 - y1
    den = d[0] * ey - d[1] * ex
    if abs(den) < 1e-12:
        return None
    wx, wy = x1 - p[0], y1 - p[1]
    s = (wx * ey - wy * ex) / den
    t = (wx * d[1] - wy * d[0]) / den
    if s < 0 or t < -1e-9 or t > 1 + 1e-9:
        return None
    return s


def extend_dangling(segments, layers, targets, *, snap, eps):
    """targets: extra edges [((x1, y1), (x2, y2)), ...] (column box sides). Returns (segments', log)."""
    cell = max(snap * 4, eps * 10)
    grid = defaultdict(list)
    edges = []
    for s in segments:
        if s["layer"] in layers:
            edges.append((s["a"], s["b"], s["id"]))
    for k, (a, b) in enumerate(targets):
        edges.append((a, b, f"TARGET{k}"))
    for i, (a, b, _) in enumerate(edges):
        x0, x1 = sorted((a[0], b[0]))
        y0, y1 = sorted((a[1], b[1]))
        for gx in range(int(math.floor((x0 - snap) / cell)), int(math.floor((x1 + snap) / cell)) + 1):
            for gy in range(int(math.floor((y0 - snap) / cell)), int(math.floor((y1 + snap) / cell)) + 1):
                grid[(gx, gy)].append(i)

    def near(p):
        return grid.get((int(math.floor(p[0] / cell)), int(math.floor(p[1] / cell))), ())
    out, log = [], []
    for s in segments:
        if s["layer"] not in layers:
            out.append(s)
            continue
        pts = [s["a"], s["b"]]
        moved = False
        for end in (0, 1):
            p, q = pts[end], pts[1 - end]
            cand = [i for i in near(p) if edges[i][2] != s["id"]]
            if any(_seg_dist(p[0], p[1], edges[i][0], edges[i][1]) <= eps for i in cand):
                continue
            L = math.hypot(p[0] - q[0], p[1] - q[1])
            if L <= 0:
                continue
            d = ((p[0] - q[0]) / L, (p[1] - q[1]) / L)
            best = None
            for i in cand:
                h = _ray_hit(p, d, edges[i][0], edges[i][1])
                if h is not None and h <= snap and (best is None or h < best[0]):
                    best = (h, edges[i][2])
            if best:
                pts[end] = (p[0] + d[0] * best[0], p[1] + d[1] * best[0])
                moved = True
                log.append({"code": "HEAL_EXTEND", "id": s["id"], "end": end, "by": best[0], "to": best[1]})
        out.append(dict(s, a=pts[0], b=pts[1]) if moved else s)
    return out, log


def policy_record():
    return {"policy": POLICY_ID, "gap_m": GAP_M, "snap_m": SNAP_M, "ang_tol_rad": ANG_TOL,
            "rule": "merge collinear pieces and duplicates within GAP_M; extend a dangling end to the first line "
                    "within SNAP_M; wider gaps stay open and are reported, never closed by guess"}

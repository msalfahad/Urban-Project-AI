"""CONCRETE STRIP GUARD - a drawn band face is never lost because a member is cast against it.

Why (T-050 trace, general on Kuwait villas): footings and columns on a neighbour side are cast against the plot line, so
the outer face of a perimeter band coincides with member edges. The frozen ledger samples every line at 5 points
(`concrete_completeness._entities`) and removes a line as EXPLAINED_BY_MEMBER when 4 of 5 points touch a member
(`_explained_share`, EXPLAINED_SHARE 0.8), whatever length the members really cover; the face's parallel partner is then
left unpaired (`_parallel_pairs`) and the whole side of the band vanishes with no record. A paired strip is also
measured on the shorter face (paired overlap), so a closed band loses one width per corner.

This module is a NEW method piece beside the frozen builder (concrete_completeness.py is FROZEN and not edited). It is not
wired into any released method. Given the strip builder's input (the straight faces of one layer group, with the frozen
ledger state of each when known) and the member footprints, it reports:

  1. every face pair at a strip width as a strip measured on its CENTRE LINE; strip ends that meet at a corner are
     joined at the centre-line intersection, so a closed ring is measured exactly (corners counted once):
     plan area = sum(centre-line length x width) = outer ring area - inner ring area;
  2. the part of a strip whose centre line lies inside a member footprint (a footing cast against the plot line) is
     HELD STRIP_UNDER_MEMBER with the member ids (the concrete may already be in the member: the reviewer decides);
     the rest is MEASURED. Covered length, never a 0.8 all-or-nothing on 5 sample points;
  3. every face stretch with no partner at a strip width is HELD STRIP_FACE_UNPAIRED with its id, length and reason,
     never silently absent and never 0;
  4. per face the covered-length share (within the explain tolerance of a member edge, or inside a non-footing member)
     next to the frozen 5-point share, and, when the frozen ledger states are given, the frozen view: which faces the
     frozen builder removed and which partner faces it then left unpaired (FROZEN_SILENT_OMISSION).

Rules
  UP-QTY-STATUS-001  every drawn face is reported once: in a strip (MEASURED or HELD under a member), HELD unpaired, or
                     UNSUPPORTED (bad data). Missing data never becomes 0.
  UP-KB-PREC-001     as drawn: lengths and widths come from the drawn faces; the section depth is passed in (schedule),
                     never defaulted here; no depth -> no volume (area only).

Conservation (tests): released + held-under-member centre-line length = the strip centre line; every face length is in
a strip (paired stretch), in a HELD unpaired record or in an UNSUPPORTED record.

Input (drawing units; `unit_m` = metres per drawing unit, e.g. 0.001 for a drawing in mm)
  lines   [{"id", "layer", "a": (x, y), "b": (x, y), "state": frozen ledger state (optional)}]
  members [{"id", "kind": "FOOTING" | "COLUMN" | ..., "poly": [(x, y), ...]}]   closed footprints

Nothing here names a project, a sheet, a layer or a handle.
"""

from __future__ import annotations

import math

METHOD = "CONCRETE_STRIP_GUARD_V1"
RULES = ("UP-QTY-STATUS-001", "UP-KB-PREC-001")
EXPLAIN_TOL_M = 0.03           # as concrete_completeness PROFILE EXPLAIN_TOL_M (a line this close to a member edge)
FROZEN_EXPLAINED_SHARE = 0.8   # as concrete_completeness PROFILE EXPLAINED_SHARE (frozen 5-point rule, for comparison)
FROZEN_SAMPLES = (0.0, 0.25, 0.5, 0.75, 1.0)     # as concrete_completeness._entities
PARALLEL_SIN = 0.035           # as concrete_completeness._parallel_pairs (about 2 degrees)
MIN_STRETCH_M = 1e-4           # face stretches shorter than this are not reported (rounding)
CORNER_SIN = 0.17              # two strips meet at a corner only when their directions differ by more than ~10 deg
REMOVED_STATES = ("EXPLAINED_BY_MEMBER", "CONTEXT_OF_OTHER_SHEET")   # frozen ledger states that leave the strip search


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _pt(p):
    try:
        return len(p) >= 2 and _num(p[0]) and _num(p[1])
    except TypeError:
        return False


def _r(v):
    return round(v, 6)


def _merge(iv):
    out = []
    for a, b in sorted(iv):
        if b - a <= 0:
            continue
        if out and a <= out[-1][1] + 1e-12:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [tuple(x) for x in out]


def _subtract(iv, cut):
    res = []
    cut = _merge(cut)
    for a, b in _merge(iv):
        pieces = [(a, b)]
        for c0, c1 in cut:
            nxt = []
            for x, y in pieces:
                if c1 <= x or c0 >= y:
                    nxt.append((x, y))
                    continue
                if c0 > x:
                    nxt.append((x, c0))
                if c1 < y:
                    nxt.append((c1, y))
            pieces = nxt
        res.extend(pieces)
    return res


def _intersect(iv, other):
    out = []
    for a, b in _merge(iv):
        for c, d in _merge(other):
            lo, hi = max(a, c), min(b, d)
            if hi > lo:
                out.append((lo, hi))
    return _merge(out)


def _total(iv):
    return sum(b - a for a, b in _merge(iv))


def _point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if xc > x:
                inside = not inside
    return inside


def _seg_dist(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - a[0]) * dx + (py - a[1]) * dy) / L2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy)


def _at(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _inside_intervals(a, b, poly):
    """parameter intervals (0..1) of segment a-b strictly inside the polygon."""
    ts = {0.0, 1.0}
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        ex, ey = q[0] - p[0], q[1] - p[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-15:
            continue
        t = ((p[0] - a[0]) * ey - (p[1] - a[1]) * ex) / den
        s = ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / den
        if -1e-12 <= s <= 1 + 1e-12 and 0.0 < t < 1.0:
            ts.add(t)
    ts = sorted(ts)
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        if t1 - t0 < 1e-12:
            continue
        mx, my = _at(a, b, (t0 + t1) / 2)
        if _point_in_poly(mx, my, poly) and min(_seg_dist(mx, my, poly[i], poly[(i + 1) % n])
                                                 for i in range(n)) > 1e-9:
            out.append((t0, t1))
    return _merge(out)


def _near_interval(a, b, p, q, tol):
    """parameter interval (0..1) of segment a-b within tol of segment p-q (distance along a line is convex)."""
    f = lambda t: _seg_dist(*_at(a, b, t), p, q)          # noqa: E731
    lo, hi = 0.0, 1.0
    for _ in range(100):                                 # ternary search for the minimum
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if f(m1) <= f(m2):
            hi = m2
        else:
            lo = m1
    tm = (lo + hi) / 2
    if f(tm) > tol:
        return None

    def edge(inside, outside):
        if f(outside) <= tol:
            return outside
        for _ in range(60):
            mid = (inside + outside) / 2
            if f(mid) <= tol:
                inside = mid
            else:
                outside = mid
        return inside
    return (edge(tm, 0.0), edge(tm, 1.0))


def _face_cover(a, b, members, tol):
    """intervals (0..1) of a face explained by members, as the frozen rule's geometry but by length:
    within tol of a member edge, or inside a member that is not a FOOTING (a band line inside a footing is not it)."""
    iv = []
    for m in members:
        poly = m["poly"]
        for i in range(len(poly)):
            r = _near_interval(a, b, poly[i], poly[(i + 1) % len(poly)], tol)
            if r:
                iv.append(r)
        if m["kind"] != "FOOTING":
            iv.extend(_inside_intervals(a, b, poly))
    return _merge(iv)


def _sample_share(a, b, members, tol):
    """the frozen 5-point share (concrete_completeness._explained_share geometry), for comparison only."""
    hit = 0
    for t in FROZEN_SAMPLES:
        x, y = _at(a, b, t)
        ok = False
        for m in members:
            poly = m["poly"]
            if any(_seg_dist(x, y, poly[i], poly[(i + 1) % len(poly)]) <= tol for i in range(len(poly))):
                ok = True
            elif m["kind"] != "FOOTING" and _point_in_poly(x, y, poly):
                ok = True
            if ok:
                break
        hit += ok
    return hit / len(FROZEN_SAMPLES)


def _pairs(faces, wmin, wmax):
    """greedy pairing by smallest width: [(i, j, width, (s0, s1) in face i's metres, (u0, u1) in face j's metres)].
    A face may pair with several partners on disjoint stretches; a stretch is used once."""
    cand = []
    for i, fa in enumerate(faces):
        for j in range(i + 1, len(faces)):
            fb = faces[j]
            if abs(fa["ux"] * fb["uy"] - fa["uy"] * fb["ux"]) > PARALLEL_SIN:
                continue
            ax, ay = fa["a"]
            w = abs((fb["a"][0] - ax) * fa["uy"] - (fb["a"][1] - ay) * fa["ux"])
            w2 = abs((fb["b"][0] - ax) * fa["uy"] - (fb["b"][1] - ay) * fa["ux"])
            w = (w + w2) / 2
            if not (wmin - 1e-9 <= w <= wmax + 1e-9):
                continue
            s0 = (fb["a"][0] - ax) * fa["ux"] + (fb["a"][1] - ay) * fa["uy"]
            s1 = (fb["b"][0] - ax) * fa["ux"] + (fb["b"][1] - ay) * fa["uy"]
            lo, hi = max(0.0, min(s0, s1)), min(fa["L"], max(s0, s1))
            if hi - lo > MIN_STRETCH_M:
                cand.append((round(w, 9), fa["id_sort"], fb["id_sort"], i, j, w))
    cand.sort()
    used = {i: [] for i in range(len(faces))}
    out = []
    for _, _, _, i, j, w in cand:
        fa, fb = faces[i], faces[j]
        ax, ay = fa["a"]
        s0 = (fb["a"][0] - ax) * fa["ux"] + (fb["a"][1] - ay) * fa["uy"]
        s1 = (fb["b"][0] - ax) * fa["ux"] + (fb["b"][1] - ay) * fa["uy"]
        same = s1 >= s0                                  # face j runs the same way as face i
        lo, hi = max(0.0, min(s0, s1)), min(fa["L"], max(s0, s1))
        to_j = lambda s: (s - s0) if same else (s0 - s)  # noqa: E731  face i metres -> face j metres
        to_i = lambda u: (s0 + u) if same else (s0 - u)  # noqa: E731
        used_j_on_i = [tuple(sorted((to_i(u0), to_i(u1)))) for u0, u1 in used[j]]
        free = _subtract([(lo, hi)], used[i] + used_j_on_i)
        for x0, x1 in free:
            if x1 - x0 <= MIN_STRETCH_M:
                continue
            used[i].append((x0, x1))
            used[j].append(tuple(sorted((to_j(x0), to_j(x1)))))
            out.append((i, j, w, (x0, x1), same, s0))
    return out, used


def _line_x(p, u, q, v):
    """intersection of lines p + s u and q + t v -> (s, t) or None when parallel."""
    den = u[0] * v[1] - u[1] * v[0]
    if abs(den) < CORNER_SIN:
        return None
    dx, dy = q[0] - p[0], q[1] - p[1]
    return (dx * v[1] - dy * v[0]) / den, (dx * u[1] - dy * u[0]) / den


def _join_corners(strips):
    """extend strip ends that meet at a corner to their centre-line intersection (each end joined at most once)."""
    ends = []
    for k, s in enumerate(strips):
        for e in (0, 1):
            ends.append((k, e))
    best = []
    for x in range(len(strips)):
        for y in range(x + 1, len(strips)):
            sa, sb = strips[x], strips[y]
            r = _line_x(sa["p0"], sa["u"], sb["p0"], sb["u"])
            if r is None:
                continue
            s, t = r
            reach = max(sa["width"], sb["width"])
            # the intersection must lie near one END of each strip (not in its middle: a T joint is not a corner)
            da = min((abs(s - 0.0), 0), (abs(s - sa["len"]), 1))
            db = min((abs(t - 0.0), 0), (abs(t - sb["len"]), 1))
            if da[0] <= reach and db[0] <= reach:
                best.append((da[0] + db[0], x, da[1], s, y, db[1], t))
    best.sort()
    taken = set()
    for _, x, ex, s, y, ey, t in best:
        if (x, ex) in taken or (y, ey) in taken:
            continue
        taken.update(((x, ex), (y, ey)))
        strips[x]["join"][ex] = (y, s)
        strips[y]["join"][ey] = (x, t)
    for st in strips:
        lo = st["join"][0][1] if st["join"][0] else 0.0
        hi = st["join"][1][1] if st["join"][1] else st["len"]
        st["c0"], st["c1"] = min(lo, hi), max(lo, hi)


def _cycles(strips):
    """strips whose both ends are joined, in closed chains -> list of index sets (closed rings)."""
    seen, rings = set(), []
    for k, st in enumerate(strips):
        if k in seen or not (st["join"][0] and st["join"][1]):
            continue
        comp, stack, ok = set(), [k], True
        while stack:
            n = stack.pop()
            if n in comp:
                continue
            comp.add(n)
            for j in strips[n]["join"]:
                if not j:
                    ok = False
                    continue
                stack.append(j[0])
        seen |= comp
        if ok:
            rings.append(sorted(comp))
    return rings


def guard(lines, members, unit_m, strip_width_m, explain_tol_m=EXPLAIN_TOL_M, section_depth_m=None,
          frozen_strip_length_m=None):
    """-> {"strips": [...], "held": [...], "unsupported": [...], "faces": [...], "rings": [...], "frozen_view": {...},
    "totals": {...}}. strip_width_m = (wmin, wmax) in metres (a profile's STRIP_WIDTH_M or a schedule width band);
    never defaulted here. Every face appears once in a strip, a HELD record or an UNSUPPORTED record."""
    res = {"method": METHOD, "rules": list(RULES), "strips": [], "held": [], "unsupported": [], "faces": [],
           "rings": [], "frozen_view": None, "totals": None}
    lines = list(lines or [])
    ok_unit = _num(unit_m) and unit_m > 0
    ok_w = (strip_width_m is not None and len(strip_width_m) == 2 and all(_num(w) for w in strip_width_m)
            and 0 < strip_width_m[0] <= strip_width_m[1])
    if not (ok_unit and ok_w):
        reason = "UNIT_UNKNOWN" if not ok_unit else "STRIP_WIDTH_UNKNOWN"
        res["unsupported"] = [{"status": "UNSUPPORTED", "reason": reason, "id": ln.get("id"), "method": METHOD}
                              for ln in lines]
        return res
    if section_depth_m is not None and not (_num(section_depth_m) and section_depth_m > 0):
        raise ValueError("section_depth_m must be a positive number or None")
    wmin, wmax = strip_width_m
    tol = explain_tol_m
    mem = []
    for k, m in enumerate(members or []):
        poly = m.get("poly") or []
        if len(poly) < 3 or not all(_pt(p) for p in poly):
            res["unsupported"].append({"status": "UNSUPPORTED", "reason": "BAD_MEMBER_DATA", "id": m.get("id"),
                                       "kind": m.get("kind"), "method": METHOD})
            continue
        mem.append({"id": m.get("id", f"member{k}"), "kind": (m.get("kind") or "UNKNOWN").upper(),
                    "poly": [(p[0] * unit_m, p[1] * unit_m) for p in poly]})
    faces = []
    for k, ln in enumerate(lines):
        a, b = ln.get("a"), ln.get("b")
        lid = ln.get("id", f"line{k}")
        if not (_pt(a) and _pt(b)) or math.dist(a[:2], b[:2]) * unit_m <= MIN_STRETCH_M:
            res["unsupported"].append({"status": "UNSUPPORTED", "reason": "BAD_LINE_DATA", "id": lid,
                                       "layer": ln.get("layer"), "method": METHOD})
            continue
        A, B = (a[0] * unit_m, a[1] * unit_m), (b[0] * unit_m, b[1] * unit_m)
        L = math.dist(A, B)
        faces.append({"id": lid, "id_sort": str(lid), "layer": ln.get("layer"), "state": ln.get("state"),
                      "a": A, "b": B, "L": L, "ux": (B[0] - A[0]) / L, "uy": (B[1] - A[1]) / L})
    # 4. per face: covered length vs the frozen 5-point share
    for f in faces:
        cov = _face_cover(f["a"], f["b"], mem, tol)
        share = _total(cov)
        five = _sample_share(f["a"], f["b"], mem, tol)
        f["covered_share"] = share
        res["faces"].append({"id": f["id"], "layer": f["layer"], "length_m": _r(f["L"]),
                             "covered_length_m": _r(share * f["L"]), "covered_share": _r(share),
                             "frozen_5pt_share": five, "frozen_rule_explained": five >= FROZEN_EXPLAINED_SHARE,
                             "frozen_state": f["state"]})
    # 1. pairs -> strips on the centre line
    pairs, used = _pairs(faces, wmin, wmax)
    strips = []
    for i, j, w, (x0, x1), same, s0 in pairs:
        fa, fb = faces[i], faces[j]
        ax, ay = fa["a"]
        side = (fb["a"][0] - ax) * -fa["uy"] + (fb["a"][1] - ay) * fa["ux"]     # left (+) or right (-) of face i
        nx, ny = -fa["uy"] * math.copysign(w / 2, side), fa["ux"] * math.copysign(w / 2, side)
        p0 = (ax + fa["ux"] * x0 + nx, ay + fa["uy"] * x0 + ny)
        strips.append({"faces": (fa["id"], fb["id"]), "fi": i, "fj": j, "width": w, "p0": p0,
                       "u": (fa["ux"], fa["uy"]), "len": x1 - x0, "join": [None, None], "x": (x0, x1),
                       "same": same, "s0": s0})
    _join_corners(strips)
    # a joined corner: the face stretches beyond the paired overlap, up to one width, are the corner's own faces
    paired = {i: list(v) for i, v in used.items()}
    corner = {i: [] for i in range(len(faces))}
    for st in strips:
        x0, x1 = st["x"]
        to_j = (lambda s, st=st: (s - st["s0"]) if st["same"] else (st["s0"] - s))
        for e, (lo, hi) in ((0, (x0 - st["width"] - 1e-6, x0)), (1, (x1, x1 + st["width"] + 1e-6))):
            if not st["join"][e]:
                continue
            fi, fj = st["fi"], st["fj"]
            corner[fi].extend(_intersect([(lo, hi)], [(0.0, faces[fi]["L"])]))
            corner[fj].extend(_intersect([tuple(sorted((to_j(lo), to_j(hi))))], [(0.0, faces[fj]["L"])]))
    for i in corner:
        corner[i] = _subtract(corner[i], used[i])
        used[i] = used[i] + corner[i]
        res["faces"][i]["in_strip_length_m"] = _r(_total(used[i]))
        res["faces"][i]["corner_length_m"] = _r(_total(corner[i]))
    rings = _cycles(strips)
    in_ring = {k for r in rings for k in r}
    for k, st in enumerate(strips):
        c0, c1 = st["c0"], st["c1"]
        a = (st["p0"][0] + st["u"][0] * c0, st["p0"][1] + st["u"][1] * c0)
        b = (st["p0"][0] + st["u"][0] * c1, st["p0"][1] + st["u"][1] * c1)
        L = c1 - c0
        under = {}
        for m in mem:
            for t0, t1 in _inside_intervals(a, b, m["poly"]):
                under.setdefault(m["id"], []).append((t0 * L, t1 * L))
        all_under = _merge([iv for v in under.values() for iv in v])
        free = _subtract([(0.0, L)], all_under)
        base = {"kind": "BAND_STRIP", "faces": list(st["faces"]), "layers": sorted({str(faces[st["fi"]]["layer"]),
                                                                               str(faces[st["fj"]]["layer"])}),
                "strip_width_m": _r(st["width"]), "ring": next((n for n, r in enumerate(rings) if k in r), None),
                "corner_joined": [bool(st["join"][0]), bool(st["join"][1])], "method": METHOD, "rules": list(RULES)}
        for s0, s1 in free:
            if s1 - s0 <= MIN_STRETCH_M:
                continue
            rec = dict(base, status="MEASURED", from_m=_r(s0), to_m=_r(s1), strip_length_m=_r(s1 - s0),
                       area_m2=_r((s1 - s0) * st["width"]))
            if section_depth_m is not None:
                rec["section_depth_m"] = section_depth_m
                rec["volume_m3"] = _r((s1 - s0) * st["width"] * section_depth_m)
            res["strips"].append(rec)
        for s0, s1 in all_under:
            if s1 - s0 <= MIN_STRETCH_M:
                continue
            mids = sorted(str(mid) for mid, iv in under.items() if _intersect(iv, [(s0, s1)]))
            kinds = sorted({m["kind"] for m in mem if str(m["id"]) in mids})
            res["held"].append(dict(base, status="HELD", reason="STRIP_UNDER_MEMBER", members=mids,
                                    member_kinds=kinds, from_m=_r(s0), to_m=_r(s1), strip_length_m=_r(s1 - s0),
                                    area_m2=_r((s1 - s0) * st["width"])))
    for n, r in enumerate(rings):
        res["rings"].append({"ring": n, "strips": len(r), "closed": True,
                             "centre_line_m": _r(sum(strips[k]["c1"] - strips[k]["c0"] for k in r)),
                             "area_m2": _r(sum((strips[k]["c1"] - strips[k]["c0"]) * strips[k]["width"] for k in r))})
    # 3. face stretches with no partner
    for i, f in enumerate(faces):
        for s0, s1 in _subtract([(0.0, f["L"])], used[i]):
            if s1 - s0 <= MIN_STRETCH_M:
                continue
            res["held"].append({"status": "HELD", "reason": "STRIP_FACE_UNPAIRED", "id": f["id"], "layer": f["layer"],
                                "from_m": _r(s0), "to_m": _r(s1), "length_m": _r(s1 - s0), "face_length_m": _r(f["L"]),
                                "detail": "no parallel face at a strip width "
                                          f"{wmin:g}-{wmax:g} m along this stretch",
                                "frozen_state": f["state"], "method": METHOD, "rules": list(RULES)})
    # frozen view: what the frozen builder keeps once the ledger removed its explained faces
    if any(f["state"] for f in faces):
        removed = [i for i, f in enumerate(faces) if f["state"] in REMOVED_STATES]
        kept = [f for f in faces if f["state"] not in REMOVED_STATES]
        kpairs, kused = _pairs(kept, wmin, wmax)
        kept_overlap = sum(x1 - x0 for _, _, _, (x0, x1), _, _ in kpairs)
        omissions = []
        for i in removed:
            omissions.append({"status": "HELD", "reason": "FROZEN_SILENT_OMISSION", "id": faces[i]["id"],
                              "frozen_state": faces[i]["state"], "length_m": _r(faces[i]["L"]),
                              "detail": "removed by the frozen ledger before the strip search",
                              "paired_here_m": _r(_total(used[i])), "method": METHOD})
        for k, f in enumerate(kept):
            i = faces.index(f)
            lost = _intersect(_subtract([(0.0, f["L"])], kused[k]), paired[i])
            if _total(lost) > MIN_STRETCH_M:
                omissions.append({"status": "HELD", "reason": "FROZEN_SILENT_OMISSION", "id": f["id"],
                                  "frozen_state": f["state"], "length_m": _r(_total(lost)),
                                  "detail": "its strip partner was removed by the frozen ledger: left unpaired",
                                  "paired_here_m": _r(_total(used[i])), "method": METHOD})
        # paired overlap (shorter face) vs centre line, on the strips whose two faces the frozen ledger kept
        kept_ids = {f["id"] for f in kept}
        basis = sum((st["c1"] - st["c0"]) - st["len"] for st in strips if set(st["faces"]) <= kept_ids)
        res["frozen_view"] = {"kept_overlap_length_m": _r(kept_overlap), "omissions": omissions,
                              "corner_basis_loss_m": _r(basis),
                              "frozen_strip_length_m": frozen_strip_length_m}
    meas = sum(s["strip_length_m"] for s in res["strips"])
    under = sum(h["strip_length_m"] for h in res["held"] if h["reason"] == "STRIP_UNDER_MEMBER")
    res["totals"] = {
        "released_length_m": _r(meas), "held_under_member_length_m": _r(under),
        "strip_centre_line_m": _r(meas + under),
        "released_area_m2": _r(sum(s["area_m2"] for s in res["strips"])),
        "held_under_member_area_m2": _r(sum(h["area_m2"] for h in res["held"] if h["reason"] == "STRIP_UNDER_MEMBER")),
        "released_volume_m3": (_r(sum(s["volume_m3"] for s in res["strips"])) if section_depth_m is not None
                               else None),
        "held_unpaired_face_length_m": _r(sum(h["length_m"] for h in res["held"]
                                              if h["reason"] == "STRIP_FACE_UNPAIRED")),
        "n_strips": len(res["strips"]), "n_held": len(res["held"]), "n_unsupported": len(res["unsupported"]),
        "n_rings": len(rings), "in_ring_strips": len(in_ring)}
    return res

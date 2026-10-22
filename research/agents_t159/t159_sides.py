"""T-159 facade sides (research only, not a method, not wired): split a facade outline into SIDES and give each side
its plan length, its facing and the openings on it.

A side is a maximal run of the outline between two corners: consecutive straight edges that lie on one line
(direction within ANG_TOL_DEG and offset within OFF_TOL_M), or consecutive arc edges of one circle (centre and radius
within OFF_TOL_M). The run INCLUDES its openings (UP-FACADE-001: the outer face is closed across each opening), so the
sides add back to the outline run exactly. Arc sides carry their true arc length (r x sweep), never the chord.

Facing: the outward normal of the side, named by the nearest of four plan axes given as compass names by the caller
(the drawing's north arrow decides them; nothing is assumed here). A side shorter than RETURN_MAX_M is a RETURN (a
jog or reveal-like step between two faces): listed on its own, never merged into a neighbour, never dropped.

Pure functions, metres in, metres out. Used by t159_alsenan.py (development villa) and tested by check_t159.py on a
hand-calculated non-Alsenan house."""
import math

ANG_TOL_DEG = 0.5
OFF_TOL_M = 0.002
RETURN_MAX_M = 0.30


def _len(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def _dir(a, b):
    L = _len(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L) if L > 0 else (0.0, 0.0)


def signed_area(edges):
    """shoelace over the edge start points (arcs flattened by their ends: the sign is what is used)."""
    s = 0.0
    for e in edges:
        s += e["a"][0] * e["b"][1] - e["b"][0] * e["a"][1]
    return s / 2.0


def _same_line(e, f):
    if not (e["straight"] and f["straight"]):
        return False
    u, v = _dir(e["a"], e["b"]), _dir(f["a"], f["b"])
    if u[0] * v[0] + u[1] * v[1] < math.cos(math.radians(ANG_TOL_DEG)):
        return False
    # offset of f's end from e's line
    d = (f["b"][0] - e["a"][0]) * u[1] - (f["b"][1] - e["a"][1]) * u[0]
    return abs(d) <= OFF_TOL_M


def _same_circle(e, f):
    if e["straight"] or f["straight"]:
        return False
    return _len(e["c"], f["c"]) <= OFF_TOL_M and abs(e["r"] - f["r"]) <= OFF_TOL_M


def split_sides(edges, axes, drop=()):
    """edges: the closed outline in order, each {"a", "b", "len_m", "straight", ("c", "r" for arcs), "opening"}.
    axes: {"+x": name, "-x": name, "+y": name, "-y": name} compass names of the outward normals along the plan axes.
    drop: indexes of edges that are not building faces (passage mouths, owner Q-67 A): they end a side and are
    reported separately. -> list of sides {"edges", "len_m", "kind": STRAIGHT | ARC | RETURN, "facing", "normal",
    "openings": [(opening id, width m)]}; sides keep outline order."""
    n = len(edges)
    if n < 3:
        return []
    ccw = signed_area(edges) > 0
    drop = set(drop)
    # start at a corner so a side does not wrap across the start
    start = 0
    for i in range(n):
        p, e = edges[i - 1], edges[i]
        if (i - 1) % n in drop or i in drop or not (_same_line(p, e) or _same_circle(p, e)):
            start = i
            break
    order = [(start + j) % n for j in range(n)]
    groups, cur = [], []
    for i in order:
        if i in drop:
            if cur:
                groups.append(cur)
            groups.append([i])
            cur = []
            continue
        if cur and (_same_line(edges[cur[-1]], edges[i]) or _same_circle(edges[cur[-1]], edges[i])):
            cur.append(i)
        else:
            if cur:
                groups.append(cur)
            cur = [i]
    if cur:
        groups.append(cur)
    sides = []
    for g in groups:
        es = [edges[i] for i in g]
        L = sum(e["len_m"] for e in es)
        if g[0] in drop:
            kind = "NOT_A_FACE"
        elif not es[0]["straight"]:
            kind = "ARC"
        elif L < RETURN_MAX_M:
            kind = "RETURN"
        else:
            kind = "STRAIGHT"
        if es[0]["straight"]:
            u = _dir(es[0]["a"], es[-1]["b"])
            nrm = (u[1], -u[0]) if ccw else (-u[1], u[0])
        else:
            # arc: the normal at its middle, pointing away from the centre when the arc bulges out
            m = es[len(es) // 2]
            mid = ((m["a"][0] + m["b"][0]) / 2, (m["a"][1] + m["b"][1]) / 2)
            u = _dir(es[0]["a"], es[-1]["b"])
            out = (u[1], -u[0]) if ccw else (-u[1], u[0])
            v = _dir(m["c"], mid)
            nrm = v if v[0] * out[0] + v[1] * out[1] >= 0 else (-v[0], -v[1])
        if abs(nrm[0]) >= abs(nrm[1]):
            facing = axes["+x"] if nrm[0] > 0 else axes["-x"]
        else:
            facing = axes["+y"] if nrm[1] > 0 else axes["-y"]
        ops = {}
        for e in es:
            if e.get("opening"):
                ops[e["opening"]] = ops.get(e["opening"], 0.0) + e["len_m"]
        sides.append({"edges": g, "len_m": L, "kind": kind, "facing": facing, "normal": nrm,
                      "a": es[0]["a"], "b": es[-1]["b"],
                      "openings": sorted((k, round(v, 6)) for k, v in ops.items()),
                      "radius_m": None if es[0]["straight"] else es[0]["r"]})
    return sides


def name_sides(sides):
    """N / S / E / W style names: facing + sequence in outline order, returns and non-faces numbered with them."""
    seq = {}
    for s in sides:
        seq[s["facing"]] = seq.get(s["facing"], 0) + 1
        s["name"] = "%s-%d" % (s["facing"], seq[s["facing"]])
    return sides


def _poly_from_edges(edges, step_m=0.05):
    from shapely.geometry import Polygon
    pts = []
    for e in edges:
        if e["straight"]:
            pts.append(tuple(e["a"]))
        else:
            c, r = e["c"], e["r"]
            a0 = math.atan2(e["a"][1] - c[1], e["a"][0] - c[0])
            a1 = math.atan2(e["b"][1] - c[1], e["b"][0] - c[0])
            sweep = e["len_m"] / r
            # walk from a to b the way of the edge's own sweep (sign from the shorter consistent turn)
            d = (a1 - a0) % (2 * math.pi)
            sgn = 1.0 if abs(d - sweep) < abs((2 * math.pi - d) - sweep) else -1.0
            n = max(2, int(math.ceil(sweep * r / step_m)))
            for i in range(n):
                t = a0 + sgn * sweep * i / n
                pts.append((c[0] + r * math.cos(t), c[1] + r * math.sin(t)))
    return Polygon(pts).buffer(0)


def against_upper(side, edges, upper_edges, eps_m=0.01):
    """split one STRAIGHT side of a floor by what stands above it on the next floor's outline (same plan frame):
    FLUSH (the upper outline runs on the same line: the face continues up), COVERED (the upper plate lies over the
    face: an upper floor or slab over it), EDGE (nothing above: the face ends at this floor's roof edge / parapet).
    -> {"FLUSH": m, "COVERED": m, "EDGE": m}, re-adding to the side length; an arc side -> None (read by hand)."""
    from shapely.geometry import LineString
    if side.get("radius_m") is not None:
        return None
    up = _poly_from_edges(upper_edges)
    me = _poly_from_edges(edges)
    a, b = side["a"], side["b"]
    seg = LineString([a, b])
    L = seg.length
    if L <= 0:
        return {"FLUSH": 0.0, "COVERED": 0.0, "EDGE": 0.0}
    # FLUSH: overlap of the side with upper outline edges on the same line (parallel, offset <= eps), by projection
    ua = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    spans = []
    for e in upper_edges:
        if not e["straight"]:
            continue
        p, q = e["a"], e["b"]
        Le = _len(p, q)
        if Le <= 0:
            continue
        v = ((q[0] - p[0]) / Le, (q[1] - p[1]) / Le)
        if abs(ua[0] * v[1] - ua[1] * v[0]) > math.sin(math.radians(ANG_TOL_DEG)):
            continue
        if abs((p[0] - a[0]) * ua[1] - (p[1] - a[1]) * ua[0]) > eps_m:
            continue
        t0 = (p[0] - a[0]) * ua[0] + (p[1] - a[1]) * ua[1]
        t1 = (q[0] - a[0]) * ua[0] + (q[1] - a[1]) * ua[1]
        lo, hi = max(0.0, min(t0, t1)), min(L, max(t0, t1))
        if hi > lo:
            spans.append((lo, hi))
    spans.sort()
    flush, cur = 0.0, None
    for lo, hi in spans:
        if cur is None or lo > cur[1]:
            if cur:
                flush += cur[1] - cur[0]
            cur = [lo, hi]
        else:
            cur[1] = max(cur[1], hi)
    if cur:
        flush += cur[1] - cur[0]
    # a point a little inside the floor from the face: is the upper plate over it?
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    n = side["normal"]
    inn = LineString([(a[0] - n[0] * 4 * eps_m, a[1] - n[1] * 4 * eps_m),
                      (b[0] - n[0] * 4 * eps_m, b[1] - n[1] * 4 * eps_m)])
    over = inn.intersection(up).length
    covered = max(0.0, over - flush)
    edge = max(0.0, L - flush - covered)
    del u, me
    return {"FLUSH": round(flush, 6), "COVERED": round(covered, 6), "EDGE": round(edge, 6)}


def band_area(length_m, bands):
    """gross face area of one side: sum of length x (top - bottom) over its height bands; any band with an unknown
    level -> None (HELD), never 0."""
    tot = 0.0
    for b in bands:
        if b.get("bottom") is None or b.get("top") is None:
            return None
        h = b["top"] - b["bottom"]
        if h < 0:
            raise ValueError("band top below its bottom")
        tot += length_m * h
    return tot


def house_facade(floors, axes):
    """every side of every floor with its gross face area from levels (metres), generic for any villa.
    floors: bottom-up [{"name", "edges" (the floor's outline, one plan frame for all floors), "outside": outside
    ground level in front of the lowest floor's faces, "floor": this floor's level, "edge_top": top of a face that
    is a roof edge (roof + parapet), "next_floor": the next floor's level (None on the top floor), "lower_roof":
    level of the lower roof a face of this floor stands on (default: "floor"), "arc_above": {side name: FLUSH |
    COVERED | EDGE} for arcs}]. A level given as None is unknown: the band is HELD (None), never 0.
    -> [{"floor", "side", "len_m", "kind", "facing", "portions": [(cls, len, bottom, top)], "area_m2" or None}]"""
    out = []
    for i, fl in enumerate(floors):
        up = floors[i + 1] if i + 1 < len(floors) else None
        dn = floors[i - 1] if i > 0 else None
        for s in name_sides(split_sides(fl["edges"], axes)):
            if s["kind"] == "ARC":
                a = {"FLUSH": 0.0, "COVERED": 0.0, "EDGE": 0.0}
                a[(fl.get("arc_above") or {}).get(s["name"], "EDGE")] = s["len_m"]
            elif up is None:
                a = {"FLUSH": 0.0, "COVERED": 0.0, "EDGE": s["len_m"]}
            else:
                a = against_upper(s, fl["edges"], up["edges"])
            parts = []
            for cls in ("FLUSH", "COVERED", "EDGE"):
                L = a[cls]
                if L <= 1e-9:
                    continue
                top = fl["edge_top"] if cls == "EDGE" else fl.get("next_floor")
                if dn is None:
                    parts.append((cls, L, fl.get("outside"), top))
                else:
                    b = against_upper(s, fl["edges"], dn["edges"]) if s["kind"] != "ARC" else None
                    if b is None:
                        parts.append((cls, L, fl.get("floor"), top))
                    elif sum(1 for v in a.values() if v > 1e-9) > 1 and sum(1 for v in b.values() if v > 1e-9) > 1:
                        # split above AND below: where the two splits fall along the side is not compared here ->
                        # HELD (no area), never a proportional guess
                        parts.append((cls + "/SPLIT_BOTH_WAYS", L, None, top))
                    else:
                        # one of the two splits is the whole side: the product is exact
                        for bc, bl in b.items():
                            if bl <= 1e-9:
                                continue
                            bot = fl.get("lower_roof", fl.get("floor")) if bc == "COVERED" else fl.get("floor")
                            parts.append((cls + "/" + bc, L * bl / s["len_m"], bot, top))
            area = 0.0
            for _, L, bot, top in parts:
                if bot is None or top is None:
                    area = None
                    break
                if top < bot:
                    raise ValueError("face top below its bottom on %s %s" % (fl["name"], s["name"]))
                area += L * (top - bot)
            out.append({"floor": fl["name"], "side": s["name"], "len_m": s["len_m"], "kind": s["kind"],
                        "facing": s["facing"], "portions": parts, "area_m2": area})
    return out

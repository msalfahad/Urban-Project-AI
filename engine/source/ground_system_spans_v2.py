"""GROUND_SYSTEM_SPANS_V2 - ground-beam span splitter and strap measurement, face to face (generic; stdlib only).

A NEW module beside the frozen S5 chain (ground_beam_network V1 bands -> research span register -> ground_system_rebar
S5). It never edits or imports the frozen S5 rebar module and changes no released quantity: it produces span and strap
length records that a later integration (lane I) may wire in.

It corrects the three span defects the T-138 hand ledger found in the frozen S5 register:

1. SUPPORT_ON_BAND: every support outline drawn ON a straight band (positive overlap with the band strip, full or
   partial width) splits the band. A band that runs across a founded column is two spans, not one.
2. FACE_TO_FACE: a span is measured between the support faces along the band axis (the extent of the support outline
   clipped to the band strip), never "centreline minus an assumed column size"; a support whose edge is collinear with
   a band face is handled like any other (the clip is exact).
3. STRAP_AXIS: an oblique strap is measured along its own axis between the faces of the two footings it joins (where
   the strap centreline leaves one footing outline and enters the other), never as the gap between the footings'
   projections on the axis (that is shorter for an oblique strap).

Inputs (drawing units; ``units`` "mm" or "m"; every output length is in metres):
  bands     [{band_id, u: (ux, uy) unit axis, lo_off, hi_off (offsets of the two faces along n = (-uy, ux)),
              t0, t1 (band extent along u), handles: [...], kind: "STRAIGHT" (default) | "ARC"}]
            (the ground_beam_network.pair_straight band shape; an ARC band is listed UNSUPPORTED, never measured);
  supports  [{support_id, kind: "COLUMN" | "FOOTING", polygon: [(x, y), ...], handles: [...]}];
  classes   optional length classes of the project's ground-beam sections, e.g. the printed titles
            [{"detail_id": "GT5M", "op": ">", "limit_m": 5.0}, {"detail_id": "LT5M", "op": "<", "limit_m": 5.0}, ...].

Rules:
  * URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1 (ground beams only, never STRAP): length from the bound plan band,
    four bases stored apart: centreline (support reference to support reference), clear concrete, support face to
    face, bar straight run lower bound (= face to face; development / laps / hooks are not in it).
  * A band end is a node: COLUMN (a column outline at the end), BEAM_JUNCTION (another, non-parallel band at the end;
    when the band's own faces run past the other band's face, the junction zone is cut off), FOOTING_FACE (a free band
    end lying over a footing outline ends at the footing face) or FREE_END. A span with a FREE_END is HELD.
  * Bands crossing or meeting a band mid-span do not split it (they are listed as intermediate); a footing under the
    middle of a band without a column on it does not split it either (listed as FOOTING_UNDER_SPAN, a flag).
  * Length class: chosen from the span AFTER splitting, on the face-to-face basis; the centreline class is stored
    beside it and a disagreement is flagged. No title applies (e.g. exactly on a "more than" / "less than" limit) ->
    both neighbours stay candidates and the class is HELD; never a pick.
  * Straps: no Urban rule or owner answer sets the strap length basis (URBAN-BEAM-TYPE-...@v1 never applies to STRAP),
    so every strap span is HELD with its candidate values stored apart (axis face to face, each edge face to face,
    the S5-style projection gap, footing centre to centre); missing never becomes 0.
"""

from __future__ import annotations

import math

POLICY_ID = "GROUND_SYSTEM_SPANS_V2"
RULE_GB = "URBAN-BEAM-TYPE-FROM-SCHEDULE-LENGTH-FROM-PLAN@v1"
RULE_STATUS = "UP-QTY-STATUS-001"
UNIT_TO_M = {"mm": 0.001, "m": 1.0}
TOL_M = 0.005                     # geometric contact / coincidence tolerance (5 mm), scaled to the drawing units
PARALLEL_SIN = 0.2                # |sin| below this: the other band is a continuation, not a junction
RELEASED, HELD, UNSUPPORTED = "RELEASED", "HELD", "UNSUPPORTED"
NODE_KINDS = ("COLUMN", "BEAM_JUNCTION", "FOOTING_FACE", "GAP_TO_COLUMN", "FREE_END")


class SpanError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------------ geometry
def _dot(p, u):
    return p[0] * u[0] + p[1] * u[1]


def _clip(poly, a, b, c):
    """Sutherland-Hodgman: keep the part of poly with a*x + b*y >= c (convex clip window, any simple subject)."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _clip_strip(poly, u, n, t0, t1, lo, hi):
    """Part of poly inside {t0 <= u.p <= t1, lo <= n.p <= hi}."""
    g = list(poly)
    for a, b, c in ((u[0], u[1], t0), (-u[0], -u[1], -t1), (n[0], n[1], lo), (-n[0], -n[1], -hi)):
        if not g:
            break
        g = _clip(g, a, b, c)
    return g


def _area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2.0 if len(poly) >= 3 else 0.0


def _centroid(poly):
    a = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
            for i in range(len(poly))) / 2.0
    if abs(a) < 1e-12:
        return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))
    cx = sum((poly[i][0] + poly[(i + 1) % len(poly)][0]) *
             (poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1])
             for i in range(len(poly))) / (6 * a)
    cy = sum((poly[i][1] + poly[(i + 1) % len(poly)][1]) *
             (poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1])
             for i in range(len(poly))) / (6 * a)
    return (cx, cy)


def _seg_dist(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
    return math.hypot(p[0] - a[0] - t * vx, p[1] - a[1] - t * vy)


def _segs_intersect(a, b, c, d):
    def orient(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    return (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0)


def _seg_seg_dist(a, b, c, d):
    if _segs_intersect(a, b, c, d):
        return 0.0
    return min(_seg_dist(a, c, d), _seg_dist(b, c, d), _seg_dist(c, a, b), _seg_dist(d, a, b))


def _inside(p, poly):
    x, y = p
    ins = False
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            ins = not ins
    return ins


def _poly_seg_dist(poly, a, b):
    if _inside(a, poly) or _inside(b, poly):
        return 0.0
    return min(_seg_seg_dist(poly[i], poly[(i + 1) % len(poly)], a, b) for i in range(len(poly)))


def _ray_hits(poly, p, d):
    """Parameters s >= 0 where the ray p + s d crosses an edge of poly (d need not be unit)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-12:
            continue
        s = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
        t = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
        if s >= -1e-9 and -1e-9 <= t <= 1 + 1e-9:
            out.append(max(0.0, s))
    return sorted(out)


def _norm(v):
    L = math.hypot(v[0], v[1])
    if L == 0:
        raise SpanError("zero-length axis")
    return (v[0] / L, v[1] / L)


# ------------------------------------------------------------------------------------------------------ inputs
def _check_units(units):
    if units not in UNIT_TO_M:
        raise SpanError(f"units {units!r} not in {sorted(UNIT_TO_M)}")
    return UNIT_TO_M[units]


def _band(b):
    kind = b.get("kind", "STRAIGHT")
    if kind != "STRAIGHT":
        poly = [tuple(map(float, p[:2])) for p in (b.get("polygon") or [])]
        return {"band_id": str(b["band_id"]), "kind": kind, "handles": list(b.get("handles") or []),
                "polygon": poly if len(poly) >= 3 else None}
    if abs(math.hypot(*b["u"]) - 1.0) > 1e-6:
        raise SpanError(f"band {b['band_id']}: axis u must be a unit vector")
    u = _norm(b["u"])
    lo, hi = sorted((float(b["lo_off"]), float(b["hi_off"])))
    t0, t1 = sorted((float(b["t0"]), float(b["t1"])))
    if hi - lo <= 0 or t1 - t0 <= 0:
        raise SpanError(f"band {b['band_id']}: zero width or length")
    return {"band_id": str(b["band_id"]), "u": u, "n": (-u[1], u[0]), "lo": lo, "hi": hi, "t0": t0, "t1": t1,
            "handles": list(b.get("handles") or []), "kind": kind}


def _rect(b, t0=None, t1=None):
    u, n = b["u"], b["n"]
    t0 = b["t0"] if t0 is None else t0
    t1 = b["t1"] if t1 is None else t1
    pt = lambda t, o: (t * u[0] + o * n[0], t * u[1] + o * n[1])  # noqa: E731
    return [pt(t0, b["lo"]), pt(t1, b["lo"]), pt(t1, b["hi"]), pt(t0, b["hi"])]


def _support(s):
    if s.get("kind") not in ("COLUMN", "FOOTING"):
        raise SpanError(f"support {s.get('support_id')}: kind {s.get('kind')!r} not COLUMN / FOOTING")
    poly = [tuple(map(float, p[:2])) for p in s["polygon"]]
    if len(poly) >= 2 and poly[0] == poly[-1]:
        poly = poly[:-1]
    if len(poly) < 3 or _area(poly) <= 0:
        raise SpanError(f"support {s['support_id']}: polygon needs three or more points and an area")
    return {"support_id": str(s["support_id"]), "kind": s["kind"], "polygon": poly,
            "handles": list(s.get("handles") or [])}


# ------------------------------------------------------------------------------------------------------ classes
def length_class(length_m, classes):
    """(candidates, state). A title applies when the length satisfies it strictly ('>' / '<' as printed). None apply
    -> the titles whose limit the length sits on stay candidates, state ON_LIMIT (HELD). Several apply -> all are
    candidates (state CANDIDATES, the detail is not chosen here)."""
    if not classes or length_m is None:
        return [], "NOT_CLASSIFIED"
    hit = [c["detail_id"] for c in classes
           if (c["op"] == ">" and length_m > c["limit_m"] + 1e-9) or (c["op"] == "<" and length_m < c["limit_m"] - 1e-9)]
    if hit:
        return sorted(hit), ("ONE" if len(hit) == 1 else "CANDIDATES")
    on = sorted(c["detail_id"] for c in classes if abs(length_m - c["limit_m"]) <= 1e-9)
    return on, "ON_LIMIT"


# ------------------------------------------------------------------------------------------------------ bands
def _support_interval(b, s, tol):
    """(a, c, width_fraction) of support s on band b (along u), or None when it does not overlap the strip."""
    g = _clip_strip(s["polygon"], b["u"], b["n"], b["t0"], b["t1"], b["lo"], b["hi"])
    if len(g) < 3:
        return None
    ts = [_dot(p, b["u"]) for p in g]
    os_ = [_dot(p, b["n"]) for p in g]
    a, c = min(ts), max(ts)
    across = max(os_) - min(os_)
    if c - a <= tol or across <= tol:
        return None
    return a, c, across / (b["hi"] - b["lo"])


def _junction_interval(b, o, tol):
    """Interval along band b covered by the strip of band o (o extended by tol past its ends), or None."""
    if abs(b["u"][0] * o["u"][1] - b["u"][1] * o["u"][0]) < PARALLEL_SIN:
        return None
    g = _clip_strip(_rect(b), o["u"], o["n"], o["t0"] - tol, o["t1"] + tol, o["lo"], o["hi"])
    if len(g) < 3:
        return None
    ts = [_dot(p, b["u"]) for p in g]
    a, c = min(ts), max(ts)
    if c - a <= tol:
        return None
    return a, c


def _end_edge(b, t):
    u, n = b["u"], b["n"]
    return ((t * u[0] + b["lo"] * n[0], t * u[1] + b["lo"] * n[1]),
            (t * u[0] + b["hi"] * n[0], t * u[1] + b["hi"] * n[1]))


def _touching(b, t, items, tol):
    a, c = _end_edge(b, t)
    return [it for it in items if _poly_seg_dist(it["polygon"], a, c) <= tol]


def _merge(ivs, tol):
    out = []
    for a, c, ref in sorted(ivs):
        if out and a <= out[-1][1] + tol:
            out[-1] = (out[-1][0], max(out[-1][1], c), out[-1][2] + ref)
        else:
            out.append((a, c, list(ref)))
    return out


def _centre_station(b, kind, refs, by_id, bands_by_id, face_t):
    """Support reference station on the band axis (centreline basis)."""
    if kind == "COLUMN" or kind == "FOOTING_FACE":
        cs = [_dot(_centroid(by_id[r]["polygon"]), b["u"]) for r in refs]
        return sum(cs) / len(cs), ("column centroid projected" if kind == "COLUMN" else
                                   "footing outline centroid projected")
    if kind == "BEAM_JUNCTION":
        st = []
        for r in refs:
            o = bands_by_id.get(r)
            if o is None:            # a curved band: no straight centreline to cross
                continue
            mid_o = (o["lo"] + o["hi"]) / 2.0
            den = _dot(b["u"], o["n"])
            if abs(den) < 1e-12:
                continue
            m = (b["lo"] + b["hi"]) / 2.0
            p0 = (m * b["n"][0], m * b["n"][1])        # point on b's centreline at station 0
            st.append((mid_o - _dot(p0, o["n"])) / den)
        if st:
            return sum(st) / len(st), "other band centreline crossing"
    return face_t, "no support centre (free end): the face station"


def _free_end_node(b, t, sign, cols, others, feet, tol, width):
    """Node of a band end that no column or junction zone cuts: a column or another band touching the end edge; else
    a column within one band width of the end (GAP_TO_COLUMN, HELD with candidates); else a footing outline under
    the end (FOOTING_FACE: the end moves to the footing face on the span side); else FREE_END.
    Returns (kind, refs, extra) with extra["t"] = the end station when it moves."""
    tc = _touching(b, t, cols, tol)
    if tc:
        return "COLUMN", sorted(c["support_id"] for c in tc), {}
    tb = _touching(b, t, others, tol)
    if tb:
        return "BEAM_JUNCTION", sorted(o["band_id"] for o in tb), {}
    fh = []
    for f in feet:
        iv = _support_interval(b, f, tol)
        if iv and iv[0] <= t + tol and iv[1] >= t - tol:
            fh.append((iv, f))
    foot_t = (max(iv[1] for iv, _ in fh) if sign == 1 else min(iv[0] for iv, _ in fh)) if fh else None
    a, c = _end_edge(b, t)
    # a column beside the end that reaches past the end station into the span (drawn a little off the band)
    near = []
    for col in cols:
        ts = [_dot(p, b["u"]) for p in col["polygon"]]
        reaches_in = (max(ts) > t + tol) if sign == 1 else (min(ts) < t - tol)
        d = _poly_seg_dist(col["polygon"], a, c)
        if reaches_in and d <= width:
            near.append((d, col))
    if near:
        d, col = min(near, key=lambda z: z[0])
        ts = [_dot(p, b["u"]) for p in col["polygon"]]
        col_face = max(ts) if sign == 1 else min(ts)
        cands = {"band_end": t, f"column_face {col['support_id']}": col_face}
        if foot_t is not None:
            cands["footing_face " + "+".join(sorted(f["support_id"] for _, f in fh))] = foot_t
        return "GAP_TO_COLUMN", [col["support_id"]], {"gap": d, "candidates": cands, "t": t}
    if fh:
        return "FOOTING_FACE", sorted(f["support_id"] for _, f in fh), {"t": foot_t}
    return "FREE_END", [], {}


def split_ground_beams(bands, supports, *, units="mm", classes=None, tol_m=TOL_M):
    """Spans of every straight band, split at every support on it and measured face to face."""
    k = _check_units(units)
    tol = tol_m / k
    B = [_band(b) for b in bands]
    ids = [b["band_id"] for b in B]
    if len(set(ids)) != len(ids):
        raise SpanError(f"band id entered twice: {sorted({i for i in ids if ids.count(i) > 1})}")
    S = [_support(s) for s in supports]
    if len({s["support_id"] for s in S}) != len(S):
        raise SpanError("support id entered twice")
    by_id = {s["support_id"]: s for s in S}
    cols = [s for s in S if s["kind"] == "COLUMN"]
    feet = [s for s in S if s["kind"] == "FOOTING"]
    straight = [b for b in B if b["kind"] == "STRAIGHT"]
    bands_by_id = {b["band_id"]: b for b in straight}
    for b in straight:
        b["polygon"] = _rect(b)
    outlines = straight + [b for b in B if b["kind"] != "STRAIGHT" and b.get("polygon")]
    others = {b["band_id"]: [o for o in outlines if o is not b and (
        o["kind"] != "STRAIGHT" or abs(b["u"][0] * o["u"][1] - b["u"][1] * o["u"][0]) >= PARALLEL_SIN)]
        for b in straight}
    spans, band_rows, unsupported = [], [], []
    for b in B:
        if b["kind"] != "STRAIGHT":
            unsupported.append({"band_id": b["band_id"], "handles": b["handles"], "status": UNSUPPORTED,
                                "why": f"{b['kind']} band: V2 measures straight bands only; carried, never 0"})
            continue
        L_band = b["t1"] - b["t0"]
        # 1. columns on the band (any overlap with the strip, full or partial width)
        on_cols = []
        for c in cols:
            iv = _support_interval(b, c, tol)
            if iv:
                on_cols.append((iv[0], iv[1], [c["support_id"]], iv[2]))
        cut = _merge([(a, c_, ref) for a, c_, ref, _ in on_cols], tol)
        frac = {ref[0]: f for _, _, ref, f in on_cols}
        # 2. junction zones of other bands that cover a band end
        jz, inter = [], []
        for o in straight:
            if o is b:
                continue
            iv = _junction_interval(b, o, tol)
            if not iv:
                continue
            if iv[0] <= b["t0"] + tol or iv[1] >= b["t1"] - tol:
                jz.append((iv[0], iv[1], [o["band_id"]]))
            else:
                inter.append({"band_id": o["band_id"], "station_m": round(((iv[0] + iv[1]) / 2 - b["t0"]) * k, 4),
                              "relation": "CROSSING_OR_TEE (no split)"})
        # 3. free intervals between the cuts
        blocks = [(a, c_, "COLUMN", ref) for a, c_, ref in cut] + [(a, c_, "BEAM_JUNCTION", ref) for a, c_, ref in jz]
        blocks.sort()
        free, cur = [], b["t0"]
        cur_node = None
        for a, c_, kind, ref in blocks:
            if a > cur + tol:
                free.append((cur, a, cur_node, (kind, ref)))
            if c_ > cur:
                cur, cur_node = c_, (kind, ref)
            elif cur_node is None and a <= cur + tol:
                cur_node = (kind, ref)
        if b["t1"] > cur + tol:
            free.append((cur, b["t1"], cur_node, None))
        flags_band = []
        pieces = []
        width = b["hi"] - b["lo"]
        for s0, s1, n0, n1 in free:
            nodes = []
            for t, nd, sign in ((s0, n0, 1), (s1, n1, -1)):
                if nd is None:
                    nd = _free_end_node(b, t, sign, cols, others[b["band_id"]], feet, tol, width)
                else:
                    nd = (nd[0], nd[1], {})
                nodes.append((nd[2].get("t", t), nd))
            (ta, na), (tb_, nb) = nodes
            if tb_ - ta <= tol:
                flags_band.append(f"BAND_PIECE_INSIDE_SUPPORT {round(s0 * k, 4)}..{round(s1 * k, 4)} m "
                                  f"({na[0]} {na[1]} / {nb[0]} {nb[1]}): no span")
                continue
            pieces.append((ta, tb_, na, nb))
        for i, (ta, tb_, na, nb) in enumerate(pieces, start=1):
            f2f = (tb_ - ta) * k
            ca, how_a = _centre_station(b, na[0], na[1], by_id, bands_by_id, ta)
            cb, how_b = _centre_station(b, nb[0], nb[1], by_id, bands_by_id, tb_)
            cl = abs(cb - ca) * k
            flags = []
            for nd in (na, nb):
                if nd[0] == "COLUMN":
                    for r in nd[1]:
                        if r in frac and frac[r] < 1.0 - tol / width:
                            flags.append(f"PARTIAL_WIDTH_SUPPORT {r}: covers {frac[r]:.2f} of the band width")
            under = []
            for f in feet:
                iv = _support_interval(b, f, tol)
                if iv and iv[0] < tb_ - tol and iv[1] > ta + tol and f["support_id"] not in na[1] + nb[1] and \
                        not any(_inside(_centroid(c["polygon"]), f["polygon"]) for c in cols):
                    under.append(f["support_id"])
            if under:
                flags.append(f"FOOTING_WITHOUT_COLUMN_UNDER_SPAN {sorted(under)}: no column on it, so not a support "
                             "(no split); listed for the checker")
            cls_f, st_f = length_class(f2f, classes)
            cls_c, st_c = length_class(cl, classes)
            if classes and cls_f != cls_c:
                flags.append(f"LENGTH_BASIS_CHANGES_CLASS face-to-face {cls_f} vs centreline {cls_c}")
            held, alts = [], {}
            for end, nd, t_face in (("start", na, ta), ("end", nb, tb_)):
                if nd[0] == "FREE_END":
                    held.append(f"FREE_END at the {end}: no column, band or footing; the support is not established")
                if nd[0] == "GAP_TO_COLUMN":
                    held.append(f"GAP_TO_COLUMN at the {end}: the band stops {nd[2]['gap'] * k:.3f} m short of "
                                f"{nd[1]}; which face is the support is not printed")
                    for name, t_alt in nd[2]["candidates"].items():
                        L_alt = (tb_ - t_alt) * k if end == "start" else (t_alt - ta) * k
                        alts[f"{end}:{name}"] = {"face_to_face_m": round(L_alt, 4),
                                                 "class": length_class(L_alt, classes)[0]}
            if alts and classes and len({tuple(v["class"]) for v in alts.values()} | {tuple(cls_f)}) > 1:
                flags.append("END_CANDIDATES_CHANGE_CLASS: " + "; ".join(f"{k_} {v['face_to_face_m']} m {v['class']}"
                                                                         for k_, v in alts.items()))
            if st_f == "ON_LIMIT":
                held.append(f"ON_LIMIT: {f2f:.3f} m meets no printed title; candidates {cls_f}")
            spans.append({
                "span_id": f"{b['band_id']}#{i}", "band_id": b["band_id"], "family": "GROUND_BEAM", "index": i,
                "handles": list(b["handles"]),
                "start": {"kind": na[0], "refs": na[1], "face_station_m": round(ta * k, 4),
                          "centre_station_m": round(ca * k, 4), "centre_how": how_a},
                "end": {"kind": nb[0], "refs": nb[1], "face_station_m": round(tb_ * k, 4),
                        "centre_station_m": round(cb * k, 4), "centre_how": how_b},
                "lengths": {"centreline_m": round(cl, 4), "clear_concrete_m": round(f2f, 4),
                            "face_to_face_m": round(f2f, 4), "bar_run_lb_m": None if held else round(f2f, 4),
                            "basis": "support face to face along the band axis (bar straight run lower bound; "
                                     "development / laps / hooks not included)",
                            "end_candidates": alts},
                "width_m": round(width * k, 4),
                "class_face_to_face": cls_f, "class_state": st_f, "class_centreline": cls_c,
                "status": HELD if held else RELEASED, "held_reasons": held, "flags": flags,
                "intermediate": inter, "rule_ids": [RULE_GB, RULE_STATUS]})
        interior = [{"support_id": "+".join(ref), "along_m": round((c_ - a) * k, 4),
                     "width_fraction": round(min(frac.get(r, 1.0) for r in ref), 4)}
                    for a, c_, ref in cut if a > b["t0"] + tol and c_ < b["t1"] - tol]
        band_rows.append({"band_id": b["band_id"], "handles": b["handles"], "band_length_m": round(L_band * k, 4),
                          "spans": len(pieces), "interior_supports": interior,
                          "junction_zones_at_ends": [{"band_id": "+".join(r), "from_m": round(a * k, 4),
                                                      "to_m": round(c_ * k, 4)} for a, c_, r in jz],
                          "flags": flags_band})
    return {"policy": POLICY_ID, "units": units, "spans": spans, "bands": band_rows, "unsupported": unsupported,
            "conservation": _conservation(spans, band_rows, B, unsupported)}


def _conservation(spans, band_rows, B, unsupported):
    by = {}
    for s in spans:
        by.setdefault(s["band_id"], []).append(s)
    ok_count = all(len(by.get(r["band_id"], [])) == r["spans"] for r in band_rows)
    ok_once = len(band_rows) + len(unsupported) == len(B)
    ok_len = all(sum(s["lengths"]["face_to_face_m"] for s in by.get(r["band_id"], [])) <= r["band_length_m"] + 1e-6
                 for r in band_rows)
    ok_held = all((s["status"] == HELD) == (s["lengths"]["bar_run_lb_m"] is None) for s in spans)
    checks = {"every_band_once": ok_once, "span_count_per_band": ok_count,
              "spans_within_band_length": ok_len, "held_span_carries_no_bar_run": ok_held}
    return {"checks": checks, "all_pass": all(checks.values())}


# ------------------------------------------------------------------------------------------------------ straps
def measure_straps(straps, footings, *, units="mm", tol_m=TOL_M):
    """straps: [{strap_id, mark, edges: [((x, y), (x, y)), ((x, y), (x, y))], handles}]; footings: supports of kind
    FOOTING. Every strap is HELD (no Urban length basis for straps); the candidate values are stored apart."""
    k = _check_units(units)
    tol = tol_m / k
    F = [_support(f) for f in footings]
    out = []
    for st in straps:
        (a0, a1), (b0, b1) = [tuple(map(lambda p: tuple(map(float, p[:2])), e)) for e in st["edges"]]
        ua = _norm((a1[0] - a0[0], a1[1] - a0[1]))
        ub = _norm((b1[0] - b0[0], b1[1] - b0[1]))
        if ua[0] * ub[1] - ua[1] * ub[0] > 1e-3 or -(ua[0] * ub[1] - ua[1] * ub[0]) > 1e-3:
            raise SpanError(f"strap {st['strap_id']}: edges are not parallel")
        if _dot(ua, ub) < 0:
            b0, b1, ub = b1, b0, (-ub[0], -ub[1])
        u = ua
        n = (-u[1], u[0])
        width = abs(_dot(b0, n) - _dot(a0, n))
        mid_a = ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2)
        mid_b = ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2)
        mid = ((mid_a[0] + mid_b[0]) / 2, (mid_a[1] + mid_b[1]) / 2)
        flags, held = [], ["STRAP_LENGTH_BASIS_NOT_SET: no Urban rule or owner answer sets the strap length basis "
                           f"({RULE_GB} never applies to STRAP); candidates stored apart"]
        ends = []
        for sign in (-1, 1):
            d = (sign * u[0], sign * u[1])
            best = None
            for f in F:
                if _inside(mid, f["polygon"]):
                    continue
                hits = _ray_hits(f["polygon"], mid, d)
                if hits and (best is None or hits[0] < best[0]):
                    best = (hits[0], f)
            ends.append(best)
        res = {"strap_id": st["strap_id"], "mark": st.get("mark"), "family": "STRAP_BEAM",
               "handles": list(st.get("handles") or []), "width_m": round(width * k, 4),
               "axis_unit": [round(u[0], 6), round(u[1], 6)], "status": HELD, "held_reasons": held, "flags": flags,
               "rule_ids": [RULE_STATUS]}
        if not all(ends):
            held.append("NO_FOOTING_AT_END: the strap axis meets no footing outline at "
                        f"{'both ends' if not any(ends) else 'one end'}")
            res.update({"start_footing": ends[0][1]["support_id"] if ends[0] else None,
                        "end_footing": ends[1][1]["support_id"] if ends[1] else None,
                        "candidates": {"axis_face_to_face_m": None}})
            out.append(res)
            continue
        (s_lo, f_lo), (s_hi, f_hi) = ends
        axis = (s_lo + s_hi) * k
        edge_vals = []
        for e0, e1 in ((a0, a1), (b0, b1)):
            em = ((e0[0] + e1[0]) / 2, (e0[1] + e1[1]) / 2)
            vals = []
            for sign, f in ((-1, f_lo), (1, f_hi)):
                h = _ray_hits(f["polygon"], em, (sign * u[0], sign * u[1]))
                vals.append(h[0] if h else None)
            edge_vals.append(None if None in vals else round((vals[0] + vals[1]) * k, 4))
        p_lo = [_dot(p, u) for p in f_lo["polygon"]]
        p_hi = [_dot(p, u) for p in f_hi["polygon"]]
        gap = (min(p_hi) - max(p_lo)) * k
        c2c = abs(_dot(_centroid(f_hi["polygon"]), u) - _dot(_centroid(f_lo["polygon"]), u)) * k
        if None in edge_vals:
            flags.append("EDGE_MEETS_NO_FOOTING: one strap edge does not reach both footing outlines")
        elif abs(edge_vals[0] - edge_vals[1]) > 2 * tol_m:
            flags.append(f"OBLIQUE_FACES: the two edges meet the footing faces {edge_vals[0]:.3f} / "
                         f"{edge_vals[1]:.3f} m apart")
        if abs(gap - axis) > tol_m:
            flags.append(f"PROJECTION_GAP_DIFFERS: footing projections on the axis leave {gap:.3f} m, the axis "
                         f"face to face is {axis:.3f} m (the frozen S5 register takes the projection gap)")
        res.update({"start_footing": f_lo["support_id"], "end_footing": f_hi["support_id"],
                    "candidates": {"axis_face_to_face_m": round(axis, 4), "edge_face_to_face_m": edge_vals,
                                   "projection_gap_m": round(gap, 4), "footing_centre_to_centre_m": round(c2c, 4)}})
        out.append(res)
    return out


def policy_record():
    return {"policy_id": POLICY_ID, "rules": [RULE_GB, RULE_STATUS],
            "statement": "a ground-beam band is split at every column outline on it (full or partial width) and at "
                         "end junction zones; spans are measured face to face along the band axis; a free end over a "
                         "footing ends at the footing face; class from the split span; straps measured along their "
                         "own axis between the footing faces and HELD (no strap length basis rule)",
            "node_kinds": list(NODE_KINDS)}

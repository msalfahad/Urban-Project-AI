"""Ground-beam physical network: paired faces -> bands -> support-to-support spans (generic, accurate-side).

A ground beam is drawn as two parallel faces at the beam width. This module turns admitted face primitives into
physical bands without any project constant (width, tolerances and admitted layers are parameters).

Two rules distinguish it from the single-best-partner pairing it supersedes:

MULTI_PARTNER_PAIRING
    A face may pair against several partner faces on the same side, provided every partner lies on the same
    offset line (parallel, at the beam width) and the partners are contiguous along the face. The combined partner
    geometry must satisfy the same physical constraints as a single partner:
      * parallel and at the beam width (+- tol);
      * positive overlap; the combined band at least ``min_overlap`` long;
      * contiguous: a gap between partner pieces wider than ``join_tol`` splits the band (the gap stays an
        UNPAIRED face interval with reason PARTNER_GAP);
      * no intervening face strictly between the two faces (INTERVENING_FACE -> CONFLICT, not a band);
      * one physical beam region: a face with valid partners on BOTH sides over the same interval is a shared
        line, not a beam face (SHARED_FACE_AMBIGUOUS -> CONFLICT);
      * node consistency: a non-parallel admitted face crossing the strip at a partner split stops the merge
        (NODE_AT_SPLIT).
    Faces on a non-admitted layer (annotation / detail linework) never become faces (LAYER_NOT_ADMITTED); faces
    shorter than ``min_face`` are kept in the ledger as SHORT_FACE. Every source handle is preserved.

ARC_OVERLAP
    Two concentric arcs at the beam width form a curved band only over their COMMON angular range. The strip
    length is the centreline radius x the overlap angle, never the longer (or the first) arc's sweep. Arcs
    with no common range make no band; a third concentric arc strictly between two faces is an intervening face.

Conservation: every admitted face (and arc) ends either covered by a band or in the unpaired ledger with a reason,
and covered + unpaired length equals the face length. No source face disappears silently.
"""

from __future__ import annotations

import math
from collections import defaultdict

POLICY_ID = "GROUND_BEAM_NETWORK_V1"
RULES = ("MULTI_PARTNER_PAIRING", "ARC_OVERLAP")
REASONS = ("LAYER_NOT_ADMITTED", "SHORT_FACE", "NO_PARTNER", "PARTNER_GAP", "INTERVENING_FACE",
           "SHARED_FACE_AMBIGUOUS", "BAND_TOO_SHORT", "NO_ANGULAR_OVERLAP", "DUPLICATE_PARTNER")
TWO_PI = 2.0 * math.pi


# ------------------------------------------------------------------ straight faces
def _face(f):
    x0, y0 = f["p0"]
    x1, y1 = f["p1"]
    L = math.hypot(x1 - x0, y1 - y0)
    u = ((x1 - x0) / L, (y1 - y0) / L) if L > 0 else (1.0, 0.0)
    return dict(f, L=L, u=u, n=(-u[1], u[0]))


def _canon_axis(u):
    """One direction per parallel family (so every face on a line projects onto the same axis)."""
    ux, uy = u
    if ux < -1e-12 or (abs(ux) <= 1e-12 and uy < 0):
        ux, uy = -ux, -uy
    return ux, uy


def _proj(p, u):
    return p[0] * u[0] + p[1] * u[1]


def _interval(f, u):
    a, b = _proj(f["p0"], u), _proj(f["p1"], u)
    return (a, b) if a <= b else (b, a)


def _subtract(iv, cuts):
    """Interval minus a list of intervals -> list of remaining intervals."""
    out = [iv]
    for c0, c1 in sorted(cuts):
        nxt = []
        for a, b in out:
            if c1 <= a or c0 >= b:
                nxt.append((a, b))
                continue
            if c0 > a:
                nxt.append((a, c0))
            if c1 < b:
                nxt.append((c1, b))
        out = nxt
    return [(a, b) for a, b in out if b - a > 1e-6]


def pair_straight(faces, *, width, tol, admitted_layers, min_face=300.0, min_overlap=300.0, parallel_eps=0.01,
                  join_tol=1.0):
    """faces: [{handle, layer, p0: (x, y), p1: (x, y)}] -> {bands, strips, conflicts, unpaired, rejected, ledger}."""
    rejected, admitted = [], []
    for f in faces:
        g = _face(f)
        if g["layer"] not in admitted_layers:
            rejected.append({"handle": g["handle"], "layer": g["layer"], "length": g["L"], "reason": "LAYER_NOT_ADMITTED"})
        elif g["L"] < min_face:
            rejected.append({"handle": g["handle"], "layer": g["layer"], "length": g["L"], "reason": "SHORT_FACE"})
        else:
            admitted.append(g)
    admitted.sort(key=lambda g: str(g["handle"]))

    # ---- candidate strips: every parallel pair at the beam width with positive overlap
    strips, near = [], []
    for i, a in enumerate(admitted):
        for b in admitted[i + 1:]:
            if abs(a["u"][0] * b["u"][1] - a["u"][1] * b["u"][0]) > parallel_eps:
                continue
            u = _canon_axis(a["u"])
            n = (-u[1], u[0])
            oa = _proj(a["p0"], n)
            ob = _proj(b["p0"], n)
            off = ob - oa
            ia, ib = _interval(a, u), _interval(b, u)
            lo, hi = max(ia[0], ib[0]), min(ia[1], ib[1])
            if hi - lo <= join_tol:
                continue
            if abs(abs(off) - width) > tol:
                if abs(abs(off) - width) <= 3 * tol:
                    near.append({"faces": [a["handle"], b["handle"]], "offset": abs(off), "reason": "WIDTH_MISMATCH"})
                continue
            lo_face, hi_face = (a, b) if off > 0 else (b, a)          # lo_face: smaller normal offset
            strips.append({"u": u, "n": n, "lo_off": min(oa, ob), "hi_off": max(oa, ob), "t0": lo, "t1": hi,
                           "faces": (lo_face["handle"], hi_face["handle"]), "state": "CANDIDATE"})

    by_handle = {g["handle"]: g for g in admitted}

    # ---- intervening face: a parallel admitted face strictly between the two faces, overlapping the strip
    conflicts = []
    for s in strips:
        for g in admitted:
            if g["handle"] in s["faces"]:
                continue
            if abs(g["u"][0] * s["u"][1] - g["u"][1] * s["u"][0]) > parallel_eps:
                continue
            og = _proj(g["p0"], s["n"])
            if not (s["lo_off"] + tol < og < s["hi_off"] - tol):
                continue
            ig = _interval(g, s["u"])
            if min(ig[1], s["t1"]) - max(ig[0], s["t0"]) > join_tol:
                s["state"] = "CONFLICT"
                s["reason"] = "INTERVENING_FACE"
                s["intervening"] = g["handle"]
                break

    # ---- shared face: one face with valid strips on both sides over a common interval
    side = defaultdict(list)                  # handle -> [(strip, side sign)]
    for s in strips:
        if s["state"] != "CANDIDATE":
            continue
        side[s["faces"][0]].append((s, +1))
        side[s["faces"][1]].append((s, -1))
    for h, lst in side.items():
        for s1, d1 in lst:
            for s2, d2 in lst:
                if d1 == d2 or s1 is s2:
                    continue
                if min(s1["t1"], s2["t1"]) - max(s1["t0"], s2["t0"]) > join_tol:
                    for s in (s1, s2):
                        s["state"] = "CONFLICT"
                        s["reason"] = "SHARED_FACE_AMBIGUOUS"
                        s["shared_face"] = h

    # ---- duplicate partners (overlapping drawn duplicates on the same offset line)
    groups = defaultdict(list)
    for s in strips:
        if s["state"] == "CANDIDATE":
            groups[(s["faces"][0], round(s["hi_off"] - s["lo_off"]))].append(s)
            groups[(s["faces"][1], -round(s["hi_off"] - s["lo_off"]))].append(s)
    for key, lst in groups.items():
        lst.sort(key=lambda s: (s["t0"], s["faces"]))
        for x, y in zip(lst, lst[1:]):
            if y["state"] == "CANDIDATE" and x["state"] == "CANDIDATE" and \
                    min(x["t1"], y["t1"]) - max(x["t0"], y["t0"]) > join_tol and \
                    abs(x["lo_off"] - y["lo_off"]) <= tol and abs(x["hi_off"] - y["hi_off"]) <= tol:
                y["state"] = "CONFLICT"
                y["reason"] = "DUPLICATE_PARTNER"

    for s in strips:
        if s["state"] == "CONFLICT":
            conflicts.append({"faces": list(s["faces"]), "reason": s["reason"], "t0": s["t0"], "t1": s["t1"],
                              "detail": s.get("intervening") or s.get("shared_face")})

    # ---- merge contiguous strips sharing an offset line pair into one physical band
    live = [s for s in strips if s["state"] == "CANDIDATE"]
    parent = list(range(len(live)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    crossers = [g for g in admitted]
    for i, x in enumerate(live):
        for j in range(i + 1, len(live)):
            y = live[j]
            if abs(x["u"][0] * y["u"][1] - x["u"][1] * y["u"][0]) > parallel_eps:
                continue
            if abs(x["lo_off"] - y["lo_off"]) > tol or abs(x["hi_off"] - y["hi_off"]) > tol:
                continue
            if not set(x["faces"]) & set(y["faces"]):
                # contiguous strips on the same two lines join only through a common face
                continue
            gap = max(y["t0"] - x["t1"], x["t0"] - y["t1"])
            if gap > join_tol:
                continue
            split = x["t1"] if abs(y["t0"] - x["t1"]) <= abs(x["t0"] - y["t1"]) else x["t0"]
            if _crossed_at(crossers, x, split, parallel_eps, tol):
                x.setdefault("nodes", []).append(split)
                continue
            parent[find(i)] = find(j)
    comps = defaultdict(list)
    for i, s in enumerate(live):
        comps[find(i)].append(s)

    bands = []
    for ss in comps.values():
        ss.sort(key=lambda s: s["t0"])
        t0, t1 = ss[0]["t0"], max(s["t1"] for s in ss)
        lo_faces = sorted({s["faces"][0] for s in ss}, key=str)
        hi_faces = sorted({s["faces"][1] for s in ss}, key=str)
        lo_off = sum(s["lo_off"] for s in ss) / len(ss)
        hi_off = sum(s["hi_off"] for s in ss) / len(ss)
        u, n = ss[0]["u"], ss[0]["n"]
        rule = "MULTI_PARTNER_PAIRING" if (len(lo_faces) > 1 or len(hi_faces) > 1) else "SINGLE_PARTNER"
        b = {"kind": "STRAIGHT", "u": u, "n": n, "t0": t0, "t1": t1, "lo_off": lo_off, "hi_off": hi_off,
             "width": hi_off - lo_off, "length": t1 - t0, "faces_a": lo_faces, "faces_b": hi_faces,
             "handles": sorted(set(lo_faces) | set(hi_faces), key=str), "strips": len(ss), "rule": rule,
             "state": "ACCEPTED" if t1 - t0 >= min_overlap else "REJECTED", "polygon": None}
        if b["state"] == "REJECTED":
            b["reason"] = "BAND_TOO_SHORT"
        b["polygon"] = _rect(u, n, t0, t1, lo_off, hi_off)
        bands.append(b)
    bands.sort(key=lambda b: (b["handles"][0] if b["handles"] else "", b["t0"]))

    # ---- face ledger: covered + unpaired = face length
    ledger, unpaired = [], []
    covered = defaultdict(list)
    for b in bands:
        if b["state"] != "ACCEPTED":
            continue
        for h in b["handles"]:
            g = by_handle[h]
            ig = _interval(g, b["u"])
            covered[h].append((max(ig[0], b["t0"]), min(ig[1], b["t1"])))
    conflict_iv = defaultdict(list)
    for s in strips:
        if s["state"] == "CONFLICT":
            for h in s["faces"]:
                conflict_iv[h].append((s["t0"], s["t1"], s["reason"]))
    for g in admitted:
        u = _canon_axis(g["u"])
        iv = _interval(g, u)
        cov = sorted((max(a, iv[0]), min(b, iv[1])) for a, b in covered.get(g["handle"], []) if b > a)
        merged = []
        for a, b in cov:
            if merged and a <= merged[-1][1] + 1e-6:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        cov_len = sum(b - a for a, b in merged)
        rest = _subtract(iv, merged)
        for a, b in rest:
            hit = [r for c0, c1, r in conflict_iv.get(g["handle"], []) if min(c1, b) - max(c0, a) > join_tol]
            short = [x for x in bands if x["state"] == "REJECTED" and g["handle"] in x["handles"]
                     and min(x["t1"], b) - max(x["t0"], a) > join_tol]
            if hit:
                reason = hit[0]
            elif short:
                reason = "BAND_TOO_SHORT"
            elif any(m[1] <= a + join_tol for m in merged) and any(m[0] >= b - join_tol for m in merged):
                reason = "PARTNER_GAP"            # a hole between covered parts of the same face
            else:
                reason = "NO_PARTNER"
            unpaired.append({"handle": g["handle"], "t0": a, "t1": b, "length": b - a, "reason": reason})
        ledger.append({"handle": g["handle"], "layer": g["layer"], "length": g["L"], "covered": cov_len,
                       "unpaired": sum(b - a for a, b in rest)})
    return {"policy": POLICY_ID, "bands": [b for b in bands if b["state"] == "ACCEPTED"],
            "rejected_bands": [b for b in bands if b["state"] != "ACCEPTED"], "conflicts": conflicts,
            "unpaired": unpaired, "rejected_faces": rejected, "near_misses": near, "ledger": ledger,
            "params": {"width": width, "tol": tol, "min_face": min_face, "min_overlap": min_overlap,
                       "parallel_eps": parallel_eps, "join_tol": join_tol, "admitted_layers": sorted(admitted_layers)}}


def _crossed_at(faces, strip, t, parallel_eps, tol):
    """A non-parallel face that spans the strip (from one face line to the other) at station t."""
    u, n = strip["u"], strip["n"]
    for g in faces:
        if g["handle"] in strip["faces"]:
            continue
        if abs(g["u"][0] * u[1] - g["u"][1] * u[0]) <= parallel_eps:
            continue
        a = (_proj(g["p0"], u), _proj(g["p0"], n))
        b = (_proj(g["p1"], u), _proj(g["p1"], n))
        lo, hi = sorted((a[1], b[1]))
        if lo > strip["lo_off"] + tol or hi < strip["hi_off"] - tol:
            continue
        if b[1] == a[1]:
            continue
        mid = (strip["lo_off"] + strip["hi_off"]) / 2.0
        s = a[0] + (b[0] - a[0]) * (mid - a[1]) / (b[1] - a[1])
        if abs(s - t) <= tol:
            return True
    return False


def _rect(u, n, t0, t1, lo, hi):
    p = lambda t, o: (t * u[0] + o * n[0], t * u[1] + o * n[1])
    return [p(t0, lo), p(t1, lo), p(t1, hi), p(t0, hi)]


# ------------------------------------------------------------------ arcs
def _ccw(a):
    """Normalise an arc to (start, sweep) counter-clockwise, radians. ``cw`` arcs are re-expressed CCW."""
    a0, a1 = a["a0"], a["a1"]
    if a.get("cw"):
        a0, a1 = a1, a0
    s = a0 % TWO_PI
    sweep = (a1 - a0) % TWO_PI
    if sweep == 0.0:
        sweep = TWO_PI
    return s, sweep


def angular_overlap(r1, r2):
    """Common part of two CCW circular intervals (start, sweep) -> list of (start, sweep)."""
    out = []
    for (s1, w1), (s2, w2) in ((r1, r2), (r2, r1)):
        d = (s2 - s1) % TWO_PI
        if d < w1:
            ov = min(w1 - d, w2)
            if ov > 1e-9:
                out.append(((s1 + d) % TWO_PI, ov))
    uniq = []
    for s, w in out:
        if not any(abs(((s - t + math.pi) % TWO_PI) - math.pi) < 1e-9 and abs(w - v) < 1e-9 for t, v in uniq):
            uniq.append((s, w))
    if len(uniq) == 2 and abs(uniq[0][1] + uniq[1][1] - min(r1[1], r2[1])) < 1e-9 and \
            (r1[1] >= TWO_PI - 1e-9 or r2[1] >= TWO_PI - 1e-9):
        return [min(uniq, key=lambda z: -z[1])]
    return uniq


def _deg(x):
    return round(math.degrees(x) % 360.0, 4)


def pair_arcs(arcs, *, width, tol, admitted_layers, centre_tol=5.0, min_overlap=0.0):
    """arcs: [{handle, layer, cx, cy, r, a0, a1 (radians, CCW a0 -> a1), cw: bool}] -> {bands, conflicts, unpaired}."""
    rejected = [{"handle": a["handle"], "reason": "LAYER_NOT_ADMITTED"} for a in arcs if a["layer"] not in admitted_layers]
    A = sorted([a for a in arcs if a["layer"] in admitted_layers], key=lambda a: str(a["handle"]))
    cands, conflicts, nolap = [], [], []
    for i, a in enumerate(A):
        for b in A[i + 1:]:
            if math.hypot(a["cx"] - b["cx"], a["cy"] - b["cy"]) > centre_tol:
                continue
            if abs(abs(a["r"] - b["r"]) - width) > tol:
                continue
            ra, rb = _ccw(a), _ccw(b)
            ov = angular_overlap(ra, rb)
            if not ov:
                nolap.append({"faces": [a["handle"], b["handle"]], "reason": "NO_ANGULAR_OVERLAP",
                              "arc_a_range_deg": [_deg(ra[0]), _deg(ra[0] + ra[1])],
                              "arc_b_range_deg": [_deg(rb[0]), _deg(rb[0] + rb[1])]})
                continue
            inner, outer = (a, b) if a["r"] < b["r"] else (b, a)
            for s, w in ov:
                cands.append({"inner": inner, "outer": outer, "start": s, "sweep": w, "ra": ra, "rb": rb,
                              "a": a, "b": b, "state": "CANDIDATE"})
    # intervening concentric arc
    for c in cands:
        for g in A:
            if g in (c["inner"], c["outer"]):
                continue
            if math.hypot(g["cx"] - c["inner"]["cx"], g["cy"] - c["inner"]["cy"]) > centre_tol:
                continue
            if not (c["inner"]["r"] + tol < g["r"] < c["outer"]["r"] - tol):
                continue
            if angular_overlap((c["start"], c["sweep"]), _ccw(g)):
                c["state"], c["reason"], c["detail"] = "CONFLICT", "INTERVENING_FACE", g["handle"]
    # shared face: an arc with valid partners inside and outside over a common angle
    by = defaultdict(list)
    for c in cands:
        if c["state"] == "CANDIDATE":
            by[c["inner"]["handle"]].append((c, "OUT"))
            by[c["outer"]["handle"]].append((c, "IN"))
    for h, lst in by.items():
        for c1, d1 in lst:
            for c2, d2 in lst:
                if d1 != d2 and angular_overlap((c1["start"], c1["sweep"]), (c2["start"], c2["sweep"])):
                    for c in (c1, c2):
                        c["state"], c["reason"], c["detail"] = "CONFLICT", "SHARED_FACE_AMBIGUOUS", h
    bands = []
    for c in cands:
        if c["state"] != "CANDIDATE":
            conflicts.append({"faces": [c["a"]["handle"], c["b"]["handle"]], "reason": c["reason"],
                              "detail": c["detail"]})
            continue
        r0, r1 = c["inner"]["r"], c["outer"]["r"]
        rc = (r0 + r1) / 2.0
        L = rc * c["sweep"]
        if L < min_overlap:
            conflicts.append({"faces": [c["a"]["handle"], c["b"]["handle"]], "reason": "BAND_TOO_SHORT", "detail": L})
            continue
        cx, cy = c["inner"]["cx"], c["inner"]["cy"]
        k = max(int(math.degrees(c["sweep"]) / 3), 4)
        outer = [(cx + r1 * math.cos(c["start"] + c["sweep"] * j / k), cy + r1 * math.sin(c["start"] + c["sweep"] * j / k))
                 for j in range(k + 1)]
        inner = [(cx + r0 * math.cos(c["start"] + c["sweep"] * j / k), cy + r0 * math.sin(c["start"] + c["sweep"] * j / k))
                 for j in range(k, -1, -1)]
        bands.append({"kind": "ARC", "rule": "ARC_OVERLAP", "state": "ACCEPTED",
                      "handles": sorted([c["a"]["handle"], c["b"]["handle"]], key=str),
                      "centre": (cx, cy), "r_inner": r0, "r_outer": r1, "width": r1 - r0,
                      "ARC_A_RANGE": [_deg(c["ra"][0]), _deg(c["ra"][0] + c["ra"][1])],
                      "ARC_B_RANGE": [_deg(c["rb"][0]), _deg(c["rb"][0] + c["rb"][1])],
                      "OVERLAP_RANGE": [_deg(c["start"]), _deg(c["start"] + c["sweep"])],
                      "overlap_rad": c["sweep"], "start_rad": c["start"],
                      "CENTERLINE_RADIUS": rc, "CENTERLINE_ARC_LENGTH": L, "length": L,
                      "SOURCE_HANDLES": sorted([c["a"]["handle"], c["b"]["handle"]], key=str),
                      "polygon": outer + inner})
    # unpaired angular ranges per arc
    unpaired = []
    for g in A:
        rg = _ccw(g)
        cov = [(b["start_rad"], b["overlap_rad"]) for b in bands if g["handle"] in b["handles"]]
        rest = _arc_minus(rg, cov)
        reason = "NO_PARTNER"
        if any(g["handle"] in c["faces"] for c in conflicts):
            reason = next(c["reason"] for c in conflicts if g["handle"] in c["faces"])
        elif any(g["handle"] in x["faces"] for x in nolap):
            reason = "NO_ANGULAR_OVERLAP"
        for s, w in rest:
            unpaired.append({"handle": g["handle"], "range_deg": [_deg(s), _deg(s + w)], "sweep_rad": w,
                             "length": g["r"] * w, "reason": reason if not cov else "UNPAIRED_SWEEP"})
    return {"policy": POLICY_ID, "bands": bands, "conflicts": conflicts + nolap, "unpaired": unpaired,
            "rejected_faces": rejected}


def _arc_minus(rg, cov):
    """CCW interval minus CCW intervals, in the local frame of rg."""
    s0, w0 = rg
    cuts = []
    for s, w in cov:
        d = (s - s0) % TWO_PI
        cuts.append((d, min(d + w, w0)))
    rest = _subtract((0.0, w0), cuts)
    return [((s0 + a) % TWO_PI, b - a) for a, b in rest if b - a > 1e-9]


# ------------------------------------------------------------------ spans and topology
def span_length(piece_coords, band):
    """V3 span length convention: straight = projected extent along the band axis; curved = centreline arc length x
    the piece's share of the band area."""
    if band["kind"] == "ARC":
        return band["CENTERLINE_ARC_LENGTH"] * band["_piece_area"] / band["_area"]
    u = band["u"]
    xs = [_proj(p, u) for p in piece_coords]
    return max(xs) - min(xs)


def end_supports(band, t, columns, other_bands, *, tol=5.0):
    """Classify one band end at station t: COLUMN / BEAM_JUNCTION / FREE_END (with refs)."""
    u, n = band["u"], band["n"]
    mid = (band["lo_off"] + band["hi_off"]) / 2.0
    p = (t * u[0] + mid * n[0], t * u[1] + mid * n[1])
    refs = []
    for c in columns:
        x0, y0, x1, y1 = c["bbox"]
        hw = band["width"] / 2.0
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        al = [_proj(q, u) for q in corners]
        ac = [_proj(q, n) - mid for q in corners]
        if min(ac) <= hw + tol and max(ac) >= -hw - tol and min(al) - tol <= t <= max(al) + tol:
            refs.append({"kind": "COLUMN", "ref": c["id"], "centre_station": (min(al) + max(al)) / 2.0})
    for o in other_bands:
        if o is band or o["kind"] != "STRAIGHT":
            continue
        if abs(o["u"][0] * u[1] - o["u"][1] * u[0]) < 0.2:
            continue
        mo = (o["lo_off"] + o["hi_off"]) / 2.0
        po = _proj(p, o["u"])
        off = _proj(p, o["n"])
        if o["t0"] - tol <= po <= o["t1"] + tol and o["lo_off"] - band["width"] / 2 - tol <= off <= \
                o["hi_off"] + band["width"] / 2 + tol:
            # station of the other band's centreline along this band
            q = (po * o["u"][0] + mo * o["n"][0], po * o["u"][1] + mo * o["n"][1])
            refs.append({"kind": "BEAM", "ref": "+".join(map(str, o["handles"])), "centre_station": _proj(q, u)})
    kind = "COLUMN" if any(r["kind"] == "COLUMN" for r in refs) else ("BEAM_JUNCTION" if refs else "FREE_END")
    return {"kind": kind, "refs": refs}


def policy_record():
    return {"policy_id": POLICY_ID, "rules": list(RULES), "reasons": list(REASONS),
            "statement": "two faces at the beam width pair over their common extent; a face may pair with several "
                         "contiguous collinear partners; arcs pair over their common angular range; every face ends "
                         "covered or in the unpaired ledger with a reason"}

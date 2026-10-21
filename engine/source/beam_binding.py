"""BEAM TAG -> PLAN BAND BINDING (V2) - type identity from the tag, section from the tag's OWN schedule namespace,
length from the ONE plan band the tag names. Positive constraints only; never nearest-text.

namespace() / lookup()   simple (B*), continuous (CB*) and strap (SB*) beam types live in separate namespaces; a lookup
                         answers only from the namespace of the exact type token (a B1 lookup can never return CB1, a
                         CB1 lookup never falls back to B1, no normalisation strips a letter).
merge_lines()            element segments of ANY orientation -> maximal collinear lines (pieces whose gap <= eps are
                         merged; the source keys of every piece are kept).
bind()                   a tag is BOUND to a band only when exactly one pair of parallel element lines passes ALL of:
                           breadth     separation = the scheduled breadth of the tag's own type (authoring tolerance;
                                       then the width-deviation policy, reported)
                           orientation band axis parallel to the tag baseline (rotation read from the source entity)
                           span        the tag centre projects inside the pair's common span
                           adjacency   the tag box lies inside the band, or its near edge is within GAP_FACTOR text
                                       heights of the band edge, and no other element line lies between tag and band
                           margin      no second band passes the same constraints within MARGIN_FACTOR text heights
                         0 survivors -> NO_BAND_PARALLEL_TO_TAG / NO_BAND_AT_SCHEDULED_BREADTH; 2+ -> AMBIGUOUS_BAND.
lengths()                four separately stored bases for a bound band:
                           PLAN_DRAWN_EXTENT          the pair's common drawn span (edge lines as drawn)
                           CLEAR_FACE_TO_FACE_LENGTH  along the band centre line between the faces of the first support
                                                      outline met on each side of the tag (columns / other bands)
                           SUPPORT_CENTRELINE_LENGTH  between the centres of those two supports, projected on the axis
                           SCHEDULE_SPAN_LENGTH       continuous beams only: sum of the printed spans (never measured)
                         an end that meets no support is FREE_END (cantilever / unsupported): the clear and centre-line
                         bases are then BLOCKED for that band, the drawn extent stays.

Project-agnostic; stdlib only. Units: native drawing units in, millimetres / metres out through umm.
"""

from __future__ import annotations

import hashlib
import json
import math
import re

POLICY_ID = "BEAM_BINDING_V2"
GAP_FACTOR = 1.0              # tag-to-band clear gap, in text heights (a label is written against the band it names)
MARGIN_FACTOR = 1.5           # a competing band within this many text heights makes the tag ambiguous
CHAR_WIDTH = 0.8              # text box length = characters x height x CHAR_WIDTH (box only; never a quantity)
ANGLE_TOL_DEG = 1.0
WIDTH_DEVIATION_MAX = 0.05
NAMESPACE_RE = re.compile(r"^(CB|SB|B)(\d+)$")
NAMESPACES = {"CB": "CONTINUOUS", "SB": "STRAP", "B": "SIMPLE"}
OTHER = "OTHER"                   # scheduled rows whose name is not B<n> / CB<n> / SB<n> (exact lookup only)

BOUND = "BOUND"
BOUND_DEV = "BOUND_WITH_WIDTH_DEVIATION"
NO_PARALLEL = "NO_BAND_PARALLEL_TO_TAG"
NO_BREADTH = "NO_BAND_AT_SCHEDULED_BREADTH"
NOT_ADJACENT = "NO_BAND_ADJACENT_TO_TAG"
AMBIGUOUS = "AMBIGUOUS_BAND"
NOT_SCHEDULED = "SECTION_NOT_SCHEDULED"
BOUND_STATES = (BOUND, BOUND_DEV)


# ------------------------------------------------------------------ namespaces
def namespace(t) -> str | None:
    m = NAMESPACE_RE.match(str(t or ""))
    if m:
        return NAMESPACES[m.group(1)]
    return OTHER if str(t or "").strip() else None


def split_library(rows: dict) -> dict:
    """{type: row} from one or more schedules -> {namespace: {type: row}}; every key filed under its own namespace."""
    out = {}
    for t in sorted(rows):
        out.setdefault(namespace(t), {})[t] = rows[t]
    return out


def lookup(libraries: dict, t):
    """libraries {"SIMPLE": {type: row}, "CONTINUOUS": {...}, "STRAP": {...}} -> the row of exactly this type from
    its own namespace, else None. A type token is never rewritten."""
    ns = namespace(t)
    if ns is None:
        return None
    return (libraries.get(ns) or {}).get(t)


def namespace_audit(libraries: dict) -> dict:
    """Every library key must belong to the namespace it is filed under; one key in two namespaces is a collision."""
    wrong, seen, coll = [], {}, []
    for ns, lib in sorted(libraries.items()):
        for t in sorted(lib):
            if namespace(t) != ns:
                wrong.append({"type": t, "filed_under": ns, "namespace": namespace(t)})
            if t in seen:
                coll.append({"type": t, "namespaces": [seen[t], ns]})
            seen[t] = ns
    return {"misfiled": wrong, "collisions": coll, "state": "PASS" if not wrong and not coll else "FAIL"}


# ------------------------------------------------------------------ geometry
def _canon(dx, dy, tol):
    a = math.atan2(dy, dx) % math.pi
    if a >= math.pi - tol:
        a -= math.pi
    return a


def merge_lines(segments, *, eps, angle_tol=1e-3) -> list:
    """segments [(key, x1, y1, x2, y2)] -> [{"keys", "angle", "u", "n", "offset", "t0", "t1"}] maximal collinear lines."""
    items = []
    for key, x1, y1, x2, y2 in segments:
        L = math.hypot(x2 - x1, y2 - y1)
        if L <= eps:
            continue
        a = _canon(x2 - x1, y2 - y1, angle_tol)
        u = (math.cos(a), math.sin(a))
        n = (-u[1], u[0])
        off = (x1 * n[0] + y1 * n[1] + x2 * n[0] + y2 * n[1]) / 2.0
        t1, t2 = sorted((x1 * u[0] + y1 * u[1], x2 * u[0] + y2 * u[1]))
        items.append((a, off, t1, t2, key))
    items.sort()
    groups = []
    for it in items:
        for g in groups:
            if abs(g["angle"] - it[0]) <= angle_tol and abs(g["offset"] - it[1]) <= eps:
                g["pieces"].append(it)
                break
        else:
            groups.append({"angle": it[0], "offset": it[1], "pieces": [it]})
    out = []
    for g in groups:
        a = g["angle"]
        u = (math.cos(a), math.sin(a))
        n = (-u[1], u[0])
        ps = sorted(g["pieces"], key=lambda p: (p[2], p[3], p[4]))
        cur = [ps[0][2], ps[0][3], [ps[0][4]]]
        for p in ps[1:]:
            if p[2] <= cur[1] + eps:
                cur[1] = max(cur[1], p[3])
                cur[2].append(p[4])
            else:
                out.append({"keys": sorted(cur[2]), "angle": a, "u": u, "n": n, "offset": g["offset"],
                            "t0": cur[0], "t1": cur[1]})
                cur = [p[2], p[3], [p[4]]]
        out.append({"keys": sorted(cur[2]), "angle": a, "u": u, "n": n, "offset": g["offset"], "t0": cur[0], "t1": cur[1]})
    out.sort(key=lambda l: (round(l["angle"], 6), round(l["offset"], 3), round(l["t0"], 3)))
    return out


def _seg_cross(p, q, a, b) -> bool:
    """Proper intersection of segments pq and ab (shared end points excluded)."""
    def orient(o, s, t):
        return (s[0] - o[0]) * (t[1] - o[1]) - (s[1] - o[1]) * (t[0] - o[0])
    d1, d2 = orient(a, b, p), orient(a, b, q)
    d3, d4 = orient(p, q, a), orient(p, q, b)
    return (d1 * d2 < 0) and (d3 * d4 < 0)


def text_box(mark) -> dict:
    """Tag box from the insertion point (lower-left), rotation, height and character count."""
    r = math.radians(mark.get("rotation_deg") or 0.0)
    u = (math.cos(r), math.sin(r))
    n = (-u[1], u[0])
    h = float(mark.get("height") or 0.0)
    L = len(str(mark.get("value") or "")) * h * CHAR_WIDTH
    c = (mark["x"] + u[0] * L / 2 + n[0] * h / 2, mark["y"] + u[1] * L / 2 + n[1] * h / 2)
    return {"centre": c, "u": u, "n": n, "half_len": L / 2, "half_h": h / 2, "height": h,
            "angle": _canon(u[0], u[1], math.radians(ANGLE_TOL_DEG))}


def _pairs(lines, box, width, tol, eps, angle_tol):
    """Parallel pairs at separation width +- tol, parallel to the tag, whose common span holds the tag centre."""
    out = []
    par = [l for l in lines if abs(l["angle"] - box["angle"]) <= angle_tol]
    cx, cy = box["centre"]
    for i, a in enumerate(par):
        for b in par[i + 1:]:
            if abs(a["angle"] - b["angle"]) > angle_tol:
                continue
            sep = abs(b["offset"] - a["offset"])
            if sep <= eps or (width is not None and abs(sep - width) > tol):
                continue
            u = a["u"]
            tc = cx * u[0] + cy * u[1]
            t0, t1 = max(a["t0"], b["t0"]), min(a["t1"], b["t1"])
            if not (t0 < tc < t1):
                continue
            lo, hi = sorted((a["offset"], b["offset"]))
            out.append({"lines": (a, b) if a["offset"] <= b["offset"] else (b, a), "lo": lo, "hi": hi, "t0": t0, "t1": t1,
                        "u": u, "n": a["n"], "angle": a["angle"], "sep": sep, "tc": tc})
    return out


def _gap(pair, box):
    """Clear gap (native) between the tag box and the band across the band axis; <= 0 when they overlap."""
    cx, cy = box["centre"]
    oc = cx * pair["n"][0] + cy * pair["n"][1]
    top, bot = oc + box["half_h"], oc - box["half_h"]
    if bot >= pair["hi"]:
        return bot - pair["hi"], oc
    if top <= pair["lo"]:
        return pair["lo"] - top, oc
    return 0.0, oc


def _intervening(pair, box, segments, eps):
    """Another element line crossing the straight path from the tag centre to the near band edge."""
    gap, oc = _gap(pair, box)
    if gap <= 0:
        return []
    n = pair["n"]
    edge = pair["lo"] if oc < pair["lo"] else pair["hi"]
    cx, cy = box["centre"]
    q = (cx + n[0] * (edge - oc), cy + n[1] * (edge - oc))
    p = (cx + n[0] * (box["half_h"] if edge > oc else -box["half_h"]), cy + n[1] * (box["half_h"] if edge > oc else -box["half_h"]))
    own = set(pair["lines"][0]["keys"]) | set(pair["lines"][1]["keys"])
    hit = []
    for key, x1, y1, x2, y2 in segments:
        if key in own:
            continue
        if _seg_cross(p, q, (x1, y1), (x2, y2)):
            hit.append(key)
    return sorted(hit)


def bind(marks, libraries, lines, segments, *, umm, tol_mm, eps, gap_factor=GAP_FACTOR, margin_factor=MARGIN_FACTOR,
         angle_tol_deg=ANGLE_TOL_DEG, deviation=WIDTH_DEVIATION_MAX) -> list:
    """marks [{"key", "value", "type", "x", "y", "rotation_deg", "height"}]; libraries per namespace; lines from
    merge_lines(segments); segments the raw element segments (for the intervening-line test)."""
    at = math.radians(angle_tol_deg)
    out = []
    for m in sorted(marks, key=lambda z: z["key"]):
        sec = lookup(libraries, m["type"])
        rec = {"type": m["type"], "namespace": namespace(m["type"]), "mark_key": m["key"], "mark_value": m["value"],
               "mark_xy": [round(m["x"], 3), round(m["y"], 3)], "rotation_deg": round(m.get("rotation_deg") or 0.0, 3),
               "text_height": m.get("height"), "B_cm": sec and sec.get("B_cm"), "D_cm": sec and sec.get("D_cm")}
        if not sec or sec.get("B_cm") is None or sec.get("D_cm") is None:
            out.append(dict(rec, state=NOT_SCHEDULED))
            continue
        box = text_box(m)
        width = sec["B_cm"] * 10.0 / umm
        h = box["height"]
        parallel = _pairs(lines, box, None, None, eps, at)
        if not parallel:
            out.append(dict(rec, state=NO_PARALLEL))
            continue
        deviation_mm = None
        cands = _pairs(lines, box, width, tol_mm / umm, eps, at)
        if not cands:
            cands = _pairs(lines, box, width, deviation * width, eps, at)
            deviation_mm = "POLICY" if cands else None
        if not cands:
            seps = sorted({round(p["sep"] * umm, 1) for p in parallel if _gap(p, box)[0] <= margin_factor * h})
            out.append(dict(rec, state=NO_BREADTH, scheduled_breadth_mm=sec["B_cm"] * 10.0,
                            adjacent_separations_mm=seps))
            continue
        scored = []
        for p in cands:
            g, _ = _gap(p, box)
            blockers = _intervening(p, box, segments, eps)
            scored.append((p, g, blockers))
        ok = [s for s in scored if s[1] <= gap_factor * h and not s[2]]
        near = [s for s in scored if s[1] <= margin_factor * h and not s[2]]
        if not ok:
            out.append(dict(rec, state=NOT_ADJACENT, nearest_clear_gap_in_text_heights=round(min(s[1] for s in scored) / h, 3)
                            if h else None))
            continue
        if len(near) > 1:
            out.append(dict(rec, state=AMBIGUOUS, candidates=len(near),
                            gaps_in_text_heights=sorted(round(s[1] / h, 3) for s in near)))
            continue
        p, g, _ = ok[0]
        a, b = p["lines"]
        dev = round(p["sep"] * umm - sec["B_cm"] * 10.0, 1) if deviation_mm else None
        out.append(dict(rec, state=BOUND if dev is None else BOUND_DEV, width_deviation_mm=dev,
                        drawn_breadth_mm=round(p["sep"] * umm, 1), clear_gap_in_text_heights=round(g / h, 3) if h else None,
                        tag_overlaps_band=g == 0.0, band=_band_record(p)))
    return out


def _band_record(p) -> dict:
    a, b = p["lines"]
    mid = (p["lo"] + p["hi"]) / 2.0
    u, n = p["u"], p["n"]
    pt = lambda t: [round(u[0] * t + n[0] * mid, 3), round(u[1] * t + n[1] * mid, 3)]
    return {"edge_keys": [a["keys"], b["keys"]], "angle_rad": round(p["angle"], 9), "u": [round(v, 12) for v in u],
            "n": [round(v, 12) for v in n], "lo": round(p["lo"], 3), "hi": round(p["hi"], 3), "t0": round(p["t0"], 3),
            "t1": round(p["t1"], 3), "tag_t": round(p["tc"], 3), "centreline": [pt(p["t0"]), pt(p["t1"])]}


def band_polygon(band) -> list:
    u, n = band["u"], band["n"]
    P = lambda t, o: (u[0] * t + n[0] * o, u[1] * t + n[1] * o)
    return [P(band["t0"], band["lo"]), P(band["t1"], band["lo"]), P(band["t1"], band["hi"]), P(band["t0"], band["hi"])]


def _inside(poly, x, y) -> bool:
    inside, k = False, len(poly)
    for i in range(k):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % k]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def lengths(band, supports, *, umm, step, schedule_spans_m=None) -> dict:
    """supports [{"id", "polygon"}] outlines a beam may stop in (columns, other bands). Walk the band centre line from
    the tag outwards in `step` increments (native)."""
    u, n = band["u"], band["n"]
    mid = (band["lo"] + band["hi"]) / 2.0
    at = lambda t: (u[0] * t + n[0] * mid, u[1] * t + n[1] * mid)
    drawn = (band["t1"] - band["t0"]) * umm / 1000.0
    res = {"PLAN_DRAWN_EXTENT": round(drawn, 6)}
    ends = {}
    for side, sgn in (("lo", -1), ("hi", 1)):
        t = band["tag_t"]
        hit = None
        lim = band["t0"] - step if sgn < 0 else band["t1"] + step
        while (t >= lim) if sgn < 0 else (t <= lim):
            x, y = at(t)
            s = next((c for c in supports if _inside(c["polygon"], x, y)), None)
            if s is not None:
                proj = [px * u[0] + py * u[1] for px, py in s["polygon"]]
                ends[side] = {"support": s["id"], "face_t": t, "centre_t": (min(proj) + max(proj)) / 2.0}
                break
            t += sgn * step
        if side not in ends:
            ends[side] = None
    res["ends"] = {k: (v and {"support": v["support"]}) for k, v in ends.items()}
    if ends["lo"] and ends["hi"]:
        res["CLEAR_FACE_TO_FACE_LENGTH"] = round((ends["hi"]["face_t"] - ends["lo"]["face_t"]) * umm / 1000.0, 6)
        res["SUPPORT_CENTRELINE_LENGTH"] = round((ends["hi"]["centre_t"] - ends["lo"]["centre_t"]) * umm / 1000.0, 6)
        res["state"] = "BOTH_ENDS_SUPPORTED"
    else:
        res["CLEAR_FACE_TO_FACE_LENGTH"] = None
        res["SUPPORT_CENTRELINE_LENGTH"] = None
        res["state"] = "FREE_END" if (ends["lo"] or ends["hi"]) else "NO_SUPPORT_MET"
    res["SCHEDULE_SPAN_LENGTH"] = round(sum(schedule_spans_m), 6) if schedule_spans_m else None
    res["step_native"] = step
    return res


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "gap_factor_text_heights": GAP_FACTOR, "margin_factor_text_heights": MARGIN_FACTOR,
           "char_width": CHAR_WIDTH, "angle_tol_deg": ANGLE_TOL_DEG, "width_deviation_max": WIDTH_DEVIATION_MAX,
           "namespaces": NAMESPACES,
           "constraints": ["breadth = scheduled B of the tag's own type", "band parallel to the tag baseline",
                           "tag centre inside the common span", "tag inside or within GAP_FACTOR text heights, nothing between",
                           "unique within MARGIN_FACTOR text heights"],
           "length_bases": ["PLAN_DRAWN_EXTENT", "CLEAR_FACE_TO_FACE_LENGTH", "SUPPORT_CENTRELINE_LENGTH", "SCHEDULE_SPAN_LENGTH"],
           "never": ["nearest-text association", "a type from another namespace", "a length fitted to any target"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec


# ------------------------------------------------------------------ supports along a bound band
def _line_hit(band, seg):
    """Parameter t on the band axis where segment seg crosses the band centre line (None if it does not)."""
    u, n = band["u"], band["n"]
    mid = (band["lo"] + band["hi"]) / 2.0
    _, x1, y1, x2, y2 = seg
    o1 = x1 * n[0] + y1 * n[1] - mid
    o2 = x2 * n[0] + y2 * n[1] - mid
    if (o1 > 0) == (o2 > 0) or o1 == o2:
        return None
    f = o1 / (o1 - o2)
    x, y = x1 + f * (x2 - x1), y1 + f * (y2 - y1)
    return x * u[0] + y * u[1]


def supports(band, segments, *, eps, max_support_native, margin_native, columns=()) -> list:
    """Support intervals along the band centre line.
    columns  [{"id", "polygon"}]: a column outline the centre line passes through is one support over its projected
             extent (two faces, centre known).
    segments element lines (beam edges): a line that properly crosses the centre line is a face; two parallel faces
             <= max_support_native apart with no other crossing between are one support (a girder, two faces); an
             unpaired crossing is a one-face support (centre unknown). A line that only meets the band edge - a beam
             framing in from one side - is not a support."""
    own = set(band["edge_keys"][0]) | set(band["edge_keys"][1])
    u, n = band["u"], band["n"]
    mid = (band["lo"] + band["hi"]) / 2.0
    lo_lim, hi_lim = band["t0"] - margin_native, band["t1"] + margin_native
    out = []
    for c in columns:
        poly = c["polygon"]
        ts = []
        k = len(poly)
        for i in range(k):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % k]
            t = _line_hit(band, ("", x1, y1, x2, y2))
            if t is not None:
                ts.append(t)
        if len(ts) >= 2 and lo_lim <= min(ts) and max(ts) <= hi_lim:
            out.append({"t_a": round(min(ts), 6), "t_b": round(max(ts), 6), "faces": 2, "keys": [c["id"]], "kind": "COLUMN"})
    hits = []
    for seg in segments:
        if seg[0] in own:
            continue
        t = _line_hit(band, seg)
        if t is None or not (lo_lim <= t <= hi_lim):
            continue
        if any(g["t_a"] - eps <= t <= g["t_b"] + eps for g in out if g["kind"] == "COLUMN"):
            continue                                            # a beam line drawn into a column face
        _, x1, y1, x2, y2 = seg
        hits.append((round(t, 6), seg[0], _canon(x2 - x1, y2 - y1, 1e-3)))
    hits.sort()
    merged = []
    for t, k, a in hits:
        if merged and t - merged[-1]["t"] <= eps and abs(merged[-1]["a"] - a) <= 1e-3:
            merged[-1]["keys"].append(k)
        else:
            merged.append({"t": t, "a": a, "keys": [k]})
    i = 0
    while i < len(merged):
        h = merged[i]
        nx = merged[i + 1] if i + 1 < len(merged) else None
        if nx and nx["t"] - h["t"] <= max_support_native and abs(nx["a"] - h["a"]) <= 1e-3:
            out.append({"t_a": h["t"], "t_b": nx["t"], "faces": 2, "keys": h["keys"] + nx["keys"], "kind": "BEAM"})
            i += 2
        else:
            out.append({"t_a": h["t"], "t_b": h["t"], "faces": 1, "keys": h["keys"], "kind": "FACE"})
            i += 1
    out.sort(key=lambda g: (g["t_a"], g["t_b"]))
    return out


def occurrences(bound, segments, *, umm, eps, max_support_mm, schedule_spans=None, columns=()) -> dict:
    """bound: bind() records in a BOUND state on one sheet. A SIMPLE / OTHER tag names the one support-bounded segment
    holding it; a CONTINUOUS type names the run of segments from the first to the last of its tags on that band.
    Two different types on overlapping segments -> BAND_TYPE_CONFLICT (all of them blocked); a second tag of the same
    simple type on the same segment is REPEATED_TAG (one occurrence)."""
    schedule_spans = schedule_spans or {}
    by_band = {}
    for r in bound:
        k = json.dumps(r["band"]["edge_keys"])
        by_band.setdefault(k, []).append(r)
    occ, notes = [], []
    for k in sorted(by_band):
        rs = sorted(by_band[k], key=lambda r: r["band"]["tag_t"])
        band = rs[0]["band"]
        sup = supports(band, segments, eps=eps, max_support_native=max_support_mm / umm,
                       margin_native=max_support_mm / umm, columns=columns)
        def seg_of(t):
            lo = max((g for g in sup if g["t_b"] < t), key=lambda g: g["t_b"], default=None)
            hi = min((g for g in sup if g["t_a"] > t), key=lambda g: g["t_a"], default=None)
            return lo, hi
        items = []
        for r in rs:
            lo, hi = seg_of(r["band"]["tag_t"])
            inside = any(g["t_a"] <= r["band"]["tag_t"] <= g["t_b"] for g in sup)
            items.append({"rec": r, "lo": lo, "hi": hi, "inside_support": inside})
        groups = {}
        for it in items:
            t = it["rec"]["type"]
            groups.setdefault(t, []).append(it)
        spans = []
        for t, its in sorted(groups.items()):
            ns = namespace(t)
            if ns == "CONTINUOUS":
                spans.append({"type": t, "items": its, "lo": its[0]["lo"], "hi": its[-1]["hi"], "kind": ns})
            else:
                seen = {}
                for it in its:
                    key = (it["lo"] and it["lo"]["t_a"], it["hi"] and it["hi"]["t_a"])
                    if key in seen:
                        seen[key]["items"].append(it)
                        notes.append({"band": k, "type": t, "mark_key": it["rec"]["mark_key"], "note": "REPEATED_TAG"})
                    else:
                        seen[key] = {"type": t, "items": [it], "lo": it["lo"], "hi": it["hi"], "kind": ns}
                spans.extend(seen.values())
        def extent(sp):
            a = sp["lo"]["t_b"] if sp["lo"] else band["t0"]
            b = sp["hi"]["t_a"] if sp["hi"] else band["t1"]
            return a, b
        for sp in spans:
            a, b = extent(sp)
            others = [o for o in spans if o is not sp and o["type"] != sp["type"]
                      and min(b, extent(o)[1]) - max(a, extent(o)[0]) > eps]
            sp["conflict"] = sorted({o["type"] for o in others})
        for sp in spans:
            its = sp["items"]
            rec = {"type": sp["type"], "namespace": sp["kind"], "band": k, "tags": [i["rec"]["mark_key"] for i in its],
                   "B_cm": its[0]["rec"]["B_cm"], "D_cm": its[0]["rec"]["D_cm"],
                   "drawn_breadth_mm": its[0]["rec"]["drawn_breadth_mm"], "band_record": band}
            if sp["conflict"]:
                occ.append(dict(rec, state="BAND_TYPE_CONFLICT", conflict_with=sp["conflict"], lengths=None))
                continue
            if any(i["inside_support"] for i in its):
                occ.append(dict(rec, state="TAG_INSIDE_SUPPORT", lengths=None))
                continue
            lo, hi = sp["lo"], sp["hi"]
            L = {"PLAN_DRAWN_EXTENT": None, "CLEAR_FACE_TO_FACE_LENGTH": None, "SUPPORT_CENTRELINE_LENGTH": None,
                 "SCHEDULE_SPAN_LENGTH": (round(sum(schedule_spans[sp["type"]]), 6) if sp["type"] in schedule_spans else None)}
            interior = [g for g in sup if lo and hi and lo["t_b"] < g["t_a"] and g["t_b"] < hi["t_a"]]
            if lo and hi:
                inner = sum(g["t_b"] - g["t_a"] for g in interior)
                L["CLEAR_FACE_TO_FACE_LENGTH"] = round((hi["t_a"] - lo["t_b"] - inner) * umm / 1000.0, 6)
                if lo["faces"] == 2 and hi["faces"] == 2:
                    L["SUPPORT_CENTRELINE_LENGTH"] = round(((hi["t_a"] + hi["t_b"]) - (lo["t_a"] + lo["t_b"])) / 2.0 * umm / 1000.0, 6)
                a0 = lo["t_a"] if lo["faces"] == 2 else lo["t_b"]
                b0 = hi["t_b"] if hi["faces"] == 2 else hi["t_a"]
                L["PLAN_DRAWN_EXTENT"] = round((min(b0, band["t1"]) - max(a0, band["t0"])) * umm / 1000.0, 6)
                state = "MEASURED"
            else:
                a, b = extent(sp)
                L["PLAN_DRAWN_EXTENT"] = round((b - a) * umm / 1000.0, 6)
                state = "FREE_END"
            n_seg = len(interior) + 1 if lo and hi else None
            occ.append(dict(rec, state=state, lengths=L, segments_between_supports=n_seg,
                            interior_supports=len(interior),
                            supports_used=[{"kind": g["kind"], "keys": g["keys"]} for g in
                                           ([lo] if lo else []) + interior + ([hi] if hi else [])]))
    return {"occurrences": occ, "notes": notes}

"""Tolerance-aware reconciliation of two CAD routes (K1 vs K2, or D1 vs D1') — R8.2 §14-§16.

Never averages, never votes, never prefers the route closer to a benchmark.
It says, object by object, whether two independent realisations of the same
source agree, and why not when they do not.

CORRELATION (identity first)
    Each realised item is keyed by its SOURCE identity:
        (source handle, instance path of INSERT handles + MINSERT cell, family, span)
    Blocks are correlated by BLOCK-RECORD HANDLE, never by name (anonymous
    *U names differ between routes). Within one source object with several
    items (polyline spans) an item may be disambiguated by geometry only when
    exactly one candidate lies within tolerance; otherwise
    AMBIGUOUS_CORRELATION. No cross-object nearest-neighbour matching, ever.
    A D1 handle printed truncated ('v+3B', see libredwg_map) can correlate
    only to a D2 handle whose low 16 bits are v and which exceeds 0xFFFF —
    reported as the weaker basis TRUNCATED_HANDLE_LOW_BITS.

PER-ITEM RESULT: PASS / WARN / BLOCK (+ field_class), or
    UNMATCHED_A / UNMATCHED_B (PRESENCE), AMBIGUOUS_CORRELATION,
    KNOWN_LIBRARY_LIMITATION (a pre-registered limitation of one route holds here).

VERDICT
    SOURCE_DECODE_CONFLICT  a correlated object disagrees beyond tolerance (scope SOURCE)
    BLOCK                   content present in one route only, visibility / block
                            lineage disagreement, or ambiguous correlation
    KNOWN_LIBRARY_LIMITATION  every disagreement is explained by a pre-registered limitation
    WARN                    only sub-significance numeric differences
    PASS

TOLERANCES (declared before any real-project comparison; never tuned to a result)
    SYNTHETIC: fixture coordinates are exact decimals; pass 1e-9, warn 1e-6 native units.
    REAL: numerical noise only, relative to the drawing's own coordinate magnitude M:
        pass = max(1024 * eps * M, decimal-text step)   eps = 2**-52
        warn = 1e6 * eps * M
      1024 eps M bounds 16 nesting levels x ~8 flops x 4 ulp with 2x margin; the text
      step covers a route that prints fewer significant digits than float64 holds.
      Nothing here uses a project total, room or quantity. Units are NOT assumed:
      tolerances are in native units because no unit context exists yet (R8.3).
    Curve centres/radii are ill-conditioned for shallow arcs; their tolerance is the
    position tolerance x max(1, radius/chord). End and mid points use the position tolerance.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

EPS = 2.0 ** -52
PASS, WARN, BLOCK = "PASS", "WARN", "BLOCK"
UNMATCHED_A, UNMATCHED_B, AMBIGUOUS = "UNMATCHED_A", "UNMATCHED_B", "AMBIGUOUS_CORRELATION"
KNOWN_LIMITATION = "KNOWN_LIBRARY_LIMITATION"
SOURCE_DECODE_CONFLICT = "SOURCE_DECODE_CONFLICT"


class Tolerance:
    def __init__(self, name, position_pass, position_warn, basis):
        self.name, self.position_pass, self.position_warn, self.basis = name, position_pass, position_warn, basis

    def as_dict(self):
        return {"name": self.name, "position_pass": self.position_pass, "position_warn": self.position_warn,
                "basis": self.basis}


SYNTHETIC = Tolerance("SYNTHETIC", 1e-9, 1e-6, "exact decimal fixtures; float64 noise of composed maps is ~1e-12")


def real_tolerance(coordinate_magnitude: float, decimal_digits: int | None = None) -> Tolerance:
    m = max(1.0, float(coordinate_magnitude))
    p = 1024.0 * EPS * m
    if decimal_digits:
        p = max(p, 2.0 * m * 10.0 ** (-(decimal_digits - 1)))
    return Tolerance("REAL", p, max(1e6 * EPS * m, 10.0 * p),
                     f"1024*eps*M with M={m:g}" + (f"; text step {decimal_digits} digits" if decimal_digits else ""))


# ---------------------------------------------------------------- route items
def _strip(h):
    if h is None:
        return None
    h = str(h)
    return h.split(":", 1)[1] if h[:3] in ("D1:", "D2:") else h


def _family(kind):
    return kind


def route_items(realised) -> dict:
    """Group a RealisedGeometry into {(handle, path): [items]} per family."""
    items = defaultdict(list)

    def key(lin):
        return (_strip(lin.source_handle if lin.source_handle is not None else lin.obs_id),
                tuple(_strip(p) for p in lin.instance_path))

    for s in realised.segments:
        items[key(s.lineage) + ("SEGMENT",)].append({"family": "SEGMENT", "pts": [s.a, s.b], "kind": s.lineage.kind})
    for a in realised.arcs:
        items[key(a.lineage) + ("CIRCULAR_ARC",)].append({"family": "CIRCULAR_ARC", "center": a.center, "radius": a.radius,
                                                           "start": a.start, "mid": a.mid, "end": a.end,
                                                           "direction": a.direction, "source": a.source,
                                                           "kind": a.lineage.kind})
    for c in realised.circles:
        items[key(c.lineage) + ("CIRCLE",)].append({"family": "CIRCLE", "center": c.center, "radius": c.radius,
                                                     "kind": c.lineage.kind})
    for e in realised.elliptical_arcs:
        items[key(e.lineage) + ("ELLIPTICAL_ARC",)].append({"family": "ELLIPTICAL_ARC", "center": e.center,
                                                             "start": e.start, "mid": e.mid, "end": e.end,
                                                             "direction": e.direction, "full": e.full,
                                                             "kind": e.lineage.kind})
    return items


def _d(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _compare(a, b, tol):
    """(status, field_class, max_delta)."""
    f = a["family"]
    if f != b["family"]:
        return BLOCK, "KIND", None
    if f == "SEGMENT":
        d = min(max(_d(a["pts"][0], b["pts"][0]), _d(a["pts"][1], b["pts"][1])),
                max(_d(a["pts"][0], b["pts"][1]), _d(a["pts"][1], b["pts"][0])))
        return _grade(d, tol, "POSITION")
    if f == "CIRCLE":
        return _grade(max(_d(a["center"], b["center"]), abs(a["radius"] - b["radius"])), tol, "POSITION")
    fwd = max(_d(a["start"], b["start"]), _d(a["end"], b["end"]))
    rev = max(_d(a["start"], b["end"]), _d(a["end"], b["start"]))
    same_dir = a["direction"] == b["direction"]
    # the same physical arc traversed the other way is the same arc with reversed direction
    if fwd <= rev:
        d_ends, dir_ok = fwd, same_dir
    else:
        d_ends, dir_ok = rev, not same_dir
    d_mid = _d(a["mid"], b["mid"])
    pos = max(d_ends, d_mid)
    if not dir_ok:
        return BLOCK, "ORIENTATION", pos
    st, fc, _ = _grade(pos, tol, "POSITION")
    if f == "CIRCULAR_ARC":
        chord = max(_d(a["start"], a["end"]), 1e-300)
        k = max(1.0, a["radius"] / chord)
        dc = max(_d(a["center"], b["center"]), abs(a["radius"] - b["radius"]))
        st2, fc2, _ = _grade(dc, Tolerance("C", tol.position_pass * k, tol.position_warn * k, ""), "CURVE_CENTRE")
        if [PASS, WARN, BLOCK].index(st2) > [PASS, WARN, BLOCK].index(st):
            return st2, fc2, max(pos, dc)
        return st, fc, max(pos, dc)
    return st, fc, max(pos, _d(a["center"], b["center"]))


def _grade(d, tol, field_class):
    if d <= tol.position_pass:
        return PASS, None, d
    if d <= tol.position_warn:
        return WARN, field_class, d
    return BLOCK, field_class, d


def _correlate_key(ka, kbs):
    """Exact identity, else truncated-handle low-bits correlation (unique only)."""
    if ka in kbs:
        return ka, "SOURCE_HANDLE"

    def trunc_match(x, y):
        if x == y:
            return True
        if x and x.endswith("+3B"):
            v = x[:-3].split("[")[0]
            tail = x[len(x.split("[")[0]):] if "[" in x else ""
            yy, ytail = y.split("[")[0], (y[len(y.split("[")[0]):] if "[" in y else "")
            try:
                return tail == ytail and int(yy) > 0xFFFF and (int(yy) & 0xFFFF) == int(v)
            except ValueError:
                return False
        return False

    cands = [kb for kb in kbs if kb[2] == ka[2] and len(kb[1]) == len(ka[1]) and trunc_match(ka[0], kb[0])
             and all(trunc_match(x, y) for x, y in zip(ka[1], kb[1]))]
    if len(cands) == 1:
        return cands[0], "TRUNCATED_HANDLE_LOW_BITS"
    if len(cands) > 1:
        return None, AMBIGUOUS
    return None, None


def _match_group(key, la, lb, tol, basis, lim):
    """Items of ONE source object (same handle, instance path and family)."""
    out = []

    def row(st, fc, d, fam):
        if st == BLOCK and lim:
            st = KNOWN_LIMITATION
        return {"key": list(key), "status": st, "field_class": fc, "max_delta": d, "family": fam, "basis": basis}

    if len(la) == 1 and len(lb) == 1:
        st, fc, d = _compare(la[0], lb[0], tol)
        return [row(st, fc, d, la[0]["family"])]
    left = []
    for it in la:
        cands = [j for j, other in enumerate(lb) if _compare(it, other, tol)[0] in (PASS, WARN)]
        if len(cands) == 1:
            st, fc, d = _compare(it, lb[cands[0]], tol)
            out.append(row(st, fc, d, it["family"]))
            lb.pop(cands[0])
        elif len(cands) > 1:
            out.append({"key": list(key), "status": AMBIGUOUS, "field_class": "CORRELATION",
                        "family": it["family"], "basis": basis})
            lb.pop(cands[0])
        else:
            left.append(it)
    for it in left:                       # same object, no item within tolerance: a geometry disagreement
        if lb:
            st, fc, d = _compare(it, lb.pop(0), tol)
            out.append(row(BLOCK if st == PASS else st, fc or "POSITION", d, it["family"]))
        else:
            out.append({"key": list(key), "status": KNOWN_LIMITATION if lim else UNMATCHED_A,
                        "field_class": "PRESENCE", "family": it["family"], "basis": basis})
    for it in lb:
        out.append({"key": list(key), "status": KNOWN_LIMITATION if lim else UNMATCHED_B,
                    "field_class": "PRESENCE", "family": it["family"], "basis": basis})
    return out


def reconcile(a, b, tolerance: Tolerance = SYNTHETIC, known_limitations_b=(), insert_blocks_a=None,
              insert_blocks_b=None, name_a="A", name_b="B") -> dict:
    """a, b: RealisedGeometry of two routes. known_limitations_b: [(handle, path)] where route
    B raised a pre-registered KNOWN_LIBRARY_LIMITATION. insert_blocks_*: {insert handle: block record handle}."""
    ia, ib = route_items(a), route_items(b)
    rows = []
    used_b = set()
    limited = {(_strip(h), tuple(_strip(x) for x in p)) for h, p in known_limitations_b}
    bases = Counter()
    for ka, la in sorted(ia.items(), key=lambda kv: str(kv[0])):
        kb, basis = _correlate_key(ka, set(ib) - used_b)
        lim = (ka[0], ka[1]) in limited or (kb is not None and (kb[0], kb[1]) in limited)
        if kb is None:
            st = AMBIGUOUS if basis == AMBIGUOUS else UNMATCHED_A
            for it in la:
                rows.append({"key": list(ka), "status": KNOWN_LIMITATION if lim else st,
                             "field_class": "PRESENCE", "family": it["family"]})
            continue
        used_b.add(kb)
        bases[basis] += 1
        rows.extend(_match_group(ka, list(la), list(ib[kb]), tolerance, basis, lim))
    for kb, lb in ib.items():
        if kb in used_b:
            continue
        lim = (kb[0], kb[1]) in limited
        for it in lb:
            rows.append({"key": list(kb), "status": KNOWN_LIMITATION if lim else UNMATCHED_B,
                         "field_class": "PRESENCE", "family": it["family"]})
    # visibility: hidden observations must agree by (handle, path)
    ha = Counter((_strip(h["obs_id"]), tuple(_strip(x) for x in h["instance_path"])) for h in a.hidden)
    hb = Counter((_strip(h["obs_id"]), tuple(_strip(x) for x in h["instance_path"])) for h in b.hidden)
    for k in (ha - hb) + (hb - ha):
        rows.append({"key": list(k), "status": BLOCK, "field_class": "VISIBILITY", "family": "HIDDEN"})
    # block lineage by record handle (names never compared)
    block_rows = 0
    if insert_blocks_a is not None and insert_blocks_b is not None:
        for ins, blk in insert_blocks_a.items():
            other = insert_blocks_b.get(ins)
            if other is not None and _strip(other) != _strip(blk):
                rows.append({"key": [ins], "status": BLOCK, "field_class": "BLOCK_LINEAGE", "family": "INSERT"})
            block_rows += other is not None
    status = Counter(r["status"] for r in rows)
    fields = Counter(r["field_class"] for r in rows if r["status"] not in (PASS,))
    geometry_conflict = any(r["status"] == BLOCK and r["field_class"] in ("POSITION", "CURVE_CENTRE", "ORIENTATION", "KIND")
                            for r in rows)
    presence = status[UNMATCHED_A] + status[UNMATCHED_B]
    other_block = any(r["status"] == BLOCK and r["field_class"] in ("VISIBILITY", "BLOCK_LINEAGE") for r in rows)
    if geometry_conflict:
        verdict, field_class, scope = SOURCE_DECODE_CONFLICT, "GEOMETRY", "SOURCE"
    elif presence or other_block or status[AMBIGUOUS]:
        verdict = BLOCK
        field_class = "PRESENCE" if presence else ("CORRELATION" if status[AMBIGUOUS] else
                                                   next(r["field_class"] for r in rows if r["status"] == BLOCK))
        scope = "ROUTE"
    elif status[KNOWN_LIMITATION]:
        verdict, field_class, scope = KNOWN_LIMITATION, "KNOWN_LIBRARY_LIMITATION", "ROUTE"
    elif status[WARN]:
        verdict, field_class, scope = WARN, "POSITION", "NUMERIC"
    else:
        verdict, field_class, scope = PASS, None, None
    return {"verdict": verdict, "field_class": field_class, "scope": scope,
            "correlated_by": "BLOCK_RECORD_HANDLE" if block_rows else "SOURCE_HANDLE",
            "correlation_bases": dict(bases), "tolerance": tolerance.as_dict(),
            "counts": dict(status), "non_pass_by_field": dict(fields), "items": rows,
            "routes": [name_a, name_b]}

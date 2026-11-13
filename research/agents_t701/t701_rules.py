"""T-701 rules (every villa): reconcile an engine finish line (plaster / paint, m2) against a reference takeoff to
named physical or rule causes, and check that a held line covers the bound of the datum it hangs on.

R-T701-1 ROOM BRIDGE (exact, per room, per end of the engine range). For one face set of one room:
    his gross G = sum(L_i x F_i) over his rows (m2); his weighted length L_h = sum(L_i), height F_w = G / L_h;
    engine: drawn face L_e (lm), height basis H (m) of the layer (plaster: slab / roof underside, Q-72; paint: finished
    ceiling, Q-48 A), engine net N (m2) at that end of its range.
      LENGTH     = G - L_e x F_w             (his lengths vs the drawn faces)
      HEIGHT     = L_e x (F_w - H)           (his flat height vs the layer's height basis)
      DEDUCTIONS = L_e x H - N               (openings in full Q-73, beam ends, held items: what the engine removes)
    LENGTH + HEIGHT + DEDUCTIONS = G - N exactly (Decimal, asserted). Every term keeps its unit (m2); lm and m are
    inputs only. A line with no engine value (HELD blank) is NOT bridged: it is listed, never 0. A height outside
    0 < H <= 15 m (a level in mm or cm), a net above the gross (negative deductions) or low > high is refused.
    His half-deduction of his opening list is his own step on the whole statement, never a component of a room.
R-T701-2 DATUM BOUND COVERAGE. A held line whose height hangs on a datum that merged records bound (s_lo .. s_hi) must
    carry the net at both ends of that bound: low = L_e x S_lo - fixed - w_held x S_lo - beam ends, high = L_e x S_hi
    - fixed - beam ends (a held opening of width w with no printed height is 0 .. w x S). A line priced at one
    scenario inside the bound is NARROW: the corrected bound replaces it at integration (HELD, never a point).
R-T701-3 ONE FINISH PER FACE. A face under full-height porcelain carries the wet-wall render (plaster trade line) but
    no paint; a paint figure on such a face is refused.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

CAUSES = ("ENGINE_RIGHT", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "UNRESOLVED", "HELD", "ENGINE_WRONG",
          "ENGINE_OMISSION")
H_MAX = Decimal("15")   # a storey / shaft height in metres; above this the input is a level in mm / cm


def D(x):
    if x is None:
        raise ValueError("missing value (HELD stays HELD, never 0)")
    if isinstance(x, float):
        raise TypeError("pass numbers as strings or Decimal, not float")
    return Decimal(str(x))


def q6(x):
    return D(x).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _height(h, what):
    h = D(h)
    if not (Decimal(0) < h <= H_MAX):
        raise ValueError(f"{what}: height {h} m outside 0 .. {H_MAX} m (a level in mm / cm?)")
    return h


def his_gross(rows):
    """rows: [(length lm, height m)] -> (gross m2, total length lm, weighted height m)."""
    if not rows:
        raise ValueError("no reference rows")
    g = sum((D(L) * _height(F, "his row") for L, F in rows), Decimal(0))
    lh = sum((D(L) for L, _ in rows), Decimal(0))
    if lh <= 0:
        raise ValueError("reference length must be > 0")
    return g, lh, g / lh


def room_bridge(rows, face_lm, ends):
    """R-T701-1. ends: {'low': (H, N), 'high': (H, N)} -> per end {gap, LENGTH, HEIGHT, DEDUCTIONS} (m2, exact)."""
    G, lh, fw = his_gross(rows)
    le = D(face_lm)
    if le <= 0:
        raise ValueError("drawn face must be > 0 lm")
    if set(ends) != {"low", "high"}:
        raise ValueError("both ends of the engine range are needed")
    if D(ends["low"][1]) > D(ends["high"][1]):
        raise ValueError("engine low > high")
    out = {"his_gross": q6(G), "his_length_lm": q6(lh), "his_weighted_height_m": q6(fw), "face_lm": q6(le)}
    for k in ("low", "high"):
        h = _height(ends[k][0], f"engine {k}")
        n = D(ends[k][1])
        if n <= 0:
            raise ValueError(f"engine {k} net {n} <= 0: a blank line is listed, never bridged as 0")
        length = G - le * fw
        height = le * (fw - h)
        ded = le * h - n
        if ded < 0:
            raise ValueError(f"engine {k}: net {n} above its gross {le * h}")
        gap = G - n
        if abs(length + height + ded - gap) > Decimal("1e-12"):   # F_w = G / L_h may not terminate
            raise AssertionError("bridge does not close")
        out[k] = {"H_m": q6(h), "net": q6(n), "gap": q6(gap), "LENGTH": q6(length), "HEIGHT": q6(height),
                  "DEDUCTIONS": q6(ded)}
    return out


def pair_close(his, eng_low, eng_high, components):
    """components: [(name, at_engine_low_end, at_engine_high_end, cause)]; each end must sum to his - engine exactly."""
    his, lo, hi = D(his), D(eng_low), D(eng_high)
    if lo > hi:
        raise ValueError("engine low > high")
    for name, a, b, cause in components:
        if cause not in CAUSES:
            raise ValueError(f"{name}: unknown cause {cause}")
    s_lo = sum((D(a) for _, a, _, _ in components), Decimal(0))
    s_hi = sum((D(b) for _, _, b, _ in components), Decimal(0))
    if s_lo != his - lo or s_hi != his - hi:
        raise AssertionError(f"pair does not close: {s_lo} vs {his - lo}, {s_hi} vs {his - hi}")
    by = {}
    for _, a, b, cause in components:
        x = by.setdefault(cause, [Decimal(0), Decimal(0)])
        x[0] += D(a)
        x[1] += D(b)
    return {"gap_at_engine_low": q6(his - lo), "gap_at_engine_high": q6(his - hi),
            "by_cause": {k: [q6(v[0]), q6(v[1])] for k, v in sorted(by.items())}}


def datum_bound(face_lm, s_lo, s_hi, fixed, held_width="0", beam_ends="0"):
    """R-T701-2: net bound of a face over a bounded soffit / top S (m) -> (low, high) m2."""
    le = D(face_lm)
    a, b = _height(s_lo, "datum low"), _height(s_hi, "datum high")
    if a > b:
        raise ValueError("datum low > high")
    f, w, be = D(fixed), D(held_width), D(beam_ends)
    if min(le, f, w, be) < 0:
        raise ValueError("negative term")
    low = le * a - f - w * a - be
    high = le * b - f - be
    if low <= 0:
        raise ValueError("bound low <= 0: deductions exceed the face (check units / inputs)")
    return q6(low), q6(high)


def coverage(line_low, line_high, bound):
    """R-T701-2: COVERED when the line's range contains the datum bound, else NARROW with the corrected bound."""
    lo, hi = D(line_low), D(line_high)
    blo, bhi = bound
    if lo <= blo and hi >= bhi:
        return {"status": "COVERED", "line": [q6(lo), q6(hi)], "bound": [blo, bhi]}
    return {"status": "NARROW", "line": [q6(lo), q6(hi)], "bound": [blo, bhi],
            "change": [q6(blo - lo), q6(bhi - hi)]}


def finish_layers(face_lm, soffit, ceiling, openings, tiled=False, paint=None):
    """R-T701-3 + the two height bases on one face set: -> {'plaster': m2, 'paint': m2 or None}.
    openings: [(width, height)] fully inside the paint height. A tiled (full-height porcelain) face takes the render
    (plaster trade) and no paint; passing a paint figure for it is refused."""
    le = D(face_lm)
    s, c = _height(soffit, "soffit"), _height(ceiling, "ceiling")
    if c > s:
        raise ValueError("finished ceiling above the structural soffit")
    op = sum((D(w) * _height(h, "opening") for w, h in openings), Decimal(0))
    for w, h in openings:
        if D(h) > c:
            raise ValueError("opening head above the paint height: split it by layer first")
    if tiled:
        if paint is not None:
            raise ValueError("paint on a full-height tiled face (one finish per face)")
        # render to the tile top (= finished ceiling) by the tiler; the band above is its own plaster line
        return {"plaster_render": q6(le * c - op), "band_above_ceiling": q6(le * (s - c)), "paint": None}
    return {"plaster": q6(le * s - op), "paint": q6(le * c - op)}

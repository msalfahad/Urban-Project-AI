"""T-740 PAINT AREA RULE (UP-FIN-PAINT-002 1.0.0, rules/rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json; every villa;
research, unwired: no method, candidate or default reads this module).

Owner rule 2026-11-12 (main chat; board top note 'OWNER RULE 2026-11-12 PAINT'; AGENT_BRIEF 'Paint area'): "Paint,
technically would be close enough to plastering (inside the building) outside will also should be the same, the
difference is with the corners outside maybe only and lm for windows doors and corners, so the Area is the same."
Confirmed in the same session: paint stops at the false ceiling (Q-72 kept) and tiled faces get no paint.

R-T740-1  PAINT FACE = PLASTER FACE. For every plastered face (internal or external, wall or soffit):
              paint m2 = plaster m2 of the same face - the band above a false ceiling - the tiled part of the face
          Corners, beads and window / door edges are lm items beside the m2, never extra paint area. The two ends of a
          HELD range are paired by scenario (low with low, high with high): the band and tile terms of one end are the
          ones of the same scenario as that end's plaster figure. A HELD (blank) plaster face gives a HELD paint face,
          never 0; an unknown band or tile part gives an AT_MOST paint face (upper end only), never a guessed value.
          A face whose whole plaster area is tiled has NO paint face (0 by the rule, a determined zero, not a missing
          value).
R-T740-2  BAND PART OF A DEDUCTION. The band above a false ceiling on one face = lm x (plaster top - paint top) less
          the part of each deduction that lies inside the band:
              opening   width x overlap([sill, head], [paint top, plaster top])
              beam end  width x min(depth below the soffit, band height) per end; the part of a beam end deeper than
                        the band lies in the painted zone and is a paint deduction too (no wall face there)
          Where no false ceiling is built (a void / double-height face, a stair shaft), there is no band.
R-T740-3  GAP ALLOCATION. On one face the engine's plaster - paint gap = BAND + TILED - (engine paint - rule paint);
          the last term is split into named causes, each computed from its own ledger item (never back-solved from
          the total); what is left is the residual, reported, never hidden.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

RULE_ID = "UP-FIN-PAINT-002"
RULE_VERSION = "1.0.0"
RULEBOOK = "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.2.0.json"
CAUSES = ("BAND", "TILED", "VOID_NO_CEILING", "OPENING_BASIS_MISMATCH", "BEAM_END_BELOW_CEILING", "LEDGER_ROUNDING",
          "PLASTER_CONTACT_NOT_DEDUCTED", "RETURN_RULE_RESTATED")


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("a missing value is HELD, not a number")
    if isinstance(x, float):
        x = repr(x)
    try:
        v = Decimal(str(x))
    except Exception as e:  # noqa: BLE001
        raise RuleError(f"not a number: {x!r}") from e
    if not v.is_finite():
        raise RuleError(f"not finite: {x!r}")
    return v


def q6(x) -> Decimal:
    return D(x).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _m(x, name, hi="30"):
    v = D(x)
    if v < 0:
        raise RuleError(f"{name} negative")
    if v > D(hi):
        raise RuleError(f"{name} {v} looks like mm, not m")
    return v


def _pair(x, name):
    """None -> None (HELD); a number -> (v, v); a (lo, hi) pair -> (lo, hi) with lo <= hi; m2 never negative."""
    if x is None:
        return None
    if isinstance(x, (tuple, list)):
        if len(x) != 2:
            raise RuleError(f"{name}: a range is (low, high)")
        if x[0] is None or x[1] is None:
            return (None if x[0] is None else D(x[0]), None if x[1] is None else D(x[1]))
        lo, hi = D(x[0]), D(x[1])
    else:
        lo = hi = D(x)
    if lo < 0 or hi < 0:
        raise RuleError(f"{name}: negative m2")
    return lo, hi


# ---- R-T740-1 ------------------------------------------------------------------------------------------------------
def paint_face(plaster, band=0, tiled=0, edges_lm=None):
    """paint face of one plastered face under UP-FIN-PAINT-002.

    plaster, band, tiled: m2 as a number, a scenario-paired (low, high) range, or None (HELD / not established).
    edges_lm: corners / beads / reveal edges in lm, passed through beside the m2 and never added to it.
    -> {"status": RULE | NO_PAINT_FACE | AT_MOST | HELD, "paint": (lo, hi) or None, "high": upper end or None, ...}"""
    p = _pair(plaster, "plaster")
    out = {"rule": f"{RULE_ID} {RULE_VERSION}", "edges_lm": None if edges_lm is None else str(q6(_m(edges_lm, "lm", "100000")))}
    if p is None or p[0] is None or p[1] is None:
        return dict(out, status="HELD", paint=None, high=None,
                    why="plaster face HELD: its paint face stays HELD (never 0)")
    b, t = _pair(band, "band"), _pair(tiled, "tiled")
    known_b = b is not None and None not in b
    known_t = t is not None and None not in t
    if not (known_b and known_t):
        # upper end only: every deduction that is known at the high end, the unknown part taken as 0 there
        bh = b[1] if (b is not None and b[1] is not None) else D(0)
        th = t[1] if (t is not None and t[1] is not None) else D(0)
        hi = p[1] - bh - th
        if hi < 0:
            raise RuleError("band + tile exceed the plaster face")
        return dict(out, status="AT_MOST", paint=None, high=q6(hi),
                    why="band or tile part not established: paint is at most this (upper end only), HELD")
    ends = []
    for i in (0, 1):
        v = p[i] - b[i] - t[i]
        if v < 0:
            raise RuleError("band + tile exceed the plaster face (check the scenario pairing / units)")
        ends.append(v)
    lo, hi = min(ends), max(ends)
    if hi == 0:
        return dict(out, status="NO_PAINT_FACE", paint=(q6(0), q6(0)), high=q6(0),
                    why="the whole plaster face is tiled or above the ceiling: no paint face")
    return dict(out, status="RULE", paint=(q6(lo), q6(hi)), high=q6(hi),
                why="paint = plaster - band above the false ceiling - tiled part")


def paint_faces(plaster_faces, ceiling_bands=None, tiled_faces=None):
    """R-T740-1 over many faces keyed by face id: {face: plaster}, {face: band}, {face: tiled} -> {face: result}.
    A band or tile keyed to a face with no plaster face is refused (paint where no plaster: EXCESS, never priced)."""
    ceiling_bands, tiled_faces = ceiling_bands or {}, tiled_faces or {}
    stray = (set(ceiling_bands) | set(tiled_faces)) - set(plaster_faces)
    if stray:
        raise RuleError(f"band / tile on a face with no plaster face: {sorted(stray)}")
    return {f: paint_face(plaster_faces[f], ceiling_bands.get(f, 0), tiled_faces.get(f, 0)) for f in plaster_faces}


# ---- R-T740-2 ------------------------------------------------------------------------------------------------------
def overlap(a0, a1, b0, b1):
    a0, a1, b0, b1 = D(a0), D(a1), D(b0), D(b1)
    if a1 < a0 or b1 < b0:
        raise RuleError("interval end below its start")
    return max(D(0), min(a1, b1) - max(a0, b0))


def opening_band_part(width, sill, head, paint_top, plaster_top):
    """m2 of an opening that lies inside the band [paint top, plaster top] (heights above the finished floor, m)."""
    w = _m(width, "width")
    pt, pl = _m(paint_top, "paint top", "15"), _m(plaster_top, "plaster top", "15")
    if pt > pl:
        raise RuleError("paint top above the plaster top")
    return w * overlap(_m(sill, "sill", "15"), _m(head, "head", "15"), pt, pl)


def opening_paint_part(width, sill, head, paint_top):
    """m2 of an opening below the paint top (the paint deduction)."""
    return _m(width, "width") * overlap(_m(sill, "sill", "15"), _m(head, "head", "15"), D(0), _m(paint_top, "paint top", "15"))


def beam_end_split(width, depth_below_soffit, band_height, ends):
    """one beam framing into the face: (in band, below the ceiling) m2 over `ends` ends."""
    w, d, h = _m(width, "width", "3"), _m(depth_below_soffit, "depth", "3"), _m(band_height, "band", "15")
    n = D(ends)
    if n < 0 or n != n.to_integral_value():
        raise RuleError("ends is a whole count")
    return q6(n * w * min(d, h)), q6(n * w * max(D(0), d - h))


def band(face_lm, plaster_top, paint_top, band_parts):
    """R-T740-2: lm x (plaster top - paint top) - parts inside the band."""
    pl, pt = _m(plaster_top, "plaster top", "15"), _m(paint_top, "paint top", "15")
    if pt > pl:
        raise RuleError("paint top above the plaster top")
    gross = _m(face_lm, "lm", "1000") * (pl - pt)
    parts = sum((D(x) for x in band_parts), D(0))
    if parts < 0 or parts > gross:
        raise RuleError("band parts outside 0 .. band")
    return q6(gross), q6(gross - parts)


# ---- R-T740-3 ------------------------------------------------------------------------------------------------------
def allocate(plaster, engine_paint, band_m2, tiled_m2, named):
    """one end of one face: gap = plaster - engine paint; rule paint = plaster - band - tiled;
    named = [(cause, m2)] with m2 = engine paint - rule paint per cause (positive: the engine paints more).
    -> dict with the residual ((engine paint - rule paint) - sum(named)) which must be reported, 0 when fully allocated.
    Identity: gap = band + tiled - (engine paint - rule paint)."""
    p, q, b, t = D(plaster), D(engine_paint), D(band_m2), D(tiled_m2)
    for c, _ in named:
        if c not in CAUSES:
            raise RuleError(f"unknown cause {c}")
    gap = p - q
    rule = p - b - t
    s = sum((D(v) for _, v in named), D(0))
    residual = (q - rule) - s
    return {"gap": q6(gap), "rule_paint": q6(rule), "band": q6(b), "tiled": q6(t),
            "named": [(c, str(q6(v))) for c, v in named], "residual": q6(residual)}

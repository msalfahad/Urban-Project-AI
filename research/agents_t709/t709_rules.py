"""T-709 rules (research, unwired; every villa). Decimal arithmetic, metres and m2; HELD is None, never 0.

R-T709-1  DOUBLE-HEIGHT CONTINUITY. A wall face that bounds a slab-free zone (stairwell / void) and is solid on the
          storey below AND above is one face from the lower floor to the upper roof soffit (owner Q-72 answer 2026-11-02:
          'measure full exposed wall heights continuously through the stairwell'; scope extended here from the stair
          shaft to any stairwell / void, PROPOSED). When the lower storey's room line stops at its own soffit (plaster)
          or ceiling (paint) and the upper storey's line starts at its floor datum, the band in between is real face:
              plaster band = lm x (FFL_upper - plaster_top_lower)
              paint band   = lm x (FFL_upper - paint_top_lower) - contacts inside the band
          Where the lower storey has NO wall under the upper face (a beam carries it), the band is the beam's face:
          HELD by name with its depth datum, never 0.
R-T709-2  REFERENCE ROW BINDING. A reference row binds to a drawn element only when its length equals a drawn / printed
          run within max(0.10 m, 1 %) and exactly one candidate matches; two matches -> AMBIGUOUS, none -> UNRESOLVED.
          A bound row is compared in the line that already carries that face (never priced twice, never moved into a
          class it does not belong to).
R-T709-3  RETURN BRIDGE. His n x t x run against the engine's per-id returns closes exactly; the split into a COUNT
          term and a UNIT term depends on the order, so both orders are shown and each term is a range.
R-T709-4  RETURN PAINT WIRING. One FIN.PAINT return row per plastered return line, keyed by the plaster face id: a
          valued return -> HELD, bound 0 .. its plaster m2 (frame-covered depth not printed); a return with wet rooms on
          both sides -> HELD, same bound, flagged NOT_ESTABLISHED (one finish per face, R-T701-3); a blank plaster
          return -> HELD by name, no bound. Never a value, never 0, never folded into a released paint line.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP


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


def _metres(x, name, hi="30"):
    v = D(x)
    if v < 0:
        raise RuleError(f"{name} negative")
    if v > D(hi):
        raise RuleError(f"{name} {v} looks like mm, not m")
    return v


# ---- R-T709-1 -------------------------------------------------------------------------------------------------------
def double_height_band(lm, ffl_upper, top_lower, contacts=None):
    """band m2 between the lower line's top (plaster soffit or paint ceiling, absolute level) and the upper line's floor
    datum; contacts = [m2] built against the face inside the band. lm None -> HELD (None)."""
    if lm is None or ffl_upper is None or top_lower is None:
        return None
    L = _metres(lm, "lm")
    a, b = _metres(ffl_upper, "FFL upper", "100"), _metres(top_lower, "top lower", "100")
    if b > a:
        raise RuleError("the lower line already reaches above the upper floor datum: no band, check the levels")
    gross = L * (a - b)
    c = sum((D(x) for x in (contacts or [])), D(0))
    if c < 0 or c > gross:
        raise RuleError("contacts outside 0 .. band")
    return q6(gross - c)


def beam_band(lm, beam_depth):
    """lower storey has no wall: the face below the upper floor is a beam face; depth not established -> HELD."""
    if beam_depth is None:
        return None
    return q6(_metres(lm, "lm") * _metres(beam_depth, "beam depth", "3"))


# ---- R-T709-2 -------------------------------------------------------------------------------------------------------
def bind_row(his_lm, candidates):
    """candidates [(name, drawn_lm)] -> ('BOUND', name, diff) | ('UNRESOLVED', None, None) | ('AMBIGUOUS', names, None)"""
    h = _metres(his_lm, "his length", "200")
    hits = []
    for name, lm in candidates:
        d = _metres(lm, "drawn length", "200")
        tol = max(D("0.10"), d * D("0.01"))
        if abs(h - d) <= tol:
            hits.append((name, q6(h - d)))
    if not hits:
        return ("UNRESOLVED", None, None)
    if len(hits) > 1:
        return ("AMBIGUOUS", [n for n, _ in hits], None)
    return ("BOUND", hits[0][0], hits[0][1])


# ---- R-T709-3 -------------------------------------------------------------------------------------------------------
def return_bridge(his_n, his_t, his_run, engine_values):
    n = D(his_n)
    if n != n.to_integral_value() or n < 0:
        raise RuleError("his count is not a whole number")
    t, run = _metres(his_t, "depth", "1"), _metres(his_run, "run", "20")
    vals = [D(v) for v in engine_values]
    if any(v is None or v <= 0 for v in vals):
        raise RuleError("an engine return value is blank or 0: list it HELD outside the bridge")
    m = len(vals)
    if m == 0:
        raise RuleError("no engine returns")
    unit_his = t * run
    his = n * unit_his
    eng = sum(vals, D(0))
    mean = eng / m
    # order 1: count at the engine mean, then unit on his count; order 2: count at his unit, then unit on m
    c1, u1 = (n - m) * mean, n * (unit_his - mean)
    c2, u2 = (n - m) * unit_his, m * (unit_his - mean)
    gap = his - eng
    for c, u in ((c1, u1), (c2, u2)):
        if abs(c + u - gap) > D("0.000001"):
            raise RuleError("bridge does not close")
    return {"his": str(q6(his)), "engine": str(q6(eng)), "gap": str(q6(gap)), "engine_count": m, "his_count": int(n),
            "his_unit": str(q6(unit_his)), "engine_mean": str(q6(mean)),
            "count_term": [str(x) for x in sorted([q6(c1), q6(c2)])],
            "unit_term": [str(x) for x in sorted([q6(u1), q6(u2)])]}


# ---- R-T709-4 -------------------------------------------------------------------------------------------------------
def return_paint_row(face_id, plaster_class, plaster_m2, both_sides_wet):
    if plaster_class == "RELEASED":
        v = D(plaster_m2)
        if v <= 0:
            raise RuleError(f"{face_id}: released plaster return must be > 0")
        return {"element_id": face_id + ":RETURN_PAINT", "item_code": "FIN.PAINT", "class": "HELD", "value": None,
                "bound_beside_m2": [str(q6(0)), str(q6(v))],
                "flag": "NOT_ESTABLISHED (wet rooms both sides)" if both_sides_wet else "frame-covered depth not printed"}
    if plaster_class == "HELD":
        if plaster_m2 is not None:
            raise RuleError(f"{face_id}: a HELD plaster return carries no value")
        return {"element_id": face_id + ":RETURN_PAINT", "item_code": "FIN.PAINT", "class": "HELD", "value": None,
                "bound_beside_m2": None, "flag": "HELD by name (plaster return blank)"}
    raise RuleError(f"{face_id}: plaster class {plaster_class!r} not a return state")

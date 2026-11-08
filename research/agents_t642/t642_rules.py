"""T-642 fix-row checks (research, unwired; lane S; NO new rule: the existing rules applied to one strip at a time).

Rules applied (no new rule version): UP-CONC-JOINT-001 1.0.0 (a column removes only its own footprint from a beam),
R-T610-1 (a crossing block once, at the deeper depth), R-T624-1 (a) / (b) (a named T-229 add is a region of the
drawing: a strip is BILLED by a line when the line's value carries a named term whose region holds it), R-T619-1
(a depth range -> the low end SET + a HELD companion for the rest, never a midpoint), UP-QTY-STATUS-001 (HELD never 0).

Every villa, per drawn strip of beam concrete (a plan polygon between drawn faces, outside every column footprint):
  (1) owners = the lines whose billed plan or named term covers it; exactly one owner -> BILLED_ONCE; none ->
      OMISSION (a fix row with its own quantity); two or more -> DOUBLE (refused as a result: one owner per piece);
  (2) an OMISSION is valued only at a depth with a drawing source (a printed mark bound to the member, a schedule row);
      when two marks are possible the strip is a RANGE: low end SET, companion HELD 0 .. (high - low); an unsourced
      depth used as a point is refused;
  (3) a billed term that differs from the strip's drawn volume leaves its residual named (the model fit that makes it),
      never silently absorbed and never re-billed;
  (4) a Checker figure taken from a route G band (rectangle) is compared with the CANDIDATE LINE (value = rectangle +
      named terms), never with the band alone (lesson of this task: 2 of 3 'ENGINE_WRONG' items were already billed by
      a T-229 term the band figure does not show).
HELD lines (parapet, any blank line): a blank line must carry a named cause (a WAITING key / owner decision / defect
id); a blank with no cause, or a cause with a figure, is refused; the bound shown beside it is never summed.
"""
from __future__ import annotations

RULES = ("UP-CONC-JOINT-001", "R-T610-1", "R-T624-1", "R-T619-1", "UP-QTY-STATUS-001")
EPS_M2 = 1e-6
PIECE_SHARE = 0.99          # a line owns a strip when its billed plan / term region holds >= 99 % of it
ADD_TOL_M3 = 0.001          # R-T624-1 (a) named-add tolerance (read only, quoted)


class Refused(ValueError):
    """An input that would make a fix row wrong."""


def owners_of(strip_m2, covers):
    """covers: {line_id: covered m2 of the strip (billed plan or named-term region)}. -> (state, [owners])"""
    if strip_m2 <= EPS_M2:
        raise Refused("empty strip")
    own = sorted(k for k, v in covers.items() if v >= PIECE_SHARE * strip_m2)
    part = sorted(k for k, v in covers.items() if EPS_M2 < v < PIECE_SHARE * strip_m2)
    if len(own) > 1:
        raise Refused(f"strip billed by two lines {own}: one owner per band piece (double count)")
    if own and part:
        raise Refused(f"strip owned by {own[0]} and partly billed again by {part}")
    if own:
        return "BILLED_ONCE", own
    if part:
        return "PARTLY_BILLED", part
    return "OMISSION", []


def value_omission(strip_m2, depths):
    """depths: [{'mark':..., 'depth_m':..., 'source':...}] the depths the drawing allows for the strip.
    -> {'set_m3', 'companion_low_m3', 'companion_high_m3', 'state'}"""
    if not depths:
        raise Refused("no depth: the strip stays HELD (never 0)")
    for d in depths:
        if not d.get("source"):
            raise Refused(f"depth {d.get('depth_m')} of {d.get('mark')} has no drawing source: never used as a point")
        if d.get("depth_m") is None or not (0.05 <= d["depth_m"] <= 3.0):
            raise Refused(f"depth {d.get('depth_m')} out of range (mm or a typo)")
    vals = sorted(strip_m2 * d["depth_m"] for d in depths)
    lo, hi = vals[0], vals[-1]
    if hi - lo <= 1e-9:
        return {"state": "MEASURED", "set_m3": lo, "companion_low_m3": None, "companion_high_m3": None}
    return {"state": "RANGE_LOW_SET", "set_m3": lo, "companion_low_m3": 0.0, "companion_high_m3": hi - lo}


def compare_with_line(own_m3, line_value_m3, rect_m3, terms, piece_term=None):
    """(4) own drawn volume against the candidate LINE (rectangle + named terms), not the band rectangle.
    terms: {name: m3}. The line must decompose (R-T624-1 (b)). own_m3 is the whole member (piece_term None: compared
    with the line and with the rectangle) or one piece billed by a named term (compared with that term).
    -> signed deltas (own - engine)."""
    res = line_value_m3 - rect_m3 - sum(terms.values())
    if abs(res) > 1e-4:
        raise Refused(f"line {line_value_m3} does not decompose into rectangle {rect_m3} + terms {terms} ({res:+.6f})")
    if piece_term is not None:
        if piece_term not in terms:
            raise Refused(f"piece term {piece_term} is not a term of the line")
        d = own_m3 - terms[piece_term]
        return {"delta_vs_term_m3": d, "decomposition_residual_m3": res, "within_add_tol": abs(d) <= ADD_TOL_M3,
                "checker_band_view_m3": own_m3}
    return {"delta_vs_line_m3": own_m3 - line_value_m3, "delta_vs_band_m3": own_m3 - rect_m3,
            "decomposition_residual_m3": res, "within_add_tol": abs(own_m3 - line_value_m3) <= ADD_TOL_M3}


def class_held_line(line, cause, bound=None):
    """A HELD line in a trial BOQ: blank with a named cause; the bound beside it is never the quantity."""
    if line.get("measured_net") is not None:
        raise Refused(f"{line['line_id']}: a HELD line with a figure (a held line summed into a total)")
    if not cause or not str(cause).strip():
        raise Refused(f"{line['line_id']}: HELD blank with no cause")
    rec = {"line_id": line["line_id"], "class": "HELD_WITH_CAUSE", "cause": cause, "quantity": None}
    if bound is not None:
        lo = bound.get("at_least_m3")
        if lo is None or lo < 0:
            raise Refused(f"{line['line_id']}: a bound must carry its established floor")
        rec["bound_beside"] = dict(bound)
    return rec

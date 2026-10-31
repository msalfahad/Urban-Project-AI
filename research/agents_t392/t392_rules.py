"""T-392 rules: ownership residuals left by the T-387 census (research only, every villa; stdlib + shapely).

Nothing here produces or changes a BOQ quantity. Each rule turns a residual into a named physical cause with its m3,
or refuses.

R-T392-1 (neighbour-overlap deduction against the drawn cells) a line may deduct an 'overlap with a neighbour' only
         when the two members' DRAWN cells (each between its own drawn edges, arcs as arcs) intersect by that area
         (within TOL_M2). An overlap read from a fitted or derived band set that the drawn cells do not reproduce is not
         shared volume: the deduction is a GAP of its own size on the deducting line (named, with the ledger that made
         it), never 'removed once' and never 'rounding'. The neighbour does not carry it either (a member measured
         between its own drawn edges, closed by the faces of the members that own the crossings, cannot hold another
         member's cell).
R-T392-2 (rectangular band end across an oblique carrier face) a member that stops on an oblique carrier face is
         measured to that face (its drawn cell); a band rectangle cut square at an end point that crosses the face
         holds a part BEYOND the face (inside the carrier: DOUBLE with the carrier when the carrier is billed between
         its own faces) and misses a part SHORT of the face (GAP unless another owner, e.g. a column, holds it). Both
         are reported apart, never netted: band - beyond + short = cell must close within TOL_M2, otherwise refused.
R-T392-3 (straight side longer than a tank footprint) a drawn line pair that is longer than the side of a tank
         footprint is split at the tank's outer footprint: the inside part is the tank wall (its tank line); the outside
         parts are the element the other drawings show at the same place (named per sheet, each with its line or
         MISSING, never 0); assigning an outside part to the tank is refused.
R-T392-4 (residual of a re-measured member against its band set) a residual between a member measured between its
         drawn edges and the band set that preceded it is located piece by piece (per drawn piece: plan not covered
         by the bands); the residual is LOCATED when the pieces' uncovered plan reproduces it within TOL_M2 x depth
         and no other line's drawn cell holds any of it; otherwise it stays RECHECK with the unlocated part.
"""

from __future__ import annotations

TOL_M2 = 1e-4
TOL_M3 = 0.001


class Refused(ValueError):
    """an input the rules must not accept silently."""


def _num(x, what):
    if x is None:
        raise Refused(f"MISSING: {what} (never 0)")
    x = float(x)
    if x < -1e-12:
        raise Refused(f"NEGATIVE: {what} {x}")
    return x


def _units_m(depth_m):
    d = _num(depth_m, "depth")
    if d <= 0 or d > 5.0:
        raise Refused(f"UNITS: depth {d} is not metres")
    return d


def overlap_deduction(deducted_m2, drawn_overlap_m2, depth_m, name):
    """R-T392-1. Returns {'status': COUNTED_ONCE | GAP | DOUBLE, 'm3', 'name'}."""
    if not str(name or "").strip():
        raise Refused("UNNAMED: a deduction needs the ledger that made it")
    a = _num(deducted_m2, "deducted plan")
    o = _num(drawn_overlap_m2, "drawn overlap")
    if a > 10.0 or o > 10.0:
        raise Refused("UNITS: plan areas above 10 m2 for a sliver: mm2 given as m2?")
    d = _units_m(depth_m)
    diff = a - o
    if abs(diff) <= TOL_M2:
        return {"status": "COUNTED_ONCE", "m3": 0.0, "name": name}
    if diff > 0:       # deducted more than the drawn cells share: built and billed by neither
        return {"status": "GAP", "m3": round(diff * d, 6), "name": name}
    return {"status": "DOUBLE", "m3": round(-diff * d, 6), "name": name}


def band_end_vs_face(band_m2, cell_m2, beyond_m2, short_m2, short_owned_m2, depth_m):
    """R-T392-2. short_owned_m2: part of the short region another owner (a column) holds. Returns the DOUBLE (beyond
    the face) and GAP (short of the face, not owned) in m3, apart; refuses a non-closing set."""
    b, c = _num(band_m2, "band plan"), _num(cell_m2, "drawn cell")
    be, sh, so = _num(beyond_m2, "band beyond face"), _num(short_m2, "cell short of band"), _num(short_owned_m2,
                                                                                                  "short owned")
    d = _units_m(depth_m)
    if abs((b - be + sh) - c) > TOL_M2:
        raise Refused(f"NOT_CLOSED: band {b} - beyond {be} + short {sh} != cell {c}")
    if so > sh + TOL_M2:
        raise Refused("OWNED_EXCEEDS_SHORT: another owner cannot hold more than the short region")
    out = {"double_m3": round(be * d, 6), "gap_m3": round((sh - so) * d, 6),
           "net_m3_never_used": round((sh - so - be) * d, 6)}
    out["status"] = ("BOTH" if be > TOL_M2 and sh - so > TOL_M2 else "DOUBLE" if be > TOL_M2 else
                     "GAP" if sh - so > TOL_M2 else "CLOSED")
    return out


def split_side(pair_length_m, tank_side_m, before_m, after_m, outside_owner):
    """R-T392-3. before_m / after_m: the pair's run beyond the tank footprint at each end (drawn). outside_owner:
    {'element': str, 'lines': [{'sheet': .., 'line_id' or None, 'status': ..}]}; MISSING when line_id is None."""
    L, s = _num(pair_length_m, "pair length"), _num(tank_side_m, "tank side")
    a, b = _num(before_m, "run before"), _num(after_m, "run after")
    if L > 200 or s > 200:
        raise Refused("UNITS: metres expected")
    if abs(a + s + b - L) > 1e-3:
        raise Refused(f"NOT_CLOSED: {a} + {s} + {b} != {L}")
    el = str((outside_owner or {}).get("element") or "")
    if not el:
        raise Refused("NO_OWNER: the outside part needs its element from the other drawings")
    if "pool" in el.lower() or "tank" in el.lower():
        raise Refused("TANK_OWNS_OUTSIDE: the part outside the tank footprint is not tank concrete")
    lines = []
    for ln in outside_owner.get("lines") or []:
        lines.append(dict(ln, state=("MISSING" if not ln.get("line_id") else ln.get("status") or "BOUND")))
    if not lines:
        raise Refused("NO_LINE_STATED: each sheet's element needs its line or MISSING")
    return {"inside_m": s, "outside_m": round(a + b, 4), "outside_parts_m": [a, b], "element": el, "lines": lines}


def locate_residual(member_m2, pieces, depth_m, other_cells_in_member_m2=0.0):
    """R-T392-4. pieces: [(piece_m2, uncovered_m2)], member_m2 drawn total; band_cover_m2 implied. Returns LOCATED with
    the per-piece m3, or RECHECK with the unlocated part."""
    d = _units_m(depth_m)
    m = _num(member_m2, "member plan")
    tot = sum(_num(p, "piece") for p, _ in pieces)
    if abs(tot - m) > TOL_M2:
        raise Refused(f"PIECES_NOT_MEMBER: pieces {tot} != member {m}")
    unc = [round(_num(u, "uncovered") * d, 6) for _, u in pieces]
    if _num(other_cells_in_member_m2, "other cells") > TOL_M2:
        return {"status": "RECHECK", "per_piece_m3": unc, "reason": "another line's drawn cell lies in the member"}
    return {"status": "LOCATED", "per_piece_m3": unc, "located_m3": round(sum(unc), 6)}

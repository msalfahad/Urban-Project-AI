"""T-673 rules (project-agnostic; scope: every villa with a printed RC lintel schedule and drawn opening heads).

R-T673-1 1.0.0  LINTEL EXISTENCE FROM A DRAWN HEAD (robust margin test).
    Provenance: R-T453-4 (a lintel is REQUIRED only where masonry is built above the head: the head sits below every
    candidate piece's clear height by D + the floor bed stand-in), ERS s.2.4 / s.3 'build before deduct', and the T-201 /
    T-207 / T-238 drawn-head reads (DRAWING-CONFIRMED, each with its own measured drawn tolerance). New here: a head that
    is not printed but DRAWING-CONFIRMED by a merged drawn-geometry read may decide existence ONLY when the decision does
    not flip anywhere inside the read's own tolerance band:
        spare = min(clear heights) - (head_hi + tol) - (D + bed)
        spare >= 0                                   -> REQUIRED   (existence DRAWING-CONFIRMED, never VERIFIED here)
        max(clear) - (head_lo - tol) < D             -> FLAGGED    (the member serves the opening: no lintel line)
        otherwise                                    -> HELD_BY_NAME (decision inside the tolerance / some pieces only)
    Prerequisites, refused or HELD otherwise: head known (no head -> HELD, never 0); the opening DEDUCTED inside drawn
    host pieces (ON_HELD_WALL / IN_HELD_PIECE / HELD -> HELD with the host named); clear heights > 0 in metres;
    head and clear height on ONE datum (the host run's structural datum); a printed head always governs a drawn one.

R-T673-2 1.0.0  BEARING TEST AT PRINTED PRECISION (Lead ruling F-T650-3, 2026-11-09: compare at 1 mm, rounded, never
    truncated). a_mm = round-half-up(a, 0.001); a_mm >= b_min -> BOUNDED else FLAGGED_DEFICIT. R-T516-1 is not edited.

R-T673-3 1.0.0  RC LINTEL m3 RANGE ON ONE MASONRY LINE (composition of R-T650-1 / R-T524-1 / R-T544-1 (4), no new factor).
    BOTH ENDS BOUNDED (ceiling convention, as R-T650-1 BOUNDED):
        lo = B D (w + 2 b_min);  hi = B D (w + c_s + c_e), c = a rounded UP to the mm (R-T544-1 (1)); a search-capped end
        takes its extended-search value, none -> hi OPEN.
    AN END FLAGGED_DEFICIT (MIN-BEARING convention, as R-T524-1):
        lo = B D (w + sum of the BOUNDED ends' b_min);  hi = B D (w + sum(b_min if BOUNDED else a_eff)).
    SHARED PIER p (stopper = the neighbouring opening):
        neighbour released / in this set on the MIN-BEARING convention -> it occupies b_min of the pier: this end's
            available a_eff = p - b_min (deficit if a_eff < b_min);
        both members on the ceiling convention -> each takes b_min in its own hi and the pier remainder
            p - 2 b_min (>= 0) is ONE joint record, counted once in the family high (R-T544-1 (4): pier once);
        neighbour HELD blank (existence open) -> the full pier is this end's ceiling (an upper bound; the neighbour, if
            later established, must re-split the pier).
    Refused: lengths outside (0, 30] m, mm / cm passed as m, a deficit stated with a >= b_min, a released neighbour that
    is not recorded, a curved head or a width above the last printed band given a straight-lintel m3 (FLAGGED, owned by
    the structural line that carries the head), a quantity of 0 for a HELD line.
"""
from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

B_MIN = Decimal("0.40")
Q6 = Decimal("0.000001")
MM = Decimal("0.001")
BOUNDED, DEFICIT = "BOUNDED", "FLAGGED_DEFICIT"
REQUIRED, FLAGGED, HELD_BY_NAME, HELD = "REQUIRED", "FLAGGED", "HELD_BY_NAME", "HELD"


class Refused(ValueError):
    pass


def D(x, what="value"):
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, (int, float, str, Decimal)):
        raise Refused(f"{what}: {x!r} is not a number")
    v = Decimal(str(x))
    if v.is_nan() or v < 0 or v > 30:
        raise Refused(f"{what}: {x!r} is not a length in metres")
    return v


def q6(v):
    return None if v is None else v.quantize(Q6, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------------------------------- R-T673-1
def existence(*, head_lo, head_hi, tol, fill_state, clear_heights, d, bed, head_status):
    if head_lo is None or head_hi is None:
        return HELD, None, "head not established (no printed or drawn head): existence HELD, never 0"
    if head_status not in ("PRINTED", "DRAWING-CONFIRMED", "VERIFIED"):
        raise Refused(f"head status {head_status!r} cannot decide existence")
    h0, h1, t = D(head_lo, "head_lo"), D(head_hi, "head_hi"), D(tol, "tolerance")
    if h0 > h1:
        raise Refused("head_lo above head_hi")
    if t > Decimal("0.10"):
        raise Refused(f"tolerance {tol} m is not a drawn-read tolerance (mm passed as m?)")
    if fill_state != "DEDUCTED":
        return HELD, None, f"opening is {fill_state} in the merged fill: the host masonry above the head is not established"
    if not clear_heights:
        return HELD, None, "host wall has no drawn pieces with a printed soffit"
    cs = [D(c, "clear height") for c in clear_heights]
    if any(c <= 0 for c in cs) or any(c > 10 for c in cs):
        raise Refused("clear height not in metres")
    dd, bb = D(d, "D"), D(bed, "bed")
    if head_status == "PRINTED":
        t = Decimal(0)
    spare = min(cs) - (h1 + t) - (dd + bb)
    if spare >= 0:
        return REQUIRED, q6(spare), "masonry above the head under every piece within the read tolerance"
    if max(cs) - (h0 - t) < dd:
        return FLAGGED, q6(spare), "no piece leaves room for the band depth: the member serves the opening (designer)"
    return HELD_BY_NAME, q6(spare), "the decision flips inside the read tolerance or holds under some pieces only"


# ---------------------------------------------------------------------------------------------------- R-T673-2
def bearing_state(a, b_min=B_MIN):
    a = D(a, "available")
    a_mm = a.quantize(MM, rounding=ROUND_HALF_UP)
    return (BOUNDED if a_mm >= b_min else DEFICIT), a_mm


def ceil_mm(a):
    return D(a).quantize(MM, rounding=ROUND_CEILING)


# ---------------------------------------------------------------------------------------------------- R-T673-3
def lintel_m3(lintel, neighbours, b_min=B_MIN):
    """lintel = {id, width_m, B, D, form, ends: [{side, a, stopper (COLUMN | END | OPENING | SEARCH_LIMIT),
    stopper_id, extended}]}; neighbours = {opening id: 'RELEASED' | 'MIN_BEARING' | 'CEILING' | 'HELD'}.
    Returns lo / hi m3 and, for a ceiling pair, the pier remainder as its own record."""
    if lintel.get("form") in ("CURVED", "ABOVE_LAST_BAND"):
        raise Refused(f"{lintel['id']}: {lintel['form']} head is FLAGGED (structural line), never a straight lintel m3")
    w, B, Dd = D(lintel["width_m"], "width"), D(lintel["B"], "B"), D(lintel["D"], "D")
    if w <= 0 or w > 10:
        raise Refused(f"{lintel['id']}: width {w} not in metres")
    if not (Decimal("0.05") <= B <= Decimal("0.60") and Decimal("0.10") <= Dd <= Decimal("0.80")):
        raise Refused(f"{lintel['id']}: section {B} x {Dd} not in metres")
    ends = lintel["ends"]
    if sorted(e["side"] for e in ends) != ["END", "START"]:
        raise Refused(f"{lintel['id']}: needs one START and one END")
    rows = []
    for e in ends:
        stop = e["stopper"]
        a = D(e["a"], f"{lintel['id']} {e['side']} a")
        if stop == "SEARCH_LIMIT":
            a = D(e["extended"]) if e.get("extended") is not None else None
            stop = e.get("extended_stopper", "COLUMN") if a is not None else "SEARCH_LIMIT"
        nb = None
        if stop == "OPENING":
            nb = neighbours.get(e["stopper_id"])
            if nb is None:
                raise Refused(f"{lintel['id']}: pier neighbour {e['stopper_id']} not recorded")
            if nb in ("RELEASED", "MIN_BEARING"):
                a = a - b_min
                if a < 0:
                    a = Decimal(0)
        if a is None:
            rows.append({"side": e["side"], "state": BOUNDED, "a": None, "a6": None, "ceiling": None, "pier": None})
            continue
        st, a_mm = bearing_state(a, b_min)
        rows.append({"side": e["side"], "state": st, "a": a_mm, "a6": q6(a), "ceiling": ceil_mm(a),
                     "pier": (e["stopper_id"], nb) if stop == "OPENING" else None})
    deficit = any(r["state"] == DEFICIT for r in rows)
    pier_rem = []
    if deficit:
        conv = "MIN_BEARING"
        lo_len = w + sum(b_min for r in rows if r["state"] == BOUNDED)
        hi_len = w + sum(b_min if r["state"] == BOUNDED else r["a6"] for r in rows)
    else:
        conv = "CEILING"
        lo_len = w + 2 * b_min
        hi_len, open_ = w, False
        for r in rows:
            if r["pier"] and r["pier"][1] == "CEILING":
                hi_len += b_min
                pier_rem.append(r["pier"][0])
            elif r["ceiling"] is None:
                open_ = True
            else:
                hi_len += r["ceiling"]
        if open_:
            hi_len = None
    lo = q6(B * Dd * lo_len)
    hi = None if hi_len is None else q6(B * Dd * hi_len)
    if lo <= 0:
        raise Refused(f"{lintel['id']}: lo {lo} <= 0")
    return {"id": lintel["id"], "convention": conv, "state": "HELD_BY_NAME" if deficit else "BOUNDED",
            "lo_m3": lo, "hi_m3": hi, "length_lo_m": q6(lo_len), "length_hi_m": q6(hi_len),
            "ends": rows, "pier_shared_ceiling_with": pier_rem}


def pier_remainder(p, B, Dd, b_min=B_MIN):
    p = D(p, "pier")
    rem = p - 2 * b_min
    if rem < 0:
        raise Refused(f"pier {p} < 2 b_min: not a ceiling pair (deficit pair, R-T524-1)")
    return q6(D(B) * D(Dd) * rem)


def family_total(rows):
    """rows: [{'lo_m3', 'hi_m3'}] (lintels and pier remainders); HELD blank rows are listed, never added as 0."""
    lo, hi = Decimal(0), Decimal(0)
    hi_open = False
    for r in rows:
        if r.get("lo_m3") is None:
            raise Refused("a HELD blank row cannot enter a total (never 0)")
        lo += Decimal(str(r["lo_m3"]))
        if r.get("hi_m3") is None:
            hi_open = True
        else:
            hi += Decimal(str(r["hi_m3"]))
    return q6(lo), (None if hi_open else q6(hi))


# ---------------------------------------------------------------------------------------------------- census
CAUSES = ("DESIGNER ITEM", "MEASURABLE NOW", "OPEN BOUND")


def census_row(*, member, line_id, cause, cause_ref, fix, lo=None, hi=None):
    if cause not in CAUSES:
        raise Refused(f"cause {cause!r}")
    if cause == "DESIGNER ITEM" and not cause_ref:
        raise Refused(f"{line_id}: a designer item names its D-nn / Q-nn")
    if lo is not None and D(lo) == 0:
        raise Refused(f"{line_id}: a HELD line is never 0")
    if cause == "MEASURABLE NOW" and lo is None:
        raise Refused(f"{line_id}: MEASURABLE NOW needs its drawn quantity")
    return {"member": member, "line_id": line_id, "cause": cause, "cause_ref": cause_ref, "fix": fix,
            "low_m3": None if lo is None else format(D(lo).quantize(Q6), "f"),
            "high_m3": None if hi is None else format(D(hi).quantize(Q6), "f")}

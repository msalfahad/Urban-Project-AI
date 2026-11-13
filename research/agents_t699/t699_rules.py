"""T-699 rules (project-agnostic; scope: every villa with RC / precast lintels over masonry openings). Research only,
unwired. Built on R-T673-3 (t673_rules), R-T678-1 / -3 (t678_rules) and R-T696-1 (bound_rounding_v1), none edited.

R-T699-1 1.0.0  ONE-SIDED BOUNDS OF A LINTEL LINE (existence open, or one end open).
    Physical element: the lintel over ONE opening: section B (host wall thickness) x D (printed schedule depth) x length
    (clear width w + the bearing taken at each end). Its line quantity Q is 0 (no lintel: no masonry above the head, or
    a member soffit serves the opening) or, if the lintel exists, lies in [lo, hi] of R-T673-3 on the same ends.
    (a) AT_MOST = hi of R-T673-3 on the recorded ends (CEILING when every end is BOUNDED, MIN_BEARING when an end is in
        deficit; a shared pier is split by the neighbour's state exactly as R-T673-3 says). It holds whether or not
        the lintel exists (Q = 0 or Q <= hi), so it is stated even when existence is open. Refused (no AT_MOST, the
        datum named): an end with no recorded stopper (R-T678-3), no jamb evidence, a curved head (R-T673-3: owned by
        the structural line that carries it), an unknown section. A width conflict takes the largest width with the
        jamb split that maximises hi (the span between the two stoppers is fixed by the drawing).
    (b) AT_LEAST = lo of R-T673-3 (or of R-T678-3 with one end open) ONLY when existence is REQUIRED (R-T678-1). With
        existence open the lo is shown beside as CONDITIONAL ('if REQUIRED'), never as a bound: the line may be 0.
    (c) A head that reaches a member soffit (c_hi - head < D: no room for the lintel depth) is NOT a lintel: EXCLUDED,
        the member owns it (register 'lintel at a beam soffit'); while the soffit is open this is a CONDITIONAL
        EXCLUSION naming the member.
    (d) Bearing b_min: the printed schedule bearing governs (drawing before company rule); where the drawing prints
        none, the owner minimum 0.15 m (owner 2026-11-02, T-448 lintel rule) is the bearing of the lo.
    (e) Directed rounding R-T696-1: AT_LEAST floors, AT_MOST ceils at 6 dp, from the exact decimal products.
    (f) A family AT_MOST sums the lines' AT_MOST; where two lines of the set share one pier and both take the full
        pier as their ceiling (both existence open), the family counts the pier once (R-T544-1 (4)).
    Nothing becomes 0: a missing input is HELD by name, a blank line stays blank (the bound sits beside it).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t678"))
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import t678_rules as R78  # noqa: E402
import bound_rounding_v1 as BR  # noqa: E402

R73 = R78.R73
Refused = R73.Refused
X = Decimal
OWNER_B_MIN = X("0.15")
REQUIRED, FLAGGED, HELD_BY_NAME, HELD = R73.REQUIRED, R73.FLAGGED, R73.HELD_BY_NAME, R73.HELD
EXISTENCE = (REQUIRED, "OPEN", "CONDITIONAL_EXCLUSION", "EXCLUDED")
CAUSES = ("DESIGNER ITEM", "NEEDS OWNER RULE", "MEASURABLE NOW", "METHOD GAP")
RECORDED = ("COLUMN", "END_OF_MASONRY", "END", "OPENING", "SEARCH_LIMIT")


def b_min_of(printed_bearing):
    """(d): the printed schedule bearing governs; none printed -> the owner minimum 0.15 m."""
    if printed_bearing is None:
        return OWNER_B_MIN
    b = R73.D(printed_bearing, "printed bearing")
    if not (X("0.05") <= b <= X("1.0")):
        raise Refused(f"printed bearing {printed_bearing} not in metres")
    return b


def _check_section(B, Dd, oid):
    if B is None or Dd is None:
        raise Refused(f"{oid}: section not known (B or D missing): HELD by name, never 0")
    B, Dd = R73.D(B, "B"), R73.D(Dd, "D")
    if not (X("0.05") <= B <= X("0.60") and X("0.10") <= Dd <= X("0.80")):
        raise Refused(f"{oid}: section {B} x {Dd} not in metres")
    return B, Dd


def _resolve_end(oid, e, neighbours, b_min):
    """R-T673-3 resolution of ONE end in exact decimals: (state, a_exact, ceiling_mm, pier)."""
    stop = e.get("stopper")
    if stop not in RECORDED:
        raise Refused(f"{oid} {e.get('side')}: stopper {stop!r} not recorded (R-T678-3: OPEN end)")
    a = R73.D(e["a"], "available")
    if stop == "SEARCH_LIMIT":
        if e.get("extended") is None:
            raise Refused(f"{oid} {e['side']}: search limit with no extended stopper (OPEN end)")
        a = R73.D(e["extended"], "extended")
    pier = None
    if stop == "OPENING":
        nb = neighbours.get(e.get("stopper_id"))
        if nb is None:
            raise Refused(f"{oid}: pier neighbour {e.get('stopper_id')!r} not recorded (OPEN end)")
        if nb in ("RELEASED", "MIN_BEARING"):
            a = max(a - b_min, X(0))
        pier = (e["stopper_id"], nb)
    st, _ = R73.bearing_state(a, b_min)
    return st, a, R73.ceil_mm(a), pier


def _exact_ends(lintel, neighbours, b_min):
    if len(lintel["ends"]) != 2:
        raise Refused(f"{lintel['id']}: needs two ends")
    return [_resolve_end(lintel["id"], e, neighbours, b_min) for e in lintel["ends"]]


def at_most(lintel, neighbours=None, b_min=X("0.40")):
    """(a): exact hi of R-T673-3 and its R-T696-1 ceiling. lintel = {id, width_m | width_range, B, D, form, ends}."""
    neighbours = neighbours or {}
    oid = lintel["id"]
    if lintel.get("form") in ("CURVED", "ABOVE_LAST_BAND"):
        raise Refused(f"{oid}: {lintel['form']} head: never a straight-lintel m3 (R-T673-3)")
    if not lintel.get("ends"):
        raise Refused(f"{oid}: no jamb evidence: AT_MOST not formed, never 0")
    B, Dd = _check_section(lintel.get("B"), lintel.get("D"), oid)
    rng = lintel.get("width_range")
    widths = [R73.D(w, "width") for w in (rng if rng else [lintel["width_m"]])]
    if any(w <= 0 or w > 10 for w in widths):
        raise Refused(f"{oid}: width not in metres")
    best = None
    for w in widths:
        extra = w - min(widths)       # a wider opening eats the jamb availability (span between stoppers fixed)
        splits = [(extra, X(0)), (X(0), extra)] if extra else [(X(0), X(0))]
        for s0, s1 in splits:
            ends = []
            for e, s in zip(lintel["ends"], (s0, s1)):
                e2 = dict(e)
                e2["a"] = R73.D(e["a"]) - s
                if e2["a"] < 0:
                    break
                ends.append(e2)
            else:
                rows = _exact_ends({"id": oid, "ends": ends}, neighbours, b_min)
                deficit = any(r[0] == R73.DEFICIT for r in rows)
                if deficit:
                    length = w + sum(b_min if r[0] == R73.BOUNDED else r[1] for r in rows)
                    conv = "MIN_BEARING"
                else:
                    length = w
                    for st, a, c, pier in rows:
                        length += b_min if (pier and pier[1] == "CEILING") else c
                    conv = "CEILING"
                hi = BR.mul(B, Dd, length)
                if best is None or hi > best[0]:
                    best = (hi, conv, w, length)
    hi, conv, w, length = best
    return {"id": oid, "at_most_exact": hi, "at_most": BR.round_high(hi), "convention": conv,
            "width_used": w, "length_hi": length}


def conditional_lo(lintel, neighbours=None, b_min=X("0.40")):
    """lo of R-T673-3 (bounded ends' b_min only when an end is in deficit or open): the lintel's least length if it
    exists. With existence open this is CONDITIONAL, never a bound (b)."""
    neighbours = neighbours or {}
    oid = lintel["id"]
    if lintel.get("form") in ("CURVED", "ABOVE_LAST_BAND"):
        raise Refused(f"{oid}: {lintel['form']} head: never a straight-lintel m3 (R-T673-3)")
    B, Dd = _check_section(lintel.get("B"), lintel.get("D"), oid)
    rng = lintel.get("width_range")
    w = min(R73.D(x, "width") for x in rng) if rng else R73.D(lintel["width_m"], "width")
    n_bounded = 0
    deficit_or_open = False
    for e in lintel.get("ends") or []:
        if e.get("stopper") == "SEARCH_LIMIT" and e.get("extended") is None:
            # R-T678-3: at least the searched distance is free masonry: b_min fits if a >= b_min; the hi stays OPEN
            deficit_or_open = True
            if R73.bearing_state(e["a"], b_min)[0] == R73.BOUNDED:
                n_bounded += 1
            continue
        try:
            st, *_ = _resolve_end(oid, e, neighbours, b_min)
        except Refused:
            deficit_or_open = True
            continue
        if st == R73.BOUNDED:
            n_bounded += 1
        else:
            deficit_or_open = True
    if not lintel.get("ends"):
        deficit_or_open = True
    length = w + n_bounded * b_min
    lo = BR.mul(B, Dd, length)
    if lo <= 0:
        raise Refused(f"{oid}: lo <= 0")
    return {"id": oid, "lo_exact": lo, "lo": BR.round_low(lo), "length_lo": length,
            "convention": "MIN_BEARING" if deficit_or_open else "CEILING"}


def one_sided(*, existence, lintel, neighbours=None, b_min=X("0.40"), excluded_by=None):
    """the R-T699-1 statement of one line: {existence, at_least, at_most, conditional_lo, ...}. Quantity stays blank."""
    if existence not in EXISTENCE:
        raise Refused(f"existence {existence!r}")
    if existence in ("CONDITIONAL_EXCLUSION", "EXCLUDED") and not excluded_by:
        raise Refused(f"{lintel['id']}: an exclusion names the member that serves the opening")
    if existence == "EXCLUDED":
        return {"id": lintel["id"], "existence": existence, "excluded_by": excluded_by, "at_least": None,
                "at_most": None, "conditional_lo": None, "why_no_at_most": "not a lintel: the member owns it"}
    out = {"id": lintel["id"], "existence": existence, "excluded_by": excluded_by, "at_least": None, "at_most": None,
           "conditional_lo": None, "why_no_at_most": None, "convention": None}
    try:
        m = at_most(lintel, neighbours, b_min)
        out["at_most"], out["convention"], out["length_hi"] = m["at_most"], m["convention"], m["length_hi"]
    except Refused as exc:
        out["why_no_at_most"] = str(exc)
    try:
        lo = conditional_lo(lintel, neighbours, b_min)
    except Refused as exc:
        out["why_no_lo"] = str(exc)
        return out
    if existence == REQUIRED:
        out["at_least"] = lo["lo"]
    else:
        out["conditional_lo"] = lo["lo"]
    if out["at_most"] is not None:
        top = out["at_most"]
        if lo["lo"] > top:
            raise Refused(f"{lintel['id']}: lo {lo['lo']} above AT_MOST {top}")
    return out


def family_at_most(rows, shared_piers=()):
    """(f): rows [{id, at_most_exact}], shared_piers [(id1, id2, double_counted_exact)] -> family AT_MOST."""
    tot = BR.add(*[r["at_most_exact"] for r in rows]) if rows else X(0)
    for _, _, dbl in shared_piers:
        tot = tot - X(dbl)
    return BR.round_high(tot)

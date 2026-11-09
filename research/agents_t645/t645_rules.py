"""R-T645-1 STAIR FINISH HOLD CENSUS (every villa; research provenance, proposed): every HELD-blank B7 stair finish line
(FIN.STAIR.FLIGHT lm, FIN.MARBLE.RISER m2, FIN.MARBLE.TREAD m2, FIN.STAIR.SOFFIT m2) gets exactly one class, a named
cause and, where the evidence allows it, a fix row. Nothing is wired here; no new rule value is introduced.

Classes (T-645 row, owner directive 2026-11-08 12:40 item 3):
  A_DRAWN    the flight is drawn and dimensioned: governing riser count, drawn front edges (widths, by handle), drawn
             going and printed finished levels -> the quantity by the SAME method as the released B7 lines (E1 riser
             line L-0afa7bd3: risers x (rise / risers - tread marble 0.030, UP-STAIR-006) x drawn width): fix row
             HELD blank -> RELEASED with its evidence status
  A_CARRIED  a reading of a flight whose quantity another line carries (seen through the opening, folded partial,
             double count; T-425 / T-429 R-T429-1 one flight one valued line): no figure, the carrier is named
  B_HELD     winder or curved part not dimensioned (OWNER_RULE_STAIRS_2026-10-24 s.4 S-9: winders never generated, no
             walking-line offset assumed; Q-50 A cond curved part): stays blank, the figure of the drawn region beside
  C_OPEN     depends on an open designer item (count conflict, an undrawn edge or going): stays HELD; a fix row bounds
             it only where the drawings give both readings (low .. high) or a drawn part (low .. OPEN)

Physical rules (generic calculator, every villa):
  finished riser  R = (FFL_to - FFL_from) / governing risers (uniform finished riser: owner construction method, R the
                  intended finished riser, OWNER_RULE_STAIRS_2026-10-24 s.1); levels in metres, a rise over 6 m in one
                  flight is mm (refused)
  visible riser   sum of the drawn front-edge widths (one riser under each nosing, a proud column notch included) x
                  (R - tread marble thickness); R <= t refused
  flight (B7-01)  pitch line nosing to nosing = sum over the drawn goings of hypot(going, R) (straight flight; a winder
                  or curved going is never generated: refused)
  soffit          (T-281 ledger) true area per piece by method O and D; a lower bound only sums pieces present in every
                  reading, by ONE method at a time (never the smaller row of each method mixed)
"""
from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 40
CLASSES = ("A_DRAWN", "A_CARRIED", "B_HELD", "C_OPEN")
STATUSES = ("VERIFIED", "PARTIALLY VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "UNKNOWN")
Q6 = Decimal("0.000001")
KINDS = ("STRAIGHT", "WINDER", "CURVED")


class RuleError(Exception):
    pass


def D(x):
    return None if x is None else Decimal(str(x))


def q(x):
    return D(x).quantize(Q6)


def S(x):
    if x is None:
        return None
    s = format(D(x).normalize(), "f")
    return "0" if s in ("-0", "0.0") else s


def _pos(x, what):
    v = D(x)
    if v is None:
        raise RuleError(f"{what} missing (never 0)")
    if v <= 0:
        raise RuleError(f"{what} {v} is not positive")
    return v


# ---- generic stair finish calculator --------------------------------------------------------------------------------

def finished_riser(ffl_from, ffl_to, risers):
    """uniform finished riser from two finished levels and the governing riser count."""
    if risers is None:
        raise RuleError("riser count missing (HELD, never 0)")
    if not isinstance(risers, int) or isinstance(risers, bool) or risers < 1:
        raise RuleError(f"riser count {risers!r} is not a positive whole number")
    a, b = D(ffl_from), D(ffl_to)
    if a is None or b is None:
        raise RuleError("finished level missing (never 0)")
    rise = b - a
    if rise <= 0:
        raise RuleError(f"a flight rises (levels {a} -> {b})")
    if rise > 6:
        raise RuleError(f"{rise} m in one flight is not a rise in metres (mm refused)")
    return rise / risers


def visible_riser_m2(widths, riser, tread_t):
    """risers of one flight: sum of the drawn front-edge widths x (R - tread marble)."""
    if widths is None or len(widths) == 0:
        raise RuleError("no drawn riser width (HELD, never 0)")
    ws = [_pos(w, "riser width") for w in widths]
    if any(w > 6 for w in ws):
        raise RuleError("riser width over 6 m: mm read as m refused")
    r, t = _pos(riser, "riser"), _pos(tread_t, "tread marble thickness")
    if r <= t:
        raise RuleError(f"riser {r} not above the tread marble {t}")
    return sum(ws) * (r - t)


def flight_lm(goings, riser, kind="STRAIGHT"):
    """pitch line nosing to nosing on a straight flight: sum of hypot(going, R) over the drawn goings."""
    if kind not in KINDS:
        raise RuleError(f"unknown flight kind {kind!r}")
    if kind != "STRAIGHT":
        raise RuleError(f"{kind.lower()} flight: winder / curved going not dimensioned, never generated and no "
                        "walking-line offset assumed (S-9): HELD")
    if goings is None or len(goings) == 0:
        raise RuleError("no drawn going (HELD, never 0)")
    r = _pos(riser, "riser")
    tot = Decimal(0)
    for g in goings:
        g = _pos(g, "going")
        if g > 2:
            raise RuleError("going over 2 m: mm read as m refused")
        tot += (g * g + r * r).sqrt()
    return tot


def winder_area(*_a, **_k):
    """refused by design: a winder subdivision is never generated (S-9, A8 / A9)."""
    raise RuleError("winder tread / riser geometry not drawn: generated winder refused (S-9), HELD")


def soffit_low(pieces_by_method):
    """lower bound of a soffit line: per method the sum of the pieces present in every reading; the low is the
    smaller method total (one method at a time)."""
    tot = {}
    for m, pieces in pieces_by_method.items():
        if not pieces:
            raise RuleError(f"method {m}: no measured piece")
        tot[m] = sum(_pos(v, f"{m} piece") for v in pieces)
    return min(tot.values()), tot


# ---- census rules ---------------------------------------------------------------------------------------------------

def check_entry(e):
    lid = e.get("line_id")
    if e.get("class") not in CLASSES:
        raise RuleError(f"{lid}: unknown class {e.get('class')!r}")
    if not (e.get("cause") or "").strip():
        raise RuleError(f"{lid}: a line needs a named cause (blank cause refused)")
    if not e.get("sources"):
        raise RuleError(f"{lid}: no source cited")
    fix = e.get("fix")
    if e["class"] == "A_DRAWN":
        if fix is None:
            raise RuleError(f"{lid}: A_DRAWN needs a fix row")
        if not e.get("handles"):
            raise RuleError(f"{lid}: A_DRAWN quantity without drawn handles refused")
        check_fix(lid, fix, release=True)
    elif e["class"] == "C_OPEN":
        if fix is not None:
            check_fix(lid, fix, release=False)
    elif fix is not None:
        raise RuleError(f"{lid}: class {e['class']} carries no quantity fix row")
    if e["class"] == "A_CARRIED" and not e.get("carrier"):
        raise RuleError(f"{lid}: A_CARRIED must name its carrier line")
    if e["class"] in ("B_HELD", "C_OPEN") and e.get("measured_net") not in (None,):
        raise RuleError(f"{lid}: a HELD line shown with a value refused")


def check_fix(lid, fix, release):
    a, b = fix.get("after") or {}, fix.get("before") or {}
    if b.get("class") != "HELD" or any(b.get(k) is not None for k in ("measured_net", "held_low", "held_high")):
        raise RuleError(f"{lid}: a T-645 fix row starts from a HELD-blank line (before stated)")
    if not fix.get("basis"):
        raise RuleError(f"{lid}: a fix row states its arithmetic basis")
    cls = a.get("class")
    if release:
        if cls != "RELEASED":
            raise RuleError(f"{lid}: an A_DRAWN fix row releases the computed quantity")
        v = D(a.get("measured_net"))
        if v is None or v <= 0:
            raise RuleError(f"{lid}: a HELD line released as 0 / blank refused")
        if a.get("evidence") not in STATUSES[:4]:
            raise RuleError(f"{lid}: a released quantity needs its evidence status")
        return
    if cls != "HELD":
        raise RuleError(f"{lid}: a C_OPEN fix row keeps the line HELD")
    if a.get("measured_net") is not None:
        raise RuleError(f"{lid}: HELD with a value refused")
    lo, hi = D(a.get("held_low")), D(a.get("held_high"))
    if lo is None or lo <= 0:
        raise RuleError(f"{lid}: a bound needs a positive low end (HELD 0 refused)")
    if hi is not None and hi < lo:
        raise RuleError(f"{lid}: bound out of order {lo} .. {hi}")


def census_counts(entries):
    out = {c: 0 for c in CLASSES}
    for e in entries:
        out[e["class"]] += 1
    fixes = [e for e in entries if e.get("fix")]
    return {"by_class": out, "lines": len(entries), "fix_rows": len(fixes),
            "released_rows": sum(1 for e in fixes if e["fix"]["after"]["class"] == "RELEASED"),
            "bounded_rows": sum(1 for e in fixes if e["fix"]["after"]["class"] == "HELD"),
            "stay_held_blank": sum(1 for e in entries if not e.get("fix") and e["class"] != "A_CARRIED"),
            "carried": out["A_CARRIED"]}

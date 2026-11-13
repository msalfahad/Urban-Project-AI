"""T-659 rules (research, unwired): the SMALL B10 concrete elements (parapets, boundary pad / wall, blinding, dome, pool,
lift) restated line by line from the drawings, for any villa.

R-T659-1 VALUE ONLY WHAT IS PRINTED. A component is VALUED only when every factor of its solid (each plan dimension, the
    section, the count) carries a printed source. A typical / N.I.S. detail whose dimension reads 'AS PER ARCH', 'SEE ARCH
    PLAN', 'AS PER SCHEDULE' or 'as per lift manufacturer' gives no figure: the line stays HELD with that factor named.
R-T659-2 HELD BLANK CARRIES ITS COEFFICIENT. A held-blank line whose solid is printed except for one factor (a count, a
    thickness, a section, a depth) carries, beside it, the volume per unit of that factor (m3 per pad, m3 per m of
    thickness, m3 per m2 of section) and, where every alternative shares a printed minimum, an AT_LEAST floor with its
    status. Neither is the line quantity; a coefficient is never multiplied by a count or a thickness that is not
    printed (no default, no borrowed detail of another element, no freelancer figure).
R-T659-3 ONE ELEMENT, ONE OWNER, BUILD BEFORE DEDUCT. Where a typical detail draws a member running THROUGH another (the
    boundary-wall ground beam through its column pad: the beam soffit on the pad soffit), the through-running member keeps
    its full section and the pad owns its solid NET of the shared volume: pad_net = L x W x T - b_beam x L x min(T, d_beam).
    A pad coefficient gross of the beam counts the shared prism twice.
R-T659-4 TWO PRINTED READINGS GIVE THE BOUND; A PROVISIONAL READING SITS BESIDE. Where two printed sections disagree the
    bound runs from the smallest to the largest reading (each end with its drawn basis); an owner-provisional choice or a
    single reading (one side of a band lost) is reported beside, never as the bound, and never replaces it.
R-T659-5 HELD NEVER 0. A low end of 0 only where the open question is whether the element is built at all
    (existence_open); a blank line names its item; a total is stated only when no component is blank.

Provenance: T-659 (2026-11-09), on R-T572-1 .. 4, T-319 (parapet floor, R-T311-2), Q-27 A, Q-28 A (provisional), Q-65 C,
D-14, D-15, D-33, D-35, D-39, D-43. Scope: every villa.
"""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP

Q6 = Decimal("0.000001")
STATUSES = ("VALUED", "BOUNDED", "LOWER_ONLY", "HELD_BLANK")
REFUSED_BASIS = ("GENERIC", "DEFAULT", "ASSUMED", "BORROWED", "FREELANCER", "TYPICAL VALUE")
UNPRINTED_MARKERS = ("AS PER ARCH", "SEE ARCH PLAN", "AS PER SCHEDULE", "AS PER LIFT MANUFACTURER", "NOT PRINTED")
MAX_M = Decimal("200")  # a dimension above this in metres (a 1300 pad length) is read as a unit slip (mm), refused


class Refused(ValueError):
    """A reading the rules refuse."""


def d6(x) -> Decimal:
    if x is None:
        raise Refused("missing value: carry it HELD with its item, never 0")
    if isinstance(x, bool):
        raise Refused("not a quantity")
    if isinstance(x, str):
        s = x.strip().lower()
        if s.endswith("mm"):
            raise Refused("lengths in m only (mm refused)")
        if s.endswith("%"):
            raise Refused("a percentage is not a quantity")
    v = Decimal(str(x))
    if v < 0:
        raise Refused("negative quantity")
    return v.quantize(Q6, rounding=ROUND_HALF_UP)


def dim(x, source: str) -> Decimal:
    """A printed dimension in metres with its source (R-T659-1)."""
    if not source or not str(source).strip():
        raise Refused("a dimension without its printed source")
    up = str(source).upper()
    if any(m in up for m in UNPRINTED_MARKERS):
        raise Refused(f"not a printed figure: {source}")
    if any(b in up for b in REFUSED_BASIS):
        raise Refused(f"refused basis: {source}")
    v = d6(x)
    if v == 0:
        raise Refused("a zero dimension")
    if v > MAX_M:
        raise Refused(f"{v} m is not a member dimension (mm slip?)")
    return v


def box(l: Decimal, w: Decimal, h: Decimal) -> Decimal:
    return (l * w * h).quantize(Q6, rounding=ROUND_HALF_UP)


def pad_net_of_through_beam(pad_l, pad_w, pad_t, beam_b, beam_d) -> dict:
    """R-T659-3: the pad's own solid net of the ground beam that runs through it on the same soffit."""
    for v in (pad_l, pad_w, pad_t, beam_b, beam_d):
        if not isinstance(v, Decimal):
            raise Refused("dimensions must come through dim()")
    if beam_b >= pad_w:
        raise Refused("beam wider than the pad: the pad is not a separate element")
    gross = box(pad_l, pad_w, pad_t)
    shared = box(beam_b, pad_l, min(pad_t, beam_d))
    return {"gross_m3": gross, "shared_with_beam_m3": shared, "net_m3": (gross - shared).quantize(Q6)}


def cap_area_per_m(chord: Decimal, rise: Decimal) -> Decimal:
    """Outer surface of a spherical cap (pi (a^2 + h^2)), m2 = m3 of shell per m of thickness (thin-shell coefficient)."""
    a = chord / 2
    return (Decimal(str(math.pi)) * (a * a + rise * rise)).quantize(Q6, rounding=ROUND_HALF_UP)


def component(line_id, item_code, element, status, *, low=None, high=None, value=None, low_basis=None, high_basis=None,
              item=None, existence_open=False, floor=None, coefficients=None, beside=None, sources=None) -> dict:
    """One ledger row, checked against R-T659-1 .. 5."""
    if status not in STATUSES:
        raise Refused(f"status {status}")
    for b in (low_basis, high_basis):
        if b and any(r in b.upper() for r in REFUSED_BASIS):
            raise Refused(f"refused basis for a bound: {b}")
    row = {"line_id": line_id, "item_code": item_code, "element_id": element, "status": status, "unit": "m3",
           "value": None, "low": None, "high": None, "low_basis": low_basis, "high_basis": high_basis, "item": item,
           "existence_open": bool(existence_open), "floor": floor, "coefficients": coefficients or [],
           "beside": beside or [], "sources": sources or []}
    if status == "VALUED":
        if value is None or low is not None or high is not None or item:
            raise Refused("a valued line carries one figure and no held item")
        row["value"] = str(d6(value))
    elif status == "BOUNDED":
        lo, hi = d6(low), d6(high)
        if lo > hi:
            raise Refused("low above high")
        if lo == 0 and not existence_open:
            raise Refused("a low of 0 only where the element's existence is open (R-T659-5)")
        if not (low_basis and high_basis):
            raise Refused("each end needs its drawn basis")
        if not item:
            raise Refused("a bounded line names what keeps it from a value")
        row["low"], row["high"] = str(lo), str(hi)
    elif status == "LOWER_ONLY":
        lo = d6(low)
        if lo == 0:
            raise Refused("a lower-only bound of 0 says nothing: carry the line blank")
        if not (low_basis and item):
            raise Refused("lower basis and the open upper item are required")
        row["low"] = str(lo)
    else:  # HELD_BLANK
        if value is not None or low is not None or high is not None:
            raise Refused("a blank line carries no figure (R-T659-2: floors and coefficients go beside)")
        if not item:
            raise Refused("a blank line names its item")
    if floor is not None:
        if status != "HELD_BLANK":
            raise Refused("an AT_LEAST floor travels beside a blank line only")
        if not floor.get("basis") or not floor.get("status"):
            raise Refused("a floor needs its basis and status")
        floor["m3"] = str(d6(floor["m3"]))
    for c in row["coefficients"]:
        if not c.get("per") or not c.get("basis"):
            raise Refused("a coefficient needs its unit factor and basis")
        c["m3_per_unit"] = str(d6(c["m3_per_unit"]))
        if c.get("applied_to_count") is not None:
            raise Refused("a coefficient is never multiplied by an unprinted count (R-T659-2)")
    for b in row["beside"]:
        if b.get("as_bound"):
            raise Refused("a provisional / single reading is reported beside, never as the bound (R-T659-4)")
    return row


def ledger_totals(rows) -> dict:
    """R-T659-5 / R-T572-3: one unit; a side is stated only when every row carries it."""
    seen = set()
    for r in rows:
        if r["line_id"] in seen:
            raise Refused(f"line {r['line_id']} twice")
        seen.add(r["line_id"])
        if r["unit"] != "m3":
            raise Refused("m3 only")
    lows = [r for r in rows if r["status"] in ("VALUED", "BOUNDED", "LOWER_ONLY")]
    blank = [r for r in rows if r["status"] == "HELD_BLANK"]
    lo = sum((Decimal(r["value"] or r["low"]) for r in lows), Decimal("0"))
    hi_ok = all(r["status"] in ("VALUED", "BOUNDED") for r in rows)
    hi = sum((Decimal(r["value"] or r["high"]) for r in rows), Decimal("0")) if hi_ok else None
    return {"lines": len(rows), "valued": sum(r["status"] == "VALUED" for r in rows),
            "bounded": sum(r["status"] == "BOUNDED" for r in rows),
            "lower_only": sum(r["status"] == "LOWER_ONLY" for r in rows), "blank": len(blank),
            "carried_low_m3": str(lo.quantize(Q6)), "carried_high_m3": str(hi.quantize(Q6)) if hi is not None else None,
            "total_stateable": not blank and hi_ok,
            "floors_beside_m3": str(sum((Decimal(r["floor"]["m3"]) for r in rows if r["floor"]), Decimal("0")).quantize(Q6))}

"""R-T648-1 FINISHES HELD-LINE CAUSE CENSUS (every villa; research provenance, proposed; no new rule value).

Every HELD line of a trial BOQ that no committed record gives a cause (finding F-T636-1) gets exactly ONE cause class, a
named source (a merged task record, an owner Q-id, a designer D-nn, a held line id) and, only where every term of the
quantity is printed, a fix row with its own hand calculation (DRAWING-CONFIRMED, not wired). Nothing is released here.

Cause classes:
  OWNER_DECISION     an ANSWERED owner decision (Q-id) or an owner-confirmed Urban rule fixes why the line is held or
                     bounded (e.g. Q-45 thickness band: a range, never a mid value)
  OWNER_OPEN         an owner item still OPEN on the board (named id: ORR-007, OD-1, OWNER_NOTES_SIGMA item 3): held
                     until answered; agents do not ask again
  DESIGNER_ITEM      a designer clarification (D-nn) or a sheet missing from the issued set (D-62) holds a term
  CHECKER_DOWNGRADE  a Checker verdict downgraded the line (cited by verdict)
  PRINTED_VALUE_GAP  a term the quantity needs is printed on no sheet (named sheet / term), with no D-nn of its own
  DEPENDENCY         the line follows another HELD line (by line id) and is released only with it
  ENGINE_DEFECT      the line is not a physical piece of its family (named engine defect / merged ruling): it stays
                     held by name until the defect is closed; never valued, never dropped

Generic rules (every villa):
  one cause           a line carries exactly one class and one primary source; secondary facts go in 'also'
  freelancer refused  a freelancer figure, row or total is never a cause and never a source
  held never 0        a HELD line keeps measured_net None; a bound <= 0 at both ends or a fix row valued 0 is refused
  fix row             only when every term is printed (or owner-fixed): value = the product of the printed terms,
                      recomputed here; status DRAWING-CONFIRMED (or ASSUMED - OWNER-APPROVED with its Q-id); not wired
  band                a bound from an owner band (Q-45) must equal area x band ends exactly (1e-6); a mid value refused
  dependency          a DEPENDENCY must name a line id that is itself HELD; a self-reference is refused
"""
from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 40
CLASSES = ("OWNER_DECISION", "OWNER_OPEN", "DESIGNER_ITEM", "CHECKER_DOWNGRADE", "PRINTED_VALUE_GAP", "DEPENDENCY",
           "ENGINE_DEFECT")
FIX_STATUSES = ("DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED")
Q6 = Decimal("0.000001")
FREELANCER_WORDS = ("freelancer", "his row", "his figure", "his total", "his sheet", "his bed", "his marble")


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


def band_bound(area_m2, band, unit_slip_guard=True):
    """(low, high) of a layer whose thickness the owner gives as a band (Q-45): area x band ends, never a mid value."""
    a = D(area_m2)
    if a is None or a <= 0:
        raise RuleError(f"area {area_m2} missing or <= 0 (held is never 0)")
    lo, hi = D(band[0]), D(band[1])
    if not (Decimal(0) < lo < hi):
        raise RuleError(f"band {band}: not a range (a single or mid value is refused)")
    if unit_slip_guard and hi > Decimal("0.5"):
        raise RuleError(f"band {band}: cm read as m refused")
    return q(a * lo), q(a * hi)


def fix_value(terms):
    """a fix row value: the product of printed terms {name: (value, source)}; every term needs a source."""
    if not terms:
        raise RuleError("fix row with no terms")
    v = Decimal(1)
    for name, (val, src) in terms.items():
        if not src:
            raise RuleError(f"term {name} has no printed source: fix row refused (HELD)")
        d = D(val)
        if d is None or d <= 0:
            raise RuleError(f"term {name} = {val}: missing or <= 0 (held is never 0)")
        if d > 50:
            raise RuleError(f"term {name} = {val} m: unit slip refused")
        v *= d
    return q(v)


def check_entry(e, held_ids=None):
    lid = e.get("line_id")
    if e.get("class") not in CLASSES:
        raise RuleError(f"{lid}: class {e.get('class')!r}")
    if not e.get("cause") or not e.get("source"):
        raise RuleError(f"{lid}: no named cause / source")
    txt = (e["cause"] + " " + e["source"]).lower()
    for w in FREELANCER_WORDS:
        if w in txt:
            raise RuleError(f"{lid}: a freelancer figure is never a cause ({w!r})")
    if e.get("measured_net") is not None:
        raise RuleError(f"{lid}: a HELD line carries a value")
    lo, hi = D(e.get("held_low")), D(e.get("held_high"))
    if lo is not None and hi is not None:
        if hi <= 0:
            raise RuleError(f"{lid}: bound {lo} .. {hi}: held as 0 refused")
        if lo > hi:
            raise RuleError(f"{lid}: low {lo} > high {hi}")
    if e["class"] == "DEPENDENCY":
        dep = e.get("depends_on")
        if not dep or dep == lid:
            raise RuleError(f"{lid}: DEPENDENCY without another line id")
        if held_ids is not None and dep not in held_ids:
            raise RuleError(f"{lid}: depends on {dep}, which is not HELD")
    if e["class"] == "OWNER_DECISION" and not e.get("owner_ref"):
        raise RuleError(f"{lid}: OWNER_DECISION without its Q-id / owner rule id")
    if e["class"] == "DESIGNER_ITEM" and not str(e.get("designer_ref", "")).startswith("D-"):
        raise RuleError(f"{lid}: DESIGNER_ITEM without its D-nn")
    fx = e.get("fix")
    if fx:
        if fx.get("status") not in FIX_STATUSES:
            raise RuleError(f"{lid}: fix row status {fx.get('status')!r}")
        v = fix_value({k: tuple(t) for k, t in fx["terms"].items()})
        if D(fx["value"]) != v:
            raise RuleError(f"{lid}: fix row {fx['value']} != product of its printed terms {v}")
        if fx.get("wired"):
            raise RuleError(f"{lid}: a fix row of this census is never wired")
    return True


def census_counts(entries, held_ids=None):
    by, by_tu = {}, {}
    seen = set()
    for e in entries:
        if e["line_id"] in seen:
            raise RuleError(f"{e['line_id']}: classed twice")
        seen.add(e["line_id"])
        check_entry(e, held_ids)
        by[e["class"]] = by.get(e["class"], 0) + 1
        k = f"{e['group']}|{e['unit']}"
        by_tu.setdefault(k, {"before_no_cause": 0, "after_with_cause": 0, "fix_rows": 0})
        by_tu[k]["before_no_cause"] += 1
        by_tu[k]["after_with_cause"] += 1
        by_tu[k]["fix_rows"] += 1 if e.get("fix") else 0
    return {"lines": len(entries), "by_class": dict(sorted(by.items())),
            "fix_rows": sum(1 for e in entries if e.get("fix")),
            "by_trade_unit": dict(sorted(by_tu.items()))}

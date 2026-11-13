"""R-T734-1 .. -3: WATERPROOFING H4 EVIDENCE (every villa; research provenance, proposed; nothing wired or released).

R-T734-1 DOWNGRADE EVIDENCE FOR A RELEASED LINE ABOVE ITS OWN BAND (owner 2026-10-24 23:57; F-T705-2; R-T691-2).
  (a) A released quantity is downgrade-ELIGIBLE only when it lies OUTSIDE the band its own same-basis measurement
      establishes (low .. high, same physical element, same unit) by more than half its rounding step; inside the band
      it is not a downgrade case (an open term inside the band is shown beside, never by a record).
  (b) The record only moves the named line(s) to HELD (or CONFLICT). It carries NO quantity of its own: the released
      figure is its binding engine quantity, kept in the audit rows; never a Checker measurement, never a promotion.
  (c) The after-state the wiring package writes once the record applies is the measured band (both ends from the
      drawing), not the high end: an end is never chosen because it is larger, closer to another figure or "safer".
  (d) A correction that RAISES a released value (a chord ring under-measured) is never a downgrade: it is a Gate B
      change of a released value with its own re-measure; it needs no record and waits on none.
  (e) Without a valid record the released figure stays as released: a package never replaces it by itself.

R-T734-2 OUTLINE BY NAMED LINES (independent re-measure of an orthogonal face). A face bounded by straight drawn
  lines is rebuilt from the lines themselves: the ordered boundary alternates horizontal (y) and vertical (x) carrier
  lines (collinear pieces on one carrier, a door gap closed on the wall's outer face, merged), each vertex is the
  intersection of two consecutive carriers, area by the shoelace and perimeter by the edge sum. No buffer, snapping or
  flood fill: a carrier that is not perpendicular to its neighbour, or a self-crossing ring, is refused.

R-T734-3 CENSUS RESTATEMENT ACROSS CANDIDATES (refines R-T710-3). Every census entry is checked on the new candidate:
  LIVE (same index entry: class, unit, value, bounds, item, element), STALE (any of those changed: named field by
  field) or GONE (line absent). A MISSING entry stays MISSING only while no line of its item code exists for its room.
  The cause is re-derived from the after-state: a penetration row whose low equals its high (no W.C. in the room) is
  MEASURABLE_NOW, not DESIGNER; a HELD entry never reads 0.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

Q6 = Decimal("0.000001")
DOWNGRADE_STATES = ("HELD", "CONFLICT")
QUANTITY_KEYS = ("checker_qty", "qty", "measured_net", "corrected_qty", "value", "low", "high")


class RuleError(Exception):
    pass


def D(x):
    if x is None:
        raise RuleError("missing value")
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        raise RuleError("not a finite number")
    try:
        d = Decimal(str(x))
    except Exception as ex:                                       # noqa: BLE001
        raise RuleError(f"not a number: {x!r}") from ex
    if not d.is_finite():
        raise RuleError("not a finite number")
    return d


def q6(v):
    return D(v).quantize(Q6, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------------------------------- R-T734-1
def eligibility(released, low, high, step="0.001"):
    """R-T734-1 (a): ABOVE_BAND / BELOW_BAND / INSIDE_BAND for a released value against its own band. Half a rounding
    step of the released figure is tolerated (a 3-decimal line may sit 0.0005 outside an exact bound)."""
    r, lo, hi, h = D(released), D(low), D(high), D(step) / 2
    if lo < 0 or hi < 0 or r < 0:
        raise RuleError("a quantity is never negative")
    if lo > hi:
        raise RuleError("inverted band (low above high)")
    if r > hi + h:
        return {"state": "ABOVE_BAND", "excess": q6(r - hi), "eligible": True}
    if r < lo - h:
        return {"state": "BELOW_BAND", "excess": q6(r - lo), "eligible": True}
    return {"state": "INSIDE_BAND", "excess": Decimal("0.000000"), "eligible": False}


def record_draft(*, candidate_version, line_ids, unit, engine_qty, state, basis_label, reason, evidence):
    """R-T734-1 (b): the fields a Checker types into `boq_export_v1.py downgrade-add` (the tool binds project, revision
    set and line content from the candidate itself). Refused: a promotion state, a quantity of its own, no evidence."""
    if state not in DOWNGRADE_STATES:
        raise RuleError(f"state {state!r}: a record can only downgrade ({DOWNGRADE_STATES})")
    ids = list(line_ids)
    if not ids or len(set(ids)) != len(ids):
        raise RuleError("a record names at least one line, each once")
    if not evidence or any("=" not in e for e in evidence):
        raise RuleError("evidence: one or more 'SHEET=PRINTED VALUE' items")
    if not reason or not basis_label:
        raise RuleError("reason and basis label are required")
    return {"candidate_version": candidate_version, "line_ids": sorted(ids), "unit": unit,
            "engine_qty_binding": float(q6(engine_qty)), "state": state, "basis_label": basis_label,
            "reason": reason, "evidence": list(evidence)}


def validate_draft(d):
    """-> [problems]: a draft that carries a quantity of its own or promotes is refused (R-T734-1 (b))."""
    p = [f"{k}: a downgrade carries no quantity of its own" for k in QUANTITY_KEYS if k in d]
    if d.get("state") not in DOWNGRADE_STATES:
        p.append(f"state {d.get('state')!r} is not a downgrade")
    if not d.get("line_ids"):
        p.append("line_ids required")
    if not d.get("evidence"):
        p.append("evidence required")
    return p


def after_state(released, band, record=None):
    """R-T734-1 (c) / (e): what the wiring package may write for a released line. Without a valid record (one naming
    this line, a downgrade state, binding the released figure) the line stays RELEASED at its figure. With it, the line
    is HELD with the band; a band that would RAISE the line above its released figure is refused (a downgrade never
    raises)."""
    r = D(released)
    if record is None:
        return {"class": "RELEASED", "value": q6(r), "why": "no Checker downgrade record: the released figure stands"}
    if validate_draft(record):
        return {"class": "RELEASED", "value": q6(r), "why": "record invalid: " + "; ".join(validate_draft(record))}
    if abs(D(record["engine_qty_binding"]) - r) > Decimal("0.0005"):
        return {"class": "RELEASED", "value": q6(r), "why": "record binds another quantity (STALE): not applied"}
    lo, hi = D(band[0]), D(band[1])
    if lo > hi:
        raise RuleError("inverted band")
    if hi > r:
        raise RuleError("a downgrade never raises: the band's high end lies above the released figure")
    return {"class": "HELD", "low": q6(lo), "high": q6(hi), "audit_candidate_qty": q6(r),
            "why": f"{record['state']}: {record['basis_label']}"}


def is_downgrade(before, after):
    """R-T734-1 (d): a change is a downgrade only when it lowers (or holds) a released value; a raise never is."""
    return D(after) < D(before)


# ---------------------------------------------------------------------------------------------------- R-T734-2
def ortho_ring(carriers):
    """R-T734-2: carriers = ordered [('H', y) | ('V', x), ...] around the face, alternating; -> vertices (closed)."""
    n = len(carriers)
    if n < 4 or n % 2:
        raise RuleError("an orthogonal ring needs an even number (>= 4) of alternating carriers")
    for i in range(n):
        a, b = carriers[i][0], carriers[(i + 1) % n][0]
        if a not in ("H", "V") or b not in ("H", "V"):
            raise RuleError(f"carrier kind {a!r} / {b!r}")
        if a == b:
            raise RuleError(f"carriers {i} and {(i + 1) % n} are parallel: merge collinear pieces first")
    pts = []
    for i in range(n):
        k, v = carriers[i]
        k2, v2 = carriers[(i + 1) % n]
        pts.append((D(v2), D(v)) if k == "H" else (D(v), D(v2)))
    return pts


def shoelace(pts):
    s = Decimal(0)
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def perimeter(pts):
    t = Decimal(0)
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        t += abs(x2 - x1) + abs(y2 - y1)                          # orthogonal edges only
    return t


def _segments_cross(p1, p2, p3, p4):
    def o(a, b, c):
        v = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
        return (v > 0) - (v < 0)
    return o(p1, p2, p3) * o(p1, p2, p4) < 0 and o(p3, p4, p1) * o(p3, p4, p2) < 0


def face(carriers, unit_scale="1"):
    """R-T734-2: area (m2) and perimeter (m) of the ring the carriers bound; coordinates in drawing units x unit_scale
    metres (mm -> 0.001). A self-crossing ring is refused."""
    s = D(unit_scale)
    pts = [(x * s, y * s) for x, y in ortho_ring(carriers)]
    n = len(pts)
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if _segments_cross(pts[i], pts[(i + 1) % n], pts[j], pts[(j + 1) % n]):
                raise RuleError("self-crossing ring: the carrier order is wrong")
    a = shoelace(pts)
    if a == 0:
        raise RuleError("zero-area ring")
    return {"area_m2": q6(a), "perimeter_m": q6(perimeter(pts)), "vertices": n}


def net_membrane(face_m2, discs_r_m, *, chords=None):
    """flat membrane = face - every disc; discs at TRUE pi r^2 (R-T691-1) or, when chords is given, as the inscribed
    n-chord polygon a 1 mm-sagitta trace leaves (to reconstruct an engine figure, never as the corrected value)."""
    f = D(face_m2)
    tot = Decimal(0)
    for r in discs_r_m:
        r = D(r)
        if r <= 0:
            raise RuleError("radius must be positive")
        if r > 50:
            raise RuleError("radius above 50 m: mm read as m")
        a = (D(math.pi) * r * r) if chords is None else D(chords / 2 * float(r) ** 2 * math.sin(2 * math.pi / chords))
        tot += a
    if tot >= f:
        raise RuleError("openings larger than the face")
    return q6(f - tot)


# ---------------------------------------------------------------------------------------------------- R-T734-3
FIELDS = ("class", "unit", "measured_net", "held_low", "held_high", "item_code", "element_id")


def restate(old, new):
    """R-T734-3: LIVE / STALE (fields named) / GONE for one index entry across two candidates."""
    if old is None:
        raise RuleError("no entry on the old candidate: not a census row")
    if new is None:
        return {"state": "GONE", "changed": []}
    ch = [f for f in FIELDS if old.get(f) != new.get(f)]
    return {"state": "STALE" if ch else "LIVE", "changed": ch}


def missing_still_missing(item_code, room_id, lines):
    """R-T734-3: a MISSING family stays MISSING only while no line of its item code exists for its room."""
    if not room_id:
        raise RuleError("a missing entry names its room")
    return not any(ln["item_code"] == item_code and str(ln["element_id"]).startswith(room_id + ":") for ln in lines)


def penetration_cause(low, high):
    """R-T734-3: firm count (low == high) is MEASURABLE_NOW; an open W.C. term is DESIGNER (pan outlet type)."""
    lo, hi = D(low), D(high)
    if lo < 1:
        raise RuleError("a printed floor drain gives at least 1: a penetration count never reads 0")
    if hi < lo:
        raise RuleError("inverted count")
    if lo != lo.to_integral_value() or hi != hi.to_integral_value():
        raise RuleError("pcs are whole numbers")
    return "MEASURABLE_NOW" if lo == hi else "DESIGNER"


def census_counts(entries):
    """counts by cause; refuses an entry without exactly one cause or a HELD entry reading 0"""
    out = {}
    for e in entries:
        c = e.get("cause")
        if not c or not isinstance(c, str):
            raise RuleError(f"{e.get('key')}: no cause")
        if e.get("status") == "HELD" and e.get("value") in (0, 0.0, "0", Decimal(0)):
            raise RuleError(f"{e.get('key')}: HELD read as 0")
        out[c] = out.get(c, 0) + 1
    return dict(sorted(out.items()))

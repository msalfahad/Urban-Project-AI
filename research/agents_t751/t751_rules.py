"""R-T751-1 .. -4 1.0.0 (every villa): closing the exterior paint edge / corner bounds from the drawn elevations
(OWNER RULE PAINT 2026-11-12, UP-FIN-PAINT-002 1.0.0: "lm for windows doors and corners, so the Area is the same";
OD-V3-4 beads are separate lm items; R-T746-1..3, R-T747-1..3 unchanged and still in force).

Physical element: one external arris (vertical building corner, opening jamb / head edge) counted once, in lm, from
the plan and the elevation together; an area attribution is decided by the plane the piece is drawn in.

R-T751-1 VERTICAL CORNER ABOVE A DATUM (parapet ends, plinth corners):
  1. The arris at a convex corner runs from the datum to the TOP OF THE CORNER as drawn at that corner: the corner's
     own outline line in the elevation that sees both faces (its end point), or a printed level at that corner.
  2. Where the drawn top of the corner is ROUNDED (an end round of radius r in the elevation plane), the vertical arris
     stops at the tangent point (top - r); the developed round belongs to the top-edge run, never to the corner item
     (one arris, one item). The round is shown beside the corner (developed pi r / 2) so the top-edge owner can take it.
  3. A higher face standing BEHIND the corner (drawn on the beyond / hidden layer, not on the corner's own outline)
     does not raise the corner: it is a separate element (step, stop-end) and is named, never added here.
  4. A corner with no drawn and no printed top stays HELD with its cause, as the bound it had; never 0, never the
     bound's high end.
  5. Units: metres; a level that reads as millimetres (> 100) or a top below its datum is refused.
R-T751-2 ARCHED OPENING EDGE: outside edge = 2 x (springing - sill) + the developed head measured along the drawn
  head line (a chain of the opening's own line from jamb top to jamb top); a rectangle composition 2 x (crown - sill)
  + w is refused wherever the head is drawn arched; the developed figure is checked against the merged ledger
  (|diff| <= 0.001 m per opening) and the residual rectangle - developed is named per opening.
R-T751-3 PLANE ATTRIBUTION: a drawn piece (stones, a surround) belongs to the face drawn in the SAME plane (the front
  layer); a door / wall drawn beyond (hidden / beyond layer) behind it is another face. A zone is deducted only from
  the face it lies on; a zone on an open side (no face key) is its own missing item, never a deduction elsewhere.
R-T751-4 BOUND CLOSURE: a closed value must lie inside the bound it closes (low <= value <= high), else the earlier
  bound or the new reading is wrong and the closure is refused; every closure carries its handles.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

RULE_IDS = ("R-T751-1", "R-T751-2", "R-T751-3", "R-T751-4")
VERSION = "1.0.0"
Q = Decimal("0.000001")
MAX_LEVEL_M = Decimal("100")
LEDGER_TOL = Decimal("0.001")
FRONT_LAYERS = ("1",)
BEYOND_LAYERS = ("5",)


class RuleError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise RuleError("a missing value is HELD, not a number")
    if isinstance(x, bool):
        raise RuleError("not a number")
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
    return D(x).quantize(Q, rounding=ROUND_HALF_UP)


def s6(x) -> str:
    return str(q6(x))


def _level(x, name):
    v = D(x)
    if v > MAX_LEVEL_M or v < -MAX_LEVEL_M:
        raise RuleError(f"{name} {v} reads as millimetres: levels are metres")
    return v


def corner_extra(corner, datum, *, top=None, round_r=None, source=None, held=None):
    """R-T751-1: lm of a vertical corner arris above `datum`.

    top: the drawn / printed top of the corner itself (metres) or None when not drawn and not printed.
    round_r: radius of the drawn end round at the top (the arris stops at the tangent point top - r).
    held: the (low, high) bound kept when top is None (with its cause in `source`).
    """
    d = _level(datum, "datum")
    if top is None:
        if held is None:
            raise RuleError(f"{corner}: no drawn top and no bound: HELD blank must be named, never 0")
        lo, hi = D(held[0]), D(held[1])
        if lo < 0 or hi < lo:
            raise RuleError(f"{corner}: bad bound {held}")
        return {"corner": corner, "state": "HELD", "lm": [s6(lo), s6(hi)], "source": source, "round_lm": None}
    t = _level(top, "top")
    r = D(0) if round_r is None else D(round_r)
    if r < 0:
        raise RuleError(f"{corner}: negative round radius")
    tangent = t - r
    if tangent < d:
        raise RuleError(f"{corner}: top {t} - round {r} lies below the datum {d}")
    lm = tangent - d
    rnd = None if r == 0 else s6(D(str(math.pi)) * r / 2)
    return {"corner": corner, "state": "DRAWN", "lm": [s6(lm), s6(lm)], "source": source, "round_lm": rnd,
            "top": s6(t), "tangent": s6(tangent)}


def arched_edge(opening, *, sill, springing, head_developed, width, crown, ledger=None):
    """R-T751-2: outside jambs + developed head (lm); returns the rectangle composition beside it, refused as the
    governing figure."""
    s, sp, c = _level(sill, "sill"), _level(springing, "springing"), _level(crown, "crown")
    h, w = D(head_developed), D(width)
    if not (s < sp <= c):
        raise RuleError(f"{opening}: sill {s} / springing {sp} / crown {c} out of order")
    if w <= 0 or h <= 0:
        raise RuleError(f"{opening}: width and developed head must be positive")
    if h < w:
        raise RuleError(f"{opening}: a developed head shorter than its span is not an arch over that span")
    dev = 2 * (sp - s) + h
    rect = 2 * (c - s) + w
    out = {"opening": opening, "basis": "ARC_DEVELOPED", "lm": s6(dev), "rectangle_refused": s6(rect),
           "rectangle_minus_developed": s6(rect - dev), "jambs": s6(2 * (sp - s)), "head": s6(h)}
    if ledger is not None:
        diff = dev - D(ledger)
        if abs(diff) > LEDGER_TOL:
            raise RuleError(f"{opening}: developed {dev} vs ledger {ledger}: {diff} beyond {LEDGER_TOL}")
        out["ledger"] = s6(ledger)
        out["ledger_diff"] = s6(diff)
    return out


def plane_attribution(piece_layer, face_layer):
    """R-T751-3: ON_FACE when the piece and the face are drawn in the same (front) plane; OFF_FACE when the face is
    drawn beyond the piece; anything else is refused (no guessing)."""
    if piece_layer in FRONT_LAYERS and face_layer in FRONT_LAYERS:
        return "ON_FACE"
    if piece_layer in FRONT_LAYERS and face_layer in BEYOND_LAYERS:
        return "OFF_FACE"
    raise RuleError(f"plane not decided by layers piece {piece_layer!r} / face {face_layer!r}")


def close_bound(item, low, high, value, handles):
    """R-T751-4: a closure inside its bound, with its handles."""
    lo, hi, v = D(low), D(high), D(value)
    if hi < lo:
        raise RuleError(f"{item}: inverted bound")
    if not handles:
        raise RuleError(f"{item}: a closure needs the handles it was read from")
    if not (lo <= v <= hi):
        raise RuleError(f"{item}: closed value {v} outside its bound {lo} .. {hi}")
    return {"item": item, "before": [s6(lo), s6(hi)], "after": s6(v), "narrowed_by": s6(hi - lo), "handles": handles}


def polyline_length(points, unit="m"):
    """Developed length of a drawn head line given as its vertices (metres only; mm is refused, not converted)."""
    if unit != "m":
        raise RuleError(f"unit {unit!r}: lengths are metres")
    if len(points) < 2:
        raise RuleError("a head line needs at least two vertices")
    tot = 0.0
    for a, b in zip(points, points[1:]):
        tot += math.dist(a, b)
    return q6(repr(tot))


def sum_lm(items):
    """Sum lm items (low, high); a HELD-blank item (lm None) makes the total blank-with-part, never 0."""
    lo = hi = Decimal(0)
    blank = []
    for it in items:
        if it["lm"] is None:
            blank.append(it.get("corner") or it.get("item"))
            continue
        lo += D(it["lm"][0])
        hi += D(it["lm"][1])
    return {"lm": [s6(lo), s6(hi)], "blank": blank}

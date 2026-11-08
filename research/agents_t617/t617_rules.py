"""R-T617-1 OPENING HEAD BOUND FROM DRAWN MEMBERS (every villa; research rule, unwired; T-617).

Physical element: an opening's structural head is the underside of whatever closes the hole at the top. Where no
height is printed, the head is still bounded ABOVE by the soffit of every member drawn (or printed by note) across the
opening's width in the host wall line: a hole cannot pass through a concrete beam.

Inputs per member over the opening (all from the drawings; nothing defaulted):
  * BEAM ON PLAN: storey interval H (FFL to the next FFL, printed levels), the build-up b between the next FFL and the
    structural top of the slab carrying the beam (a drawn / verified value; for a roof the roof build-up r; b >= 0 is
    the only thing known when it is not drawn), the overall printed depth D (schedule 'D-(Depth)', slab inside it: the
    FULL basis, T-395), the slab thickness t:   soffit above this FFL = H - b - D.
  * NOTE-POSITIONED MEMBER (a printed note gives a level L, no section, no datum point): whatever point of the member L
    names (top, axis or soffit), the soffit is <= L above the note's datum; the datum is never above the FFL of the
    storey, so the soffit is <= L above the FFL. Whether the member lies on the opening's wall line must be shown by
    the drawing or the note; if not shown, the bound is a SCENARIO (reading), never applied silently.

Head bound h_max = min(soffits of the members established over the opening). Lower bound: only a printed height,
level or dimension; a plan gap, a sill at F.F.L. or a door symbol gives none (stays 0, named). A default door height
(Q-55's internal-door 2.20, the freelancer's flat 2.40) is never used for a lift entrance (R-T608-1).

Effect on a wall face of height F carrying the opening (width w, deducted in full, Q-73):
  deduction in [0, w x min(h_max, F)]  ->  the face range narrows by w x (F - h_max) only when h_max < F.
  A face measured to the slab soffit (Q-72 plaster) under a member of depth D in a slab t keeps at least w x (D - t) above
  any opening under that member: F - h_max = (H - b - t) - (H - b - D) = D - t, independent of b.
Quantities are Decimal; a missing input gives NO bound from that member (named), never a default and never 0.
"""
from __future__ import annotations

from decimal import Decimal

D = Decimal
RULE_ID = "R-T617-1"
GOVERNING = ["Q-72 (plaster to the slab underside, paint to the finished ceiling)", "Q-73 (full deduction)",
             "R-T608-1 (lift landing door: no door-trade fallback height)", "R-T395-1 (FULL depth basis)",
             "R-T556-1 (plaster height = interval - b - t)", "UP-DOOR-HGT-001 (printed heights only)", "ERS s.2 / s.3"]
REFUSED_HEIGHTS = {"2.20": "Q-55 C internal-door fallback (door trade only)", "2.40": "freelancer flat height"}


class BoundError(ValueError):
    pass


def _d(x, name):
    if x is None:
        return None
    if isinstance(x, float):
        raise BoundError(f"{name}: float refused, pass a Decimal string")
    v = D(str(x))
    if v < 0:
        raise BoundError(f"{name}: negative {v}")
    return v


def beam_soffit(interval, buildup, depth, unit="m"):
    """Soffit of a plan beam above the FFL of the storey below it. Missing input -> None (no bound), never a default."""
    if unit != "m":
        raise BoundError(f"unit {unit!r}: metres only (convert before, mm / cm refused)")
    H, b, Dp = _d(interval, "interval"), _d(buildup, "buildup"), _d(depth, "depth")
    if H is None or b is None or Dp is None:
        return None
    if Dp >= H:
        raise BoundError(f"depth {Dp} >= interval {H}: not a beam over a storey opening")
    return H - b - Dp


def note_member_soffit(level):
    """A member positioned only by a printed level: soffit <= level above the storey FFL (any reference point)."""
    return _d(level, "level")


def head_bound(members, printed_height=None):
    """members: list of dicts {id, soffit (Decimal or None), on_wall_line: True | False | 'SCENARIO'}.
    Returns {low, high, high_scenario, basis, named_missing}. A printed height settles it (low = high)."""
    if printed_height is not None:
        h = _d(printed_height, "printed_height")   # a PRINTED value is used as printed (defaults: default_height)
        return {"low": h, "high": h, "high_scenario": h, "basis": "PRINTED", "named_missing": []}
    firm, scen, missing = [], [], []
    for m in members:
        if m.get("on_wall_line") not in (True, False, "SCENARIO"):
            raise BoundError(f"{m.get('id')}: on_wall_line must be True / False / 'SCENARIO'")
        if m["on_wall_line"] is False:
            continue
        if m.get("soffit") is None:
            missing.append(m.get("id"))
            continue
        (firm if m["on_wall_line"] is True else scen).append((m["soffit"], m["id"]))
    high = min(firm) if firm else None
    high_s = min(firm + scen) if (firm or scen) else None
    return {"low": D("0"), "high": high[0] if high else None, "high_by": high[1] if high else None,
            "high_scenario": high_s[0] if high_s else None, "high_scenario_by": high_s[1] if high_s else None,
            "basis": "DRAWN_MEMBER_BOUND" if high else "NO_BOUND", "named_missing": missing}


def default_height(value):
    """Any attempt to give a lift entrance a default / borrowed height is refused."""
    raise BoundError(f"default height {value} refused for a lift entrance: {REFUSED_HEIGHTS.get(str(value), 'no source')}"
                     " (printed heights only, R-T608-1 / UP-DOOR-HGT-001)")


def face_deduction_bound(width, face_h, h_high):
    """Deduction range of one opening on one face. h_high None -> the face height (no bound)."""
    w, F = _d(width, "width"), _d(face_h, "face_h")
    if w is None or F is None:
        raise BoundError("width and face height are required (HELD upstream, never 0)")
    cap = F if h_high is None else min(F, D(str(h_high)))
    return {"low": D("0"), "high": w * cap, "narrowing": w * (F - cap)}


def opening_in_storeys(opening_id, storeys):
    """An opening id belongs to one storey: an id seen in two storeys is refused (counted once)."""
    seen = [s for s, ids in storeys.items() if opening_id in ids]
    if len(seen) != 1:
        raise BoundError(f"{opening_id}: found in {len(seen)} storeys {seen}: one storey per opening")
    return seen[0]

"""T-238 rules (proposed, every villa; pure functions, stdlib only, imported by no engine module).

UP-OPEN-ARCH-001 v1.1 (proposed; extends T-227 r2's v1, Checker ruling 2026-10-23 20:14; ERS s.3; owner Q-73 final
'deduct the actual opening, only from masonry that physically exists'; owner Q-32 A for the window line):

  A1 OPENING LINE. An opening is read on its opening line: the jamb lines the plan width binds to and the arch chain /
     arc that springs from them. A line drawn outside it (a surround band, an archivolt, a moulding, a 0.05 edge line,
     a recessed panel) is a wall-face element. A dimension chain that ends on such a line is not the opening's height.
  A2 TWO TRADES, TWO MEASURES. Masonry / plaster / paint deduct the TRUE outline: jamb rectangle (width x springing) +
     the arch segment as drawn (chain or arc, never its chord, never the enclosing rectangle). The WINDOW line keeps the
     owner's Q-32 A enclosing rectangle on the opening line (width x crown). Both are kept side by side.
  A3 EDGES. Reveal / arris lengths of an arched opening = 2 x springing + the arch LENGTH + sill (window) ; the
     rectangle perimeter 2 x crown + 2 x width is refused.
  A4 HEIGHT CAP. A finish ledger that caps an opening at the plastered height H deducts the outline clipped at H.
  A5 CURVED ON PLAN. An opening curved on plan is a developed surface: the plaster / paint deduction is the developed
     outline; until it is developed it is HELD with the enclosing bound (developed width x crown) as its upper limit.
  A6 EVIDENCE. A drawn arc with no printed dimension, bound to a census opening, is a SOURCE-SUPPORTED candidate until
     the Checker re-measures it; an arched feature not bound to a census opening is UNKNOWN (never a quantity).
"""
from __future__ import annotations

import math

DC = "DRAWING-CONFIRMED"
VERIFIED = "VERIFIED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"
SS = "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK"
OWNER = "ASSUMED — OWNER-APPROVED"
ESTABLISHED = (DC, VERIFIED)
TOL = 1e-9


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------ geometry
def profile_segment(width_m, spring_m, profile, tol=0.002):
    """Arch drawn as a chain of points (x from the left jamb 0 .. width, y above the opening bottom), from the left
    springing to the right springing. Returns (segment_m2, arch_length_m, crown_m). Refuses a chord, a profile that
    does not spring from both jambs and a point outside the jambs (A1)."""
    if not profile or len(profile) < 3:
        raise ValueError("ARCH_AS_CHORD: an arch needs its drawn profile, not only the two springing points")
    (x0, y0), (x1, y1) = profile[0], profile[-1]
    if abs(x0) > tol or abs(x1 - width_m) > tol or abs(y0 - spring_m) > tol or abs(y1 - spring_m) > tol:
        raise ValueError("ARCH_NOT_ON_OPENING_LINE: the profile must spring from both jambs at the springing level")
    for x, y in profile:
        if x < -tol or x > width_m + tol or y < spring_m - tol:
            raise ValueError("ARCH_OUTSIDE_JAMBS: a profile point lies outside the opening (band or moulding line?)")
    pts = [(0.0, spring_m)] + [tuple(p) for p in profile] + [(width_m, spring_m)]
    area = abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(len(pts)))) / 2.0
    length = sum(math.dist(profile[i], profile[i + 1]) for i in range(len(profile) - 1))
    return area, length, max(y for _, y in profile)


def circular_segment(chord_m, rise_m):
    """A segmental arch drawn as one circular arc: (segment_m2, arc_length_m, radius_m)."""
    if chord_m <= 0 or rise_m <= 0 or rise_m > chord_m / 2 + 1e-9:
        raise ValueError("SEGMENT_IMPOSSIBLE: 0 < rise <= chord / 2")
    r = (chord_m ** 2 / 4 + rise_m ** 2) / (2 * rise_m)
    th = 2 * math.asin(min(1.0, chord_m / (2 * r)))
    return r * r / 2 * (th - math.sin(th)), r * th, r


# ------------------------------------------------------------------------------------------------ the record
def arched_outline(oid, width_m, spring_m, crown_m, segment_m2, arch_length_m, band_m=None, status=DC,
                   window_width_m=None, sill_edge=True):
    """One arched opening read on its opening line (A1-A3). window_width_m: the printed width for the window line
    (Q-32 A) when it differs from the drawn width by drafting precision."""
    if None in (width_m, spring_m, crown_m, segment_m2, arch_length_m):
        return {"id": oid, "status": HELD, "reason": "OPENING_LINE_NOT_READ"}
    rise = crown_m - spring_m
    if rise <= 0 or segment_m2 <= 0 or segment_m2 > width_m * rise + 1e-6:
        raise ValueError(f"{oid}: ARCH_SEGMENT_IMPOSSIBLE (the segment must lie inside width x rise)")
    if arch_length_m < width_m - 1e-6:
        raise ValueError(f"{oid}: ARCH_SHORTER_THAN_CHORD")
    ww = width_m if window_width_m is None else window_width_m
    rect = width_m * spring_m
    return {"id": oid, "status": status, "width_m": _r(width_m), "spring_m": _r(spring_m), "crown_m": _r(crown_m),
            "jamb_rectangle_m2": _r(rect), "arch_segment_m2": _r(segment_m2),
            "masonry_deduction_m2": _r(rect + segment_m2), "finish_deduction_m2": _r(rect + segment_m2),
            "window_area_q32a_m2": _r(ww * crown_m), "arch_length_m": _r(arch_length_m),
            "reveal_lm": _r(2 * spring_m + arch_length_m + (width_m if sill_edge else 0.0)),
            "arch_edge_extra_m": _r(arch_length_m - width_m),
            "band_m": band_m, "band_crown_m": None if band_m is None else _r(crown_m + band_m)}


def clipped_finish_deduction(outline, cap_h_m, profile=None):
    """A4: the outline below a plastered height H. Exact when H >= crown or H <= springing; between them it needs
    the drawn profile (else HELD)."""
    if outline.get("status") not in ESTABLISHED + (SS,):
        return {"status": HELD, "m2": None, "reason": "OPENING_HELD"}
    w, s, c = outline["width_m"], outline["spring_m"], outline["crown_m"]
    if cap_h_m is None:
        return {"status": HELD, "m2": None, "reason": "FACE_HEIGHT_HELD"}
    if cap_h_m >= c - TOL:
        return {"status": outline["status"], "m2": outline["finish_deduction_m2"], "reason": "below the cap"}
    if cap_h_m <= s + TOL:
        return {"status": outline["status"], "m2": _r(w * cap_h_m), "reason": "cap below the springing"}
    if not profile:
        return {"status": HELD, "m2": None, "reason": "CAP_INSIDE_ARCH: profile needed"}
    pts = [(0.0, 0.0)] + [tuple(p) for p in profile] + [(w, 0.0)]
    out = []
    for i in range(len(pts)):                                  # Sutherland-Hodgman against y <= cap
        p, q = pts[i - 1], pts[i]
        pin, qin = p[1] <= cap_h_m, q[1] <= cap_h_m
        if qin:
            if not pin:
                out.append((p[0] + (q[0] - p[0]) * (cap_h_m - p[1]) / (q[1] - p[1]), cap_h_m))
            out.append(q)
        elif pin:
            out.append((p[0] + (q[0] - p[0]) * (cap_h_m - p[1]) / (q[1] - p[1]), cap_h_m))
    a = abs(sum(out[i][0] * out[i - 1][1] - out[i - 1][0] * out[i][1] for i in range(len(out)))) / 2.0
    return {"status": outline["status"], "m2": _r(a), "reason": "clipped at the cap"}


def curved_plan_bound(oid, developed_width_m, crown_lo_m, crown_hi_m):
    """A5: a window curved on plan. The finish deduction is HELD until the developed outline is drawn; the enclosing
    developed rectangle on the opening crown is its upper bound (never the surround crown)."""
    return {"id": oid, "status": HELD, "finish_deduction_upper_m2": _r(developed_width_m * crown_hi_m),
            "window_q32a_range_m2": (_r(developed_width_m * crown_lo_m), _r(developed_width_m * crown_hi_m)),
            "reason": "CURVED_ON_PLAN: developed outline not drawn"}


# ------------------------------------------------------------------------------------------------ checks (refusals)
def check_masonry_deduction(claimed_m2, outline, tol=0.005):
    """A2: refuse anything but the true outline for masonry / plaster / paint."""
    if outline.get("status") not in ESTABLISHED + (SS,):
        raise ValueError("OPENING_HELD: no deduction from a held outline (net stays HELD, never 0)")
    w, crown = outline["width_m"], outline["crown_m"]
    if outline.get("band_crown_m") is not None and abs(claimed_m2 - w * outline["band_crown_m"]) <= tol:
        raise ValueError("BAND_CROWN_AS_HEAD: the surround band crown was taken as the opening head")
    if abs(claimed_m2 - w * crown) <= tol:
        raise ValueError("RECTANGLE_FOR_MASONRY: width x crown is the Q-32 A window area, not the opening")
    if abs(claimed_m2 - outline["jamb_rectangle_m2"]) <= tol:
        raise ValueError("ARCH_DROPPED: the arch segment is part of the opening")
    if abs(claimed_m2 - outline["masonry_deduction_m2"]) > tol:
        raise ValueError(f"NOT_THE_OUTLINE: the deduction differs from the outline {outline['masonry_deduction_m2']}")
    return True


def check_window_area(claimed_m2, outline, window_width_m=None, tol=0.005):
    """Q-32 A on the opening line: width x crown; the band crown and the true outline are both refused."""
    w = outline["width_m"] if window_width_m is None else window_width_m
    if outline.get("band_crown_m") is not None and abs(claimed_m2 - w * outline["band_crown_m"]) <= tol:
        raise ValueError("BAND_CROWN_AS_HEAD: the window rectangle runs to the opening crown, not the band")
    if abs(claimed_m2 - w * outline["crown_m"]) > tol:
        raise ValueError(f"NOT_Q32A: window area is width x crown = {w * outline['crown_m']:.4f}")
    return True


def check_reveal(claimed_lm, outline, tol=0.005):
    """A3: an arched opening's reveal follows the arch."""
    w, c = outline["width_m"], outline["crown_m"]
    if abs(claimed_lm - (2 * c + 2 * w)) <= tol:
        raise ValueError("RECTANGLE_PERIMETER: the head of an arched opening is its arch, not a straight head")
    if abs(claimed_lm - outline["reveal_lm"]) > tol:
        raise ValueError(f"NOT_THE_REVEAL: 2 x springing + arch + sill = {outline['reveal_lm']}")
    return True


def dimension_target(chain_end_m, opening_crown_m, band_crowns_m=(), tol=0.003):
    """A1: what a vertical dimension chain ends on. 'OPENING' when it ends on the opening crown, 'BAND' when it ends
    on a line outside the opening, else 'UNBOUND'."""
    if abs(chain_end_m - opening_crown_m) <= tol:
        return "OPENING"
    if any(abs(chain_end_m - b) <= tol for b in band_crowns_m):
        return "BAND"
    return "UNBOUND"


# ------------------------------------------------------------------------------------------------ census + delta
CENSUS_CODES = {
    "RECT_ON_OPENING_LINE": "rectangular; outline = jamb lines (width equals the plan width); no arc, no outer chain",
    "ARCH_READ_ON_OPENING_LINE": "arched; the merged ledgers already read the opening line",
    "BAND_CROWN_READ_AS_HEAD": "arched with a surround; a merged ledger read the band crown (defect)",
    "ARCH_READ_AS_RECTANGLE": "arched; a merged ledger deducted width x crown from masonry / finishes (defect)",
    "CURVED_ON_PLAN": "curved on plan; developed outline HELD (A5)",
    "ARCH_DRAWN_NOT_DIMENSIONED": "arched; drawn outline, no printed dimension: SOURCE-SUPPORTED candidate (A6)",
    "NOT_DRAWN": "no elevation / section draws the opening: HELD",
    "HELD_ELSEWHERE": "outline held for another cause (width / count / view)",
    "FEATURE_NOT_AN_OPENING": "arched wall-face or open-side feature, not a census opening",
    "UNBOUND_FEATURE": "arched feature not bound to a census opening: UNKNOWN",
}


def census_code(form, arc_drawn, merged_head_m=None, opening_crown_m=None, band_crown_m=None,
                merged_masonry_m2=None, outline_m2=None, curved_on_plan=False, drawn=True, tol=0.003):
    """Classify one census opening against the merged ledgers (procedure step 1-2 of T-238)."""
    if not drawn:
        return "NOT_DRAWN"
    if curved_on_plan:
        return "CURVED_ON_PLAN"
    if not arc_drawn:
        return "RECT_ON_OPENING_LINE"
    if merged_head_m is not None and band_crown_m is not None and abs(merged_head_m - band_crown_m) <= tol:
        return "BAND_CROWN_READ_AS_HEAD"
    if merged_masonry_m2 is not None and outline_m2 is not None and abs(merged_masonry_m2 - outline_m2) > 0.005:
        return "ARCH_READ_AS_RECTANGLE"
    if merged_head_m is None:
        return "ARCH_DRAWN_NOT_DIMENSIONED"
    return "ARCH_READ_ON_OPENING_LINE"


def delta_row(line, opening, ledger, item, unit, old, new, new_status, cause, applied_by=""):
    """One DELTA row: old -> new with its cause; HELD stays visible (never 0)."""
    def fmt(v):
        if v is None:
            return "HELD"
        if isinstance(v, str):
            return v
        return f"{v:.3f}"
    ch = ""
    if isinstance(old, (int, float)) and isinstance(new, (int, float)):
        ch = f"{new - old:+.3f}"
    elif new is None or isinstance(new, str):
        ch = "to HELD" if not (isinstance(old, str) or old is None) else "unchanged (HELD)"
    elif old is None or isinstance(old, str):
        ch = "HELD -> value"
    return {"line": line, "opening": opening, "merged_ledger": ledger, "item": item, "unit": unit, "old": fmt(old),
            "new": fmt(new), "change": ch, "new_status": new_status, "cause": cause, "applied_by": applied_by}

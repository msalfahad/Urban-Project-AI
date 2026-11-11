"""T-688 rules (project-agnostic; scope: any villa's suspended or ground slab plan drawn as member / slab edge lines,
any reference workbook). Research only, unwired: changes no line, no quantity, no frozen method, no rule version file.

R-T688-1 1.0.0  OWN PANEL NODING OF A SLAB PLAN. Provenance: T-688 (1F slab residual, development villa), the Checker
    re-measures of T-180 P18 (unnoded line ends 0.003 mm short of their carrier), ERS s.2.2 (define the physical element
    first). The physical element "slab panel" is the concrete between member faces, net of drawn voids and of stair
    zones, at its own thickness.
    (a) Faces come from the plan's edge lines (members, slab edges, column outlines, void outlines) after every open
        segment end is extended by ext (gap closing) and the set is noded + polygonized; no detector region label is
        used.
    (b) A face crossed by at least two opening-symbol lines (the drawn X of a void, the radial lines of a dome opening)
        that span it (their envelope covers at least 80 % of the face's envelope) is an OPENING: never slab, never
        0-filled, listed with its area. A symbol sitting in a corner of a larger face means the void outline did not
        close (an unnoded end): the face is not an opening and the void is not deducted, so the noding of (a) must
        close it first (tested adversely).
    (c) A face no wider than the widest drawn member section (narrow side of its minimum rotated rectangle, tolerance
        tol) and carrying no level mark of its own is a BAND (member strip), not slab.
    (d) Every other face inside the plan is a PANEL; its area is the face area; the plan is invariant under mirror,
        rotation and unit scale (tested), so a panel's area may never depend on orientation or drawing units.

R-T688-2 1.0.0  A REFERENCE AREA TYPED AS A ROUND CONSTANT. Provenance: T-683 R-T683-2 (slab storey bridge: GF 207,
    1F 120, roof 31.84 / 13.35 m2, all typed, no derivation), T-688, ERS s.2.6 (reconcile to the physical or
    mathematical cause and name the residual).
    (a) A reference area with no derivation (a typed constant) is read only at the resolution of its last printed digit
        (u = 1 m2 for 120, 0.01 m2 for 31.84): the reference measured value lies in [v - u/2, v + u/2]; the rounding
        component of the difference is bounded by +- u/2 x t, the rest is SCOPE (a part of the drawn element the
        reference left out, or added).
    (b) Before a scope is claimed, the engine geometry is re-measured independently (own noding, R-T688-1); a difference
        engine vs own beyond the tolerance is OUR ERROR and is named first.
    (c) The scope is attributed to a set of drawn panels ONLY when exactly one subset of the engine panels fits the
        scope band (UNIQUE_CANDIDATE, still a candidate, never VERIFIED); when several fit it stays UNRESOLVED with the
        count of fitting subsets; when none fits, the gap is not whole panels (convention or partial panel: name it).
        The subset closest to the reference is never picked (ERS: never choose a number because it is closer).
    (d) The convention check is made on the reference's other storeys of the same sheet: a storey whose typed value
        agrees with the engine within its own rounding band shows the same measuring convention (panel net between
        member faces), so the storey that does not agree is scope, not convention.

R-T688-3 1.0.0  A DETECTOR REGION LABEL IS NOT THE PHYSICAL ELEMENT. Provenance: Checker F-V-P18-2 (2026-11-10 22:57):
    a ground-floor face 0.95 x 1.20 m with its own level mark +0.30 labelled BEAM_STRIP inside a band that pairs two
    panel edges; lessons register proposal of the same run.
    (a) A face is a member strip only when its width equals a drawn member section (within tol) AND it carries no level
        mark of its own; a face carrying its own level mark is slab (a level is printed on a floor, not on a beam), and
        a face wider than every drawn member section is slab even without a mark.
    (b) A band produced by pairing two panel edges whose distance is no drawn member section is refused as a member;
        its runs, when the member is bounded, stay outside that face.
    (c) Ownership follows the physical element: ground slab (B10-05) for a ground-slab face, the ground-beam line
        (B10-04) only for the drawn member strip.
"""
from __future__ import annotations

import itertools
import math
from decimal import Decimal

R1, R2, R3 = "R-T688-1 1.0.0", "R-T688-2 1.0.0", "R-T688-3 1.0.0"


class Refused(ValueError):
    pass


def D(v) -> Decimal:
    return Decimal(str(v))


# ------------------------------------------------------------------------------------------------ R-T688-1
def _extend(c, d):
    if d <= 0 or len(c) < 2 or c[0] == c[-1]:
        return c

    def mv(a, b):
        dx, dy = a[0] - b[0], a[1] - b[1]
        n = math.hypot(dx, dy) or 1.0
        return (a[0] + dx / n * d, a[1] + dy / n * d)
    c = list(c)
    c[0], c[-1] = mv(c[0], c[1]), mv(c[-1], c[-2])
    return c


def classify_faces(edges, openings=(), level_marks=(), *, unit_m=0.001, ext=30.0, max_member_width=0.6, tol=0.005):
    """edges / openings: lists of point lists (drawing units); level_marks: points of printed levels.
    Returns faces [{'area_m2', 'class', 'width_m', 'polygon'}] (R-T688-1 (a)-(d))."""
    from shapely.geometry import LineString, Point
    from shapely.ops import polygonize, unary_union
    if unit_m <= 0:
        raise Refused("unit_m must be positive")
    lines = [LineString(_extend(e, ext)) for e in edges if len(e) >= 2]
    ops = [LineString(o) for o in openings if len(o) >= 2]
    out = []
    for f in polygonize(unary_union(lines)):
        pieces = [f.intersection(g) for g in ops]
        pieces = [g for g in pieces if g.length > 1e-6 * (1.0 / unit_m)]
        n_op = len(pieces)
        if n_op >= 2:   # (b) the symbol must span the face, not sit in a corner of a larger (leaked) face
            span = unary_union(pieces).envelope.area / (f.envelope.area or 1.0)
            if span < 0.8:
                n_op = 0
        has_mark = any(f.contains(Point(p)) for p in level_marks)
        xs = list(f.minimum_rotated_rectangle.exterior.coords)
        w = min(math.dist(xs[0], xs[1]), math.dist(xs[1], xs[2])) * unit_m
        if n_op >= 2:
            cls = "OPENING"
        elif w <= max_member_width + tol and not has_mark:
            cls = "BAND"
        else:
            cls = "PANEL"
        out.append({"area_m2": f.area * unit_m * unit_m, "class": cls, "width_m": w, "polygon": f})
    return out


def panel_total(faces):
    return sum(f["area_m2"] for f in faces if f["class"] == "PANEL")


# ------------------------------------------------------------------------------------------------ R-T688-2
def resolution(printed: str) -> Decimal:
    """u of a typed constant from its printed digits: '120' -> 1, '31.84' -> 0.01."""
    s = printed.strip()
    if not s or not all(ch.isdigit() or ch == "." for ch in s) or s.count(".") > 1:
        raise Refused(f"not a typed numeric constant: {printed!r}")
    return Decimal(1) if "." not in s else Decimal(1).scaleb(-len(s.split(".")[1]))


def fitting_subsets(panels_m2, lo, hi, grid=Decimal("0.000001")):
    """number of subsets (by line, duplicates counted apart) of the engine panels whose sum lies in [lo, hi]."""
    counts = {0: 1}
    for v in panels_m2:
        k = int(D(v) / grid)
        nxt = dict(counts)
        for s_, m in counts.items():
            nxt[s_ + k] = nxt.get(s_ + k, 0) + m
        counts = nxt
    lo_k, hi_k = int(D(lo) / grid), int(D(hi) / grid)
    fits = sum(m for s_, m in counts.items() if lo_k <= s_ <= hi_k)
    return fits


def unique_subset(panels, lo, hi):
    """the one fitting subset (ids) when exactly one exists among small inputs, else None."""
    ids = list(panels)
    hit = None
    for r in range(1, len(ids) + 1):
        for comb in itertools.combinations(ids, r):
            s_ = sum(D(panels[i]) for i in comb)
            if D(lo) <= s_ <= D(hi):
                if hit is not None:
                    return None
                hit = comb
    return hit


def typed_constant_residual(engine_panels, own_panels, ref_printed, t, *, tol_m2="0.005", other_storeys=()):
    """engine_panels / own_panels: {line_id: m2}; ref_printed: the reference area as printed; t: thickness (m) used by
    both sides. other_storeys: [(name, engine_m2, ref_printed)] for the convention check (d).
    Returns the statement dict with the m3 split: OUR_ERROR + ROUNDING band + SCOPE band, and the status."""
    if set(engine_panels) != set(own_panels):
        raise Refused("own re-measure must locate every engine panel (R-T688-2 (b))")
    t = D(t)
    eng = sum(D(v) for v in engine_panels.values())
    own = sum(D(v) for v in own_panels.values())
    ref = D(ref_printed)
    u = resolution(ref_printed)
    our = own - eng
    our_err = abs(our) > D(tol_m2)
    diff_m3 = (ref - eng) * t
    # scope band in m2 (engine side taken at the own re-measure when ours is in error, else at the engine)
    base = own if our_err else eng
    scope_lo, scope_hi = base - (ref + u / 2), base - (ref - u / 2)
    conv = []
    for name, e_m2, r_p in other_storeys:
        ru = resolution(r_p)
        d_ = D(r_p) - D(e_m2)
        conv.append({"storey": name, "ref_minus_engine_m2": d_, "within_rounding": abs(d_) <= ru / 2})
    same_convention = bool(conv) and all(c["within_rounding"] for c in conv)
    if scope_hi < 0 or scope_lo <= 0 <= scope_hi:
        status, n = ("ROUNDING_ONLY" if scope_lo <= 0 <= scope_hi else "REFERENCE_LARGER"), None
    else:
        n = fitting_subsets(list(engine_panels.values()), scope_lo, scope_hi)
        status = "UNIQUE_CANDIDATE" if n == 1 else ("UNRESOLVED_AMBIGUOUS" if n > 1 else "NOT_WHOLE_PANELS")
    return {"rule": R2, "engine_m2": eng, "own_m2": own, "own_minus_engine_m2": our, "our_error": our_err,
            "reference_m2": ref, "resolution_m2": u, "difference_m3": diff_m3,
            "split_m3": {"our_error": (eng - own) * t if our_err else Decimal(0),
                         "own_vs_engine_noise": Decimal(0) if our_err else our * t,
                         "rounding_band": (-(u / 2) * t, (u / 2) * t),
                         "scope_band": (-scope_hi * t, -scope_lo * t)},
            "scope_band_m2": (scope_lo, scope_hi), "fitting_subsets": n, "status": status,
            "convention_check": conv, "same_convention": same_convention}


# ------------------------------------------------------------------------------------------------ R-T688-3
def face_owner(width_m, length_m, *, own_level_mark: bool, member_sections_m, tol=0.005):
    """R-T688-3: 'GROUND_SLAB' / 'MEMBER_STRIP' for one face of a ground plan; member_sections_m are the drawn widths of
    the members on that plan. A band pairing two panel edges at a distance that is no member section is refused."""
    if width_m <= 0 or length_m <= 0:
        raise Refused("face dimensions must be positive")
    w = min(width_m, length_m)
    is_section = any(abs(w - s_) <= tol for s_ in member_sections_m)
    if own_level_mark:
        return {"owner": "GROUND_SLAB", "line_family": "B10-05", "why": "own level mark: a floor, not a member"}
    if is_section:
        return {"owner": "MEMBER_STRIP", "line_family": "B10-04", "why": f"width {w:g} m = a drawn member section"}
    if w > max(member_sections_m or [0]) + tol:
        return {"owner": "GROUND_SLAB", "line_family": "B10-05", "why": f"width {w:g} m wider than every member"}
    return {"owner": "UNRESOLVED", "line_family": None, "why": f"width {w:g} m matches no member section"}


def band_refused(pair_distance_m, member_sections_m, tol=0.005):
    """R-T688-3 (b): a band from two paired panel edges at a distance that is no drawn member section is refused."""
    return not any(abs(pair_distance_m - s_) <= tol for s_ in member_sections_m)

"""T-227 rules (proposed, every villa; pure functions, stdlib only, imported by no engine module).

UP-MAS-DATUM-001  A level mark is a structural slab datum only when the documents make it one:
  R1 a printed structural level (S.S.L / T.O.S / slab top) governs;
  R2 a printed build-up under a finished mark gives slab top = mark - build-up;
  R3 a layer DRAWN (unprinted) between the level line and the hatched structure of a cut section gives slab top =
     mark - layer only for a zone of the cut zone's own type and never for a roof / terrace whose falls are printed
     (a constant drawn layer cannot carry a fall: T-214 CONSTANT_LAYER_VS_FALLS);
  R4 otherwise the mark is a finished / unknown datum: HELD (ROOF_MARK_NOT_SLAB), never the slab by subtraction.
  A storey height for the block-height rule (owner Q-60 A) exists only when BOTH bounding slab tops are established.
UP-MAS-HEADS-002  An opening is deducted from its run (owner Q-73) by width x height only when its height is
  DRAWING-CONFIRMED or VERIFIED in a merged ledger; a HELD opening keeps the net HELD with bounds, never 0.
UP-MAS-TIEBEAM-001  A tie beam called for by a note with no section printed is a deduction strip of unknown depth:
  the run's net stays HELD, the smallest held quantity is (strip length x depth); never a default depth.
UP-OPEN-LIFT-001  A lift landing (shaft) opening is a supplier / designer item: an owner door-height fallback whose
  scope is 'internal door' is not extended to it (ERS s.3); its height is HELD unless printed or drawn.
UP-MAS-VOID-001  A wall piece under an open slab void (dome / skylight opening) with no member, ring or slab drawn
  over it, and no section cutting it, has no top: HELD, never the storey height.
UP-MAS-BAND-001  A drawn wall band whose thickness is no block family and whose material is printed nowhere is HELD on
  its material (never booked as block, never as concrete).
UP-OPEN-ARCH-001 (r2, Checker 20:14 ruling; ERS s.3; owner Q-73 final 'deduct the actual opening, only from masonry that
  physically exists'; Q-32 A for the window line)  An opening's height is read on the OPENING line. A surround band,
  moulding or stepped reveal drawn outside it is a wall-face element, never the opening. Masonry / plaster / paint
  deduct the TRUE outline: jamb rectangle (width x spring) + the arch segment as drawn (the drawn chain or arc, never
  its chord, never the enclosing rectangle). The WINDOW line keeps the owner's Q-32 A enclosing rectangle on the opening
  line (width x crown): a rule difference between trades, kept side by side.
"""
from __future__ import annotations

DC = "DRAWING-CONFIRMED"
VERIFIED = "VERIFIED"
HELD = "HELD"
SS = "SOURCE-SUPPORTED PENDING INDEPENDENT CHECK"
ESTABLISHED = (DC, VERIFIED)
BLOCK_FAMILIES_M = (0.10, 0.15, 0.20, 0.25, 0.30)
TOL = 1e-9


def _r(x, n=3):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------- UP-MAS-DATUM-001
def slab_top_from_mark(mark):
    """mark: dict(level_m, kind 'FLOOR' | 'ROOF', printed_structural_level_m, printed_buildup_m, drawn_layer_m,
    drawn_layer_zone_type, zone_type, falls_printed (bool)). Returns dict(status, slab_top_m, rule, reason)."""
    lvl = mark.get("level_m")
    if lvl is None:
        return {"status": HELD, "slab_top_m": None, "rule": "R4", "reason": "NO_LEVEL"}
    if mark.get("printed_structural_level_m") is not None:
        return {"status": DC, "slab_top_m": _r(mark["printed_structural_level_m"]), "rule": "R1",
                "reason": "printed structural level"}
    if mark.get("printed_buildup_m") is not None:
        b = mark["printed_buildup_m"]
        if b < 0:
            raise ValueError("a build-up is a thickness (>= 0)")
        return {"status": DC, "slab_top_m": _r(lvl - b), "rule": "R2", "reason": "printed build-up"}
    layer = mark.get("drawn_layer_m")
    if layer is not None:
        if mark.get("kind") == "ROOF" or mark.get("falls_printed"):
            return {"status": HELD, "slab_top_m": None, "rule": "R3",
                    "reason": "CONSTANT_LAYER_VS_FALLS: a constant drawn layer is not a roof build-up (falls printed)"}
        if mark.get("drawn_layer_zone_type") != mark.get("zone_type"):
            return {"status": HELD, "slab_top_m": None, "rule": "R3",
                    "reason": "LAYER_OTHER_ZONE: the drawn layer belongs to another zone type"}
        return {"status": DC, "slab_top_m": _r(lvl - layer), "rule": "R3", "reason": "drawn layer, same zone type"}
    return {"status": HELD, "slab_top_m": None, "rule": "R4",
            "reason": "ROOF_MARK_NOT_SLAB" if mark.get("kind") == "ROOF" else "FINISHED_MARK_NOT_SLAB"}


def storey_structural_height(floor_mark, roof_mark):
    lo, hi = slab_top_from_mark(floor_mark), slab_top_from_mark(roof_mark)
    if lo["status"] in ESTABLISHED and hi["status"] in ESTABLISHED:
        return {"status": DC, "height_m": _r(hi["slab_top_m"] - lo["slab_top_m"]), "floor": lo, "roof": hi}
    return {"status": HELD, "height_m": None, "floor": lo, "roof": hi,
            "reason": "; ".join(f"{n}: {d['reason']}" for n, d in (("floor", lo), ("roof", hi))
                                if d["status"] not in ESTABLISHED)}


def block_height_under_member(storey, depth_m):
    """Owner Q-60 A: slab top to the underside of the member above (beam depth, or the slab where no beam)."""
    if storey["status"] not in ESTABLISHED or depth_m is None:
        return {"status": HELD, "height_m": None}
    return {"status": DC, "height_m": _r(storey["height_m"] - depth_m)}


def held_sensitivity_m2_per_cm(lengths_m):
    """m2 of gross per 0.01 m of an unknown datum, over the pieces that hang on it (information, not a quantity)."""
    return _r(sum(lengths_m) * 0.01, 4)


# ------------------------------------------------------------------------------------------- UP-MAS-HEADS-002
def apply_heads(gross_m2, gross_status, base_deductions_m2, openings, heads):
    """openings: ids inside the run still HELD before; heads: id -> dict(width_m, height_m, area_m2, status).
    Returns the new deductions, the openings still HELD and the net (formed only on an established gross with no held
    opening left)."""
    added, still = 0.0, []
    for oid in openings:
        h = heads.get(oid)
        if h and h.get("status") in ESTABLISHED and h.get("area_m2") is not None:
            if h.get("width_m") is not None and h.get("height_m") is not None:
                if abs(h["width_m"] * h["height_m"] - h["area_m2"]) > 0.0015:
                    raise ValueError(f"{oid}: area is not width x height")
            added += h["area_m2"]
        else:
            still.append(oid)
    ded = _r(base_deductions_m2 + added)
    net = None
    if gross_status in (SS, VERIFIED) and not still and gross_m2 is not None:
        net = _r(gross_m2 - ded)
        if net < -TOL:
            raise ValueError("deductions exceed the gross face")
    return {"deductions_m2": ded, "added_m2": _r(added), "still_held": still, "net_m2": net}


# ------------------------------------------------------------------------------------------- UP-MAS-TIEBEAM-001
def tie_beam_strip(storey_m, threshold_m, strip_length_m, depth_m=None, storey_status=DC):
    """A note 'tie beams at <level> where the storey is higher than <threshold>'. Returns whether it applies and
    the strip area (HELD without a printed depth)."""
    if storey_status not in ESTABLISHED or storey_m is None:
        return {"applies": None, "status": HELD, "strip_m2": None, "reason": "storey height not established"}
    if storey_m <= threshold_m + TOL:
        return {"applies": False, "status": DC, "strip_m2": 0.0, "reason": "storey not above the threshold"}
    if depth_m is None:
        return {"applies": True, "status": HELD, "strip_m2": None,
                "reason": f"tie beam required; section not printed: strip {strip_length_m:.3f} m x depth HELD"}
    return {"applies": True, "status": DC, "strip_m2": _r(strip_length_m * depth_m), "reason": "printed section"}


# ------------------------------------------------------------------------------------------- UP-OPEN-LIFT-001
def opening_height(kind, printed_m=None, drawn_m=None, owner_fallback=None):
    """owner_fallback: dict(height_m, scope) e.g. the Q-55 'internal door' fallback. Returns dict(status, height_m)."""
    if printed_m is not None:
        return {"status": DC, "height_m": printed_m, "basis": "printed"}
    if drawn_m is not None:
        return {"status": DC, "height_m": drawn_m, "basis": "drawn"}
    if owner_fallback and owner_fallback.get("scope") == kind:
        return {"status": "ASSUMED — OWNER-APPROVED", "height_m": owner_fallback["height_m"], "basis": "owner fallback"}
    return {"status": HELD, "height_m": None,
            "basis": "no printed / drawn height; owner fallback scope "
                     f"{(owner_fallback or {}).get('scope', 'none')} does not cover {kind}"}


# ------------------------------------------------------------------------------------------- UP-MAS-VOID-001
def piece_top(member_above=None, section_top_m=None):
    if member_above is not None:
        return {"status": DC, "top": member_above}
    if section_top_m is not None:
        return {"status": DC, "top": section_top_m}
    return {"status": HELD, "top": None, "reason": "UNDER_OPEN_VOID: nothing drawn over the piece"}


# ------------------------------------------------------------------------------------------- UP-MAS-BAND-001
def band_material(t_m, printed_material=None):
    if printed_material:
        return {"status": DC, "material": printed_material}
    if any(abs(t_m - f) < 0.005 for f in BLOCK_FAMILIES_M):
        return {"status": "PROJECT-SPECIFIC", "material": "BLOCK (owner Q-60 type fallback)"}
    return {"status": HELD, "material": None, "reason": f"NO_BLOCK_FAMILY_{t_m:.2f}: material printed nowhere"}


# ------------------------------------------------------------------------------------------- UP-OPEN-ARCH-001
def polygon_area(pts):
    """Shoelace area of a closed outline (list of (x, y), any orientation)."""
    n = len(pts)
    return abs(sum(pts[i][0] * pts[i - 1][1] - pts[i - 1][0] * pts[i][1] for i in range(n))) / 2.0


def arched_opening(width_m, spring_m, arch_profile, band_m=None, tol=0.002):
    """An arched opening read on its opening line.

    arch_profile: the drawn arch as points (x, y) in metres, x from the left jamb (0) to the right jamb (width_m), y
    above the opening bottom, from the left springing (0, spring_m) to the right springing (width_m, spring_m); the
    drawn chain (or the arc sampled finely), never only its two ends. band_m: a surround band drawn outside the opening
    (information only: it never enters the outline). Returns the masonry deduction outline and the Q-32 A window area.
    """
    if width_m is None or spring_m is None or not arch_profile:
        return {"status": HELD, "reason": "OPENING_LINE_NOT_READ: width, springing or arch profile missing"}
    if width_m <= 0 or spring_m < 0:
        raise ValueError("width must be > 0 and springing >= 0")
    if len(arch_profile) < 3:
        raise ValueError("ARCH_AS_CHORD: an arch needs its drawn profile, not only the two springing points")
    (x0, y0), (x1, y1) = arch_profile[0], arch_profile[-1]
    if abs(x0) > tol or abs(x1 - width_m) > tol or abs(y0 - spring_m) > tol or abs(y1 - spring_m) > tol:
        raise ValueError("ARCH_NOT_ON_OPENING_LINE: the profile must spring from both jambs at the springing level")
    for x, y in arch_profile:
        if x < -tol or x > width_m + tol or y < spring_m - tol:
            raise ValueError("ARCH_OUTSIDE_JAMBS: a profile point lies outside the opening (surround or moulding line?)")
    outline = [(0.0, 0.0)] + [tuple(p) for p in arch_profile] + [(width_m, 0.0)]
    area = polygon_area(outline)
    crown = max(y for _, y in arch_profile)
    rect = width_m * spring_m
    return {"status": DC, "width_m": _r(width_m), "spring_m": _r(spring_m), "crown_m": _r(crown),
            "jamb_rectangle_m2": _r(rect, 4), "arch_segment_m2": _r(area - rect, 4),
            "masonry_deduction_m2": _r(area, 4), "window_area_q32a_m2": _r(width_m * crown, 4),
            "band_m": band_m, "band_crown_m": None if band_m is None else _r(crown + band_m)}


def check_masonry_deduction(claimed_m2, opening, tol=0.005):
    """Refuse a masonry / plaster / paint deduction for an arched opening that is not its true outline."""
    if opening.get("status") not in ESTABLISHED:
        raise ValueError("OPENING_HELD: no deduction from a held outline (net stays HELD, never 0)")
    w, crown = opening["width_m"], opening["crown_m"]
    if opening.get("band_crown_m") is not None and abs(claimed_m2 - w * opening["band_crown_m"]) <= tol:
        raise ValueError("BAND_CROWN_AS_HEAD: the surround band crown was taken as the opening head")
    if abs(claimed_m2 - w * crown) <= tol and abs(w * crown - opening["masonry_deduction_m2"]) > tol:
        raise ValueError("RECTANGLE_FOR_MASONRY: width x crown is the Q-32 A window area, not the masonry opening")
    if abs(claimed_m2 - opening["masonry_deduction_m2"]) > tol:
        raise ValueError("NOT_THE_OUTLINE: the deduction differs from the opening outline "
                         f"{opening['masonry_deduction_m2']:.4f} m2")
    return True


def measured_arched_opening(width_m, spring_m, crown_m, arch_segment_m2, band_m=None, status=DC):
    """The same record from a measurement made off the drawing (profile area already integrated by the reader); the
    repository keeps the measured values, never the drawing's coordinates."""
    if None in (width_m, spring_m, crown_m, arch_segment_m2):
        return {"status": HELD, "reason": "OPENING_LINE_NOT_READ"}
    rise = crown_m - spring_m
    if rise < 0 or arch_segment_m2 < 0 or arch_segment_m2 > width_m * rise + 1e-6:
        raise ValueError("ARCH_SEGMENT_IMPOSSIBLE: the segment must lie inside width x rise")
    rect = width_m * spring_m
    return {"status": status, "width_m": _r(width_m), "spring_m": _r(spring_m), "crown_m": _r(crown_m),
            "jamb_rectangle_m2": _r(rect, 4), "arch_segment_m2": _r(arch_segment_m2, 4),
            "masonry_deduction_m2": _r(rect + arch_segment_m2, 4), "window_area_q32a_m2": _r(width_m * crown_m, 4),
            "band_m": band_m, "band_crown_m": None if band_m is None else _r(crown_m + band_m)}

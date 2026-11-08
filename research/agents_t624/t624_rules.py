"""R-T624-1 (PROPOSED, research, unwired; lane S): closing beam-band pieces that R-T614-1 left open, every villa.

Physical element: a part of a drawn beam band next to a column or another beam (union of drawn outlines), owned
once (UP-CONC-JOINT-001 1.0.0; R-T600-1 node once; R-T610-1 deeper member at a crossing; R-T614-1 (g) billing only
inside a line's own measured extent or a named add).

(a) A NAMED ADD IS PLACED BY ITS OWN CONSTRUCTION. A T-229 add (END_SHORT_*, CUT_AT_*, the run value that replaces a
    T-110 value) is the volume of a region T-229 built from the drawing (the strip of the band beyond the billed face,
    bounded by the members the beam frames into; the gap between two pieces of one band). The region is rebuilt from
    the drawing and the piece is BILLED_BY_ADD when (i) the piece lies inside it within ADD_TOL_M3 of volume and (ii)
    the region's area x depth equals the printed add within ADD_TOL_M3 (or ADD_TOL_REL). Matching the add VALUE by a
    subset of drawn parts (R-T614-1 (g)(iii)) is not placement: it is used only when no construction is recorded.
(b) A RUN VALUE IS DECOMPOSED, NEVER TREATED AS ONE ADD. 'T-229 run X replaces T-110 Y +Z' places nothing by Z:
    the run value equals the sum of its pieces' rectangles and its named gap / end terms; a piece inside none of them
    is not billed by the run.
(c) THE DRAWN END OF A BAND IS EACH FACE'S OWN END. Where one face of a band stops early (a crossing beam's face
    takes over) and the other runs on to a column, the band reaches the column face: the region between the hull end
    (the shorter face's station) and the column face, inside the band width, outside every other drawn band, whose
    boundary is drawn all round (band face, other beam's face, column outline) except the side it shares with the
    band, is MEASURED and belongs to that band's line (R-T614-1 (b): up to the next drawn member face). A side that
    is not drawn keeps it HELD (R-T614-1 (f) unchanged).
(d) A WEDGE IS NOT A FIT RESIDUAL WHEN THE DRAWN FACES REACH THE COLUMN. A skewed band meeting an orthogonal column
    leaves a wedge between the rectangle's square end and the column face. When both drawn faces end on the column
    outline (within END_TOL_M) the wedge is drawn concrete of the beam whatever its area (T-229 SQUARE_MAX 0.002 m2
    is a fit tolerance for fitted quads, not a measure of the drawing).
(e) A JUNCTION PIECE DEDUCTED FROM ONE BAND IS BILLED ONCE BY THE OTHER when it lies inside the other band's
    rectangle and that line's value carries the whole rectangle; the companion range of a crossing fix row then
    closes to its low end (no point collapsed without this proof).
(f) ADVERSE: billing is never proved by a match whose tolerance is larger than the piece itself.
"""
from __future__ import annotations

import math

from shapely.geometry import LineString, Polygon  # noqa: F401
from shapely.ops import unary_union

RULE_ID = "R-T624-1"
EPS_M2 = 1e-6
ADD_TOL_M3 = 0.001          # the R-T614-1 (g) named-add tolerance (1 dm3) ...
ADD_TOL_REL = 0.01          # ... or 1 % of the add
END_TOL_M = 0.02            # a face end within 20 mm of a column outline ends on that column (R-T614-1)
LINE_BUF_M = 0.002          # a boundary edge within 2 mm of a drawn line is drawn
DRAWN_COVER_MIN = 0.99      # share of the non-shared boundary that must be drawn (c)
SQUARE_MAX_M2 = 0.002       # T-229 beam_support.SQUARE_MAX (read only; quoted to show where (d) overrides it)


class Refused(ValueError):
    """An input that would make the closure wrong."""


def tol_m3(add_m3):
    return max(ADD_TOL_M3, ADD_TOL_REL * abs(add_m3))


def place_in_add(piece, add_region, add_m3, depth_m, owned_drawn_m2=None):
    """(a) Is the piece billed by a named add whose region is rebuilt from the drawing?
    piece / add_region: plans (m2); add_m3: printed add; depth_m: the line's depth; owned_drawn_m2: the drawn area the
    region should hold (the region's drawn content); when given, the region area must agree with it as well."""
    if depth_m is None:
        raise Refused("a named add cannot be placed without the line's depth")
    if add_region is None or add_region.is_empty:
        return {"verdict": "NO_REGION", "in_add_m2": 0.0, "outside_m2": piece.area}
    inside = piece.intersection(add_region).area
    outside = piece.area - inside
    region_m3 = add_region.area * depth_m
    rec = {"in_add_m2": inside, "outside_m2": outside, "region_m2": add_region.area, "region_m3": region_m3,
           "region_vs_add_m3": region_m3 - add_m3, "tol_m3": tol_m3(add_m3)}
    if owned_drawn_m2 is not None:
        rec["region_vs_drawn_m3"] = (add_region.area - owned_drawn_m2) * depth_m
    ok_region = abs(region_m3 - add_m3) <= tol_m3(add_m3)
    ok_piece = outside * depth_m <= ADD_TOL_M3
    if ok_region and ok_piece:
        refuse_tolerance_larger_than_piece(piece.area, depth_m, outside * depth_m)
        rec["verdict"] = "BILLED_BY_ADD"
    elif ok_region:
        rec["verdict"] = "PARTLY_IN_ADD"
    else:
        rec["verdict"] = "ADD_REGION_DISAGREES"
    return rec


def refuse_tolerance_larger_than_piece(piece_m2, depth_m, residual_m3):
    """(f) A piece 'billed' only because its unplaced residual is inside a tolerance larger than the piece is not
    billed: the residual must be a small part of the piece, never the piece itself."""
    if piece_m2 * depth_m <= ADD_TOL_M3 and residual_m3 > 0.5 * piece_m2 * depth_m:
        raise Refused(f"piece {piece_m2 * depth_m:.6f} m3 is smaller than the tolerance; its unplaced part "
                      f"{residual_m3:.6f} m3 cannot be absorbed by a {ADD_TOL_M3} m3 tolerance")
    return True


def decompose_run(run_m3, terms):
    """(b) A run value is the sum of named terms {name: m3}; returns the residual (must be within 1e-4 m3)."""
    res = run_m3 - sum(terms.values())
    if abs(res) > 1e-4:
        raise Refused(f"run {run_m3} does not decompose into its named terms (residual {res:+.6f} m3)")
    return res


def drawn_cover(region, drawn_lines, shared=None, buf=LINE_BUF_M):
    """(c) Share of the region's boundary (minus the part shared with the band, 'shared') lying on drawn lines."""
    b = region.boundary
    if shared is not None and not shared.is_empty:
        b = b.difference(shared.buffer(buf))
    if b.length <= 0:
        return 1.0
    lines = unary_union([ln.buffer(buf) for ln in drawn_lines])
    return b.intersection(lines).length / b.length


def end_gap_region(band_strip, other_bands, columns):
    """(c) the band-width strip between the hull end and the column face, net of every other drawn band and column."""
    return band_strip.difference(unary_union(list(other_bands) + list(columns)))


def classify_end_gap(region, cover, depth_m):
    if region.area <= EPS_M2:
        return {"state": "NONE", "m2": region.area, "m3": 0.0}
    if cover < DRAWN_COVER_MIN:
        return {"state": "HELD", "m2": region.area, "m3": None, "bound_m3": region.area * depth_m if depth_m else None,
                "reason": f"boundary drawn {cover:.3f} < {DRAWN_COVER_MIN}: the band does not reach the column"}
    if depth_m is None:
        return {"state": "HELD", "m2": region.area, "m3": None, "reason": "depth unknown"}
    return {"state": "MEASURED", "m2": region.area, "m3": region.area * depth_m}


def faces_reach_column(face_end_points, column, tol=END_TOL_M):
    """(d) True when every drawn face end of the band at this end lies on the column outline (within tol)."""
    return all(column.exterior.distance(_pt(p)) <= tol for p in face_end_points)


def _pt(p):
    from shapely.geometry import Point
    return Point(p)


def classify_wedge(wedge_m2, faces_reach, depth_m):
    """(d) the unbilled wedge at a skewed band end."""
    if wedge_m2 <= EPS_M2:
        return {"class": "NONE", "m3": 0.0}
    if faces_reach:
        if depth_m is None:
            return {"class": "DRAWN_WEDGE_HELD", "m3": None}
        return {"class": "DRAWN_WEDGE", "m3": wedge_m2 * depth_m,
                "t229_would_call_square": wedge_m2 <= SQUARE_MAX_M2}
    return {"class": "FIT_RESIDUAL" if wedge_m2 <= SQUARE_MAX_M2 else "UNEXPLAINED", "m3": None}


def junction_tip(tip, owner_rect, owner_value_m3, owner_rect_terms_m3, other_billed, depth_owner):
    """(e) tip: the part of a crossing zone inside the owner's rectangle; owner_value_m3: its line value;
    owner_rect_terms_m3: the line value's terms that are its rectangle(s) x depth (must hold the whole rectangle);
    other_billed: the other band's billed plan (junction deduction applied)."""
    if tip.area <= EPS_M2:
        return {"state": "NONE"}
    in_owner = tip.intersection(owner_rect).area
    in_other = tip.intersection(other_billed).area
    full_rect = abs(owner_rect_terms_m3 - owner_rect.area * depth_owner) <= 1e-4
    rec = {"tip_m2": tip.area, "in_owner_rect_m2": in_owner, "in_other_billed_m2": in_other,
           "owner_rect_billed_whole": full_rect}
    if in_owner >= tip.area - EPS_M2 and in_other <= EPS_M2 and full_rect:
        rec.update(state="BILLED_ONCE_BY_OWNER", companion_m3=0.0)
    elif in_other > EPS_M2 and in_owner > EPS_M2 and full_rect:
        rec.update(state="DOUBLE", companion_m3=-min(in_owner, in_other) * depth_owner)
    else:
        rec.update(state="UNRESOLVED", companion_m3=None)
    return rec


def unit(u):
    n = math.hypot(*u)
    return (u[0] / n, u[1] / n)

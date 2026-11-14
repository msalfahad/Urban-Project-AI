"""T-786 rule UNMARKED_PIECE_DEPTH_V1 (proposed; company default ladder owner 2026-11-13 + owner Q-61 (5); any villa).

Physical element first. A concrete piece drawn on a slab plan with no mark of its own is one of two things:

  (a) a BEAM piece (a downstand in the beam line: a span past a column, a projecting beam end, a ring piece): its depth
      follows the company ladder  printed mark / section  >  same mark  >  adjacent span on the same line  >  0.60;
  (b) a ROOF-EDGE PROJECTION BAND (البروز): a band drawn OUTSIDE the outer face of an edge beam, along the roof edge,
      usually with rounded corners following the architectural facade line. It is not in any beam line.

Evidence that decides (b): a printed section that CUTS the band and draws only the edge beam (and its upstand) with no
concrete in the band (owner Q-61 (5): 'exclude only if the sections conclusively show no concrete beam'). A band of the
SAME drawn type elsewhere on the same set (outside an edge beam, roof edge, no mark) takes the same reading by element
type. The beam depth ladder does not apply to (b): it is the roof slab carried out to the facade line, cast with the slab,
so its depth = the PRINTED slab thickness (DEFAULT label: the band's own section is not printed; the designer item
replaces it). No printed slab thickness -> HELD with the range (0 .. the beam default), never 0 and never a borrowed
value.

    beam piece          m3 = plan area x ladder depth
    projection band     m3 = plan area x printed slab thickness

Refusals: mm read as m (a depth or a thickness above 3.0 m), negative / NaN, a 'band' that is not outside an edge beam
(it stays a beam piece), a section that does not cut the band (no evidence, the ladder stays).
"""
from __future__ import annotations

import math

BEAM_DEFAULT_DEPTH_M = 0.60      # company default (owner 2026-11-13): no mark, no adjacent span


class DepthRuleError(ValueError):
    pass


def _pos(name, v, hi=3.0):
    if v is None:
        return None
    if not isinstance(v, (int, float)) or isinstance(v, bool) or math.isnan(v) or v <= 0:
        raise DepthRuleError(f"{name} must be a positive number in metres, got {v!r}")
    if v > hi:
        raise DepthRuleError(f"{name} {v} m is above {hi} m: millimetres read as metres?")
    return float(v)


def beam_piece_depth(printed=None, same_mark=None, adjacent_span=None):
    """Company ladder for an unmarked BEAM piece -> (depth m, label, step)."""
    for step, v in (("printed", printed), ("same_mark", same_mark), ("adjacent_span", adjacent_span)):
        d = _pos(step, v)
        if d is not None:
            return d, ("DRAWING-READ" if step == "printed" else "DEFAULT"), step
    return BEAM_DEFAULT_DEPTH_M, "DEFAULT", "company_default_0.60"


def classify(outside_edge_beam: bool, roof_edge: bool, section_cuts_band: bool | None,
             section_shows_concrete_in_band: bool | None, same_type_as_cut_band: bool = False):
    """-> 'PROJECTION_BAND' or 'BEAM_PIECE'.

    A band is a projection only when it lies outside an edge beam on a roof edge AND either a section cuts it and shows no
    concrete in it, or it is the same drawn type as a band so cut. Anything else stays a beam piece (ladder)."""
    if not (outside_edge_beam and roof_edge):
        return "BEAM_PIECE"
    if section_cuts_band:
        return "BEAM_PIECE" if section_shows_concrete_in_band else "PROJECTION_BAND"
    return "PROJECTION_BAND" if same_type_as_cut_band else "BEAM_PIECE"


def piece_m3(plan_m2, kind, slab_thickness=None, printed=None, same_mark=None, adjacent_span=None):
    """Volume of one unmarked piece. Returns dict(net | low/high, label, depth, step)."""
    a = _pos("plan_m2", plan_m2, hi=1.0e4)
    if a is None:
        raise DepthRuleError("plan area missing: the piece is HELD by the caller, not valued here")
    if kind == "PROJECTION_BAND":
        t = _pos("slab_thickness", slab_thickness)
        if t is None:
            return {"class": "HELD", "net": None, "low": 0.0, "high": round(a * BEAM_DEFAULT_DEPTH_M, 6),
                    "label": None, "depth_m": None, "step": "projection_no_printed_slab_thickness"}
        return {"class": "RELEASED", "net": round(a * t, 6), "label": "DEFAULT", "depth_m": t,
                "step": "projection_printed_slab_thickness"}
    if kind != "BEAM_PIECE":
        raise DepthRuleError(f"unknown kind {kind!r}")
    d, label, step = beam_piece_depth(printed, same_mark, adjacent_span)
    return {"class": "RELEASED", "net": round(a * d, 6), "label": label, "depth_m": d, "step": step}

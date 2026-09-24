"""Which wall does this opening belong to?

The defect this replaces pooled a floor's openings and shared the deduction out across wall-thickness bands in
proportion to wall length.  The floor total survives that; the split between a 150 mm line and a 200 mm line does
not, and those are priced separately.  A door is in one wall.  Either the drawing says which, or nobody does.

So an opening is assigned to a host on spatial evidence, entirely or not at all.  Where two hosts remain
plausible - a junction, a doorway between two thicknesses - the opening is HOST_WALL_UNRESOLVED and the affected
wall split is blocked from pricing.  Nothing is ever apportioned.
"""

from __future__ import annotations

from engine.qs_core import geom
from engine.qs_core.entities import (CONFIDENCE_NONE, CONFIDENCE_PROVEN, CONFIDENCE_STRONG, CONFIDENCE_WEAK,
                                     Evidence, HOST_ASSIGNED, HOST_WALL_UNRESOLVED)

# The margin by which the leading candidate has to beat its rival before the engine calls the question settled.
# It is a property of the evidence, not of any project: two candidates that score within this of each other are
# not distinguishable by the geometry in front of us.
DECISIVE_MARGIN = 0.15


def build_wall_lines(bands, tolerance, max_opening_span):
    """Join collinear segments of equal thickness into the wall they are segments of.

    A wall interrupted by a door arrives from an extractor as two segments.  They are not two walls, and the door
    is in neither of them - it is in the gap.  Grouping by line and thickness puts the hole back in the wall it
    belongs to, which is also how a surveyor measures: the wall gross, less its openings.

    A gap wider than `max_opening_span` is not an opening, so segments either side of it stay separate walls.
    The caller supplies that span because it is a fact about the building, not about the algorithm.
    """
    from engine.qs_core.entities import Evidence, GeometryComponent, KIND_WALL_BAND

    groups = {}
    for b in bands:
        bb = b.bbox
        offset = bb.y0 if b.axis == geom.AXIS_X else bb.x0
        key = (b.floor, b.axis, round(offset / tolerance), round((b.thickness or 0) / tolerance))
        groups.setdefault(key, []).append(b)

    lines = []
    for (floor, axis, _o, _t), members in sorted(groups.items()):
        members.sort(key=lambda m: m.bbox.x0 if axis == geom.AXIS_X else m.bbox.y0)
        runs, current = [], [members[0]]
        for prev, nxt in zip(members, members[1:]):
            pb, nb = prev.bbox, nxt.bbox
            gap = (nb.x0 - pb.x1) if axis == geom.AXIS_X else (nb.y0 - pb.y1)
            if gap <= max_opening_span + tolerance:
                current.append(nxt)
            else:
                runs.append(current)
                current = [nxt]
        runs.append(current)
        for run in runs:
            env = geom.bbox([r for m in run for r in m.rects])
            thickness = run[0].thickness
            ref = (f"WALL-LINE::{floor}::{axis}::{round(env.y0 if axis == geom.AXIS_X else env.x0, 4)}"
                   f"::{round(env.x0 if axis == geom.AXIS_X else env.y0, 4)}::{thickness}")
            line = GeometryComponent(ref, KIND_WALL_BAND, [env], floor, run[0].source_revision,
                                     thickness=thickness, axis=axis, layer=run[0].layer,
                                     material_length=round(sum(m.length for m in run), 9))
            line.evidence.append(Evidence("WALL_LINE_ASSEMBLED_FROM_COLLINEAR_SEGMENTS",
                                          {"SEGMENTS": [m.component_ref for m in run],
                                           "MATERIAL_LENGTH_M": round(sum(m.length for m in run), 6),
                                           "ENVELOPE_LENGTH_M": round(line.length, 6),
                                           "MAX_OPENING_SPAN_M": max_opening_span,
                                           "WHY": "these segments lie on one line at one thickness, separated "
                                                  "only by gaps an opening could explain"}))
            lines.append(line)
    return lines


def _containment(opening, band):
    """How much of the opening lies inside this wall band, as a fraction of the opening."""
    inter = 0.0
    for r in band.rects:
        i = opening.rect.intersection(r)
        if i:
            inter += i.area
    return inter / opening.rect.area if opening.rect.area > 0 else 0.0


def _axis_agreement(opening, band):
    """A door runs along its wall.  A candidate whose axis disagrees is almost never the host."""
    if not opening.axis or not band.axis:
        return 0.5
    return 1.0 if opening.axis == band.axis else 0.0


def _thickness_agreement(opening, band, tol):
    """The opening is drawn as deep as the wall it pierces, when the source draws it that way."""
    depth = min(opening.rect.width, opening.rect.height)
    if band.thickness is None or depth <= 0:
        return 0.5
    return 1.0 if abs(depth - band.thickness) <= tol else max(0.0, 1.0 - abs(depth - band.thickness)
                                                              / max(band.thickness, tol))


def _span_overlap(opening, band):
    """How much of the opening's length is covered by the wall's own run."""
    ob, bb = opening.rect, band.bbox
    if band.axis == geom.AXIS_X:
        lo, hi = max(ob.x0, bb.x0), min(ob.x1, bb.x1)
        span = ob.width
    elif band.axis == geom.AXIS_Y:
        lo, hi = max(ob.y0, bb.y0), min(ob.y1, bb.y1)
        span = ob.height
    else:
        return 0.0
    return max(0.0, hi - lo) / span if span > 0 else 0.0


def _proximity(opening, band, tol):
    cx, cy = opening.rect.centroid
    d = min(geom.distance_point_to_rect(cx, cy, r) for r in band.rects)
    return max(0.0, 1.0 - d / max(tol * 4.0, 1e-9))


def score_host(opening, band, tol):
    """Every piece of evidence, weighted, and kept visible so a reviewer can disagree with the weighting."""
    parts = {
        "CONTAINMENT": _containment(opening, band),
        "AXIS_AGREEMENT": _axis_agreement(opening, band),
        "THICKNESS_AGREEMENT": _thickness_agreement(opening, band, tol),
        "SPAN_OVERLAP": _span_overlap(opening, band),
        "PROXIMITY": _proximity(opening, band, tol),
    }
    weights = {"CONTAINMENT": 0.40, "AXIS_AGREEMENT": 0.20, "THICKNESS_AGREEMENT": 0.20,
               "SPAN_OVERLAP": 0.15, "PROXIMITY": 0.05}
    parts["SCORE"] = sum(parts[k] * w for k, w in weights.items())
    parts["WEIGHTS"] = weights
    return parts


def assign_opening_host(opening, wall_bands, tolerance):
    """Assign the opening to one host wall band, or to none at all.

    Returns the opening, mutated, carrying its candidates, its evidence, its confidence and its status.  There is
    no branch in which a deduction is divided between candidates.
    """
    candidates = []
    for band in wall_bands:
        if band.floor != opening.floor:
            continue
        if not opening.rect.expanded(tolerance * 2).overlaps(band.bbox):
            continue
        s = score_host(opening, band, tolerance)
        if s["CONTAINMENT"] <= 0 and s["PROXIMITY"] <= 0:
            continue
        candidates.append((s, band))
    candidates.sort(key=lambda t: (-t[0]["SCORE"], t[1].component_ref))

    opening.host_candidates = [{"COMPONENT_REF": b.component_ref, "THICKNESS_M": b.thickness,
                                "SCORE": round(s["SCORE"], 6), "EVIDENCE": s} for s, b in candidates]

    if not candidates:
        opening.host_status = HOST_WALL_UNRESOLVED
        opening.host_confidence = CONFIDENCE_NONE
        opening.host_component_ref = None
        opening.host_thickness = None
        opening.host_evidence = [Evidence("NO_HOST_CANDIDATE",
                                          {"WHY": "no wall band on this floor intersects or lies within "
                                                  "tolerance of the opening",
                                           "TOLERANCE_M": tolerance})]
        return opening

    best_s, best_b = candidates[0]
    runner = candidates[1][0]["SCORE"] if len(candidates) > 1 else None
    margin = best_s["SCORE"] - runner if runner is not None else None

    decisive = (runner is None) or (margin >= DECISIVE_MARGIN)
    hosted = best_s["CONTAINMENT"] >= 0.5 and best_s["AXIS_AGREEMENT"] >= 0.5

    if decisive and hosted:
        opening.host_status = HOST_ASSIGNED
        opening.host_component_ref = best_b.component_ref
        opening.host_thickness = best_b.thickness
        opening.host_confidence = (CONFIDENCE_PROVEN if best_s["CONTAINMENT"] >= 0.99
                                   and best_s["THICKNESS_AGREEMENT"] >= 0.99 else CONFIDENCE_STRONG)
        opening.host_evidence = [Evidence("HOST_PROVED_BY_GEOMETRY",
                                          {"BEST": best_s, "RUNNER_UP_SCORE": runner, "MARGIN": margin,
                                           "DECISIVE_MARGIN": DECISIVE_MARGIN})]
        return opening

    opening.host_status = HOST_WALL_UNRESOLVED
    opening.host_component_ref = None
    opening.host_thickness = None
    opening.host_confidence = CONFIDENCE_WEAK if hosted else CONFIDENCE_NONE
    opening.host_evidence = [Evidence(
        "HOST_AMBIGUOUS" if not decisive else "HOST_NOT_CONTAINED",
        {"WHY": ("two or more wall bands are equally plausible hosts; apportioning the deduction between them "
                 "would put material against a wall that does not have this hole in it"
                 if not decisive else
                 "the leading candidate does not contain the opening, or runs across it rather than along it"),
         "BEST": best_s, "RUNNER_UP_SCORE": runner, "MARGIN": margin, "DECISIVE_MARGIN": DECISIVE_MARGIN,
         "CANDIDATES": [c["COMPONENT_REF"] for c in opening.host_candidates]})]
    return opening


def build_opening_register(openings, wall_bands, tolerance):
    """The canonical register: every opening, its host or its lack of one, and the totals that follow."""
    for o in openings:
        assign_opening_host(o, wall_bands, tolerance)
    assigned = [o for o in openings if o.host_status == HOST_ASSIGNED]
    unresolved = [o for o in openings if o.host_status != HOST_ASSIGNED]
    by_band, by_thickness, width_by_band, unmeasured = {}, {}, {}, {}
    for o in assigned:
        width_by_band[o.host_component_ref] = round(width_by_band.get(o.host_component_ref, 0.0)
                                                    + (o.width or 0.0), 9)
        if o.area is None:
            unmeasured.setdefault(o.host_component_ref, []).append(o.opening_ref)
            continue
        by_band[o.host_component_ref] = round(by_band.get(o.host_component_ref, 0.0) + o.area, 9)
        key = None if o.host_thickness is None else round(o.host_thickness, 4)
        by_thickness[key] = round(by_thickness.get(key, 0.0) + o.area, 9)
    measurable = [o for o in openings if o.area is not None]
    return {
        "REGISTER": [o.as_dict() for o in sorted(openings, key=lambda x: x.opening_ref)],
        "OPENING_COUNT": len(openings),
        "MEASURABLE_COUNT": len(measurable),
        "ASSIGNED_COUNT": len(assigned),
        "UNRESOLVED_COUNT": len(unresolved),
        "UNRESOLVED_REFS": sorted(o.opening_ref for o in unresolved),
        "TOTAL_OPENING_AREA_M2": round(sum(o.area for o in measurable), 9),
        "ASSIGNED_AREA_M2": round(sum(o.area for o in assigned if o.area is not None), 9),
        "UNRESOLVED_AREA_M2": round(sum(o.area for o in unresolved if o.area is not None), 9),
        "DEDUCTION_BY_WALL_COMPONENT_M2": dict(sorted(by_band.items())),
        "HOSTED_WIDTH_BY_WALL_COMPONENT_M": dict(sorted(width_by_band.items())),
        "UNMEASURED_OPENINGS_BY_WALL_COMPONENT": {k: sorted(v) for k, v in sorted(unmeasured.items())},
        "DEDUCTION_BY_THICKNESS_M2": {str(k): v for k, v in sorted(by_thickness.items(), key=lambda kv:
                                                                   (kv[0] is None, kv[0]))},
        "ALLOCATION_RULE": "an opening is deducted from exactly one host wall band, or from none; no deduction "
                           "is ever divided between candidates",
        "TOLERANCE_M": tolerance,
    }


def wall_band_quantities(wall_bands, register, height, geometry_includes_openings, blocked_note=None):
    """Net wall area per band: gross less the openings this band hosts, and nothing else.

    `geometry_includes_openings` is a question about the SOURCE, which only the extractor can answer.  Some
    extractors draw a wall straight through its doorway, so the gross already includes the hole; others stop the
    wall at each jamb, so the hole has to be added back before it can be deducted.  Getting this wrong
    double-counts every door, which is why it is an argument with no default.

    The height is an input too: where it comes from is the caller's evidence to carry.
    """
    ded = register["DEDUCTION_BY_WALL_COMPONENT_M2"]
    widths = register["HOSTED_WIDTH_BY_WALL_COMPONENT_M"]
    unmeasured = register["UNMEASURED_OPENINGS_BY_WALL_COMPONENT"]
    unresolved_floors = {o["FLOOR"] for o in register["REGISTER"]
                         if o["HOST_ASSIGNMENT_STATUS"] != HOST_ASSIGNED}
    rows = []
    for b in sorted(wall_bands, key=lambda x: x.component_ref):
        material = b.material_length if b.material_length is not None else b.length
        gross_length = material if geometry_includes_openings else material + widths.get(b.component_ref, 0.0)
        gross = gross_length * height
        d = ded.get(b.component_ref, 0.0)
        mine_unmeasured = unmeasured.get(b.component_ref, [])
        blocked = b.floor in unresolved_floors or bool(mine_unmeasured)
        why = None
        if mine_unmeasured:
            why = ("an opening this band hosts has no established height, so its deduction cannot be "
                   f"computed: {mine_unmeasured}")
        elif blocked:
            why = (blocked_note or "an opening on this floor has no proved host, so the split between "
                                   "thicknesses on this floor is not final")
        rows.append({
            "COMPONENT_REF": b.component_ref, "FLOOR": b.floor, "THICKNESS_M": b.thickness,
            "MATERIAL_LENGTH_M": round(material, 6),
            "HOSTED_OPENING_WIDTH_M": round(widths.get(b.component_ref, 0.0), 6),
            "GROSS_LENGTH_M": round(gross_length, 6), "HEIGHT_M": height,
            "GROSS_AREA_M2": round(gross, 6), "OPENING_DEDUCTION_M2": round(d, 6),
            "NET_AREA_M2": round(gross - d, 6),
            "GROSS_BASIS": ("the wall as drawn, which already spans its openings" if geometry_includes_openings
                            else "the wall material plus the openings it hosts, so the wall over a door is "
                                 "counted before the door is deducted"),
            "DEDUCTION_SOURCE": "the openings whose host is this band, in full",
            "STATUS": ("BLOCKED_BY_UNMEASURED_OPENING" if mine_unmeasured else
                       "BLOCKED_BY_UNRESOLVED_OPENING" if blocked else "FINAL_QUANTITY_AVAILABLE"),
            "BLOCKED_NOTE": why,
        })
    return rows

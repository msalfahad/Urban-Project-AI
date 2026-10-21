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


# How much of a gap an opening has to occupy before it explains the gap.  A 0.9 m door does not explain a 2 m
# hole in a wall; something else is going on there and the engine does not decide what.
GAP_OCCUPANCY = 0.90

GAP_BRIDGED_BY_CONFIRMED_OPENING = "BRIDGED_BY_A_CONFIRMED_OPENING"
GAP_BRIDGED_BY_CONTINUATION_GEOMETRY = "BRIDGED_BY_CONTINUATION_GEOMETRY"
GAP_BRIDGED_BY_DECLARED_CAD_CONTINUITY = "BRIDGED_BY_DECLARED_CAD_CONTINUITY"
GAP_NOT_BRIDGED_NO_EVIDENCE = "NOT_BRIDGED_NO_CONTINUITY_EVIDENCE"
GAP_NOT_BRIDGED_TOO_WIDE = "NOT_BRIDGED_WIDER_THAN_ANY_OPENING_IN_THIS_SOURCE"


def _axis_span(rect, axis):
    return (rect.x0, rect.x1) if axis == geom.AXIS_X else (rect.y0, rect.y1)


def _cross_span(rect, axis):
    return (rect.y0, rect.y1) if axis == geom.AXIS_X else (rect.x0, rect.x1)


def _covered(lo, hi, spans):
    """How much of [lo, hi] the given intervals cover, as a fraction."""
    if hi <= lo:
        return 0.0
    merged = []
    for a, b in sorted((max(lo, a), min(hi, b)) for a, b in spans):
        if b <= a:
            continue
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return sum(b - a for a, b in merged) / (hi - lo)


def _bridging_pairs(openings):
    """Openings whose resolved host is a pair of bracketing wall ends: each one closes exactly that gap.

    This is the inversion the review asked for.  A confirmed opening is itself the evidence that two collinear
    segments are one interrupted wall - it does not have to overlap both of them first to prove it.
    """
    out = {}
    for o in openings or ():
        rec = getattr(getattr(o, "candidate", None), "host_record", None) or {}
        if rec.get("HOST_STATUS") != "HOST_CONFIRMED":
            continue
        # the host resolver reports which two segments face each other across the gap.  Falling back to the
        # whole host set only works where the host was a single pair; a run chopped into five pieces has the
        # same physical meaning and must bridge the same gap, which is why the pair is carried explicitly.
        pair = rec.get("HOST_BRACKETING_SEGMENT_REFS")
        if not pair:
            refs = rec.get("HOST_SEGMENT_REFS") or []
            pair = refs if len(refs) == 2 else None
        if pair:
            out[frozenset(pair)] = getattr(o, "opening_ref", None) or rec.get("CANDIDATE_REF")
    return out


def _gap_evidence(axis, lo, hi, offset_lo, offset_hi, floor, prev_ref, next_ref,
                  max_opening_span, tolerance, openings, continuation_geometry, cad_continuity,
                  bridging_pairs=None):
    """Is there evidence that wall material continues across this gap, or only that it could?

    A maximum opening span can REJECT a join - a 4 m hole is not a door - but it cannot prove one.  Two unrelated
    walls that happen to lie on one line, 2 m apart, are two walls; joining them invents a wall, and every
    quantity on that invented wall is wrong in a way no total will reveal.
    """
    width = hi - lo
    if width > max_opening_span + tolerance:
        return {"BRIDGED": False, "RELATION": GAP_NOT_BRIDGED_TOO_WIDE, "GAP_M": round(width, 6),
                "MAX_OPENING_SPAN_M": max_opening_span,
                "WHY": "no opening in this source is this wide, so the gap is not an opening"}
    pair = frozenset((prev_ref, next_ref))
    bridged_by = (bridging_pairs or {}).get(pair)
    if bridged_by:
        return {"BRIDGED": True, "RELATION": GAP_BRIDGED_BY_CONFIRMED_OPENING, "GAP_M": round(width, 6),
                "OPENINGS": [bridged_by], "OCCUPANCY": None,
                "WHY": "a confirmed opening was resolved to these two wall ends, so the wall runs through the "
                       "gap and the opening is deducted from it; the opening is the evidence for the join, "
                       "not the other way round"}
    for rec in cad_continuity or ():
        if frozenset(rec.get("SEGMENTS", ())) >= pair:
            return {"BRIDGED": True, "RELATION": GAP_BRIDGED_BY_DECLARED_CAD_CONTINUITY,
                    "GAP_M": round(width, 6), "REFERENCE": rec.get("REFERENCE"),
                    "WHY": "the source states that these segments are one object"}
    spans = []
    for o in openings or ():
        if getattr(o, "floor", None) != floor or getattr(o, "rect", None) is None:
            continue          # no footprint yet: its host is unresolved, so it proves no continuity
        r = o.rect
        c0, c1 = _cross_span(r, axis)
        if min(c1, offset_hi) - max(c0, offset_lo) <= -tolerance:
            continue
        spans.append((_axis_span(r, axis), o.opening_ref))
    share = _covered(lo, hi, [s for s, _ref in spans])
    if share >= GAP_OCCUPANCY:
        return {"BRIDGED": True, "RELATION": GAP_BRIDGED_BY_CONFIRMED_OPENING, "GAP_M": round(width, 6),
                "OPENINGS": sorted(ref for _s, ref in spans), "OCCUPANCY": round(share, 6),
                "WHY": "a confirmed opening occupies the gap, so the wall runs through it and the opening is "
                       "deducted from it"}
    cont = [_axis_span(r, axis) for r in (continuation_geometry or ())
            if min(_cross_span(r, axis)[1], offset_hi) - max(_cross_span(r, axis)[0], offset_lo) > -tolerance]
    cshare = _covered(lo, hi, cont)
    if cshare >= GAP_OCCUPANCY:
        return {"BRIDGED": True, "RELATION": GAP_BRIDGED_BY_CONTINUATION_GEOMETRY, "GAP_M": round(width, 6),
                "OCCUPANCY": round(cshare, 6),
                "WHY": "geometry that continues the wall across the gap is drawn here, for example a lintel or "
                       "a header over an opening"}
    return {"BRIDGED": False, "RELATION": GAP_NOT_BRIDGED_NO_EVIDENCE, "GAP_M": round(width, 6),
            "OPENING_OCCUPANCY": round(share, 6), "CONTINUATION_OCCUPANCY": round(cshare, 6),
            "REQUIRED_OCCUPANCY": GAP_OCCUPANCY,
            "WHY": "the gap is narrow enough that an opening could explain it, and nothing in the source says "
                   "one does; a maximum span can reject a join but cannot prove one"}


def build_wall_lines(bands, tolerance, max_opening_span, openings=(), continuation_geometry=(),
                     cad_continuity=()):
    """Join collinear segments of equal thickness into the wall they are segments of - where the source says so.

    A wall interrupted by a door arrives from an extractor as two segments.  They are not two walls, and the door
    is in neither of them - it is in the gap.  Putting the hole back in the wall it belongs to is how a surveyor
    measures: the wall gross, less its openings.

    But a gap is only closed on EVIDENCE that something spans it: a confirmed opening filling it, geometry drawn
    across it, or the source declaring the segments one object.  `max_opening_span` is a veto, not a proof.
    """
    from engine.qs_core.entities import Evidence, GeometryComponent, KIND_WALL_BAND

    groups = {}
    for b in bands:
        bb = b.bbox
        offset = bb.y0 if b.axis == geom.AXIS_X else bb.x0
        key = (b.floor, b.axis, round(offset / tolerance), round((b.thickness or 0) / tolerance))
        groups.setdefault(key, []).append(b)

    bridging = _bridging_pairs(openings)
    lines, gap_log = [], []
    for (floor, axis, _o, _t), members in sorted(groups.items()):
        members.sort(key=lambda m: m.bbox.x0 if axis == geom.AXIS_X else m.bbox.y0)
        runs, current, bridges = [], [members[0]], [[]]
        for prev, nxt in zip(members, members[1:]):
            pb, nb = prev.bbox, nxt.bbox
            lo, hi = ((pb.x1, nb.x0) if axis == geom.AXIS_X else (pb.y1, nb.y0))
            off_lo, off_hi = _cross_span(pb, axis)
            ev = _gap_evidence(axis, lo, hi, off_lo, off_hi, floor, prev.component_ref, nxt.component_ref,
                               max_opening_span, tolerance, openings, continuation_geometry, cad_continuity,
                               bridging_pairs=bridging)
            ev.update({"FLOOR": floor, "AXIS": axis, "FROM_SEGMENT": prev.component_ref,
                       "TO_SEGMENT": nxt.component_ref, "FROM_M": round(lo, 6), "TO_M": round(hi, 6),
                       "THICKNESS_M": prev.thickness})
            gap_log.append(ev)
            if hi - lo <= tolerance or ev["BRIDGED"]:
                current.append(nxt)
                bridges[-1].append(ev)
            else:
                runs.append(current)
                current, bridges = [nxt], bridges + [[]]
        runs.append(current)
        for run, bridged in zip(runs, bridges):
            rects = [r for m in run for r in m.rects]
            env = geom.bbox(rects)
            thickness = run[0].thickness
            # the run that actually has material in it, as the UNION of the segments' spans.  Summing their
            # lengths would count a wall drawn twice on two layers twice, which is a quantity error that no
            # later check can see, because the doubled length is perfectly self-consistent.
            spans = [_axis_span(r, axis) for r in rects]
            material_length = _covered(min(a for a, _b in spans), max(b for _a, b in spans), spans) * \
                (max(b for _a, b in spans) - min(a for a, _b in spans))
            overlapped = round(sum(b - a for a, b in spans) - material_length, 9)
            ref = (f"WALL-LINE::{floor}::{axis}::{round(env.y0 if axis == geom.AXIS_X else env.x0, 4)}"
                   f"::{round(env.x0 if axis == geom.AXIS_X else env.y0, 4)}::{thickness}")
            line = GeometryComponent(ref, KIND_WALL_BAND, [env], floor, run[0].source_revision,
                                     thickness=thickness, axis=axis, layer=run[0].layer,
                                     material_length=round(material_length, 9),
                                     material_rects=list(rects))
            line.evidence.append(Evidence("WALL_LINE_ASSEMBLED_FROM_COLLINEAR_SEGMENTS",
                                          {"SEGMENTS": [m.component_ref for m in run],
                                           "MATERIAL_LENGTH_M": round(material_length, 6),
                                           "SEGMENT_LENGTH_SUM_M": round(sum(m.length for m in run), 6),
                                           "OVERLAPPING_SEGMENT_LENGTH_M": overlapped,
                                           "ENVELOPE_LENGTH_M": round(line.length, 6),
                                           "MAX_OPENING_SPAN_M": max_opening_span,
                                           "GAPS_CLOSED": bridged,
                                           "WHY": "these segments lie on one line at one thickness, and every "
                                                  "gap between them is closed by evidence that material or an "
                                                  "opening continues across it"}))
            lines.append(line)
    lines.sort(key=lambda c: c.component_ref)
    return lines, gap_log


# ---------------------------------------------------------------- does this wall's material span its openings?
MATERIAL_SPANS = "MATERIAL_SPANS_ITS_OPENINGS"
MATERIAL_STOPS = "MATERIAL_STOPS_AT_THE_JAMBS"
BASIS_NOT_TESTABLE = "NO_OPENING_ON_THIS_LINE_TO_TEST"
BASIS_UNRESOLVED = "OPENING_BASIS_UNRESOLVED"
SPANS_SHARE = 0.90
STOPS_SHARE = 0.10


def evaluate_opening_basis(wall_lines, openings, tolerance):
    """Per wall line, on evidence: does the drawn material run through its openings, or stop at the jambs?

    One Boolean for a whole drawing revision is a guess about a mixed population.  Extractors, and draughtsmen,
    are not consistent within one file: a facade drawn as one polyline spans its windows while an internal
    partition drawn segment by segment stops at every door.  Asserting one answer for both double-counts every
    opening in one of them.  So the question is asked of each line, against the openings that actually lie in it.
    """
    out = {}
    for line in wall_lines:
        material = line.material_rects or line.rects
        tested = []
        for o in openings:
            # an opening whose host is unresolved has no footprint yet, so there is nothing to test it with;
            # its line is blocked by the host question, not by a basis it cannot have
            if o.rect is None or o.floor != line.floor or \
                    not o.rect.expanded(tolerance).overlaps(line.bbox):
                continue
            inter = sum(i.area for i in (o.rect.intersection(r) for r in material) if i)
            share = inter / o.rect.area if o.rect.area > 0 else 0.0
            tested.append({"OPENING_REF": o.opening_ref, "MATERIAL_SHARE_OF_THE_OPENING": round(share, 6),
                           "READS_AS": (MATERIAL_SPANS if share >= SPANS_SHARE else
                                        MATERIAL_STOPS if share <= STOPS_SHARE else BASIS_UNRESOLVED)})
        readings = {t["READS_AS"] for t in tested}
        if not tested:
            basis, conf, status = BASIS_NOT_TESTABLE, CONFIDENCE_NONE, BASIS_NOT_TESTABLE
            why = ("no opening lies in this wall line, so there is nothing to deduct and the basis makes no "
                   "difference to its quantity")
        elif readings == {MATERIAL_SPANS}:
            basis, conf, status = MATERIAL_SPANS, CONFIDENCE_PROVEN, MATERIAL_SPANS
            why = ("the drawn material covers the footprint of every opening in this line, so the gross length "
                   "already includes them and they are deducted once")
        elif readings == {MATERIAL_STOPS}:
            basis, conf, status = MATERIAL_STOPS, CONFIDENCE_PROVEN, MATERIAL_STOPS
            why = ("the drawn material stops at the jambs of every opening in this line, so the wall over each "
                   "opening has to be added back before the opening is deducted")
        else:
            basis, conf, status = BASIS_UNRESOLVED, CONFIDENCE_NONE, BASIS_UNRESOLVED
            why = ("the openings in this line do not agree: some are covered by material and some are not, so "
                   "the engine cannot state one gross basis for the line")
        out[line.component_ref] = {
            "COMPONENT_REF": line.component_ref, "FLOOR": line.floor, "THICKNESS_M": line.thickness,
            "BASIS": basis, "STATUS": status, "CONFIDENCE": conf,
            "MATERIAL_SPANS_THE_OPENING": basis == MATERIAL_SPANS,
            "MATERIAL_STOPS_AT_THE_JAMBS": basis == MATERIAL_STOPS,
            "OPENINGS_TESTED": sorted(tested, key=lambda t: t["OPENING_REF"]),
            "DETECTED_BY": "the drawn material of this line intersected with the footprint of each opening "
                           f"that lies in it; >= {SPANS_SHARE} covered reads as spanning, <= {STOPS_SHARE} as "
                           "stopping at the jambs, anything between as unresolved",
            "WHY": why}
    return out


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
    if opening.rect is None:
        opening.host_status = HOST_WALL_UNRESOLVED
        opening.host_confidence = CONFIDENCE_NONE
        opening.host_candidates = []
        opening.host_evidence = [Evidence("NO_FOOTPRINT_TO_SCORE", {
            "WHY": "this opening has no resolved depth, so it has no rectangle; its host is decided by "
                   "qs_core.hosting from the material around it, not by scoring overlaps"})]
        return opening
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


def assign_host_lines(openings, wall_lines):
    """Map each opening's resolved host SEGMENTS onto the wall LINE they belong to.

    This is part of an opening's final state, not of the register that reports it: the deduction, the
    dependency graph and the questions all need to know which line an opening is deducted from, and they must
    all be told the same thing.  It is deterministic and idempotent, so running it before the evidence barrier
    and again inside the register cannot produce two answers.
    """
    from engine.qs_core.entities import HOST_ASSIGNED, HOST_WALL_UNRESOLVED

    by_segment = {}
    for ln in wall_lines:
        for e in ln.evidence:
            for seg in e.detail.get("SEGMENTS", []) or []:
                by_segment[seg] = ln
    for o in openings:
        rec = getattr(getattr(o, "candidate", None), "host_record", None) or {}
        refs = rec.get("HOST_SEGMENT_REFS") or []
        host_lines = {by_segment[r].component_ref for r in refs if r in by_segment}
        candidates = []
        for c in rec.get("CANDIDATES", []):
            wall_lines = sorted({by_segment[r].component_ref for r in c["COMPONENT_REFS"]
                                 if r in by_segment})
            candidates.append({"COMPONENT_REF": wall_lines[0] if len(wall_lines) == 1 else None,
                               "WALL_LINES": wall_lines, "SEGMENT_REFS": c["COMPONENT_REFS"],
                               "SCORE": c["SCORE"], "RELATION": c["RELATION"], "EVIDENCE": c["EVIDENCE"]})
        o.host_candidates = candidates
        if rec.get("HOST_STATUS") == "HOST_CONFIRMED" and len(host_lines) == 1:
            o.host_status = HOST_ASSIGNED
            o.host_component_ref = sorted(host_lines)[0]
            o.host_thickness = rec.get("HOST_THICKNESS_M")
            o.host_confidence = rec.get("CONFIDENCE")
            o.host_evidence = [Evidence("HOST_PROVED_BY_THE_MATERIAL_AROUND_THE_OPENING", dict(rec))]
        else:
            o.host_status = HOST_WALL_UNRESOLVED
            o.host_component_ref = None
            o.host_thickness = None
            o.host_confidence = rec.get("CONFIDENCE", CONFIDENCE_NONE)
            o.host_evidence = [Evidence("HOST_NOT_RESOLVED", dict(
                rec, WALL_LINES_THE_SEGMENTS_BELONG_TO=sorted(host_lines),
                NOTE="the opening exists; what is unresolved is which wall it is deducted from"))]
    return openings


def register_from_hosts(openings, wall_lines, tolerance):
    """The canonical register: every physical opening, the wall line it is deducted from, and that deduction.

    It reports the opening's final state and adds nothing to it.  Openings whose host is unresolved keep their
    place and carry no deduction.
    """
    assign_host_lines(openings, wall_lines)
    return _summarise(openings, tolerance)


def build_opening_register(openings, wall_bands, tolerance):
    """Score-based host assignment, kept for callers that have no segment-level host resolution."""
    for o in openings:
        assign_opening_host(o, wall_bands, tolerance)
    return _summarise(openings, tolerance)


def _summarise(openings, tolerance):
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


def wall_band_quantities(wall_lines, register, height_record, basis_by_ref, blocked_by_ref,
                         identity_by_ref=None):
    """Net wall area per line: gross on that line's own evidenced basis, less the openings it hosts.

    Three things had to be true before this function could compute anything, and each of them is now an
    evidenced record rather than an assumption: the line's identity (is it masonry at all), its opening basis
    (does its drawn material run through its openings), and the height (from the evidence hierarchy).  Where any
    of them is open, or the dependency graph says this line's value could move, the row carries no quantity -
    only a diagnostic value under a name that cannot be summed by accident.
    """
    from engine.qs_core import evidence as EV, quantities as QY

    ded = register["DEDUCTION_BY_WALL_COMPONENT_M2"]
    widths = register["HOSTED_WIDTH_BY_WALL_COMPONENT_M"]
    height_ok = EV.established(height_record)
    height = height_record.get("VALUE") if height_record else None
    identity_by_ref = identity_by_ref or {}
    rows = []
    for b in sorted(wall_lines, key=lambda x: x.component_ref):
        basis = basis_by_ref.get(b.component_ref, {"BASIS": BASIS_NOT_TESTABLE})
        material = b.material_length if b.material_length is not None else b.length
        hosted_width = widths.get(b.component_ref, 0.0)
        d = ded.get(b.component_ref, 0.0)
        ident = identity_by_ref.get(b.component_ref, {})

        if basis["BASIS"] == MATERIAL_SPANS:
            gross_length, gross_why = material, ("the drawn material of this line runs through its openings, "
                                                 "so its length already includes them")
        elif basis["BASIS"] == MATERIAL_STOPS:
            gross_length, gross_why = material + hosted_width, ("the drawn material stops at each jamb, so the "
                                                                "wall over each opening is added back before "
                                                                "the opening is deducted")
        elif basis["BASIS"] == BASIS_NOT_TESTABLE:
            gross_length, gross_why = material, ("no opening lies in this line, so both bases give the same "
                                                 "length and the question does not arise")
        else:
            gross_length, gross_why = None, ("the openings in this line disagree about the basis, so its gross "
                                             "length is not established")

        h = height if height_ok else None
        computable = gross_length is not None and h is not None
        net = round(gross_length * h - d, 6) if computable else None
        from engine.qs_core import masonry as _MA

        reasons = list((blocked_by_ref.get(b.component_ref) or {}).get("REASONS", []))
        billable = ident.get("BILLABLE_AS_MASONRY")
        geometry = ident.get("GEOMETRY_IDENTITY")
        material_identity = ident.get("MATERIAL_IDENTITY")
        # A band the drawing settles is NOT a wall is a settled exclusion, not an open question: blocking a
        # subtotal because a column shares a thickness family withholds finished work for an answered reason.
        excluded = geometry == _MA.NON_WALL_ARTEFACT
        # A wall whose material nobody states is the opposite case: measurable, unbilled, and a question.  The
        # reasons come from the same function the dependency graph blocks on, so the row status and the graph
        # cannot disagree about how much of this floor is held up.
        for r in _MA.identity_blocks(ident):
            if r not in reasons:
                reasons.append(r)
        final = computable and not reasons and not excluded and billable is not False
        row = {
            "COMPONENT_REF": b.component_ref, "FLOOR": b.floor, "THICKNESS_M": b.thickness,
            "THICKNESS_FAMILY_M": ident.get("THICKNESS_FAMILY_M"),
            "WALL_GEOMETRY_IDENTITY": ident.get("GEOMETRY_IDENTITY"),
            "WALL_MATERIAL_IDENTITY": ident.get("MATERIAL_IDENTITY"),
            "MATERIAL_EVIDENCE": ident.get("MATERIAL_EVIDENCE"),
            "BILLABLE_AS_MASONRY": billable,
            "MATERIAL_LENGTH_M": round(material, 6),
            "HOSTED_OPENING_WIDTH_M": round(hosted_width, 6),
            "OPENING_BASIS": basis["BASIS"], "OPENING_BASIS_EVIDENCE": basis,
            "GROSS_LENGTH_M": None if gross_length is None else round(gross_length, 6),
            "GROSS_BASIS": gross_why,
            "HEIGHT_M": h, "HEIGHT_EVIDENCE": height_record,
            "GROSS_AREA_M2": round(gross_length * h, 6) if computable else None,
            "OPENING_DEDUCTION_M2": round(d, 6),
            "DEDUCTION_SOURCE": "the openings whose host is this line, in full",
            "NET_AREA_M2": net if final else None,
            "STATUS": (QY.FINAL if final else
                       "EXCLUDED_NOT_MASONRY" if excluded else "BLOCKED_PENDING_ANSWERS"),
            "EXCLUDED_BECAUSE": ident.get("WHY_GEOMETRY") if excluded else None,
            "EXCLUDED_REASON_KIND": ident.get("GEOMETRY_ARTEFACT_REASON") if excluded else None,
            "BLOCKED_BY": reasons or ([] if final else [
                {"KIND": "OPENING_BASIS_UNRESOLVED" if gross_length is None else
                         "WALL_HEIGHT_NOT_ESTABLISHED" if h is None else "NOT_ESTABLISHED_AS_MASONRY",
                 "WHY": (gross_why if gross_length is None else
                         "no established source gives this wall's height" if h is None else
                         ident.get("WHY_MATERIAL", "this band is not established to be billable masonry"))}]),
        }
        if not final:
            row[QY.diagnostic_name("NET_AREA_M2")] = net
            if gross_length is None:
                row[QY.diagnostic_name("NET_AREA_M2_IF_MATERIAL_SPANS")] = (
                    round(material * h - d, 6) if h is not None else None)
                row[QY.diagnostic_name("NET_AREA_M2_IF_MATERIAL_STOPS_AT_JAMBS")] = (
                    round((material + hosted_width) * h - d, 6) if h is not None else None)
            row["BLOCKED_NOTE"] = "; ".join(r.get("WHY", "") for r in row["BLOCKED_BY"]) or None
        rows.append(row)
    return rows

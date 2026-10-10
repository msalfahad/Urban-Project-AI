"""Which wall does this opening belong to - asked of the wall SEGMENTS, after the opening is known to exist.

A door is a hole in a wall, and a hole is drawn as the absence of material.  Asking whether the door's rectangle
overlaps wall material therefore asks the wrong question: in a source that stops each wall at its jambs the
correct answer is zero overlap, every time.  What identifies the host is the material AROUND the opening - two
collinear wall ends bracketing it, faces on both transverse sides, jambs that coincide with those ends, an axis
that agrees with the block's rotation, a gap the span fits.

Proximity is in here too, weighted almost to nothing.  It is a tie-break of last resort and never a reason: a
door two metres from a wall is not in that wall because there is nothing nearer.

The opening's DEPTH is not an input to any of this.  It is an output: once the host is known, the depth is the
host's thickness, and only then does the opening have a rectangle at all.
"""

from __future__ import annotations

from engine.qs_core import geom
from engine.qs_core.entities import CONFIDENCE_NONE, CONFIDENCE_PROVEN, CONFIDENCE_STRONG, CONFIDENCE_WEAK, \
    Evidence

HOST_CONFIRMED = "HOST_CONFIRMED"
HOST_UNRESOLVED = "HOST_WALL_UNRESOLVED"

BRACKETED_BY_TWO_WALL_ENDS = "BRACKETED_BY_TWO_COLLINEAR_WALL_ENDS"
INSIDE_ONE_WALL_RUN = "INSIDE_ONE_WALL_RUN"

# The evidence and what each piece is worth.  Structural fit dominates because it is the only term that
# distinguishes the wall an opening interrupts from a wall that merely happens to be near it.
WEIGHTS = {
    "STRUCTURAL_FIT": 0.30,        # the gap the opening sits in, or the run it sits inside
    "PARALLEL_FACES": 0.15,        # wall faces on both transverse sides of the opening
    "JAMB_ALIGNMENT": 0.15,        # the source's own reveals coincide with these wall ends
    "AXIS_AGREEMENT": 0.15,        # the opening runs along this wall, not across it
    "SPAN_FIT": 0.15,              # the interruption is as wide as the opening
    "THICKNESS_MATCH": 0.05,       # the same wall thickness either side
    "PROXIMITY": 0.05,             # last, and least
}

# The margin by which the leading group has to beat its rival before the question is settled.  Two groups within
# this of each other are not distinguishable by the geometry in front of us.
DECISIVE_MARGIN = 0.15

# Proximity alone may never host an opening: something structural has to fit.
STRUCTURAL_FIT_MIN = 0.50


def _axis_of(band):
    if band.axis:
        return band.axis
    b = band.bbox
    return geom.AXIS_X if b.width >= b.height else geom.AXIS_Y


def _along(band, axis):
    b = band.bbox if hasattr(band, "bbox") else geom.bbox(band.rects)
    return (b.x0, b.x1) if axis == geom.AXIS_X else (b.y0, b.y1)


def _across(band, axis):
    b = band.bbox if hasattr(band, "bbox") else geom.bbox(band.rects)
    return (b.y0, b.y1) if axis == geom.AXIS_X else (b.x0, b.x1)


class _Run:
    """Touching collinear segments of one thickness, treated as the one run of material they are.

    How finely an extractor chops a wall is a property of the extractor.  Looking for the host among raw
    segments makes the answer depend on that, so touching segments are coalesced first and the group keeps
    every reference it was built from.
    """

    def __init__(self, members, axis):
        self.members = list(members)
        self.axis = axis
        self.floor = members[0].floor
        self.thickness = members[0].thickness
        self.rects = [r for m in members for r in m.rects]
        self.component_ref = members[0].component_ref
        self.refs = sorted(m.component_ref for m in members)


def _coalesce(bands, axis, tolerance):
    """Group the segments on each line-and-thickness into the runs of material they actually form."""
    lines = {}
    for b in bands:
        a0, a1 = _across(b, axis)
        key = (b.floor, round((a0 + a1) / 2 / max(tolerance, 1e-9)),
               round((b.thickness or 0) / max(tolerance, 1e-9)))
        lines.setdefault(key, []).append(b)
    runs = []
    for _key, members in sorted(lines.items(), key=lambda kv: str(kv[0])):
        members.sort(key=lambda m: _along(m, axis)[0])
        current = [members[0]]
        for prev, nxt in zip(members, members[1:]):
            if _along(nxt, axis)[0] - _along(prev, axis)[1] <= tolerance:
                current.append(nxt)
            else:
                runs.append(_Run(current, axis))
                current = [nxt]
        runs.append(_Run(current, axis))
    return runs


def _groups_on_axis(candidate, bands, axis, tolerance):
    """Every wall group that could host this opening if it runs along `axis`."""
    c = candidate.cross(axis)
    lo, hi = candidate.interval(axis)
    on_line = [r for r in _coalesce([b for b in bands
                                     if b.floor == candidate.floor and _axis_of(b) == axis], axis, tolerance)
               if _across(r, axis)[0] - tolerance * 4 <= c <= _across(r, axis)[1] + tolerance * 4]

    groups = []
    for r in on_line:                                     # the opening lies inside one run of material
        s0, s1 = _along(r, axis)
        if s0 - tolerance <= lo and hi <= s1 + tolerance:
            groups.append({"SEGMENTS": [r], "RELATION": INSIDE_ONE_WALL_RUN, "GAP_M": None, "AXIS": axis})

    ordered = sorted(on_line, key=lambda r: _along(r, axis)[0])
    for prev, nxt in zip(ordered, ordered[1:]):
        gap_lo, gap_hi = _along(prev, axis)[1], _along(nxt, axis)[0]
        if gap_hi - gap_lo <= tolerance:
            continue
        if not (gap_lo - tolerance * 4 <= lo and hi <= gap_hi + tolerance * 4):
            continue
        groups.append({"SEGMENTS": [prev, nxt], "RELATION": BRACKETED_BY_TWO_WALL_ENDS,
                       "GAP_M": round(gap_hi - gap_lo, 6), "GAP_FROM": round(gap_lo, 6),
                       "GAP_TO": round(gap_hi, 6), "AXIS": axis,
                       # the two segments that actually face each other across the gap.  A run may be chopped
                       # into many pieces, and the wall builder works segment by segment, so the pair it has
                       # to be told about is this one, not the whole run.
                       "BRACKETING_REFS": sorted((prev.members[-1].component_ref,
                                                  nxt.members[0].component_ref))})
    return groups


def _score(candidate, group, tolerance):
    axis = group["AXIS"]
    lo, hi = candidate.interval(axis)
    c = candidate.cross(axis)
    segments = group["SEGMENTS"]

    if group["RELATION"] == BRACKETED_BY_TWO_WALL_ENDS:
        gap = group["GAP_M"]
        fit = max(0.0, 1.0 - abs(gap - candidate.span) / max(candidate.span, tolerance))
        structural, span_fit = fit, fit
    else:
        run = _along(segments[0], axis)
        length = run[1] - run[0]
        structural = 1.0 if length > 0 else 0.0
        span_fit = min(1.0, candidate.span / length) if length > 0 else 0.0

    across = [_across(b, axis) for b in segments]
    inside = sum(1 for a0, a1 in across if a0 - tolerance <= c <= a1 + tolerance)
    parallel = inside / len(across)

    if candidate.jamb_points and group["RELATION"] == BRACKETED_BY_TWO_WALL_ENDS:
        ends = (group["GAP_FROM"], group["GAP_TO"])
        js = sorted(p[0] if axis == geom.AXIS_X else p[1] for p in candidate.jamb_points)
        jamb = 1.0 if (len(js) >= 2 and abs(js[0] - ends[0]) <= tolerance * 4
                       and abs(js[-1] - ends[1]) <= tolerance * 4) else 0.0
    else:
        jamb = 0.5                                        # no reveals drawn: neither for nor against

    stated = candidate.axis or (None if candidate.rotation is None else
                                (geom.AXIS_X if round(candidate.rotation / 90.0) % 2 == 0 else geom.AXIS_Y))
    axis_agreement = 0.5 if stated is None else (1.0 if stated == axis else 0.0)

    thicknesses = [b.thickness for b in segments if b.thickness is not None]
    if len(thicknesses) < 2:
        thickness_match = 1.0 if thicknesses else 0.5
    else:
        spread = max(thicknesses) - min(thicknesses)
        thickness_match = 1.0 if spread <= tolerance else max(0.0, 1.0 - spread / max(thicknesses))

    cx, cy = candidate.centre
    d = min(geom.distance_point_to_rect(cx, cy, r) for b in segments for r in b.rects)
    proximity = max(0.0, 1.0 - d / max(candidate.span, tolerance * 10))

    parts = {"STRUCTURAL_FIT": structural, "PARALLEL_FACES": parallel, "JAMB_ALIGNMENT": jamb,
             "AXIS_AGREEMENT": axis_agreement, "SPAN_FIT": span_fit,
             "THICKNESS_MATCH": thickness_match, "PROXIMITY": proximity}
    parts["SCORE"] = sum(parts[k] * w for k, w in WEIGHTS.items())
    parts["WEIGHTS"] = dict(WEIGHTS)
    del lo, hi
    return parts


def resolve_host(candidate, bands, tolerance):
    """Resolve one opening's host wall group, or report that the geometry does not settle it."""
    axes = [candidate.axis] if candidate.axis else [geom.AXIS_X, geom.AXIS_Y]
    groups = []
    for axis in axes:
        groups += _groups_on_axis(candidate, bands, axis, tolerance)

    scored = []
    for g in groups:
        s = _score(candidate, g, tolerance)
        scored.append({"COMPONENT_REFS": sorted({ref for b in g["SEGMENTS"] for ref in b.refs}),
                       "BRACKETING_REFS": g.get("BRACKETING_REFS"),
                       "RELATION": g["RELATION"], "AXIS": g["AXIS"], "GAP_M": g.get("GAP_M"),
                       "THICKNESS_M": g["SEGMENTS"][0].thickness,
                       "SCORE": round(s["SCORE"], 6), "EVIDENCE": s, "_GROUP": g})
    scored.sort(key=lambda r: (-r["SCORE"], r["COMPONENT_REFS"]))

    published = [{k: v for k, v in r.items() if k != "_GROUP"} for r in scored]
    if not scored:
        record = {"HOST_STATUS": HOST_UNRESOLVED, "HOST_SEGMENT_REFS": [], "HOST_THICKNESS_M": None,
                  "DEPTH_M": None, "CANDIDATES": published, "CONFIDENCE": CONFIDENCE_NONE,
                  "WHY": "no wall group on this floor brackets or contains this opening; the wall it belongs "
                         "to is missing from the extraction, or the opening is drawn away from its wall",
                  "DECISIVE_MARGIN": DECISIVE_MARGIN}
        candidate.host_record = record
        return record

    best = scored[0]
    runner = scored[1]["SCORE"] if len(scored) > 1 else None
    margin = None if runner is None else round(best["SCORE"] - runner, 6)
    decisive = runner is None or margin >= DECISIVE_MARGIN
    structural = best["EVIDENCE"]["STRUCTURAL_FIT"] >= STRUCTURAL_FIT_MIN

    if decisive and structural:
        thickness = best["THICKNESS_M"]
        record = {"HOST_STATUS": HOST_CONFIRMED, "HOST_SEGMENT_REFS": best["COMPONENT_REFS"],
                  "HOST_BRACKETING_SEGMENT_REFS": best.get("BRACKETING_REFS"),
                  "RELATION": best["RELATION"], "AXIS": best["AXIS"], "GAP_M": best["GAP_M"],
                  "HOST_THICKNESS_M": thickness, "DEPTH_M": thickness,
                  "CANDIDATES": published, "RUNNER_UP_SCORE": runner, "MARGIN": margin,
                  "DECISIVE_MARGIN": DECISIVE_MARGIN,
                  "CONFIDENCE": CONFIDENCE_PROVEN if best["SCORE"] >= 0.9 else CONFIDENCE_STRONG,
                  "WHY": ("the material around this opening identifies one wall: " + best["RELATION"].lower()
                          .replace("_", " ")),
                  "DEPTH_SOURCE": "the host wall's own thickness, taken after the host was resolved"}
        candidate.host_record = record
        candidate.depth = thickness
        if candidate.axis is None:
            candidate.axis = best["AXIS"]
        return record

    record = {"HOST_STATUS": HOST_UNRESOLVED, "HOST_SEGMENT_REFS": [], "HOST_THICKNESS_M": None,
              "DEPTH_M": None, "CANDIDATES": published, "RUNNER_UP_SCORE": runner, "MARGIN": margin,
              "DECISIVE_MARGIN": DECISIVE_MARGIN, "CONFIDENCE": CONFIDENCE_WEAK,
              "WHY": ("two or more wall groups are equally plausible hosts, and apportioning a deduction "
                      "between them would put material against a wall that does not have this hole in it"
                      if not decisive else
                      "nothing structural fits: the leading group is only the nearest one, and proximity is "
                      "not a reason")}
    candidate.host_record = record
    return record


def resolve_hosts(candidates, bands, tolerance):
    """Resolve every confirmed opening's host, and publish the register of what was decided and what was not."""
    from engine.qs_core import admission as AD

    records = []
    for c in sorted(candidates, key=lambda x: x.candidate_ref):
        if c.existence != AD.EXISTS_CONFIRMED:
            continue
        rec = resolve_host(c, bands, tolerance)
        c.classification = (AD.OPENING_CONFIRMED_HOST_CONFIRMED if rec["HOST_STATUS"] == HOST_CONFIRMED
                            else AD.OPENING_CONFIRMED_HOST_UNRESOLVED)
        c.admission_evidence.append(Evidence("HOST_RESOLUTION", {
            "HOST_STATUS": rec["HOST_STATUS"], "HOST_SEGMENT_REFS": rec["HOST_SEGMENT_REFS"],
            "WHY": rec["WHY"],
            "NOTE": "the opening exists either way; what an unresolved host costs is a deduction, not its "
                    "place in the population"}))
        records.append(dict(rec, CANDIDATE_REF=c.candidate_ref, FLOOR=c.floor, TYPE=c.opening_type))
    confirmed = [r for r in records if r["HOST_STATUS"] == HOST_CONFIRMED]
    return {
        "REGISTER": records,
        "PHYSICAL_OPENINGS": len(records),
        "HOST_CONFIRMED": len(confirmed),
        "HOST_UNRESOLVED": len(records) - len(confirmed),
        "HOST_UNRESOLVED_REFS": sorted(r["CANDIDATE_REF"] for r in records
                                       if r["HOST_STATUS"] != HOST_CONFIRMED),
        "WEIGHTS": dict(WEIGHTS), "DECISIVE_MARGIN": DECISIVE_MARGIN,
        "STRUCTURAL_FIT_MIN": STRUCTURAL_FIT_MIN,
        "RULE": "a host is decided by the material around the opening, never by proximity alone, and never by "
                "requiring the opening to overlap material it is the absence of",
    }

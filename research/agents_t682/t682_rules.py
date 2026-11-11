"""T-682 rule (project-agnostic; scope: every villa whose slab top under a roof is bounded by R-T678-2). Research rule
read by the T-682 inputs builder; the candidate ARCH_TAKEOFF_V3.0.67 re-checks the record it leaves on each line.

R-T682-1 1.0.0  ONE SLAB PLANE MEANS ONE PLANE IN PLAN AND IN EVERY SECTION (extends R-T678-2 1.0.0, not edited;
    Checker challenge F-V678-2, Verifier 2026-11-10T17:58Z).
    Provenance: R-T678-2 transfers a lower bound of the slab top (s_lo = drawn head - tol + printed beam depth) to
    every member under ONE slab plane, and refuses 'two planes' only on a caller's boolean read from the plan (no level,
    step or thickness text inside the outline). A section can draw a step the plan does not print: the bound must
    then not cross it. New here:
    (a) the plane is stated as a record, not a boolean: {outline, plan_texts_inside: [level / step / thickness texts
        printed inside the outline], section_steps: [{section, step_m, inside_plane (True / False), evidence}]};
    (b) REFUSED when any plan text inside names a level, a step or a thickness (R-T678-2 'two planes'), and when any
        section step with step_m > 0 lies inside the plane (inside_plane True) or its position is not stated
        (inside_plane None: never assumed outside);
    (c) a section step drawn OUTSIDE the plane (inside_plane False, with its evidence) does not split it; it is kept
        in the result as checked;
    (d) otherwise the bound is R-T678-2 exactly (slab_top_lower_bound with one_plane=True), and the result carries
        the plane record so a later reader sees what was checked.
    Refused also: a step not in metres (> 2.0 or negative), a section with no evidence text.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t678"))
import t678_rules as R78  # noqa: E402

D = R78.D
q6 = R78.q6
Refused = R78.Refused
RULE = "R-T682-1 1.0.0"
PLANE_TEXT_KINDS = ("LEVEL", "STEP", "THICKNESS")


def check_plane(plane):
    """-> {'state': 'ONE_PLANE', 'steps_outside': [...], 'outline': ...}; raises Refused (R-T682-1 (b))."""
    if not isinstance(plane, dict) or not plane.get("outline"):
        raise Refused("R-T682-1: the slab plane is stated as a record with its outline")
    for t in plane.get("plan_texts_inside") or ():
        if t.get("kind") in PLANE_TEXT_KINDS:
            raise Refused(f"R-T682-1: plan text {t.get('text')!r} ({t['kind']}) inside the outline: two planes")
    outside = []
    for s in plane.get("section_steps") or ():
        if not s.get("section") or not s.get("evidence"):
            raise Refused("R-T682-1: a section step names its section and its evidence")
        st = D(s.get("step_m"), "step")
        if st < 0 or st > Decimal("2.0"):
            raise Refused(f"R-T682-1: step {st} not in metres")
        if st == 0:
            continue
        where = s.get("inside_plane")
        if where is None:
            raise Refused(f"R-T682-1: section {s['section']} draws a {st} m step whose position against the plane is "
                          f"not stated (never assumed outside)")
        if where is True:
            raise Refused(f"R-T682-1: section {s['section']} draws a {st} m step inside the plane: stepped soffit, no "
                          f"transfer of the bound")
        outside.append({"section": s["section"], "step_m": str(q6(st)), "evidence": s["evidence"]})
    return {"state": "ONE_PLANE", "outline": plane["outline"], "steps_outside": outside,
            "sections_checked": sorted({s["section"] for s in plane.get("section_steps") or ()}), "rule": RULE}


def slab_top_lower_bound(*, heads, plane, finished_ceiling=None):
    """R-T682-1: the plane checked in plan and section first, then R-T678-2 unchanged."""
    pl = check_plane(plane)
    r = R78.slab_top_lower_bound(heads=heads, one_plane=True, finished_ceiling=finished_ceiling)
    return dict(r, plane=pl, rule=f"{RULE} over R-T678-2 1.0.0")

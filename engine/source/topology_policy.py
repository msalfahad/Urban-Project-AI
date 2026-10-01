"""TOPOLOGY_TOLERANCE_POLICY (R8.8) - frozen BEFORE any room total of any project was looked at.

The problem it answers
    Two routes reading the same drawing differed by 4.4e-11 drawing units on one wall line; the legacy room method
    (exact `is_horizontal` and raster cells) moved 1.64 m2 between two rooms. Any single tolerance has a cliff
    somewhere; the defect is not the size of the tolerance but that nobody can see when a result sits on a cliff.

The policy: three bands and a stability certificate
    NOISE        d <= eps_n   the two values are the same number written twice (representation noise)
    AMBIGUOUS    eps_n < d < eps_r   neither noise nor a deliberately drawn distance
    AUTHORED     d >= eps_r   a drawn, physical distance: the features are distinct

    eps_n = max(1, M) * 2**-30   (M = largest coordinate magnitude in the input, native units)
        Basis: NUMERIC REPRESENTATION. float64 has unit roundoff 1.1e-16; a placement composes at most 16 insert
        levels (kernel MAX_NESTING_DEPTH) of a few operations each, and a DXF text round trip keeps 16-17
        significant digits, so honest route noise is below ~1e-13 relative (observed: 4e-16 relative, H584).
        2**-30 = 9.3e-10 relative leaves more than three orders of magnitude of margin above that, and is the same
        order as the kernel's similarity tolerance (1e-9). It is unit-free because noise is relative to the
        numbers, not to millimetres.
    eps_r = 1 mm of PHYSICAL length, converted with the revision's own unit claim (native_to_mm)
        Basis: AUTHORED PRECISION. A plan states and builds lengths to the millimetre; nothing a takeoff resolves
        (a gap, a reveal, a wall face) is drawn deliberately below 1 mm, and at 1:50-1:100 it is invisible on the
        sheet. A separation below 1 mm and above noise is therefore not evidence of intent either way.
        Without a unit claim eps_r does not exist and nothing is certified.

    The topology is built twice, at eps_n and at eps_r. A site is CERTIFIED only when the two builds give the
    same site (same boundary source identities, area within eps_r x perimeter). Otherwise it is
    TOLERANCE_SENSITIVE -> REVIEW_REQUIRED: the answer depends on a decision inside the ambiguous band. This is
    what makes the tolerance unable to swallow a real difference: anything decided differently at the two ends of
    the band is surfaced, not resolved.

Predicates (which tolerance applies)
    points_coincident, junction_snap, segment_endpoint_on_segment, curve_endpoint_on_curve, crossing:
        eps_n (topology build), and again at eps_r (certificate build)
    is_horizontal, is_vertical, axis_alignment: NOT USED. The engine has no axis predicate at all; walls at any
        angle are handled by exact intersection. (The H584 defect class is removed, not toleranced.)
    closed_cycle: by the planar graph (a face is a cycle of the half-edge structure), no tolerance of its own
    label_on_boundary: distance from a label point to its site boundary <= eps_r -> ambiguity finding
    sliver: a site with area <= eps_r x perimeter / 2 is a zero-width sliver, never a room
    region membership noise: eps_n
    opening closure: a ray from the door's hinge / closed-leaf end must meet an admitted wall within
        JAMB_ALLOWANCE_RATIO x leaf radius at BOTH ends; exactly one of the two leaf hypotheses may succeed

Never mutate source geometry
    Clustering decides TOPOLOGICAL equivalence (which end points are one node). Physical part coordinates are not
    rewritten; each site records its boundary source identities, and its area bound states the largest effect the
    node clustering can have (eps x perimeter).

Project-agnostic; stdlib only. The digest below is frozen in the R8.8 register and tested.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "TOPOLOGY_TOLERANCE_POLICY_V1"
NOISE_RELATIVE = 2.0 ** -30
AUTHORED_PRECISION_MM = 1.0
JAMB_ALLOWANCE_RATIO = 0.25
MIN_BAND_RATIO = 10.0              # eps_r must exceed eps_n by at least this factor, or the policy is degenerate

NOISE, AMBIGUOUS, AUTHORED = "NOISE", "AMBIGUOUS", "AUTHORED"

PREDICATES = {
    "points_coincident": "eps_n (build) / eps_r (certificate build)",
    "junction_snap": "eps_n (build) / eps_r (certificate build)",
    "segment_endpoint_on_segment": "eps_n (build) / eps_r (certificate build)",
    "curve_endpoint_on_curve": "eps_n (build) / eps_r (certificate build)",
    "crossing": "exact intersection; end-point proximity by eps",
    "is_horizontal": "NOT USED (no axis predicate exists in the engine)",
    "is_vertical": "NOT USED (no axis predicate exists in the engine)",
    "axis_alignment": "NOT USED (no axis predicate exists in the engine)",
    "closed_cycle": "planar half-edge faces; no separate tolerance",
    "label_on_boundary": "eps_r",
    "sliver": "area <= eps_r x perimeter / 2",
    "region_membership_noise": "eps_n",
    "opening_closure_reach": f"JAMB_ALLOWANCE_RATIO = {JAMB_ALLOWANCE_RATIO} x leaf radius",
}


def eps_noise(max_abs_coordinate: float) -> float:
    return max(1.0, abs(float(max_abs_coordinate))) * NOISE_RELATIVE


def eps_authored(native_to_mm) -> float | None:
    if native_to_mm is None or not float(native_to_mm) > 0:
        return None
    return AUTHORED_PRECISION_MM / float(native_to_mm)


def band(d: float, e_n: float, e_r: float) -> str:
    return NOISE if d <= e_n else AUTHORED if d >= e_r else AMBIGUOUS


def tolerances(max_abs_coordinate, native_to_mm) -> dict:
    e_n = eps_noise(max_abs_coordinate)
    e_r = eps_authored(native_to_mm)
    ok = e_r is not None and e_r >= MIN_BAND_RATIO * e_n
    return {"eps_n": e_n, "eps_r": e_r, "valid": ok,
            "reason": None if ok else ("no unit claim: the authored band does not exist" if e_r is None
                                       else "degenerate: eps_r is not at least 10 x eps_n")}


def record() -> dict:
    rec = {"id": POLICY_ID, "noise_relative": NOISE_RELATIVE, "noise_basis": "numeric representation (float64, "
           "<= 16 insert levels, DXF 16-17 digit text); relative, unit-free",
           "authored_precision_mm": AUTHORED_PRECISION_MM, "authored_basis": "construction / setting-out precision "
           "of a plan; converted with the revision's own unit claim",
           "jamb_allowance_ratio": JAMB_ALLOWANCE_RATIO, "min_band_ratio": MIN_BAND_RATIO,
           "bands": [NOISE, AMBIGUOUS, AUTHORED], "predicates": PREDICATES,
           "certificate": "two builds (eps_n, eps_r); a site is CERTIFIED only if identical in both",
           "calibration": "none: no room total, benchmark row or project value was read to choose any number here",
           "source_geometry": "never rewritten; clustering is topological equivalence only"}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec

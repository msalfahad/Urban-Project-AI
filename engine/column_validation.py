"""E1.4 — a column is not confirmed while its own geometry disagrees.

THE DEFECT THIS REPLACES

External review of frozen E1.3 found a loop classified as a structural
column whose recorded footprint_box_mm spans roughly 600 x 2600 mm while
its recorded size_mm reads 600 x 250 mm. Two numbers describing one
footprint, an order of magnitude apart in one direction, and the
classification survived.

No structural classification may outlive an internal geometry
inconsistency. A 600 x 2600 figure may be a column, a pier, a wall stub,
a duct or a stair nosing - but whatever it is, a classifier that reports
its size as 600 x 250 does not know which, and must say so.

WHAT THIS DOES

Every candidate's geometry is derived here, from its own closed loop, and
cross-checked against what was reported about it. Where they disagree the
candidate is UNRESOLVED and the disagreement is recorded with both
numbers.

WHAT IT REFUSES TO DO

Nothing is deleted. A candidate that fails is still a real drawn figure
and keeps its geometry; only the claim that it is a structural column is
withheld.

And no candidate becomes a column merely because it is a closed loop,
because it repeats, because it touches a wall, because part of it lies on
a structural layer, or because it resembles another loop. LAYER EVIDENCE
IS EVIDENCE, NOT TRUTH: it raises a candidate and never settles it.
"""

from __future__ import annotations

import hashlib
import math

MODEL = "NO_STRUCTURAL_CLASSIFICATION_SURVIVES_ITS_OWN_INCONSISTENCY_V1"

STRUCTURAL_COLUMN_CONFIRMED = "STRUCTURAL_COLUMN_CONFIRMED"
STRUCTURAL_COLUMN_UNRESOLVED = "STRUCTURAL_COLUMN_UNRESOLVED"
NOT_A_STRUCTURAL_COLUMN = "NOT_A_STRUCTURAL_COLUMN"

EXISTENCE_STATUSES = (STRUCTURAL_COLUMN_CONFIRMED,
                      STRUCTURAL_COLUMN_UNRESOLVED,
                      NOT_A_STRUCTURAL_COLUMN)

# How far the derived and reported figures may differ and still agree.
SIZE_TOLERANCE_MM = 5.0
# A closed loop whose two sides differ by more than this is not a compact
# footprint. It is not thereby disqualified - it is a reason to look.
COMPACT_ASPECT_LIMIT = 4.0

LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH = (
    "a structural layer is where the author put something. It raises a "
    "candidate and settles nothing: a wall stub, a duct, a plinth and a "
    "stair nosing all end up on structural layers too. Nothing becomes a "
    "column because of its layer, because it is closed, because it "
    "repeats, because it touches a wall, or because it resembles another "
    "loop")

NOTHING_IS_DELETED = (
    "a candidate that fails validation keeps its geometry and its "
    "identity as a drawn figure. What is withheld is only the claim that "
    "it is a structural column. Deleting drawn material to tidy a "
    "classification loses the drawing")

WHY_SELF_CONSISTENCY_COMES_FIRST = (
    "the derived footprint and the reported size describe the same thing. "
    "If they disagree, at least one is wrong and nothing downstream can "
    "tell which. Every other question about the candidate - exposure, "
    "clear-face ownership - is asked of a geometry that has to be settled "
    "first")


def model_hash() -> str:
    parts = [MODEL, str(SIZE_TOLERANCE_MM), str(COMPACT_ASPECT_LIMIT)] \
        + list(EXISTENCE_STATUSES)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def derive_geometry(loop) -> dict:
    """Everything about a closed loop, computed from the loop itself."""
    pts = [(float(x), float(y)) for x, y in (loop or ())]
    if len(pts) < 3:
        return {"DERIVED": False,
                "why": "fewer than three points is not a closed footprint"}
    if pts[0] != pts[-1]:
        pts = pts + [pts[0]]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    per = sum(math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
              for i in range(len(pts) - 1))
    area = abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
                   for i in range(len(pts) - 1))) / 2.0
    longest = max(
        math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
        for i in range(len(pts) - 1))
    short, long_ = (min(w, h), max(w, h))
    return {
        "DERIVED": True,
        "derived_bbox_width_mm": round(w, 3),
        "derived_bbox_height_mm": round(h, 3),
        "derived_perimeter_mm": round(per, 3),
        "derived_area_mm2": round(area, 3),
        "longest_member_extent_mm": round(longest, 3),
        "vertices": len(pts) - 1,
        "aspect_ratio": round(long_ / short, 3) if short > 0 else None,
        "footprint_is_compact": (
            short > 0 and (long_ / short) <= COMPACT_ASPECT_LIMIT),
    }


def cross_check(derived, reported_size_mm) -> dict:
    """Do the derived footprint and the reported size describe one thing?"""
    if not derived.get("DERIVED"):
        return {"DERIVED_GEOMETRY_SELF_CONSISTENT": False,
                "why": derived.get("why", "no geometry was derived")}
    if not reported_size_mm or len(tuple(reported_size_mm)) != 2:
        return {
            "DERIVED_GEOMETRY_SELF_CONSISTENT": False,
            "reported_size_mm": None,
            "why": ("nothing was reported to cross-check the derived "
                    "footprint against, so self-consistency is not "
                    "established"),
        }
    rw, rh = (float(reported_size_mm[0]), float(reported_size_mm[1]))
    dw = derived["derived_bbox_width_mm"]
    dh = derived["derived_bbox_height_mm"]
    # a footprint may be reported in either order
    direct = (abs(dw - rw) <= SIZE_TOLERANCE_MM
              and abs(dh - rh) <= SIZE_TOLERANCE_MM)
    swapped = (abs(dw - rh) <= SIZE_TOLERANCE_MM
               and abs(dh - rw) <= SIZE_TOLERANCE_MM)
    ok = direct or swapped
    return {
        "DERIVED_GEOMETRY_SELF_CONSISTENT": bool(ok),
        "reported_size_mm": [rw, rh],
        "derived_size_mm": [dw, dh],
        "matched_in_reported_order": bool(direct),
        "matched_with_the_two_sides_swapped": bool(swapped and not direct),
        "worst_disagreement_mm": round(
            min(max(abs(dw - rw), abs(dh - rh)),
                max(abs(dw - rh), abs(dh - rw))), 3),
        "tolerance_mm": SIZE_TOLERANCE_MM,
        "why": ("the derived footprint and the reported size describe the "
                "same figure and agree" if ok else
                "the derived footprint and the reported size describe the "
                "same figure and do not agree. Nothing downstream can tell "
                "which is wrong, so the structural claim is withheld"),
    }


def assess(candidate) -> dict:
    """One candidate's existence status, and why.

    `candidate` carries `loop` (the closed footprint), optionally
    `reported_size_mm`, and whatever evidence was gathered about it:
    `on_structural_layer`, `repeats_as_a_family`, `touches_a_wall`,
    `has_a_block_reference`, `resembles_another_loop`.
    """
    derived = derive_geometry(candidate.get("loop"))
    checked = cross_check(derived, candidate.get("reported_size_mm"))
    consistent = checked["DERIVED_GEOMETRY_SELF_CONSISTENT"]

    raising = [k for k in ("on_structural_layer", "repeats_as_a_family",
                           "touches_a_wall", "has_a_block_reference",
                           "resembles_another_loop")
               if candidate.get(k)]

    if not consistent:
        status = STRUCTURAL_COLUMN_UNRESOLVED
        why = ("its own geometry does not agree with what was reported "
               "about it, so what this figure is has not been established")
    elif not derived.get("footprint_is_compact"):
        status = STRUCTURAL_COLUMN_UNRESOLVED
        why = (f"the footprint is {derived['aspect_ratio']} times longer "
               "than it is wide. A figure that long may be a pier, a wall "
               "stub, a duct or a nosing, and the drawing has not "
               "established which")
    elif not raising:
        status = STRUCTURAL_COLUMN_UNRESOLVED
        why = ("the geometry is self-consistent and compact, and nothing "
               "in the drawing raises it as structure. A compact closed "
               "loop on its own is not a column")
    else:
        status = STRUCTURAL_COLUMN_CONFIRMED
        why = ("the geometry is self-consistent and compact, and the "
               "drawing raises it as structure: " + ", ".join(raising))

    return {
        "COLUMN_EXISTENCE_STATUS": status,
        "DERIVED_GEOMETRY_SELF_CONSISTENT": consistent,
        "evidence_raising_it_as_structure": raising,
        "layer_evidence_is_evidence_not_truth":
            LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH,
        "nothing_is_deleted": NOTHING_IS_DELETED,
        "why": why,
        **derived,
        **{k: v for k, v in checked.items() if k != "why"},
        "self_consistency_why": checked.get("why"),
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "EXISTENCE_STATUSES": list(EXISTENCE_STATUSES),
        "SIZE_TOLERANCE_MM": SIZE_TOLERANCE_MM,
        "COMPACT_ASPECT_LIMIT": COMPACT_ASPECT_LIMIT,
        "why": {
            "self_consistency_comes_first": WHY_SELF_CONSISTENCY_COMES_FIRST,
            "layer_evidence_is_evidence_not_truth":
                LAYER_EVIDENCE_IS_EVIDENCE_NOT_TRUTH,
            "nothing_is_deleted": NOTHING_IS_DELETED,
        },
    }

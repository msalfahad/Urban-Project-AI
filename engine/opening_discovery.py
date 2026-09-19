"""E1.4 — find an opening from the door, as well as from the gap.

THE DEFECT THIS REPLACES

Frozen E1.3 discovered openings in one direction only:

    wall ends  ->  candidate gap  ->  inspect door evidence

So a doorway existed, for the system, only if its two jambs had already
become dangling ends of material-wall faces. Cold review found rooms
closed on the drawing, with a door leaf and a quarter-circle swing arc
plainly drawn, where the walk stopped anyway: no candidate gap had ever
been proposed there, so the gap ontology was never asked. Widening how
far apart two ends may be changed nothing, which ruled out distance and
left the direction of the search.

A real door must not disappear because its jamb was not already
classified as a material-wall free end.

WHAT THIS ADDS

A second, independent path, in the other direction:

    door evidence -> opening candidate -> host wall search
                  -> jamb / wall interruption alignment
                  -> portal classification

and then a reconciliation of the two. Where both paths find the same
opening it is CONFIRMED_BY_BOTH; where only one does, that is said; where
they disagree about the same place it is CONFLICT, not a silent pick.

The exact geometry still comes from CAD. A leaf and an arc say an opening
is HERE; they never supply its coordinates, and appearance alone is never
a portal.

WHAT IS KEPT

Everything, including what failed: every wall end, every door entity,
every swing arc, every opening candidate from either path, and every
host-wall match that was attempted and rejected, with the reason. E1.3
had no record of a wall end that never became a candidate gap, so "a door
is visible but there is no portal" could not be audited without rerunning
the session.
"""

from __future__ import annotations

import hashlib
import math

MODEL = "AN_OPENING_IS_FOUND_FROM_THE_DOOR_AS_WELL_AS_FROM_THE_GAP_V1"

# --- door evidence -------------------------------------------------------
DOOR_LEAF = "A_DOOR_LEAF_IS_DRAWN"
SWING_ARC = "A_QUARTER_CIRCLE_SWING_ARC_IS_DRAWN"
DOOR_BLOCK = "A_DOOR_BLOCK_REFERENCE_IS_INSERTED"
HINGE_POINT = "A_HINGE_POINT_IS_DRAWN"
OPENING_SYMBOL = "AN_OPENING_SYMBOL_IS_DRAWN"
JAMB_GEOMETRY = "JAMB_GEOMETRY_RETURNS_INTO_THE_WALL"
THRESHOLD = "A_THRESHOLD_IS_DRAWN"
WALL_INTERRUPTION = "THE_WALL_BAND_IS_INTERRUPTED_HERE"
SCHEDULE_REFERENCE = "A_SCHEDULE_OR_DOOR_REFERENCE_NAMES_IT"

DOOR_EVIDENCE = (DOOR_LEAF, SWING_ARC, DOOR_BLOCK, HINGE_POINT,
                 OPENING_SYMBOL, JAMB_GEOMETRY, THRESHOLD,
                 WALL_INTERRUPTION, SCHEDULE_REFERENCE)

# Evidence that an opening EXISTS somewhere here. None of it is geometry.
ESTABLISHES_THAT_AN_OPENING_EXISTS = (DOOR_LEAF, SWING_ARC, DOOR_BLOCK,
                                      OPENING_SYMBOL, SCHEDULE_REFERENCE)

# --- reconciliation statuses --------------------------------------------
CONFIRMED_BY_BOTH = "CONFIRMED_BY_BOTH"
CONFIRMED_DOOR_FIRST = "CONFIRMED_DOOR_FIRST"
CONFIRMED_GAP_FIRST = "CONFIRMED_GAP_FIRST"
PROBABLE = "PROBABLE"
CONFLICT = "CONFLICT"
UNRESOLVED = "UNRESOLVED"

RECONCILIATION_STATUSES = (CONFIRMED_BY_BOTH, CONFIRMED_DOOR_FIRST,
                           CONFIRMED_GAP_FIRST, PROBABLE, CONFLICT,
                           UNRESOLVED)

# --- why a host-wall match can be rejected ------------------------------
NO_HOST_WALL_WITHIN_REACH = "NO_HOST_WALL_WITHIN_REACH_OF_THE_DOOR"
HOST_WALL_NOT_INTERRUPTED = "THE_HOST_WALL_RUNS_UNBROKEN_THROUGH_THE_DOOR"
DOOR_NOT_ALIGNED_WITH_THE_WALL = "THE_DOOR_DOES_NOT_ALIGN_WITH_THE_WALL"
AMBIGUOUS_HOST_WALL = "MORE_THAN_ONE_WALL_COULD_HOST_IT"
NO_JAMB_GEOMETRY_EITHER_SIDE = "NEITHER_SIDE_OF_THE_OPENING_HAS_A_JAMB"

REJECTION_REASONS = (NO_HOST_WALL_WITHIN_REACH, HOST_WALL_NOT_INTERRUPTED,
                     DOOR_NOT_ALIGNED_WITH_THE_WALL, AMBIGUOUS_HOST_WALL,
                     NO_JAMB_GEOMETRY_EITHER_SIDE)

APPEARANCE_IS_NOT_A_PORTAL = (
    "a leaf and an arc establish that an opening exists somewhere here. "
    "They do not establish where it starts, where it stops, or how wide "
    "it is. The geometry comes from the CAD wall the opening sits in, and "
    "a portal is never inferred from appearance alone")

A_DOOR_MUST_NOT_DISAPPEAR = (
    "an opening whose jambs were never classified as material-wall free "
    "ends was, before this pass, invisible to the whole system: no "
    "candidate gap, so no classification, so a closed room read as not "
    "established. Discovery now runs in both directions so that the "
    "absence of one representation cannot delete a drawn door")

WHAT_IS_KEPT_INCLUDES_WHAT_FAILED = (
    "every wall end, door entity, swing arc, opening candidate and "
    "host-wall match attempt is recorded, including the rejected ones and "
    "the reason each was rejected. A reviewer asking why a visible door "
    "produced no portal can answer it from the run")


def model_hash() -> str:
    parts = [MODEL] + list(DOOR_EVIDENCE) + list(RECONCILIATION_STATUSES) \
        + list(REJECTION_REASONS)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


# How far a wall's own interruption may lie off that wall's line and
# still be that wall's interruption. It is a drawing tolerance.
SPAN_LIES_ON_THE_WALL_MM = 50.0

A_SPAN_BELONGS_TO_THE_WALL_IT_INTERRUPTS = (
    "an interruption is a stretch where a particular wall stops. A gap "
    "somewhere else on the floor is not this wall's interruption however "
    "near the door happens to be, and offering every wall every gap makes "
    "any door match something. Both ends of the span have to lie on this "
    "wall's own line")


def _off_line(p, a, b) -> float:
    """How far a point lies off the infinite line through a and b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    if n <= 0:
        return _dist(p, a)
    return abs((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / n


def door_first(doors, walls, *, reach_mm, align_deg=10.0,
               span_on_wall_mm=SPAN_LIES_ON_THE_WALL_MM) -> dict:
    """From each piece of door evidence, look for the wall that hosts it.

    `doors` are dicts with `door_id`, `at_mm`, `evidence`, and optionally
    `direction`. `walls` are dicts with `wall_id`, `a`, `b`, and
    `interrupted_spans` - the stretches where that wall's band stops.
    """
    cos_lim = math.cos(math.radians(align_deg))
    candidates, attempts = [], []
    for d in doors:
        ev = set(d.get("evidence") or ())
        if not (ev & set(ESTABLISHES_THAT_AN_OPENING_EXISTS)):
            attempts.append({
                "door_id": d.get("door_id"),
                "MATCHED": False,
                "REJECTED_BECAUSE": "NO_EVIDENCE_THAT_AN_OPENING_EXISTS",
                "evidence": sorted(ev),
                "why": ("nothing here establishes that an opening exists, "
                        "so no host wall was looked for"),
            })
            continue

        at = tuple(d["at_mm"])
        near = []
        for w in walls:
            a, b = tuple(w["a"]), tuple(w["b"])
            L = _dist(a, b) or 1.0
            t = max(0.0, min(1.0, ((at[0] - a[0]) * (b[0] - a[0])
                                   + (at[1] - a[1]) * (b[1] - a[1])) / (L * L)))
            foot = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
            gap = _dist(at, foot)
            if gap <= reach_mm:
                near.append((gap, w, foot))
        near.sort(key=lambda r: r[0])

        if not near:
            attempts.append({
                "door_id": d.get("door_id"), "MATCHED": False,
                "REJECTED_BECAUSE": NO_HOST_WALL_WITHIN_REACH,
                "searched_reach_mm": reach_mm,
                "why": ("door evidence is drawn here and no wall lies "
                        "within reach to host the opening"),
            })
            continue

        gap, w, foot = near[0]
        spans = [s for s in (w.get("interrupted_spans") or ())]
        wa, wb = tuple(w["a"]), tuple(w["b"])
        hosting, best = None, None
        for s in spans:
            sa, sb = tuple(s["from_mm"]), tuple(s["to_mm"])
            # the span has to be an interruption of THIS wall
            if max(_off_line(sa, wa, wb), _off_line(sb, wa, wb)) \
                    > span_on_wall_mm:
                continue
            # NOT `d`: that is the door under test, and shadowing it here
            # made the door a float two lines later
            sep = _dist(_mid(sa, sb), foot)
            if sep > reach_mm:
                continue
            if best is None or sep < best:
                hosting, best = s, sep
        if hosting is None:
            attempts.append({
                "door_id": d.get("door_id"), "MATCHED": False,
                "host_wall_id": w.get("wall_id"),
                "REJECTED_BECAUSE": HOST_WALL_NOT_INTERRUPTED,
                "spans_offered_for_this_wall": len(spans),
                "a_span_belongs_to_the_wall_it_interrupts":
                    A_SPAN_BELONGS_TO_THE_WALL_IT_INTERRUPTS,
                "why": ("the nearest wall runs unbroken past this door. An "
                        "opening needs the wall to stop; a leaf drawn "
                        "against an unbroken wall is not a portal"),
            })
            continue

        if d.get("direction"):
            u = d["direction"]
            wa, wb = tuple(w["a"]), tuple(w["b"])
            wl = _dist(wa, wb) or 1.0
            wu = ((wb[0] - wa[0]) / wl, (wb[1] - wa[1]) / wl)
            if abs(u[0] * wu[0] + u[1] * wu[1]) < cos_lim:
                attempts.append({
                    "door_id": d.get("door_id"), "MATCHED": False,
                    "host_wall_id": w.get("wall_id"),
                    "REJECTED_BECAUSE": DOOR_NOT_ALIGNED_WITH_THE_WALL,
                    "why": ("the door does not lie along the wall it would "
                            "have to sit in"),
                })
                continue

        attempts.append({"door_id": d.get("door_id"), "MATCHED": True,
                         "host_wall_id": w.get("wall_id")})
        candidates.append({
            "OPENING_CANDIDATE_ID": f"DOOR-FIRST-{d.get('door_id')}",
            "FOUND_BY": "DOOR_FIRST",
            "door_id": d.get("door_id"),
            "door_evidence": sorted(ev),
            "host_wall_id": w.get("wall_id"),
            # the geometry is the wall's own interruption, never the door's
            "start_mm": list(hosting["from_mm"]),
            "end_mm": list(hosting["to_mm"]),
            "width_mm": round(_dist(tuple(hosting["from_mm"]),
                                    tuple(hosting["to_mm"])), 3),
            "geometry_came_from": "THE_HOST_WALLS_OWN_INTERRUPTION",
            "appearance_is_not_a_portal": APPEARANCE_IS_NOT_A_PORTAL,
        })
    return {
        "MODEL": MODEL,
        "OPENING_CANDIDATES": candidates,
        "HOST_WALL_MATCH_ATTEMPTS": attempts,
        "matched": sum(1 for a in attempts if a.get("MATCHED")),
        "rejected": sum(1 for a in attempts if not a.get("MATCHED")),
        "a_door_must_not_disappear": A_DOOR_MUST_NOT_DISAPPEAR,
        "what_is_kept_includes_what_failed": WHAT_IS_KEPT_INCLUDES_WHAT_FAILED,
    }


A_SPAN_IS_ONE_OPENING = (
    "several pieces of door evidence can stand at one interruption - two "
    "leaves of a double door, a leaf and its swing arc, a leaf drawn "
    "twice. They are evidence about that one opening. Counting them as "
    "separate openings turns the strength of the evidence into a number "
    "of doors that are not there")


def reconcile(gap_first, door_first_out, *, same_place_mm=150.0,
              width_tolerance_mm=50.0) -> dict:
    """Put the two searches beside each other, deterministically.

    `same_place_mm` is how close two findings must be to be the same
    opening; `width_tolerance_mm` is how closely they must then agree
    about how wide it is. They are two different questions and they had
    better not share one number.
    """
    rows = []
    used_door = set()
    for g in gap_first:
        ga, gb = tuple(g["start_mm"]), tuple(g["end_mm"])
        gm = _mid(ga, gb)
        match = None
        for d in door_first_out.get("OPENING_CANDIDATES", ()):
            dm = _mid(tuple(d["start_mm"]), tuple(d["end_mm"]))
            if _dist(gm, dm) <= same_place_mm:
                match = d
                break
        if match is None:
            rows.append({
                "OPENING_ID": g.get("GAP_ID") or g.get("OPENING_CANDIDATE_ID"),
                "RECONCILIATION_STATUS": CONFIRMED_GAP_FIRST,
                "gap_first": g, "door_first": None,
                "why": ("the gap search proposed this opening and the door "
                        "search found no door evidence for it"),
            })
            continue
        used_door.add(match["OPENING_CANDIDATE_ID"])
        w_g = _dist(ga, gb)
        w_d = match["width_mm"]
        if abs(w_g - w_d) > width_tolerance_mm:
            status, why = CONFLICT, (
                "both searches found an opening in the same place and "
                f"disagree about its width: {round(w_g, 1)} mm against "
                f"{round(w_d, 1)} mm. Neither is preferred")
        else:
            status, why = CONFIRMED_BY_BOTH, (
                "the gap search and the door search independently found "
                "the same opening, at the same place, at the same width")
        rows.append({
            "OPENING_ID": g.get("GAP_ID") or g.get("OPENING_CANDIDATE_ID"),
            "RECONCILIATION_STATUS": status,
            "gap_first": g, "door_first": match, "why": why,
        })

    # ONE SPAN IS ONE OPENING. Several doors can evidence the same
    # interruption - a double leaf, a leaf and its arc, a leaf drawn twice
    # - and each is evidence about that one opening, not another opening.
    by_span = {}
    for d in door_first_out.get("OPENING_CANDIDATES", ()):
        if d["OPENING_CANDIDATE_ID"] in used_door:
            continue
        key = tuple(sorted((tuple(round(v, 3) for v in d["start_mm"]),
                            tuple(round(v, 3) for v in d["end_mm"]))))
        by_span.setdefault(key, []).append(d)
    for key, group in by_span.items():
        evidence = sorted({e for d in group for e in d["door_evidence"]})
        strong = set(evidence) & set(ESTABLISHES_THAT_AN_OPENING_EXISTS)
        first = group[0]
        rows.append({
            "OPENING_ID": first["OPENING_CANDIDATE_ID"],
            "RECONCILIATION_STATUS": (CONFIRMED_DOOR_FIRST if strong
                                      else PROBABLE),
            "gap_first": None, "door_first": first,
            "door_ids_evidencing_this_opening": sorted(
                d["door_id"] for d in group),
            "doors_evidencing_this_opening": len(group),
            "door_evidence": evidence,
            "one_span_is_one_opening": A_SPAN_IS_ONE_OPENING,
            "why": ("the door search found this opening from drawn door "
                    "evidence and the gap search never proposed it. This is "
                    "the case that used to vanish"
                    if strong else
                    "the door search found something here on weaker "
                    "evidence and the gap search did not propose it"),
        })

    counts = {s: sum(1 for r in rows if r["RECONCILIATION_STATUS"] == s)
              for s in RECONCILIATION_STATUSES}
    return {
        "MODEL": MODEL,
        "RECONCILED_OPENINGS": rows,
        "counts_by_status": counts,
        "RECONCILIATION_STATUSES": list(RECONCILIATION_STATUSES),
        "a_door_must_not_disappear": A_DOOR_MUST_NOT_DISAPPEAR,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "DOOR_EVIDENCE": list(DOOR_EVIDENCE),
        "ESTABLISHES_THAT_AN_OPENING_EXISTS":
            list(ESTABLISHES_THAT_AN_OPENING_EXISTS),
        "RECONCILIATION_STATUSES": list(RECONCILIATION_STATUSES),
        "REJECTION_REASONS": list(REJECTION_REASONS),
        "why": {
            "appearance_is_not_a_portal": APPEARANCE_IS_NOT_A_PORTAL,
            "a_door_must_not_disappear": A_DOOR_MUST_NOT_DISAPPEAR,
            "what_is_kept_includes_what_failed":
                WHAT_IS_KEPT_INCLUDES_WHAT_FAILED,
        },
    }

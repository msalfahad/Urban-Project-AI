"""E1.4 — every independently established fragment of an open region's edge.

THE DEFECT THIS REPLACES

Frozen E1.3 walks a boundary from the face the seed first meets and stops
where the drawing stops. That is right, and it is not complete. One walk
terminating proves only that THAT walk ran out; it proves nothing about
other stretches of wall belonging to the same open region.

PANTRY shows it. The frozen source-only observation, made before any
proposal existed, reports a wall on the north, a wall on the west, a
piered wall on the south, and an east side open toward DINING. The frozen
fragment record establishes essentially the west run and stops. So
COMPLETE_REGION_NOT_ESTABLISHED was handled honestly, while
ALL_INDEPENDENTLY_ESTABLISHED_BOUNDARY_FRAGMENTS were not recovered.

WHAT THIS DOES

For an open or partial candidate, search for further fragments and record
each one that CAD evidence establishes, separately, with its own two
terminations. Fragments are never joined to each other across anything
the drawing does not build.

HOW A SEARCH MAY BE DIRECTED, AND WHAT IT MAY NOT SUPPLY

The frozen source-only visual observation may act as a SEMANTIC SEARCH
HYPOTHESIS: "the north side is a physical wall" may send the search to
look north. It may not supply a coordinate, a length, an extent or a
shape. A fragment becomes established only when CAD evidence establishes
its exact geometry and its role, and a hypothesis that finds nothing is
recorded as having found nothing.
"""

from __future__ import annotations

import hashlib

MODEL = "ONE_WALK_RUNNING_OUT_IS_NOT_EVIDENCE_THAT_NOTHING_ELSE_IS_DRAWN_V1"

# --- fragment status -----------------------------------------------------
FRAGMENT_ESTABLISHED = "FRAGMENT_ESTABLISHED"
FRAGMENT_HYPOTHESISED_NOT_FOUND = "FRAGMENT_HYPOTHESISED_NOT_FOUND"
FRAGMENT_UNRESOLVED = "FRAGMENT_UNRESOLVED"

FRAGMENT_STATUSES = (FRAGMENT_ESTABLISHED, FRAGMENT_HYPOTHESISED_NOT_FOUND,
                     FRAGMENT_UNRESOLVED)

# --- how a fragment's end is terminated ---------------------------------
TERMINATES_AT_A_WALL_END = "TERMINATES_AT_A_WALL_END"
TERMINATES_AT_AN_UNCLASSIFIED_GAP = "TERMINATES_AT_AN_UNCLASSIFIED_GAP"
TERMINATES_AT_A_CLASSIFIED_PORTAL = "TERMINATES_AT_A_CLASSIFIED_PORTAL"
TERMINATES_WHERE_THE_ROLE_CHANGES = "TERMINATES_WHERE_THE_ROLE_CHANGES"
TERMINATES_AT_ANOTHER_FRAGMENT = "TERMINATES_AT_ANOTHER_FRAGMENT"
NO_VALID_CONTINUATION = "NO_VALID_CONTINUATION"

TERMINATIONS = (TERMINATES_AT_A_WALL_END, TERMINATES_AT_AN_UNCLASSIFIED_GAP,
                TERMINATES_AT_A_CLASSIFIED_PORTAL,
                TERMINATES_WHERE_THE_ROLE_CHANGES,
                TERMINATES_AT_ANOTHER_FRAGMENT, NO_VALID_CONTINUATION)

# --- what a hypothesis may and may not do -------------------------------
A_HYPOTHESIS_DIRECTS_A_SEARCH = (
    "a frozen source-only observation may say WHERE to look: which side "
    "of a candidate, and what kind of thing to look for. That is a "
    "search direction and nothing else")

A_HYPOTHESIS_OWNS_NO_COORDINATE = (
    "no coordinate, length, extent, thickness or shape may come from a "
    "visual observation. Every number in an established fragment comes "
    "from CAD. Where the search finds nothing, the hypothesis is recorded "
    "as unmet and no geometry is produced from it")

A_FRAGMENT_IS_NEVER_EXTENDED_ACROSS_AN_UNSUPPORTED_OPENING = (
    "a fragment stops where the drawing stops carrying it. It is never "
    "lengthened across a gap that nothing has classified, and two "
    "fragments are never joined into one because doing so would complete "
    "a region")

COMPLETENESS_IS_NOT_CLOSURE = (
    "recovering every established fragment of an open region's edge does "
    "not close the region and is not meant to. COMPLETE_PHYSICAL_REGION_"
    "STATUS and BOUNDARY_FRAGMENT_STATUS stay separate: a region may have "
    "every fragment recovered and still be open, and that is a complete "
    "answer")


def model_hash() -> str:
    parts = [MODEL] + list(FRAGMENT_STATUSES) + list(TERMINATIONS)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def hypothesis(candidate_id, side, expecting, *, source) -> dict:
    """A search direction taken from a frozen source-only observation."""
    return {
        "CANDIDATE_ID": candidate_id,
        "SIDE": side,
        "EXPECTING": expecting,
        "SOURCE": source,
        "a_hypothesis_directs_a_search": A_HYPOTHESIS_DIRECTS_A_SEARCH,
        "a_hypothesis_owns_no_coordinate": A_HYPOTHESIS_OWNS_NO_COORDINATE,
    }


def fragment(fragment_id, candidate_id, *, source_hypothesis, cad_entity_ids,
             interval_ids, ordered_geometry, semantic_role,
             boundary_capabilities, start_termination, end_termination,
             confidence, provenance) -> dict:
    """One fragment, established from CAD, with both of its ends named."""
    return {
        "FRAGMENT_ID": fragment_id,
        "CANDIDATE_ID": candidate_id,
        "FRAGMENT_STATUS": FRAGMENT_ESTABLISHED,
        "SOURCE_HYPOTHESIS": source_hypothesis,
        "CAD_ENTITY_IDS": list(cad_entity_ids),
        "INTERVAL_IDS": list(interval_ids),
        "ORDERED_GEOMETRY": [[round(float(x), 3), round(float(y), 3)]
                             for x, y in ordered_geometry],
        "SEMANTIC_ROLE": semantic_role,
        "BOUNDARY_CAPABILITIES": sorted(boundary_capabilities),
        "START_TERMINATION": start_termination,
        "END_TERMINATION": end_termination,
        "CONFIDENCE": confidence,
        "PROVENANCE": provenance,
        "a_hypothesis_owns_no_coordinate": A_HYPOTHESIS_OWNS_NO_COORDINATE,
        "never_extended_across_an_unsupported_opening":
            A_FRAGMENT_IS_NEVER_EXTENDED_ACROSS_AN_UNSUPPORTED_OPENING,
    }


def unmet(hypo, *, searched, why) -> dict:
    """A hypothesis the CAD did not support. Recorded, never filled in."""
    return {
        "FRAGMENT_ID": None,
        "CANDIDATE_ID": hypo["CANDIDATE_ID"],
        "FRAGMENT_STATUS": FRAGMENT_HYPOTHESISED_NOT_FOUND,
        "SOURCE_HYPOTHESIS": hypo,
        "what_was_searched": searched,
        "why": why,
        "no_geometry_was_produced": (
            "the observation said to look here and CAD established "
            "nothing. That is the finding; nothing was drawn from the "
            "observation to fill the gap"),
    }


def summarise(candidate_id, fragments, *, complete_region_status) -> dict:
    """The two statuses, side by side and not conflated."""
    est = [f for f in fragments if f["FRAGMENT_STATUS"] == FRAGMENT_ESTABLISHED]
    return {
        "CANDIDATE_ID": candidate_id,
        "COMPLETE_PHYSICAL_REGION_STATUS": complete_region_status,
        "BOUNDARY_FRAGMENT_STATUS": (
            "EVERY_ESTABLISHED_FRAGMENT_RECOVERED" if est
            else "NO_FRAGMENT_ESTABLISHED"),
        "established_fragment_count": len(est),
        "hypotheses_not_met": sum(
            1 for f in fragments
            if f["FRAGMENT_STATUS"] == FRAGMENT_HYPOTHESISED_NOT_FOUND),
        "completeness_is_not_closure": COMPLETENESS_IS_NOT_CLOSURE,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "FRAGMENT_STATUSES": list(FRAGMENT_STATUSES),
        "TERMINATIONS": list(TERMINATIONS),
        "why": {
            "a_hypothesis_directs_a_search": A_HYPOTHESIS_DIRECTS_A_SEARCH,
            "a_hypothesis_owns_no_coordinate":
                A_HYPOTHESIS_OWNS_NO_COORDINATE,
            "never_extended_across_an_unsupported_opening":
                A_FRAGMENT_IS_NEVER_EXTENDED_ACROSS_AN_UNSUPPORTED_OPENING,
            "completeness_is_not_closure": COMPLETENESS_IS_NOT_CLOSURE,
        },
    }

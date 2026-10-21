"""E1.4 — a visual finding blocks geometry only if it could change it.

THE DEFECT THIS REPLACES

Frozen E1.3 gated releases on the NAME of a challenge status. KITCHEN was
answered VISUALLY_CONSISTENT and carried, alongside it, the observation
COLUMN_EXPOSURE_UNRESOLVED - whose own stated reason was that the crop
cannot settle whether a black column is inside the wall band or projecting,
that it does not change the extent of the region, and that it is recorded
rather than a veto. E1.3 nonetheless mapped the status name into a
release-blocking physical finding and withheld the region.

A name is not an effect. "I cannot tell X" blocks geometry only when
knowing X would move the geometry.

WHAT THIS DOES

Every physical finding records what it affects: the chain elements it
touches, whether it could move the proposed boundary, and what it asks
for. Gating reads the effect, never the name. A finding that cannot move
the boundary is DIAGNOSTIC and is carried forward; one that can is
BLOCKING.

AND WHAT A WEAKER SOURCE CANNOT DO

A representation's inability to resolve something is not evidence against
a stronger one. CAD establishing an architectural finish face, and a
raster crop being unable to determine column exposure, is not a conflict:
it is one source silent where another speaks. A conflict needs the weaker
source to show something POSITIVE that the stronger reading cannot
accommodate. The two are recorded separately, and both remain
cross-representation corroboration of the same drawing family - never
independent truth about the building.
"""

from __future__ import annotations

import hashlib

MODEL = "A_FINDING_BLOCKS_GEOMETRY_ONLY_IF_IT_COULD_CHANGE_THAT_GEOMETRY_V1"

# --- what a finding does to the proposed boundary -----------------------
AFFECTS_YES = True
AFFECTS_NO = False
AFFECTS_UNRESOLVED = "unresolved"

BLOCKING = "BLOCKING"
DIAGNOSTIC = "DIAGNOSTIC"

EFFECTS = (BLOCKING, DIAGNOSTIC)

# --- what the visual source actually did --------------------------------
NO_VISUAL_EVIDENCE = "NO_VISUAL_EVIDENCE"
VISUAL_UNRESOLVED = "VISUAL_UNRESOLVED"
VISUAL_SUPPORT = "VISUAL_SUPPORT"
VISUAL_CONTRADICTION = "VISUAL_CONTRADICTION"

VISUAL_POSITIONS = (NO_VISUAL_EVIDENCE, VISUAL_UNRESOLVED, VISUAL_SUPPORT,
                    VISUAL_CONTRADICTION)

# Only a positive contradiction can challenge stronger source geometry.
MAY_CHALLENGE_STRONGER_SOURCE = (VISUAL_CONTRADICTION,)

# --- recommended actions -------------------------------------------------
RECORD_AND_CARRY_FORWARD = "RECORD_AND_CARRY_FORWARD"
WITHHOLD_UNTIL_RESOLVED = "WITHHOLD_UNTIL_RESOLVED"
HUMAN_REVIEW = "HUMAN_REVIEW"

ACTIONS = (RECORD_AND_CARRY_FORWARD, WITHHOLD_UNTIL_RESOLVED, HUMAN_REVIEW)

A_NAME_IS_NOT_AN_EFFECT = (
    "the words a reviewer chose from a vocabulary do not say what their "
    "observation does to the geometry. Gating on the word withheld a "
    "region whose reviewer had written, in the same answer, that the "
    "uncertainty does not change the region's extent. What a finding "
    "affects is recorded and is what gates")

UNRESOLVED_IS_NOT_CONTRADICTION = (
    "a weaker representation failing to resolve something is not evidence "
    "against a stronger one. CAD establishing a finish face while a raster "
    "crop cannot determine a column's exposure is one source silent where "
    "another speaks, not a disagreement. A conflict requires the weaker "
    "source to show something positive the stronger reading cannot hold")

SAME_DRAWING_FAMILY = (
    "the crop and the CAD are two representations of one drawing. "
    "Agreement between them is CROSS_REPRESENTATION_CORROBORATION. "
    "Neither is independent truth about what was built")

BOTH_INTERPRETATIONS_SAME_BOUNDARY = (
    "where an uncertainty has two readings and both leave the clear "
    "boundary in the same place, the uncertainty cannot move the "
    "geometry. It is recorded against the region and it does not withhold "
    "it")


def model_hash() -> str:
    parts = [MODEL] + list(EFFECTS) + list(VISUAL_POSITIONS) + list(ACTIONS)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def finding(name, *, evidence, confidence, affects_proposed_boundary,
            affected_chain_elements=(), visual_position=VISUAL_UNRESOLVED,
            why="", recommended_action=None) -> dict:
    """One physical finding, with its effect recorded rather than inferred."""
    affects = affects_proposed_boundary
    if affects is AFFECTS_YES:
        effect = BLOCKING
        action = recommended_action or WITHHOLD_UNTIL_RESOLVED
    elif affects is AFFECTS_NO:
        effect = DIAGNOSTIC
        action = recommended_action or RECORD_AND_CARRY_FORWARD
    else:
        # It is not known whether it could move the boundary. Not knowing
        # THAT is itself a reason to withhold: the geometry might move.
        effect = BLOCKING
        action = recommended_action or HUMAN_REVIEW
    return {
        "FINDING": name,
        "EVIDENCE": list(evidence),
        "CONFIDENCE": confidence,
        "AFFECTS_PROPOSED_BOUNDARY": affects,
        "AFFECTED_CHAIN_ELEMENTS": list(affected_chain_elements),
        "VISUAL_POSITION": visual_position,
        "EFFECT": effect,
        "RECOMMENDED_ACTION": action,
        "why": why,
        "a_name_is_not_an_effect": A_NAME_IS_NOT_AN_EFFECT,
        "same_drawing_family": SAME_DRAWING_FAMILY,
    }


def cross_representation(stronger_establishes, visual_position, *,
                         what) -> dict:
    """Whether the weaker source actually challenges the stronger one."""
    challenges = visual_position in MAY_CHALLENGE_STRONGER_SOURCE
    return {
        "WHAT": what,
        "STRONGER_SOURCE_ESTABLISHES": stronger_establishes,
        "VISUAL_POSITION": visual_position,
        "IS_A_CROSS_REPRESENTATION_CHALLENGE": challenges,
        "why": ("the weaker representation shows something positive that "
                "the stronger reading cannot accommodate" if challenges else
                "the weaker representation is silent or unresolved here, "
                "which is not evidence against the stronger source"),
        "unresolved_is_not_contradiction": UNRESOLVED_IS_NOT_CONTRADICTION,
        "same_drawing_family": SAME_DRAWING_FAMILY,
    }


def gate(findings) -> dict:
    """The release effect of a set of findings. Effects gate, names do not."""
    blocking = [f for f in findings if f["EFFECT"] == BLOCKING]
    diagnostic = [f for f in findings if f["EFFECT"] == DIAGNOSTIC]
    return {
        "COLD_VISUAL_FINDINGS_BLOCK_THE_GEOMETRY": bool(blocking),
        "blocking": [f["FINDING"] for f in blocking],
        "diagnostic_and_carried_forward": [f["FINDING"] for f in diagnostic],
        "why": ("; ".join(
            f"{f['FINDING']} could move the proposed boundary"
            f"{' at ' + ', '.join(map(str, f['AFFECTED_CHAIN_ELEMENTS'])) if f['AFFECTED_CHAIN_ELEMENTS'] else ''}"
            for f in blocking)
            or ("no finding could move the proposed boundary. Every "
                "finding is recorded and carried forward")),
        "a_name_is_not_an_effect": A_NAME_IS_NOT_AN_EFFECT,
        "both_interpretations_same_boundary":
            BOTH_INTERPRETATIONS_SAME_BOUNDARY,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "EFFECTS": list(EFFECTS),
        "VISUAL_POSITIONS": list(VISUAL_POSITIONS),
        "MAY_CHALLENGE_STRONGER_SOURCE": list(MAY_CHALLENGE_STRONGER_SOURCE),
        "ACTIONS": list(ACTIONS),
        "why": {
            "a_name_is_not_an_effect": A_NAME_IS_NOT_AN_EFFECT,
            "unresolved_is_not_contradiction": UNRESOLVED_IS_NOT_CONTRADICTION,
            "same_drawing_family": SAME_DRAWING_FAMILY,
            "both_interpretations_same_boundary":
                BOTH_INTERPRETATIONS_SAME_BOUNDARY,
        },
    }

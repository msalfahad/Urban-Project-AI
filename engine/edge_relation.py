"""E1.3 §2 — an edge relation, not a Boolean called "open".

E1.2's arbitration fell back to::

    visual_says_open = bool(v1_open_sides)

and Kitchen showed why that is unsafe. The cold source-only pass had
written, under OPEN_SIDES, that the main body of the kitchen continues
into its own southern leg with no wall between them. That is a true
observation about the INSIDE of one region. Collapsed to a Boolean it
became "this region is open to another region", which is a different
claim the pass never made.

A list is not a verdict. A side of a candidate stands in one of a small
number of RELATIONS to what lies beyond it, and the difference between
"no wall here because the space continues into itself" and "no wall here
because another space begins" is the whole question. So the observer
names the relation, and arbitration consumes the relation.
"""

from __future__ import annotations

import hashlib

MODEL = "AN_EDGE_HAS_A_RELATION_NOT_A_BOOLEAN_V1"

# ---------------------------------------------------------------- relations
PHYSICAL_BOUNDARY_WALL = "PHYSICAL_BOUNDARY_WALL"
PHYSICAL_BOUNDARY_DOOR_PORTAL = "PHYSICAL_BOUNDARY_DOOR_PORTAL"
PHYSICAL_BOUNDARY_OPEN_TO_OTHER_SPACE = "PHYSICAL_BOUNDARY_OPEN_TO_OTHER_SPACE"
INTERNAL_CONTINUITY_WITHIN_CANDIDATE = "INTERNAL_CONTINUITY_WITHIN_CANDIDATE"
FUNCTIONAL_SUBZONE_BOUNDARY_WITHOUT_WALL = (
    "FUNCTIONAL_SUBZONE_BOUNDARY_WITHOUT_WALL")
EXTERNAL_OPENING = "EXTERNAL_OPENING"
GLAZING = "GLAZING"
UNRESOLVED_EDGE_RELATION = "UNRESOLVED_EDGE_RELATION"

EDGE_RELATIONS = (
    PHYSICAL_BOUNDARY_WALL,
    PHYSICAL_BOUNDARY_DOOR_PORTAL,
    PHYSICAL_BOUNDARY_OPEN_TO_OTHER_SPACE,
    INTERNAL_CONTINUITY_WITHIN_CANDIDATE,
    FUNCTIONAL_SUBZONE_BOUNDARY_WITHOUT_WALL,
    EXTERNAL_OPENING,
    GLAZING,
    UNRESOLVED_EDGE_RELATION,
)

# Which relations describe a PHYSICAL boundary of the candidate against
# something outside it. The two that do not are the whole point of the
# vocabulary: they describe the candidate's own interior.
BOUNDS_THE_CANDIDATE_PHYSICALLY = (
    PHYSICAL_BOUNDARY_WALL,
    PHYSICAL_BOUNDARY_DOOR_PORTAL,
    PHYSICAL_BOUNDARY_OPEN_TO_OTHER_SPACE,
    EXTERNAL_OPENING,
    GLAZING,
)

# Relations that say a physical boundary is ABSENT here and another space
# begins. Only these may be read as "this candidate is physically open".
SAYS_THE_CANDIDATE_IS_PHYSICALLY_OPEN = (
    PHYSICAL_BOUNDARY_OPEN_TO_OTHER_SPACE,
)

# Relations that describe the candidate's own inside. A candidate is not
# open because of these, however many of them there are.
DESCRIBES_THE_INSIDE_OF_THE_CANDIDATE = (
    INTERNAL_CONTINUITY_WITHIN_CANDIDATE,
    FUNCTIONAL_SUBZONE_BOUNDARY_WITHOUT_WALL,
)

INTERNAL_CONTINUITY_IS_NOT_OPENNESS = (
    "a region whose own body continues round a corner, past a nib or into "
    "its own leg is one region with an interesting shape. Nothing has been "
    "said about what lies beyond it. Counting that as an open side makes a "
    "coherent L-shaped room report itself as leaking into its neighbour")

A_SUBZONE_IS_NOT_A_SEPARATOR = (
    "a line where a functional name might change, with no wall, no portal "
    "and no drawn separator, is a question about naming. It is not a "
    "physical boundary and it cannot make one appear")


def model_hash() -> str:
    return hashlib.sha256(
        "|".join([MODEL] + list(EDGE_RELATIONS)).encode("utf-8")
    ).hexdigest()[:24]


def relation_is_valid(relation: str) -> bool:
    return relation in EDGE_RELATIONS


def physically_open(relations) -> bool | None:
    """Is the candidate physically open, per the classified relations?

    True only when some edge is classified as opening onto ANOTHER space.
    False when every edge is classified and none of them is. None when
    nothing has been classified, or an edge relation is unresolved: an
    unclassified edge is not evidence of enclosure.
    """
    rels = [r for r in (relations or ()) if relation_is_valid(r)]
    if not rels:
        return None
    if any(r in SAYS_THE_CANDIDATE_IS_PHYSICALLY_OPEN for r in rels):
        return True
    if UNRESOLVED_EDGE_RELATION in rels:
        return None
    return False


def summarise(relations) -> dict:
    """Count the relations and say what they do and do not establish."""
    rels = list(relations or ())
    unknown = sorted({r for r in rels if not relation_is_valid(r)})
    counts = {r: rels.count(r) for r in EDGE_RELATIONS if r in rels}
    return {
        "MODEL": MODEL,
        "EDGE_RELATIONS_SEEN": counts,
        "not_a_relation_in_this_vocabulary": unknown,
        "PHYSICALLY_OPEN": physically_open(rels),
        "edges_bounding_the_candidate": sum(
            counts.get(r, 0) for r in BOUNDS_THE_CANDIDATE_PHYSICALLY),
        "edges_describing_its_own_inside": sum(
            counts.get(r, 0) for r in DESCRIBES_THE_INSIDE_OF_THE_CANDIDATE),
        "internal_continuity_is_not_openness":
            INTERNAL_CONTINUITY_IS_NOT_OPENNESS,
        "a_subzone_is_not_a_separator": A_SUBZONE_IS_NOT_A_SEPARATOR,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "EDGE_RELATIONS": list(EDGE_RELATIONS),
        "BOUNDS_THE_CANDIDATE_PHYSICALLY":
            list(BOUNDS_THE_CANDIDATE_PHYSICALLY),
        "SAYS_THE_CANDIDATE_IS_PHYSICALLY_OPEN":
            list(SAYS_THE_CANDIDATE_IS_PHYSICALLY_OPEN),
        "DESCRIBES_THE_INSIDE_OF_THE_CANDIDATE":
            list(DESCRIBES_THE_INSIDE_OF_THE_CANDIDATE),
        "why": {
            "internal_continuity_is_not_openness":
                INTERNAL_CONTINUITY_IS_NOT_OPENNESS,
            "a_subzone_is_not_a_separator": A_SUBZONE_IS_NOT_A_SEPARATOR,
        },
    }

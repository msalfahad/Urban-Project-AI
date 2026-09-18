"""E1.4 — what an interval's role lets it DO, asked one question at a time.

THE DEFECT THIS REPLACES

Frozen E1.2 and E1.3 carry a single Boolean per interval:

    MAY_BOUND_MATERIAL = (MATERIAL_WALL_FACE, GLAZING, COLUMN, POOL_CONTOUR)

One flag answered every engineering question at once, and POOL_CONTOUR was
inside it. Downstream, boundary_role_of() asked about SHAPE before it asked
about ROLE:

    if iv.kind in ("ARC", "CIRCLE"):
        return CURVED_MATERIAL_FACE

so the edge of a swimming pool, being an arc, became a curved MATERIAL WALL
FACE. Frozen E1.3 has about 31.57 m of boundary chain resting on intervals
whose own semantic role is POOL_CONTOUR. That number is evidence of the
failure class; it is not a target and nothing here is tuned to it.

WHAT REPLACES IT

A role says WHAT A THING IS. A capability says WHAT QUESTION IT CAN ANSWER.
They are different, and there is more than one question:

    can it bound a physical space at all?
    can it bound the clear floor region a surveyor measures?
    can it carry gross wall length?
    can it carry material wall length?
    can it host an opening?
    can it be the clear finish face?

A role grants some of those and not others. Glazing bounds a space and is
not masonry. A structural column exists whether or not it owns the finish
face. A door portal bounds topology and contributes no material. A pool
contour bounds the pool, and bounds no room.

CURVE SHAPE AND ENGINEERING ROLE ARE INDEPENDENT DIMENSIONS. A curved wall
is curved AND a wall; a pool edge is curved and is not a wall. Shape never
decides role, and role never flattens shape: exact curve geometry stays
first-class either way.
"""

from __future__ import annotations

import hashlib

from engine import interval_role as ir

MODEL = "A_ROLE_IS_WHAT_A_THING_IS_A_CAPABILITY_IS_WHAT_IT_CAN_ANSWER_V1"

# --- the capabilities, each a separate engineering question --------------
CAN_BOUND_PHYSICAL_SPACE = "CAN_BOUND_PHYSICAL_SPACE"
CAN_BOUND_CLEAR_FLOOR_REGION = "CAN_BOUND_CLEAR_FLOOR_REGION"
CAN_CONTRIBUTE_GROSS_WALL_LENGTH = "CAN_CONTRIBUTE_GROSS_WALL_LENGTH"
CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH = "CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH"
CAN_HOST_OPENING = "CAN_HOST_OPENING"
CAN_BE_CLEAR_FINISH_FACE = "CAN_BE_CLEAR_FINISH_FACE"
CAN_BOUND_POOL_WATER_REGION = "CAN_BOUND_POOL_WATER_REGION"

CAPABILITIES = (
    CAN_BOUND_PHYSICAL_SPACE,
    CAN_BOUND_CLEAR_FLOOR_REGION,
    CAN_CONTRIBUTE_GROSS_WALL_LENGTH,
    CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH,
    CAN_HOST_OPENING,
    CAN_BE_CLEAR_FINISH_FACE,
    CAN_BOUND_POOL_WATER_REGION,
)

THESE_ARE_DIMENSIONS_NOT_ANSWERS = (
    "each capability is a separate question about one interval. The table "
    "below says which questions a semantic role can answer at all. It does "
    "not say that a particular interval DOES answer them here: exposure, "
    "clear-face ownership and opening evidence are established per interval "
    "by their own passes, and a capability the role permits can still be "
    "withheld by them")

SHAPE_IS_NOT_A_ROLE = (
    "an arc is a shape. A wall, a pool edge, a door swing and a drafting "
    "annotation can all be drawn as one. Asking about the shape before "
    "asking about the role is how a pool contour became a curved material "
    "wall face. Role is established first and independently; the curve is "
    "then carried through exactly, whatever the role turned out to be")

# --- what each role is CAPABLE of ---------------------------------------
#
# Read a row as: this is the most this role could ever answer. Nothing here
# grants a capability to an interval whose own evidence does not support it.
_TABLE = {
    ir.MATERIAL_WALL_FACE: (
        CAN_BOUND_PHYSICAL_SPACE, CAN_BOUND_CLEAR_FLOOR_REGION,
        CAN_CONTRIBUTE_GROSS_WALL_LENGTH,
        CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH,
        CAN_HOST_OPENING, CAN_BE_CLEAR_FINISH_FACE),
    # glazing closes a space and is not masonry
    ir.GLAZING: (
        CAN_BOUND_PHYSICAL_SPACE, CAN_BOUND_CLEAR_FLOOR_REGION,
        CAN_CONTRIBUTE_GROSS_WALL_LENGTH,
        CAN_BE_CLEAR_FINISH_FACE),
    # a column exists as structure; whether it owns the finish face is a
    # separate question its own pass answers
    ir.COLUMN: (
        CAN_BOUND_PHYSICAL_SPACE, CAN_BOUND_CLEAR_FLOOR_REGION,
        CAN_CONTRIBUTE_GROSS_WALL_LENGTH,
        CAN_CONTRIBUTE_MATERIAL_WALL_LENGTH,
        CAN_BE_CLEAR_FINISH_FACE),
    ir.COLUMN_CANDIDATE_UNRESOLVED: (),
    ir.AMBIGUOUS_PAIRED_BAND: (),
    # the edge of the water bounds the pool, and bounds no room
    ir.POOL_CONTOUR: (CAN_BOUND_POOL_WATER_REGION,),
    ir.POOL_INTERNAL_GEOMETRY: (),
    ir.CASEWORK: (),
    ir.CABINET_FRONT: (),
    ir.COUNTER_EDGE: (),
    ir.FIXTURE: (),
    ir.FURNITURE: (),
    ir.STAIR_GEOMETRY: (),
    ir.DIMENSION_LINE: (),
    ir.DIMENSION_WITNESS: (),
    ir.CONSTRUCTION_LINE: (),
    # a door is evidence of an opening. It is not the wall it sits in and
    # it contributes no material
    ir.DOOR: (),
    ir.ANNOTATION: (),
    ir.LEVEL_OR_GRID_ANNOTATION: (),
    ir.UNKNOWN: (),
}

WHY_A_POOL_CONTOUR_BOUNDS_NO_ROOM = (
    "the line where the water stops is the boundary of the pool. It is not "
    "a wall face, it carries no wall length, no opening sits in it, and no "
    "room is bounded by it. It is kept, with its own capability, because "
    "the pool is a real region with a real edge")

WHY_A_DOOR_IS_NOT_A_WALL = (
    "a door leaf and its swing arc are evidence that an opening exists. "
    "They are not the wall the opening is in. A portal bounds topology and "
    "contributes zero material, and the leaf itself bounds nothing")


def model_hash() -> str:
    parts = [MODEL] + list(CAPABILITIES) + [
        f"{r}:{','.join(sorted(c))}" for r, c in sorted(_TABLE.items())]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def capabilities_of(role) -> tuple:
    """The most this semantic role could ever answer."""
    return tuple(_TABLE.get(role, ()))


def has(role, capability) -> bool:
    return capability in _TABLE.get(role, ())


def record(role) -> dict:
    """One interval's capability row, every question answered explicitly."""
    got = _TABLE.get(role)
    if got is None:
        return {
            "SEMANTIC_ENTITY_ROLE": role,
            "ROLE_IS_NOT_IN_THE_CAPABILITY_TABLE": True,
            "why": (
                "a role with no capability row is not silently given the "
                "capabilities of anything else. Every question is answered "
                "no, and the omission is reported"),
            **{c: False for c in CAPABILITIES},
        }
    return {
        "SEMANTIC_ENTITY_ROLE": role,
        **{c: (c in got) for c in CAPABILITIES},
        "these_are_dimensions_not_answers": THESE_ARE_DIMENSIONS_NOT_ANSWERS,
    }


def roles_missing_a_capability_row() -> tuple:
    return tuple(r for r in ir.ROLES if r not in _TABLE)


def assert_every_role_is_answered() -> None:
    missing = roles_missing_a_capability_row()
    if missing:
        raise ValueError(
            "every semantic role must have an explicit capability row, so "
            f"that none inherits another's: missing {sorted(missing)}")


def frozen_parameters() -> dict:
    assert_every_role_is_answered()
    return {
        "MODEL": MODEL,
        "CAPABILITIES": list(CAPABILITIES),
        "CAPABILITY_BY_SEMANTIC_ROLE": {
            r: sorted(c) for r, c in sorted(_TABLE.items())},
        "why": {
            "these_are_dimensions_not_answers":
                THESE_ARE_DIMENSIONS_NOT_ANSWERS,
            "shape_is_not_a_role": SHAPE_IS_NOT_A_ROLE,
            "a_pool_contour_bounds_no_room": WHY_A_POOL_CONTOUR_BOUNDS_NO_ROOM,
            "a_door_is_not_a_wall": WHY_A_DOOR_IS_NOT_A_WALL,
        },
    }

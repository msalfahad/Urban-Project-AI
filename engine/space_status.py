"""E1.3 §1, §3 — three layers, and E1 owns exactly one of them.

Kitchen made the confusion concrete. The cold passes agreed on every
physical fact: the ring follows drawn walls, the counter is excluded, the
outside door is a portal, and nothing crosses between the main body and
the southern leg. The challenge that withheld the room was a question
about NAMING - whether that leg would be called an entry lobby. A
functional subdivision with no physical separator was allowed to veto a
physical boundary, and a physically established room was lost to a
question E1 is not even permitted to answer.

    PHYSICAL_SPACE_GEOMETRY   what the drawing physically encloses
    FUNCTIONAL_ZONE_IDENTITY  what the resulting spaces are called
    TRADE_MEASUREMENT_ZONE    what a trade measures over them

E1 establishes the first. It may record what it does not know about the
second. It decides nothing at all about the third.
"""

from __future__ import annotations

import hashlib

MODEL = "PHYSICAL_GEOMETRY_AND_FUNCTIONAL_IDENTITY_ARE_DIFFERENT_QUESTIONS_V1"

PHYSICAL_SPACE_GEOMETRY = "PHYSICAL_SPACE_GEOMETRY"
FUNCTIONAL_ZONE_IDENTITY = "FUNCTIONAL_ZONE_IDENTITY"
TRADE_MEASUREMENT_ZONE = "TRADE_MEASUREMENT_ZONE"
LAYERS = (PHYSICAL_SPACE_GEOMETRY, FUNCTIONAL_ZONE_IDENTITY,
          TRADE_MEASUREMENT_ZONE)

E1_ESTABLISHES = (PHYSICAL_SPACE_GEOMETRY,)
E1_MAY_RECORD_UNCERTAINTY_ABOUT = (FUNCTIONAL_ZONE_IDENTITY,)
E1_DECIDES_NOTHING_ABOUT = (TRADE_MEASUREMENT_ZONE,)

# ------------------------------------------------- physical geometry status
ESTABLISHED_CLOSED = "ESTABLISHED_CLOSED"
ESTABLISHED_OPEN = "ESTABLISHED_OPEN"
PARTIAL_BOUNDARY_ESTABLISHED = "PARTIAL_BOUNDARY_ESTABLISHED"
BOUNDARY_CONFLICT = "BOUNDARY_CONFLICT"
PHYSICAL_UNRESOLVED = "UNRESOLVED"
PHYSICAL_GEOMETRY_STATUSES = (ESTABLISHED_CLOSED, ESTABLISHED_OPEN,
                              PARTIAL_BOUNDARY_ESTABLISHED,
                              BOUNDARY_CONFLICT, PHYSICAL_UNRESOLVED)

# Both of the first two are RESULTS. An established open region is not a
# failure to close; it is the drawing saying the room is open.
PHYSICAL_GEOMETRY_ESTABLISHED = (ESTABLISHED_CLOSED, ESTABLISHED_OPEN)

# ------------------------------------------------ functional identity status
IDENTITY_ESTABLISHED = "IDENTITY_ESTABLISHED"
MULTIPLE_FUNCTIONAL_ZONES_POSSIBLE = "MULTIPLE_FUNCTIONAL_ZONES_POSSIBLE"
FUNCTIONAL_SUBZONE_UNRESOLVED = "FUNCTIONAL_SUBZONE_UNRESOLVED"
IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
IDENTITY_UNRESOLVED = "UNRESOLVED"
FUNCTIONAL_IDENTITY_STATUSES = (IDENTITY_ESTABLISHED,
                                MULTIPLE_FUNCTIONAL_ZONES_POSSIBLE,
                                FUNCTIONAL_SUBZONE_UNRESOLVED,
                                IDENTITY_CONFLICT, IDENTITY_UNRESOLVED)

# NONE of these blocks physical geometry. That is the whole correction.
FUNCTIONAL_STATUS_NEVER_BLOCKS_PHYSICAL_GEOMETRY = (
    "a region may be geometrically established while what to call its "
    "parts is still open. The walls do not move when the argument about "
    "the name is settled, so the name cannot be a precondition for "
    "recording the walls")

# --------------------------------------- one physical region, several names
ONE_PHYSICAL_REGION = "ONE_PHYSICAL_REGION_MULTIPLE_FUNCTIONAL_ZONES"
PHYSICAL_REGION_RELATION_UNRESOLVED = "PHYSICAL_REGION_RELATION_UNRESOLVED"
SEPARATE_PHYSICAL_REGIONS = "SEPARATE_PHYSICAL_REGIONS"
REGION_RELATIONS = (ONE_PHYSICAL_REGION, SEPARATE_PHYSICAL_REGIONS,
                    PHYSICAL_REGION_RELATION_UNRESOLVED)

NOT_BY_PROXIMITY_AND_NOT_BY_DIFFERENCE = (
    "two labels near each other do not make one region, and two different "
    "labels do not make two. The relation is established by what physically "
    "separates them, or it is recorded as unresolved")

E1_DECIDES_NO_TRADE_ZONE = (
    "which surfaces a trade measures, where a floor finish changes and what "
    "counts as one room for pricing are decisions with their own evidence "
    "and their own authority. E1 supplies the physical geometry they are "
    "argued over and takes no part in the argument")


def model_hash() -> str:
    parts = ([MODEL] + list(LAYERS) + list(PHYSICAL_GEOMETRY_STATUSES)
             + list(FUNCTIONAL_IDENTITY_STATUSES) + list(REGION_RELATIONS))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def physical_status(*, chain, boundary_conflict=False,
                    any_material_established=True) -> dict:
    """Read the physical status off the boundary chain, nothing else."""
    if boundary_conflict:
        st, why = BOUNDARY_CONFLICT, (
            "two established readings of this boundary disagree about what "
            "was built, and the disagreement is not settled")
    elif not any_material_established or not chain["CHAIN"]:
        st, why = PHYSICAL_UNRESOLVED, (
            "no established material boundary was found around this point")
    elif chain["CLOSED_BY_DRAWN_MATERIAL"]:
        st, why = ESTABLISHED_CLOSED, (
            "drawn material closes this region, with every element of the "
            "ring carrying an established role")
    elif chain["length_with_no_material_mm"] > 0 and chain["runs"] >= 1:
        st, why = ESTABLISHED_OPEN, (
            "the drawing establishes material along part of this boundary "
            "and establishes that there is none along the rest. That is a "
            "result: the region is open")
    else:
        st, why = PARTIAL_BOUNDARY_ESTABLISHED, (
            "some of the boundary is established and the remainder is "
            "neither established as material nor established as open")
    return {
        "PHYSICAL_GEOMETRY_STATUS": st,
        "geometry_is_established": st in PHYSICAL_GEOMETRY_ESTABLISHED,
        "material_length_mm": chain.get("material_length_mm", 0.0),
        "length_with_no_material_mm":
            chain.get("length_with_no_material_mm", 0.0),
        "why": why,
    }


def functional_status(*, labels_inside=(), subzone_suggested=False,
                      separator_between_labels=None,
                      identity_conflict=False) -> dict:
    """What is known, and not known, about the naming. Never a blocker."""
    labels = sorted({x for x in labels_inside or ()})
    if identity_conflict:
        st, why = IDENTITY_CONFLICT, (
            "two established readings name this region differently and "
            "nothing settles which is right")
    elif len(labels) > 1:
        st, why = MULTIPLE_FUNCTIONAL_ZONES_POSSIBLE, (
            f"{len(labels)} labels sit inside one physical region: "
            + ", ".join(labels))
    elif subzone_suggested:
        st, why = FUNCTIONAL_SUBZONE_UNRESOLVED, (
            "a part of this region was read as possibly having a function "
            "of its own, with nothing physical separating it. Whether it is "
            "named separately is not settled here")
    elif labels:
        st, why = IDENTITY_ESTABLISHED, (
            f"one label, {labels[0]}, sits inside this physical region")
    else:
        st, why = IDENTITY_UNRESOLVED, "no label was established inside it"

    if separator_between_labels is True:
        rel = SEPARATE_PHYSICAL_REGIONS
    elif separator_between_labels is False and len(labels) > 1:
        rel = ONE_PHYSICAL_REGION
    elif len(labels) > 1:
        rel = PHYSICAL_REGION_RELATION_UNRESOLVED
    else:
        rel = None

    return {
        "FUNCTIONAL_IDENTITY_STATUS": st,
        "labels_inside": labels,
        "REGION_RELATION": rel,
        "blocks_physical_geometry": False,
        "why": why,
        "functional_status_never_blocks_physical_geometry":
            FUNCTIONAL_STATUS_NEVER_BLOCKS_PHYSICAL_GEOMETRY,
        "not_by_proximity_and_not_by_difference":
            NOT_BY_PROXIMITY_AND_NOT_BY_DIFFERENCE,
    }


def assert_no_trade_decision(record: dict) -> None:
    """E1 must not have decided anything in the trade layer."""
    banned = ("TRADE_MEASUREMENT_ZONE", "trade_zone", "finish_zone",
              "floor_finish", "skirting_zone", "boq", "BOQ", "rate",
              "quantity_m2", "area_m2_for_measurement")
    import json as _json
    blob = _json.dumps(record, default=str)
    hits = sorted({b for b in banned
                   if b in blob and b != "TRADE_MEASUREMENT_ZONE"})
    # the layer NAME may appear (it is named in order to be disclaimed);
    # a trade DECISION may not.
    if hits:
        raise AssertionError(
            f"a trade-layer decision appears in an E1 record: {hits}. "
            + E1_DECIDES_NO_TRADE_ZONE)


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "LAYERS": list(LAYERS),
        "E1_ESTABLISHES": list(E1_ESTABLISHES),
        "E1_MAY_RECORD_UNCERTAINTY_ABOUT":
            list(E1_MAY_RECORD_UNCERTAINTY_ABOUT),
        "E1_DECIDES_NOTHING_ABOUT": list(E1_DECIDES_NOTHING_ABOUT),
        "PHYSICAL_GEOMETRY_STATUSES": list(PHYSICAL_GEOMETRY_STATUSES),
        "PHYSICAL_GEOMETRY_ESTABLISHED": list(PHYSICAL_GEOMETRY_ESTABLISHED),
        "FUNCTIONAL_IDENTITY_STATUSES": list(FUNCTIONAL_IDENTITY_STATUSES),
        "REGION_RELATIONS": list(REGION_RELATIONS),
        "why": {
            "functional_status_never_blocks_physical_geometry":
                FUNCTIONAL_STATUS_NEVER_BLOCKS_PHYSICAL_GEOMETRY,
            "not_by_proximity_and_not_by_difference":
                NOT_BY_PROXIMITY_AND_NOT_BY_DIFFERENCE,
            "E1_decides_no_trade_zone": E1_DECIDES_NO_TRADE_ZONE,
        },
    }

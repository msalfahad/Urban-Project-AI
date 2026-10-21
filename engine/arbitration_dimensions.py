"""E1.3 §15 — witnesses can agree about one thing and differ about another.

E1.2 stored one ARBITRATION_STATE per candidate and made every
disagreement compete for it. Kitchen's record therefore read
A18_CONFIRMED while the thing actually in dispute - whether a leg of the
room has a function of its own - was invisible in that field and decided
the release somewhere else entirely.

Three questions are arbitrated separately because three different kinds
of evidence answer them:

    PHYSICAL_TOPOLOGY   is this region enclosed, and where is it open
    BOUNDARY_ROLE       is each boundary piece the thing it is called
    FUNCTIONAL_IDENTITY what are the resulting spaces called

The third never blocks the first. A physically confirmed enclosure whose
internal naming is unresolved is a valid, complete E1 result.
"""

from __future__ import annotations

import hashlib

from engine import edge_relation as er

MODEL = "ARBITRATION_IS_DIMENSIONED_NOT_ONE_OVERLOADED_VERDICT_V1"

PHYSICAL_TOPOLOGY_ARBITRATION = "PHYSICAL_TOPOLOGY_ARBITRATION"
BOUNDARY_ROLE_ARBITRATION = "BOUNDARY_ROLE_ARBITRATION"
FUNCTIONAL_IDENTITY_ARBITRATION = "FUNCTIONAL_IDENTITY_ARBITRATION"
DIMENSIONS = (PHYSICAL_TOPOLOGY_ARBITRATION, BOUNDARY_ROLE_ARBITRATION,
              FUNCTIONAL_IDENTITY_ARBITRATION)

# ------------------------------------------------------- topology states
TOPOLOGY_AGREED_CLOSED = "AGREED_CLOSED"
TOPOLOGY_AGREED_OPEN = "AGREED_OPEN"
TOPOLOGY_CAD_CORRECTED_A18 = "CAD_AND_VISUAL_CORRECTED_A18"
TOPOLOGY_A18_CORRECTED_CAD = "A18_AND_VISUAL_CORRECTED_CAD"
TOPOLOGY_PARTIALLY_AGREED = "AGREED_EXCEPT_AT_NAMED_EDGES"
TOPOLOGY_UNRESOLVED = "UNRESOLVED"
TOPOLOGY_STATES = (TOPOLOGY_AGREED_CLOSED, TOPOLOGY_AGREED_OPEN,
                   TOPOLOGY_CAD_CORRECTED_A18, TOPOLOGY_A18_CORRECTED_CAD,
                   TOPOLOGY_PARTIALLY_AGREED, TOPOLOGY_UNRESOLVED)

# --------------------------------------------------- boundary role states
ROLE_AGREED = "ROLE_AGREED"
ROLE_CHALLENGED_BY_VISUAL = "ROLE_CHALLENGED_BY_VISUAL"
ROLE_CHALLENGED_BY_CAD = "ROLE_CHALLENGED_BY_CAD"
ROLE_UNRESOLVED = "UNRESOLVED"
ROLE_STATES = (ROLE_AGREED, ROLE_CHALLENGED_BY_VISUAL,
               ROLE_CHALLENGED_BY_CAD, ROLE_UNRESOLVED)

# ----------------------------------------------------- identity states
IDENTITY_AGREED = "IDENTITY_AGREED"
IDENTITY_MULTIPLE_ZONES_POSSIBLE = "MULTIPLE_ZONES_POSSIBLE"
IDENTITY_CHALLENGED = "IDENTITY_CHALLENGED"
IDENTITY_UNRESOLVED = "UNRESOLVED"
IDENTITY_STATES = (IDENTITY_AGREED, IDENTITY_MULTIPLE_ZONES_POSSIBLE,
                   IDENTITY_CHALLENGED, IDENTITY_UNRESOLVED)

BLOCKS_PHYSICAL_RELEASE = (TOPOLOGY_UNRESOLVED,)
ROLE_BLOCKS_PHYSICAL_RELEASE = (ROLE_UNRESOLVED, ROLE_CHALLENGED_BY_VISUAL)

IDENTITY_NEVER_BLOCKS_PHYSICAL_RELEASE = (
    "no state in the identity dimension blocks physical geometry. It is "
    "recorded, it travels forward, and a later stage with the authority to "
    "name spaces resolves it")


def model_hash() -> str:
    parts = ([MODEL] + list(DIMENSIONS) + list(TOPOLOGY_STATES)
             + list(ROLE_STATES) + list(IDENTITY_STATES))
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def physical_topology(*, a18_says_open, cad_open, edge_relations=(),
                      unresolved_edges=(), v2_says_open_side_closed=False,
                      v2_says_wall_removed=False) -> dict:
    """Is it enclosed? Decided on structured edge relations, not a count."""
    visual_open = er.physically_open(edge_relations)
    notes = []
    if v2_says_open_side_closed:
        visual_open = True
        notes.append("the cold challenge says a side the drawing leaves "
                     "open has been given a built edge")
    elif v2_says_wall_removed:
        visual_open = False
        notes.append("the cold challenge says a drawn wall is missing from "
                     "the boundary")
    else:
        notes.append(
            "the cold source-only pass classified the edges; "
            + ("some edge opens onto another space"
               if visual_open is True else
               "no edge opens onto another space" if visual_open is False
               else "the edge relations do not settle it"))

    if unresolved_edges:
        state = TOPOLOGY_PARTIALLY_AGREED
        notes.append(f"{len(unresolved_edges)} edge(s) remain unclassified: "
                     + ", ".join(str(x) for x in sorted(unresolved_edges)))
    elif a18_says_open is None:
        state = (TOPOLOGY_UNRESOLVED if visual_open is None
                 else TOPOLOGY_AGREED_OPEN if visual_open
                 else TOPOLOGY_AGREED_CLOSED)
        notes.append("the frozen reading states no topology, so the CAD "
                     "evidence and the cold pass decide it between them")
    elif bool(a18_says_open) == bool(cad_open):
        state = TOPOLOGY_AGREED_OPEN if cad_open else TOPOLOGY_AGREED_CLOSED
        notes.append("the frozen reading and the CAD boundary agree")
    elif visual_open is True and a18_says_open:
        state = TOPOLOGY_A18_CORRECTED_CAD
        notes.append("the cold pass classifies an edge as opening onto "
                     "another space, with the frozen reading and against "
                     "the CAD boundary")
    elif visual_open is False and not a18_says_open:
        state = TOPOLOGY_CAD_CORRECTED_A18
        notes.append("the cold pass classifies no edge as opening onto "
                     "another space, with the CAD boundary and against the "
                     "frozen reading")
    elif visual_open is False and a18_says_open:
        state = TOPOLOGY_CAD_CORRECTED_A18
        notes.append("the CAD boundary is material and the cold pass sees "
                     "enclosure, so the frozen reading of an open side is "
                     "what was wrong")
    else:
        state = TOPOLOGY_UNRESOLVED
        notes.append("nothing independent settles which reading is right")

    return {
        "DIMENSION": PHYSICAL_TOPOLOGY_ARBITRATION,
        "STATE": state,
        "a18_says_open": a18_says_open,
        "cad_open": cad_open,
        "visual_says_physically_open": visual_open,
        "edge_relations": sorted(set(edge_relations or ())),
        "unresolved_edges": sorted(unresolved_edges or ()),
        "blocks_physical_release": state in BLOCKS_PHYSICAL_RELEASE,
        "notes": notes,
    }


def boundary_role(*, ambiguous_bands=(), unresolved_intervals=(),
                  v2_role_challenges=(), unresolved_gaps=()) -> dict:
    """Is each piece of the boundary the thing it is called?"""
    notes = []
    if v2_role_challenges:
        state = ROLE_CHALLENGED_BY_VISUAL
        notes.append("the cold challenge disputes what a boundary piece is: "
                     + ", ".join(sorted(v2_role_challenges)))
    elif ambiguous_bands:
        state = ROLE_CHALLENGED_BY_CAD
        notes.append(f"{len(ambiguous_bands)} band(s) on the boundary that "
                     "CAD itself cannot tell from a counter or a bar")
    elif unresolved_gaps:
        state = ROLE_UNRESOLVED
        notes.append(f"{len(unresolved_gaps)} gap(s) on the boundary whose "
                     "class is not established")
    elif unresolved_intervals:
        state = ROLE_UNRESOLVED
        notes.append(f"{len(unresolved_intervals)} boundary interval(s) "
                     "carry no established role")
    else:
        state = ROLE_AGREED
        notes.append("every boundary piece names an established role and "
                     "nothing disputes it")
    return {
        "DIMENSION": BOUNDARY_ROLE_ARBITRATION,
        "STATE": state,
        "ambiguous_bands": sorted(ambiguous_bands or ()),
        "unresolved_intervals": sorted(unresolved_intervals or ()),
        "unresolved_gaps": sorted(unresolved_gaps or ()),
        "v2_role_challenges": sorted(v2_role_challenges or ()),
        "blocks_physical_release": state in ROLE_BLOCKS_PHYSICAL_RELEASE,
        "notes": notes,
    }


def functional_identity(*, labels_inside=(), a18_identities=(),
                        v2_subzone_suggested=False,
                        v2_wrong_functional_region=False) -> dict:
    """What is it called? Recorded, forwarded, and never a blocker."""
    labels = sorted({x for x in labels_inside or ()})
    a18 = sorted({x for x in a18_identities or ()})
    notes = []
    if v2_wrong_functional_region:
        state = IDENTITY_CHALLENGED
        notes.append("the cold challenge disputes the identity assigned to "
                     "this region. That is a question about the name and "
                     "says nothing about the walls")
    elif len(labels) > 1:
        state = IDENTITY_MULTIPLE_ZONES_POSSIBLE
        notes.append(f"{len(labels)} labels inhabit one physical region: "
                     + ", ".join(labels))
    elif v2_subzone_suggested:
        state = IDENTITY_MULTIPLE_ZONES_POSSIBLE
        notes.append("the cold challenge reads a possible functional "
                     "subzone with no physical separator drawn across it")
    elif labels and a18 and not set(labels) & set(a18):
        state = IDENTITY_CHALLENGED
        notes.append("the CAD label and the frozen reading name this region "
                     "differently")
    elif labels:
        state = IDENTITY_AGREED
        notes.append(f"one established label: {labels[0]}")
    else:
        state = IDENTITY_UNRESOLVED
        notes.append("no label was established inside this region")
    return {
        "DIMENSION": FUNCTIONAL_IDENTITY_ARBITRATION,
        "STATE": state,
        "labels_inside": labels,
        "a18_identities": a18,
        "v2_subzone_suggested": bool(v2_subzone_suggested),
        "blocks_physical_release": False,
        "identity_never_blocks_physical_release":
            IDENTITY_NEVER_BLOCKS_PHYSICAL_RELEASE,
        "notes": notes,
    }


def arbitrate(*, topology_args, role_args, identity_args) -> dict:
    """All three dimensions, kept apart, in one record."""
    t = physical_topology(**topology_args)
    r = boundary_role(**role_args)
    i = functional_identity(**identity_args)
    return {
        "MODEL": MODEL,
        PHYSICAL_TOPOLOGY_ARBITRATION: t,
        BOUNDARY_ROLE_ARBITRATION: r,
        FUNCTIONAL_IDENTITY_ARBITRATION: i,
        "blocks_physical_release": bool(t["blocks_physical_release"]
                                        or r["blocks_physical_release"]),
        "dimensions_may_disagree": (
            "physical enclosure confirmed while functional subdivision "
            "stays unresolved is a valid outcome, and this record can say "
            "so because the two have their own fields"),
        "identity_never_blocks_physical_release":
            IDENTITY_NEVER_BLOCKS_PHYSICAL_RELEASE,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "DIMENSIONS": list(DIMENSIONS),
        "TOPOLOGY_STATES": list(TOPOLOGY_STATES),
        "ROLE_STATES": list(ROLE_STATES),
        "IDENTITY_STATES": list(IDENTITY_STATES),
        "BLOCKS_PHYSICAL_RELEASE": list(BLOCKS_PHYSICAL_RELEASE),
        "ROLE_BLOCKS_PHYSICAL_RELEASE": list(ROLE_BLOCKS_PHYSICAL_RELEASE),
        "why": {"identity_never_blocks_physical_release":
                IDENTITY_NEVER_BLOCKS_PHYSICAL_RELEASE},
    }

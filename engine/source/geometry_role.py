"""GEOMETRY ROLE ADMISSION (R8.8): what a canonical part IS, before any room topology is built.

Why
    The legacy room method consumed every curve in the region and tried to explain the resulting cells afterwards.
    Furniture, dimension graphics and door leaves then became walls, and a sheet frame became a room. Here a part
    reaches ROOM TOPOLOGY only when it is POSITIVELY admitted as topology-bearing; everything else is either
    positively excluded (furniture, fixtures, annotation, dimension graphics, sheet frame, opening symbols, stairs)
    or UNKNOWN, and unknown physical geometry BLOCKS the sites it touches (it is never silently ignored).

Evidence (never one kind alone)
    LAYER_ROLE          the effective layer's name tokens against a generic AEC lexicon (exact tokens, not
                        substrings; a bound-xref prefix "<xref>$n$" is the DWG binding convention and is split off;
                        a layer-0 child takes the layer of the insert that places it - ByLayer)
    BLOCK_NAME_ROLE     the innermost block's name tokens (presentation metadata: corroboration only)
    INSTANCE_CONTEXT    MODEL_SPACE | SYMBOL_OCCURRENCE | SHEET_FRAME_OCCURRENCE (the selected region's own frame
                        occurrence, named by an owner-confirmed region claim)
    BLOCK_DEFINITION    what one top-level symbol occurrence contains: NO_BOUNDARY_LAYER (none of its parts is on
                        a wall / column / glazing layer) and DOOR_SIGNATURE (a circular swing whose open end meets a
                        straight leaf part of the same occurrence)
    ENTITY_TYPE         the source entity type (LINE, LWPOLYLINE, ARC, CIRCLE, ELLIPSE)

    A rule names the combination it needs (ROLE_RULES). Layer alone, a block name alone, a visual guess, a size or
    a substring never decide a role. The strength of an assignment is recorded: STRUCTURAL (block identity /
    occurrence structure is part of the evidence) or CORROBORATED (layer role + entity type + instance context).

Project-agnostic: the lexicon is generic AEC vocabulary; no project, file or person names; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field

from . import canonical_input as CI

# ---------------------------------------------------------------- roles
TOPOLOGY_BOUNDARY = "TOPOLOGY_BOUNDARY"              # wall face line
STRUCTURAL_OBSTACLE = "STRUCTURAL_OBSTACLE"          # column outline (bounds the floor, admitted)
GLAZING_BOUNDARY = "GLAZING_BOUNDARY"                # window / glazing line closing a wall opening (admitted)
OPENING_SYMBOL = "OPENING_SYMBOL"                    # door leaf, swing, frame: never a wall; supplies closures
OPENING_BOUNDARY = "OPENING_BOUNDARY"                # virtual closure derived from a proven opening (topology only)
FURNITURE = "FURNITURE"
SANITARY_FIXTURE = "SANITARY_FIXTURE"
STAIR_GEOMETRY = "STAIR_GEOMETRY"                    # physical, not a room boundary; marks the site it lies in
LIFT_GEOMETRY = "LIFT_GEOMETRY"
ANNOTATION_GRAPHICS = "ANNOTATION_GRAPHICS"
DIMENSION_GRAPHICS = "DIMENSION_GRAPHICS"
SHEET_FRAME = "SHEET_FRAME"
TITLE_BLOCK = "TITLE_BLOCK"
PRESENTATION_OVERHEAD = "PRESENTATION_OVERHEAD"      # hidden / overhead lines: above or below the cut plane
UNKNOWN_PHYSICAL = "UNKNOWN_PHYSICAL"
UNKNOWN_PRESENTATION = "UNKNOWN_PRESENTATION"
BOUNDARY_CURVE_UNSUPPORTED = "BOUNDARY_CURVE_UNSUPPORTED"  # a boundary-layer curve the topology cannot node

ROLES = (TOPOLOGY_BOUNDARY, STRUCTURAL_OBSTACLE, GLAZING_BOUNDARY, OPENING_SYMBOL, OPENING_BOUNDARY, FURNITURE,
         SANITARY_FIXTURE, STAIR_GEOMETRY, LIFT_GEOMETRY, ANNOTATION_GRAPHICS, DIMENSION_GRAPHICS, SHEET_FRAME,
         TITLE_BLOCK, PRESENTATION_OVERHEAD, UNKNOWN_PHYSICAL, UNKNOWN_PRESENTATION, BOUNDARY_CURVE_UNSUPPORTED)

# ROOM TOPOLOGY consumes exactly these (OPENING_BOUNDARY is derived, never a source part)
TOPOLOGY_ADMITTED = (TOPOLOGY_BOUNDARY, STRUCTURAL_OBSTACLE, GLAZING_BOUNDARY, OPENING_BOUNDARY)
# positively not topology-bearing: excluded without blocking
TOPOLOGY_EXCLUDED = (OPENING_SYMBOL, FURNITURE, SANITARY_FIXTURE, STAIR_GEOMETRY, LIFT_GEOMETRY, ANNOTATION_GRAPHICS,
                     DIMENSION_GRAPHICS, SHEET_FRAME, TITLE_BLOCK, PRESENTATION_OVERHEAD)
# block every site they touch
TOPOLOGY_BLOCKING = (UNKNOWN_PHYSICAL, UNKNOWN_PRESENTATION, BOUNDARY_CURVE_UNSUPPORTED)

STRUCTURAL, CORROBORATED, NONE = "STRUCTURAL", "CORROBORATED", "NONE"

# ---------------------------------------------------------------- generic lexicon (exact tokens)
LAYER_LEXICON = {
    "WALL": ("WALL", "WALLS", "MUR"),
    "COLUMN": ("COL", "COLS", "COLUMN", "COLUMNS"),
    "GLAZING": ("WINDOW", "WINDOWS", "WIN", "GLAZ", "GLAZING", "GLASS", "CURTAINWALL"),
    "DOOR": ("DOOR", "DOORS"),
    "FURNITURE": ("FURN", "FURNI", "FURNITURE"),
    "FIXTURE": ("FIXTURE", "FIXTURES", "SANITARY", "PLUMBING", "PLUMB"),
    "STAIR": ("STAIR", "STAIRS", "STAIRCASE"),
    "LIFT": ("LIFT", "LIFTS", "ELEVATOR", "ELEV"),
    "DIMENSION": ("DIM", "DIMS", "DIMENSION", "DIMENSIONS"),
    "ANNOTATION": ("TEXT", "TEXTS", "NOTE", "NOTES", "ANNO", "ANNOTATION", "ARROW", "LEADER", "TAG", "LABEL", "SYMB"),
    "SHEET_FRAME": ("FRAME", "BORDER", "TITLE", "TITLEBLOCK", "SHEET"),
    "HIDDEN_LINE": ("HIDDEN", "OVERHEAD", "ABOVE"),
    "NON_PLOT": ("DEFPOINTS",),
}
BLOCK_LEXICON = {
    "FURNITURE": ("BED", "SOFA", "COUCH", "CHAIR", "ARMCHAIR", "TABLE", "DESK", "WARDROBE", "CABINET", "BENCH",
                  "DRESSER", "NIGHTSTAND", "BOOKCASE", "SHELF", "SHELVES", "TV", "RUG", "CARPET", "PLANT"),
    "SANITARY": ("WC", "TOILET", "BASIN", "WASHBASIN", "SINK", "LAVATORY", "SHOWER", "BATHTUB", "TUB", "BIDET",
                 "URINAL"),
    "DOOR": ("DOOR", "DOORS"),
}
BOUNDARY_LAYER_ROLES = ("WALL", "COLUMN", "GLAZING")
_BIND = re.compile(r"^(.*?)\$\d+\$(.*)$")


def tokens(name):
    """Exact name tokens: the bound-xref prefix "<xref>$n$" is split off (DWG bind convention), the rest is split
    on non-alphanumerics, and trailing digits are dropped from each token ("ARROW2" -> "ARROW")."""
    if not name:
        return ()
    n = str(name).upper()
    m = _BIND.match(n)
    local = m.group(2) if m else n
    out = []
    for t in re.split(r"[^A-Z0-9]+", local):
        t = re.sub(r"\d+$", "", t)
        if t:
            out.append(t)
    return tuple(out)


def _lex(name, lexicon):
    found = sorted({role for role, words in lexicon.items() for t in tokens(name) if t in words})
    return found[0] if len(found) == 1 else (None if not found else "CONFLICT:" + "+".join(found))


def layer_role(name):
    return _lex(name, LAYER_LEXICON)


def block_name_role(name):
    return _lex(name, BLOCK_LEXICON)


# ---------------------------------------------------------------- the rules (frozen data)
ROLE_RULES = (
    {"id": "GR-01", "role": SHEET_FRAME, "strength": STRUCTURAL,
     "requires": "INSTANCE_CONTEXT=SHEET_FRAME_OCCURRENCE (the region's own frame occurrence, by block identity)"},
    {"id": "GR-02", "role": OPENING_SYMBOL, "strength": STRUCTURAL,
     "requires": "INSTANCE_CONTEXT=SYMBOL_OCCURRENCE + BLOCK_DEFINITION=DOOR_SIGNATURE + LAYER_ROLE=DOOR on the "
                 "occurrence (or BLOCK_NAME_ROLE=DOOR)"},
    {"id": "GR-03", "role": FURNITURE, "strength": STRUCTURAL,
     "requires": "INSTANCE_CONTEXT=SYMBOL_OCCURRENCE + BLOCK_DEFINITION=NO_BOUNDARY_LAYER + (LAYER_ROLE=FURNITURE or "
                 "BLOCK_NAME_ROLE=FURNITURE)"},
    {"id": "GR-04", "role": SANITARY_FIXTURE, "strength": STRUCTURAL,
     "requires": "INSTANCE_CONTEXT=SYMBOL_OCCURRENCE + BLOCK_DEFINITION=NO_BOUNDARY_LAYER + (LAYER_ROLE=FIXTURE or "
                 "BLOCK_NAME_ROLE=SANITARY)"},
    {"id": "GR-05", "role": TOPOLOGY_BOUNDARY, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=WALL + INSTANCE_CONTEXT=MODEL_SPACE + ENTITY_TYPE in {LINE, LWPOLYLINE, ARC, CIRCLE}"},
    {"id": "GR-06", "role": STRUCTURAL_OBSTACLE, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=COLUMN + INSTANCE_CONTEXT=MODEL_SPACE + ENTITY_TYPE in {LINE, LWPOLYLINE, ARC, CIRCLE}"},
    {"id": "GR-07", "role": GLAZING_BOUNDARY, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=GLAZING + INSTANCE_CONTEXT=MODEL_SPACE + ENTITY_TYPE in {LINE, LWPOLYLINE, ARC}"},
    {"id": "GR-08", "role": BOUNDARY_CURVE_UNSUPPORTED, "strength": CORROBORATED,
     "requires": "LAYER_ROLE in {WALL, COLUMN, GLAZING} + ENTITY_TYPE=ELLIPSE (or an elliptical realisation)"},
    {"id": "GR-09", "role": FURNITURE, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=FURNITURE + INSTANCE_CONTEXT=MODEL_SPACE"},
    {"id": "GR-10", "role": SANITARY_FIXTURE, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=FIXTURE + INSTANCE_CONTEXT=MODEL_SPACE"},
    {"id": "GR-11", "role": STAIR_GEOMETRY, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=STAIR + INSTANCE_CONTEXT=MODEL_SPACE"},
    {"id": "GR-12", "role": LIFT_GEOMETRY, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=LIFT + INSTANCE_CONTEXT=MODEL_SPACE"},
    {"id": "GR-13", "role": DIMENSION_GRAPHICS, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=DIMENSION (any context)"},
    {"id": "GR-14", "role": ANNOTATION_GRAPHICS, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=ANNOTATION (any context)"},
    {"id": "GR-15", "role": SHEET_FRAME, "strength": CORROBORATED,
     "requires": "LAYER_ROLE=SHEET_FRAME + INSTANCE_CONTEXT=MODEL_SPACE"},
    {"id": "GR-16", "role": PRESENTATION_OVERHEAD, "strength": CORROBORATED,
     "requires": "LAYER_ROLE in {HIDDEN_LINE, NON_PLOT}"},
    {"id": "GR-99", "role": UNKNOWN_PHYSICAL, "strength": NONE,
     "requires": "no rule above holds: unknown physical geometry (blocks every site it touches)"},
)
POLICY_ID = "GEOMETRY_ROLE_EVIDENCE_POLICY_V1"


def policy_record() -> dict:
    rec = {"id": POLICY_ID, "rules": list(ROLE_RULES), "layer_lexicon": {k: list(v) for k, v in LAYER_LEXICON.items()},
           "block_lexicon": {k: list(v) for k, v in BLOCK_LEXICON.items()},
           "admitted_to_room_topology": list(TOPOLOGY_ADMITTED), "excluded": list(TOPOLOGY_EXCLUDED),
           "blocking": list(TOPOLOGY_BLOCKING),
           "never_alone": ["layer name", "block name", "visual guess", "geometry size", "name substring"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec


@dataclass(frozen=True)
class RoleAssignment:
    part_key: str | None
    role: str
    strength: str
    rule_id: str
    evidence: dict = field(default_factory=dict)


# ---------------------------------------------------------------- per-occurrence structure
def _occurrence(part):
    path = part.identity.instance_handles or ()
    return ("I" + path[0]) if path else ("E" + str(part.identity.source_handle))


def _conic(part):
    """(centre, radius, start point, end point, sweep) of a circular swing; None if not circular."""
    g = part.geometry
    if part.kind == "ARC":
        cx, cy, r, a0, a1 = g
        sweep = (a1 - a0) % (2 * math.pi)
        return (cx, cy), r, (cx + r * math.cos(a0), cy + r * math.sin(a0)), (cx + r * math.cos(a1), cy + r * math.sin(a1)), sweep
    if part.kind == "ELLIPTICAL_ARC":
        cx, cy, ux, uy, vx, vy, t0, t1 = g
        ru, rv = math.hypot(ux, uy), math.hypot(vx, vy)
        if ru == 0 or abs(ru - rv) > 1e-9 * ru or abs(ux * vx + uy * vy) > 1e-9 * ru * rv:
            return None                                   # a true ellipse: not a circular swing
        p = lambda t: (cx + ux * math.cos(t) + vx * math.sin(t), cy + uy * math.cos(t) + vy * math.sin(t))
        return (cx, cy), ru, p(t0), p(t1), abs(t1 - t0)
    return None


def door_signature(parts, eps=None):
    """DOOR_SIGNATURE of one occurrence: exactly ONE circular swing curve (ARC, or an elliptical realisation with
    equal perpendicular semi-diameters) sweeping less than pi. Returns its hinge (centre), radius and both end
    points, or None. Which end is the closed leaf is NOT guessed here: the opening closure (topology) tries both and
    accepts exactly one that lands on admitted walls at both ends, or reports the opening unresolved."""
    swings = [(p, _conic(p)) for p in parts if p.kind in ("ARC", "ELLIPTICAL_ARC")]
    swings = [(p, c) for p, c in swings if c is not None and 0.0 < c[4] < math.pi]
    if len(swings) != 1:
        return None
    sp, (c, r, a, b, sweep) = swings[0]
    return {"swing_part": sp.identity.key, "hinge": c, "radius": r, "ends": (a, b), "sweep_rad": sweep}


# ---------------------------------------------------------------- admission
def admit(inp: CI.CanonicalMeasurementInput, *, frame_insert: str | None, eps: float,
          insert_layers: dict | None = None) -> dict:
    """{part key: RoleAssignment} for every VISIBLE part of the input, plus the door occurrences found.

    frame_insert   the top-level insert occurrence of the region's sheet frame (owner-confirmed region claim)
    eps            coincidence tolerance (the frozen numeric tolerance of the topology policy)
    insert_layers  {top-level insert handle: insert layer} for ByLayer of layer-0 children (optional)"""
    insert_layers = insert_layers or {}
    occ = {}
    for p in inp.parts:
        if p.visibility == CI.VISIBLE:
            occ.setdefault(_occurrence(p), []).append(p)
    occ_info = {}
    for o, ps in occ.items():
        if not o.startswith("I"):
            continue
        roles_in = {layer_role(_eff(p, insert_layers)) for p in ps}
        info = {"no_boundary_layer": not (roles_in & set(BOUNDARY_LAYER_ROLES)),
                "layer_roles": sorted(r for r in roles_in if r),
                "block_name": ps[0].lineage[-1].block_name if ps[0].lineage else None,
                "door_signature": None}
        if "DOOR" in roles_in or block_name_role(info["block_name"]) == "DOOR":
            info["door_signature"] = door_signature(ps)
        occ_info[o] = info
    out = {}
    for o, ps in occ.items():
        for p in ps:
            a = _assign(p, o, occ_info.get(o), frame_insert, insert_layers)
            out[p.identity.key] = a
    doors = {o: i["door_signature"] for o, i in occ_info.items() if i["door_signature"] is not None}
    return {"roles": out, "doors": doors, "occurrences": occ_info, "policy": POLICY_ID}


def _eff(p, insert_layers):
    if p.layer == "0" and p.identity.instance_handles:
        return insert_layers.get(p.identity.instance_handles[0], p.layer)
    return p.layer


def _assign(p, occ_id, info, frame_insert, insert_layers) -> RoleAssignment:
    key = p.identity.key
    lay = _eff(p, insert_layers)
    lr = layer_role(lay)
    path = p.identity.instance_handles or ()
    ctx = ("SHEET_FRAME_OCCURRENCE" if (path and frame_insert is not None and path[0] == frame_insert)
           else "SYMBOL_OCCURRENCE" if path else "MODEL_SPACE")
    bname = p.lineage[-1].block_name if p.lineage else None
    br = block_name_role(bname) if path else None
    etype = p.entity_type
    ev = {"LAYER_ROLE": lr, "layer": lay, "INSTANCE_CONTEXT": ctx, "BLOCK_NAME_ROLE": br, "ENTITY_TYPE": etype,
          "KIND": p.kind}
    if info is not None:
        ev["BLOCK_DEFINITION"] = {"NO_BOUNDARY_LAYER": info["no_boundary_layer"],
                                  "DOOR_SIGNATURE": info["door_signature"] is not None}
    linear = etype in ("LINE", "LWPOLYLINE", "ARC", "CIRCLE") and p.kind in ("SEGMENT", "ARC", "CIRCLE")

    def r(role, rid, strength):
        return RoleAssignment(key, role, strength, rid, ev)
    if ctx == "SHEET_FRAME_OCCURRENCE":
        return r(SHEET_FRAME, "GR-01", STRUCTURAL)
    if ctx == "SYMBOL_OCCURRENCE" and info is not None:
        if info["door_signature"] is not None and ("DOOR" in info["layer_roles"] or br == "DOOR"):
            return r(OPENING_SYMBOL, "GR-02", STRUCTURAL)
        if info["no_boundary_layer"] and (lr == "FURNITURE" or br == "FURNITURE"):
            return r(FURNITURE, "GR-03", STRUCTURAL)
        if info["no_boundary_layer"] and (lr == "FIXTURE" or br == "SANITARY"):
            return r(SANITARY_FIXTURE, "GR-04", STRUCTURAL)
    if lr in BOUNDARY_LAYER_ROLES and (etype == "ELLIPSE" or p.kind == "ELLIPTICAL_ARC"):
        return r(BOUNDARY_CURVE_UNSUPPORTED, "GR-08", CORROBORATED)
    if ctx == "MODEL_SPACE" and linear:
        if lr == "WALL":
            return r(TOPOLOGY_BOUNDARY, "GR-05", CORROBORATED)
        if lr == "COLUMN":
            return r(STRUCTURAL_OBSTACLE, "GR-06", CORROBORATED)
        if lr == "GLAZING" and p.kind != "CIRCLE":
            return r(GLAZING_BOUNDARY, "GR-07", CORROBORATED)
    if ctx == "MODEL_SPACE":
        if lr == "FURNITURE":
            return r(FURNITURE, "GR-09", CORROBORATED)
        if lr == "FIXTURE":
            return r(SANITARY_FIXTURE, "GR-10", CORROBORATED)
        if lr == "STAIR":
            return r(STAIR_GEOMETRY, "GR-11", CORROBORATED)
        if lr == "LIFT":
            return r(LIFT_GEOMETRY, "GR-12", CORROBORATED)
        if lr == "SHEET_FRAME":
            return r(SHEET_FRAME, "GR-15", CORROBORATED)
    if lr == "DIMENSION":
        return r(DIMENSION_GRAPHICS, "GR-13", CORROBORATED)
    if lr == "ANNOTATION":
        return r(ANNOTATION_GRAPHICS, "GR-14", CORROBORATED)
    if lr in ("HIDDEN_LINE", "NON_PLOT"):
        return r(PRESENTATION_OVERHEAD, "GR-16", CORROBORATED)
    return r(UNKNOWN_PHYSICAL, "GR-99", NONE)

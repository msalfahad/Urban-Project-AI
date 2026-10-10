"""Four-layer measurement model in code (PA05 §10):

A PHYSICAL_GEOMETRY -> B TOPOLOGICAL_RELATION -> C TRADE_MEASUREMENT_REGION -> D TRADE_QUANTITY.

A synthetic closure is a measurement object with MATERIAL_PRESENT = False,
PHYSICAL_WALL = False, GEOMETRY_AUTHORITY = False, REVERSIBLE = True; the
physical layer's hash is identical before and after closures are applied
and removed, and CI proves it.
"""

from __future__ import annotations

import copy
import hashlib
import json

from engine.ingest import ids

TRADE_RULES = {
    # trade -> how an opening site of each class is treated in the measurement region
    "FLOOR": {"CONFIRMED_DOOR_OPENING": "VIRTUAL_CLOSURE", "OPEN_PASSAGE": "VIRTUAL_CLOSURE", "UNRESOLVED_OPENING_SITE": "VIRTUAL_CLOSURE_PROVISIONAL", "CONFIRMED_GLAZED_SEPARATOR": "VIRTUAL_CLOSURE", "CONFIRMED_WINDOW_OPENING": "N/A"},
    "WALL_PLASTER": {"CONFIRMED_DOOR_OPENING": "GROSS_CONTINUITY_WITH_DEDUCTION", "OPEN_PASSAGE": "NO_WALL", "UNRESOLVED_OPENING_SITE": "NO_WALL_PROVISIONAL", "CONFIRMED_GLAZED_SEPARATOR": "NO_WALL", "CONFIRMED_WINDOW_OPENING": "GROSS_CONTINUITY_WITH_DEDUCTION"},
    "WALL_CERAMIC": {"CONFIRMED_DOOR_OPENING": "HOST_WALLS_ONLY", "OPEN_PASSAGE": "HOST_WALLS_ONLY", "UNRESOLVED_OPENING_SITE": "HOST_WALLS_ONLY", "CONFIRMED_GLAZED_SEPARATOR": "HOST_WALLS_ONLY", "CONFIRMED_WINDOW_OPENING": "HOST_WALLS_ONLY"},
    "WATERPROOFING": {"CONFIRMED_DOOR_OPENING": "RULE_DEPENDENT_THRESHOLD", "OPEN_PASSAGE": "RULE_DEPENDENT_THRESHOLD", "UNRESOLVED_OPENING_SITE": "RULE_DEPENDENT_THRESHOLD", "CONFIRMED_GLAZED_SEPARATOR": "VIRTUAL_CLOSURE", "CONFIRMED_WINDOW_OPENING": "N/A"},
}
CLOSURE_STAMP = {"MATERIAL_PRESENT": False, "PHYSICAL_WALL": False, "GEOMETRY_AUTHORITY": False, "REVERSIBLE": True, "LAYER": "C_TRADE_MEASUREMENT_REGION"}


def physical_hash(spaces, faces):
    """Hash of the physical layer (A) only: space boundaries, faces, site classes; closures are not part of it."""
    body = {"SPACES": [{k: s[k] for k in ("PHYSICAL_SPACE_ID", "BOUNDARY_CHAIN", "WALL_BOUNDARY_LM", "OPENING_SITES", "OPEN_EDGES")} for s in spaces],
            "FACES": [{k: f[k] for k in ("FACE_ID", "DEVELOPED_LENGTH_MM", "GEOMETRY")} for f in faces]}
    return hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()


def closures_for(space, sites_by_id, trade):
    rules = TRADE_RULES[trade]
    out = []
    for rel in space["OPENING_SITES"]:
        s = sites_by_id[rel["OPENING_SITE_ID"]]
        treatment = rules.get(s["CLASS"], "N/A")
        out.append(dict(CLOSURE_STAMP, CLOSURE_ID=ids.closure_id(space["VIEW"], s["OPENING_SITE_ID"], trade), TRADE=trade, OPENING_SITE_ID=s["OPENING_SITE_ID"],
                        SITE_CLASS=s["CLASS"], TREATMENT=treatment, SPAN_MM=s["SPAN_MM"], CHORD_MM=s["CHORD_MM"],
                        STATUS="PROVISIONAL" if treatment.endswith("PROVISIONAL") or treatment == "RULE_DEPENDENT_THRESHOLD" else "SOURCE_ESTABLISHED"))
    return out


def build_region(space, sites_by_id, trade):
    """Layer C region for one space and trade: the physical boundary plus closures; the physical record is deep-copied, never edited."""
    cl = closures_for(space, sites_by_id, trade)
    region = {"TRADE_MEASUREMENT_REGION_ID": ids.make_id("TRADE_ZONE", space["PHYSICAL_SPACE_ID"], trade), "TRADE": trade, "PHYSICAL_SPACE_ID": space["PHYSICAL_SPACE_ID"],
              "PHYSICAL_EDGES": copy.deepcopy(space["BOUNDARY_CHAIN"]), "VIRTUAL_CLOSURES": cl, "OPEN_EDGES": copy.deepcopy(space["OPEN_EDGES"]),
              "FORMED": not space["OPEN_EDGES"] and not space["UNRESOLVED_EDGES"], "LAYER": "C_TRADE_MEASUREMENT_REGION"}
    return region


def remove_closures(region):
    """Reversibility: strip the closures and return what the physical layer contributed."""
    return {"PHYSICAL_EDGES": region["PHYSICAL_EDGES"], "OPEN_EDGES": region["OPEN_EDGES"]}


def prove_reversible(spaces, faces, sites, trades=("FLOOR", "WALL_PLASTER", "WALL_CERAMIC", "WATERPROOFING")):
    """Build every region, remove closures, and prove the physical layer hash is unchanged."""
    before = physical_hash(spaces, faces)
    by = {s["OPENING_SITE_ID"]: s for s in sites}
    regions = [build_region(sp, by, t) for sp in spaces for t in trades]
    for r in regions:
        remove_closures(r)
        for c in r["VIRTUAL_CLOSURES"]:
            assert c["MATERIAL_PRESENT"] is False and c["PHYSICAL_WALL"] is False and c["GEOMETRY_AUTHORITY"] is False and c["REVERSIBLE"] is True
    after = physical_hash(spaces, faces)
    return {"PHYSICAL_HASH_BEFORE": before, "PHYSICAL_HASH_AFTER": after, "REVERSIBLE": before == after, "REGIONS": len(regions),
            "CLOSURES": sum(len(r["VIRTUAL_CLOSURES"]) for r in regions)}, regions

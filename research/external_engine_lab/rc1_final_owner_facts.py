"""Qortuba RC1 final lab: record the owner's floor-finish sequencing method as an Urban owner method rule
(URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1) and the owner's identification of the five PAINTRY FIXTURE lines as
the counter / cabinet outline (QORTUBA-NEW-PAINTRY-COUNTER-CABINETRY-OWNER-001@v1, fingerprint-bound). Run once; the
committed files are then only verified.

    python3 research/external_engine_lab/rc1_final_owner_facts.py <work>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

RULES = ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json"
OBJECTS = ROOT / "data/registry/OWNER_OBJECT_FACTS.json"
PHYS = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"
METHOD = "URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD"
FACT = "QORTUBA-NEW-PAINTRY-COUNTER-CABINETRY-OWNER-001"
COUNTER = ("H478", "H482", "H532", "H536", "H541")
CABINETRY = ["LATER_INSTALLED_CABINETRY", "FIXED_JOINERY", "WARDROBE", "VANITY_UNIT"]
BUILT = ["STRUCTURAL_OBSTACLE", "STRUCTURAL_COLUMN", "MASONRY_WALL", "CONCRETE_WALL", "SHAFT", "DUCT",
         "BUILT_OBSTACLE", "BUILT_PLINTH", "PERMANENT_CURB", "VOID", "OPENING"]

RULE = {
    "rule_id": METHOD, "version": 1, "authority": ["PROJECT_OWNER", "URBAN_OWNER_METHOD"],
    "received": "RC1 finalization brief §1-§3 (Mohammad: 'Tiles are installed under everything because we install the "
                "tiles first, then install the cabinets')",
    "scope": {"applies_to": "every Urban project unless a project specification explicitly overrides it",
              "revision_scoped": False},
    "trade": "FLOOR_FINISH",
    "applicability": {"floor": "a room floor that receives a continuous tile / porcelain / ceramic finish",
                      "space_classes": ["DRY_INTERNAL_ROOM", "WET_SERVICE_ROOM", "SERVICE_ROOM"],
                      "object_classes": CABINETRY,
                      "conditions": ["the physical floor exists beneath the object (the object stands INSIDE the "
                                     "certified site, it is not a boundary or a hole of it)",
                                     "the floor finish is laid BEFORE the cabinetry / joinery is installed",
                                     "no project specification states otherwise"]},
    "treatment": "FOOTPRINT_INCLUDED",
    "statement": "where cabinetry / joinery is installed AFTER the floor finish and sits on the finished floor, the "
                 "floor finish continues underneath it: the cabinet / joinery footprint does NOT reduce the floor-"
                 "finish area",
    "object_class_authority": "the object must be CLASSED as cabinetry / joinery by an owner object fact, a project "
                              "specification or an explicit class map - never by shape, rectangle detection or layer "
                              "alone",
    "excluded_object_classes": BUILT,
    "never": ["a finish carried through a structural column, masonry / concrete wall, shaft, built duct, built "
              "masonry / concrete plinth, permanent curb, void or opening", "cabinetry inferred from geometry or a "
              "layer name", "loose furniture as cabinetry (loose furniture keeps its own project authority)",
              "a change of any site, wall or counter geometry"],
    "relations": [{"fact": "QORTUBA-NEW-FLOOR-OBJECT-FOOTPRINT-OWNER-001@v1", "relation": "GENERALISES",
                   "why": "the same no-deduction principle for built-in wardrobes / joinery, now an Urban method for "
                          "every tiled room; the Qortuba fact stays as project corroboration and remains the authority "
                          "for loose furniture in dry rooms"}]}


def fact(inp, scope):
    from engine.source import owner_claims as OC
    by = {p.identity.key: p for p in inp.parts}
    keys = [f"QORTUBA_REV_NEW|{h}||SEGMENT|0" for h in COUNTER]
    return {"fact_id": FACT, "version": 1, "kind": "TRADE_OBJECT_IDENTITY", "authority": ["PROJECT_OWNER"],
            "received": "RC1 finalization brief §4 (the five FIXTURE-layer lines represent the counter / cabinet "
                        "outline for the floor-finish question; ceramic is installed BEFORE the cabinets)",
            "scope": dict(scope, site_zone="PAINTRY", trade="FLOOR_FINISH"),
            "allowed_domains": ["FLOOR_FINISH_OBJECT_CLASS"],
            "parts": [{"handle": k.split("|")[1][1:], "key": k, "source_layer": by[k].layer,
                       "fingerprint": OC.part_fingerprint(by[k]),
                       "physical_reading": "COUNTER_CABINET_OUTLINE (sits on the finished ceramic floor)"} for k in keys],
            "statement": {"object_class": "LATER_INSTALLED_CABINETRY", "accepts_observed_roles": ["SANITARY_FIXTURE"],
                          "installed_after_floor_finish": True, "sits_on_finished_floor": True,
                          "text": "the PAINTRY FIXTURE lines H478 / H482 / H532 / H536 / H541 outline the kitchen "
                                  "counter / cabinets, installed after the ceramic floor"},
            "is_not": ["a geometry change", "a deduction", "a rule for any other room, revision or project",
                       "a class for any other FIXTURE-layer entity"],
            "transfer_forbidden": ["the old Qortuba revision", "any other Qortuba revision, region or plan variant",
                                   "the DWG (identity NOT_ESTABLISHED)", "P7757", "Al Rashed",
                                   "any future villa or project", "an Urban default"],
            "relations": [{"rule": f"{METHOD}@v1", "relation": "SUPPLIES_THE_OBJECT_CLASS"}]}


def main(work):
    import r8_8_topology as LAB
    inp = LAB.inputs(Path(work))["NEW_K2"]
    r = json.loads(RULES.read_text())
    if not any(x["rule_id"] == METHOD for x in r["rules"]):
        r["rules"].append(RULE)
        RULES.write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
    scope = next(f for f in json.loads(PHYS.read_text())["facts"]
                 if f["fact_id"] == "QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001")["scope"]
    OBJECTS.write_text(json.dumps({"SCHEMA": "URBAN_OWNER_OBJECT_FACTS_V1", "facts": [fact(inp, scope)]},
                                  indent=1, ensure_ascii=False) + "\n")
    print(METHOD, FACT)


if __name__ == "__main__":
    main(sys.argv[1])

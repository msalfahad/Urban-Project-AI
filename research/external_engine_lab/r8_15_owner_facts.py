"""R8.15 lab: record the three new owner PHYSICAL facts (bound to the current new-revision source parts) and the
Urban owner METHOD rule for wet / service marble thresholds. Run once; the committed files are then only verified.

    python3 research/external_engine_lab/r8_15_owner_facts.py <work>

Facts (data/registry/OWNER_PHYSICAL_FACTS.json):
  QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001              BUILT_OBSTACLE (H2060 / H2061, all eight segments)
  QORTUBA-NEW-MB-DRESS-PASSAGE-FULL-HEIGHT-OWNER-001 PASSAGE_HEAD_CONDITION (the passage band end + target face)
  QORTUBA-NEW-MAIN-ENTRANCE-MARBLE-OWNER-001       THRESHOLD_FINISH_CONSTRUCTION (the entrance door symbol parts)
Rule (data/registry/URBAN_OWNER_METHOD_RULES.json):
  URBAN-WET-SERVICE-MARBLE-THRESHOLD@v1
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

import r8_13_qortuba as R13                                                                   # noqa: E402
from engine.source import owner_claims as OC                                                  # noqa: E402

FACTS = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"
RULES = ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json"
DUCT = "QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001"
MBD = "QORTUBA-NEW-MB-DRESS-PASSAGE-FULL-HEIGHT-OWNER-001"
ENTR = "QORTUBA-NEW-MAIN-ENTRANCE-MARBLE-OWNER-001"
MARBLE_RULE = "URBAN-WET-SERVICE-MARBLE-THRESHOLD"
TRANSFER = ["the old Qortuba revision (QP-17 / QP-18 stay old-revision rules)", "any other Qortuba revision, region "
            "or plan variant", "the DWG (identity NOT_ESTABLISHED)", "P7757", "Al Rashed", "any future villa or "
            "project", "an Urban default", "any other entity of the same shape, layer or presentation"]
DUCT_PARTS = {f"QORTUBA_REV_NEW|H2060||SEGMENT|{i}": "DUCT_ENCLOSURE_OUTER_FACE" for i in range(4)} | \
    {f"QORTUBA_REV_NEW|H2061||SEGMENT|{i}": "DUCT_ENCLOSURE_INNER_FACE" for i in range(4)}
MBD_PARTS = {"QORTUBA_REV_NEW|H1894||SEGMENT|0": "PASSAGE_JAMB_FACE (band end)",
             "QORTUBA_REV_NEW|H1893||SEGMENT|0": "REAL_WALL_FACE (passage wall, M.B.ROOM side)",
             "QORTUBA_REV_NEW|H1895||SEGMENT|0": "REAL_WALL_FACE (passage wall, DRESS side)",
             "QORTUBA_REV_NEW|H518||SEGMENT|0": "REAL_WALL_FACE (continuous face the passage meets)"}
ENTRANCE_INSTANCE = "677"


def scope(inp, **extra):
    rev = inp.revision
    return {"project": "QORTUBA", "source_revision_id": rev.revision_id, "source_anchor_sha256": rev.anchor_sha256,
            "region_id": inp.region_id, "frame_id": inp.frame_id, "plan": "PLAN_VARIANT_4_SELECTED", **extra}


def _part(p, reading):
    return {"handle": p.identity.source_handle, "key": p.identity.key, "source_layer": p.layer,
            "fingerprint": OC.part_fingerprint(p), "physical_reading": reading}


def facts(inp) -> list:
    by_key = {p.identity.key: p for p in inp.parts}
    door = sorted((p for p in inp.parts if p.identity.instance_handles == (ENTRANCE_INSTANCE,)),
                  key=lambda p: p.identity.key)
    return [
        {"fact_id": DUCT, "version": 1, "kind": "BUILT_OBSTACLE", "authority": ["PROJECT_OWNER"],
         "received": "R8.15 brief §1-§2 (owner reviewed the source-plan crop)", "scope": scope(inp),
         "parts": [_part(by_key[k], r) for k, r in DUCT_PARTS.items()],
         "statement": {"text": "the 2.10 x 0.40 m rectangle in the BED.ROOM is a REAL DUCT",
                       "physical_class": "DUCT", "physical_role": "DUCT / BUILT_OBSTACLE",
                       "topology_effect": "PHYSICAL_OBSTACLE", "floor_effect": "EXCLUDED_FROM_ROOM_FLOOR",
                       "ceiling_effect": "EXCLUDED_FROM_NORMAL_CEILING",
                       "footprint": "derived from source geometry (never a target value)",
                       "material": "NOT STATED (the role implies no material)",
                       "corroborating_presentation": {
                           "parts": ["QORTUBA_REV_NEW|H2062||SEGMENT|0", "QORTUBA_REV_NEW|H2065||SEGMENT|0"],
                           "role": "a dashed X on a hidden layer - corroboration only, never a bound part, never a "
                                   "duct identity elsewhere"}},
         "transfer_forbidden": TRANSFER,
         "never": ["closed rectangle + X = duct", "a duct anywhere else", "a re-layered CAD entity", "a quantity"]},
        {"fact_id": MBD, "version": 1, "kind": "PASSAGE_HEAD_CONDITION", "authority": ["PROJECT_OWNER"],
         "received": "R8.15 brief §3 (owner reviewed the plan crop)", "scope": scope(inp),
         "parts": [_part(by_key[k], r) for k, r in MBD_PARTS.items()],
         "statement": {"text": "the ~1.20 m passage between M.B.ROOM and DRESS is FULL HEIGHT: no head, no soffit",
                       "head_condition": "FULL_HEIGHT", "top_soffit": "NONE", "ceiling": "NORMAL CEILING CONTINUES "
                       "through the passage footprint (no deduction)", "passage": "remains physically open",
                       "side_jambs": "may exist (source decides)"},
         "supersedes_in_scope": ["PASSAGE_HEAD_CONDITION_NOT_ESTABLISHED for this passage (R8.14)"],
         "does_not_use": ["QP-18 (old revision: it states the opposite and does not transfer)"],
         "transfer_forbidden": TRANSFER, "never": ["a head height", "a soffit", "a transfer to another passage"]},
        {"fact_id": ENTR, "version": 1, "kind": "THRESHOLD_FINISH_CONSTRUCTION", "authority": ["PROJECT_OWNER"],
         "received": "R8.15 brief §5-§6 (owner reviewed the entrance threshold; construction photo of the TYPE)",
         "scope": scope(inp), "parts": [_part(p, "MAIN_APARTMENT_ENTRANCE_DOOR_SYMBOL") for p in door],
         "statement": {"text": "MAIN APARTMENT ENTRANCE: an explicit MARBLE THRESHOLD / برطاش is installed; the "
                               "threshold is part of the apartment scope",
                       "threshold_treatment": "MARBLE_THRESHOLD_EXPLICIT", "scope_side": "APARTMENT",
                       "floor_interface": "apartment porcelain ends at the apartment-side marble edge; the common-area "
                                          "finish begins after the opposite edge",
                       "geometry": "the physical threshold strip from source", "rise_mm": "NOT_STATED",
                       "photo": "shows the threshold TYPE only - never a dimension source",
                       "boq": "a separate MARBLE_THRESHOLD trade item (no price)"},
         "supersedes_in_scope": ["the R8.14 post-run unit-boundary 50 / 50 porcelain split for this door"],
         "transfer_forbidden": TRANSFER,
         "never": ["porcelain inside the threshold", "a 50 / 50 split with the landing", "a rise or water-containment "
                   "function copied from the Urban wet / service rule", "dimensions from the photograph"]}]


def urban_rule() -> dict:
    return {"SCHEMA": "URBAN_OWNER_METHOD_RULES_V1", "rules": [{
        "rule_id": MARBLE_RULE, "version": 1, "authority": ["PROJECT_OWNER", "URBAN_OWNER_METHOD"],
        "received": "R8.15 brief §7-§14 (Mohammad promoted it to an Urban rule)",
        "scope": {"applies_to": "every Urban project unless a project specification explicitly overrides it",
                  "revision_scoped": False},
        "applicability": ["BATHROOM", "KITCHEN", "WASHING_LAUNDRY_ROOM", "IRONING_ROOM"],
        "applicability_rule": "a doorway serving such a room: either side carries the room type through an "
                              "authoritative, TRADE-SCOPED room-type map (never raw text alone)",
        "not_applicable_to": ["bedroom doors", "living-room doors", "general dry <-> dry doors", "external entrances "
                              "(unless separate project evidence exists)", "PAINTRY / pantry (not named by the owner)"],
        "measurement": {"clear_width": "SOURCE (the doorway strip)", "depth": "SOURCE (the doorway strip)",
                        "rise_mm": 20, "rise_is": "VERTICAL height above the adjoining finished floor",
                        "extent": "the FULL CLEAR DOOR OPENING WIDTH x the physical threshold depth"},
        "trade": "MARBLE_THRESHOLD", "function": "WATER_CONTAINMENT_BARRIER",
        "floor_interfaces": {"wet": "wet floor tile ends at the wet-side marble edge",
                             "dry": "dry porcelain ends at the dry-side marble edge",
                             "marble": "owns the complete threshold footprint (no half tile inside it)"},
        "supersedes_in_scope": ["QORTUBA-NEW-DRY-WET-TRANSITION-AT-DOOR-PLANE-OWNER-001@v1 where the rule applies "
                                "(the split stays in force for any dry / wet door the rule does not cover)"],
        "never": ["a waterproofing extent change", "a slope", "a drainage", "a material rate or price",
                  "20 mm as a horizontal width or depth", "a universal horizontal depth", "a hydraulic claim"]}]}


def main(work):
    inps, _, _ = R13.Q10.inputs(work)
    inp = inps["NEW_K2"]
    raw = json.loads(FACTS.read_text())
    keep = [f for f in raw["facts"] if f["fact_id"] not in (DUCT, MBD, ENTR)]
    raw["SCHEMA"] = "URBAN_OWNER_PHYSICAL_FACTS_V2"
    raw["facts"] = keep + facts(inp)
    FACTS.write_text(json.dumps(raw, indent=1, ensure_ascii=False) + "\n")
    RULES.write_text(json.dumps(urban_rule(), indent=1, ensure_ascii=False) + "\n")
    print(len(raw["facts"]), "physical facts;", [len(f["parts"]) for f in raw["facts"]])


if __name__ == "__main__":
    main(sys.argv[1])

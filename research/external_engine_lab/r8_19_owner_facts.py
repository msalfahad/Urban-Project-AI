"""R8.19 lab: record the two Urban owner METHOD rules for exposed object faces (columns; interior ducts / boxed-out
faces) and the scoped Qortuba statement for the H2060 BED.ROOM duct finish. Run once; the committed files are then
only verified.

    python3 research/external_engine_lab/r8_19_owner_facts.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METHOD = ROOT / "data/registry/OWNER_METHOD_FACTS.json"
RULES = ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json"
PHYS = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"
DUCT = "QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001"
DUCT_FINISH = "QORTUBA-NEW-BED-ROOM-DUCT-FINISH-OWNER-001"

RULES_NEW = [
    {"rule_id": "URBAN-EXPOSED-COLUMN-FINISH-METHOD", "version": 1,
     "authority": ["PROJECT_OWNER", "URBAN_OWNER_METHOD"], "received": "R8.19 brief §1-§5",
     "scope": {"applies_to": "every Urban project unless a project specification states the column finish",
               "revision_scoped": False},
     "method": {"principle": "an EXPOSED column face inside a room follows the surrounding room treatment",
                "requires": ["PHYSICAL_EXPOSURE (the face is a room-facing boundary of the certified room)"],
                "dry_area": ["SKIRTING (on the existing wall-contact path only)", "PLASTER", "PAINT"],
                "wet_full_wall_tile_area": ["PORCELAIN / WALL TILE (the room's wall-tile trade and height)"],
                "height": "the room's own authorised wall-finish height for that trade",
                "physical_class": "COLUMN_FACE stays its own class; it is never merged into WALL_FACE"},
     "never": ["a finish because an object is structurally a column", "a finish on a hidden / embedded / "
               "wall-buried face", "paint on a wet / full-wall-tile column", "normal skirting in a full-wall-tile room",
               "new skirting where the contact path already covers the face"]},
    {"rule_id": "URBAN-EXPOSED-INTERIOR-DUCT-FINISH-METHOD", "version": 1,
     "authority": ["PROJECT_OWNER", "URBAN_OWNER_METHOD"], "received": "R8.19 brief §6-§8",
     "scope": {"applies_to": "every Urban project: exposed interior duct / boxed-out faces where the surrounding "
                             "DRY room treatment applies", "revision_scoped": False},
     "method": {"principle": "an exposed interior duct / boxed-out face takes the surrounding dry-room treatment",
                "requires": ["OWNER_PHYSICAL_AUTHORITY (the duct is established as a built obstacle)",
                             "PHYSICAL_EXPOSURE (room-facing faces of the certified room only)"],
                "dry_area": ["SKIRTING (on the existing wall-contact path only)", "PLASTER", "PAINT"],
                "height": "the room's own authorised dry wall-finish height",
                "physical_class": "OBSTACLE / DUCT_FACE stays its own class; it is never merged into WALL_FACE"},
     "never": ["a finish on faces against existing walls, internal faces, non-room-facing faces or faces outside the "
               "measurement region", "a finish for a generic obstacle without owner physical authority",
               "a wet-room treatment by analogy (not stated)", "new skirting where the contact path already covers "
               "the face"]}]


def duct_fact(phys):
    d = phys[DUCT]
    return {"fact_id": DUCT_FINISH, "version": 1, "kind": "FINISH_SCOPE", "authority": ["PROJECT_OWNER"],
            "received": "R8.19 brief §6-§7", "scope": dict(d["scope"], trades=["PLASTER", "PAINT", "SKIRTING"],
                                                            space_classes=["DRY_INTERNAL_ROOM"]),
            "statement": {"text": "the current exposed BED.ROOM duct (H2060 / H2061) receives SKIRTING, PLASTER and "
                                  "PAINT on its exposed room-facing faces",
                          "object": f"{DUCT}@v1", "parts": [p["key"] for p in d["parts"]],
                          "trades": {"PLASTER": "exposed vertical faces at the dry 3.15 m height",
                                     "PAINT": "exposed vertical faces at the dry 3.15 m height",
                                     "SKIRTING": "unchanged: the existing V4 AUTHORISED_OBSTACLE_FACE path"},
                          "exposure": "room-facing faces of the certified BED.ROOM site only"},
            "unit": None, "transfer_forbidden": ["the old Qortuba revision", "any other region, plan or floor",
                                                  "the DWG (identity NOT_ESTABLISHED)", "P7757", "Al Rashed",
                                                  "any future project (the Urban rule governs there)"],
            "relations": [{"rule": "URBAN-EXPOSED-INTERIOR-DUCT-FINISH-METHOD@v1", "relation": "CORROBORATING",
                           "scope": "this duct", "why": "the project statement the Urban rule generalises"}]}


def main():
    m, r = json.loads(METHOD.read_text()), json.loads(RULES.read_text())
    phys = {f["fact_id"]: f for f in json.loads(PHYS.read_text())["facts"]}
    if not any(f["fact_id"] == DUCT_FINISH for f in m["facts"]):
        m["facts"].append(duct_fact(phys))
        METHOD.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n")
    have = {x["rule_id"] for x in r["rules"]}
    r["rules"] += [x for x in RULES_NEW if x["rule_id"] not in have]
    RULES.write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
    print([f["fact_id"] for f in m["facts"]][-1], [x["rule_id"] for x in r["rules"]])


if __name__ == "__main__":
    main()

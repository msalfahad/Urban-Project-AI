"""R8.20 lab: record the owner's human closure reviews (H2430 / H2431 / I1471, bound to the R8.19 packet digests) and
the I1471 physical construction rationale (the ~200 mm wall thickened / aligned to conceal the structural column),
fingerprint-bound to the admitted source parts. Run once; the committed files are then only verified.

    python3 research/external_engine_lab/r8_20_owner_facts.py <work>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

PHYS = ROOT / "data/registry/OWNER_PHYSICAL_FACTS.json"
REVIEWS = ROOT / "data/registry/OWNER_CLOSURE_REVIEWS.json"
FACT = "QORTUBA-NEW-I1471-200MM-WALL-COLUMN-CONCEALMENT-OWNER-001"
PARTS = [("QORTUBA_REV_NEW|H519||SEGMENT|0", "LEFT_WALL_200MM_FACE (band WB-d0fa2ebe87cedccd)"),
         ("QORTUBA_REV_NEW|H525||SEGMENT|0", "LEFT_WALL_200MM_FACE (band WB-d0fa2ebe87cedccd)"),
         ("QORTUBA_REV_NEW|H1472||SEGMENT|0", "LEFT_JAMB_CAP_200MM (I1471)"),
         ("QORTUBA_REV_NEW|H518||SEGMENT|0", "RIGHT_WALL_150MM_FACE (band WB-2c6e6cc37179fbc6)"),
         ("QORTUBA_REV_NEW|H523||SEGMENT|0", "RIGHT_WALL_150MM_FACE (band WB-2c6e6cc37179fbc6)"),
         ("QORTUBA_REV_NEW|H1473||SEGMENT|0", "RIGHT_JAMB_CAP_150MM (I1471)")] + \
        [(f"QORTUBA_REV_NEW|H716||SEGMENT|{i}", "STRUCTURAL_COLUMN_CONCEALED_BY_THE_200MM_WALL (H716)")
         for i in range(4)]


def fact(inp, scope):
    from engine.source import owner_claims as OC
    by = {p.identity.key: p for p in inp.parts}
    return {"fact_id": FACT, "version": 1, "kind": "PHYSICAL_CONSTRUCTION_RATIONALE", "authority": ["PROJECT_OWNER"],
            "received": "R8.20 brief §2-§6 (owner review of the I1471 packet)", "scope": dict(scope, opening="I1471"),
            "allowed_domains": [],
            "parts": [{"handle": k.split("|")[1][1:], "key": k, "source_layer": by[k].layer,
                       "fingerprint": OC.part_fingerprint(by[k]), "physical_reading": r} for k, r in PARTS],
            "statement": {"text": "the LEFT wall at I1471 is intentionally ~200 mm thick: it is thickened / aligned to "
                                  "conceal the structural column; the other wall is ~150 mm; the 50 mm stagger is "
                                  "intentional construction geometry",
                          "is_not": ["a drafting error", "a snap error", "a finish offset", "a dimension error",
                                     "a wall-band reconstruction error"],
                          "geometry_change": "NONE - the deterministic geometry stays exactly what the admitted source "
                                             "proves (200 / 150 mm, 50 mm stagger)",
                          "role": "CORROBORATING RATIONALE (why the geometry exists); authorises no topology, "
                                  "geometry, quantity or trade change"},
            "transfer_forbidden": ["another door", "another wall", "another floor or plan", "another revision",
                                   "another project", "an Urban wall rule ('walls beside columns are 200 mm')"],
            "relations": []}


REVIEW_TEXT = {
    "H2430": "the zero-material topology cap correctly represents the end of a real wall at the open Hall / Lobby "
             "passage; the passage stays OPEN; the cap is no blockwork, closes nothing physically and creates no "
             "plaster, paint, skirting or ceiling",
    "H2431": "the zero-material topology cap correctly represents the end of a real wall at the open Hall / Lobby "
             "passage; the passage stays OPEN; the cap is no blockwork, closes nothing physically and creates no "
             "plaster, paint, skirting or ceiling",
    "I1471": "the door-strip interpretation is correct: the doorway passes through walls of ~150 mm and ~200 mm; the "
             "offset / stagger is intentional"}


def reviews():
    pk = json.loads((ROOT / "tests/r8_19/registers/CLOSURE_RELEASE_STATUS.json").read_text())["review_packets"]
    out = []
    for name in ("H2430", "H2431", "I1471"):
        p = pk[name]
        out.append({"review_id": f"QORTUBA-NEW-{name}-CLOSURE-REVIEW-OWNER-001", "version": 1,
                    "closure": p.get("closure_id", name), "closure_name": name, "packet": "R8.19 "
                    "CLOSURE_RELEASE_STATUS.review_packets." + name, "packet_digest": p["closure_digest"],
                    "decision": "ACCEPT", "reviewer": "Mohammad", "reviewer_role": "PROJECT_OWNER",
                    "received": "R8.20 brief §1-§2", "statement": REVIEW_TEXT[name],
                    "effect": "HUMAN_REVIEW condition of CLOSURE_RELEASE_MODEL_V1 for this exact closure record only",
                    "never": ["geometry", "topology", "quantity", "trade", "a release"]})
    return {"SCHEMA": "URBAN_OWNER_CLOSURE_REVIEWS_V1",
            "policy": "CLOSURE_HUMAN_REVIEW_POLICY_V1: a review is versioned human evidence for ONE closure record "
                      "digest; a changed closure voids it; never self-approved", "reviews": out}


def main(work):
    import r8_8_topology as LAB
    inp = LAB.inputs(Path(work))["NEW_K2"]
    phys = json.loads(PHYS.read_text())
    scope = next(f for f in phys["facts"] if f["fact_id"] == "QORTUBA-NEW-BED-ROOM-DUCT-OWNER-001")["scope"]
    if not any(f["fact_id"] == FACT for f in phys["facts"]):
        phys["facts"].append(fact(inp, scope))
        PHYS.write_text(json.dumps(phys, indent=1, ensure_ascii=False) + "\n")
    REVIEWS.write_text(json.dumps(reviews(), indent=1, ensure_ascii=False) + "\n")
    print(FACT, [r["review_id"] for r in reviews()["reviews"]])


if __name__ == "__main__":
    main(sys.argv[1])

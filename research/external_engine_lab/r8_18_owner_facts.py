"""R8.18 lab: record the owner's current-Qortuba DRY wall-finish height (3.15 m, plaster + paint) as a scoped method
fact, and two Urban owner METHOD rules (dynamic wall-finish height; reveal finish). Run once; the committed files are
then only verified.

    python3 research/external_engine_lab/r8_18_owner_facts.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METHOD = ROOT / "data/registry/OWNER_METHOD_FACTS.json"
RULES = ROOT / "data/registry/URBAN_OWNER_METHOD_RULES.json"
DRY = "QORTUBA-NEW-DRY-WALL-FINISH-HEIGHT-OWNER-001"
WIN = "QORTUBA-NEW-NORMAL-WINDOWS-ABOVE-FLOOR-OWNER-001"
TRANSFER = ["the old Qortuba revision (QP-03 / QP-04 3.00 m stay old-revision rules)", "any other Qortuba revision, "
            "region, plan variant or floor", "the DWG (identity NOT_ESTABLISHED)", "the wet / service rooms (their "
            "own 3.20 m tile fact)", "P7757", "Al Rashed", "any future villa or project", "an Urban default"]


def dry_fact(base_scope):
    scope = {k: v for k, v in base_scope.items() if k not in ("trade", "trades", "space_classes")}
    return {"fact_id": DRY, "version": 1, "kind": "WALL_FINISH_HEIGHT", "authority": ["PROJECT_OWNER"],
            "received": "R8.18 brief §1-§2 (owner answer to the R8.17 dry-room wall height question)",
            "scope": dict(scope, trades=["PLASTER", "PAINT"], space_classes=["DRY_INTERNAL_ROOM"],
                          floor="the selected SECOND FLOOR apartment plan (PLAN_VARIANT_4_SELECTED)"),
            "statement": {"text": "for the CURRENT selected Qortuba scope, DRY INTERNAL WALL PLASTER and PAINT run to "
                                  "3.15 m", "plaster_height_m": 3.15, "paint_height_m": 3.15,
                          "values": [{"trade": "PLASTER", "attribute": "HEIGHT_M", "value": 3.15},
                                     {"trade": "PAINT", "attribute": "HEIGHT_M", "value": 3.15}],
                          "is": "the owner-authorised RESULT for this scope (wall-height authority rank 4)",
                          "owner_rationale": {"floor_to_floor_m": 4.00, "beam_zone_m": 0.60,
                                              "ceiling_decor_zone_m": 0.15, "floor_buildup_m": 0.10,
                                              "result_m": 3.15, "status": "OWNER_RATIONALE (example arithmetic) - the "
                                              "components are NOT source-established and form no formula"},
                          "source_corroboration": "the region text 'LEVEL R.F = 4.00 m' (a level, never a wall "
                                                  "height by itself)",
                          "does_not_apply_to": ["wet / service wall tile (3.20 m fact)", "PAINTRY", "ceilings"]},
            "unit": "m", "transfer_forbidden": TRANSFER,
            "relations": [{"rule": "QP-03 QORTUBA_INTERNAL_PLASTER_HEIGHT = 3.00 m", "relation": "SUPERSEDED_IN_SCOPE",
                           "scope": "the selected NEW revision dry internal rooms only; QP-03 stays for the old revision",
                           "why": "a CHANGE of value (3.00 -> 3.15 m) for the new revision"},
                          {"rule": "QP-04 QORTUBA_INTERNAL_PAINT_HEIGHT = 3.00 m", "relation": "SUPERSEDED_IN_SCOPE",
                           "scope": "the selected NEW revision dry internal rooms only; QP-04 stays for the old revision",
                           "why": "a CHANGE of value (3.00 -> 3.15 m) for the new revision"}]}


RULES_NEW = [
    {"rule_id": "URBAN-WALL-FINISH-HEIGHT-METHOD", "version": 1, "authority": ["PROJECT_OWNER", "URBAN_OWNER_METHOD"],
     "received": "R8.18 brief §1, §3", "scope": {"applies_to": "every Urban project", "revision_scoped": False},
     "method": {"principle": "WALL FINISH HEIGHT IS NOT A COMPANY-WIDE NUMBER: it is established per floor / "
                             "measurement scope and per trade",
                "hierarchy": ["explicit source wall / finish height", "section / elevation clear height",
                              "derived clear height from authoritative vertical components",
                              "project / source-bound owner fact", "permitted project default", "BLOCKED"],
                "derivation_evidence": ["floor-to-floor / level", "beam depth", "suspended / decorative ceiling "
                                        "depth", "floor build-up / finishing depth", "other vertical constraints"]},
     "never": ["URBAN_DEFAULT_WALL_HEIGHT", "a wall height from floor-to-floor alone", "one floor's height on another",
               "a derivation with an unknown component"]},
    {"rule_id": "URBAN-REVEAL-FINISH-METHOD", "version": 1, "authority": ["PROJECT_OWNER", "URBAN_OWNER_METHOD"],
     "received": "R8.18 brief §14-§17", "scope": {"applies_to": "every Urban project unless a project instruction "
                                                                "states the reveal finish", "revision_scoped": False},
     "method": {"default": "PLASTER", "porcelain": "ONLY when explicitly requested / shown / project-authorised",
                "paint": "on a reveal owned by a painted dry surface; never invented in a wet / service room",
                "sliding_doors": "side-jamb ownership follows the aluminium profile / frame position where the source "
                                 "shows it; otherwise PLASTER default",
                "ambiguity": "a reveal whose owning side the source does not establish is QUESTION / BLOCK for that "
                             "reveal only"},
     "never": ["porcelain because an adjacent room is wet", "every reveal one finish",
               "one reveal in two room finishes"]}]


def main():
    m = json.loads(METHOD.read_text())
    base = next(f for f in m["facts"] if f["fact_id"] == WIN and f["version"] == 1)["scope"]
    m["facts"] = [f for f in m["facts"] if f["fact_id"] != DRY] + [dry_fact(base)]
    METHOD.write_text(json.dumps(m, indent=1, ensure_ascii=False) + "\n")
    r = json.loads(RULES.read_text())
    ids = {x["rule_id"] for x in RULES_NEW}
    r["rules"] = [x for x in r["rules"] if x["rule_id"] not in ids] + RULES_NEW
    RULES.write_text(json.dumps(r, indent=1, ensure_ascii=False) + "\n")
    print(len(m["facts"]), "method facts;", [x["rule_id"] for x in r["rules"]])


if __name__ == "__main__":
    main()

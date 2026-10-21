"""QS_MEASUREMENT_REGION_REGISTER + OPENING_REGISTER v4 (directive §8, §9,
§11): trade-specific regions built from physical geometry and topological
relations, with virtual closures that carry zero material and no geometry
authority. Openings stay physical records with their own deduction and
reveal.

    python3 -m research.qs_wall_treatment_01.measurement_regions_v4
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import measurement_region_builder as MRB
from engine import opening_register as OR
from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.owner_parameters import p7757_registry

OUT = Path(P.OUT_DIR)
OWNER_RULE_VERSION = "P7757_OWNER_PARAMETERS (3.20 normal; full deduction; reveals separate)"
PROJECT_RULE_VERSION = "data/registry/P7757_PROJECT_RULES.json"


def _v(reg, k):
    v = reg[k]
    return v["VALUE"] if isinstance(v, dict) else v


def run() -> dict:
    v3 = json.loads((OUT / "P7757_WALL_TREATMENT_ESTIMATE_v3.json").read_text("utf-8"))
    link = json.loads((OUT / "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json").read_text("utf-8"))
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    reg = p7757_registry()
    saloon = next(s for s in v3["SETS"] if s["PLAN"]["SET_ID"] == "GF-SALOON-NORMAL-PLASTER")
    fs = saloon["FACE_SET"]
    by_id = {f["FACE_ID"]: f for b in ("ESTABLISHED_FACES", "PROVISIONAL_FACES", "UNRESOLVED_FACES", "EXCLUDED_FACES") for f in fs.get(b, [])}
    # ---- openings (physical layer) ------------------------------------------
    openings = []
    for o in fs.get("OPENINGS", []) or saloon["PLAN"]["OPENINGS"]:
        oid = o["OPENING_ID"] if isinstance(o, dict) else o
        od = o if isinstance(o, dict) else {}
        typ = od.get("TYPE", "UNRESOLVED")
        w = od.get("width_m")
        if typ == "DOOR":
            h, hs = _v(reg, "DOOR_HEIGHT"), "PROVISIONAL_DEFAULT"
            wsrc = od.get("width_source") or "PROVISIONAL_DEFAULT"
            w = w if w is not None else _v(reg, "DOOR_WIDTH")
            rd, rds = _v(reg, "DOOR_REVEAL_DEPTH") if "DOOR_REVEAL_DEPTH" in reg else 0.15, "PROVISIONAL_DEFAULT"
        elif typ in ("WINDOW", "GLAZING"):
            h, hs = (_v(reg, "WINDOW_HEIGHT"), "PROVISIONAL_DEFAULT") if typ == "WINDOW" else (None, "NOT_ESTABLISHED")
            wsrc = od.get("width_source") or ("PROVISIONAL_DEFAULT" if typ == "WINDOW" else "NOT_ESTABLISHED")
            w = w if w is not None else (_v(reg, "WINDOW_WIDTH") if typ == "WINDOW" else None)
            rd, rds = _v(reg, "WINDOW_REVEAL_DEPTH"), "PROVISIONAL_DEFAULT"
        else:
            h, hs, wsrc, rd, rds = None, "NOT_ESTABLISHED", "NOT_ESTABLISHED", None, "NOT_ESTABLISHED"
        openings.append(OR.opening(opening_id=oid, host_face=od.get("HOSTED_IN"), opening_type=typ, width_m=w, width_source=wsrc,
                                   height_m=h, height_source=hs, deduction_rule="FULL_OPENING_DEDUCTION",
                                   reveal_depth_m=(od.get("reveal_depth_m") or rd), reveal_depth_source=("DRAWING_PRINTED_DIMENSION" if od.get("reveal_depth_m") else rds)))
    # ---- SALOON run as a LINEAR_RUN of physical edges --------------------------
    def edge(fid, kind, L, state, a, b, src):
        return {"EDGE_ID": fid, "KIND": kind, "length_m": L, "a": a, "b": b, "trace_ids": [fid], "STATE": state, "length_source": src,
                "provenance": {"SOURCE": src}}
    phys = [edge("SEG-02", "PHYSICAL_WALL_FACE", 5.15, "OWNER_ESTABLISHED", (0, 0), (5.15, 0), "owner-verified 515 + CAD-260#01"),
            edge("COL-02-BOND", "EXPOSED_COLUMN_FACE", 0.20, "PROVISIONAL", (5.15, 0), (5.15, 0.20), "CAD pier hatch extent"),
            edge("SEG-03", "PHYSICAL_WALL_FACE", 2.00, "OWNER_ESTABLISHED", (5.15, 0.20), (5.15, 2.20), "CAD 2.000"),
            edge("GLZ-02", "GLAZING_BOUNDARY", 6.331, "OWNER_ESTABLISHED", (5.15, 2.20), (5.15, 8.53), "633 chain segment / CAD glazing band"),
            edge("OE-01", "OPEN_PHYSICAL_EDGE", 1.30, "ESTABLISHED", (0, 0), (0, 1.30), "no material: wall face -> free column (ST p1/p3/p4)"),
            edge("LOOP-059", "EXPOSED_COLUMN_FACE", st["D2"]["COLUMN_EXPOSED_TO_ROOM"]["GIRTH_LM_STRUCTURAL"], "PROVISIONAL", (0, 1.30), (0, 1.55), "structural 30x60 column, 4 faces")]
    sites = [{"SITE_ID": "S-OE-01", "SITE_TYPE": "CONFIRMED_OPEN_PASSAGE", "termination_a": (0, 1.55), "termination_b": (5.15, 8.53), "span_m": None,
              "evidence": "SALOON <-> RECEPTION open plan; no wall, beam overhead (ST p4)", "trace_ids": ["OE-01"]}]
    regions = []
    regions.append(MRB.build(region_id="R-GF-SALOON-PLASTER-RUN", physical_geometry=phys, topological_relations=sites, opening_register=openings,
                             trade="NORMAL_INTERNAL_PLASTER", measurement_basis="LINEAR_RUN", owner_rule_version=OWNER_RULE_VERSION,
                             project_rule_version=PROJECT_RULE_VERSION))
    # the same faces as an OPEN_PLAN cell: the open passage is closed VIRTUALLY (zero material) only to form a cell
    regions.append(MRB.build(region_id="R-GF-SALOON-OPEN-PLAN-CELL", physical_geometry=[e for e in phys if e["KIND"] != "OPEN_PHYSICAL_EDGE"],
                             topological_relations=sites, opening_register=openings, trade="NORMAL_INTERNAL_PLASTER",
                             measurement_basis="WALL_FACE_PLASTER_OPEN_PLAN_CELL", owner_rule_version=OWNER_RULE_VERSION,
                             project_rule_version=PROJECT_RULE_VERSION))
    # ---- SE roof edge and tower ring as LINEAR_RUNs ------------------------------
    sol = link["PORTIONS_PROPOSED"]["SOLID_PORTION_NE"]
    lat = link["PORTIONS_PROPOSED"]["LATTICE_KERB_PORTION_SW"]
    se = [edge("SE-RE-SOLID-EXT", "PHYSICAL_WALL_FACE", sol["OUTER_FACE_LENGTH_M"], "PROPOSED_CORRESPONDENCE", (0, 0), (sol["OUTER_FACE_LENGTH_M"], 0), "CAD-4804 NE portion"),
          edge("SE-RE-KERB-EXT", "CURVED_MATERIAL_FACE", lat["KERB_ZONE_LINE_LENGTH_M"], "PROPOSED_CORRESPONDENCE", (sol["OUTER_FACE_LENGTH_M"], 0), (7.45, 0), "CAD-4808 kerb zone"),
          edge("SE-RE-BAL", "OPEN_PHYSICAL_EDGE", lat["KERB_ZONE_LINE_LENGTH_M"], "ESTABLISHED", (sol["OUTER_FACE_LENGTH_M"], 1), (7.45, 1), "lattice: zero material face")]
    regions.append(MRB.build(region_id="R-ROOF-SE-EDGE-EXTERNAL", physical_geometry=se, topological_relations=[], opening_register=[],
                             trade="ROOF_PARAPET_PLASTER", measurement_basis="LINEAR_RUN", owner_rule_version=OWNER_RULE_VERSION,
                             project_rule_version=PROJECT_RULE_VERSION))
    tower = st["TOWER_ROOF_13_90_OUTLINE_p6"]
    regions.append(MRB.build(region_id="R-ROOF-TOWER-RING", physical_geometry=[edge("TOWER-RING", "PHYSICAL_WALL_FACE", tower["DEVELOPED_PERIMETER_M"], "PROVISIONAL", (0, 0), (0, 0), "ST p6 exterior ring")],
                             topological_relations=[], opening_register=[], trade="ROOF_PARAPET_PLASTER", measurement_basis="LINEAR_RUN",
                             owner_rule_version=OWNER_RULE_VERSION, project_rule_version=PROJECT_RULE_VERSION))
    regions.append(MRB.build(region_id="R-ROOF-SW-EDGE", physical_geometry=[edge("SW-RE-SOLID", "UNRESOLVED_EDGE", 4.325, "NOT_ESTABLISHED", (0, 0), (4.325, 0), "no height source")],
                             topological_relations=[], opening_register=[], trade="ROOF_PARAPET_PLASTER", measurement_basis="LINEAR_RUN",
                             owner_rule_version=OWNER_RULE_VERSION, project_rule_version=PROJECT_RULE_VERSION))
    # invariants over the register
    inv = {"EVERY_CLOSURE_ZERO_MATERIAL": all(c["MATERIAL_PRESENT"] is False and c["PHYSICAL_WALL"] is False and c["GEOMETRY_AUTHORITY"] is False
                                             and c["quantity_length_contribution"] == 0.0 for r in regions for c in r["VIRTUAL_CLOSURES"]),
           "NO_UNRESOLVED_GAP_SILENTLY_CLOSED": all(not r["FORMED"] or not r["UNRESOLVED_RELATIONS"]["UNRESOLVED_EDGES"] for r in regions),
           "OPENINGS_SURVIVE_CLOSURE": all(len(r["OPENINGS"]) == len(openings) for r in regions[:2])}
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "QS_MEASUREMENT_REGION_REGISTER", "LAYERS": MRB.LAYERS, "REGIONS": regions, "INVARIANTS": inv,
           "INPUTS": {"OWNER_RULE_VERSION": OWNER_RULE_VERSION, "PROJECT_RULE_VERSION": PROJECT_RULE_VERSION}}
    p = OUT / "QS_MEASUREMENT_REGION_REGISTER.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    op = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "OPENING_REGISTER", "VERSION": "v4", "OPENINGS": openings,
          "RULE": "PHYSICAL_OPENING, MEASUREMENT_CLOSURE, OPENING_DEDUCTION and REVEAL_QUANTITY are separate records; the deduction rule is the ENGINEERING rulebook (full deduction)"}
    q = OUT / "OPENING_REGISTER_v4.json"
    q.write_text(json.dumps(op, indent=2, default=str) + "\n", encoding="utf-8")
    return {"REGIONS": [(r["MEASUREMENT_REGION_ID"], r["MEASUREMENT_REGION_STATUS"], r["GROSS_BASIS"]["VALUE"], len(r["VIRTUAL_CLOSURES"]), r["QUANTITY_STATE"]) for r in regions],
            "OPENINGS": [(o["OPENING_ID"], o["TYPE"], o["AREA"], o["DEDUCTION_AMOUNT"], o["REVEAL_AREA"], o["STATUS"]) for o in openings],
            "INVARIANTS": inv, "SHA": {"REGIONS": hashlib.sha256(p.read_bytes()).hexdigest()[:16], "OPENINGS": hashlib.sha256(q.read_bytes()).hexdigest()[:16]}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))

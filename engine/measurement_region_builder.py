"""QS_MEASUREMENT_REGION_BUILDER - the four-layer output contract (§8, §9).

Wraps engine.qs_measurement_region.build_region (which owns the ring test
and the synthetic closures) and returns the record shape the directive
requires, with every virtual closure stamped

    MATERIAL_PRESENT = False, PHYSICAL_WALL = False, GEOMETRY_AUTHORITY = False

and the four layers kept apart by name:
    PHYSICAL_GEOMETRY -> TOPOLOGICAL_RELATION -> QS_MEASUREMENT_GEOMETRY -> TRADE_QUANTITY
This module stops at the third layer: it computes a GROSS_BASIS (sum of
contributing physical edge lengths) and lists the openings; deductions
and net areas are the trade engine's.
"""

from __future__ import annotations

from engine import qs_measurement_region as QSMR
from engine.quantity_state import weakest

LAYERS = ("PHYSICAL_GEOMETRY", "TOPOLOGICAL_RELATION",
          "QS_MEASUREMENT_GEOMETRY", "TRADE_QUANTITY")
CLOSURE_STAMP = {"MATERIAL_PRESENT": False, "PHYSICAL_WALL": False,
                 "GEOMETRY_AUTHORITY": False, "LAYER": "QS_MEASUREMENT_GEOMETRY"}


def build(*, region_id, physical_geometry, topological_relations, opening_register,
          trade, measurement_basis, owner_rule_version, project_rule_version) -> dict:
    r = QSMR.build_region(region_id=region_id, physical_edges=physical_geometry,
                          sites=topological_relations, openings=opening_register,
                          trade=trade, basis=measurement_basis)
    closures = [dict(c, **CLOSURE_STAMP) for c in r["SYNTHETIC_CLOSURES"]]
    for c in closures:
        assert c["material_present"] is False and c["quantity_length_contribution"] == 0.0
    contributing = r["GROSS_BASIS"]["CONTRIBUTING_EDGES"]
    non = r["GROSS_BASIS"]["NON_CONTRIBUTING_EDGES"]
    open_edges = [e["EDGE_ID"] for e in physical_geometry if e["KIND"] == "OPEN_PHYSICAL_EDGE"]
    unresolved = [e["EDGE_ID"] for e in physical_geometry if e["KIND"] == "UNRESOLVED_EDGE"]
    unresolved_sites = [s["SITE_ID"] for s in topological_relations if s["SITE_TYPE"] == "UNRESOLVED_GAP"]
    gross = r["GROSS_BASIS"]["VALUE"]
    by_id = {e["EDGE_ID"]: e for e in physical_geometry}
    states = [by_id[e["EDGE_ID"]].get("STATE", "NOT_ESTABLISHED") for e in contributing] or ["NOT_ESTABLISHED"]
    formed = r["MEASUREMENT_REGION_STATUS"] != "MEASUREMENT_REGION_NOT_ESTABLISHED"
    qstate = ("NOT_ESTABLISHED" if not formed or unresolved else weakest(states))
    return {
        "MEASUREMENT_REGION_ID": region_id, "TRADE": trade,
        "MEASUREMENT_BASIS": measurement_basis,
        "OWNER_RULE_VERSION": owner_rule_version, "PROJECT_RULE_VERSION": project_rule_version,
        "LAYER_OF_THIS_RECORD": "QS_MEASUREMENT_GEOMETRY",
        "PHYSICAL_EDGES": [dict(e, LAYER="PHYSICAL_GEOMETRY") for e in physical_geometry],
        "VIRTUAL_CLOSURES": closures,
        "OPEN_EDGES": open_edges,
        "OPENINGS": [dict(o, LAYER="PHYSICAL_GEOMETRY") for o in opening_register],
        "GROSS_BASIS": {"UNIT": "lm", "VALUE": gross, "CONTRIBUTING_EDGES": contributing,
                        "NON_CONTRIBUTING_EDGES": non,
                        "RULE": "sum of contributing physical edge lengths; closures contribute 0"},
        "DEDUCTIONS": "TRADE_QUANTITY layer (engine.wall_treatment_engine)",
        "ADDITIONS": "TRADE_QUANTITY layer",
        "NET_BASIS": "TRADE_QUANTITY layer",
        "UNRESOLVED_RELATIONS": {"UNRESOLVED_EDGES": unresolved, "UNRESOLVED_GAPS": unresolved_sites},
        "FORMED": formed, "MEASUREMENT_REGION_STATUS": r["MEASUREMENT_REGION_STATUS"],
        "WHY_NOT_FORMED": r["NOT_ESTABLISHED_BECAUSE"],
        "PROVENANCE": {"REGION_BUILDER": QSMR.RULE_VERSION,
                       "INVARIANTS": r.get("INVARIANTS"), "RAW": {k: r[k] for k in r if k not in (
                           "PHYSICAL_EDGES", "SYNTHETIC_CLOSURES", "OPENINGS", "GROSS_BASIS")}},
        "QUANTITY_STATE": qstate,
    }

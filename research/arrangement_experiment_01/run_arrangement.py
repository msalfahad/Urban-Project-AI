"""Build the hard arrangement from frozen E1.4 evidence. Research only."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from engine import interval_role as ir
from research.arrangement_experiment_01 import arrangement as A
from research.arrangement_experiment_01 import protocol as P
from tools import run_e1_4 as r14

OUT = Path("data/experiments/ARRANGEMENT_EXPERIMENT_01")


class Args:
    decode = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
    a18_dir = "data/runs/7757/blind/A18-GF-001"
    raster = "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg"
    rules = "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json"
    prior_e1_3 = "data/runs/7757/e1_3"
    sandbox = ""
    v2_sandbox = ""
    out = "data/runs/7757/e1_4"


def main() -> int:
    t0 = time.time()
    a = Args()
    st = r14._core(a)
    t_core = time.time() - t0

    built = st["built"]
    pieces = built["pieces"]
    iv_by_id = st["iv_by_id"]
    exposed = set(st["owner"]["object_ids_that_own_the_room_face"])
    gf_by_id = {p.object_id: p for p in st["gf"]["primitives"]}

    def role_of(oid):
        iv = iv_by_id.get(oid)
        return iv.role if iv is not None else None

    # curve provenance: the analytical arc behind a linearised edge
    curves = {}
    for pc in pieces:
        oid = pc.get("object_id") or ""
        iv = iv_by_id.get(oid)
        if iv is None or iv.kind not in ("ARC", "CIRCLE"):
            continue
        parent = gf_by_id.get(iv.parent_object_id)
        if parent is None:
            continue
        pc["curve"] = {
            "ANALYTICAL_KIND": iv.kind,
            "SOURCE_ENTITY_ID": iv.parent_object_id,
            "SOURCE_INTERVAL_ID": oid,
            "centre_mm": [getattr(parent, "cx", None),
                          getattr(parent, "cy", None)],
            "radius_mm": getattr(parent, "radius", None),
            "TOPOLOGY_LINEARISATION_TOLERANCE_MM":
                A.ARC_TOPOLOGY_TOLERANCE_MM,
            "the_linearisation_is_not_the_geometry":
                A.A_LINEARISATION_IS_NOT_THE_GEOMETRY,
        }
        curves[oid] = pc["curve"]

    portals = [g for g in st["gaps"]["rows"] if g.get("IS_A_PORTAL")]
    unresolved = [g for g in st["gaps"]["rows"]
                  if g.get("GAP_CLASS") == "UNRESOLVED_GAP"]

    # object-level pairing, so a face inside a wall can be recognised
    mates_by_object = {}
    for i, ms in (built["mates"] or {}).items():
        pi = (pieces[i].get("object_id") or "").split("#")[0]
        for m in ms:
            pj = (pieces[m["mate"]].get("object_id") or "").split("#")[0]
            if pi and pj:
                mates_by_object.setdefault(pi, set()).add(pj)
    mates_by_object = {k: sorted(v) for k, v in mates_by_object.items()}

    t1 = time.time()
    arr = A.build(pieces, portals=portals, unresolved=unresolved,
                  role_of=role_of, exposed_ids=exposed)
    cells, edges = A.attach_edges_to_cells(arr["cells"], arr["edges"])
    cells = A.classify_cells(cells, edges, mates_by_object=mates_by_object)
    t_arr = time.time() - t1

    counts = {}
    for c in cells:
        counts[c["CELL_CLASS"]] = counts.get(c["CELL_CLASS"], 0) + 1
    by_role = {}
    for e in edges:
        by_role[e["EDGE_ROLE"]] = by_role.get(e["EDGE_ROLE"], 0) + 1

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "arrangement").mkdir(exist_ok=True)

    def write(name, body):
        p = OUT / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                                default=str) + "\n", encoding="utf-8")
        return hashlib.sha256(p.read_bytes()).hexdigest()

    write("arrangement/HARD_EDGE_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "METHOD": P.METHOD_1,
        "HARD_EDGE_ROLES": list(P.HARD_EDGE_ROLES),
        "SEPARATES": list(P.SEPARATES),
        "DOES_NOT_SEPARATE": list(P.DOES_NOT_SEPARATE),
        "SEPARATION_UNRESOLVED": list(P.SEPARATION_UNRESOLVED),
        "why_a_non_material_edge_exists_at_all":
            P.WHY_A_NON_MATERIAL_EDGE_EXISTS_AT_ALL,
        "a_soft_partition_is_never_a_wall": P.A_SOFT_PARTITION_IS_NEVER_A_WALL,
        "NO_SOFT_PARTITION_IS_PRESENT_IN_THIS_REGISTER": True,
        "what_the_arrangement_was_not_given":
            list(P.WHAT_THE_ARRANGEMENT_MAY_NOT_BE_GIVEN),
        "edges": len(edges),
        "edges_by_role": by_role,
        "material_length_mm": round(
            sum(e["WALL_LENGTH_CONTRIBUTION_MM"] for e in edges), 3),
        "non_material_edges": sum(1 for e in edges
                                  if not e["MATERIAL_PRESENT"]),
        "EDGES": edges,
    })
    write("arrangement/CELL_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "METHOD": P.METHOD_1,
        "CELL_CLASSES": list(P.CELL_CLASSES),
        "wall_thickness_is_not_room": P.WALL_THICKNESS_IS_NOT_ROOM,
        "cells": len(cells),
        "cells_by_class": counts,
        "free_space_area_mm2": round(
            sum(c["area_mm2"] for c in cells
                if c["CELL_CLASS"] == P.FREE_SPACE_CELL), 3),
        "CELLS": [{k: v for k, v in c.items() if k != "_geom"}
                  for c in cells],
    })
    write("arrangement/CELL_ADJACENCY_REGISTER.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "ADJACENCY": [{"CELL_ID": c["CELL_ID"],
                       "CELL_CLASS": c["CELL_CLASS"],
                       "ADJACENT_CELL_IDS": c["ADJACENT_CELL_IDS"],
                       "BOUNDING_EDGE_IDS": c["BOUNDING_EDGE_IDS"]}
                      for c in cells],
    })
    write("arrangement/CURVE_PROVENANCE.json", {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "a_linearisation_is_not_the_geometry":
            A.A_LINEARISATION_IS_NOT_THE_GEOMETRY,
        "TOPOLOGY_LINEARISATION_TOLERANCE_MM": A.ARC_TOPOLOGY_TOLERANCE_MM,
        "analytical_curve_source_intervals": len(curves),
        "CURVES": curves,
    })

    import pickle
    (OUT / "_cache").mkdir(exist_ok=True)
    with open(OUT / "_cache" / "arrangement.pkl", "wb") as fh:
        pickle.dump({"cells": cells, "edges": edges, "st_keys": "not cached"},
                    fh)

    print(json.dumps({
        "edges": len(edges),
        "edges_by_role": by_role,
        "cells": len(cells),
        "cells_by_class": counts,
        "analytical_curves_retained": len(curves),
        "seconds_rebuilding_e1_4_evidence": round(t_core, 1),
        "seconds_building_the_arrangement": round(t_arr, 1),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Why does the admitted edge set enclose so little? A measurement.

The hard arrangement built from exactly what E1.4 admits encloses almost
nothing. Before concluding anything about the REPRESENTATION, this asks
whether the arrangement is starved by E1.4's evidence gates or by the
drawing itself, by building the same arrangement from four progressively
wider edge sets and reporting what each encloses.

This rewrites no classifier and changes no E1.4 output. It measures.
"""

from __future__ import annotations

import json
from pathlib import Path

from engine import boundary_capability as bcap
from engine import boundary_walk as bw
from engine import cad_geometry as cg
from engine import interval_role as ir
from tools import run_e1_2 as r12
from tools import run_e1_4 as r14

OUT = Path("data/experiments/ARRANGEMENT_EXPERIMENT_01")
SLIVER_MM2 = 1.0e5


class Args:
    decode = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
    a18_dir = "data/runs/7757/blind/A18-GF-001"
    raster = "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg"
    rules = "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json"
    prior_e1_3 = "data/runs/7757/e1_3"
    sandbox = ""
    v2_sandbox = ""
    out = "data/runs/7757/e1_4"


def _faces(prims, extra_spans, snap_mm=1.0):
    from shapely.geometry import LineString
    from shapely.ops import polygonize, unary_union
    look = []
    for m in prims:
        role = bcap.boundary_role_for(m.interval.role,
                                      kind=m.interval.kind)["BOUNDARY_ROLE"]
        sg = cg._as_segment(m, role=role)
        try:
            pts = sg.points(tol_mm=cg.DENSIFY_TOL_MM)
        except Exception:
            continue
        if len(pts) >= 2:
            look.append({"points": pts, "key": sg.object_id,
                         "object_id": sg.object_id,
                         "boundary_role": sg.role, "layer": sg.layer})
    pieces = bw.pieces_from(look, tol_mm=cg.DENSIFY_TOL_MM)
    lines = []
    for pc in pieces:
        pts = [(round(x / snap_mm) * snap_mm, round(y / snap_mm) * snap_mm)
               for x, y in pc["coords"]]
        ded = [pts[0]] + [p for i, p in enumerate(pts[1:], 1)
                          if p != pts[i - 1]]
        if len(ded) >= 2:
            lines.append(LineString(ded))
    for s in extra_spans:
        a = tuple(round(v / snap_mm) * snap_mm for v in s["start_mm"])
        b = tuple(round(v / snap_mm) * snap_mm for v in s["end_mm"])
        if a != b:
            lines.append(LineString([a, b]))
    faces = list(polygonize(unary_union(lines)))
    big = [f for f in faces if f.area > SLIVER_MM2]
    return {
        "intervals_offered": len(prims),
        "length_offered_m": round(
            sum(m.interval.length_mm for m in prims) / 1000.0, 1),
        "noded_pieces": len(pieces),
        "faces": len(faces),
        "faces_larger_than_0_1_m2": len(big),
        "enclosed_area_m2": round(sum(f.area for f in faces) / 1e6, 1),
        "enclosed_area_in_big_faces_m2": round(
            sum(f.area for f in big) / 1e6, 1),
    }


def main() -> int:
    a = Args()
    st = r14._core(a)
    interp, gf = st["interp"], st["gf"]
    by_id = {p.object_id: p for p in gf["primitives"]}
    sem = {r["INTERVAL_ID"]: r for r in st["semantics"]["ROWS"]}
    hidden = set(st["owner"]["object_ids_that_do_not_own_the_room_face"])
    allp = r12.interval_prims(interp["roles"]["intervals"], by_id,
                              only_material=False)

    portals = [g for g in st["gaps"]["rows"] if g.get("IS_A_PORTAL")]
    unres = [g for g in st["gaps"]["rows"]
             if g.get("GAP_CLASS") == "UNRESOLVED_GAP"]
    spans = [{"start_mm": tuple(g["start_mm"]), "end_mm": tuple(g["end_mm"])}
             for g in portals + unres]

    def keep(fn):
        return [m for m in allp if m.interval.length_mm > 0 and fn(m.interval)]

    sets = {
        "A_E1_4_ADMITTED": keep(lambda iv: (
            bcap.may_bound_a_clear_floor_region(iv.role)
            and sem.get(iv.interval_id, {}).get("MAY_BE_ASKED_TO_BOUND")
            and ((iv.provenance or {}).get("object_id")
                 or iv.parent_object_id) not in hidden)),
        "B_PLUS_NOT_IN_THE_CUT_PLANE": keep(lambda iv: (
            bcap.may_bound_a_clear_floor_region(iv.role)
            and ((iv.provenance or {}).get("object_id")
                 or iv.parent_object_id) not in hidden)),
        "C_PLUS_HELD_BACK_STRUCTURE": keep(
            lambda iv: bcap.may_bound_a_clear_floor_region(iv.role)),
        "D_E1_2_MAY_BOUND_MATERIAL": keep(lambda iv: iv.may_bound_material),
    }

    rows = {}
    for name, prims in sets.items():
        rows[name] = _faces(prims, spans)
        rows[name]["with_portal_and_unresolved_spans"] = len(spans)
        print(name, json.dumps(rows[name]))

    body = {
        "EXPERIMENT_ID": "ARRANGEMENT_EXPERIMENT_01",
        "WHAT_THIS_MEASURES": (
            "whether the hard arrangement is starved by E1.4's evidence "
            "gates or by the drawing itself. Four progressively wider edge "
            "sets, the same arrangement, and what each encloses"),
        "NO_CLASSIFIER_WAS_REWRITTEN": True,
        "NOTHING_HERE_IS_A_METHOD": (
            "these are diagnostics. Only set A is the experiment's hard "
            "arrangement; B, C and D exist to locate the cause"),
        "SNAP_MM": 1.0,
        "SETS": {
            "A_E1_4_ADMITTED": "role gate + line semantics + ownership",
            "B_PLUS_NOT_IN_THE_CUT_PLANE": "A plus hidden-linetype linework",
            "C_PLUS_HELD_BACK_STRUCTURE": "B plus structure held back by "
                                          "clear-face ownership",
            "D_E1_2_MAY_BOUND_MATERIAL": "everything frozen E1.2 would admit",
        },
        "RESULTS": rows,
    }
    p = OUT / "arrangement" / "EDGE_SET_DIAGNOSTIC.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

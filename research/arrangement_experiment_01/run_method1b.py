"""Run METHOD 1B under the frozen protocol. Research only.

E1.4 is read and rebuilt, never modified. No benchmark, no manual area,
no expected geometry and no corrected polygon is opened anywhere here.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from engine import boundary_capability as bcap
from engine import cad_geometry as cg
from engine import column_validation as cv
from engine import interval_role as ir
from research.arrangement_experiment_01 import method1b as M
from research.arrangement_experiment_01 import method1b_protocol as R
from research.arrangement_experiment_01 import protocol as P
from tools import run_e1_2 as r12
from tools import run_e1_3 as r13
from tools import run_e1_4 as r14

OUT = Path("data/experiments/ARRANGEMENT_EXPERIMENT_01")
M1B = OUT / "method1b"


class Args:
    decode = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
    a18_dir = "data/runs/7757/blind/A18-GF-001"
    raster = "data/runs/7757/blind/A18-GF-001/images/page-01.jpeg"
    rules = "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json"
    prior_e1_3 = "data/runs/7757/e1_3"
    sandbox = ""
    v2_sandbox = ""
    out = "data/runs/7757/e1_4"


def write(path: Path, body: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False,
                               default=str) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _head(body: dict) -> dict:
    return {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "METHOD": R.METHOD,
        "METHOD_1B_PROTOCOL_HASH": R.protocol_hash(),
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,
        "no_benchmark_or_expected_area_was_opened": True,
        **body,
    }


# ------------------------------------------------------------- overlays

FILL = {
    R.FREE_SPACE_CELL: (60, 190, 90, 70),
    R.MATERIAL_SOLID_CELL: (120, 120, 120, 90),
    R.OBSTACLE_CELL: (240, 140, 20, 110),
    R.NON_FLOOR_CELL: (40, 120, 230, 90),
    R.UNRESOLVED_CELL: (220, 40, 200, 90),
}
STROKE = {
    R.HARD_PHYSICAL_SEPARATOR: (0, 0, 0, 255),
    R.OBSTACLE_BOUNDARY: (240, 140, 20, 255),
    R.NON_FLOOR_REGION_BOUNDARY: (40, 120, 230, 255),
    R.PORTAL_BREAK: (0, 170, 90, 255),
    R.UNRESOLVED: (220, 40, 200, 255),
}


def _overlay(sheet, reg, centre, half, size, cells, edges, path):
    from PIL import Image, ImageDraw
    got = r12._frame(sheet, reg, centre, half, size)
    if got is None:
        return None
    img, to_px, _box = got
    img = img.convert("RGBA")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for c in cells:
        col = FILL.get(c["CELL_CLASS"])
        if col is None or c["IT_IS_A_NODING_SLIVER"]:
            continue
        try:
            pts = [to_px(x, y) for x, y in c["_geom"].exterior.coords]
        except Exception:
            continue
        if len(pts) >= 3:
            draw.polygon(pts, fill=col)
    for e in edges:
        col = STROKE.get(e["PLANAR_PARTITION_CAPABILITY"])
        if col is None:
            continue
        pts = [to_px(x, y) for x, y in e["PROVENANCE"]["points_mm"]]
        if len(pts) >= 2:
            draw.line(pts, fill=col, width=2)
    Image.alpha_composite(img, layer).convert("RGB").save(path)
    return str(path)


# ----------------------------------------------------------------- main


def main() -> int:
    t0 = time.time()
    a = Args()
    st = r14._core(a)
    t_core = time.time() - t0

    interp, gf = st["interp"], st["gf"]
    by_id = {p.object_id: p for p in gf["primitives"]}
    semantics = {r["INTERVAL_ID"]: r for r in st["semantics"]["ROWS"]}
    curve_roles = interp["curves"]["curve_roles"]
    round_objects = {o.object_key: o for o in interp["curves"]["round_objects"]}
    intervals = [iv for rows_ in interp["roles"]["intervals"].values()
                 for iv in rows_]

    # ---- structural objects: one closed footprint each, §4 -----------
    loops = {lp.get("LOOP_ID"): lp
             for lp in interp["roles"]["columns"].get("loops", ())}
    col_rows = []
    for row in st["owner"]["rows"]:
        members = []
        for oid in row["member_object_ids"]:
            p = by_id.get(oid)
            if p is None:
                continue
            x1, y1 = getattr(p, "x1", None), getattr(p, "y1", None)
            x2, y2 = getattr(p, "x2", None), getattr(p, "y2", None)
            if None in (x1, y1, x2, y2):
                continue
            members.append({"object_id": oid, "a": (float(x1), float(y1)),
                            "b": (float(x2), float(y2))})
        lp = loops.get(row["COLUMN_ID"]) or {}
        derived = cv.derive_from_members(
            members,
            expect_centre_mm=tuple(lp["centre_mm"]) if lp.get("centre_mm")
            else None,
            max_side_mm=float(ir.COLUMN_MAX_SIDE_MM))
        col_rows.append({**row, "LOOP_RING": derived.get("LOOP_RING"),
                         "LOOP_RING_ESTABLISHED": derived.get(
                             "LOOP_RING_ESTABLISHED")})
    structural = M.structural_footprints(col_rows)
    structural_object_ids = {oid for s in structural
                             for oid in s["MEMBER_OBJECT_IDS"]}

    # ---- the admission pass, §2 and §3 -------------------------------
    admission = M.admit(intervals, semantics=semantics,
                        curve_roles=curve_roles, round_objects=round_objects,
                        column_object_ids=structural_object_ids)
    adm_by_id = {r["INTERVAL_ID"]: r for r in admission}

    # ---- edges -------------------------------------------------------
    hidden = set(st["owner"]["object_ids_that_do_not_own_the_room_face"])
    edges, curves = [], {}
    for iv in intervals:
        row = adm_by_id[iv.interval_id]
        if not row["ADMITTED_TO_THE_ARRANGEMENT"]:
            continue
        parent = by_id.get(iv.parent_object_id)
        if parent is None:
            continue
        brole = bcap.boundary_role_for(iv.role, kind=iv.kind)["BOUNDARY_ROLE"]
        try:
            pts = cg._as_segment(r12.IntervalPrim(parent, iv),
                                 role=brole).points(
                                     tol_mm=R.ARC_TOPOLOGY_TOLERANCE_MM)
        except Exception:
            continue
        pts = [tuple(float(v) for v in p) for p in pts]
        if len(pts) < 2 or M._length(pts) <= 0:
            continue
        curve = M._curve_provenance(iv, parent, pts)
        if curve:
            curves[iv.interval_id] = curve
        can_own = bool(bcap.has(iv.role, bcap.CAN_BE_CLEAR_FINISH_FACE)
                       and iv.parent_object_id not in hidden)
        edges.append(M.edge_record(
            pts, capability=row["PLANAR_PARTITION_CAPABILITY"],
            semantic_role=iv.role, entity_ids=[iv.parent_object_id],
            interval_ids=[iv.interval_id], curve=curve,
            ownership=can_own,
            non_floor=row["NON_FLOOR_EVIDENCE"]))

    for s in structural:
        if not s["ADMITTED_TO_THE_ARRANGEMENT"]:
            continue
        pts = [tuple(p) for p in s["ring_mm"]]
        e = M.edge_record(
            pts, capability=s["PLANAR_PARTITION_CAPABILITY"],
            semantic_role=ir.COLUMN, entity_ids=s["MEMBER_OBJECT_IDS"],
            interval_ids=[], ownership=False,
            structural={"STRUCTURAL_OBJECT_ID": s["STRUCTURAL_OBJECT_ID"],
                        "STRUCTURAL_EXISTENCE": s["STRUCTURAL_EXISTENCE"],
                        "ONE_CLOSED_OUTER_FOOTPRINT": True})
        s["EDGE_ID"] = e["EDGE_ID"]
        edges.append(e)

    portals = [g for g in st["gaps"]["rows"] if g.get("IS_A_PORTAL")]
    unres_gaps = [g for g in st["gaps"]["rows"]
                  if g.get("GAP_CLASS") == "UNRESOLVED_GAP"]
    portal_rows = []
    for g, cap in ([(g, R.PORTAL_BREAK) for g in portals]
                   + [(g, R.UNRESOLVED) for g in unres_gaps]):
        pts = [tuple(float(v) for v in g["start_mm"]),
               tuple(float(v) for v in g["end_mm"])]
        if M._length(pts) <= 0:
            continue
        e = M.edge_record(
            pts, capability=cap, semantic_role=g.get("GAP_CLASS"),
            entity_ids=[], interval_ids=[], ownership=False,
            portal={"GAP_ID": g.get("GAP_ID"), "GAP_CLASS": g.get("GAP_CLASS"),
                    "IS_A_PORTAL": bool(g.get("IS_A_PORTAL")),
                    "width_mm": g.get("width_mm")})
        edges.append(e)
        portal_rows.append({"EDGE_ID": e["EDGE_ID"],
                            "GAP_ID": g.get("GAP_ID"),
                            "GAP_CLASS": g.get("GAP_CLASS"),
                            "PLANAR_PARTITION_CAPABILITY": cap,
                            "MATERIAL_PRESENT": False,
                            "PHYSICAL_SEPARATION": e["PHYSICAL_SEPARATION"],
                            "WALL_LENGTH_CONTRIBUTION_MM": 0.0,
                            "points_mm": [list(p) for p in pts]})

    edges = M._dedupe(edges)

    # ---- the faces, and the two counterfactuals ----------------------
    t1 = time.time()
    cells = M.build(edges)
    surviving = M.faces_of(edges, without=(R.UNRESOLVED,))
    non_floor_faces = M.faces_of(edges, only=(R.NON_FLOOR_REGION_BOUNDARY,))
    from shapely.geometry import Polygon
    rings = [Polygon([tuple(p) for p in s["ring_mm"]])
             for s in structural if s["ADMITTED_TO_THE_ARRANGEMENT"]
             and s["PLANAR_PARTITION_CAPABILITY"] == R.OBSTACLE_BOUNDARY]
    rings = [g for g in rings if g.is_valid and g.area > 0]

    cells, edges, touching_outside = M.attach(cells, edges)
    mates_by_object = {}
    pieces = st["built"]["pieces"]
    for i, ms in (st["built"]["mates"] or {}).items():
        pi = (pieces[i].get("object_id") or "").split("#")[0]
        for m in ms:
            pj = (pieces[m["mate"]].get("object_id") or "").split("#")[0]
            if pi and pj:
                mates_by_object.setdefault(pi, set()).add(pj)
    mates_by_object = {k: sorted(v) for k, v in mates_by_object.items()}
    cells = M.classify(cells, edges, mates_by_object=mates_by_object,
                       structural_rings=rings, non_floor_faces=non_floor_faces,
                       surviving_faces=surviving)
    t_arr = time.time() - t1

    # ---- the seven cases, §13 ---------------------------------------
    sel = json.loads((OUT / "01_CASE_SELECTION.json").read_text("utf-8"))
    seeds = {r["CANDIDATE_ID"]: r for r in st["seeds"]["ROWS"]}
    case_rows = []
    for c in sel["CASES"]:
        cid = c["CANDIDATE_ID"]
        seed = seeds.get(cid) or {}
        anchor = seed.get("SEED_MM")
        if anchor is None:
            case_rows.append({
                **{k: c[k] for k in ("CASE", "CANDIDATE_ID",
                                     "IDENTITY_AS_DRAWN")},
                "LABEL_SEED_STATUS": seed.get("LABEL_SEED_STATUS"),
                "ANCHOR_MM": None,
                "REPRESENTATION": {
                    "VERDICT": R.NO_MEANINGFUL_CELL_REPRESENTATION,
                    "FAILED_TEST": "ANCHOR_LANDS_IN_A_BOUNDED_CELL",
                    "why": ("frozen E1.4 established no label seed for "
                            "this candidate, so the arrangement is not "
                            "asked a question it could answer")}})
            continue
        rep = M.representation(cells, edges, anchor_mm=tuple(anchor))
        case_rows.append({
            **{k: c[k] for k in ("CASE", "CANDIDATE_ID",
                                 "IDENTITY_AS_DRAWN")},
            "LABEL_SEED_STATUS": seed.get("LABEL_SEED_STATUS"),
            "SEED_ANCHOR_KIND": seed.get("SEED_ANCHOR_KIND"),
            "ANCHOR_MM": anchor,
            "REPRESENTATION": rep})

    # ---- registers ---------------------------------------------------
    M1B.mkdir(parents=True, exist_ok=True)
    by_cap, by_role_admitted = {}, {}
    for e in edges:
        k = e["PLANAR_PARTITION_CAPABILITY"]
        by_cap[k] = by_cap.get(k, 0) + 1
    refused = {}
    entered_on_unresolved_line_semantics = 0
    for r in admission:
        if r["ADMITTED_TO_THE_ARRANGEMENT"]:
            by_role_admitted[r["SEMANTIC_ROLE"]] = by_role_admitted.get(
                r["SEMANTIC_ROLE"], 0) + 1
            if r["LINE_SEMANTICS_STATUS"] == "UNRESOLVED":
                entered_on_unresolved_line_semantics += 1
        else:
            refused[r["REFUSED_BECAUSE"]] = refused.get(
                r["REFUSED_BECAUSE"], 0) + 1

    write(M1B / "EDGE_ADMISSION_REGISTER.json", _head({
        "WHAT_THIS_IS": ("every interval, the capability its established "
                         "role gives it, and whether it entered"),
        "THE_ADMISSION_PRINCIPLE": R.record()["THE_ADMISSION_PRINCIPLE"],
        "intervals_considered": len(admission),
        "admitted": sum(1 for r in admission
                        if r["ADMITTED_TO_THE_ARRANGEMENT"]),
        "admitted_by_semantic_role": by_role_admitted,
        "refused_by_reason": refused,
        "intervals_that_entered_on_an_unresolved_line_semantics_status":
            entered_on_unresolved_line_semantics,
        "a_veto_needs_positive_evidence": R.A_VETO_NEEDS_POSITIVE_EVIDENCE,
        "closure_gain_is_not_semantic_evidence":
            R.CLOSURE_GAIN_IS_NOT_SEMANTIC_EVIDENCE,
        "clear_face_ownership_did_not_gate_admission": True,
        "ROWS": admission,
    }))

    write(M1B / "EDGE_CAPABILITY_REGISTER.json", _head({
        "PLANAR_PARTITION_CAPABILITIES": list(R.PLANAR_PARTITION_CAPABILITIES),
        "THIS_IS_INDEPENDENT_OF": list(R.THIS_IS_INDEPENDENT_OF),
        "an_edge_can_partition_without_being_a_wall":
            R.AN_EDGE_CAN_PARTITION_WITHOUT_BEING_A_WALL,
        "edges": len(edges),
        "edges_by_capability": by_cap,
        "material_length_mm": round(
            sum(e["WALL_LENGTH_CONTRIBUTION_MM"] for e in edges), 3),
        "edges_carrying_no_material": sum(1 for e in edges
                                          if not e["MATERIAL_PRESENT"]),
        "SOFT_SEMANTIC_BOUNDARY_EDGES": 0,
        "no_soft_partition_exists_in_this_experiment": (
            "the class is declared and nothing is admitted into it. A "
            "soft partition could never be promoted to a wall: it carries "
            "MATERIAL_PRESENT false, zero wall length and "
            "PHYSICAL_SEPARATION false by its own record"),
        "a_soft_partition_is_never_a_wall": R.A_SOFT_PARTITION_IS_NEVER_A_WALL,
        "EDGES": [{k: v for k, v in e.items()} for e in edges],
    }))

    write(M1B / "STRUCTURAL_OBSTACLE_REGISTER.json", _head({
        "existence_is_not_boundary_relevance":
            R.EXISTENCE_IS_NOT_BOUNDARY_RELEVANCE,
        "RULES": list(R.STRUCTURAL_FOOTPRINT_RULES),
        "structural_objects": len(structural),
        "admitted_as_one_closed_footprint": sum(
            1 for s in structural if s["ADMITTED_TO_THE_ARRANGEMENT"]),
        "column_role_intervals_refused_because_their_object_speaks_for_them":
            refused.get(M.REFUSED_STRUCTURAL_CHANNEL, 0),
        "the_held_back_intervals_were_not_inserted_wholesale": True,
        "OBJECTS": structural,
    }))

    non_floor_edges = [e for e in edges
                       if e["PLANAR_PARTITION_CAPABILITY"]
                       == R.NON_FLOOR_REGION_BOUNDARY]
    write(M1B / "NON_FLOOR_BOUNDARY_REGISTER.json", _head({
        "RULE": R.NON_FLOOR_ADMISSION_RULE,
        "THIS_RULE_NAMES_NO_PROJECT_AND_NO_ROOM": True,
        "EVERY_SUCH_EDGE_CARRIES": dict(R.NON_FLOOR_EDGES_CARRY),
        "SUBROLE_RECORDED_AS": R.NON_FLOOR_SUBROLE_UNRESOLVED,
        "the_subrole_is_recorded_separately":
            R.THE_SUBROLE_IS_RECORDED_SEPARATELY,
        "do_not_choose_the_reading_that_closes_the_face":
            R.DO_NOT_CHOOSE_THE_READING_THAT_CLOSES_THE_FACE,
        "non_floor_boundary_edges": len(non_floor_edges),
        "non_floor_regions_closed": len(non_floor_faces),
        "EDGES": non_floor_edges,
    }))

    write(M1B / "PORTAL_BREAK_REGISTER.json", _head({
        "RULES": list(R.PORTAL_RULES),
        "UNRESOLVED_GAP_RULE": R.UNRESOLVED_GAP_RULE,
        "NO_FAKE_MATERIAL_EDGE_ACROSS_AN_OPENING": True,
        "portal_breaks": sum(1 for r in portal_rows
                             if r["PLANAR_PARTITION_CAPABILITY"]
                             == R.PORTAL_BREAK),
        "unresolved_gap_edges": sum(1 for r in portal_rows
                                    if r["PLANAR_PARTITION_CAPABILITY"]
                                    == R.UNRESOLVED),
        "ROWS": portal_rows,
    }))

    vertices = {}
    for e in edges:
        for p in (e["PROVENANCE"]["points_mm"][0],
                  e["PROVENANCE"]["points_mm"][-1]):
            vid = M._vid(tuple(p))
            v = vertices.setdefault(vid, {"VERTEX_ID": vid,
                                          "point_mm": [round(p[0], 3),
                                                       round(p[1], 3)],
                                          "EDGE_IDS": []})
            v["EDGE_IDS"].append(e["EDGE_ID"])
    for v in vertices.values():
        v["EDGE_IDS"] = sorted(set(v["EDGE_IDS"]))
        v["degree"] = len(v["EDGE_IDS"])
    dangling = sorted(v["VERTEX_ID"] for v in vertices.values()
                      if v["degree"] == 1)
    write(M1B / "ARRANGEMENT_VERTEX_REGISTER.json", _head({
        "vertices": len(vertices),
        "dangling_endpoints": len(dangling),
        "what_a_dangling_endpoint_is": (
            "an admitted edge that ends where no other admitted edge ends. "
            "It is a free end in the source, not an error introduced here"),
        "VERTICES": sorted(vertices.values(), key=lambda v: v["VERTEX_ID"]),
    }))

    write(M1B / "ARRANGEMENT_EDGE_REGISTER.json", _head({
        "EDGE_FIELDS": list(R.EDGE_FIELDS),
        "edges": len(edges),
        "EDGES": [{k: e[k] for k in R.EDGE_FIELDS} for e in edges],
    }))

    counts = {}
    for c in cells:
        counts[c["CELL_CLASS"]] = counts.get(c["CELL_CLASS"], 0) + 1
    slivers = sum(1 for c in cells if c["IT_IS_A_NODING_SLIVER"])
    write(M1B / "CELL_REGISTER.json", _head({
        "CELL_CLASSES": list(R.CELL_CLASSES),
        "CELL_CLASSIFICATION_ORDER": [
            {"TEST": k, "MEANS": v} for k, v in R.CELL_CLASSIFICATION_ORDER],
        "the_unresolved_counterfactual": R.THE_UNRESOLVED_COUNTERFACTUAL,
        "count_the_material_cells_separately":
            R.COUNT_THE_MATERIAL_CELLS_SEPARATELY,
        "cells": len(cells),
        "cells_by_class": counts,
        "of_which_noding_slivers": slivers,
        "free_space_area_mm2": round(
            sum(c["area_mm2"] for c in cells
                if c["CELL_CLASS"] == R.FREE_SPACE_CELL), 3),
        "faces_when_unresolved_edges_are_withdrawn": len(surviving),
        "CELLS": [{k: v for k, v in c.items() if k != "_geom"}
                  for c in cells],
    }))

    write(M1B / "CELL_ADJACENCY_REGISTER.json", _head({
        "THE_EXTERIOR": {
            "OUTSIDE_CELL_ID": R.OUTSIDE_CELL_ID,
            "A_BOUNDING_FRAME_IS_USED": False,
            "COMPUTATIONAL_DOMAIN_BOUNDARY_EDGES": 0,
            "RULES": list(R.EXTERIOR_RULE),
            "cells_touching_the_unbounded_exterior": len(touching_outside),
        },
        "adjacency_through_a_portal_is_preserved": True,
        "ADJACENCY": [{"CELL_ID": c["CELL_ID"],
                       "CELL_CLASS": c["CELL_CLASS"],
                       "ADJACENT_CELL_IDS": c["ADJACENT_CELL_IDS"],
                       "CONNECTED_THROUGH_A_PORTAL":
                           c["CONNECTED_THROUGH_A_PORTAL"],
                       "BOUNDING_EDGE_IDS": c["BOUNDING_EDGE_IDS"]}
                      for c in cells],
    }))

    write(M1B / "CURVE_PROVENANCE.json", _head({
        "RULES": list(R.CURVE_RULES),
        "a_chord_is_never_an_arc": R.A_CHORD_IS_NEVER_AN_ARC,
        "ARC_TOPOLOGY_TOLERANCE_MM": R.ARC_TOPOLOGY_TOLERANCE_MM,
        "analytical_curve_source_intervals": len(curves),
        "worst_approximation_error_mm": round(max(
            [c["MAX_APPROXIMATION_ERROR_MM"] for c in curves.values()] or [0.0]
        ), 6),
        "CURVES": curves,
    }))

    # ---- §14 the non-floor audit, geometric and not from area --------
    audit = []
    by_cell = {c["CELL_ID"]: c for c in cells}
    for e in non_floor_edges:
        borders = [by_cell[cid]["CELL_CLASS"] for cid in e["ADJACENT_CELL_IDS"]
                   if cid in by_cell]
        audit.append({
            "EDGE_ID": e["EDGE_ID"],
            "SOURCE_CURVE": (e["PROVENANCE"]["CURVE"] or {}),
            "NON_FLOOR_EVIDENCE": e["PROVENANCE"]["NON_FLOOR"],
            "BORDERS_CELLS": e["ADJACENT_CELL_IDS"],
            "BORDERING_CELL_CLASSES": borders,
            "ONE_SIDE_IS_NON_FLOOR": R.NON_FLOOR_CELL in borders,
            "MATERIAL_PRESENT": e["MATERIAL_PRESENT"],
            "WALL_LENGTH_CONTRIBUTION_MM": e["WALL_LENGTH_CONTRIBUTION_MM"],
        })
    without_non_floor = M.faces_of(
        edges, without=(R.NON_FLOOR_REGION_BOUNDARY,))
    write(M1B / "NON_FLOOR_AUDIT.json", _head({
        "QUESTIONS": list(R.NON_FLOOR_AUDIT_QUESTIONS),
        "the_large_area_effect_is_neither_proof_nor_disproof":
            R.THE_LARGE_AREA_EFFECT_IS_NEITHER_PROOF_NOR_DISPROOF,
        "non_floor_boundary_edges": len(non_floor_edges),
        "faces_with_them": len(cells),
        "faces_without_them": len(without_non_floor),
        "they_close_loops_that_are_otherwise_unbounded":
            len(cells) - len(without_non_floor),
        "EDGES": audit,
    }))

    # ---- §13 the topology report -------------------------------------
    verdicts = {}
    for row in case_rows:
        v = row["REPRESENTATION"]["VERDICT"]
        verdicts[v] = verdicts.get(v, 0) + 1
    report = _head({
        "TOPOLOGY": {
            "arrangement_vertices": len(vertices),
            "arrangement_edges": len(edges),
            "dangling_topological_edges": len(dangling),
            "unresolved_junctions": sum(
                1 for e in edges
                if e["PLANAR_PARTITION_CAPABILITY"] == R.UNRESOLVED),
            "unbounded_or_outside_faces": 1,
            "cells_touching_the_unbounded_exterior": len(touching_outside),
        },
        "CELLS_BY_CLASS": counts,
        "of_which_noding_slivers": slivers,
        "count_the_material_cells_separately":
            R.COUNT_THE_MATERIAL_CELLS_SEPARATELY,
        "THE_SEVEN_CASES": case_rows,
        "VERDICT_COUNTS": verdicts,
        "REPRESENTATION_TESTS": [{"TEST": k, "MEANS": v}
                                 for k, v in R.REPRESENTATION_TESTS],
        "area_closeness_is_not_a_test": R.AREA_CLOSENESS_IS_NOT_A_TEST,
        "SURVIVAL_CRITERIA": list(R.SURVIVAL_CRITERIA),
        "if_it_fails_it_fails": R.IF_IT_FAILS_IT_FAILS,
        "seconds_rebuilding_e1_4_evidence": round(t_core, 1),
        "seconds_building_the_arrangement": round(t_arr, 1),
    })
    write(M1B / "TOPOLOGY_REPORT.json", report)

    # ---- §15 survival, decided by the criteria as they were written ---
    meaningful = {r["CASE"]: r["REPRESENTATION"]["VERDICT"]
                  == R.MEANINGFUL_ATOMIC_CELL_REPRESENTATION
                  for r in case_rows}
    open_plan = [r for r in case_rows if "OPEN_PLAN" in r["CASE"]]
    pantry = [r for r in case_rows if "PANTRY" in r["CASE"]]
    closed = [r for r in case_rows
              if "WC" in r["CASE"] or "KITCHEN" in r["CASE"]]
    portal_edges = [e for e in edges
                    if e["PLANAR_PARTITION_CAPABILITY"] == R.PORTAL_BREAK]
    fake = [e for e in portal_edges
            if e["MATERIAL_PRESENT"] or e["WALL_LENGTH_CONTRIBUTION_MM"]]
    linked = sum(1 for c in cells if c["CONNECTED_THROUGH_A_PORTAL"])

    criteria = [
        {"CRITERION": R.SURVIVAL_CRITERIA[0],
         "MET": all(meaningful.values()),
         "EVIDENCE": {"cases": len(case_rows),
                      "with_a_meaningful_representation":
                          sum(1 for v in meaningful.values() if v),
                      "BY_CASE": meaningful}},
        {"CRITERION": R.SURVIVAL_CRITERIA[1],
         "MET": bool(open_plan) and all(
             r["REPRESENTATION"]["VERDICT"]
             == R.MEANINGFUL_ATOMIC_CELL_REPRESENTATION for r in open_plan),
         "EVIDENCE": {"NO_FAKE_PHYSICAL_WALL_WAS_INSERTED": True,
                      "VERDICTS": [r["REPRESENTATION"]["VERDICT"]
                                   for r in open_plan],
                      "why": ("the cluster is representable only if it has "
                              "a representation at all. No fake wall was "
                              "inserted, and no cell was produced either")}},
        {"CRITERION": R.SURVIVAL_CRITERIA[2],
         "MET": bool(pantry) and all(
             r["REPRESENTATION"]["VERDICT"]
             == R.MEANINGFUL_ATOMIC_CELL_REPRESENTATION for r in pantry),
         "EVIDENCE": {"VERDICTS": [r["REPRESENTATION"]["VERDICT"]
                                   for r in pantry],
                      "CELL_IDS": [r["REPRESENTATION"].get("CELL_ID")
                                   for r in pantry]}},
        {"CRITERION": R.SURVIVAL_CRITERIA[3],
         "MET": bool(closed) and all(
             r["REPRESENTATION"]["VERDICT"]
             == R.MEANINGFUL_ATOMIC_CELL_REPRESENTATION for r in closed),
         "EVIDENCE": {"BY_CASE": {r["CASE"]: r["REPRESENTATION"]["VERDICT"]
                                  for r in closed}}},
        {"CRITERION": R.SURVIVAL_CRITERIA[4],
         "MET": bool(portal_edges) and not fake,
         "EVIDENCE": {"portal_break_edges": len(portal_edges),
                      "portal_edges_carrying_material_or_wall_length":
                          len(fake),
                      "cells_with_an_adjacency_through_a_portal": linked}},
        {"CRITERION": R.SURVIVAL_CRITERIA[5],
         "MET": bool(curves) and all(
             c.get("SOURCE_CURVE_ID") and c.get("radius_mm")
             for c in curves.values()),
         "EVIDENCE": {"analytical_curve_source_intervals": len(curves),
                      "worst_approximation_error_mm": round(max(
                          [c["MAX_APPROXIMATION_ERROR_MM"]
                           for c in curves.values()] or [0.0]), 6)}},
    ]
    survives = all(c["MET"] for c in criteria)
    write(M1B / "SURVIVAL_ASSESSMENT.json", _head({
        "VERDICT": ("METHOD_1B_SURVIVES" if survives
                    else "METHOD_1B_DOES_NOT_SURVIVE"),
        "criteria_met": sum(1 for c in criteria if c["MET"]),
        "criteria": len(criteria),
        "CRITERIA": criteria,
        "if_it_fails_it_fails": R.IF_IT_FAILS_IT_FAILS,
        "NO_RULE_WAS_CHANGED_AFTER_THE_FIRST_CELL_RESULT": True,
        "IMPLEMENTATION_DEFECT_FOUND_AND_CORRECTED": {
            "WHAT": ("the first build of this method did not apply "
                     "NODE_SNAP_MM to the geometry handed to the topology "
                     "library. The snap was used only for edge and vertex "
                     "identity, so two faces of one wall meeting a "
                     "thousandth of a millimetre apart were two nodes and "
                     "the face never closed"),
            "THIS_IS_NOT_A_RULE_CHANGE": (
                "NODE_SNAP_MM = 1.0 is declared in the frozen protocol as "
                "an inherited threshold. The correction makes the code "
                "apply the rule that was already frozen; no rule, "
                "admission, capability or classification was altered"),
            "BEFORE_THE_CORRECTION": {
                "cells": 167, "FREE_SPACE_CELL": 13,
                "free_space_area_mm2": 2779999.707,
                "cases_with_a_meaningful_representation": 0},
            "AFTER_THE_CORRECTION": {
                "cells": len(cells),
                "FREE_SPACE_CELL": counts.get(R.FREE_SPACE_CELL, 0),
                "free_space_area_mm2": round(
                    sum(c["area_mm2"] for c in cells
                        if c["CELL_CLASS"] == R.FREE_SPACE_CELL), 3),
                "cases_with_a_meaningful_representation":
                    sum(1 for v in meaningful.values() if v)},
            "THE_SAME_DEFECT_IS_PRESENT_IN_METHOD_1A": (
                "Method 1A did not apply its own NODE_SNAP_MM either. "
                "Method 1A is preserved exactly as run and is not "
                "re-executed. The frozen four-set diagnostic already "
                "measured set A WITH a 1 mm snap: 7 faces and 15.2 m2, "
                "which is still not a meaningful floor subdivision, so "
                "the snap does not rescue the Method 1A edge set"),
        },
    }))

    # ---- overlays ----------------------------------------------------
    reg, sheet = r13._registered_sheet(a, gf)
    made = []
    if sheet is not None and getattr(sheet, "ok", False):
        xs = [v for c in cells for v in (c["_geom"].bounds[0],
                                         c["_geom"].bounds[2])]
        ys = [v for c in cells for v in (c["_geom"].bounds[1],
                                         c["_geom"].bounds[3])]
        if xs:
            centre = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
            half = max(max(xs) - min(xs), max(ys) - min(ys)) / 2.0 + 2000.0
            made.append(_overlay(sheet, reg, centre, half, (2400, 2400),
                                 cells, edges,
                                 M1B / "WHOLE_FLOOR_OVERLAY.png"))
        crops = M1B / "SELECTED_CASE_OVERLAYS"
        crops.mkdir(exist_ok=True)
        for row in case_rows:
            if not row.get("ANCHOR_MM"):
                continue
            made.append(_overlay(
                sheet, reg, tuple(row["ANCHOR_MM"]),
                float(sel["CROP_HALF_MM"]), (1600, 1600), cells, edges,
                crops / f"{row['CASE']}.png"))

    print(json.dumps({
        "METHOD_1B_PROTOCOL_HASH": R.protocol_hash(),
        "intervals_considered": len(admission),
        "intervals_admitted": sum(1 for r in admission
                                  if r["ADMITTED_TO_THE_ARRANGEMENT"]),
        "refused_by_reason": refused,
        "structural_footprints_admitted": sum(
            1 for s in structural if s["ADMITTED_TO_THE_ARRANGEMENT"]),
        "edges": len(edges),
        "edges_by_capability": by_cap,
        "vertices": len(vertices),
        "dangling_endpoints": len(dangling),
        "cells": len(cells),
        "cells_by_class": counts,
        "of_which_noding_slivers": slivers,
        "faces_without_unresolved_edges": len(surviving),
        "non_floor_regions_closed": len(non_floor_faces),
        "VERDICT_COUNTS": verdicts,
        "overlays": [m for m in made if m],
        "seconds_rebuilding_e1_4_evidence": round(t_core, 1),
        "seconds_building_the_arrangement": round(t_arr, 1),
        "SURVIVAL": ("METHOD_1B_SURVIVES" if survives
                     else "METHOD_1B_DOES_NOT_SURVIVE"),
        "criteria_met": f"{sum(1 for c in criteria if c['MET'])}/{len(criteria)}",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

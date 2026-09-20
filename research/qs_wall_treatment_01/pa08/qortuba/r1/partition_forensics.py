"""PA08-QORTUBA-R1 §2: partition forensics for the merged seven-room cell, written BEFORE any geometry rule changes.

For every boundary responsible for the merged cell: raw entities, layers, entity types, linetypes, block relations, parallel face
pairs, face separation, authored thickness dimensions nearby, door / window block intersections, column / junction relations, the
PA07R2 (blind, frozen) band status and the reason PA07R2 rejected or left it unresolved.  An ablation on the raster proves which
boundaries are causal: sealing a boundary's missing geometry on a copy of the raster and re-labelling shows which labelled rooms separate.

Nothing here changes the engine; the register is the diagnosis the rule changes of §3-§6 must answer to.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from engine.ingest import material_bands as MB, pipeline7 as P7, planar_faces as PF
from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba import blind as B

OUT_R1 = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
BLIND = B.BLIND
MERGED_ANCHOR_WORDS = ("HALL", "BED.ROOM", "M.B.ROOM", "BATH", "DRESS")

# The boundaries of the merged cell, by CAD object id (Qortuba entity handles; forensic addresses, never engine constants).
# GAP_CHORDS are the seal geometry the engine did NOT draw (door / end gaps), as (x0, y0, x1, y1) in view mm, used only by the ablation.
BOUNDARIES = [
    {"ID": "QPB-01", "NAME": "HALL / BED.ROOM(SW) partition, y ~ 150 297-150 497 (200 mm)", "ENTITIES": ["CAD-470", "CAD-477", "CAD-471", "CAD-718.3883d402", "CAD-718.bce4e4ad"],
     "GAP_CHORDS": []},
    {"ID": "QPB-02", "NAME": "BATH(SW) / BED.ROOM(SW) partition, y ~ 148 447-148 597 (150 mm) with the door 1988 at its east end", "ENTITIES": ["CAD-472", "CAD-475", "CAD-473"],
     "GAP_CHORDS": [(1096831, 148447, 1097931, 148447), (1096831, 148597, 1097931, 148597), (1096831, 148447, 1096831, 148597)]},
    {"ID": "QPB-03", "NAME": "BATH(SW) / HALL lobe return, x ~ 1 096 081-1 096 231 (150 mm) with the door 2044 at its south end", "ENTITIES": ["CAD-465", "CAD-467"],
     "GAP_CHORDS": [(1096081, 148597, 1096081, 149497), (1096231, 148597, 1096231, 149497)]},
    {"ID": "QPB-04", "NAME": "HALL / BED.ROOM(SE) partition, y ~ 150 997-151 147 (150 mm) with the 1 900 x 700 closed outline", "ENTITIES": ["CAD-815", "CAD-816", "CAD-1547", "CAD-1548", "CAD-550", "CAD-551", "CAD-1947", "CAD-1948", "CAD-549", "CAD-546"],
     "GAP_CHORDS": [(1099281, 150997, 1099281, 151147), (1099881, 150997, 1099881, 151147)]},
    {"ID": "QPB-05", "NAME": "BED.ROOM(SW) / BED.ROOM(SE) partition, x ~ 1 097 931-1 098 081 (150 mm) with the door 841 at its north end", "ENTITIES": ["CAD-552", "CAD-554", "CAD-555"],
     "GAP_CHORDS": []},
    {"ID": "QPB-06", "NAME": "HALL / DRESS + HALL / M.B.ROOM partition, y ~ 155 747-155 947 with the door 1471", "ENTITIES": ["CAD-518", "CAD-523", "CAD-519", "CAD-525", "CAD-1892"],
     "GAP_CHORDS": []},
    {"ID": "QPB-07", "NAME": "DRESS / M.B.ROOM partition, x ~ 1 098 581-1 098 731 (150 mm) ending 1 200 mm short of the y ~ 155 822 wall", "ENTITIES": ["CAD-1893", "CAD-1895"],
     "GAP_CHORDS": [(1098581, 155897, 1098581, 157097), (1098731, 155897, 1098731, 157097)]},
    {"ID": "QPB-08", "NAME": "BATH(NW) / DRESS partition, x ~ 1 095 681-1 095 831 (150 mm) with the door 1443 at its south end and the wardrobe strip beside it", "ENTITIES": ["CAD-526", "CAD-531", "CAD-514", "CAD-1445", "CAD-517", "CAD-1446"],
     "GAP_CHORDS": [(1095681, 156897, 1095681, 157797), (1095831, 156897, 1095831, 157797), (1095681, 159897, 1095681, 160247), (1095831, 159897, 1095831, 160247)]},
    {"ID": "QPB-09", "NAME": "UNRESOLVED band strips bordering the cell: side chords without end caps (200 mm corridors)", "ENTITIES": [], "GAP_CHORDS": "UNRESOLVED_STRIP_END_CAPS"},
]

FAILURE_CLASSES = {
    "FC-1_ANGLE_FRAME_FLIP": "material_bands._angle returns pi - epsilon (not 0) for a horizontal line whose endpoints differ by ~1e-11 mm in y; the pairing frame (ux, uy) then flips sign for that line, its offset becomes -y instead of +y, and it never pairs with its true parallel face although both lines share direction key 0.  A pure floating-point defect of the generic engine.",
    "FC-2_END_GAP_NOT_CLASSIFIED": "band_topology classifies gaps only INSIDE a band's extent (between covered intervals).  A door drawn at the END of a wall run, against a perpendicular wall (a corner door), is an end gap: the band terminates at the jamb, _end_state records FREE_END, nothing is classified and nothing is sealed.  Qortuba draws most doors this way.",
    "FC-3_UNRESOLVED_STRIP_UNCAPPED": "unresolved_seals chords both faces of an UNRESOLVED band over its extent but never the two ends of the strip; the 150-200 mm interior becomes an open corridor from one end of the wall to the other, joining whatever rooms the ends touch.",
    "FC-4_CLOSED_OUTLINE_BEYOND_THICKNESS_RANGE": "a closed WALL-layer outline 1 900 x 700 mm exceeds THICKNESS[1] = 600 mm, so its long sides never form a candidate pair; the outline is neither a band, a column loop nor a joinery loop and is left unsealed with rooms on both sides.",
    "FC-5_WALL_FACE_ROLE_AS_HATCH_STROKE": "the PA06 primitive role classifier tags a 600 mm WALL-layer face as HATCH_STROKE (member of a family of >= 8 short parallel strokes at regular spacing) because it lies at the same spacing as the sanitary hatch beside it; material_bands re-admits strokes > 300 mm but the angle-frame flip (FC-1) then prevents its pairing.",
    "FC-6_THIN_OR_ISOLATED_PARTITION_DEMOTED": "PA07R2 guards THIN_BAND_UNCONFIRMED (150 mm pair without hatch or end-face evidence) and ISOLATED_PAIR (joined to no established band) demote real 150 mm partitions whose only fill evidence is the authored 15 cm dimensions of the drawing; the demotion is correct as a guard, but the demoted band then loses its end-gap door (FC-2) and its strip corridor (FC-3).",
    "FC-7_FURNITURE_AGAINST_WALL_STRIP_ACCEPTED": "a wall face paired with furniture / fixture lines 600 mm away (a bed or a counter drawn against the wall, partly in a block, partly exploded) forms a 600 mm strip with returns at both ends; END_CAPS_BOTH makes its fill EVIDENCED and it is ACCEPTED, then the true 200 mm partition sharing that face is demoted CLOSED_OUTLINE_AGAINST_WALL.",
    "FC-8_DOOR_LEAF_PARALLEL_TO_HOST": "the Qortuba door block draws leaf + frame only (no swing); the leaf hangs parallel to the perpendicular wall beside the corner door, so even an end-gap classifier must read the leaf as evidence at the gap although it is not inside the host band's gap rectangle.",
}


def _load(name):
    return json.loads((BLIND / f"{name}.json").read_text("utf-8"))


def _rc(meta, x, y):
    return int((meta["y1"] - y) / meta["cell"]), int((x - meta["x0"]) / meta["cell"])


def _raster_add(kind, polys, meta):
    k = kind.copy(); H, W = k.shape; cell = meta["cell"]
    for pts in polys:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(2, int(math.hypot(bx - ax, by - ay) / (cell * 0.5)) + 1)
            for i in range(n):
                t = i / (n - 1); rr, cc = _rc(meta, ax + (bx - ax) * t, ay + (by - ay) * t)
                if 0 <= rr < H and 0 <= cc < W and k[rr, cc] == 0:
                    k[rr, cc] = PF.KIND_CODES["UNRESOLVED_CHORD"]
    return k


def run():
    cfg = json.loads((B.OUT / "PA08_BLIND_CONFIG.json").read_text("utf-8"))
    r = P7.run(cfg)
    vid = next(v for v in r.grids7 if r.grids7[v] is not None)
    view = next(v for v in r.views if v["VIEW_ID"] == vid)
    prims = {p.object_id: p for p in view["PRIMITIVES"]}
    roles = r.roles[vid]
    g = r.grids7[vid]; meta = g["meta"]; kind0 = g["kind"]
    # blind (frozen PA07R2) registers
    blind_bands = _load("PA07_MATERIAL_BAND_REGISTER")["ROWS"]
    blind_by_face = defaultdict(list)
    for row in blind_bands:
        for f in row["SIDE_A_FACE_IDS"] + row["SIDE_B_FACE_IDS"]:
            blind_by_face[f.split("@")[0]].append(row)
    display = {row["OBJECT_ID"].split("@")[0]: row for row in _load("PA07_DISPLAY_SEMANTICS_REGISTER")["ROWS"]}
    blind_roles = {row["OBJECT_ID"].split("@")[0]: row for row in _load("PA06_PRIMITIVE_ROLE_REGISTER")["ROWS"]}
    dims = _load("DIMENSION_CHAIN_REGISTER")["ROWS"]
    blind_spaces = _load("PA07_PHYSICAL_SPACE_REGISTER")["ROWS"]
    merged_blind = max(blind_spaces, key=lambda s: len(s["ANCHORS"]))
    # interim (current working tree) bands
    now_by_face = defaultdict(list)
    for b in r.bands7[vid]:
        for f in list(b["SIDE_A"]) + list(b["SIDE_B"]):
            now_by_face[f.split("@")[0]].append(b)
    # door block instances
    inst = defaultdict(list)
    for p in view["PRIMITIVES"]:
        if p.provenance.layer == "DOOR" and p.kind == "SEGMENT" and "@" in p.object_id:
            inst[p.object_id.split("@")[-1]].append(p)
    doors = []
    for h, ps in inst.items():
        xs = [q for p in ps for q in (p.x1, p.x2)]; ys = [q for p in ps for q in (p.y1, p.y2)]
        doors.append({"BLOCK_INSTANCE": h, "PIECES": len(ps), "BBOX_MM": [round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))], "SWING_ARC": False, "PIECE_ROLES": sorted({roles.get(p.object_id, {}).get("ROLE") for p in ps})})
    cols = [p for p in view["PRIMITIVES"] if p.kind == "SEGMENT" and (p.provenance.layer.startswith("COL") or p.provenance.layer.startswith("A-COL"))]
    anchors = [(t.value.strip(), _rc(meta, t.x, t.y)) for t in view["TEXTS"] if t.value.strip().upper() in MERGED_ANCHOR_WORDS]

    def groups(kind):
        label, _ = PF.label_faces(kind)
        by = defaultdict(list)
        for name, (rr, cc) in anchors:
            by[int(label[rr, cc])].append(name)
        return sorted(by.values(), key=len, reverse=True)

    def near(p, x0, y0, x1, y1, tol):
        return min(p.x1, p.x2) < x1 + tol and max(p.x1, p.x2) > x0 - tol and min(p.y1, p.y2) < y1 + tol and max(p.y1, p.y2) > y0 - tol

    def strip_caps():
        out = []
        for b in r.bands7[vid]:
            if b["STATUS"] != "UNRESOLVED" or b["KIND"] != "S":
                continue
            h = b["THK"] / 2
            for t in b["EXTENT"]:
                out.append([MB.band_point(b, t, -h), MB.band_point(b, t, +h)])
        return out

    rows = []
    seal_sets = {}
    for bd in BOUNDARIES:
        ents = []
        xs, ys = [], []
        for oid in bd["ENTITIES"]:
            p = prims.get(oid)
            if p is None:
                ents.append({"OBJECT_ID": oid, "PRESENT": False}); continue
            d = display.get(oid, {}); ro = roles.get(oid, {}); br = blind_roles.get(oid, {})
            xs += [p.x1, p.x2]; ys += [p.y1, p.y2]
            ents.append({"OBJECT_ID": oid, "HANDLE": getattr(p.provenance, "handle", None), "ENTITY_TYPE": d.get("ENTITY_TYPE"), "LAYER": p.provenance.layer, "LINETYPE": d.get("LINETYPE"), "LINETYPE_SOURCE": d.get("LINETYPE_SOURCE"),
                         "BLOCK_PATH": list(p.provenance.block_path or []), "LENGTH_MM": round(p.length_mm, 1), "P1_MM": [round(p.x1, 1), round(p.y1, 1)], "P2_MM": [round(p.x2, 1), round(p.y2, 1)],
                         "ANGLE_RAW_RAD": MB._angle(p), "DIR_KEY": MB._dir_key(MB._angle(p)),
                         "PA06_ROLE_BLIND": {k: br.get(k) for k in ("ROLE", "ROLE_STATUS", "ROLE_EVIDENCE", "MATERIAL")}, "PA06_ROLE_NOW": {k: ro.get(k) for k in ("ROLE", "ROLE_STATUS")},
                         "BLIND_PA07R2_BANDS": [{"BAND_ID": x["BAND_ID"], "STATUS": x["MATERIAL_STATUS"], "THICKNESS_MM": x["THICKNESS_MM"], "LENGTH_MM": x["DEVELOPED_LENGTH_MM"], "REASON": x.get("REJECTION_REASON"), "FACE_SIDE_CONFLICT": x.get("FACE_SIDE_CONFLICT")} for x in blind_by_face.get(oid, [])],
                         "INTERIM_R3_BANDS": [{"KEY": x["KEY"], "STATUS": x["STATUS"], "THICKNESS_MM": round(x["THK"]), "LENGTH_MM": round(x["LENGTH"]), "REASON": (x.get("REASON") or "")[:160]} for x in now_by_face.get(oid, [])]})
        pres = [prims[o] for o in bd["ENTITIES"] if o in prims and prims[o].kind == "SEGMENT"]
        # parallel pairs: raw engine pairing vs the same pairing with a canonical (bucket) angle, to expose FC-1
        raw_pairs = [(a.object_id, b_.object_id, round(d), round(iv[1] - iv[0])) for a, b_, d, iv, *_ in MB._pairs(pres)]
        canon = []
        by_key = defaultdict(list)
        for p in pres:
            by_key[MB._dir_key(MB._angle(p))].append(p)
        for key, items in by_key.items():
            ang = key * MB.ANGLE_TOL; ux, uy = math.cos(ang), math.sin(ang)
            offs = [(-uy * p.x1 + ux * p.y1, MB._proj(p, ux, uy), p) for p in items]
            for i, (o1, (lo1, hi1), p1) in enumerate(offs):
                for o2, (lo2, hi2), p2 in offs[i + 1:]:
                    dd = abs(o2 - o1); ov = min(hi1, hi2) - max(lo1, lo2)
                    if ov > 0 and dd >= 30:
                        canon.append((p1.object_id, p2.object_id, round(dd), round(ov), "IN_THICKNESS_RANGE" if MB.THICKNESS[0] <= dd <= MB.THICKNESS[1] else "OUTSIDE_THICKNESS_RANGE"))
        bx0, by0, bx1, by1 = (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0)
        dims_near = [{"DISPLAY_TEXT": dm["DISPLAY_TEXT"], "MEASURED_VALUE_MM": dm["MEASURED_VALUE_MM"], "READ_STATUS": dm["READ_STATUS"], "ORIGINS_MM": dm["DIMENSION_LINE"]["ORIGINS_MM"]}
                     for dm in dims if xs and dm["DIMENSION_LINE"] and all(bx0 - 1500 <= o[0] <= bx1 + 1500 and by0 - 1500 <= o[1] <= by1 + 1500 for o in dm["DIMENSION_LINE"]["ORIGINS_MM"]) and 75 <= dm["MEASURED_VALUE_MM"] <= 600]
        doors_near = [dd for dd in doors if xs and dd["BBOX_MM"][0] < bx1 + 300 and dd["BBOX_MM"][2] > bx0 - 300 and dd["BBOX_MM"][1] < by1 + 300 and dd["BBOX_MM"][3] > by0 - 300]
        cols_near = [{"OBJECT_ID": c.object_id, "LAYER": c.provenance.layer, "LENGTH_MM": round(c.length_mm), "P1": [round(c.x1), round(c.y1)], "P2": [round(c.x2), round(c.y2)]} for c in cols if xs and near(c, bx0, by0, bx1, by1, 300)]
        # ablation geometry for this boundary: every entity face + the missing gap chords
        polys = [[(prims[o].x1, prims[o].y1), (prims[o].x2, prims[o].y2)] for o in bd["ENTITIES"] if o in prims and prims[o].kind == "SEGMENT"]
        if bd["GAP_CHORDS"] == "UNRESOLVED_STRIP_END_CAPS":
            polys = strip_caps()
        else:
            polys += [[(x0, y0), (x1, y1)] for x0, y0, x1, y1 in bd["GAP_CHORDS"]]
        seal_sets[bd["ID"]] = polys
        rows.append({"BOUNDARY_ID": bd["ID"], "NAME": bd["NAME"], "RAW_ENTITIES": ents, "LAYERS": sorted({e.get("LAYER") for e in ents if e.get("LAYER")}), "ENTITY_TYPES": sorted({str(e.get("ENTITY_TYPE")) for e in ents if e.get("ENTITY_TYPE")}),
                     "LINETYPES": sorted({str(e.get("LINETYPE")) for e in ents if e.get("LINETYPE")}), "BLOCK_RELATIONS": sorted({"/".join(e["BLOCK_PATH"]) or "MODEL_SPACE" for e in ents if "BLOCK_PATH" in e}),
                     "PARALLEL_FACE_PAIRS": {"ENGINE_PAIRS_AS_IS": raw_pairs, "PAIRS_WITH_CANONICAL_ANGLE": canon}, "FACE_SEPARATION_MM": sorted({c[2] for c in canon}),
                     "AUTHORED_THICKNESS_DIMENSIONS_NEAR": dims_near, "DOOR_WINDOW_INTERSECTIONS": doors_near, "COLUMN_JUNCTION_RELATIONS": cols_near, "SEAL_GEOMETRY_MISSING": bd["GAP_CHORDS"] if isinstance(bd["GAP_CHORDS"], str) else [list(c) for c in bd["GAP_CHORDS"]]})
    base = groups(kind0)
    for row in rows:
        gr = groups(_raster_add(kind0, seal_sets[row["BOUNDARY_ID"]], meta))
        row["ABLATION_ALONE"] = {"LARGEST_GROUP": len(gr[0]), "GROUPS": [sorted(x) for x in gr]}
    allp = [p for ps in seal_sets.values() for p in ps]
    gr_all = groups(_raster_add(kind0, allp, meta))
    loo = {}
    for bid in seal_sets:
        polys = [p for k, ps in seal_sets.items() if k != bid for p in ps]
        gr = groups(_raster_add(kind0, polys, meta))
        loo[bid] = {"LARGEST_GROUP": len(gr[0]), "STILL_MERGED": [sorted(x) for x in gr if len(x) > 1]}
    for row in rows:
        row["ABLATION_LEAVE_ONE_OUT"] = loo[row["BOUNDARY_ID"]]
        row["CAUSAL"] = loo[row["BOUNDARY_ID"]]["LARGEST_GROUP"] > 1
    # why PA07R2 rejected / left unresolved each boundary (failure class assignment, from the evidence above)
    why = {
        "QPB-01": ["FC-1_ANGLE_FRAME_FLIP", "FC-7_FURNITURE_AGAINST_WALL_STRIP_ACCEPTED", "FC-3_UNRESOLVED_STRIP_UNCAPPED"],
        "QPB-02": ["FC-5_WALL_FACE_ROLE_AS_HATCH_STROKE", "FC-1_ANGLE_FRAME_FLIP", "FC-2_END_GAP_NOT_CLASSIFIED", "FC-8_DOOR_LEAF_PARALLEL_TO_HOST"],
        "QPB-03": ["FC-6_THIN_OR_ISOLATED_PARTITION_DEMOTED", "FC-2_END_GAP_NOT_CLASSIFIED", "FC-8_DOOR_LEAF_PARALLEL_TO_HOST"],
        "QPB-04": ["FC-1_ANGLE_FRAME_FLIP", "FC-4_CLOSED_OUTLINE_BEYOND_THICKNESS_RANGE"],
        "QPB-05": [],
        "QPB-06": [],
        "QPB-07": ["FC-2_END_GAP_NOT_CLASSIFIED"],
        "QPB-08": ["FC-6_THIN_OR_ISOLATED_PARTITION_DEMOTED", "FC-2_END_GAP_NOT_CLASSIFIED", "FC-3_UNRESOLVED_STRIP_UNCAPPED", "FC-8_DOOR_LEAF_PARALLEL_TO_HOST"],
        "QPB-09": ["FC-3_UNRESOLVED_STRIP_UNCAPPED"],
    }
    for row in rows:
        row["FAILURE_CLASSES"] = why[row["BOUNDARY_ID"]]
        row["WHY_PA07R2_REJECTED_OR_UNRESOLVED_IT"] = [FAILURE_CLASSES[c] for c in why[row["BOUNDARY_ID"]]] or ["no failure: this boundary is sealed by PA07R2 (control row)"]
    import subprocess as _sp
    head = _sp.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(_sp.run(["git", "status", "--porcelain", "engine/"], capture_output=True, text=True).stdout.strip())
    reg = {"ARTIFACT": "QORTUBA_PARTITION_FAILURE_REGISTER", "PHASE": "PA08_QORTUBA_R1 §2", "STATUS": "DIAGNOSIS_BEFORE_RULE_CHANGES",
           "ENGINE_UNDER_DIAGNOSIS": {"GIT_HEAD": head, "ENGINE_WORKING_TREE_MODIFIED": dirty,
                                      "REQUIREMENT": "this register must be produced with the engine files as they stood at the PA07R2 freeze, the engine that FAILED; producing it on the repaired rules would describe a merge that no longer happens",
                                      "STATUS": "VALID_DIAGNOSIS" if not dirty else "INVALID: the engine working tree carries changes; re-run with the frozen engine files"},
           "BLIND_MERGED_CELL": {"SPACE_ID": merged_blind["SPACE_ID"], "AREA_GEOMETRIC_M2": merged_blind["AREA_GEOMETRIC_M2"], "ANCHORS": [a.get("TEXT") or a.get("RAW_TEXT") for a in merged_blind["ANCHORS"]], "FREEZE": "PA08_QORTUBA_BLIND_01 (not rewritten)"},
           "RUN_NOTE": "the run below is the frozen PA07R2 engine on the Qortuba sources: the same seven labelled rooms fall into one raster cell as in the blind freeze, and the ablation measures which boundary, once sealed, separates which rooms",
           "RASTER_ANCHORS": [a[0] for a in anchors], "BASE_GROUPING": [sorted(x) for x in base], "ALL_BOUNDARIES_SEALED_GROUPING": [sorted(x) for x in gr_all],
           "FAILURE_CLASSES": FAILURE_CLASSES, "BOUNDARIES": rows,
           "PRINCIPLE": "each boundary is explained by a generic mechanism (a floating-point frame flip, an unclassified end gap, an uncapped strip, a thickness-range edge, a role misclassification, a guard demotion); no Qortuba coordinate, label or expected area enters any rule that answers it"}
    OUT_R1.mkdir(parents=True, exist_ok=True)
    (OUT_R1 / "QORTUBA_PARTITION_FAILURE_REGISTER.json").write_text(json.dumps(reg, indent=1, ensure_ascii=False, default=str), "utf-8")
    return reg


if __name__ == "__main__":
    reg = run()
    print("base", reg["BASE_GROUPING"][0])
    print("all sealed", reg["ALL_BOUNDARIES_SEALED_GROUPING"])
    for row in reg["BOUNDARIES"]:
        print(row["BOUNDARY_ID"], "causal", row["CAUSAL"], "alone->largest", row["ABLATION_ALONE"]["LARGEST_GROUP"], "LOO still merged", row["ABLATION_LEAVE_ONE_OUT"]["STILL_MERGED"], row["FAILURE_CLASSES"])
        print("    pairs as-is", row["PARALLEL_FACE_PAIRS"]["ENGINE_PAIRS_AS_IS"][:4], "| canonical", row["PARALLEL_FACE_PAIRS"]["PAIRS_WITH_CANONICAL_ANGLE"][:5])
        print("    dims near", [(d["DISPLAY_TEXT"], d["MEASURED_VALUE_MM"]) for d in row["AUTHORED_THICKNESS_DIMENSIONS_NEAR"]][:8], "doors", [d["BLOCK_INSTANCE"] for d in row["DOOR_WINDOW_INTERSECTIONS"]], "cols", len(row["COLUMN_JUNCTION_RELATIONS"]))

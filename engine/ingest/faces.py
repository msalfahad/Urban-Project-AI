"""Atomic wall faces v3 (PA05 §6): every wall-layer entity (line or arc, any
orientation) yields two atomic faces with exact developed length and a
normal direction; side spaces are attached later by the space builder.
No axis alignment, no bounding boxes."""

from __future__ import annotations

import math

from engine.ingest import curves, ids


def atomic_faces(view_id, prims, wall_layers, entity_ids):
    out = []
    for p in prims:
        if p.provenance.layer not in wall_layers:
            continue
        eid = entity_ids[p.object_id]
        if p.kind == "SEGMENT":
            L = math.hypot(p.x2 - p.x1, p.y2 - p.y1)
            if L < 1e-6:
                continue
            ang = math.atan2(p.y2 - p.y1, p.x2 - p.x1)
            nx, ny = -math.sin(ang), math.cos(ang)
            orient = "HORIZONTAL" if abs(math.sin(ang)) < 1e-3 else ("VERTICAL" if abs(math.cos(ang)) < 1e-3 else "ANGLED")
            geom = {"KIND": "LINE", "A": [round(p.x1, 1), round(p.y1, 1)], "B": [round(p.x2, 1), round(p.y2, 1)], "ANGLE_DEG": round(math.degrees(ang), 3)}
            mid = ((p.x1 + p.x2) / 2, (p.y1 + p.y2) / 2)
            for sgn in (1, -1):
                out.append({"FACE_ID": ids.face_id(view_id, eid, sgn), "ENTITY_ID": eid, "GEOMETRY": geom, "GEOMETRY_TYPE": orient, "DEVELOPED_LENGTH_MM": round(L, 1),
                            "NORMAL_DIRECTION": [round(sgn * nx, 6), round(sgn * ny, 6)], "PROBE_MM": [mid[0] + sgn * nx * 150, mid[1] + sgn * ny * 150],
                            "HOST_OBJECT": None, "SIDE_A_SPACE": None, "SIDE_B_SPACE": None, "MATERIAL_ROLE": "WALL_LIKE (layer evidence)", "EXPOSURE_STATUS": "NOT_ESTABLISHED",
                            "CLEAR_FINISH_FACE_STATUS": "NOT_ESTABLISHED", "SOURCE": {"LAYER": p.provenance.layer, "HANDLE": p.provenance.handle}, "BOUNDING_BOX_USED": False})
        elif p.kind in ("ARC", "CIRCLE"):
            a = curves.arc_from_primitive(p) if p.kind == "ARC" else {"R": p.radius, "SWEEP_RAD": 2 * math.pi, "LENGTH": 2 * math.pi * p.radius, "START": None, "END": None}
            mid_ang = (p.start_angle + a["SWEEP_RAD"] / 2) if p.kind == "ARC" else 0.0
            geom = {"KIND": "ARC" if p.kind == "ARC" else "CIRCLE", "CENTRE": [round(p.cx, 1), round(p.cy, 1)], "R_MM": round(p.radius, 1), "SWEEP_RAD": round(a["SWEEP_RAD"], 5),
                    "START_ANGLE": round(p.start_angle, 5), "END_ANGLE": round(p.end_angle, 5)}
            for sgn in (1, -1):        # +1 = outward (convex side), -1 = inward
                out.append({"FACE_ID": ids.face_id(view_id, eid, sgn), "ENTITY_ID": eid, "GEOMETRY": geom, "GEOMETRY_TYPE": "ARC" if p.kind == "ARC" else "CIRCLE", "DEVELOPED_LENGTH_MM": round(a["LENGTH"], 1),
                            "NORMAL_DIRECTION": "RADIAL_OUT" if sgn > 0 else "RADIAL_IN", "PROBE_MM": [p.cx + (p.radius + sgn * 150) * math.cos(mid_ang), p.cy + (p.radius + sgn * 150) * math.sin(mid_ang)],
                            "HOST_OBJECT": None, "SIDE_A_SPACE": None, "SIDE_B_SPACE": None, "MATERIAL_ROLE": "WALL_LIKE (layer evidence)", "EXPOSURE_STATUS": "NOT_ESTABLISHED",
                            "CLEAR_FINISH_FACE_STATUS": "NOT_ESTABLISHED", "SOURCE": {"LAYER": p.provenance.layer, "HANDLE": p.provenance.handle}, "BOUNDING_BOX_USED": False})
    return out


def summarise(faces):
    by = {}
    for f in faces:
        by.setdefault(f["GEOMETRY_TYPE"], {"COUNT": 0, "DEVELOPED_M": 0.0})
        by[f["GEOMETRY_TYPE"]]["COUNT"] += 1
        by[f["GEOMETRY_TYPE"]]["DEVELOPED_M"] = round(by[f["GEOMETRY_TYPE"]]["DEVELOPED_M"] + f["DEVELOPED_LENGTH_MM"] / 1000, 3)
    return by

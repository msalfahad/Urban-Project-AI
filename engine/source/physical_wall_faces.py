"""PHYSICAL_WALL_FACE_REGISTER - wall faces exist before any finish decision (generic).

Layers, each kept separately so an unknown material never makes a wall face disappear:

    PHYSICAL_WALL_FACE_AREA      length x height per face (2 faces for a free-standing wall)
    GROSS_PLASTER_ELIGIBLE_AREA  physical face area where the plaster rule applies (project rule / default)
    OPENING_DEDUCTION            opening area on that face (0 when the band is already net of openings)
    CERAMIC_EXCLUSION            tiled area on that face (when known)
    PAINT_ELIGIBLE_AREA          plaster-eligible - openings - ceramic
    FINAL_FINISH_ASSIGNMENT      the material, or BLOCKED / UNASSIGNED - never a zero area

Height comes from the WALL_HEIGHT evidence ladder (resolved by the caller); its origin travels with the area.
Room semantic certification is not required to measure a physical face. Stdlib only.
"""

from __future__ import annotations

from engine.source import quantity_scenarios as QS

INTERNAL, EXTERNAL = "INTERNAL", "EXTERNAL"


def faces(wall, height):
    """wall: {wall_id, floor, length_m, thickness_mm, position INTERNAL|EXTERNAL, openings_m2_per_face?,
    net_of_openings: bool, ceramic_m2: {face: m2}?, finish: {face: material|None}, plaster_rule: bool|None};
    height: evidence_ladder.resolve result (WALL_HEIGHT)."""
    out = []
    sides = ("A", "B")
    for s in sides:
        fid = f"{wall['wall_id']}:{s}"
        role = "EXTERIOR_FACE" if wall.get("position") == EXTERNAL and s == "B" else "INTERIOR_FACE"
        if not height["resolved"]:
            out.append({"face_id": fid, "wall_id": wall["wall_id"], "floor": wall.get("floor"), "face_role": role,
                        "physical_area_m2": None, "height": None, "state": "UNQUANTIFIED",
                        "why": "wall height unresolved (length kept)", "length_m": wall["length_m"]})
            continue
        h, lo, hi = height["value"], height["low"], height["high"]
        phys = wall["length_m"] * h
        openings = 0.0 if wall.get("net_of_openings") else (wall.get("openings_m2_per_face") or 0.0)
        ceramic = (wall.get("ceramic_m2") or {}).get(s, 0.0)
        plaster_rule = wall.get("plaster_rule")
        plaster = phys if plaster_rule is not False else 0.0
        paint = max(plaster - openings - ceramic, 0.0)
        finish = (wall.get("finish") or {}).get(s)
        out.append({"face_id": fid, "wall_id": wall["wall_id"], "floor": wall.get("floor"), "face_role": role,
                    "length_m": wall["length_m"], "height_m": h, "height_level": height["level"],
                    "height_origin": height["fact_origin"],
                    "PHYSICAL_WALL_FACE_AREA": phys, "physical_low_m2": wall["length_m"] * lo,
                    "physical_high_m2": wall["length_m"] * hi,
                    "GROSS_PLASTER_ELIGIBLE_AREA": plaster,
                    "plaster_applicability": "PROJECT_RULE" if plaster_rule else (
                        "NOT_APPLICABLE" if plaster_rule is False else "LIKELY_BY_DEFAULT"),
                    "OPENING_DEDUCTION": openings, "CERAMIC_EXCLUSION": ceramic, "PAINT_ELIGIBLE_AREA": paint,
                    "FINAL_FINISH_ASSIGNMENT": finish or "BLOCKED_FINISH_NOT_ASSIGNED",
                    "state": "MEASURED" if height["authority"] == "VERIFIED" else "PROVISIONAL_HEIGHT"})
    return out


def register(walls, height_for):
    """height_for(wall) -> WALL_HEIGHT resolution. Returns faces + the physical-area scenario (finish-independent)."""
    allf, parts = [], []
    for w in walls:
        hs = height_for(w)
        fs = faces(w, hs)
        allf += fs
        for f in fs:
            if f.get("PHYSICAL_WALL_FACE_AREA") is None:
                parts.append(QS.part(f["face_id"], "UNQUANTIFIED", why=f["why"]))
            elif f["state"] == "MEASURED" and f["physical_low_m2"] == f["physical_high_m2"]:
                parts.append(QS.part(f["face_id"], "VERIFIED", f["PHYSICAL_WALL_FACE_AREA"], origin=f["height_origin"]))
            else:
                parts.append(QS.part(f["face_id"], "PROVISIONAL", f["PHYSICAL_WALL_FACE_AREA"],
                                     min(f["physical_low_m2"], f["PHYSICAL_WALL_FACE_AREA"]),
                                     max(f["physical_high_m2"], f["PHYSICAL_WALL_FACE_AREA"]),
                                     origin=f["height_origin"], why=f"height from {f['height_level']}"))
    return {"faces": allf, "physical_area": QS.combine(parts, unit="m2"),
            "paint_eligible_m2": sum(f.get("PAINT_ELIGIBLE_AREA") or 0.0 for f in allf),
            "finish_unassigned_faces": sum(1 for f in allf
                                           if f.get("FINAL_FINISH_ASSIGNMENT") == "BLOCKED_FINISH_NOT_ASSIGNED")}

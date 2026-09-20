"""Wall-material continuity model (PA06 WS3).

A gap becomes a topological site only inside a HOST_WALL_CONTEXT: a wall
band (paired faces, or a single-line wall) whose material coverage stops
and resumes along its own axis.  Two stubs that happen to be collinear
across a corridor terminate at T-junctions and are not a site.  Sites are
classified from door, window, glazing, junction and free-space evidence;
what cannot be decided stays UNRESOLVED_SITE.  Nothing here closes a
room: physical separators are listed for the space builder, and trade
closures are applied later by the measurement layer.
"""

from __future__ import annotations

import math
from collections import defaultdict

from engine.ingest import ids
from engine.ingest.primitive_roles import _paired, _angle, _len, ANGLE_TOL

SITE_CLASSES = ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING", "CONFIRMED_OPEN_PASSAGE", "MATERIAL_CONTINUITY_GAP", "CAD_JUNCTION_GAP", "TRUE_WALL_TERMINATION", "UNRESOLVED_SITE")
PHYSICAL_SEPARATOR_CLASSES = ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING", "MATERIAL_CONTINUITY_GAP", "CAD_JUNCTION_GAP")   # leaf / frame / continuing material
JUNCTION_MM, MIN_PASSAGE_MM, MAX_SITE_MM = 120.0, 500.0, 4000.0
BAND_MERGE_MM = 30.0
HINGE_TOL = 450.0
TERMINATION_TOL = 80.0


def _project(p, ux, uy):
    a, b = p.x1 * ux + p.y1 * uy, p.x2 * ux + p.y2 * uy
    return (a, b) if a <= b else (b, a)


def _union(intervals):
    out = []
    for lo, hi in sorted(intervals):
        if out and lo <= out[-1][1] + 1e-6:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


def build_bands(prims, roles):
    """Wall bands from material faces.  Paired faces define a band (axis + thickness); unpaired faces are attached to
    the band whose face line they lie on; collinear bands within a wall thickness are merged; the leftovers are
    single-line bands.  A band is the HOST_WALL_CONTEXT every site must have."""
    faces = [p for p in prims if p.kind == "SEGMENT" and roles.get(p.object_id, {}).get("ROLE") == "MATERIAL_WALL_FACE"]
    pairs = _paired(faces)
    by_id = {p.object_id: p for p in faces}
    info = {}
    for p in faces:
        ang = _angle(p); ux, uy = math.cos(ang), math.sin(ang)
        info[p.object_id] = (ang, ux, uy, -uy * p.x1 + ux * p.y1)
    # 1 paired faces -> raw bands
    raw = {}
    for p in faces:
        if p.object_id not in pairs:
            continue
        ang, ux, uy, off = info[p.object_id]
        q = by_id[pairs[p.object_id][0]]
        off_q = info[q.object_id][3]
        axis, thk = (off + off_q) / 2, abs(off_q - off)
        key = (int(round(ang / ANGLE_TOL)), int(round(axis / BAND_MERGE_MM)))
        b = raw.setdefault(key, {"ANGLE": ang, "U": (ux, uy), "AXES": [], "THICKNESS": [], "MEMBERS": []})
        b["AXES"].append(axis); b["THICKNESS"].append(thk); b["MEMBERS"].append(p)
    # 2 merge collinear raw bands of one direction whose axes lie within half a wall thickness
    merged = []
    for d in sorted({k[0] for k in raw}):
        group = sorted([(k, b) for k, b in raw.items() if k[0] == d], key=lambda kb: sum(kb[1]["AXES"]) / len(kb[1]["AXES"]))
        cur = None
        for k, b in group:
            axis = sum(b["AXES"]) / len(b["AXES"])
            if cur and abs(axis - cur["AXIS_OFFSET"]) <= max(cur["THK_MED"], 200.0) / 2 + BAND_MERGE_MM:
                cur["MEMBERS"] += b["MEMBERS"]; cur["THICKNESS"] += b["THICKNESS"]; cur["AXES"] += b["AXES"]
                cur["AXIS_OFFSET"] = sum(cur["AXES"]) / len(cur["AXES"]); cur["THK_MED"] = sorted(cur["THICKNESS"])[len(cur["THICKNESS"]) // 2]
            else:
                cur = {"ANGLE": b["ANGLE"], "U": b["U"], "MEMBERS": list(b["MEMBERS"]), "THICKNESS": list(b["THICKNESS"]), "AXES": list(b["AXES"]), "AXIS_OFFSET": axis,
                       "THK_MED": sorted(b["THICKNESS"])[len(b["THICKNESS"]) // 2], "DIR": d}
                merged.append(cur)
    # 3 attach unpaired faces that lie on a band's face line; leftovers become single-line bands
    single = {}
    for p in faces:
        if p.object_id in pairs:
            continue
        ang, ux, uy, off = info[p.object_id]
        d = int(round(ang / ANGLE_TOL))
        host = None
        for b in merged:
            if b["DIR"] == d and abs(abs(off - b["AXIS_OFFSET"]) - b["THK_MED"] / 2) <= 25:
                lo, hi = _project(p, ux, uy)
                # only if it continues the band along its axis (within 2 m of the band's extent)
                ext = [_project(m, ux, uy) for m in b["MEMBERS"]]
                if min(abs(lo - e[1]) for e in ext) <= 2000 or min(abs(hi - e[0]) for e in ext) <= 2000 or any(e[0] <= lo <= e[1] for e in ext):
                    host = b; break
        if host:
            host["MEMBERS"].append(p)
        else:
            key = (d, int(round(off / BAND_MERGE_MM)))
            single.setdefault(key, {"ANGLE": ang, "U": (ux, uy), "MEMBERS": [], "THICKNESS": [], "AXES": [off], "AXIS_OFFSET": off, "THK_MED": None, "DIR": d})["MEMBERS"].append(p)
    out = []
    for b in merged + list(single.values()):
        ux, uy = b["U"]; nx, ny = -uy, ux
        faces_rows = []
        for p in b["MEMBERS"]:
            off = info[p.object_id][3]
            side = "AXIS" if b["THK_MED"] is None else ("A" if off < b["AXIS_OFFSET"] else "B")
            faces_rows.append({"ENTITY": p.object_id, "SIDE": side, "INTERVAL": _project(p, ux, uy), "OFFSET": off, "PRIM": p})
        cov = _union([f["INTERVAL"] for f in faces_rows])
        out.append({"BAND_ID": ids.make_id("WALL_FACE", "BAND", b["DIR"], round(b["AXIS_OFFSET"] / BAND_MERGE_MM), tol=1.0).replace("WF-", "WB-"), "ANGLE": b["ANGLE"], "U": (ux, uy), "NORMAL": (nx, ny),
                    "AXIS_OFFSET": b["AXIS_OFFSET"], "THICKNESS_MM": round(b["THK_MED"], 1) if b["THK_MED"] else None, "FACES": faces_rows, "COVERAGE": cov,
                    "EXTENT": (cov[0][0], cov[-1][1]) if cov else None, "STATUS": "SOURCE_ESTABLISHED" if b["THK_MED"] else "PROVISIONAL_SINGLE_LINE",
                    "SINGLE_LINE": [f["ENTITY"] for f in faces_rows] if b["THK_MED"] is None else []})
    return out


def _point_on_axis(b, t):
    ux, uy = b["U"]; nx, ny = b["NORMAL"]
    return (ux * t + nx * b["AXIS_OFFSET"], uy * t + ny * b["AXIS_OFFSET"])


def _termination(b, t, bands, prims, roles):
    """What terminates the band at axis coordinate t: a jamb return, a T-junction with another band, or a free end."""
    px, py = _point_on_axis(b, t)
    thk = b["THICKNESS_MM"] or 150.0
    # jamb return: a short material / unknown segment perpendicular to the axis at t, spanning the band thickness
    for p in prims:
        if p.kind != "SEGMENT" or roles.get(p.object_id, {}).get("ROLE") in ("HATCH_STROKE", "DIMENSION_LINE", "DIMENSION_EXTENSION", "DOOR_SWING", "DOOR_LEAF"):
            continue
        L = _len(p)
        if not (0.5 * thk <= L <= 1.5 * thk + 20):
            continue
        if abs(((_angle(p) - b["ANGLE"]) % math.pi) - math.pi / 2) > 5 * ANGLE_TOL:
            continue
        mx, my = (p.x1 + p.x2) / 2, (p.y1 + p.y2) / 2
        if math.hypot(mx - px, my - py) <= TERMINATION_TOL + thk / 2:
            return {"KIND": "JAMB_RETURN", "ENTITY": p.object_id}
    # T-junction: a perpendicular band whose coverage contains the point and whose axis passes within half a thickness
    for o in bands:
        if o is b or abs(((o["ANGLE"] - b["ANGLE"]) % math.pi) - math.pi / 2) > 10 * ANGLE_TOL:
            continue
        oux, ouy = o["U"]; onx, ony = o["NORMAL"]
        dist_axis = abs((px * onx + py * ony) - o["AXIS_OFFSET"])
        along = px * oux + py * ouy
        if dist_axis <= (o["THICKNESS_MM"] or 150.0) / 2 + TERMINATION_TOL and any(lo - TERMINATION_TOL <= along <= hi + TERMINATION_TOL for lo, hi in o["COVERAGE"]):
            return {"KIND": "T_JUNCTION", "BAND": o["BAND_ID"]}
    return {"KIND": "FREE_END", "ENTITY": None}


def _door_evidence(b, t0, t1, prims, roles):
    span = t1 - t0
    p0, p1 = _point_on_axis(b, t0), _point_on_axis(b, t1)
    out = []
    hinged = []
    for p in prims:
        if roles.get(p.object_id, {}).get("ROLE") != "DOOR_SWING":
            continue
        if min(math.hypot(p.cx - p0[0], p.cy - p0[1]), math.hypot(p.cx - p1[0], p.cy - p1[1])) <= HINGE_TOL and 0.35 * span <= p.radius <= 1.3 * span:
            hinged.append(p)
    for p in hinged:
        if abs(p.radius - span) <= 0.3 * span:
            out.append({"SWING": p.object_id, "RADIUS_MM": round(p.radius, 1), "LEAVES": 1})
    if not out and len(hinged) >= 2:
        pair = sorted(hinged, key=lambda p: -p.radius)[:2]
        if abs(pair[0].radius + pair[1].radius - span) <= 0.3 * span:
            out = [{"SWING": p.object_id, "RADIUS_MM": round(p.radius, 1), "LEAVES": 1} for p in pair]
    return out


def _strip_segments(b, t0, t1, prims, roles, allowed_roles):
    """Segments inside the band strip across the gap (parallel to the axis, within the thickness), e.g. window frame / sill lines."""
    ux, uy = b["U"]; nx, ny = b["NORMAL"]
    half = (b["THICKNESS_MM"] or 150.0) / 2 + 40
    hits = []
    for p in prims:
        r = roles.get(p.object_id, {})
        if p.kind != "SEGMENT" or r.get("ROLE") not in allowed_roles:
            continue
        if abs((_angle(p) - b["ANGLE"]) % math.pi) > 5 * ANGLE_TOL and abs(((_angle(p) - b["ANGLE"]) % math.pi) - math.pi) > 5 * ANGLE_TOL:
            continue
        off = (p.x1 * nx + p.y1 * ny) - b["AXIS_OFFSET"]
        if abs(off) > half:
            continue
        lo, hi = _project(p, ux, uy)
        overlap = min(hi, t1) - max(lo, t0)
        if overlap >= 0.5 * (t1 - t0):
            hits.append({"ENTITY": p.object_id, "ROLE": r.get("ROLE"), "OVERLAP_MM": round(overlap, 1)})
    return hits


def _free_space(b, t0, t1, side, prims, roles):
    """No material face parallel to the band within 400 mm beyond the band on that side across the gap -> free space."""
    ux, uy = b["U"]; nx, ny = b["NORMAL"]
    half = (b["THICKNESS_MM"] or 150.0) / 2
    sgn = -1 if side == "A" else 1
    for p in prims:
        if p.kind != "SEGMENT" or not roles.get(p.object_id, {}).get("MATERIAL"):
            continue
        if abs((_angle(p) - b["ANGLE"]) % math.pi) > 5 * ANGLE_TOL and abs(((_angle(p) - b["ANGLE"]) % math.pi) - math.pi) > 5 * ANGLE_TOL:
            continue
        off = (p.x1 * nx + p.y1 * ny) - b["AXIS_OFFSET"]
        if sgn * off <= half + 5 or sgn * off > half + 400:
            continue
        lo, hi = _project(p, ux, uy)
        if min(hi, t1) - max(lo, t0) > 0.5 * (t1 - t0):
            return False
    return True


def find_sites(view_id, prims, roles, entity_ids):
    """TOPOLOGICAL_SITE_REGISTER rows plus the list of non-sites (collinear stubs) for one view."""
    bands = build_bands(prims, roles)
    sites, non_sites = [], []
    for b in bands:
        cov = b["COVERAGE"]
        if not cov:
            continue
        ux, uy = b["U"]
        def face_at(t, side):
            for f in b["FACES"]:
                if f["SIDE"] == side and min(abs(f["INTERVAL"][0] - t), abs(f["INTERVAL"][1] - t)) <= TERMINATION_TOL:
                    return entity_ids.get(f["ENTITY"], f["ENTITY"])
            return None
        for (lo1, hi1), (lo2, hi2) in zip(cov, cov[1:]):
            span = lo2 - hi1
            if span <= 0:
                continue
            left, right = _termination(b, hi1, bands, prims, roles), _termination(b, lo2, bands, prims, roles)
            p0, p1 = _point_on_axis(b, hi1), _point_on_axis(b, lo2)
            common = {"HOST_WALL_ID": b["BAND_ID"], "FACE_A": face_at(hi1, "A") or face_at(hi1, "AXIS"), "FACE_B": face_at(hi1, "B"), "WALL_AXIS": {"ANGLE_DEG": round(math.degrees(b["ANGLE"]), 3), "OFFSET_MM": round(b["AXIS_OFFSET"], 1)},
                      "WALL_THICKNESS_MM": b["THICKNESS_MM"], "GAP_SPAN_MM": round(span, 1), "LEFT_TERMINATION": left, "RIGHT_TERMINATION": right,
                      "CHORD_MM": [[round(p0[0], 1), round(p0[1], 1)], [round(p1[0], 1), round(p1[1], 1)]], "VIEW": view_id, "HOST_WALL_STATUS": b["STATUS"]}
            if left["KIND"] == "T_JUNCTION" and right["KIND"] == "T_JUNCTION":
                non_sites.append(dict(common, WHY="both ends of the gap terminate at perpendicular walls: two walls meeting a crossing wall, not an opening", RECORD="COLLINEAR_STUBS_NOT_A_SITE"))
                continue
            door = _door_evidence(b, hi1, lo2, prims, roles)
            window = _strip_segments(b, hi1, lo2, prims, roles, ("WINDOW_FRAME", "GLAZING", "UNKNOWN_GEOMETRY", "DECORATIVE_GEOMETRY"))
            glazing = [w for w in window if w["ROLE"] == "GLAZING"]
            free_a, free_b = _free_space(b, hi1, lo2, "A", prims, roles), _free_space(b, hi1, lo2, "B", prims, roles)
            continues = not (free_a and free_b) and span < MIN_PASSAGE_MM
            if span < JUNCTION_MM:
                cls, why = "CAD_JUNCTION_GAP", "gap below the junction tolerance"
            elif span < MIN_PASSAGE_MM:
                cls, why = "MATERIAL_CONTINUITY_GAP", "too narrow for a passage: the wall continues"
            elif door:
                cls, why = "CONFIRMED_DOOR_OPENING", f"door swing of the gap width hinged at a jamb ({len(door)} leaf/leaves)"
            elif glazing or (window and len(window) >= 1 and span <= MAX_SITE_MM):
                cls, why = "CONFIRMED_WINDOW_OPENING", "frame / glazing lines inside the wall strip across the gap"
            elif span > MAX_SITE_MM:
                cls, why = "TRUE_WALL_TERMINATION", f"span {round(span)} mm exceeds the opening band: the wall ends (open plan), no closure"
            elif left["KIND"] == "T_JUNCTION" or right["KIND"] == "T_JUNCTION":
                cls, why = "UNRESOLVED_SITE", "one end meets a crossing wall: passage / stub undecidable from geometry"
            else:
                cls, why = "UNRESOLVED_SITE", "jamb pair with no leaf, frame or glazing: door / passage undecided"
            sid = ids.opening_site_id(view_id, common["FACE_A"] or b["BAND_ID"], common["FACE_B"] or b["BAND_ID"], ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2))
            sites.append(dict(common, SITE_ID=sid, CLASS=cls, WHY=why, MATERIAL_CONTINUES_ACROSS=continues, DOOR_EVIDENCE=door, WINDOW_EVIDENCE=window,
                              OPENING_EVIDENCE={"LEAF_COUNT": sum(d["LEAVES"] for d in door), "DOUBLE_LEAF": len(door) >= 2}, JUNCTION_EVIDENCE=[left, right],
                              FREE_SPACE_ON_SIDE_A=free_a, FREE_SPACE_ON_SIDE_B=free_b, PHYSICAL_SEPARATOR=cls in PHYSICAL_SEPARATOR_CLASSES,
                              TOPOLOGY_CELL_BARRIER=cls in ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING", "UNRESOLVED_SITE", "CONFIRMED_OPEN_PASSAGE", "MATERIAL_CONTINUITY_GAP", "CAD_JUNCTION_GAP"),
                              RELATION_STATUS={"CONFIRMED_DOOR_OPENING": "SOURCE_ESTABLISHED", "CONFIRMED_WINDOW_OPENING": "SOURCE_ESTABLISHED", "CAD_JUNCTION_GAP": "SOURCE_ESTABLISHED",
                                               "MATERIAL_CONTINUITY_GAP": "SOURCE_ESTABLISHED", "TRUE_WALL_TERMINATION": "SOURCE_ESTABLISHED"}.get(cls, "NOT_ESTABLISHED")))
        # free band ends that are not part of a gap: true terminations (open plan ends), recorded, never closed
        for t, which in ((cov[0][0], "START"), (cov[-1][1], "END")):
            term = _termination(b, t, bands, prims, roles)
            if term["KIND"] == "FREE_END" and (b["EXTENT"][1] - b["EXTENT"][0]) >= 500:
                p = _point_on_axis(b, t)
                sites.append({"SITE_ID": ids.make_id("OPENING_SITE", view_id, b["BAND_ID"], which, [p[0], p[1]], tol=50.0), "VIEW": view_id, "HOST_WALL_ID": b["BAND_ID"], "CLASS": "TRUE_WALL_TERMINATION",
                              "WHY": "band end with no return, no crossing wall and no collinear continuation", "GAP_SPAN_MM": None, "CHORD_MM": None, "WALL_THICKNESS_MM": b["THICKNESS_MM"],
                              "LEFT_TERMINATION": term, "RIGHT_TERMINATION": None, "PHYSICAL_SEPARATOR": False, "TOPOLOGY_CELL_BARRIER": False, "RELATION_STATUS": "SOURCE_ESTABLISHED",
                              "FACE_A": None, "FACE_B": None, "DOOR_EVIDENCE": [], "WINDOW_EVIDENCE": [], "HOST_WALL_STATUS": b["STATUS"]})
    return sites, non_sites, bands


def summarise(sites):
    return {c: sum(1 for s in sites if s["CLASS"] == c) for c in SITE_CLASSES}

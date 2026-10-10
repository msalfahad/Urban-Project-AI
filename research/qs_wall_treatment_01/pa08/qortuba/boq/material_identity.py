"""What each measured wall band actually IS, before anything is priced as blockwork.

Two faces with a measured spacing are a geometric pair.  They are not, on that evidence alone, a masonry wall: a column
has two faces, so does a stair flight, so does a drafting arrow, and each of them will report a thickness if you ask for
one.  This module reads the object class off the evidence the band engine already recorded - the CAD layers the faces were
drawn on, the band type, the face roles, the end caps and the fill - and says which bands may become a blockwork quantity.

Nothing here measures anything.  Every field is read from a frozen register and joined; no band is created, moved,
merged or re-thicknessed.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

R1 = Path(PR.OUT_DIR) / "pa08_qortuba_r1"
QS = Path(PR.OUT_DIR) / "pa08_qortuba_qs01"

OBJECT_CLASSES = ("MASONRY_WALL", "COMPOUND_WALL", "COLUMN", "PIER", "SHAFT", "FACADE_ASSEMBLY",
                  "GEOMETRIC_PAIR_ONLY", "UNRESOLVED")
WALL_LAYERS = {"WALL"}
NON_STRUCTURAL_LAYERS = {"FIRNTUR", "B-FURNI", "WINDOW", "DOOR", "FRAME", "OFFICE NAME"}
APARTMENT_ROOMS = {"HALL / whgm", "M.B.ROOM", "BED.ROOM", "PAINTRY", "DRESS", "BATH", "UNLABELLED_INTERNAL_SPACE"}
PIER_MAX_LENGTH_M = 1.50


def reg(folder, name):
    return json.loads((folder / f"{name}.json").read_text("utf-8"))


def classify(band, length_m, rooms):
    """One band, one object class, and the evidence that produced it."""
    layers = set(band["LAYERS"] or [])
    btype = band["BAND_TYPE"]
    roles = {band["ROLE_A"], band["ROLE_B"]}
    caps_both = bool((band["MATERIAL_FILL"] or {}).get("END_CAPS_BOTH"))
    ev = []

    if roles == {"UNKNOWN_GEOMETRY"} or not (layers & (WALL_LAYERS | {"COL", "STAIR"})):
        ev.append(f"drawn on {sorted(layers) or 'no'} layer(s) with face roles {sorted(roles)}: nothing here says wall")
        return "GEOMETRIC_PAIR_ONLY", ev, False
    if btype == "COLUMN_BAND" or roles == {"COLUMN_FACE"}:
        ev.append(f"the band engine typed this {btype} with face roles {sorted(roles)}")
        if caps_both:
            ev.append("closed at both ends with an evidenced fill, which is a column footprint and not a wall run")
        return ("COLUMN" if length_m <= PIER_MAX_LENGTH_M else "PIER"), ev, False
    if layers == {"COL"}:
        ev.append("drawn on the COL layer alone: a column footprint, not a wall")
        return ("COLUMN" if length_m <= PIER_MAX_LENGTH_M else "PIER"), ev, False
    if "STAIR" in layers:
        ev.append(f"drawn on the STAIR layer ({sorted(layers)}), bounding {sorted(rooms) or 'stair space only'}")
        ev.append("stair enclosure or flight geometry: it reports a thickness because it is a pair, not because it is "
                  "masonry the apartment pays for")
        return "SHAFT", ev, False
    if "COL" in layers and layers & WALL_LAYERS:
        ev.append("drawn on both COL and WALL: a column embedded in a wall run, so the area is part wall and part frame")
        if caps_both and length_m <= PIER_MAX_LENGTH_M:
            ev.append("closed at both ends and shorter than a wall run")
            return "PIER", ev, False
        return "COMPOUND_WALL", ev, False
    if layers & WALL_LAYERS:
        extra = sorted(layers - WALL_LAYERS)
        ev.append("drawn on the WALL layer" + (f" with {extra} geometry inside it" if extra else ""))
        ev.append(f"band material status {band['MATERIAL_STATUS']}, face roles {sorted(roles)}")
        return "MASONRY_WALL", ev, True
    ev.append(f"layers {sorted(layers)} do not resolve to an object class")
    return "UNRESOLVED", ev, False


def wall_identity():
    """One row per wall band: what it is, whether blockwork may be billed from it, and why."""
    mb = {b["BAND_ID"]: b for b in reg(R1, "PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER")["ROWS"]}
    rows = []
    for r in reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]:
        b = mb[r["BAND_ID"]]
        rooms = sorted({z for z in r["ROOM_SIDE_A"] + r["ROOM_SIDE_B"] if z in APARTMENT_ROOMS})
        cls, ev, is_masonry = classify(b, r["LENGTH_M"], rooms)
        thk_ok = b["THICKNESS_STATUS"] == "ESTABLISHED"
        rows.append({
            "WALL_ID": r["WALL_ID"], "BAND_ID": r["BAND_ID"],
            "THICKNESS_MM": r["THICKNESS_MM"], "LENGTH_M": r["LENGTH_M"],
            "ROOMS": rooms, "INSIDE_APARTMENT": bool(rooms),
            "CAD_LAYERS": sorted(b["LAYERS"] or []), "BAND_TYPE": b["BAND_TYPE"],
            "FACE_ROLES": [b["ROLE_A"], b["ROLE_B"]],
            "MATERIAL_STATUS": b["MATERIAL_STATUS"], "THICKNESS_STATUS": b["THICKNESS_STATUS"],
            "END_CAPS_BOTH": bool((b["MATERIAL_FILL"] or {}).get("END_CAPS_BOTH")),
            "FILL": (b["MATERIAL_FILL"] or {}).get("FILL"),
            "PHYSICAL_OBJECT_CLASS": cls,
            "BLOCKWORK_CONFIRMED": bool(is_masonry and b["MATERIAL_STATUS"] == "ACCEPTED"),
            "THICKNESS_ITEM_ESTABLISHED": thk_ok,
            "EVIDENCE": ev,
            "STATUS": ("BLOCKWORK_ELIGIBLE" if (is_masonry and b["MATERIAL_STATUS"] == "ACCEPTED" and thk_ok)
                       else "BLOCKWORK_ELIGIBLE_THICKNESS_ITEM_AMBIGUOUS"
                       if (is_masonry and b["MATERIAL_STATUS"] == "ACCEPTED")
                       else "GEOMETRIC_REFERENCE_ONLY"),
            "OPENINGS": r["OPENINGS"],
        })
    return rows


# ---------------------------------------------------------------------------- where each glazed element stands
def _perp_along(angle, x, y):
    a = round(angle, 1)
    if a == 0.0:
        return y, x
    if a == 90.0:
        return -x, y
    return None, None


def glazed_hosts():
    """Join every blue element to the wall band it stands in, and to the room that band bounds.

    The band's own centreline, thickness and extent are frozen fields; so is the element's position.  Matching one to the
    other is a lookup, not a new detection, and the result is labelled DIAGNOSTIC because the register never carried it.
    """
    mb = {b["BAND_ID"]: b for b in reg(R1, "PA08_QORTUBA_R1_MATERIAL_BAND_REGISTER")["ROWS"]}
    walls = reg(QS, "QORTUBA_QS01_BLOCK_WALL_TAKEOFF")["ROWS"]
    rooms = [r for r in reg(QS, "QORTUBA_ROOM_REGISTER")["ROWS"] if r["INSIDE_APARTMENT"]]
    out = []
    for e in reg(QS, "QORTUBA_QS01_BLUE_ELEMENT_SCHEDULE")["ROWS"]:
        x, y = e["POSITION_MM"]
        best = None
        for w in walls:
            c = mb[w["BAND_ID"]].get("CENTERLINE_IF_DERIVED")
            if not c or c.get("KIND") != "LINE":
                continue
            perp, along = _perp_along(c["ANGLE_DEG"], x, y)
            if perp is None:
                continue
            e0, e1 = c["EXTENT_MM"]
            d = abs(perp - c["AXIS_OFFSET_MM"])
            if d <= w["THICKNESS_MM"] / 2 + 60 and e0 - 300 <= along <= e1 + 300:
                if best is None or d < best[1]:
                    best = (w, d)
        host = best[0] if best else None
        # a room NAME is not a room: this plan has two rooms called BED.ROOM, so the attribution is carried by id
        near = []
        for r in rooms:
            b = r["BBOX_MM"]
            gap = max(max(b[0] - x, 0, x - b[2]), max(b[1] - y, 0, y - b[3]))
            if gap <= 1200:
                near.append((r["ROOM_ID"], r["CANONICAL_NAME"], round(gap)))
        near.sort(key=lambda z: z[2])
        band_rooms = sorted({z for z in (host["ROOM_SIDE_A"] + host["ROOM_SIDE_B"]) if z in APARTMENT_ROOMS}) if host else []
        if host and near:
            # keep only candidates the host band actually bounds, when that narrows it
            on_band = [n for n in near if n[1] in band_rooms]
            near = on_band or near
        room_id = near[0][0] if near else None
        room = (near[0][1] if near else (band_rooms[0] if len(band_rooms) == 1 else None))
        out.append({
            "BLUE_ELEMENT_ID": e["BLUE_ELEMENT_ID"], "TYPE": e["TYPE"], "WIDTH_M": round(e["WIDTH_MM"] / 1000, 4),
            "WALL_BELOW": e["WALL_BELOW"],
            "INTERRUPTS_THE_WALL_IN_PLAN": not e["WALL_BELOW"],
            "HOST_WALL_ID": (host["WALL_ID"] if host else None),
            "HOST_WALL_THICKNESS_MM": (host["THICKNESS_MM"] if host else e["FRAME_DEPTH_MM"]),
            "HOST_WALL_OPENING_SITES": (len(host["OPENINGS"]) if host else None),
            "HOST_BAND_LAYERS": (sorted(mb[host["BAND_ID"]]["LAYERS"] or []) if host else []),
            "HOST_BAND_ROOMS": band_rooms,
            "ROOM": room, "ROOM_ID": room_id,
            "ROOM_BBOX_GAP_MM": (near[0][2] if near else None),
            "ROOM_BASIS": (f"nearest room bounding box on the host band, {near[0][2]} mm away, from the frozen register"
                           if near else "the only apartment room the host band bounds" if len(band_rooms) == 1
                           else "not resolved"),
            "ROOM_STATE": "DIAGNOSTIC_ATTRIBUTION" if (near or len(band_rooms) == 1) else "NOT_ESTABLISHED",
            "OPENING_SITE_ID": e["OPENING_SITE_ID"],
            "SKIRTING_EFFECT_IN_WORKPAPER": e["SKIRTING_EFFECT"],
        })
    return out


def summary():
    rows = wall_identity()
    by_t = defaultdict(lambda: defaultdict(float))
    for r in rows:
        t = str(int(r["THICKNESS_MM"]))
        by_t[t][r["PHYSICAL_OBJECT_CLASS"]] += r["LENGTH_M"]
    return {t: {k: round(v, 3) for k, v in sorted(d.items())} for t, d in sorted(by_t.items(), key=lambda kv: int(kv[0]))}

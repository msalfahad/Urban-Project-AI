"""WET_BASE_OWNER_V1 (T-440, rule R-T440-1, any villa): one owner per wall base where a skirting line's room runs
into a room tiled full height.

Physical element: the BASE of a wall or column face (the strip from finished floor up to the skirting height). In a
room tiled full height (owner Q-06 / Q-37 A / Q-48 A: wet rooms and the open pantry box) the wall tile covers that
strip, so no skirting is built there; the face's base has ONE owner, the wall-tile line (ERS s.2.2, UP-SKIRT-001).
The engine keys skirting lines by ENGINE room; an engine room can hold a tiled room only in PART (open plan), so its
skirting line can carry tiled faces. This module audits each face of such a line:

    face role WALL / COLUMN (base-bearing)   in a FULL-HEIGHT-TILE room -> base owner = that room's wall-tile line;
                                                                           any skirting the line still carries on
                                                                           the face is an OVER-COUNT (lm)
                                             in a DRY room               -> base owner = the skirting line (KEPT)
                                             room or class not known     -> UNRESOLVED (HELD, never 0, never moved)
    face role DOOR / PASSAGE / ZONE / OPEN   -> no base (NONE), whatever the room
    face role WINDOW (sill window)           -> the base under the sill: tile in a tiled room, the skirting line's
                                                bounded range in a dry room (reported, not valued here)

It moves no quantity: it states, per face, the owner and the over-count the line still carries. A carried length that
is not known stays UNKNOWN (the over-count is then not a number). Coordinates never enter; faces are ids, drawn
handles, roles and metres.
"""
from __future__ import annotations

RULE_ID = "R-T440-1"
METHOD = "WET_BASE_OWNER_V1"
TOL_M = 0.0005

BASE_ROLES = ("WALL", "COLUMN")
NO_BASE_ROLES = ("DOOR", "PASSAGE", "ZONE", "OPEN")
WINDOW_ROLES = ("WINDOW",)
ROLES = BASE_ROLES + NO_BASE_ROLES + WINDOW_ROLES
TILED = "WET_FULL_HEIGHT_TILE"
DRY = "DRY"
CLASSES = (TILED, DRY)


class AuditError(ValueError):
    pass


def _num(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise AuditError(f"{what}: a number in metres is required, got {v!r}")
    if v < 0:
        raise AuditError(f"{what}: negative length {v}")
    return float(v)


def validate(faces, rooms):
    """faces: [{face_id, line_id, room, role, length_m, carried_lm (None = not known), handles}];
    rooms: {room_id: {finish_class, tile_line, class_source}}."""
    seen = set()
    for f in faces:
        fid = f.get("face_id")
        if not fid:
            raise AuditError("a face needs a face_id")
        if fid in seen:
            raise AuditError(f"{fid}: face listed twice (one face, one row)")
        seen.add(fid)
        if f.get("unit", "m") != "m":
            raise AuditError(f"{fid}: unit must be m (mm or other units are refused)")
        if f.get("role") not in ROLES:
            raise AuditError(f"{fid}: unknown role {f.get('role')!r}")
        ln = _num(f.get("length_m"), f"{fid} length_m")
        if f.get("carried_lm") is not None:
            c = _num(f["carried_lm"], f"{fid} carried_lm")
            if c > ln + TOL_M:
                raise AuditError(f"{fid}: carries {c} lm on a {ln} m face")
    for rid, r in rooms.items():
        if r.get("finish_class") not in CLASSES and r.get("finish_class") is not None:
            raise AuditError(f"{rid}: unknown finish class {r.get('finish_class')!r}")
        if r.get("finish_class") == TILED and not r.get("class_source"):
            raise AuditError(f"{rid}: a tiled class needs its source (owner answer / rule)")


def face_owner(f, rooms):
    """one row per face: base owner, over-count, status."""
    role, ln, car = f["role"], float(f["length_m"]), f.get("carried_lm")
    room = rooms.get(f.get("room")) if f.get("room") else None
    cls = room.get("finish_class") if room else None
    row = {"face_id": f["face_id"], "line_id": f["line_id"], "room": f.get("room"), "role": role,
           "handles": f.get("handles", ""), "length_m": round(ln, 6), "finish_class": cls,
           "carried_lm": None if car is None else round(float(car), 6)}
    if role in NO_BASE_ROLES:
        row.update(base_lm=0.0, owner="NONE", over_lm=0.0, status="NO_BASE")
        return row
    if room is None or cls is None:
        row.update(base_lm=round(ln, 6) if role in BASE_ROLES else None, owner=None, over_lm=None,
                   status="UNRESOLVED")
        return row
    if role in WINDOW_ROLES:
        if cls == TILED:
            row.update(base_lm=0.0, owner=room.get("tile_line") or None,
                       over_lm=None if car is None else round(float(car), 6),
                       status="WINDOW_BASE_TILED" if room.get("tile_line") else "UNRESOLVED")
        else:
            row.update(base_lm=0.0, owner=f["line_id"], over_lm=0.0, status="WINDOW_BASE_RANGE")
        return row
    if cls == DRY:
        row.update(base_lm=round(ln, 6), owner=f["line_id"], over_lm=0.0, status="KEPT")
        return row
    tile = room.get("tile_line")
    if not tile:
        row.update(base_lm=round(ln, 6), owner=None, over_lm=None, status="UNRESOLVED")
        return row
    over = None if car is None else round(float(car), 6)
    row.update(base_lm=round(ln, 6), owner=tile, over_lm=over,
               status="UNKNOWN" if car is None else ("OVER_COUNT" if over > TOL_M else "TILE_OWNS"))
    return row


def audit(faces, rooms):
    validate(faces, rooms)
    rows = [face_owner(f, rooms) for f in faces]
    known = [r for r in rows if r["over_lm"] is not None]
    unknown = [r["face_id"] for r in rows if r["over_lm"] is None]
    tiled_base = sum(r["base_lm"] for r in rows if r["finish_class"] == TILED and r["role"] in BASE_ROLES)
    return {
        "rule": RULE_ID, "method": METHOD, "rows": rows,
        "over_count_lm": None if unknown else round(sum(r["over_lm"] for r in known), 6),
        "over_count_known_lm": round(sum(r["over_lm"] for r in known), 6),
        "unknown_faces": unknown,
        "tiled_base_lm": round(tiled_base, 6),
        "kept_lm": round(sum(r["base_lm"] for r in rows if r["status"] == "KEPT"), 6),
    }


def closure(room_base_lm, parts):
    """a tiled room's whole wall + column base against the parts each line (or no line) carries:
    parts = {label: lm or None}. Returns residual (None when a part is not known)."""
    base = _num(room_base_lm, "room_base_lm")
    if any(v is None for v in parts.values()):
        return {"base_lm": base, "parts": parts, "residual_lm": None, "closes": False}
    res = round(base - sum(_num(v, k) for k, v in parts.items()), 6)
    return {"base_lm": base, "parts": parts, "residual_lm": res, "closes": abs(res) <= TOL_M}


def additions_clear(additions, rooms):
    """a later addition to the same skirting line (e.g. a cut-off dry face joined back) must not land on a tiled
    room's face: returns the addition faces that do (they would re-create the over-count)."""
    bad = []
    for a in additions:
        r = rooms.get(a.get("room")) if a.get("room") else None
        if r is None or r.get("finish_class") is None:
            bad.append({"face_id": a["face_id"], "why": "room not known: UNRESOLVED"})
        elif r["finish_class"] == TILED and a.get("role") in BASE_ROLES:
            bad.append({"face_id": a["face_id"], "why": f"on tiled room {a['room']}: base owned by the wall tile"})
    return bad

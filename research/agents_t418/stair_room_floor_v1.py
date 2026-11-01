"""STAIR_ROOM_FLOOR_V1 (T-418, research only, not wired): the floor-finish parts of a STAIR ROOM face.

Defect it answers (T-418, from T-414): a room classified as a stair room (its face holds flights, a well or a landing)
received NO floor-finish line for its whole face, so the floor parts inside it (the hall at the foot of the flight, a
lower lobby, the floor beyond the stair width at an arrival) fell out of the floor-finish family silently.

Rule R-T418-1 (every villa, finishes; scope: a room face that holds any stair element):
  1. the face is PARTITIONED, never dropped: every m2 of it is one of
       B7      a stair element (flight treads / winders below the cut, a landing between flights, an arrival landing
               that an owner rule gives to the stair); owned by STAIRS, never a floor-finish quantity here;
       FLOOR   a walkable floor at a printed level (a level mark inside it, or the storey FFL reached without a step);
               owned by FLOOR FINISHES (B3-01), one line per part, finish by the owner rule or the approved default;
       VOID    an opening in the floor (stair well, flights seen through the slab opening): no floor, no line;
       SOLID   a wall, divider, stringer or column footprint inside the face: no floor;
       UNREAD  a part the drawing does not settle: HELD with the bound 0 .. its area, never 0 and never a figure;
  2. the parts re-add to the face (closure) and never overlap each other;
  3. a FLOOR part with no level evidence is HELD (UNREAD), never assumed at the storey FFL;
  4. a FLOOR part that overlaps a B7 polygon, an exterior space (porch / court) or another room's floor polygon is
     REFUSED (tread counted as floor, porch counted inside, a floor counted twice);
  5. CENSUS: every face with a FLOOR part must be bound to a floor-finish line id; a FLOOR part with no line is a
     SILENT_OMISSION finding, never 0.

Units: 'm' or 'mm' on input; output m / m2. Geometry with shapely (pinned in requirements.txt).
"""
from __future__ import annotations

from shapely.geometry import Polygon
from shapely.ops import unary_union

METHOD = "STAIR_ROOM_FLOOR_V1"
RULE = "R-T418-1"
KINDS = ("B7", "FLOOR", "VOID", "SOLID", "UNREAD")
STATUS_DC = "DRAWING-CONFIRMED"
STATUS_OWNER = "ASSUMED — OWNER-APPROVED"
STATUS_HELD = "HELD"
TOL_M2 = 1e-6
SCALE = {"m": 1.0, "mm": 0.001}


class Refused(ValueError):
    """an input the rule refuses (the message names the part and the reason)"""


def _poly(pts, s):
    p = Polygon([(x * s, y * s) for x, y in pts])
    if not p.is_valid or p.area <= 0:
        raise Refused(f"invalid polygon {pts!r}")
    return p


def partition(room, units="m", others=()):
    """room: {'id', 'storey_ffl', 'face': [(x, y) ...], 'parts': [{'id', 'kind', 'poly': [...], 'level': float|None,
    'level_src': str, 'finish': str|None, 'finish_rule': str|None, 'finish_status': str|None, 'owner_line': str|None,
    'note': str}]}; others: [{'id', 'class': 'B7'|'EXTERIOR'|'FLOOR', 'poly': [...]}] polygons of other lines / spaces
    in the same frame. Returns {'room', 'face_m2', 'rows', 'closure_m2', 'floor_m2', 'held_bound', 'findings'}."""
    if units not in SCALE:
        raise Refused(f"units {units!r} not in {sorted(SCALE)}")
    s = SCALE[units]
    face = _poly(room["face"], s)
    ffl = room.get("storey_ffl")
    rows, polys = [], []
    for p in room["parts"]:
        k = p["kind"]
        if k not in KINDS:
            raise Refused(f"{p['id']}: kind {k!r} not in {KINDS}")
        g = _poly(p["poly"], s)
        if g.difference(face).area > TOL_M2:
            raise Refused(f"{p['id']}: lies {g.difference(face).area:.6f} m2 outside the room face")
        for q_id, q in polys:
            ov = g.intersection(q).area
            if ov > TOL_M2:
                raise Refused(f"{p['id']} overlaps {q_id} by {ov:.6f} m2 (one m2, one part)")
        polys.append((p["id"], g))
        row = {"room": room["id"], "part": p["id"], "kind": k, "area_m2": round(g.area, 6), "level": p.get("level"),
               "level_src": p.get("level_src", ""), "family": None, "status": None, "bound": None,
               "finish": None, "finish_rule": None, "owner_line": p.get("owner_line"), "note": p.get("note", "")}
        if k == "FLOOR":
            if p.get("level") is None:
                # rule 3: a floor part with no level evidence is never assumed at the storey FFL
                row.update(kind="UNREAD", status=STATUS_HELD, bound=[0.0, round(g.area, 6)],
                           note=(row["note"] + "; " if row["note"] else "") + "no level evidence: HELD")
            else:
                for o in others:
                    og = _poly(o["poly"], s)
                    ov = g.intersection(og).area
                    if ov > TOL_M2:
                        what = {"B7": "stair element counted as floor", "EXTERIOR": "exterior space counted inside",
                                "FLOOR": "floor counted twice"}.get(o["class"], o["class"])
                        raise Refused(f"{p['id']}: {what} ({o['id']}, {ov:.6f} m2)")
                if not p.get("finish") or not p.get("finish_status"):
                    raise Refused(f"{p['id']}: a floor part needs its finish and the finish's status (rule or HELD)")
                sub = ffl is not None and abs(p["level"] - ffl) > 1e-9
                row.update(family="B3-01", status=STATUS_DC, finish=p["finish"], finish_rule=p.get("finish_rule"),
                           finish_status=p["finish_status"], sub_level=sub)
        elif k == "UNREAD":
            row.update(status=STATUS_HELD, bound=[0.0, round(g.area, 6)])
        elif k == "B7":
            row.update(family="B7", status="OWNED_ELSEWHERE")
        else:
            row.update(status="NO_FLOOR")
        rows.append(row)
    union = unary_union([g for _, g in polys]) if polys else Polygon()
    closure = face.area - union.area
    if abs(closure) > 1e-4 or face.symmetric_difference(union).area > 1e-4:
        raise Refused(f"{room['id']}: parts do not re-add to the face (face {face.area:.6f}, parts {union.area:.6f})")
    floor = sum(r["area_m2"] for r in rows if r["kind"] == "FLOOR")
    held = [r["bound"] for r in rows if r["kind"] == "UNREAD"]
    return {"room": room["id"], "face_m2": round(face.area, 6), "rows": rows, "closure_m2": round(closure, 6),
            "floor_m2": round(floor, 6),
            "held_bound": [0.0, round(sum(b[1] for b in held), 6)] if held else None,
            "findings": [{"finding": "SILENT_OMISSION", "room": room["id"], "part": r["part"], "m2": r["area_m2"]}
                         for r in rows if r["kind"] == "FLOOR" and not r["owner_line"]]}


def census(results, floor_lines):
    """rule 5 over several rooms: floor_lines = {part id: line id} of the candidate. A FLOOR part with no line is a
    SILENT_OMISSION; a line bound to a non-floor part is refused."""
    out = []
    for res in results:
        for r in res["rows"]:
            lid = floor_lines.get(r["part"]) or r["owner_line"]
            if r["kind"] != "FLOOR":
                if r["part"] in floor_lines:
                    raise Refused(f"{r['part']}: a floor-finish line on a {r['kind']} part")
                continue
            out.append({"room": res["room"], "part": r["part"], "m2": r["area_m2"], "line": lid,
                        "state": "BOUND" if lid else "SILENT_OMISSION"})
    return out

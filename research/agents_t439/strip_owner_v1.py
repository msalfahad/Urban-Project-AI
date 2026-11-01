"""STRIP_OWNER_V1 (research module, unwired; any villa; provenance T-439): who owns the CEILING and the SKIRTING of a
floored strip that carries a floor-finish line but no ceiling or skirting line (the T-435 'SILENT' class).

Rule R-T439-1 (proposed; rules UP-CEIL-001, UP-SKIRT-001, R-T286-1, R-T440-1, R-CEIL-R2-1 .. 3 at their own scope):

1. KIND. A strip is a DOORWAY strip only when opening jambs bound it on two edges (R-T286-1). A strip lying inside a
   printed room box (area inside the box = its area, 5 cm2 tolerance) is a ROOM PIECE of that room, whatever engine
   zone line, fixture outline or prolonged edge cut it out. Anything else (outside every box, across two boxes) is
   HELD with its area kept.
2. CEILING. DOORWAY strip: reason OPENING_SOFFIT_IN_WALL (the head is the opening's soffit / lintel); a room ceiling
   proposed for it is REFUSED unless a drawn soffit is cited. ROOM PIECE: the room's ceiling continues over it: one
   proposal line = the strip's plan area (horizontal decor, incl. bulkhead undersides, DRAWING-CONFIRMED area, the
   room's class), plus the owner-method bulkhead faces of the beam face segments that lie in the strip and that no
   existing line carries: height D - max(0.60, D_neighbour) where the neighbour is slab or a CALCULATED beam (owner
   Q-43 line + Q-48 A, ASSUMED - OWNER-APPROVED); a face toward an unregistered / held / conflicting piece, or of a
   beam that is not CALCULATED, is HELD in lm (Q-61 C), never 0. The beam faces are measured on the WHOLE room
   ceiling, not on the strip (an engine zone line never makes or hides a bulkhead).
3. SKIRTING (per edge). WALL_FACE in a room tiled full height: the base belongs to the room's wall-tile line
   (TILE_OWNS, R-T440-1; refused without that line); WALL_FACE in any other room: skirting lm = the drawn face, or, if
   a fixture outline covers the face, HELD (no owner rule on skirting behind fixed joinery); OPENING_JAMB: DOORWAY
   (UP-SKIRT-001: not across door openings; the jamb returns stay with the opening's own record); ROOM_EDGE_OPEN,
   ZONE_LINE_UNDRAWN, FIXTURE_OUTLINE: no wall, no base (NO_BASE), length named. An unknown role is refused.
4. Every result names its evidence; HELD / UNKNOWN never become 0; lengths in metres, areas in m2 (another unit is
   refused).
No villa constant, layer, handle or room id is in this module."""
from __future__ import annotations

OWNER_ALLOW = 0.60          # owner Q-43 manual line: beam allowance below the slab (m)
BOX_TOL_M2 = 0.0005         # a strip lies in a box when inside-area >= area - 5 cm2
ROLES = ("WALL_FACE", "OPENING_JAMB", "ROOM_EDGE_OPEN", "ZONE_LINE_UNDRAWN", "FIXTURE_OUTLINE")
ST_DC = "DRAWING-CONFIRMED"
ST_OA = "ASSUMED - OWNER-APPROVED"
ST_H = "HELD"
ST_NA = "NOT_APPLICABLE_WITH_EVIDENCE"


class StripError(ValueError):
    """The record cannot be decided as given (unit, unknown role, missing owner line, refused proposal)."""


def _unit(rec, want, key="unit"):
    u = rec.get(key, want)
    if u != want:
        raise StripError(f"{rec.get('id', '?')}: unit {u!r}, expected {want!r}")


# ---------------------------------------------------------------------------------------------- geometry (optional)
def classify_edges(polygon, drawn, tol=0.002):
    """polygon: shapely Polygon of the strip (metres); drawn: [(ref, role, shapely LineString)] of the drawn lines near
    it. Returns [{'length_m', 'role', 'refs'}] per edge: the role of a drawn line lying on >= 50 % of the edge, else
    ZONE_LINE_UNDRAWN (an engine zone line is not a drawn line)."""
    from shapely.geometry import LineString
    out = []
    cs = list(polygon.exterior.coords)
    for a, b in zip(cs, cs[1:]):
        e = LineString([a, b])
        if e.length < 1e-6:
            continue
        hits = [(r, ro) for r, ro, s in drawn if s.buffer(tol, cap_style=2).intersection(e).length >= 0.5 * e.length]
        role = hits[0][1] if hits else "ZONE_LINE_UNDRAWN"
        if len({ro for _, ro in hits}) > 1:
            role = "CONFLICT"
        out.append({"length_m": round(e.length, 6), "role": role, "refs": sorted(r for r, _ in hits)})
    return out


# ------------------------------------------------------------------------------------------------------- the rule
def strip_kind(strip, room):
    _unit(strip, "m2")
    jambs = sum(1 for e in strip["edges"] if e["role"] == "OPENING_JAMB")
    if jambs >= 2:
        return "DOORWAY"
    inside = strip.get("in_room_box_m2")
    if room is not None and inside is not None and inside >= strip["floor_m2"] - BOX_TOL_M2:
        return "ROOM_PIECE"
    return "HELD"


def _face_height(seg):
    if seg.get("beam_status") != "CALCULATED" or seg.get("beam_depth_m") is None:
        return None
    nc = seg.get("neighbour")
    if nc == "SLAB":
        dn = 0.0
    elif nc == "BEAM" and seg.get("neighbour_status") == "CALCULATED" and seg.get("neighbour_depth_m") is not None:
        dn = seg["neighbour_depth_m"]
    else:
        return None
    return max(0.0, seg["beam_depth_m"] - max(OWNER_ALLOW, dn))


def ceiling(strip, room, kind, segments=(), proposal=None):
    """segments: beam face segments in this strip, measured on the whole room ceiling: {'m', 'beam', 'beam_depth_m',
    'beam_status', 'neighbour' (SLAB / BEAM / UNREGISTERED / ...), 'neighbour_depth_m', 'neighbour_status',
    'carried_by' (an existing line id or None)}. proposal: an attempted {'kind': 'ROOM_CEILING', 'soffit_ref'} to test
    refusals. Returns the ceiling record."""
    if kind == "DOORWAY":
        if proposal and proposal.get("kind") == "ROOM_CEILING" and not proposal.get("soffit_ref"):
            raise StripError(f"{strip['id']}: a room ceiling on a doorway strip needs a drawn soffit (none cited)")
        return {"status": "REASON", "code": "OPENING_SOFFIT_IN_WALL", "m2": None,
                "evidence": "jambs bound the strip: its head is the opening's soffit (UP-CEIL-001 eligible surfaces)"}
    if kind == "HELD":
        return {"status": ST_H, "code": "STRIP_OUTSIDE_EVERY_BOX", "m2": None, "area_kept_m2": strip["floor_m2"]}
    bulk, held, low = [], [], []
    for s in segments:
        _unit(s, "m")
        if s.get("carried_by"):
            continue
        h = _face_height(s)
        if h is None:
            held.append({"beam": s.get("beam"), "m": round(s["m"], 4), "why": "neighbour or beam not CALCULATED "
                         "(Q-61 C: HELD edge, never 0)", "neighbour": s.get("neighbour")})
        elif h <= 0:
            low.append({"beam": s.get("beam"), "m": round(s["m"], 4), "why": "beam no deeper than the 0.60 m owner "
                        "allowance or than its neighbour: hidden above the decor ceiling, no face"})
        else:
            bulk.append({"beam": s.get("beam"), "m": round(s["m"], 4), "height_m": round(h, 4),
                         "m2": round(s["m"] * h, 6)})
    bm2 = round(sum(b["m2"] for b in bulk), 6)
    return {"status": "PROPOSAL", "code": "CEILING_CONTINUES_FROM_ROOM", "room": room["id"],
            "room_class": room["class"], "decor_m2": round(strip["floor_m2"], 6), "decor_status": ST_DC,
            "bulkhead_faces": bulk, "bulkhead_m2": bm2, "bulkhead_status": ST_OA if bulk else None,
            "held_edges": held, "held_edge_m": round(sum(h["m"] for h in held), 4) if held else None,
            "no_face": low,
            "paintable_owner_m2": round(strip["floor_m2"] + bm2, 6),
            "board_type": ST_H if room["class"] == "WET" else "gypsum board (dry room)"}


def skirting(strip, room, kind):
    rows = []
    for e in strip["edges"]:
        _unit(e, "m")
        r, L = e["role"], e["length_m"]
        if r not in ROLES:
            raise StripError(f"{strip['id']}: edge role {r!r} is not decidable (refused)")
        if r == "WALL_FACE":
            if room is not None and room.get("full_height_tile"):
                if not room.get("wall_tile_line"):
                    raise StripError(f"{strip['id']}: tiled room {room['id']} without its wall-tile line")
                rows.append({"m": L, "owner": "TILE_OWNS", "line": room["wall_tile_line"], "status": ST_NA})
            elif e.get("fixture_covers"):
                rows.append({"m": L, "owner": "HELD_BEHIND_FIXTURE", "line": None, "status": ST_H})
            elif kind == "HELD":
                rows.append({"m": L, "owner": "HELD_WITH_STRIP", "line": None, "status": ST_H})
            else:
                rows.append({"m": L, "owner": "SKIRTING", "line": (room or {}).get("skirting_line"), "status": ST_DC})
        elif r == "OPENING_JAMB":
            rows.append({"m": L, "owner": "DOORWAY", "line": None, "status": "REASON"})
        else:
            rows.append({"m": L, "owner": "NO_BASE", "line": None, "status": "REASON"})
    skirt = [x["m"] for x in rows if x["owner"] == "SKIRTING"]
    held = [x["m"] for x in rows if x["status"] == ST_H]
    tile = [x["m"] for x in rows if x["owner"] == "TILE_OWNS"]
    return {"rows": rows, "skirting_lm": round(sum(skirt), 4) if skirt else None,
            "held_lm": round(sum(held), 4) if held else None, "tile_owned_lm": round(sum(tile), 4) if tile else None,
            "status": (ST_H if held else ST_DC if skirt else ST_NA if tile else "REASON")}


def decide(strip, room, segments=(), proposal=None):
    k = strip_kind(strip, room)
    return {"id": strip["id"], "kind": k, "floor_m2": strip["floor_m2"],
            "ceiling": ceiling(strip, room, k, segments, proposal), "skirting": skirting(strip, room, k)}


def room_closure(box_net_m2, pieces_m2):
    """The room box re-added from its pieces (m2): residual, never forced to 0."""
    if any(v is None for v in pieces_m2.values()):
        raise StripError("a piece without a figure cannot close a box")
    return round(box_net_m2 - sum(pieces_m2.values()), 6)


"""R-T335-1: CEILING-PLANE CROSS-TRADE OWNERSHIP (research rule, any villa; T-335). Pure Python, no drawing access.

Provenance: R-T295-1 (one owner surface per plan piece, T-295 MERGED 964c5ebe, imported, not edited), R-CEIL-R3-2 (a
bulkhead face only on a free beam edge with decor ceiling on its open side, T-283 MERGED 6e141df6), the owner wall
height Q-43 / Q-48 A (plaster, paint and wall tile stop at the underside of the 0.15 decor ceiling: GF 3.65, 1F / 2F
3.35), Q-52 C MODIFIED (plaster MAY run above the false ceiling depending on the specification: no specification prints
it, so the band above the decor ceiling is HELD), UP-CEIL-001 / O-P8-02 (every ceiling line PROVISIONAL: the ceiling type
is not in a plan), WORKFLOW_CONTROLS s.5 (statuses), ENGINEERING_REASONING_STANDARD s.2.1 / s.3 (build before deduct;
one element, several geometries). Nothing here edits an engine module, rule or knowledge file, candidate or released
line: lane I (T-284) applies the FILL table.

PHYSICAL ELEMENT. The ceiling plane of a room is everything the occupant sees above the wall finish: (1) the
horizontal decor ceiling (gypsum board on hangers, 0.15 below the slab soffit, Q-48 A), (2) bulkhead vertical faces
where a beam drops below it on a free edge, (3) an exposed slab soffit (plaster + paint on concrete) ONLY where no decor
ceiling is built, (4) no-ceiling / stair / dome pieces (R-T295-1). Wall finishes (plaster, paint, wall tile) are
VERTICAL faces up to the decor underside; the band between the decor underside and the slab soffit or beam bottom is a
wall face hidden behind the decor ceiling (Q-52 C: HELD), never a ceiling face. A surface carries LAYERS: the board
(gypsum, FIN.CEILING), the plaster coat (FIN.PLASTER) and the paint coat (FIN.PAINT). Different layers on one face are
different work (board + paint is not a double count); the SAME layer on one face in two lines is.

Rules (each refusal code is the first word of the error):
1. ONE LAYER, ONE LINE. Every claim names (surface_id, layer, line_id). The same (surface, layer) in two lines is refused
   (LAYER_TWICE).
2. LAYER FITS THE SURFACE. A decor (gypsum) horizontal piece takes BOARD and PAINT only: a PLASTER claim on it is
   refused (PLASTER_BEHIND_DECOR: the slab soffit behind a gypsum ceiling is not a finished face unless a specification
   says so; concrete ceiling plaster NOT SPECIFIED -> HELD by name, never booked). An exposed soffit takes PLASTER and
   PAINT only: a BOARD claim is refused (BOARD_ON_EXPOSED). A bulkhead face takes BOARD and PAINT. VOID / DOME pieces take
   nothing (VOID_FINISHED). A STAIR_SOFFIT piece belongs to the stair finish, never to a FIN.CEILING decor line or a wall
   line (STAIR_SOFFIT_IN_CEILING / STAIR_SOFFIT_IN_WALL); it may bind to a STAIRWELL-role line (the candidate's
   'stair-well ceiling / soffit' line, whose scope names the soffit) or to no line. An EXTERIOR soffit line (over
   outside air) holds no interior face (INTERIOR_IN_EXTERIOR_LINE).
3. WALL LINES STOP AT THE DECOR UNDERSIDE. A wall face (plaster / paint / tile) whose top is above the decor underside of
   its room by more than TOL_H books part of the hidden band: refused (BAND_IN_WALL_LINE) unless the band is declared
   HELD apart (then it is a HELD row, blank, with its 0 .. length x band height range shown). A wall top below the decor
   underside leaves an unfinished strip: listed GAP with its m2, never silent. A wall line claiming a horizontal piece is
   refused (HORIZONTAL_IN_WALL_LINE); a wall line claiming a bulkhead face is refused (BULKHEAD_IN_WALL_LINE): a beam
   face on the wall line is wall (below the decor underside only), a free beam edge is bulkhead (R-CEIL-R3-2).
4. HELD / UNKNOWN surfaces are BLANK with a named item, never 0 and never in a line's carried total (HELD_AS_ZERO).
5. UNITS: areas m2, lengths and heights m (BAD_UNITS on a value that is plainly millimetres).
6. DOUBLE COUNT REPORT. `overlaps(claims)` returns every (surface, layer) booked twice with its m2; `cross_trade(...)`
   returns per room: ceiling pieces (horizontal, by owner), bulkheads, wall lines (height vs decor underside), the band,
   gaps, and the double count in m2 (0.000 when the rule holds).
"""
from __future__ import annotations

RULE_ID = "R-T335-1"
TOL = 0.00011           # area tolerance (sources state m2 to 0.0001)
TOL_H = 0.005           # height tolerance (m): printed levels are to 0.01 m

BOARD, PLASTER, PAINT, TILE = "BOARD", "PLASTER", "PAINT", "TILE"
LAYERS = (BOARD, PLASTER, PAINT, TILE)
DECOR, EXPOSED, BULKHEAD, VOID, DOME, STAIR_SOFFIT, HELD_CEILING = (
    "DECOR", "EXPOSED_SOFFIT", "BULKHEAD", "VOID", "DOME", "STAIR_SOFFIT", "HELD_CEILING")
WALL = "WALL"
SURFACES = (DECOR, EXPOSED, BULKHEAD, VOID, DOME, STAIR_SOFFIT, HELD_CEILING, WALL)
ALLOWED = {DECOR: (BOARD, PAINT), EXPOSED: (PLASTER, PAINT), BULKHEAD: (BOARD, PAINT), VOID: (), DOME: (),
           STAIR_SOFFIT: (PLASTER, PAINT, BOARD), HELD_CEILING: (BOARD, PAINT), WALL: (PLASTER, PAINT, TILE)}
WALL_CODES = ("FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE")
CEILING_CODES = ("FIN.CEILING",)
DETERMINATE = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED")
HELD_ST = ("HELD", "UNKNOWN")


class CrossTradeError(ValueError):
    """a claim, surface or wall line the rule refuses (the code is the first word of the message)."""


def _num(v, what, big):
    if v is None:
        return None
    v = float(v)
    if v < 0:
        raise CrossTradeError(f"NEGATIVE: {what} {v!r}")
    if v > big:
        raise CrossTradeError(f"BAD_UNITS: {what} {v!r} is not a villa value (millimetres?)")
    return v


def check_surface(s):
    """s: surface_id, room_id, kind (SURFACES), m2, status, held_item; a WALL also top_m (its finish top above F.F.L.),
    length_m."""
    sid = s.get("surface_id")
    if s.get("kind") not in SURFACES:
        raise CrossTradeError(f"UNKNOWN_SURFACE: {sid} {s.get('kind')!r}")
    _num(s.get("m2"), f"{sid} m2", 2000)
    _num(s.get("top_m"), f"{sid} top", 30)
    _num(s.get("length_m"), f"{sid} length", 500)
    st = s.get("status")
    if st in HELD_ST:
        if s.get("m2") is not None and s.get("carried") is not None:
            raise CrossTradeError(f"HELD_AS_ZERO: {sid} is {st}; blank with its item, never {s.get('carried')!r}")
        if not s.get("held_item"):
            raise CrossTradeError(f"HELD_UNNAMED: {sid} is {st} without its named item")
    elif st not in DETERMINATE:
        raise CrossTradeError(f"UNKNOWN_STATUS: {sid} {st!r}")
    return True


def role(line):
    """the surface a line measures: a declared `role` (a ceiling paint / soffit plaster line says CEILING), else by its
    item code: FIN.CEILING -> CEILING, FIN.PLASTER / FIN.PAINT / FIN.WALL.TILE -> WALL (the candidate's room-face
    lines are wall faces: face length x the owner wall height, Q-43 / Q-48 A), anything else OTHER."""
    if line.get("role"):
        return line["role"]
    code = line["item_code"]
    return "CEILING" if code in CEILING_CODES else "WALL" if code in WALL_CODES else "OTHER"


def ceiling_role(element_id):
    """the role of a candidate FIN.CEILING line from its element id: '<room>:ceiling' / ':ceiling over void' = a room
    (decor) ceiling line; ':stairwell ceiling' = the stair-well ceiling / soffit line (BLOCKED_RFI in the candidate:
    its scope includes the stair underside); 'SOFFIT:<floor>:PL-nn' = an exterior soffit over outside air."""
    e = element_id or ""
    if e.startswith("SOFFIT:"):
        return "EXTERIOR"
    if e.endswith(":stairwell ceiling"):
        return "STAIRWELL"
    if e.endswith(":ceiling") or e.endswith(":ceiling over void"):
        return "CEILING"
    raise CrossTradeError(f"UNKNOWN_CEILING_LINE: element {element_id!r} (bind the line's grain before integrating)")


def check_claim(claim, surfaces, lines):
    """rule 2 / 3 / 4 on one claim {surface_id, layer, line_id}."""
    s = surfaces.get(claim["surface_id"])
    if s is None:
        raise CrossTradeError(f"UNKNOWN_SURFACE: claim on {claim['surface_id']!r}")
    ln = lines.get(claim["line_id"])
    if ln is None:
        raise CrossTradeError(f"UNKNOWN_LINE: {claim['line_id']!r}")
    lay, kind, code = claim["layer"], s["kind"], ln["item_code"]
    wall_line, ceil_line = role(ln) == "WALL", role(ln) == "CEILING"
    if lay not in LAYERS:
        raise CrossTradeError(f"UNKNOWN_LAYER: {lay!r}")
    if s.get("status") in HELD_ST:
        raise CrossTradeError(f"HELD_AS_ZERO: {s['surface_id']} is {s['status']} ({s.get('held_item')}); it is booked "
                              f"in no line ({claim['line_id']}) until released")
    if wall_line and kind in (DECOR, EXPOSED, HELD_CEILING, VOID, DOME):
        raise CrossTradeError(f"HORIZONTAL_IN_WALL_LINE: {s['surface_id']} ({kind}) in wall line {claim['line_id']}")
    if wall_line and kind == BULKHEAD:
        raise CrossTradeError(f"BULKHEAD_IN_WALL_LINE: {s['surface_id']} (free beam edge) in wall line "
                              f"{claim['line_id']}; a beam face on the wall line is wall, a free edge is bulkhead")
    if role(ln) == "EXTERIOR":
        raise CrossTradeError(f"INTERIOR_IN_EXTERIOR_LINE: {s['surface_id']} ({kind}) in exterior soffit line "
                              f"{claim['line_id']}; an exterior soffit over outside air holds no interior face")
    if kind == STAIR_SOFFIT:
        if ceil_line:
            raise CrossTradeError(f"STAIR_SOFFIT_IN_CEILING: {s['surface_id']} in {claim['line_id']}; the flight's "
                                  f"underside is the stair finish")
        if wall_line:
            raise CrossTradeError(f"STAIR_SOFFIT_IN_WALL: {s['surface_id']} in wall line {claim['line_id']}")
    if kind in (VOID, DOME):
        raise CrossTradeError(f"VOID_FINISHED: {s['surface_id']} ({kind}) has no ceiling; booked in {claim['line_id']}")
    if kind == WALL and not wall_line:
        raise CrossTradeError(f"WALL_IN_CEILING_LINE: {s['surface_id']} in {claim['line_id']} ({code})")
    if lay not in ALLOWED[kind]:
        if kind == DECOR and lay == PLASTER:
            raise CrossTradeError(f"PLASTER_BEHIND_DECOR: {s['surface_id']} carries a gypsum ceiling; the slab soffit "
                                  f"behind it is not plastered unless a specification says so (HELD by name)")
        if kind == EXPOSED and lay == BOARD:
            raise CrossTradeError(f"BOARD_ON_EXPOSED: {s['surface_id']} is an exposed soffit; no gypsum board")
        raise CrossTradeError(f"LAYER_NOT_ON_SURFACE: {lay} on {s['surface_id']} ({kind})")
    return True


def overlaps(claims, surfaces):
    """rule 1 / 6: every (surface, layer) booked in more than one line, with its m2. Returns [] when none."""
    seen, out = {}, []
    for c in claims:
        k = (c["surface_id"], c["layer"])
        seen.setdefault(k, []).append(c["line_id"])
    for (sid, lay), lids in sorted(seen.items()):
        if len(lids) > 1:
            out.append({"surface_id": sid, "layer": lay, "lines": sorted(lids),
                        "m2": surfaces[sid].get("m2")})
    return out


def validate(claims, surfaces, lines):
    """every rule; refuses the first double count (LAYER_TWICE)."""
    for s in surfaces.values():
        check_surface(s)
    for c in claims:
        check_claim(c, surfaces, lines)
    ov = overlaps(claims, surfaces)
    if ov:
        o = ov[0]
        raise CrossTradeError(f"LAYER_TWICE: {o['surface_id']} {o['layer']} in {o['lines']} ({o['m2']} m2 counted "
                              f"twice)")
    return True


def wall_band(wall, decor_underside_m, band_top_m, declared_held=False):
    """rule 3 on one wall face {surface_id, length_m, top_m, m2}: returns {'band_m2': (lo, hi), 'gap_m2'} or refuses.
    decor_underside_m: the room's decor underside (Q-48 A); band_top_m: slab soffit (or beam bottom) above the face."""
    sid, top, L = wall["surface_id"], float(wall["top_m"]), float(wall["length_m"])
    if band_top_m + TOL_H < decor_underside_m:
        raise CrossTradeError(f"DECOR_ABOVE_SOFFIT: {sid} decor underside {decor_underside_m} above the soffit "
                              f"{band_top_m}")
    if top > decor_underside_m + TOL_H:
        if not declared_held:
            raise CrossTradeError(f"BAND_IN_WALL_LINE: {sid} finish top {top} above the decor underside "
                                  f"{decor_underside_m}: {round(L * (top - decor_underside_m), 4)} m2 of the hidden "
                                  f"band is booked as a wall face (declare it HELD apart, Q-52 C)")
    gap = round(max(0.0, decor_underside_m - top) * L, 4) if top < decor_underside_m - TOL_H else 0.0
    band_hi = round(L * max(0.0, band_top_m - decor_underside_m), 4)
    return {"surface_id": sid, "band_m2": (0.0, band_hi), "gap_m2": gap}


def cross_trade(room_id, surfaces, claims, lines, decor_underside_m=None, band_top_m=None):
    """rule 6 for one room: carried m2 per (kind, layer) from determinate surfaces, HELD by name, wall band ranges,
    gaps and the double count (m2 of every (surface, layer) booked twice; 0.0 when the rule holds)."""
    mine = {k: s for k, s in surfaces.items() if s.get("room_id") == room_id}
    cl = [c for c in claims if c["surface_id"] in mine]
    carried, held, bands, gaps = {}, [], [], 0.0
    for c in cl:
        s = mine[c["surface_id"]]
        k = f"{s['kind']} / {c['layer']} / {lines[c['line_id']]['item_code']}"
        carried[k] = round(carried.get(k, 0.0) + (s.get("m2") or 0.0), 6)
    for s in mine.values():
        if s.get("status") in HELD_ST:
            held.append({"surface_id": s["surface_id"], "kind": s["kind"], "plan_m2": s.get("m2"),
                         "held_item": s["held_item"]})
        if s["kind"] == WALL and decor_underside_m is not None and s.get("top_m") is not None:
            b = wall_band(s, decor_underside_m, band_top_m if band_top_m is not None else decor_underside_m,
                          declared_held=bool(s.get("band_held")))
            bands.append(b)
            gaps += b["gap_m2"]
    double = round(sum((o["m2"] or 0.0) * (len(o["lines"]) - 1) for o in overlaps(cl, surfaces)), 6)
    return {"room_id": room_id, "carried_m2": dict(sorted(carried.items())), "held": held,
            "band_m2": (0.0, round(sum(b["band_m2"][1] for b in bands), 4)), "gap_m2": round(gaps, 4),
            "double_count_m2": double}

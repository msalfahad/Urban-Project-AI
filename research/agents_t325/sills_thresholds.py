"""T-325: sills and thresholds as their own item (every villa). Research only: no engine quantity is changed.

Physical elements (ERS s.2.1), per opening, each measured once and owned by one line or NO_LINE:

- WINDOW (sill above the floor):
  * SILL_IN  the room-side sill surface between the room wall face and the frame (UP-REVEAL-001 'the sill surface is
    its own item'); depth = room face to frame line on the plan; a frame flush with the face = NONE (no surface).
  * SILL_OUT the external sill surface between the frame and the outer wall face (the T-313 OUT / SILL row).
  Each in m2 AND its front edge in m.l (the length a sill piece is ordered by); the piece count is 1 per side with a
  surface. Material: only a printed specification or an owner rule sets it; with neither, the quantity stands
  (DRAWING-CONFIRMED geometry) and the MATERIAL is UNKNOWN (never a default stone, never 'marble because thresholds
  are marble').
- FLOOR-LEVEL WINDOW (sill 0):
  * THRESHOLD_IN  room side: the strip is floor (UP-REVEAL-001 'floor-level glazing: the strip is the room's floor
    finish'): it belongs to the room floor line, never a threshold piece.
  * THRESHOLD_OUT outside: when an outdoor floor adjoins at the same level it is that floor's finish; when the face
    stands over outside air (no floor beyond), it is an EXTERNAL SILL AT FLOOR LEVEL (material UNKNOWN as above).
- DOOR: the THRESHOLD strip through the wall (clear width x wall thickness, one strip, UP-THR-001, OWNER_APPROVED):
  a doorway serving a wet room -> MARBLE threshold (URBAN-WET-SERVICE-MARBLE-THRESHOLD v1: the full clear width x the
  physical depth; its 20 mm rise is VERTICAL and never a plan depth); any other doorway -> the floor porcelain
  continued through the doorway, counted once; an external entrance is outside the marble rule (no marble without
  project evidence) and its finish stays as the candidate line states. A door has no sill.
  The FINISH CHANGE edge (m.l) is recorded where the floor finish changes at the opening (a marble threshold has two:
  wet side and dry side): it is geometry for the tile cut, NOT a BOQ item (no rule or specification makes a transition
  profile an item), so it carries no line.
- ARCH / doorless PASSAGE: the strip is floor (the floor continues, UP-THR-001 'other doorways'); no threshold piece.

Refused: a default sill / threshold depth (depth unknown -> UNRESOLVED, never typical and never 0); the 20 mm rise
taken as a horizontal depth; one opening's component in two lines (a threshold in its reveal line AND a threshold
line); two openings in one line; a component booked missing while a line of any family carries it; an unknown unit.
Units: every length in metres; `to_m` converts an explicit unit.
"""

from __future__ import annotations

import math

UNIT_TO_M = {"m": 1.0, "mm": 0.001, "cm": 0.01}
NO_LINE = "NO_LINE"
NOT_AN_ITEM = "NOT_AN_ITEM"
MARBLE_RISE_M = 0.020          # URBAN-WET-SERVICE-MARBLE-THRESHOLD v1 rise_mm 20: VERTICAL only
WET_TYPES = {"BATHROOM", "KITCHEN", "WASHING_LAUNDRY_ROOM", "IRONING_ROOM", "WC", "LAUNDRY"}


class LedgerError(ValueError):
    pass


def to_m(value, unit):
    if value is None:
        return None
    if unit not in UNIT_TO_M:
        raise LedgerError(f"unknown unit {unit!r}")
    return float(value) * UNIT_TO_M[unit]


def depth_from_plan(face_offset_m, frame_offset_m):
    """depth = perpendicular distance between a wall face and the frame line, both signed offsets across the wall
    (a mirror or rotation flips both signs and leaves the distance)."""
    if face_offset_m is None or frame_offset_m is None:
        return None
    return abs(float(face_offset_m) - float(frame_offset_m))


def _r(x):
    return None if x is None else round(x, 6)


def _len(op, key):
    v = op.get(key)
    if v is None:
        return None
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
        raise LedgerError(f"{op['id']}: {key} must be a non-negative length in metres, got {v!r}")
    return float(v)


def _guard(op):
    if op.get("default_depth") or op.get("typical_depth"):
        raise LedgerError(f"{op['id']}: a default / typical sill or threshold depth is refused (measure it or leave "
                          "it UNRESOLVED)")
    if op.get("depth_from_rise"):
        raise LedgerError(f"{op['id']}: the 20 mm marble rise is vertical; it is never a plan depth")


def _row(op, component, depth, width, *, state, element, material, material_source, unit_note="", edges=1):
    m2 = None if (depth is None or width is None) else _r(depth * width)
    ml = _r(width * edges) if (width is not None and state in ("MEASURED", "HELD")) else None
    if state == "NONE":
        m2, ml = 0.0, 0.0
    return {"opening": op["id"], "kind": op["kind"], "floor": op.get("floor"), "component": component,
            "physical_element": element, "depth_m": _r(depth), "width_m": _r(width), "m2": m2, "edge_ml": ml,
            "pcs": (0 if state == "NONE" else (1 if state == "MEASURED" else None)), "state": state,
            "material": material, "material_source": material_source, "note": unit_note,
            "line_id": NO_LINE, "binding": "UNBOUND"}


def _material_or_unknown(op, side):
    spec = (op.get("spec") or {}).get(side)
    if spec:
        return spec["material"], spec["source"]
    return "UNKNOWN", "no printed specification and no owner rule for this component"


def window_rows(op):
    """op: id, kind WINDOW | FLOOR_GLAZING, floor, width_m, depth_in_m, depth_out_m, outside ('FLOOR' | 'AIR' | None),
    outside_floor_line (line id of the adjoining outdoor floor, if any), room_floor_line, spec {side: {material,
    source}}. -> rows SILL_IN / SILL_OUT or THRESHOLD_IN / THRESHOLD_OUT."""
    _guard(op)
    w = _len(op, "width_m")
    din, dout = _len(op, "depth_in_m"), _len(op, "depth_out_m")
    rows = []
    if op["kind"] == "WINDOW":
        for comp, d, side, el in (("SILL_IN", din, "in", "internal sill surface (room face to frame)"),
                                  ("SILL_OUT", dout, "out", "external sill surface (frame to outer face)")):
            st = "UNRESOLVED" if (d is None or w is None) else ("NONE" if d == 0 else "MEASURED")
            mat, src = _material_or_unknown(op, side) if st == "MEASURED" else ("-", "no surface" if st == "NONE"
                                                                               else "geometry not established")
            rows.append(_row(op, comp, d, w, state=st, element=el, material=mat, material_source=src))
        return rows
    if op["kind"] != "FLOOR_GLAZING":
        raise LedgerError(f"{op['id']}: window_rows takes WINDOW or FLOOR_GLAZING, got {op['kind']!r}")
    st = "UNRESOLVED" if (din is None or w is None) else ("NONE" if din == 0 else "MEASURED")
    r = _row(op, "THRESHOLD_IN", din, w, state=st, element="room-side strip at floor level = room floor",
             material="the room's floor finish" if st == "MEASURED" else "-",
             material_source="UP-REVEAL-001 (floor-level glazing: the strip is floor)")
    r["binding"] = "ROOM_FLOOR" if st == "MEASURED" else "UNBOUND"
    rows.append(r)
    st = "UNRESOLVED" if (dout is None or w is None) else ("NONE" if dout == 0 else "MEASURED")
    outside = op.get("outside")
    if st == "MEASURED" and outside == "FLOOR":
        el, mat, src = ("outside strip at floor level = the adjoining outdoor floor", "the outdoor floor's finish",
                        "UP-REVEAL-001 + the outdoor floor line")
    elif st == "MEASURED" and outside == "AIR":
        el = "external sill at floor level (frame to outer face over outside air; no floor beyond)"
        mat, src = _material_or_unknown(op, "out")
    elif st == "MEASURED":
        el, mat, src = "outside strip at floor level", "UNKNOWN", "what adjoins outside is not established"
        st = "HELD"
    else:
        el, mat, src = "outside strip at floor level", "-", "no surface" if st == "NONE" else "geometry not established"
    rows.append(_row(op, "THRESHOLD_OUT", dout, w, state=st, element=el, material=mat, material_source=src))
    return rows


def door_rows(op):
    """op: id, kind DOOR | GATE | ARCH | PASSAGE, floor, clear_width_m, wall_t_m, sides [room types], external (bool).
    -> one THRESHOLD row (+ the finish-change edge record). A sill on a door is refused."""
    _guard(op)
    if op.get("sill"):
        raise LedgerError(f"{op['id']}: a door / passage has no sill (refused)")
    w, t = _len(op, "clear_width_m"), _len(op, "wall_t_m")
    sides = [s for s in (op.get("sides") or []) if s]
    wet = any(s in WET_TYPES for s in sides)
    st = "UNRESOLVED" if (w is None or t is None) else "MEASURED"
    if op["kind"] in ("ARCH", "PASSAGE"):
        el, mat, src = "floor strip through the opening (floor continues)", "the floor finish continued", \
            "UP-THR-001 (other doorways: floor continues, counted once)"
        change = 0
    elif op.get("external"):
        el, mat, src = "external entrance threshold strip", "HELD (exterior sill: by specification, none printed; marble rule not " \
            "applicable to external entrances)", "URBAN-WET-SERVICE-MARBLE-THRESHOLD v1 not_applicable_to"
        change = 1 if st == "MEASURED" else None
    elif wet:
        el, mat, src = "marble threshold (full clear width x physical depth; rise 0.020 m vertical)", "MARBLE", \
            "UP-THR-001 + URBAN-WET-SERVICE-MARBLE-THRESHOLD v1 (OWNER_APPROVED)"
        change = 2
    else:
        el, mat, src = "doorway strip: floor porcelain continued through the doorway", "FLOOR PORCELAIN", \
            "UP-THR-001 (dry doorway: once, as its own line)"
        change = 0
    r = _row(op, "THRESHOLD", t, w, state=st, element=el, material=mat, material_source=src)
    if st != "MEASURED":
        r["pcs"] = None
    edge = {"opening": op["id"], "kind": op["kind"], "floor": op.get("floor"), "component": "FINISH_CHANGE_EDGE",
            "physical_element": "where the floor finish changes at the opening (tile cut line)",
            "depth_m": None, "width_m": _r(w), "m2": None,
            "edge_ml": (None if (w is None or change is None) else _r(w * change)), "pcs": None,
            "state": st if change is not None else "UNRESOLVED", "material": "-",
            "material_source": "geometry only", "note": f"{change} edge(s)" if change is not None else "",
            "line_id": NOT_AN_ITEM, "binding": NOT_AN_ITEM}
    return [r, edge]


def ledger(openings):
    seen, rows = set(), []
    for op in openings:
        if op["id"] in seen:
            raise LedgerError(f"opening {op['id']} listed twice")
        seen.add(op["id"])
        rows += window_rows(op) if op["kind"] in ("WINDOW", "FLOOR_GLAZING") else door_rows(op)
    return rows


def bind(rows, binding):
    """binding: {(opening, component): line_id}. One component -> one line; one line -> one opening; a component
    already owned by the room floor or NOT_AN_ITEM is never bound to a line (it would be counted twice)."""
    owner = {}
    keyed = {(r["opening"], r["component"]): r for r in rows}
    for (op, comp), lid in binding.items():
        if (op, comp) not in keyed:
            raise LedgerError(f"binding names no ledger row: {op} {comp}")
        r = keyed[(op, comp)]
        if r["binding"] in ("ROOM_FLOOR", NOT_AN_ITEM):
            raise LedgerError(f"{op} {comp}: already carried by {r['binding']}; a second line would count it twice")
        if r["line_id"] != NO_LINE and r["line_id"] != lid:
            raise LedgerError(f"{op} {comp}: one component in two lines ({r['line_id']}, {lid})")
        if lid in owner and owner[lid] != op:
            raise LedgerError(f"line {lid} carries two openings ({owner[lid]}, {op})")
        owner[lid] = op
        r["line_id"], r["binding"] = lid, "BOUND"
    return rows


def refuse_double(rows, lines_by_opening):
    """lines_by_opening: {opening: [(family, line_id), ...]} from a search of EVERY family. A threshold that sits in
    its reveal line AND in a threshold / floor line is refused; returns the rows unchanged when none does."""
    thr = {"ARCH.THRESHOLD", "FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN"}
    for r in rows:
        if r["component"] not in ("THRESHOLD_OUT", "THRESHOLD_IN", "THRESHOLD") or r["binding"] != "BOUND":
            continue
        fams = {f for f, lid in lines_by_opening.get(r["opening"], ()) if lid != r["line_id"]}
        if r["component"] != "THRESHOLD" and fams & thr:
            raise LedgerError(f"{r['opening']}: threshold in its reveal line and in {sorted(fams & thr)}")
    return rows


def totals(rows):
    out = {}
    for r in rows:
        if r["component"] == "FINISH_CHANGE_EDGE":
            k = ("FINISH_CHANGE_EDGE", r["state"])
            a = out.setdefault(k, {"n": 0, "m2": 0.0, "edge_ml": 0.0})
            a["n"] += 1
            a["edge_ml"] += r["edge_ml"] or 0.0
            continue
        k = (f"{r['component']}|{r['material']}", r["state"])
        a = out.setdefault(k, {"n": 0, "m2": 0.0, "edge_ml": 0.0})
        a["n"] += 1
        if r["state"] == "MEASURED":            # HELD / UNRESOLVED never add a number (never 0 either)
            a["m2"] += r["m2"]
            a["edge_ml"] += r["edge_ml"]
    return {f"{k[0]}|{k[1]}": {"n": v["n"], "m2": round(v["m2"], 6), "edge_ml": round(v["edge_ml"], 6)}
            for k, v in sorted(out.items())}


def reconcile(value, parts, tol=1e-6):
    s = math.fsum(parts)
    if abs(s - value) > tol:
        raise LedgerError(f"residual {value - s:.6f} not named")
    return round(value - s, 6)

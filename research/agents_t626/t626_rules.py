"""R-T626-1 PER-ROOM / PER-FIELD MEMBRANE EVIDENCE (every villa; research rule, unwired; T-626).

Physical element: the waterproofing membrane LAID on the structural floor of each wet room (UP-WP-001 .. 005,
UP-WP-LAY-001) and on each roof / terrace field inside its parapet or wall faces (UP-WP-ROOF-001); its upturns are a
separate quantity (UP-WP-002 / UP-WP-UPTURN-015) and are not part of this rule's area. Physical laid area only: laps,
roll waste and procurement are separate quantities (never added here).

  1. WET BASIS. A room takes the wet-room membrane only on drawn wet evidence (a sanitary fixture or floor drain on
     the plan or the sanitary drawing, UP-WET-001 / 002) or on a named owner rule (e.g. Q-37 A pantry, Q-30 kitchen).
     A room LABEL alone is never wet evidence (a dry room called 'service' or a store next to a bath stays dry).
  2. OWN AREA. The laid area is the room outline to the drawn wall / column faces (a shower recess or any floor bay
     that belongs to the room is INSIDE the outline and adds), less every opening the membrane does not cross (a
     shaft, a column standing on the slab, a skylight / dome opening on a roof) that lies inside the outline. An
     opening that crosses the outline or lies outside it is refused (it would deduct what is not there).
     Roof fields are measured to the INNER parapet / wall faces; a circle opening is measured as a circle (its
     radius at full drawing precision), never as the engine's chord polygon.
  3. EVIDENCE PER ROW. Each statement row is judged by R-T621-1 (read only): ROOM, PIECE or READING, from own
     drawing measures with handles; a measure from the engine, the reference or a report is refused; DIFFERS beyond
     0.001 m2 is a finding, never absorbed.
  4. RESIDUAL SPLIT. When a READING row's own expression differs from its delta, the difference is split into named
     components (each with its own READING), and only the remainder stays UNRESOLVED; the parts re-add EXACTLY to the
     original delta. TOLERANCE is allowed only below 0.01 m2. HELD is never 0; a HELD row keeps its class (the drawing
     bound is evidence for the Lead, not a release).
"""
from __future__ import annotations

import math
from decimal import Decimal

D = Decimal
Z = D("0")
RULE_ID = "R-T626-1"
GOVERNING = ["UP-WP-001 .. 005", "UP-WP-LAY-001", "UP-WP-ROOF-001", "UP-WET-001 / 002", "Q-37 A", "Q-30", "Q-29",
             "Q-24", "Q-34 (top roof HELD)", "R-T621-1 (evidence statuses)", "R-T606-1 (outline geometry)",
             "ERS s.2 / s.3"]
Q6 = D("0.000001")
TOL_MAX = D("0.01")
OPENING_KINDS = ("SHAFT", "COLUMN", "SKYLIGHT", "VOID")


class RuleError(ValueError):
    pass


def q6(x) -> Decimal:
    return D(repr(float(x))).quantize(Q6) if isinstance(x, float) else D(str(x)).quantize(Q6)


def wet_basis(room: str, evidence: dict) -> str:
    """the basis that makes a room wet: 'FIXTURES: ...' or 'OWNER: ...'; refuses a label alone or nothing."""
    fx = [f for f in (evidence.get("fixtures") or []) if f]
    owner = evidence.get("owner_rule")
    if fx:
        return "FIXTURES: " + " + ".join(fx) + (f" ({evidence['fixture_source']})" if evidence.get("fixture_source") else "")
    if owner:
        return "OWNER: " + owner
    if evidence.get("label"):
        raise RuleError(f"{room}: a room label alone is not wet evidence (R-T626-1 (1))")
    raise RuleError(f"{room}: no wet evidence: the room stays dry (no membrane)")


def _poly(p):
    from shapely.geometry import Polygon
    return Polygon(p)


def circle(c, r, n=4096):
    """a circle opening as a polygon of n sides (shapely); its exact area is pi r^2 (see membrane_area)."""
    return [(c[0] + r * math.cos(2 * math.pi * i / n), c[1] + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def membrane_area(outline, bays=(), openings=()) -> dict:
    """laid membrane area (m2, metres in) of one wet-room floor or one roof field.

    outline: polygon points to the drawn faces; bays: polygons that belong to the room (shower recess) and touch it;
    openings: [{'kind': SHAFT / COLUMN / SKYLIGHT / VOID, 'poly': points} | {'kind': ..., 'circle': (c, r)}]."""
    from shapely.ops import unary_union
    room = _poly(outline)
    if not room.is_valid or room.area <= 0:
        raise RuleError("the outline is not a simple polygon")
    for b in bays:
        bp = _poly(b)
        if bp.intersection(room).area > 1e-9:
            raise RuleError("a bay overlaps the room: it would be counted twice")
        if bp.distance(room) > 1e-9:
            raise RuleError("a bay that does not touch the room is not part of it")
        # close the CAD-noise sliver along the shared edge (rotated drawings): +/- 1e-9 m mitre buffer, area effect
        # below 1e-8 m2
        room = unary_union([room, bp]).buffer(1e-9, join_style=2).buffer(-1e-9, join_style=2)
    if room.geom_type != "Polygon":
        raise RuleError("the room with its bays is not one polygon")
    gross = D(repr(room.area))
    ded, rows = Z, []
    for o in openings:
        k = o.get("kind")
        if k not in OPENING_KINDS:
            raise RuleError(f"opening kind {k!r} unknown")
        if "circle" in o:
            (cx, cy), r = o["circle"]
            if r <= 0:
                raise RuleError("a circle opening needs a positive radius")
            shape = _poly(circle((cx, cy), r))
            exact = D(repr(math.pi * r * r))
        else:
            shape = _poly(o["poly"])
            exact = D(repr(shape.area))
        if not room.buffer(1e-9).contains(shape):
            raise RuleError(f"{k} opening is not inside the outline: never deduct what is not there")
        ded += exact
        rows.append({"kind": k, "area": str(q6(exact))})
    net = gross - ded
    if net <= 0:
        raise RuleError("the openings take the whole field")
    return {"gross": str(q6(gross)), "deducted": str(q6(ded)), "net": str(q6(net)), "openings": rows}


def split_residual(delta, parts: list[dict]) -> list[dict]:
    """split a residual row's delta into named parts (each {'name', 'qty' (signed), 'class', 'evidence'}); the
    remainder is ONE UNRESOLVED part; the parts re-add exactly to delta."""
    out, acc = [], Z
    for p in parts:
        q = D(str(p["qty"]))
        if p.get("class") == "TOLERANCE" and q.copy_abs() >= TOL_MAX:
            raise RuleError(f"TOLERANCE {q} >= {TOL_MAX}: name the cause")
        if p.get("class") in ("UNRESOLVED", None):
            raise RuleError("a named part has a class other than UNRESOLVED (the remainder is the only UNRESOLVED)")
        if not p.get("evidence"):
            raise RuleError(f"part {p.get('name')!r} has no drawing evidence")
        acc += q
        out.append(dict(p, qty=str(q)))
    rem = D(str(delta)) - acc
    if rem:
        out.append({"name": "RESIDUAL (remainder)", "qty": str(rem), "class": "UNRESOLVED", "evidence": "none: "
                    "the reference row has no sub-rows"})
    assert sum((D(p["qty"]) for p in out), Z) == D(str(delta))
    return out

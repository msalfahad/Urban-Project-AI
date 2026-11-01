"""STAIR_ROOM_HELD_FACES_V1 (T-447, research; any villa): settle the skirting faces a stair-room face table left HELD
(guard bands, doorless-opening reveal jambs, open sides of a floor part) from the drawings' own evidence, and trace a
freelancer's gross-outline length to named constructions. Stdlib only; nothing here is wired into a method.

Rules (R-T447-1 .. 5, proposed, research):
  R-T447-1  GUARD EDGE. A floor part's edge along a stair divider / well band is a skirting FACE only when a drawing
            shows a solid vertical surface down to the floor (a wall cut on the wall layer, or an upstand drawn solid in
            a section). When a section draws the band as a BALUSTRADE (posts and rails, with the flight behind visible
            between the floor and the lowest rail), the edge is NOT_APPLICABLE (no skirting along a guard / void edge:
            UP-SKIRT-001 wall and column faces only; defect B12). With neither shown it stays GUARD_HELD (blank, never 0).
  R-T447-2  DOORLESS JAMB. A doorless opening's jamb return is skirted only when ALL five conditions of the owner rule
            URBAN-SKIRTING-OPENING-METHOD v1 (DOORLESS_OPENING) hold: no door, a real vertical jamb, a skirting-eligible
            side, the room's floor finish reaches the jamb, and the opening is not part of a full-wall-tile room. One
            condition shown FALSE -> NOT_APPLICABLE (with the condition and its evidence); one UNKNOWN and none FALSE ->
            HELD; all TRUE -> INCLUDED (PROVISIONAL, as the method says).
  R-T447-3  FLOOR BEYOND A LEVEL MARK. A strip between floor parts with no drawn element (no wall, guard, nosing or
            step line on any visible layer) and a level mark whose point lies inside it is floor at that level; so is a
            strip with no closed outline at the cut (single lines, hidden overhead outlines only) where a section shows
            the floor flat; otherwise HELD. Hidden (overhead) outlines never make a strip SOLID at floor level. An open side then has no face; the faces of
            the strip's own walls join the floor part.
  R-T447-4  OUTLINE TRACE. A freelancer's gross skirting length is reconciled by rectilinear constructions built from
            drawn lines only (never fitted); a construction is accepted only when it reproduces his figure within
            0.005 m, and each added stretch is classed (ROOM FACE / STAIR SIDE owned elsewhere / GUARD no face).
  R-T447-5  Held stays blank with its cause; NOT_APPLICABLE carries its evidence; a lm is never reported for a guard
            edge or a jamb that fails the owner rule; no settled face may share wall line, plan interval and level with
            a stair side stretch (R-T441-2 reused) or with another listed face (own overlap test).
"""
from __future__ import annotations

METHOD = "STAIR_ROOM_HELD_FACES_V1"
RULES = ("R-T447-1", "R-T447-2", "R-T447-3", "R-T447-4", "R-T447-5")
TOL = 1e-6
MAX_M = 50.0

FACE = "FACE"                       # DRAWING-CONFIRMED skirting face, lm counted
NOT_APPLICABLE = "NOT_APPLICABLE"   # no skirting by owner rule, with evidence
NO_FACE = "NO_FACE"                 # open side, nothing to skirt
HELD = "HELD"
UNKNOWN = "UNKNOWN"
INCLUDED_PROVISIONAL = "INCLUDED_PROVISIONAL"
STATUSES = (FACE, NOT_APPLICABLE, NO_FACE, HELD, UNKNOWN, INCLUDED_PROVISIONAL)

JAMB_CONDITIONS = ("no_door", "real_jamb", "eligible_side", "floor_finish_reaches_jamb", "not_full_wall_tile_room")


class Refused(ValueError):
    pass


def _r(x):
    return round(x + 0.0, 6)


def _len_ok(L, what):
    if L is None:
        return
    if not (0 < L <= MAX_M):
        raise Refused(f"{what}: length {L} m outside (0, {MAX_M}] (unit slip?)")


# ------------------------------------------------------------------------------------------------ R-T447-1 guard edge
def guard_edge(edge):
    """edge: {id, length, evidence: {wall_cut: bool|None, section_solid_to_floor: bool|None,
    section_balustrade_open_below_rail: bool|None}, refs: [...]} -> resolved record."""
    _len_ok(edge["length"], edge["id"])
    ev = edge.get("evidence", {})
    refs = edge.get("refs") or []
    solid = ev.get("wall_cut") is True or ev.get("section_solid_to_floor") is True
    open_ = ev.get("section_balustrade_open_below_rail") is True
    if solid and open_:
        raise Refused(f"{edge['id']}: evidence says both solid to the floor and open below the rail")
    if solid:
        if not refs:
            raise Refused(f"{edge['id']}: FACE without a drawing reference")
        return {"id": edge["id"], "status": FACE, "lm": _r(edge["length"]), "refs": refs,
                "cause": "solid vertical surface to the floor"}
    if open_:
        if not refs:
            raise Refused(f"{edge['id']}: NOT_APPLICABLE without a drawing reference (R-T447-5)")
        return {"id": edge["id"], "status": NOT_APPLICABLE, "lm": None, "refs": refs,
                "cause": "balustrade: posts and rails, flight visible below the lowest rail; no skirting on a guard "
                         "edge (UP-SKIRT-001, B12)"}
    return {"id": edge["id"], "status": HELD, "lm": None, "refs": refs, "candidate_lm": _r(edge["length"]),
            "cause": "guard band: wall, upstand or balustrade not established (GUARD_HELD)"}


def check_guard(record):
    """refuse a guard edge reported with skirting lm while its evidence is a balustrade, or a held edge as 0."""
    if record["status"] == NOT_APPLICABLE and record.get("lm"):
        raise Refused(f"{record['id']}: balustrade edge skirted as a wall face (R-T447-1)")
    if record["status"] in (HELD, UNKNOWN) and record.get("lm") == 0:
        raise Refused(f"{record['id']}: held carried as 0 (blank, never 0)")
    return True


# ------------------------------------------------------------------------------------------------ R-T447-2 jambs
def doorless_jambs(op):
    """op: {opening_id, jambs: [depth, ...], conditions: {name: True|False|None}, evidence: {name: text}}."""
    if not op.get("opening_id"):
        raise Refused("jamb without an opening id")
    for d in op["jambs"]:
        if not (0 < d <= 1.0):
            raise Refused(f"{op['opening_id']}: jamb depth {d} m outside (0, 1] (unit slip?)")
    cond = op.get("conditions", {})
    missing = [c for c in JAMB_CONDITIONS if c not in cond]
    if missing:
        raise Refused(f"{op['opening_id']}: conditions not stated: {missing}")
    ev = op.get("evidence", {})
    false = [c for c in JAMB_CONDITIONS if cond[c] is False]
    unknown = [c for c in JAMB_CONDITIONS if cond[c] is None]
    for c in false:
        if not ev.get(c):
            raise Refused(f"{op['opening_id']}: condition {c} FALSE without evidence")
    total = _r(sum(op["jambs"]))
    if false:
        return {"opening_id": op["opening_id"], "status": NOT_APPLICABLE, "lm": None, "failed": false,
                "candidate_lm": total, "cause": "; ".join(f"{c}: {ev[c]}" for c in false)}
    if unknown:
        return {"opening_id": op["opening_id"], "status": HELD, "lm": None, "unknown": unknown, "candidate_lm": total,
                "cause": "owner-rule condition(s) not established: " + ", ".join(unknown)}
    return {"opening_id": op["opening_id"], "status": INCLUDED_PROVISIONAL, "lm": total,
            "cause": "URBAN-SKIRTING-OPENING-METHOD v1 DOORLESS_OPENING: all five conditions hold"}


# ------------------------------------------------------------------------------------------------ R-T447-3 strips
def strip_class(strip):
    """strip: {id, w, d, visible_elements: [{handle, closed_outline, layer_class}], level_mark_inside:
    level|None, section_flat: bool, step_line: bool, adjacent_level: level} -> FLOOR / SOLID / HELD with m2."""
    for v in (strip["w"], strip["d"]):
        _len_ok(v, strip["id"])
    area = _r(strip["w"] * strip["d"])
    vis = strip.get("visible_elements") or []
    solid = [v for v in vis if v.get("closed_outline") or v.get("layer_class") == "WALL"]
    if solid:
        return {"id": strip["id"], "class": "SOLID", "m2": area, "cause": "drawn element " + solid[0]["handle"]}
    mark = strip.get("level_mark_inside")
    if mark is not None:
        return {"id": strip["id"], "class": "FLOOR", "level": mark, "m2": area,
                "cause": "level mark point inside the strip, no wall / guard / step drawn (R-T447-3)"}
    if strip.get("section_flat") and strip.get("adjacent_level") is not None and not strip.get("step_line"):
        return {"id": strip["id"], "class": "FLOOR", "level": strip["adjacent_level"], "m2": area,
                "cause": "no closed outline or wall drawn at the cut (only single lines and hidden overhead outlines), "
                         "no step line, and a section shows the floor flat: floor at the adjacent level"}
    return {"id": strip["id"], "class": HELD, "m2": None, "candidate_m2": area,
            "cause": "nothing settles floor or solid"}


# ------------------------------------------------------------------------------------------------ R-T447-4 trace
def histogram_perimeter(cols):
    """perimeter of a rectilinear outline made of columns [(x0, x1, height)] standing on y = 0, contiguous in x."""
    cols = sorted(cols)
    for (a0, a1, _), (b0, _b1, _h) in zip(cols, cols[1:]):
        if abs(a1 - b0) > TOL:
            raise Refused(f"columns not contiguous at {a1} / {b0}")
    for c in cols:
        _len_ok(c[1] - c[0], "column width")
        _len_ok(c[2], "column height")
    width = cols[-1][1] - cols[0][0]
    per = 2 * width + cols[0][2] + cols[-1][2]
    for (_, _, h1), (_, _, h2) in zip(cols, cols[1:]):
        per += abs(h1 - h2)
    return _r(per)


def histogram_area(cols):
    return _r(sum((c[1] - c[0]) * c[2] for c in cols))


def trace(target_lm, constructions, tol=0.005):
    """constructions: {name: cols}; returns the ones reproducing target_lm within tol (never fitted)."""
    out = []
    for name, cols in constructions.items():
        p = histogram_perimeter(cols)
        out.append({"construction": name, "perimeter_m": p, "area_m2": histogram_area(cols),
                    "matches": abs(p - target_lm) <= tol})
    return out


def classify_added(stretches):
    """stretches added by an accepted construction: each {id, lm, cls in ROOM_FACE / STAIR_SIDE / GUARD}."""
    allowed = ("ROOM_FACE", "STAIR_SIDE", "GUARD")      # ordered: the summary must be byte-stable
    tot = {k: 0.0 for k in allowed}
    for s in stretches:
        if s["cls"] not in allowed:
            raise Refused(f"{s['id']}: class {s['cls']} not in {sorted(allowed)}")
        if s["cls"] == "STAIR_SIDE" and not s.get("owner"):
            raise Refused(f"{s['id']}: stair-side stretch without its owning stair stretch")
        _len_ok(s["lm"], s["id"])
        tot[s["cls"]] += s["lm"]
    return {k: _r(v) for k, v in tot.items()}


# ------------------------------------------------------------------------------------------------ R-T447-5 overlap
def face_overlaps(faces, others):
    """faces / others: [{id, line, t0, t1, level}] -> overlapping pairs (same wall line, same level, plan overlap)."""
    out = []
    for f in faces:
        for o in others:
            if f["line"] != o["line"]:
                continue
            lo, hi = o.get("lo", o.get("level")), o.get("hi", o.get("level"))
            if not (lo - TOL <= f["level"] <= hi + TOL):
                continue
            ov = min(max(f["t0"], f["t1"]), max(o["t0"], o["t1"])) - max(min(f["t0"], f["t1"]), min(o["t0"], o["t1"]))
            if ov > TOL:
                out.append({"face": f["id"], "other": o["id"], "overlap_m": _r(ov)})
    return out


def settle(table, others=()):
    """table: list of resolved records (guard / jamb / face rows with 'kind'); returns totals; refuses overlaps."""
    faces = [r for r in table if r["status"] == FACE]
    for r in table:
        if r.get("kind") == "GUARD":
            check_guard(r)
        if r["status"] not in STATUSES:
            raise Refused(f"{r.get('id')}: unknown status {r['status']}")
        if r["status"] in (HELD, UNKNOWN) and r.get("lm") is not None:
            raise Refused(f"{r.get('id')}: held row carries a lm")
        if r["status"] == NOT_APPLICABLE and not (r.get("refs") or r.get("cause")):
            raise Refused(f"{r.get('id')}: NOT_APPLICABLE without evidence")
    geo = [r for r in faces if "line" in r]
    ov = face_overlaps(geo, list(others))
    ov += [p for p in face_overlaps(geo, geo) if p["face"] < p["other"]]
    if ov:
        raise Refused(f"face shared with another owner: {ov} (R-T447-5)")
    return {"confirmed_lm": _r(sum(r["lm"] for r in faces)),
            "not_applicable": sum(1 for r in table if r["status"] == NOT_APPLICABLE),
            "held": [r["id"] for r in table if r["status"] in (HELD, UNKNOWN)]}

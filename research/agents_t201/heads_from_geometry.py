"""T-201: opening heads and sills from DRAWN geometry when no sheet prints them (any villa; not wired, no engine file).

The physical element: an opening's head and sill are vertical distances from a datum. Where no chain prints them, an
elevation or a section may still DRAW the opening (CAD geometry, 1:1 model units). This module turns drawn geometry
into a head / sill only when every step is evidenced, and otherwise holds it:

1. DATUM: a level of the SAME view (a level-marker tick or a dimension-chain tick with its printed level) fixes the
   drawing y of a known level; units are declared ('mm' or 'm'); a missing datum is refused (never the drawing origin,
   never the ground line by assumption).
2. BINDING: drawn rectangles are bound to plan openings by along-facade position. The offset between the plan
   positions and the drawn centres is solved from the data, the spacing must agree within tol for every bound pair,
   the drawn width must agree with the plan jamb-to-jamb width within tol (otherwise the drawn outline is NOT the
   opening: e.g. shutters hide the reveal edges -> HELD with the drawn candidates), mirroring only when declared, and an
   ambiguous solution (two offsets fit equally) binds nothing.
3. RE-DATUM (T-198 lesson): absolute levels first, then height above the finished floor of the floor the opening
   sits on; an unknown FFL holds only the above-FFL value, never the opening height (head - sill).
4. CURRENT ISSUE: when the geometry comes from an earlier issue than the current set, every edge is checked against
   the current issue (an overlay residual per edge); any edge beyond tol -> DIFFERS -> HELD. A check that was not
   made leaves the value DRAWING-CONFIRMED BY GEOMETRY with 'current issue NOT CHECKED' (never silently agreed).
5. A section cut gives the head at the cut only; a run whose count / pier is unsettled stays HELD on its width.

Statuses follow WORKFLOW_CONTROLS s.5; a drawn value is never VERIFIED here (the Checker re-measures).
"""
from __future__ import annotations

DC_GEOM = "DRAWING-CONFIRMED"
HELD = "HELD"
UNKNOWN = "UNKNOWN"

UNIT = {"mm": 0.001, "m": 1.0}


class GeometryError(ValueError):
    pass


def _u(units):
    if units not in UNIT:
        raise GeometryError(f"units must be one of {sorted(UNIT)}, got {units!r}")
    return UNIT[units]


def datum(y_drawn, level_m, units, source):
    """A datum = (drawing y of a known level, that level in m, units, source). Every argument is required."""
    if y_drawn is None or level_m is None or not source:
        raise GeometryError("a datum needs the drawn y, its printed level and a source (no default datum)")
    _u(units)
    if abs(level_m) > 100:
        raise GeometryError(f"level {level_m} m is not a building level (units mix-up?)")
    return {"y": float(y_drawn), "level_m": float(level_m), "units": units, "source": source}


def level_of(y_drawn, dat):
    return round(dat["level_m"] + (y_drawn - dat["y"]) * _u(dat["units"]), 6)


def bind(plan, drawn, tol_m=0.02, mirrored=False, units="mm"):
    """plan: [(id, pos_m centre along the facade, width_m)]; drawn: [(key, x0, x1)] in drawing units.
    Returns {'bound': {id: key}, 'offset_m', 'width_check': {id: (plan_w, drawn_w, ok)}, 'status', 'why'}.
    The offset is solved from the data: every plan / drawn pairing proposes one, the one under which the most
    openings bind within tol wins; a tie between two different offsets is AMBIGUOUS (nothing bound)."""
    k = _u(units)
    if not plan or not drawn:
        return {"bound": {}, "offset_m": None, "width_check": {}, "status": UNKNOWN, "why": "nothing to bind"}
    sgn = -1.0 if mirrored else 1.0
    dc = [(key, sgn * (x0 + x1) / 2 * k, abs(x1 - x0) * k) for key, x0, x1 in drawn]
    cands = {}
    for _, p, _w in plan:
        for _, c, _ in dc:
            off = round(c - p, 3)
            cands.setdefault(off, 0)
    scored = []
    for off in cands:
        b = {}
        used = set()
        for pid, p, pw in plan:
            best = None
            for key, c, w in dc:
                if key in used:
                    continue
                if abs(c - p - off) <= tol_m:
                    best = (key, w) if best is None else best
            if best:
                b[pid] = best
                used.add(best[0])
        scored.append((len(b), off, b))
    scored.sort(key=lambda s: -s[0])
    top = scored[0]
    rivals = [s for s in scored[1:] if s[0] == top[0] and abs(s[1] - top[1]) > tol_m]
    if rivals and top[0] > 0:
        return {"bound": {}, "offset_m": None, "width_check": {}, "status": "AMBIGUOUS",
                "why": f"{len(rivals) + 1} offsets bind {top[0]} openings each"}
    wc = {}
    for pid, p, pw in plan:
        if pid in top[2]:
            w = top[2][pid][1]
            wc[pid] = (pw, round(w, 4), abs(w - pw) <= tol_m)
    return {"bound": {pid: v[0] for pid, v in top[2].items()}, "offset_m": top[1], "width_check": wc,
            "status": "BOUND" if top[0] else UNKNOWN, "why": ""}


def head_record(oid, width_m, y_sill, y_head, dat, ffl_m=None, width_ok=True, current_issue=None, tol_m=0.02,
                cut_only=False, count_held=None, candidates=None):
    """One opening's head / sill from drawn edges. y_* in drawing units on the view of `dat`.
    current_issue: None (not checked) or a list of edge residuals in metres against the current issue."""
    if y_sill is None or y_head is None:
        return {"id": oid, "status": HELD, "height_m": None, "sill_level_m": None,
                "head_level_m": None, "why": "the opening exists on the plan but no sheet draws its head" if not candidates else
                "drawn edges are not the opening's (basis not decidable): candidates only",
                "candidates": candidates or []}
    # levels to the centimetre: the printed levels of a set are to the cm, and a DWF plot carries about 2 mm per unit
    s, h = round(level_of(y_sill, dat), 2), round(level_of(y_head, dat), 2)
    if h <= s:
        raise GeometryError(f"{oid}: head {h} not above sill {s}")
    rec = {"id": oid, "sill_level_m": s, "head_level_m": h, "height_m": round(h - s, 3),
           "ffl_m": ffl_m, "sill_above_ffl_m": None, "head_above_ffl_m": None, "status": DC_GEOM, "why": "",
           "issue_check": "NOT CHECKED", "candidates": candidates or []}
    if ffl_m is not None:
        rec["sill_above_ffl_m"] = round(s - ffl_m, 3)
        rec["head_above_ffl_m"] = round(h - ffl_m, 3)
        if rec["sill_above_ffl_m"] < -tol_m:
            raise GeometryError(f"{oid}: sill below its finished floor ({rec['sill_above_ffl_m']} m): wrong datum or floor")
    if not width_ok:
        rec.update(status=HELD, why="drawn outline width differs from the plan jamb-to-jamb width: the drawn edges "
                                    "are not the opening's (e.g. shutters / frame); candidates only")
        return rec
    if current_issue is not None:
        worst = max(abs(r) for r in current_issue) if current_issue else 0.0
        rec["issue_check"] = f"AGREES (max edge offset {worst:.3f} m)" if worst <= tol_m else \
            f"DIFFERS (edge offset {worst:.3f} m > {tol_m} m)"
        if worst > tol_m:
            rec.update(status=HELD, why="the current issue draws the opening differently")
            return rec
    if count_held:
        rec.update(status=HELD, why=f"height drawn at the cut; width / count held: {count_held}")
    elif cut_only:
        rec["why"] = "head read at a section cut through the opening"
    return rec


def area(rec, width_m):
    """Opening area w x (head - sill) only when the record is established; HELD / UNKNOWN never become 0."""
    if rec.get("status") != DC_GEOM or rec.get("height_m") is None or width_m is None:
        return None
    return round(width_m * rec["height_m"], 4)

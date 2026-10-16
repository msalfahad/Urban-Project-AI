"""DOOR FEASIBILITY (M9 Phase 2B-2, ARCH_TAKEOFF_V2.4 only) - for every door: what the drawing shows, what Urban
requires, where they differ and whether the required wall opening can physically fit (registry 1.1.0 UP-DOOR-FEAS-001,
UP-DOOR-OPEN-002, UP-DOOR-HGT-001, UP-DOOR-DEP-001; values through the project rules, UP-RULES-001).

    floor_context(S, ents, roles, unit_m, rooms, floor, walls=None)  -> the plan geometry one floor's doors are read in
    clearances(o, ctx)          -> along the host wall, beyond each jamb: the plain wall on both faces, then the first
                                   constraint (COLUMN, OPENING, CORNER, JUNCTION, WALL_END, OPEN_RUN) and its distance
    swing(el, ctx, leaf_m, ...) -> the sector the (larger) leaf sweeps, against walls, columns and drawn fixtures
    classify(...)               -> STANDARD_FITS_AS_DRAWN | ENLARGEMENT_GEOMETRICALLY_POSSIBLE | ENLARGEMENT_CONSTRAINED |
                                   ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW | INSUFFICIENT_DRAWING_EVIDENCE
    feasibility(model, contexts, resolver, facts) -> per door row, the four views (AS_DRAWN / OWNER_STANDARD /
                                   PROPOSED_MODIFICATION / UNRESOLVED, elevators EXCLUDED), the approvals required
    jamb_plaster_lines(ctx, lines, model, resolver, facts, line) -> the door jamb / head plaster lines at the height of
                                   each door's category (UP-DOOR-HGT-001: main entrance 2.50 m)

Geometric clearance is never a structural approval; a column, beam or structural wall is never cut by recommendation;
a proposed modification never reaches the as-drawn quantities. Nothing here changes a drawn dimension.
Project-agnostic; stdlib only."""

from __future__ import annotations

import math

from engine.source import door_standards as DSTD
from engine.source import knowledge as K

POLICY_ID = "DOOR_FEASIBILITY_V1"
ENGINE_PIER_M = 0.10                     # ENGINE_REVIEW_THRESHOLD (project_rules.ENGINE_PIER_M), not an owner standard
TOL_M = 0.001
REACH_M = 3.0
FACE_TOL_M = 0.01
CORNER_SPAN_M = 0.45
SAMPLE_M = 0.02
SYMBOL_TOL_M = 0.15                                             # the closed leaf's end within the jambs (+/- 0.15 m)
PROBE_M = 0.25
CLASSES = ("STANDARD_FITS_AS_DRAWN", "ENLARGEMENT_GEOMETRICALLY_POSSIBLE", "ENLARGEMENT_CONSTRAINED",
           "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW", "INSUFFICIENT_DRAWING_EVIDENCE")
ORDINARY = (DSTD.INTERNAL, DSTD.BATH, DSTD.EXTERNAL)
FIXTURE_RE = ("WC", "TOILET", "BASIN", "SINK", "SHOWER", "TUB", "VANITY", "WASH", "COOKER", "FRIDGE", "WARDROBE",
              "CABINET", "COUNTER")


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _inside(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def floor_context(S, ents, roles, unit_m, rooms, floor, walls=None):
    wall_l = {k for k, v in roles.items() if v == "WALL"}
    col_l = {k for k, v in roles.items() if v == "COLUMN"}
    return {"floor": floor, "unit_m": unit_m, "S": S,
            "wall_segs": [s for s in ents.get("segments") or () if s["layer"] in wall_l],
            "columns": list(S.get("column_boxes") or ()),
            "frame_drawn": bool(S.get("column_boxes")) or any(s["layer"] in col_l for s in ents.get("segments") or ()),
            "openings": list(S.get("openings") or ()), "faces": S.get("faces") or [], "rooms": rooms,
            "inserts": ents.get("inserts") or [], "swings": S.get("doors") or {},
            "walls": (walls or {}).get("walls") or []}


def _union(iv, tol):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1] + tol:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def clearances(o, ctx):
    """beyond each jamb of band opening o (drawing frame u, n, s0, s1, o0, o1): -> {"START": side, "END": side}, a
    side = {"plain_m", "constraint", "constraint_id", "faces_m": [face o0, face o1], "beyond": spaces}."""
    um = ctx["unit_m"]
    u, n = tuple(o["u"]), tuple(o["n"])
    lo, hi = sorted((o["o0"], o["o1"]))
    ftol, reach = FACE_TOL_M / um, REACH_M / um
    faces = {lo: [], hi: []}
    crosses = []
    for s in ctx["wall_segs"]:
        a, b = s["a"], s["b"]
        d = (b[0] - a[0], b[1] - a[1])
        L = math.hypot(*d)
        if L <= 0:
            continue
        sa, sb, na, nb = _dot(a, u), _dot(b, u), _dot(a, n), _dot(b, n)
        if abs(_cross(u, (d[0] / L, d[1] / L))) <= 1e-3:
            for off in (lo, hi):
                if abs(na - off) <= ftol and abs(nb - off) <= ftol:
                    faces[off].append((min(sa, sb), max(sa, sb)))
            continue
        if abs(nb - na) > 1e-12:
            n0, n1 = sorted((na, nb))
            if n1 >= lo - ftol and n0 <= hi + ftol:          # the segment crosses into the wall strip
                t = (0.5 * (lo + hi) - na) / (nb - na)
                if 0.0 <= t <= 1.0:
                    crosses.append((sa + (sb - sa) * t, s["id"]))
    cov = {off: _union(iv, 1e-3 / um) for off, iv in faces.items()}
    out = {}
    for side, sj, sg in (("START", o["s0"], -1), ("END", o["s1"], 1)):
        probe = sj + sg * 2 * ftol
        reachf = []
        for off in (lo, hi):
            iv = next((x for x in cov[off] if x[0] - ftol <= probe <= x[1] + ftol), None)
            reachf.append(0.0 if iv is None else max(0.0, (iv[1] - sj) if sg > 0 else (sj - iv[0])))
        events = []
        for x0, y0, x1, y1 in ctx["columns"]:
            cs = [_dot(p, u) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            cn = [_dot(p, n) for p in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
            if max(cn) < lo - ftol or min(cn) > hi + ftol:
                continue
            near = min(cs) - sj if sg > 0 else sj - max(cs)
            if near >= -ftol and near <= reach:
                events.append((max(0.0, near), "COLUMN", f"column at {min(cs) * um:.2f} m"))
        for p in ctx["openings"]:
            if p["opening_id"] == o["opening_id"] or abs(_cross(u, tuple(p["u"]))) > 1e-3:
                continue
            sn = _dot(tuple(p["n"]), n)                         # the other opening's own frame may be reversed
            plo, phi = sorted((p["o0"] * sn, p["o1"] * sn))
            if phi < lo - ftol or plo > hi + ftol:
                continue
            q = sorted((p["s0"] * _dot(tuple(p["u"]), u), p["s1"] * _dot(tuple(p["u"]), u)))
            near = q[0] - sj if sg > 0 else sj - q[1]
            if near >= -ftol and near <= reach:
                events.append((max(0.0, near), "OPENING", f"{p['kind']} {p['opening_id']}"))
        for sc, sid in crosses:
            near = sc - sj if sg > 0 else sj - sc
            if 2 * ftol < near <= reach:
                events.append((near, "CROSSING", sid))
        dmin, dmax = min(reachf), max(reachf)
        s_end = sj + sg * dmin
        touch = [_touches(ctx["wall_segs"], (u[0] * s_end + n[0] * off, u[1] * s_end + n[1] * off), u, 2 * ftol)
                 for off in (lo, hi)]
        if dmax - dmin <= 2 * ftol:
            face_kind = "JUNCTION" if all(touch) else "CORNER" if any(touch) else "WALL_END"
            what = {"JUNCTION": "a crossing wall", "CORNER": "a wall corner", "WALL_END": "a free wall end"}[face_kind]
        elif dmax - dmin <= CORNER_SPAN_M / um:
            face_kind, what = "CORNER", "a wall corner"
        else:
            face_kind = "JUNCTION"
            what = f"a wall joining on the {'o0' if reachf[0] <= reachf[1] else 'o1'} face"
        face_ev = (dmin, face_kind, f"{what} at {dmin * um:.2f} m")
        cand = [e for e in events if e[1] != "CROSSING"] + ([face_ev] if dmin < reach else [])
        cross_at = [e for e in events if e[1] == "CROSSING"]
        if cross_at and (not cand or min(cross_at)[0] < min(cand)[0] - 2 * ftol):
            cand.append((min(cross_at)[0], "JUNCTION", f"crossing wall line {min(cross_at)[2]}"))
        if not cand:
            out[side] = {"plain_m": round(reach * um, 6), "constraint": "OPEN_RUN", "constraint_id": None,
                         "faces_m": [round(x * um, 6) for x in reachf]}
            continue
        d, kind, cid = min(cand, key=lambda e: (e[0], ("COLUMN", "OPENING", "JUNCTION", "CORNER",
                                                     "WALL_END").index(e[1])))
        out[side] = {"plain_m": round(d * um, 6), "constraint": kind, "constraint_id": cid,
                     "faces_m": [round(x * um, 6) for x in reachf]}
    return out


def _touches(segs, p, u, tol):
    """a wall segment that is not parallel to u and ends at (or passes through) point p."""
    for s in segs:
        a, b = s["a"], s["b"]
        d = (b[0] - a[0], b[1] - a[1])
        L = math.hypot(*d)
        if L <= 0 or abs(_cross(u, (d[0] / L, d[1] / L))) <= 1e-3:
            continue
        t = max(0.0, min(1.0, ((p[0] - a[0]) * d[0] + (p[1] - a[1]) * d[1]) / (L * L)))
        if math.dist(p, (a[0] + d[0] * t, a[1] + d[1] * t)) <= tol:
            return True
    return False


def _space_at(ctx, p):
    for f in ctx["faces"]:
        if _inside(p[0], p[1], f["polygon"]) and not any(_inside(p[0], p[1], h) for h in f.get("hole_polygons") or ()):
            return f
    return None


def beyond(o, ctx, side, dist_m):
    """the spaces on both faces of the wall at the enlarged jamb (dist_m beyond the jamb on `side`)."""
    um = ctx["unit_m"]
    u, n = tuple(o["u"]), tuple(o["n"])
    lo, hi = sorted((o["o0"], o["o1"]))
    s = (o["s0"] - dist_m / um) if side == "START" else (o["s1"] + dist_m / um)
    out = []
    for off in (lo - PROBE_M / um, hi + PROBE_M / um):
        p = (u[0] * s + n[0] * off, u[1] * s + n[1] * off)
        f = _space_at(ctx, p)
        out.append({"face_id": f["face_id"] if f else None, "codes": list(f.get("codes") or ()) if f else []})
    return out


def swing(el, ctx, leaf_m, hinge_shift_m=0.0):
    """the quarter disc the leaf of width leaf_m sweeps about its hinge (moved hinge_shift_m outward when the hinge
    jamb moves) against the walls, columns and drawn fixtures on the swing side. None leaf / no swing: NOT_EVALUATED."""
    um = ctx["unit_m"]
    occs = [x for x in el.get("swings") or () if x in ctx["swings"]]
    if not occs or el.get("u") is None or leaf_m is None or el.get("leaf_count", 1) != 1:
        return {"state": "NOT_EVALUATED", "why": "no single drawn leaf" if el.get("leaf_count", 1) == 1 else
                "double leaf: each leaf's swing is not re-evaluated", "leaf_m": leaf_m}
    sw = ctx["swings"][occs[0]]
    u, n = tuple(el["u"]), tuple(el["n"])
    H = sw["hinge"]
    ends = [tuple(e) for e in sw["ends"]]
    rel = [(e[0] - H[0], e[1] - H[1]) for e in ends]
    open_end = max(rel, key=lambda r: abs(_dot(r, n)))
    closed = min(rel, key=lambda r: abs(_dot(r, n)))
    sgn = 1.0 if _dot(open_end, n) > 0 else -1.0
    toward = 1.0 if _dot(closed, u) > 0 else -1.0
    o = next((x for x in ctx["openings"] if x["opening_id"] == el.get("opening_id")), None)
    if o is not None:
        # the closed leaf must lie across the gap: a symbol closing outside the jambs (rotated / mis-mirrored) gives
        # no swing side - it is reported, never evaluated as CLEAR or CONFLICT
        cs = _dot((H[0] + closed[0], H[1] + closed[1]), tuple(o["u"]))
        g0, g1 = sorted((o["s0"], o["s1"]))
        if not (g0 - SYMBOL_TOL_M / um <= cs <= g1 + SYMBOL_TOL_M / um):
            return {"state": "NOT_EVALUATED", "leaf_m": leaf_m, "swing_side": None,
                    "why": "SWING_SYMBOL_INCONSISTENT: the drawn leaf closes outside the opening's jambs; the swing "
                           "side is not established from this symbol"}
    H = (H[0] - toward * u[0] * hinge_shift_m / um, H[1] - toward * u[1] * hinge_shift_m / um)
    R = leaf_m / um
    lo, hi = sorted((o["o0"], o["o1"])) if o else (_dot(H, n) - 0.01 / um, _dot(H, n) + 0.01 / um)
    tol = FACE_TOL_M / um

    def in_sector(p):
        d = (p[0] - H[0], p[1] - H[1])
        r = math.hypot(*d)
        if r >= R - tol or r <= tol:
            return False
        a, b = _dot(d, u) * toward, _dot(d, n) * sgn
        if a <= tol or b <= tol:                                # behind the hinge or on the wall line: clear
            return False
        q = _dot(p, n)
        return not (lo - tol <= q <= hi + tol)                  # the host wall strip itself is not an obstruction
    hits = []
    step = SAMPLE_M / um
    for s in ctx["wall_segs"]:
        a, b = s["a"], s["b"]
        if min(math.dist(H, a), math.dist(H, b)) > R + math.dist(a, b):
            continue
        k = max(1, int(math.dist(a, b) / step))
        if any(in_sector((a[0] + (b[0] - a[0]) * i / k, a[1] + (b[1] - a[1]) * i / k)) for i in range(k + 1)):
            hits.append({"kind": "WALL", "id": s["id"]})
    for k, (x0, y0, x1, y1) in enumerate(ctx["columns"], 1):
        pts = [(x0 + (x1 - x0) * i / 8, y0 + (y1 - y0) * j / 8) for i in range(9) for j in range(9)]
        if any(in_sector(p) for p in pts):
            hits.append({"kind": "COLUMN", "id": f"column {k}"})
    for i in ctx["inserts"]:
        nm = str(i.get("name") or "").upper()
        if not any(w in nm for w in FIXTURE_RE):
            continue
        b = i.get("box")
        p = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else (i.get("x"), i.get("y"))
        if p[0] is not None and in_sector(p):
            hits.append({"kind": "FIXTURE", "id": i.get("name")})
    return {"state": "CONFLICT" if hits else "CLEAR", "leaf_m": round(leaf_m, 6), "obstructions": hits,
            "swing_side": "n+" if sgn > 0 else "n-", "hinge_moved_m": round(hinge_shift_m, 6)}


def _structure(el, o, ctx, resolver):
    host = None
    for w in ctx["walls"]:
        if o and w.get("wall_id") == o.get("band_id"):
            host = w["wall_id"]
    r = resolver.get("UP-DOOR-FEAS-001", "wall_structure",
                     {"floor": el["floor"], "wall_id": host, "opening_id": el.get("opening_id")})
    if r["value"] == "STRUCTURAL":
        return "STRUCTURAL", r
    if r["value"] == "NON_STRUCTURAL":
        return "NON_STRUCTURAL_SPECIFIED", r
    if r["state"] == "CONFLICT_REVIEW":
        return "UNKNOWN", r
    return ("MASONRY_INDICATED" if ctx["frame_drawn"] else "UNKNOWN"), r


def _placements(d, sides, pier):
    """the ways the enlargement d can be placed: (name, take_start, take_end, remaining piers)."""
    av = {k: max(0.0, s["plain_m"] - (0.0 if s["constraint"] in ("COLUMN", "OPEN_RUN") else pier))
          for k, s in sides.items()}
    opts = []
    for name, ts, te in (("SPLIT_EQUAL", d / 2, d / 2), ("START_SIDE", d, 0.0), ("END_SIDE", 0.0, d)):
        if ts <= av["START"] + TOL_M and te <= av["END"] + TOL_M:
            opts.append((name, ts, te))
    if not opts and av["START"] + av["END"] >= d - TOL_M:
        te = min(av["END"], d)
        opts.append(("UNEQUAL", d - te, te))
    out = []
    for name, ts, te in opts:
        out.append({"placement": name, "start_m": round(ts, 6), "end_m": round(te, 6),
                    "pier_left_start_m": round(sides["START"]["plain_m"] - ts, 6),
                    "pier_left_end_m": round(sides["END"]["plain_m"] - te, 6)})
    return out, {k: round(v, 6) for k, v in av.items()}


def classify(category, el, need_m, sides, structure, swing_rec, placements):
    """-> (class, reasons)."""
    if category == DSTD.MAIN:
        return "STANDARD_FITS_AS_DRAWN", ["main entrance: the actual project dimensions govern (UP-DOOR-CLS-004)"]
    if category not in ORDINARY:
        return "INSUFFICIENT_DRAWING_EVIDENCE", [f"door category {category} is not settled"]
    if el["state"] != "CONFIRMED" or el.get("structural_opening_width_m") is None:
        return "INSUFFICIENT_DRAWING_EVIDENCE", [f"door width state {el['state']} (no measured wall opening)"]
    if el.get("hold"):
        return "INSUFFICIENT_DRAWING_EVIDENCE", ["width held: " + el["hold"]]
    if need_m is None:
        return "INSUFFICIENT_DRAWING_EVIDENCE", ["the applicable door standard is in conflict (project rules)"]
    if need_m <= TOL_M:
        return "STANDARD_FITS_AS_DRAWN", ["the CAD wall opening meets the required wall opening"]
    if sides is None:
        return "INSUFFICIENT_DRAWING_EVIDENCE", ["the host wall of the opening is not read (no band opening)"]
    if placements:
        if structure in ("STRUCTURAL", "UNKNOWN"):
            return "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW", [
                f"the plain wall allows it, but the host wall's structural status is {structure}"]
        if swing_rec["state"] == "CONFLICT":
            return "ENLARGEMENT_CONSTRAINED", ["the larger leaf's swing meets " + ", ".join(
                f"{h['kind'].lower()} {h['id']}" for h in swing_rec["obstructions"][:3])]
        return "ENLARGEMENT_GEOMETRICALLY_POSSIBLE", [f"{p['placement']}" for p in placements[:1]] + (
            [swing_rec["why"]] if str(swing_rec.get("why") or "").startswith("SWING_SYMBOL") else [])
    blockers = {k: s["constraint"] for k, s in sides.items()}
    if all(b == "COLUMN" for b in blockers.values()):
        return "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW", [
            "columns on both sides: the opening can only widen by altering a structural element (never recommended)"]
    return "ENLARGEMENT_CONSTRAINED", ["not enough plain wall: START " + blockers["START"] + f" at "
                                       f"{sides['START']['plain_m']:.2f} m, END {blockers['END']} at "
                                       f"{sides['END']['plain_m']:.2f} m"]


def door_height_v24(category, facts, resolver, target):
    """UP-DOOR-HGT-001 under V2.4: a project rule, then a source height (facts), then the owner standard
    (OWNER_STANDARD_ASSUMED); a main-entrance candidate between the external and main-entrance standards; an elevator
    landing not established."""
    if category == DSTD.ELEVATOR:
        return {"value_m": None, "state": "MISSING_DOCUMENT", "source": "the elevator landing door data",
                "flag": "JAMB_HEIGHT_NOT_ESTABLISHED"}
    if category == DSTD.MAIN_CAND:
        lo, hi = K.reference_height(DSTD.EXTERNAL), K.reference_height(DSTD.MAIN)
        return {"value_m": None, "range_m": [lo, hi], "state": "CLASS_PENDING", "flag": "JAMB_HEIGHT_CLASS_PENDING",
                "source": "main-entrance candidate: external aluminium or main entrance"}
    cat = category if category in ORDINARY + (DSTD.MAIN,) else DSTD.INTERNAL
    r = resolver.get("UP-DOOR-HGT-001", "door_height_m", dict(target, door_category=cat))
    if r["project_rule_ids"]:
        return {"value_m": r["value"], "state": r["state"], "source": r["source"], "rules": r["project_rule_ids"]}
    if r["state"] == "CONFLICT_REVIEW":
        return {"value_m": None, "state": "CONFLICT_REVIEW", "source": r.get("note"), "flag": "PROJECT_RULE_CONFLICT"}
    h = DSTD.door_height(cat, facts)
    st = "OWNER_STANDARD_ASSUMED" if h["state"] == "ASSUMED" and h.get("precedence") == "OWNER_RULE" else \
        "PROJECT_SPECIFIED" if h["state"] == "ASSUMED" else \
        ("DRAWING_CONFIRMED" if h.get("precedence") == "APPROVED_DRAWING" else "PROJECT_SPECIFIED")
    return {"value_m": h["value_m"], "state": st, "source": h["source"],
            "class_note": None if category in ORDINARY + (DSTD.MAIN,) else
            f"category {category}: every candidate class shares the {h['value_m']:.2f} m standard"}


def feasibility(model, contexts, *, resolver, facts):
    rows = []
    for el in model["elements"]:
        cat, basis = DSTD.door_category(el)
        ctx = contexts.get(el["floor"])
        o = next((x for x in (ctx or {}).get("openings") or () if x["opening_id"] == el.get("opening_id")), None)
        cad = el.get("structural_opening_width_m")
        t = {"floor": el["floor"], "opening_id": el.get("opening_id"), "door_category": cat,
             "room_id": next((sd.get("room_id") for sd in el.get("sides") or () if sd.get("room_id")), None)}
        row = {"element_id": el["element_id"], "floor": el["floor"], "opening_id": el.get("opening_id"),
               "category": cat, "category_basis": basis, "state": el["state"],
               "spaces": [sd.get("room_name") or sd.get("kind") for sd in el.get("sides") or ()],
               "cad_wall_opening_m": None if cad is None else round(cad, 6),
               "rules": ["UP-DOOR-FEAS-001", "UP-DOOR-OPEN-002", "UP-DOOR-HGT-001"]}
        if cat == DSTD.ELEVATOR:
            row.update(view="EXCLUDED", feasibility=None, why="elevator entrance: the elevator schedule")
            rows.append(row)
            continue
        nom = resolver.get("UP-DOOR-OPEN-002", "required_nominal_door_m", t) if cat in ORDINARY else None
        alw = resolver.get("UP-DOOR-OPEN-002", "allowance_m", t)
        pier = resolver.get("UP-DOOR-FEAS-001", "min_pier_m", t)
        allowance = alw["value"]
        need = req = None
        cad = None if cad is None else round(cad, 6)
        if nom is not None and nom["value"] is not None and allowance is not None and cad is not None:
            req = round(nom["value"] + allowance, 6)
            need = round(max(0.0, req - cad), 6)
        row["standard"] = None if nom is None else {
            "required_nominal_door_m": nom["value"], "state": nom["state"], "urban_nominal_m": nom["urban_value"],
            "allowance_m": allowance, "allowance_state": alw["state"], "required_wall_opening_m": req,
            "project_rule_ids": nom["project_rule_ids"], "source": nom["source"]}
        row["available_nominal_m"] = None if cad is None or allowance is None else round(cad - allowance, 6)
        row["enlargement_m"] = need
        row["compliance"] = ("NOT_APPLICABLE" if cat not in ORDINARY else "NOT_ESTABLISHED" if need is None else
                             "ENLARGEMENT_REQUIRED" if need > TOL_M else "MEETS_STANDARD")
        sides = clearances(o, ctx) if (o is not None and ctx is not None and el["state"] == "CONFIRMED") else None
        row["clearances"] = sides
        pier_m = pier["value"] if pier["value"] is not None else ENGINE_PIER_M
        place, avail = (_placements(need, sides, pier_m) if sides is not None and need and need > TOL_M
                        else ([], None))
        row["pier"] = {"value_m": pier_m, "state": pier["state"], "note": pier.get("note")}
        row["placements"], row["available_m"] = place, avail
        structure, sres = _structure(el, o, ctx, resolver) if ctx is not None else ("UNKNOWN", None)
        row["host_wall"] = {"structure": structure, "basis": (sres or {}).get("source") or (
            "the plan draws a column frame and the wall on a masonry wall layer (not verified)"
            if structure == "MASONRY_INDICATED" else "no column frame is drawn on this plan; the structural drawings "
                                                     "decide" if structure == "UNKNOWN" else None)}
        best = place[0] if place else None
        leaf = None if nom is None else nom["value"]
        hinge_shift = 0.0
        sw = {"state": "NOT_EVALUATED", "why": "no enlargement", "leaf_m": leaf}
        if ctx is not None and need and need > TOL_M and best is not None:
            occ = next((x for x in el.get("swings") or () if x in ctx["swings"]), None)
            if occ is not None and o is not None:
                hs = _dot(tuple(ctx["swings"][occ]["hinge"]), tuple(o["u"]))
                hinge_side = "START" if abs(hs - o["s0"]) <= abs(hs - o["s1"]) else "END"
                hinge_shift = best["start_m"] if hinge_side == "START" else best["end_m"]
            sw = swing(el, ctx, leaf, hinge_shift)
            sw["as_drawn"] = swing(el, ctx, (el.get("nominal_leaf_width_m") or [None])[0], 0.0)["state"]
        row["swing"] = sw
        cls, reasons = classify(cat, el, need, sides, structure, sw, place)
        row["feasibility"], row["reasons"] = cls, reasons
        if sides is not None and need and need > TOL_M:
            for k in ("START", "END"):
                sides[k]["beyond_at_enlarged_jamb"] = beyond(o, ctx, k, (best or {}).get(
                    "start_m" if k == "START" else "end_m") or 0.0)
            special = sorted({c for k in ("START", "END") for b in sides[k]["beyond_at_enlarged_jamb"]
                              for c in b["codes"] if c in ("STAIR", "SHAFT", "LIFT")})
            if special:
                why = "a " + "/".join(special).lower() + " space at the enlarged jamb"
                if cls == "ENLARGEMENT_GEOMETRICALLY_POSSIBLE":
                    # the governing reason first; the placement is only what the plain wall would allow
                    row["feasibility"] = cls = "ENLARGEMENT_CONSTRAINED"
                    row["reasons"] = [why] + [f"plain wall alone would allow {r_}" for r_ in row["reasons"]]
                else:
                    row["reasons"].append(why)
        h = door_height_v24(cat, facts, resolver, {"floor": el["floor"], "opening_id": el.get("opening_id")})
        row["height"] = h
        if need and need > TOL_M:
            sc = [_scope_of(ctx, sd.get("room_id")) for sd in el.get("sides") or ()]
            row["proposed_modification"] = {
                "status": "MODIFICATION_PROPOSED_NOT_APPROVED", "feasibility": cls, "placement": best,
                "required_increase_m": need, "max_feasible_enlargement_m": None if avail is None else
                round(avail["START"] + avail["END"], 6),
                "max_feasible_nominal_m": None if (avail is None or cad is None or allowance is None) else
                round(cad + avail["START"] + avail["END"] - allowance, 6),
                # a side read only to REACH_M (OPEN_RUN): the maximum is at least this, not exactly this
                "max_feasible_is_lower_bound": bool(sides) and any(sd["constraint"] == "OPEN_RUN"
                                                                   for sd in sides.values()),
                "dependency_impacts": DSTD.dependency_impacts(need, {"value_m": h.get("value_m"),
                                                                     "state": h["state"]},
                                                              el.get("wall_t_m"), (o or {}).get("jambs") or
                                                              [(o or {}).get("start_jamb"), (o or {}).get("end_jamb")],
                                                              sc),
                "if_not_approved": {"door_that_fits_m": row["available_nominal_m"],
                                    "note": "the CAD wall opening less the allowance: a smaller door than the owner "
                                            "standard"},
                "approvals": _approvals(cls, structure)}
        row["view"] = ("UNRESOLVED" if cls in ("INSUFFICIENT_DRAWING_EVIDENCE",
                                                "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW") else
                       "PROPOSED_MODIFICATION" if need and need > TOL_M else "OWNER_STANDARD")
        row["released_as_drawn"] = bool(el.get("released"))
        rows.append(row)
    return {"policy": POLICY_ID, "rule_set": K.rule_set(), "rule_set_digest": K.digest(), "rows": rows,
            "views": views(rows), "approvals": [dict(a, element_id=r["element_id"], floor=r["floor"])
                                                for r in rows for a in (r.get("proposed_modification") or {})
                                                .get("approvals") or ()],
            "summary": {c: sum(1 for r in rows if r.get("feasibility") == c) for c in CLASSES},
            "conservation": {"elements": len(model["elements"]), "rows": len(rows),
                             "ok": len(rows) == len(model["elements"]) ==
                             len({r["element_id"] for r in rows})},
            "never": ["a proposed modification in the as-drawn quantities", "geometric clearance as structural "
                      "approval", "a column, beam or structural wall cut by recommendation"]}


def _scope_of(ctx, room_id):
    from engine.source import owner_finish_scope as OFS
    r = next((x for x in (ctx or {}).get("rooms") or () if x.get("room_id") == room_id), None)
    return OFS.finish_scope(r)["scope"] if r else None


def _approvals(cls, structure):
    out = [{"who": "owner / architect", "what": "the wall-opening enlargement as a design change (drawing revision)"}]
    if structure in ("MASONRY_INDICATED", "NON_STRUCTURAL_SPECIFIED"):
        out.append({"who": "structural engineer", "what": "confirm the host wall is non-load-bearing and the lintel "
                                                          "over the wider opening"})
    if cls == "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW" or structure in ("STRUCTURAL", "UNKNOWN"):
        out.append({"who": "structural engineer", "what": "review: structural element or unknown structure at the "
                                                          "opening - no alteration is recommended without it"})
    if cls == "ENLARGEMENT_CONSTRAINED":
        out.append({"who": "owner / architect", "what": "accept a smaller door, or relocate / redesign the opening"})
    return out


def views(rows):
    """AS_DRAWN (the released doors as the drawing shows them), OWNER_STANDARD (the standard each requires),
    PROPOSED_MODIFICATION (the enlargements, never as drawn), UNRESOLVED, EXCLUDED - never added together."""
    v = {"AS_DRAWN": {}, "OWNER_STANDARD": {}, "PROPOSED_MODIFICATION": {}, "UNRESOLVED": {}, "EXCLUDED": {}}
    for r in rows:
        if r.get("view") == "EXCLUDED":
            v["EXCLUDED"][r["category"]] = v["EXCLUDED"].get(r["category"], 0) + 1
            continue
        if r["released_as_drawn"]:
            a = v["AS_DRAWN"].setdefault(r["category"], {"count": 0, "cad_wall_opening_m": 0.0})
            a["count"] += 1
            a["cad_wall_opening_m"] = round(a["cad_wall_opening_m"] + (r["cad_wall_opening_m"] or 0.0), 6)
        if r.get("standard"):
            s = v["OWNER_STANDARD"].setdefault(r["category"], {"count": 0, "meets": 0, "enlargement_required": 0})
            s["count"] += 1
            s["meets"] += r["compliance"] == "MEETS_STANDARD"
            s["enlargement_required"] += r["compliance"] == "ENLARGEMENT_REQUIRED"
        pm = r.get("proposed_modification")
        if pm:
            p = v["PROPOSED_MODIFICATION"].setdefault(r["feasibility"], {"count": 0, "enlargement_m": 0.0})
            p["count"] += 1
            p["enlargement_m"] = round(p["enlargement_m"] + pm["required_increase_m"], 6)
        if r["view"] == "UNRESOLVED":
            v["UNRESOLVED"][r["feasibility"]] = v["UNRESOLVED"].get(r["feasibility"], 0) + 1
    v["note"] = "four views of the same doors; never added together; the BOQ door lines stay as drawn"
    return v


def jamb_plaster_lines(ctx, lines, model, resolver, facts, line):
    """the V2.3 door jamb / head plaster lines (UP-FIN-PLASTER-001, 2 x wall t x H + t x w) rebuilt at the height of
    each door's category; -> (lines, unresolved)."""
    by = {(el["floor"], el.get("opening_id")): el for el in model["elements"] if el.get("opening_id")}
    out, unres = [], []
    for ln in lines:
        if not (ln["item_code"] == "FIN.PLASTER" and ln.get("physical_element") == "door jambs and head"):
            out.append(ln)
            continue
        fl, rid = ln["location"]["floor"], ln["location"]["room_id"]
        oid = rid.split("-OPENING-", 1)[-1]
        el = by.get((fl, oid))
        cat = DSTD.door_category(el)[0] if el else DSTD.UNRESOLVED
        h = door_height_v24(cat, facts, resolver, {"floor": fl, "opening_id": oid})
        inp = dict(ln["calculation"]["inputs"])
        t, w = inp["wall_t_m"], inp["width_m"]
        room = {"room_id": rid, "floor": fl, "name_en": ln["location"]["room_name_en"],
                "name_ar": ln["location"]["room_name_ar"]}
        f = "2 x wall thickness x door height (by category) + wall thickness x opening width"
        if h.get("value_m") is None:
            if h.get("range_m"):
                lo, hi = h["range_m"]
                q = (f"JAMB_HEIGHT_CLASS_PENDING (UP-DOOR-HGT-001): door {oid} is a main-entrance candidate - "
                     f"{lo:.2f} m (external aluminium) or {hi:.2f} m (main entrance)")
                out.append(line(ctx, item_code="FIN.PLASTER", room=room, element="door jambs and head", unit="m2",
                                net=None, formula=f, inputs=dict(inp, height_m=None, height_state=h["state"],
                                                                  category=cat),
                                ref=K.ref("UP-DOOR-HGT-001"),
                                bounded={"low": round(2 * t * lo + t * w, 6), "high": round(2 * t * hi + t * w, 6),
                                         "basis": q}, rfi={"question": q, "unlocks": rid}))
            else:
                q = f"{h.get('flag', 'JAMB_HEIGHT_NOT_ESTABLISHED')} (UP-DOOR-HGT-001): door {oid} ({cat}): " \
                    f"{h.get('source')}"
                out.append(line(ctx, item_code="FIN.PLASTER", room=room, element="door jambs and head", unit="m2",
                                net=None, formula=f, inputs=dict(inp, height_m=None, height_state=h["state"],
                                                                  category=cat),
                                ref=K.ref("UP-DOOR-HGT-001"), rfi={"question": q, "unlocks": rid}))
            unres.append({"room_id": rid, "floor": fl, "item": "FIN.PLASTER", "reason": q})
            continue
        H = h["value_m"]
        out.append(line(ctx, item_code="FIN.PLASTER", room=room, element="door jambs and head", unit="m2",
                        net=round(2 * t * H + t * w, 6), ev="PROVISIONAL", formula=f,
                        inputs=dict(inp, height_m=H, height_state=h["state"], height_source=h.get("source"),
                                    category=cat), ref=K.ref("UP-DOOR-HGT-001"),
                        notes="FRAME_ALIGNMENT_PLASTER: confirm with the frame detail how much of the jambs and head "
                              f"is plastered; height {h['state']}"))
    return out, unres


def csv_rows(rep):
    out = []
    for r in rep["rows"]:
        s = r.get("standard") or {}
        c = r.get("clearances") or {}
        pm = r.get("proposed_modification") or {}
        out.append({"element_id": r["element_id"], "floor": r["floor"], "opening_id": r["opening_id"],
                    "category": r["category"], "view": r.get("view"), "feasibility": r.get("feasibility"),
                    "cad_wall_opening_m": r["cad_wall_opening_m"],
                    "required_nominal_door_m": s.get("required_nominal_door_m"),
                    "required_wall_opening_m": s.get("required_wall_opening_m"), "standard_state": s.get("state"),
                    "available_nominal_m": r.get("available_nominal_m"), "enlargement_m": r.get("enlargement_m"),
                    "compliance": r.get("compliance"),
                    "start_clearance_m": (c.get("START") or {}).get("plain_m"),
                    "start_constraint": (c.get("START") or {}).get("constraint"),
                    "end_clearance_m": (c.get("END") or {}).get("plain_m"),
                    "end_constraint": (c.get("END") or {}).get("constraint"),
                    "placement": (pm.get("placement") or {}).get("placement"),
                    "swing": (r.get("swing") or {}).get("state"), "host_wall": (r.get("host_wall") or {}).get("structure"),
                    "door_if_not_approved_m": (pm.get("if_not_approved") or {}).get("door_that_fits_m"),
                    "height_m": (r.get("height") or {}).get("value_m"), "height_state": (r.get("height") or {}).get("state"),
                    "reasons": "; ".join(r.get("reasons") or ())})
    return out


CSV_COLUMNS = ("element_id", "floor", "opening_id", "category", "view", "feasibility", "cad_wall_opening_m",
               "required_nominal_door_m", "required_wall_opening_m", "standard_state", "available_nominal_m",
               "enlargement_m", "compliance", "start_clearance_m", "start_constraint", "end_clearance_m",
               "end_constraint", "placement", "swing", "host_wall", "door_if_not_approved_m", "height_m",
               "height_state", "reasons")


def policy_record():
    return {"policy": POLICY_ID, "rule_set": K.rule_set(), "rule_set_digest": K.digest(), "classes": list(CLASSES),
            "reach_m": REACH_M, "corner_span_m": CORNER_SPAN_M, "face_tolerance_m": FACE_TOL_M,
            "rules": ["UP-DOOR-FEAS-001", "UP-DOOR-OPEN-002", "UP-DOOR-HGT-001", "UP-DOOR-DEP-001", "UP-RULES-001"]}

"""TILE LAYOUT (M9 S1) - exact cutting plan of a RECTANGULAR surface for one tile size (generic; stdlib only).

    layout(room, spec, *, orientation, align_x, align_y, constraints)  -> one layout: pieces, cuts, offcuts, material result
    best(room, spec, constraints)                                       -> the minimum-waste FEASIBLE layout + every layout tried
    compare(room, specs, selected, constraints)                         -> one row per candidate size; the selected size stays
                                                                           primary, the others are recommendations only

Scope (S1): a rectangle (length x width, or a 4-vertex right-angled polygon), straight pattern, uniform joint. Anything
else - an L-shaped room, a column inside, a shower tray, a diagonal or herringbone pattern - is BLOCKED with the reason
POLYGON_OPTIMIZER_NOT_IMPLEMENTED (S2) / PATTERN_NOT_IMPLEMENTED; nothing is approximated by a bounding box.

Per axis the pieces are exact: tiles of module (tile + joint) from the start line, the remainder cut at the wall.
    CORNER          a full tile against the start wall
    CENTRED_TILE    a full tile centred on the axis (equal cuts at both walls)
    CENTRED_JOINT   a joint on the axis centre line (equal cuts at both walls)
Cut pieces are taken from whole tiles or from retained offcuts (guillotine cuts, best-fit, largest piece first); an
offcut is retained only when both sides reach constraints["min_reusable_m"] (None: no offcut is ever reused). The
plan is a FEASIBLE cutting plan found by a deterministic heuristic - an upper bound on the tiles needed for that
layout, not a proof of the minimum.

constraints (every value the caller's, recorded in the result; nothing defaulted silently):
    joint_m             joint width (required)
    min_cut_m           smallest acceptable cut dimension; a layout with a smaller cut is infeasible (None: no limit)
    min_reusable_m      smallest offcut side kept for reuse (None: no reuse)
    kerf_m              material lost per cut line (default 0)
    rotation_allowed    an offcut may be turned 90 degrees (default False: grain / shade direction kept)
    orientations        allowed orientations (default (0, 90)); alignments: allowed start alignments (default all three)
    objective           "CONSUMED_MATERIAL" (default: fewest tiles opened, then the least owner-defined cutting waste)
                        or "CUTTING_WASTE" (the owner-defined waste first). The owner definition credits retained
                        offcuts; until cross-room reuse is planned (S2) a retained offcut saves nothing, and ranking by
                        cutting waste alone prefers layouts that open more tiles - the default therefore ranks by the
                        material consumed and reports the owner-defined waste of the layout chosen
    wet_room            True adds the FALLS_TO_DRAIN_NOT_MODELLED concern
"""

from __future__ import annotations

import math

from engine.source import material_result as WP

METHOD = "TILE_RECT_EXACT_V1"
ALIGNMENTS = ("CORNER", "CENTRED_TILE", "CENTRED_JOINT")
ORIENTATIONS = (0, 90)
OBJECTIVES = ("CUTTING_WASTE", "CONSUMED_MATERIAL")
EPS = 1e-6
POLYGON_BLOCK = "POLYGON_OPTIMIZER_NOT_IMPLEMENTED (S2): the S1 tile engine lays rectangles only"


class LayoutError(ValueError):
    pass


def rectangle(room):
    """(a, b) side lengths of a rectangular room, or None when the room is not a rectangle."""
    if room.get("length_m") is not None and room.get("width_m") is not None and not room.get("polygon"):
        return float(room["length_m"]), float(room["width_m"])
    pts = [tuple(map(float, p)) for p in room.get("polygon") or []]
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) < EPS:
        pts = pts[:-1]
    # drop collinear vertices
    clean = []
    n = len(pts)
    for i in range(n):
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cross) > 1e-9:
            clean.append(b)
    if len(clean) != 4:
        return None
    sides = [math.dist(clean[i], clean[(i + 1) % 4]) for i in range(4)]
    for i in range(4):
        a, b, c = clean[i - 1], clean[i], clean[(i + 1) % 4]
        dot = (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1])
        if abs(dot) > 1e-6 * max(sides) ** 2:
            return None
    if abs(sides[0] - sides[2]) > 1e-6 or abs(sides[1] - sides[3]) > 1e-6:
        return None
    return sides[0], sides[1]


def axis_pieces(D, t, g, align):
    """piece lengths along one axis of length D, from the start wall, for tile length t and joint g."""
    if align not in ALIGNMENTS:
        raise LayoutError(f"unknown alignment {align}")
    if D <= EPS:
        return []

    def run(avail, start):
        out, pos = [], start
        while avail - pos >= t - EPS:
            out.append(t)
            pos += t + g
        if avail - pos > EPS:
            out.append(avail - pos)
        return out
    if align == "CORNER":
        return run(D, 0.0)
    H = D / 2.0
    if align == "CENTRED_JOINT":
        side = run(H, g / 2.0)
        return side[::-1] + side
    if D <= t + EPS:                                   # CENTRED_TILE in a room narrower than one tile
        return [D]
    side = run(H, t / 2.0 + g)
    return side[::-1] + [t] + side


def _cut(rect, px, py, kerf):
    """cut a px x py piece from the corner of rect (w, h); two guillotine options, keep the one whose larger leftover
    is larger. -> (leftovers [(w, h)], rotated?) with leftovers of positive size only."""
    w, h = rect
    dx, dy = w - px, h - py
    kx = kerf if dx > EPS else 0.0
    ky = kerf if dy > EPS else 0.0
    a = [(dx - kx, h), (px, dy - ky)]                  # vertical cut first
    b = [(w, dy - ky), (dx - kx, py)]                  # horizontal cut first
    a = [r for r in a if r[0] > EPS and r[1] > EPS]
    b = [r for r in b if r[0] > EPS and r[1] > EPS]
    big = lambda rs: max((r[0] * r[1] for r in rs), default=0.0)      # noqa: E731
    return a if big(a) >= big(b) - 1e-12 else b


def _fits(rect, px, py, rot):
    w, h = rect
    if w >= px - EPS and h >= py - EPS:
        return (px, py)
    if rot and w >= py - EPS and h >= px - EPS:
        return (py, px)
    return None


def _plan(cuts, tx, ty, c):
    """cut pieces [(px, py)] from whole tiles / offcuts. -> (tiles opened, offcuts retained, scrap area, kerf, log)."""
    min_re, kerf, rot = c.get("min_reusable_m"), c.get("kerf_m") or 0.0, bool(c.get("rotation_allowed"))
    pool, opened, scrap, from_offcut = [], 0, 0.0, 0
    for px, py in sorted(cuts, key=lambda p: (-p[0] * p[1], -max(p), -p[0])):
        best = None
        for i, r in enumerate(pool):
            f = _fits(r, px, py, rot)
            if f and (best is None or r[0] * r[1] < pool[best[0]][0] * pool[best[0]][1] - 1e-12):
                best = (i, f)
        if best is not None:
            src = pool.pop(best[0])
            fx, fy = best[1]
            from_offcut += 1
        else:
            src, (fx, fy) = (tx, ty), (px, py)
            opened += 1
        for r in _cut(src, fx, fy, kerf):
            if min_re is not None and min(r) >= min_re - EPS:
                pool.append(r)
            else:
                scrap += r[0] * r[1]
    return opened, pool, scrap, from_offcut


def layout(room, spec, *, orientation=0, align_x="CORNER", align_y="CORNER", constraints):
    c = dict(constraints)
    if c.get("joint_m") is None:
        raise LayoutError("constraints['joint_m'] is required (the joint width is a design input, never assumed)")
    if spec.get("pattern", "STRAIGHT") != "STRAIGHT":
        return WP.blocked(method=METHOD, spec=spec, reason=f"PATTERN_NOT_IMPLEMENTED: {spec.get('pattern')} (S2)",
                          location=_loc(room), line_id=room.get("line_id"))
    ab = rectangle(room)
    if ab is None:
        return WP.blocked(method=METHOD, spec=spec, reason=POLYGON_BLOCK, location=_loc(room),
                          line_id=room.get("line_id"), net_installed_m2=room.get("net_area_m2"))
    X, Y = ab
    g = c["joint_m"]
    tx, ty = (spec["length_m"], spec["width_m"]) if orientation == 0 else (spec["width_m"], spec["length_m"])
    xs, ys = axis_pieces(X, tx, g, align_x), axis_pieces(Y, ty, g, align_y)
    full, cuts, placed = 0, [], 0.0
    small = []
    min_cut = c.get("min_cut_m")
    for px in xs:
        for py in ys:
            placed += px * py
            if abs(px - tx) <= EPS and abs(py - ty) <= EPS:
                full += 1
                continue
            cuts.append((px, py))
            for d, td in ((px, tx), (py, ty)):
                if abs(d - td) > EPS and min_cut is not None and d < min_cut - EPS:
                    small.append(round(d, 4))
    opened, pool, scrap, from_off = _plan(cuts, tx, ty, c)
    consumed_units = full + opened
    tile_a = tx * ty
    net = X * Y
    offcuts = sum(r[0] * r[1] for r in pool)
    concerns = []
    if small:
        concerns.append(f"SMALL_CUT: {len(small)} cut side(s) below {min_cut:g} m (smallest {min(small):g} m)")
    if tx > X + EPS or ty > Y + EPS:
        concerns.append("TILE_EXCEEDS_ROOM_DIMENSION: every piece along that axis is cut")
    if c.get("wet_room"):
        concerns.append("FALLS_TO_DRAIN_NOT_MODELLED: the layout is a flat plane; falls, drain position and envelope "
                        "cuts are not modelled")
    if c.get("min_reusable_m") is None:
        concerns.append("NO_OFFCUT_REUSE: min_reusable_m not given - every cut piece uses a whole tile (upper bound)")
    grid = _grid(X, Y, tx, ty, g)
    pack = WP.packaging(unit="box", consumed_units=consumed_units, unit_area_m2=tile_a,
                        units_per_pack=spec.get("pieces_per_box"), pack_area_m2=spec.get("box_area_m2"),
                        consumed_m2=consumed_units * tile_a, spare_allowance=c.get("spare_allowance"),
                        source=spec.get("packaging_source"))
    lay = {"room_sides_m": [X, Y], "orientation": orientation, "tile_along_x_m": tx, "tile_along_y_m": ty,
           "align_x": align_x, "align_y": align_y, "pieces_x_m": [round(p, 6) for p in xs],
           "pieces_y_m": [round(p, 6) for p in ys], "positions": len(xs) * len(ys), "full_tiles": full,
           "cut_pieces": len(cuts), "cut_from_offcuts": from_off, "tiles_opened_for_cuts": opened,
           "tiles_without_reuse": full + len(cuts), "grid_check": grid,
           "offcuts_retained_m": sorted([[round(r[0], 4), round(r[1], 4)] for r in pool], reverse=True),
           "scrap_m2": round(scrap, 6), "feasible": not small, "small_cuts_m": sorted(set(small))}
    assumptions = [f"joint {g:g} m", f"kerf {c.get('kerf_m') or 0:g} m",
                   f"min reusable offcut {c['min_reusable_m']:g} m" if c.get("min_reusable_m") is not None
                   else "no offcut reuse", f"min cut {min_cut:g} m" if min_cut is not None else "no minimum cut",
                   "offcut rotation allowed" if c.get("rotation_allowed") else "offcut rotation not allowed",
                   "no perimeter expansion gap modelled (pieces run to the finished wall line)",
                   "offcuts retained are reported, never credited to another room (cross-room reuse: S2)"]
    units = {"unit": "pcs", "unit_area_m2": tile_a, "consumed_units": consumed_units, "full": full, "cut": len(cuts)}
    return WP.make_result(method=METHOD, spec=spec, net_installed_m2=net, placed_m2=placed,
                          consumed_m2=consumed_units * tile_a, reusable_offcuts_m2=offcuts, units=units, pack=pack,
                          layout=lay, assumptions=assumptions, concerns=concerns, line_id=room.get("line_id"),
                          location=_loc(room), rule_refs=c.get("rule_refs", ()),
                          state="COMPUTED_REVIEW" if (small or concerns and c.get("wet_room")) else "COMPUTED")


def _grid(X, Y, tx, ty, g):
    """the takeoff-skill grid count ceil((L+g)/(t+g)) x ceil((W+g)/(t+g)): a cross-check (CORNER, no reuse)."""
    nx, ny = math.ceil((X + g) / (tx + g) - 1e-9), math.ceil((Y + g) / (ty + g) - 1e-9)
    return {"columns": nx, "rows": ny, "tiles": nx * ny}


def _loc(room):
    return {k: room.get(k) for k in ("room_id", "floor", "name_en", "name_ar") if room.get(k) is not None}


def _key(res, objective):
    lay = res["layout"]
    w, n = round(res["cutting_waste_m2"], 6), res["units"]["consumed_units"]
    head = (w, n) if objective == "CUTTING_WASTE" else (n, w)
    return head + (lay["cut_pieces"], ORIENTATIONS.index(lay["orientation"]), ALIGNMENTS.index(lay["align_x"]),
                   ALIGNMENTS.index(lay["align_y"]))


def best(room, spec, constraints):
    """the minimum-waste feasible layout over the allowed orientations and start alignments (same constraints for
    every candidate). -> {"selected": result, "tried": [summary rows], "feasible": bool, "note": ...}"""
    c = dict(constraints)
    objective = c.get("objective", "CONSUMED_MATERIAL")
    if objective not in OBJECTIVES:
        raise LayoutError(f"objective {objective}")
    oris = tuple(c.get("orientations") or ORIENTATIONS)
    if abs(spec["length_m"] - spec["width_m"]) <= EPS:
        oris = oris[:1]                                    # a square tile: 90 degrees is the same layout
    aligns = tuple(c.get("alignments") or ALIGNMENTS)
    tried = []
    for o in oris:
        for ax in aligns:
            for ay in aligns:
                r = layout(room, spec, orientation=o, align_x=ax, align_y=ay, constraints=c)
                if r["state"] == "BLOCKED":
                    return {"selected": r, "tried": [], "feasible": False, "note": r["blocked_by"]}
                tried.append(r)
    feas = [r for r in tried if r["layout"]["feasible"]]
    pool = feas or tried
    sel = min(pool, key=lambda r: _key(r, objective))
    note = "" if feas else "NO_FEASIBLE_LAYOUT: every layout has a cut below min_cut_m; the least-waste one is shown"
    if not feas:
        sel["concerns"] = sorted(set(sel["concerns"] + [note]))
        sel["state"] = "COMPUTED_REVIEW"
    other = min(pool, key=lambda r: _key(r, "CUTTING_WASTE" if objective == "CONSUMED_MATERIAL" else "CONSUMED_MATERIAL"))
    if objective == "CUTTING_WASTE" and other["units"]["consumed_units"] < sel["units"]["consumed_units"]:
        sel["concerns"] = sorted(set(sel["concerns"] + [
            f"LOWER_CONSUMPTION_LAYOUT_EXISTS: {_name(other)} opens {other['units']['consumed_units']} tiles against "
            f"{sel['units']['consumed_units']} (the selected one keeps more offcuts)"]))
    if objective == "CONSUMED_MATERIAL" and other["cutting_waste_m2"] < sel["cutting_waste_m2"] - 1e-6:
        sel["concerns"] = sorted(set(sel["concerns"] + [
            f"LOWER_OWNER_WASTE_LAYOUT_EXISTS: {_name(other)} has {other['cutting_waste_m2']:.3f} m2 cutting waste "
            f"against {sel['cutting_waste_m2']:.3f} m2 but opens {other['units']['consumed_units']} tiles against "
            f"{sel['units']['consumed_units']} (its saving is retained offcuts, not reused in S1)"]))
    rows = [{"layout": _name(r), "feasible": r["layout"]["feasible"], "full": r["units"]["full"],
             "cut": r["units"]["cut"], "consumed": r["units"]["consumed_units"],
             "cutting_waste_m2": r["cutting_waste_m2"], "reusable_offcuts_m2": r["reusable_offcuts_m2"],
             "small_cuts_m": r["layout"]["small_cuts_m"]} for r in tried]
    return {"selected": sel, "tried": rows, "feasible": bool(feas), "note": note, "objective": objective}


def _name(r):
    lay = r["layout"]
    return f"{lay['orientation']}deg {lay['align_x']}/{lay['align_y']}"


def compare(room, specs, selected, constraints):
    """one row per candidate size under the same constraints. The selected spec stays the BOQ basis; a candidate with
    less waste is reported as a RECOMMENDATION only (never substituted)."""
    if selected not in [s["spec_id"] for s in specs]:
        raise LayoutError(f"the selected size {selected} is not among the candidates")
    rows = []
    for s in specs:
        b = best(room, s, constraints)
        r = b["selected"]
        p = r.get("packaging") or {}
        rows.append({"spec_id": s["spec_id"], "name_en": s.get("name_en"), "name_ar": s.get("name_ar"),
                     "role": "SELECTED (BOQ basis)" if s["spec_id"] == selected else "ALTERNATIVE (recommendation only)",
                     "state": r["state"], "blocked_by": r.get("blocked_by"),
                     "net_m2": r["net_installed_m2"],
                     "layout": _name(r) if r["state"] != "BLOCKED" else None,
                     "full": (r.get("units") or {}).get("full"), "cut": (r.get("units") or {}).get("cut"),
                     "consumed": (r.get("units") or {}).get("consumed_units"),
                     "material_consumed_m2": r["consumed_m2"], "placed_m2": r["placed_m2"], "joint_m2": r["joint_m2"],
                     "reusable_offcuts_m2": r["reusable_offcuts_m2"], "cutting_waste_m2": r["cutting_waste_m2"],
                     "cutting_waste_pct": r["cutting_waste_pct"],
                     "waste_if_offcuts_discarded_m2": r["waste_if_offcuts_discarded_m2"],
                     "boxes": p.get("packs"), "packaging_state": p.get("state"),
                     "packaging_surplus_m2": p.get("packaging_surplus_m2"), "procurement_boxes": p.get("procurement_packs"),
                     "procurement_pcs": p.get("procurement_units"), "feasible": b["feasible"],
                     "concerns": r["concerns"], "result": r, "tried": b["tried"]})
    sel = next(x for x in rows if x["spec_id"] == selected)
    objective = dict(constraints).get("objective", "CONSUMED_MATERIAL")
    for x in rows:
        x["recommendation"] = ""
        if x is sel or x["state"] == "BLOCKED" or sel["state"] == "BLOCKED" or not x["feasible"]:
            continue
        dm = sel["material_consumed_m2"] - x["material_consumed_m2"]
        dw = sel["cutting_waste_m2"] - x["cutting_waste_m2"]
        better = dm > 1e-6 if objective == "CONSUMED_MATERIAL" else dw > 1e-6
        if better:
            x["recommendation"] = (f"RECOMMENDATION ONLY: {dm:+.3f} m2 less material consumed and {dw:+.3f} m2 less "
                                   f"cutting waste than the selected {selected}; the BOQ stays on {selected} unless the "
                                   f"owner / designer changes the specification")
    return rows

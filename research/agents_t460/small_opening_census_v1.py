"""SMALL OPENING CENSUS V1 (T-460 item C5, research, unwired): every jambed wall-band gap NARROWER than the engine's
0.50 m opening minimum is reported once, classified from the drawing's own evidence, never silently dropped and never 0.

DEFECT REPRODUCED (engine 5eded7df..aa79343a, read only): lintel_measure.openings / robust_geometry.openings, the band
path that feeds arch_rooms.spaces()["openings"] and so every opening deduction of blockwork, plaster, paint, tiles and
skirting, keep a band gap only when g >= min_gap_m = 0.50 m (opening_gaps.band_gaps `g < min_gap: continue`) and drop
every column-cut piece narrower than 0.50 m (lintel_measure._split_at_columns). A 0.40 m window or vent between two
masonry jambs therefore produces no opening record: its blockwork / plaster / paint stays in the wall, against the owner
rule Q-73 (CONFIRMED 2026-10-22: "Deduct the full area of every actual opening ... Apply the rule only to masonry that
physically exists").

PHYSICAL ELEMENT: a hole through the masonry of a wall, bounded on both sides by a jamb (masonry, column or closure
line), at any width. A gap in the band's face lines is NOT always such a hole: where a perpendicular wall crosses the
band, both faces of the band stop at the crossing wall's faces although masonry is continuous (a wall junction).

    census(segments, unit_m, wall_layers, columns=(), *, window_layers=(), swings=None, heights=None,
           floor_m=FLOOR_M, tol="UNIT_RELATIVE", geom_factory=None) -> {"records", "summary", "engine_openings"}

    segments       plan segments {"id", "layer", "a", "b"} of ONE plan frame (drawing units)
    unit_m         metres per drawing unit; None -> UNITS_MISSING, nothing measured (raises ValueError)
    wall_layers    the WALL-role layers (arch_plan.layer_roles), the same list arch_rooms.spaces() uses
    columns        column boxes as arch_rooms.spaces() builds them (obstacles that cut a gap at a column face)
    window_layers  WINDOW-role layers: glazing inside a gap is the evidence of a window
    swings         door swings (arch_rooms.door_swings); a swing that fits the gap (arch_rooms.match_swings) is a door
    heights        {probe_id: height_m} printed / scheduled opening heights (sill-to-head of the masonry hole); a
                   missing height keeps the deduction area HELD with the width measured (never 0, never dropped)
    floor_m        the numerical probe floor: band covers closer than the 1 mm merge tolerance are one cover anyway;
                   the floor only stops zero-width coincidences, it is not an engineering threshold
    geom_factory   callable(unit_m) -> robust_geometry.Geometry: the robust path of the candidate (route arch_rooms with
                   geom); None -> lintel_measure.openings (the LEGACY / tol path)

Classes (R-T460-1; first that holds):
    ENGINE_OPENING            width >= 0.50: already an engine opening (unchanged; listed for the reconciliation)
    SMALL_WINDOW              glazing lines of a WINDOW layer cover at least half the gap width (arch_rooms' own
                              WINDOW test, GLAZING_SHARE): an actual opening -> DEDUCT width x height
    SMALL_DOOR                a door swing fits the gap (arch_rooms.match_swings): an actual opening -> DEDUCT
    WALL_JUNCTION             both jambs are faces of one crossing wall whose two faces run on past BOTH faces of the
                              band (an X / through junction): continuous masonry -> NOT_AN_OPENING (evidence: the
                              crossing face ids)
    SUB_MIN_GAP_UNEXPLAINED   a jambed gap with no symbol: HELD (blockwork / plaster of that width x height is a named
                              range: [net - w x h, net]); never deducted, never kept silently
Deduction status per record: DEDUCT_MEASURED (width and height known), DEDUCT_HEIGHT_HELD (width known, height not
established), NOT_AN_OPENING, HELD, ENGINE (unchanged).
General: no layer, block, room or project name is coded; mirrored, rotated, mm and m plans read alike (vectors and
distances only). Unwired: no frozen file, method, rule or candidate line is changed.
"""

from __future__ import annotations

import math

POLICY = "SMALL_OPENING_CENSUS_V1"
RULES = ("Q-73", "UP-QTY-STATUS-001", "R-T460-1")
ENGINE_MIN_GAP_M = 0.50      # lintel_measure.openings / robust_geometry.openings default min_gap_m (checked by a test)
FLOOR_M = 0.002              # numerical probe floor (twice the 1 mm cover merge tolerance)
GLAZING_SHARE = 0.5          # arch_rooms.spaces: kind WINDOW when glazing >= 0.5 x width
JUNCTION_REACH_M = 0.03      # a crossing face counts when it runs beyond the band face by more than the 30 mm jamb tol
PERP_COS = 0.02              # a jamb face is across the band axis within about 1.1 degrees
SAME_M = 0.001               # a probe gap and an engine opening are one gap when both ends agree within 1 mm


def _openings(segments, unit_m, wall_layers, columns, min_gap_m, tol, geom_factory, region_id):
    if geom_factory is None:
        from engine.source import lintel_measure as LM
        return LM.openings(segments, unit_m, wall_layers, columns, tol=tol, min_gap_m=min_gap_m)
    from engine.source import robust_geometry as RG
    geom = geom_factory(unit_m)
    geom.context = region_id
    return RG.openings(segments, unit_m, wall_layers, columns, tol=tol, geom=geom, min_gap_m=min_gap_m)


def _frame(o, p):
    return (p[0] * o["u"][0] + p[1] * o["u"][1], p[0] * o["n"][0] + p[1] * o["n"][1])


def _glazing_m(o, segments, window_layers, unit_m):
    eps = 0.5e-3 / unit_m
    tot, ids = 0.0, []
    for s in segments:
        if s["layer"] not in window_layers:
            continue
        m = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
        su, so = _frame(o, m)
        if o["s0"] - eps <= su <= o["s1"] + eps and o["o0"] - eps <= so <= o["o1"] + eps:
            tot += math.dist(s["a"], s["b"]) * unit_m
            ids.append(s["id"])
    return tot, sorted(ids)


def _junction(o, segments, wall_layers, unit_m):
    """the crossing wall's face ids when both jambs are faces running on past both band faces, else None"""
    tol = 0.03 / unit_m                                   # the band-gap jamb tolerance (30 mm)
    reach = JUNCTION_REACH_M / unit_m
    lo, hi = sorted((o["o0"], o["o1"]))
    found = {}
    for side, s_at in (("start", o["s0"]), ("end", o["s1"])):
        ids = []
        for s in segments:
            if s["layer"] not in wall_layers:
                continue
            (sa, oa), (sb, ob) = _frame(o, s["a"]), _frame(o, s["b"])
            L = math.dist(s["a"], s["b"])
            if L <= 0 or abs(sb - sa) > PERP_COS * L:      # not across the band axis
                continue
            if abs((sa + sb) / 2 - s_at) > tol:
                continue
            ids.append((s["id"], min(oa, ob), max(oa, ob)))
        # the crossing wall continues on BOTH sides of the band: a face piece leaving the band's low face outward by
        # at least the reach, and one leaving its high face outward (one piece through the band also counts)
        below = [sid for sid, a, b in ids if a <= lo - reach and b >= lo - tol]
        above = [sid for sid, a, b in ids if b >= hi + reach and a <= hi + tol]
        if not below or not above:  # (strictly beyond: a <= lo - reach)
            return None
        found[side] = sorted(set(below) | set(above))
    return found


def census(segments, unit_m, wall_layers, columns=(), *, window_layers=(), swings=None, heights=None,
           floor_m=FLOOR_M, tol="UNIT_RELATIVE", geom_factory=None, region_id="PLAN"):
    if unit_m is None or not unit_m > 0:
        raise ValueError("UNITS_MISSING: metres per drawing unit not established; nothing is measured")
    heights = dict(heights or {})
    wall_layers = sorted(wall_layers)
    window_layers = set(window_layers)
    eng, _rej = _openings(segments, unit_m, wall_layers, columns, ENGINE_MIN_GAP_M, tol, geom_factory, region_id)
    probe, _rej2 = _openings(segments, unit_m, wall_layers, columns, floor_m, tol, geom_factory, region_id)
    same = SAME_M / unit_m

    def is_engine(p):
        return any(e["band_id"] == p["band_id"] and abs(e["s0"] - p["s0"]) <= same and abs(e["s1"] - p["s1"]) <= same
                   for e in eng)

    served = {}
    if swings:
        from engine.source import arch_rooms as AR
        served = AR.match_swings(probe, swings, unit_m)
    recs = []
    n = 0
    for p in sorted(probe, key=lambda x: (x["band_id"], x["s0"])):
        w = p["width_m"]
        base = {"band_id": p["band_id"], "layer": p["layer"], "width_m": round(w, 6), "wall_t_m": round(p["wall_t_m"], 6),
                "start_jamb": p["start_jamb"], "end_jamb": p["end_jamb"], "split_at_column": p["split_at_column"]}
        if w >= ENGINE_MIN_GAP_M:
            recs.append(dict(base, probe_id=None, cls="ENGINE_OPENING" if is_engine(p) else "PROBE_ONLY_WIDE",
                             status="ENGINE" if is_engine(p) else "HELD", evidence={}))
            continue
        n += 1
        pid = f"SG-{n:03d}"
        glz, gids = _glazing_m(p, segments, window_layers, unit_m)
        door = (served.get(p["opening_id"]) or [None])[0]
        jn = _junction(p, segments, wall_layers, unit_m)
        if glz >= GLAZING_SHARE * w and glz > 0:
            cls, ev = "SMALL_WINDOW", {"glazing_m": round(glz, 6), "glazing_ids": gids}
        elif door is not None:
            cls, ev = "SMALL_DOOR", {"swing": door}
        elif jn is not None:
            cls, ev = "WALL_JUNCTION", {"crossing_faces": jn}
        else:
            cls, ev = "SUB_MIN_GAP_UNEXPLAINED", {}
        rec = dict(base, probe_id=pid, cls=cls, evidence=ev, height_m=None, deduct_m2=None)
        if cls in ("SMALL_WINDOW", "SMALL_DOOR"):
            h = heights.get(pid)
            if h is None:
                rec.update(status="DEDUCT_HEIGHT_HELD", reason="opening height not printed / scheduled: area HELD, "
                                                              "width measured; never 0")
            else:
                rec.update(status="DEDUCT_MEASURED", height_m=float(h), deduct_m2=round(w * float(h), 6))
        elif cls == "WALL_JUNCTION":
            rec.update(status="NOT_AN_OPENING", reason="a crossing wall runs through the band: continuous masonry")
        else:
            rec.update(status="HELD", reason="jambed gap with no window, door or junction evidence: masonry over this "
                                             "width x height is a named range, never deducted or kept silently")
        recs.append(rec)
    small = [r for r in recs if r["probe_id"]]
    summ = {"policy": POLICY, "engine_min_gap_m": ENGINE_MIN_GAP_M, "floor_m": floor_m,
            "engine_openings": len(eng), "probe_gaps": len(probe),
            "probe_only_wide": sum(r["cls"] == "PROBE_ONLY_WIDE" for r in recs),
            "sub_min": len(small),
            "by_class": {c: sum(r["cls"] == c for r in small) for c in
                         ("SMALL_WINDOW", "SMALL_DOOR", "WALL_JUNCTION", "SUB_MIN_GAP_UNEXPLAINED")},
            "deduct_measured_m2": round(sum(r["deduct_m2"] for r in small if r["deduct_m2"] is not None), 6),
            "deduct_width_height_held_m": round(sum(r["width_m"] for r in small if r["status"] == "DEDUCT_HEIGHT_HELD"), 6),
            "lost_by_engine": sum(r["cls"] in ("SMALL_WINDOW", "SMALL_DOOR") for r in small)}
    return {"records": recs, "summary": summ, "engine_openings": [o["opening_id"] for o in eng]}


def wall_deduction(gross_m2, records, faces=1):
    """net masonry / finish area of one wall after the small openings of this census (per face for finishes):
    -> {"net_m2", "net_low_m2", "state"}; a height-HELD opening keeps the net a range (state HELD), never 0."""
    if gross_m2 is None:
        return {"net_m2": None, "net_low_m2": None, "state": "HELD"}
    known = sum(r["deduct_m2"] for r in records if r.get("status") == "DEDUCT_MEASURED") * faces
    held = [r for r in records if r.get("status") in ("DEDUCT_HEIGHT_HELD", "HELD")]
    net = gross_m2 - known
    if held:
        return {"net_m2": round(net, 6), "net_low_m2": None, "state": "HELD",
                "held": [r["probe_id"] for r in held]}
    return {"net_m2": round(net, 6), "net_low_m2": round(net, 6), "state": "MEASURED"}

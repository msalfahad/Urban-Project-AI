"""EXCAVATION_LEDGER_V1 (T-170, research, unwired, stdlib only): excavation / backfill ledger per footing pit and per
ground-beam / strap trench, built only from PRINTED levels and PRINTED dimensions; every link that is not printed is
HELD by name, never a default and never 0.

Physical element (ERS s.2.1). For each isolated footing the earthwork is a pit dug from the EXISTING GROUND down to the
EXCAVATION FORMATION; in it sit, bottom up: the plain-concrete blinding (thickness t_b, projecting p beyond the footing
on every side), the underlay (protection screed + membrane, thickness u), the footing (L x W x H), then the neck and,
near the top, the ground beams; the rest of the pit is BACKFILL. The level chain (owner Q-21 C: existing ground,
formation, blinding bottom / top, footing bottom / top, neck start / end, finished levels, never "subtract 10 cm"):

    formation F                      (HELD unless printed as a value; a printed MINIMUM depth is a bound, not a value)
    blinding top     = F + t_b
    footing bottom   = F + t_b + u
    footing top      = F + t_b + u + H
    excavation depth D = EG - F      (EG: existing ground at the pit; a sloping EG uses the four corner values)

Quantities kept apart (ERS s.3): the NEAT pit plan (blinding extent (L + 2p) x (W + 2p): the smallest hole the printed
detail needs), the WORKING-SPACE plan ((L + 2p + 2ws) x (W + 2p + 2ws): ws is a method / specification fact, HELD
unless stated, UP-EXC-001 / OQ-13), the excavation VOLUME (plan x D), the buried-structure volumes that displace soil
(blinding, underlay, footing, neck, ground beam) and BACKFILL (excavation - buried structure below EG). Disposal =
excavation - backfill re-used is a separate line, never computed here.

Pit overlaps (defect L-N10-03): neat plans that really intersect are reported with their intersection area (an
excavation counted twice if pits are summed); for every neighbouring pair the working space at which the two pits
would start to merge is w* = max(gap_x, gap_y) / 2 (axis-aligned outlines), so the overlap is a FACT of the drawing
for any working space the owner / specification later fixes, not an assumption.

Volumes for a sloping existing ground: with EG known at the four corners of a rectangular pit and EG planar over it,
the volume is exactly plan x (mean corner EG - F) (the mean of a plane's corner values is its centroid value).
"""
from __future__ import annotations

METHOD_ID = "EXCAVATION_LEDGER_V1"
DRAWING_CONFIRMED, HELD, UNKNOWN = "DRAWING-CONFIRMED", "HELD", "UNKNOWN"
_UNIT = {"m": 1.0, "cm": 0.01, "mm": 0.001}


class LedgerError(ValueError):
    pass


def to_m(value, unit):
    """A printed number with its declared unit -> metres; an undeclared unit is refused (never guessed)."""
    if value is None:
        return None
    if unit not in _UNIT:
        raise LedgerError(f"UNIT_NOT_DECLARED: {unit!r}")
    return float(value) * _UNIT[unit]


def _r(x, n=6):
    return None if x is None else round(x, n)


def _fact(d, key):
    """A level / dimension fact is {"value": float, "status": ..., "ref": ...}; a bound is {"bound": "AT_MOST", ...}."""
    v = (d or {}).get(key)
    if v is None:
        return None, f"{key.upper()}_NOT_PRINTED"
    if v.get("value") is None:
        why = f"{key.upper()}_ONLY_A_BOUND ({v.get('bound')} {v.get('limit')})" if v.get("bound") else \
            f"{key.upper()}_NOT_PRINTED"
        return None, why
    return float(v["value"]), None


def neat_rect(f, proj):
    """Axis-aligned neat pit rectangle (x0, y0, x1, y1) in m: the drawn footing outline grown by the blinding
    projection; None when the projection is not printed for this footing's detail."""
    if proj is None:
        return None
    x0, y0 = f["x0_m"], f["y0_m"]
    return (x0 - proj, y0 - proj, x0 + f["dx_m"] + proj, y0 + f["dy_m"] + proj)


def footing_pit(f, levels):
    """One pit row. f: {id, type, L_m, W_m, H_m, x0_m, y0_m, dx_m, dy_m, detail}; levels: {detail_name: {blinding_m,
    underlay_m, projection_m}, "formation": fact, "existing_ground": fact or {"corners": [4 facts]},
    "working_space_m": fact, "neck": {id: fact m3}}."""
    det = (levels.get("details") or {}).get(f.get("detail"))
    held = []
    if det is None:
        held.append("FOOTING_DETAIL_NOT_IDENTIFIED")
        det = {}
    tb, u, p = det.get("blinding_m"), det.get("underlay_m"), det.get("projection_m")
    for k, v in (("BLINDING_THICKNESS", tb), ("UNDERLAY", u), ("BLINDING_PROJECTION", p)):
        if v is None:
            held.append(f"{k}_NOT_PRINTED")
    L, W, H = f.get("L_m"), f.get("W_m"), f.get("H_m")
    if None in (L, W, H):
        held.append("FOOTING_SIZE_NOT_PRINTED")
    if f.get("conflict"):
        held.append("FOOTING_CONFLICT: " + f["conflict"])
    ok_size = None not in (L, W, H) and not f.get("conflict")
    footprint = L * W if ok_size else None
    neat = (L + 2 * p) * (W + 2 * p) if ok_size and p is not None else None
    ws, ws_why = _fact(levels, "working_space_m")
    plan_ws = (L + 2 * p + 2 * ws) * (W + 2 * p + 2 * ws) if neat is not None and ws is not None else None
    # level chain above formation (relative; DRAWING-CONFIRMED where every link is printed)
    rel = {"blinding_top": tb, "footing_bottom": (tb + u) if None not in (tb, u) else None,
           "footing_top": (tb + u + H) if None not in (tb, u, H) else None}
    F, f_why = _fact(levels, "formation")
    eg_mean, eg_why = _existing_ground(levels, f["id"])
    D = (eg_mean - F) if None not in (eg_mean, F) else None
    if D is not None and D <= 0:
        raise LedgerError(f"FORMATION_NOT_BELOW_EXISTING_GROUND at {f['id']}: D = {D}")
    lim = (levels.get("formation") or {}).get("limit")
    if F is not None and lim is not None and (levels["formation"].get("bound") == "AT_MOST") and F > lim + 1e-9:
        raise LedgerError(f"FORMATION_ABOVE_PRINTED_LIMIT at {f['id']}: {F} > {lim}")
    absolute = {k: (_r(F + v) if None not in (F, v) else None) for k, v in rel.items()}
    blinding_m3 = neat * tb if None not in (neat, tb) else None
    underlay_m3 = footprint * u if None not in (footprint, u) else None
    footing_m3 = footprint * H if footprint is not None else None
    neck = ((levels.get("neck") or {}).get(f["id"]) or {}).get("value")
    vol = plan = None
    why_v = []
    if neat is None:
        why_v.append("NEAT_PLAN_HELD")
    if ws is None:
        why_v.append(ws_why)
    if D is None:
        why_v += [w for w in (f_why, eg_why) if w]
    if not why_v:
        plan = plan_ws
        vol = plan * D
    backfill = None
    why_b = list(why_v)
    if neck is None:
        why_b.append("NECK_VOLUME_HELD (neck ends: T-205 R-NECK-ENDS-1)")
    if not f.get("gb_in_pit_m3_known"):
        why_b.append("GROUND_BEAM_PART_IN_PIT_HELD")
    if vol is not None and not why_b[len(why_v):]:
        backfill = vol - (blinding_m3 + underlay_m3 + footing_m3 + neck + f.get("gb_in_pit_m3", 0.0))
    return {
        "id": f["id"], "kind": "PIT", "type": f.get("type"), "outline": f.get("outline"),
        "footprint_m2": _r(footprint), "neat_plan_m2": _r(neat),
        "neat_status": DRAWING_CONFIRMED if neat is not None else HELD,
        "working_space_plan_m2": _r(plan_ws),
        "above_formation_m": {k: _r(v) for k, v in rel.items()},
        "absolute_m": absolute,
        "depth_m": _r(D), "existing_ground_mean_m": _r(eg_mean),
        "excavation_m3": _r(vol), "excavation_status": DRAWING_CONFIRMED if vol is not None else HELD,
        "excavation_why": "; ".join(why_v) or None,
        "m3_per_m_depth_neat": _r(neat),
        "buried": {"blinding_m3": _r(blinding_m3), "underlay_m3": _r(underlay_m3), "footing_m3": _r(footing_m3),
                   "neck_m3": _r(neck)},
        "backfill_m3": _r(backfill), "backfill_status": DRAWING_CONFIRMED if backfill is not None else HELD,
        "backfill_why": "; ".join(why_b) or None,
        "held": held,
    }


def _existing_ground(levels, fid):
    eg = levels.get("existing_ground")
    per = (levels.get("existing_ground_at") or {}).get(fid)
    src = per if per is not None else eg
    if src is None:
        return None, "EXISTING_GROUND_NOT_PRINTED"
    if "corners" in src:
        vals = [c.get("value") if c else None for c in src["corners"]]
        if len(vals) != 4 or any(v is None for v in vals):
            return None, "EXISTING_GROUND_CORNER_MISSING"
        return sum(vals) / 4.0, None
    if src.get("value") is None:
        return None, "EXISTING_GROUND_NOT_PRINTED"
    return float(src["value"]), None


def trench(g, levels):
    """A ground-beam / strap trench: length x (b + 2p); depth from EG to the beam's blinding bottom (GB bottom - t_b),
    HELD while the GB top / depth is not printed."""
    det = (levels.get("details") or {}).get(g.get("detail")) or {}
    p, tb = det.get("projection_m"), det.get("blinding_m")
    b, L, d = g.get("width_m"), g.get("length_m"), g.get("depth_m")
    held = []
    if p is None:
        held.append("BLINDING_PROJECTION_NOT_PRINTED")
    if b is None or L is None:
        held.append("WIDTH_OR_LENGTH_NOT_IN_THE_INPUT")
    neat = L * (b + 2 * p) if None not in (L, b, p) else None
    top = (g.get("top") or {}).get("value")
    why = []
    if top is None:
        why.append("GB_TOP_NOT_PRINTED (FFL +1.00 minus an unprinted build-up; T-200 / T-206)")
    if d is None:
        why.append("GB_DEPTH_NOT_ESTABLISHED (" + (g.get("depth_why") or "not printed") + ")")
    if tb is None:
        why.append("BLINDING_THICKNESS_NOT_PRINTED")
    eg, eg_why = _existing_ground(levels, g["id"])
    if eg is None:
        why.append(eg_why)
    depth = (eg - (top - d - tb)) if not why else None
    vol = neat * depth if None not in (neat, depth) else None
    return {"id": g["id"], "kind": g.get("kind", "TRENCH"), "mark": g.get("mark"), "length_m": _r(L),
            "width_m": _r(b), "neat_plan_m2": _r(neat), "neat_status": DRAWING_CONFIRMED if neat is not None else HELD,
            "depth_m": _r(depth), "excavation_m3": _r(vol),
            "excavation_status": DRAWING_CONFIRMED if vol is not None else HELD,
            "excavation_why": "; ".join(why + held) or None, "held": held}


def overlaps(footings, levels, w_report_m=1.0):
    """Pairs of pits: real neat-plan intersections (m2) and the working space w* at which two pits start to merge."""
    rects, by_id = [], {f["id"]: f for f in footings}
    for f in footings:
        det = (levels.get("details") or {}).get(f.get("detail")) or {}
        r = neat_rect(f, det.get("projection_m"))
        if r is not None and not f.get("conflict"):
            rects.append((f["id"], r))
    out = []
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            (a, ra), (b, rb) = rects[i], rects[j]
            ix = min(ra[2], rb[2]) - max(ra[0], rb[0])
            iy = min(ra[3], rb[3]) - max(ra[1], rb[1])
            if ix > 1e-9 and iy > 1e-9:
                fa, fb = by_id[a], by_id[b]
                fx = min(fa["x0_m"] + fa["dx_m"], fb["x0_m"] + fb["dx_m"]) - max(fa["x0_m"], fb["x0_m"])
                fy = min(fa["y0_m"] + fa["dy_m"], fb["y0_m"] + fb["dy_m"]) - max(fa["y0_m"], fb["y0_m"])
                out.append({"a": a, "b": b, "neat_overlap_m2": _r(ix * iy), "w_star_m": 0.0,
                            "footing_overlap_m2": _r(fx * fy) if fx > 1e-9 and fy > 1e-9 else 0.0})
                continue
            gx, gy = max(0.0, -ix), max(0.0, -iy)
            w = max(gx, gy) / 2.0
            if w <= w_report_m:
                out.append({"a": a, "b": b, "neat_overlap_m2": 0.0, "w_star_m": _r(w, 4), "footing_overlap_m2": 0.0})
    return sorted(out, key=lambda o: (o["w_star_m"], o["a"], o["b"]))


def ledger(footings, beams, levels):
    pits = [footing_pit(f, levels) for f in footings]
    trs = [trench(g, levels) for g in beams]
    ov = overlaps(footings, levels)
    rows = pits + trs

    def tot(key, status_key):
        dc = [r[key] for r in rows if r.get(status_key) == DRAWING_CONFIRMED and r.get(key) is not None]
        # no confirmed line -> None (BLANK), never 0
        return {"DRAWING-CONFIRMED": _r(sum(dc)) if dc else None, "lines": len(dc),
                "HELD_lines": sum(1 for r in rows if r.get(status_key) != DRAWING_CONFIRMED)}
    neat_overlap = sum(o["neat_overlap_m2"] for o in ov)
    foot_overlap = sum(o["footing_overlap_m2"] for o in ov)
    return {"method": METHOD_ID, "pits": pits, "trenches": trs, "overlaps": ov,
            "totals": {"neat_plan_m2": tot("neat_plan_m2", "neat_status"),
                       "neat_overlap_m2": _r(neat_overlap), "footing_overlap_m2": _r(foot_overlap),
                       "excavation_m3": tot("excavation_m3", "excavation_status"),
                       "backfill_m3": tot("backfill_m3", "backfill_status")}}

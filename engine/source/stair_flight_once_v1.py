"""STAIR FLIGHT ONCE V1 - each stair flight is measured on ONE storey: a flight drawn again on the plan above is listed,
never measured twice, and never silently dropped.

    flights_once(plans, *, unit_m, section_risers=None) -> record

Opt-in, not wired: no method version reads it (ARCH_TAKEOFF_V2.9 .. V2.13 and arch_rooms.cross_plan_flights are
untouched). It re-reads what the released route already found - the flights of every plan (arch_rooms.stair_flights
records) and the plan-to-plan alignment - and decides, for each flight that lies over a flight of the plan below,
which storey the flight belongs to: the storey whose floor it LEAVES (owner Q-62 A cond: each element once).

Why: arch_rooms.cross_plan_flights types a flight lying over a flight of the plan below as STACKED (counted again, "a
stair core") whenever no void mark is near it. A plan of the top storey of a dog-leg stair draws the two flights of the
storey below for orientation (under the cut line, seen through the stair opening); STACKED then counts them twice.

THE DECISION, per flight g of plan p that lies over a flight f of plan p - 1 (after the alignment; the shared tread
area exceeds PAIR_SHARE of the smaller flight - the same test as STAIR_SAME_FLIGHT of the released route):

1. STOREY OF g, from the drawing only, in this order:
   a. LEVELS printed at g's ends (a level mark within END_REACH_M of an end line, nearer that end than the other):
      a level below this plan's floor (and not below the plan below's floor) -> g belongs to the storey below
      (BELOW: it arrives at this floor); a level above this plan's floor -> g leaves this floor (OWN).
      A mark equal to the plan's own floor level sets nothing (the arrival landing and the foot of the next flight
      both carry it).
   b. THE SLAB ABOVE plan p (the structural slab plan of that storey's roof / floor), given as evidence:
         NONE_DRAWN  the slab plan above draws no stair and no stair opening: nothing rises from this floor -> BELOW
         DRAWN_AT    the stair panels / openings it draws, as polygons in this plan's drawing units: g's footprint
                     inside one (>= COVER_SHARE) -> a stair rises here (OWN); outside all of them -> BELOW
         DRAWN       a stair is drawn above but not located on this plan: OWN only when g is a DIFFERENT flight from
                     f (the match of step 2 fails: another flight in the same place, under a slab that carries a
                     stair); when g repeats f exactly the drawing does not say which -> HELD
         NOT_READ / missing -> no evidence
   c. no evidence -> HELD (STOREY_NOT_SET), never counted, never dropped.
2. A BELOW flight is the same flight seen from above only if it matches f EXACTLY: the same number of treads, every
   footprint corner within MATCH_TOL_M of f's after the alignment, and f itself COUNTED on plan p - 1 (plans are
   decided bottom-up). Then g is SEEN_ABOVE: 0 here, measured once on plan p - 1 (the line names f). Any difference
   (another tread count, a shifted outline, f held or itself a repeat, f already matched by another flight) -> HELD:
   a range low 0 .. high the flight's own value, with every reason; never 0 and never counted twice.
3. A flight that lies over nothing below keeps the released reading (COUNTED), unless its printed end levels put it in
   the storey below: then it is HELD (NO_MATCH_BELOW: the stair of the storey below is not drawn on its own plan).
   A flight the released route already reads SEEN_THROUGH_VOID (drawn_on_plan_below) stays exposure as released.

Quantities per flight: tread marble m2 = sum of the tread polygons (UP-STAIR-003, as released), step lm = sum of the
step widths (UP-STAIR-008, as released). The record gives them before (the released reading: COUNTED and STACKED
counted, SEEN_THROUGH_VOID as exposure) and after (COUNTED only; HELD as a range; SEEN_ABOVE 0 with its reference).
Optional section_risers {storey: risers} (owner Q-46 A: the section counts) is compared with the riser lines the
storey's own flights draw; the difference is listed, nothing is changed by it.

Rules: Q-46 A, Q-62 A cond, Q-66 B / Q-70 A cond (landings are not flights: untouched here), UP-STAIR-002 (stair
geometry from the drawing), UP-STAIR-003, UP-STAIR-008, UP-QTY-STATUS-001 (released / held / unsupported; missing is
never 0). Project-agnostic: no layer name, room name, level or coordinate of any project; works in any drawing unit
(unit_m), under any rotation or mirror of the drawing (only distances and areas are used).
"""

from __future__ import annotations

import math

from shapely.geometry import Polygon
from shapely.ops import unary_union

METHOD_ID = "STAIR_FLIGHT_ONCE_V1"
PAIR_SHARE = 0.6           # shared tread area / smaller flight's: the flight lies over the one below (released value)
MATCH_TOL_M = 0.01         # every footprint corner within this of the lower flight's: the same outline
END_REACH_M = 1.50         # a level mark this close to a flight's end line is a level of that end
LEVEL_TOL_M = 0.005        # two levels closer than this are the same level
COVER_SHARE = 0.5          # a flight this much inside a stair panel / opening of the slab above lies under it

COUNTED, SEEN_ABOVE, HELD, EXPOSURE = "COUNTED", "SEEN_ABOVE", "HELD", "SEEN_THROUGH_VOID"
OWN, BELOW = "OWN", "BELOW"


def _poly(points):
    p = Polygon(points)
    return p if p.is_valid else p.buffer(0)


def _treads(fl):
    return unary_union([_poly(q) for q in fl.get("tread_quads") or () if len(q) >= 3])


def _moved(points, off):
    return [(x - off[0], y - off[1]) for x, y in points]


def _ends(fl):
    """the two end lines of a flight's footprint (first and last tread line), drawing units. Straight flights carry a
    4-corner footprint [(u0,n0), (u1,n0), (u1,n1), (u0,n1)]; a radial one inner + outer[::-1]."""
    fp = fl["footprint"]
    if fl.get("kind") == "RADIAL":
        n = len(fp) // 2
        return (fp[0], fp[-1]), (fp[n - 1], fp[n])
    return (fp[0], fp[1]), (fp[2], fp[3])


def _dist_seg(q, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((q[0] - ax) * dx + (q[1] - ay) * dy) / L))
    return math.hypot(q[0] - ax - t * dx, q[1] - ay - t * dy)


def end_levels(fl, marks, unit_m):
    """the printed levels at each end of a flight: [levels at end A, levels at end B] (metres)."""
    ea, eb = _ends(fl)
    reach = END_REACH_M / unit_m
    out = ([], [])
    for m in marks or ():
        q = (m["x"], m["y"])
        da, db = _dist_seg(q, *ea), _dist_seg(q, *eb)
        k = 0 if da < db else 1 if db < da else None
        if k is not None and min(da, db) <= reach:
            out[k].append(float(m["value_m"]))
    return out


def _level_storey(levels, level, below_level):
    """BELOW / OWN / None from the printed end levels of a flight on a plan at `level`."""
    flat = [v for end in levels for v in end]
    if any(v < level - LEVEL_TOL_M and (below_level is None or v >= below_level - LEVEL_TOL_M) for v in flat):
        return BELOW, [v for v in flat if v < level - LEVEL_TOL_M]
    if any(v > level + LEVEL_TOL_M for v in flat):
        return OWN, [v for v in flat if v > level + LEVEL_TOL_M]
    return None, flat


def _corner_shift(fp_a, fp_b):
    """the largest distance from a corner of either footprint to the nearest corner of the other (drawing units)."""
    if not fp_a or not fp_b:
        return math.inf
    one = max(min(math.dist(p, q) for q in fp_b) for p in fp_a)
    two = max(min(math.dist(p, q) for q in fp_a) for p in fp_b)
    return max(one, two)


def _values(fl):
    return round(sum(fl.get("tread_areas_m2") or ()), 6), round(sum(fl.get("step_widths_m") or ()), 6)


def _pair(g, lower, off):
    """the flight of the plan below that g lies over (largest shared tread share > PAIR_SHARE), with that share."""
    tg = _treads({"tread_quads": [_moved(q, off) for q in g.get("tread_quads") or ()]})
    best, share = None, 0.0
    for f in lower:
        tf = _treads(f)
        small = min(tg.area, tf.area)
        if small <= 0:
            continue
        s = tg.intersection(tf).area / small
        if s > share:
            best, share = f, s
    return (best, share) if best is not None and share > PAIR_SHARE else (None, share)


def _slab_storey(slab, g_fp, exact):
    """BELOW / OWN / HELD-reason / None from the slab-above evidence of the plan."""
    state = (slab or {}).get("state") or "NOT_READ"
    src = (slab or {}).get("source") or ""
    if state == "NONE_DRAWN":
        return BELOW, f"SLAB_ABOVE_DRAWS_NO_STAIR: {src}".rstrip(": ")
    if state == "DRAWN_AT":
        polys = [_poly(p) for p in slab.get("polygons") or () if len(p) >= 3]
        fp = _poly(g_fp)
        inside = max((fp.intersection(p).area / fp.area for p in polys), default=0.0) if fp.area > 0 else 0.0
        if inside >= COVER_SHARE:
            return OWN, f"STAIR_DRAWN_IN_SLAB_ABOVE_AT_THE_FLIGHT ({100 * inside:.0f} % under it): {src}".rstrip(": ")
        return BELOW, f"SLAB_ABOVE_DRAWS_NO_STAIR_AT_THE_FLIGHT ({100 * inside:.0f} % under a stair panel): {src}" \
            .rstrip(": ")
    if state == "DRAWN":
        if exact:
            return "HELD", (f"STAIR_DRAWN_IN_SLAB_ABOVE_NOT_LOCATED: the flight repeats the one below exactly and the "
                            f"slab above carries a stair somewhere - a core or the same flight seen from above: {src}"
                            ).rstrip(": ")
        return OWN, (f"STAIR_DRAWN_IN_SLAB_ABOVE (not located) and the flight differs from the one below: another "
                     f"flight in the same place, rising from this floor: {src}").rstrip(": ")
    return None, None


def flights_once(plans, *, unit_m, section_risers=None):
    """plans (storey order, lowest first): [{"floor", "level_m", "flights": [flight records in drawing units: flight_id,
    kind, footprint, tread_quads, tread_areas_m2, step_widths_m, tread_lines, optional drawn_on_plan_below],
    "level_marks": [{"x", "y", "value_m"}], "slab_above": {"state", "polygons", "source"} or None,
    "offset_to_below": (dx, dy) or None}] - offset_to_below carries this plan onto the plan below (lower = this - d,
    the released floor_offset of the column grid); None = not aligned (no pairing: every flight keeps its reading).
    -> {"method", "flights": [...], "totals": {...}, "section_check": [...], "warnings": [...]}"""
    rows, warnings = [], []
    state_of = {}                                  # (floor, flight_id) -> state, decided bottom-up
    matched = set()                                # lower flights already taken by a SEEN_ABOVE
    for i, P in enumerate(plans):
        floor, level = P["floor"], P.get("level_m")
        below = plans[i - 1] if i > 0 else None
        below_level = below.get("level_m") if below else None
        off = P.get("offset_to_below")
        lower = [f for f in (below or {}).get("flights") or ()] if below and off is not None else []
        if below and off is None and P.get("flights"):
            warnings.append(f"NOT_ALIGNED: {floor} is not aligned on {below['floor']}; its flights keep their reading")
        for g in P.get("flights") or ():
            fid = g.get("flight_id")
            tread, step = _values(g)
            levels = end_levels(g, P.get("level_marks"), unit_m)
            row = {"floor": floor, "flight_id": fid, "kind": g.get("kind"), "treads": len(g.get("tread_areas_m2") or ()),
                   "tread_m2": tread, "step_lm": step, "end_levels_m": [sorted(set(e)) for e in levels],
                   "released_reading": EXPOSURE if g.get("drawn_on_plan_below") else
                   ("STACKED" if g.get("stacked_over") else "SINGLE"), "reasons": [], "evidence": []}
            if g.get("drawn_on_plan_below"):
                row.update(state=EXPOSURE, storey=(g["drawn_on_plan_below"] or {}).get("floor"), counted_tread_m2=None,
                           counted_step_lm=None, held=None)
                row["evidence"].append("released SEEN_THROUGH_VOID: exposure, measured on the plan below (unchanged)")
                rows.append(row)
                state_of[(floor, fid)] = EXPOSURE
                continue
            f, share = _pair(g, lower, off) if lower else (None, 0.0)
            exact, shift_m = False, None
            if f is not None:
                shift_m = _corner_shift(_moved(g["footprint"], off), f["footprint"]) * unit_m
                same_n = len(g.get("tread_areas_m2") or ()) == len(f.get("tread_areas_m2") or ())
                exact = same_n and shift_m <= MATCH_TOL_M
                row.update(over=f.get("flight_id"), over_share=round(share, 4), outline_shift_m=round(shift_m, 4),
                           over_treads=len(f.get("tread_areas_m2") or ()))
            lv, lv_vals = _level_storey(levels, level, below_level) if level is not None else (None, [])
            storey_by, why = None, None
            if lv:
                storey_by = lv
                why = (f"PRINTED_END_LEVEL {', '.join(f'{v:+.2f}' for v in lv_vals)} "
                       f"{'below' if lv == BELOW else 'above'} this floor {level:+.2f}")
            elif f is not None:
                storey_by, why = _slab_storey(P.get("slab_above"), g["footprint"], exact)
            if f is None:
                if storey_by == BELOW:
                    row["reasons"].append(f"NO_MATCH_BELOW: {why}, and no flight of the plan below lies under it")
                    _held(row)
                else:
                    row.update(state=COUNTED, storey=floor, counted_tread_m2=tread, counted_step_lm=step, held=None)
                    row["evidence"].append(why or "lies over no flight of the plan below: released reading kept")
            elif storey_by == OWN:
                row.update(state=COUNTED, storey=floor, counted_tread_m2=tread, counted_step_lm=step, held=None)
                row["evidence"].append(why)
            elif storey_by == BELOW:
                row["evidence"].append(why)
                key = (below["floor"], f.get("flight_id"))
                miss = []
                if len(g.get("tread_areas_m2") or ()) != len(f.get("tread_areas_m2") or ()):
                    miss.append(f"STEP_COUNT_DIFFERS: {len(g.get('tread_areas_m2') or ())} treads here, "
                                f"{len(f.get('tread_areas_m2') or ())} on {below['floor']}")
                if shift_m > MATCH_TOL_M:
                    miss.append(f"OUTLINE_SHIFT {shift_m:.3f} m > {MATCH_TOL_M} m")
                if state_of.get(key) != COUNTED:
                    miss.append(f"LOWER_COPY_NOT_COUNTED: {f.get('flight_id')} is {state_of.get(key) or 'unknown'} on "
                                f"{below['floor']}")
                if key in matched:
                    miss.append(f"LOWER_FLIGHT_ALREADY_MATCHED: {f.get('flight_id')} is seen above by another flight")
                if miss:
                    row["reasons"] += miss
                    _held(row, storey=below["floor"])
                else:
                    matched.add(key)
                    row.update(state=SEEN_ABOVE, storey=below["floor"], counted_tread_m2=0.0, counted_step_lm=0.0,
                               held=None, measured_on=f"{below['floor']} {f.get('flight_id')}")
                    row["evidence"].append(f"same flight as {f.get('flight_id')} of {below['floor']}: "
                                           f"{row['treads']} treads, outline within {shift_m:.4f} m")
            else:
                row["reasons"].append(why if storey_by == "HELD" else
                                      "STOREY_NOT_SET: no printed level at its ends and no slab-above evidence; it "
                                      "lies over a flight of the plan below (a core or the same flight seen from above)")
                _held(row)
            state_of[(floor, fid)] = row["state"]
            rows.append(row)
    return {"method": METHOD_ID, "flights": rows, "totals": _totals(rows),
            "section_check": _section_check(rows, section_risers), "warnings": warnings}


def _held(row, storey=None):
    row.update(state=HELD, storey=storey, counted_tread_m2=None, counted_step_lm=None,
               held={"tread_m2": {"low": 0.0, "high": row["tread_m2"]}, "step_lm": {"low": 0.0, "high": row["step_lm"]}})


def _totals(rows):
    def s(key, pred):
        return round(sum(r[key] for r in rows if pred(r)), 6)
    released = lambda r: r["released_reading"] != EXPOSURE        # noqa: E731
    out = {"before": {"tread_m2": s("tread_m2", released), "step_lm": s("step_lm", released)},
           "after_counted": {"tread_m2": s("tread_m2", lambda r: r["state"] == COUNTED),
                             "step_lm": s("step_lm", lambda r: r["state"] == COUNTED)},
           "seen_above_removed": {"tread_m2": s("tread_m2", lambda r: r["state"] == SEEN_ABOVE),
                                  "step_lm": s("step_lm", lambda r: r["state"] == SEEN_ABOVE)},
           "held_high": {"tread_m2": s("tread_m2", lambda r: r["state"] == HELD),
                         "step_lm": s("step_lm", lambda r: r["state"] == HELD)},
           "exposure_unchanged": {"tread_m2": s("tread_m2", lambda r: r["state"] == EXPOSURE),
                                  "step_lm": s("step_lm", lambda r: r["state"] == EXPOSURE)}}
    for k in ("tread_m2", "step_lm"):
        out["after_range_" + k] = [out["after_counted"][k], round(out["after_counted"][k] + out["held_high"][k], 6)]
        # conservation: every released m2 / lm is counted, removed as a repeat or held
        out["conservation_" + k] = round(out["before"][k] - out["after_counted"][k] - out["seen_above_removed"][k] -
                                         out["held_high"][k], 6)
    return out


def _section_check(rows, section_risers):
    """the riser lines each storey's own flights draw against the section's riser count (listed only).
    section_risers: {storey: risers} (every flight the storey measures) or {storey: {"risers": n, "flight_ids": [...]}}
    (one stair of the storey: the flights the section cuts)."""
    out = []
    for storey, spec in (section_risers or {}).items():
        n, ids = (spec["risers"], set(spec.get("flight_ids") or ())) if isinstance(spec, dict) else (spec, None)
        own = [r for r in rows if r["floor"] == storey and r["state"] in (COUNTED, HELD)
               and (r["storey"] in (storey, None)) and (ids is None or r["flight_id"] in ids)]
        drawn = sum(r["treads"] + 1 for r in own)
        out.append({"storey": storey, "section_risers": n, "plan_riser_lines_of_own_flights": drawn,
                    "difference": n - drawn, "flights": [r["flight_id"] for r in own],
                    "note": "listed only (owner Q-46 A: the section counts the steps; tread polygons stay the plan's)"})
    return out

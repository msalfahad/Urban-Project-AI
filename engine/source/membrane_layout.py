"""MEMBRANE LAYOUT (M9 S1) - exact roll plan of a RECTANGULAR wet room for one sheet membrane (generic; stdlib only).

    surfaces(room, *, upturn_h, doorways, doorway_detail)   -> the net waterproofed surfaces, one row per BOQ item
    plan(room, spec, *, constraints)                         -> roll plan + material result (material_result schema)

Net surfaces (UP-WP-002 v2.0.0, UP-WP-003 v1.1.0):
    FIN.WP.FLOOR     the room floor (inside the finished wall line)
    FIN.WP.DOORWAY   each doorway floor piece, door width x wall depth (outside the room polygon, so never in the floor)
    FIN.WP.UPTURN    upturn height x the full boundary, doorway segments included (no door deduction); when the
                     project detail puts the doorway 0.20 m inside the doorway piece (doorway_detail
                     UPTURN_WITHIN_DOORWAY_PIECE) the doorway segments leave the upturn and are billed once, in the piece
    doorway_detail NOT_ESTABLISHED (default) keeps both rows and raises DOORWAY_UPTURN_DETAIL_REQUIRED and
    DOORWAY_DOUBLE_COVERAGE_REVIEW; SEPARATE_RETURN keeps both rows (a vertical return / water stop is detailed).

Roll plan (constraints and spec values recorded in the result; nothing defaulted silently):
    floor     strips of the roll width along the chosen direction; n = 1 when the cross width fits one roll, else
              n = ceil((D - W) / (W - side_lap)) + 1 (each further 1.00 m strip adds 0.90 m with a 0.10 m lap); the last
              strip is trimmed lengthwise (the trim feeds the upturn lanes when it is wide enough); a strip longer than a
              roll is spliced with end laps
    upturn    a band (upturn height + side lap onto the floor membrane) cut as lanes across the roll width; each joint
              in a band run takes an end lap; a closed loop also laps at its closure
    doorway   door width x (wall depth + side lap onto the floor membrane); jamb returns and the water stop are the
              project detail (DOORWAY_UPTURN_DETAIL_REQUIRED), not invented here
    band (constraints band_planner MIN_SEGMENT_V2_5; ARCH_TAKEOFF_V2.5 only): a new band segment is the shortest
              (1 cm steps) whose lanes finish the band - one end lap per lane, not two - and a segment that would
              open a roll is weighed against filling the largest open roll tail first (fewest rolls, joints, membrane)
    corners / penetrations   counted and flagged (CORNER_TREATMENT_NOT_SPECIFIED / PENETRATION_DETAIL_NOT_SPECIFIED)
              unless the selected system defines them: never quantified by a guess
    rolls     full-width segments first-fit into whole rolls; an untouched roll tail is PACKAGING SURPLUS, not waste

Balance: rolls x roll area = net installed + overlap + cutting waste + reusable offcuts + packaging surplus.
Never: a fixed waste percentage, net / roll area as the roll count, a lap below the spec minimum.
Scope (S1): a rectangle; anything else is BLOCKED (POLYGON_OPTIMIZER_NOT_IMPLEMENTED, S2).
"""

from __future__ import annotations

import math

from engine.source import material_result as WP
from engine.source import plane_poly as PP
from engine.source.tile_layout import rectangle

METHOD = "MEMBRANE_RECT_EXACT_V1"
POLY_METHOD = "MEMBRANE_POLYGON_STRIPS_V1"
DOORWAY_DETAILS = ("NOT_ESTABLISHED", "SEPARATE_RETURN", "UPTURN_WITHIN_DOORWAY_PIECE")
DIRECTIONS = ("ALONG_X", "ALONG_Y", "MIN_MATERIAL")
# ARCH_TAKEOFF_V2.5 (constraints["band_planner"]): the band planner proven against the independent hand calculations
# of the Phase 2B-3 proof library; without the key every earlier method keeps the loop below unchanged
BAND_MIN_SEGMENT = "MIN_SEGMENT_V2_5"
EPS = 1e-6
POLYGON_BLOCK = "POLYGON_OPTIMIZER_NOT_IMPLEMENTED (S2): the S1 membrane engine lays rectangles only"


class MembraneError(ValueError):
    pass


def _ceil_cm(x):
    return math.ceil(round(x * 100.0, 6)) / 100.0


def surfaces(room, *, upturn_h, doorways=(), doorway_detail="NOT_ESTABLISHED"):
    """-> {"rows": [{item_code, net_m2, formula, inputs}], "perimeter_lm", "doorway_segments_lm", "upturn_lm",
    "flags", "runs"} or None when the room is not a rectangle."""
    if doorway_detail not in DOORWAY_DETAILS:
        raise MembraneError(f"doorway_detail {doorway_detail}")
    ab = rectangle(room)
    if ab is None:
        return None
    X, Y = ab
    P = 2.0 * (X + Y)
    dws = [dict(d) for d in doorways]
    for d in dws:
        if d.get("width_m") is None or d.get("depth_m") is None:
            raise MembraneError("a doorway needs width_m and depth_m (the wall depth at the opening)")
    door_lm = sum(d["width_m"] for d in dws)
    within = doorway_detail == "UPTURN_WITHIN_DOORWAY_PIECE"
    up_lm = P - door_lm if within else P
    rows = [{"item_code": "FIN.WP.FLOOR", "net_m2": X * Y, "formula": "length x width (inside the finished wall line)",
             "inputs": {"length_m": X, "width_m": Y}}]
    for i, d in enumerate(dws, 1):
        rows.append({"item_code": "FIN.WP.DOORWAY", "doorway": d.get("door_id") or f"D{i}",
                     "net_m2": d["width_m"] * d["depth_m"], "formula": "door width x wall depth",
                     "inputs": {"width_m": d["width_m"], "depth_m": d["depth_m"]}})
    rows.append({"item_code": "FIN.WP.UPTURN", "net_m2": up_lm * upturn_h,
                 "formula": ("(perimeter - doorway segments, billed in the doorway pieces) x upturn height" if within
                             else "full perimeter incl. doorway segments x upturn height (no door deduction)"),
                 "inputs": {"perimeter_lm": P, "doorway_segments_lm": door_lm, "upturn_lm": up_lm, "upturn_h_m": upturn_h}})
    flags = []
    if dws and doorway_detail == "NOT_ESTABLISHED":
        flags += ["DOORWAY_UPTURN_DETAIL_REQUIRED", "DOORWAY_DOUBLE_COVERAGE_REVIEW"]
    if within:
        flags += [f"DOORWAY_SEGMENT_BILLED_IN_DOORWAY_PIECE ({door_lm:g} lm)"]
        if any(d["depth_m"] < upturn_h - EPS for d in dws):
            flags.append("DOORWAY_PIECE_SHALLOWER_THAN_UPTURN")
    return {"rows": rows, "perimeter_lm": P, "doorway_segments_lm": door_lm, "upturn_lm": up_lm, "flags": flags,
            "runs": _runs(X, Y, dws, within), "sides": (X, Y)}


def _runs(X, Y, dws, within):
    """band runs: one closed loop, or (doorway segments excluded) the open runs between doorways. A doorway with
    position_lm (distance along the boundary from the origin corner, counter-clockwise) places its gap exactly;
    without positions the runs are one open run of the remaining length (flagged)."""
    P = 2.0 * (X + Y)
    if not within or not dws:
        return {"runs": [{"length_m": P, "closed": True}], "approximate": False}
    if all(d.get("position_lm") is not None for d in dws):
        gaps = sorted((d["position_lm"] % P, d["width_m"]) for d in dws)
        runs = []
        for i, (s, w) in enumerate(gaps):
            nxt = gaps[(i + 1) % len(gaps)][0] + (P if i + 1 == len(gaps) else 0.0)
            ln = nxt - (s + w)
            if ln < -EPS:
                raise MembraneError("doorways overlap along the boundary")
            if ln > EPS:
                runs.append({"length_m": ln, "closed": False})
        return {"runs": runs, "approximate": False}
    return {"runs": [{"length_m": P - sum(d["width_m"] for d in dws), "closed": False}], "approximate": len(dws) > 1}


class _Rolls:
    def __init__(self, W, L):
        self.W, self.L, self.used = W, L, []

    def cut(self, length, purpose):
        """a full-width segment from the first roll with room for it (first fit), else a new roll."""
        if length > self.L + EPS:
            raise MembraneError(f"a segment of {length} m is longer than the roll")
        for i, u in enumerate(self.used):
            if self.L - sum(x[0] for x in u) >= length - EPS:
                u.append((length, purpose))
                return i
        self.used.append([(length, purpose)])
        return len(self.used) - 1

    def records(self):
        return [{"roll": i + 1, "segments": [{"length_m": round(a, 4), "for": p} for a, p in u],
                 "cut_m": round(sum(a for a, _ in u), 6), "untouched_tail_m": round(self.L - sum(a for a, _ in u), 6)}
                for i, u in enumerate(self.used)]


def _strip_plan(L_s, D_c, W, L_r, side, end):
    n = 1 if D_c <= W + EPS else math.ceil((D_c - W) / (W - side) - EPS) + 1
    w_last = D_c - (n - 1) * (W - side)
    k = 1 if L_s <= L_r + EPS else math.ceil((L_s - L_r) / (L_r - end) - EPS) + 1
    lengths = [L_r] * (k - 1) + [L_s - (k - 1) * (L_r - end)] if k > 1 else [L_s]
    return n, w_last, k, lengths


def plan(room, spec, *, constraints):
    """constraints: upturn_h_m (required; UP-WP-002 v2.0.0 gives 0.20), doorways [{door_id, width_m, depth_m,
    position_lm?}], doorway_detail, direction (ALONG_X | ALONG_Y | MIN_MATERIAL, default MIN_MATERIAL),
    min_reusable_m (None: no offcut retained), penetrations (count, default 0), spare_allowance, rule_refs."""
    c = dict(constraints)
    if c.get("upturn_h_m") is None:
        raise MembraneError("constraints['upturn_h_m'] is required (the rule store gives UP-WP-002)")
    direction = c.get("direction", "MIN_MATERIAL")
    if direction not in DIRECTIONS:
        raise MembraneError(f"direction {direction}")
    sf = surfaces(room, upturn_h=c["upturn_h_m"], doorways=c.get("doorways", ()),
                  doorway_detail=c.get("doorway_detail", "NOT_ESTABLISHED"))
    loc = {k: room.get(k) for k in ("room_id", "floor", "name_en", "name_ar") if room.get(k) is not None}
    if sf is None:
        return WP.blocked(method=METHOD, spec=spec, reason=POLYGON_BLOCK, location=loc, line_id=room.get("line_id"),
                          rule_refs=c.get("rule_refs", ()))
    if direction == "MIN_MATERIAL":
        opts = [_one(sf, spec, c, d, loc, room) for d in ("ALONG_X", "ALONG_Y")]
        sel = min(opts, key=lambda r: (r["units"]["consumed_units"], round(r["consumed_m2"], 6),
                                       round(r["cutting_waste_m2"], 6), DIRECTIONS.index(r["layout"]["direction"])))
        sel["layout"]["alternatives"] = [{"direction": r["layout"]["direction"], "rolls": r["units"]["consumed_units"],
                                          "consumed_m2": r["consumed_m2"], "overlap_m2": r["overlap_m2"],
                                          "cutting_waste_m2": r["cutting_waste_m2"],
                                          "packaging_surplus_m2": r["packaging"]["packaging_surplus_m2"]} for r in opts]
        return sel
    return _one(sf, spec, c, direction, loc, room)


def _one(sf, spec, c, direction, loc, room, floor_fn=None, method=METHOD):
    X, Y = sf["sides"]
    W, L_r = spec["roll_width_m"], spec["roll_length_m"]
    side, end = spec["min_side_lap_m"], spec["min_end_lap_m"]
    h = c["upturn_h_m"]
    b = h + side                                                    # band: upturn + lap onto the floor membrane
    min_re = c.get("min_reusable_m")
    L_s, D_c = (X, Y) if direction == "ALONG_X" else (Y, X)
    rolls = _Rolls(W, L_r)
    lanes, scrap, retained, laid = [], [], [], {"floor": 0.0, "doorway": 0.0, "upturn": 0.0}
    concerns = list(sf["flags"])
    if b > W + EPS:
        raise MembraneError("the upturn band is wider than the roll")
    k_lanes = int(math.floor(W / b + EPS))

    def leftover(w, ln, why):
        if w <= EPS or ln <= EPS:
            return
        (retained if (min_re is not None and min(w, ln) >= min_re - EPS) else scrap).append((w, ln, why))

    def lanes_from(w, ln, why):
        """a strip of width w and length ln, cut into band lanes; the residue is left over."""
        k = int(math.floor(w / b + EPS))
        for _ in range(k):
            lanes.append(ln)
        leftover(w - k * b, ln, why + " residue")

    # floor strips
    if floor_fn is None:
        n, w_last, k, lengths = _strip_plan(L_s, D_c, W, L_r, side, end)
        for s in range(n):
            for ln in lengths:
                rolls.cut(ln, f"floor strip {s + 1}")
                if s == n - 1 and W - w_last > EPS:
                    trim = W - w_last
                    if trim >= b - EPS:
                        lanes_from(trim, ln, "floor edge trim")
                    else:
                        leftover(trim, ln, "floor edge trim")
        floor_mat = ((n - 1) * W + w_last) * (L_s + (k - 1) * end)
        seams = {"longitudinal": {"count": n - 1, "each_lm": L_s, "lap_m": side, "running_lm": round((n - 1) * L_s, 6)},
                 "transverse_floor": {"count": n * (k - 1), "lap_m": end,
                                      "running_lm": round((k - 1) * ((n - 1) * W + w_last), 6)}}
        extra = {}
    else:
        floor_mat, seams, n, w_last, k, lengths, extra = floor_fn(direction, rolls, lanes_from, leftover, scrap)
    laid["floor"] = floor_mat
    # doorway pieces
    dw_pieces = []
    for r in sf["rows"]:
        if r["item_code"] != "FIN.WP.DOORWAY":
            continue
        pw, pl = r["inputs"]["width_m"], r["inputs"]["depth_m"] + side
        md, Md = min(pw, pl), max(pw, pl)
        laid["doorway"] += pw * pl
        dw_pieces.append({"doorway": r["doorway"], "piece_m": [round(pw, 4), round(pl, 4)], "lap_lm": pw})
        if md <= b + EPS:
            _band_piece(Md, md, lanes, rolls, leftover, k_lanes, b, f"doorway {r['doorway']}")
        elif md <= W + EPS:
            seg = Md if Md > W + EPS else md
            across = md if seg == Md else Md
            rolls.cut(seg, f"doorway {r['doorway']}")
            lanes_from(W - across, seg, f"doorway {r['doorway']} side")
        else:
            raise MembraneError("a doorway piece wider than the roll in both directions (splice it: S2)")
    # ARCH_TAKEOFF_V2.5: membrane patches of a resolved corner / penetration detail, cut from this membrane
    detail_pieces = []
    for dp in c.get("detail_pieces") or ():
        a_, b_ = sorted((dp["a_m"], dp["b_m"]))                    # a_: the narrow side of the patch
        n_ = int(dp["count"])
        laid["detailing"] = laid.get("detailing", 0.0) + n_ * a_ * b_
        if a_ <= b + EPS:                                          # narrower than a band lane: from the lanes
            for i in range(n_):
                _band_piece(b_, a_, lanes, rolls, leftover, k_lanes, b, f"{dp['what']} {i + 1}")
        elif a_ <= W + EPS:                                        # side by side across a full-width segment
            per = int(math.floor(W / a_ + EPS))
            for s_ in range(-(-n_ // per)):
                rolls.cut(b_, dp["what"])
                lanes_from(W - min(per, n_ - s_ * per) * a_, b_, f"{dp['what']} residue")
        else:
            raise MembraneError("a patch wider than the roll")
        detail_pieces.append({"what": dp["what"], "piece_m": [round(a_, 4), round(b_, 4)], "count": n_})
    # upturn band runs
    joints, band_pieces = 0, []
    runs = sf["runs"]["runs"]
    total_need = sum(r["length_m"] for r in runs)
    guard = 0
    planner = c.get("band_planner")
    if planner is not None:
        if planner != BAND_MIN_SEGMENT:
            raise MembraneError(f"band_planner {planner}")

        def snapshot():
            return list(lanes), [list(u) for u in rolls.used], list(scrap), list(retained)

        def restore(s):
            lanes[:], scrap[:], retained[:] = s[0], s[2], s[3]
            rolls.used[:] = [list(u) for u in s[1]]
        joints, band_pieces, band_cuts = _band_min_segment(runs, lanes, rolls, lanes_from, k_lanes, b, end,
                                                           snapshot, restore)
        runs = ()                                                  # planned: the loop below has nothing to do
    for run in runs:
        remaining, first = run["length_m"], True
        while remaining > EPS:
            guard += 1
            if guard > 10000:
                raise MembraneError("the band plan did not converge")
            lap = end if (not first or run["closed"]) else 0.0
            ln = _take_lane(lanes, remaining + lap, lap, min(remaining, b))
            if ln is None:
                # one segment long enough for the rest of the band (k lanes side by side), first fit into the rolls
                seg = min(L_r, _ceil_cm(max(total_need / k_lanes, min(remaining, b)) + 2 * end))
                rolls.cut(seg, "upturn lanes")
                lanes_from(W, seg, "upturn lane segment")
                continue
            cover = min(ln - lap, remaining)
            used = cover + lap
            band_pieces.append(used)
            if ln - used > EPS:
                lanes.append(ln - used)
            if lap > 0:
                joints += 1
            remaining -= cover
            total_need -= cover
            first = False
    laid["upturn"] = b * sum(band_pieces)
    for ln in lanes:
        leftover(b, ln, "unused lane")
    runs = sf["runs"]["runs"]
    seams["upturn_end_laps"] = {"count": joints, "lap_m": end, "running_lm": round(joints * b, 6)}
    seams["upturn_to_floor_lap"] = {"lap_m": side, "running_lm": round(sum(r["length_m"] for r in runs), 6)}
    seams["doorway_to_floor_lap"] = {"lap_m": side, "running_lm": round(sum(p["lap_lm"] for p in dw_pieces), 6)}
    # net, overlap, balance
    net = sum(r["net_m2"] for r in sf["rows"])
    mat = sum(laid.values())
    overlap = mat - net
    packing = None
    if planner is not None:                                     # ARCH_TAKEOFF_V2.5: the fewest rolls (exact)
        segs = [x for u in rolls.used for x in u]
        bins, packing = pack_rolls([x[0] for x in segs], L_r)
        rolls.used[:] = [[segs[i] for i in b] for b in bins]
    recs = rolls.records()
    n_rolls = len(recs)
    surplus = sum(r["untouched_tail_m"] for r in recs) * W
    consumed = n_rolls * W * L_r - surplus
    off = sum(w * ln for w, ln, _ in retained)
    waste_tracked = sum(w * ln for w, ln, _ in scrap)
    if abs(consumed - (mat + off + waste_tracked)) > 1e-5:
        raise MembraneError(f"roll plan does not balance: consumed {consumed} vs laid {mat} + offcuts {off} + scrap "
                            f"{waste_tracked}")
    corners = 4 + 2 * len(dw_pieces)
    det = {"corners": {"count": corners, "state": "NOT_QUANTIFIED" if not spec.get("corner_treatment") else "BY_SYSTEM",
                       "detail": spec.get("corner_treatment")},
           "penetrations": {"count": int(c.get("penetrations") or 0),
                            "state": "NOT_QUANTIFIED" if not spec.get("penetration_detail") else "BY_SYSTEM",
                            "detail": spec.get("penetration_detail")}}
    if not spec.get("corner_treatment"):
        concerns.append(f"CORNER_TREATMENT_NOT_SPECIFIED: {corners} corner(s) counted, corner pieces not quantified")
    if det["penetrations"]["count"] and not spec.get("penetration_detail"):
        concerns.append(f"PENETRATION_DETAIL_NOT_SPECIFIED: {det['penetrations']['count']} penetration(s) counted, "
                        f"collars / patches not quantified")
    if sf["runs"]["approximate"]:
        concerns.append("BAND_RUNS_APPROXIMATED: several doorways without position_lm; the band is cut as one open run")
    if min_re is None:
        concerns.append("NO_OFFCUT_RETAINED: min_reusable_m not given - every leftover counts as cutting waste")
    pack = {"pack_unit": "roll", "units_per_pack": 1, "pack_area_m2": round(W * L_r, 6), "consumed_units": n_rolls,
            "spare": WP.spare(), "spare_units": 0, "source": spec.get("data_sheet") or spec.get("authority"),
            "state": "RESOLVED", "reason": "", "packs": n_rolls, "pack_total_m2": round(n_rolls * W * L_r, 6),
            "packaging_surplus_m2": round(surplus, 6), "procurement_units": n_rolls, "procurement_packs": n_rolls,
            "procurement_m2": round(n_rolls * W * L_r, 6)}
    sp = c.get("spare_allowance")
    if sp and sp.get("state") == "OWNER_SET":
        need = consumed * sp["pct"] / 100.0 - surplus          # the untouched tails cover the spare first
        extra = math.ceil(need / (W * L_r) - 1e-9) if need > EPS else 0
        pack.update(spare=sp, spare_units=extra, procurement_units=n_rolls + extra, procurement_packs=n_rolls + extra,
                    procurement_m2=round((n_rolls + extra) * W * L_r, 6))
    comps = [{"component": "floor", "item_code": "FIN.WP.FLOOR", "net_m2": round(sf["rows"][0]["net_m2"], 6),
              "laid_m2": round(laid["floor"], 6), "overlap_m2": round(laid["floor"] - sf["rows"][0]["net_m2"], 6)},
             {"component": "doorway", "item_code": "FIN.WP.DOORWAY",
              "net_m2": round(sum(r["net_m2"] for r in sf["rows"] if r["item_code"] == "FIN.WP.DOORWAY"), 6),
              "laid_m2": round(laid["doorway"], 6)},
             {"component": "upturn", "item_code": "FIN.WP.UPTURN", "net_m2": round(sf["rows"][-1]["net_m2"], 6),
              "laid_m2": round(laid["upturn"], 6), "overlap_m2": round(laid["upturn"] - sf["rows"][-1]["net_m2"], 6)}]
    comps[1]["overlap_m2"] = round(comps[1]["laid_m2"] - comps[1]["net_m2"], 6)
    if detail_pieces:                                              # ARCH_TAKEOFF_V2.5 only
        comps.append({"component": "detailing", "item_code": "FIN.WP.DETAILING", "net_m2": 0.0,
                      "laid_m2": round(laid["detailing"], 6), "overlap_m2": round(laid["detailing"], 6),
                      "pieces": detail_pieces})
    lay = {"direction": direction, "strip_length_m": L_s, "cross_width_m": D_c, "floor_strips": n,
           "last_strip_width_m": round(w_last, 6), "pieces_per_strip": k, "strip_piece_lengths_m": [round(x, 4) for x in lengths],
           "band_width_m": round(b, 6), "lanes_per_roll_width": k_lanes, "band_pieces_m": [round(x, 4) for x in band_pieces],
           "band_runs": runs, "doorway_pieces": dw_pieces, "seams": seams, "details": det, "rolls": recs,
           "offcuts_retained": [[round(w, 4), round(ln, 4), why] for w, ln, why in retained],
           "scrap": [[round(w, 4), round(ln, 4), why] for w, ln, why in scrap],
           "surfaces": sf["rows"], "perimeter_lm": sf["perimeter_lm"], "doorway_segments_lm": sf["doorway_segments_lm"],
           "upturn_lm": sf["upturn_lm"]}
    lay.update(extra)
    if planner is not None:
        lay["roll_packing"] = packing
        lay["band_planner"] = {"planner": planner, "segments": band_cuts,
                               "rule": "each new band segment is the shortest (1 cm steps) whose lanes finish the "
                                       "band; when that segment would open a roll, filling the largest open roll tail "
                                       "first is evaluated and kept if it gives fewer rolls (then fewer joints, then "
                                       "less membrane)"}
    assumptions = [f"roll {W:g} x {L_r:g} m ({spec.get('spec_id')})", f"side lap {side:g} m ({(spec.get('lap_source') or {}).get('side')})",
                   f"end lap {end:g} m ({(spec.get('lap_source') or {}).get('end')})", f"upturn {h:g} m",
                   f"upturn band laps {side:g} m onto the floor membrane (band width {b:g} m)",
                   f"doorway piece laps {side:g} m onto the floor membrane; jamb returns / water stop not modelled",
                   "the last floor strip is trimmed lengthwise; a trim at least one band wide is cut into band lanes",
                   f"doorway detail {c.get('doorway_detail', 'NOT_ESTABLISHED')}",
                   f"min reusable offcut {min_re:g} m" if min_re is not None else "no offcut retained"]
    units = {"unit": "roll", "unit_area_m2": W * L_r, "consumed_units": n_rolls, "full": None, "cut": None}
    return WP.make_result(method=method, spec=spec, net_installed_m2=net, placed_m2=net, overlap_m2=overlap,
                          consumed_m2=consumed, reusable_offcuts_m2=off, units=units, pack=pack, layout=lay,
                          assumptions=assumptions, concerns=concerns, line_id=room.get("line_id"), location=loc,
                          rule_refs=c.get("rule_refs", ()), state="COMPUTED_REVIEW" if concerns else "COMPUTED",
                          components=comps)


def surfaces_polygon(room, *, upturn_h, doorways=(), doorway_detail="NOT_ESTABLISHED"):
    """surfaces() for any simple polygon room (metres) with obstructions (room["holes"]). The upturn runs on the
    room's boundary: room["perimeter_lm"] when the caller measured it (the BOQ line's basis), else the outer ring plus
    every obstruction ring; each ring is a closed band loop."""
    if doorway_detail not in DOORWAY_DETAILS:
        raise MembraneError(f"doorway_detail {doorway_detail}")
    poly = [tuple(map(float, q)) for q in room.get("polygon") or []]
    if len(poly) < 3:
        return None
    holes = [[tuple(map(float, q)) for q in h] for h in room.get("holes") or ()]
    A = abs(PP.area(poly)) - sum(abs(PP.area(h)) for h in holes)
    hole_lm = [PP.perimeter(h) for h in holes]
    P = float(room["perimeter_lm"]) if room.get("perimeter_lm") is not None else PP.perimeter(poly) + sum(hole_lm)
    dws = [dict(d) for d in doorways]
    for d in dws:
        if d.get("width_m") is None or d.get("depth_m") is None:
            raise MembraneError("a doorway needs width_m and depth_m (the wall depth at the opening)")
    door_lm = sum(d["width_m"] for d in dws)
    within = doorway_detail == "UPTURN_WITHIN_DOORWAY_PIECE"
    up_lm = P - door_lm if within else P
    rows = [{"item_code": "FIN.WP.FLOOR", "net_m2": A, "formula": "room polygon area - obstructions",
             "inputs": {"area_m2": A, "obstructions": len(holes)}}]
    for i, d in enumerate(dws, 1):
        rows.append({"item_code": "FIN.WP.DOORWAY", "doorway": d.get("door_id") or f"D{i}",
                     "net_m2": d["width_m"] * d["depth_m"], "formula": "door width x wall depth",
                     "inputs": {"width_m": d["width_m"], "depth_m": d["depth_m"]}})
    rows.append({"item_code": "FIN.WP.UPTURN", "net_m2": up_lm * upturn_h,
                 "formula": ("(boundary - doorway segments, billed in the doorway pieces) x upturn height" if within
                             else "full boundary incl. doorway segments x upturn height (no door deduction)"),
                 "inputs": {"perimeter_lm": P, "doorway_segments_lm": door_lm, "upturn_lm": up_lm, "upturn_h_m": upturn_h}})
    flags = []
    if dws and doorway_detail == "NOT_ESTABLISHED":
        flags += ["DOORWAY_UPTURN_DETAIL_REQUIRED", "DOORWAY_DOUBLE_COVERAGE_REVIEW"]
    if within:
        flags += [f"DOORWAY_SEGMENT_BILLED_IN_DOORWAY_PIECE ({door_lm:g} lm)"]
        if any(d["depth_m"] < upturn_h - EPS for d in dws):
            flags.append("DOORWAY_PIECE_SHALLOWER_THAN_UPTURN")
    outer = max(P - sum(hole_lm), 0.0)
    if within and dws:
        runs = {"runs": [{"length_m": outer - door_lm, "closed": False}] +
                [{"length_m": h, "closed": True} for h in hole_lm], "approximate": len(dws) > 1}
    else:
        runs = {"runs": [{"length_m": outer, "closed": True}] + [{"length_m": h, "closed": True} for h in hole_lm],
                "approximate": False}
    x0, y0, x1, y1 = PP.bbox(PP.rotate(poly, PP.frame_angle(poly)))
    return {"rows": rows, "perimeter_lm": P, "doorway_segments_lm": door_lm, "upturn_lm": up_lm, "flags": flags,
            "runs": runs, "sides": (x1 - x0, y1 - y0), "polygon": poly, "holes": holes}


def _poly_floor(sf, spec):
    """floor strips over the polygon: strips of the roll width along the frame axis (longest wall), stacked across
    it with the side lap; in each strip one piece per connected run of the room (band_intervals), spliced with end
    laps when longer than a roll. Every piece is cut at full roll width; the last strip is trimmed lengthwise (the
    trim feeds the band lanes, as for a rectangle). Material that falls outside the room (a splayed or stepped wall,
    an obstruction) is trimmed at the wall: cutting waste. laid = the room area each piece covers, so the floor
    overlap = laid - net = the side and end laps inside the room exactly."""
    theta = PP.frame_angle(sf["polygon"])
    P0 = PP.rotate(sf["polygon"], theta)
    H0 = [PP.rotate(h, theta) for h in sf["holes"]]
    W, L_r = spec["roll_width_m"], spec["roll_length_m"]
    side, end = spec["min_side_lap_m"], spec["min_end_lap_m"]

    def run(direction, rolls, lanes_from, leftover, scrap):
        P, H = P0, H0
        if direction == "ALONG_Y":                     # swap axes: strips run along the frame's y axis
            P = [(y, x) for x, y in P]
            H = [[(y, x) for x, y in h] for h in H]
        x0, y0, x1, y1 = PP.bbox(P)
        D = y1 - y0
        n = 1 if D <= W + EPS else math.ceil((D - W) / (W - side) - EPS) + 1
        w_last = D - (n - 1) * (W - side)
        laid, pieces, longest, k_max, splices, shaped_trim = 0.0, [], 0.0, 1, 0, 0.0
        for i in range(n):
            ya = y0 + i * (W - side)
            w = W if i < n - 1 else w_last
            for xa, xb in PP.band_intervals(P, H, ya, ya + w):
                L_s = xb - xa
                k = 1 if L_s <= L_r + EPS else math.ceil((L_s - L_r) / (L_r - end) - EPS) + 1
                lens = [L_r] * (k - 1) + [L_s - (k - 1) * (L_r - end)] if k > 1 else [L_s]
                k_max, splices, longest = max(k_max, k), splices + k - 1, max(longest, L_s)
                pos = xa
                for ln in lens:
                    rolls.cut(ln, f"floor strip {i + 1}")
                    if W - w > EPS:
                        trim = W - w
                        if trim >= (sf["_band"]) - EPS:
                            lanes_from(trim, ln, "floor edge trim")
                        else:
                            leftover(trim, ln, "floor edge trim")
                    cov = PP.region_area_in_rect(P, H, (pos, ya, pos + ln, ya + w))
                    t = w * ln - cov
                    if t > 1e-9:
                        scrap.append((t / ln, ln, "trim at the wall line (shaped; area-equivalent width)"))
                        shaped_trim += t
                    laid += cov
                    pieces.append(round(ln, 4))
                    pos += ln - end
        seams = {"longitudinal": {"count": n - 1, "each_lm": round(longest, 6), "lap_m": side,
                                  "running_lm": None},
                 "transverse_floor": {"count": splices, "lap_m": end, "running_lm": None}}
        extra = {"frame_rotation_deg": round(math.degrees(theta), 4), "floor_pieces_m": pieces,
                 "trim_at_walls_m2": round(shaped_trim, 6), "shape": "POLYGON"}
        return laid, seams, n, w_last, k_max, pieces, extra
    return run


def plan_polygon(room, spec, *, constraints):
    """plan() for any simple polygon room with obstructions (M9 S2; the architectural route calls it for a wet room
    that is not a rectangle). Same constraints, same balance: rolls x roll area = net installed + overlap + cutting
    waste + reusable offcuts + packaging surplus."""
    c = dict(constraints)
    if c.get("upturn_h_m") is None:
        raise MembraneError("constraints['upturn_h_m'] is required (the rule store gives UP-WP-002)")
    direction = c.get("direction", "MIN_MATERIAL")
    if direction not in DIRECTIONS:
        raise MembraneError(f"direction {direction}")
    loc = {k: room.get(k) for k in ("room_id", "floor", "name_en", "name_ar") if room.get(k) is not None}
    sf = surfaces_polygon(room, upturn_h=c["upturn_h_m"], doorways=c.get("doorways", ()),
                          doorway_detail=c.get("doorway_detail", "NOT_ESTABLISHED"))
    if sf is None:
        return WP.blocked(method=POLY_METHOD, spec=spec, reason="NO_ROOM_POLYGON", location=loc,
                          line_id=room.get("line_id"), rule_refs=c.get("rule_refs", ()))
    sf["_band"] = c["upturn_h_m"] + spec["min_side_lap_m"]
    fl = _poly_floor(sf, spec)
    dirs = ("ALONG_X", "ALONG_Y") if direction == "MIN_MATERIAL" else (direction,)
    opts = [_one(sf, spec, c, d, loc, room, floor_fn=fl, method=POLY_METHOD) for d in dirs]
    sel = min(opts, key=lambda r: (r["units"]["consumed_units"], round(r["consumed_m2"], 6),
                                   round(r["cutting_waste_m2"], 6), DIRECTIONS.index(r["layout"]["direction"])))
    if len(opts) > 1:
        sel["layout"]["alternatives"] = [{"direction": r["layout"]["direction"], "rolls": r["units"]["consumed_units"],
                                          "consumed_m2": r["consumed_m2"], "overlap_m2": r["overlap_m2"],
                                          "cutting_waste_m2": r["cutting_waste_m2"],
                                          "packaging_surplus_m2": r["packaging"]["packaging_surplus_m2"]} for r in opts]
    return sel


def _take_lane(lanes, need, lap, min_cover):
    """best-fit lane: the shortest that covers the need, else the longest that still covers min_cover past its lap."""
    if not lanes:
        return None
    fit = [x for x in lanes if x >= need - EPS]
    if fit:
        x = min(fit)
    else:
        x = max(lanes)
        if x - lap < min_cover - EPS:
            return None
    lanes.remove(x)
    return x


def _band_piece(length, width, lanes, rolls, leftover, k_lanes, b, why):
    """a narrow piece (width <= band width) from a lane; a new lane segment when none is long enough."""
    fit = [x for x in lanes if x >= length - EPS]
    if not fit:
        rolls.cut(length, why)
        # the segment gives k lanes of this length; one is used here, the others join the pool
        for _ in range(k_lanes - 1):
            lanes.append(length)
        leftover(rolls.W - k_lanes * b, length, why + " residue")
        x = length
    else:
        x = min(fit)
        lanes.remove(x)
    if b - width > EPS:
        leftover(b - width, length, why + " width trim")
    if x - length > EPS:
        lanes.append(x - length)


# ------------------------------------------------------------------------------------- ARCH_TAKEOFF_V2.5 band planner
def _fill_band(todo, lanes, end, b):
    """cover the band runs todo [[remaining, closed, started]] from the lanes as far as they go (copies; the lane
    choice of _take_lane). -> (pieces, joints, lanes left, runs left)."""
    todo, lanes, pieces, joints = [list(t) for t in todo], list(lanes), [], 0
    while todo:
        rem, closed, started = todo[0]
        while rem > EPS:
            lap = end if (closed or started) else 0.0
            ln = _take_lane(lanes, rem + lap, lap, min(rem, b))
            if ln is None:
                todo[0] = [rem, closed, started]
                return pieces, joints, lanes, todo
            cover = min(ln - lap, rem)
            used = cover + lap
            pieces.append(used)
            if ln - used > EPS:
                lanes.append(ln - used)
            joints += lap > 0
            rem -= cover
            started = True
        todo.pop(0)
    return pieces, joints, lanes, []


def _min_band_segment(todo, lanes, k_lanes, b, L_r, end):
    """the shortest full-width segment (whole cm) whose k lanes, with the lanes left, finish the band; L_r when no
    segment of one roll length does (the planner then cuts another)."""
    need = sum(t[0] for t in todo)
    c0 = max(1, math.ceil(round(need / k_lanes * 100.0, 6)))
    for cm in range(c0, int(round(L_r * 100.0)) + 1):
        seg = cm / 100.0
        if not _fill_band(todo, list(lanes) + [seg] * k_lanes, end, b)[3]:
            return seg
    return L_r


def _band_min_segment(runs, lanes, rolls, lanes_from, k_lanes, b, end, snapshot, restore):
    """ARCH_TAKEOFF_V2.5: the band runs covered from the lane pool, then from new segments, each the shortest whose
    lanes finish the band (_min_band_segment). A segment that fits no open roll tail opens a roll: filling the
    largest open tail first (when its lanes cover something) is planned to the end as well and kept only when it
    gives fewer rolls, then fewer joints, then less membrane. -> (joints, band pieces, [{length_m, basis}])."""
    L_r = rolls.L

    def cut_total():
        return round(sum(x[0] for u in rolls.used for x in u), 6)

    def n_rolls():
        return len(pack_rolls([x[0] for u in rolls.used for x in u], L_r)[0])

    def cut(seg, basis, cuts):
        rolls.cut(seg, "upturn lanes" if basis == "SHORTEST_FINISHING_SEGMENT" else "upturn lanes (roll tail)")
        lanes_from(rolls.W, seg, "upturn lane segment")
        cuts.append({"length_m": round(seg, 4), "basis": basis})

    def plan(todo):
        pieces, joints, left, todo = _fill_band(todo, lanes, end, b)
        lanes[:] = left
        if not todo:
            return pieces, joints, []
        seg = _min_band_segment(todo, lanes, k_lanes, b, L_r, end)
        tail = max((L_r - sum(x[0] for x in u) for u in rolls.used), default=0.0)
        tail = math.floor(round(tail * 100.0, 6)) / 100.0
        if seg > tail + EPS and tail - end >= min(todo[0][0], b) - EPS:
            s0 = snapshot()
            ca = []
            cut(seg, "SHORTEST_FINISHING_SEGMENT", ca)
            pa, ja, ra = plan(todo)
            ka = (n_rolls(), joints + ja, cut_total())
            sa = snapshot()
            restore(s0)
            cb = []
            cut(tail, "LARGEST_ROLL_TAIL", cb)
            pb, jb, rb = plan(todo)
            if (n_rolls(), joints + jb, cut_total()) < ka:
                return pieces + pb, joints + jb, cb + rb
            restore(sa)
            return pieces + pa, joints + ja, ca + ra
        cs = []
        cut(seg, "SHORTEST_FINISHING_SEGMENT", cs)
        p2, j2, r2 = plan(todo)
        return pieces + p2, joints + j2, cs + r2
    todo = [[r["length_m"], r["closed"], False] for r in runs]
    pieces, joints, cuts = plan(todo)
    return joints, pieces, cuts


def pack_rolls(lengths, L, node_limit=200000):
    """ARCH_TAKEOFF_V2.5: whole rolls of length L for full-width pieces, fewest rolls. First fit decreasing, then -
    unless it already meets the lower bound ceil(sum / L) - an exact branch and bound (deterministic, at most
    node_limit nodes). -> (bins [[piece index ...]], {"method", "lower_bound", "first_fit_decreasing", "proven"})."""
    q = [int(round(x * 10000.0)) for x in lengths]                  # integers (tenths of a mm): no float drift
    cap = int(round(L * 10000.0))
    order = sorted(range(len(q)), key=lambda i: (-q[i], i))
    ffd, loads = [], []
    for i in order:
        for k in range(len(ffd)):
            if cap - loads[k] >= q[i]:
                ffd[k].append(i)
                loads[k] += q[i]
                break
        else:
            ffd.append([i])
            loads.append(q[i])
    lb = -(-sum(q) // cap) if q else 0
    info = {"method": "FIRST_FIT_DECREASING", "lower_bound": lb, "first_fit_decreasing": len(ffd), "proven": True}
    if len(ffd) <= lb:
        return ffd, info
    best = [len(ffd), [list(b) for b in ffd]]
    nodes, complete = [0], [True]

    def go(k, bins, ld):
        if len(bins) >= best[0] or best[0] <= lb:
            return
        nodes[0] += 1
        if nodes[0] > node_limit:
            complete[0] = False
            return
        if k == len(order):
            best[0], best[1] = len(bins), [list(b) for b in bins]
            return
        i = order[k]
        seen = set()
        for j in range(len(bins)):
            room = cap - ld[j]
            if room >= q[i] and room not in seen:
                seen.add(room)
                bins[j].append(i)
                ld[j] += q[i]
                go(k + 1, bins, ld)
                ld[j] -= q[i]
                bins[j].pop()
        bins.append([i])
        ld.append(q[i])
        go(k + 1, bins, ld)
        ld.pop()
        bins.pop()
    go(0, [], [])
    info.update(method="EXACT_BRANCH_AND_BOUND", proven=complete[0] or best[0] <= lb, nodes=nodes[0])
    return [sorted(b, key=lambda i: (-q[i], i)) for b in best[1]], info

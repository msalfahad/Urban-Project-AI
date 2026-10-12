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
from engine.source.tile_layout import rectangle

METHOD = "MEMBRANE_RECT_EXACT_V1"
DOORWAY_DETAILS = ("NOT_ESTABLISHED", "SEPARATE_RETURN", "UPTURN_WITHIN_DOORWAY_PIECE")
DIRECTIONS = ("ALONG_X", "ALONG_Y", "MIN_MATERIAL")
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


def _one(sf, spec, c, direction, loc, room):
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
    laid["floor"] = floor_mat
    seams = {"longitudinal": {"count": n - 1, "each_lm": L_s, "lap_m": side, "running_lm": round((n - 1) * L_s, 6)},
             "transverse_floor": {"count": n * (k - 1), "lap_m": end,
                                  "running_lm": round((k - 1) * ((n - 1) * W + w_last), 6)}}
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
    # upturn band runs
    joints, band_pieces = 0, []
    runs = sf["runs"]["runs"]
    total_need = sum(r["length_m"] for r in runs)
    guard = 0
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
            band_pieces.append(round(used, 4))
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
    seams["upturn_end_laps"] = {"count": joints, "lap_m": end, "running_lm": round(joints * b, 6)}
    seams["upturn_to_floor_lap"] = {"lap_m": side, "running_lm": round(sum(r["length_m"] for r in runs), 6)}
    seams["doorway_to_floor_lap"] = {"lap_m": side, "running_lm": round(sum(p["lap_lm"] for p in dw_pieces), 6)}
    # net, overlap, balance
    net = sum(r["net_m2"] for r in sf["rows"])
    mat = sum(laid.values())
    overlap = mat - net
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
    lay = {"direction": direction, "strip_length_m": L_s, "cross_width_m": D_c, "floor_strips": n,
           "last_strip_width_m": round(w_last, 6), "pieces_per_strip": k, "strip_piece_lengths_m": [round(x, 4) for x in lengths],
           "band_width_m": round(b, 6), "lanes_per_roll_width": k_lanes, "band_pieces_m": band_pieces,
           "band_runs": runs, "doorway_pieces": dw_pieces, "seams": seams, "details": det, "rolls": recs,
           "offcuts_retained": [[round(w, 4), round(ln, 4), why] for w, ln, why in retained],
           "scrap": [[round(w, 4), round(ln, 4), why] for w, ln, why in scrap],
           "surfaces": sf["rows"], "perimeter_lm": sf["perimeter_lm"], "doorway_segments_lm": sf["doorway_segments_lm"],
           "upturn_lm": sf["upturn_lm"]}
    assumptions = [f"roll {W:g} x {L_r:g} m ({spec.get('spec_id')})", f"side lap {side:g} m ({(spec.get('lap_source') or {}).get('side')})",
                   f"end lap {end:g} m ({(spec.get('lap_source') or {}).get('end')})", f"upturn {h:g} m",
                   f"upturn band laps {side:g} m onto the floor membrane (band width {b:g} m)",
                   f"doorway piece laps {side:g} m onto the floor membrane; jamb returns / water stop not modelled",
                   "the last floor strip is trimmed lengthwise; a trim at least one band wide is cut into band lanes",
                   f"doorway detail {c.get('doorway_detail', 'NOT_ESTABLISHED')}",
                   f"min reusable offcut {min_re:g} m" if min_re is not None else "no offcut retained"]
    units = {"unit": "roll", "unit_area_m2": W * L_r, "consumed_units": n_rolls, "full": None, "cut": None}
    return WP.make_result(method=METHOD, spec=spec, net_installed_m2=net, placed_m2=net, overlap_m2=overlap,
                          consumed_m2=consumed, reusable_offcuts_m2=off, units=units, pack=pack, layout=lay,
                          assumptions=assumptions, concerns=concerns, line_id=room.get("line_id"), location=loc,
                          rule_refs=c.get("rule_refs", ()), state="COMPUTED_REVIEW" if concerns else "COMPUTED",
                          components=comps)


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

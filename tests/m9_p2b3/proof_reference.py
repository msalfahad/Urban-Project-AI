"""INDEPENDENT REFERENCE CALCULATIONS - Phase 2B-3 proof library (ARCH_TAKEOFF_V2.5).

Written from the construction method - how a sheet membrane is set out, cut and lapped on site - and never from the
engine: this file imports nothing from engine/ or tools/ (test_p2b3_independence checks every import), works in whole
millimetres (the engine works in metres with tolerances) and finds its minimum cut lengths and roll counts by
exhaustive search instead of the engine's formulas and first-fit packing.

Every proof case states its expected values as a hand calculation (proof_cases.py). This module recomputes the same
quantities as an arithmetic cross-check of that hand calculation, and does the searches a hand calculation cannot do
exhaustively. It never supplies an expected value on its own.

    strips(D, roll)                        the floor strips across a cross width D: count and widths
    floor(poly, roll, along)               the floor strips of a rectilinear area: cut pieces, laid area, side laps,
                                           the trim of each last-strip piece
    lanes_of(trim_w, length, band)         the band lanes an offcut gives (whole lanes only; the rest is scrap)
    cover(runs, pool, lap)                 the band pieces that cover the eligible upturn runs from a pool of lanes
    min_segment(runs, pool, roll, band)    the shortest new full-width segment whose lanes finish the band
    min_rolls(pieces, roll_length)         the fewest whole rolls the pieces can be cut from (exact search)
    membrane(area, roll, along)            the whole area: A, upturn, laps by kind, B, consumed, waste, rolls

Construction method (the rules the hand calculations state):
    floor     strips of the roll width laid side by side with the side lap; the last strip is cut down lengthwise to
              what is left of the cross width; a strip longer than a roll is spliced with an end lap
    band      the upturn is cut as lanes of (upturn height + lap onto the floor membrane) along a roll; a full-width
              segment gives floor(roll width / band width) lanes; each band piece after the first of an open run
              laps onto the piece before it, a closed loop laps at every joint including its closure
    offcuts   the trim of a last floor strip is cut into lanes first; a doorway piece takes the shortest lane that
              is long enough; the band takes the pool lanes, the shortest that finishes a run or else the longest
    new cut   when the pool is empty, the shortest new segment (10 mm steps) whose lanes finish every remaining run
"""

from __future__ import annotations

MM = 1000


def mm(x_m):
    """metres -> whole millimetres (every input of a proof case is a whole number of millimetres)."""
    v = round(x_m * MM)
    if abs(v - x_m * MM) > 1e-6:
        raise ValueError(f"{x_m} m is not a whole number of millimetres")
    return int(v)


def m(x_mm):
    return x_mm / MM


def m2(x_mm2):
    return x_mm2 / (MM * MM)


def ceil_to(x, step):
    """the smallest multiple of step >= x (integers)."""
    return -(-x // step) * step


# ------------------------------------------------------------------------------------------------ floor strips
def strips(D, W, s):
    """the strip count across a cross width D (mm): the smallest n with W + (n - 1)(W - s) >= D, found by counting
    strips one at a time; -> (n, [width of each strip as laid])."""
    n, reach = 1, W
    while reach < D:
        n += 1
        reach += W - s
    widths = [W] * (n - 1) + [D - (n - 1) * (W - s)]
    return n, widths


def _slabs(poly):
    """the rectilinear polygon cut into horizontal slabs between consecutive vertex levels: [(y0, y1, [(xa, xb)])],
    the inside x-intervals of each slab by the even-odd rule on its mid level."""
    ys = sorted({p[1] for p in poly})
    out = []
    for y0, y1 in zip(ys, ys[1:]):
        ym2 = y0 + y1                                       # twice the mid level (stays an integer)
        xs = []
        for i in range(len(poly)):
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
            if ax == bx and min(ay, by) * 2 < ym2 < max(ay, by) * 2:
                xs.append(ax)
        xs.sort()
        out.append((y0, y1, [(xs[k], xs[k + 1]) for k in range(0, len(xs), 2)]))
    return out


def _merge(ivs):
    out = []
    for a, b in sorted(ivs):
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _swap(poly):
    return [(y, x) for x, y in poly]


def floor(poly, W, s, e, L_roll, along):
    """the floor strips of a rectilinear area (mm). along "X": strips run along x and are stacked in y from the
    lowest y; along "Y": the same with the axes swapped. In each strip one piece per connected stretch of the area
    across the strip's band (a piece covers the whole stretch; material outside the area is cut off at the wall).
    -> {"n", "widths", "pieces": [{"strip", "length", "width", "laid"}], "cuts": [cut lengths], "laid", "trims"}"""
    P = poly if along == "X" else _swap(poly)
    sl = _slabs(P)
    y0, y1 = min(p[1] for p in P), max(p[1] for p in P)
    n, widths = strips(y1 - y0, W, s)
    pieces, cuts, trims, laid, outside = [], [], [], 0, 0
    for i, w in enumerate(widths):
        ya, yb = y0 + i * (W - s), y0 + i * (W - s) + w
        ivs = _merge([iv for (sa, sb, xs) in sl if min(sb, yb) > max(sa, ya) for iv in xs])
        for xa, xb in ivs:
            L = xb - xa
            # the area under this piece: every slab's inside length within [xa, xb] times its height within the band
            cov = sum((min(sb, yb) - max(sa, ya)) * sum(max(0, min(b, xb) - max(a, xa)) for a, b in xs)
                      for sa, sb, xs in sl if min(sb, yb) > max(sa, ya))
            k, lens = 1, [L]
            if L > L_roll:                                    # spliced: each further piece laps e onto the last
                k, rest, lens = 1, L - L_roll, [L_roll]
                while rest > 0:
                    k += 1
                    nxt = min(L_roll, rest + e)
                    lens.append(nxt)
                    rest -= nxt - e
            for ln in lens:
                cuts.append(ln)
                if w < W:
                    trims.append((W - w, ln))
            # a splice laps e over the piece before it: that strip of the area is covered twice
            pieces.append({"strip": i + 1, "length": L, "width": w, "laid": cov + (k - 1) * e * w, "splices": k - 1})
            laid += cov + (k - 1) * e * w
            outside += w * L - cov                              # cut off at the wall line (a stepped wall)
    return {"n": n, "widths": widths, "pieces": pieces, "cuts": cuts, "laid": laid, "trims": trims, "outside": outside}


def floor_side_laps(poly, W, s, along):
    """the side-lap area inside the area (mm2): the area covered twice where neighbouring strips overlap."""
    P = poly if along == "X" else _swap(poly)
    sl = _slabs(P)
    y0, y1 = min(p[1] for p in P), max(p[1] for p in P)
    n, widths = strips(y1 - y0, W, s)
    tot = 0
    for i in range(1, n):
        ya, yb = y0 + i * (W - s), y0 + i * (W - s) + s           # the band strip i laps over strip i - 1
        tot += sum((min(sb, yb) - max(sa, ya)) * sum(b - a for a, b in xs)
                   for sa, sb, xs in sl if min(sb, yb) > max(sa, ya))
    return tot


def polygon_area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) // 2


def perimeter(poly):
    return sum(abs(poly[(i + 1) % len(poly)][0] - poly[i][0]) + abs(poly[(i + 1) % len(poly)][1] - poly[i][1])
               for i in range(len(poly)))


# ------------------------------------------------------------------------------------------------ band
def lanes_of(trim_w, length, b):
    """whole band lanes of width b from an offcut trim_w x length -> (lanes, scrap mm2)."""
    k = trim_w // b
    return [length] * k, (trim_w - k * b) * length


def cover(runs, pool, e):
    """cover the runs [(length, closed)] or [(length, closed, started)] from the pool of lane lengths (mm), as far as
    the pool goes. A piece after the first of an open run, and every piece of a closed loop, laps e onto the piece
    before it. Lane choice: the shortest lane that finishes the run, else the longest lane (if it covers anything past
    its lap). -> (pieces [(length, lapped)], pool left, rest): rest = the runs still to cover, the current one with
    what is left of it and started=True (empty when the band is finished)."""
    pool = sorted(pool)
    pieces = []
    todo = [tuple(r) + (False,) if len(r) == 2 else tuple(r) for r in runs]
    while todo:
        L, closed, started = todo[0]
        rem = L
        while rem > 0:
            lap = e if (closed or started) else 0
            fit = [x for x in pool if x >= rem + lap]
            if fit:
                x = min(fit)
            elif pool and pool[-1] > lap:
                x = pool[-1]
            else:
                return pieces, pool, [(rem, closed, started)] + todo[1:]
            pool.remove(x)
            used = min(x, rem + lap)
            pieces.append((used, lap > 0))
            rem -= used - lap
            if x - used > 0:
                pool.append(x - used)
                pool.sort()
            started = True
        todo.pop(0)
    return pieces, pool, []


def min_segment(rest, pool, k, e, L_roll, step=10):
    """the shortest new full-width segment (a multiple of `step` mm) whose k lanes, with what is left of the pool,
    finish the rest of the band: searched upward from (remaining need / k) - never a formula.
    -> (segment, pieces, pool left) or None (more than one roll length of lanes)."""
    need = sum(r[0] for r in rest)
    seg = ceil_to(max(1, -(-need // k)), step)
    while seg <= L_roll:
        pieces, left, todo = cover(rest, list(pool) + [seg] * k, e)
        if not todo:
            return seg, pieces, left
        seg += step
    return None


# ------------------------------------------------------------------------------------------------ rolls
def min_rolls(pieces, L_roll):
    """the fewest rolls of length L_roll the full-width pieces can be cut from: exhaustive branch and bound (no
    first-fit). -> (rolls, [[pieces of each roll]])."""
    ps = sorted(pieces, reverse=True)
    lb = -(-sum(ps) // L_roll)
    best = [len(ps) + 1, None]

    def go(i, bins):
        if len(bins) >= best[0]:
            return
        if i == len(ps):
            best[0], best[1] = len(bins), [list(b) for b in bins]
            return
        seen = set()
        for b in bins:
            room = L_roll - sum(b)
            if ps[i] <= room and room not in seen:
                seen.add(room)
                b.append(ps[i])
                go(i + 1, bins)
                b.pop()
                if best[0] == lb:
                    return
        bins.append([ps[i]])
        go(i + 1, bins)
        bins.pop()
    go(0, [])
    return best[0], best[1]


def tails(rolls, L_roll):
    return sorted(L_roll - sum(r) for r in rolls)


# ------------------------------------------------------------------------------------------------ the area
def membrane(area, *, W=1000, L_roll=10000, s=100, e=100, h=200, along="X", band_split=None):
    """the whole membrane of one area (mm inputs):
        area: {"poly": [(x, y)...] rectilinear, "runs": [(length, closed)] eligible upturn runs,
               "doorways": [(width, depth)] doorway continuation pieces, "patches": [(a, b, count)] detail patches}
        band_split: None, or a list of new band segment lengths the plan cuts instead of the minimum single segment
                    (e.g. two segments sized to existing roll tails) - checked to cover the band
    -> quantities in metres / square metres and the cutting plan."""
    b = h + s
    k = W // b
    fl = floor(area["poly"], W, s, e, L_roll, along)
    A = polygon_area(area["poly"])
    pool, scrap = [], fl["outside"]
    for tw, ln in fl["trims"]:
        got, sc = lanes_of(tw, ln, b) if tw >= b else ([], tw * ln)
        pool += got
        scrap += sc
    cuts = list(fl["cuts"])
    door_pieces = []
    for w, t in area.get("doorways", ()):
        pw = t + s                                           # the doorway piece laps s onto the floor membrane
        if pw > b:
            raise ValueError("a doorway piece wider than a band lane is outside this reference")
        fit = [x for x in pool if x >= w]
        if fit:
            x = min(fit)
            pool.remove(x)
            if x - w > 0:
                pool.append(x - w)
        else:                                                # a new segment as long as the door is wide
            cuts.append(w)
            pool += [w] * (k - 1)
            scrap += (W - k * b) * w
        scrap += (b - pw) * w if pw < b else 0
        door_pieces.append((w, pw))
    patches = 0
    for pa, pb, n in area.get("patches", ()):                  # membrane patches of a detail (a <= b)
        a_, b_ = sorted((pa, pb))
        patches += n * a_ * b_
        if a_ <= b:                                          # narrower than a lane: from the lanes
            for _ in range(n):
                fit = [x for x in pool if x >= b_]
                if fit:
                    x = min(fit)
                    pool.remove(x)
                    if x - b_ > 0:
                        pool.append(x - b_)
                else:
                    cuts.append(b_)
                    pool += [b_] * (k - 1)
                    scrap += (W - k * b) * b_
                scrap += (b - a_) * b_
        else:                                                # side by side across a full-width segment of length b_
            per = W // a_
            for i in range(-(-n // per)):
                cuts.append(b_)
                rest_w = W - min(per, n - i * per) * a_
                got, sc = lanes_of(rest_w, b_, b)
                pool += got
                scrap += sc
    runs = list(area["runs"])
    pieces, left, rest = cover(runs, pool, e)                 # the offcut lanes first
    new_segments = []
    if rest:
        if band_split is None:
            got = min_segment(rest, left, k, e, L_roll)
            if got is None:
                raise ValueError("the band needs more than one roll length of lanes")
            seg, more, left = got
            new_segments = [seg]
        else:
            new_segments = list(band_split)
            more, left, todo = cover(rest, list(left) + [x for sg in band_split for x in [sg] * k], e)
            if todo:
                raise ValueError(f"the band split {band_split} does not cover the band")
        pieces = pieces + more
    for sg in new_segments:
        cuts.append(sg)
        scrap += (W - k * b) * sg
    scrap += sum(left) * b                                    # unused lanes
    band_len = sum(p for p, _ in pieces)
    joints = sum(1 for _, lapped in pieces if lapped)
    elig = sum(L for L, _ in runs)
    side = floor_side_laps(area["poly"], W, s, along)
    splices = sum(p["splices"] for p in fl["pieces"])
    laps = {"floor_side": side,
            "floor_end": sum(e * p["width"] for p in fl["pieces"] for _ in range(p["splices"])),
            "band_to_floor": elig * s, "band_end": joints * b * e,
            "doorway_to_floor": sum(w * s for w, _ in door_pieces)}
    upturn = elig * h
    doorway_net = sum(w * t for w, t in area.get("doorways", ()))
    laid = fl["laid"] + sum(w * pw for w, pw in door_pieces) + band_len * b + patches
    B = A + upturn + doorway_net + sum(laps.values()) + patches
    consumed = sum(cuts) * W
    n_rolls, plan = min_rolls(cuts, L_roll)
    if laid != B:
        raise AssertionError(f"laid {laid} != A + upturn + doorway + laps {B}")
    if consumed != laid + scrap:
        raise AssertionError(f"consumed {consumed} != laid {laid} + scrap {scrap}")
    return {"A_m2": m2(A), "perimeter_m": m(perimeter(area["poly"])), "eligible_m": m(elig),
            "upturn_m2": m2(upturn), "doorway_net_m2": m2(doorway_net), "subtotal_A_upturn_m2": m2(A + upturn),
            "floor_strips": fl["n"], "strip_widths_m": [m(x) for x in fl["widths"]],
            "floor_cuts_m": [m(x) for x in fl["cuts"]], "floor_splices": splices,
            "floor_laid_m2": m2(fl["laid"]), "trimmed_at_walls_m2": m2(fl["outside"]),
            "band_width_m": m(b), "lanes_per_width": k, "band_pieces_m": sorted(m(p) for p, _ in pieces),
            "band_joints": joints, "new_band_segments_m": [m(x) for x in new_segments],
            "laps_m2": {k_: m2(v) for k_, v in laps.items()}, "laps_total_m2": m2(sum(laps.values())),
            "detailing_m2": m2(patches),
            "B_m2": m2(B), "consumed_m2": m2(consumed), "waste_m2": m2(consumed - laid),
            "cuts_m": sorted((m(x) for x in cuts), reverse=True), "rolls": n_rolls,
            "roll_plan_m": [[m(x) for x in r] for r in plan], "tails_m": [m(x) for x in tails(plan, L_roll)],
            "untouched_m2": m2(n_rolls * L_roll * W - consumed)}


def shared_rolls(cut_lists, L_roll=10000):
    """the fewest rolls for the full-width cuts of several areas of one membrane system (exact)."""
    return min_rolls([c for cl in cut_lists for c in cl], L_roll)



# ------------------------------------------------------------------------------------------------ doors
# The owner values typed from the registry 1.1.0 rules (UP-DOOR-OPEN-002, UP-DOOR-HGT-001); the 0.10 m pier is the
# engine's review threshold (not an owner standard: owner question N-2) and the 3.00 m reading reach is the engine's.
DOOR_NOMINAL_MM = {"INTERNAL_PVC": 1000, "BATHROOM_PVC": 900, "EXTERNAL_ALUMINIUM": 1000}
ALLOWANCE_MM, PIER_MM, REACH_MM = 100, 100, 3000
HEIGHT_MM = {"INTERNAL_PVC": 2200, "BATHROOM_PVC": 2200, "EXTERNAL_ALUMINIUM": 2200, "MAIN_ENTRANCE": 2500}
WALL_T_MM = 200


def door(plan, *, nominal_override=None):
    """the two-room plan of the door proof cases (mm): party wall x 4000..4200 between y 200 and 4200, the door gap
    y s0..s1; constraints along the wall: the exterior-wall junctions at y 200 / 4200, a partition across room A at
    y a_partition..+200, columns standing in the wall strip. -> the door's owner-rule values."""
    p = {"a_word": "BEDROOM", "b_word": "LIVING", "s0": 1500, "s1": 2400, "b_right": 8200,
         "columns": [[600, 3400]]}
    p.update({k: v for k, v in plan.items() if k not in ("rules",)})
    s0, s1 = p["s0"], p["s1"]
    cad = s1 - s0
    cat = "BATHROOM_PVC" if "BATH" in p["a_word"] else "INTERNAL_PVC"
    nom = nominal_override if nominal_override is not None else DOOR_NOMINAL_MM[cat]
    req = nom + ALLOWANCE_MM
    need = max(0, req - cad)
    # constraints along the wall line: (position y, kind)
    cons = [(200, "JUNCTION"), (4200, "JUNCTION")]
    if p.get("a_partition") is not None:
        cons += [(p["a_partition"], "JUNCTION"), (p["a_partition"] + 200, "JUNCTION")]
    for cx, cy in p["columns"]:
        if cx < 4200 and cx + 400 > 4000:                     # the column stands in the wall strip
            cons += [(cy, "COLUMN"), (cy + 400, "COLUMN")]

    def side(jamb, sign):
        best = None
        for y, kind in cons:
            d = (y - jamb) * sign
            if d >= 0 and (best is None or d < best[0]):
                best = (d, kind)
        if best is None or best[0] > REACH_MM:
            return {"plain": REACH_MM, "kind": "OPEN_RUN"}
        return {"plain": best[0], "kind": best[1]}
    st, en = side(s0, -1), side(s1, +1)
    av = {k: max(0, v["plain"] - (0 if v["kind"] == "COLUMN" else PIER_MM)) for k, v in (("S", st), ("E", en))}
    place = None
    if need:
        if av["S"] >= need / 2 and av["E"] >= need / 2:
            place = ("SPLIT_EQUAL", need / 2, need / 2)
        elif av["S"] >= need:
            place = ("START_SIDE", need, 0)
        elif av["E"] >= need:
            place = ("END_SIDE", 0, need)
        elif av["S"] + av["E"] >= need:
            place = ("UNEQUAL", need - av["E"], av["E"])
    depth_b = p["b_right"] - 4200
    swing = None if not need else ("CONFLICT" if nom > depth_b else "CLEAR")
    rule_struct = next((r["value"] for r in plan.get("rules", ()) if r.get("parameter") == "wall_structure"), None)
    structure = {"NON_STRUCTURAL": "NON_STRUCTURAL_SPECIFIED", "STRUCTURAL": "STRUCTURAL"}.get(
        rule_struct, "MASONRY_INDICATED" if p["columns"] else "UNKNOWN")
    if not need:
        feas = "STANDARD_FITS_AS_DRAWN"
    elif structure in ("UNKNOWN", "STRUCTURAL"):
        feas = "ENLARGEMENT_REQUIRES_ENGINEERING_REVIEW"
    elif swing == "CONFLICT" or place is None:
        feas = "ENLARGEMENT_CONSTRAINED"
    else:
        feas = "ENLARGEMENT_GEOMETRICALLY_POSSIBLE"
    H = HEIGHT_MM[cat]
    return {"category": cat, "cad_wall_opening_m": m(cad), "required_nominal_door_m": m(nom),
            "required_wall_opening_m": m(req), "available_nominal_m": m(cad - ALLOWANCE_MM), "enlargement_m": m(need),
            "start_constraint": st["kind"], "start_plain_m": m(st["plain"]), "end_constraint": en["kind"],
            "end_plain_m": m(en["plain"]), "max_feasible_enlargement_m": m(av["S"] + av["E"]) if need else None,
            "placement": place[0] if place else None, "placement_start_m": m(place[1]) if place else None,
            "placement_end_m": m(place[2]) if place else None, "swing": swing, "leaf_m": m(nom),
            "structure": structure, "feasibility": feas, "door_that_fits_m": m(cad - ALLOWANCE_MM),
            "height_m": m(H), "assumed_area_m2": m2(cad * H),
            "jamb_plaster_m2": m2(2 * WALL_T_MM * H + WALL_T_MM * cad)}


def main_entrance(width_mm):
    H = HEIGHT_MM["MAIN_ENTRANCE"]
    return {"category": "MAIN_ENTRANCE", "cad_wall_opening_m": m(width_mm), "height_m": m(H),
            "assumed_area_m2": m2(width_mm * H), "jamb_plaster_m2": m2(2 * WALL_T_MM * H + WALL_T_MM * width_mm)}

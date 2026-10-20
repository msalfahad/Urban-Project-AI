"""MEMBRANE FOLD V5 (task T-124; opt-in, read by no released method) - MEMBRANE_FOLD_V4's layouts with the owner Q-58 A
roll count made on ONE set of rolls, so that every leftover is booked once.

The defect it fixes (found by T-120, fixture X; general to every villa): MEMBRANE_FOLD_V3.counts (and V4, which calls
it) places the pieces cut from offcuts into the leftovers of the MAIN strips' packing alone, then packs the pieces that
did not fit together with the main strips into new bins. The second packing can fill the very roll end the first step
promised away: an 11.00 x 5.50 m roof less 1.00 x 3.00 m claims 8 rolls with four 1.00 x 1.00 m patch pieces, while
8 rolls of the 76.50 m of main strips leave only 3.50 m of full-width roll end (4.00 m needed). V3 / V4 / V2.12 /
V2.13 are not edited (V2.13 already refuses such a count by its own proof); this version counts A correctly.

What V5 does (no new rule and no new tolerance; strips, upturn-only strips, patches and B / C counts are V4's):
    pieces      main strip pieces (band width x length) are always cut from a roll (owner Q-30 / Q-35 C). The other
                pieces of the area (owner Q-58 A): each upturn-only strip piece (need width = residual extent + lap
                per joining side, MEMBRANE_FOLD_V3) and each patch piece (along x across; a patch wider than the roll is
                cut in roll-width pieces, the last one only as wide as is left)
    plan A      a fixed point on one set of rolls: pack the pieces cut from rolls (MEMBRANE_LAYOUT.pack_rolls), lay
                each roll out (longest piece first from the roll's start), list its real offcuts (the full-width roll
                end; the side trim beside every piece narrower than the roll), place every other piece in an offcut
                (largest first into the smallest offcut that holds it, no turning: the strip direction is the roll's
                length); an offcut that takes a piece is split once into the length beyond it and the width beside
                it, so a leftover shrinks after every piece and is never used twice. A piece no offcut holds is moved
                to the pieces cut from rolls and everything is packed and placed again, until every piece has a place.
                It ends at the latest when every piece is cut from a roll, i.e. at the Q-58 B packing: A <= B always.
    check       the plan is checked on the rectangles themselves (shapely): every piece inside its roll, no two pieces
                overlapping, every listed piece placed once, the roll count = the rolls of the plan. A plan that
                fails raises FoldError (never a silent count).
    ledger      kept apart per layout (owner 2026-10-20 17:54 (5)): installed m2 (floor + 0.20 m upturn with mitred
                corners + opening upturns, the surface V3 must cover), floor m2, upturn m2, gross cut m2 (every piece
                as cut), lap m2 (side and splice laps of the main strips + the laps and over-cover of the upturn-only
                pieces), trim m2 (main strip beyond the surface + the corner trim of rectangular patch pieces), offcut
                left m2 (rolls x roll area - gross cut), rolls; plus the balance check installed = gross - lap - trim.
    audit       audit_v3(layout, spec) checks a MEMBRANE_FOLD_V3 / V4 Q-58 A count against the rolls V3 itself
                packs: VALID (a placement of V3's own-offcut pieces on those rolls is shown), INVALID (proven
                impossible: a piece larger than every offcut, the wide pieces longer than the roll ends together, or
                more piece area than free area) or NOT_PROVEN (neither), with the V5 count as the corrected figure.
    choice      owner Q-49 A over every layout of every wall frame (V4) with the V5 A count: fewest rolls, tie the
                shorter strip metres, then the smaller cut m2, then the listed order. Same fewest under A / B / C ->
                RELEASED; otherwise HELD_Q58 with low / high (owner Q-58 A is conditional; never 0).

    plan_q58_a(layout_frame_polygon, lay, spec) -> the plan A of one layout (rolls, pieces with positions, offcuts left)
    audit_v3(lay, spec)                          -> VALID / INVALID / NOT_PROVEN for a V3 / V4 Q-58 A count
    fold(polygon, holes, unit_m, spec)           -> MEMBRANE_FOLD_V4.fold + "layouts_v5" + "choice_v5" + flags
    plan(polygon, ...)                           -> one area alone, or a HELD row (never 0)
Project-agnostic: no layer, room name, size or count of any project. shapely 2 (requirements.txt)."""

from __future__ import annotations

import math

from shapely.geometry import box
from shapely.ops import unary_union

from engine.source import membrane_fold_v3 as F3
from engine.source import membrane_fold_v4 as F4
from engine.source import membrane_layout as ML

METHOD_ID = "MEMBRANE_FOLD_V5"
EPS = F3.EPS
BASES = F3.BASES
Q49_A = F4.Q49_A
Q58 = F4.Q58
VALID, INVALID, NOT_PROVEN = "VALID", "INVALID", "NOT_PROVEN"
ROLL_END, SIDE_TRIM = "ROLL_END", "SIDE_TRIM"
RULES = tuple(F4.RULES) + ("owner Q-58 A: each leftover of the area booked once, on the rolls actually bought (T-124)",)
DEFAULT = dict(F4.DEFAULT)
FoldError = F4.FoldError
NOT_PLANNABLE = "HELD_PIECE_LARGER_THAN_ROLL"


class PieceTooLarge(FoldError):
    """a piece longer or wider than one roll: no plan cuts it from one roll (a patch is not spliced: its laps are by
    detail, no Urban rule), so the layout's Q-58 A / B counts are held, never counted as one roll."""
BALANCE_TOL_M2 = F3.NUMERIC_M2          # the V2 coverage limit (1 cm2), not a new tolerance


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------ pieces
def pieces(lay, spec):
    """(main pieces, other pieces) of one V3 / V4 layout. Main: every MAIN strip piece, width = the band width. Other:
    every upturn-only strip piece (width = its need width) and every patch piece (length = along the strips; a patch
    wider than the roll in roll-width pieces, the last only as wide as is left)."""
    W = spec["roll_width_m"]
    main, other = [], []
    for k, s in enumerate(lay["strips"], 1):
        for j, x in enumerate(s["piece_lengths_m"], 1):
            if s["kind"] == "MAIN":
                main.append({"id": f"S{k}.{j}", "what": "MAIN", "w": s["width_m"], "l": x})
            else:
                other.append({"id": f"U{k}.{j}", "what": s["kind"], "w": s["need_width_m"], "l": x})
    for k, q in enumerate(lay["patches"], 1):
        n = max(1, math.ceil(q["across_m"] / W - EPS))
        for j in range(n):
            other.append({"id": f"P{k}.{j + 1}", "what": q["kind"], "w": _r(min(W, q["across_m"] - j * W), 6),
                          "l": q["along_m"]})
    return main, other


# ------------------------------------------------------------------------------------------------ one set of rolls
def _rolls(cut, L, W):
    """the pieces cut from rolls packed into whole rolls and laid out: -> (rolls, free offcuts, packing info)."""
    bins, info = ML.pack_rolls([p["l"] for p in cut], L) if cut else ([], {"proven": True, "lower_bound": 0})
    rolls, free = [], []
    for k, b in enumerate(sorted(bins, key=lambda b: min(b)), 1):
        x, on = 0.0, []
        for i in sorted(b, key=lambda i: (-cut[i]["l"], i)):
            p = cut[i]
            on.append(dict(p, roll=k, x0=x, x1=x + p["l"], y0=0.0, y1=p["w"], source="ROLL"))
            if W - p["w"] > EPS:
                free.append({"roll": k, "kind": SIDE_TRIM, "of": p["id"], "x0": x, "x1": x + p["l"], "y0": p["w"],
                             "y1": W})
            x += p["l"]
        if L - x > EPS:
            free.append({"roll": k, "kind": ROLL_END, "of": f"roll {k}", "x0": x, "x1": L, "y0": 0.0, "y1": W})
        rolls.append({"roll": k, "pieces": on, "used_m": x})
    return rolls, free, info


def _ow(o):
    return o["y1"] - o["y0"]


def _ol(o):
    return o["x1"] - o["x0"]


def _place(own, rolls, free):
    """each piece into the smallest real offcut that holds it, largest piece first; the offcut is split once (length
    beyond, width beside) so it shrinks and is never used twice. -> (placed, not placed); rolls / free updated."""
    placed, rest = [], []
    for p in sorted(own, key=lambda e: (-e["w"] * e["l"], -e["l"], e["id"])):
        cand = [o for o in free if p["w"] <= _ow(o) + EPS and p["l"] <= _ol(o) + EPS]
        if not cand:
            rest.append(p)
            continue
        o = min(cand, key=lambda o: (_ow(o) * _ol(o), _ol(o), o["roll"], o["x0"], o["y0"]))
        free.remove(o)
        q = dict(p, roll=o["roll"], x0=o["x0"], x1=o["x0"] + p["l"], y0=o["y0"], y1=o["y0"] + p["w"],
                 source=f"OWN_{o['kind']}", offcut_of=o["of"], offcut_w=_r(_ow(o)), offcut_l=_r(_ol(o)))
        placed.append(q)
        rolls[o["roll"] - 1]["pieces"].append(q)
        if _ol(o) - p["l"] > EPS:
            free.append(dict(o, x0=o["x0"] + p["l"]))
        if _ow(o) - p["w"] > EPS:
            free.append(dict(o, x1=o["x0"] + p["l"], y0=o["y0"] + p["w"]))
    return placed, rest


def check_plan(rolls, expected_ids, W, L):
    """the plan checked on its rectangles: inside the roll, no overlap, every piece once. -> [failures]."""
    fails, seen = [], []
    for r in rolls:
        bx = []
        for q in r["pieces"]:
            seen.append(q["id"])
            if q["x0"] < -EPS or q["y0"] < -EPS or q["x1"] > L + EPS or q["y1"] > W + EPS:
                fails.append(f"OUTSIDE_ROLL: {q['id']} on roll {r['roll']}")
            if abs((q["x1"] - q["x0"]) - q["l"]) > EPS or abs((q["y1"] - q["y0"]) - q["w"]) > EPS:
                fails.append(f"SIZE: {q['id']} placed {q['x1'] - q['x0']:.4f} x {q['y1'] - q['y0']:.4f}")
            bx.append(box(q["x0"], q["y0"], q["x1"], q["y1"]))
        for i in range(len(bx)):
            for j in range(i + 1, len(bx)):
                if bx[i].intersection(bx[j]).area > 1e-8:
                    fails.append(f"OVERLAP: {r['pieces'][i]['id']} / {r['pieces'][j]['id']} on roll {r['roll']}")
    if sorted(seen) != sorted(expected_ids):
        fails.append("PIECES: the plan does not hold every piece exactly once")
    return fails


def _lower_bound(main, other, W, L):
    """rolls no plan can go below: the main strips' own packing bound and the total piece area over the roll area."""
    lb_main = ML.pack_rolls([p["l"] for p in main], L)[1].get("lower_bound", 0) if main else 0
    area = sum(p["w"] * p["l"] for p in main + other)
    return max(lb_main, math.ceil(area / (W * L) - 1e-9))


def plan_q58_a(lay, spec):
    """owner Q-58 A for one layout on ONE set of rolls (the fixed point above). -> dict with rolls, the plan, the
    pieces from rolls and from own offcuts, the offcuts left, the lower bound and the check."""
    W, L = spec["roll_width_m"], spec["roll_length_m"]
    main, other = pieces(lay, spec)
    return fixpoint(main, other, W, L)


def fixpoint(main, other, W, L):
    """the plan A of given pieces: main pieces from rolls, the other pieces in own offcuts of the same rolls when one
    holds them, else from a roll; packed and placed again until every piece has a place (see the module text)."""
    for p in main + other:
        if p["l"] > L + EPS or p["w"] > W + EPS or p["l"] <= 0 or p["w"] <= 0:
            raise PieceTooLarge(f"piece {p['id']} ({p['what']}) {p['w']} x {p['l']} m does not fit a {W} x {L} m "
                                f"roll")
    cut, own, rounds = list(main), list(other), 0
    while True:
        rounds += 1
        rolls, free, info = _rolls(cut, L, W)
        placed, rest = _place(own, rolls, free)
        if not rest:
            break
        moved = {p["id"] for p in rest}
        cut = cut + sorted(rest, key=lambda p: p["id"])
        own = [p for p in own if p["id"] not in moved]
    fails = check_plan(rolls, [p["id"] for p in main + other], W, L)
    if fails:
        raise FoldError("Q-58 A plan failed its check: " + "; ".join(fails))
    left = sorted(({"roll": o["roll"], "kind": o["kind"], "width_m": _r(_ow(o)), "length_m": _r(_ol(o))}
                   for o in free if _ol(o) > EPS and _ow(o) > EPS), key=lambda o: (o["roll"], o["kind"], -o["length_m"]))
    gross = sum(p["w"] * p["l"] for p in main + other)
    return {"rule": Q58, "reading": "Q58_A", "rolls": len(rolls), "rounds": rounds,
            "lower_bound": _lower_bound(main, other, W, L), "packing_minimal_proven": bool(info.get("proven")),
            "pieces_from_rolls": [{k: p[k] for k in ("id", "what", "w", "l")} for p in cut],
            "pieces_from_own_offcuts": [{k: (_r(v, 6) if isinstance(v, float) else v) for k, v in q.items()}
                                        for q in placed],
            "plan": [{"roll": r["roll"], "used_m": _r(r["used_m"]), "left_m": _r(L - r["used_m"]),
                      "pieces": [{k: (_r(v, 6) if isinstance(v, float) else v) for k, v in q.items()}
                                 for q in r["pieces"]]} for r in rolls],
            "offcuts_left": left, "gross_cut_m2": _r(gross, 6),
            "offcut_left_m2": _r(len(rolls) * W * L - gross, 6), "check": "PASSED"}


# ------------------------------------------------------------------------------------------------ audit of V3 counts
def audit_v3(lay, spec):
    """a MEMBRANE_FOLD_V3 / V4 Q-58 A count checked on the rolls V3 itself packs (main pieces + the pieces it cuts from
    rolls): its own-offcut pieces placed in the real offcuts of THOSE rolls. -> {verdict, claimed, corrected, why,
    leftovers (V3's promise on the main-only packing), final rolls}."""
    W, L = spec["roll_width_m"], spec["roll_length_m"]
    c = lay["counts"]["Q58_A"]
    main, _other = pieces(lay, spec)
    rest = [{"id": f"X{k}", "what": e["what"], "w": e["w"], "l": e["l"]}
            for k, e in enumerate(c["pieces_from_rolls"], 1)]
    own = [{"id": f"O{k}", "what": e["what"], "w": e["w"], "l": e["l"],
            "promised": f"{e.get('offcut')} {e.get('offcut_w')} x {e.get('offcut_l')}"}
           for k, e in enumerate(c["pieces_from_own_offcuts"], 1)]
    promise = []
    bins_m = ML.pack_rolls([p["l"] for p in main], L)[0] if main else []
    for k, b in enumerate(sorted(bins_m, key=lambda b: min(b)), 1):
        u = sum(main[i]["l"] for i in b)
        promise.append({"roll": k, "used_m": _r(u), "left_m": _r(L - u)})
    rolls, free, _info = _rolls(main + rest, L, W)
    out = {"claimed": c["rolls"], "rolls_v3_packs": len(rolls), "own_offcut_pieces": len(own),
           "v3_leftovers_main_only": promise,
           "final_roll_ends_m": [_r(_ol(o)) for o in free if o["kind"] == ROLL_END],
           "final_side_trims": [(_r(_ow(o)), _r(_ol(o))) for o in free if o["kind"] == SIDE_TRIM]}
    why = []
    if len(rolls) != c["rolls"]:
        why.append(f"COUNT: V3's pieces from rolls pack into {len(rolls)} rolls, it counts {c['rolls']}")
    # necessary conditions (a failure proves the count impossible)
    for p in own:
        if not any(p["w"] <= _ow(o) + EPS and p["l"] <= _ol(o) + EPS for o in free):
            why.append(f"NO_OFFCUT_HOLDS: {p['what']} {p['w']:.3f} x {p['l']:.3f} m")
    trim_w = max((_ow(o) for o in free if o["kind"] == SIDE_TRIM), default=0.0)
    wide = [p for p in own if p["w"] > max(trim_w, W / 2.0) + EPS]   # cannot lie in a trim, nor two side by side
    ends = sum(_ol(o) for o in free if o["kind"] == ROLL_END)
    if sum(p["l"] for p in wide) > ends + EPS:
        why.append(f"ROLL_ENDS_TOO_SHORT: {len(wide)} piece(s) wider than every trim and half the roll need "
                   f"{sum(p['l'] for p in wide):.3f} m of roll end, the rolls leave {ends:.3f} m")
    free_m2 = sum(_ow(o) * _ol(o) for o in free)
    if sum(p["w"] * p["l"] for p in own) > free_m2 + 1e-9:
        why.append(f"AREA: own-offcut pieces {sum(p['w'] * p['l'] for p in own):.4f} m2 > offcuts {free_m2:.4f} m2")
    placed, miss = _place(own, rolls, free)
    try:
        v5 = plan_q58_a(lay, spec)["rolls"]
    except PieceTooLarge:
        v5 = None
    try:
        same = fixpoint(main, [dict(p) for p in rest] + [{k: p[k] for k in ("id", "what", "w", "l")} for p in own],
                        W, L)["rolls"]
    except PieceTooLarge as ex:
        same = None
        why.append(f"PIECE_LARGER_THAN_ROLL: {ex}")
    if why:
        verdict = INVALID
    elif not miss and not check_plan(rolls, [p["id"] for p in main + rest + own], W, L):
        verdict = VALID
    else:
        verdict = NOT_PROVEN
        why.append("no placement found for " + ", ".join(f"{p['what']} {p['w']:.3f} x {p['l']:.3f}" for p in miss))
    out.update(verdict=verdict, why=why, corrected=same if verdict != VALID else c["rolls"],
               corrected_note="the same pieces as V3 (its widths), each leftover booked once (fixpoint)",
               v5_rolls=v5, v5_note="V5's own pieces (a patch wider than the roll: last piece only as wide "
                                             "as is left)",
               placement=[{k: (_r(v, 4) if isinstance(v, float) else v) for k, v in q.items()} for q in placed])
    return out


# ------------------------------------------------------------------------------------------------ ledger
def ledger(p, lay, spec, floor_m2, a_plan):
    """installed, upturn, gross cut, laps, trims and offcuts kept apart for one layout (p in the layout frame)."""
    h, W, L, lap = spec["upturn_h_m"], spec["roll_width_m"], spec["roll_length_m"], spec["lap_m"]
    geo = F3.strips(p, h, W, L, lap)
    outer, opening = F3.required(p, h)
    req = outer if opening is None else unary_union([outer, opening])
    installed = req.area
    mains = [box(s["x0"], s["s0"], s["x1"], s["s1"]) for s in geo["main"]]
    M = unary_union(mains) if mains else None
    main_cut = sum(s["width_m"] * x for s in geo["main"] for x in s["piece_lengths_m"])
    main_union = M.area if M is not None else 0.0
    main_in = M.intersection(req).area if M is not None else 0.0
    up_cut = sum(s["need_width_m"] * x for s in geo["added"] for x in s["piece_lengths_m"])
    up_res = sum(s["residual_m2"] for s in geo["added"])
    patch_m2 = sum(q["m2"] for q in lay["patches"])
    patch_cut = sum(q["along_m"] * q["across_m"] for q in lay["patches"])
    lap_m2 = (main_cut - main_union) + (up_cut - up_res)
    trim_m2 = (main_union - main_in) + (patch_cut - patch_m2)
    gross = main_cut + up_cut + patch_cut
    covered = main_in + up_res + patch_m2 + lay["numerical_residual_m2"]
    rolls = a_plan["rolls"]
    bought = None if rolls is None else rolls * W * L
    return {"installed_m2": _r(installed, 4), "floor_m2": _r(floor_m2, 4), "upturn_m2": _r(installed - floor_m2, 4),
            "gross_cut_m2": _r(gross, 4), "lap_m2": _r(lap_m2, 4), "trim_m2": _r(trim_m2, 4),
            "offcut_left_m2": None if bought is None else _r(bought - gross, 4), "rolls_q58_a": rolls,
            "roll_m2_bought": _r(bought, 4),
            "balance_m2": _r(installed - covered, 6),
            "balanced": abs(installed - covered) <= BALANCE_TOL_M2}


# ------------------------------------------------------------------------------------------------ fold
def _key(lay, basis):
    n = lay["rolls_v5"][basis]
    return (math.inf if n is None else n, round(lay["strip_metres"], 4), round(lay["cut_m2"], 4), lay["index"])


def fold(polygon, *, holes=(), unit_m=1.0, spec=None):
    """MEMBRANE_FOLD_V4.fold (unchanged) + per layout the Q-58 A plan on one set of rolls, the V3 audit and the ledger,
    + the owner Q-49 A choice with the V5 A count."""
    spec = dict(DEFAULT, **(spec or {}))
    base = F4.fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    frs = base["frames_v4"]
    lays = []
    for x in base["layouts_v4"]:
        fi = x["frame"]
        if fi == 0:
            pf, _td = F3._frame(polygon, holes, unit_m)
        else:
            pf, _td = F4._frame_at(polygon, holes, unit_m, frs[fi]["frame_deg"])
        p = F3._to_layout(pf, x["direction"], x["start"])
        try:
            a = plan_q58_a(x, spec)
            b = x["rolls_by_basis"]["Q58_B"]
        except PieceTooLarge as ex:            # V3 / V4 count such a piece as if it fitted one roll: held here
            a, b = {"rolls": None, "state": NOT_PLANNABLE, "reason": str(ex), "plan": [], "pieces_from_rolls": [],
                    "pieces_from_own_offcuts": [], "offcuts_left": [], "lower_bound": None}, None
        au = audit_v3(x, spec)
        rv = {"Q58_A": a["rolls"], "Q58_B": b, "Q58_C": x["rolls_by_basis"]["Q58_C"]}
        if rv["Q58_A"] is not None and rv["Q58_A"] > rv["Q58_B"]:
            raise FoldError("Q-58 A plan needs more rolls than cutting every piece from a roll")
        lays.append({"index": x["index"], "name": x["name"], "frame": fi, "direction": x["direction"],
                     "start": x["start"], "strip_metres": x["strip_metres"], "cut_m2": x["cut_m2"],
                     "rolls_v4": dict(x["rolls_by_basis"]), "rolls_v5": rv, "plan_q58_a": a, "audit_v3_a": au,
                     "ledger": ledger(p, x, spec, base["floor_m2"], a)})
    pick = {b: min(lays, key=lambda y: _key(y, b))["index"] for b in BASES}
    mins = {b: lays[pick[b]]["rolls_v5"][b] for b in BASES}
    known = [v for v in mins.values() if v is not None]
    released = None not in mins.values() and len(set(mins.values())) == 1
    sel = lays[pick["Q58_A"]]
    old = base["choice_v4"]["by_reading"]["Q58_A"]["rolls"]
    flags = list(base.get("flags_v4") or ())
    if any(y["audit_v3_a"]["verdict"] == INVALID for y in lays):
        flags.append("V3_Q58_A_COUNT_INVALID_IN_A_LAYOUT")
    if any(y["audit_v3_a"]["verdict"] == NOT_PROVEN for y in lays):
        flags.append("V3_Q58_A_COUNT_NOT_PROVEN_IN_A_LAYOUT")
    if any(y["plan_q58_a"].get("state") == NOT_PLANNABLE for y in lays):
        flags.append("PIECE_LARGER_THAN_ROLL_IN_A_LAYOUT")
    if mins["Q58_A"] != old:
        flags.append("CHOSEN_Q58_A_ROLLS_CORRECTED")
    if not all(y["ledger"]["balanced"] for y in lays):
        flags.append("LEDGER_NOT_BALANCED")                 # shown, never hidden: see ledger balance_m2
    choice = {"rule": Q49_A, "open_rule": Q58, "state": "RELEASED" if released else "HELD_Q58",
              "by_reading": {b: {"layout": pick[b], "name": lays[pick[b]]["name"], "rolls": mins[b]} for b in BASES},
              "rolls": mins["Q58_B"] if released else None,
              "rolls_bounded": None if released or not known else {"low": min(known), "high": max(known)},
              "q58_a": {"layout": sel["index"], "name": sel["name"], "rolls": mins["Q58_A"],
                        "v4_claimed": old, "plan": sel["plan_q58_a"]["plan"], "ledger": sel["ledger"]}}
    base.update(method_v5=METHOD_ID, layouts_v5=lays, choice_v5=choice, flags_v5=flags)
    return base


def plan(polygon, *, holes=(), unit_m=1.0, spec=None, floor=None, room_id=None, name=None, group="WET_AREA"):
    """one area alone (owner Q-49 A); a missing or unusable input -> HELD (never 0)."""
    spec = dict(DEFAULT, **(spec or {}))
    base = {"method": METHOD_ID, "floor": floor, "room_id": room_id, "name": name, "group": group}
    for k in DEFAULT:
        if spec.get(k) is None or spec[k] <= 0:
            return dict(base, state="HELD", reason=f"MISSING_INPUT_{k.upper()}", choice=None)
    if spec["lap_m"] >= spec["roll_width_m"] or spec["lap_m"] >= spec["roll_length_m"]:
        return dict(base, state="HELD", reason="LAP_NOT_SMALLER_THAN_ROLL", choice=None)
    if not polygon:
        return dict(base, state="HELD", reason="NO_OUTLINE", choice=None)
    try:
        f = fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    except FoldError as ex:
        return dict(base, state="HELD", reason=f"OUTLINE_NOT_USABLE: {ex}", choice=None)
    return dict(base, state="COMPUTED", floor_m2=f["floor_m2"], choice=f["choice_v5"], flags=f["flags_v5"])


def policy_record():
    return {"method": METHOD_ID, "rules": list(RULES), "defaults": dict(DEFAULT), "bases": dict(F3.BASIS_TEXT),
            "purchase_rule": Q49_A, "open_rule": Q58,
            "replaces_nothing": "beside MEMBRANE_FOLD_V3 / V4 (unchanged); opt-in, read by no released method"}

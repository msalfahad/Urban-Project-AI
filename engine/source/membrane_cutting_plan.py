"""MEMBRANE CUTTING PLAN V1 (task T-089, opt-in; no released method or quantity changed) - per wet room and per roof,
EACH ALONE (owner Q-49 = A, 2026-10-19 22:35), the installer's cutting plan of the owner's strip method:

    every strip (width x length), which roll it is cut from and where on that roll, the rolls to buy, the leftover
    metres of full-width roll per roll and per area, the side trim m2 of the narrow strips (scrap), the own pieces of
    a skylight / opening upturn on a roof; project totals for wet areas, the pantry and roofs, each a sum of the areas;
    a text table and an SVG drawing per area (strips numbered, the roll number on each strip).

Built on MEMBRANE_FOLD_V2 (engine/source/membrane_fold_v2.py, read, never edited): its strips() lays the owner's strips
(Q-30 worked example: first strip W - h of floor, next W - lap, last strip cut; strips h longer at both ends, Q-35 C;
a strip longer than the roll spliced with the end lap, UP-WP-002). This module only lays them out four ways, packs them
into whole rolls and selects:

    candidates  two directions (along the room's longest wall / across it) x two start walls (the lower wall of the
                room frame / the opposite wall) - the four layouts MEMBRANE_FOLD_V2 already reports
    selection   owner Q-49 A: the layout with the fewest whole rolls; tie: the shorter total strip length (roll metres
                used). A remaining tie (the same rolls and the same metres) is reported with every tied layout listed,
                the first in candidate order is drawn (no quantity depends on it: rolls, metres and leftover are equal;
                the side trim of each tied layout is shown)
    rolls       the strip pieces packed whole into rolls (a piece is never cut across two rolls) by
                membrane_layout.pack_rolls (first fit decreasing, then an exact branch and bound when it does not meet
                the lower bound). Proof per area (scout answer R-05): lower bound L1 = ceil(sum of piece lengths /
                roll length); rolls = L1 -> optimal, one-line proof; rolls > L1 -> the gap is reported with the exact
                search's verdict (PROVEN_BY_EXHAUSTIVE_SEARCH or NOT_PROVEN)
    leftover    per roll: roll length - pieces cut from it (metres of full-width roll, reusable or returnable);
                per area: rolls x roll length - piece metres
    side trim   per narrow strip: (roll width - strip width) x piece length, m2 (scrap)
    identity    cut m2 + side trim m2 = piece metres x roll width (checked on every area)

Never: a held area as 0 (it is listed with its reason and left out of the sums, which say how many are held); rolls
from net area / roll area (the owner's ceil(cut / roll area) is shown beside, a difference flagged); a direction
chosen by anything but Q-49 A; offcuts carried from one area to another (Q-49 A: each room alone).

Inputs: lap 0.10 m, roll 1.00 x 10.00 m and the 0.20 m upturn come from the owner rules (UP-WP-001 / UP-WP-002 /
UP-WP-003) as inputs (spec), never constants of this module.

    plan(polygon, holes, unit_m, spec, floor, room_id, name, group)  -> one area's cutting plan (or HELD)
    held(floor, room_id, name, group, reason)                        -> a HELD area row
    project(areas)                                                   -> totals per group and overall, held listed
    text_table(area) / svg(area)                                     -> printable cutting plan of one area
Project-agnostic. shapely 2 (requirements.txt), no other dependency."""

from __future__ import annotations

import math

from shapely import affinity
from shapely.geometry import Polygon

from engine.source import membrane_fold_v2 as F
from engine.source import membrane_layout as ML

METHOD_ID = "MEMBRANE_CUTTING_PLAN_V1"
EPS = 1e-9
GROUPS = ("WET_AREA", "PANTRY", "ROOF")
PROOF_NODE_LIMIT = 5_000_000      # the second, longer exact search for an area whose rolls exceed the lower bound
LOWER, OPPOSITE = "LOWER_WALL_OF_ROOM_FRAME", "OPPOSITE_WALL"
CANDIDATES = ((F.ALONG_LONG, LOWER), (F.ALONG_LONG, OPPOSITE), (F.ACROSS, LOWER), (F.ACROSS, OPPOSITE))
RULES = ("owner Q-49 A (each wet room and each roof alone, fewest rolls, tie: shorter strip length)",
         "owner Q-30 (strip method)", "owner Q-35 C", "owner Q-37 A", "owner Q-24 + addendum (roofs like a bathroom)",
         "owner Q-29 (each dome an open skylight, 0.20 m upturn round it)", "UP-WP-001", "UP-WP-002", "UP-WP-003",
         "UP-QTY-STATUS-001")


class PlanError(ValueError):
    pass


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# the four layouts in the room frame pf (longest wall along x, lower-left at 0, 0): the polygon the strips are laid
# on, and the map from that layout's frame back to pf (for the drawing)
def _to_layout(pf, direction, start):
    p = pf if direction == F.ALONG_LONG else affinity.rotate(pf, 90.0, origin=(0.0, 0.0))
    if start == OPPOSITE:
        p = affinity.scale(p, 1.0, -1.0, origin=(0.0, 0.0))
    return p


def _back(direction, start):
    if direction == F.ALONG_LONG:
        return (lambda x, y: (x, y)) if start == LOWER else (lambda x, y: (x, -y))
    return (lambda x, y: (y, -x)) if start == LOWER else (lambda x, y: (-y, -x))


def _frame(polygon, holes, unit_m):
    ring, removed = F.clean_ring(polygon, unit_m)
    if len(ring) < 3:
        raise PlanError("the outline needs at least 3 points")
    hs = [F.clean_ring(h, unit_m)[0] for h in holes or ()]
    poly = Polygon(ring, [h for h in hs if len(h) >= 3])
    if not poly.is_valid or poly.area <= EPS:
        raise PlanError("the outline is not a simple polygon with an area")
    ang = F.room_frame(ring)
    c = poly.centroid
    pf = affinity.rotate(poly, -ang, origin=(c.x, c.y))
    pf = affinity.translate(pf, -pf.bounds[0], -pf.bounds[1])
    return poly, pf, ang, removed


def _layout(pf, direction, start, spec):
    h, W, L, lap = spec["upturn_h_m"], spec["roll_width_m"], spec["roll_length_m"], spec["lap_m"]
    p = _to_layout(pf, direction, start)
    ss = F.strips(p, h, W, L, lap)
    pieces = []
    for k, s in enumerate(ss, 1):
        n = len(s["piece_lengths_m"])
        for j, pl in enumerate(s["piece_lengths_m"]):
            pieces.append({"strip": k, "piece": j + 1, "pieces_in_strip": n, "width_m": s["width_m"],
                           "length_m": pl})
    lens = [pc["length_m"] for pc in pieces]
    bins, info = ML.pack_rolls(lens, L)
    if len(bins) > (info.get("lower_bound") or 0) and not info.get("proven"):
        # the exact search stopped at its default node limit: run it once more with PROOF_NODE_LIMIT (deterministic)
        bins2, info2 = ML.pack_rolls(lens, L, node_limit=PROOF_NODE_LIMIT)
        if len(bins2) <= len(bins):
            bins, info = bins2, info2
    rolls = []
    for rn, b in enumerate(bins, 1):
        pos = 0.0
        cuts = []
        for i in b:
            pc = pieces[i]
            pc["roll"] = rn
            pc["from_m"], pc["to_m"] = _r(pos), _r(pos + pc["length_m"])
            pos += pc["length_m"]
            cuts.append(i)
        rolls.append({"roll": rn, "pieces": cuts, "used_m": _r(pos), "leftover_m": _r(L - pos)})
    metres = sum(lens)
    cut = sum(pc["width_m"] * pc["length_m"] for pc in pieces)
    trim = sum((W - pc["width_m"]) * pc["length_m"] for pc in pieces if W - pc["width_m"] > 1e-9)
    lb = info.get("lower_bound") or 0
    if len(bins) <= lb:
        proof = (f"OPTIMAL: {len(bins)} roll(s) = lower bound ceil({metres:.2f} m / {L:.2f} m) = {lb}")
        proof_state = "OPTIMAL_AT_LOWER_BOUND"
    else:
        proof_state = "PROVEN_BY_EXHAUSTIVE_SEARCH" if info.get("proven") else "NOT_PROVEN"
        proof = (f"GAP: {len(bins)} roll(s) > lower bound ceil({metres:.2f} m / {L:.2f} m) = {lb}; "
                 f"{proof_state.lower().replace('_', ' ')} (no piece may be cut across two rolls)")
    # the drawing: each strip's sheet (x0..x1 along, s0..s1 across) and each splice, mapped back to the room frame
    back = _back(direction, start)
    sheets = []
    pi = 0
    for k, s in enumerate(ss, 1):
        n = len(s["piece_lengths_m"])
        xs = [s["x0"]]
        for j in range(n - 1):
            xs.append(xs[-1] + s["piece_lengths_m"][j] - lap)
        segs = []
        for j in range(n):
            a = xs[j]
            b = s["x1"] if j == n - 1 else xs[j] + s["piece_lengths_m"][j]
            corners = [back(a, s["s0"]), back(b, s["s1"])]
            segs.append({"piece": j + 1, "roll": pieces[pi + j]["roll"],
                         "box": (min(c[0] for c in corners), min(c[1] for c in corners),
                                 max(c[0] for c in corners), max(c[1] for c in corners))})
        pi += n
        sheets.append({"strip": k, "segments": segs})
    fold_cut = sum(s["width_m"] * s["length_m"] for s in ss)
    return {"direction": direction, "start": start, "strips": len(ss),
            "strip_list": [{"strip": k, "width_m": _r(s["width_m"]), "length_m": _r(s["length_m"]),
                            "floor_from_m": s["floor_from_m"], "floor_to_m": s["floor_to_m"],
                            "pieces": [{kk: pc[kk] for kk in ("piece", "length_m", "roll", "from_m", "to_m")}
                                       for pc in pieces if pc["strip"] == k]}
                           for k, s in enumerate(ss, 1)],
            "rolls": rolls, "rolls_to_buy": len(bins), "strip_metres": _r(metres),
            "leftover_m": _r(len(bins) * L - metres), "cut_m2": _r(cut), "side_trim_m2": _r(trim),
            "consumed_m2": _r(metres * W), "fold_v2_cut_m2": _r(fold_cut),
            "rolls_by_cut_area": math.ceil(round(cut, 6) / (W * L) - EPS) if cut > EPS else 0,
            "lower_bound": lb, "packing": info.get("method"), "proof_state": proof_state, "proof": proof,
            "_sheets": sheets}


def held(*, floor, room_id, name=None, group="WET_AREA", reason):
    """an area whose outline or wet status is held: listed with its reason, no number, never 0."""
    if group not in GROUPS:
        raise PlanError(f"unknown group {group}")
    return {"method": METHOD_ID, "floor": floor, "room_id": room_id, "name": name, "group": group, "state": "HELD",
            "reason": reason, "rolls_to_buy": None, "strip_metres": None, "leftover_m": None, "cut_m2": None,
            "side_trim_m2": None}


def plan(polygon, *, holes=(), unit_m=1.0, spec=None, floor=None, room_id=None, name=None, group="WET_AREA"):
    """the cutting plan of one area alone (Q-49 A): the four layouts, the selected one with every strip and roll."""
    if group not in GROUPS:
        raise PlanError(f"unknown group {group}")
    spec = dict(F.DEFAULT, **(spec or {}))
    for k in F.DEFAULT:
        if spec.get(k) is None or spec[k] <= 0:
            return held(floor=floor, room_id=room_id, name=name, group=group, reason=f"MISSING_INPUT_{k.upper()}")
    if spec["lap_m"] >= spec["roll_width_m"] or spec["lap_m"] >= spec["roll_length_m"]:
        return held(floor=floor, room_id=room_id, name=name, group=group, reason="LAP_NOT_SMALLER_THAN_ROLL")
    if not polygon:
        return held(floor=floor, room_id=room_id, name=name, group=group, reason="NO_OUTLINE")
    try:
        poly, pf, ang, removed = _frame(polygon, holes, unit_m)
        lays = [_layout(pf, d, s, spec) for d, s in CANDIDATES]
    except (PlanError, F.FoldError) as ex:
        return held(floor=floor, room_id=room_id, name=name, group=group, reason=f"OUTLINE_NOT_USABLE: {ex}")
    key = [(x["rolls_to_buy"], round(x["strip_metres"], 4)) for x in lays]
    best = min(key)
    tied = [i for i, k in enumerate(key) if k == best]
    sel = lays[tied[0]]
    flags = []
    if len({k[0] for k in key}) > 1:
        flags.append("LAYOUT_CHANGES_ROLLS")
    if len(tied) > 1:
        flags.append("TIE_SAME_ROLLS_AND_METRES")
    if sel["proof_state"] != "OPTIMAL_AT_LOWER_BOUND":
        flags.append("ROLLS_ABOVE_LOWER_BOUND")
    # a layout whose roll count the exact search did not prove could still win if its lower bound beats the selection
    unproven = [lays[i] for i in range(len(lays)) if lays[i]["proof_state"] == "NOT_PROVEN" and
                (lays[i]["lower_bound"], round(lays[i]["strip_metres"], 4)) < best]
    if unproven:
        flags.append("SELECTION_NOT_PROVEN")
    if sel["rolls_by_cut_area"] != sel["rolls_to_buy"]:
        flags.append("ROLL_COUNT_BASES_DIFFER")
    if any(pc["pieces"] and len(pc["pieces"]) > 1 for pc in sel["strip_list"]):
        flags.append("STRIP_SPLICED_WITH_END_LAP")
    if abs(sel["cut_m2"] + sel["side_trim_m2"] - sel["consumed_m2"]) > 1e-3:
        raise PlanError("identity cut + side trim = consumed failed")       # a code fault, never a quantity
    # coverage and the opening upturn come from the fold V2 check of the selected direction and start
    fv = F.fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    fd = {o["direction"]: o for o in fv["directions"]}[sel["direction"]]
    short = fd["upturn_shortfall_m2"] if sel["start"] == LOWER else fd["other_start"]["upturn_shortfall_m2"]
    if short:
        flags.append("UPTURN_SHORTFALL_BY_DETAIL")
    opening = None
    if poly.interiors:
        hu = fd["hole_upturn"] if sel["start"] == LOWER else None
        lm = sum(r.length for r in poly.interiors)
        opening = {"openings": len(poly.interiors), "upturn_lm": _r(lm), "upturn_m2": _r(lm * spec["upturn_h_m"]),
                   "folded_from_strips_m2": None if hu is None else hu["covered_by_strips_m2"],
                   "own_pieces_m2": None if hu is None else hu["own_pieces_m2"],
                   "own_pieces_in_roll_count": False,
                   "note": "skylight / opening upturn (Q-24, Q-29): the part the strips' sheet folds up is inside the "
                           "strips; the rest is own pieces by detail, reported in m2 and not in the roll count (no "
                           "Urban rule says how they are cut)"}
        if hu is None:
            # the fold V2 reports the opening split for the lower start only: recompute it for the opposite start
            opening.update(_hole_split(pf, sel, spec))
        flags.append("OPENING_UPTURN_OWN_PIECES")
    other = [{"strips_run_deg_mod90": x["frame_deg_mod90"],
              "least_rolls": min(y["rolls_if_alone"] for y in x["directions"])} for x in fv["other_frames"]]
    if other and min(o["least_rolls"] for o in other) < sel["rolls_to_buy"]:
        flags.append("ANOTHER_WALL_FRAME_NEEDS_FEWER_ROLLS")
    out = {"method": METHOD_ID, "floor": floor, "room_id": room_id, "name": name, "group": group,
           "state": "COMPUTED", "floor_m2": _r(poly.area), "boundary_lm": _r(poly.exterior.length +
                                                                           sum(r.length for r in poly.interiors)),
           "frame_deg": _r(ang, 4), "collinear_or_repeated_removed": removed,
           "selected": {k: v for k, v in sel.items() if not k.startswith("_")},
           "candidates": [{k: x[k] for k in ("direction", "start", "strips", "rolls_to_buy", "strip_metres",
                                             "leftover_m", "cut_m2", "side_trim_m2", "lower_bound", "proof_state")}
                          for x in lays],
           "tied_with": [{"direction": lays[i]["direction"], "start": lays[i]["start"],
                          "side_trim_m2": lays[i]["side_trim_m2"]} for i in tied[1:]],
           "rolls_to_buy": sel["rolls_to_buy"], "strip_metres": sel["strip_metres"],
           "leftover_m": sel["leftover_m"], "cut_m2": sel["cut_m2"], "side_trim_m2": sel["side_trim_m2"],
           "upturn_shortfall_m2": short, "opening_upturn": opening, "other_wall_frames": other,
           "flags": flags, "spec": {k: spec[k] for k in F.DEFAULT}, "rules": list(RULES),
           "_draw": {"pf": pf, "sheets": sel["_sheets"]}}
    return out


def _hole_split(pf, sel, spec):
    """the opening-upturn split (folded from the strips / own pieces) for a layout started at the opposite wall."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    p = _to_layout(pf, sel["direction"], sel["start"])
    h = spec["upturn_h_m"]
    ss = F.strips(p, h, spec["roll_width_m"], spec["roll_length_m"], spec["lap_m"])
    sheets = unary_union([box(s["x0"], s["s0"], s["x1"], s["s1"]) for s in ss])
    req = sum(r.length for r in p.interiors) * h
    cov = unary_union(F._flaps(p, h, holes=True)).intersection(sheets).area
    return {"folded_from_strips_m2": _r(cov), "own_pieces_m2": _r(max(req - cov, 0.0))}


def public(area):
    """the area without its drawing internals (for JSON)."""
    return {k: v for k, v in area.items() if not k.startswith("_")}


# ------------------------------------------------------------------------------------------------ project
def project(areas):
    """totals per group (wet areas, pantry, roofs) and overall, each only a sum of the areas computed alone (Q-49 A);
    held areas are listed and counted, never added as 0."""
    seen = set()
    for a in areas:
        k = (a["floor"], a["room_id"], a["group"])
        if k in seen:
            raise PlanError(f"area {k} appears twice")
        seen.add(k)

    def tot(rows):
        done = [a for a in rows if a["state"] == "COMPUTED"]
        hl = [a for a in rows if a["state"] != "COMPUTED"]
        return {"areas": len(done), "held": len(hl),
                "held_rows": [{"floor": a["floor"], "room_id": a["room_id"], "name": a["name"], "reason": a["reason"]}
                              for a in hl],
                "rolls_to_buy": sum(a["rolls_to_buy"] for a in done),
                "membrane_cut_m2": _r(sum(a["cut_m2"] for a in done)),
                "strip_metres": _r(sum(a["strip_metres"] for a in done)),
                "leftover_m": _r(sum(a["leftover_m"] for a in done)),
                "side_trim_m2": _r(sum(a["side_trim_m2"] for a in done)),
                "floor_m2": _r(sum(a["floor_m2"] for a in done)),
                "complete": not hl}

    groups = {g: tot([a for a in areas if a["group"] == g]) for g in GROUPS if any(a["group"] == g for a in areas)}
    return {"method": METHOD_ID, "rules": list(RULES), "groups": groups, "all": tot(areas),
            "never": ["a held area as 0", "offcuts carried from one area to another (Q-49 A)",
                      "rolls from net area / roll area"]}


# ------------------------------------------------------------------------------------------------ printables
def text_table(a):
    """the printable cutting plan of one area (plain text)."""
    head = f"{a['floor']} | {a['name'] or a['room_id']} | {a['group']}"
    if a["state"] != "COMPUTED":
        return f"{head}\n  HELD: {a['reason']} (no quantity; never 0)\n"
    s = a["selected"]
    sp = a["spec"]
    lines = [head,
             f"  floor {a['floor_m2']:.2f} m2, layout {s['direction']} from the {s['start']}, roll "
             f"{sp['roll_width_m']:.2f} x {sp['roll_length_m']:.2f} m, lap {sp['lap_m']:.2f} m, upturn "
             f"{sp['upturn_h_m']:.2f} m",
             "  strip | width m | length m | piece: length m -> roll (from - to m)"]
    for st in s["strip_list"]:
        pcs = "; ".join(f"{p['piece']}: {p['length_m']:.2f} -> roll {p['roll']} ({p['from_m']:.2f} - {p['to_m']:.2f})"
                        for p in st["pieces"])
        lines.append(f"  S{st['strip']:<4} | {st['width_m']:.2f}    | {st['length_m']:.2f}     | {pcs}")
    for r in s["rolls"]:
        lines.append(f"  roll {r['roll']}: used {r['used_m']:.2f} m, leftover {r['leftover_m']:.2f} m")
    lines.append(f"  rolls {a['rolls_to_buy']} | strip metres {a['strip_metres']:.2f} | leftover {a['leftover_m']:.2f} m"
                 f" | membrane cut {a['cut_m2']:.2f} m2 | side trim {a['side_trim_m2']:.2f} m2")
    lines.append(f"  {s['proof']}")
    for c in a["candidates"]:
        lines.append(f"  layout {c['direction']} / {c['start']}: {c['rolls_to_buy']} roll(s), "
                     f"{c['strip_metres']:.2f} m, trim {c['side_trim_m2']:.2f} m2")
    if a["opening_upturn"]:
        o = a["opening_upturn"]
        lines.append(f"  openings {o['openings']}: upturn {o['upturn_lm']:.2f} lm / {o['upturn_m2']:.2f} m2, own "
                     f"pieces {o['own_pieces_m2']} m2 by detail (not in the roll count)")
    if a["flags"]:
        lines.append("  flags: " + ", ".join(a["flags"]))
    return "\n".join(lines) + "\n"


def svg(a, px_per_m=60.0, margin_px=40.0):
    """an SVG drawing of the selected layout on the area's outline (room frame: longest wall horizontal): strips
    numbered, the roll number on each piece, splices shown. A held area gives a one-line SVG saying HELD."""
    if a["state"] != "COMPUTED":
        return ('<svg xmlns="http://www.w3.org/2000/svg" width="480" height="40"><text x="8" y="24" '
                f'font-family="sans-serif" font-size="14">HELD: {_esc(a["reason"])}</text></svg>')
    pf, sheets = a["_draw"]["pf"], a["_draw"]["sheets"]
    xs = [b for sh in sheets for sg in sh["segments"] for b in (sg["box"][0], sg["box"][2])] + [pf.bounds[0],
                                                                                             pf.bounds[2]]
    ys = [b for sh in sheets for sg in sh["segments"] for b in (sg["box"][1], sg["box"][3])] + [pf.bounds[1],
                                                                                             pf.bounds[3]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    k = px_per_m
    wpx, hpx = (x1 - x0) * k + 2 * margin_px, (y1 - y0) * k + 2 * margin_px + 24

    def P(x, y):
        return (margin_px + (x - x0) * k, margin_px + 24 + (y1 - y) * k)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{wpx:.0f}" height="{hpx:.0f}" '
           f'viewBox="0 0 {wpx:.0f} {hpx:.0f}" font-family="sans-serif">',
           f'<rect width="100%" height="100%" fill="#ffffff"/>',
           f'<text x="{margin_px:.0f}" y="20" font-size="13" fill="#000">{_esc(a["floor"])} {_esc(a["name"] or a["room_id"])}'
           f': {a["rolls_to_buy"]} roll(s), {a["strip_metres"]:.2f} m of strips, {a["leftover_m"]:.2f} m left</text>']
    palette = ("#4e79a7", "#f28e2b", "#59a14f", "#e15759", "#76b7b2", "#edc948", "#b07aa1", "#9c755f")
    for sh in sheets:
        for sg in sh["segments"]:
            bx = sg["box"]
            (ax, ay), (bx2, by2) = P(bx[0], bx[3]), P(bx[2], bx[1])
            col = palette[(sg["roll"] - 1) % len(palette)]
            out.append(f'<rect x="{ax:.1f}" y="{ay:.1f}" width="{bx2 - ax:.1f}" height="{by2 - ay:.1f}" fill="{col}" '
                       f'fill-opacity="0.25" stroke="{col}" stroke-width="1.5"/>')
            cx, cy = (ax + bx2) / 2, (ay + by2) / 2
            lab = f"S{sh['strip']}" + (f".{sg['piece']}" if len(sh["segments"]) > 1 else "") + f" R{sg['roll']}"
            out.append(f'<text x="{cx:.1f}" y="{cy + 4:.1f}" font-size="11" text-anchor="middle" fill="#000">'
                       f'{lab}</text>')
    for ring in [pf.exterior] + list(pf.interiors):
        pts = " ".join(f"{P(x, y)[0]:.1f},{P(x, y)[1]:.1f}" for x, y in ring.coords)
        out.append(f'<polyline points="{pts}" fill="none" stroke="#000" stroke-width="2"/>')
    out.append("</svg>")
    return "\n".join(out)


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def policy_record():
    return {"method": METHOD_ID, "rules": list(RULES), "defaults_from_rules": dict(F.DEFAULT),
            "replaces_nothing": "opt-in beside MEMBRANE_FOLD_V2; no released method reads it"}

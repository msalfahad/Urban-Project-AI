"""MEMBRANE CUTTING PLAN V2 (task T-096; read by ARCH_TAKEOFF_V2.12) - the installer's cutting plan of one wet room or
roof ALONE (owner Q-49 A) on MEMBRANE_FOLD_V3, which closes every uncovered upturn (an upturn-only strip at an outline
step parallel to the strips, a listed patch elsewhere). MEMBRANE_CUTTING_PLAN_V1 (T-089, on MEMBRANE_FOLD_V2) is kept as
it is.

    purchase(fold)       the four layouts (two strip directions x two start walls) counted under the three readings of
                         owner Q-58 (OPEN; MEMBRANE_FOLD_V3.BASIS_TEXT); per reading the layout with the fewest whole
                         rolls (tie: shorter strip metres, then smaller cut m2, then the listed order). The same fewest
                         count under all three readings -> RELEASED, with the cutting plan of the layout that reaches it
                         under Q58_B (every piece from a roll); otherwise HELD_Q58 with a bounded count (low / high) and
                         the cutting plans under Q58_B and Q58_A (which pieces come from the area's own offcuts)
    plan(polygon, ...)   one area alone: MEMBRANE_FOLD_V3.fold + purchase, or a HELD row (never 0)
    text_table(area)     printable cutting plan: every strip / patch piece, which roll, metres left; patches listed
Each cutting plan is packed again from its pieces and must give the fold's own count (a code fault otherwise).
Project-agnostic. shapely 2 (requirements.txt)."""

from __future__ import annotations

import math

from engine.source import arch_v211 as AV
from engine.source import membrane_fold_v3 as F3

METHOD_ID = "MEMBRANE_CUTTING_PLAN_V2"
Q49_A = AV.Q49_A

Q58 = ("owner Q-58 OPEN (membrane pieces the straight strips do not reach: cut from the same area's own leftover / side "
       "trim (A), every piece from a roll (B), or ready-made pieces by detail (C))")
LAYOUT_NAMES = {(F3.ALONG_LONG, F3.LOWER): "ALONG_LONGEST_WALL / LOWER_EDGE_OF_ROOM_FRAME",
                (F3.ALONG_LONG, F3.OPPOSITE): "ALONG_LONGEST_WALL / OPPOSITE_EDGE_OF_ROOM_FRAME",
                (F3.ACROSS, F3.LOWER): "ACROSS_LONGEST_WALL / LOWER_EDGE_OF_ROOM_FRAME",
                (F3.ACROSS, F3.OPPOSITE): "ACROSS_LONGEST_WALL / OPPOSITE_EDGE_OF_ROOM_FRAME"}




# ------------------------------------------------------------------------------------------------ purchase
def _key(lays, i, basis):
    x = lays[i]
    return (x["rolls_by_basis"][basis], round(x["strip_metres"], 4), round(x["cut_m2"], 4), i)


def _cutting_plan(lay, basis, spec):
    """the pieces of one layout cut from rolls under one reading of Q-58 and packed into whole rolls; the count must
    equal the layout's own count for that reading."""
    from engine.source import membrane_layout as ML
    L = spec["roll_length_m"]
    W = spec["roll_width_m"]
    pieces = []
    for k, s in enumerate(lay["strips"], 1):
        for j, x in enumerate(s["piece_lengths_m"], 1):
            pieces.append({"strip": f"S{k}", "kind": s["kind"], "piece": j, "of": len(s["piece_lengths_m"]),
                           "width_m": s["width_m"], "length_m": x})
    c = lay["counts"][basis]
    if basis == "Q58_B":
        for k, q in enumerate(lay["patches"], 1):
            n = max(1, math.ceil(q["across_m"] / W - F3.EPS))
            for j in range(n):
                pieces.append({"strip": f"P{k}", "kind": q["kind"], "piece": j + 1, "of": n,
                               "width_m": round(min(W, q["across_m"] - j * W), 4), "length_m": q["along_m"]})
    elif basis == "Q58_A":
        # the main strips from rolls; an upturn-only strip or patch from the area's own offcut when it fits
        # (pieces_from_own_offcuts), else from a roll (pieces_from_rolls)
        pieces = [pc for pc in pieces if pc["kind"] == "MAIN"]
        for k, e in enumerate(c["pieces_from_rolls"], 1):
            pieces.append({"strip": f"X{k}", "kind": e["what"], "piece": 1, "of": 1, "width_m": round(e["w"], 4),
                           "length_m": e["l"]})
    bins, packing = ML.pack_rolls([p["length_m"] for p in pieces], L) if pieces else ([], {"proven": True})
    if len(bins) != c["rolls"]:
        raise ValueError(f"cutting plan gives {len(bins)} rolls under {basis}, the fold {c['rolls']}")
    plan = []
    for k, b in enumerate(sorted(bins, key=lambda b: min(b)), 1):
        cut = [pieces[i] for i in sorted(b, key=lambda i: (-pieces[i]["length_m"], i))]
        u = sum(x["length_m"] for x in cut)
        plan.append({"roll": k, "pieces": [dict(x) for x in cut], "used_m": round(u, 4), "left_m": round(L - u, 4)})
    used = sum(p["length_m"] for p in pieces)
    return {"rolls": len(bins), "pieces_from_rolls_m": round(used, 4), "leftover_m": round(len(bins) * L - used, 4),
            "cutting_plan": plan, "packing_proven": packing.get("proven", True),
            "pieces_from_own_offcuts": c.get("pieces_from_own_offcuts") or []}


def purchase(fold):
    """owner Q-49 A for one area alone on the MEMBRANE_FOLD_V3 layouts, under the three readings of owner Q-58."""
    sp = fold["spec"]
    W, L, lap = sp["roll_width_m"], sp["roll_length_m"], sp["lap_m"]
    lays = fold["layouts_v3"]
    best = {b: min(range(len(lays)), key=lambda i: _key(lays, i, b)) for b in F3.BASES}
    mins = {b: lays[best[b]]["rolls_by_basis"][b] for b in F3.BASES}
    readings = {b: {"rolls": mins[b], "layout": LAYOUT_NAMES[(lays[best[b]]["direction"], lays[best[b]]["start"])],
                    "rule": F3.BASIS_TEXT[b]} for b in F3.BASES}
    released = len(set(mins.values())) == 1
    sel = lays[best["Q58_B"]]
    plan_b = _cutting_plan(sel, "Q58_B", sp)
    flags = list(fold.get("flags_v3") or ())
    if sel["upturn_strips"]:
        flags.append("UPTURN_ONLY_STRIPS_IN_CHOSEN_LAYOUT")
    if sel["patches"]:
        flags.append("PATCHES_IN_CHOSEN_LAYOUT")
    if not plan_b["packing_proven"]:
        flags.append("PACKING_NOT_PROVEN_MINIMAL")
    if any(c["rolls_if_alone"] < mins["Q58_C"] for fr in fold.get("other_frames") or () for c in fr["directions"]):
        flags.append("ANOTHER_WALL_FRAME_NEEDS_FEWER_ROLLS")       # shown, never selected (not one of the four)
    out = {"rule": Q49_A, "method": F3.METHOD_ID, "state": "RELEASED" if released else "HELD_Q58",
           "direction": sel["direction"], "start": sel["start"],
           "strips": len(sel["strips"]), "upturn_only_strips": sel["upturn_strips"],
           "upturn_only_strip_m": sel["upturn_strip_m"],
           "rolls": mins["Q58_B"] if released else None,
           "rolls_bounded": None if released else {"low": min(mins.values()), "high": max(mins.values())},
           "rolls_by_reading": readings,
           "strip_length_m": sel["strip_metres"], "cut_m2": sel["cut_m2"],
           "leftover_m": plan_b["leftover_m"] if released else None,
           "side_trim_m2": round(sel["strip_metres"] * W - sel["cut_m2"], 4),
           "patches": [{k: q.get(k) for k in ("kind", "m2", "along_m", "across_m", "centre_room_frame_m",
                                               "centre_drawing_units")} for q in sel["patches"]],
           "patch_m2": sel["patch_m2"], "residual_before_v2_strips_m2": sel["residual_before_m2"],
           "residual_after_m2": sel["residual_after_m2"], "numerical_residual_m2": sel["numerical_residual_m2"],
           "cutting_plan": plan_b["cutting_plan"], "cutting_plan_reading": "Q58_B",
           "roll": {"width_m": W, "length_m": L, "lap_m": lap},
           "layouts": [{"direction": x["direction"], "start": x["start"], "rolls_by_reading": x["rolls_by_basis"],
                        "strip_metres": x["strip_metres"], "cut_m2": x["cut_m2"], "upturn_only_strips": x["upturn_strips"],
                        "patch_m2": x["patch_m2"], "residual_before_v2_strips_m2": x["residual_before_m2"]}
                       for x in lays], "flags": flags}
    if not released:
        sa = lays[best["Q58_A"]]
        out["cutting_plan_q58_a"] = _cutting_plan(sa, "Q58_A", sp)
        out["reason"] = (f"{Q58}: rolls {readings['Q58_A']['rolls']} (A) / {readings['Q58_B']['rolls']} (B) / "
                         f"{readings['Q58_C']['rolls']} (C); held, never 0")
    return out


def plan(polygon, *, holes=(), unit_m=1.0, spec=None, floor=None, room_id=None, name=None, group="WET_AREA"):
    """the cutting plan of one area alone (Q-49 A) on MEMBRANE_FOLD_V3; a missing or unusable input -> HELD."""
    spec = dict(F3.DEFAULT, **(spec or {}))
    base = {"method": METHOD_ID, "floor": floor, "room_id": room_id, "name": name, "group": group}
    for k in F3.DEFAULT:
        if spec.get(k) is None or spec[k] <= 0:
            return dict(base, state="HELD", reason=f"MISSING_INPUT_{k.upper()}", purchase=None)
    if spec["lap_m"] >= spec["roll_width_m"] or spec["lap_m"] >= spec["roll_length_m"]:
        return dict(base, state="HELD", reason="LAP_NOT_SMALLER_THAN_ROLL", purchase=None)
    if not polygon:
        return dict(base, state="HELD", reason="NO_OUTLINE", purchase=None)
    try:
        f = F3.fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    except F3.FoldError as ex:
        return dict(base, state="HELD", reason=f"OUTLINE_NOT_USABLE: {ex}", purchase=None)
    return dict(base, state="COMPUTED", floor_m2=f["floor_m2"], purchase=purchase(f))


def text_table(a):
    """the printable cutting plan of one area (plain text)."""
    head = f"{a['floor']} | {a['name'] or a['room_id']} | {a['group']}"
    if a["state"] != "COMPUTED":
        return f"{head}\n  HELD: {a['reason']} (no quantity; never 0)\n"
    p = a["purchase"]
    rd = p["rolls_by_reading"]
    out = [head, f"  floor {a['floor_m2']:.2f} m2, layout {p['direction']} / {p['start']}, {p['strips']} strips "
                 f"({p['upturn_only_strips']} upturn-only), {p['strip_length_m']:.2f} m of strips"]
    if p["state"] == "RELEASED":
        out.append(f"  rolls {p['rolls']} (the same under owner Q-58 A / B / C), leftover {p['leftover_m']:.2f} m")
    else:
        out.append(f"  rolls HELD (owner Q-58 open): A {rd['Q58_A']['rolls']} / B {rd['Q58_B']['rolls']} / "
                   f"C {rd['Q58_C']['rolls']}, never 0")
    for r in p["cutting_plan"]:
        out.append(f"  roll {r['roll']}: " + " + ".join(f"{q['strip']}.{q['piece']} {q['width_m']:.2f}x"
                                                        f"{q['length_m']:.2f}" for q in r["pieces"])
                   + f", {r['left_m']:.2f} m left")
    for q in p["patches"]:
        out.append(f"  patch {q['kind']}: {q['m2']:.4f} m2, {q['along_m']:.2f} x {q['across_m']:.2f} m at "
                   f"{q['centre_room_frame_m']} (room frame, m)")
    if p["flags"]:
        out.append("  flags: " + ", ".join(p["flags"]))
    return "\n".join(out) + "\n"


def policy_record():
    return {"method": METHOD_ID, "fold": F3.METHOD_ID, "purchase_rule": Q49_A, "open_rule": Q58,
            "readings": dict(F3.BASIS_TEXT),
            "replaces_nothing": "beside MEMBRANE_CUTTING_PLAN_V1 (unchanged); read by ARCH_TAKEOFF_V2.12"}

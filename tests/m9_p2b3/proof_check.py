"""HAND vs REFERENCE - Phase 2B-3 proof library: the independent reference calculator (proof_reference) re-run on
each proof case's geometry, its results keyed like the hand-calculated expected values (an arithmetic cross-check of
the hand calculation; neither side touches the engine)."""

from __future__ import annotations

import proof_reference as R


def reference_values(case):
    ref = case.get("reference")
    if not ref:
        return {}
    area = {"poly": ref["poly_mm"], "runs": ref["runs_mm"], "doorways": ref.get("doorways_mm", ()),
            "patches": ref.get("patches_mm", ())}
    lap = ref.get("lap_mm", 100)
    r = R.membrane(area, along=ref["along"], s=lap, e=lap)
    extra = ref.get("extra_net_m2", 0.0)
    out = {"A_net_m2": r["A_m2"], "perimeter_m": r["perimeter_m"],
           "upturn_m2": round(r["upturn_m2"] - extra, 6), "doorway_continuation_m2": r["doorway_net_m2"],
           "proven_subtotal_m2": round(r["A_m2"] + r["upturn_m2"] - extra + r["doorway_net_m2"], 6),
           "floor_strips": r["floor_strips"], "last_strip_w_m": r["strip_widths_m"][-1],
           "band_pieces_m": r["band_pieces_m"], "band_joints": r["band_joints"],
           "laps_m2": r["laps_total_m2"], "detailing_m2": r["detailing_m2"], "B_m2": r["B_m2"],
           "consumed_m2": r["consumed_m2"], "waste_m2": r["waste_m2"], "rolls": r["rolls"], "cuts_m": r["cuts_m"],
           "untouched_m2": r["untouched_m2"]}
    if not extra:
        out["eligible_m"] = r["eligible_m"]
    else:
        out["transition_m2"] = extra
    if ref.get("alt_along"):
        a = R.membrane(area, along=ref["alt_along"], band_split=ref.get("alt_split_mm"), s=lap, e=lap)
        out.update(alt_rolls=a["rolls"], alt_consumed_m2=a["consumed_m2"],
                   alt_seams=(a["floor_strips"] - 1) + a["band_joints"])
    return out


def hand_vs_reference(case):
    """rows {quantity, hand, reference, result} for every expected quantity the reference computes."""
    ref = reference_values(case)
    rows = []
    for k, h in case["expected"].items():
        if k not in ref:
            continue
        v = ref[k]
        ok = (abs(h - v) <= 1e-9) if isinstance(h, (int, float)) and not isinstance(h, bool) else \
            (h == v if not isinstance(h, list) else len(h) == len(v) and all(abs(x - y) <= 1e-9 for x, y in zip(h, v)))
        rows.append({"quantity": k, "hand": h, "reference": v, "result": "AGREE" if ok else "DISAGREE"})
    return rows


def door_reference_values(case):
    plan = case["plan"]
    if plan.get("main_entrance"):
        me = plan["main_entrance"]
        return R.main_entrance(me["s1"] - me["s0"])
    over = next((r["value"] for r in plan.get("rules", ()) if r.get("parameter") == "required_nominal_door_m"), None)
    out = R.door(plan, nominal_override=None if over is None else R.mm(over))
    if case.get("scope_check"):
        out["scope_check_required_nominal_door_m"] = R.door(dict(plan, **case["scope_check"],
                                                                 a_word="BEDROOM"))["required_nominal_door_m"]
    return out


def door_hand_vs_reference(case):
    ref = door_reference_values(case)
    rows = []
    for k, h in case["expected"].items():
        if k not in ref:
            continue
        v = ref[k]
        ok = abs(h - v) <= 1e-9 if isinstance(h, (int, float)) and not isinstance(h, bool) and v is not None else h == v
        rows.append({"quantity": k, "hand": h, "reference": v, "result": "AGREE" if ok else "DISAGREE"})
    return rows

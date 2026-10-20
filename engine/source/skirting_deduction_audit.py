"""SKIRTING DEDUCTION AUDIT (T-106): every released skirting line must re-add from its own trail.

A reviewer checks a skirting line (FIN.SKIRTING, unit lm) by re-adding it: gross - listed deductions + listed
additions = measured net. T-016a found that on the released ARCH_TAKEOFF_V2.11 run of one real villa 20 of 28 lines do
not re-add (17.035 m in total). The cause (traced in research/agents_t106/): release_safety.skirting (F-17) takes the
equal-split V1 credit of the boundary edges that are skirted under one reading and not under the other (a window frame
on the room face: sill window or floor glazing) off the certain line and holds the whole edge in a separate bounded
range line, but the certain line's deduction list never names that credit. The net is consistent; the trail is not.

This check piece reads canonical BOQ lines (URBAN_CANONICAL_BOQ_LINE_V1, any villa, any method version that writes
them) and gives every skirting line with a quantity exactly one record. It is NOT wired into a released method: no
line, quantity or note is changed and nothing is released here (a later output version fixes the listing).

    audit(lines, rooms=None, *, item_codes=("FIN.SKIRTING",), tol_m=TOL_M) -> {"policy", "records", "summary"}

Records (one per quantity line; status / reason):
    READDS                                  gross - deductions + additions = net within tol_m: nothing to explain
    HELD SKIRTING_UNEXPLAINED               the difference is not listed. unexplained_lm is signed (> 0: taken off
                                            and not listed; < 0: listed and not taken off), never 0 and never absorbed.
                                            candidate: what the engine took off without listing it, component by
                                            component (the F-17 credit stated by the room's bounded range line, the
                                            V2.8 thresholds moved to it, and with the room records the V2.8 floor
                                            glazing); matches = the components add up to the difference within tol_m.
                                            A match names the cause; the record stays HELD, because the line's own
                                            trail is still incomplete (UP-QTY-STATUS-001)
    HELD SKIRTING_NOT_READDABLE             gross, net or a deduction / addition length is missing or not a number:
                                            the line cannot be re-added (missing never becomes 0)
    HELD SKIRTING_UNIT_UNKNOWN              the line's unit is not a length unit this check knows (lm / m / cm / mm):
                                            nothing is assumed
A second record HELD SKIRTING_DECOMPOSITION_MISMATCH is added when the line's calculation inputs give the boundary
role by role and the roles do not add up to the boundary, or the boundary is not the gross.
Lines of the item without a quantity state (BOUNDED_EXPOSURE ranges, BLOCKED_RFI) are counted in the summary as
not_net_lines; they carry no net to re-add.

Lengths are reported in metres (a line in mm or cm is converted by its own unit). Rules: UP-SKIRT-001, UP-CER-002
(lm), UP-CER-003 (door openings deducted), UP-CER-004 (no skirting in a fully tiled wet room), UP-QTY-STATUS-001.
"""

from __future__ import annotations

import math

POLICY = "SKIRTING_DEDUCTION_AUDIT_V1"
RULES = ("UP-SKIRT-001", "UP-CER-002", "UP-CER-003", "UP-CER-004", "UP-QTY-STATUS-001")
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")      # engine/source/boq_line.py QUANTITY_STATES
RANGE_STATE = "BOUNDED_EXPOSURE"
UNIT_M = {"lm": 1.0, "m": 1.0, "cm": 0.01, "mm": 0.001}
TOL_M = 1e-5          # the canonical line rounds each length to 1e-6 m; a handful of rounded terms stays under 1e-5
# the boundary roles of a skirting line's calculation inputs (ARCH_TAKEOFF_V2.x room skirting): perimeter split by role,
# coincident roles split equally, so these add up to the boundary
TO_RANGE_KEYS = ("WINDOW_SILL_NOT_ESTABLISHED", "FLOOR_GLAZING_ON_")   # arch_v28.skirting_adjustment to_range_by keys
ROLE_KEYS = ("wall", "column", "door", "passage", "glazing_edge", "other", "window_threshold")


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _where(ln):
    loc = ln.get("location") or {}
    return {"line_id": ln.get("line_id"), "item_code": ln.get("item_code"), "floor": loc.get("floor"),
            "room_id": loc.get("room_id"), "room_name_en": loc.get("room_name_en"),
            "element_id": loc.get("element_id")}


def _range_lines(lines, item_codes):
    """{(item_code, room_id): [range line]} of the bounded range lines (F-17) of the audited items."""
    out = {}
    for ln in lines:
        if ln.get("item_code") in item_codes and ln.get("evidence_state") == RANGE_STATE:
            rid = (ln.get("location") or {}).get("room_id")
            if rid is not None:
                out.setdefault((ln["item_code"], rid), []).append(ln)
    return out


def _components(ranges, k, rooms, room_id):
    """what the engine took off the line without listing it, component by component (m), from the room's bounded range
    line(s) of the same item and, when given, the room record (ARCH_ROOMS skirting_windows_v28):
      F17_EQUAL_SPLIT_CREDIT   release_safety.skirting: the V1 equal-split share of the edges skirted under one reading
                               only (the edge itself is held whole in the range line)
      V28_TO_RANGE             arch_v28.skirting_adjustment: window thresholds moved whole to the range line (sill not
                               established, floor glazing on a wall / column line)
      V28_FLOOR_GLAZING        arch_v28: floor-level glazing thresholds, skirted under no reading (room record only)
      V28_RANGE_OUT_CREDIT     arch_v28: the F-17 credit of floor-glazing edges taken out of the range (room record only)
    -> ([component], complete) or (None, False) when the room has no range line and no room record"""
    rs = ranges.get(k) or []
    comps, complete, ids = [], True, []
    credit = to_range = 0.0
    for r in rs:
        f = UNIT_M.get(r.get("unit"))
        inp = (r.get("calculation") or {}).get("inputs") or {}
        c, by = inp.get("v1_equal_split_credit_lm"), inp.get("unresolved_by_roles") or {}
        if f is None or not _num(c) or not all(_num(v) for v in by.values()):
            complete = False
            continue
        ids.append(r.get("line_id"))
        credit += c * f
        to_range += sum(v for kk, v in by.items() if kk.startswith(TO_RANGE_KEYS)) * f
    if ids:
        comps.append({"what": "F17_EQUAL_SPLIT_CREDIT", "lm": round(credit, 6), "range_line_ids": ids})
    room = (rooms or {}).get(room_id)
    adj = (room or {}).get("skirting_windows_v28") if room else None
    if adj:
        vals = {n: adj.get(src) for n, src in (("V28_TO_RANGE", "to_range_lm"),
                                                ("V28_FLOOR_GLAZING", "floor_glazing_lm"),
                                                ("V28_RANGE_OUT_CREDIT", "range_out_credit_lm"))}
        if not all(_num(v) for v in vals.values()):
            complete = False
        else:
            if ids and abs(vals["V28_TO_RANGE"] - to_range) > TOL_M:
                complete = False              # the room record and the range line disagree: no explanation chosen
            comps += [{"what": n, "lm": round(v, 6), "source": "room record"} for n, v in vals.items() if v > 1e-9]
    elif to_range > 1e-9:
        comps.append({"what": "V28_TO_RANGE", "lm": round(to_range, 6), "range_line_ids": ids})
        complete = False                      # floor glazing / range-out credit not readable from the lines alone
    if not comps and not ids and not adj:
        return None, False
    return comps, complete


def _candidate(ranges, k, rooms, residual_m, tol_m):
    comps, complete = _components(ranges, k, rooms, k[1])
    if comps is None:
        return None
    total = sum(c["lm"] for c in comps)
    return {"components": comps, "total_lm": round(total, 6), "complete": complete,
            "matches": abs(residual_m - total) <= tol_m,
            "basis": "taken off the certain line and not listed: F-17 holds the edges skirted under one reading only "
                     "whole in the bounded range line; V2.8 moves sill-unknown thresholds there and drops floor glazing"}


def _decomposition(ln, f, gross_m, tol_m):
    inp = (ln.get("calculation") or {}).get("inputs") or {}
    if not _num(inp.get("boundary")) or not all(_num(inp.get(k)) for k in ROLE_KEYS):
        return None
    b = inp["boundary"] * f
    s = sum(inp[k] for k in ROLE_KEYS) * f
    t = tol_m * len(ROLE_KEYS)
    return {"boundary_lm": round(b, 6), "role_sum_lm": round(s, 6), "gross_lm": round(gross_m, 6),
            "differs": abs(b - s) > t or abs(b - gross_m) > t}


def audit_line(ln, ranges=None, rooms=None, *, tol_m=TOL_M):
    """-> [records] of one skirting line with a quantity state (one main record, plus a decomposition record)."""
    rec = {"policy": POLICY, **_where(ln)}
    unit = ln.get("unit")
    f = UNIT_M.get(unit)
    if f is None:
        return [{**rec, "status": "HELD", "reason": "SKIRTING_UNIT_UNKNOWN", "unit": unit,
                 "basis": f"unit {unit!r} is not a known length unit; nothing is assumed"}]
    gross, net = ln.get("gross"), ln.get("measured_net")
    missing = [n for n, v in (("gross", gross), ("measured_net", net)) if not _num(v)]
    terms = {}
    for side in ("deductions", "additions"):
        items = ln.get(side) or []
        bad = [i for i, d in enumerate(items) if not isinstance(d, dict) or not _num(d.get("lm"))]
        missing += [f"{side}[{i}].lm" for i in bad]
        terms[side] = [d for d in items if isinstance(d, dict) and _num(d.get("lm"))]
    if missing:
        return [{**rec, "status": "HELD", "reason": "SKIRTING_NOT_READDABLE", "missing": missing,
                 "basis": "a length of the line's own trail is missing: it cannot be re-added (never read as 0)"}]
    g, n = gross * f, net * f
    ded = sum(d["lm"] for d in terms["deductions"]) * f
    add = sum(d["lm"] for d in terms["additions"]) * f
    residual = g - ded + add - n
    main = {**rec, "gross_lm": round(g, 6), "listed_deductions_lm": round(ded, 6),
            "listed_additions_lm": round(add, 6), "net_lm": round(n, 6),
            "readd_lm": round(g - ded + add, 6)}
    out = []
    if abs(residual) <= tol_m:
        out.append({**main, "status": "READDS"})
    else:
        k = (ln.get("item_code"), (ln.get("location") or {}).get("room_id"))
        cand = _candidate(ranges or {}, k, rooms, residual, tol_m)
        rec_h = {**main, "status": "HELD", "reason": "SKIRTING_UNEXPLAINED", "unexplained_lm": round(residual, 6),
                 "candidate": cand,
                 "basis": (f"gross {g:.3f} - listed deductions {ded:.3f} + listed additions {add:.3f} = "
                           f"{g - ded + add:.3f} m, but the net is {n:.3f} m: {residual:+.3f} m "
                           + ("taken off without being listed" if residual > 0 else "listed but not taken off"))}
        if cand and cand["matches"]:
            # the listing that re-adds with no quantity change: each unlisted component as its own deduction
            prop = ded + cand["total_lm"]
            rec_h["proposed_listing"] = {"add_deductions": [c for c in cand["components"] if c["lm"] > 1e-9],
                                         "deductions_lm": round(prop, 6), "readds": abs(g - prop + add - n) <= tol_m}
        out.append(rec_h)
    dec = _decomposition(ln, f, g, tol_m)
    if dec is not None:
        out[0]["decomposition"] = dec
        if dec["differs"]:
            out.append({**rec, "status": "HELD", "reason": "SKIRTING_DECOMPOSITION_MISMATCH", **dec,
                        "basis": "the boundary roles of the calculation inputs do not add up to the boundary / gross"})
    return out


def audit(lines, rooms=None, *, item_codes=("FIN.SKIRTING",), tol_m=TOL_M):
    """-> {"policy", "records", "summary"} for every line of item_codes in lines (canonical BOQ lines). rooms: the
    run's room records (ARCH_ROOMS rooms, a list or {room_id: room}), optional: they name the V2.8 floor-glazing
    components that the lines alone do not carry."""
    item_codes = tuple(item_codes)
    if isinstance(rooms, (list, tuple)):
        rooms = {r.get("room_id"): r for r in rooms if isinstance(r, dict)}
    ranges = _range_lines(lines, item_codes)
    records, not_net = [], []
    for ln in lines:
        if ln.get("item_code") not in item_codes:
            continue
        if ln.get("evidence_state") not in QUANTITY_STATES:
            not_net.append({**_where(ln), "evidence_state": ln.get("evidence_state")})
            continue
        records.extend(audit_line(ln, ranges, rooms, tol_m=tol_m))
    return {"policy": POLICY, "tol_m": tol_m, "records": records, "summary": summary(records, not_net)}


def summary(records, not_net=()):
    main = [r for r in records if r.get("reason") != "SKIRTING_DECOMPOSITION_MISMATCH"]
    un = [r for r in main if r.get("reason") == "SKIRTING_UNEXPLAINED"]
    by = {}
    for r in records:
        key = r["status"] + (f":{r['reason']}" if r.get("reason") else "")
        by[key] = by.get(key, 0) + 1
    matched = [r for r in un if (r.get("candidate") or {}).get("matches")]
    return {"quantity_lines": len(main), "readds": by.get("READDS", 0), "held": len(records) - by.get("READDS", 0),
            "by_status": dict(sorted(by.items())),
            "unexplained_lines": len(un), "unexplained_lm": round(sum(r["unexplained_lm"] for r in un), 6),
            "explained_by_components": {"lines": len(matched),
                                          "lm": round(sum(r["unexplained_lm"] for r in matched), 6)},
            "unmatched_line_ids": [r["line_id"] for r in un if r not in matched],
            "not_net_lines": len(not_net), "not_net": list(not_net)}


def policy_record():
    return {"policy": POLICY, "rules": list(RULES), "tol_m": TOL_M, "units": dict(UNIT_M),
            "statuses": ["READDS", "HELD"],
            "held_reasons": ["SKIRTING_UNEXPLAINED", "SKIRTING_NOT_READDABLE", "SKIRTING_UNIT_UNKNOWN",
                             "SKIRTING_DECOMPOSITION_MISMATCH"],
            "wired": False,
            "never": ["a difference absorbed or shown as 0", "a missing length read as 0", "a unit assumed",
                      "a change to a line, quantity or note"]}

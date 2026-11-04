"""FINISH MATERIALS TABLE V5 (task T-499, from F-T496-1; opt-in, UNWIRED_PRODUCER: read by no released method and by
no candidate V3.0.x; no released or candidate quantity changes).

Physical element: unchanged from V4 (engine/source/finish_materials_table_v4.py, kept byte-identical): a tiled surface
of one product on its bed / render, and the adhesive bags and tile boxes bought for it. V5 changes no ROW: it changes
only how a SUBTOTAL over rows is printed when some of those rows carry no number.

Defect fixed (F-T496-1, reproduced on the working branch b6133032 against the T-455 ledger of V3.0.45):

    V1 .. V4 sums      a key summed over a group in which some rows are HELD prints the sum of the known rows under
                       the plain key (e.g. FIN.WALL.TILE area 340.3038 m2 over 12 of 18 lines), and 'cement bags to
                       buy' is rounded up from that partial sum: a known part read as the total.
    V4 purchase        a HELD adhesive group with no known row prints bags_known 0.0 ('known part 0.000000'): a 0
                       for a quantity nobody knows.
    T-455 by code      the reader's own subtotals start from 0.0 and add 'or 0.0': v4_bags_known 0.0 on every item
                       code, bound / flat bags 0.0 on a group with no bounded row.

Rule R-T499-1 (SUBTOTAL OVER HELD ROWS; project-independent; AGENT_BRIEF 'HELD is never 0', UP-QTY-STATUS-001):
    a subtotal is COMPUTED only when every row of its group carries a number for that key; then it is the V4 figure,
    unchanged, and the output carries no new key. If ANY row is held for that key the subtotal is HELD: the plain key
    is None, '<key>_status' is 'HELD', '<key>_at_least' carries the known part (None when no row is known, never 0.0)
    and the held rows are listed (V1's not_in_sum, or '<key>_held_rows'). A figure derived from a held subtotal (bags
    to buy) is HELD too. A BOUND over held rows is a bound only when every held row carries one; otherwise its low end
    is kept as an AT_LEAST over the bounded rows, its high end is None and the unbounded rows are listed.

Never: a held value as 0, a known part printed as the total, a whole-bag figure rounded from a partial sum.
Project-agnostic: no project, layer, room name or count appears in this module.
"""

from __future__ import annotations

import copy

from engine.source import finish_materials_table_v4 as V4

METHOD_ID = "FINISH_MATERIALS_TABLE_V5"
SUPERSEDES = V4.METHOD_ID
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
RULES = V4.RULES + ("R-T499-1@1.0.0 (a subtotal over any HELD row is HELD; the known part AT_LEAST with the held "
                    "rows listed; a fully determinate subtotal unchanged)",)
CHANGE = {
    "v4_ref": "engine/source/finish_materials_table.py:252 _sums (partial sum under the plain key, to-buy from it); "
              "finish_materials_table_v4.py:222 _adhesive_purchase (bags_known 0.0 with no known row)",
    "v5": "R-T499-1: HELD subtotal with AT_LEAST known part and the held rows; rows, determinate subtotals unchanged",
}

HELD, OK = V4.HELD, V4.OK
KINDS = V4.KINDS
DRY_FLOOR, WET_FLOOR, WET_WALL = V4.DRY_FLOOR, V4.WET_FLOOR, V4.WET_WALL
STAIR_FLIGHT, STAIR_LANDING, ROOF, BALCONY = V4.STAIR_FLIGHT, V4.STAIR_LANDING, V4.ROOF, V4.BALCONY
PORCELAIN_CERAMIC, MARBLE_STONE = V4.PORCELAIN_CERAMIC, V4.MARBLE_STONE
OWNER_VALUES = V4.OWNER_VALUES
row = V4.row
tiles_from_counts = V4.tiles_from_counts
weakest = V4.weakest

_TO_BUY = {"cement_bags_to_buy_low": "cement_bags_low", "cement_bags_to_buy_high": "cement_bags_high"}


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def subtotal(items):
    """items: [(row id, value or None)] -> {'value', 'status', 'at_least', 'held_rows', 'rows'} by R-T499-1.
    An empty group has no subtotal (value None, status 'NO_ROWS'), never 0."""
    items = list(items)
    held = [i for i, v in items if v is None]
    known = [v for _, v in items if v is not None]
    if not items:
        return {"value": None, "status": "NO_ROWS", "at_least": None, "held_rows": [], "rows": 0}
    if held:
        return {"value": None, "status": HELD, "at_least": _r(sum(known)) if known else None,
                "held_rows": held, "rows": len(items)}
    return {"value": _r(sum(known)), "status": OK, "at_least": None, "held_rows": [], "rows": len(items)}


def bound_subtotal(rows):
    """the owner-rule adhesive BOUND over the rows whose bags are HELD (V4 'adhesive_bound_bags'). Complete only when
    every such row carries a bound; else low = AT_LEAST over the bounded rows, high None, unbounded rows listed."""
    held = [r for r in rows if r.get("adhesive_bags") is None]
    bounded = [r for r in held if r.get("adhesive_bound_bags")]
    unbounded = [r["id"] for r in held if not r.get("adhesive_bound_bags")]
    if not held:
        return {"low": None, "high": None, "status": "NO_HELD_ROWS", "unbounded_rows": [], "rows": 0}
    lo = _r(sum(r["adhesive_bound_bags"]["low"] for r in bounded)) if bounded else None
    if unbounded:
        return {"low": None, "high": None, "low_at_least": lo, "status": HELD, "unbounded_rows": unbounded,
                "rows": len(held)}
    return {"low": lo, "high": _r(sum(r["adhesive_bound_bags"]["high"] for r in bounded)), "status": "BOUND",
            "unbounded_rows": [], "rows": len(held)}


def _hold(out, key, held_ids, list_key=None):
    """R-T499-1 on one key of a subtotal dict (in place). Determinate keys are not touched."""
    if not held_ids:
        return
    out[key + "_at_least"] = out.get(key)
    out[key] = None
    out[key + "_status"] = HELD
    if list_key:
        out[list_key] = list(held_ids)


def _sums(rows):
    """V4 sums with R-T499-1: every key listed in not_in_sum is HELD with its known part AT_LEAST; the bags to buy
    of a held cement key HELD; render / spatter dash operations the same; the held-row adhesive bound complete or
    an AT_LEAST."""
    out = copy.deepcopy(V4._sums(rows))
    nis = out.get("not_in_sum") or {}
    for k, ids in nis.items():
        if k in out:
            _hold(out, k, ids)
    for buy, src in _TO_BUY.items():
        if nis.get(src) and buy in out:
            out[buy] = None
            out[buy + "_status"] = HELD
            out[buy + "_reason"] = f"{src} HELD over {len(nis[src])} row(s): no whole bags from a partial sum"
    for op in (out.get("wet_wall_operations") or {}).values():
        _hold(op, "area_m2", op.get("area_not_in_sum"))
        _hold(op, "mortar_m3", op.get("mortar_not_in_sum"))
    if out.get("adhesive_bound_bags_held_rows") is not None:
        b = bound_subtotal(rows)
        if b["status"] != "BOUND":
            out["adhesive_bound_bags_held_rows"] = b
    return out


def _groups(rows):
    groups = {}
    for r in rows:
        if r["finish"] is None and r["kind"] in (ROOF, BALCONY):
            continue                       # same exclusion as V4._adhesive_purchase
        groups.setdefault(r["adhesive_group"], []).append(r)
    return groups


def _adhesive_purchase(rows):
    """V4 purchase per adhesive group; a HELD group's known part is AT_LEAST, and None (never 0.0) with no known row."""
    out = copy.deepcopy(V4._adhesive_purchase(rows))
    for g, rs in _groups(rows).items():
        rec = out[g]
        if rec["status"] != HELD:
            continue
        known = [r for r in rs if r["adhesive_bags"] is not None]
        rec["bags_at_least"] = rec["bags_known"] if known else None
        if not known:
            rec["bags_known"] = None
            rec["why"] = (f"{len(rec['held_rows'])} row(s) HELD: the group's bags are not computed (never 0); "
                          f"no row carries a number (no known part)")
        b = bound_subtotal(rs)
        if b["status"] == HELD:
            rec["bound_bags_held_rows"] = b
    return out


def _box_purchase(rows, packaging):
    """V4 boxes per tile product; a product's area over a held row is HELD with the known part AT_LEAST."""
    out = copy.deepcopy(V4._box_purchase(rows, packaging))
    for rec in out["products"].values():
        if rec["area_not_in_sum"] and rec["area_m2"] is not None:
            _hold(rec, "area_m2", rec["area_not_in_sum"])
    return out


def by_group(rows, key_of):
    """subtotals of rows grouped by key_of(row) (an item code, a floor): lines, released, held, and per field a
    subtotal() record: area_m2, adhesive_v3_flat_bags, adhesive_bags; plus bound_subtotal() of the held rows.
    The reader-side replacement of hand-rolled 0.0-seeded sums (F-T496-1)."""
    out = {}
    for r in rows:
        out.setdefault(key_of(r), []).append(r)
    res = {}
    for g, rs in out.items():
        res[g] = {"lines": len(rs), "released": sum(r["area_m2"] is not None for r in rs),
                  "held": sum(r["area_m2"] is None for r in rs),
                  "area_m2": subtotal((r["id"], r["area_m2"]) for r in rs),
                  "adhesive_v3_flat_bags": subtotal((r["id"], r.get("adhesive_v3_flat_bags")) for r in rs),
                  "adhesive_bags": subtotal((r["id"], r["adhesive_bags"]) for r in rs),
                  "adhesive_bound_bags_held_rows": bound_subtotal(rs)}
    return res


def purchase_from_lines(lines, project=None, packaging=None):
    """V4.purchase_from_lines (rows byte-identical) with the V5 purchase subtotals."""
    base = V4.purchase_from_lines(lines, project, packaging)
    rows = base["rows"]
    return {"method": METHOD_ID, "rows": rows,
            "adhesive": _adhesive_purchase(rows), "tiles": _box_purchase(rows, packaging)}


def table(elements, values=OWNER_VALUES, project=None, packaging=None):
    """V4.table rows (byte-identical); sums per floor, per kind and for the project and the purchase by R-T499-1."""
    ids = [e.get("id") for e in elements]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        raise ValueError(f"duplicate element ids (a surface is reported once): {dup}")
    rows = [row(e, values, project) for e in elements]
    floors, kinds = {}, {}
    for r in rows:
        floors.setdefault(r["floor"], []).append(r)
        kinds.setdefault(r["kind"], []).append(r)
    return {"method": METHOD_ID, "supersedes": SUPERSEDES, "rules": list(RULES), "owner_values": values,
            "project_overrides": copy.deepcopy(project), "packaging": copy.deepcopy(packaging), "rows": rows,
            "per_floor": {f: _sums(v) for f, v in floors.items()},
            "per_kind": {k: _sums(v) for k, v in kinds.items()},
            "project": _sums(rows),
            "purchase": {"adhesive": _adhesive_purchase(rows), "tiles": _box_purchase(rows, packaging)}}


__all__ = ["METHOD_ID", "SUPERSEDES", "RULES", "subtotal", "bound_subtotal", "by_group", "row", "table",
           "purchase_from_lines", "tiles_from_counts", "weakest"]

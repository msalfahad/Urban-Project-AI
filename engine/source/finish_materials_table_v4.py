"""FINISH MATERIALS TABLE V4 (task T-455, owner directive 2026-11-02 B3 'tiles purchase quantities' as corrected by the
owner's site practice and the consolidated directive 'understand before calculating'; opt-in, UNWIRED_PRODUCER: read by
no released method and by no candidate V3.0.x; no released or candidate quantity changes).

Physical elements: a tiled surface (floor, wet floor, wet wall, outdoor floor) of ONE tile product laid on its bed or
render; the products bought for it are (a) tile adhesive in 20 kg bags and (b) the tiles themselves in whole boxes.
Net installed area, consumption, cutting waste, packaging surplus, spare and the purchase are kept apart (MISSION
'three layers'; UP-CER-010: packaging surplus and spare separate, never a flat size-based waste percentage).

Behaviour changes against FINISH_MATERIALS_TABLE_V3 (engine/source/finish_materials_table_v3.py, kept byte-identical):

    V1 .. V3 adhesive   area / 5 m2 per 20 kg bag for every porcelain / ceramic row whatever the tile size (Q-45 first
                        answer), and the project sum rounded up across every tile type and every row, held rows left
                        out of the sum but the 'bags to buy' still printed from the partial sum.
    V4 adhesive         UPC-ADHESIVE-001@1.0.0 (OWNER CONFIRMED 2026-11-02): coverage by tile size, 60 x 60 and
                        'normal' 5 m2, 120 x 60 3 m2, 160 x 80 3 m2 per 20 kg bag; a row keeps FRACTIONAL bags; bags
                        are rounded UP once per adhesive product at its purchasing group (default one group 'PROJECT':
                        one adhesive product for the villa), never per room, per floor or per kind. A row with no tile
                        size is HELD (never the 60 x 60 rate) with a BOUND beside it: area / 5 .. area / 3 bags, the
                        range over every size the owner rule can price (a bound, never the quantity). A group with a
                        held row has no bags to buy (HELD with its known part), never a partial figure. Per floor /
                        per kind 'adhesive_bags_to_buy' is None: rounding happens at the purchasing group only.
    V4 boxes (new)      per TILE PRODUCT (the caller's 'tile_product', one size per product): tiles consumed = the sum
                        of the rooms' layout counts (TILE_COUNT_V1 / TILE_POLYGON_GRID_V1, any simple polygon,
                        obstructions cut around: the layout IS the cutting waste, so a non-rectangular room is no
                        longer blocked); CONSERVATIVE (no offcut reuse) and OPTIMISED (offcut reuse inside the same
                        room, owner Q-59 B modified) kept as two figures; boxes = ceil(project tiles / pieces per box)
                        + ONE spare box per tile product (owner directive 2026-11-02 B3); the per-room-rounded figure
                        sum(ceil(room tiles / pieces per box)) + 1 is reported beside it as the comparison, never
                        bought (project <= per-room always: ceil of a sum <= sum of ceils). Pieces per box only from
                        a supplier / product sheet with its source; else boxes HELD (PACKAGING_NOT_ESTABLISHED), the
                        tile count still shown.

Never: a tile size, a box size, a waste percentage or a tile count invented, borrowed or defaulted; a held value as 0;
m2 / tile face used as the count (it is reported only as the NET LOWER BOUND, no cutting). Marble / stone rows: adhesive
HELD (Q-45: stone coverage not given) and boxes HELD (no packaging rule for cut stone).

Evidence status (WORKFLOW_CONTROLS s.5): a material inherits the weakest evidence status of its inputs (the caller's
'evidence_status' of the area; missing -> UNKNOWN); a HELD material is HELD. Order: VERIFIED > DRAWING-CONFIRMED >
ASSUMED - OWNER-APPROVED > UNKNOWN > HELD. The OWNER CONFIRMED rate never upgrades an unverified area.

Project-agnostic: no project, layer, room name or count appears in this module. Function names avoid the BOQ family
name terms so the T-130 guard keeps meaning 'a family is measured'.
"""

from __future__ import annotations

import copy
import math

from engine.source import company_rulebook_v1 as RB
from engine.source import finish_materials_table as V1
from engine.source import finish_materials_table_v3 as V3

METHOD_ID = "FINISH_MATERIALS_TABLE_V4"
SUPERSEDES = V3.METHOD_ID
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
RULES = V3.RULES + ("UPC-ADHESIVE-001@1.0.0 (OWNER CONFIRMED 2026-11-02: 5 / 3 / 3 m2 per 20 kg bag by tile size; ceil "
                    "per product at the purchasing group)",
                    "UP-CER-010@1.0.0 (cutting waste from the room layout; packaging surplus and spare separate)",
                    "owner Q-59 B modified (offcut reuse inside the same room only: OPTIMISED beside CONSERVATIVE)",
                    "owner directive 2026-11-02 B3 (boxes rounded at PROJECT level per tile type; one spare box per "
                    "tile type)")
CHANGE = {
    "v3_ref": "engine/source/finish_materials_table.py:68 / :232 (adhesive 5 m2 per bag, any size) and :272 (one "
              "project ceil over every row and tile type, partial sums included)",
    "v4": "adhesive by tile size (UPC-ADHESIVE-001), fractional per row, ceil per purchasing group, held group -> no "
          "bags to buy; boxes per tile product at project level + 1 spare box",
    "effect_beds_and_render": "none (V3 row, byte-identical apart from the adhesive keys)",
}

KINDS = V3.KINDS
DRY_FLOOR, WET_FLOOR, WET_WALL = V3.DRY_FLOOR, V3.WET_FLOOR, V3.WET_WALL
STAIR_FLIGHT, STAIR_LANDING, ROOF, BALCONY = V3.STAIR_FLIGHT, V3.STAIR_LANDING, V3.ROOF, V3.BALCONY
PORCELAIN_CERAMIC, MARBLE_STONE = V3.PORCELAIN_CERAMIC, V3.MARBLE_STONE
OWNER_VALUES = V3.OWNER_VALUES

HELD, OK = "HELD", "COMPUTED"
ADH_RID = "UPC-ADHESIVE-001"
SPARE_BOXES_PER_PRODUCT = 1
SPARE_SOURCE = "owner directive 2026-11-02 B3 (T-455 row): one spare box per tile type"
EVIDENCE = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "UNKNOWN", "HELD")
_EV_ALIAS = {"ASSUMED - OWNER-APPROVED": "ASSUMED — OWNER-APPROVED"}
ADH_KEYS = ("adhesive_bags", "adhesive_status", "adhesive_reason")


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _ceil(x):
    return int(math.ceil(round(x, 9) - 1e-9)) if x > 0 else 0


def _evidence(v):
    v = _EV_ALIAS.get(v, v)
    if v is None:
        return "UNKNOWN"
    if v not in EVIDENCE:
        raise ValueError(f"evidence_status {v!r} is not a WORKFLOW_CONTROLS s.5 status ({', '.join(EVIDENCE)})")
    return v


def weakest(statuses):
    """the weakest WORKFLOW_CONTROLS s.5 evidence status of a list (empty -> UNKNOWN)."""
    s = [_evidence(x) for x in statuses]
    return max(s, key=EVIDENCE.index) if s else "UNKNOWN"


def _size(e):
    """the element's tile size key ('120x60') with its source, or (None, reason). A size needs its source."""
    t = e.get("tile_cm")
    if t is None:
        return None, "TILE_SIZE_NOT_GIVEN (no printed size, no project document, no owner project decision)"
    if not str(e.get("tile_size_source") or "").strip():
        raise ValueError(f"element {e.get('id')!r}: a tile size needs its source (drawing, specification or owner "
                         f"project decision); a size with no source is never used")
    key = RB._size_key(t)
    if key is None:
        raise ValueError(f"element {e.get('id')!r}: tile size {t!r} is not 'L x W' in cm")
    return key, None


def tiles_from_counts(conservative, optimised=None):
    """two TILE_COUNT_V1 count_room() records of one room (offcut_reuse=False, and offcut_reuse=<usable side> when the
    installer / project gives one) -> the element's 'tiles' entry. A HELD record gives None (never 0)."""
    def take(rec):
        if rec is None or rec.get("status") != "RELEASED" or rec.get("tiles_to_buy") is None:
            return None
        return int(rec["tiles_to_buy"])
    out = {"conservative": take(conservative), "optimised": take(optimised),
           "source": "TILE_COUNT_V1 (TILE_POLYGON_GRID_V1 layouts, fewest-tiles layout of 8)",
           "net_m2": (conservative or {}).get("net_m2")}
    if conservative is not None and conservative.get("status") != "RELEASED":
        out["held_reason"] = conservative.get("held_reason")
    return out


def _adhesive_row(e, r):
    """UPC-ADHESIVE-001 on one row: fractional bags or HELD with the owner-rule bound."""
    area, finish = r["area_m2"], r["finish"]
    v3 = {k: r.get(k) for k in ADH_KEYS}
    out = {"adhesive_v3_flat_bags": v3["adhesive_bags"], "tile_cm": None, "tile_size_source": None,
           "adhesive_coverage_m2_per_bag": None, "adhesive_basis": None, "adhesive_bound_bags": None,
           "adhesive_group": e.get("adhesive_group", "PROJECT"), "adhesive_rule": RB._ref(ADH_RID)}
    if area is None:
        return dict(out, adhesive_bags=None, adhesive_status=HELD, adhesive_reason="AREA_HELD (never 0)")
    if finish is None:
        return dict(out, adhesive_bags=None, adhesive_status=HELD,
                    adhesive_reason="FINISH_NOT_GIVEN (no tile or stone named for this surface)")
    if finish != PORCELAIN_CERAMIC:
        return dict(out, adhesive_bags=None, adhesive_status=HELD,
                    adhesive_reason=f"ADHESIVE_COVERAGE_NOT_GIVEN for {finish} (Q-45: marble / stone coverage HELD)")
    key, why = _size(e)
    if key is None:
        return dict(out, adhesive_bags=None, adhesive_status=HELD, adhesive_reason=why,
                    adhesive_bound_bags={"low": _r(area / 5.0), "high": _r(area / 3.0),
                                         "basis": "range over every tile size UPC-ADHESIVE-001 prices (5 .. 3 m2 per "
                                                  "bag): a BOUND, never the quantity"})
    res = RB.adhesive_bags([{"id": e.get("id"), "area_m2": area, "tile_cm": key, "material": finish,
                             "purchasing_group": out["adhesive_group"]}], (e.get("project") or None))
    x = res["rows"][0]
    out.update(tile_cm=key, tile_size_source=e["tile_size_source"])
    if x["status"] != RB.OK:
        return dict(out, adhesive_bags=None, adhesive_status=HELD, adhesive_reason=x["why"],
                    adhesive_bound_bags={"low": _r(area / 5.0), "high": _r(area / 3.0),
                                         "basis": "range over every tile size UPC-ADHESIVE-001 prices: a BOUND"})
    return dict(out, adhesive_bags=_r(x["consumption"], 9), adhesive_status=OK, adhesive_reason=None,
                adhesive_coverage_m2_per_bag=x["coverage_m2_per_bag"], adhesive_basis=x["basis"])


def _tiles_row(e, r):
    t = e.get("tiles") or {}
    for k in ("conservative", "optimised"):
        v = t.get(k)
        if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
            raise ValueError(f"element {e.get('id')!r}: tiles[{k!r}] must be a whole count >= 0, got {v!r}")
    if (t.get("conservative") is not None or t.get("optimised") is not None) and not str(t.get("source") or "").strip():
        raise ValueError(f"element {e.get('id')!r}: a tile count needs its source (the room's layout record)")
    if (t.get("conservative") is not None and t.get("optimised") is not None
            and t["optimised"] > t["conservative"]):
        raise ValueError(f"element {e.get('id')!r}: the optimised count (offcut reuse) exceeds the conservative one")
    key = r.get("tile_cm")
    lower = None
    if key is not None and r["area_m2"] is not None:
        a, b = (float(p) / 100.0 for p in key.split("x"))
        lower = _r(r["area_m2"] / (a * b), 6)
    return {"tile_product": e.get("tile_product"), "tiles_conservative": t.get("conservative"),
            "tiles_optimised": t.get("optimised"), "tiles_source": t.get("source"),
            "tiles_net_lower_bound": lower,
            "tiles_reason": (None if t.get("conservative") is not None else
                             t.get("held_reason") or "LAYOUT_COUNT_NOT_GIVEN (UP-CER-010: the count comes from the "
                                                     "room's layout, never m2 / tile face)")}


def row(e, values=OWNER_VALUES, project=None):
    """V3's row; the adhesive keys by UPC-ADHESIVE-001 (fractional), plus the tile purchase keys."""
    r = V3.row(e, values, project)
    ee = dict(e, project=project)
    r.update(_adhesive_row(ee, r))
    r.update(_tiles_row(e, r))
    r["evidence_status"] = _evidence(e.get("evidence_status")) if r["area_m2"] is not None else "HELD"
    for o in r.get("operations") or ():
        if o["op"] == "ADHESIVE_AND_PORCELAIN":
            o.update(adhesive_bags=r["adhesive_bags"], adhesive_status=r["adhesive_status"],
                     adhesive_reason=r["adhesive_reason"], adhesive_v3_flat_bags=r["adhesive_v3_flat_bags"])
    return r


def _sums(rows):
    """V3 sums; adhesive bags are summed (fractional) but never rounded below the purchasing group."""
    out = V3._sums(rows)
    out["adhesive_bags_to_buy"] = None
    out["adhesive_bags_to_buy_reason"] = "rounded only at the purchasing group (see purchase.adhesive)"
    out["adhesive_bound_bags_held_rows"] = {
        "low": _r(sum(r["adhesive_bound_bags"]["low"] for r in rows if r.get("adhesive_bound_bags"))),
        "high": _r(sum(r["adhesive_bound_bags"]["high"] for r in rows if r.get("adhesive_bound_bags"))),
    } if any(r.get("adhesive_bound_bags") for r in rows) else None
    return out


def _adhesive_purchase(rows):
    groups = {}
    for r in rows:
        if r["finish"] is None and r["kind"] in (ROOF, BALCONY):
            continue                       # no tile named on a roof / balcony: reported on the row, not an adhesive row
        groups.setdefault(r["adhesive_group"], []).append(r)
    out = {}
    for g, rs in groups.items():
        held = [r["id"] for r in rs if r["adhesive_bags"] is None]
        known = sum(r["adhesive_bags"] for r in rs if r["adhesive_bags"] is not None)
        bound = [r["adhesive_bound_bags"] for r in rs if r.get("adhesive_bound_bags")]
        rec = {"rows": len(rs), "bags_known": _r(known, 6), "held_rows": held, "unit": "bag of 20 kg",
               "rule": RB._ref(ADH_RID), "evidence_status": "HELD" if held else weakest(r["evidence_status"] for r in rs),
               "waste": "NOT APPLIED (UPC-ADHESIVE-001: waste separate, sourced value only)"}
        if held:
            lo = known + sum(b["low"] for b in bound)
            hi = known + sum(b["high"] for b in bound)
            rec.update(status=HELD, bags_to_buy=None,
                       why=f"{len(held)} row(s) HELD: the group's bags are not computed (never 0); known part {known:.6f}",
                       bound_bags_to_buy=({"low": _ceil(lo), "high": _ceil(hi),
                                           "basis": "known rows + the owner-rule bound of the size-less rows; a BOUND"}
                                          if len(bound) == len(held) else None))
        else:
            rec.update(status=OK, bags_net=_r(known, 9), bags_to_buy=_ceil(known), bound_bags_to_buy=None)
        out[g] = rec
    return out


def _packaging(packaging, product):
    p = (packaging or {}).get(product)
    if p is None:
        return None
    n = p.get("pieces_per_box")
    if isinstance(n, bool) or not isinstance(n, int) or n <= 0:
        raise ValueError(f"{product}: pieces_per_box must be a whole number > 0, got {n!r}")
    if not str(p.get("source") or "").strip():
        raise ValueError(f"{product}: packaging with no source (supplier / product sheet) is never applied")
    return {"pieces_per_box": n, "source": p["source"]}


def _boxes(counts, ppb):
    tiles = sum(counts)
    project = _ceil(tiles / ppb)
    per_room = sum(_ceil(c / ppb) for c in counts)
    assert project <= per_room
    return {"tiles": tiles, "boxes_net": project, "spare_boxes": SPARE_BOXES_PER_PRODUCT,
            "boxes_to_buy": project + SPARE_BOXES_PER_PRODUCT,
            "per_room_rounded_boxes": per_room + SPARE_BOXES_PER_PRODUCT,
            "saving_vs_per_room_boxes": per_room - project,
            "tiles_bought": (project + SPARE_BOXES_PER_PRODUCT) * ppb,
            "packaging_surplus_tiles": project * ppb - tiles}


def _box_purchase(rows, packaging):
    named, unnamed, stone = {}, [], []
    for r in rows:
        if r["finish"] == MARBLE_STONE:
            stone.append(r["id"])
        elif r.get("tile_product"):
            named.setdefault(r["tile_product"], []).append(r)
        elif r["finish"] is not None:
            unnamed.append(r["id"])
    out = {"products": {}, "product_not_named": unnamed,
           "product_not_named_reason": "no tile product named for these rows: boxes HELD (a product is the purchasing "
                                       "unit; rows are never grouped by a guessed product)" if unnamed else None,
           "stone_rows": stone,
           "stone_reason": "marble / stone: no box packaging rule for cut stone; purchase HELD" if stone else None}
    for prod, rs in named.items():
        sizes = sorted({r["tile_cm"] for r in rs if r["tile_cm"] is not None})
        area_rows = [r for r in rs if r["area_m2"] is not None]
        rec = {"rows": [r["id"] for r in rs], "tile_cm": sizes[0] if len(sizes) == 1 else None,
               "area_m2": _r(sum(r["area_m2"] for r in area_rows)) if area_rows else None,
               "area_not_in_sum": [r["id"] for r in rs if r["area_m2"] is None],
               "tiles_net_lower_bound": None, "spare_source": SPARE_SOURCE}
        held = []
        if len(sizes) > 1:
            held.append(f"SIZE_CONFLICT: product {prod!r} carries sizes {sizes}")
        if not sizes:
            held.append("TILE_SIZE_NOT_GIVEN for the product")
        if len(sizes) == 1 and not rec["area_not_in_sum"]:
            a, b = (float(p) / 100.0 for p in sizes[0].split("x"))
            rec["tiles_net_lower_bound"] = _ceil(rec["area_m2"] / (a * b))
        cons = [r["tiles_conservative"] for r in rs]
        opt = [r["tiles_optimised"] for r in rs]
        missing = [r["id"] for r in rs if r["tiles_conservative"] is None]
        if missing:
            held.append(f"LAYOUT_COUNT_NOT_GIVEN for {missing} (never m2 / tile face)")
        pk = _packaging(packaging, prod)
        if pk is None:
            held.append("PACKAGING_NOT_ESTABLISHED: no pieces-per-box from a supplier / product sheet")
        rec["packaging"] = pk
        rec["tiles_conservative"] = None if missing else sum(cons)
        rec["tiles_optimised"] = None if missing or any(o is None for o in opt) else sum(opt)
        if held:
            rec.update(status=HELD, why="; ".join(held), conservative=None, optimised=None, evidence_status="HELD")
        else:
            rec.update(status=OK, why=None, conservative=_boxes(cons, pk["pieces_per_box"]),
                       optimised=(None if rec["tiles_optimised"] is None else _boxes(opt, pk["pieces_per_box"])),
                       evidence_status=weakest(r["evidence_status"] for r in rs),
                       note="OPTIMISED reuses offcuts inside the same room only (Q-59): not guaranteed field "
                            "performance; CONSERVATIVE is the no-reuse purchase")
        out["products"][prod] = rec
    return out


def purchase_from_lines(lines, project=None, packaging=None):
    """the purchase section for areas ALREADY MEASURED upstream (a candidate line index, a verified ledger): lines =
    [{'id', 'area_m2' (None = HELD), 'area_reason', 'kind' (a KINDS value, a label only), 'finish' (default by kind),
    'tile_cm', 'tile_size_source', 'tile_product', 'tiles', 'adhesive_group', 'evidence_status'}]. No surface is
    re-measured here; the same adhesive and box rules as table()."""
    ids = [x.get("id") for x in lines]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        raise ValueError(f"duplicate line ids (a surface is reported once): {dup}")
    rows = []
    for x in lines:
        kind = x.get("kind")
        if kind not in KINDS:
            raise ValueError(f"line {x.get('id')!r}: kind {kind!r} is not one of {KINDS}")
        a = x.get("area_m2")
        if a is not None and (isinstance(a, bool) or not isinstance(a, (int, float)) or not math.isfinite(a) or a < 0):
            raise ValueError(f"line {x.get('id')!r}: area {a!r} is not a finite number >= 0")
        r = {"id": x.get("id"), "floor": x.get("floor"), "kind": kind,
             "finish": x.get("finish", V3.DEFAULT_FINISH.get(kind)), "area_m2": _r(a),
             "status": "RELEASED" if a is not None else HELD, "reason": None if a is not None else
             (x.get("area_reason") or "AREA_HELD (never 0)")}
        r["adhesive_bags"] = V1.materials(kind, r["finish"], r["area_m2"])["adhesive_bags"]   # the V1 .. V3 figure
        r.update(_adhesive_row(dict(x, project=project), r))
        r.update(_tiles_row(x, r))
        r["evidence_status"] = _evidence(x.get("evidence_status")) if a is not None else "HELD"
        rows.append(r)
    return {"method": METHOD_ID, "rows": rows,
            "adhesive": _adhesive_purchase(rows), "tiles": _box_purchase(rows, packaging)}


def table(elements, values=OWNER_VALUES, project=None, packaging=None):
    """rows in input order; sums per floor, per kind and for the project (V3 keys; adhesive never rounded there); the
    purchase section: adhesive bags per purchasing group and tile boxes per tile product. packaging: {tile_product:
    {'pieces_per_box': n, 'source': '<supplier / product sheet>'}}. ids must be unique."""
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

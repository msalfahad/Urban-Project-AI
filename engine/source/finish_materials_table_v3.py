"""FINISH MATERIALS TABLE V3 (task T-457, owner directive 2026-11-02 C2 as re-scoped by the owner's site practice and
the consolidated directive 'understand before calculating'; opt-in, UNWIRED_PRODUCER: read by no released method and
by no candidate V3.0.x; no released or candidate quantity changes).

ONE behaviour change against FINISH_MATERIALS_TABLE_V2 (engine/source/finish_materials_table_v2.py, kept byte-identical),
on the WET_WALL kind only:

    V1 / V2 WET_WALL   one cement-sand 'bed' 0.02 m, mix 1:4, + 5 % waste, cement 8 bags and sand 1.1 m3 per m3
                       (labelled owner Q-45 B, PROVISIONAL), AND tile adhesive (20 kg / 5 m2) on the same m2; the
                       layer is summed into the same mortar / cement / sand totals as the floor beds; no spatter dash.
    V3 WET_WALL        the owner's three operations on the same wet-wall m2 (UPC-WETWALL-001, OWNER CONFIRMED
                       2026-11-02), each its own record, none omitted, none counted twice:
                         SPATTER_DASH            (طرطشة, plasterer)  area; mortar by UPC-CEMENT-LAYERS-METHOD-001
                         LEVELLING_RENDER        (مساح ناعم, tiler)   area; mortar by UPC-CEMENT-LAYERS-METHOD-001
                         ADHESIVE_AND_PORCELAIN  (لاصق + بورسلان, tiler) area; adhesive bags = the ONE fixing material
                       the tile 'bed' keys are NOT_APPLICABLE on a wet wall (second_fixing_bed = false), never 0 and
                       never HELD; the bed totals (mortar / cement / sand / bags to buy) are floor beds only.

Why (step 1, research/agents_t457/T-457_WET_WALL_FIXING.md): V1 / V2 never charge two mortar layers on one wet wall: the
0.02 m layer is the levelling render, and the candidate's wet-room FIN.PLASTER backing (R-WET-BACKING-1 / R-T329) is
that same coat. What was wrong is its identity: it was reported as a tile fixing bed beside the adhesive, priced with a
thickness / mix that the company rulebook 1.0.0 records as an ENGINE ASSUMPTION (UPC-CEMENT-LAYERS-METHOD-001: 'the
earlier 2 cm 1:4 wet-wall render was an engine assumption and is NOT a company rule'), and mixed into the floor-bed
cement and sand. V3 keeps the render as its own activity and takes its thickness / mix only from a sourced level 1 / 2 /
4 value (project document, owner project decision, documented engineering estimate) through the rulebook's
cement_layer; with none the render's materials are HELD with the method named, its area released (a missing
non-critical procurement parameter never blocks the area). Cement bags / sand of the render and spatter dash stay HELD
(NEEDS_PER_M3_FIGURES): the 1:4 floor-bed / black-block figures are never borrowed.

Refused (ValueError, nothing computed): a wet-wall element that asks for a mortar fixing bed (keys 'fixing_bed_m',
'bed_m' or 'bed_low_m' / 'bed_high_m'), since render + adhesive is the method (owner 2026-11-02). A layer thickness above
0.10 m is a millimetre value or a typo: that layer's mortar is HELD (THICKNESS_OUT_OF_RANGE), never computed.

Every other kind (dry / wet floors, stair flights and landings, roofs, balconies) is V2's own row, byte-identical: the
floor tile keeps its cement-sand bed (UPC-TILE-BED-001) and its adhesive. Adhesive coverage is V2's (5 m2 per 20 kg
bag for porcelain / ceramic); the tile-size rates of UPC-ADHESIVE-001 are not wired here. Project-agnostic: no project,
layer, room name or count."""

from __future__ import annotations

import copy

from engine.source import company_rulebook_v1 as RB
from engine.source import finish_materials_table as V1
from engine.source import finish_materials_table_v2 as V2

METHOD_ID = "FINISH_MATERIALS_TABLE_V3"
SUPERSEDES = V2.METHOD_ID
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
RULES = V2.RULES + ("UPC-WETWALL-001@1.0.0 (owner 2026-11-02: three operations, no second fixing bed)",
                    "UPC-CEMENT-LAYERS-METHOD-001@1.0.0 (render / spatter dash values: sourced levels 1, 2, 4 only)",
                    "T-457 C2: a wet wall carries one fixing material (adhesive); its render is its own activity")
CHANGE = {
    "v2_ref": "engine/source/finish_materials_table.py:60 / :64 (bed_m WET_WALL 0.02, mix 1:4) via V1.materials",
    "v3": "WET_WALL: bed keys NOT_APPLICABLE; operations SPATTER_DASH / LEVELLING_RENDER / ADHESIVE_AND_PORCELAIN",
    "effect_other_kinds": "none (V2 row, byte-identical)",
    "effect_totals": "mortar / cement / sand totals are floor beds only; render and spatter dash summed apart",
}

KINDS = V2.KINDS
DRY_FLOOR, WET_FLOOR, WET_WALL = V2.DRY_FLOOR, V2.WET_FLOOR, V2.WET_WALL
STAIR_FLIGHT, STAIR_LANDING, ROOF, BALCONY = V2.STAIR_FLIGHT, V2.STAIR_LANDING, V2.ROOF, V2.BALCONY
PORCELAIN_CERAMIC, MARBLE_STONE = V2.PORCELAIN_CERAMIC, V2.MARBLE_STONE
DEFAULT_FINISH = V2.DEFAULT_FINISH
OWNER_VALUES = V2.OWNER_VALUES
polygon_area = V2.polygon_area
surface = V2.surface

NOT_APPLICABLE = "NOT_APPLICABLE"
NO_BED = ("NO_FIXING_BED_ON_WET_WALL (UPC-WETWALL-001: levelling render + adhesive is the method, second_fixing_bed "
          "= false; the render is its own operation below)")
BED_KEYS = ("bed_low_m", "bed_high_m", "mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high",
            "sand_m3_low", "sand_m3_high")
BED_SUM_KEYS = ("mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high", "sand_m3_low", "sand_m3_high")
ASKED_BED = ("fixing_bed_m", "bed_m", "bed_low_m", "bed_high_m")
MAX_LAYER_M = 0.10            # input sanity only: a thicker 'render' is a millimetre value or a typo, never computed
OPERATIONS = (
    ("SPATTER_DASH", "طرطشة", "plasterer (معلم المساح)"),
    ("LEVELLING_RENDER", "مساح ناعم", "tiler (معلم السيراميك)"),
    ("ADHESIVE_AND_PORCELAIN", "لاصق + بورسلان", "tiler"),
)
_RB_RULE = "UPC-WETWALL-001"


def _layer(op, area, project):
    """spatter dash / levelling render: the rulebook's level-4 method (mortar m3 = area x sourced thickness)."""
    if area is None:
        return {"mortar_m3": None, "mortar_status": "HELD",
                "mortar_reason": "AREA_HELD (the wet-wall area is held: never 0)",
                "thickness_m": None, "thickness_basis": None, "thickness_source": None, "mix": None,
                "sensitivity_m3_per_mm": None, "materials_status": "HELD", "materials_reason": "AREA_HELD"}
    c = RB.cement_layer(area, op, project)
    t, mix = c["thickness"], c["mix"]
    out = {"mortar_m3": c.get("mortar_m3"), "mortar_status": c["status"],
           "mortar_reason": c.get("why"), "thickness_m": t["value"], "thickness_basis": t["basis"],
           "thickness_source": t["source"], "mix": mix["value"], "sensitivity_m3_per_mm": c["sensitivity_m3_per_mm"],
           "materials_status": c.get("materials_status", "HELD"),
           "materials_reason": c.get("materials_why") or "the layer's mortar volume is HELD"}
    if c["status"] == RB.OK and t["value"] > MAX_LAYER_M:
        out.update(mortar_m3=None, mortar_status="HELD", materials_status="HELD",
                   mortar_reason=f"THICKNESS_OUT_OF_RANGE ({t['value']} m > {MAX_LAYER_M} m: a millimetre value or a "
                                 f"typo; never computed)", materials_reason="THICKNESS_OUT_OF_RANGE")
    return out


def _operations(r, project):
    area = r["area_m2"]
    ops = []
    for op, ar, by in OPERATIONS:
        rec = {"op": op, "ar": ar, "by": by, "rule": f"{_RB_RULE}@1.0.0", "area_m2": area,
               "area_status": r["status"], "area_reason": r["reason"]}
        if op == "ADHESIVE_AND_PORCELAIN":
            rec.update(fixing_material="ADHESIVE", adhesive_bags=r["adhesive_bags"],
                       adhesive_status=r["adhesive_status"], adhesive_reason=r["adhesive_reason"])
        else:
            rec.update(_layer(op, area, project))
        ops.append(rec)
    return ops


def row(e, values=OWNER_VALUES, project=None):
    """V2's row; on a wet wall the tile bed is NOT_APPLICABLE and the three owner operations are listed."""
    if e.get("kind") != WET_WALL:
        return V2.row(e, values)
    asked = [k for k in ASKED_BED if e.get(k) is not None]
    if asked:
        raise ValueError(f"element {e.get('id')!r}: a mortar fixing bed asked on a wet wall ({', '.join(asked)}): "
                         f"SECOND_FIXING_BED refused, levelling render + adhesive is the method (UPC-WETWALL-001)")
    r = V2.row(e, values)
    for k in BED_KEYS:
        r[k] = None
    r.update(mix=None, mortar_status=NOT_APPLICABLE, mortar_reason=NO_BED, cement_sand_status=NOT_APPLICABLE,
             cement_sand_reason=NO_BED, fixing_material="ADHESIVE", operations=_operations(r, project))
    return r


def _op_sums(rows):
    out = {}
    for op, _, _ in OPERATIONS[:2]:
        recs = [(r["id"], o) for r in rows for o in r.get("operations") or () if o["op"] == op]
        if not recs:
            continue
        a = [o["area_m2"] for _, o in recs if o["area_m2"] is not None]
        m = [o["mortar_m3"] for _, o in recs if o["mortar_m3"] is not None]
        out[op] = {"rows": len(recs),
                   "area_m2": V1._r(sum(a)) if a else None,
                   "area_not_in_sum": [i for i, o in recs if o["area_m2"] is None],
                   "mortar_m3": V1._r(sum(m)) if m else None,
                   "mortar_not_in_sum": [i for i, o in recs if o["mortar_m3"] is None],
                   "cement_bags": None, "sand_m3": None,
                   "materials_status": "HELD (NEEDS_PER_M3_FIGURES of a sourced mix; UPC-CEMENT-LAYERS-METHOD-001)"}
    return out


def _sums(rows):
    """V1 sums for the area and the adhesive over every row; the bed totals over the rows that HAVE a bed (a wet wall's
    bed is NOT_APPLICABLE: neither summed nor listed as held); render / spatter dash summed apart."""
    out = V1._sums(rows)
    bedded = [r for r in rows if r.get("mortar_status") != NOT_APPLICABLE]
    na = [r["id"] for r in rows if r.get("mortar_status") == NOT_APPLICABLE]
    if bedded:
        b = V1._sums(bedded)
        for k in BED_SUM_KEYS + ("cement_bags_to_buy_low", "cement_bags_to_buy_high"):
            out[k] = b[k]
        nis = {k: v for k, v in out["not_in_sum"].items() if k not in BED_SUM_KEYS}
        nis.update({k: v for k, v in b["not_in_sum"].items() if k in BED_SUM_KEYS})
        out["not_in_sum"] = nis
    else:
        for k in BED_SUM_KEYS + ("cement_bags_to_buy_low", "cement_bags_to_buy_high"):
            out[k] = None
        out["not_in_sum"] = {k: v for k, v in out["not_in_sum"].items() if k not in BED_SUM_KEYS}
    out["bed_not_applicable_rows"] = na
    out["wet_wall_operations"] = _op_sums(rows)
    return out


def table(elements, values=OWNER_VALUES, project=None):
    """Rows in input order, sums per floor, per kind and for the project (a held value is listed under not_in_sum,
    never added as 0; ids must be unique). project: rulebook overrides {rule_id: {param: {value, level, source}}}."""
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
            "project_overrides": copy.deepcopy(project), "rows": rows,
            "per_floor": {f: _sums(v) for f, v in floors.items()},
            "per_kind": {k: _sums(v) for k, v in kinds.items()},
            "project": _sums(rows)}

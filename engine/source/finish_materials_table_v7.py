"""FINISH MATERIALS TABLE V7 (task T-528, from Q-53 C; opt-in, UNWIRED_PRODUCER: read by no released method and by no
candidate V3.0.x; no released or candidate quantity changes).

Physical element: the 1:3 cement-sand BED laid under stair marble (treads, risers, landings; owner Q-45: stair bed
0.03 m, mix 1:3). What is BUILT is the installed bed (area x bed thickness, no loss: R-T521-1, V6). What the bed is MADE
OF is derived from its mix (owner Q-53 answer C, CALCULATED PROVISIONAL RATE, record UP-STAIR-017 1.0.0 in
URBAN_RULES 1.8.0, read through engine/source/rule_store_v2.py, never retyped):

    dry volume  = mortar m3 x dry_volume_factor (1.33)
    cement      = dry volume x 1 / (1 + 3) = 0.3325 m3 -> x 1440 kg/m3 = 478.8 kg -> / 50 kg = 9.576 bags per m3
    sand        = dry volume x 3 / (1 + 3) = 0.9975 m3 loose per m3

V7 recomputes those figures from the record's own params and refuses the record when its printed theoretical figures
disagree with that arithmetic (STAIR_RATE_INCONSISTENT -> the stair cement / sand stay HELD, nothing invented).

Defect fixed (Verifier 2026-11-05 09:00 on T-521 MERGED; Worker 2 08:46): V1 .. V6 hold the stair cement / sand
('MIX_1:3_CEMENT_SAND_NOT_GIVEN') although Q-53 is answered. V7 = V6 with, on a STAIR_FLIGHT / STAIR_LANDING row whose
mix is 1:3 and whose installed bed is produced (R-T528-1):

    cement_bags_low / high, sand_m3_low / high     INSTALLED mortar x the theoretical rate (no loss, never rounded)
    cement_kg_low / high, cement_m3_low / high     the same cement as weight and loose volume (new keys, stair only)
    cement_bags_procurement_*, sand_m3_procurement_* the V6 PROCUREMENT mortar (installed + the Q-45 5 % named loss,
                                                   its own account, D-T518-1) x the same theoretical rate
    cement_sand_status                             'CALCULATED PROVISIONAL' (the Q-53 label), cement_sand_reason None
    stair_rate                                     the rule reference, params and the recomputed figures
    bed_purchasing_allowance                       the record's PRELIMINARY PURCHASING layer (10 bags + 1.00 m3 per
                                                   m3 of installed mortar), a separate labelled layer: never summed
                                                   into the theoretical or the procurement keys, never the to-buy

Cement bags are rounded once per purchasing group from PROCUREMENT (V6 purchase['bed_mortar'], unchanged code): the
stair rows now carry numbers, so a group with only released beds prints its whole bags; sand stays loose m3.

Unchanged (byte-identical to V6): every row that is not a 1:3 stair bed; a stair bed with no bed thickness (HELD);
a stair bed with another mix (HELD as V1: no rate given, and the 1:4 figures are never borrowed); a held stair area;
a held procurement (loss with no source). Project-agnostic: no project, layer, room name or count in this module.
"""

from __future__ import annotations

import copy
import math

from engine.source import finish_materials_table_v5 as V5
from engine.source import finish_materials_table_v6 as V6
from engine.source import rule_store_v2 as RS

METHOD_ID = "FINISH_MATERIALS_TABLE_V7"
SUPERSEDES = V6.METHOD_ID
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
RULES = V6.RULES + ("R-T528-1@1.0.0 (stair marble 1:3 bed: theoretical cement / sand = mortar m3 x the UP-STAIR-017 "
                    "Q-53 C rate derived from the mix; installed and procurement each their own field; the "
                    "preliminary purchasing allowance a separate layer)",)
CHANGE = {
    "v6_ref": "engine/source/finish_materials_table.py:216-218 (1:3 has no per_m3_of_mortar entry -> "
              "MIX_1:3_CEMENT_SAND_NOT_GIVEN) inherited by V2 .. V6",
    "v7": "R-T528-1: stair 1:3 cement / sand from UP-STAIR-017 (Q-53 C), recomputed from its params",
    "effect_stair": "stair cement / sand keys leave HELD (installed and procurement); subtotals and group to-buy over "
                    "them leave HELD when no other row is held",
    "effect_other_keys": "none (every non-stair row byte-identical to V6)",
}

HELD, OK = V6.HELD, V6.OK
NOT_APPLICABLE = V6.NOT_APPLICABLE
KINDS = V6.KINDS
DRY_FLOOR, WET_FLOOR, WET_WALL = V6.DRY_FLOOR, V6.WET_FLOOR, V6.WET_WALL
STAIR_FLIGHT, STAIR_LANDING, ROOF, BALCONY = V6.STAIR_FLIGHT, V6.STAIR_LANDING, V6.ROOF, V6.BALCONY
PORCELAIN_CERAMIC, MARBLE_STONE = V6.PORCELAIN_CERAMIC, V6.MARBLE_STONE
OWNER_VALUES = V6.OWNER_VALUES
LOSS_Q45 = V6.LOSS_Q45
subtotal = V6.subtotal
tiles_from_counts = V6.tiles_from_counts
weakest = V6.weakest

STAIR_KINDS = (STAIR_FLIGHT, STAIR_LANDING)
STAIR_MIX = "1:3"
STAIR_RULE_ID = "UP-STAIR-017"
STAIR_RULE_SET = "1.8.0"
STATUS_Q53 = "CALCULATED PROVISIONAL"
ALLOWANCE_LABEL = ("PRELIMINARY PURCHASING allowance (UP-STAIR-017 / Q-53: about 10 bags + 1.00 m3 per m3), a separate "
                   "layer: never the theoretical quantity, never summed into procurement or the to-buy")
_TOL = 1e-9


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _pos(v):
    return (not isinstance(v, bool)) and isinstance(v, (int, float)) and math.isfinite(v) and v > 0


def _ratio(mix):
    """'1:3' -> (1.0, 3.0), else None."""
    try:
        a, b = (float(x) for x in str(mix).split(":"))
    except (TypeError, ValueError):
        return None
    return (a, b) if _pos(a) and _pos(b) else None


def stair_rate(rule=None):
    """the 1:3 stair bed rate from UP-STAIR-017 -> (rate dict or None, held reason or None). The rate is recomputed
    from the record's params (dry factor, ratio, density, bag mass); a record that is not OWNER_APPROVED, not 1:3,
    missing a parameter or printing figures that disagree with its own arithmetic is refused (HELD), never patched."""
    if rule is None:
        rule = RS.rule(STAIR_RULE_ID, STAIR_RULE_SET)
    rid = rule.get("rule_id")
    if rid != STAIR_RULE_ID or rule.get("status") != "OWNER_APPROVED":
        return None, f"STAIR_RATE_NOT_APPROVED ({rid!r} status {rule.get('status')!r}: only an OWNER_APPROVED " \
                     f"{STAIR_RULE_ID} is applied)"
    p = rule.get("params") or {}
    if p.get("mix_cement_sand") != STAIR_MIX:
        return None, f"STAIR_RATE_MIX_MISMATCH (record mix {p.get('mix_cement_sand')!r}, bed mix {STAIR_MIX})"
    ratio = _ratio(p.get("mix_cement_sand"))
    need = ("dry_volume_factor", "cement_bulk_density_kg_m3", "bag_kg")
    miss = [k for k in need if not _pos(p.get(k))]
    if ratio is None or miss:
        return None, f"STAIR_RATE_PARAM_NOT_GIVEN ({', '.join(miss) or 'mix ratio'}): no figure derived"
    c, s = ratio
    dry = float(p["dry_volume_factor"])
    cem_m3 = dry * c / (c + s)
    cem_kg = cem_m3 * float(p["cement_bulk_density_kg_m3"])
    bags = cem_kg / float(p["bag_kg"])
    sand = dry * s / (c + s)
    derived = {"theoretical_cement_m3_per_m3": cem_m3, "theoretical_cement_kg_per_m3": cem_kg,
               "theoretical_cement_bags_per_m3": bags, "theoretical_sand_m3_per_m3": sand}
    bad = [k for k, v in derived.items() if p.get(k) is not None and abs(float(p[k]) - v) > 1e-6 * max(1.0, v)]
    if bad:
        return None, f"STAIR_RATE_INCONSISTENT ({', '.join(bad)} printed in {rid} disagree with its own derivation)"
    pa = rule.get("purchasing_allowance") or {}
    allowance = None
    if _pos(pa.get("cement_bags_per_m3")) and _pos(pa.get("sand_m3_per_m3")):
        allowance = {"cement_bags_per_m3": float(pa["cement_bags_per_m3"]), "sand_m3_per_m3": float(pa["sand_m3_per_m3"])}
    return {"rule_id": rid, "rule_version": rule.get("version"), "rule_set": STAIR_RULE_SET,
            "source": (rule.get("approval") or {}).get("source"), "status": STATUS_Q53, "mix": STAIR_MIX,
            "dry_volume_factor": dry, "cement_bulk_density_kg_m3": float(p["cement_bulk_density_kg_m3"]),
            "bag_kg": float(p["bag_kg"]), "cement_m3_per_m3": _r(cem_m3, 9), "cement_kg_per_m3": _r(cem_kg, 9),
            "cement_bags_per_m3": _r(bags, 9), "sand_m3_per_m3": _r(sand, 9),
            "arithmetic": f"{dry} x {c:g}/{c + s:g} x {p['cement_bulk_density_kg_m3']:g} / {p['bag_kg']:g} = "
                          f"{_r(bags, 6)} bags; sand {dry} x {s:g}/{c + s:g} = {_r(sand, 6)} m3",
            "purchasing_allowance": allowance}, None


def _is_stair_bed(r):
    return r.get("kind") in STAIR_KINDS and r.get("mix") == STAIR_MIX and r.get("mortar_status") != NOT_APPLICABLE


def row(e, values=OWNER_VALUES, project=None, loss=LOSS_Q45, rule=None):
    """V6's row; on a released 1:3 stair bed the cement / sand from the Q-53 rate (R-T528-1)."""
    per = (values.get("per_m3_of_mortar") or {}).get(STAIR_MIX)
    if per is not None:
        raise ValueError(f"values['per_m3_of_mortar']['{STAIR_MIX}'] given ({per!r}): V7 reads the 1:3 rate from "
                         f"{STAIR_RULE_ID} only (two rate sources refused)")
    r = V6.row(e, values, project, loss)
    if not _is_stair_bed(r) or r["mortar_m3_low"] is None:
        return r            # not a stair 1:3 bed, or its bed is HELD (thickness / area): V6 byte-identical
    rate, why = stair_rate(rule)
    r["stair_rate"] = rate
    if rate is None:
        r["cement_sand_reason"] = f"{r.get('cement_sand_reason')}; {why}"
        r["bed_purchasing_allowance"] = None
        return r
    b, k, m, s = (rate["cement_bags_per_m3"], rate["cement_kg_per_m3"], rate["cement_m3_per_m3"],
                  rate["sand_m3_per_m3"])
    for lh in ("low", "high"):
        mo = r[f"mortar_m3_{lh}"]
        r[f"cement_bags_{lh}"] = _r(mo * b)
        r[f"cement_kg_{lh}"] = _r(mo * k)
        r[f"cement_m3_{lh}"] = _r(mo * m)
        r[f"sand_m3_{lh}"] = _r(mo * s)
        pm = r.get(f"bed_procurement_m3_{lh}")
        r[f"cement_bags_procurement_{lh}"] = None if pm is None else _r(pm * b)
        r[f"sand_m3_procurement_{lh}"] = None if pm is None else _r(pm * s)
    r.update(cement_sand_status=STATUS_Q53, cement_sand_reason=None)
    pa = rate["purchasing_allowance"]
    r["bed_purchasing_allowance"] = None if pa is None else {
        "label": ALLOWANCE_LABEL,
        "cement_bags_low": _r(r["mortar_m3_low"] * pa["cement_bags_per_m3"]),
        "cement_bags_high": _r(r["mortar_m3_high"] * pa["cement_bags_per_m3"]),
        "sand_m3_low": _r(r["mortar_m3_low"] * pa["sand_m3_per_m3"]),
        "sand_m3_high": _r(r["mortar_m3_high"] * pa["sand_m3_per_m3"])}
    return r


def _bed_purchase(rows):
    """V6 purchase per group (unchanged code); a group holding a 1:3 stair bed also lists its stair rows and the
    stair purchasing allowance subtotal (labelled, never in to-buy)."""
    out = V6._bed_purchase(rows)
    for g, rec in out.items():
        st = [r for r in rows if r.get("mortar_group", V6.DEFAULT_GROUP) == g and "stair_rate" in r]
        if not st:
            continue
        rec["stair_1_3_rows"] = [r["id"] for r in st]
        al = {}
        for k in ("cement_bags_low", "cement_bags_high", "sand_m3_low", "sand_m3_high"):
            al[k] = subtotal((r["id"], (r["bed_purchasing_allowance"] or {}).get(k)) for r in st)
        rec["stair_purchasing_allowance"] = {"label": ALLOWANCE_LABEL, "subtotals": al}
    return out


def table(elements, values=OWNER_VALUES, project=None, packaging=None, loss=LOSS_Q45, rule=None):
    """V6.table with R-T528-1 on the stair rows. ids must be unique."""
    ids = [e.get("id") for e in elements]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        raise ValueError(f"duplicate element ids (a surface is reported once): {dup}")
    rows = [row(e, values, project, loss, rule) for e in elements]
    floors, kinds = {}, {}
    for r in rows:
        floors.setdefault(r["floor"], []).append(r)
        kinds.setdefault(r["kind"], []).append(r)
    return {"method": METHOD_ID, "supersedes": SUPERSEDES, "rules": list(RULES), "owner_values": values,
            "loss": copy.deepcopy(loss), "project_overrides": copy.deepcopy(project),
            "packaging": copy.deepcopy(packaging), "rows": rows,
            "per_floor": {f: V6._sums(v) for f, v in floors.items()},
            "per_kind": {k: V6._sums(v) for k, v in kinds.items()},
            "project": V6._sums(rows),
            "purchase": {"adhesive": V5._adhesive_purchase(rows), "tiles": V5._box_purchase(rows, packaging),
                         "bed_mortar": _bed_purchase(rows)}}


def diff_v6(elements, values=OWNER_VALUES, project=None, packaging=None, loss=LOSS_Q45):
    """per row the keys whose value moved V6 -> V7 (new keys included); a non-stair row lists none."""
    t6 = V6.table(elements, values, project, packaging, loss)
    t7 = table(elements, values, project, packaging, loss)
    out = []
    for a, b in zip(t6["rows"], t7["rows"]):
        moved = sorted(k for k in set(a) | set(b) if a.get(k, "<absent>") != b.get(k, "<absent>"))
        out.append({"id": a["id"], "kind": a["kind"], "moved": moved,
                    "v6": {k: a.get(k) for k in moved}, "v7": {k: b.get(k) for k in moved}})
    return out


__all__ = ["METHOD_ID", "SUPERSEDES", "RULES", "LOSS_Q45", "stair_rate", "row", "table", "diff_v6", "subtotal",
           "tiles_from_counts", "weakest"]

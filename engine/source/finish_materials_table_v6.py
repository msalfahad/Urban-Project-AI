"""FINISH MATERIALS TABLE V6 (task T-521, from D-T518-1; opt-in, UNWIRED_PRODUCER: read by no released method and by
no candidate V3.0.x; no released or candidate quantity changes).

Physical element: the cement-sand BED laid under a floor tile / stair marble (owner Q-45: regular floors 0.03 - 0.04 m,
wet floors 0.04 - 0.06 m, stairs 0.03 m; 1:4 = about 8 x 50 kg cement and 1.1 m3 loose sand per m3 of mortar). What is
BUILT is the installed bed: area x bed thickness. What is BOUGHT is the installed bed + a named loss (Q-45 B 5 %,
ASSUMED - OWNER-APPROVED 2026-10-20 12:15) + the pack rounding of the cement, once per purchasing group. Three layers,
each its own field (lesson PROPOSED 2026-11-05: waste never inside installed).

Defect fixed (D-T518-1, Checker CONFIRMED on T-518 MERGED 7f7b7564):

    V1 .. V5   engine/source/finish_materials_table.py:213-214 materials(): mortar_m3 = area x bed x (1 + mortar_waste),
               cement / sand derived from it, no waste field: 10 m2 dry floor -> 0.315 .. 0.420 m3 printed as the bed
               (installed 0.300 .. 0.400); the per-floor / per-kind / project 'cement bags to buy' rounded at every level.
    V6 row     mortar_m3_low / high, cement_bags_low / high, sand_m3_low / high are INSTALLED (no loss): exactly V5 /
               (1 + 0.05) where V5 folded the waste. Beside them, per row:
                 bed_loss                      {'value', 'source', 'status'} or None (the one loss record applied)
                 bed_loss_m3_low / high        procurement - installed
                 bed_procurement_m3_low / high installed x (1 + loss): byte-identical to the V5 mortar figure at 5 %
                 cement_bags_procurement_*, sand_m3_procurement_*  from the procurement mortar (= V5 cement / sand)
                 bed_procurement_status / _reason   HELD when the loss carries no source: the installed bed is still
                                               produced (a missing procurement parameter never blocks what is built)
                 mortar_group                  the purchasing group (caller's 'mortar_group', default 'PROJECT')
    V6 sums    the V5 R-T499-1 subtotals over the INSTALLED keys; procurement keys subtotalled the same way (HELD over
               any held row, AT_LEAST known part); 'cement_bags_to_buy_*' per floor / per kind / project is None: the
               ceil happens once per purchasing group, from PROCUREMENT, in purchase['bed_mortar'].
    V6 purchase  purchase['bed_mortar'][group]: installed / loss / procurement mortar, cement bags and sand, and
               cement_bags_to_buy_low / high = ceil(procurement bags) ONCE for the group; HELD (never a partial whole
               bag figure) when any bedded row of the group is held for that key. Sand stays loose m3: no load size is
               sourced (SAND_PACK_NOT_ESTABLISHED), so it is never rounded.

Unchanged from V5 (byte-identical, imported): the surface, the adhesive (UPC-ADHESIVE-001) and the tile boxes; the wet
wall (owner 2026-11-02: spatter dash + levelling render + adhesive and porcelain, no second fixing bed: its bed keys
stay NOT_APPLICABLE, no loss, no procurement bed, not in any bed sum or group); the render / spatter dash layers (the
rulebook's cement_layer, no waste inside); the 1:3 stair bed cement / sand stays HELD as V1 (the Q-53 calculated rate
is not wired by this task); roof / balcony screed thickness HELD (Q-41).

One loss source only: V6 reads the loss from its 'loss' argument (default LOSS_Q45). values['mortar_waste'] is never
applied; if present it must equal the loss value (two disagreeing waste sources -> ValueError, nothing computed).
Never: a loss with no source applied, a held value as 0, a whole-bag figure rounded from a partial sum or below the
purchasing group. Project-agnostic: no project, layer, room name or count appears in this module.
"""

from __future__ import annotations

import copy
import math

from engine.source import finish_materials_table_v5 as V5

METHOD_ID = "FINISH_MATERIALS_TABLE_V6"
SUPERSEDES = V5.METHOD_ID
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
RULES = V5.RULES + ("R-T521-1@1.0.0 (tile-bed / screed mortar INSTALLED = area x bed, no loss; the named loss and the "
                    "procurement each their own field; cement bags rounded once per purchasing group from procurement)",)
CHANGE = {
    "v5_ref": "engine/source/finish_materials_table.py:213-214 (mortar_m3 = area x bed x (1 + mortar_waste)) inherited "
              "by V2 :49, V3 V2.row, V4 V3.row, V5 V4.row; finish_materials_table.py:270-271 (to-buy at every level)",
    "v6": "R-T521-1: installed bed without loss; bed_loss / bed_procurement fields; to-buy per purchasing group only",
    "effect_installed": "mortar / cement / sand plain keys drop by exactly 1 / 1.05 on every bedded row",
    "effect_procurement": "bed_procurement_* and *_procurement_* = the V5 plain-key values at the Q-45 5 %",
    "effect_other_keys": "none (surface, adhesive, boxes, wet-wall operations byte-identical to V5)",
}

HELD, OK = V5.HELD, V5.OK
NOT_APPLICABLE = "NOT_APPLICABLE"
KINDS = V5.KINDS
DRY_FLOOR, WET_FLOOR, WET_WALL = V5.DRY_FLOOR, V5.WET_FLOOR, V5.WET_WALL
STAIR_FLIGHT, STAIR_LANDING, ROOF, BALCONY = V5.STAIR_FLIGHT, V5.STAIR_LANDING, V5.ROOF, V5.BALCONY
PORCELAIN_CERAMIC, MARBLE_STONE = V5.PORCELAIN_CERAMIC, V5.MARBLE_STONE
# the V5 owner values without 'mortar_waste': in V6 the loss lives only in the loss record (LOSS_Q45)
OWNER_VALUES = {k: v for k, v in V5.OWNER_VALUES.items() if k != "mortar_waste"}
subtotal = V5.subtotal
tiles_from_counts = V5.tiles_from_counts
weakest = V5.weakest

LOSS_Q45 = {
    "value": 0.05,
    "source": "owner Q-45 answer B 2026-10-19 21:40 (waste 5 % on mortar, practice value accepted, PROVISIONAL); "
              "applicability kept by the owner correction 2026-10-20 12:15 (OWNER_DIRECTIVE_2026-10-20 withdrawal note)",
    "status": "ASSUMED — OWNER-APPROVED",
}
DEFAULT_GROUP = "PROJECT"
PAIRS = (("low", "low"), ("high", "high"))
INSTALLED_KEYS = ("mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high", "sand_m3_low",
                  "sand_m3_high")
PROC_KEYS = ("bed_loss_m3_low", "bed_loss_m3_high", "bed_procurement_m3_low", "bed_procurement_m3_high",
             "cement_bags_procurement_low", "cement_bags_procurement_high", "sand_m3_procurement_low",
             "sand_m3_procurement_high")
_TO_BUY = ("cement_bags_to_buy_low", "cement_bags_to_buy_high")
SAND_PACK = "SAND_PACK_NOT_ESTABLISHED (loose m3; no load / bag size sourced: never rounded)"


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _ceil(x):
    return int(math.ceil(round(x, 9) - 1e-9)) if x > 0 else 0


def _loss(loss):
    """the loss record -> (factor or None, record, held reason or None). No source -> not applied (HELD), never 0."""
    if loss is None:
        return None, None, "LOSS_NOT_GIVEN (no named loss for the bed mortar: procurement HELD, installed produced)"
    if not isinstance(loss, dict):
        raise ValueError(f"loss must be {{'value', 'source', 'status'}}, got {loss!r}")
    v = loss.get("value")
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v < 1:
        return None, dict(loss), f"LOSS_INVALID ({v!r}: a fraction 0 <= f < 1; never applied)"
    rec = {"value": float(v), "source": loss.get("source"), "status": loss.get("status")}
    if not str(loss.get("source") or "").strip():
        return None, rec, "LOSS_SOURCE_NOT_GIVEN (a loss with no source is never applied: procurement HELD)"
    return float(v), rec, None


def _values(values, factor):
    w = values.get("mortar_waste")
    if w is not None and factor is not None and abs(float(w) - factor) > 1e-12:
        raise ValueError(f"two waste sources disagree: values['mortar_waste'] {w!r} vs loss {factor!r}; V6 applies the "
                         f"loss record only")
    return dict(values, mortar_waste=0.0)


def _bedded(r):
    return r.get("mortar_status") != NOT_APPLICABLE


def row(e, values=OWNER_VALUES, project=None, loss=LOSS_Q45):
    """V5's row with the bed INSTALLED (no loss) under the plain keys and the loss / procurement beside it."""
    factor, rec, why = _loss(loss)
    r = V5.row(e, _values(values, factor), project)
    r["mortar_group"] = e.get("mortar_group", DEFAULT_GROUP)
    r["mortar_stage"] = "INSTALLED" if _bedded(r) else NOT_APPLICABLE
    blank = {k: None for k in PROC_KEYS}
    if not _bedded(r):
        r.update(blank, bed_loss=None, bed_procurement_status=NOT_APPLICABLE, bed_procurement_reason=r["mortar_reason"])
        return r
    r.update(blank, bed_loss=rec)
    if r["mortar_m3_low"] is None:
        r.update(bed_procurement_status=HELD, bed_procurement_reason=f"INSTALLED_BED_HELD: {r['mortar_reason']}")
        return r
    if factor is None:
        r.update(bed_procurement_status=HELD, bed_procurement_reason=why)
        return r
    # procurement through the same V1 arithmetic at the named loss: byte-identical to V5 at 5 %
    p = V5.row(e, dict(values, mortar_waste=factor), project)
    for lh, _ in PAIRS:
        r[f"bed_procurement_m3_{lh}"] = p[f"mortar_m3_{lh}"]
        r[f"bed_loss_m3_{lh}"] = _r(p[f"mortar_m3_{lh}"] - r[f"mortar_m3_{lh}"])
        r[f"cement_bags_procurement_{lh}"] = p[f"cement_bags_{lh}"]
        r[f"sand_m3_procurement_{lh}"] = p[f"sand_m3_{lh}"]
    r.update(bed_procurement_status=r["mortar_status"], bed_procurement_reason=None)
    return r


def _proc_sums(rows):
    bedded = [r for r in rows if _bedded(r)]
    return {k: subtotal((r["id"], r[k]) for r in bedded) for k in PROC_KEYS}


def _sums(rows):
    """V5 sums (R-T499-1) over the installed keys; procurement subtotals beside them; no whole bags below the group."""
    out = V5._sums(rows)
    for k in _TO_BUY:
        out[k] = None
        out.pop(k + "_status", None)
        out[k + "_reason"] = "rounded only once per purchasing group, from PROCUREMENT (see purchase.bed_mortar)"
    out["bed_mortar_stage"] = "INSTALLED (no loss: R-T521-1)"
    out["bed_procurement"] = _proc_sums(rows)
    return out


def _bed_purchase(rows):
    groups = {}
    for r in rows:
        if _bedded(r):
            groups.setdefault(r["mortar_group"], []).append(r)
    out = {}
    for g, rs in groups.items():
        s = {k: subtotal((r["id"], r[k]) for r in rs) for k in INSTALLED_KEYS + PROC_KEYS}
        losses = sorted({(r["bed_loss"] or {}).get("source") or "" for r in rs if r["bed_loss"]})
        rec = {"rows": len(rs), "row_ids": [r["id"] for r in rs], "subtotals": s,
               "loss_sources": [x for x in losses if x], "unit_cement": "bag of 50 kg", "sand": SAND_PACK,
               "evidence_status": "HELD" if any(r["area_m2"] is None for r in rs) else weakest(
                   r["evidence_status"] for r in rs)}
        for lh, _ in PAIRS:
            c = s[f"cement_bags_procurement_{lh}"]
            if c["status"] == OK:
                rec[f"cement_bags_to_buy_{lh}"] = _ceil(c["value"])
                rec[f"cement_bags_to_buy_{lh}_status"] = OK
            else:
                rec[f"cement_bags_to_buy_{lh}"] = None
                rec[f"cement_bags_to_buy_{lh}_status"] = HELD
                rec[f"cement_bags_to_buy_{lh}_reason"] = (
                    f"procurement cement HELD over {len(c['held_rows'])} row(s) {c['held_rows']}: no whole bags from a "
                    f"partial sum (known part AT_LEAST {c['at_least']})")
        out[g] = rec
    return out


def table(elements, values=OWNER_VALUES, project=None, packaging=None, loss=LOSS_Q45):
    """V5.table with R-T521-1: rows, sums per floor / kind / project, the V5 adhesive and tile purchase unchanged, and
    purchase['bed_mortar'] per purchasing group. ids must be unique."""
    ids = [e.get("id") for e in elements]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        raise ValueError(f"duplicate element ids (a surface is reported once): {dup}")
    rows = [row(e, values, project, loss) for e in elements]
    floors, kinds = {}, {}
    for r in rows:
        floors.setdefault(r["floor"], []).append(r)
        kinds.setdefault(r["kind"], []).append(r)
    return {"method": METHOD_ID, "supersedes": SUPERSEDES, "rules": list(RULES), "owner_values": values,
            "loss": copy.deepcopy(loss), "project_overrides": copy.deepcopy(project),
            "packaging": copy.deepcopy(packaging), "rows": rows,
            "per_floor": {f: _sums(v) for f, v in floors.items()},
            "per_kind": {k: _sums(v) for k, v in kinds.items()},
            "project": _sums(rows),
            "purchase": {"adhesive": V5._adhesive_purchase(rows), "tiles": V5._box_purchase(rows, packaging),
                         "bed_mortar": _bed_purchase(rows)}}


def diff_v5(elements, values=OWNER_VALUES, project=None, packaging=None):
    """the V5 -> V6 diff per row and material key: installed keys V6 / V5 ratio, procurement equal to V5, every other
    row key byte-identical (returned as the list of keys that moved)."""
    t5 = V5.table(elements, dict(values, mortar_waste=LOSS_Q45["value"]), project, packaging)
    t6 = table(elements, values, project, packaging, LOSS_Q45)
    out = []
    for a, b in zip(t5["rows"], t6["rows"]):
        moved = sorted(k for k in a if k not in INSTALLED_KEYS and a[k] != b.get(k))
        rec = {"id": a["id"], "kind": a["kind"], "other_keys_moved": moved, "keys": {}}
        for k in INSTALLED_KEYS:
            lh = k.rsplit("_", 1)[1]
            proc = {"mortar_m3": "bed_procurement_m3_", "cement_bags": "cement_bags_procurement_",
                    "sand_m3": "sand_m3_procurement_"}[k.rsplit("_", 1)[0]] + lh
            rec["keys"][k] = {"v5": a[k], "v6_installed": b[k], "v6_procurement": b[proc],
                              "ratio_v6_v5": None if not a[k] or b[k] is None else _r(b[k] / a[k], 9)}
        out.append(rec)
    return out


__all__ = ["METHOD_ID", "SUPERSEDES", "RULES", "LOSS_Q45", "row", "table", "diff_v5", "subtotal", "tiles_from_counts",
           "weakest"]

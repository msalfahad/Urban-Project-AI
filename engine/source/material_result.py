"""MATERIAL RESULT (M9 S1) - what a layout consumes, kept apart from the net BOQ quantity (generic; stdlib).

Not engine/source/waste_procurement.py (V3b, the rule-driven waste layer of the earlier rounds, unchanged): this
schema records a CUTTING PLAN's material, never a waste percentage.

A material result is a VIEW of one canonical BOQ line (boq_line.py): it names the line it belongs to and never changes
that line's measured_net. Every area is reported on its own:

    net_installed_m2       the surface finished (the BOQ net: tile joints included, each membrane point once)
    placed_m2              material lying in the work outside any lap (tiles: the pieces; membrane: = net)
    joint_m2               net - placed (tiles only)
    overlap_m2             material lying in laps (membrane side / end laps, upturn lap onto the floor)
    consumed_m2            material cut from opened units (tiles opened x tile area; rolls cut x roll area - untouched
                           remainder)
    reusable_offcuts_m2    offcuts at least the minimum reusable size, retained (not credited to another room in S1)
    cutting_waste_m2       consumed - placed - overlap - reusable offcuts            (owner definition, M9 S1 addendum)
    cutting_waste_pct      cutting_waste / net_installed x 100
    packaging              whole boxes / rolls; packaging surplus = packs x pack area - consumed (UNRESOLVED without
                           pack data - never guessed)
    spare_allowance        NOT_SET unless the owner sets one (with its source); never a default percentage
    procurement            packs to order = consumed units + spare units, in whole packs

Material balance (checked on every result): consumed = placed + overlap + cutting waste + reusable offcuts, and
packs x pack area = consumed + packaging surplus.
"""

from __future__ import annotations

import math

SCHEMA = "URBAN_MATERIAL_RESULT_V1"
STATES = ("COMPUTED", "COMPUTED_REVIEW", "BLOCKED")
PACK_STATES = ("RESOLVED", "UNRESOLVED")
TOL = 1e-6


class ResultError(ValueError):
    pass


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def spare(pct=None, source=None):
    """an owner-approved spare allowance (attic stock); without both a value and its source it stays NOT_SET."""
    if pct is None:
        return {"state": "NOT_SET", "pct": None, "source": None}
    if not source:
        raise ResultError("a spare allowance needs its source (owner decision / specification)")
    if pct < 0:
        raise ResultError("a spare allowance cannot be negative")
    return {"state": "OWNER_SET", "pct": pct, "source": source}


def packaging(*, unit, consumed_units, unit_area_m2, units_per_pack=None, pack_area_m2=None, consumed_m2,
              spare_allowance=None, source=None):
    """whole packs for the consumed units (+ spare). units_per_pack None -> UNRESOLVED (counts in units only)."""
    sp = spare_allowance or spare()
    spare_units = math.ceil(consumed_units * sp["pct"] / 100.0 - 1e-9) if sp["state"] == "OWNER_SET" else 0
    rec = {"pack_unit": unit, "units_per_pack": units_per_pack, "pack_area_m2": _r(pack_area_m2),
           "consumed_units": consumed_units, "spare": sp, "spare_units": spare_units, "source": source}
    if not units_per_pack:
        rec.update(state="UNRESOLVED", reason="PACKAGING_NOT_ESTABLISHED: no pieces-per-box / roll data for the "
                   "selected product (supplier or data sheet needed)", packs=None, pack_total_m2=None,
                   packaging_surplus_m2=None, procurement_units=consumed_units + spare_units,
                   procurement_packs=None, procurement_m2=None)
        return rec
    if pack_area_m2 is None:
        pack_area_m2 = units_per_pack * unit_area_m2
    packs = math.ceil(consumed_units / units_per_pack - 1e-9)
    proc_packs = math.ceil((consumed_units + spare_units) / units_per_pack - 1e-9)
    rec.update(state="RESOLVED", reason="", packs=packs, pack_area_m2=_r(pack_area_m2), pack_total_m2=_r(packs * pack_area_m2),
               packaging_surplus_m2=_r(packs * pack_area_m2 - consumed_m2), procurement_units=consumed_units + spare_units,
               procurement_packs=proc_packs, procurement_m2=_r(proc_packs * pack_area_m2))
    return rec


SPEC_KEYS = ("spec_id", "kind", "name_en", "name_ar", "length_m", "width_m", "roll_width_m", "roll_length_m",
             "min_side_lap_m", "min_end_lap_m", "pieces_per_box", "box_area_m2", "authority", "lap_source", "data_sheet",
             "overrides", "packaging_source")


def _spec_view(spec):
    return {k: spec.get(k) for k in SPEC_KEYS if spec.get(k) is not None} if spec else {}


def make_result(*, method, spec, net_installed_m2, placed_m2, consumed_m2, reusable_offcuts_m2, overlap_m2=0.0,
                units, pack, layout, assumptions, concerns=(), line_id=None, location=None, rule_refs=(),
                state="COMPUTED", components=None):
    """units: {"unit": "pcs" | "roll", "unit_area_m2", "consumed_units", "full", "cut"}; pack: packaging(...)."""
    waste = consumed_m2 - placed_m2 - overlap_m2 - reusable_offcuts_m2
    joint = net_installed_m2 - placed_m2 if spec["kind"] == "TILE" else 0.0
    res = {"schema": SCHEMA, "method": method, "state": state, "line_id": line_id, "location": location or {},
           "material_spec": _spec_view(spec),
           "net_installed_m2": _r(net_installed_m2), "placed_m2": _r(placed_m2), "joint_m2": _r(joint),
           "overlap_m2": _r(overlap_m2), "consumed_m2": _r(consumed_m2), "reusable_offcuts_m2": _r(reusable_offcuts_m2),
           "cutting_waste_m2": _r(waste),
           "cutting_waste_pct": _r(100.0 * waste / net_installed_m2, 4) if net_installed_m2 > 0 else None,
           "waste_if_offcuts_discarded_m2": _r(waste + reusable_offcuts_m2),
           "utilisation_pct": _r(100.0 * (placed_m2 + overlap_m2) / consumed_m2, 4) if consumed_m2 > 0 else None,
           "units": units, "packaging": pack, "spare_allowance": pack.get("spare") if pack else None,
           "layout": layout, "components": components or [], "assumptions": list(assumptions),
           "concerns": sorted(set(concerns)), "rule_refs": list(rule_refs), "blocked_by": None}
    return check(res)


def blocked(*, method, spec, reason, net_installed_m2=None, line_id=None, location=None, assumptions=(), rule_refs=()):
    """a calculation the S1 engine cannot do: every material quantity is None, the reason names the missing capability."""
    return {"schema": SCHEMA, "method": method, "state": "BLOCKED", "line_id": line_id, "location": location or {},
            "material_spec": _spec_view(spec),
            "net_installed_m2": _r(net_installed_m2), "placed_m2": None, "joint_m2": None, "overlap_m2": None,
            "consumed_m2": None, "reusable_offcuts_m2": None, "cutting_waste_m2": None, "cutting_waste_pct": None,
            "waste_if_offcuts_discarded_m2": None, "utilisation_pct": None, "units": None, "packaging": None,
            "spare_allowance": None, "layout": None, "components": [], "assumptions": list(assumptions),
            "concerns": [], "rule_refs": list(rule_refs), "blocked_by": reason}


def check(res):
    """the balance and sign rules every computed result obeys (ResultError otherwise)."""
    if res["state"] == "BLOCKED":
        if not res.get("blocked_by"):
            raise ResultError("a blocked result names what blocks it")
        if any(res[k] is not None for k in ("consumed_m2", "cutting_waste_m2", "packaging")):
            raise ResultError("a blocked result carries no material quantity")
        return res
    for k in ("net_installed_m2", "placed_m2", "consumed_m2", "reusable_offcuts_m2", "overlap_m2"):
        if res[k] is None or res[k] < -TOL:
            raise ResultError(f"{k} must be a non-negative number")
    if res["cutting_waste_m2"] < -1e-5:
        raise ResultError(f"negative cutting waste {res['cutting_waste_m2']}: the material does not balance")
    parts = res["placed_m2"] + res["overlap_m2"] + res["cutting_waste_m2"] + res["reusable_offcuts_m2"]
    if abs(parts - res["consumed_m2"]) > 1e-5:
        raise ResultError("consumed != placed + overlap + cutting waste + reusable offcuts")
    if res["placed_m2"] > res["net_installed_m2"] + 1e-5:
        raise ResultError("more material placed than the net surface (a lap counted as placed?)")
    u = res["units"]
    if abs(u["consumed_units"] * u["unit_area_m2"] - res["consumed_m2"]) > 1e-5 and u["unit"] != "roll":
        raise ResultError("consumed area != consumed units x unit area")
    p = res["packaging"]
    if p["state"] == "RESOLVED" and abs(p["pack_total_m2"] - res["consumed_m2"] - p["packaging_surplus_m2"]) > 1e-5:
        raise ResultError("packs x pack area != consumed + packaging surplus")
    if p["state"] == "RESOLVED" and p["packaging_surplus_m2"] < -1e-5:
        raise ResultError("negative packaging surplus")
    return res


def trace(line, res, tol=5e-4):
    """the result belongs to the line and carries the line's net: [] or the breaks found."""
    out = []
    if res.get("line_id") != line["line_id"]:
        out.append(f"result names {res.get('line_id')}, not {line['line_id']}")
    if res["state"] != "BLOCKED" and line.get("measured_net") is not None and \
            abs(res["net_installed_m2"] - line["measured_net"]) > tol:
        out.append(f"net {res['net_installed_m2']} != line measured_net {line['measured_net']}")
    return out


def policy_record():
    return {"policy_id": SCHEMA,
            "definitions": {"cutting_waste": "consumed - placed - overlap - reusable offcuts retained",
                            "cutting_waste_pct": "cutting waste / net installed area x 100",
                            "packaging_surplus": "whole packs x pack area - consumed",
                            "procurement": "whole packs for consumed + spare units",
                            "spare_allowance": "NOT_SET unless owner-approved with its source"},
            "never": ["a flat waste percentage", "net / pack area as the pack count", "waste or procurement inside "
                      "measured_net", "a pack size the data does not give"]}

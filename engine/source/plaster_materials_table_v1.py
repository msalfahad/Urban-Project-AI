"""PLASTER MATERIALS TABLE V1 (task T-454, owner directive 2026-11-02 B2 'plaster purchase quantities' as corrected by
the owner's site practice and the consolidated directive 'understand before calculating'; opt-in, UNWIRED_PRODUCER:
read by no released method and by no candidate V3.0.x; no released or candidate quantity changes).

Physical elements (one face, its coats kept apart; ERS s.2.1, owner OD-V3B-4 .. 7 layer order, UPC-WETWALL-001):

    DRY_WALL_PLASTER   a dry interior face: SPATTER coat thrown on the substrate, then the two-coat cement plaster
                       (first coat 'بطانة' + finishing coat 'ضهارة'), then paint. Layers: BOND_COAT + WALL_PLASTER.
    WET_WALL_RENDER    a tiled wet face (bathrooms, kitchens, pantries, laundry, ironing rooms): SPATTER coat
                       (plasterer), LEVELLING_RENDER under the tile (tiler), adhesive + porcelain (FINISH_MATERIALS_TABLE_V3).
                       Layers here: BOND_COAT + LEVELLING_RENDER. No second fixing bed (UPC-WETWALL-001).
    anything else      (an unclassified face, a mixed dry / wet line) -> every layer HELD (CLASS_NOT_ESTABLISHED).

For each layer: area m2 (the face area, never re-measured here) -> mortar m3 = area x thickness (UPC-CEMENT-LAYERS-
METHOD-001, level 4 method) -> cement bags / sand m3 = mortar m3 x per-m3 figures of the applicable mix. Water HELD.

Values (search order of UPC-CEMENT-LAYERS-METHOD-001: project spec -> drawings -> owner project decision -> company
rulebook -> documented estimate). The company rulebook 1.0.0 gives none, so REFERENCE (below) carries the documented
engineering reference values, each with its source and kind, passed to the rulebook as level 4 overrides:

    WALL_PLASTER       0.015 + 0.005 = 0.020 m, kind EXACT (two printed coat thicknesses, summed)
    LEVELLING_RENDER   0.015 m, kind MINIMUM ('not less than'): a printed minimum is a BOUND, never the quantity
                       (lessons register 2026-11-02, T-350): mortar is reported AT_LEAST, the line stays HELD
    BOND_COAT          no thickness in any accessible source: mortar HELD (area released)
    mixes              no cement : sand ratio in any accessible source for any of the three layers: cement / sand HELD
                       (NEEDS_MIX). The black-block 1:4 (Q-78) and the stair-bed 1:3 (Q-53) are never borrowed.

A project passes its own values (level 1 specification / 2 owner decision) with `project` (rulebook override form) and
per-m3 mix figures with `mix_figures` = {layer: {"cement_bags_per_m3": x, "sand_m3_per_m3": y, "source": "..."}};
an entry with no source is refused. Labels: a material is labelled from its weakest input (lessons register, T-453):
an ENGINEERING ESTIMATE thickness gives ESTIMATED-NET (never VERIFIED-NET, whatever the area label); a HELD area
gives HELD (never 0). Project-agnostic: no project, layer, room name or count. Function names avoid the B4-05 /
B9-04 family name terms so the T-130 guard keeps meaning 'a family is measured'.
"""

from __future__ import annotations

import copy
import math

from engine.source import company_rulebook_v1 as RB

METHOD_ID = "PLASTER_MATERIALS_TABLE_V1"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
SUPERSEDES = None
RULES = ("UPC-CEMENT-LAYERS-METHOD-001@1.0.0 (mortar m3 = area x sourced thickness; values level 1 / 2 / 4 only)",
         "UPC-WETWALL-001@1.0.0 (wet wall: spatter + levelling render + adhesive / porcelain; no second fixing bed)",
         "UPC-HEIGHT-001@1.0.0 (plaster to the structural slab / roof underside: an AREA rule, applied upstream)",
         "OD-V3B-4 .. 7 (owner 2026-10-04: spatter under every finished wall face, then the next coat)")

DRY, WET = "DRY_WALL_PLASTER", "WET_WALL_RENDER"
CLASSES = (DRY, WET)
LAYERS = {DRY: ("BOND_COAT", "WALL_PLASTER"), WET: ("BOND_COAT", "LEVELLING_RENDER")}
RB_LAYER = {"BOND_COAT": "SPATTER_DASH", "WALL_PLASTER": "WALL_PLASTER", "LEVELLING_RENDER": "LEVELLING_RENDER"}
AR = {"BOND_COAT": "طرطشة", "WALL_PLASTER": "لياسة (بطانة + ضهارة)", "LEVELLING_RENDER": "مساح ناعم تحت السيراميك"}
RID = "UPC-CEMENT-LAYERS-METHOD-001"
HELD, AT_LEAST, OK = "HELD", "AT_LEAST", "COMPUTED"
VNET, PNET, ENET = "VERIFIED-NET", "PROVISIONAL-NET", "ESTIMATED-NET"
AREA_LABELS = (VNET, PNET)
MAX_LAYER_M = 0.10            # input sanity: a thicker coat is a millimetre value or a typo, never computed

_KSE = ("Kuwait Society of Engineers, 'Bayt Al-Omr: general advice to citizens on building' (2023), finishing works "
        "list (Drive: Engineering Sources / 01 Kuwait References)")
REFERENCE = {
    "WALL_PLASTER": {"thickness_m": 0.020, "kind": "EXACT",
                     "parts_m": {"first coat (بطانة)": 0.015, "finishing coat (ضهارة)": 0.005},
                     "source": _KSE + ", item 60: first coat 1.5 cm, washed sand; item 62: second coat 0.5 cm, washed "
                               "and sieved sand (sum 2.0 cm)"},
    "LEVELLING_RENDER": {"thickness_m": 0.015, "kind": "MINIMUM",
                         "source": _KSE + ", item 75: wet-area wall render under ceramic 'not less than 1.5 cm'"},
    "BOND_COAT": {"thickness_m": None, "kind": None,
                  "source": _KSE + ", item 57: spatter with fine aggregate 'per the specification' (no thickness, no "
                            "mix)"},
}
MIX_SOURCE_NOTE = ("no accessible source prints a cement : sand ratio for spatter, wall plaster or levelling render; "
                   "the Kuwait General Specification 1990 text available through the connector stops at chapter "
                   "02230 (T-080); the 1:4 black-block (Q-78) and 1:3 stair-bed (Q-53) figures are never borrowed")


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _num(v, what):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v) or v < 0:
        raise ValueError(f"{what} must be a finite number >= 0, got {v!r}")
    return float(v)


def reference_overrides(reference=REFERENCE):
    """REFERENCE -> rulebook level 4 overrides (only the thickness values a source prints)."""
    ov = {}
    for layer, ref in reference.items():
        if ref.get("thickness_m") is not None:
            ov[f"{RB._LAYERS[RB_LAYER[layer]]}_thickness_m"] = {"value": ref["thickness_m"], "level": 4,
                                                                 "source": ref["source"]}
    return {RID: ov} if ov else {}


def _merge(project, reference):
    """a project value (level 1 / 2 / 4) wins over the reference estimate, parameter by parameter."""
    out = copy.deepcopy(reference_overrides(reference))
    for rid, params in (project or {}).items():
        out.setdefault(rid, {}).update(copy.deepcopy(params))
    return out


def _kind(layer, eff, reference):
    """EXACT / MINIMUM of the thickness actually used (a project value is EXACT unless it says 'kind')."""
    p = eff.get(RID, {}).get(f"{RB._LAYERS[RB_LAYER[layer]]}_thickness_m")
    if p is None:
        return None
    ref = reference.get(layer) or {}
    if ref.get("thickness_m") is not None and p.get("source") == ref.get("source"):
        return ref["kind"]
    return p.get("kind", "EXACT")


def _mix(layer, mix_figures):
    m = (mix_figures or {}).get(layer)
    if m is None:
        return None
    if not str(m.get("source") or "").strip():
        raise ValueError(f"{layer}: mix figures with no source are never applied")
    return {"cement_bags_per_m3": _num(m.get("cement_bags_per_m3"), f"{layer} cement bags per m3"),
            "sand_m3_per_m3": _num(m.get("sand_m3_per_m3"), f"{layer} sand m3 per m3"), "source": m["source"]}


def _layer_row(e, layer, eff, reference, mix_figures):
    area, alabel = e.get("area_m2"), e.get("area_label")
    rec = {"layer": layer, "ar": AR[layer], "area_m2": _r(area), "area_label": alabel if area is not None else HELD,
           "rule": f"{RID}@1.0.0", "water": HELD, "water_reason": "water_l_per_m3 not given (UPC-CEMENT-LAYERS-METHOD-001)"}
    if area is None:
        return dict(rec, status=HELD, label=HELD, reason=e.get("area_reason") or "AREA_HELD (never 0)",
                    mortar_m3=None, mortar_m3_at_least=None, thickness_m=None, thickness_kind=None,
                    thickness_basis=None, thickness_source=None, sensitivity_m3_per_mm=None,
                    cement_bags=None, sand_m3=None, materials_status=HELD, materials_reason="AREA_HELD")
    c = RB.cement_layer(area, RB_LAYER[layer], eff)
    t = c["thickness"]
    kind = _kind(layer, eff, reference)
    rec.update(thickness_m=t["value"], thickness_kind=kind, thickness_basis=t["basis"], thickness_source=t["source"],
               sensitivity_m3_per_mm=c["sensitivity_m3_per_mm"])
    if c["status"] != RB.OK:
        return dict(rec, status=HELD, label=HELD, reason=c["why"], mortar_m3=None, mortar_m3_at_least=None,
                    cement_bags=None, sand_m3=None, materials_status=HELD, materials_reason="THICKNESS_NOT_SOURCED")
    if t["value"] > MAX_LAYER_M:
        why = f"THICKNESS_OUT_OF_RANGE ({t['value']} m > {MAX_LAYER_M} m: a millimetre value or a typo; never computed)"
        return dict(rec, status=HELD, label=HELD, reason=why, mortar_m3=None, mortar_m3_at_least=None,
                    cement_bags=None, sand_m3=None, materials_status=HELD, materials_reason="THICKNESS_OUT_OF_RANGE")
    m3 = _r(c["mortar_m3"], 9)
    estimate = t["level"] == 4
    label = ENET if estimate else alabel
    if kind == "MINIMUM":
        rec.update(status=AT_LEAST, label=HELD, mortar_m3=None, mortar_m3_at_least=m3,
                   reason="printed thickness is a minimum ('not less than'): a bound beside a HELD figure, never the "
                          "quantity")
    else:
        rec.update(status=OK, label=label, mortar_m3=m3, mortar_m3_at_least=None,
                   reason="ENGINEERING ESTIMATE thickness (level 4): never VERIFIED" if estimate else t["basis"])
    mix = _mix(layer, mix_figures)
    if mix is None:
        rec.update(cement_bags=None, sand_m3=None, materials_status=HELD,
                   materials_reason="NEEDS_MIX: " + MIX_SOURCE_NOTE)
    else:
        base = rec["mortar_m3"] if rec["mortar_m3"] is not None else rec["mortar_m3_at_least"]
        rec.update(cement_bags=_r(base * mix["cement_bags_per_m3"], 6), sand_m3=_r(base * mix["sand_m3_per_m3"], 6),
                   materials_status=rec["status"], materials_reason=f"mix figures: {mix['source']}")
    return rec


def row(e, project=None, reference=REFERENCE, mix_figures=None):
    """one face element {id, class, area_m2 (None = HELD), area_label, area_reason} -> its layers."""
    if e.get("area_m2") is not None:
        _num(e["area_m2"], f"element {e.get('id')!r} area")
        if e.get("area_label") not in AREA_LABELS:
            raise ValueError(f"element {e.get('id')!r}: a released area needs its label ({', '.join(AREA_LABELS)})")
    cls = e.get("class")
    out = {"id": e.get("id"), "class": cls, "area_m2": _r(e.get("area_m2")), "source": e.get("source")}
    if cls not in CLASSES:
        why = f"CLASS_NOT_ESTABLISHED ({cls!r}): dry plaster or wet render not settled for this face; every layer HELD"
        out["layers"] = [{"layer": ly, "ar": AR[ly], "area_m2": _r(e.get("area_m2")), "class_held": True,
                          "status": HELD, "label": HELD,
                          "reason": why, "mortar_m3": None, "mortar_m3_at_least": None, "cement_bags": None,
                          "sand_m3": None, "materials_status": HELD, "water": HELD}
                         for ly in ("BOND_COAT", "WALL_PLASTER", "LEVELLING_RENDER")]
        return out
    eff = _merge(project, reference)
    out["layers"] = [_layer_row(e, ly, eff, reference, mix_figures) for ly in LAYERS[cls]]
    return out


def _sums(rows):
    out = {}
    for ly in ("BOND_COAT", "WALL_PLASTER", "LEVELLING_RENDER"):
        recs = [(r["id"], x) for r in rows for x in r["layers"] if x["layer"] == ly]
        if not recs:
            continue
        area_in = [x["area_m2"] for _, x in recs if x["area_m2"] is not None and not x.get("class_held")]
        m =[x["mortar_m3"] for _, x in recs if x.get("mortar_m3") is not None]
        lo = [x["mortar_m3_at_least"] for _, x in recs if x.get("mortar_m3_at_least") is not None]
        out[ly] = {"rows": len(recs),
                   "area_m2": _r(sum(area_in)) if area_in else None,
                   "area_not_in_sum": [i for i, x in recs if x["area_m2"] is None or x.get("class_held")],
                   "mortar_m3": _r(sum(m)) if m else None,
                   "mortar_m3_at_least": _r(sum(lo)) if lo else None,
                   "mortar_not_in_sum": [i for i, x in recs if x.get("mortar_m3") is None],
                   "cement_bags": None if any(x.get("cement_bags") is None for _, x in recs)
                   else _r(sum(x["cement_bags"] for _, x in recs)),
                   "sand_m3": None if any(x.get("sand_m3") is None for _, x in recs)
                   else _r(sum(x["sand_m3"] for _, x in recs))}
    return out


def table(elements, project=None, reference=REFERENCE, mix_figures=None):
    """rows in input order + sums per layer (a held value is listed under *_not_in_sum, never added as 0; a cement /
    sand total exists only when every row of the layer has one; ids must be unique)."""
    ids = [e.get("id") for e in elements]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        raise ValueError(f"duplicate element ids (a face is reported once): {dup}")
    rows = [row(e, project, reference, mix_figures) for e in elements]
    return {"method": METHOD_ID, "rules": list(RULES), "reference": copy.deepcopy(reference),
            "project_overrides": copy.deepcopy(project), "mix_figures": copy.deepcopy(mix_figures),
            "rows": rows, "sums": _sums(rows)}

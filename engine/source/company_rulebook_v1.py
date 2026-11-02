"""COMPANY RULEBOOK V1 (T-448) - the Urban Projects Company Rulebook: lookup with the 5-level hierarchy and the
procurement calculators of its OWNER CONFIRMED rules (generic; stdlib only; nothing here knows a project).

    load() / digest() / record(rule_id)                    the rulebook file rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json
    param(rule_id, name, project=None)                     -> {value, level, basis, source}; a project override wins
    lintel(masonry_opening_m, project=None, bearing=None)  -> precast lintel piece (UPC-LINTEL-001)
    adhesive_bags(rows, project=None, waste=None)          -> tile adhesive bags per row and per purchasing group
    aac_bond_bags(rows, project=None, waste=None)          -> white AAC glue kg / bags per row and per purchasing group
    black_blocks(net_area_m2, thickness_m, project=None, waste=None) -> black block count (UPC-BLACK-BLOCK-001)
    black_block_laying_materials(mortar_m3, project=None)  -> cement bags / loose sand of black-block mortar
    tile_bed(area_m2, floor_kind, project=None)            -> floor tile bed mortar / cement / sand as a range
    cement_layer(area_m2, layer, project=None)             -> spatter dash / render / plaster materials (level 4 method)

These are RULE calculators (a given quantity -> materials by an owner rate). They measure nothing and produce no BOQ
line: no family of BOQ_FAMILY_MASTER changes capability here (B9-04 masonry joint mortar and B4-05 spatter dash stay
NOT_IMPLEMENTED until their integration rows, T-372 / T-364, wire a measured quantity through them and register it).
The names avoid the family name terms on purpose so the T-130 guard keeps meaning 'a family is measured'.

Hierarchy (MISSION consolidated directive 2026-11-02): 1 PROJECT DOCUMENT, 2 OWNER PROJECT DECISION, 3 OWNER CONFIRMED
COMPANY RULE (the file), 4 ENGINEERING ESTIMATE, 5 ASSUMPTION-UNRESOLVED. A project override is passed as
    project = {rule_id: {param_name: {"value": v, "level": 1 | 2 | 4, "source": "<document / decision / reference>"}}}
and applies to that call only: the rulebook file is never changed. Level 4 may fill only a parameter the company rules
leave empty (value null), and must carry a source. A value that no level supplies is HELD (never 0, never a default).
Net quantity, consumption, waste and procurement are kept apart; waste is applied only when a sourced value is given.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = "rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"
METHOD = "COMPANY_RULEBOOK_V1"
VERSION = "1.0.0"
BASIS = {1: "PROJECT DOCUMENT", 2: "OWNER PROJECT DECISION", 3: "OWNER CONFIRMED COMPANY RULE",
         4: "ENGINEERING ESTIMATE", 5: "ASSUMPTION-UNRESOLVED"}
HELD, FLAGGED, OK = "HELD", "FLAGGED", "COMPUTED"
EPS = 1e-9


class RulebookError(ValueError):
    pass


@lru_cache(maxsize=None)
def _book():
    return json.loads((ROOT / "rules" / REL).read_text(encoding="utf-8"))


def load():
    return copy.deepcopy(_book())


def digest():
    return hashlib.sha256(json.dumps(_book(), sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def record(rule_id):
    for r in _book()["records"]:
        if r["rule_id"] == rule_id:
            return copy.deepcopy(r)
    raise KeyError(f"{rule_id} is not in the company rulebook {VERSION}")


def _ref(rule_id):
    return f"{rule_id}@{record(rule_id)['version']} (rulebook {VERSION})"


def param(rule_id, name, project=None):
    """the effective value of one parameter: a level 1 / 2 project override, else the company value (level 3), else a
    sourced level 4 estimate for a parameter the company leaves empty, else HELD (level 5, value None)."""
    rec = record(rule_id)
    if name not in rec["params"]:
        raise KeyError(f"{rule_id} has no parameter {name!r}")
    company = rec["params"][name]["value"]
    ov = ((project or {}).get(rule_id) or {}).get(name)
    if ov is not None:
        lvl, src = ov.get("level"), ov.get("source")
        if lvl not in (1, 2, 4):
            raise RulebookError(f"{rule_id}.{name}: an override must be level 1, 2 or 4, got {lvl!r}")
        if not isinstance(src, str) or not src.strip():
            raise RulebookError(f"{rule_id}.{name}: an override needs its source")
        if lvl == 4 and company is not None:
            raise RulebookError(f"{rule_id}.{name}: an engineering estimate cannot replace an OWNER CONFIRMED value")
        if ov.get("value") is None:
            raise RulebookError(f"{rule_id}.{name}: an override with no value (missing is HELD, never an override)")
        return {"value": copy.deepcopy(ov["value"]), "level": lvl, "basis": BASIS[lvl], "source": src}
    if company is None:
        return {"value": None, "level": 5, "basis": BASIS[5], "source": f"{_ref(rule_id)}: {name} not given"}
    return {"value": copy.deepcopy(company), "level": 3, "basis": BASIS[3], "source": _ref(rule_id)}


def _num(v, what, positive=True):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
        raise RulebookError(f"{what} must be a finite number, got {v!r}")
    if v < 0 or (positive and v == 0):
        raise RulebookError(f"{what} must be {'> 0' if positive else '>= 0'}, got {v!r}")
    return float(v)


def _ceil(x):
    return int(math.ceil(round(x, 9) - EPS)) if x > 0 else 0


def _waste(waste):
    if waste is None:
        return None
    if not isinstance(waste, dict) or not str(waste.get("source") or "").strip():
        raise RulebookError("waste must be {'value': fraction, 'source': ...}: a waste with no source is never applied")
    v = _num(waste.get("value"), "waste", positive=False)
    if v >= 1:
        raise RulebookError(f"waste is a fraction (< 1), got {v!r}")
    return {"value": v, "source": waste["source"]}


# ---------------------------------------------------------------- lintels

def lintel(masonry_opening_m, project=None, bearing=None):
    """one precast lintel for one masonry opening. bearing: {'m': value, 'source': ...} from the drawings / supplier."""
    rid = "UPC-LINTEL-001"
    if masonry_opening_m is None:
        return {"rule": _ref(rid), "status": HELD, "why": "masonry opening width not established (never 0)"}
    w = _num(masonry_opening_m, "masonry opening")
    stock = param(rid, "stock_lengths_m", project)
    minb = param(rid, "min_bearing_each_side_m", project)
    if bearing is not None:
        if not str(bearing.get("source") or "").strip():
            raise RulebookError("a project bearing needs its source (drawing, note or supplier table)")
        b = _num(bearing.get("m"), "bearing")
        if b < minb["value"] - EPS:
            return {"rule": _ref(rid), "status": FLAGGED, "masonry_opening_m": w, "bearing_m": b,
                    "why": f"CONFLICT: the project bearing {b} m is below the company minimum {minb['value']} m "
                           f"({minb['source']}); reported, never silently used",
                    "bearing_source": bearing["source"]}
        bsrc, blvl = bearing["source"], 1
    else:
        b, bsrc, blvl = minb["value"], minb["source"], minb["level"]
    need = round(w + 2 * b, 6)
    lengths = sorted(float(x) for x in stock["value"])
    pick = next((x for x in lengths if x >= need - EPS), None)
    out = {"rule": _ref(rid), "masonry_opening_m": w, "bearing_m": b, "bearing_basis": BASIS[blvl],
           "bearing_source": bsrc, "required_m": need, "stock_lengths_m": lengths, "stock_basis": stock["basis"],
           "stock_source": stock["source"], "capacity_check": "NOT_PERFORMED (owner practice is not structural "
                                                              "approval: supplier load / span table or drawings)"}
    if pick is None:
        return dict(out, status=FLAGGED, count=None, piece_m=None,
                    why=f"needs {need} m > the longest stock length {lengths[-1]} m: cast-in-situ or design, "
                        f"never forced into a stock piece")
    return dict(out, status=OK, count=1, piece_m=pick, unit="nr")


# ---------------------------------------------------------------- grouped bag calculators

def _size_key(tile_cm):
    if isinstance(tile_cm, str):
        parts = tile_cm.lower().replace(" ", "").split("x")
        try:
            a, b = (float(p) for p in parts)
        except ValueError:
            return None
    else:
        try:
            a, b = (float(p) for p in tile_cm)
        except (TypeError, ValueError):
            return None
    if a <= 0 or b <= 0:
        return None
    hi, lo = max(a, b), min(a, b)
    return f"{hi:g}x{lo:g}"


def _group(rows_out, unit_per_bag, waste, what):
    groups = {}
    for r in rows_out:
        groups.setdefault(r["purchasing_group"], []).append(r)
    res = {}
    for g, rs in groups.items():
        held = [r["id"] for r in rs if r["status"] == HELD]
        known = round(sum(r["consumption"] for r in rs if r["status"] != HELD), 9)
        rec = {"rows": len(rs), "consumption_known": known, "held_rows": held, "waste": waste}
        if held:
            rec.update(status=HELD, bags_to_buy=None,
                       why=f"{len(held)} row(s) HELD: the group's {what} bags are not computed (never 0); "
                           f"known part {known}")
        else:
            gross = known * (1 + waste["value"]) if waste else known
            rec.update(status=OK, consumption_with_waste=round(gross, 9) if waste else None,
                       bags_net=round(known / unit_per_bag, 9), bags_to_buy=_ceil(gross / unit_per_bag),
                       waste_applied=bool(waste))
        res[g] = rec
    return res


def adhesive_bags(rows, project=None, waste=None):
    """rows: [{'id', 'area_m2', 'tile_cm': '120x60' | (120, 60), 'purchasing_group' (default 'PROJECT'),
    'material' (default 'PORCELAIN_CERAMIC')}]. Bags rounded up once per purchasing group, room values fractional."""
    rid = "UPC-ADHESIVE-001"
    w = _waste(waste)
    bag_kg = param(rid, "bag_kg", project)
    table = param(rid, "coverage_m2_per_bag_by_size_cm", project)
    normal = param(rid, "coverage_m2_per_bag_normal_class", project)
    classified = ((project or {}).get(rid) or {}).get("normal_class_sizes") or {}
    out = []
    for r in rows:
        rec = {"id": r.get("id"), "purchasing_group": r.get("purchasing_group", "PROJECT"), "rule": _ref(rid)}
        area = r.get("area_m2")
        if area is None:
            out.append(dict(rec, status=HELD, consumption=None, why="area HELD (never 0)"))
            continue
        area = _num(area, f"area of {r.get('id')}", positive=False)
        if r.get("material", "PORCELAIN_CERAMIC") != "PORCELAIN_CERAMIC":
            out.append(dict(rec, status=HELD, consumption=None,
                            why=f"coverage for {r.get('material')} not given (Q-45: marble / stone HELD)"))
            continue
        key = _size_key(r.get("tile_cm"))
        if key is None:
            out.append(dict(rec, status=HELD, consumption=None, why="tile size not given"))
            continue
        if key in table["value"]:
            cov, basis, src = float(table["value"][key]), table["basis"], table["source"]
        elif key in classified:
            csrc = classified[key]
            if not isinstance(csrc, str) or not csrc.strip():
                raise RulebookError(f"the NORMAL classification of {key} needs its source")
            cov, basis, src = float(normal["value"]), BASIS[2], f"{csrc}; rate {normal['source']}"
        else:
            out.append(dict(rec, status=HELD, consumption=None, tile=key,
                            why=f"tile {key} is not in the OWNER CONFIRMED table and not classified NORMAL by the "
                                f"project / owner: HELD, never the 60 x 60 rate"))
            continue
        out.append(dict(rec, status=OK, tile=key, area_m2=area, coverage_m2_per_bag=cov, basis=basis, source=src,
                        consumption=round(area / cov, 9), bag_kg=bag_kg["value"]))
    # consumption is in bags here; the group divides by 1 bag per bag
    return {"rule": _ref(rid), "unit": "bag of %g kg" % bag_kg["value"], "rows": out,
            "groups": _group(out, 1.0, w, "adhesive")}


def aac_bond_bags(rows, project=None, waste=None):
    """rows: [{'id', 'net_area_m2', 'thickness_m', 'purchasing_group'}] -> kg per row; 25 kg bags per group."""
    rid = "UPC-AAC-GLUE-001"
    w = _waste(waste)
    bag = param(rid, "bag_kg", project)
    rates = param(rid, "kg_per_m2_by_thickness_m", project)
    out = []
    for r in rows:
        rec = {"id": r.get("id"), "purchasing_group": r.get("purchasing_group", "PROJECT"), "rule": _ref(rid)}
        area, t = r.get("net_area_m2"), r.get("thickness_m")
        if area is None:
            out.append(dict(rec, status=HELD, consumption=None, why="net area HELD (never 0)"))
            continue
        area = _num(area, f"area of {r.get('id')}", positive=False)
        key = None if t is None else f"{_num(t, 'thickness'):.2f}"
        if key not in rates["value"]:
            out.append(dict(rec, status=HELD, consumption=None,
                            why=f"no OWNER CONFIRMED glue rate for an AAC block of thickness {t} m"))
            continue
        k = float(rates["value"][key])
        out.append(dict(rec, status=OK, net_area_m2=area, thickness_m=float(key), kg_per_m2=k, basis=rates["basis"],
                        source=rates["source"], consumption=round(area * k, 9)))
    return {"rule": _ref(rid), "unit": "kg; bags of %g kg" % bag["value"], "rows": out,
            "groups": _group(out, float(bag["value"]), w, "AAC glue")}


# ---------------------------------------------------------------- single-quantity calculators

def black_blocks(net_area_m2, thickness_m, project=None, waste=None):
    rid = "UPC-BLACK-BLOCK-001"
    w = _waste(waste)
    if net_area_m2 is None:
        return {"rule": _ref(rid), "status": HELD, "why": "net wall area HELD (never 0)"}
    a = _num(net_area_m2, "net area", positive=False)
    mods = param(rid, "confirmed_modules_m", project)
    key = f"{_num(thickness_m, 'thickness'):.2f}"
    mod = mods["value"].get(key)
    if mod is None:
        return {"rule": _ref(rid), "status": HELD, "thickness_m": float(key),
                "why": f"the installed module of the {key} m black block is not stated (block schedule, project "
                       f"evidence or supplier data): HELD, the 12.5 / m2 rate is not borrowed"}
    if abs(mod[0] - 0.40) > EPS or abs(mod[1] - 0.20) > EPS:
        return {"rule": _ref(rid), "status": HELD, "module_m": mod, "module_basis": mods["basis"],
                "why": "the 12.5 / m2 company rate applies only to a confirmed 40 x 20 installed module"}
    rate = param(rid, "blocks_per_m2_40x20_module", project)
    theo = round(a * rate["value"], 9)
    out = {"rule": _ref(rid), "status": OK, "net_area_m2": a, "thickness_m": float(key), "module_m": mod,
           "module_basis": mods["basis"], "module_source": mods["source"], "blocks_per_m2": rate["value"],
           "theoretical_count": theo, "waste": w}
    out["procurement_count"] = _ceil(theo * (1 + w["value"])) if w else None
    return out


def black_block_laying_materials(mortar_m3, project=None):
    rid = "UPC-BLACK-MORTAR-001"
    if mortar_m3 is None:
        return {"rule": _ref(rid), "status": HELD, "why": "mortar volume HELD (never 0)"}
    v = _num(mortar_m3, "mortar m3", positive=False)
    c, s = param(rid, "cement_bags_per_m3", project), param(rid, "loose_sand_m3_per_m3", project)
    return {"rule": _ref(rid), "status": OK, "mix": param(rid, "mix_cement_sand", project)["value"], "mortar_m3": v,
            "cement_bags": round(v * c["value"], 9), "sand_m3_loose": round(v * s["value"], 9),
            "basis": c["basis"], "source": c["source"]}


def tile_bed(area_m2, floor_kind, project=None):
    """floor_kind 'REGULAR' or 'WET'; returns (low, high) bounds, never one invented number."""
    rid = "UPC-TILE-BED-001"
    name = {"REGULAR": "thickness_m_regular_floor", "WET": "thickness_m_wet_floor"}.get(floor_kind)
    if name is None:
        return {"rule": _ref(rid), "status": HELD, "why": f"floor kind {floor_kind!r} has no bed rule"}
    if area_m2 is None:
        return {"rule": _ref(rid), "status": HELD, "why": "area HELD (never 0)"}
    a = _num(area_m2, "area", positive=False)
    t = param(rid, name, project)
    c, s = param(rid, "cement_bags_per_m3", project), param(rid, "loose_sand_m3_per_m3", project)
    lo, hi = (float(x) for x in t["value"])
    m = (round(a * lo, 9), round(a * hi, 9))
    return {"rule": _ref(rid), "status": OK, "floor_kind": floor_kind, "area_m2": a, "thickness_m": (lo, hi),
            "thickness_basis": t["basis"], "mortar_m3": m,
            "cement_bags": tuple(round(x * c["value"], 9) for x in m),
            "sand_m3_loose": tuple(round(x * s["value"], 9) for x in m)}


_LAYERS = {"SPATTER_DASH": "spatter_dash", "LEVELLING_RENDER": "levelling_render", "WALL_PLASTER": "wall_plaster"}


def cement_layer(area_m2, layer, project=None):
    """level 4 method: mortar m3 = area x thickness; HELD unless a thickness is sourced (levels 1, 2 or 4). Cement and
    sand need a sourced mix figure ('<layer>_cement_bags_per_m3' / '<layer>_sand_m3_per_m3' are not company values)."""
    rid = "UPC-CEMENT-LAYERS-METHOD-001"
    p = _LAYERS.get(layer)
    if p is None:
        raise RulebookError(f"unknown layer {layer!r}; known: {', '.join(_LAYERS)}")
    if area_m2 is None:
        return {"rule": _ref(rid), "status": HELD, "why": "area HELD (never 0)"}
    a = _num(area_m2, "area", positive=False)
    t = param(rid, f"{p}_thickness_m", project)
    mix = param(rid, f"{p}_mix", project)
    out = {"rule": _ref(rid), "layer": layer, "area_m2": a, "sensitivity_m3_per_mm": round(a / 1000.0, 9),
           "thickness": t, "mix": mix}
    if t["value"] is None:
        return dict(out, status=HELD, mortar_m3=None,
                    why=f"{layer} thickness not given by the project, the owner or the company rules: HELD with this "
                        f"method named (area lines unaffected)")
    th = _num(t["value"], f"{layer} thickness")
    out.update(status=OK, mortar_m3=round(a * th, 9), label=t["basis"])
    if mix["value"] is None:
        out.update(materials_status=HELD, materials_why=f"{layer} mix not given: cement / sand HELD")
    else:
        out.update(materials_status="NEEDS_PER_M3_FIGURES",
                   materials_why="cement bags / sand per m3 of this mix come from a sourced reference, not from the "
                                 "black-block 1:4 rule")
    return out

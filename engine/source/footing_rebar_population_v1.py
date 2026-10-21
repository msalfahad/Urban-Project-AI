"""FOOTING_REBAR_POPULATION_V1 - footing steel by bar population from the footing schedule (generic, NOT wired).

Board T-136 (first slice of T-009, plan P-08). A NEW opt-in piece: it reads footing schedule rows as printed (mark,
plan size, depth, bottom / top mesh both ways), binds each row by mark to the footings route G releases (route G's
own FOOTINGS concrete items are passed in as data - this module imports no route), and computes per footing and per
direction: bar count, bar length, kg (net) and the procurement figure, each with a status. Nothing is wired into a
released method; the frozen S4 engine (footing_rebar.py) is untouched.

Rules applied (no value without a source):
  * URBAN-REBAR-NET-AND-PROCUREMENT@v1 (rules/methods/URBAN_METHOD_REGISTER_V3.json:111, engine/source/
    urban_methods_v3.py:56): kg = count x length x kg/m per bar set; net uses only bars the source supports, cover
    from the structural notes; procurement adds laps only where a bar exceeds the 12 m stock length; hooks / bends
    only from a detail or note, otherwise BLOCKED; never kg/m3.
  * The rule gives NO count formula for spacing ('T d @ s') or per-metre ('n T d /m') notation. Such a count is
    therefore HELD (owner question Q-71) and reported as the three readings A / B / C, never as one number and never
    0: A = ceil(dist_in / s), B = A + 1 (both edge bars), C = rate x full dimension (fractional; route G's reading).
    dist_in = distribution side - 2 x cover. A count printed as 'n T d' is the printed count (RELEASED).
  * Cover: only a cover record the caller takes from a printed structural note (value, wording MINIMUM / EXACT,
    source). No record -> every length and kg HELD (COVER_NOT_PRINTED). A MINIMUM cover gives the straight run at that
    cover, labelled AT_PRINTED_MINIMUM_COVER (cover_authority D1.2: the run is then a maximum, never a lower bound).
  * End treatment per layer only from a detail the caller cites; a layer with no cited end -> its components HELD
    (END_TREATMENT_NOT_DRAWN); the straight core is shown as a value, not released.
  * Owner Q-17 A: the schedule size is the drawing-verified size; Q-31 C: a footing whose outline and schedule
    disagree, or that carries two marks, stays HELD (never chosen); UP-QTY-STATUS-001: held never becomes 0.
  * Unit mass only from rebar_unit_mass (project method). Sizes in the unit the schedule header prints (mm / cm / m);
    no unit -> the row is HELD (UNIT_NOT_PRINTED).
Stdlib + engine.source accurate modules only; project-agnostic (no layer names, marks or coordinates of any villa).
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.source import rebar_unit_mass as UM
from engine.source import urban_methods_v3 as UM3

POLICY_ID = "FOOTING_REBAR_POPULATION_V1"
RULE_ID = "URBAN-REBAR-NET-AND-PROCUREMENT@v1"
RULE_REF = "rules/methods/URBAN_METHOD_REGISTER_V3.json:111"
COUNT_QUESTION = "Q-71"

RELEASED = "RELEASED"
HELD = "HELD"
NOT_APPLICABLE = "NOT_APPLICABLE"

EXPLICIT, PER_METRE, SPACING = "EXPLICIT_COUNT", "BARS_PER_METRE", "SPACING"
EMPTY, MERGED, UNREADABLE = "EMPTY", "MERGED", "UNREADABLE"

LAYERS = ("BOTTOM", "TOP")
DIRECTIONS = ("SHORT", "LONG")
COMPONENTS = tuple(f"{la}_{d}" for la in LAYERS for d in DIRECTIONS)

_UNIT_MM = {"mm": 1.0, "cm": 10.0, "m": 1000.0}
_MARK = r"(?:%%[cC]|[Øø⌀ΦφɸTtYyDdHh#])"
_RE_COUNT = re.compile(rf"^(\d+)\s*[-xX]?\s*{_MARK}\s*(\d+(?:\.\d+)?)$")
_RE_PER_M = re.compile(rf"^(\d+(?:\.\d+)?)\s*{_MARK}\s*(\d+(?:\.\d+)?)\s*/\s*m$")
_RE_SPACE = re.compile(rf"^{_MARK}\s*(\d+(?:\.\d+)?)\s*@\s*(\d+(?:\.\d+)?)\s*(mm|cm|m)?$")
_RE_NUM = re.compile(r"^\d+(?:\.\d+)?$")
_RE_DIA_PM = re.compile(r"^(\d+(?:\.\d+)?)\s*/\s*m$")
_RE_ROUTE_MARK = re.compile(r"^FTG:[^:]+:([^@:]+)@")


class FootingPopulationError(ValueError):
    pass


def _f(v):
    return float(v) if v is not None else None


# ------------------------------------------------------------------ schedule cell grammar
def parse_cell(text=None, *, count=None, dia=None, spacing_unit=None, merged=False):
    """One schedule cell as printed. Either `text` ('8 T 12', '9T14/m', 'T12@150mm', '%%c12@20cm') or the split
    pair (`count`, `dia`) of a block attribute row ('9', '14/m'). A spacing without a unit takes `spacing_unit` (the
    unit the schedule header prints); with neither the cell is UNREADABLE (never guessed)."""
    raw = text if text is not None else f"{count or ''} | {dia or ''}"
    if merged:
        return {"mode": MERGED, "raw": raw, "reason": "merged schedule cell: its value is not this footing's own"}
    if text is None:
        c, d = (count or "").strip(), (dia or "").strip()
        if not c and not d:
            return {"mode": EMPTY, "raw": raw, "reason": "empty schedule cell"}
        m = _RE_DIA_PM.match(d)
        if _RE_NUM.match(c) and m:
            return {"mode": PER_METRE, "rate_per_m": float(c), "dia_mm": float(m.group(1)), "raw": raw}
        if _RE_NUM.match(c) and _RE_NUM.match(d) and float(c).is_integer():
            return {"mode": EXPLICIT, "count": int(float(c)), "dia_mm": float(d), "raw": raw}
        return {"mode": UNREADABLE, "raw": raw, "reason": "count / diameter pair not in a known notation"}
    t = " ".join(str(text).split())
    if not t:
        return {"mode": EMPTY, "raw": raw, "reason": "empty schedule cell"}
    m = _RE_COUNT.match(t)
    if m:
        return {"mode": EXPLICIT, "count": int(m.group(1)), "dia_mm": float(m.group(2)), "raw": raw}
    m = _RE_PER_M.match(t)
    if m:
        return {"mode": PER_METRE, "rate_per_m": float(m.group(1)), "dia_mm": float(m.group(2)), "raw": raw}
    m = _RE_SPACE.match(t)
    if m:
        unit = m.group(3) or spacing_unit
        if unit not in _UNIT_MM:
            return {"mode": UNREADABLE, "raw": raw, "reason": "spacing printed without a unit and the schedule "
                                                               "header prints none"}
        return {"mode": SPACING, "spacing_mm": float(m.group(2)) * _UNIT_MM[unit], "dia_mm": float(m.group(1)),
                "raw": raw}
    return {"mode": UNREADABLE, "raw": raw, "reason": "text not in a known bar notation"}


def schedule_row(mark, size, unit, cells, *, source="", spacing_unit=None):
    """size = (side_a, side_b, depth) as printed, in `unit` (the schedule header's unit). cells = {component:
    parsed cell | text | (count, dia)} for any of BOTTOM_SHORT .. TOP_LONG. Sides are sorted: L = longer."""
    row = {"mark": str(mark).strip(), "source": source, "cells": {}, "held": None}
    if unit not in _UNIT_MM:
        row["held"] = "UNIT_NOT_PRINTED: the schedule prints no size unit"
        row["L_mm"] = row["W_mm"] = row["D_mm"] = None
    else:
        try:
            a, b, d = (float(x) * _UNIT_MM[unit] for x in size)
        except (TypeError, ValueError):
            a = b = d = None
        if not (a and b):
            row["held"] = "SIZE_NOT_READ: a plan side is missing or unreadable"
            row["L_mm"] = row["W_mm"] = None
            row["D_mm"] = d
        else:
            row["L_mm"], row["W_mm"], row["D_mm"] = max(a, b), min(a, b), d
    for comp, c in (cells or {}).items():
        if comp not in COMPONENTS:
            raise FootingPopulationError(f"{mark}: unknown component {comp}")
        if isinstance(c, dict) and "mode" in c:
            row["cells"][comp] = c
        elif isinstance(c, tuple):
            row["cells"][comp] = parse_cell(count=c[0], dia=c[1], spacing_unit=spacing_unit)
        else:
            row["cells"][comp] = parse_cell(c, spacing_unit=spacing_unit)
    return row


def rows_from_block_attributes(attrs, unit, *, source="", spacing_unit=None):
    """A schedule row drawn as a block with one attribute per cell (single layer: SH-B/SH-D/LO-B/LO-D; two layers:
    SH-B-B .. (bottom) and SH-T-B .. (top)). The plan sides are the two size attributes other than the depth."""
    a = {str(k).upper(): ("" if v is None else str(v)) for k, v in attrs.items()}
    mark = a.get("FO-TY") or a.get("TYPE") or a.get("MARK")
    if not mark:
        raise FootingPopulationError(f"block row without a mark attribute: {sorted(a)}")
    sides = [a.get(k) for k in ("W", "H", "L") if a.get(k)]
    depth = a.get("DEPHT") or a.get("DEPTH") or a.get("D")
    size = (sides + [None, None])[:2] + [depth]
    cells = {}
    if any(k.startswith("SH-T-") or k.startswith("SH-B-") for k in a):
        for la, tag in (("TOP", "T"), ("BOTTOM", "B")):
            for d, s in (("SHORT", "SH"), ("LONG", "LO")):
                cnt, dia = a.get(f"{s}-{tag}-B"), a.get(f"{s}-{tag}-D")
                if cnt is not None or dia is not None:
                    cells[f"{la}_{d}"] = (cnt or "", dia or "")
    else:
        for d, s in (("SHORT", "SH"), ("LONG", "LO")):
            cnt, dia = a.get(f"{s}-B"), a.get(f"{s}-D")
            if cnt is not None or dia is not None:
                cells[f"BOTTOM_{d}"] = (cnt or "", dia or "")
    row = schedule_row(mark, size, unit, cells, source=source, spacing_unit=spacing_unit)
    row["boxed_raw"] = a.get("BOXED")          # None when the row type has no BOXED cell (two-layer rows: TOP / BOT)
    return row


# ------------------------------------------------------------------ route G footings (data only)
def footings_from_route_items(items):
    """The physical footings route G releases, from its FOOTINGS concrete items (dicts). One occurrence per item;
    a footing with two marks, a size conflict, a clipped (non-rectangular) outline or an unresolved item is HELD."""
    out = []
    for it in items:
        if it.get("trade") != "CONCRETE" or it.get("family") != "FOOTINGS":
            continue
        cid = it.get("component_id") or it.get("item_id")
        m = _RE_ROUTE_MARK.match(cid or "")
        dims = it.get("dimensions") or {}
        occ = {"occurrence_id": cid, "mark": m.group(1) if m else None, "drawn_m": dims.get("drawn_m"),
               "schedule_m": dims.get("schedule_m"), "route_m3": it.get("base"), "held": None}
        blk, form = it.get("blocker") or "", it.get("formula") or ""
        if it.get("category") == "UNRESOLVED":
            occ["held"] = f"ROUTE_UNRESOLVED: {blk}"
        elif not m:
            occ["held"] = "TWO_MARKS_ONE_FOOTING: route G found one footing labelled with two types (Q-31 C)"
        elif blk in ("SOURCE_CONFLICT", "SECTION_CONFLICT"):
            occ["held"] = f"SIZE_OR_TYPE_CONFLICT ({blk}; Q-31 C)"
        elif blk in ("OUTLINE_NOT_CONFIRMED", "FOOTING_TAG_MISSING"):
            occ["held"] = f"OCCURRENCE_NOT_CONFIRMED ({blk})"
        elif "clipped" in form:
            occ["held"] = ("OUTLINE_CLIPPED: the drawn outline is not the schedule rectangle (it is cut where it meets "
                           "a neighbour), so where the schedule bars run is not drawn")
        out.append(occ)
    return out


# ------------------------------------------------------------------ one component
def _component(occ, row, comp, cover, end, kgm_of, stock_m):
    la, d = comp.split("_")
    cell = row["cells"].get(comp)
    rec = {"occurrence_id": occ["occurrence_id"], "mark": occ["mark"], "component": comp, "status": None,
           "reasons": [], "raw": cell.get("raw") if cell else None, "dia_mm": None, "count": None,
           "count_range": None, "bar_length_m": None, "net_kg": None, "net_kg_range": None,
           "procurement_kg": None, "readings": None}
    if cell is None:
        rec["status"] = NOT_APPLICABLE
        rec["reasons"].append(f"the schedule row prints no {comp} cell")
        return rec
    if cell["mode"] in (EMPTY, MERGED, UNREADABLE):
        rec["status"] = HELD
        rec["reasons"].append(f"{cell['mode']}: {cell['reason']}")
        return rec
    rec["dia_mm"] = cell["dia_mm"]
    if occ.get("held"):
        rec["reasons"].append(occ["held"])
    if row.get("held"):
        rec["reasons"].append(row["held"])
    if rec["reasons"]:
        rec["status"] = HELD
        return rec
    # SHORT bars run along the short side and are spread along the long side; LONG bars the reverse
    run_mm, dist_mm = (row["W_mm"], row["L_mm"]) if d == "SHORT" else (row["L_mm"], row["W_mm"])
    if not cover:
        rec["status"] = HELD
        rec["reasons"].append("COVER_NOT_PRINTED: no structural note gives the footing cover")
        return rec
    c = float(cover["value_mm"])
    net_mm, dist_in_mm = run_mm - 2 * c, dist_mm - 2 * c
    if net_mm <= 0 or dist_in_mm <= 0:
        rec["status"] = HELD
        rec["reasons"].append("FOOTING_SMALLER_THAN_COVERS")
        return rec
    L = net_mm / 1000.0
    rec["bar_length_m"] = L
    kgm = kgm_of(cell["dia_mm"])
    rec["kg_per_m"] = kgm
    if cell["mode"] == EXPLICIT:
        n_lo = n_hi = cell["count"]
        rec["count"] = n_lo
    else:
        if cell["mode"] == PER_METRE:
            s_mm = 1000.0 / cell["rate_per_m"]
            n_c = cell["rate_per_m"] * dist_mm / 1000.0
        else:
            s_mm = cell["spacing_mm"]
            n_c = dist_mm / s_mm
        n_a = math.ceil(dist_in_mm / s_mm - 1e-9)
        n_b = n_a + 1
        n_lo, n_hi = n_a, n_b
        rec["count_range"] = (n_a, n_b)
        rec["readings"] = {"A_ceil_inside_cover": {"count": n_a, "kg": n_a * L * kgm},
                           "B_A_plus_edge_bar": {"count": n_b, "kg": n_b * L * kgm},
                           "C_rate_x_full_side": {"count": n_c, "kg": n_c * L * kgm}}
        rec["reasons"].append(f"COUNT_RULE_NOT_SET: {RULE_ID} ({RULE_REF}) gives no count formula for "
                              f"{cell['mode']} notation (owner {COUNT_QUESTION})")
    kg_lo, kg_hi = n_lo * L * kgm, n_hi * L * kgm
    if not (end and end.get("state") == "STRAIGHT"):
        rec["reasons"].append(f"END_TREATMENT_NOT_DRAWN: no detail cited for the {la.lower()} bar ends; straight "
                              f"core only")
    rec["net_kg_range"] = (kg_lo, kg_hi)
    rec["cover_basis"] = f"{cover.get('wording', 'UNSTATED')} {c:g} mm ({cover.get('source', '')})"
    if L > stock_m:
        rec["reasons"].append(f"PROCUREMENT_LAP_NOT_PRINTED: bar {L:.3f} m > {stock_m:g} m stock length")
        rec["procurement_note"] = "HELD"
    else:
        rec["procurement_note"] = f"= net (bar {L:.3f} m <= {stock_m:g} m stock: no splice, {RULE_ID})"
    if rec["reasons"]:
        rec["status"] = HELD
    else:
        rec["status"] = RELEASED
        rec["net_kg"] = kg_lo
        rec["procurement_kg"] = kg_lo
    rec["formula"] = (f"n x (side {run_mm:g} - 2 x {c:g} mm) x kg/m = "
                      f"{rec['count'] if rec['count'] is not None else rec['count_range']} x {L:.4f} m x "
                      f"{kgm:.6f} kg/m")
    return rec


# ------------------------------------------------------------------ run
def run(footings, rows, *, cover, end_treatment, unit_mass, project_rule_override=None):
    """footings: footings_from_route_items(...) or the same shape; rows: schedule_row(...) records; cover: {value_mm,
    wording, source} from a printed note or None; end_treatment: {"BOTTOM": {"state": "STRAIGHT", "source": ...} |
    None, "TOP": ... | None}; unit_mass: rebar_unit_mass config."""
    UM.validate(unit_mass)
    rule = UM3.resolve(RULE_ID, project_rule_override)
    stock_m = float(rule["parameters"]["stock_length_m"])
    kgm_of = lambda dia: UM.kg_per_m(dia, unit_mass)  # noqa: E731
    by_mark = defaultdict(list)
    for r in rows:
        by_mark[r["mark"]].append(r)
    dup = sorted(k for k, v in by_mark.items() if len(v) > 1)
    comps, occ_rows = [], []
    for occ in sorted(footings, key=lambda o: str(o["occurrence_id"])):
        cand = by_mark.get(occ["mark"]) if occ["mark"] else None
        o = dict(occ)
        if occ["mark"] and not cand:
            o["held"] = o.get("held") or f"NO_SCHEDULE_ROW: mark {occ['mark']} is not in the footing schedule"
        if occ["mark"] in dup:
            o["held"] = o.get("held") or f"SCHEDULE_ROW_TWICE: mark {occ['mark']} has two schedule rows"
        row = cand[0] if cand else {"mark": occ["mark"], "cells": {}, "held": None, "L_mm": None, "W_mm": None}
        if not cand or o.get("held") and not row["cells"]:
            cs = [{"occurrence_id": o["occurrence_id"], "mark": o["mark"], "component": "ALL", "status": HELD,
                   "reasons": [o["held"]], "net_kg": None, "net_kg_range": None, "readings": None}]
        else:
            cs = [_component(o, row, comp, cover, (end_treatment or {}).get(comp.split("_")[0]), kgm_of, stock_m)
                  for comp in COMPONENTS]
        comps.extend(cs)
        rel = sum(c["net_kg"] for c in cs if c["status"] == RELEASED)
        lo = sum(c["net_kg_range"][0] for c in cs if c["status"] == HELD and c.get("net_kg_range"))
        hi = sum(c["net_kg_range"][1] for c in cs if c["status"] == HELD and c.get("net_kg_range"))
        unq = [c["component"] for c in cs if c["status"] == HELD and not c.get("net_kg_range")]
        if row.get("boxed_raw") is not None and o["mark"]:
            # a BOXED cell is printed for this row type: its bars are not given as count x diameter, so they are
            # held unquantified (an empty cell is not proof that no boxed bars exist)
            unq.append(f"BOXED(printed {row['boxed_raw']!r})")
        occ_rows.append({"occurrence_id": o["occurrence_id"], "mark": o["mark"], "held": o.get("held"),
                         "released_kg": rel, "held_kg_range": (lo, hi) if (lo or hi) else None,
                         "held_unquantified": unq,
                         "boxed_raw": row.get("boxed_raw"),
                         "status": RELEASED if not any(c["status"] == HELD for c in cs) else HELD})
    bound = {o["mark"] for o in footings if o.get("mark")}
    unplaced = sorted(m for m in by_mark if m not in bound)
    totals = {"released_kg": sum(r["released_kg"] for r in occ_rows),
              "held_kg_low": sum(r["held_kg_range"][0] for r in occ_rows if r["held_kg_range"]),
              "held_kg_high": sum(r["held_kg_range"][1] for r in occ_rows if r["held_kg_range"]),
              "held_unquantified_components": sum(len(r["held_unquantified"]) for r in occ_rows),
              "occurrences": len(occ_rows),
              "occurrences_released": sum(1 for r in occ_rows if r["status"] == RELEASED)}
    readings = defaultdict(float)
    for c in comps:
        for k, v in (c.get("readings") or {}).items():
            if c["status"] == HELD and not [x for x in c["reasons"] if not x.startswith(("COUNT_RULE", "END_TREAT"))]:
                readings[k] += v["kg"]
    return {"policy": POLICY_ID, "rule": RULE_ID, "rule_ref": RULE_REF, "stock_length_m": stock_m,
            "rule_authority": rule["authority"], "cover": cover, "end_treatment": end_treatment,
            "components": comps, "occurrences": occ_rows, "totals": totals,
            "count_readings_kg": dict(readings), "schedule_rows_without_footing": unplaced,
            "check": conservation(comps, occ_rows, totals)}


def conservation(comps, occ_rows, totals, tol=1e-6):
    rel_c = sum(c["net_kg"] for c in comps if c["status"] == RELEASED)
    held_zero = all(c["net_kg"] is None for c in comps if c["status"] != RELEASED)
    rel_has = all(c["net_kg"] is not None and c["net_kg"] > 0 for c in comps if c["status"] == RELEASED)
    once = all(sum(1 for c in comps if c["occurrence_id"] == r["occurrence_id"] and c["component"] == k) <= 1
               for r in occ_rows for k in COMPONENTS)
    checks = {"components_add_to_released_total": abs(rel_c - totals["released_kg"]) <= tol,
              "held_components_carry_no_released_kg": held_zero,
              "released_components_carry_kg": rel_has,
              "each_component_once_per_footing": once}
    return {"checks": checks, "all_pass": all(checks.values())}


def policy_record():
    return {"policy_id": POLICY_ID, "rule": RULE_ID, "rule_ref": RULE_REF, "count_question": COUNT_QUESTION,
            "components": list(COMPONENTS),
            "rules": ["printed count 'n T d' -> that count (RELEASED when cover and ends are sourced)",
                      "per-metre / spacing notation -> HELD with readings A / B / C until the owner sets the count",
                      "cover only from a printed note; length = side - 2 x cover",
                      "ends only from a cited detail; held never becomes 0; not wired"]}

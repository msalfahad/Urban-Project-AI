"""REPORTING V3 - unit control: engine units -> final BOQ display units (reporting only, no quantity change).

The engine keeps its calculation units (kg for reinforcement, ASCII m3 / m2 / nr). The final BOQ, the workbooks and the
PDF use the QS convention of the manual workbooks: concrete m³, reinforcement t, areas m², lengths lm, counts No.
A conversion is a pure factor applied at display time; nothing is rounded before display (3 decimals for tonnes).

    display(model)            -> a copy of the reporting model in display units, with the engine value kept beside it
    unit_register(model)      -> UNIT_REGISTER rows (ITEM, ENGINE_UNIT, DISPLAY_UNIT, CONVERSION, STATUS)
    unit_control(model, ...)  -> the UNIT_CONTROL gate (fails on kg rebar, non-m³ concrete, cross-unit or cross-basis sums,
                                 or a benchmark comparison made before unit normalisation)
"""

from __future__ import annotations

import copy
import re
from collections import defaultdict

POLICY_ID = "URBAN_BOQ_UNIT_CONTROL_V1"
IN_TOTAL = ("COMPUTED", "PARTIAL")

# engine unit -> (display unit, factor, decimals, role)
UNIT_POLICY = {
    "m3": ("m³", 1.0, 3, "volume"),
    "m2": ("m²", 1.0, 2, "area"),
    "lm": ("lm", 1.0, 2, "length"),
    "nr": ("No.", 1.0, 0, "count"),
    "kg": ("t", 0.001, 3, "weight"),
    "m": ("m", 1.0, 3, "dimension"),          # a printed dimension (stair going), never a BOQ quantity or a total
}
DISPLAY_UNITS = {v[0] for v in UNIT_POLICY.values()}
TRADE_UNITS = {                               # the official final-BOQ unit set per trade
    "CONCRETE": {"m³"},
    "REBAR": {"t"},
    "BLOCKWORK": {"m²"},
    "PLASTER_PAINT": {"m²", "lm"},             # lm only for the extras (beads) - separate rows
    "FLOORING_PORCELAIN": {"m²", "lm"},        # skirting lm
    "CEILINGS": {"m²", "lm"},                  # cornice lm
    "WALL_TILE_WATERPROOFING": {"m²", "lm"},   # upturn path lm if published separately
    "ALUMINIUM_OPENINGS": {"m²", "lm", "No."},  # curved glazing developed length lm, counts No.
    "STAIRS_RAILINGS": {"m²", "lm", "m"},      # marble m², nosing / railing lm, going = dimension
}
# the official convention table of the addendum (also listed where nothing is published yet)
CONVENTION = [
    ("CONCRETE / RC / BLINDING", "m³"), ("REINFORCEMENT / REBAR", "t"), ("BLOCKWORK", "m²"), ("PLASTER", "m²"),
    ("PAINT", "m²"), ("FLOOR PORCELAIN / CERAMIC", "m²"), ("CEILINGS", "m²"), ("WALL TILE", "m²"),
    ("WATERPROOFING MEMBRANE", "m²"), ("WATERPROOFING UPTURN PATH", "lm"), ("ALUMINIUM / GLASS AREA", "m²"),
    ("CURVED GLAZING LENGTH ONLY", "lm"), ("DOORS / WINDOWS COUNTS", "No."), ("MARBLE TREAD / RISER / LANDING", "m²"),
    ("NOSING", "lm"), ("SKIRTING", "lm"), ("HANDRAIL / RAILING", "lm"),
]
REBAR_BASIS = {
    "Procurement weight incl. laps (complete sets)": "OFFICIAL BASIS - procurement incl. laps, complete bar sets",
    "Net design weight (complete sets)": "ALTERNATIVE BASIS - net design weight; reference only, never added",
    "Straight weight - sets with hooks not detailed": "PARTIAL SETS - straight bar awaiting hook / bend detail; separate "
                                                      "subtotal, never added",
    "Bar sets / members not computable": "NOT COMPUTABLE - no quantity",
}
REBAR_TOTAL_ITEM = "TOTAL PROJECT REBAR"


def line_basis(ln) -> str:
    """The measurement basis a line belongs to (rebar: NET / PROC / STRAIGHT / BLK from the code; else the summary item)."""
    if ln["trade"] == "REBAR":
        m = re.search(r"-(NET|PROC|STRAIGHT|BLK)$", ln["code"])
        return m.group(1) if m else ("BLK" if ln["status"] == "BLOCKED" else "UNKNOWN")
    return ln.get("sumrow") or "-"


def _conv(v, f):
    return None if v is None else v * f


def _conv_text(eu, du, f):
    return "x 1 (label only)" if f == 1.0 and eu != du else ("none" if f == 1.0 else f"/ {round(1 / f):,} ({eu} -> {du})")


def display(model) -> dict:
    """Copy of the reporting model in display units. Engine values stay beside the display values (engine_qty /
    engine_unit); quantities are multiplied by the policy factor only - no rounding."""
    m = copy.deepcopy(model)
    for ln in m["lines"]:
        du, f, _, role = UNIT_POLICY[ln["unit"]]
        ln["engine_unit"], ln["engine_qty"] = ln["unit"], ln["qty"]
        ln["unit"], ln["qty"], ln["unit_role"] = du, _conv(ln["qty"], f), role
        ln["basis"] = line_basis(ln)
        if f != 1.0 and ln["engine_qty"] is not None:
            ln["formula"] = f"{ln['formula']}  [engine {ln['engine_qty']:,.3f} {ln['engine_unit']} / {round(1 / f):,} = " \
                            f"{ln['qty']:,.4f} {du}]"
    rows = []
    for r in m["master"]["rows"]:
        du, f, _, _ = UNIT_POLICY[r["unit"]]
        r["engine_unit"], r["engine_total"] = r["unit"], r["total"]
        r["unit"] = du
        for lv in m["levels"]:
            r[lv] = _conv(r[lv], f)
        r["total"] = _conv(r["total"], f)
        r["basis"] = REBAR_BASIS.get(r["item"], "-") if r["trade"] == "REBAR" else "as measured"
        rows.append(r)
    # one explicit, non-numeric project-rebar row: the bases are alternatives / states and are never summed
    reb = {r["item"]: r for r in rows if r["trade"] == "REBAR"}
    if reb:
        proc = reb.get("Procurement weight incl. laps (complete sets)")
        part = reb.get("Straight weight - sets with hooks not detailed")
        note = (f"PARTIAL: official basis = procurement, complete sets {proc['total']:,.3f} t (computed subtotal)"
                if proc else "PARTIAL")
        if part:
            note += f"; partial sets {part['total']:,.3f} t straight bar awaiting hook / bend detail (separate subtotal)"
        note += "; net / procurement / partial are never summed"
        last = max(i for i, r in enumerate(rows) if r["trade"] == "REBAR")
        rows.insert(last + 1, {"trade": "REBAR", "item": REBAR_TOTAL_ITEM, "item_ar": "إجمالي حديد التسليح", "unit": "t",
                               **{lv: None for lv in m["levels"]}, "total": None, "statuses": ["PARTIAL"],
                               "status": "PARTIAL", "no_total": True, "basis": note, "engine_unit": "kg",
                               "engine_total": None})
    m["master"]["rows"] = rows
    m["master"]["rule"] = (m["master"]["rule"] + "; units: concrete m³, reinforcement t (engine kg / 1000), areas m², "
                           "lengths lm, counts No.; rebar bases are shown separately and never summed")
    m["unit_policy"] = POLICY_ID
    return m


def unit_register(dmodel) -> dict:
    rows = []
    for r in dmodel["master"]["rows"]:
        eu = r["engine_unit"]
        du, f, dec, role = UNIT_POLICY[eu]
        rows.append({"ITEM": f"{r['trade']} / {r['item']}", "ENGINE_UNIT": eu, "DISPLAY_UNIT": du,
                     "CONVERSION": _conv_text(eu, du, f), "FACTOR": f, "DISPLAY_DECIMALS": dec,
                     "BASIS": r.get("basis", "-"),
                     "STATUS": "NOT_SUMMED (bases differ)" if r.get("no_total") else "CONVERTED_FOR_DISPLAY"})
    seen = {(x["ITEM"].split(" / ")[0], x["DISPLAY_UNIT"]) for x in rows}
    for t, units in TRADE_UNITS.items():
        for lu in sorted({x["unit"] for x in dmodel["lines"] if x["trade"] == t} - {du for (tt, du) in seen if tt == t}):
            rows.append({"ITEM": f"{t} / (line-level only)", "ENGINE_UNIT": next(k for k, v in UNIT_POLICY.items()
                                                                                if v[0] == lu),
                         "DISPLAY_UNIT": lu, "CONVERSION": "none", "FACTOR": 1.0, "DISPLAY_DECIMALS": 3, "BASIS": "-",
                         "STATUS": "DIMENSION_ONLY (never a BOQ total)" if lu == "m" else "LINE_LEVEL_ONLY"})
    conv = []
    published = {x["DISPLAY_UNIT"] for x in rows}
    for item, du in CONVENTION:
        conv.append({"ITEM": item, "OFFICIAL_UNIT": du,
                     "STATUS": "IN USE" if du in published else "NOT PUBLISHED YET"})
    upt = next(c for c in conv if c["ITEM"] == "WATERPROOFING UPTURN PATH")
    upt["STATUS"] = ("NOT PUBLISHED SEPARATELY - the upturn is inside the membrane m² (floor + path x upturn height); a "
                     "separate lm row needs the engine to publish the path length as its own line")
    return {"SCHEMA": "URBAN_BOQ_UNIT_REGISTER_V1", "policy": POLICY_ID,
            "engine_to_display": [{"ENGINE_UNIT": k, "DISPLAY_UNIT": v[0], "FACTOR": v[1], "DISPLAY_DECIMALS": v[2],
                                   "ROLE": v[3]} for k, v in UNIT_POLICY.items()],
            "convention": conv, "rows": rows,
            "rule": "reporting unit change only: display = engine x factor, no rounding before display; engine registers "
                    "keep kg / m3 / m2 / nr; unlike units and unlike bases are never added"}


def unit_scoped_formulas(cell_maps) -> list:
    """Every SUMIFS subtotal must carry the unit criterion (column F); returns the offending formulas."""
    bad = []
    for cm in cell_maps:
        for c in cm:
            f = c.get("formula") or ""
            if c["kind"] == "formula" and "SUMIFS(" in f and ",$F$" not in f:
                bad.append(f"{c['sheet']}!{c['cell']}")
    return bad


def unit_control(dmodel, evaluation=None, cell_maps=()) -> dict:
    lines, rows = dmodel["lines"], dmodel["master"]["rows"]
    problems = defaultdict(list)
    for ln in lines:
        if ln["unit"] not in DISPLAY_UNITS:
            problems["units_in_policy"].append(ln["line_id"])
        if ln["unit"] not in TRADE_UNITS.get(ln["trade"], DISPLAY_UNITS):
            problems["trade_units_official"].append(f"{ln['line_id']} {ln['unit']}")
        if ln["trade"] == "REBAR" and ln["unit"] != "t":
            problems["rebar_in_tonnes"].append(ln["line_id"])
        if ln["trade"] == "CONCRETE" and ln["unit"] != "m³":
            problems["concrete_in_m3"].append(ln["line_id"])
        if ln["unit"] == "m" and ln.get("sumrow"):
            problems["dimension_never_totalled"].append(ln["line_id"])
    want, bases, units_of = defaultdict(float), defaultdict(set), defaultdict(set)
    for ln in lines:
        if ln.get("sumrow"):
            units_of[(ln["trade"], ln["sumrow"])].add(ln["unit"])
            if ln["status"] in IN_TOTAL and ln["qty"] is not None:
                want[(ln["trade"], ln["sumrow"], ln["unit"])] += ln["qty"]
                bases[(ln["trade"], ln["sumrow"], ln["unit"])].add(ln.get("basis") or line_basis(ln))
    keys = set()
    for r in rows:
        k = (r["trade"], r["item"], r["unit"])
        if k in keys:
            problems["one_row_per_item_and_unit"].append(str(k))
        keys.add(k)
        if r["trade"] == "REBAR" and r["unit"] != "t":
            problems["rebar_in_tonnes"].append(f"master {r['item']} {r['unit']}")
        if r["trade"] == "CONCRETE" and r["unit"] != "m³":
            problems["concrete_in_m3"].append(f"master {r['item']} {r['unit']}")
        if r.get("no_total"):
            if r["total"] is not None or any(r[lv] is not None for lv in dmodel["levels"]):
                problems["bases_never_summed"].append(f"master {r['item']} carries a number")
            continue
        exp = want.get(k, 0.0)
        if abs((r["total"] or 0.0) - exp) > 1e-6 * max(1.0, abs(exp)):
            problems["no_cross_unit_sum"].append(f"{k}: row {r['total']} != same-unit lines {exp}")
        if len(bases.get(k, ())) > 1:
            problems["single_basis_per_row"].append(f"{k}: {sorted(bases[k])}")
    for ln in lines:                                  # a count / area / length never feeds a row of another unit
        if ln.get("sumrow") and ln["status"] in IN_TOTAL and ln["qty"] is not None:
            if (ln["trade"], ln["sumrow"], ln["unit"]) not in keys:
                problems["no_cross_unit_sum"].append(f"{ln['line_id']} has no same-unit summary row")
    reb = [r for r in rows if r["trade"] == "REBAR"]
    if reb and not any(r["item"] == REBAR_TOTAL_ITEM and r.get("no_total") and r["status"] == "PARTIAL" for r in reb):
        problems["rebar_total_partial_not_summed"].append("missing")
    if reb and sum(1 for r in reb if (r.get("basis") or "").startswith("OFFICIAL")) != 1:
        problems["rebar_one_official_basis"].append("exactly one official basis row required")
    bad = unit_scoped_formulas(cell_maps)
    if bad:
        problems["subtotal_formulas_unit_scoped"] += bad[:10]
    if evaluation is not None:
        for e in evaluation.get("rows", []):
            if e.get("difference_pct") is not None and not (e.get("units_normalised") and e.get("benchmark_unit_normalised")
                                                            == e.get("v3_display_unit")):
                problems["compare_after_normalisation"].append(e.get("benchmark"))
    names = ["units_in_policy", "trade_units_official", "rebar_in_tonnes", "concrete_in_m3", "dimension_never_totalled",
             "one_row_per_item_and_unit", "no_cross_unit_sum", "single_basis_per_row", "bases_never_summed",
             "rebar_total_partial_not_summed", "rebar_one_official_basis", "subtotal_formulas_unit_scoped",
             "compare_after_normalisation"]
    checks = {n: not problems.get(n) for n in names}
    return {"policy": POLICY_ID, "state": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "problems": {k: v[:10] for k, v in problems.items() if v}}


# --------------------------------------------------------------- benchmark unit normalisation (evaluation only)
BENCH_UNIT = {"م2": "m²", "m2": "m²", "م.ط": "lm", "lm": "lm", "m3": "m³", "م3": "m³", "t": "t", "طن": "t", "عدد": "No.",
              "nr": "No."}

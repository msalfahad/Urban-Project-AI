"""PLASTER MATERIALS TABLE V3 (task T-504, from F-T499-1; opt-in, UNWIRED_PRODUCER: read by no released method and by
no candidate V3.0.x; no released or candidate quantity changes; V1 and V2 are untouched and still the row producers).

Physical element: unchanged from V1 / V2: the wet placed mortar of each coat of one face (area x thickness), then its
cement bags / sand m3 by the coat's mix. V3 changes no ROW: V1 rows (area / thickness stage) and V2 rows (mix stage)
are carried byte-identical. V3 changes only how a SUBTOTAL over the rows of one coat is printed when some of those rows
carry no number.

Defect fixed (F-T499-1, reproduced on the merged T-454 ledger, plaster lines unchanged V3.0.45 .. V3.0.50):

    V1 _sums     'mortar_m3' of a coat sums the rows that have one and prints it under the plain key, the held rows only
                 listed beside (WALL_PLASTER 4.726962 m3 over 25 of 52 rows, 27 HELD): a known part read as the total.
                 'area_m2' and 'mortar_m3_at_least' the same (BOND_COAT 576.6519 m2 over 37 of 70 rows).
    V2 _sums     cement / sand totals are already None over a held row, but with no known part and no status; the
                 1:3 / 1:4 / 1:5 sensitivity is summed over the rows that have one (45.27 bags over 25 of 52) with no
                 HELD marker, so the dry estimate inherits the partial sum.

Rule R-T504-1 (R-T499-1 applied to plaster; project-independent; AGENT_BRIEF 'HELD is never 0', UP-QTY-STATUS-001):
    per coat and per key (area_m2, mortar_m3, cement_bags, sand_m3, each sensitivity ratio) the subtotal record is
        {value, status, at_least, exact_part, bound_part, bound_rows, held_rows, rows}
    COMPUTED  every row of the coat carries an exact figure: value = the V1 / V2 sum, unchanged.
    HELD      any row carries no exact figure: value None; at_least = exact part + the AT_LEAST bounds of the rows that
              carry one (a printed-minimum thickness, V1), None when no row carries either (never 0.0); bound_rows and
              held_rows (no figure, no bound) listed; bound_complete True only when no row is in held_rows.
    NO_ROWS   the coat has no row: value None.
    A face whose class (dry / wet) is not established has no figure for any coat (its area is beside, not in a coat).
    The coat's s5_status is the weakest of its rows' (V2) and HELD whenever any subtotal of the coat is HELD.
Mix stage: V2 already multiplies only determinate parts per row and keeps a row HELD where its mix or thickness is; V3
sums those rows by R-T504-1 and never multiplies a subtotal.

Never: a held value as 0, a known part printed as the total, a bound added to an exact figure under the plain key.
Project-agnostic: no project, room name or count. Function names avoid the B4-05 / B9-04 family name terms (T-130).
"""

from __future__ import annotations

import copy

from engine.source import plaster_materials_table_v1 as V1
from engine.source import plaster_materials_table_v2 as V2

METHOD_ID = "PLASTER_MATERIALS_TABLE_V3"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"
SUPERSEDES = None             # V1 / V2 keep producing the rows; V3 replaces only their coat subtotals
RULES = V2.RULES + ("R-T504-1@1.0.0 (R-T499-1 on plaster coats: a subtotal over any row with no exact figure is HELD; "
                    "the known part AT_LEAST with the bound and held rows listed; a fully determinate subtotal "
                    "unchanged)",)
CHANGE = {
    "v1_ref": "engine/source/plaster_materials_table_v1.py:192 _sums (partial area / mortar sums under the plain key)",
    "v2_ref": "engine/source/plaster_materials_table_v2.py:204 _sums (no known part; sensitivity summed over the rows "
              "that have one, no HELD marker)",
    "v3": "R-T504-1: per coat and key a subtotal record; rows of V1 / V2 unchanged",
}

HELD, AT_LEAST, OK = V1.HELD, V1.AT_LEAST, V1.OK
NO_ROWS = "NO_ROWS"
COATS = ("BOND_COAT", "WALL_PLASTER", "LEVELLING_RENDER")
# key -> (exact field on a row, bound field on a row or None)
KEYS = {"area_m2": ("area_m2", None), "mortar_m3": ("mortar_m3", "mortar_m3_at_least"),
        "cement_bags": ("cement_bags", "cement_bags_at_least"), "sand_m3": ("sand_m3", "sand_m3_at_least")}
_V1_KEYS = ("area_m2", "mortar_m3")


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def subtotal(items):
    """items: [(row id, exact figure or None, AT_LEAST bound or None)] -> the R-T504-1 subtotal record."""
    items = list(items)
    if not items:
        return {"value": None, "status": NO_ROWS, "at_least": None, "exact_part": None, "bound_part": None,
                "bound_rows": [], "held_rows": [], "bound_complete": False, "rows": 0}
    exact = [v for _, v, _ in items if v is not None]
    bound_rows = [i for i, v, b in items if v is None and b is not None]
    bounds = [b for _, v, b in items if v is None and b is not None]
    held_rows = [i for i, v, b in items if v is None and b is None]
    if not bound_rows and not held_rows:
        return {"value": _r(sum(exact)), "status": OK, "at_least": None, "exact_part": _r(sum(exact)),
                "bound_part": None, "bound_rows": [], "held_rows": [], "bound_complete": True, "rows": len(items)}
    ex = _r(sum(exact)) if exact else None
    bd = _r(sum(bounds)) if bounds else None
    known = exact + bounds
    return {"value": None, "status": HELD, "at_least": _r(sum(known)) if known else None, "exact_part": ex,
            "bound_part": bd, "bound_rows": bound_rows, "held_rows": held_rows,
            "bound_complete": not held_rows, "rows": len(items)}


def _row_value(x, field):
    """a coat record's figure for one field; a class-held face carries none for any coat (its area is beside)."""
    if x.get("class_held"):
        return None
    return x.get(field)


def _coat_sums(recs):
    out = {"rows": len(recs), "row_ids": [i for i, _ in recs]}
    for key, (f, b) in KEYS.items():
        out[key] = subtotal((i, _row_value(x, f), None if b is None else _row_value(x, b)) for i, x in recs)
    sens = {}
    for n in V2.SENSITIVITY_SAND_PARTS:
        k = f"1:{n}"
        per = {}
        for part in ("cement_bags", "sand_m3"):
            items = []
            for i, x in recs:
                s = x.get("sensitivity_not_a_quantity")
                v = None if s is None or x.get("class_held") else s[k][part]
                bound = str(x.get("sensitivity_basis") or "").startswith("AT_LEAST")
                items.append((i, None if bound else v, v if bound else None))
            per[part] = subtotal(items)
        sens[k] = per
    out["sensitivity_not_a_quantity"] = sens
    if all("s5_status" in x for _, x in recs):
        st = max((x["s5_status"] for _, x in recs), key=lambda s: V2._RANK[s])
        held_any = any(out[k]["status"] == HELD for k in KEYS)
        out["s5_status"] = V2.S5_HELD if held_any else st
    return out


def sums(rows):
    """per coat: the R-T504-1 subtotal records over V1 or V2 rows (a coat with no row is not listed)."""
    out = {}
    for ly in COATS:
        recs = [(r["id"], x) for r in rows for x in r["layers"] if x["layer"] == ly]
        if recs:
            out[ly] = _coat_sums(recs)
    return out


def status_changes(v1_sums, v2_sums, v3_sums):
    """every V1 / V2 coat subtotal printed as a figure (or as an unmarked partial) that V3 prints HELD:
    [{coat, key, was (table, printed value), now status, at_least, rows, held_rows, bound_rows}]."""
    out = []
    for ly, s3 in v3_sums.items():
        s1, s2 = (v1_sums or {}).get(ly, {}), (v2_sums or {}).get(ly, {})
        for key in _V1_KEYS:
            if s3[key]["status"] == HELD and s1.get(key) is not None:
                out.append({"coat": ly, "key": key, "was": ("V1", s1[key]), "now": HELD,
                            "at_least": s3[key]["at_least"], "rows": s3[key]["rows"],
                            "held_rows": len(s3[key]["held_rows"]), "bound_rows": len(s3[key]["bound_rows"])})
        if s3["mortar_m3"]["status"] == HELD and s1.get("mortar_m3_at_least") is not None:
            out.append({"coat": ly, "key": "mortar_m3_at_least", "was": ("V1", s1["mortar_m3_at_least"]),
                        "now": HELD, "at_least": s3["mortar_m3"]["at_least"], "rows": s3["mortar_m3"]["rows"],
                        "held_rows": len(s3["mortar_m3"]["held_rows"]),
                        "bound_rows": len(s3["mortar_m3"]["bound_rows"])})
        for k, sens in (s2.get("sensitivity_not_a_quantity") or {}).items():
            for part in ("cement_bags", "sand_m3"):
                rec = s3["sensitivity_not_a_quantity"][k][part]
                if rec["status"] == HELD and sens.get(part) is not None:
                    out.append({"coat": ly, "key": f"sensitivity {k} {part}", "was": ("V2", sens[part]),
                                "now": HELD, "at_least": rec["at_least"], "rows": rec["rows"],
                                "held_rows": len(rec["held_rows"]), "bound_rows": len(rec["bound_rows"])})
    return out


def apply(v2_table):
    """V2 table -> V3 table: V2 rows unchanged, sums by R-T504-1, and the list of subtotals whose status changes."""
    rows = copy.deepcopy(v2_table["rows"])
    v1_sums = V1._sums(rows)
    s3 = sums(rows)
    return {"method": METHOD_ID, "reads": v2_table.get("method"), "rules": list(RULES),
            "conversion": copy.deepcopy(v2_table.get("conversion")), "mix_given": copy.deepcopy(v2_table.get("mix_given")),
            "rows": rows, "sums": s3, "v1_sums": v1_sums, "v2_sums": copy.deepcopy(v2_table.get("sums")),
            "status_changes": status_changes(v1_sums, v2_table.get("sums"), s3)}


def table(elements, project=None, reference=V1.REFERENCE, mix=None, conversion=V2.CONVERSION):
    """elements (V1 form) -> V1 area / thickness stage -> V2 mix stage -> V3 subtotals."""
    return apply(V2.table(elements, project=project, reference=reference, mix=mix, conversion=conversion))


__all__ = ["METHOD_ID", "SUPERSEDES", "RULES", "subtotal", "sums", "status_changes", "apply", "table"]

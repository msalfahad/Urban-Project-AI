"""GENERIC BOQ RECONCILIATION (M7) - a frozen engine run against a reference bill of quantities, by family and
storey, after the run was frozen (generic, stdlib only; no project vocabulary, no reference value enters the engine).

    read_reference(text)                      GENERIC_BOQ_CSV_V1 -> rows {family, storey, quantity, unit, ref, text}
    engine_side(items)                        {(family, storey): {base, exposure_low, exposure_high, n, n_unresolved}}
    reconcile(items, ref_rows, *, rate=None)  -> {"rows", "totals", "unmapped"}

GENERIC_BOQ_CSV_V1: a CSV with the columns FAMILY, STOREY, QUANTITY, UNIT (m3) and optionally ITEM_REF,
DESCRIPTION. FAMILY is a structural family in words (a few common English synonyms are mapped below; anything else
is UNMAPPED and reported, never guessed). STOREY is a storey token (FOUNDATION, GROUND, GF, 1F, ...) or blank / ALL
(then the family is compared over all storeys).

Per (family, storey), with the engine's measured base B (PROVISIONAL + VERIFIED) and its unresolved exposure
[Elo, Eh] (never added to B by the engine; here it only bounds the explanation), the reference R and a tolerance
t = max(2 % of R, 0.05 m3):
    MATCH                    |R - B| <= t
    EXPLAINED_BY_UNRESOLVED  B < R <= B + Eh + t (the difference is inside what the engine reported unresolved)
    ENGINE_SHORT             R > B + Eh + t (missing scope, a missed element or a different convention)
    ENGINE_OVER              R < B - t (an over-count, a double count, or the reference is short)
    ENGINE_ONLY / REFERENCE_ONLY   one side has nothing
A state is a lead for investigation on the drawing, never a correction: no engine value is changed by this module.
rate (a unit rate per m3, a reporting input only) turns each difference into money; it is never used by the engine.
"""

from __future__ import annotations

import csv
import io
from collections import defaultdict

POLICY_ID = "GENERIC_BOQ_RECONCILE_M7"
FORMAT = "GENERIC_BOQ_CSV_V1"
FAMILY_WORDS = {
    "FOOTINGS": ("FOOTING", "FOOTINGS", "ISOLATED FOOTING", "PAD FOOTING", "FOUNDATION", "FOUNDATIONS"),
    "GROUND_BEAMS": ("GROUND BEAM", "GROUND BEAMS", "TIE BEAM", "TIE BEAMS", "PLINTH BEAM", "GRADE BEAM"),
    "STRAP_BEAMS": ("STRAP BEAM", "STRAP BEAMS", "STRAP"),
    "COLUMNS": ("COLUMN", "COLUMNS"),
    "COLUMN_NECKS": ("NECK", "NECKS", "COLUMN NECK", "COLUMN NECKS", "STUB COLUMN", "STUB COLUMNS"),
    "BEAMS": ("BEAM", "BEAMS", "SUSPENDED BEAM", "SUSPENDED BEAMS", "DROP BEAM", "DROP BEAMS"),
    "SLABS": ("SLAB", "SLABS", "SUSPENDED SLAB", "SUSPENDED SLABS", "ROOF SLAB", "FLOOR SLAB"),
    "GROUND_SLAB": ("GROUND SLAB", "SLAB ON GRADE", "GROUND FLOOR SLAB ON GRADE"),
    "PLAIN_CONCRETE": ("BLINDING", "PLAIN CONCRETE", "LEAN CONCRETE", "PCC"),
    "STAIRS": ("STAIR", "STAIRS", "STAIRCASE"),
    "WALLS": ("WALL", "WALLS", "RETAINING WALL", "SHEAR WALL", "BOUNDARY WALL"),
}
STOREY_WORDS = {"FOUNDATION": ("FOUNDATION", "FDN", "FOOTING LEVEL"), "GROUND": ("GROUND", "GL", "GRADE"),
                "GF": ("GF", "GROUND FLOOR", "G.F"), "1F": ("1F", "FIRST FLOOR", "1ST FLOOR", "F.F"),
                "2F": ("2F", "SECOND FLOOR", "2ND FLOOR"), "3F": ("3F", "THIRD FLOOR", "3RD FLOOR"),
                "RF": ("RF", "ROOF", "ROOF FLOOR")}
TOL_REL, TOL_ABS = 0.02, 0.05


def _norm(s):
    return " ".join(str(s or "").upper().replace("_", " ").replace("-", " ").split())


def map_family(word):
    w = _norm(word)
    for fam, ws in FAMILY_WORDS.items():
        if w == fam.replace("_", " ") or w in ws:
            return fam
    return None


def map_storey(word):
    w = _norm(word)
    if w in ("", "ALL", "TOTAL", "*"):
        return "ALL"
    for st, ws in STOREY_WORDS.items():
        if w == st or w in ws:
            return st
    return None


def read_reference(text):
    rows = []
    for k, r in enumerate(csv.DictReader(io.StringIO(text)), 2):
        q = r.get("QUANTITY")
        try:
            qv = float(q)
        except (TypeError, ValueError):
            qv = None
        rows.append({"line": k, "family_text": r.get("FAMILY"), "storey_text": r.get("STOREY"),
                     "family": map_family(r.get("FAMILY")), "storey": map_storey(r.get("STOREY")),
                     "quantity": qv, "unit": _norm(r.get("UNIT")) or "M3", "ref": r.get("ITEM_REF") or "",
                     "text": (r.get("DESCRIPTION") or "")[:120]})
    return rows


def engine_side(items):
    out = defaultdict(lambda: {"base": 0.0, "exposure_low": 0.0, "exposure_high": 0.0, "n": 0, "n_unresolved": 0})
    for i in items:
        if i.get("trade") != "CONCRETE":
            continue
        k = (i["family"], i.get("storey"))
        if i.get("category") in ("PROVISIONAL", "VERIFIED"):
            out[k]["base"] += i.get("base") or 0.0
            out[k]["n"] += 1
        elif i.get("category") == "UNRESOLVED":
            out[k]["exposure_low"] += i.get("exposure_low") or 0.0
            out[k]["exposure_high"] += i.get("exposure_high") or 0.0
            out[k]["n_unresolved"] += 1
    return dict(out)


def _state(B, Eh, R):
    if R is None:
        return "ENGINE_ONLY"
    if B == 0.0 and Eh == 0.0:
        return "REFERENCE_ONLY" if R > 0 else "MATCH"
    t = max(TOL_REL * abs(R), TOL_ABS)
    if abs(R - B) <= t:
        return "MATCH"
    if B < R <= B + Eh + t:
        return "EXPLAINED_BY_UNRESOLVED"
    if R > B + Eh + t:
        return "ENGINE_SHORT"
    return "ENGINE_OVER"


def reconcile(items, ref_rows, *, rate=None):
    eng = engine_side(items)
    unmapped = [r for r in ref_rows if r["family"] is None or r["storey"] is None or r["quantity"] is None or
                r["unit"] not in ("M3", "CUM", "CU.M", "CUBIC METRE", "CUBIC METER")]
    ref = defaultdict(float)
    n_ref = defaultdict(int)
    for r in ref_rows:
        if r in unmapped:
            continue
        ref[(r["family"], r["storey"])] += r["quantity"]
        n_ref[(r["family"], r["storey"])] += 1
    # a reference row with storey ALL compares the family over every storey of the engine
    keys = set(eng) | {k for k in ref if k[1] != "ALL"}
    fam_all = {k[0] for k in ref if k[1] == "ALL"}
    rows = []
    for fam in sorted({k[0] for k in keys} | fam_all):
        if fam in fam_all:
            B = sum(v["base"] for k, v in eng.items() if k[0] == fam)
            El = sum(v["exposure_low"] for k, v in eng.items() if k[0] == fam)
            Eh = sum(v["exposure_high"] for k, v in eng.items() if k[0] == fam)
            R = sum(v for k, v in ref.items() if k[0] == fam)
            rows.append(_row(fam, "ALL", B, El, Eh, R, sum(n for k, n in n_ref.items() if k[0] == fam), rate))
            continue
        for st in sorted({k[1] for k in keys if k[0] == fam}, key=str):
            e = eng.get((fam, st), {"base": 0.0, "exposure_low": 0.0, "exposure_high": 0.0})
            R = ref.get((fam, st))
            rows.append(_row(fam, st, e["base"], e["exposure_low"], e["exposure_high"], R, n_ref.get((fam, st), 0),
                             rate))
    tot = defaultdict(lambda: {"n": 0, "engine_base_m3": 0.0, "reference_m3": 0.0})
    for r in rows:
        t = tot[r["STATE"]]
        t["n"] += 1
        t["engine_base_m3"] += r["ENGINE_BASE_M3"]
        t["reference_m3"] += r["REFERENCE_M3"] or 0.0
    return {"policy": POLICY_ID, "format": FORMAT, "rows": rows,
            "totals": {k: {kk: round(vv, 4) if isinstance(vv, float) else vv for kk, vv in v.items()}
                       for k, v in sorted(tot.items())},
            "engine_base_m3": round(sum(r["ENGINE_BASE_M3"] for r in rows), 4),
            "engine_exposure_high_m3": round(sum(r["ENGINE_UNRESOLVED_HIGH_M3"] for r in rows), 4),
            "reference_m3": round(sum(r["REFERENCE_M3"] or 0.0 for r in rows), 4),
            "unmapped": [{k: r[k] for k in ("line", "family_text", "storey_text", "quantity", "unit")}
                         for r in unmapped]}


def _row(fam, st, B, El, Eh, R, n_ref, rate):
    d = None if R is None else R - B
    return {"FAMILY": fam, "STOREY": st, "ENGINE_BASE_M3": round(B, 4), "ENGINE_UNRESOLVED_LOW_M3": round(El, 4),
            "ENGINE_UNRESOLVED_HIGH_M3": round(Eh, 4), "REFERENCE_M3": None if R is None else round(R, 4),
            "REFERENCE_ROWS": n_ref, "DIFF_REF_MINUS_ENGINE_M3": None if d is None else round(d, 4) + 0.0,
            "STATE": _state(B, Eh, R),
            "DIFF_VALUE_AT_RATE": None if (d is None or rate is None) else round(d * rate, 3) + 0.0}

"""PA04 §10 self-checks run over a register before it is accepted.

Each check returns {"CHECK": name, "PASS": bool, "FINDINGS": [...]}.  A
register is accepted only when every applicable check passes or every
failure is recorded as an explicit finding in the gate.
"""

from __future__ import annotations

import re

VALID_STATES = ("SOURCE_ESTABLISHED_QUANTITY", "OWNER_PARAMETRIC_QUANTITY", "PROVISIONAL_QUANTITY", "CONTRACTOR_MEASUREMENT_QUANTITY",
                "NOT_ESTABLISHED", "GEOMETRIC_REFERENCE_ONLY")
UNITS = ("m", "lm", "m2", "m3", "nr", "count")
BENCHMARK_FIGURES = (1151.1375, 1469.9675, 82.399, 48.47, 96.94, 12.9, 116.495, 58.2475, 19.88, 25.34, 19.04, 113.76, 69.0)


def _walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")
    else:
        yield path, obj


def source_completeness(lines, required=("SOURCE",)):
    f = [l.get("ID") or l.get("LINE_ID") or l.get("FACE_ID") for l in lines if any(not l.get(k) for k in required)]
    return {"CHECK": "SOURCE_COMPLETENESS_CHECK", "PASS": not f, "FINDINGS": f}


def dimension_ownership(lines):
    """Every line that carries a printed value must say what owns it."""
    f = [l.get("ID") for l in lines if l.get("PRINTED_VALUE") is not None and not l.get("OWNER")]
    return {"CHECK": "DIMENSION_OWNERSHIP_CHECK", "PASS": not f, "FINDINGS": f}


def geometry_closure(faces, expected_perimeter_m=None, tol=0.05):
    """The classified boundary (wall + open + door + unresolved) must sum to the region perimeter."""
    total = round(sum(x.get("LENGTH_M", 0) for x in faces), 3)
    if expected_perimeter_m is None:
        return {"CHECK": "GEOMETRY_CLOSURE_CHECK", "PASS": True, "FINDINGS": [], "CLASSIFIED_LM": total}
    ok = abs(total - expected_perimeter_m) <= tol * max(1.0, expected_perimeter_m)
    return {"CHECK": "GEOMETRY_CLOSURE_CHECK", "PASS": ok, "FINDINGS": [] if ok else [f"classified {total} vs perimeter {expected_perimeter_m}"], "CLASSIFIED_LM": total}


def trade_eligibility(lines):
    """A quantity in m2 with an unknown treatment / finish must not be a
    SOURCE_ESTABLISHED / OWNER_PARAMETRIC quantity."""
    f = []
    for l in lines:
        if l.get("UNIT") == "m2" and l.get("TREATMENT_STATUS") in ("UNKNOWN", "NOT_ESTABLISHED") and l.get("QUANTITY_STATE") in ("SOURCE_ESTABLISHED_QUANTITY", "OWNER_PARAMETRIC_QUANTITY"):
            f.append(l.get("ID") or l.get("LINE_ID"))
    return {"CHECK": "TRADE_ELIGIBILITY_CHECK", "PASS": not f, "FINDINGS": f}


def unit_check(lines):
    f = []
    for l in lines:
        u = l.get("UNIT")
        if u is not None and u not in UNITS:
            f.append(f"{l.get('ID') or l.get('LINE_ID')}: unit {u}")
        if l.get("QUANTITY_STATE") is not None and l["QUANTITY_STATE"] not in VALID_STATES:
            f.append(f"{l.get('ID') or l.get('LINE_ID')}: state {l['QUANTITY_STATE']}")
    return {"CHECK": "UNIT_CHECK", "PASS": not f, "FINDINGS": f}


def provenance(lines, keys=("SOURCE_ENTITY_IDS", "SOURCE")):
    f = [l.get("ID") or l.get("LINE_ID") for l in lines if not any(l.get(k) for k in keys)]
    return {"CHECK": "PROVENANCE_CHECK", "PASS": not f, "FINDINGS": f}


def cross_sheet_contradiction(pairs, tol=0.02):
    """pairs: [{"ITEM": ..., "A": value, "A_SOURCE": ..., "B": value, "B_SOURCE": ...}]
    A contradiction is recorded, never resolved here."""
    f = []
    for p in pairs:
        a, b = p.get("A"), p.get("B")
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) > tol * max(abs(a), abs(b), 1e-9):
            f.append({"ITEM": p["ITEM"], "A": a, "A_SOURCE": p.get("A_SOURCE"), "B": b, "B_SOURCE": p.get("B_SOURCE"), "RESOLVED_HERE": False})
    return {"CHECK": "CROSS_SHEET_CONTRADICTION_CHECK", "PASS": not f, "FINDINGS": f}


def benchmark_leakage(obj):
    hits = []
    for path, v in _walk(obj):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            for b in BENCHMARK_FIGURES:
                if abs(float(v) - b) < 1e-6:
                    hits.append({"AT": path, "VALUE": v})
        elif isinstance(v, str) and re.search(r"invoice\s*no|benchmark value|contractor total", v, re.I):
            hits.append({"AT": path, "TEXT": v[:60]})
    return {"CHECK": "BENCHMARK_LEAKAGE_CHECK", "PASS": not hits, "FINDINGS": hits}


def run_all(register, lines, faces=None, contradictions=None, perimeter=None, required_source=("SOURCE",), provenance_keys=("SOURCE_ENTITY_IDS", "SOURCE")):
    checks = [source_completeness(lines, required_source), dimension_ownership(lines), geometry_closure(faces or [], perimeter),
              trade_eligibility(lines), unit_check(lines), provenance(lines, provenance_keys), cross_sheet_contradiction(contradictions or []),
              benchmark_leakage(register)]
    return {"CHECKS": checks, "ALL_PASS": all(c["PASS"] for c in checks), "FAILED": [c["CHECK"] for c in checks if not c["PASS"]]}

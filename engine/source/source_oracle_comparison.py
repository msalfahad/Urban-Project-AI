"""SOURCE_ORACLE_COMPARISON_REGISTER (generic).

One row per (element, fact): the Urban production value beside an external oracle's value.
Results: MATCH / CLOSE / CONFLICT / NOT_COMPARABLE / ORACLE_UNAVAILABLE.
A row is evidence for a reviewer. It NEVER changes the Urban value: the Urban fact passed in is copied, not edited,
and no function here returns a value to write back.
Stdlib only.
"""

from __future__ import annotations

import copy
import hashlib
import json

from . import cad_oracle as CO

MATCH = "MATCH"
CLOSE = "CLOSE"
CONFLICT = "CONFLICT"
NOT_COMPARABLE = "NOT_COMPARABLE"
UNAVAILABLE = "ORACLE_UNAVAILABLE"
RESULTS = (MATCH, CLOSE, CONFLICT, NOT_COMPARABLE, UNAVAILABLE)
FIELDS = ("comparison_id", "element_id", "fact_type", "urban_value", "urban_source_refs", "urban_status",
          "oracle_name", "oracle_value", "oracle_refs", "oracle_status", "difference", "difference_percent",
          "basis_match", "result", "note")


def _cid(element_id, fact_type, oracle):
    return "SOC-" + hashlib.sha256(json.dumps([element_id, fact_type, oracle]).encode()).hexdigest()[:12]


def compare(urban, oracle_answer, *, basis_match, abs_tol=0.0, rel_tol=0.0, close_rel_tol=None):
    """urban: {element_id, fact_type, value, source_refs, status}. oracle_answer: cad_oracle.answer(...) or a dict
    with the same keys. Numeric values: |d| <= abs_tol or <= rel_tol x |urban| -> MATCH, within close_rel_tol ->
    CLOSE, else CONFLICT. Non-numeric: equal -> MATCH else CONFLICT."""
    u = copy.deepcopy(urban)
    o = dict(oracle_answer)
    row = {"comparison_id": _cid(u["element_id"], u["fact_type"], o.get("oracle")), "element_id": u["element_id"],
           "fact_type": u["fact_type"], "urban_value": u.get("value"), "urban_source_refs": u.get("source_refs", []),
           "urban_status": u.get("status"), "oracle_name": o.get("oracle"), "oracle_value": o.get("value"),
           "oracle_refs": o.get("refs", []), "oracle_status": o.get("state"), "difference": None,
           "difference_percent": None, "basis_match": bool(basis_match), "note": None}
    if o.get("state") != CO.OK:
        row["result"] = UNAVAILABLE
        row["note"] = "oracle incomplete or unavailable - not a value" if o.get("state") == CO.INCOMPLETE else \
            "oracle unavailable"
        return row
    if not basis_match or u.get("value") is None:
        row["result"] = NOT_COMPARABLE
        row["note"] = "measurement basis differs" if not basis_match else "no Urban value"
        return row
    a, b = u["value"], o["value"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        d = b - a
        row["difference"] = d
        row["difference_percent"] = None if not a else 100.0 * d / a
        tol = max(abs_tol, rel_tol * abs(a))
        if abs(d) <= tol:
            row["result"] = MATCH
        elif close_rel_tol is not None and abs(d) <= close_rel_tol * abs(a):
            row["result"] = CLOSE
        else:
            row["result"] = CONFLICT
    else:
        row["result"] = MATCH if a == b else CONFLICT
    return row


def register(rows):
    ids = [r["comparison_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate comparison ids")
    from collections import Counter
    return {"register": "SOURCE_ORACLE_COMPARISON_REGISTER", "fields": list(FIELDS), "rows": rows,
            "summary": dict(Counter(r["result"] for r in rows)),
            "rule": "no oracle value changes an Urban value; rows are review evidence only"}

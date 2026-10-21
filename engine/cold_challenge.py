"""Cold-challenge reconciliation (PA04 stage C).

A primary reading and an independent reading of the same source question
are compared field by field.  No majority vote, no averaging: each field is
AGREE, DISAGREE, PRIMARY_ONLY, CHALLENGER_ONLY or AGREE_ON_NUMBER_ONLY (same
value, incompatible reasoning / basis).  The reconciliation also records
which authority (DWG, printed dimension, section, structural, owner
evidence) decides a disagreement, or that none does (UNRESOLVED).
"""

from __future__ import annotations

AUTHORITIES = ("DWG_DXF", "PRINTED_DIMENSION", "SECTION_ELEVATION", "STRUCTURAL_SOURCE", "SOURCE_HIERARCHY", "OWNER_EVIDENCE", "NONE")
THRESHOLDS = {"NEW_ROOM_OR_VOID_IDENTITY": 0.0, "DOUBLE_HEIGHT_INTERPRETATION": 0.0, "CURVE_M2": 2.0, "FACADE_OR_PARAPET_M2": 5.0,
              "STRUCTURAL_FACE_OWNERSHIP": 0.0, "PROJECT_WIDE_RULE": 0.0, "SOURCE_DISAGREEMENT": 0.0, "LOW_MEDIUM_CONFIDENCE_WITH_IMPACT": 0.0}


def challenge_required(*, kind, quantity_impact_m2=0.0, confidence="HIGH"):
    if kind not in THRESHOLDS:
        raise ValueError(f"unknown challenge kind {kind}")
    if kind in ("CURVE_M2", "FACADE_OR_PARAPET_M2"):
        return quantity_impact_m2 > THRESHOLDS[kind]
    if kind == "LOW_MEDIUM_CONFIDENCE_WITH_IMPACT":
        return confidence in ("LOW", "MEDIUM") and quantity_impact_m2 > 0
    return True


def compare_field(name, primary, challenger, *, primary_basis=None, challenger_basis=None, tol=0.02):
    def same(a, b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
            return abs(a - b) <= tol * max(abs(a), abs(b), 1e-9)
        return a == b
    if primary is None and challenger is None:
        verdict = "BOTH_ABSENT"
    elif primary is None:
        verdict = "CHALLENGER_ONLY"
    elif challenger is None:
        verdict = "PRIMARY_ONLY"
    elif same(primary, challenger):
        numeric = isinstance(primary, (int, float)) and not isinstance(primary, bool)
        verdict = "AGREE_ON_NUMBER_ONLY" if (numeric and primary_basis and challenger_basis and primary_basis != challenger_basis) else "AGREE"
    else:
        verdict = "DISAGREE"
    return {"FIELD": name, "PRIMARY": primary, "CHALLENGER": challenger, "PRIMARY_BASIS": primary_basis, "CHALLENGER_BASIS": challenger_basis, "VERDICT": verdict}


def reconcile(item_id, fields, *, decided_by=None, decision=None, note=None):
    """fields: list from compare_field.  decided_by names the authority that
    settles the DISAGREE / *_ONLY fields (or NONE -> UNRESOLVED)."""
    if decided_by is not None and decided_by not in AUTHORITIES:
        raise ValueError(f"unknown authority {decided_by}")
    open_fields = [f["FIELD"] for f in fields if f["VERDICT"] in ("DISAGREE", "PRIMARY_ONLY", "CHALLENGER_ONLY", "AGREE_ON_NUMBER_ONLY")]
    if open_fields and decided_by is None:
        raise ValueError(f"{item_id}: open fields {open_fields} need decided_by (or NONE)")
    status = "AGREED" if not open_fields else ("RESOLVED_BY_" + decided_by if decided_by != "NONE" else "UNRESOLVED")
    return {"ITEM_ID": item_id, "FIELDS": fields, "OPEN_FIELDS": open_fields, "DECIDED_BY": decided_by, "DECISION": decision, "STATUS": status,
            "MAJORITY_VOTE": False, "AVERAGED": False, "NOTE": note}

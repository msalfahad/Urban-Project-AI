"""One canonical state lattice (PA06 WS10) with adapters at the boundaries.

Result concepts: SOURCE_ESTABLISHED, OWNER_PROJECT_INPUT, OWNER_PARAMETRIC,
PROVISIONAL, GEOMETRIC_REFERENCE_ONLY, NOT_ESTABLISHED, SOURCE_REQUIRED,
HUMAN_REVIEW, NOT_APPLICABLE.  Five status dimensions stay separate; no
single confidence field collapses them.  Historical artifacts are never
rewritten: adapters translate old tokens forward when they are read.
"""

from __future__ import annotations

CONCEPTS = ("SOURCE_ESTABLISHED", "OWNER_PROJECT_INPUT", "OWNER_PARAMETRIC", "PROVISIONAL", "GEOMETRIC_REFERENCE_ONLY", "NOT_ESTABLISHED", "SOURCE_REQUIRED", "HUMAN_REVIEW", "NOT_APPLICABLE")
DIMENSIONS = ("IDENTITY_STATUS", "GEOMETRY_STATUS", "TOPOLOGY_STATUS", "MEASUREMENT_STATUS", "QUANTITY_STATUS")
LADDER = ("SOURCE_ESTABLISHED", "OWNER_PROJECT_INPUT", "OWNER_PARAMETRIC", "PROVISIONAL", "GEOMETRIC_REFERENCE_ONLY", "NOT_ESTABLISHED", "SOURCE_REQUIRED")
RANK = {c: i for i, c in enumerate(LADDER)}
# adapters: old vocabulary -> canonical concept (boundary only)
ADAPTERS = {
    "quantity_state": {"SOURCE_ESTABLISHED_QUANTITY": "SOURCE_ESTABLISHED", "OWNER_PARAMETRIC_QUANTITY": "OWNER_PARAMETRIC", "PROVISIONAL_QUANTITY": "PROVISIONAL", "PROVISIONAL_DEFAULT_QUANTITY": "PROVISIONAL",
                       "CONTRACTOR_MEASUREMENT_QUANTITY": "NOT_APPLICABLE", "NOT_ESTABLISHED": "NOT_ESTABLISHED", "GEOMETRIC_REFERENCE_ONLY": "GEOMETRIC_REFERENCE_ONLY"},
    "height_parameters": {"OWNER_AUTHORISED": "OWNER_PROJECT_INPUT", "SOURCE_ESTABLISHED": "SOURCE_ESTABLISHED", "PROVISIONAL": "PROVISIONAL", "NOT_ESTABLISHED": "NOT_ESTABLISHED"},
    "a21_provenance": {"DRAWING": "SOURCE_ESTABLISHED", "SPECIFICATION": "SOURCE_ESTABLISHED", "URBAN_STANDARD": "OWNER_PARAMETRIC", "CONTRACTOR_RULE": "NOT_APPLICABLE",
                       "OWNER_PROJECT_INPUT": "OWNER_PROJECT_INPUT", "TEMPORARY_DEFAULT": "PROVISIONAL", "UNKNOWN": "NOT_ESTABLISHED"},
    "self_checks": {"SOURCE_ESTABLISHED_QUANTITY": "SOURCE_ESTABLISHED", "OWNER_PARAMETRIC_QUANTITY": "OWNER_PARAMETRIC", "PROVISIONAL_QUANTITY": "PROVISIONAL", "PROVISIONAL_DEFAULT_QUANTITY": "PROVISIONAL",
                    "CONTRACTOR_MEASUREMENT_QUANTITY": "NOT_APPLICABLE", "NOT_ESTABLISHED": "NOT_ESTABLISHED", "GEOMETRIC_REFERENCE_ONLY": "GEOMETRIC_REFERENCE_ONLY"},
    "pa05_status": {"SOURCE_ESTABLISHED": "SOURCE_ESTABLISHED", "OWNER_ESTABLISHED": "OWNER_PROJECT_INPUT", "PROVISIONAL": "PROVISIONAL", "TEMPORARY_DEFAULT": "PROVISIONAL",
                    "NOT_ESTABLISHED": "NOT_ESTABLISHED", "NOT_APPLICABLE": "NOT_APPLICABLE", "CONFLICT": "HUMAN_REVIEW", "HUMAN_REVIEW": "HUMAN_REVIEW"},
    "owner_parameter_source_type": {"OWNER_PROJECT_INPUT": "OWNER_PROJECT_INPUT", "TEMPORARY_OWNER_DEFAULT": "PROVISIONAL", "TEMPORARY_DEFAULT": "PROVISIONAL", "DRAWING": "SOURCE_ESTABLISHED",
                                    "SPECIFICATION": "SOURCE_ESTABLISHED", "UNKNOWN": "NOT_ESTABLISHED", "URBAN_STANDARD": "OWNER_PARAMETRIC"},
}
# reverse adapter into the quantity engines' vocabulary (engine.quantity_state) so old code keeps its own checks
TO_QUANTITY_STATE = {"SOURCE_ESTABLISHED": "SOURCE_ESTABLISHED_QUANTITY", "OWNER_PROJECT_INPUT": "OWNER_PARAMETRIC_QUANTITY", "OWNER_PARAMETRIC": "OWNER_PARAMETRIC_QUANTITY",
                     "PROVISIONAL": "PROVISIONAL_QUANTITY", "GEOMETRIC_REFERENCE_ONLY": "NOT_ESTABLISHED", "NOT_ESTABLISHED": "NOT_ESTABLISHED", "SOURCE_REQUIRED": "NOT_ESTABLISHED",
                     "HUMAN_REVIEW": "NOT_ESTABLISHED", "NOT_APPLICABLE": "NOT_ESTABLISHED"}


def adapt(token, vocabulary):
    """Translate a token from an older vocabulary; unknown tokens are HUMAN_REVIEW, never silently established."""
    if token in CONCEPTS:
        return token
    return ADAPTERS[vocabulary].get(str(token).strip(), "HUMAN_REVIEW")


def record(**dims):
    out = {}
    for d in DIMENSIONS:
        v = dims.get(d, "NOT_ESTABLISHED")
        if v not in CONCEPTS:
            raise ValueError(f"{d}: {v} is not a canonical concept")
        out[d] = v
    extra = set(dims) - set(DIMENSIONS)
    if extra:
        raise ValueError(f"unknown status dimensions {sorted(extra)}; a single CONFIDENCE field is not allowed")
    return out


def weakest(values):
    vals = list(values)
    for special in ("HUMAN_REVIEW",):
        if special in vals:
            return special
    ranked = [v for v in vals if v in RANK]
    if not ranked:
        return "NOT_APPLICABLE" if vals and all(v == "NOT_APPLICABLE" for v in vals) else "NOT_ESTABLISHED"
    return max(ranked, key=lambda v: RANK[v])


def migration_report(module_tokens):
    """module_tokens: {module name: (vocabulary key, [tokens found in that module])} -> PA06_STATUS_MIGRATION_REPORT."""
    rows = []
    for mod, (vocab, toks) in module_tokens.items():
        for t in toks:
            rows.append({"MODULE": mod, "TOKEN": t, "VOCABULARY": vocab, "CANONICAL": adapt(t, vocab), "ADAPTER_AT_BOUNDARY": True, "MODULE_REWRITTEN": False})
    return {"ARTIFACT": "PA06_STATUS_MIGRATION_REPORT", "CANONICAL_CONCEPTS": CONCEPTS, "STATUS_DIMENSIONS": DIMENSIONS, "ROWS": rows,
            "UNMAPPED": [r for r in rows if r["CANONICAL"] == "HUMAN_REVIEW" and r["TOKEN"] not in ("HUMAN_REVIEW", "CONFLICT")],
            "RULE": "old modules keep their vocabularies; every value crossing into the PA06 registers passes through adapt(); historical artifacts are not rewritten"}

"""One canonical status model (PA05 §11).

Five independent dimensions, one vocabulary.  Forward adapters translate
the older tokens (QUANTITY_STATE etc.) into this model; frozen artifacts
are never rewritten.
"""

from __future__ import annotations

VOCAB = ("SOURCE_ESTABLISHED", "OWNER_ESTABLISHED", "PROVISIONAL", "TEMPORARY_DEFAULT", "NOT_ESTABLISHED", "NOT_APPLICABLE", "CONFLICT", "HUMAN_REVIEW")
DIMENSIONS = ("SOURCE_STATUS", "GEOMETRY_STATUS", "SEMANTIC_STATUS", "MEASUREMENT_STATUS", "QUANTITY_STATUS")
RANK = {v: i for i, v in enumerate(("SOURCE_ESTABLISHED", "OWNER_ESTABLISHED", "PROVISIONAL", "TEMPORARY_DEFAULT", "NOT_ESTABLISHED"))}

# forward adapters for the vocabularies used in PA01-PA04 artifacts
LEGACY = {
    "SOURCE_ESTABLISHED_QUANTITY": "SOURCE_ESTABLISHED", "OWNER_PARAMETRIC_QUANTITY": "OWNER_ESTABLISHED", "PROVISIONAL_QUANTITY": "PROVISIONAL",
    "CONTRACTOR_MEASUREMENT_QUANTITY": "NOT_APPLICABLE", "NOT_ESTABLISHED": "NOT_ESTABLISHED", "GEOMETRIC_REFERENCE_ONLY": "NOT_APPLICABLE",
    "ESTABLISHED_FROM_DWG": "SOURCE_ESTABLISHED", "ESTABLISHED": "SOURCE_ESTABLISHED", "OWNER_ESTABLISHED": "OWNER_ESTABLISHED", "OWNER_PROJECT_INPUT": "OWNER_ESTABLISHED",
    "OWNER_AUTHORISED": "OWNER_ESTABLISHED", "PROVISIONAL": "PROVISIONAL", "PROVISIONAL_DEFAULT": "TEMPORARY_DEFAULT", "TEMP_DEFAULT": "TEMPORARY_DEFAULT",
    "PROPOSED_CORRESPONDENCE": "PROVISIONAL", "UNKNOWN": "NOT_ESTABLISHED", "UNRESOLVED": "HUMAN_REVIEW", "NOT_FULLY_ESTABLISHED": "PROVISIONAL",
    "DERIVED_PROVISIONAL": "PROVISIONAL", "SITE_RECORD": "NOT_APPLICABLE", "PRINTED_OWNED": "SOURCE_ESTABLISHED",
}


def status(**dims):
    """Build a status record; every given dimension must use the vocabulary; missing dimensions are NOT_ESTABLISHED."""
    out = {}
    for d in DIMENSIONS:
        v = dims.get(d, "NOT_ESTABLISHED")
        if v not in VOCAB:
            raise ValueError(f"{d}: '{v}' is not in the canonical vocabulary {VOCAB}")
        out[d] = v
    extra = set(dims) - set(DIMENSIONS)
    if extra:
        raise ValueError(f"unknown status dimensions {sorted(extra)}")
    return out


def from_legacy(token, dimension="QUANTITY_STATUS"):
    """Translate an older token; unknown tokens become HUMAN_REVIEW (never silently established)."""
    if token in VOCAB:
        v = token
    else:
        v = LEGACY.get(str(token).strip(), "HUMAN_REVIEW")
    return status(**{dimension: v})


def weakest(values):
    """The weakest of several states along the establishment ladder; CONFLICT / HUMAN_REVIEW / NOT_APPLICABLE propagate as themselves."""
    vals = list(values)
    for special in ("CONFLICT", "HUMAN_REVIEW"):
        if special in vals:
            return special
    ranked = [v for v in vals if v in RANK]
    if not ranked:
        return "NOT_APPLICABLE" if vals and all(v == "NOT_APPLICABLE" for v in vals) else "NOT_ESTABLISHED"
    return max(ranked, key=lambda v: RANK[v])


def quantity_status_from(source, geometry, semantic, measurement):
    """A quantity is never stronger than the weakest of its inputs."""
    return weakest([source, geometry, semantic, measurement])

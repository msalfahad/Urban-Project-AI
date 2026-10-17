"""GRAPHIC EVIDENCE POLICY - what a drawn detail may and may not contribute to an accurate reinforcement quantity.

Generic, stdlib only. A graphic reading (a bar shape on a detail sheet, a leader, a link icon) is classified into
exactly one of four classes, and the class decides whether the portion it describes may carry length / kg:

    GRAPHIC_EXPLICIT_DIMENSIONED          the portion carries a printed dimension             -> may produce quantity
    GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY  the portion's ends bind to project-source levels    -> may produce quantity,
                                          (schedule size, cover note, bar levels)                only if all four
                                                                                                 DERIVATION_CONDITIONS hold
    GRAPHIC_EXPLICIT_SHAPE_ONLY           shape / connectivity / topology / identity /        -> NO length, NO kg
                                          applicability are drawn, the extent is not
    GRAPHIC_NTS_OR_UNDIMENSIONED          interpretation / QA evidence only                   -> NO length, NO kg

A plotted-scale reading is never a length basis: a typical detail is not measured by its plot ("NEVER measure an NTS
typical detail by its plotted scale"). A portion with no drawing at all carries NO_GRAPHIC_EVIDENCE.

Portion states (one per portion of a modelled bar):
    KNOWN_STRAIGHT_SEGMENT        a released straight segment (its kg is known steel; the complete bar is a lower bound)
    DERIVED_LOWER_BOUND           a released derived segment (class A or B, envelope lower bound)
    SHAPE_FOUND_LENGTH_BLOCKED    the portion exists and its shape is drawn; its length is not established
    BLOCKED_UNQUANTIFIED          the portion is not established (existence or extent)
"""

from __future__ import annotations

GRAPHIC_EXPLICIT_DIMENSIONED = "GRAPHIC_EXPLICIT_DIMENSIONED"
GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY = "GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY"
GRAPHIC_EXPLICIT_SHAPE_ONLY = "GRAPHIC_EXPLICIT_SHAPE_ONLY"
GRAPHIC_NTS_OR_UNDIMENSIONED = "GRAPHIC_NTS_OR_UNDIMENSIONED"
CLASSES = (GRAPHIC_EXPLICIT_DIMENSIONED, GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY, GRAPHIC_EXPLICIT_SHAPE_ONLY,
           GRAPHIC_NTS_OR_UNDIMENSIONED)
NO_GRAPHIC_EVIDENCE = "NO_GRAPHIC_EVIDENCE"
QUANTITY_CLASSES = (GRAPHIC_EXPLICIT_DIMENSIONED, GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY)

# rule B: all four must hold for a derived portion to carry quantity
ENDPOINTS_DETERMINISTIC = "ENDPOINTS_DETERMINISTIC"
DIMENSIONS_FROM_PROJECT_SOURCE = "DIMENSIONS_FROM_PROJECT_SOURCE"
DERIVATION_REPRODUCIBLE = "DERIVATION_REPRODUCIBLE"
NO_CONTRADICTING_PROJECT_SOURCE = "NO_CONTRADICTING_PROJECT_SOURCE"
DERIVATION_CONDITIONS = (ENDPOINTS_DETERMINISTIC, DIMENSIONS_FROM_PROJECT_SOURCE, DERIVATION_REPRODUCIBLE,
                         NO_CONTRADICTING_PROJECT_SOURCE)

# length bases
PRINTED_DIMENSION = "PRINTED_DIMENSION"
PROJECT_SOURCE_GEOMETRY = "PROJECT_SOURCE_GEOMETRY"
PLOTTED_SCALE = "PLOTTED_SCALE"
LENGTH_BASES = (PRINTED_DIMENSION, PROJECT_SOURCE_GEOMETRY, PLOTTED_SCALE)

KNOWN_STRAIGHT_SEGMENT = "KNOWN_STRAIGHT_SEGMENT"
DERIVED_LOWER_BOUND = "DERIVED_LOWER_BOUND"
SHAPE_FOUND_LENGTH_BLOCKED = "SHAPE_FOUND_LENGTH_BLOCKED"
BLOCKED_UNQUANTIFIED = "BLOCKED_UNQUANTIFIED"
PORTION_STATES = (KNOWN_STRAIGHT_SEGMENT, DERIVED_LOWER_BOUND, SHAPE_FOUND_LENGTH_BLOCKED, BLOCKED_UNQUANTIFIED)
RELEASED_PORTION_STATES = (KNOWN_STRAIGHT_SEGMENT, DERIVED_LOWER_BOUND)

RULES = {
    "A": "GRAPHIC_EXPLICIT_DIMENSIONED may produce quantity (from the printed dimension)",
    "B": "GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY may produce quantity only if the endpoints are deterministic, the "
         "dimensions come from project-source geometry, the derivation is reproducible and no project source "
         "contradicts it",
    "C": "GRAPHIC_EXPLICIT_SHAPE_ONLY may establish shape, connectivity, topology, component identity and "
         "applicability, but may NOT create an undimensioned bar length or kg",
    "D": "GRAPHIC_NTS_OR_UNDIMENSIONED is interpretation / QA evidence only",
    "SCALE": "a plotted-scale reading is never a length basis; an N.T.S. typical detail is never measured by its plot",
}


class GraphicPolicyError(ValueError):
    """A graphic reading was asked to carry a quantity the policy does not allow."""


def _check_class(cls):
    if cls not in CLASSES and cls != NO_GRAPHIC_EVIDENCE:
        raise GraphicPolicyError(f"unknown graphic evidence class {cls!r}")


def failed_conditions(conditions):
    """The rule-B conditions that do not hold (missing counts as not holding)."""
    conditions = conditions or {}
    return [c for c in DERIVATION_CONDITIONS if conditions.get(c) is not True]


def may_quantify(cls, conditions=None):
    """(allowed, reason) for a portion of class `cls`; `conditions` maps DERIVATION_CONDITIONS -> bool (rule B)."""
    _check_class(cls)
    if cls == GRAPHIC_EXPLICIT_DIMENSIONED:
        return True, RULES["A"]
    if cls == GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY:
        bad = failed_conditions(conditions)
        return (not bad), (RULES["B"] if not bad else f"rule B fails: {', '.join(bad)}")
    if cls == GRAPHIC_EXPLICIT_SHAPE_ONLY:
        return False, RULES["C"]
    if cls == GRAPHIC_NTS_OR_UNDIMENSIONED:
        return False, RULES["D"]
    return False, "no graphic evidence: the portion is not drawn"


def admit_length(cls, length_mm, *, basis, conditions=None, nts=False):
    """Return `length_mm` if the policy lets a portion of class `cls` carry it on `basis`; raise otherwise.

    PLOTTED_SCALE is refused for every class (and an N.T.S. figure can never be measured); class A needs a
    PRINTED_DIMENSION, class B a PROJECT_SOURCE_GEOMETRY derivation with all four conditions; C and D never carry
    length."""
    _check_class(cls)
    if basis not in LENGTH_BASES:
        raise GraphicPolicyError(f"unknown length basis {basis!r}")
    if basis == PLOTTED_SCALE:
        raise GraphicPolicyError("a plotted-scale reading is never a length basis" +
                                 (" (N.T.S. figure)" if nts else ""))
    ok, why = may_quantify(cls, conditions)
    if not ok:
        raise GraphicPolicyError(why)
    if cls == GRAPHIC_EXPLICIT_DIMENSIONED and basis != PRINTED_DIMENSION:
        raise GraphicPolicyError("a dimensioned portion takes its length from the printed dimension")
    if cls == GRAPHIC_DERIVED_FROM_SOURCE_GEOMETRY and basis != PROJECT_SOURCE_GEOMETRY:
        raise GraphicPolicyError("a derived portion takes its length from project-source geometry")
    if length_mm is None or length_mm < 0:
        raise GraphicPolicyError("an admitted length must be a non-negative number")
    return float(length_mm)


def portion(portion_id, cls, *, shape_found, length_mm=None, basis=None, conditions=None, nts=False,
            known_segment=False):
    """One classified portion of a modelled bar: {portion, graphic_evidence_class, shape, length_mm, state, why}.

    `known_segment` marks a straight segment whose length came from the frozen source quantity (schedule size and
    cover, not the graphic); it is KNOWN_STRAIGHT_SEGMENT whatever the graphic class, because the graphic is not
    its length basis. Otherwise a length is admitted only through admit_length()."""
    _check_class(cls)
    if known_segment:
        if length_mm is None:
            raise GraphicPolicyError("a known straight segment needs its frozen length")
        return {"portion": portion_id, "graphic_evidence_class": cls, "shape": "SOURCE_FOUND" if shape_found else
                "NOT_DRAWN", "length_mm": float(length_mm), "length_basis": "FROZEN_SOURCE_QUANTITY",
                "state": KNOWN_STRAIGHT_SEGMENT, "why": "frozen straight length kept as known steel"}
    if length_mm is not None:
        admitted = admit_length(cls, length_mm, basis=basis, conditions=conditions, nts=nts)
        return {"portion": portion_id, "graphic_evidence_class": cls, "shape": "SOURCE_FOUND",
                "length_mm": admitted, "length_basis": basis, "state": DERIVED_LOWER_BOUND,
                "why": may_quantify(cls, conditions)[1]}
    why = may_quantify(cls, conditions)[1]
    return {"portion": portion_id, "graphic_evidence_class": cls,
            "shape": "SOURCE_FOUND" if shape_found else "NOT_DRAWN", "length_mm": None, "length_basis": None,
            "state": SHAPE_FOUND_LENGTH_BLOCKED if shape_found else BLOCKED_UNQUANTIFIED, "why": why}


def policy_record():
    return {"policy": "GRAPHIC_EVIDENCE_POLICY_V1", "classes": list(CLASSES), "rules": dict(RULES),
            "derivation_conditions": list(DERIVATION_CONDITIONS), "length_bases_allowed": [PRINTED_DIMENSION,
                                                                                          PROJECT_SOURCE_GEOMETRY],
            "length_bases_refused": [PLOTTED_SCALE], "portion_states": list(PORTION_STATES),
            "no_graphic": NO_GRAPHIC_EVIDENCE}

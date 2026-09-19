"""QUANTITY STATES and the weakest-input rule (directive §18, §19).

Every output line carries exactly one of five states. The state of a
derived quantity is the weakest state among its inputs, in this order:

    SOURCE_ESTABLISHED_QUANTITY    every input established from a source
    OWNER_PARAMETRIC_QUANTITY      an owner / project input is inside
    PROVISIONAL_QUANTITY           a provisional geometry input is inside
    CONTRACTOR_MEASUREMENT_QUANTITY a contractor convention is the basis
    NOT_ESTABLISHED                a critical input is missing

Units never mix: a total is per unit, and asking for one total across
m2 / lm / m3 / count / ton / KWD raises.
"""

from __future__ import annotations

STATES = ("SOURCE_ESTABLISHED_QUANTITY", "OWNER_PARAMETRIC_QUANTITY",
          "PROVISIONAL_QUANTITY", "CONTRACTOR_MEASUREMENT_QUANTITY",
          "NOT_ESTABLISHED")
RANK = {s: i for i, s in enumerate(STATES)}

# how an input's provenance maps onto a quantity state
INPUT_STATE = {
    "SOURCE_ESTABLISHED": "SOURCE_ESTABLISHED_QUANTITY",
    "ESTABLISHED": "SOURCE_ESTABLISHED_QUANTITY",
    "ESTABLISHED_FROM_DWG": "SOURCE_ESTABLISHED_QUANTITY",
    "OWNER_ESTABLISHED": "SOURCE_ESTABLISHED_QUANTITY",
    "OWNER_PROJECT_INPUT": "OWNER_PARAMETRIC_QUANTITY",
    "OWNER_PARAMETRIC": "OWNER_PARAMETRIC_QUANTITY",
    "PROVISIONAL": "PROVISIONAL_QUANTITY",
    "PROVISIONAL_DEFAULT": "PROVISIONAL_QUANTITY",
    "PROPOSED_CORRESPONDENCE": "PROVISIONAL_QUANTITY",
    "CONTRACTOR_MEASUREMENT_RULE": "CONTRACTOR_MEASUREMENT_QUANTITY",
    "SITE_RECORD": "CONTRACTOR_MEASUREMENT_QUANTITY",
    "NOT_ESTABLISHED": "NOT_ESTABLISHED",
    "AMBIGUOUS": "NOT_ESTABLISHED",
    "UNRESOLVED": "NOT_ESTABLISHED",
    None: "NOT_ESTABLISHED",
}

UNITS = ("m2", "lm", "m3", "count", "ton", "KWD")


class UnitMixError(ValueError):
    pass


def input_state(provenance) -> str:
    if provenance in STATES:
        return provenance
    return INPUT_STATE.get(provenance, "NOT_ESTABLISHED")


def weakest(inputs) -> str:
    """inputs: provenance / state strings of every critical input."""
    states = [input_state(i) for i in inputs] or ["NOT_ESTABLISHED"]
    return max(states, key=lambda s: RANK[s])


def totals_by_unit(lines) -> dict:
    """{unit: {state: total}} - never a cross-unit sum."""
    out = {}
    for ln in lines:
        u = ln.get("UNIT")
        if u not in UNITS:
            raise UnitMixError(f"unknown unit {u!r}")
        st = ln.get("QUANTITY_STATE")
        if st not in STATES:
            raise ValueError(f"line without a quantity state: {ln}")
        v = ln.get("VALUE")
        if v is None:
            continue
        out.setdefault(u, {}).setdefault(st, 0.0)
        out[u][st] = round(out[u][st] + float(v), 4)
    return out


def grand_total(lines):
    """Refused by design: a total across units is not a quantity."""
    units = {ln.get("UNIT") for ln in lines}
    if len(units) > 1:
        raise UnitMixError(f"cannot total across units {sorted(u for u in units if u)}")
    return totals_by_unit(lines)

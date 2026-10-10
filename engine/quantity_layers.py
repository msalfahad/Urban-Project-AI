"""QUANTITY LAYERS - the bases a trade item carries, never collapsed (§10).

    PHYSICAL_DESIGN_GEOMETRY        what exists: faces, lengths, heights
    MEASURED_NET_QUANTITY           engineering / QS: full physical opening
                                    deduction, reveals separate, project
                                    parameters; state is the weakest input
    OWNER_PARAMETRIC_QUANTITY  \\    the state of MEASURED_NET when an owner
    PROVISIONAL_DEFAULT_QUANTITY/   input or a temporary default is inside
    CONTRACTOR_MEASUREMENT_QUANTITY contractor / site commercial convention
                                    (half deductions, site heights, 2m=1m)
    WASTE_FACTOR, PROCUREMENT_QUANTITY   what is bought
    RATE, AMOUNT                    a supplier's price on a date, KWD

Physical = 100, engineering net = 92, contractor measured = 96,
procurement = 92 x (1 + waste): all can be correct at once, for different
purposes. A difference between two layers is MEASUREMENT_BASIS_DIFFERENCE
until the bases have been compared and an error shown.

A contractor convention never becomes physical geometry, and a rate
never becomes a rule. Nothing here approves a BOQ.
"""

from __future__ import annotations

LAYERS = (
    "PHYSICAL_DESIGN_GEOMETRY", "MEASURED_NET_QUANTITY",
    "OWNER_PARAMETRIC_QUANTITY", "PROVISIONAL_DEFAULT_QUANTITY",
    "CONTRACTOR_MEASUREMENT_QUANTITY", "WASTE_FACTOR", "PROCUREMENT_QUANTITY",
    "RATE", "AMOUNT",
)
BASES = ("ENGINEERING_QS", "CONTRACTOR_SITE_MEASUREMENT")
DIFFERENCE_CLASSES = (
    "MEASUREMENT_BASIS_DIFFERENCE", "DIMENSION_OWNERSHIP_DIFFERENCE",
    "CAD_MAPPING_DIFFERENCE", "DRAWING_AMBIGUITY", "IDENTITY_MAPPING_DIFFERENCE",
    "SCOPE_DIFFERENCE", "AGREEMENT", "UNRESOLVED",
)
DRIVERS = ("HEIGHT", "OPENING_DEDUCTION", "DOOR_DIMENSION", "REVEALS",
           "PARAPET_BASIS", "FACADE_BASIS", "GEOMETRY", "SCOPE", "OTHER")


def _num(x):
    return isinstance(x, (int, float))


def layered_item(*, item_id: str, trade: str, unit: str, physical: dict,
                 measured_net: dict, contractor: dict | None,
                 waste_factor=None, rate=None, currency: str = "KWD") -> dict:
    """One trade item with every layer present and none merged.

    physical      {LENGTH_M / AREA_M2 basis facts, STATUS}
    measured_net  {VALUE, STATE (SOURCE_ESTABLISHED / OWNER_PARAMETRIC /
                  PROVISIONAL_DEFAULT / NOT_ESTABLISHED), RULES, INPUTS}
    contractor    {VALUE, RULES, SOURCE_TYPE} or None when the convention
                  cannot be applied to this item
    """
    v = measured_net.get("VALUE")
    proc = (round(v * (1 + waste_factor), 4) if _num(v) and _num(waste_factor) else None)
    amount = (round(proc * rate, 3) if _num(proc) and _num(rate) else None)
    c = contractor or {"VALUE": None, "RULES": None,
                       "SOURCE_TYPE": "CONTRACTOR_MEASUREMENT_RULE",
                       "STATUS": "NOT_APPLIED"}
    delta = (round(c["VALUE"] - v, 4) if _num(v) and _num(c.get("VALUE")) else None)
    return {
        "ITEM_ID": item_id, "TRADE": trade, "UNIT": unit,
        "PHYSICAL_DESIGN_GEOMETRY": physical,
        "MEASURED_NET_QUANTITY": {**measured_net, "BASIS": "ENGINEERING_QS"},
        "QUANTITY_STATE_OF_MEASURED_NET": measured_net.get("STATE"),
        "OWNER_PARAMETRIC_QUANTITY": (v if measured_net.get("STATE") == "OWNER_PARAMETRIC_QUANTITY" else None),
        "PROVISIONAL_DEFAULT_QUANTITY": (v if measured_net.get("STATE") == "PROVISIONAL_DEFAULT_QUANTITY" else None),
        "CONTRACTOR_MEASUREMENT_QUANTITY": {**c, "BASIS": "CONTRACTOR_SITE_MEASUREMENT"},
        "WASTE_FACTOR": waste_factor,
        "PROCUREMENT_QUANTITY": proc,
        "RATE": {"VALUE": rate, "CURRENCY": currency,
                 "STATUS": "QUOTED" if _num(rate) else "NO_RATE_QUOTED"},
        "AMOUNT": {"VALUE": amount, "CURRENCY": currency},
        "CONTRACTOR_MINUS_ENGINEERING": delta,
        "DIFFERENCE_CLASS": ("MEASUREMENT_BASIS_DIFFERENCE" if delta not in (None, 0.0)
                             else ("AGREEMENT" if delta == 0.0 else "UNRESOLVED")),
        "LAYERS_ARE_NEVER_COLLAPSED": True,
        "NOT_AN_APPROVED_BOQ": True,
    }

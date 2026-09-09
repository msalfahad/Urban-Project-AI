"""E14 support — a faithful mirror of the web app's BoqFormulaEngine.

Urban Projects Manager (the Flutter web app) computes every BOQ quantity from a
`formulaType` plus a `measurements` map, in `lib/core/utils/boq_formula_engine.dart`.
When our system writes a BOQ into the app's Firestore, the app re-computes the
quantity with *its* engine — so ours must agree to the decimal, or the number
the engineer approved and the number the app shows will differ.

This module reproduces that Dart logic exactly. The tests pin it to the app's
definitions; if the app's engine ever changes, a test here should fail and tell
us to re-sync.

    formulaType : quantity
    'simple'    : qty
    'area'      : length * width
    'volume'    : length * width * height
    'perimeter' : perimeter * height
"""

from __future__ import annotations

# The ordered measurement field names each formula type expects — identical to
# BoqFormulaEngine.fieldsFor in the app.
FIELDS_FOR: dict[str, list[str]] = {
    "simple": ["qty"],
    "area": ["length", "width"],
    "volume": ["length", "width", "height"],
    "perimeter": ["perimeter", "height"],
}


def compute_quantity(formula_type: str, values: dict[str, float]) -> float:
    """Reproduce BoqFormulaEngine.computeQuantity exactly.

    A missing field reads as 0, matching the app's `values['x'] ?? 0`.
    """
    if formula_type == "area":
        return (values.get("length", 0.0)) * (values.get("width", 0.0))
    if formula_type == "volume":
        return (
            values.get("length", 0.0)
            * values.get("width", 0.0)
            * values.get("height", 0.0)
        )
    if formula_type == "perimeter":
        return (values.get("perimeter", 0.0)) * (values.get("height", 0.0))
    # 'simple' and any unknown type fall through to the app's default branch.
    return values.get("qty", 0.0)


def total_cost(formula_type: str, values: dict[str, float], cost_rate: float) -> float:
    return compute_quantity(formula_type, values) * cost_rate


def total_selling(
    formula_type: str, values: dict[str, float], selling_rate: float
) -> float:
    return compute_quantity(formula_type, values) * selling_rate

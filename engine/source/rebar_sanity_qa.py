"""kg/m3 QA helpers - sanity layer, not the accurate reinforcement implementation (generic).

Moved here from engine/bbs_steel.py (ratio_check) and engine/source/rebar_model.py (ratio_qa). The accurate BBS code
does not depend on them; the old names remain as deprecated wrappers (module __getattr__) that call this module and
warn. Nothing here produces, completes or changes a reinforcement quantity. Stdlib only.
"""

from __future__ import annotations

# kg/m3 sanity band (a check, not the quantity).
RATIO_YELLOW = (70.0, 200.0)
RATIO_RED = (40.0, 300.0)


def ratio_band_check(steel_kg: float, concrete_m3: float) -> dict:
    """Compare steel / concrete against the sanity band (QA only)."""
    if concrete_m3 <= 0:
        return {"ratio": None, "status": "n/a"}
    ratio = steel_kg / concrete_m3
    if ratio < RATIO_RED[0] or ratio > RATIO_RED[1]:
        status = "RED"
    elif ratio < RATIO_YELLOW[0] or ratio > RATIO_YELLOW[1]:
        status = "YELLOW"
    else:
        status = "OK"
    return {"ratio": ratio, "status": status, "band": {"yellow": RATIO_YELLOW, "red": RATIO_RED}}


def intensity_qa(kg, *, volume_m3=None, area_m2=None, n_elements=None) -> dict:
    """Reasonableness diagnostics only - the output never feeds a quantity."""
    return {"use": "QA_ONLY", "kg_per_m3": kg / volume_m3 if volume_m3 else None,
            "kg_per_m2": kg / area_m2 if area_m2 else None, "kg_per_element": kg / n_elements if n_elements else None}

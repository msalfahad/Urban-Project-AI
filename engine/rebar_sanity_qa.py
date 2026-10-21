"""kg/m3 QA helper - production-layer sanity check, not the reinforcement quantity.

Moved here from engine/bbs_steel.py (ratio_check). Production modules may not import engine.source (R8.1 / R8.2
boundary), and engine/source modules may import only the stdlib and engine.source, so the QA layer has one copy on
each side: this one for production (engine/__init__, the bbs_steel deprecated wrapper) and
engine/source/rebar_sanity_qa.py for the source layer. A parity test keeps the two identical. Nothing here produces,
completes or changes a reinforcement quantity. Stdlib only.
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

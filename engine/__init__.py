"""Urban Projects engine — deterministic code modules.

Everything in this package is pure arithmetic and rules: no model, no tokens,
identical every time. Agents read and explain; the engine calculates. Nothing
here calls an AI.
"""

from .units import Quantity, Unit, UnitError
from .unit_guard import TakeoffRecord, GuardResult, check, check_batch

__all__ = [
    "Quantity",
    "Unit",
    "UnitError",
    "TakeoffRecord",
    "GuardResult",
    "check",
    "check_batch",
]

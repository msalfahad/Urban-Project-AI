"""Urban Projects engine — deterministic code modules.

Everything in this package is pure arithmetic and rules: no model, no tokens,
identical every time. Agents read and explain; the engine calculates. Nothing
here calls an AI.
"""

from .units import Quantity, Unit, UnitError
from .unit_guard import TakeoffRecord, GuardResult, check, check_batch
from .boq_formula import compute_quantity, FIELDS_FOR
from .rate_library import RateLibrary, RateCategory, RateItem
from .audit_log import AuditLog, AuditEntry
from .pm_sync import (
    ApprovedBoqLine,
    measurement_to_formula,
    to_boq_item_doc,
    expected_quantity,
    sync_boq,
    firestore_writer,
)

__all__ = [
    "Quantity",
    "Unit",
    "UnitError",
    "TakeoffRecord",
    "GuardResult",
    "check",
    "check_batch",
    "compute_quantity",
    "FIELDS_FOR",
    "RateLibrary",
    "RateCategory",
    "RateItem",
    "AuditLog",
    "AuditEntry",
    "ApprovedBoqLine",
    "measurement_to_formula",
    "to_boq_item_doc",
    "expected_quantity",
    "sync_boq",
    "firestore_writer",
]

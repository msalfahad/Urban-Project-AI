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
from .alerts import Thresholds, Alert, check_variance, check_rate_age
from .waste import waste_factor, gross_quantity, family_of
from .cooling import floor_load, tons_for_area, select_units
from .preliminaries import preliminaries, PrelimRate
from .finance import FinanceReport, CostLine
from .estimate_actual import OutturnReport, TradeOutturn
from .bbs_steel import Bar, steel_from_bars, ratio_check
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
    "Thresholds",
    "Alert",
    "check_variance",
    "check_rate_age",
    "waste_factor",
    "gross_quantity",
    "family_of",
    "floor_load",
    "tons_for_area",
    "select_units",
    "preliminaries",
    "PrelimRate",
    "FinanceReport",
    "CostLine",
    "OutturnReport",
    "TradeOutturn",
    "Bar",
    "steel_from_bars",
    "ratio_check",
    "ApprovedBoqLine",
    "measurement_to_formula",
    "to_boq_item_doc",
    "expected_quantity",
    "sync_boq",
    "firestore_writer",
]

"""Phase 0 — the deterministic BOQ/Excel Auditor (E7).

No model, no tokens, no network. Pure arithmetic and rules over a takeoff or a
priced BOQ. This is the permanent exam every takeoff must pass — the same rules
that already found 15,181 KWD of defects in the current files.

The public surface:

    from engine.audit import audit_workbook, audit_rows, Severity

`audit_workbook(path)` loads an .xlsx and audits it. `audit_rows(rows)` audits an
already-parsed list of BoqRow (used in tests and when the rows come from
somewhere other than Excel).
"""

from .model import BoqRow, Issue, Severity, AuditReport
from .auditor import audit_rows, audit_workbook
from .rules import AuditConfig

__all__ = [
    "BoqRow",
    "Issue",
    "Severity",
    "AuditReport",
    "AuditConfig",
    "audit_rows",
    "audit_workbook",
]

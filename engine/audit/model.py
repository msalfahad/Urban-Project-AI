"""Data model for the Phase 0 auditor.

A `BoqRow` is the normalized form of one spreadsheet row, decoupled from Excel so
the rules never touch openpyxl. The Excel loader produces these; the rules
consume them; tests build them directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Traffic-light severity.

    RED    — blocks approval: a wrong number, a broken reference, a mixed total.
    YELLOW — must be reviewed: suspicious but not certainly wrong.
    GREEN  — informational / passed.
    """

    RED = "RED"
    YELLOW = "YELLOW"
    GREEN = "GREEN"

    @property
    def rank(self) -> int:
        return {"GREEN": 0, "YELLOW": 1, "RED": 2}[self.value]


@dataclass
class BoqRow:
    """One normalized BOQ line.

    Numeric fields are `None` when the cell was blank or unreadable — that is a
    meaningful state (a blank price is a defect), so it is never silently
    coerced to 0.
    """

    row_index: int                     # 1-based row number in the sheet
    sheet: str = ""
    description: str = ""
    unit: str = ""                     # raw unit label as written (m2, م2, no, ...)
    quantity: float | None = None
    unit_rate: float | None = None
    amount: float | None = None

    # Structural / formula metadata from the spreadsheet.
    amount_formula: str = ""           # e.g. "=E5*F5" or "=SUM(G5:G9)"
    quantity_formula: str = ""
    cell_errors: list[str] = field(default_factory=list)  # e.g. ["#REF!"]

    is_total_row: bool = False         # a subtotal / total / grand-total line
    # Rows a SUM covers, split by which column the SUM is in. Money totals sum
    # the amount column (mixing units there is normal); quantity totals sum the
    # quantity column (mixing units there is the 295.44 defect).
    amount_sum_rows: list[int] = field(default_factory=list)
    qty_sum_rows: list[int] = field(default_factory=list)
    section: str = ""                  # trade / package grouping if known

    # Convenience passthrough for rules that need the raw cells.
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_priced_line(self) -> bool:
        """A measured, priceable line (not a header or a total)."""
        return not self.is_total_row and bool(self.description.strip())


@dataclass
class Issue:
    """One finding against one row (or a group of rows)."""

    rule: str                          # rule id, e.g. "R05_mixed_units"
    severity: Severity
    message: str
    row_index: int | None = None
    sheet: str = ""
    detail: dict = field(default_factory=dict)
    estimated_kwd_impact: float | None = None

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
            "row_index": self.row_index,
            "sheet": self.sheet,
            "detail": self.detail,
            "estimated_kwd_impact": self.estimated_kwd_impact,
        }


@dataclass
class AuditReport:
    """The result of auditing a set of rows or a workbook."""

    issues: list[Issue] = field(default_factory=list)
    rows_checked: int = 0
    sheets: list[str] = field(default_factory=list)
    source: str = ""

    @property
    def status(self) -> Severity:
        """Overall verdict: RED if any red, else YELLOW if any yellow, else GREEN."""
        if any(i.severity is Severity.RED for i in self.issues):
            return Severity.RED
        if any(i.severity is Severity.YELLOW for i in self.issues):
            return Severity.YELLOW
        return Severity.GREEN

    @property
    def approved(self) -> bool:
        """A takeoff may only proceed with zero RED findings."""
        return self.status is not Severity.RED

    def counts(self) -> dict[str, int]:
        c = {"RED": 0, "YELLOW": 0, "GREEN": 0}
        for i in self.issues:
            c[i.severity.value] += 1
        return c

    def by_rule(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for i in self.issues:
            out[i.rule] = out.get(i.rule, 0) + 1
        return out

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "approved": self.approved,
            "rows_checked": self.rows_checked,
            "sheets": self.sheets,
            "source": self.source,
            "counts": self.counts(),
            "by_rule": self.by_rule(),
            "issues": [i.to_dict() for i in self.issues],
        }

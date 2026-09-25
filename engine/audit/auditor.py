"""Orchestrator: run every rule over the rows and assemble the report."""

from __future__ import annotations

from .model import BoqRow, AuditReport
from .rules import ALL_RULES, AuditConfig


def audit_rows(rows: list[BoqRow], config: AuditConfig | None = None, source: str = "") -> AuditReport:
    """Run all deterministic rules over already-parsed rows."""
    cfg = config or AuditConfig()
    issues = []
    for rule in ALL_RULES:
        issues.extend(rule(rows, cfg))
    # stable ordering: severity (RED first), then sheet, then row
    issues.sort(key=lambda i: (-i.severity.rank, i.sheet, i.row_index or 0, i.rule))
    sheets = sorted({r.sheet for r in rows})
    return AuditReport(
        issues=issues,
        rows_checked=len(rows),
        sheets=sheets,
        source=source,
    )


def audit_workbook(path: str, config: AuditConfig | None = None) -> AuditReport:
    """Load an .xlsx and audit it end to end."""
    from .excel_loader import load_rows

    rows = load_rows(path)
    return audit_rows(rows, config=config, source=path)

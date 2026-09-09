"""Render an AuditReport as human-readable text (for the terminal or Cowork).

Deterministic formatting only — no model. The traffic-light headline first, then
findings grouped RED → YELLOW, each pointing at a sheet and row a person can open.
"""

from __future__ import annotations

from .model import AuditReport, Severity

_ICON = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}


def render(report: AuditReport) -> str:
    counts = report.counts()
    lines: list[str] = []
    head = _ICON[report.status.value]
    lines.append(f"{head}  AUDIT {report.status.value}"
                 + ("  — approved (no blocking issues)" if report.approved
                    else "  — NOT approved: fix RED issues first"))
    if report.source:
        lines.append(f"    file: {report.source}")
    lines.append(f"    sheets: {', '.join(report.sheets) or '—'}   rows checked: {report.rows_checked}")
    lines.append(f"    RED {counts['RED']}   YELLOW {counts['YELLOW']}")
    lines.append("")

    def block(sev: Severity):
        group = [i for i in report.issues if i.severity is sev]
        if not group:
            return
        lines.append(f"{_ICON[sev.value]} {sev.value} ({len(group)})")
        for i in group:
            loc = ""
            if i.sheet or i.row_index:
                loc = f" [{i.sheet}" + (f":row {i.row_index}" if i.row_index else "") + "]"
            impact = ""
            if i.estimated_kwd_impact:
                impact = f"  (~{i.estimated_kwd_impact:+.2f} KWD)"
            lines.append(f"  • {i.rule}{loc}: {i.message}{impact}")
        lines.append("")

    block(Severity.RED)
    block(Severity.YELLOW)

    if report.approved and counts["YELLOW"] == 0:
        lines.append("No issues found. Takeoff passes the Phase 0 exam.")
    return "\n".join(lines).rstrip() + "\n"

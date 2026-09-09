"""Phase 0 flow: Excel/BOQ → audit → review/approve → structured BOQ → TEST write.

The one flow the owner asked for, end to end and deterministic. Two safety
properties are enforced in code, not by convention:

1. **Approval requires zero RED findings.** `approve()` raises unless the audit
   is clean of blocking issues and a human approver is named.

2. **Writes go only to a sandbox path.** `write_to_sandbox()` targets a
   dedicated `sandbox/` collection tree and refuses any path under `projects/`,
   so Phase 0 can never touch a production BOQ. Going live against the real
   `projects/{id}/boqItems` is a separate, deliberate step (E14), not this flow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from engine.audit import audit_workbook, audit_rows, AuditReport, Severity
from engine.audit.model import BoqRow
from engine.pm_sync import ApprovedBoqLine, to_boq_item_doc

# The sandbox collection tree. Deliberately NOT "projects" — the app's real BOQs
# live at projects/{id}/boqItems and this flow must never write there.
SANDBOX_ROOT = "sandbox"


class ApprovalError(RuntimeError):
    """Raised when an unapproved or RED takeoff is pushed toward a write."""


class SandboxViolation(RuntimeError):
    """Raised if a write is aimed anywhere but the sandbox tree."""


@dataclass
class CandidateLine:
    """A structured BOQ line drafted from an audited row, awaiting approval."""

    row_index: int
    sheet: str
    description: str
    unit: str
    quantity: float
    unit_rate: float


@dataclass
class ApprovedBoq:
    project_tag: str
    approver: str
    approved_at: datetime
    lines: list[CandidateLine] = field(default_factory=list)


def build_candidate_boq(rows: list[BoqRow]) -> list[CandidateLine]:
    """Draft structured lines from the priced (non-total) rows of a takeoff."""
    out: list[CandidateLine] = []
    for r in rows:
        if not r.is_priced_line:
            continue
        if r.quantity is None or r.unit_rate is None:
            continue
        out.append(CandidateLine(
            row_index=r.row_index,
            sheet=r.sheet,
            description=r.description,
            unit=r.unit,
            quantity=r.quantity,
            unit_rate=r.unit_rate,
        ))
    return out


def approve(
    report: AuditReport,
    candidate: list[CandidateLine],
    approver: str,
    project_tag: str,
) -> ApprovedBoq:
    """Gate: only a RED-free takeoff with a named human approver may proceed.

    YELLOW findings do not block (they are advisory), but RED does — matching the
    rule that a takeoff proceeds only with zero serious findings.
    """
    if not approver or not approver.strip():
        raise ApprovalError("an approver name is required to approve a takeoff")
    if report.status is Severity.RED:
        reds = [i.rule for i in report.issues if i.severity is Severity.RED]
        raise ApprovalError(
            f"cannot approve: {len(reds)} RED issue(s) must be fixed first ({', '.join(sorted(set(reds)))})"
        )
    if not candidate:
        raise ApprovalError("no priced lines to approve")
    return ApprovedBoq(
        project_tag=project_tag,
        approver=approver,
        approved_at=datetime.now(timezone.utc),
        lines=list(candidate),
    )


def sandbox_path(project_tag: str) -> str:
    """The sandbox collection an approved BOQ writes into."""
    return f"{SANDBOX_ROOT}/{project_tag}/boqItems"


def _line_to_doc(line: CandidateLine, project_tag: str, now: datetime) -> dict[str, Any]:
    # A quantity-only (simple) line: count = quantity, no dimensions → app computes qty directly.
    approved = ApprovedBoqLine(
        project_id=project_tag,
        group_id="sandbox",
        package_id="sandbox",
        package_name=line.sheet or "Sandbox",
        name=line.description,
        unit=line.unit,
        count=line.quantity,
        dimensions_m=[],
        cost_rate=line.unit_rate,
        selling_rate=0.0,
        notes=f"Phase 0 sandbox import from {line.sheet}:row {line.row_index}",
    )
    doc = to_boq_item_doc(approved, now=now)
    doc["_sandbox"] = True  # explicit marker so these are trivially identifiable/removable
    return doc


# A writer takes (collection_path, document) → id. Injected; firebase-admin in prod.
Writer = Callable[[str, dict], str]


def write_to_sandbox(approved: ApprovedBoq, writer: Writer, *, now: datetime | None = None) -> list[str]:
    """Write an approved BOQ to the sandbox tree only.

    Refuses any path outside `sandbox/`. Returns the ids written.
    """
    now = now or datetime.now(timezone.utc)
    path = sandbox_path(approved.project_tag)
    if not path.startswith(SANDBOX_ROOT + "/") or path.startswith("projects/"):
        raise SandboxViolation(f"refusing to write outside the sandbox: {path!r}")
    written = []
    for line in approved.lines:
        doc = _line_to_doc(line, approved.project_tag, now)
        written.append(writer(path, doc))
    return written


def run_phase0(path: str) -> tuple[AuditReport, list[CandidateLine]]:
    """Convenience: audit a workbook and draft its candidate BOQ in one call.

    Does NOT write anything — approval and writing are explicit later steps.
    """
    report = audit_workbook(path)
    from engine.audit.excel_loader import load_rows

    rows = load_rows(path)
    return report, build_candidate_boq(rows)

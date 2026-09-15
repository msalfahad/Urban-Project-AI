"""Phase 0 pipeline tests: approval gate + sandbox-only writes."""

import pytest

from engine.audit import audit_rows
from engine.audit.model import BoqRow
from pipeline.phase0 import (
    build_candidate_boq,
    approve,
    write_to_sandbox,
    sandbox_path,
    ApprovalError,
    SandboxViolation,
    ApprovedBoq,
    CandidateLine,
)
from datetime import datetime, timezone


def _clean_rows():
    return [
        BoqRow(row_index=2, sheet="S", description="Plaster", unit="m2", quantity=120, unit_rate=2.5, amount=300),
        BoqRow(row_index=3, sheet="S", description="Paint", unit="m2", quantity=120, unit_rate=1.0, amount=120),
        BoqRow(row_index=4, sheet="S", description="Total", is_total_row=True, amount=420, amount_sum_rows=[2, 3]),
    ]


def _red_rows():
    return [
        BoqRow(row_index=2, sheet="S", description="Plaster", unit="m2", quantity=120, unit_rate=2.5, amount=300),
        BoqRow(row_index=3, sheet="S", description="سيجما", unit="m2", quantity=1500, unit_rate=0, amount=0),
    ]


def test_build_candidate_skips_totals():
    cand = build_candidate_boq(_clean_rows())
    assert len(cand) == 2
    assert all(isinstance(c, CandidateLine) for c in cand)


def test_red_takeoff_cannot_be_approved():
    rows = _red_rows()
    report = audit_rows(rows)
    cand = build_candidate_boq(rows)
    with pytest.raises(ApprovalError):
        approve(report, cand, approver="Eng. Fahad", project_tag="TEST-alsenan")


def test_approver_name_required():
    rows = _clean_rows()
    report = audit_rows(rows)
    cand = build_candidate_boq(rows)
    with pytest.raises(ApprovalError):
        approve(report, cand, approver="", project_tag="TEST-alsenan")


def test_clean_takeoff_approves_and_writes_to_sandbox():
    rows = _clean_rows()
    report = audit_rows(rows)
    cand = build_candidate_boq(rows)
    approved = approve(report, cand, approver="Eng. Fahad", project_tag="TEST-alsenan")

    captured = []
    writer = lambda path, doc: captured.append((path, doc)) or f"id{len(captured)}"
    ids = write_to_sandbox(approved, writer)

    assert len(ids) == 2
    # Every write targets the sandbox tree, never projects/.
    assert all(p == "sandbox/TEST-alsenan/boqItems" for p, _ in captured)
    assert all(not p.startswith("projects/") for p, _ in captured)
    assert all(doc["_sandbox"] is True for _, doc in captured)


def test_write_refuses_non_sandbox_path():
    # Construct an approved BOQ whose tag would escape the sandbox root.
    bad = ApprovedBoq(
        project_tag="../projects/realproject",
        approver="x",
        approved_at=datetime.now(timezone.utc),
        lines=[CandidateLine(2, "S", "x", "m2", 1, 1)],
    )
    # sandbox_path still prefixes with sandbox/, but assert the guard holds for any
    # path that could resolve under projects/.
    with pytest.raises(SandboxViolation):
        # Force a violating path through a stubbed writer by monkey-free check:
        import pipeline.phase0 as p
        orig = p.sandbox_path
        p.sandbox_path = lambda tag: "projects/realproject/boqItems"
        try:
            write_to_sandbox(bad, lambda path, doc: "id")
        finally:
            p.sandbox_path = orig

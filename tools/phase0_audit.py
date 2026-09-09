"""Phase 0 CLI: audit a BOQ/takeoff Excel, and optionally test-write the result.

Examples
--------
Audit only (prints the RED/YELLOW/GREEN report):

    python3 -m tools.phase0_audit /path/to/alsenan_chalet.xlsx

Audit as machine-readable JSON:

    python3 -m tools.phase0_audit workbook.xlsx --json

Approve (only if no RED) and write to the TEST sandbox in Firestore:

    URBAN_ALLOW_SANDBOX_WRITE=1 URBAN_FIREBASE_SA=/path/sa.json \
    python3 -m tools.phase0_audit workbook.xlsx \
        --write-sandbox --project-tag TEST-alsenan --approver "Eng. Fahad"

Without the env vars, --write-sandbox does a dry run and prints what it *would*
write. Writes only ever target `sandbox/{tag}/boqItems`, never production.
"""

from __future__ import annotations

import argparse
import json
import sys

from engine.audit import audit_workbook
from engine.audit.report_text import render
from engine.audit.excel_loader import load_rows
from pipeline.phase0 import (
    build_candidate_boq, approve, write_to_sandbox, sandbox_path, ApprovalError,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Phase 0 deterministic BOQ auditor")
    ap.add_argument("workbook", help="path to the .xlsx takeoff/BOQ")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--write-sandbox", action="store_true",
                    help="approve (if no RED) and write to the TEST sandbox")
    ap.add_argument("--project-tag", default="TEST-sandbox",
                    help="sandbox project tag (writes go to sandbox/<tag>/boqItems)")
    ap.add_argument("--approver", default="", help="name of the human approver")
    args = ap.parse_args(argv)

    report = audit_workbook(args.workbook)

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render(report))

    if not args.write_sandbox:
        return 0 if report.approved else 1

    # Build + approve.
    rows = load_rows(args.workbook)
    candidate = build_candidate_boq(rows)
    try:
        approved = approve(report, candidate, approver=args.approver, project_tag=args.project_tag)
    except ApprovalError as exc:
        print(f"\n✋ Not writing: {exc}", file=sys.stderr)
        return 1

    dest = sandbox_path(approved.project_tag)
    # Try a live sandbox write; fall back to a dry run with a clear reason.
    try:
        from tools.firestore_sandbox import build_sandbox_writer, SandboxWriteDisabled
        try:
            writer = build_sandbox_writer()
        except SandboxWriteDisabled as exc:
            print(f"\n📝 DRY RUN → {dest} ({len(approved.lines)} lines). Live write off: {exc}")
            for l in approved.lines:
                print(f"   - {l.description} | {l.quantity:g} {l.unit} @ {l.unit_rate:g}")
            return 0
        ids = write_to_sandbox(approved, writer)
        print(f"\n✅ Wrote {len(ids)} lines to {dest} (sandbox, test-only).")
        return 0
    except Exception as exc:  # noqa: BLE001 — surface any live-write failure clearly
        print(f"\n⚠️  Sandbox write failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

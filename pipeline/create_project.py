"""Create a priced project — the "project creator" flow.

The step the owner described: after the takeoff is audited, a new project is
created in Urban Projects Manager under the client's name, priced with the
owner's own rates, with a programme attached — then the owner adjusts it by hand.

This module assembles that deterministically from pieces already built:
  - the audited trade quantities (from the حصر),
  - the Rate Library (E4) for the owner's rates,
  - the end-to-end trace (quantity → priced → web-app document),
  - the Schedule Engine (E12) for the programme.

It produces a `ProjectDraft`: the `projects/{id}` document, the priced
`boqItems`, and the programme summary — and can write them to the TEST sandbox
only (never a production project). The one human step, asking the client's name,
is the caller's (an A-agent, or the owner); everything here is code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Callable

from engine.rate_library import RateLibrary
from engine.schedule import schedule
from engine.schedule_template import reference_programme
from pipeline.end_to_end import TradeLine, TracedLine, trace
from pipeline.phase0 import sandbox_path, SANDBOX_ROOT, SandboxViolation


@dataclass
class ProjectDraft:
    project_tag: str
    client_name: str
    project_name: str
    location: str
    contract_form: str
    boq: list[TracedLine]
    total_cost: float
    programme_weeks: int | None
    project_doc: dict[str, Any]
    programme_rows: list[dict] = field(default_factory=list)

    def boq_item_docs(self) -> list[dict]:
        return [l.boq_item for l in self.boq]


def create_project(
    *,
    client_name: str,
    project_name: str,
    trade_lines: list[TradeLine],
    rates: RateLibrary,
    location: str = "",
    contract_form: str = "turnkey",
    schedule_quantities: dict | None = None,
    start_date: date | None = None,
    project_tag: str | None = None,
) -> ProjectDraft:
    """Assemble a priced project draft from audited quantities and rates."""
    if not client_name.strip():
        raise ValueError("client_name is required to create a project")
    tag = project_tag or ("TEST-" + project_name.strip().lower().replace(" ", "-"))[:60]

    traced = trace(trade_lines, rates, tag)
    total = sum(l.amount for l in traced if l.amount is not None)

    prog_weeks = None
    prog_rows: list[dict] = []
    if schedule_quantities is not None:
        prog = schedule(reference_programme(schedule_quantities), start_date=start_date)
        prog_weeks = prog.total_weeks
        prog_rows = prog.to_rows()

    now = datetime.now(timezone.utc)
    project_doc = {
        "name": project_name,
        "client": client_name,
        "location": location,
        "contractForm": contract_form,
        "status": "draft",
        "estimatedCost": total,
        "programmeWeeks": prog_weeks,
        "source": "phase0-takeoff",
        "isSandbox": True,
        "createdAt": now,
        "updatedAt": now,
    }
    return ProjectDraft(
        project_tag=tag,
        client_name=client_name,
        project_name=project_name,
        location=location,
        contract_form=contract_form,
        boq=traced,
        total_cost=total,
        programme_weeks=prog_weeks,
        project_doc=project_doc,
        programme_rows=prog_rows,
    )


# A writer takes (collection_path, doc) → id. Injected; firebase-admin in prod.
Writer = Callable[[str, dict], str]


def write_to_sandbox(draft: ProjectDraft, writer: Writer) -> dict[str, Any]:
    """Write the project doc + its priced BOQ to the TEST sandbox only.

    Refuses any path outside the `sandbox/` tree, so a production project can
    never be created by this flow. Returns the written ids.
    """
    proj_path = f"{SANDBOX_ROOT}/projects"
    boq_path = sandbox_path(draft.project_tag)  # sandbox/<tag>/boqItems
    for p in (proj_path, boq_path):
        if not p.startswith(SANDBOX_ROOT + "/") or p.startswith("projects/"):
            raise SandboxViolation(f"refusing to write outside the sandbox: {p!r}")

    project_id = writer(proj_path, {**draft.project_doc, "tag": draft.project_tag})
    boq_ids = [writer(boq_path, doc) for doc in draft.boq_item_docs()]
    return {"project_id": project_id, "boq_ids": boq_ids,
            "project_path": proj_path, "boq_path": boq_path}


def render_summary(draft: ProjectDraft) -> str:
    """A readable confirmation of what would be created."""
    lines = [
        f"NEW PROJECT (sandbox): {draft.project_name}",
        f"  client:   {draft.client_name}",
        f"  location: {draft.location or '—'}   form: {draft.contract_form}",
        f"  tag:      {draft.project_tag}",
        f"  programme: {draft.programme_weeks or '—'} weeks",
        "",
        f"  {'ITEM':28s} {'QTY':>10s} {'UNIT':5s} {'RATE':>7s} {'AMOUNT(KWD)':>12s}",
        "  " + "-" * 66,
    ]
    for l in draft.boq:
        rate = f"{l.rate:g}" if l.rate is not None else "—"
        amt = f"{l.amount:,.0f}" if l.amount is not None else "—"
        lines.append(f"  {l.trade[:28]:28s} {l.priced_qty:>10g} {l.unit:5s} {rate:>7s} {amt:>12s}")
    lines.append("  " + "-" * 66)
    lines.append(f"  {'ESTIMATED COST':>52s} {draft.total_cost:>12,.0f} KWD")
    return "\n".join(lines)

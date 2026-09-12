"""Turn what the system already holds into a `DocumentInput`.

Two sources, both already priced by code before they get here:

- a `ProjectDraft` from `pipeline.create_project` (takeoff -> rates -> programme);
- the web app's own `boqItems` documents, whose quantity the app computes from
  `formulaType` + `measurements` — reproduced here through `engine.boq_formula`
  so the figure on the quotation is the figure the app shows.

Nothing here invents a number. The client, the scopes and the reference come
from the caller; the money comes from the BOQ; the duration from the programme.
"""

from __future__ import annotations

from datetime import date

from agents.a7_quotation.schema import (
    DocumentInput, OwnerMaterial, Party, ProgrammeLine, ProjectFacts,
)
from engine.boq_formula import compute_quantity
from engine.documents import Milestone, PriceLine, summarise_by_package
from pipeline.create_project import ProjectDraft

# How the app's contract forms map onto document scopes.
FORM_SCOPES = {
    "black_structure": ["black_structure"],
    "finishing": ["finishing"],
    "turnkey": ["turnkey"],
}


def price_lines_from_draft(draft: ProjectDraft) -> list[PriceLine]:
    rows = [(l.trade, l.amount) for l in draft.boq if l.amount is not None]
    if not rows:
        raise ValueError("the draft has no priced lines")
    return summarise_by_package(rows)


def price_lines_from_boq_items(items: list[dict], rate_field: str = "sellingRate") -> list[PriceLine]:
    """Price lines from the app's `projects/{id}/boqItems` documents.

    Uses the selling rate by default — that is the client's price; the cost
    rate is the company's. Deleted items are skipped as the app skips them.
    """
    rows: list[tuple[str, float]] = []
    for item in items:
        if item.get("isDeleted"):
            continue
        package = item.get("packageName") or item.get("packageId") or ""
        qty = compute_quantity(item.get("formulaType", "simple"), item.get("measurements", {}))
        rate = float(item.get(rate_field) or 0.0)
        rows.append((package, qty * rate))
    if not rows:
        raise ValueError("no live BOQ items to price")
    lines = summarise_by_package(rows)
    if all(l.amount_kwd == 0 for l in lines):
        raise ValueError(f"every {rate_field} is zero — the BOQ is not priced for the client yet")
    return lines


def programme_from_draft(draft: ProjectDraft, starts_from: str, scope: str | None = None) -> list[ProgrammeLine]:
    if not draft.programme_weeks:
        return []
    return [ProgrammeLine(
        scope=scope or FORM_SCOPES.get(draft.contract_form, [draft.contract_form])[0],
        duration_days=draft.programme_weeks * 7,
        starts_from=starts_from,
    )]


def document_input_from_draft(
    draft: ProjectDraft,
    *,
    kind: str,
    reference: str,
    issued: date,
    client: Party,
    scopes: list[str] | None = None,
    location: str = "",
    description: str = "فيلا سكن خاص",
    floors: list[str] | None = None,
    built_area_m2: float | None = None,
    plot: str = "",
    programme_starts_from: str = "تاريخ صب اللبشة المسلحة",
    owner_materials: list[OwnerMaterial] | None = None,
    payment_milestones: list[Milestone] | None = None,
    special_requests: list[str] | None = None,
    extra_exclusions: list[str] | None = None,
    validity_days: int = 14,
) -> DocumentInput:
    project = ProjectFacts(
        name=draft.project_name,
        location=location or draft.location,
        scopes=scopes or FORM_SCOPES.get(draft.contract_form, [draft.contract_form]),
        description=description,
        plot=plot,
        floors=floors or [],
        built_area_m2=built_area_m2,
    )
    doc = DocumentInput(
        kind=kind,
        reference=reference,
        issued=issued,
        client=client,
        project=project,
        price_lines=price_lines_from_draft(draft),
        programme=programme_from_draft(draft, programme_starts_from),
        owner_materials=owner_materials or [],
        payment_milestones=payment_milestones or [],
        special_requests=special_requests or [],
        extra_exclusions=extra_exclusions or [],
        validity_days=validity_days,
    )
    doc.validate()
    return doc

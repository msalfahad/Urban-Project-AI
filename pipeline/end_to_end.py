"""End-to-end trace: drawing → takeoff → audit → priced → web-app document.

Ties the whole chain together for one project. Each `TradeLine` records where a
quantity came from (a drawing schedule), what the manual takeoff measured, its
audit status, the rate applied from the Rate Library (E4), and the resulting
priced line plus the exact `boqItems` document the web app reads.

The point the owner asked to see: information gathered from the DWG/PDF, compared
to the Excel حصر, priced with the owner's own rates, and shaped for Urban
Projects Manager — with every hop visible and every number traceable.

Deterministic: code prices and shapes; no AI computes a quantity or a total.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from engine.rate_library import RateLibrary
from engine.pm_sync import ApprovedBoqLine, to_boq_item_doc


@dataclass
class TradeLine:
    """One trade traced through the whole chain."""

    trade: str
    drawing_ref: str                 # where on the drawings this is verified
    takeoff_qty: float               # what the manual حصر measured
    unit: str                        # m3 | ton | m2 | ...
    rate_keyword: str                # how to find the rate in the Rate Library
    rate_unit: str | None = None
    priced_qty: float | None = None  # quantity actually priced (may differ: over-order)
    audit_status: str = ""           # GREEN / YELLOW / RED note from the auditor


@dataclass
class TracedLine:
    trade: str
    drawing_ref: str
    takeoff_qty: float
    priced_qty: float
    unit: str
    rate: float | None
    amount: float | None
    variance_pct: float | None
    audit_status: str
    boq_item: dict[str, Any]


def trace(
    lines: list[TradeLine],
    rates: RateLibrary,
    project_tag: str,
) -> list[TracedLine]:
    """Run every trade line through the chain, returning a full trace."""
    out: list[TracedLine] = []
    for ln in lines:
        rate = rates.rate_for(ln.rate_keyword, ln.rate_unit)
        priced_qty = ln.priced_qty if ln.priced_qty is not None else ln.takeoff_qty
        amount = rate * priced_qty if rate is not None else None
        variance = None
        if ln.takeoff_qty:
            variance = (priced_qty - ln.takeoff_qty) / ln.takeoff_qty * 100

        # The web-app document: a simple line carrying the priced quantity.
        doc = to_boq_item_doc(ApprovedBoqLine(
            project_id=project_tag,
            group_id="from-takeoff",
            package_id=ln.trade,
            package_name=ln.trade,
            name=f"{ln.trade} (drawing {ln.drawing_ref})",
            unit=ln.unit,
            count=priced_qty,
            dimensions_m=[],
            cost_rate=rate or 0.0,
            selling_rate=0.0,
            notes=f"takeoff {ln.takeoff_qty:g} {ln.unit}; audit {ln.audit_status}",
        ))
        out.append(TracedLine(
            trade=ln.trade,
            drawing_ref=ln.drawing_ref,
            takeoff_qty=ln.takeoff_qty,
            priced_qty=priced_qty,
            unit=ln.unit,
            rate=rate,
            amount=amount,
            variance_pct=variance,
            audit_status=ln.audit_status,
            boq_item=doc,
        ))
    return out


def render_trace(traced: list[TracedLine]) -> str:
    """A readable end-to-end table."""
    rows = [
        "TRADE            DRAWING        TAKEOFF     PRICED    UNIT   RATE     AMOUNT(KWD)  VAR    AUDIT",
        "-" * 100,
    ]
    total = 0.0
    for t in traced:
        amt = f"{t.amount:,.0f}" if t.amount is not None else "—"
        if t.amount:
            total += t.amount
        rate = f"{t.rate:g}" if t.rate is not None else "—"
        var = f"{t.variance_pct:+.1f}%" if t.variance_pct is not None else ""
        rows.append(
            f"{t.trade[:16]:16s} {t.drawing_ref[:13]:13s} {t.takeoff_qty:>8g} {t.priced_qty:>9g}"
            f"  {t.unit:4s}  {rate:>5s}  {amt:>10s}  {var:>6s}  {t.audit_status}"
        )
    rows.append("-" * 100)
    rows.append(f"{'TOTAL (traced trades)':>72s}  {total:>10,.0f} KWD")
    return "\n".join(rows)

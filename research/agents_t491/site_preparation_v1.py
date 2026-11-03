"""T-491 SITE_PREPARATION_V1 (research, unwired, stdlib only): the B1-01 site clearance and B1-07 preliminaries
components the owner listed on 2026-11-02 17:20 (note items (2) and (6)), as QUANTITIES ONLY (no rates, no prices).

Physical / contractual elements (ERS s.2.1), one row each:

- B1-01 SITE CLEARANCE (m2): removing vegetation, debris, loose obstructions and the surface layer from the area to be
  worked, before setting out. It is a surface operation on EXISTING ground. It is NOT formation compaction (B1-02 /
  B1-03, the compaction of the excavation formation and of each fill footprint, owned by the earthworks package
  T-350): the two are reported separately and never summed (owner 17:20 (2)).
- B1-07 PRELIMINARIES (temporary site facilities and project items, not permanent works):
  * SITE HOARDING / PROTECTION FENCE (lm): a temporary enclosure on the plot boundary for the construction period;
    gross length = the perimeter of the printed plot boundary; net length = gross less the width of every temporary
    site gate in it (the gate is its own item, by count).
  * GUARD CABIN OR TENT (nos x months), WATER TANKS (nos), WATER-TANKER TRIPS (trips per week x weeks), CONCRETE PUMP
    AND GENERATOR FOR POURS (pours / pour days from the structural pour sequence): logistics and duration items;
    a duration comes only from a project programme, a count only from a site logistics plan, pour sequence or
    contract. Never a default duration or count (no-assumptions rule).
  * TEMPORARY POWER: generator fuel OR a government temporary electricity connection, one or the other, from the
    project. Both at once is refused; neither stated stays HELD.
  * SITE AND WORKERS INSURANCE (item, by contract): present only when the contract puts it in the contractor's scope.
  * SITE HANDOVER with the Municipality and the contracting office (item): one per project (owner 17:20 (6) names it
    as an item, without a contract condition).

Statuses (WORKFLOW_CONTROLS s.5 / ERS s.2 step 6 vocabulary): DRAWING-CONFIRMED (every input printed or measured on
the drawing), PROJECT-SOURCED (from a stated project document: programme, logistics plan, pour sequence, contract;
resolution-order level 'project requirements'), ASSUMED - OWNER-APPROVED (an owner-defined item), HELD (a named input missing; quantity None, never 0,
with the formula and, where the drawing bounds it, an AT_MOST value), NOT_APPLICABLE (the exclusive alternative not
chosen), REFUSED (contradictory input).

Rules (proposed, any villa; provenance T-491, owner 2026-11-02 17:20 notes (2) and (6), Q-21 C, T-357 R-PLOT-1):
R-T491-FENCE-1 hoarding gross lm = perimeter of the printed plot boundary polygon (declared unit); net lm = gross -
  sum of the temporary gate widths; gates are a separate count; with gate count or width unknown the net is HELD with
  AT_MOST = gross (never gross reported as net, never a default gate width).
R-T491-CLR-1 site clearance is in scope when the owner rule or a printed scope puts it there (owner 17:20 (6) for
  every villa); its extent is the plot inside the printed boundary (shoelace area, T-357 R-PLOT-1) unless the
  drawings or the contract print a smaller or larger clearance limit; it is reported apart from formation and fill
  compaction footprints and never summed with them. This SUPERSEDES the T-357 R-CLR-1 'no printed scope -> no line'
  outcome only for scope (R-CLR-1 still refuses a convention extent such as plot minus footprint or a 1 m margin).
R-T491-DUR-1 a duration-driven quantity = count x duration (or rate x duration) only when both come from a project
  source (programme, logistics plan, pour sequence, contract); otherwise HELD with the formula and the missing
  inputs named; a programme duration is never defaulted.
R-T491-PWR-1 temporary power is exactly one of GENERATOR_FUEL or GOVERNMENT_TEMPORARY_CONNECTION, from the project;
  both -> REFUSED, neither -> HELD; the alternative not chosen is NOT_APPLICABLE (never a second line).
R-T491-ITEM-1 a contract-conditional item (insurance) is HELD until the contract states it; an owner-defined
  per-project item (site handover) is 1 item.
"""
from __future__ import annotations

import math
from typing import Iterable, Optional

UNIT_FACTOR = {"m": 1.0, "cm": 0.01, "mm": 0.001}
POWER_OPTIONS = ("GENERATOR_FUEL", "GOVERNMENT_TEMPORARY_CONNECTION")
RULES_SOURCE = "owner 2026-11-02 17:20 notes (2) and (6); Q-21 C; T-357 R-PLOT-1"
TOL = 1e-9


class RefusedInput(ValueError):
    """An input the rules refuse (undeclared unit, open polygon, gates longer than the boundary, two power sources)."""


def _factor(unit: str) -> float:
    if unit not in UNIT_FACTOR:
        raise RefusedInput(f"undeclared or unknown unit {unit!r}")
    return UNIT_FACTOR[unit]


def _polygon_m(polygon: Iterable, unit: str) -> list:
    f = _factor(unit)
    pts = [(float(x) * f, float(y) * f) for x, y in polygon]
    if len(pts) >= 2 and math.isclose(pts[0][0], pts[-1][0]) and math.isclose(pts[0][1], pts[-1][1]):
        pts = pts[:-1]  # explicit closing vertex
    if len(pts) < 3:
        raise RefusedInput("a plot boundary needs at least three distinct vertices")
    return pts


def perimeter(polygon: Iterable, unit: str = "m") -> float:
    pts = _polygon_m(polygon, unit)
    return sum(math.dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))


def shoelace_area(polygon: Iterable, unit: str = "m") -> float:
    pts = _polygon_m(polygon, unit)
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    area = abs(a) / 2.0
    if area <= TOL:
        raise RefusedInput("degenerate plot boundary (zero area)")
    return area


def _row(component, family, unit, quantity, status, formula, source, missing=None, at_most=None, note=""):
    if quantity is None and status not in ("HELD", "NOT_APPLICABLE", "REFUSED"):
        raise AssertionError(f"{component}: a quantity of None must be HELD / NOT_APPLICABLE / REFUSED")
    if status == "HELD" and quantity is not None:
        raise AssertionError(f"{component}: a HELD row carries no quantity")
    return {
        "component": component,
        "family": family,
        "unit": unit,
        "quantity": None if quantity is None else round(float(quantity), 6),
        "status": status,
        "formula": formula,
        "source": source,
        "missing": list(missing or []),
        "at_most": None if at_most is None else round(float(at_most), 6),
        "note": note,
    }


def hoarding(polygon, unit="m", gate_widths: Optional[list] = None, boundary_source="printed plot boundary",
             boundary_status="DRAWING-CONFIRMED") -> list:
    """Fence gross / net lm and the gate count (R-T491-FENCE-1). gate_widths: None = not known (HELD); [] = the
    project source states no temporary gate; [w, ...] = widths in the same declared unit."""
    gross = perimeter(polygon, unit)
    rows = [_row("HOARDING_GROSS_BOUNDARY", "B1-07", "lm", gross, boundary_status,
                 "perimeter of the plot boundary polygon", boundary_source,
                 note="gross boundary length; a reference length, not the payable fence when gates exist")]
    if gate_widths is None:
        rows.append(_row("HOARDING_FENCE_NET", "B1-07", "lm", None, "HELD",
                         "gross boundary - sum(temporary gate widths)", boundary_source,
                         missing=["temporary site gate count and widths (site logistics plan / contract)"],
                         at_most=gross))
        rows.append(_row("HOARDING_GATES", "B1-07", "nos", None, "HELD", "count of temporary site gates",
                         "site logistics plan / contract", missing=["temporary site gate count"]))
        return rows
    f = _factor(unit)
    widths = [float(w) * f for w in gate_widths]
    if any(w <= 0 for w in widths):
        raise RefusedInput("a gate width must be positive")
    if sum(widths) >= gross - TOL:
        raise RefusedInput("the gates are as long as or longer than the boundary")
    rows.append(_row("HOARDING_FENCE_NET", "B1-07", "lm", gross - sum(widths), boundary_status,
                     "gross boundary - sum(temporary gate widths)", boundary_source + " + stated gates"))
    rows.append(_row("HOARDING_GATES", "B1-07", "nos", len(widths), boundary_status,
                     "count of temporary site gates", "stated gates"))
    return rows


def site_clearance(polygon, unit="m", in_scope_source: Optional[str] = None, printed_limit_m2: Optional[float] = None,
                   boundary_status="DRAWING-CONFIRMED") -> dict:
    """B1-01 clearance m2 (R-T491-CLR-1). in_scope_source: the owner rule or printed scope (None -> HELD: no scope).
    printed_limit_m2: a clearance limit printed on the drawings / contract (wins over the plot extent)."""
    if not in_scope_source:
        return _row("SITE_CLEARANCE", "B1-01", "m2", None, "HELD", "plot area inside the printed boundary",
                    "none", missing=["a printed scope or owner rule putting clearance in scope"])
    if printed_limit_m2 is not None:
        if printed_limit_m2 <= 0:
            raise RefusedInput("a printed clearance limit must be positive")
        return _row("SITE_CLEARANCE", "B1-01", "m2", printed_limit_m2, "DRAWING-CONFIRMED",
                    "printed clearance limit", in_scope_source)
    return _row("SITE_CLEARANCE", "B1-01", "m2", shoelace_area(polygon, unit), boundary_status,
                "shoelace area of the printed plot boundary (extent R-T491-CLR-1)", in_scope_source,
                note="geometry DRAWING-CONFIRMED; extent rule R-T491-CLR-1 PROPOSED (release only after the Lead adopts it "
                     "as a rule version); reported apart from formation / fill compaction footprints (owner 17:20 (2)), "
                     "never summed")


def formation_compaction_reference(owner_package: str = "T-350 earthworks") -> dict:
    """Formation and fill compaction m2 belong to the earthworks package; this row only records the separation."""
    return _row("FORMATION_COMPACTION", "B1-02/B1-03", "m2", None, "HELD",
                "formation + fill compaction footprints per zone (owner 17:20 (2))", owner_package,
                missing=[f"measured in {owner_package}, not here (separate from site clearance)"])


def duration_item(component, family, unit, count=None, duration=None, count_source=None, duration_source=None,
                  count_label="count", duration_label="duration", formula=None,
                  count_hint="site logistics plan / contract") -> dict:
    """count x duration (R-T491-DUR-1). A None input, or one without its source, keeps the row HELD."""
    formula = formula or f"{count_label} x {duration_label}"
    missing = []
    if count is None or not count_source:
        missing.append(f"{count_label} (source: {count_hint})")
    if duration is None or not duration_source:
        missing.append(f"{duration_label} (source: project programme)")
    if missing:
        return _row(component, family, unit, None, "HELD", formula, "none", missing=missing)
    if count < 0 or duration < 0:
        raise RefusedInput(f"{component}: negative count or duration")
    return _row(component, family, unit, float(count) * float(duration), "PROJECT-SOURCED",
                formula, f"{count_source}; {duration_source}")


def count_item(component, family, unit, count=None, count_source=None, label="count",
               source_hint="site logistics plan / contract") -> dict:
    if count is None or not count_source:
        return _row(component, family, unit, None, "HELD", label, "none",
                    missing=[f"{label} (source: {source_hint})"])
    if count < 0:
        raise RefusedInput(f"{component}: negative count")
    return _row(component, family, unit, count, "PROJECT-SOURCED", label, count_source)


def temporary_power(chosen: Optional[Iterable[str]] = None, source: Optional[str] = None) -> list:
    """R-T491-PWR-1: exactly one of the two, from the project."""
    chosen = list(chosen or [])
    bad = [c for c in chosen if c not in POWER_OPTIONS]
    if bad:
        raise RefusedInput(f"unknown temporary power option {bad}")
    if len(set(chosen)) > 1:
        raise RefusedInput("temporary power: generator fuel AND government connection both stated (one or the other)")
    if not chosen or not source:
        return [_row(o, "B1-07", "item", None, "HELD", "one of GENERATOR_FUEL / GOVERNMENT_TEMPORARY_CONNECTION",
                     "none", missing=["the project's temporary power choice (contract / authority application)"])
                for o in POWER_OPTIONS]
    return [_row(o, "B1-07", "item", 1 if o == chosen[0] else None,
                 "PROJECT-SOURCED" if o == chosen[0] else "NOT_APPLICABLE",
                 "one of GENERATOR_FUEL / GOVERNMENT_TEMPORARY_CONNECTION", source) for o in POWER_OPTIONS]


def insurance(contract_includes: Optional[bool] = None, contract_source: Optional[str] = None) -> dict:
    if contract_includes is None or not contract_source:
        return _row("SITE_AND_WORKERS_INSURANCE", "B1-07", "item", None, "HELD", "1 item when the contract includes it",
                    "none", missing=["contract clause on site / workers insurance"])
    if not contract_includes:
        return _row("SITE_AND_WORKERS_INSURANCE", "B1-07", "item", None, "NOT_APPLICABLE",
                    "1 item when the contract includes it", contract_source)
    return _row("SITE_AND_WORKERS_INSURANCE", "B1-07", "item", 1, "PROJECT-SOURCED",
                "1 item when the contract includes it", contract_source)


def site_handover() -> dict:
    return _row("SITE_HANDOVER_MUNICIPALITY_AND_OFFICE", "B1-07", "item", 1, "ASSUMED - OWNER-APPROVED",
                "1 item per project", "owner 2026-11-02 17:20 (6): named as an item, no contract condition")


def site_preparation(project: dict) -> list:
    """All components for one project. project keys (all optional except the plot): plot_polygon, unit,
    boundary_source, boundary_status, gate_widths, clearance_scope_source, clearance_limit_m2, programme (dict of
    durations with 'source'), logistics (dict of counts with 'source'), pour_sequence (dict with pours, pour_days,
    source), temporary_power ([choice], source), insurance (bool, source)."""
    poly, unit = project["plot_polygon"], project.get("unit", "m")
    bsrc = project.get("boundary_source", "printed plot boundary")
    bst = project.get("boundary_status", "DRAWING-CONFIRMED")
    prog = project.get("programme") or {}
    log = project.get("logistics") or {}
    pours = project.get("pour_sequence") or {}
    rows = [site_clearance(poly, unit, project.get("clearance_scope_source"), project.get("clearance_limit_m2"), bst),
            formation_compaction_reference()]
    rows += hoarding(poly, unit, project.get("gate_widths"), bsrc, bst)
    rows.append(duration_item("GUARD_CABIN_OR_TENT", "B1-07", "nos x months", log.get("guard_cabins"),
                              prog.get("construction_months"), log.get("source"), prog.get("source"),
                              "cabins / tents (nos)", "construction months"))
    rows.append(count_item("WATER_TANKS", "B1-07", "nos", log.get("water_tanks"), log.get("source"),
                           "water tanks (nos)"))
    rows.append(duration_item("WATER_TANKER_TRIPS", "B1-07", "trips", log.get("tanker_trips_per_week"),
                              prog.get("water_weeks"), log.get("source"), prog.get("source"),
                              "trips per week", "weeks of water use"))
    rows.append(count_item("CONCRETE_PUMP_POURS", "B1-07", "pours", pours.get("pumped_pours"), pours.get("source"),
                           "pumped pours", "structural pour sequence / pour plan"))
    rows.append(count_item("POUR_GENERATOR_DAYS", "B1-07", "days", pours.get("pour_days"), pours.get("source"),
                           "pour days", "structural pour sequence / pour plan"))
    tp = project.get("temporary_power") or {}
    rows += temporary_power(tp.get("choice"), tp.get("source"))
    ins = project.get("insurance") or {}
    rows.append(insurance(ins.get("included"), ins.get("source")))
    rows.append(site_handover())
    return rows

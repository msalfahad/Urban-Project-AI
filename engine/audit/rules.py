"""The deterministic audit rules.

Every rule is a pure function of the parsed rows (plus config). No model, no
network, no randomness — the same workbook produces the same findings every
time. Each rule returns a list of Issue.

Coverage (the checklist the owner asked for, plus extras):

  R01  #REF! and other Excel errors ................ RED
  R02  blank / zero prices on a priced line ......... RED
  R03  amount != quantity x rate (formula error) .... RED
  R04  rounded unit-rate discrepancy ................ YELLOW
  R05  mixed units summed into one total ............ RED
  R06  total != sum of its rows ..................... RED
  R07  SUM range skips a row in the section ......... RED
  R08  concrete classification problems ............. YELLOW
  R09  steel-to-concrete ratio anomaly .............. YELLOW/RED
  R10  material line with no waste/order allowance .. YELLOW
  R11  negative or zero quantity .................... YELLOW
  R12  missing / unrecognised unit .................. YELLOW
  R13  duplicated line (possible double count) ...... YELLOW
  R14  unit-rate outlier vs like items .............. YELLOW
  R15  unit does not match its dimensions (E1) ...... RED
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from .model import BoqRow, Issue, Severity
from . import refdata

EXCEL_ERROR_TOKENS = ["#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NUM!", "#NULL!"]


@dataclass
class AuditConfig:
    amount_tolerance_rel: float = 0.005   # 0.5% relative tolerance on TOTALS (many rows round)
    amount_tolerance_abs: float = 0.010   # absolute floor (KWD) so tiny lines aren't noise
    # Per-line amount = qty x rate is held to a tight tolerance: 2-decimal
    # rounding passes, but a whole-dinar (or larger) gap is surfaced.
    line_amount_abs_tol: float = 0.01
    line_amount_rel_tol: float = 0.0005
    rounded_rate_rel: float = 0.02        # up to 2% counts as a rounding discrepancy (YELLOW), above is RED
    outlier_factor: float = 3.0           # rate > factor x median (or < median/factor)
    steel_red_min: float = refdata.STEEL_RATIO_RED_MIN
    steel_yellow_min: float = refdata.STEEL_RATIO_YELLOW_MIN
    steel_yellow_max: float = refdata.STEEL_RATIO_YELLOW_MAX
    steel_red_max: float = refdata.STEEL_RATIO_RED_MAX


# ---- helpers ------------------------------------------------------------

def _norm_desc(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _has(text: str, keywords: list[str]) -> bool:
    t = text.lower()
    return any(k.lower() in t for k in keywords)


def _contributing_rows(total: BoqRow, rows: list[BoqRow], explicit: list[int] | None) -> list[BoqRow]:
    """Rows that feed a total.

    Prefer the explicit SUM range (for the relevant column); otherwise the priced
    rows since the previous total on the same sheet (implicit section grouping).
    """
    same_sheet = [r for r in rows if r.sheet == total.sheet]
    if explicit:
        wanted = set(explicit)
        return [r for r in same_sheet if r.row_index in wanted]
    return _implicit_section_rows(total, rows)


def _close(a: float, b: float, cfg: AuditConfig) -> bool:
    return abs(a - b) <= max(cfg.amount_tolerance_abs, cfg.amount_tolerance_rel * max(abs(a), abs(b), 1.0))


# ---- rules --------------------------------------------------------------

def r01_ref_errors(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    for r in rows:
        found = [e for e in r.cell_errors if e in EXCEL_ERROR_TOKENS]
        # also scan formulas/description text for error tokens
        for token in EXCEL_ERROR_TOKENS:
            if token in r.amount_formula or token in r.quantity_formula or token in (r.description or ""):
                if token not in found:
                    found.append(token)
        if found:
            issues.append(Issue(
                rule="R01_excel_error", severity=Severity.RED,
                message=f"Excel error {', '.join(found)} in row — the number here cannot be trusted.",
                row_index=r.row_index, sheet=r.sheet, detail={"errors": found},
            ))
    return issues


def r02_blank_price(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    """Blank/zero price on a priced line.

    Only applies to *priced* sheets. A pure takeoff sheet (quantities only, no
    rates anywhere) is not missing prices — it just hasn't been priced yet — so
    those sheets are skipped to avoid false positives.
    """
    priced_sheets = {
        r.sheet for r in rows
        if r.is_priced_line and r.unit_rate is not None and r.unit_rate > 0
    }
    issues = []
    for r in rows:
        if not r.is_priced_line or r.sheet not in priced_sheets:
            continue
        if r.quantity is not None and r.quantity > 0:
            if r.unit_rate is None or r.unit_rate == 0:
                issues.append(Issue(
                    rule="R02_blank_price", severity=Severity.RED,
                    message=f"Priced line has quantity {r.quantity:g} but a blank/zero rate — this line contributes nothing to the price.",
                    row_index=r.row_index, sheet=r.sheet,
                    detail={"quantity": r.quantity, "description": r.description},
                ))
    return issues


def r03_r04_amount_vs_qty_rate(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    for r in rows:
        if r.is_total_row:
            continue
        if r.quantity is None or r.unit_rate is None or r.amount is None:
            continue
        expected = r.quantity * r.unit_rate
        line_tol = max(cfg.line_amount_abs_tol, cfg.line_amount_rel_tol * max(abs(expected), 1.0))
        if abs(expected - r.amount) <= line_tol:
            continue
        rel = abs(r.amount - expected) / max(abs(expected), 1e-9)
        impact = r.amount - expected
        if rel <= cfg.rounded_rate_rel:
            issues.append(Issue(
                rule="R04_rounded_rate_discrepancy", severity=Severity.YELLOW,
                message=(f"Amount {r.amount:g} differs from quantity x rate "
                         f"({r.quantity:g} x {r.unit_rate:g} = {expected:g}) by {rel*100:.2f}% — "
                         "likely a rounded rate; confirm which is authoritative."),
                row_index=r.row_index, sheet=r.sheet,
                detail={"amount": r.amount, "expected": expected, "quantity": r.quantity, "rate": r.unit_rate},
                estimated_kwd_impact=impact,
            ))
        else:
            issues.append(Issue(
                rule="R03_amount_formula_error", severity=Severity.RED,
                message=(f"Amount {r.amount:g} does not equal quantity x rate "
                         f"({r.quantity:g} x {r.unit_rate:g} = {expected:g})."),
                row_index=r.row_index, sheet=r.sheet,
                detail={"amount": r.amount, "expected": expected, "quantity": r.quantity, "rate": r.unit_rate},
                estimated_kwd_impact=impact,
            ))
    return issues


def r05_r06_r07_totals(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    for total in rows:
        if not total.is_total_row:
            continue

        # R05 — mixed units in a QUANTITY subtotal (the 295.44 defect).
        # Summing the money/amount column across different-unit lines is normal;
        # summing the QUANTITY column across different units is meaningless.
        qty_contributors = None
        if total.qty_sum_rows:
            qty_contributors = _contributing_rows(total, rows, total.qty_sum_rows)
        elif total.quantity is not None and not total.amount_sum_rows:
            # A hand-typed quantity total: check the implicit section only if the
            # total lives in the quantity column (no amount SUM present).
            qty_contributors = _implicit_section_rows(total, rows)
        if qty_contributors:
            units = {refdata.canonical_unit(c.unit) for c in qty_contributors if c.unit}
            units.discard("")
            if len(units) > 1:
                issues.append(Issue(
                    rule="R05_mixed_units", severity=Severity.RED,
                    message=(f"A quantity total sums rows of different units "
                             f"({', '.join(sorted(units))}) — the result is dimensionally "
                             "meaningless (the classic 295.44 defect)."),
                    row_index=total.row_index, sheet=total.sheet,
                    detail={"units": sorted(units), "rows": [c.row_index for c in qty_contributors]},
                ))

        # Money-total checks operate on the amount column.
        contributors = _contributing_rows(total, rows, total.amount_sum_rows)
        if not contributors:
            continue

        # R06 — total value vs sum of contributor amounts
        amounts = [c.amount for c in contributors if c.amount is not None]
        if total.amount is not None and amounts:
            s = sum(amounts)
            if not _close(s, total.amount, cfg):
                issues.append(Issue(
                    rule="R06_sum_mismatch", severity=Severity.RED,
                    message=f"Total {total.amount:g} does not equal the sum of its rows ({s:g}).",
                    row_index=total.row_index, sheet=total.sheet,
                    detail={"stated_total": total.amount, "computed_sum": s},
                    estimated_kwd_impact=total.amount - s,
                ))

        # R07 — an amount SUM formula that skips a priced row in the section
        if total.amount_sum_rows:
            covered = set(total.amount_sum_rows)
            implicit = _implicit_section_rows(total, rows)
            skipped = [r for r in implicit if r.row_index not in covered and r.amount not in (None, 0)]
            if skipped:
                issues.append(Issue(
                    rule="R07_skipped_sum_row", severity=Severity.RED,
                    message=(f"The SUM leaves out {len(skipped)} priced row(s) in this section "
                             f"(rows {', '.join(str(r.row_index) for r in skipped)}) — the total is understated."),
                    row_index=total.row_index, sheet=total.sheet,
                    detail={"skipped_rows": [r.row_index for r in skipped]},
                    estimated_kwd_impact=-sum(r.amount for r in skipped if r.amount),
                ))
    return issues


def _implicit_section_rows(total: BoqRow, rows: list[BoqRow]) -> list[BoqRow]:
    same_sheet = [r for r in rows if r.sheet == total.sheet]
    out: list[BoqRow] = []
    for r in sorted(same_sheet, key=lambda x: x.row_index):
        if r.row_index >= total.row_index:
            break
        if r.is_total_row:
            out = []
        elif r.is_priced_line:
            out.append(r)
    return out


def r08_concrete_classification(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    for r in rows:
        if not r.is_priced_line:
            continue
        desc = r.description or ""
        if not _has(desc, refdata.CONCRETE_KEYWORDS):
            continue
        grade = refdata.extract_grade(desc)
        is_lean = _has(desc, refdata.LEAN_KEYWORDS)
        is_structural_element = _has(desc, refdata.STRUCTURAL_ELEMENT_KEYWORDS)

        problem = None
        if grade and grade not in refdata.ALL_GRADES:
            problem = f"unrecognised concrete grade {grade}"
        elif is_structural_element and grade and grade in refdata.LEAN_GRADES:
            problem = f"structural element specified with lean-concrete grade {grade}"
        elif is_lean and is_structural_element:
            problem = "row mixes lean/blinding wording with a structural element"
        elif is_structural_element and not grade:
            problem = "structural concrete element with no grade stated"

        if problem:
            issues.append(Issue(
                rule="R08_concrete_classification", severity=Severity.YELLOW,
                message=f"Concrete classification: {problem}.",
                row_index=r.row_index, sheet=r.sheet,
                detail={"grade": grade, "lean": is_lean, "structural": is_structural_element,
                        "description": desc},
            ))
    return issues


def r09_steel_ratio(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    """Steel (kg) per concrete (m3), computed per sheet where both are present."""
    issues = []
    sheets = {r.sheet for r in rows}
    for sheet in sheets:
        srows = [r for r in rows if r.sheet == sheet and r.is_priced_line]
        steel_kg = sum(
            (r.quantity or 0) for r in srows
            if refdata.canonical_unit(r.unit) == "weight"
            and _has(r.description or "", ["steel", "rebar", "reinforc", "حديد", "تسليح"])
        )
        conc_m3 = sum(
            (r.quantity or 0) for r in srows
            if refdata.canonical_unit(r.unit) == "volume"
            and _has(r.description or "", refdata.CONCRETE_KEYWORDS)
        )
        if steel_kg <= 0 or conc_m3 <= 0:
            continue
        ratio = steel_kg / conc_m3
        sev = None
        if ratio < cfg.steel_red_min or ratio > cfg.steel_red_max:
            sev = Severity.RED
        elif ratio < cfg.steel_yellow_min or ratio > cfg.steel_yellow_max:
            sev = Severity.YELLOW
        if sev:
            issues.append(Issue(
                rule="R09_steel_ratio", severity=sev,
                message=(f"Steel-to-concrete ratio {ratio:.0f} kg/m3 on sheet '{sheet}' is outside the "
                         f"expected band ({cfg.steel_yellow_min:.0f}-{cfg.steel_yellow_max:.0f}) — "
                         "check for a units error or a steel/concrete mismatch."),
                sheet=sheet, detail={"steel_kg": steel_kg, "concrete_m3": conc_m3, "ratio": ratio},
            ))
    return issues


def r10_missing_waste(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    """One low-noise flag per material family with no waste/order allowance anywhere."""
    issues = []
    text_all = " ".join((r.description or "") for r in rows).lower()
    has_waste_line = _has(text_all, ["waste", "هالك", "order qty", "كمية الطلب", "allowance"])
    families = [k for k in refdata.WASTE_EXPECTED_KEYWORDS if k.lower() in text_all]
    if families and not has_waste_line:
        issues.append(Issue(
            rule="R10_missing_waste", severity=Severity.YELLOW,
            message=("Material lines are present (e.g. " + ", ".join(sorted(set(families))[:4]) +
                     ") but no waste / order quantity appears anywhere — margin usually leaks here."),
            detail={"families": sorted(set(families))},
        ))
    return issues


def r11_negative_or_zero_qty(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    for r in rows:
        if r.is_priced_line and r.quantity is not None and r.quantity <= 0:
            issues.append(Issue(
                rule="R11_nonpositive_quantity", severity=Severity.YELLOW,
                message=f"Priced line has a non-positive quantity ({r.quantity:g}).",
                row_index=r.row_index, sheet=r.sheet, detail={"quantity": r.quantity},
            ))
    return issues


def r12_missing_unit(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    for r in rows:
        if not r.is_priced_line or r.quantity is None:
            continue
        if not r.unit or refdata.canonical_unit(r.unit) == "":
            issues.append(Issue(
                rule="R12_missing_unit", severity=Severity.YELLOW,
                message=f"Measured line has quantity {r.quantity:g} but a missing/unrecognised unit "
                        f"({r.unit!r}).",
                row_index=r.row_index, sheet=r.sheet, detail={"unit": r.unit},
            ))
    return issues


def r13_duplicate_line(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    seen: dict[tuple, BoqRow] = {}
    for r in rows:
        if not r.is_priced_line or not r.description.strip():
            continue
        key = (_norm_desc(r.description), refdata.canonical_unit(r.unit))
        if key in seen:
            first = seen[key]
            issues.append(Issue(
                rule="R13_duplicate_line", severity=Severity.YELLOW,
                message=f"Line duplicates row {first.row_index} ('{r.description.strip()}') — possible double count.",
                row_index=r.row_index, sheet=r.sheet, detail={"first_row": first.row_index},
            ))
        else:
            seen[key] = r
    return issues


def r14_outlier_rate(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    issues = []
    groups: dict[str, list[BoqRow]] = {}
    for r in rows:
        if r.is_priced_line and r.unit_rate not in (None, 0):
            groups.setdefault(_norm_desc(r.description), []).append(r)
    for desc, grp in groups.items():
        if len(grp) < 3:
            continue
        rates = [r.unit_rate for r in grp]
        med = statistics.median(rates)
        if med <= 0:
            continue
        for r in grp:
            if r.unit_rate > med * cfg.outlier_factor or r.unit_rate < med / cfg.outlier_factor:
                issues.append(Issue(
                    rule="R14_rate_outlier", severity=Severity.YELLOW,
                    message=f"Unit rate {r.unit_rate:g} is far from the median {med:g} for like items.",
                    row_index=r.row_index, sheet=r.sheet,
                    detail={"rate": r.unit_rate, "median": med},
                ))
    return issues


def r15_unit_algebra(rows: list[BoqRow], cfg: AuditConfig) -> list[Issue]:
    """Reuse E1 Unit Guard when a row carries explicit dimensions in raw."""
    from engine.units import Quantity, Unit
    from engine.unit_guard import TakeoffRecord, check

    issues = []
    for r in rows:
        dims = r.raw.get("dimensions_m")
        if not dims:
            continue
        canon = refdata.canonical_unit(r.unit)
        unit_map = {"count": Unit.COUNT, "length": Unit.LENGTH, "area": Unit.AREA, "volume": Unit.VOLUME}
        if canon not in unit_map:
            continue
        result = check(TakeoffRecord(
            description=r.description,
            count=r.raw.get("count", 1),
            dimensions=[Quantity(float(d), Unit.LENGTH) for d in dims],
            claimed_unit=unit_map[canon],
        ))
        if not result.ok:
            issues.append(Issue(
                rule="R15_unit_algebra", severity=Severity.RED,
                message="; ".join(result.errors),
                row_index=r.row_index, sheet=r.sheet, detail={"dimensions_m": dims, "unit": r.unit},
            ))
    return issues


ALL_RULES = [
    r01_ref_errors,
    r02_blank_price,
    r03_r04_amount_vs_qty_rate,
    r05_r06_r07_totals,
    r08_concrete_classification,
    r09_steel_ratio,
    r10_missing_waste,
    r11_negative_or_zero_qty,
    r12_missing_unit,
    r13_duplicate_line,
    r14_outlier_rate,
    r15_unit_algebra,
]

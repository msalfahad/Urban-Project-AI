"""Rule-level tests for the Phase 0 auditor.

Each test proves one of the defect classes the owner named is caught, working on
BoqRow objects directly (no Excel), so a failure points straight at the rule.
"""

from engine.audit import audit_rows, Severity
from engine.audit.model import BoqRow


def _rules(report):
    return {i.rule for i in report.issues}


def line(idx, desc, unit, qty, rate, amount, **kw):
    return BoqRow(row_index=idx, sheet="S", description=desc, unit=unit,
                  quantity=qty, unit_rate=rate, amount=amount, **kw)


def total(idx, amount, **kw):
    return BoqRow(row_index=idx, sheet="S", description="Total", is_total_row=True,
                  amount=amount, **kw)


def qty_total(idx, quantity, **kw):
    """A quantity subtotal (SUM of the quantity column)."""
    return BoqRow(row_index=idx, sheet="S", description="Combined quantity",
                  is_total_row=True, quantity=quantity, **kw)


def test_ref_error_is_red():
    rows = [line(2, "Blockwork", "m2", 100, 3, None, cell_errors=["#REF!"])]
    r = audit_rows(rows)
    assert "R01_excel_error" in _rules(r)
    assert r.status is Severity.RED


def test_blank_price_is_red():
    # سيجما priced at zero for 1500 units — the audited defect. Needs a priced
    # peer so the sheet is recognised as a priced BOQ, not a bare takeoff.
    rows = [
        line(2, "Plaster", "m2", 120, 2.5, 300),
        line(3, "سيجما", "m2", 1500, 0, 0),
    ]
    r = audit_rows(rows)
    assert "R02_blank_price" in _rules(r)
    assert not r.approved


def test_formula_error_amount_not_qty_times_rate():
    rows = [line(2, "Plaster", "m2", 120, 2.5, 500)]  # 120*2.5 = 300, not 500
    r = audit_rows(rows)
    assert "R03_amount_formula_error" in _rules(r)


def test_rounded_rate_discrepancy_is_yellow():
    # 100 * 1.333 = 133.3, but amount stored 133.0 → ~0.2% rounding discrepancy.
    rows = [line(2, "Paint", "m2", 100, 1.333, 133.0)]
    r = audit_rows(rows)
    assert "R04_rounded_rate_discrepancy" in _rules(r)


def test_mixed_units_quantity_total_is_red():
    # The 295.44 defect: a QUANTITY total summing m2 + m + count.
    rows = [
        line(2, "Wall plaster", "m2", 180, None, None),
        line(3, "Skirting", "m", 100, None, None),
        line(4, "Doors", "no", 15, None, None),
        qty_total(5, 295, qty_sum_rows=[2, 3, 4]),
    ]
    r = audit_rows(rows)
    assert "R05_mixed_units" in _rules(r)


def test_money_total_across_mixed_units_is_not_flagged():
    # Summing the MONEY column across different-unit lines is normal — no R05.
    rows = [
        line(2, "Wall plaster", "m2", 180, 1, 180),
        line(3, "Skirting", "m", 100, 1, 100),
        line(4, "Doors", "no", 15, 1, 15),
        total(5, 295, amount_sum_rows=[2, 3, 4]),
    ]
    r = audit_rows(rows)
    assert "R05_mixed_units" not in _rules(r)


def test_sum_mismatch_is_red():
    rows = [
        line(2, "A", "m2", 10, 1, 10),
        line(3, "B", "m2", 20, 1, 20),
        total(4, 100),  # should be 30
    ]
    r = audit_rows(rows)
    assert "R06_sum_mismatch" in _rules(r)


def test_skipped_sum_row_is_red():
    rows = [
        line(2, "A", "m2", 10, 1, 10),
        line(3, "B", "m2", 20, 1, 20),
        line(4, "C", "m2", 30, 1, 30),
        total(5, 30, amount_sum_rows=[2, 3]),  # row 4 left out of the SUM
    ]
    r = audit_rows(rows)
    assert "R07_skipped_sum_row" in _rules(r)


def test_concrete_classification_is_yellow():
    rows = [line(2, "Reinforced concrete column C15", "m3", 10, 50, 500)]
    r = audit_rows(rows)
    assert "R08_concrete_classification" in _rules(r)


def test_steel_ratio_anomaly():
    rows = [
        line(2, "Reinforced concrete slab C30", "m3", 100, 50, 5000),
        line(3, "Reinforcement steel", "kg", 500, 0.3, 150),  # 5 kg/m3 → absurd
    ]
    r = audit_rows(rows)
    assert "R09_steel_ratio" in _rules(r)


def test_missing_waste_is_yellow():
    rows = [
        line(2, "Porcelain floor tiles", "m2", 200, 5, 1000),
        line(3, "Marble skirting", "m", 100, 3, 300),
    ]
    r = audit_rows(rows)
    assert "R10_missing_waste" in _rules(r)


def test_clean_boq_is_green():
    rows = [
        line(2, "Plaster", "m2", 120, 2.5, 300),
        line(3, "Paint", "m2", 120, 1.0, 120),
        total(4, 420, amount_sum_rows=[2, 3]),
    ]
    r = audit_rows(rows)
    assert r.status is Severity.GREEN
    assert r.approved
    assert r.issues == []

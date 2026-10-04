"""REPORTING V3 - trade workbooks, master summary, reconciliation and PDFs rendered from one frozen BOQ model.

Engine quantities are plain values copied from the model (never a formula); formulas exist only for subtotals,
totals and reconciliation arithmetic, and every formula carries the value the model expects (checked after a
LibreOffice recalculation). Same model -> same bytes.
"""

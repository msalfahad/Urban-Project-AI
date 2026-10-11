"""M5 workbooks (generated, git-ignored): 12_QUOTATION_COST_EXPOSURE.xlsx and the consolidated
M5_CONCRETE_RECONCILIATION_WORKBOOK.xlsx. KWD columns are formulas on one rate cell; totals are formulas."""

from __future__ import annotations

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

FONT = Font(name="Arial", size=10)
BOLD = Font(name="Arial", size=10, bold=True)
INPUT = Font(name="Arial", size=10, color="0000FF")
HEAD = PatternFill("solid", fgColor="DDE7F3")
KEY = PatternFill("solid", fgColor="FFFF00")


def _sheet(wb, title, rows, cols=None, kwd=None, note=None):
    ws = wb.create_sheet(title[:31])
    r0 = 1
    if note:
        ws.cell(1, 1, note).font = Font(name="Arial", size=9, italic=True)
        r0 = 3
    cols = cols or (list(rows[0].keys()) if rows else [])
    for j, c in enumerate(cols, 1):
        cell = ws.cell(r0, j, c)
        cell.font, cell.fill = BOLD, HEAD
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for i, r in enumerate(rows, r0 + 1):
        for j, c in enumerate(cols, 1):
            v = r.get(c)
            if isinstance(v, (dict, list, tuple)):
                v = str(v)
            cell = ws.cell(i, j, v)
            cell.font = FONT
    if kwd:            # {"KWD column name": "m3 column name"}: formula = m3 x rate
        for kc, mc in kwd.items():
            if kc not in cols or mc not in cols:
                continue
            jk, jm = cols.index(kc) + 1, cols.index(mc) + 1
            for i in range(r0 + 1, r0 + 1 + len(rows)):
                m = ws.cell(i, jm).value
                if isinstance(m, (int, float)):
                    ws.cell(i, jk, f"={get_column_letter(jm)}{i}*RATE").font = FONT
    for j, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(j)].width = min(60, max(10, len(str(c)) + 2))
    ws.freeze_panes = ws.cell(r0 + 1, 1)
    return ws, r0


def _rate_sheet(wb, rate, title="README", lines=()):
    ws = wb.active
    ws.title = title
    ws["A1"] = "Concrete rate (KWD per m3) - input from the owner brief M5"
    ws["A1"].font = BOLD
    ws["B1"] = rate
    ws["B1"].font, ws["B1"].fill = INPUT, KEY
    from openpyxl.workbook.defined_name import DefinedName
    wb.defined_names["RATE"] = DefinedName("RATE", attr_text=f"'{title}'!$B$1")
    for i, ln in enumerate(lines, 3):
        ws.cell(i, 1, ln).font = FONT
    ws.column_dimensions["A"].width = 110
    return ws


def workbooks(P, out):
    rate = P["rate"]
    n = P["numbers"]
    notes = ["Planning reconciliation, not engineering-approved. Nothing VERIFIED; the gate stays INCOMPLETE.",
             "RC and plain concrete (blinding) are separate lines and are never added together.",
             "Blue cell = input (rate). KWD columns are formulas: m3 x RATE.",
             "Measured = drawing-supported (frozen M4 engine + frozen S-stage registers, after the M5 ownership "
             "decisions). Conditional = drawn but needs an answer. Unmeasurable = not drawn (listed, never zero).",
             "Freelancer / MCP figures are comparison positions read from their records after the engine freeze."]
    # ---------------------------------------------------------------- 12
    wb = Workbook()
    _rate_sheet(wb, rate, lines=notes)
    ws, r0 = _sheet(wb, "EXPOSURE", P["expo"], kwd={"KWD_MEASURED_BASE": "MEASURED_BASE_M3",
                                                    "KWD_MEASURED_HIGH": "MEASURED_HIGH_M3",
                                                    "KWD_CONDITIONAL_HIGH": "CONDITIONAL_HIGH_M3"})
    _sheet(wb, "SCENARIOS", P["scen"], kwd={"KWD": "RC_M3", "VS_FREELANCER_KWD": "VS_FREELANCER_RC_M3"})
    _sheet(wb, "COST_LADDER", P["ladder"], kwd={"KWD": "M3"})
    _sheet(wb, "BLINDING_PLAIN", P["blind_cost"], kwd={"KWD": "M3"},
           note="Plain concrete, priced at the same rate only for comparison; not RC.")
    _sheet(wb, "RFIS", P["rfi"], kwd={"SWING_KWD": "SWING_M3"})
    p12 = out / "12_QUOTATION_COST_EXPOSURE.xlsx"
    wb.save(p12)
    # ---------------------------------------------------------------- consolidated
    wb = Workbook()
    _rate_sheet(wb, rate, "DASHBOARD", lines=notes + [
        "",
        f"Freelancer RC {n['freelancer_rc_m3']:.3f} m3; Urban M4 RC {n['m4_rc_m3']:.3f} m3 (+ plain "
        f"{n['m4_plain_m3']:.3f}); Urban M5 measured RC {n['urban_m5']['MEAS_BASE']:.3f} m3 "
        f"(low {n['urban_m5']['MEAS_LOW']:.3f}, high {n['urban_m5']['MEAS_HIGH']:.3f}); conditional "
        f"{n['urban_m5']['COND_LOW']:.3f} - {n['urban_m5']['COND_HIGH']:.3f} m3.",
        "Status: NOT QUOTATION-READY as a fixed price (see DECISION)."])
    _sheet(wb, "FOUR_SOURCES", P["baseline"])
    _sheet(wb, "FAMILIES", P["fam_rows"])
    _sheet(wb, "SCOPE_MATRIX", P["scope"])
    _sheet(wb, "ELEMENTS", P["elements"], kwd={"COST_KWD": "DIFF_FREELANCER_MINUS_URBAN_BASE_M3"})
    _sheet(wb, "MEMBERSHIP", P["members"])
    _sheet(wb, "BRIDGE", P["bridge"]["steps"], kwd={"KWD": "M3"})
    _sheet(wb, "FRAME_PER_FLOOR", P["frame"])
    _sheet(wb, "GROUND_SLAB_CELLS", P["gs_cells"])
    _sheet(wb, "SLAB_PANELS", P["slab_rows"])
    _sheet(wb, "UNRESOLVED_MISSING", P["missing"], kwd={"KWD_LOW": "LOW_M3", "KWD_HIGH": "HIGH_M3"})
    _sheet(wb, "DOUBLE_COUNTS", P["dcount"], kwd={"KWD": "M3_BASE"})
    _sheet(wb, "EXPOSURE", P["expo"], kwd={"KWD_MEASURED_BASE": "MEASURED_BASE_M3",
                                           "KWD_MEASURED_HIGH": "MEASURED_HIGH_M3",
                                           "KWD_CONDITIONAL_HIGH": "CONDITIONAL_HIGH_M3"})
    _sheet(wb, "SCENARIOS", P["scen"], kwd={"KWD": "RC_M3", "VS_FREELANCER_KWD": "VS_FREELANCER_RC_M3"})
    _sheet(wb, "RFIS", P["rfi"], kwd={"SWING_KWD": "SWING_M3"})
    _sheet(wb, "REFERENCES", P["inventory"])
    _sheet(wb, "CHECKS", P["checks"])
    _sheet(wb, "ENGINE_CHANGE", P["engine_change"]["rows"])
    dec = [{"LINE": "Status", "TEXT": "NOT QUOTATION-READY as a fixed-price lump sum"},
           {"LINE": "Quote", "TEXT": f"measured RC {n['urban_m5']['MEAS_BASE']:.2f} m3 as provisional (remeasurable) "
                                     "quantities"},
           {"LINE": "Allowances", "TEXT": f"conditional {n['urban_m5']['COND_LOW']:.2f} - "
                                          f"{n['urban_m5']['COND_HIGH']:.2f} m3 as separately listed items"},
           {"LINE": "Plain concrete", "TEXT": f"blinding {n['m4_plain_m3']:.2f} m3 drawn (own line); full plot only "
                                              "if specified"},
           {"LINE": "Exclusions / provisional sums", "TEXT": "pump room, tank base / walls, parapets, boundary-wall "
                                                             "pads / columns, tower dome / drums"},
           {"LINE": "Mechanism", "TEXT": "variation clause tied to the RFI answers (13)"}]
    _sheet(wb, "DECISION", dec)
    pc = out / "M5_CONCRETE_RECONCILIATION_WORKBOOK.xlsx"
    wb.save(pc)
    return {"exposure": p12.name, "consolidated": pc.name}

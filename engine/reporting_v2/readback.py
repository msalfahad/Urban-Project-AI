"""REPORTING V2 - read the saved XLSX back and validate it against the reporting model.

validate() refuses: a missing / reordered sheet; any formula that the renderer did not map from a model formula spec
(or whose text differs); any value cell that differs from the model (quantity values compared exactly - the stored
value is the engine value, only the number format rounds); a quantity cell count that differs from the model's
quantity cells; a blocked quantity written as a number; an unprotected sheet; an engine cell that is not locked; an
unlocked cell that is not a manual-check input.

recalc() opens a copy in LibreOffice Calc (headless), lets it compute every formula and compares each computed value
with the model's evaluated value. whatif() types manual values into the input cells of a copy, recalculates it, and
compares every formula with the Python evaluation of the same edits - the reconciliation behaves as specified.
"""

from __future__ import annotations

import copy
import shutil
import subprocess
import tempfile
from pathlib import Path

from .layout import quantity_cells
from .model import evaluate, is_f, is_in

ENGINE_KINDS = ("qty", "qty_text")
XL_ERRORS = ("#DIV/0!", "#VALUE!", "#REF!", "#NAME?", "#N/A", "#NUM!", "#NULL!", "Err:")


def validate(path, model, cell_map) -> dict:
    from openpyxl import load_workbook
    wb = load_workbook(str(path))
    diffs = []
    want_sheets = [s["name"][:31] for s in model["sheets"]]
    if wb.sheetnames != want_sheets:
        diffs.append(["sheet_order", wb.sheetnames, want_sheets])
    mapped = {(e[0], e[1]): e for e in cell_map}
    formulas, unlocked = 0, 0
    for ws in wb:
        if not ws.protection.sheet:
            diffs.append(["sheet_not_protected", ws.title])
        for rw in ws.iter_rows():
            for c in rw:
                if c.data_type == "f" or (isinstance(c.value, str) and c.value.startswith("=")):
                    formulas += 1
                    e = mapped.get((ws.title, c.coordinate))
                    if not e or e[2] != "formula":
                        diffs.append(["unmapped_formula", ws.title, c.coordinate, c.value])
                if c.protection.locked is False and type(c).__name__ != "MergedCell":     # a merge follows its anchor
                    unlocked += 1
                    e = mapped.get((ws.title, c.coordinate))
                    if not e or e[2] != "input":
                        diffs.append(["unlocked_non_input", ws.title, c.coordinate])
    counts = {}
    for e in cell_map:
        sheet, coord, kind, exp = e[:4]
        cell = wb[sheet][coord]
        got = cell.value
        counts[kind] = counts.get(kind, 0) + 1
        if kind in ("qty", "num", "count", "pct", "dim"):
            if isinstance(got, bool) or not isinstance(got, (int, float)) or got != exp:
                diffs.append([sheet, coord, kind, got, exp])
        elif got != exp:
            diffs.append([sheet, coord, kind, got, exp])
        if kind in ENGINE_KINDS and cell.protection.locked is False:
            diffs.append(["engine_cell_unlocked", sheet, coord])
        if kind == "input" and cell.protection.locked is not False:
            diffs.append(["input_cell_locked", sheet, coord])
    mq = quantity_cells(model)
    num_model = sum(1 for *_, c in mq if c["q"] is not None)
    txt_model = sum(1 for *_, c in mq if c["q"] is None)
    nf_model = sum(1 for s in model["sheets"] for sec in s["sections"] for r in sec["rows"] for c in r["cells"] if is_f(c))
    ni_model = sum(1 for s in model["sheets"] for sec in s["sections"] for r in sec["rows"] for c in r["cells"] if is_in(c))
    if counts.get("qty", 0) != num_model:
        diffs.append(["quantity_cell_count", counts.get("qty", 0), num_model])
    if counts.get("qty_text", 0) != txt_model:
        diffs.append(["blocked_cell_count", counts.get("qty_text", 0), txt_model])
    if counts.get("formula", 0) != nf_model or formulas != nf_model:
        diffs.append(["formula_cell_count", formulas, counts.get("formula", 0), nf_model])
    if counts.get("input", 0) != ni_model or unlocked != ni_model:
        diffs.append(["input_cell_count", unlocked, counts.get("input", 0), ni_model])
    for e in cell_map:
        if e[2] == "qty_text" and e[3] == "BLOCKED" and isinstance(wb[e[0]][e[1]].value, (int, float)):
            diffs.append(["blocked_written_as_number", e[0], e[1]])
    return {"state": "PASS" if not diffs else "FAIL", "differences": diffs[:50], "difference_count": len(diffs),
            "formula_cells": formulas, "input_cells": unlocked, "sheets_protected": sum(1 for ws in wb if ws.protection.sheet),
            "validated_quantity_cells": counts.get("qty", 0), "validated_blocked_cells": counts.get("qty_text", 0),
            "validated_cells_by_kind": counts, "validated_cells": sum(counts.values()), "sheets": wb.sheetnames}


def soffice():
    return shutil.which("soffice") or shutil.which("libreoffice")


def _recalc_values(path):
    """LibreOffice computes every formula of a copy; returns {(sheet, coord): value}."""
    from openpyxl import load_workbook
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "in" / Path(path).name
        src.parent.mkdir()
        shutil.copy(path, src)
        out = Path(td) / "out"
        r = subprocess.run([soffice(), "--headless", "--norestore", f"-env:UserInstallation=file://{td}/profile",
                            "--convert-to", "xlsx", "--outdir", str(out), str(src)], capture_output=True, text=True, timeout=300)
        got = out / src.name
        if r.returncode != 0 or not got.exists():
            raise RuntimeError(f"LibreOffice recalculation failed: {r.stderr[-400:]}")
        wb = load_workbook(str(got), data_only=True)
        return {(ws.title, c.coordinate): c.value for ws in wb for rw in ws.iter_rows() for c in rw if c.value is not None}


def _same(got, want) -> bool:
    if want in ("", None):
        return got in ("", None)
    if isinstance(want, str):
        return got == want
    return isinstance(got, (int, float)) and not isinstance(got, bool) and abs(got - want) <= 1e-9 * max(1.0, abs(want))


def recalc(path, cell_map) -> dict:
    """Every formula as LibreOffice computes it == the model's evaluated value (Python mirror of the formulas)."""
    if not soffice():
        return {"state": "SKIPPED", "reason": "LibreOffice not installed"}
    vals = _recalc_values(path)
    fs = [e for e in cell_map if e[2] == "formula"]
    diffs = [[e[0], e[1], e[3], vals.get((e[0], e[1])), e[4]] for e in fs if not _same(vals.get((e[0], e[1])), e[4])]
    errors = [[k[0], k[1], v] for k, v in vals.items() if isinstance(v, str) and v.startswith(XL_ERRORS)]
    return {"state": "PASS" if not diffs and not errors else "FAIL", "engine": "LibreOffice Calc (headless)",
            "formula_cells_checked": len(fs), "differences": diffs[:50], "difference_count": len(diffs), "error_cells": errors[:50]}


def whatif(path, model, cell_map, edits, workdir) -> dict:
    """edits: [[sheet, section, row_key, col_key, value]]. Types the values into the input cells of a copy, recalculates
    it in LibreOffice and compares every formula with evaluate() of the same edits on a copy of the model."""
    from openpyxl import load_workbook
    if not soffice():
        return {"state": "SKIPPED", "reason": "LibreOffice not installed"}
    m2 = copy.deepcopy(model)
    where = {(e[0], *map(str, e[4])): e[1] for e in cell_map if e[2] == "input"}
    wb = load_workbook(str(path))
    for sheet, sec, rk, ck, value in edits:
        coord = where[(sheet, sec, str(rk), ck)]
        wb[sheet][coord].value = value
        s = [x for x in m2["sheets"] if x["name"][:31] == sheet][0]
        sc = [x for x in s["sections"] if x["id"] == sec][0]
        j = [c["key"] for c in sc["columns"]].index(ck)
        r = [x for i, x in enumerate(sc["rows"]) if str(x.get("key", i)) == str(rk)][0]
        assert is_in(r["cells"][j]), (sheet, sec, rk, ck)
        r["cells"][j]["input"] = value
    evaluate(m2)
    expect = {}
    for s in m2["sheets"]:
        for sc in s["sections"]:
            for i, r in enumerate(sc["rows"]):
                for j, c in enumerate(r["cells"]):
                    if is_f(c):
                        expect[(s["name"][:31], sc["id"], str(r.get("key", i)), sc["columns"][j]["key"])] = c["v"]
    out = Path(workdir) / ("WHATIF_" + Path(path).name)
    wb.save(str(out))
    vals = _recalc_values(out)
    fs = [e for e in cell_map if e[2] == "formula"]
    diffs, changed = [], 0
    for e in fs:
        want = expect[(e[0], *map(str, e[5]))]
        if want != e[4]:
            changed += 1
        if not _same(vals.get((e[0], e[1])), want):
            diffs.append([e[0], e[1], vals.get((e[0], e[1])), want])
    out.unlink()
    errors = [[k[0], k[1], v] for k, v in vals.items() if isinstance(v, str) and v.startswith(XL_ERRORS)]
    return {"state": "PASS" if not diffs and not errors else "FAIL", "error_cells": errors[:50], "edits": len(edits), "formula_cells_checked": len(fs),
            "formula_cells_changed_by_edits": changed, "differences": diffs[:50], "difference_count": len(diffs),
            "model_after": m2}

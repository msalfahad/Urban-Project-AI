"""Reporting V2 - generic model, renderer and readback on a synthetic register set (no project data)."""

import ast
import json
from pathlib import Path

import pytest

from engine.reporting_v2 import layout as L
from engine.reporting_v2 import model as M
from engine.reporting_v2 import readback as RB
from engine.reporting_v2 import terms as T
from engine.reporting_v2 import xlsx as X

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def regs(tmp_path):
    p = tmp_path / "REG.json"
    p.write_text(json.dumps({"slab": {"GF": 10.1, "1F": 20.2}, "beam": 0.1, "beam2": 0.2, "blocked": None, "count": 3,
                             "rows": [{"a": 1.5}, {"a": 2.25}]}))
    return M.Registers({"REG": p})


def _model(regs, *, breakdown_cls="BREAKDOWN_ONLY", summary_override=None):
    lines = [M.line("CON", "STRUCTURAL_CONCRETE", "Concrete", "خرسانة", "m3",
                    [M.part("GF", regs.q("REG:/slab/GF"), "COMPUTED"), M.part("1F", regs.q("REG:/slab/1F"), "COMPUTED"),
                     M.part("FOUNDATION", M.blocked("BLOCKED_HEIGHT"), "BLOCKED_HEIGHT")]),
             M.line("CNT", "DOORS", "Doors", "", "nr", [M.part("GF", regs.q("REG:/count"), "COMPUTED")])]
    lines[0]["matrix"] = "CONCRETE"
    rows = [M.row(["GF slab", regs.q("REG:/slab/GF"), "COMPUTED"], cls=breakdown_cls, status="COMPUTED", tech="COMPUTED",
                  explains="CON@GF"),
            M.row(["blocked thing", M.blocked("BLOCKED_HEIGHT"), "BLOCKED"], cls="BREAKDOWN_ONLY", status="BLOCKED",
                  tech="BLOCKED_HEIGHT", explains="CON@FOUNDATION")]
    sec = M.section("S", ("SECTION", "قسم"), [M.col("i", "ITEM"), M.col("q", "QTY", "", "qty", "m3"), M.col("s", "STATUS", "", "status")], rows)
    sh = M.sheet("01_GROUND_FLOOR", ("GROUND FLOOR", "الدور الأرضي"), "BREAKDOWN", [sec], level="GF")
    proj = {"name_en": "SYNTHETIC", "name_ar": "", "phase": "TEST", "release_state": "SHADOW", "subtitle": "synthetic",
            "header": [("Project", "synthetic")]}
    return L.assemble(proj, lines, [sh], regs)


def test_declared_sum_is_exact_decimal_addition(regs):
    s = M.qsum([regs.q("REG:/beam"), regs.q("REG:/beam2")])
    assert s["q"] == 0.3 and s["sum"] == ["REG:/beam", "REG:/beam2"]
    assert M.qsum([regs.q("REG:/count"), regs.q("REG:/count")])["q"] == 6


def test_line_status_blocked_is_never_zero(regs):
    m = _model(regs)
    con = m["lines"][0]
    assert con["status"] == "PARTIAL" and con["qty"]["q"] == 30.3 and len(con["qty"]["sum"]) == 2
    only_blocked = M.line("X", "PAINT", "x", "", "m2", [M.part("GF", M.blocked("BLOCKED_MATERIAL"), "BLOCKED_MATERIAL")])
    assert only_blocked["status"] == "BLOCKED" and only_blocked["qty"]["q"] is None


def test_valid_model_passes(regs):
    v = M.validate(_model(regs), regs)
    assert v["state"] == "PASS", v["problems"]
    assert v["quantity_cells"] > 0 and v["declared_sums"] >= 1


def test_additive_row_outside_summary_fails(regs):
    v = M.validate(_model(regs, breakdown_cls="ADDITIVE"), regs)
    assert v["state"] == "FAIL" and any("outside the summary" in p for p in v["problems"])


def test_quantity_that_differs_from_its_register_fails(regs):
    m = _model(regs)
    m["sheets"][1]["sections"][0]["rows"][0]["cells"][1]["q"] = 10.2
    assert any("REG:/slab/GF" in p for p in M.validate(m, regs)["problems"])


def test_declared_sum_mismatch_fails(regs):
    m = _model(regs)
    m["lines"][0]["qty"]["q"] = 30.4
    assert M.validate(m, regs)["state"] == "FAIL"


def test_line_missing_from_summary_fails(regs):
    m = _model(regs)
    lines_sec = [s for s in m["sheets"][0]["sections"] if s["id"] == "BOQ_LINES"][0]
    lines_sec["rows"] = [r for r in lines_sec["rows"] if r.get("explains") != "CNT"]
    assert any("not on the summary" in p for p in M.validate(m, regs)["problems"])


def test_unknown_status_code_fails_closed():
    with pytest.raises(KeyError):
        M.display_status("SOMETHING_NEW")
    with pytest.raises(KeyError):
        T.explain("SOMETHING_NEW")
    assert M.display_status("BLOCKED_ANYTHING") == "BLOCKED" and T.explain("BLOCKED_UPPER_MEMBER_UNBOUND")["priority"] == "HIGH"


def test_trade_totals_only_add_one_group_and_unit(regs):
    m = _model(regs)
    totals = [s for s in m["sheets"][0]["sections"] if s["id"] == "TRADE_TOTALS"][0]["rows"]
    assert all(r["role"] == "TOTAL" for r in totals) and len(totals) == 2
    matrix = [s for s in m["sheets"][0]["sections"] if s["id"] == "FLOOR_TOTALS"][0]
    total_row = matrix["rows"][-1]
    assert total_row["role"] == "TOTAL" and total_row["cells"][2]["q"] == 30.3


def test_render_readback_and_tamper(regs, tmp_path):
    m = _model(regs)
    x = X.render(m, tmp_path / "r.xlsx")
    rb = RB.validate(tmp_path / "r.xlsx", m, x["cell_map"])
    assert rb["state"] == "PASS" and rb["formula_cells"] == 0 and rb["validated_quantity_cells"] > 0
    x2 = X.render(m, tmp_path / "r2.xlsx")
    assert x2["file_sha256"] == x["file_sha256"]                         # deterministic bytes
    from openpyxl import load_workbook
    wb = load_workbook(tmp_path / "r.xlsx")
    sheet, coord = next((s, c) for s, c, k, _ in x["cell_map"] if k == "qty")
    wb[sheet][coord] = 999.0
    wb[sheet]["Z99"] = "=SUM(1,2)"
    wb.save(tmp_path / "t.xlsx")
    bad = RB.validate(tmp_path / "t.xlsx", m, x["cell_map"])
    assert bad["state"] == "FAIL" and bad["formula_cells"] == 1 and any(d[1] == coord for d in bad["differences"])


def test_blocked_quantity_is_written_as_text_not_zero(regs, tmp_path):
    m = _model(regs)
    x = X.render(m, tmp_path / "r.xlsx")
    texts = [e for e in x["cell_map"] if e[2] == "qty_text"]
    assert texts and all(e[3] == "BLOCKED" for e in texts if e[3] != "—" and e[3] != "")


def test_reporting_package_imports_no_qto_engine():
    """The presentation layer measures nothing: no import of engine.source or any other engine module."""
    for p in sorted((ROOT / "engine" / "reporting_v2").glob("*.py")):
        tree = ast.parse(p.read_text())
        for n in ast.walk(tree):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else \
                ([n.module or ""] if isinstance(n, ast.ImportFrom) and n.level == 0 else [])
            for name in names:
                assert not name.startswith("engine") or name.startswith("engine.reporting_v2"), (p.name, name)

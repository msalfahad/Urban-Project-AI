"""T-236 runner (tools/trade_completeness.py) on the synthetic villa of test_t236_synthetic_villa.py; writes only under
pytest's tmp_path."""

from __future__ import annotations

import csv
import json

from tools import trade_completeness as R

from .test_t236_synthetic_villa import villa


def test_runner_writes_tables_and_lines_file(tmp_path):
    v = villa()
    lines = v.pop("lines")
    (tmp_path / "lines.json").write_text(json.dumps({"lines": lines}), encoding="utf-8")
    v["lines_file"] = "lines.json"
    (tmp_path / "in.json").write_text(json.dumps(v), encoding="utf-8")
    assert R.main([str(tmp_path / "in.json"), "--out", str(tmp_path / "out")]) == 0
    rows = list(csv.DictReader(open(tmp_path / "out" / "TRADE_COMPLETENESS_TRADES.csv", encoding="utf-8")))
    by = {r["trade"]: r for r in rows}
    assert by["CONCRETE.FOOTING"]["completeness_n_d"] == "3 / 4" and by["CONCRETE.FOOTING"]["verified_n_d"] == "1 / 4"
    assert by["PAINT"]["status"] == "NOT_MEASURED"
    ref = json.loads((tmp_path / "out" / "REFERENCE_LINE_ROWS.json").read_text(encoding="utf-8"))
    assert [r for r in ref if r["element_scope"] == "CONCRETE.FOOTING"][0]["missing"] == ["FDN:F3"]


def test_runner_refused_input_exit_2(tmp_path, capsys):
    v = villa()
    v["inventories"][0]["basis"] = "ENGINE_REGISTER"
    (tmp_path / "in.json").write_text(json.dumps(v), encoding="utf-8")
    assert R.main([str(tmp_path / "in.json"), "--print"]) == 2
    assert "REFUSED" in capsys.readouterr().err

"""T-346 development villa: rows 65 / 68 / 69 rebuilt byte for byte from committed, Checker-merged research files
(T-337 binding, the freelancer raw cells) and the invariants of the reconciliation. No private drawing is read."""

import csv
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t346"
sys.path.insert(0, str(HERE))

import t346_alsenan as T  # noqa: E402

OUT = T.outputs()


def rows(name):
    return list(csv.DictReader(io.StringIO(OUT[name])))


def test_byte_identical_rebuild():
    for name, text in OUT.items():
        assert (HERE / name).read_text(encoding="utf-8") == text, name


def test_statement_93150_closes_with_residual_zero():
    st = json.loads(OUT["summary.json"])["statement_m2"]
    assert st["his_total"] == pytest.approx(93.15)
    assert st["drawn_matched"] == pytest.approx(79.2134)
    assert st["double_count"] == pytest.approx(9.0)
    assert st["named_terms"] == pytest.approx(4.9366)
    assert st["unresolved"] == 0 and st["residual"] == pytest.approx(0.0, abs=1e-9)


def test_portions_close_on_the_t337_faces_and_lines():
    for r in rows("CLOSURE_T346.csv"):
        if r["difference_m2"]:
            assert abs(float(r["difference_m2"])) < 1e-6, r["t337_key"]
    keys = {r["t337_key"] for r in rows("CLOSURE_T346.csv")}
    assert {"GF/NW-7/EDGE/storey", "1F/NW-5/STOREY/storey", "1F/NW-5/PARAPET/parapet"} <= keys


def test_no_new_fill_row_and_every_part_classified():
    assert json.loads(OUT["summary.json"])["new_t314_fill_rows"] == 0
    parts = rows("ROWS_T346.csv")
    kinds = [(p["his_row"], p["kind"]) for p in parts]
    assert kinds == [("68", "MATCHED"), ("69", "MATCHED"), ("65", "DOUBLE_COUNT"), ("65", "MATCHED")]
    for p in parts:
        if p["kind"] == "DOUBLE_COUNT":
            assert float(p["drawn_m2_in_his_band"]) == 0.0
        else:
            assert float(p["drawn_m2_in_his_band"]) > 0
    assert float(parts[0]["named_terms_m2"]) == pytest.approx(0.0)     # row 68 agrees with the drawn 1.50 m portion


def test_row69_height_term_is_named_not_absorbed():
    b69 = [b for b in rows("BANDS_T346.csv") if b["his_row"] == "69"]
    top = b69[-1]
    assert float(top["drawn_width_m"]) == 0.0 and "PEAK +10.80" in top["cause"]
    assert float(top["his_minus_drawn_m2"]) == pytest.approx(4.400398, abs=1e-6)
    hidden = [b for b in b69 if float(b["drawn_width_m"]) > float(b["his_width_m"])]
    assert len(hidden) == 1 and float(hidden[0]["his_minus_drawn_m2"]) == pytest.approx(-3.1875)

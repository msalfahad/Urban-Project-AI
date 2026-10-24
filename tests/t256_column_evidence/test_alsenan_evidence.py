"""T-256 Alsenan: per-column evidence for the 15 CONFLICT columns and the 5 NOT_DRAWN upper lines of CONC.COLUMN, from
the committed values-only input (t256_extract.py on Drive 'ST7757 dxf.dxf' 9f9d1179, 'P7757_DXF_COMPRESSED.zip' ->
P7757.dxf ab54dd55, 'ST7757.pdf' 74da1523). Development villa; not an accuracy claim; nothing applied."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t256"
sys.path.insert(0, str(HERE))
import t256_alsenan_check as C  # noqa: E402

EV, ROWS, RECS, EX = C.build()
SUM = C.summarise(EV, ROWS, EX)


def test_rerun_equals_committed_ledger_and_summary():
    committed = list(csv.DictReader(open(HERE / "LEDGER_T256.csv", encoding="utf-8")))
    assert len(committed) == len(ROWS) == 15
    for a, b in zip(committed, ROWS):
        assert a["member"] == b["member"] and a["status"] == b["status"]
        assert float(a["m3_lo"]) == pytest.approx(b["m3_lo"]) and float(a["m3_hi"]) == pytest.approx(b["m3_hi"])
    assert json.loads((HERE / "summary.json").read_text(encoding="utf-8")) == json.loads(json.dumps(SUM, sort_keys=True))


def test_no_third_independent_source_settles_any_of_the_15():
    assert SUM["status_count"] == {"AGREE": 0, "SETTLED": 0, "CONFLICT": 15, "HELD": 0}
    assert SUM["basis_count"] == {"PRINTED_VS_DRAWN": 15}
    assert all(r["third_independent_printed"] == 0 for r in ROWS)


def test_ranges_unchanged_against_t248():
    assert SUM["conflict_m3"] == [pytest.approx(8.034), pytest.approx(10.119)] and SUM["equals_t248"] is True
    assert SUM["by_storey"]["GF"]["m3"] == [pytest.approx(2.07), pytest.approx(2.475)]
    assert SUM["by_storey"]["1F"]["m3"] == [pytest.approx(5.964), pytest.approx(7.644)]


def test_plot_and_architectural_plan_are_copies_not_sources():
    ind = SUM["independence"]
    assert ind["pdf_plot_same_as_dxf_on_all_15"] is True and ind["arch_copy_same_on_all_15"] is True
    assert ind["arch_column_layers"] == ["S-COL.BON"] and ind["arch_column_outlines_total"] == 59
    for s, n in (("GF", 30), ("1F", 20), ("2F", 9)):
        a = ind["arch_vs_structural"][s]
        assert a["arch_outlines"] == a["matched"] == n and a["spread_mm"] == 0.0
    assert ind["arch_face_to_face_dims_on_the_15"] == 0 and ind["slab_plan_prints_at_the_15"] == 0
    assert ind["pdf_storeys"]["1F"]["dxf_outlines_without_a_plot_fill"] == ["77B"]      # a P.C start: hatched, not filled


def test_which_dimension_conflicts_and_the_copy_pattern():
    assert SUM["differs_in"] == {"long side": 5, "short side": 5, "short side+long side": 5}
    assert SUM["drawn_equals_gr_band_1F"] == 8
    c8 = [r for r in ROWS if r["mark"] == "C8"]
    assert {r["designer_item"] for r in c8} == {"D-16"}


def test_cross_trade_plate_transfer_of_the_schedule_reading():
    assert SUM["by_storey"]["GF"]["plate_transfer_schedule_reading_m3"] == pytest.approx(0.0144)
    assert SUM["by_storey"]["1F"]["plate_transfer_schedule_reading_m3"] == pytest.approx(-0.064)
    assert {r["plate_transfer_kind"] for r in ROWS if r["storey"] == "GF"} == {"DOUBLE"}
    assert {r["plate_transfer_kind"] for r in ROWS if r["storey"] == "1F"} == {"GAP"}


def test_five_not_drawn_lines_absent_on_every_sheet():
    e = SUM["existence"]
    assert e["status_count"] == {"EXISTS": 0, "UNKNOWN": 0, "NOT_PRESENT": 5}
    assert e["route_g_m3_on_them"] == pytest.approx(2.268)
    for r in e["lines"]:
        assert set(r["searched"].values()) == {"ABSENT"} and r["m3"] is None and r["action"] == "REMOVE_LINE"
    assert e["type_table_2ND_band_types_without_a_2F_member"] == ["C4", "C6", "C7", "C8"]

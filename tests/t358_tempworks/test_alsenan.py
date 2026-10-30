"""T-358 development villa (committed inputs only: ALSENAN_TEMPWORKS_INPUT.json; sheet / note numbers and handles read
from ST7757.pdf sha 74da1523, 'ST7757 dxf.dxf' sha 9f9d1179, P7757.dxf sha ab54dd55, the architectural and sanitary
PDFs; excavation rectangles in plot-local metres from the T-170 committed input). Pins the engineering result:
B1-06 support TRIGGERED on all four plot sides (faces on or beyond the line), dewatering CONDITIONAL (3.00 m clearance,
lift threshold 4.80 m), other temporary works NOT_IN_DRAWN_SCOPE, every quantity None; and that the committed outputs
reproduce."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t358"
sys.path.insert(0, str(HERE))
import t358_alsenan_check as C  # noqa: E402

OUT = C.main(write=False)
SUM = OUT["summary"]
INP = json.loads((HERE / "ALSENAN_TEMPWORKS_INPUT.json").read_text(encoding="utf-8"))


def test_input_is_references_only():
    txt = (HERE / "ALSENAN_TEMPWORKS_INPUT.json").read_text(encoding="utf-8")
    assert "9f9d1179" in txt and "74da1523" in txt and "ab54dd55" in txt
    assert not re.search(r"\d{5,}\.\d", txt)  # no drawing coordinates (plot-local metres only)
    assert not re.search(r"[؀-ۿ]", txt)  # no Arabic note text copied


def test_every_sheet_searched_and_the_stating_notes():
    assert len(INP["set_sheets"]) == 31 and len(OUT["sheets"]) == 31
    assert all(r["searched"] for r in OUT["sheets"])
    stating = {r["sheet"] for r in OUT["sheets"] if r["b1_06"] != "absent"}
    assert stating == {"ST p.1", "ST p.8", "ST p.9", "ST p.14"}
    p8 = {s["note"]: s["class"] for s in next(r for r in INP["sheet_search"] if r["sheet"] == "ST p.8")["states"]}
    assert p8["14"] == "DEWATERING" and p8["15"] == "SUPPORT" and p8["17"] == p8["23"] == "FORMWORK_PROPS"
    p9 = {s["note"].split()[0]: s["class"] for s in next(r for r in INP["sheet_search"] if r["sheet"] == "ST p.9")["states"]}
    assert p9["4"] == "GROUNDWATER" and p9["1"] == "EXCAVATION_LEVEL"
    assert all(r["b1_06"] == "absent" for r in OUT["sheets"] if r["sheet"].startswith(("ARCH", "SAN")))


def test_dewatering_conditional_with_its_triggers_in_metres():
    d = SUM["dewatering"]
    assert d["status"] == "CONDITIONAL" and d["water_level"] == -4.5 and d["min_clearance_m"] == pytest.approx(3.0)
    rows = {r["element"]: r for r in d["rows"]}
    assert rows["pool envelope"]["status"] == "NOT_TRIGGERED"
    assert rows["lift FF"]["threshold"] == pytest.approx(4.8)
    assert d["sensitivity_ffl_datum"] == {"water_level": -3.5, "pits_clearance_m": 2.0, "lift_threshold_m": 3.8}
    assert d["quantity"] is None


def test_support_triggered_on_all_four_sides_lengths_in_metres():
    s = SUM["support"]
    assert {k: v["status"] for k, v in s.items()} == {k: "TRIGGERED" for k in ("S0", "S1", "S2", "S3")}
    assert s["S0"]["on_or_beyond_m"] == pytest.approx(15.15)  # pits only (3 F, F15, F11, F14, F10/F)
    assert s["S1"]["on_or_beyond_m"] == pytest.approx(31.37)  # boundary-wall trench, whole side
    assert s["S2"]["on_or_beyond_m"] == pytest.approx(10.0)
    assert s["S3"]["on_or_beyond_m"] == pytest.approx(11.85)
    assert all(v["quantity"] is None for v in s.values())


def test_excavations_beyond_the_plot_line_named():
    assert len(SUM["beyond_plot_line"]) == 10 and "POOL:7C6" in SUM["beyond_plot_line"]
    assert "F11:1B07" in SUM["beyond_plot_line"] and "FF:1B2B" not in SUM["beyond_plot_line"]


def test_items_have_no_quantity_and_neither_boq_has_a_row():
    assert [i["status"] for i in SUM["items"]] == ["CONDITIONAL", "TRIGGERED", "NOT_IN_DRAWN_SCOPE"]
    assert all(i["quantity"] is None and i["extent"] is None for i in SUM["items"])
    assert SUM["freelancer_rows"] == 0 and SUM["engine_lines"] == 0


def test_outputs_reproduce():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s == json.loads(json.dumps(SUM))
    for name, rows in (("SHEET_SEARCH_T358.csv", OUT["sheets"]), ("EXPOSURE_T358.csv", OUT["exposure"]),
                       ("SIDES_T358.csv", OUT["sides"]), ("ITEMS_T358.csv", OUT["items"])):
        with open(HERE / name, newline="", encoding="utf-8") as f:
            got = list(csv.DictReader(f))
        assert got == [{k: ("" if v is None else str(v)) for k, v in r.items()} for r in rows], name

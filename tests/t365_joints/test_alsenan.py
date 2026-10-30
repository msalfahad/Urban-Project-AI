"""T-365 development villa (committed inputs only: ALSENAN_JOINTS_INPUT.json; sheet / note numbers, handles and pattern
names read from ST7757.pdf sha 74da1523, 'ST7757 dxf.dxf' sha 9f9d1179, P7757.dxf sha ab54dd55, the architectural sheets
10 - 12 and sanitary-7757.pdf). Pins the engineering result: no sheet of the 31 prints a movement / expansion joint or a
sealant; the two owner-scoped joints (roof field, outside tile field; Q-42 width 3 mm) are HELD, nine are
NOT_IN_DRAWN_SCOPE, every quantity None (never 0), no RFI; the freelancer's only 'joints' row is plaster; outputs
reproduce."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t365"
sys.path.insert(0, str(HERE))
import t365_alsenan_check as C  # noqa: E402

OUT = C.main(write=False)
SUM = OUT["summary"]
INP = json.loads((HERE / "ALSENAN_JOINTS_INPUT.json").read_text(encoding="utf-8"))


def test_input_is_references_only():
    txt = (HERE / "ALSENAN_JOINTS_INPUT.json").read_text(encoding="utf-8")
    assert "9f9d1179" in txt and "74da1523" in txt and "ab54dd55" in txt
    assert not re.search(r"\d{5,}\.\d", txt)  # no drawing coordinates
    assert not re.search(r"[؀-ۿ]", txt)  # no Arabic note text copied


def test_every_sheet_searched_none_prints_a_joint():
    sheets = [s["sheet"] for s in INP["sheet_search"]]
    assert len(sheets) == 31 and len(set(sheets)) == 31
    assert sum(s.startswith("ST") for s in sheets) == 16 and sum(s.startswith("ARCH") for s in sheets) == 12
    assert SUM["sheets_printing_a_joint"] == 0


def test_dxf_census_and_non_sources():
    assert SUM["dxf_text_records"] == {"ST7757 dxf.dxf": 2253, "P7757.dxf": 276}
    assert SUM["dxf_text_joint_hits"]["ST7757 dxf.dxf"] == 0
    assert SUM["dxf_false_positives"] == 10  # title-block 'plot number' only
    assert SUM["hatches_not_joint"] == len(OUT["hatches"]) == 62
    assert {h["class"] for h in OUT["hatches"]} == {"HATCH_NOT_JOINT"}
    assert SUM["twin_columns_gap_1_100_mm"] == 0


def test_statuses_and_no_zero():
    st = {r["id"]: r["status"] for r in OUT["joints"]}
    assert st["J4"] == st["J5"] == "HELD"
    assert sorted(k for k, v in st.items() if v == "NOT_IN_DRAWN_SCOPE") == sorted(
        ["J1", "J2", "J3", "J6", "J7", "J8", "J9", "J10", "J11"])
    assert all(r["length_m"] is None and r["sealant_m"] is None for r in OUT["joints"])
    assert SUM["measured_total_m"] is None and SUM["rfi_candidates"] == []
    assert {r["v3_0_26_line"].split(" ")[0] for r in OUT["joints"]} == {"NO"}


def test_freelancer_row_is_plaster_physical_vs_payable():
    (r,) = OUT["freelancer"]
    assert r["file"] == "PLS" and r["physical_m"] == 1297.35 and r["payable_m"] == 648.675
    assert abs(r["physical_m"] / 2 - r["payable_m"]) < 1e-9 and r["verdict_proposal"].startswith("RULE_DIFFERENCE")


def test_committed_outputs_reproduce():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert s == json.loads(json.dumps(SUM))
    with open(HERE / "JOINTS_T365.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert [r["id"] for r in rows] == [r["id"] for r in OUT["joints"]]
    assert all(r["length_m"] == "" for r in rows)

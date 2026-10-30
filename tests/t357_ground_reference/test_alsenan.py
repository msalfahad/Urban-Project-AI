"""T-357 Alsenan ground reference (committed inputs only: ALSENAN_GROUND_INPUT.json, values / handles / pages from
'P7757_DXF_COMPRESSED.zip', 'ST7757 dxf.dxf' sha 9f9d1179, ST7757.pdf, the architectural and sanitary PDFs). Re-runs
the check without writing and pins the engineering results."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t357"
sys.path.insert(0, str(HERE))
import t357_alsenan_check as C  # noqa: E402

ROWS, SUM = C.main(write=False)
INP = json.loads((HERE / "ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8"))


def test_input_is_values_only():
    txt = (HERE / "ALSENAN_GROUND_INPUT.json").read_text(encoding="utf-8")
    assert "9f9d1179" in txt
    assert not re.search(r"\d{5,}\.\d", txt)  # no drawing coordinates
    assert not re.search(r"[؀-ۿ]", txt)  # no Arabic note text copied


def test_existing_ground_derived_from_four_corners_not_assumed():
    eg = SUM["existing_ground"]
    assert eg["status"] == "DERIVED" and eg["value_m"] == 0.0
    assert eg["per_corner"] == {"C1": 0.0, "C2": 0.0, "C3": 0.0, "C4": 0.0}
    named = [m for m in INP["level_marks"] if m["kind"] == "NAMED_NO_VALUE"]
    assert len(named) == 3 and all(m["value"] is None for m in named)


def test_finished_levels_never_feed_existing_ground():
    marks = [m for m in INP["level_marks"] if m["kind"] in ("FINISHED_GROUND", "FINISHED_FLOOR")]
    r = C.G.existing_ground_reference(marks, list(INP["plot"]["corners"]))
    assert r["status"] == "HELD" and r["value_m"] is None


def test_plot_area_and_printed_percentages():
    assert SUM["plot"]["area_m2"] == pytest.approx(470.55, abs=1e-6)
    assert SUM["plot"]["sides_printed_equal_dxf"] is True
    cov = SUM["coverage_check"]
    assert cov["status"] == "CONSISTENT"
    assert {r["agreement"] for r in cov["rows"]} == {"TRUNCATED"}
    assert SUM["plot_minus_gf_printed_m2"] == pytest.approx(150.56, abs=1e-6)


def test_clearance_not_in_drawn_scope_every_sheet():
    clr = SUM["clearance"]
    assert clr["status"] == "NOT_IN_DRAWN_SCOPE" and clr["area_m2"] is None
    sheets = [s["sheet"] for s in INP["sheet_search"]]
    assert len(sheets) == 31  # ST 16 + ARCH 12 + SAN 3
    assert sum(s.startswith("ST ") for s in sheets) == 16 and sum(s.startswith("ARCH ") for s in sheets) == 12


def test_eg_coefficients():
    c = {x["id"].split(" (")[0]: x["coef_m3_per_m"] for x in SUM["eg_coefficients"]}
    assert c["Z1 24 neat footing pits"] == 0.0
    assert c["Z1 24 pits, absolute formation once printed"] is None
    assert c["Z1 pool envelope in plot"] == pytest.approx(11.851051)
    assert c["pool walls below EG"] == pytest.approx(2.356727)
    assert c["pool walls above EG"] == pytest.approx(-2.356727)
    assert c["Z2 fill above EG under the GF slabs"] is None

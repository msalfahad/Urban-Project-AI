"""T-217 on the development villa (research/agents_t217: values and DXF handles only, read this run from Drive
"Alsenan chalet project" / 'ST7757 dxf.dxf'). 36 neck instances x 4 storeys -> 110 member-storey rows; 89 released
route G lines bound (28 necks + 61 storey columns); no released quantity changed."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t217"))
import t217_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.run()


def row(res, member, storey):
    return next(r for r in res["rows"] if r["member"] == member and r["storey"] == storey)


def test_counts(res):
    assert res["instances"] == 36 and res["member_storey_rows"] == 110
    assert res["released_lines_bound"] == res["released_lines_total"] == 89
    sc = res["status_counts"]
    assert sc["FOUNDATION CONFLICT"] == 5 and sc["FOUNDATION DRAFTING_NOTE"] == 6 and sc["FOUNDATION AGREE"] == 25
    assert sc["GF CONFLICT"] == 9 and sc["1F CONFLICT"] == 11 and sc["2F CONFLICT"] == 2


def test_c8_at_f14_is_printed_vs_printed_on_the_neck(res):
    r = row(res, "10E0", "FOUNDATION")
    assert (r["status"], r["basis"], r["per_m_m3"]) == ("CONFLICT", "PRINTED_VS_PRINTED", "0.2400..0.2700")
    assert "TEXT:CAP 101B" in r["candidates"] and "CGT 1DBE FOU" in r["candidates"]
    assert row(res, "10E0", "GF")["at_released_height_m3"] == "0.9000..1.0125"   # T-180 C8 range, both ends named


def test_lift_necks_drawn_and_printed_at_their_gf_section(res):
    for m in ("1099", "1093", "1096", "1090"):
        r = row(res, m, "FOUNDATION")
        assert r["status"] == "CONFLICT" and r["basis"] == "PRINTED_VS_PRINTED" and r["pit_raft"] is True
        assert "schedule band GR" in r["drawn_matches_band"]
        assert row(res, m, "GF")["status"] == "AGREE"


def test_drafting_notes_printed_by_the_drawing(res):
    r = row(res, "108D", "FOUNDATION")               # C4 at F4: drawn 0.25 on FP / CAP / GBP, CAP dims print 0.30
    assert r["status"] == "DRAFTING_NOTE" and "DIM:CAP 898/8AB/8B9/8C8" in r["candidates"]
    assert row(res, "10B7", "FOUNDATION")["status"] == "DRAFTING_NOTE"   # C at F: FP drawn 0.40, CAP prints 0.50


def test_released_lines_unchanged_and_existence_findings(res):
    lift = sum(row(res, m, "FOUNDATION")["released_m3"] for m in ("1099", "1093", "1096", "1090"))
    assert lift == pytest.approx(1.4625)
    ex = res["released_lines_on_members_not_drawn_on_that_storey"]
    assert len(ex["lines"]) == 5 and ex["m3"] == pytest.approx(2.268) and ex["status"].startswith("UNKNOWN")

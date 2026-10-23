"""T-233 Alsenan ledger from committed inputs only (ALSENAN_FOOTING_INPUT.json from Drive 'ST7757 dxf.dxf' sha
9f9d1179; freelancer cells from tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json). Re-runs the check without
writing and pins the engineering results (development villa; not an accuracy claim)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t233"
sys.path.insert(0, str(HERE))
import t233_alsenan_check as C  # noqa: E402

FRES, BRES, SUM = C.main(write=False)
TXT = (HERE / "ALSENAN_FOOTING_INPUT.json").read_text(encoding="utf-8")
INP = json.loads(TXT)


def test_input_is_values_only():
    assert INP["source"]["sha256"].startswith("9f9d1179")
    assert not re.search(r"\d{5,}\.\d", TXT)               # no sheet coordinates (5-6 digit mm values)


def test_population_each_outline_once():
    assert len(INP["outlines"]) == 26                     # foundation frame only; ground-beam plan copies excluded
    assert INP["unbound_tags"] == []
    ids = [o["id"] for o in INP["outlines"]]
    assert len(ids) == len(set(ids))
    assert SUM["not_drawn_types"] == ["F7"]               # scheduled, not on the plan: count 0, not HELD


def test_footings_by_type_and_total():
    bt = SUM["by_type"]
    assert bt["F"] == [4, pytest.approx(0.864)] and bt["F3"] == [2, pytest.approx(1.344)]
    assert bt["FN"] == [4, pytest.approx(1.158)]          # one FN drawn clipped where F9 owns 0.40 x 0.35
    assert SUM["footings_measured_m3"] == pytest.approx(64.304, abs=1e-6)
    assert sum(v[0] for v in bt.values()) == 25
    st = {r.outline: r.status for r in FRES.rows}
    assert st["180C"] == "CLIPPED" and st["1B1B"] == "HELD"
    assert sum(1 for s in st.values() if s == "AGREE") == 24


def test_f10_held_as_the_two_printed_readings():
    held = [h for h in SUM["footings_held"] if h[0] == "1B1B"][0]
    assert list(held[2]) == [pytest.approx(2.176), pytest.approx(2.275)]   # owner Q-31 C: HELD, never one end


def test_blinding_union_boundary_and_follow():
    b = SUM["blinding"]
    assert b["plan_sum_m2"] == pytest.approx(151.99) and b["overlap_once_m2"] == pytest.approx(0.195625)
    assert b["outside_m2"] == pytest.approx(1.89)        # D-14: 8 footings on the plot line
    assert b["measured_m3"] == pytest.approx(14.990438, abs=1e-6)
    # inside + outside = the candidate's released footing blinding 15.179437 (T-193): same physical plan
    assert b["measured_m3"] + 0.189 == pytest.approx(15.179437, abs=1e-6)
    f10 = [h for h in b["held"] if h[0] == "1B1B"][0]
    assert list(f10[2]) == [pytest.approx(0.5025), pytest.approx(0.59)]


def test_lines_not_closable_and_why():
    assert SUM["conc_footing"]["measured_m3"] == pytest.approx(67.6945)
    assert SUM["conc_footing"]["verdict"] == "NOT CLOSABLE: boundary band; isolated footings; straps"
    assert SUM["conc_blinding"]["verdict"].startswith("NOT CLOSABLE")


def test_freelancer_reconciled_to_named_causes():
    f = SUM["freelancer"]
    assert f["line_m3"] == pytest.approx(77.6305) and f["isolated_m3"] == pytest.approx(65.634)
    r = SUM["reconcile_isolated"]
    assert r["diff_m3"] == pytest.approx(1.33) and r["residual_m3"] == pytest.approx(0.0, abs=1e-9)
    assert f["blinding_m3"] == pytest.approx(47.055) and f["blinding_basis"] == [15, 31.37, 0.1]


def test_engine_A_isolated_equal_and_strap_excess_named():
    e = SUM["engine_A"]
    assert e["footings_diff_m3"] == pytest.approx(0.0, abs=1e-9)
    assert e["line_total"] == pytest.approx(77.2653, abs=1e-4)
    assert e["straps_diff_m3"] == pytest.approx(0.3904, abs=1e-4)


def test_candidate_v307_named_differences():
    v = SUM["engine_V307"]
    assert v["line_total"] == pytest.approx(76.874817, abs=1e-6)
    assert v["blinding_footing_minus_ours_m3"] == pytest.approx(0.189, abs=1e-5)     # the D-14 part (engine rounds to 1e-6)
    # the SB1 piece inside the unseen F10 outline: engine A carried it, V3.0.7 bounds it 0 .. 0.4025
    assert v["strap_inside_F10_outline_high"] == pytest.approx(0.70 * 0.50 * 1.15, abs=1e-4)


def test_candidate_v308_strap_range_behind_t230():
    v = SUM["engine_V308"]
    assert v["line_measured_plus_provisional"] == pytest.approx(76.8749, abs=1e-6)
    # V3.0.8 carries the T-174 SB3 high end 0.1181; T-230 (merged before it) proved one level per strap: 0.2683
    assert v["sb3_high_end"] == pytest.approx(0.1181) and v["sb3_high_end_T230"] == pytest.approx(0.2683)

"""T-205 on the development villa (research/agents_t205: values, Drive titles and DXF handles only). Established from
'ST7757 dxf.dxf' this run: 36 necks drawn on the FOUNDATION PLAN (36 labels, 36 S-COL.BON outlines), sections from the
column schedule's FOUNDATION band, footings from the footing schedule; the released V2.9 necks (28 lines, 10.8555 m3)
take h = FFL +1.00 + 1.50 - H; the freelancer 8.805 m3 = 34 necks x 1.50 m. Every neck stays HELD on the drawing-derived
method (GB / slab top and formation not printed), and the 2.0505 m3 difference reconciles with no residual."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t205"))
import t205_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.run()


def test_inventory_36_necks_by_type(res):
    from collections import Counter
    c = Counter(r["type"] for r in res["rows"])
    assert res["necks_drawn"] == 36 and res["released_lines"] == 28
    assert c == {"C": 5, "C1": 1, "C2": 4, "C3": 6, "C4": 2, "C5": 3, "C6": 1, "C7": 1, "C8": 2, "C9": 2,
                 "C10": 1, "C11": 2, "CN": 6}


def test_released_reproduced_from_its_convention(res):
    assert res["released_m3"] == pytest.approx(10.8555)
    assert res["released_sum_section_m2"] == pytest.approx(5.34)
    for r in res["rows"]:
        if r["released_m3"] is not None:
            assert r["released_length_m"] == pytest.approx(2.50 - r["footing_H_m"])


def test_reconciliation_closes_with_no_residual(res):
    rec = res["reconciliation"]
    assert rec["freelancer_m3"] == pytest.approx(8.805) and rec["difference_m3"] == pytest.approx(2.0505)
    t = rec["totals_m3"]
    assert t["scope_engine_held"] == pytest.approx(-1.35)     # CN x6 0.81, C10 0.315, 5th C 0.225 (engine HELD)
    assert t["section"] == pytest.approx(-0.165)              # his C11 0.40 x 1.10 vs printed 0.30 x 1.10
    assert t["count"] == pytest.approx(0.72)                  # his missing 6th C3 and 2nd C11 at his 1.50
    assert t["height"] == pytest.approx(2.8455)               # released 2.50 - H vs his flat 1.50
    assert rec["residual_m3"] == pytest.approx(0.0, abs=1e-9)


def test_c11_printed_section_beats_the_freelancer(res):
    c11 = [r for r in res["rows"] if r["type"] == "C11"]
    assert len(c11) == 2 and all(r["section_m2"] == pytest.approx(0.33) for r in c11)
    assert all(r["freelancer_section_m2"] == pytest.approx(0.44) for r in c11)


def test_no_neck_takes_a_finished_level_and_none_is_released(res):
    for r in res["rows"]:
        assert r["drawing_status"] == "HELD" and r["top_datum"] == "GB_TOP"
        assert r["top_m"] is None and r["footing_top_m"] is None


def test_conflicts_and_lift_necks_named(res):
    conf = {r["neck_id"].split(":")[-1] for r in res["rows"] if "SECTION_CONFLICT" in r["held_codes"]}
    assert conf == {"C8@141489,38336", "C1@137485,46080", "C2@137427,44773", "C2@138612,46077", "C9@138589,44775"}
    lift = {r["neck_id"].split(":")[-1] for r in res["rows"] if "PIT_DEPTH_NOT_PRINTED" in r["held_codes"]}
    assert lift == {"C1@137485,46080", "C2@137427,44773", "C2@138612,46077", "C9@138589,44775"}
    ftg = {r["neck_id"].split(":")[-1] for r in res["rows"] if "FOOTING_CONFLICT" in r["held_codes"]}
    assert ftg == {"C10@148899,36778", "C@150972,36507"}
    notes = {r["neck_id"].split(":")[-1] for r in res["rows"] if r["section_note"]}
    assert {"C@131290,36755", "C4@148342,50109"} <= notes        # drawn narrower, schedule + plan text govern


def test_what_if_groups_and_sensitivity(res):
    d = res["drawing_derived"]
    g = d["groups (what_if at b = d = 0, not a quantity)"]
    assert g["printed_section"]["n"] == 23 and g["printed_section"]["released_m3"] == pytest.approx(8.853)
    assert g["printed_section"]["what_if_b0_d0_m3"] == pytest.approx([8.1186, 8.1186])
    assert g["printed_section"]["released_m3"] - g["printed_section"]["what_if_b0_d0_m3"][0] == \
        pytest.approx(0.17 * g["printed_section"]["sum_section_m2"])
    assert g["lift_pit_raft"]["what_if_b0_d0_m3"] is None
    assert d["per_0.10_m_build_up_m3"] == pytest.approx(-0.534)
    assert res["stack_check_neck_vs_gf_column"]["code"] == "HELD"


def test_committed_outputs_match_the_run(res):
    s = json.loads((ROOT / "research" / "agents_t205" / "summary.json").read_text(encoding="utf-8"))
    assert s == json.loads(json.dumps(res, ensure_ascii=False))
    assert (ROOT / "research" / "agents_t205" / "LEDGER_T205.csv").read_text(encoding="utf-8") == A.ledger_csv(res)

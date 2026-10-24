"""T-267 development-villa run (ST-01) pinned: its drawing facts only, the owner rule beside, no line changed.
Hand values: GF -> 1F 4.50 / 27 = 166.667; first 166.667 + 50 - 30 = 186.667, last 166.667 + 30 - 50 = 146.667.
1F -> 2F 4.20 / 25 = 168; first 168 + 50 - 30 = 188, last 168 + 30 - 50 = 148. F0 = F1 = 50 (T-214 DRAWING-CONFIRMED)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t267"
_s = importlib.util.spec_from_file_location("t267_alsenan_check", HERE / "t267_alsenan_check.py")
A = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t267_alsenan_check", A)
_s.loader.exec_module(A)


@pytest.fixture(scope="module")
def s():
    return A.summary(A.load())


def test_committed_summary_regenerates_byte_identical():
    assert (HERE / "summary.json").read_text(encoding="utf-8") == A.render(A.load())


def test_drawing_run_holds_first_and_last_risers(s):
    for key, r in (("GF_1F", 166.667), ("1F_2F", 168.0)):
        d = s["runs"]["DRAWING"][key]
        assert d["finished_riser_mm"] == pytest.approx(r, abs=1e-3)
        assert d["first_structural_riser_mm"] is None and d["last_structural_riser_mm"] is None
        assert d["first_last_status"] == ["HELD", "HELD"]
        assert d["marble_tread_m2_measured"] == 0                       # no stair finish material printed


@pytest.mark.parametrize("key,first,last", [("GF_1F", 186.667, 146.667), ("1F_2F", 188.0, 148.0)])
def test_owner_rule_run_beside(s, key, first, last):
    d = s["runs"]["OWNER_RULE_UP_STAIR_006"][key]
    assert d["first_structural_riser_mm"] == pytest.approx(first, abs=1e-3)
    assert d["last_structural_riser_mm"] == pytest.approx(last, abs=1e-3)
    assert d["closure"]["closes"] and d["closure"]["slab_to_slab_mm"] == pytest.approx(4500.0 if key == "GF_1F" else 4200.0)


def test_counts_conflict_listed_and_ms1l_held(s):
    d = s["runs"]["DRAWING"]["GF_1F"]
    assert d["risers"] == 27 and "EXTRA_OR_MISSING_STEP" in d["findings"]
    own = {(x["component"], x["part"]): x for x in s["runs"]["OWNER_RULE_UP_STAIR_006"]["GF_1F"]["lines"]}
    assert own[("CONCRETE", "flight MS1-L")]["status"] == "HELD"
    assert own[("CONCRETE", "flight MS1-T")]["status"] == "HELD"                 # winders: no drawn soffit
    assert own[("HANDRAIL", "flight MS1-T")]["status"] == "UNSUPPORTED"
    assert own[("BARS", "all")]["quantity"] is None


def test_landings_and_flights_reconcile_with_the_merged_t258_ledger(s):
    own = {x["part"]: x["quantity"] for k in ("GF_1F", "1F_2F")
           for x in s["runs"]["OWNER_RULE_UP_STAIR_006"][k]["lines"] if x["component"] == "CONCRETE"}
    assert own["landing MS1-LD"] == pytest.approx(0.2304)                       # 1.20 x 1.20 x 0.16, T-258 VERIFIED
    assert own["landing MS2-LD-W"] == pytest.approx(0.2392)                     # 1.30 x 1.15 x 0.16
    assert own["landing MS2-LD-E"] == pytest.approx(0.2304)
    for r in s["reconciliation_t258"]:
        assert r["t267_gross_m3"] == pytest.approx(r["frozen_straight_flight_m3"], abs=1e-6)
        assert abs(r["residual_m3"]) <= 1e-4                                     # gross = T-258 net + owned elsewhere


def test_split_level_landing_and_goings(s):
    d = s["runs"]["DRAWING"]["1F_2F"]
    assert [(f["risers"], f["goings"]) for f in d["flights"]] == [(12, 11), (12, 11)]   # + 1 transition riser = 25
    assert d["risers"] == 25
    assert all(f["run_change_mm_at_280_300"] == [-220.0, 0.0] for f in d["flights"])   # 11 x (280 - 300)


def test_code_not_verified_and_applicability_not_decided(s):
    for run in s["runs"].values():
        for d in run.values():
            assert d["code"] == "CODE_NOT_VERIFIED" and d["code_applicability_decided"] is False

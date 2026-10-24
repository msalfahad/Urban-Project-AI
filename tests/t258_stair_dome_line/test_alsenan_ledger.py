"""T-258 development-villa ledger pinned: CONC.STAIR_DOME components, each once, from the committed input file."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t258"
_s = importlib.util.spec_from_file_location("t258_alsenan_check", HERE / "t258_alsenan_check.py")
A = importlib.util.module_from_spec(_s)
sys.modules.setdefault("t258_alsenan_check", A)
_s.loader.exec_module(A)


@pytest.fixture(scope="module")
def run():
    s, comps = A.summary(A.load())
    return s, {c["id"]: c for c in comps}


def test_committed_files_regenerate_byte_identical():
    js, cs = A.render(A.load())
    assert (HERE / "summary.json").read_text(encoding="utf-8") == js
    assert (HERE / "LEDGER_T258.csv").read_text(encoding="utf-8") == cs


def test_components_and_classes(run):
    s, c = run
    assert s["components"] == 46
    assert s["by_class"] == {"CLOSABLE": 13, "CONFLICT": 1, "HELD": 11, "UNKNOWN": 1, "OWNED_ELSEWHERE": 14,
                             "BESIDE": 6}
    t = s["totals"]
    assert t["closable_total"] == pytest.approx(10.855885, abs=2e-6)
    assert t["closable"]["VERIFIED"] == pytest.approx(8.344131, abs=2e-6)
    assert t["conflict"] == pytest.approx([0.863029, 1.054813], abs=2e-6)
    assert t["line_closable"] is False


def test_checker_verified_figures_reproduced(run):
    _, c = run
    assert c["ST01-MS1-U"]["value"] == pytest.approx(0.9976, abs=1e-4)      # Checker 2026-10-22 17:18
    assert c["ST01-MS2-L"]["value"] == pytest.approx(1.033445, abs=2e-6)    # Checker 01:57 / T-187
    assert c["ST01-MS2-U"]["value"] == pytest.approx(1.001373, abs=2e-6)    # T-187 Gate B
    assert c["ST01-MS1-LD"]["value"] == pytest.approx(0.2304, abs=1e-9)
    assert c["DOME-A-SHELL"]["value"] == pytest.approx(2.540681, abs=1e-6)  # T-185 / V3.0.7
    assert c["ST02-RS-S"]["value"] + 0.028928 == pytest.approx(0.9716, abs=1e-4)  # Checker gross 0.9716


def test_ms2_landing_conflict_closed_by_the_flight_edge(run):
    s, c = run
    r = s["retired_readings"][0]
    assert r["accepted"] is False
    assert r["overlap_with_flight_m3"] == pytest.approx(0.0096, abs=1e-9)
    assert r["well_end_m3"] == pytest.approx(0.0008, abs=1e-9)
    assert c["ST01-MS2-LD-W"]["value"] + c["ST01-MS2-LD-E"]["value"] == pytest.approx(0.4696, abs=1e-9)
    # 0.480 = 0.4696 + flight overlap + well end: nothing lost, nothing counted twice
    assert 0.4696 + r["overlap_with_flight_m3"] + r["well_end_m3"] == pytest.approx(0.480, abs=1e-9)


def test_held_stays_held_never_zero(run):
    _, c = run
    for i in ("ST01-MS2-TR", "ST01b-D1-WAIST", "ST03-E1-WAIST", "ST02-RS-C", "ST02-RS-C-SOFFIT", "DOME-3-SHELL",
              "DOME-A-DRUM", "ST01-MS1-T", "ST01-MS1-T-SLAB"):
        assert c[i]["value"] is None and c[i]["cls"] in ("HELD", "UNKNOWN"), i
    assert c["ST01-MS1-L"]["cls"] == "CONFLICT" and c["ST01-MS1-L"]["value"] is None


def test_floor_landings_and_rings_are_other_lines(run):
    _, c = run
    for i in ("ST01-ARR-1F", "ST01-ARR-2F", "ST02-PLATE"):
        assert c[i]["owner_line"] == "SLAB" and c[i]["cls"] == "OWNED_ELSEWHERE"
    for i in ("DOME-A-RING", "DOME-B-RING", "ST01-MS1-U-HEAD", "ST01-MS2-U-HEAD", "ST01-MS2-L-FOOT", "ST01-B3"):
        assert c[i]["owner_line"] == "BEAM"


def test_freelancer_reconciliation(run):
    s, _ = run
    rec = s["reconciliation"]
    assert rec["ST01"]["flights"]["residual"] == pytest.approx(0.0, abs=1e-5)
    assert rec["ST01"]["landings"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert rec["ST03"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert rec["DOMES"]["residual"] == pytest.approx(0.0, abs=1e-9)
    f = json.loads((HERE / "ALSENAN_STAIR_DOME_INPUT.json").read_text(encoding="utf-8"))["freelancer"]
    parts = sum(f[k]["m3"] for k in ("main_flights", "main_landings", "stair_2", "entrance", "domes"))
    assert parts == pytest.approx(f["total"]["m3"], abs=1e-4)

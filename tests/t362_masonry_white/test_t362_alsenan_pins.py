"""T-362 development-villa pins (read-only over merged ledgers; no drawing is read): outputs reproduce byte for byte,
black levels conserve against T-355 r2, white junction population equals T-355's 66 held white junctions, headline
figures and two hand-checked walls."""

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t362"))
import t362_alsenan as A  # noqa: E402

OUT = ROOT / "research" / "agents_t362"


@pytest.fixture(scope="module")
def built():
    return A.outputs()


def test_outputs_reproduce(built):
    for name, t in built[0].items():
        assert (OUT / name).read_text(encoding="utf-8") == t, name


def test_black_conserves_against_t355(built):
    S = built[1]
    b, a = S["black_t355"], S["black_restated_r_t362_3"]
    assert b["net_m"] == 543.4739 and b["levels"] == a["levels"] == 212
    # net + held + lintel cut is the same block, only reclassified
    assert a["net_m"] + a["held_m"] + a["cut_lintel_m"] == pytest.approx(b["net_m"] + b["held_m"] + b["cut_lintel_m"],
                                                                        abs=2e-4)
    assert a["net_m"] == 545.306 and a["held_m"] == 158.5505
    assert S["black_held_by_cause_restated_m"]["LINTEL_BEARING"] == 2.15     # D-GF-10 0.55 + D-1F-03 / D-1F-04 0.80


def test_bearings_cut_only_where_jambs_are_tied():
    rows = list(csv.DictReader(open(OUT / "LINTEL_BEARINGS_T362.csv", encoding="utf-8")))
    cut = {r["opening"]: float(r["bearing_cut_m"]) for r in rows if r["status"].startswith("CUT")}
    held = {r["opening"]: float(r["bearing_held_m"]) for r in rows if r["status"].startswith("HELD")}
    assert cut == {"D-1F-02": 0.8, "D-1F-05": 0.52, "D-1F-06": 0.8, "D-1F-07": 0.5093, "D-2F-03": 0.6493,
                   "D-GF-13": 0.8}
    assert held == {"D-1F-03": 0.8, "D-1F-04": 0.8, "D-GF-06": 0.8, "D-GF-10": 0.55}
    assert round(sum(cut.values()), 4) == 4.0786


def test_white_junctions_equal_t355_white_holds(built):
    wl = built[2]
    for fam in ("A", "B"):
        T = [t for t in wl["ties"] if t["family"] == fam]
        assert len(T) == 66
        assert sum(1 for t in T if t["state"] == "MEASURED") == 26
        assert all(t["ties"] is None for t in T if t["state"] != "MEASURED")     # held never 0


def test_white_headlines(built):
    S = built[1]
    a, b = S["white_family_A"]["total"], S["white_family_B"]["total"]
    assert (a["certain_net_m"], a["band_held_m"], a["ties"]) == (310.8312, 10.0, 111)
    assert (b["certain_net_m"], b["band_held_m"], b["ties"]) == (412.4188, 0.0, 142)
    assert "NOT CHOSEN" in S["white_status"]


def test_hand_walls(built):
    w = {r["wall_id"]: r for r in built[2]["walls"]}
    # GF-W11: 7.00 m of block, no opening, top 3.75: A levels 0.762 .. 3.021 (4) -> 28.00; B 0.612 .. 3.627 (6) -> 42.00
    assert (w["GF-W11"]["A_levels"], w["GF-W11"]["A_certain_net_m"]) == (4, 28.0)
    assert (w["GF-W11"]["B_levels"], w["GF-W11"]["B_certain_net_m"]) == (6, 42.0)
    # 1F-W08: 3.60 m, top 3.45: A 4 x 3.60 = 14.40; B 5 x 3.60 = 18.00
    assert (w["1F-W08"]["A_certain_net_m"], w["1F-W08"]["B_certain_net_m"]) == (14.4, 18.0)


def test_unknown_walls_held_by_name():
    rows = list(csv.DictReader(open(OUT / "UNKNOWN_WALLS_T362.csv", encoding="utf-8")))
    assert len(rows) == 7 and all(r["mesh"] == r["sharmat"] == "HELD" for r in rows)
    assert {r["wall_id"] for r in rows if r["block_type"] == "-"} == {"GF-H01", "GF-H02"}


def test_summary_conditional_totals_never_merge_families():
    S = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    keys = set(S["villa_mesh_conditional_m"])
    assert keys == {"black restated + white family A", "black restated + white family B"}

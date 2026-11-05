"""T-539 pins on the development villa (committed ids and numbers only; no drawing read): accessory ledgers V2."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t539"))
import t539_alsenan as B  # noqa: E402

T = B.texts()
FRESH = Path(tempfile.gettempdir()) / "t539_out"


def test_builder_reproduces_committed_outputs():
    bad = [k for k, v in T.items() if not (B.OUT / k).exists() or (B.OUT / k).read_text(encoding="utf-8") != v]
    if bad:
        FRESH.mkdir(exist_ok=True)
        for k, v in T.items():
            (FRESH / k).write_text(v, encoding="utf-8")
    assert not bad, f"stale {bad}; fresh copies in {FRESH}"


S = json.loads(T["SUMMARY_T539.json"])
B_ = B.build()


def test_the_13_ends_ties_reconcile_to_t526_plus_30():
    e = S["end_ties"]
    assert S["ends"] == {"listed": 12, "held": ["GF-W20 end 1"]}
    assert e["measured_nr"] == 18 and e["measured_ends"] == ["1F-W09 e0 6", "2F-W00 e1 6", "2F-W01 e0 6"]
    assert e["held_015_figures"] == {"1F-W23": {"S-A": 6, "S-B": 5, "S-C": 4}, "2F-W08": {"S-A": 6, "S-B": 6, "S-C": 5}}
    # 18 measured + 12 at the S-A what-if = the +30 T-526 carried on T-355's 0.200 course
    assert e["t526_carried_nr"] == 30.0 and e["t355_primary_on_ends_nr"] == 30
    assert e["measured_nr"] + sum(v["S-A"] for v in e["held_015_figures"].values()) == 30
    assert e["d39_2f_tie_range_0200"] == {"2F-W00": [6, 6], "2F-W01": [6, 6]}


def test_strip_ends_add_nothing_and_015_walls_held():
    s = S["strip_v2"]
    assert S["end_strip_added_m"] == 0.0 and s["end_added_m"] == 0.0
    assert s["t355_net_m"] == 543.4739 and s["v2_measured_net_m"] == 175.4844 and s["v2_measured_walls"] == 9
    assert s["held_015"]["walls"] == 25 and s["held_015"]["t355_net_m"] == 367.9895
    assert s["held_015"]["figures_net_m"] == {"S-A": 367.9895, "S-B": 357.6506, "S-C": 289.2131}
    assert round(s["v2_measured_net_m"] + s["held_015"]["t355_net_m"], 4) == s["t355_net_m"]


def test_strip_s_b_figures_equal_t355_alt210():
    import csv
    alt = {r["wall_id"]: r for r in csv.DictReader(open(B.RES / "agents_t355/MESH_BY_WALL_T355.csv", encoding="utf-8"))}
    for r in B_["strip"]:
        if r.get("fig_S-B_net_m") is not None:
            assert abs(r["fig_S-B_net_m"] - float(alt[r["wall_id"]]["alt210_net_m"])) < 1e-6, r["wall_id"]
            assert r["state"] == "HELD" and r["net_m"] is None


def test_interior_ties_020_identical_015_moved_to_held():
    i = S["ties_v2_interior"]
    assert S["ties_t355_interior"]["measured_nr_t355"] == 182
    assert S["ties_t355_interior"]["moved_to_held_015"]["junctions"] == 8
    assert S["ties_t355_interior"]["moved_to_held_015"]["ties_t355"] == 49
    assert i["ties_measured"] == 133 and i["junctions"] == 117
    assert i["figures_015"] == {"S-A": 49, "S-B": 44, "S-C": 36}
    assert S["ties_v2"]["ties_measured"] == 151 and S["ties_v2"]["junctions"] == 130
    import csv
    alt = {(r["wall_id"], r["column_at"], r["face"]): r for r in
           csv.DictReader(open(B.RES / "agents_t355/SHARMAT_T355.csv", encoding="utf-8"))}
    for r in B_["ties"]:
        if r["population"] == "INTERIOR" and r["figures"]:
            assert r["figures"]["S-B"] == int(alt[(r["wall_id"], r["column_at"], r["face"])]["alt210_ties"])
        if r["population"] == "INTERIOR" and r["state"] == "MEASURED":
            assert r["ties"] == r["t355_ties"]


def test_vjoint_mesh_reconciles_owner_and_names_the_drawing_residual():
    v = S["end_vjoint"]
    assert (v["owner_m"], v["drawing_m_t317_raw"]) == (40.9, 44.1) == (v["t526_owner"], v["t526_drawing"])
    assert v["drawing_m_classed"] == 44.2                      # GF-W16 EXT side: one band 3.75 vs raw 3.65
    gf16 = [x for x in B_["vj"] if x["wall_id"] == "GF-W16" and x["side"] == "EXT"][0]
    assert (gf16["owner_m"], gf16["drawing_m"], gf16["t317_drawing_m"]) == (3.75, 3.75, 3.65)
    assert v["held_end_sides"] == 14
    a, b = S["vjoint_by_class_before"], S["vjoint_by_class_after"]
    assert round(sum(b[k]["owner_band_m"] - a[k]["owner_band_m"] for k in a), 4) == 40.9
    assert round(sum(b[k]["drawing_band_m"] - a[k]["drawing_band_m"] for k in a), 4) == 44.2
    assert a["C"]["owner_band_m"] == 230.1439 and b["C"]["owner_band_m"] == 233.8939


def test_slivers_never_give_a_head():
    sl = S["end_piece_slivers"]
    assert len(sl) == 6 and sorted(k for k, v in sl.items() if v.startswith("OTHER")) == ["GF-W10 e1", "GF-W25 e0"]
    for e in B_["ends"]:
        if e["end_piece_sliver"].startswith("OTHER"):
            assert e["ties"] is None and e["vjoint_owner_m"] is None
    i = S["interior_slivers"]
    assert (i["SAME_MEMBER"], i["OTHER_MEMBER"], i["other_member_with_known_top"]) == (48, 2, [])


def test_no_held_row_carries_a_quantity():
    for r in B_["ties"]:
        if r["state"] != "MEASURED":
            assert r["ties"] is None
    for r in B_["strip"]:
        if str(r["state"]).startswith("HELD"):
            assert r["net_m"] is None and r["held_m"] is None
    for r in B_["vj"]:
        if r["state"] == "HELD":
            assert r["owner_m"] is None and r["drawing_m"] is None


def test_line_families_carry_the_v2_quantities():
    fam = json.loads(T["LINE_FAMILIES_T539.json"])
    q = {f["proposed_code"]: f["quantity_v2_alsenan"] for f in fam}
    assert q["MAS.TIE.SHARMAT"] == {"measured_nr": 151, "held_junctions": 104}
    assert q["MAS.MESH.BED_JOINT"] == {"measured_net_m": 175.4844, "held_015_walls": 25}


def test_2f_datum_d39_moves_no_tie_or_strip_and_upper_bound_named():
    d = S["d39_2f_sensitivity"]
    assert d["ties_moving"] == [] and d["strip_moving"] == []
    assert d["ties"]["2F-W00"] == {"v2": 6, "low": 6, "high": 6} and d["ties"]["2F-W06"]["v2"] == 24
    assert S["end_ties"]["measured_with_upper_bound"] == ["2F-W00 e1"]

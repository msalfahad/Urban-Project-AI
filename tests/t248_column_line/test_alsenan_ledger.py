"""T-248 Alsenan CONC.COLUMN ledger (columns + necks) from committed inputs only (T-217 inventory re-extracted from
Drive 'ST7757 dxf.dxf' sha 9f9d1179, T-205 necks, T-119 owner split, route G register, released A digest, freelancer
cells). Re-runs the check without writing and pins the engineering results (development villa; not an accuracy claim)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t248"
sys.path.insert(0, str(HERE))
import t248_alsenan_check as C  # noqa: E402

ROWS, MEMBERS, STACK, UNUSED, INP, SEC = C.build()
FL, FT = C.freelancer()
BYM = C.by_mark(ROWS, FL)
SUM = C.summarise(ROWS, STACK, UNUSED, INP, FL, FT)


def test_every_member_once_against_the_engine_free_inventory():
    inv = SUM["inventory"]
    assert inv["columns"] == 59 and inv["by_storey"] == {"GF": 30, "1F": 20, "2F": 9} and inv["necks"] == 36
    ids = [r["member"] for r in ROWS]
    assert len(ids) == len(set(ids)) == 59 + 36 + 5
    assert INP["t217_inventory_reproduced"] is True and len(INP["t119_binding"]) == 59 and INP["t119_unbound"] == []
    assert max(v["bind_mm"] for v in INP["t119_binding"].values()) <= 1


def test_components_split_closable_conflict_held_unknown():
    c = SUM["columns_all_storeys"]
    assert c["DRAWING-CONFIRMED"] == [28, pytest.approx(18.3465, abs=1e-6)]
    assert c["CONFLICT"] == [15, pytest.approx(8.034, abs=1e-6), pytest.approx(10.119, abs=1e-6)]
    assert c["HELD"][0] == 16 and c["UNKNOWN"] == [5]
    gf, f1, f2 = (SUM["components_by_storey"][s] for s in ("GF", "1F", "2F"))
    assert gf["DRAWING-CONFIRMED"] == [19, pytest.approx(14.0625)] and f1["DRAWING-CONFIRMED"] == [9, pytest.approx(4.284)]
    assert f2["DRAWING-CONFIRMED"] == [0, 0.0] and f2["HELD"][0] == 9      # 2F roof datum D-39: every 2F column held
    n = SUM["necks"]
    assert n["HELD"][0] == 36 and n["DRAWING-CONFIRMED"] == [0, 0.0]       # formation unprinted (Q-21 C)
    assert n["HELD"][1] == pytest.approx(9.2568, abs=1e-6) and n["HELD"][3] == 36   # lower bound only, never a value


def test_held_never_zero_and_unknown_never_valued():
    for r in ROWS:
        if r["status"] == "UNKNOWN":
            assert r["m3_lo"] is None and r["m3_hi"] is None and "D-65" in r["causes"]
        if r["status"] == "HELD":
            assert r["causes"] and (r["m3_lo"] is None or r["m3_lo"] > 0)
            assert r["m3_lo"] is None or r["m3_hi"] is None or r["m3_hi"] >= r["m3_lo"]


def test_closable_members_equal_route_g_where_a_line_exists():
    d = SUM["closable_vs_route_g"]
    assert d["members"] == 28 and d["differ"] == []
    assert d["no_route_g_line"] == ["FFRS:66A", "FFRS:69D"]               # the two 1F planted columns: missing scope
    assert d["drawing"] - d["route_g_on_them"] == pytest.approx(0.588 + 0.420)
    assert SUM["route_g_register_m3"] == {"GF": pytest.approx(20.25), "1F": pytest.approx(9.66),
                                          "2F": pytest.approx(5.376), "FOUNDATION": pytest.approx(10.8555)}
    assert SUM["route_g_unbound_lines"] == []


def test_each_intersection_once():
    assert SUM["ownership_check"] == [] and SUM["stack_check_neck_to_gf_column"] == []
    pc2f = next(r for r in ROWS if r["member"] == "SFRS:778")
    assert pc2f["top_owner"] == "BEAM_THROUGH" and pc2f["m3_hi"] == pytest.approx(0.10 * (13.15 - 9.65))
    assert set(SUM["released_double_joints_now_column_owned"]) == {"GFRS:347", "GFRS:34A", "GFRS:34D", "GFRS:350",
                                                                   "GFRS:356", "GFRS:359", "FFRS:667"}


def test_no_slab_panel_carries_a_column_and_beam_overlaps_are_named():
    p = SUM["slab_sheet_partition"]
    assert p["solid_outlines"] == 59 and p["slab_overlap"] == {}
    assert set(p["band_overlap"]) == set(SUM["released_double_joints_now_column_owned"]) | {"SFRS:778"}
    assert sum(v for k, v in p["band_overlap"].items() if k.startswith("GFRS")) == pytest.approx(0.3997, abs=5e-4)
    # face-level estimate (min of the face's column and band shares); T-241's polygon value is 0.4401 m2 (GF): the
    # estimate only proves WHICH outlines a band crosses, the m2 of the joints stays T-241's
    conflicts = [r for r in ROWS if "SECTION_CONFLICT" in r["causes"]]
    assert len(conflicts) == 27                                    # T-217's 26 member-storeys + PC-2F (T-220)


def test_footing_identity_1b1b():
    f = SUM["footing_identity_1B1B"]
    assert f["closed"] is False and f["extent_m"] == [3.25, 1.4] and f["open_gap_m"] == pytest.approx(0.7)
    assert {t["text"] for t in f["tags_inside"]} == {"F", "F10"}
    assert {t["handle"] for t in f["tags_inside"]} == {"10A5", "168B"}
    assert f["neck_outlines_inside"] == ["10A4", "10E8"]


def test_freelancer_cells_and_reconciliation():
    assert FT == {"FOUNDATION": pytest.approx(8.805), "GF": pytest.approx(17.4375), "1F": pytest.approx(7.728),
                  "2F": pytest.approx(3.381), "line": pytest.approx(39.7515),
                  "lift_walls": {"row": 11, "l": 8, "b": 0.2, "h": 1.5, "m3": pytest.approx(2.4)}}
    r1 = SUM["reconcile_freelancer"]["1F"]
    assert r1["residual_lo"] == pytest.approx(0, abs=1e-6) and r1["residual_hi"] == pytest.approx(0, abs=1e-6)
    assert r1["drawing"] == [pytest.approx(10.248), pytest.approx(11.928)]
    gf = SUM["reconcile_freelancer"]["GF"]
    assert gf["residual_hi"] == pytest.approx(0, abs=1e-6) and gf["drawing"][0] is None   # annex roof open (Q-54 B)


def test_by_mark_counts_name_his_slips():
    m = {(r["storey"], r["mark"]): r for r in BYM}
    assert (m[("GF", "C2")]["drawn_n"], m[("GF", "C2")]["his_n"]) == (4, 6)
    assert (m[("GF", "C11")]["drawn_n"], m[("GF", "C11")]["his_n"]) == (2, 1)
    assert (m[("1F", "C6")]["drawn_n"], m[("1F", "C6")]["his_n"]) == (1, 0)
    assert (m[("FOUNDATION", "C3")]["drawn_n"], m[("FOUNDATION", "C3")]["his_n"]) == (6, 5)


def test_released_a_digest_pinned():
    d = json.loads((HERE / "RELEASED_A_COLUMN_LINES.json").read_text(encoding="utf-8"))
    assert d["counts"] == {"STR.CONC.COLUMN|1F|BLOCKED_RFI": 22, "STR.CONC.COLUMN|2F|BLOCKED_RFI": 22,
                           "STR.CONC.COLUMN|GF|BLOCKED_RFI": 30, "STR.CONC.COLUMN|UNKNOWN|BLOCKED_RFI": 8,
                           "STR.CONC.NECK|FOUNDATION|BLOCKED_RFI": 1, "STR.CONC.NECK|FOUNDATION|BOUNDED_EXPOSURE": 35}
    assert all(ln["measured_net"] is None for ln in d["lines"])


def test_committed_outputs_reproduce():
    s = json.loads((HERE / "summary.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(SUM, sort_keys=True, ensure_ascii=False)) == s
    rows = list(csv.DictReader(open(HERE / "LEDGER_T248.csv", encoding="utf-8")))
    assert len(rows) == len(ROWS) and [r["member"] for r in rows] == [r["member"] for r in ROWS]


def test_neck_only_members_take_the_zone_of_their_neighbours():
    z = INP["neck_only_zone"]
    assert sorted(z) == ["10EE", "10F6", "10FE", "17C5", "17C8", "180A"]
    assert all(v["zone"] == "MAIN" and v["other_zones_outside"] for v in z.values())
    cn = [r for r in ROWS if r["storey"] == "FOUNDATION" and r["mark"] == "CN"]
    assert len(cn) == 6 and all(r["top_lo"] == r["top_hi"] == 0.95 for r in cn)


def test_candidate_v309_digest_pinned_and_reconciled_by_storey():
    c = SUM["candidate_V309"]["by_floor_state"]
    assert c["STR.CONC.COLUMN|GF|PROVISIONAL"][:2] == [30, pytest.approx(20.25)]
    assert c["STR.CONC.COLUMN|1F|PROVISIONAL"][:2] == [18, pytest.approx(9.24)]
    assert c["STR.CONC.COLUMN|1F|SOURCE_DERIVED"][:2] == [1, pytest.approx(0.588)]
    assert c["STR.CONC.COLUMN|2F|PROVISIONAL"][:2] == [8, pytest.approx(3.528)]
    blocked = sum(v[0] for k, v in c.items() if k.startswith("STR.CONC.COLUMN") and k.endswith("BLOCKED_RFI"))
    assert blocked == 9
    # GF: the candidate = route G on all 30 = closable 14.0625 + CONFLICT at the schedule end 2.475 + held at 4.50 3.7125
    gf = [r for r in ROWS if r["storey"] == "GF"]
    assert sum(r["route_g_m3"] for r in gf) == pytest.approx(20.25)
    assert sum(r["route_g_m3"] for r in gf if r["status"] == "HELD") == pytest.approx(3.7125)
    # 2F: the candidate's 3.528 on the 8 drawn members rests on the finished roof +13.90 (4.20 FFL to finished roof)
    f2 = [r for r in ROWS if r["storey"] == "2F" and r["status"] == "HELD" and r["route_g_m3"] is not None]
    assert len(f2) == 8 and sum(r["route_g_m3"] for r in f2) == pytest.approx(3.528)

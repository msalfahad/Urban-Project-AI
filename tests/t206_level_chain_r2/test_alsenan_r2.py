"""T-206 on the development villa, evidence set R2 (research/agents_t206: values, Drive titles, pages, layers and
handles only). What run 2 established from the drawings: the '2' under the isolated footings is a 2 cm membrane
(underlay 0.07 DRAWING-CONFIRMED on every isolated footing type, not carried to the lift footing whose detail prints
none); six sunken wet panels (5 on the 1F floor, 1 on the 2F floor) whose drop no sheet prints stay HELD; every footing
level stays HELD on the unprinted formation (Q-21 C) while the 'not less than 1.5 m' note stays a limit; the B20 / B23
condition of T-189 stays NOT PROVEN; and the T-200 findings are unchanged."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "research" / "agents_t206"))
import t206_alsenan_check as A  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.run()


def _datum(res, c, k):
    return next((r for r in res["datums"] if r["chain_id"] == c and r["kind"] == k), None)


def _link(res, c, layer):
    return next(r for r in res["links"] if r["chain_id"] == c and r["layer"] == layer)


def _use(res, uid):
    return next(u for u in res["uses"] if u["use_id"] == uid)


def test_t200_input_untouched_and_r2_only_adds():
    base = A.load_t200()
    r2 = A.build_r2()
    assert len(r2["chains"]) == len(base["chains"]) + len(A.FOOTING_H_CM) + len(A.SUNKEN)
    assert all(c in r2["chains"] for c in base["chains"])
    assert "sheets_searched_r2" not in base


def test_t200_findings_unchanged(res):
    assert _use(res, "A1-POOL-WALL-r1")["code"] == "FINISHED_AS_STRUCTURAL"
    assert _use(res, "A2-SILL-W01-r1")["code"] == "WRONG_REFERENCE"
    assert _use(res, "A3-NECK-TOP")["code"] == "FINISHED_AS_STRUCTURAL"
    assert _use(res, "A3-NECK-FOOT")["code"] == "NEEDS_HELD"
    assert _datum(res, "POOL", "FORMATION")["value"] == pytest.approx(-1.50)


def test_b20_b23_condition_not_proven(res):
    for uid in ("A4-STAIR-B20", "A4-STAIR-B23"):
        u = _use(res, uid)
        assert u["code"] == "FINISHED_AS_STRUCTURAL" and "not proven" in u["sensitivity"]
    for c in ("1F-FLOOR", "2F-FLOOR"):
        assert _link(res, c, "FLOOR_BUILD_UP")["status"] == "HELD"


def test_footing_underlay_printed_but_levels_held(res):
    p = A.build_r2()
    ul = {ly["chain_id"]: ly for ly in p["layers"] if ly["layer"] == "UNDERLAY"}
    for t in A.FOOTING_H_CM:
        cid = f"FTG-{t}"
        if t == "FF":
            assert cid not in ul                              # lift detail: no membrane thickness printed
            assert _link(res, cid, "UNDERLAY")["status"] == "HELD"
            assert f"{cid}/layer UNDERLAY" in _link(res, cid, "UNDERLAY")["missing"]
        else:
            assert ul[cid]["thickness"] == pytest.approx(0.07) and ul[cid]["status"] == "DRAWING-CONFIRMED"
        for kind in ("FORMATION", "FOOTING_TOP"):
            d = _datum(res, cid, kind)
            assert d is None or (d["value"] is None and d["status"] == "HELD")
        b = next(b for b in res["bounds"] if b["chain_id"] == cid)
        assert b["bound"] == "AT_MOST" and b["value"] == pytest.approx(-1.5) and b["result"].startswith("OPEN")
    assert ul["GF-EXT-F8"]["thickness"] == pytest.approx(0.07)


def test_footing_table_relations_and_labelled_what_ifs():
    rows = {r["type"]: r for r in A.footing_table()}
    assert rows["F12"]["above_formation"] == {"blinding_top": 0.10, "footing_bottom": 0.17, "footing_top": 0.87}
    assert rows["F12"]["if_formation_at_limit_-1.50"]["footing_top"] == pytest.approx(-0.63)
    assert rows["F8"]["released_convention_footing_bottom_-1.50"] == {"footing_top": -1.0, "implied_formation": -1.67}
    assert rows["FF"]["above_formation"] is None and rows["FF"]["status"].startswith("HELD")
    assert all(r["status"].startswith("HELD") for r in rows.values())


def test_sunken_wet_panels_held(res):
    assert [s[0] for s in A.SUNKEN] == ["1F-WET-275", "1F-WET-276", "1F-WET-280", "1F-WET-287", "1F-WET-298",
                                        "2F-WET-5BF"]
    for cid, storey, *_ in A.SUNKEN:
        assert _datum(res, cid, "FFL")["value"] == pytest.approx(A.STOREY_FFL[storey][0])
        assert _datum(res, cid, "SLAB_TOP")["value"] is None
        assert _link(res, cid, "WET_FLOOR_BUILD_UP")["status"] == "HELD"
        u = _use(res, f"W-{cid}")
        assert u["code"] == "WRONG_REFERENCE" and "HELD" in u["detail"]


def test_written_summary_matches_a_fresh_run():
    path = ROOT / "research" / "agents_t206" / "summary_r2.json"
    s = json.loads(path.read_text(encoding="utf-8"))
    assert s["r2"]["summary"] == A.run()["summary"]
    assert json.loads((ROOT / "research" / "agents_t206" / "ALSENAN_LEVEL_INPUT_R2.json").read_text(
        encoding="utf-8")) == A.build_r2()


def test_sunken_registration_record_and_helpers():
    sys.path.insert(0, str(ROOT / "research" / "agents_t206"))
    import t206_sunken_registration as R
    reg = json.loads((ROOT / "research" / "agents_t206" / "SUNKEN_REGISTRATION.json").read_text(encoding="utf-8"))
    assert len(reg["1F"]["sunken_panels"]) == 5 and len(reg["2F"]["sunken_panels"]) == 1
    for storey in ("1F", "2F"):     # every wet fixture group under a sunken panel, every panel over fixtures
        assert all(f["under_sunken_panel"] for f in reg[storey]["fixture_groups"])
        assert all(p["fixture_groups_overlapping"] for p in reg[storey]["sunken_panels"])
    # helpers: two fixtures 0.3 m apart group, 1.0 m apart do not; overlap tolerance 0.3 m
    assert len(R._group([[0, 0, 1, 1], [1.3, 0, 2, 1]], 0.4)) == 1
    assert len(R._group([[0, 0, 1, 1], [2.0, 0, 3, 1]], 0.4)) == 2
    assert R._overlap([0, 0, 1, 1], [1.2, 0, 2, 1]) and not R._overlap([0, 0, 1, 1], [1.5, 0, 2, 1])

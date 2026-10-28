"""T-244: pins of the development villa's V3.0.20 inputs (research/agents_t244/t244_inputs.py), read from merged
ledgers only. The Alsenan lines themselves are private (Drive); these tests pin the inputs (the hand arithmetic of each
record, from the merged values) and an edited ledger stops the build."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t244"))

import t244_inputs as L  # noqa: E402
from engine.source import arch_v3020 as A  # noqa: E402


def _recs():
    d = A.load_inputs(L.build())
    return {(r["room"], r["item_code"]): r for r in d["records"]}, d


def test_1f11_w17_room_side_hole_bounded_never_the_window_area():
    rs, _ = _recs()
    for c in L.CODES:
        r = rs[("1F-11", c)]
        assert r["before"] == {"evidence_state": "PROVISIONAL", "measured_net": 59.4511}
        assert r["state"] == "BOUNDED" and r["evidence_status"] == "HELD"
        rev = r["revisions"][0]
        assert rev["opening"] == "W17" and rev["before"] == {"m2": 11.0081}
        assert rev["after"]["range"] == [8.7414, 8.9965]
        # hand: 22.149 x 3.35 = 74.19915; - D315 1.76 - D215 1.98 = 70.45915; - 8.9965 / - 8.7414
        assert r["range"][0] == pytest.approx(70.45915 - 8.9965, abs=1e-4)
        assert r["range"][1] == pytest.approx(70.45915 - 8.7414, abs=1e-4)
        assert r["range"][0] - 59.4511 == pytest.approx(2.0115, abs=2e-4)       # the released line was LOW
        assert 9.87 not in rev["after"]["range"]                                  # never the Q-76 A window area


def test_1f13_arched_outline_both_windows_lift_door_still_held():
    rs, _ = _recs()
    for c in L.CODES:
        r = rs[("1F-13", c)]
        assert [v["opening"] for v in r["revisions"]] == ["W15", "W16"]
        assert all(v["after"]["m2"] == 4.3629 and v["before"]["range"] == [4.3629, 4.805] for v in r["revisions"])
        # hand: 132.1575 - doors 9.064 - 2 x 4.3629 = 114.3677; - lift 3.35 = 111.0177
        assert r["range"] == [pytest.approx(111.0177, abs=1e-4), pytest.approx(114.3677, abs=1e-4)]
        assert r["state"] == "BOUNDED" and "lift" in r["reasons"][0]


def test_1f04_2f03_closed_by_the_printed_heads():
    rs, _ = _recs()
    for c in L.CODES:
        a, b = rs[("1F-04", c)], rs[("2F-03", c)]
        assert a["state"] == b["state"] == "RELEASED" and a["evidence_status"] == L.OA
        assert a["value"] == pytest.approx(58.29 - 2.2 - 1.76 - 1.55 * 1.5, abs=1e-9)    # 52.005
        assert b["value"] == pytest.approx(63.315 - 1.98 - 1.76 - 1.2 * 1.5, abs=1e-9)   # 57.775
        assert a["assumption"] and b["assumption"]


def test_deltas_carried_and_not_applied():
    _, d = _recs()
    k = {(x["opening"], x["room"]): x for x in d["deltas"]}
    assert k[("W03", "GF-15")]["kind"] == "CARRIED" and k[("W03", "GF-15")]["m2"] == 18.6369
    assert k[("W03", "GF-08")]["m2"] == 5.93125 and 18.6369 + 5.93125 == pytest.approx(6.731 * 3.65)
    assert k[("W26", "ST-2F")]["kind"] == "NOT_APPLIED" and k[("W26", "ST-2F")]["value_delta"] == -0.165
    assert k[("D-GF-05", "GF-06")]["value_delta"] == k[("D-1F-07", "1F-09")]["value_delta"] == -0.11
    assert all(x["carrier"] for x in d["deltas"] if x["kind"] == "NOT_APPLIED")


def test_every_record_names_a_merged_source():
    _, d = _recs()
    tasks = {s["task"] for s in d["sources"]}
    assert tasks == {"T-302", "T-238", "T-201", "T-237", "T-255"}
    assert all(len(s["sha256"]) == 64 for s in d["sources"])
    assert {r["task"] for r in d["records"]} <= tasks


def test_edited_t302_ledger_stops_the_build(monkeypatch, tmp_path):
    f = tmp_path / "LINE.csv"
    f.write_text(L.T302.read_text(encoding="utf-8").replace("8.7414 .. 8.9965", "8.6000 .. 8.9965"), encoding="utf-8")
    monkeypatch.setattr(L, "T302", f)
    with pytest.raises(SystemExit, match="not the merged one"):
        L.merged_values()


def test_edited_t201_head_stops_the_build(monkeypatch, tmp_path):
    f = tmp_path / "C.csv"
    t = L.T201.read_text(encoding="utf-8")
    i = t.index("\nW24,")
    j = t.index("\n", i + 1)
    f.write_text(t[:i] + t[i:j].replace("2.325", "2.500", 1) + t[j:], encoding="utf-8")
    monkeypatch.setattr(L, "T201", f)
    with pytest.raises(SystemExit, match="W24"):
        L.merged_values()

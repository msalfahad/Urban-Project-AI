"""T-516 on the training villa: the 16 REQUIRED lintels of the merged T-453 r2 ledger, each jamb's masonry read from the
architectural DXF through the merged MASONRY_CENTRELINE_V2 census (research/agents_t516/t516_extract.py; numbers only
committed in out/JAMB_EVIDENCE_T516.csv, sha-pinned). No private file is needed to run these tests.

Hand checks (b_min 0.40 printed 'MIN.40cm', links 5/m, kg/m = d^2/162):
  W14 (L3 3Ø16 + 3Ø14, w 2.45): 0.618 m to the column face / 1.032 m to the far face of the L corner -> BOUNDED both;
      L in [3.25, 4.10]; links [ceil 16.25 = 17, ceil 20.5 = 21]; ceiling (3 x 256 + 3 x 196)/162 x 4.10 = 34.318519 kg.
  D-1F-07 (w 0.80): 0.109 m of its own wall + the 0.15 m cross wall = 0.259 m to the far face -> FLAGGED_DEFICIT (< 0.40);
      other end 1.090 m -> L at most 0.80 + 0.259 + 1.090 = 2.149 m, links at most ceil(10.745) = 11.
  D-GF-11 / D-GF-12: one 0.238 m pier between two REQUIRED doors -> both deficit (< one minimum, let alone two).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t516"))

import t516_jamb_bearing as T  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return T.build()


def by(doc):
    return {r["opening_id"]: r for r in doc["rows"]}


def test_census_16_of_16(doc):
    s = doc["summary"]
    assert s["lintels"] == 16 and s["ends"] == 32
    assert (s["ends_measured"], s["ends_bounded"], s["ends_deficit"], s["ends_held"]) == (0, 21, 10, 1)
    assert sorted(s["lintels_bearing_ok"]) == ["D-1F-02", "D-1F-08", "D-2F-01", "D-GF-13", "W14", "W15"]
    assert len(s["lintels_deficit"]) == 10 and s["lintels_held"] == []


def test_w14_by_hand(doc):
    r = by(doc)["W14"]
    assert r["state"] == T.OK
    assert [e["available_m"] for e in r["ends"]] == [0.618, 1.032]
    assert (r["length_lo_m"], r["length_hi_m"], r["links_lo"], r["links_hi"]) == (3.25, 4.1, 17, 21)
    assert r["straight_ceiling_kg"] == pytest.approx((3 * 256 + 3 * 196) / 162 * 4.10, abs=1e-5)


def test_d1f07_deficit_by_hand(doc):
    r = by(doc)["D-1F-07"]
    s = r["ends"][0]
    assert r["state"] == T.FLAGGED and s["state"] == T.DEFICIT and s["bearing_hi_m"] == 0.259
    assert s["bearing_lo_m"] is None and r["length_lo_m"] is None
    assert r["length_hi_m"] == pytest.approx(2.149, abs=1e-9) and r["links_hi"] == 11


def test_shared_pier_ground_floor(doc):
    b = by(doc)
    assert b["D-GF-11"]["ends"][1]["state"] == T.DEFICIT and b["D-GF-12"]["ends"][0]["state"] == T.DEFICIT
    assert b["D-GF-11"]["ends"][1]["available_m"] == b["D-GF-12"]["ends"][0]["available_m"] == 0.238


def test_never_the_minimum_on_a_deficit_end(doc):
    for r in doc["rows"]:
        for e in r["ends"]:
            if e["state"] == T.DEFICIT:
                assert e["bearing_lo_m"] is None and e["bearing_hi_m"] < 0.40
            if e["state"] == T.HELD:
                assert e["bearing_lo_m"] is None and e["bearing_hi_m"] is None


def test_span_at_least_unchanged_and_t515_ceiling_reread(doc):
    t = doc["t515_effect"]
    assert t["span_at_least_kg"] == 63.161728
    assert t["t515_straight_ceiling_kg_at_exact_0_40"] == 106.954321
    assert t["bearing_ok_true_ceiling_kg"] > t["t515_ceiling_on_ok_lintels_kg"] - 1e-9 or t["bearing_ok_ceiling_held"]


def test_committed_build_equals_build(doc):
    got = json.loads((ROOT / "research/agents_t516/out/JAMB_BEARING_T516.json").read_text(encoding="utf-8"))
    assert got == json.loads(json.dumps(doc, ensure_ascii=False, sort_keys=True))


def test_edited_evidence_refused(tmp_path, monkeypatch):
    p = tmp_path / "e.csv"
    p.write_text(T.EVIDENCE.read_text(encoding="utf-8").replace("0.618", "0.718"), encoding="utf-8")
    monkeypatch.setattr(T, "EVIDENCE", p)
    with pytest.raises(T.JambBearingError):
        T.records()

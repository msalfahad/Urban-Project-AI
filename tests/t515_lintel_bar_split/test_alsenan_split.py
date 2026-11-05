"""T-515 on the training villa, from the sha-pinned merged T-453 r2 lintel ledger + the printed lintel schedule (ST7757
p.13, transcription pinned; re-read by worker 1 on 2026-11-05 from the Drive copy: rows L1 2Ø12 / 2Ø10, L2 2Ø14 / 2Ø12,
L3 3Ø16 / 3Ø14, all 5Ø8/M, MIN.40cm bearing; no cover, no bend length printed). No private file needed.

Hand calculation (kg/m = d^2/162; span = clear opening width):
  L1 per metre of span 2 x 144/162 + 2 x 100/162 = 488/162 = 3.012346 kg/m; 14 lintels, spans 5 x 1.00 + 7 x 0.80 + 0.90
     + 0.50 (W18) = 12.00 m -> 36.148148 kg
  L2 W15 (2 x 196 + 2 x 144)/162 = 680/162 x 1.55 = 6.506173 kg
  L3 W14 (3 x 256 + 3 x 196)/162 = 1356/162 x 2.45 = 20.507407 kg
  AT_LEAST 63.161728 kg = 0.063162 t; ceiling within L (w + 0.80): 488/162 x 23.20 + 680/162 x 2.35 + 1356/162 x 3.25
     = 69.886420 + 9.864198 + 27.203704 = 106.954321 kg (beside, never a quantity)
  links ceil(5 x L): 5 x 9 (L 1.80) + 7 x 8 (1.60) + 9 (1.70) + 7 (1.30) + 12 (2.35) + 17 (3.25) = 146
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t515"))

import t515_lintel_bars as T  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return T.build()


def by(doc):
    return {r["opening_id"]: r for r in doc["rows"]}


def test_totals_by_hand(doc):
    t = doc["total"]
    assert t["state"] == T.AT_LEAST
    assert t["lintels_computed"] == 16 and len(t["lintels_held"]) == 44
    assert t["at_least_kg"] == pytest.approx(488 / 162 * 12.0 + 680 / 162 * 1.55 + 1356 / 162 * 2.45, abs=1e-6)
    assert t["at_least_kg"] == pytest.approx(63.161728, abs=1e-6)
    assert t["at_least_t"] == pytest.approx(0.063162, abs=1e-6)
    assert t["ceiling_straight_kg_beside"] == pytest.approx(106.954321, abs=1e-6)
    assert t["links_over_L"] == 146 and t["links_over_span"] == 82


@pytest.mark.parametrize("oid,kg,links", [("W14", 20.507407, 17), ("W15", 6.506173, 12), ("D-1F-08", 488 / 162 * 0.9, 9),
                                          ("D-GF-06", 488 / 162 * 1.0, 9), ("W18", 488 / 162 * 0.5, 7)])
def test_lintels_by_hand(doc, oid, kg, links):
    r = by(doc)[oid]
    assert r["at_least_kg"] == pytest.approx(kg, abs=1e-6) and r["links_over_L"] == links
    assert set(r["held_parts"]) == {"BOTTOM IN_BEARING", "TOP IN_BEARING", "BOTTOM END_BENDS", "TOP END_BENDS",
                                    "LINKS LINKS"}


def test_band_bars_follow_the_printed_row(doc):
    r = by(doc)
    dia = lambda x, role: [c["dia_mm"] for c in x["components"] if c["role"] == role and c["part"] == "SPAN"][0]  # noqa
    assert (dia(r["W14"], "BOTTOM"), dia(r["W14"], "TOP")) == (16.0, 14.0)    # L3, not the L1 bars
    assert (dia(r["W15"], "BOTTOM"), dia(r["W15"], "TOP")) == (14.0, 12.0)    # L2
    assert (dia(r["D-1F-02"], "BOTTOM"), dia(r["D-1F-02"], "TOP")) == (12.0, 10.0)


def test_held_lintels_blank_never_zero(doc):
    for r in doc["rows"]:
        if r["decision"] != "REQUIRED":
            assert r["state"] == T.HELD and r["at_least_kg"] is None and r["components"] == []
    assert {"W13", "W26"} <= set(doc["total"]["lintels_held"])


def test_no_lap_on_any_lintel(doc):
    for r in doc["rows"]:
        for c in r["components"]:
            if c["part"] == "LAPS":
                assert c["state"] == T.NOT_REQUIRED and c["kg"] == 0.0


def test_freelancer_comparison_unresolved(doc):
    assert doc["freelancer"]["verdict"] == "UNRESOLVED"


def test_committed_ledger_is_the_build(doc, tmp_path):
    p = tmp_path / "LINTEL_BAR_SPLIT_T515.json"
    p.write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    if T.OUT.exists():
        assert T.OUT.read_text(encoding="utf-8") == p.read_text(encoding="utf-8")
    else:
        pytest.fail(f"commit the build: {p}")


def test_edited_input_refused(monkeypatch):
    monkeypatch.setitem(T.PINS, T.LEDGER, "0" * 64)
    with pytest.raises(T.LintelBarError, match="sha256"):
        T.build()

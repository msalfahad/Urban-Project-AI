"""T-531 on the development villa (Alsenan; regression only), from committed records (no private file needed).

Drawing read (worker 1, 2026-11-05, Drive 'Alsenan chalet project' / ST7757.pdf, decoded into .work/private only):
p.13 LINTEL SCHEDULE L1 0-100 B x 20 2Ø12 / 2Ø10, L2 101-200 B x 20 2Ø14 / 2Ø12, L3 201-300 B x 30 3Ø16 / 3Ø14, all
5Ø8/M; LINTEL DETAIL 'MIN.40cm' both ends, bars drawn into the bearings and turned (top down, bottom up), links drawn
inside the bearings too; SECT 2-2 one closed link; no cover, bend, hook or first-link length printed. p.8 note 3: dimensions
are read, never scaled; note 9: 70 d / 40 d development of STARTER bars only; note 22: cover NOT LESS THAN 2.5 cm
(columns, slabs, beams). The structural DXF on Drive carries no detail sheet (plans and schedules only).

Hand calculation (kg/m d^2/162: 12 0.888889, 10 0.617284, 14 1.209877, 16 1.580247; L1 488/162 = 3.012346 per m):
  PRODUCED 6 (D-1F-02 1.00, D-1F-08 0.90, D-2F-01 1.00, D-GF-13 1.00, W14 2.45 L3, W15 1.55 L2):
    3.90 x 3.012346 + 1356/162 x 2.45 + 680/162 x 1.55 = 11.748148 + 20.507407 + 6.506173 = 38.761728 kg AT_LEAST
  FLAGGED 10: spans 1.00 + 0.80 + 0.80 + 0.80 + 0.80 + 1.00 + 0.80 + 0.80 + 0.80 + W18 0.4673 = 8.0673 m (W18: 32.7 mm of
    the opening lies inside column C8, the lintel's own span is 0.4673) x 3.012346 = 24.301496 kg AT_LEAST
  T-515 had W18 over 0.50 m: 63.161728 -> 63.063224 kg (-0.098504 = 0.0327 x 3.012346)
  W18 straight bar ceiling: 0.4673 + C8 depth 0.90 (bars may anchor into the column, never past its far face) + END 0.577
    = 1.9443 m x 3.012346 = 5.856904 kg (T-516 V3 concrete ceiling 1.077 m -> 3.244297 kg is not a BAR ceiling)
  D-1F-04: 0.80 + (0.0797 struct-frame gap + PC depth 0.20) + 2.12 = 3.1997 m -> 9.638602 kg
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t531"))
import t531_lintel_bars_produced as T  # noqa: E402

L1 = 488 / 162


@pytest.fixture(scope="module")
def doc():
    return T.build()


def by(doc):
    return {r["opening_id"]: r for r in doc["rows"]}


def test_parts_by_hand(doc):
    ln = doc["line"]
    assert ln["produced"]["lintels"] == ["D-1F-02", "D-1F-08", "D-2F-01", "D-GF-13", "W14", "W15"]
    assert len(ln["flagged"]["lintels"]) == 10
    assert ln["produced"]["at_least_kg"] == pytest.approx(3.90 * L1 + 1356 / 162 * 2.45 + 680 / 162 * 1.55, abs=1e-6)
    assert ln["produced"]["at_least_kg"] == pytest.approx(38.761728, abs=1e-6)
    assert ln["flagged"]["at_least_kg"] == pytest.approx(8.0673 * L1, abs=1e-6)
    assert ln["state"] == "AT_LEAST" and ln["produced"]["kg"] is None and ln["flagged"]["kg"] is None


def test_reconciles_to_t515_by_the_w18_strip(doc):
    t = doc["reconciliation_total"]
    assert t["t515_at_least_kg"] == pytest.approx(63.161728, abs=1e-6)
    assert t["delta_kg"] == pytest.approx(-0.0327 * L1, abs=1e-6)
    moved = [x for x in doc["reconciliation"] if abs(x["delta_kg"]) > 1e-9]
    assert [x["opening_id"] for x in moved] == ["W18"]


def test_w18_and_column_end_ceilings(doc):
    r = by(doc)
    w = r["W18"]
    assert w["w_net_m"] == pytest.approx(0.4673) and w["bar_straight_hi_m"] == pytest.approx(1.9443)
    assert w["ceiling_straight_kg_beside"] == pytest.approx(1.9443 * L1, abs=1e-6)
    assert w["concrete_length_hi_m"] == pytest.approx(0.4673 + 0.577)
    assert r["D-1F-04"]["bar_straight_hi_m"] == pytest.approx(3.1997)
    assert r["D-2F-03"]["bar_straight_hi_m"] == pytest.approx(0.80 + 0.7492 + 2.15)
    assert r["D-GF-06"]["bar_straight_hi_m"] == pytest.approx(1.00 + 0.759 + 0.166 + 0.25)


def test_masonry_end_ceilings_equal_t516(doc):
    for x in doc["reconciliation"]:
        o = x["opening_id"]
        if o in ("W18", "D-1F-04", "D-2F-03", "D-GF-06"):
            assert x["t531_straight_ceiling_kg"] > x["t516_v3_straight_ceiling_kg"]
        elif x["t516_v3_straight_ceiling_kg"] is None:
            assert x["t531_straight_ceiling_kg"] is None
        else:
            assert x["t531_straight_ceiling_kg"] == pytest.approx(x["t516_v3_straight_ceiling_kg"], abs=1e-5)


def test_every_row_at_least_with_named_holds(doc):
    for r in doc["rows"]:
        assert r["state"] == "AT_LEAST" and r["kg"] is None
        for p in ("B1 EXTENSION_START", "B1 BEND_END", "T1 EXTENSION_END", "S1 LINKS"):
            assert p in r["held_parts"]
        for c in r["components"]:
            if c["state"] == "HELD":
                assert c["kg"] is None


def test_held_ceilings_are_named_not_zero(doc):
    r = by(doc)
    assert r["D-2F-01"]["ceiling_straight_kg_beside"] is None       # END pier search-capped (>= 3.0 m)
    assert r["D-GF-12"]["ceiling_straight_kg_beside"] is None       # END junction HELD
    assert doc["line"]["produced"]["ceiling_held_on"] == ["D-2F-01"]
    assert doc["line"]["flagged"]["ceiling_held_on"] == ["D-GF-12"]


def test_links_provisional_counts(doc):
    r = by(doc)
    s = [c for c in r["W14"]["components"] if c["mark"] == "S1"][0]
    assert s["count_state"] == "PROVISIONAL" and (s["count_lo"], s["count_hi"]) == (17, 21)   # ceil(5 x 3.25) .. 4.10
    s = [c for c in r["D-1F-02"]["components"] if c["mark"] == "S1"][0]
    assert (s["count_lo"], s["count_hi"], s["count_alt_lo"]) == (9, 22, 10)


def test_no_lap_within_stock(doc):
    for r in doc["rows"]:
        if r["bar_straight_hi_m"] is not None:
            assert all(c["state"] == "NOT_REQUIRED" for c in r["components"] if c["part"] == "LAPS")


def test_committed_build_equals_build(doc):
    committed = (ROOT / "research/agents_t531/out/LINTEL_BARS_T531.json").read_text(encoding="utf-8")
    assert committed == T.render(doc)
    assert doc["freelancer"]["verdict"] == "UNRESOLVED"

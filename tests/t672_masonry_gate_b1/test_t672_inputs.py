"""T-672: the URBAN_V3068_INPUTS_V1 document built from the committed merged ledgers (T-670 / T-372 / T-675, sha-pinned):
counts, hand re-derivation of the restated figures and of the perimeter / bed totals, and the module's own checks of it
(load_inputs). No drawing is read here (the Drive chain run is the run of record)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t672"))

import t672_inputs as I  # noqa: E402
from engine.source import arch_v3068 as M  # noqa: E402

R6 = lambda x: round(x + 0.0, 6)  # noqa: E731


@pytest.fixture(scope="module")
def doc():
    return I.build()


def test_counts_and_sources(doc):
    assert [s["task"] for s in doc["sources"]] == ["T-670", "T-372", "T-675"]
    assert len(doc["restate"]) == 74 and sum(r["changed"] for r in doc["restate"]) == 12
    assert len(doc["not_applicable"]) == 4 and len(doc["perimeter"]) == 20 and len(doc["lintel_bed"]) == 9
    d = M.load_inputs(doc)
    assert d["_old"]["rulebook"]["version"] == "1.0.0" and d["_new"]["rulebook"]["version"] == "1.1.0"


def test_restated_figures_by_hand(doc):
    after = {(r["host"], r["item_code"]): r["after"] for r in doc["restate"] if r["changed"]}
    g = "GF-WALLS:walls t=0.15#BLOCKWORK:"
    assert after[(g + "DRAWING_CONFIRMED_BLACK", "MAS.UNITS.BLACK")] == ["VALUE", 107.4375]      # 8.595 x 12.5
    assert after[(g + "ASSUMED___OWNER_APPROVED_BLACK", "MAS.UNITS.BLACK")] == ["VALUE", R6((24.2374 - 0.68) * 12.5)]
    jr = 0.15 * (1 - 0.39 * 0.19 / (0.40 * 0.20))                                                   # 0.0110625
    assert after[(g + "ASSUMED___OWNER_APPROVED_BLACK", "MAS.MORTAR.BLACK")][1] == pytest.approx(23.5574 * jr, abs=1e-6)
    oa1 = after[("1F-WALLS:walls t=0.15#BLOCKWORK:ASSUMED___OWNER_APPROVED_BLACK", "MAS.UNITS.BLACK")]
    assert oa1[0] == "RANGE" and oa1[1] == pytest.approx([(58.2529 - 2.02 - 0.34) * 12.5, (58.2529 - 2.02) * 12.5])
    pts = sum(a[1] for (h, c), a in after.items() if c == "MAS.UNITS.BLACK" and a[0] == "VALUE")
    assert pts == pytest.approx(2571.27625 - 777.05 - 298.75)          # T-670 point total less the two 0.20 hosts


def test_perimeter_and_bed_totals(doc):
    v = [e for e in doc["perimeter"] if e["state"] != "HELD"]
    assert len(v) == 8
    assert sum(e["t372"]["low"] for e in v) == pytest.approx(0.176727, abs=1e-6)
    assert sum(e["t372"]["high"] for e in v) == pytest.approx(0.188035, abs=1e-6)
    env_hi = sum((e.get("t675") or {}).get("envelope", [0, e["t372"]["high"]])[1] for e in v)
    assert env_hi == pytest.approx(0.188035 + 0.017896 + 0.006943, abs=2e-6)
    assert all(e["t372"]["held_cause"] for e in doc["perimeter"] if e["state"] == "HELD")
    f = M.joint_factor(doc["producer"]["joint"], 0.15)
    assert f == pytest.approx(0.001389375)
    b = [e for e in doc["lintel_bed"] if e["state"] != "HELD"]
    assert sum(e["bearing_m"][0] for e in b) == pytest.approx(4.40)
    assert sum(e["bearing_m"][1] for e in b) == pytest.approx(5.48992)
    assert sum(e["low"] for e in b) == pytest.approx(0.006113, abs=1e-6)
    assert [e["opening_id"] for e in doc["lintel_bed"] if e["state"] == "HELD"] == ["D-1F-09"]


def test_adverse_tampered_ledger_refused(doc, monkeypatch):
    monkeypatch.setitem(I.PINS, I.T670, "0" * 64)
    with pytest.raises(SystemExit, match="not the merged ledger"):
        I.build()

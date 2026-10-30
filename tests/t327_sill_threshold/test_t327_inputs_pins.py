"""T-327: the development-villa inputs (research/agents_t327/t327_inputs.py) built from the pinned Checker-merged
files: counts, figures, traces, the A-GF-01 hold, the V3.0.28 line ids re-derived, and an edited ledger stopping the
build. No drawing is read here: the committed ledgers only."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t327"))

import t327_inputs as T  # noqa: E402
from engine.source import arch_v3029 as A  # noqa: E402

PID = "pid-test"


@pytest.fixture(scope="module")
def doc():
    return T.build(PID)


def test_validates_and_counts(doc):
    d = A.load_inputs(doc, PID)
    assert len(d["retype"]) == 5 and len(d["held"]) == 1 and d["sills"] == []
    assert len(d["carried"]) == 54            # 23 KEEP + 26 V3.0.28 window fills + W17 + W18 + W03 x 2 + A-GF-01
    assert all(r["trace_state"] == "TRACED" for r in d["retype"])


def test_retype_figures_by_hand(doc):
    r = {x["opening"]: x for x in doc["retype"]}
    assert set(r) == {"D-GF-02", "D-GF-10", "D-GF-14", "D-1F-03", "D-1F-04"}
    for op in ("D-GF-02", "D-GF-10", "D-GF-14", "D-1F-04"):      # wet: 0.80 x 0.15 marble
        assert (r[op]["target_item"], r[op]["m2"], r[op]["ml"], r[op]["pcs"]) == ("FIN.MARBLE.THRESHOLD", 0.12, 0.8, 1)
    assert (r["D-1F-03"]["target_item"], r["D-1F-03"]["m2"], r["D-1F-03"]["ml"]) == ("FIN.FLOOR.PORCELAIN", 0.15, 1.0)
    assert round(sum(x["m2"] for x in doc["retype"]), 6) == 0.63
    polys = {op: x["closure_polygon_m2"] for op, x in r.items()}
    assert polys == {"D-GF-02": 0.153542, "D-GF-10": 0.1575, "D-GF-14": 0.218846, "D-1F-03": 0.185778,
                     "D-1F-04": 0.131977}
    for op, x in r.items():                       # never the polygon; the excess traced to its residual
        assert x["m2"] < x["closure_polygon_m2"]
        assert abs(x["closure_polygon_m2"] - x["m2"] - x["trace"]["polygon_minus_clear_m2"]) <= 1e-6
        assert abs(x["trace"]["residual_m2"]) <= 1e-4
        assert x["floor_overlap_m2"] <= A.OVERLAP_TOL


def test_d_gf_10_on_the_checkers_width(doc):
    r = next(x for x in doc["retype"] if x["opening"] == "D-GF-10")
    assert r["width_m"] == 0.8 and r["m2"] == 0.12                       # never 0.119556 (not adopted)
    assert r["trace"]["polygon_minus_clear_m2"] == 0.0375 and r["trace"]["residual_m2"] == 0.0
    assert "overrun" in r["trace"]["cause"]


def test_arched_a_gf_01_stays_blank_and_held_gate(doc):
    a = [c for c in doc["carried"] if c["opening"] == "A-GF-01"]
    assert len(a) == 1 and a[0]["m2"] is None and a[0]["line_id"] == "L-868aee125705bb8d17f6"
    assert any("A-GF-01" in n for n in doc["notes"])
    h = doc["held"][0]
    assert (h["opening"], h["item_code"], h["state"]) == ("D-GF-15", "ARCH.THRESHOLD", "UNRESOLVED")
    assert all(h.get(k) in (None, "") for k in ("m2", "ml", "pcs"))


def test_external_doors_and_wet_keep_lines_carried_unchanged(doc):
    c = {x["opening"]: x for x in doc["carried"]}
    for op, m2 in (("D-GF-01", 0.2), ("D-GF-03", 0.18), ("D-GF-06", 0.2), ("D-GF-07", 0.4), ("D-GF-09", 0.18),
                   ("D-2F-01", 0.15)):
        assert c[op]["item_code"] == "ARCH.THRESHOLD" and c[op]["m2"] == m2
    assert not [r for r in doc["retype"] if r["external"]]


def test_v3028_ids_rederived_from_the_t326_element_ids(doc):
    from engine.source import arch_v3028 as A28
    from engine.source import boq_line as BL
    w18 = next(c for c in doc["carried"] if c["opening"] == "W18")
    eid = A28.element_id({"floor": "1F", "opening": "W18", "side": "OUT", "group": "SILL", "status": "VALUED"})
    assert w18["line_id"] == BL.line_id(PID, "ARCH.WINDOW_REVEAL", eid, "R-T326-1", "T-326", "m2")
    assert w18["m2"] == 0.04


def test_edited_ledger_stops_the_build(tmp_path, monkeypatch):
    for p in (T.FILL, T.TRACE):
        cp = tmp_path / p.name
        shutil.copy(p, cp)
        cp.write_text(cp.read_text(encoding="utf-8").replace("0.120000", "0.120001", 1), encoding="utf-8")
        pins = dict(T.PINS)
        pins[cp] = pins.pop(p)
        monkeypatch.setattr(T, "PINS", pins)
        monkeypatch.setattr(T, "FILL" if p == T.FILL else "TRACE", cp)
        with pytest.raises(T.PinError, match="edited ledger"):
            T.build(PID)
        monkeypatch.undo()

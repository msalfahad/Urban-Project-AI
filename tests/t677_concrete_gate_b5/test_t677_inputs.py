"""T-677: the URBAN_V3066_INPUTS_V1 builder (research/agents_t677/t677_inputs.py) on the committed, sha-pinned merged
ledgers: 16 lintels BOUND at R-T673-3 (0.925 .. 1.493412) + the W19 / W20 pier remainder 0 .. 0.003 on one new line
(family 0.925 .. 1.496412 = the T-673 ledger), ST-03 LOWER_ONLY AT_LEAST 0.355017, 3 ground-slab lines REVALUE
(-0.009 / +0.010559 / +0.000868 = +0.002427 m3), the court pair CONFIRM, GB BAND0038 BOUND 0.098008 .. 0.130678 on
the strip 0.326694 m2 (the slab's 0.090 m2 moves to it, both or neither); every id a full candidate id of the
V3.0.65 line index. Adverse: an edited ledger, an index of another version, a lintel whose element is another
opening, a slab whose candidate value moved."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t677"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t677_inputs as T  # noqa: E402
from engine.source import arch_v3066 as A  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return T.build("PID")


def _by(es):
    by = {}
    for e in es:
        by.setdefault(e["action"], []).append(e)
    return by


def test_entries_and_figures(built):
    by = _by(built["entries"])
    assert {k: len(v) for k, v in by.items()} == {"BOUND": 17, "ADD_SHARED": 1, "LOWER_ONLY": 1, "REVALUE": 3,
                                                  "CONFIRM": 2}
    lint = [e for e in by["BOUND"] if e["expect"]["item_code"] == "STR.CONC.LINTEL"]
    assert len(lint) == 16 and all(e["expect"]["low"] is None and e["expect"]["class"] == "HELD" for e in lint)
    lo, hi = round(sum(e["after"]["low"] for e in lint), 6), round(sum(e["after"]["high"] for e in lint), 6)
    sh = by["ADD_SHARED"][0]
    assert (lo, hi) == (0.925, 1.493412) and sh["after"] == {"low": 0.0, "high": 0.003}
    assert round(hi + sh["after"]["high"], 6) == 1.496412
    ix = {e["member"].split(" ")[1]: e["line_id"] for e in lint}
    assert sh["shared_by"] == [ix["W19"], ix["W20"]]
    st = by["LOWER_ONLY"][0]
    assert st["line_id"] == T.ST03 and st["beside"] == {"kind": "AT_LEAST_M3", "value": 0.355017,
                                                       "basis": st["beside"]["basis"]}
    rv = {e["line_id"]: e for e in by["REVALUE"]}
    assert round(sum(e["delta"] for e in rv.values()), 6) == 0.002427
    assert rv[T.SLAB_CUT]["moves_to"] == {"line_id": T.GB38, "plan_m2": 0.09, "why": rv[T.SLAB_CUT]["moves_to"]["why"]}
    assert all(e["expect"]["class"] == "RELEASED" for e in by["CONFIRM"])
    gb = next(e for e in by["BOUND"] if e["line_id"] == T.GB38)
    assert gb["expect"]["low"] == 0.09304 and gb["after"] == {"low": 0.098008, "high": 0.130678}
    ids = {ln["line_id"] for ln in json.loads(T.INDEX.read_text(encoding="utf-8"))["lines"]}
    assert all(e["line_id"] in ids for e in built["entries"] if e.get("line_id"))
    assert A.load_inputs(built, "PID")["_entries"]


def test_released_total_and_strip_once(built):
    """the five B10-05 lines add to the T-674 corrected total; the slab gives up exactly the plan the beam's one
    drawn strip holds beyond the old square-cut deduction (no double count, residual 0)"""
    by = _by(built["entries"])
    five = [e for e in by["REVALUE"] + by["CONFIRM"]]
    after = round(sum(e["after"]["value"] if e["action"] == "REVALUE" else e["expect"]["value"] for e in five), 6)
    assert after == 2.143747
    m = by["REVALUE"][[e["line_id"] for e in by["REVALUE"]].index(T.SLAB_CUT)]
    assert round(0.236694 + m["moves_to"]["plan_m2"], 6) == 0.326694
    assert round(m["delta"], 6) == round(-m["moves_to"]["plan_m2"] * 0.10, 6)


def test_adverse_edited_ledger(monkeypatch):
    monkeypatch.setitem(T.PINS, T.T673, "0" * 64)
    with pytest.raises(SystemExit, match="edited file"):
        T.build()


def _fake(monkeypatch, edit):
    real = T._load

    def fake():
        a, b, c, ix = real()
        a, b, c, ix = copy.deepcopy(a), copy.deepcopy(b), copy.deepcopy(c), copy.deepcopy(ix)
        edit(a, b, c, ix)
        return a, b, c, ix
    monkeypatch.setattr(T, "_load", fake)


def test_adverse_index_of_another_version(monkeypatch):
    _fake(monkeypatch, lambda a, b, c, ix: ix.__setitem__("candidate_version", "ARCH_TAKEOFF_V3.0.64"))
    with pytest.raises(SystemExit, match="index is"):
        T.build()


def test_adverse_lintel_bound_to_another_opening(monkeypatch):
    def edit(a, b, c, ix):
        r = next(r for r in a["lintels"] if r["opening"] == "W24")
        r["opening"] = "W25"
    _fake(monkeypatch, edit)
    with pytest.raises(SystemExit, match="is not the ledger's opening"):
        T.build()


def test_adverse_lintel_range_not_its_arithmetic(monkeypatch):
    def edit(a, b, c, ix):
        r = next(r for r in a["lintels"] if r["opening"] == "W24")
        r["high_m3"] = "0.270000"
    _fake(monkeypatch, edit)
    with pytest.raises(SystemExit, match="is not 0.04"):
        T.build()


def test_adverse_slab_candidate_moved(monkeypatch):
    def edit(a, b, c, ix):
        ln = next(x for x in ix["lines"] if x["line_id"] == T.SLAB_CUT)
        ln["measured_net"] = 0.36
    _fake(monkeypatch, edit)
    with pytest.raises(SystemExit, match="ledger"):
        T.build()

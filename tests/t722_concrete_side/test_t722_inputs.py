"""T-722: the V3.0.73 inputs built from the merged T-707 / T-711 / T-712 / T-721 ledgers and the T-723 map (pins,
rebuilt ledgers, 36 entries + 18 confirmed, every figure recomputed by the module, the three F-T723-1 restatements)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t722"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t722_inputs as T  # noqa: E402
from engine.source import arch_v3073 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return T.build("PID")


def test_ledgers_rebuild_and_pins():
    assert T.rebuild_ledgers() == {"T-707": True, "T-711": True, "T-712": True, "T-721": True}
    for p, s in T.PINS.items():
        assert T._sha(p) == s


def test_counts_and_actions(doc):
    s = T.summary(doc)
    assert s["entries"] == 36 and s["confirm"] == 18
    assert s["by_action"] == {"NARROW": 5, "AT_LEAST": 13, "NAMED": 18}
    assert [list(x) for x in s["restates"]] == [["L-e16c98075f69532a3dc7", "0.135473", "0.135481"],
                                                ["L-0bb78accf8c0a0fbdbaf", "0.242309", "0.242308"],
                                                ["L-d53e5eb08e2c6c668254", "0.147657", "0.147656"]]


def test_module_recomputes_every_figure(doc):
    d = A.load_inputs(doc, "PID")
    lows = {e["line_id"][:10]: e["_low"] for e in d["_entries"] if e["action"] == "NARROW"}
    assert lows == {"L-53f223b0": 0.45738, "L-26f6b6f2": 0.3287, "L-33a9b772": 0.3267, "L-d79d17d1": 0.3287,
                    "L-541c7e56": 0.20136}
    # COLUMN low 11.67283 -> 11.80007 (T-707 family, = T-723 census): +0.12724
    inc = sum(e["_low"] - e["expect"]["low"] for e in d["_entries"] if e["action"] == "NARROW")
    assert inc == pytest.approx(0.12724, abs=1e-9)
    al = {e["line_id"][:10]: e["_value"] for e in d["_entries"] if e["action"] == "AT_LEAST"}
    assert al["L-ab37afa1"] == 0.115155 and al["L-684fcad3"] == 1.903 and al["L-0ede77cf"] == 0.3287
    gb = [e for e in doc["entries"] if e["expect"]["item_code"] == "STR.CONC.GROUND_BEAM" and e["action"] == "AT_LEAST"]
    kept = [c for c in doc["confirm"] if c["source_task"] == "T-712"]
    assert len(gb) == 4 and len(kept) == 13
    # GROUND_BEAM beside family 5.099845 (T-712) = the 17 AT_LEAST (13 kept + 4 here)
    assert sum(float(e["beside"]["value"]) for e in gb) + sum(c["value"] for c in kept) == pytest.approx(5.099845)


def test_no_entry_is_zero_or_a_range(doc):
    for e in doc["entries"]:
        if e["action"] == "AT_LEAST":
            assert float(e["beside"]["value"]) > 0 and not e.get("after")
        if e["action"] == "NAMED":
            assert e.get("beside") is None and not e.get("after")
        if e["action"] == "NARROW":
            assert float(e["after"]["low"]) > 0


def test_adverse_unknown_map_action_refused(monkeypatch):
    real = T._load

    def bad():
        d = real()
        d = copy.deepcopy(d)
        for r in d["723"]["rows"]:
            if r.get("hub") == "T-722" and r["action"] == "TEXT":
                r["action"] = "ADD"
                break
        return d
    monkeypatch.setattr(T, "_load", bad)
    with pytest.raises(SystemExit, match="not wired"):
        T.build()


def test_adverse_ledger_figure_disagrees_with_map(monkeypatch):
    real = T._load

    def bad():
        d = copy.deepcopy(real())
        for r in d["711"]["lines"]:
            if r["line_id"].startswith("L-684fcad3"):
                r["at_least_m3"] = "1.904000"
        return d
    monkeypatch.setattr(T, "_load", bad)
    with pytest.raises(SystemExit, match="is not the ledger"):
        T.build()


def test_json_round_trip(doc):
    assert json.loads(json.dumps(doc)) == doc

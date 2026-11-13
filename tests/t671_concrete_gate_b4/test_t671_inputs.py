"""T-671: the URBAN_V3065_INPUTS_V1 builder (research/agents_t671/t671_inputs.py) on the committed, sha-pinned merged
ledgers: 5 2F roof columns BOUND at R-T669-2 (sum 1.6362 .. 2.295), annex C3 CONFIRM, 5 CN columns NOT_APPLICABLE
(3 bounds set aside, sum 1.134 .. 3.483; 2 blank), GF strip VALUE 0.050 + companion 0 .. 0.025; every id a full
candidate id of the V3.0.64 line index. Adverse: an edited ledger, a short id whose member disagrees, an index of
another version."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t671"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t671_inputs as T  # noqa: E402
from engine.source import arch_v3065 as A  # noqa: E402


@pytest.fixture(scope="module")
def built():
    return T.build("PID")


def test_entries_and_figures(built):
    es = built["entries"]
    by = {}
    for e in es:
        by.setdefault(e["action"], []).append(e)
    assert {k: len(v) for k, v in by.items()} == {"BOUND": 5, "CONFIRM": 1, "NOT_APPLICABLE": 5, "VALUE": 1,
                                                  "ADD_COMPANION": 1}
    lo = round(sum(e["after"]["low"] for e in by["BOUND"]), 6)
    hi = round(sum(e["after"]["high"] for e in by["BOUND"]), 6)
    assert (lo, hi) == (1.6362, 2.295)
    assert all(e["expect"]["element_id"].endswith("|2F") and e["expect"]["low"] is None for e in by["BOUND"])
    na = by["NOT_APPLICABLE"]
    assert all(":CN@" in e["expect"]["element_id"] and e["evidence"]["status"] == "DRAWING-CONFIRMED" for e in na)
    sa = [e["set_aside"] for e in na if e.get("set_aside")]
    assert len(sa) == 3 and round(sum(x["low"] for x in sa), 6) == 1.134 and round(sum(x["high"] for x in sa), 6) == 3.483
    assert by["VALUE"][0]["after"] == {"value": 0.05} and by["VALUE"][0]["expect"]["low"] == 0.04
    c = by["ADD_COMPANION"][0]
    assert c["after"] == {"low": 0.0, "high": 0.025} and c["companion_of"] == T.STRIP
    assert by["CONFIRM"][0]["line_id"] == T.ANNEX_C3
    ids = {ln["line_id"] for ln in json.loads(T.INDEX.read_text(encoding="utf-8"))["lines"]}
    assert all(e["line_id"] in ids for e in es if e.get("line_id"))
    assert A.load_inputs(built, "PID")["_entries"]


def test_adverse_edited_ledger(monkeypatch):
    monkeypatch.setitem(T.PINS, T.T669, "0" * 64)
    with pytest.raises(SystemExit, match="edited file"):
        T.build()


def test_adverse_short_id_member_disagrees():
    ix = {ln["line_id"]: ln for ln in json.loads(T.INDEX.read_text(encoding="utf-8"))["lines"]}
    with pytest.raises(SystemExit, match="is not the ledger's member"):
        T._full(ix, "L-d79d17d1", "C2 2F 20x50")
    with pytest.raises(SystemExit, match="is not the ledger's member"):
        T._full(ix, "L-d79d17d1", "C1 GF 20x50")
    with pytest.raises(SystemExit, match="0 candidate lines"):
        T._full(ix, "L-ffffffff", "C1 2F 20x50")


def test_adverse_index_of_another_version(monkeypatch):
    real = T._load

    def fake():
        a, b, c, ix = real()
        ix = copy.deepcopy(ix)
        ix["candidate_version"] = "ARCH_TAKEOFF_V3.0.63"
        return a, b, c, ix
    monkeypatch.setattr(T, "_load", fake)
    with pytest.raises(SystemExit, match="index is"):
        T.build()

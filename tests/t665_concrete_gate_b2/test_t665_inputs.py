"""T-665: the URBAN_V3063_INPUTS_V1 builder (research/agents_t665/t665_inputs.py) on the committed, sha-pinned merged
files only (no drawing, no Drive): 61 entries, one per T-658 r2 ledger line; the T-658 per-code totals re-add from the
entries and the stated footing bound (asserted inside build); the two Checker downgrades the V3.0.62 index applies
are materialised whole; the footing line is stated from T-595 and NOT wired (its V3.0.11 conflict record); every
entry loads in arch_v3063. Adverse: an edited pinned file stops the build; a
ledger row whose 'before' the candidate does not carry and that is not a restatement stops the build."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t665"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from engine.source import arch_v3063 as A  # noqa: E402
import t665_inputs as I  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return I.build("P")


def test_entries_and_actions(doc):
    c = Counter((e["expect"]["item_code"], e["action"]) for e in doc["entries"])
    assert len(doc["entries"]) == 60 and len({e["line_id"] for e in doc["entries"]}) == 60
    assert c == {("STR.CONC.COLUMN", "CONFIRM"): 23, ("STR.CONC.COLUMN", "UPPER_ONLY"): 6,
                 ("STR.CONC.GROUND_BEAM", "BOUND"): 8,
                 ("STR.CONC.GROUND_BEAM", "CONFIRM"): 5, ("STR.CONC.GROUND_BEAM", "LOWER_ONLY"): 16,
                 ("STR.CONC.STRAP", "CONFIRM"): 2}
    A.load_inputs(json.loads(json.dumps(doc)), "P")


def test_downgrades_whole_and_footing_not_wired(doc):
    dg = {}
    for e in doc["entries"]:
        if e.get("downgrade"):
            dg.setdefault(e["downgrade"]["downgrade_id"], set()).add(e["line_id"])
            assert e["expect"]["class"] == "RELEASED" and e["action"] in ("BOUND", "LOWER_ONLY")
    assert {k: len(v) for k, v in dg.items()} == {"DG-a31a0d7e9dd564ad": 9, "DG-2ddc451c17d2b589": 4}
    for k, v in dg.items():
        e = next(x for x in doc["entries"] if (x.get("downgrade") or {}).get("downgrade_id") == k)
        assert set(e["downgrade"]["line_ids"]) == v
    assert all(e["line_id"] != I.FOOTING_LINE for e in doc["entries"])
    (f,) = doc["not_wired"]
    assert f["line_id"] == I.FOOTING_LINE and "V3.0.11" in f["why"]
    assert f["ledger_bound"] == {"low": 1.96, "high": 2.275} and f["candidate_bound"] == {"low": 2.176, "high": 2.275}


def test_column_ceilings_name_their_datums(doc):
    up = [e for e in doc["entries"] if e["action"] == "UPPER_ONLY"]
    assert round(sum(e["beside"]["value"] for e in up), 6) == 2.80125
    for e in up:
        assert [d["kind"] for d in e["beside"]["datums"]] == ["PRINTED", "APPROVED_DATUM"]


def test_adverse_edited_pin(monkeypatch):
    monkeypatch.setitem(I.PINS, I.T658, "0" * 64)
    with pytest.raises(SystemExit, match="pinned"):
        I.build("P")


def test_adverse_ledger_row_neither_state_nor_restatement():
    r = {"line_id": "L-" + "1" * 20, "item_code": "STR.CONC.COLUMN", "element_id": "X", "status": "BOUNDED",
         "low": "0.5", "high": "0.6", "basis": "x", "item": None, "flags": []}
    ix = {"item_code": "STR.CONC.COLUMN", "element_id": "X", "unit": "m3", "class": "HELD", "held_low": 0.4,
          "held_high": 0.6}
    with pytest.raises(SystemExit, match="bound moves"):
        I._row(r, ix)

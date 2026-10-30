"""T-318: the Alsenan inputs of ARCH_TAKEOFF_V3.0.27 come ONLY from the Checker-merged T-307 / T-316 ledgers (pinned);
their per-status counts and kg are pinned here, and an edited ledger stops the build. No drawing is read."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t318"))

import t318_inputs as L  # noqa: E402
from engine.source import arch_v3027 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return L.build("alsenan-test")


def test_counts(doc):
    c = Counter((x["population"], x["status"]) for x in doc["lines"])
    assert c == {(L.DEV_POP, "BOUND_PART_WITH_HELD"): 59, (L.DEV_POP, "HELD"): 31,
                 (L.DEV_POP, "NOT_APPLICABLE_WITH_EVIDENCE"): 8, (L.TOP_POP, "DRAWING_DERIVED_P15"): 7,
                 (L.TOP_POP, "DRAWING_DERIVED_P15_PART_WITH_HELD"): 68,
                 (L.TOP_POP, "DRAWING_DERIVED_P15_PART_WITH_HELD_LEGS"): 11, (L.TOP_POP, "HELD"): 8,
                 (L.TOP_POP, "UNRESOLVED_TB_PANEL"): 4}
    assert len({x["line_id"] for x in doc["lines"]}) == 196


def test_development_kg(doc):
    d = [x for x in doc["lines"] if x["population"] == L.DEV_POP]
    assert round(sum(x["before"]["low"] for x in d), 3) == 939.794
    assert round(sum(x["before"]["high"] for x in d), 3) == 1741.976
    v = [x["valued"] for x in d if x.get("valued")]
    assert len(v) == 59
    assert (round(sum(x["low"] for x in v), 3), round(sum(x["high"] for x in v), 3)) == (136.573, 150.695)


def test_top_kg_and_closure(doc):
    t = [x for x in doc["lines"] if x["population"] == L.TOP_POP]
    assert round(sum(x["before"]["low"] for x in t), 3) == 781.395
    assert round(sum(x["before"]["high"] for x in t), 3) == 2002.348
    v = [x for x in t if x.get("p15_valued")]
    assert len(v) == 86
    assert round(sum(x["p15_valued"]["low"] for x in v), 3) == 1404.705     # T-316 s.3
    assert round(sum(x["p15_valued"]["high"] for x in v), 3) == 1546.858
    assert round(sum(x["note2_valued"]["low"] for x in v), 3) == 612.076
    assert round(sum(x["note2_valued"]["high"] for x in v), 3) == 1407.226
    # the note-2 split over ALL groups reproduces the line ledger (else build() raises)
    assert abs(sum(x["note2_all"]["low"] for x in t) - sum(x["before"]["low"] for x in t)) < 0.0015 * len(t)


def test_loads_and_envelope(doc):
    inp = A.load_inputs(doc, "alsenan-test")
    acts = Counter(x["action"] for x in inp["lines"])
    assert acts == {"PARENT": 59 + 68 + 11, "RESTATE": 31 + 8 + 4, "NA": 8, "REBASE": 7}
    parts = [x["part"] for x in inp["lines"] if x["population"] == L.TOP_POP and x.get("part")]
    assert (round(sum(p["low"] for p in parts), 3), round(sum(p["high"] for p in parts), 3)) == (612.076, 1618.961)
    for x in inp["lines"]:
        if x["action"] in ("RESTATE", "PARENT"):
            assert x["held"], x["line_id"]


def test_edited_ledger_stops_the_build(monkeypatch):
    monkeypatch.setitem(L.PINS, L.DEV, "0" * 64)
    with pytest.raises(L.PinError):
        L.build()

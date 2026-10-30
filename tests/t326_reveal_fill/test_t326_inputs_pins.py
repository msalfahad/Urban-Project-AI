"""T-326: the development-villa inputs (research/agents_t326/t326_inputs.py) built only from the merged T-313 r2 /
T-325 ledgers: pinned counts and m2 (the T-313 r2 restated missing scope 13.637 m2 and the T-325 sill fill 2.9294
m2), each face once, the 20 door reveals in FIN.PLASTER never added again, the five T-325 doors' floor faces left to
their closure lines, an edited ledger stops the build. No drawing is read here."""
from __future__ import annotations

import shutil
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t326"))

import t326_inputs as T  # noqa: E402
from engine.source import arch_v3028 as A  # noqa: E402


@pytest.fixture(scope="module")
def doc():
    return T.build("p")


def test_counts_and_m2(doc):
    s = T.summary(doc)
    assert (s["fills"], s["fill_m2"]) == (26, 2.9294)                      # 22 raised sills 2.5214 + 4 thresholds 0.408
    assert s["narrow"] == [("D-GF-07", {"low": 1.28, "high": 1.4}, 1.4)]
    assert (s["adds_valued"], s["adds_held"]) == (33, 10)
    assert s["added_m2_by_item"] == {"ARCH.REVEAL": 9.667, "ARCH.WINDOW_REVEAL": 0.04, "FIN.PLASTER": 3.93}
    assert round(sum(s["added_m2_by_item"].values()), 6) == 13.637            # T-313 r2 missing scope


def test_each_face_once_and_loads(doc):
    inp = A.load_inputs(doc, "p")
    assert len(inp["_faces"]) == len(set(inp["_faces"]))
    plaster_doors = {a["opening"] for a in doc["adds"] if a["item_code"] == "FIN.PLASTER"}
    assert plaster_doors == {"D-GF-02", "D-GF-10", "D-GF-14", "D-1F-03", "D-1F-04"}
    d1f03 = next(a for a in doc["adds"] if a["opening"] == "D-1F-03")
    assert round(sum(c["m2"] for c in d1f03["components"]), 6) == 0.81
    carried = Counter((c["source_task"], c["component"]) for c in doc["carried"])
    assert carried[("T-313", "JAMBS")] == carried[("T-313", "HEAD")] == 22
    assert carried[("T-325", "THRESHOLD")] == 27


def test_held_faces_blank(doc):
    held = {(a["opening"], a["side"], a["item_code"]) for a in doc["adds"] if a["status"] == "HELD"}
    assert ("W02", "OUT", "ARCH.REVEAL") in held and ("D-GF-15", "THROUGH", "ARCH.REVEAL") in held
    assert all(c["m2"] is None for a in doc["adds"] if a["status"] == "HELD" for c in a["components"])


def test_edited_ledger_stops_the_build(tmp_path, monkeypatch):
    cp = tmp_path / "REVEAL_LEDGER_T313.csv"
    shutil.copy(T.LED, cp)
    cp.write_text(cp.read_text(encoding="utf-8").replace("0.4,4.0", "0.5,4.0", 1), encoding="utf-8")
    monkeypatch.setattr(T, "LED", cp)
    monkeypatch.setitem(T.PINS, cp, T.PINS[T.LED.__class__(ROOT / "research/agents_t313/REVEAL_LEDGER_T313.csv")])
    with pytest.raises(T.PinError):
        T.build("p")

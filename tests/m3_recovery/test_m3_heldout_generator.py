"""The M3 defect mode of the synthetic generator: the drafting faults found on ST7757 (a 10 mm intervening stub at
line-end beams, a footing drawn by its label only) change the drawing and never the design, and the M3 engine
recovers the design quantities from the defective drawing (the held-out score of 13_HELDOUT_EVALUATION.md, on one
seed that is not in the held-out range)."""

from __future__ import annotations

import json
from pathlib import Path

from engine.source import generic_route as GR
from engine.source import provisional_estimate as PE
from tools import synthetic_villa as SV
from tools import urban_intake as UI

ROOT = Path(__file__).resolve().parents[2]
SEED = 7


def _entities(text):
    i = text.index("ENTITIES")
    return text[i:text.index("ENDSEC", i)]


def _run(dxf, prof):
    I = UI.read(dxf)
    D = GR.detect(I)
    conv = GR.merge_conventions(json.loads((ROOT / "engine/profiles/URBAN_M3_GENERIC_CONVENTIONS_V2.json")
                                           .read_text()), prof)
    items, _, _ = GR.items_from(D, conv, GR.storey_heights(conv))
    PE.check(items, conv)
    return D, items


def _base(items, fam, trade="CONCRETE"):
    return sum(i["base"] for i in items if i["family"] == fam and i["trade"] == trade and
               i["category"] == "PROVISIONAL")


def test_m3_defects_change_the_drawing_not_the_truth(tmp_path):
    clean = SV.generate(tmp_path / "clean", SEED)
    bad = SV.generate(tmp_path / "m3", SEED, m3=True)
    t0 = json.loads(clean.with_name(f"villa_{SEED}.truth.json").read_text())
    t1 = json.loads(bad.with_name(f"villa_{SEED}.truth.json").read_text())
    assert t0["quantities"] == t1["quantities"] and t0["component_list"] == t1["component_list"]
    assert t1["defects_applied"].get("FOOTING_LABEL_ONLY") == 1
    assert t1["defects_applied"].get("INTERVENING_STUB", 0) >= 1
    assert not t0["defects_applied"].get("INTERVENING_STUB")
    # the M2 drafting-noise variant draws exactly as before the M3 mode existed (a separate random stream); the
    # files differ only in the header GUIDs and timestamps ezdxf writes, so the drawn entities are compared
    n1 = SV.generate(tmp_path / "n1", SEED, defects=True).read_text()
    n2 = SV.generate(tmp_path / "n2", SEED, defects=True, m3=False).read_text()
    assert _entities(n1) == _entities(n2) and len(_entities(n1)) > 1000
    assert _entities(clean.read_text()) != _entities(bad.read_text())


def test_m3_engine_recovers_the_design_from_the_defective_drawing(tmp_path):
    bad = SV.generate(tmp_path, SEED, m3=True)
    truth = json.loads(bad.with_name(f"villa_{SEED}.truth.json").read_text())
    prof = json.loads(bad.with_name(f"villa_{SEED}.profile.json").read_text())
    D, items = _run(bad, prof)
    q = truth["quantities"]
    assert abs(_base(items, "FOOTINGS") - q["FOOTINGS"]) <= 1e-6 * q["FOOTINGS"] + 1e-9
    assert abs(_base(items, "BEAMS") - q["BEAMS_TOTAL_DEPTH"]) <= 0.02 * q["BEAMS_TOTAL_DEPTH"]
    states = [f["state"] for r in D["sheets"].values() for f in r.get("footings", [])]
    assert "LABEL_ONLY" in states

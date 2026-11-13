"""R-T763-1 plaster height / wet-room render + band split (T-763). Synthetic rooms only; no project data."""
import importlib.util
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPEC = importlib.util.spec_from_file_location("t763_fill", os.path.join(ROOT, "research", "agents_t763", "t763_fill.py"))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def test_normal_heights_and_split():
    assert M.H["GF"] == pytest.approx(4.34) and M.H["1F"] == pytest.approx(4.04) and M.H["ANNEX"] == pytest.approx(3.84)
    # GF wet room, run 5.00 lm, one door: render 5 x 3.44 - 2.20 = 15.00; band 5 x 0.90 = 4.50
    assert M.wet_render(5.0, "GF") == pytest.approx(15.0)
    assert M.wet_band(5.0, "GF") == pytest.approx(4.5)
    # annex: H - 0.90 = 2.94 is below the 3.00 tile top -> ceiling 3.00; render 4 x 3.00 - 2.20 = 9.80, band 4 x 0.84 = 3.36
    assert M.ceiling("ANNEX") == pytest.approx(3.00)
    assert M.wet_render(4.0, "ANNEX") == pytest.approx(9.8)
    assert M.wet_band(4.0, "ANNEX") == pytest.approx(3.36)
    # render + band = run x H - door, whatever the ceiling split
    for zone, run in (("GF", 6.3), ("1F", 7.1), ("ANNEX", 3.9)):
        assert M.wet_render(run, zone) + M.wet_band(run, zone) == pytest.approx(run * M.H[zone] - M.DOOR)


def test_adverse_missing_run_and_superseded_factor():
    for bad in (None, 0, -1.0):
        with pytest.raises(ValueError):
            M.wet_render(bad, "GF")
        with pytest.raises(ValueError):
            M.wet_band(bad, "1F")
    # the superseded height (band = run x 0.64) is refused
    assert M.wet_band(5.0, "1F") != pytest.approx(5.0 * 0.64)
    # a blank bead arris without a named default is never valued as 0
    with pytest.raises(ValueError):
        M.bead_value([{"bead_state": "HELD_BLANK", "edge_id": "X#NOWHERE", "low": None, "high": None}])


def test_committed_fix_rows_are_labelled():
    d = json.load(open(os.path.join(ROOT, "research", "agents_t763", "out", "FIX_ROWS.json")))
    assert d["overlap_with_MAIN_FILL_ALL"] == 0
    ids = [r["line_id"] for r in d["rows"]]
    assert len(ids) == len(set(ids))
    for r in d["rows"]:
        assert r["label"] in M.LABELS and r["basis"] and r["after"]["net"] > 0 and r["after"]["class"] == "RELEASED"
    for fam in M.FAMILIES:
        assert d["summary"][fam]["held_after"] == 0

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
    # the owner's ceiling defaults are kept as stated: wet / kitchen 2.70, dry H - 0.90
    assert M.ceiling("GF") == pytest.approx(2.70) and M.ceiling("ANNEX") == pytest.approx(2.70)
    assert M.ceiling("GF", wet=False) == pytest.approx(3.44)
    # GF wet room, run 5.00 lm, door 0.80 drawn: render 5 x 3.00 - 0.80 x 2.20 = 13.24; band 5 x 1.34 = 6.70
    om = M.openings_m2(0.80)
    assert om == pytest.approx(1.76)
    assert M.wet_render(5.0, "GF", om) == pytest.approx(13.24)
    assert M.wet_band(5.0, "GF") == pytest.approx(6.70)
    # 1F room with two openings: drawn door 0.80 + a 0.60 window 1.70 .. 2.50 -> 1.76 + 0.48
    om2 = M.openings_m2(0.80, 0.0, ({"id": "w", "w": 0.60, "sill": 1.70, "head": 2.50},))
    assert om2 == pytest.approx(2.24)
    assert M.wet_render(6.0, "1F", om2) == pytest.approx(15.76)
    assert M.wet_band(6.0, "1F") == pytest.approx(6.0 * 1.04)
    # annex: band 4 x 0.84 = 3.36
    assert M.wet_band(4.0, "ANNEX") == pytest.approx(3.36)
    # render + band = run x H - openings, whatever the split
    for zone, run in (("GF", 6.3), ("1F", 7.1), ("ANNEX", 3.9)):
        assert M.wet_render(run, zone, om2) + M.wet_band(run, zone) == pytest.approx(run * M.H[zone] - om2)


def test_adverse_missing_run_openings_and_replaced_defaults():
    for bad in (None, 0, -1.0):
        with pytest.raises(ValueError):
            M.wet_render(bad, "GF", 1.76)
        with pytest.raises(ValueError):
            M.wet_band(bad, "1F")
    # openings not read are never 0
    with pytest.raises(ValueError):
        M.wet_render(5.0, "GF", None)
    with pytest.raises(ValueError):
        M.openings_m2(None)
    with pytest.raises(ValueError):
        M.openings_m2(0.8, 0.0, ({"id": "w", "w": 0.6, "sill": None, "head": 2.5},))
    with pytest.raises(ValueError):          # a window crossing the tile top must be split explicitly
        M.openings_m2(0.8, 0.0, ({"id": "w", "w": 0.6, "sill": 2.2, "head": 3.4},))
    # a drawn 0.80 door is not the 1.00 x 2.20 default doorway; two openings both deducted
    two = M.openings_m2(0.80, 0.0, ({"id": "w", "w": 0.60, "sill": 1.70, "head": 2.50},))
    assert two != pytest.approx(M.DOOR) and two != pytest.approx(0.80 * 2.20)
    # the replaced ceiling max(H - 0.90, 3.00) and the superseded 0.64 band factor are refused
    assert M.ceiling("GF") != pytest.approx(max(M.H["GF"] - 0.90, 3.00))
    assert M.wet_band(5.0, "GF") != pytest.approx(5.0 * (M.H["GF"] - 3.44))
    assert M.wet_band(5.0, "1F") != pytest.approx(5.0 * 0.64)
    # a blank bead arris without a named default is never valued as 0
    with pytest.raises(ValueError):
        M.bead_value([{"bead_state": "HELD_BLANK", "edge_id": "X#NOWHERE", "low": None, "high": None}])


def test_shaft_resolution_refuses_unknown_held_items():
    spec = importlib.util.spec_from_file_location("t763_shaft", os.path.join(ROOT, "research", "agents_t763", "t763_shaft.py"))
    S = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(S)
    face = {"id": "X", "region": [[0, 2, 0, 3]],
            "contacts": [{"id": "MS1-T winders (HELD)", "status": "HELD", "rect": [0, 1, 1, 2]},
                         {"id": "B20 over the wall (HELD)", "status": "HELD", "rect": [0, 2, 2.5, 3]}],
            "openings": [{"id": "GF-passage-E", "status": "HELD", "rect": [0.5, 1.4, 1.0, 5.5]}]}
    out = S.resolve_faces([face])[0]
    assert all(c.get("status", "KNOWN") == "KNOWN" for c in out["contacts"]) and len(out["contacts"]) == 1
    assert out["openings"][0]["status"] == "ASSUMED" and out["openings"][0]["rect"][2:] == [1.0, 3.2]
    bad = {"id": "Y", "region": [[0, 2, 0, 3]], "contacts": [{"id": "unknown pipe", "status": "HELD", "rect": [0, 1, 0, 1]}]}
    with pytest.raises(ValueError):
        S.resolve_faces([bad])
    bad_o = {"id": "Z", "region": [[0, 2, 0, 3]], "openings": [{"id": "W99", "status": "HELD", "rect": [0, 1, 0, 1]}]}
    with pytest.raises(ValueError):
        S.resolve_faces([bad_o])


def test_committed_fix_rows_are_labelled():
    d = json.load(open(os.path.join(ROOT, "research", "agents_t763", "out", "FIX_ROWS.json")))
    assert d["overlap_with_MAIN_FILL_ALL"] == 0
    ids = [r["line_id"] for r in d["rows"]]
    assert len(ids) == len(set(ids))
    for r in d["rows"]:
        assert r["label"] in M.LABELS and r["basis"] and r["after"]["class"] == "RELEASED"
        # a 0 is only a PAINT_EDGE determined zero naming its physical cause; nothing else is ever 0
        assert r["after"]["net"] > 0 or (r["set"] == "PAINT_EDGE" and " 0: " in r["basis"])
    # the wet-room render lines are never the old one-doorway default: every one names its drawn openings
    for r in d["rows"]:
        if r["set"] in ("PLASTER_WET", "RENDER_RESTATE"):
            assert "doors" in r["basis"] and "1.00 x 2.20" not in r["basis"]
    for fam in M.FAMILIES:
        assert d["summary"][fam]["held_after"] == 0

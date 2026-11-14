"""T-782 PROJECT_INPUTS_V1: inputs sheet schema, loader, validator and derived heights.
Synthetic two-storey villa (not the training villa) for normal + adverse cases; the training-villa sheet only for
its acceptance heights 4.34 / 4.04 / annex 3.84."""
import copy
import json
import os

import pytest

from engine.source import project_inputs_v1 as P

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VILLA_1 = os.path.join(ROOT, "research", "agents_t782", "PROJECT_INPUTS_VILLA_1.json")


def rec(v, src="PRINTED", ref="synthetic section A-A"):
    return {"value": v, "source": src, "ref": ref}


def synthetic():
    # two storeys: GF +0.45 -> +3.95 (3.50), 1F +3.95 -> +7.15 (3.20); slab 0.25 GF roof, 0.20 1F roof
    return {
        "schema": "PROJECT_INPUTS_V1", "project_id": "SYNTH-2S",
        "storey_defaults": {"slab_thickness": rec(0.20), "beam_depth_default": rec(0.55, "OWNER-DEFAULT", "co. default"),
                            "ceiling_drop": rec(0.60, "OWNER-DEFAULT", "co. default"),
                            "wet_ceiling_height": rec(2.50, "OWNER-DEFAULT", "co. default"),
                            "wet_tile_height": rec(2.40, "DESIGNER", "designer answer 1")},
        "storeys": [
            {"id": "GF", "ffl": rec(0.45), "next_ffl": rec(3.95), "slab_thickness": rec(0.25)},
            {"id": "1F", "ffl": rec(3.95), "next_ffl": rec(7.15)},
        ],
        "scope": {"foundation_wp": rec(True, "OWNER-DEFAULT", "scope"), "fence": rec(False, "OWNER-DEFAULT", "scope")},
        "grades": {"concrete": rec(35, "PRINTED", "general notes")},
        "wastage_pct": {"tiles": {"value": None, "source": "HELD", "ref": "not given"}},
    }


def test_normal_two_storey_heights_and_labels():
    s = P.load(synthetic())
    assert P.storey_height(s, "GF")["value_m"] == pytest.approx(3.50)
    gf = P.plaster_height(s, "GF")
    assert gf["value_m"] == pytest.approx(3.25) and gf["label"] == "DRAWING-READ"   # all PRINTED
    f1 = P.plaster_height(s, "1F")
    assert f1["value_m"] == pytest.approx(3.00)                                     # storey default slab 0.20
    assert {c["name"] for c in f1["components"]} == {"ffl", "next_ffl", "slab_thickness"}
    dry = P.paint_height(s, "GF")
    assert dry["value_m"] == pytest.approx(2.65) and dry["label"] == "DEFAULT"      # ceiling drop is a default
    assert P.ceiling_height(s, "1F", wet=True)["value_m"] == pytest.approx(2.50)
    wet = P.paint_height(s, "1F", wet=True)
    assert wet["value_m"] == pytest.approx(0.10) and wet["state"] == "DERIVED"     # 2.50 ceiling - 2.40 tile
    assert P.blockwork_height(s, "GF")["value_m"] == pytest.approx(3.25)
    assert P.blockwork_height(s, "GF", under_beam=True)["value_m"] == pytest.approx(2.70)
    pb = P.blockwork_height(s, "GF", under_beam=True, beam_depth_m=0.70, beam_ref="beam schedule B3")
    assert pb["value_m"] == pytest.approx(2.55) and pb["label"] == "DRAWING-READ"
    assert s["scope"]["foundation_wp"]["value"] is True and s["scope"]["fence"]["value"] is False
    assert s["wastage_pct"]["tiles"]["source"] == "HELD" and s["wastage_pct"]["tiles"]["value"] is None
    assert all(not st["flags"] for st in s["storeys"])
    # JSON text and a dict give the same sheet
    assert P.load(json.dumps(synthetic())) == s


def test_adverse_missing_slab_thickness_refused():
    sh = synthetic()
    del sh["storey_defaults"]["slab_thickness"]          # 1F now has no slab thickness at all
    with pytest.raises(P.MissingInputError, match="1F.slab_thickness"):
        P.load(sh)
    sh = synthetic()
    sh["storeys"][0]["slab_thickness"] = {"value": None, "source": "HELD", "ref": "x"}
    with pytest.raises(P.MissingInputError, match="GF.slab_thickness"):
        P.load(sh)
    sh = synthetic()
    sh["storeys"][0]["slab_thickness"] = rec(0)          # 0 is never a stand-in for missing
    with pytest.raises(P.MissingInputError):
        P.load(sh)


def test_adverse_missing_storey_and_bad_records():
    sh = synthetic()
    sh["storeys"] = []
    with pytest.raises(P.MissingInputError):
        P.load(sh)
    sh = synthetic()
    del sh["storeys"][1]["next_ffl"]
    with pytest.raises(P.MissingInputError, match="1F.next_ffl"):
        P.load(sh)
    s = P.load(synthetic())
    with pytest.raises(P.MissingInputError):
        P.plaster_height(s, "2F")                          # a storey not in the sheet is refused, not 0
    for bad, err in ((rec(0.2, "GUESS"), P.InputsError), ({"value": 0.2, "source": "PRINTED"}, P.InputsError),
                     (rec("0.2"), P.InputsError), (0.2, P.InputsError)):
        sh = synthetic()
        sh["storeys"][0]["slab_thickness"] = bad
        with pytest.raises(err):
            P.load(sh)
    sh = synthetic()
    sh["storeys"][1]["next_ffl"] = rec(3.95)               # zero-height storey
    with pytest.raises(P.MissingInputError):
        P.load(sh)
    sh = synthetic()
    sh["storeys"][1]["id"] = "GF"
    with pytest.raises(P.InputsError, match="duplicate"):
        P.load(sh)
    sh = synthetic()
    sh["scope"]["fence"] = rec("yes", "OWNER-DEFAULT", "scope")
    with pytest.raises(P.InputsError):
        P.load(sh)


def test_adverse_held_optional_stays_held_never_zero():
    sh = synthetic()
    sh["storey_defaults"]["beam_depth_default"] = {"value": None, "source": "HELD", "ref": "no default"}
    sh["storey_defaults"]["wet_tile_height"] = {"value": None, "source": "HELD", "ref": "no answer"}
    s = P.load(sh)
    b = P.blockwork_height(s, "GF", under_beam=True)
    assert b["state"] == "HELD" and b["value_m"] is None
    w = P.paint_height(s, "GF", wet=True)
    assert w["state"] == "HELD" and w["value_m"] is None
    assert P.blockwork_height(s, "GF")["value_m"] == pytest.approx(3.25)   # no beam: still derived


def test_split_level_flagged_and_sloped_storey_held():
    sh = synthetic()
    sh["storeys"].append({"id": "MEZZ", "parent": "GF", "ffl": rec(-0.40), "next_ffl": rec(2.60)})
    sh["storeys"].append({"id": "RAMP", "sloped": True, "ffl_low": rec(7.15), "ffl_high": rec(7.65),
                          "next_ffl": rec(10.35)})
    s = P.load(sh)
    mz = P.storey(s, "MEZZ")
    assert "SPLIT_LEVEL:GF" in mz["flags"] and "SPLIT_LEVEL:MEZZ" in P.storey(s, "GF")["flags"]
    assert P.plaster_height(s, "MEZZ")["value_m"] == pytest.approx(2.80)    # derived, but flagged
    assert "SPLIT_LEVEL:GF" in P.plaster_height(s, "MEZZ")["flags"]
    rp = P.storey(s, "RAMP")
    assert rp["flags"] == ["SLOPED"]
    for fn in (P.storey_height, P.plaster_height, P.paint_height, P.blockwork_height):
        r = fn(s, "RAMP")
        assert r["state"] == "HELD" and r["value_m"] is None and "SLOPED" in r["flags"]
    assert not P.storey(s, "1F")["flags"]                    # 1F touches RAMP only at +7.15: no split level


def test_villa_1_sheet_acceptance_heights():
    s = P.load(VILLA_1)
    assert [st["id"] for st in s["storeys"]] == ["GF", "1F", "2F", "ANNEX"]
    assert P.storey_height(s, "GF")["value_m"] == pytest.approx(4.50, abs=1e-9)
    assert P.plaster_height(s, "GF")["value_m"] == pytest.approx(4.34, abs=1e-9)
    assert P.plaster_height(s, "1F")["value_m"] == pytest.approx(4.04, abs=1e-9)
    assert P.plaster_height(s, "2F")["value_m"] == pytest.approx(4.04, abs=1e-9)
    assert P.plaster_height(s, "ANNEX")["value_m"] == pytest.approx(3.84, abs=1e-9)
    assert P.ceiling_height(s, "ANNEX")["value_m"] == pytest.approx(2.94, abs=1e-9)   # MAIN_FILL_2 annex ceiling
    assert P.ceiling_height(s, "GF", wet=True)["value_m"] == pytest.approx(2.70, abs=1e-9)
    assert "SPLIT_LEVEL:GF" in P.storey(s, "ANNEX")["flags"]
    for k in ("foundation_wp", "fence"):
        assert s["scope"][k]["source"] == "HELD" and s["scope"][k]["value"] is None
    # filled only from owner-confirmed values: every non-HELD record is PRINTED or OWNER-DEFAULT with a ref
    raw = json.load(open(VILLA_1, encoding="utf-8"))
    def walk(o):
        if isinstance(o, dict):
            if "source" in o and "value" in o:
                yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    recs = list(walk(raw))
    assert recs and all(r["source"] in ("PRINTED", "OWNER-DEFAULT", "HELD") and r["ref"] for r in recs)


def test_villa_1_sheet_agrees_with_the_r_t763_1_patch():
    """The villa-specific constants of the T-763 fill (R-T763-1) are reproduced by the sheet: the patch can retire."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("t763_fill", os.path.join(ROOT, "research", "agents_t763", "t763_fill.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    s = P.load(VILLA_1)
    for zone in ("GF", "1F", "2F", "ANNEX"):
        assert P.plaster_height(s, zone)["value_m"] == pytest.approx(m.H[zone], abs=1e-9)
        assert P.ceiling_height(s, zone)["value_m"] == pytest.approx(m.ceiling(zone, wet=False), abs=1e-9)
        assert P.ceiling_height(s, zone, wet=True)["value_m"] == pytest.approx(m.ceiling(zone, wet=True), abs=1e-9)
    assert P.storey(s, "GF")["wet_tile_height"]["value"] == pytest.approx(m.TILE_H)

"""T-793 HEIGHT_PROVIDER_V1: storey / plaster / ceiling / paint / wall-tile heights read from PROJECT_INPUTS_V1.
Normal: a synthetic three-storey villa (not the training villa) with other FFLs and slab thicknesses, hand values.
Adverse: missing storey, missing required value, sloped storey, HELD tile top, tile top above H, sheet typed in mm.
Acceptance: the training-villa sheet returns exactly the R-T763-1 constants used by today's candidate."""
import copy
import importlib.util
import json
import os

import pytest

from engine.source import height_provider_v1 as HP

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VILLA_1 = os.path.join(ROOT, "research", "agents_t782", "PROJECT_INPUTS_VILLA_1.json")
T763 = os.path.join(ROOT, "research", "agents_t763", "t763_fill.py")


def rec(v, src="PRINTED", ref="synthetic section B-B"):
    return {"value": v, "source": src, "ref": ref}


def synthetic():
    # GF +0.60 -> +4.20 (3.60), 1F +4.20 -> +7.50 (3.30), 2F +7.50 -> +10.70 (3.20)
    # slabs: default 0.22 printed; 1F roof slab 0.30 printed; ceiling drop 0.75 / wet ceiling 2.55 / tile 2.10 designer
    return {
        "schema": "PROJECT_INPUTS_V1", "project_id": "SYNTH-3S",
        "storey_defaults": {"slab_thickness": rec(0.22),
                            "beam_depth_default": rec(0.50, "OWNER-DEFAULT", "co. default"),
                            "ceiling_drop": rec(0.75, "DESIGNER", "designer answer 4"),
                            "wet_ceiling_height": rec(2.55, "DESIGNER", "designer answer 5"),
                            "wet_tile_height": rec(2.10, "DESIGNER", "designer answer 6")},
        "storeys": [
            {"id": "GF", "ffl": rec(0.60), "next_ffl": rec(4.20)},
            {"id": "1F", "ffl": rec(4.20), "next_ffl": rec(7.50), "slab_thickness": rec(0.30)},
            {"id": "2F", "ffl": rec(7.50), "next_ffl": rec(10.70),
             "wet_tile_height": rec(3.20, "OWNER-DEFAULT", "co. default (tiles to the soffit)")},
        ],
    }


# -------------------------------------------------------------------------------------------------- normal
def test_synthetic_hand_values():
    p = HP.HeightProvider(synthetic())
    assert p.storeys() == ["GF", "1F", "2F"]
    # H = storey - slab: GF 3.60 - 0.22 = 3.38; 1F 3.30 - 0.30 = 3.00; 2F 3.20 - 0.22 = 2.98
    assert p.value("plaster", "GF") == pytest.approx(3.38)
    assert p.value("plaster", "1F") == pytest.approx(3.00)
    assert p.value("plaster", "2F") == pytest.approx(2.98)
    # dry ceiling = H - 0.75: 2.63 / 2.25 / 2.23; wet ceiling 2.55 capped at H (all H > 2.55)
    assert p.value("ceiling", "GF") == pytest.approx(2.63)
    assert p.value("ceiling", "1F") == pytest.approx(2.25)
    assert p.value("ceiling", "GF", wet=True) == pytest.approx(2.55)
    # dry paint to the ceiling; wet paint = wet ceiling - tile top = 2.55 - 2.10 = 0.45
    assert p.value("paint", "1F") == pytest.approx(2.25)
    assert p.value("paint", "GF", wet=True) == pytest.approx(0.45)
    # wet split: render 2.10, band H - 2.10 = 1.28 (GF) / 0.90 (1F); render + band = H
    assert p.value("wet_render", "GF") == pytest.approx(2.10)
    assert p.value("wet_band", "GF") == pytest.approx(1.28)
    assert p.value("wet_band", "1F") == pytest.approx(0.90)
    for sid in p.storeys():
        assert p.value("wet_render", sid) + p.value("wet_band", sid) == pytest.approx(p.value("plaster", sid))
    # blockwork under a beam: GF 3.38 - 0.50 default = 2.88
    assert p.blockwork("GF", under_beam=True)["value_m"] == pytest.approx(2.88)
    # labels: all printed / designer -> DRAWING-READ; the 2F tile is an owner default -> DEFAULT
    assert p.plaster("GF")["label"] == "DRAWING-READ"
    assert p.wall_tile("GF")["label"] == "DRAWING-READ"
    assert p.wall_tile("2F")["label"] == "DEFAULT"


def test_tile_top_above_h_is_capped_and_flagged():
    p = HP.HeightProvider(synthetic())
    t = p.wall_tile("2F")             # tile 3.20 > H 2.98
    assert t["value_m"] == pytest.approx(2.98) and "TILE_TOP_ABOVE_H" in t["flags"]
    b = p.wet_band("2F")
    assert b["state"] == "DERIVED" and b["value_m"] == 0.0 and "measured" in b["note"]


def test_table_has_every_family():
    tab = HP.HeightProvider(synthetic()).table()
    assert set(tab) == {"GF", "1F", "2F"}
    assert tab["1F"]["plaster"] == pytest.approx(3.00) and tab["1F"]["ceiling_wet"] == pytest.approx(2.55)


# -------------------------------------------------------------------------------------------------- adverse
def test_missing_storey_refused():
    p = HP.HeightProvider(synthetic())
    with pytest.raises(HP.MissingInputError):
        p.value("plaster", "3F")
    with pytest.raises(HP.InputsError):
        p.value("skirting", "GF")


def test_missing_required_value_refused_never_zero():
    s = synthetic()
    del s["storeys"][1]["next_ffl"]
    with pytest.raises(HP.MissingInputError):
        HP.HeightProvider(s)
    s = synthetic()
    s["storey_defaults"]["slab_thickness"] = {"value": None, "source": "HELD", "ref": "not printed"}
    with pytest.raises(HP.MissingInputError):
        HP.HeightProvider(s)
    s = synthetic()
    s["storey_defaults"]["slab_thickness"] = rec(0)
    with pytest.raises(HP.MissingInputError):
        HP.HeightProvider(s)


def test_sloped_storey_held_not_averaged():
    s = synthetic()
    s["storeys"][2] = {"id": "2F", "sloped": True, "ffl_low": rec(7.50), "ffl_high": rec(7.90), "next_ffl": rec(10.70)}
    p = HP.HeightProvider(s)
    for fam in ("storey", "plaster", "wall_tile", "wet_band"):
        assert p.get(fam, "2F")["state"] == "HELD" and p.get(fam, "2F")["value_m"] is None
        with pytest.raises(HP.HeldHeightError):
            p.value(fam, "2F")
    assert p.table()["2F"]["plaster"] is None
    # the other storeys are unaffected
    assert p.value("plaster", "GF") == pytest.approx(3.38)


def test_held_optional_input_stays_held():
    s = synthetic()
    s["storey_defaults"]["wet_tile_height"] = {"value": None, "source": "HELD", "ref": "no designer answer"}
    del s["storeys"][2]["wet_tile_height"]
    p = HP.HeightProvider(s)
    with pytest.raises(HP.HeldHeightError):
        p.value("wall_tile", "GF")
    with pytest.raises(HP.HeldHeightError):
        p.value("wet_band", "1F")
    # plaster and dry ceilings still derive
    assert p.value("ceiling", "1F") == pytest.approx(2.25)


def test_sheet_in_millimetres_refused_not_rescaled():
    s = synthetic()
    for st in s["storeys"]:
        st["ffl"]["value"] *= 1000
        st["next_ffl"]["value"] *= 1000
    s["storey_defaults"]["slab_thickness"] = rec(220)
    s["storeys"][1]["slab_thickness"] = rec(300)
    with pytest.raises(HP.InputsError, match="outside"):
        HP.HeightProvider(s)


def test_input_not_mutated_and_json_text_accepted():
    s = synthetic()
    before = copy.deepcopy(s)
    p1 = HP.HeightProvider(s)
    assert s == before
    p2 = HP.HeightProvider(json.dumps(s))
    assert p1.table() == p2.table()


# -------------------------------------------------------------------------------------------------- acceptance
def _t763():
    spec = importlib.util.spec_from_file_location("t763_fill_for_t793", T763)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_training_villa_equals_r_t763_1_constants():
    m = _t763()
    p = HP.HeightProvider(VILLA_1)
    assert set(p.storeys()) == set(m.H)
    for sid, h in m.H.items():
        assert abs(p.value("plaster", sid) - h) < 1e-9
        assert abs(p.value("ceiling", sid) - (h - m.CEIL_DROP)) < 1e-9
        assert abs(p.value("ceiling", sid, wet=True) - m.WET_CEIL) < 1e-9
        assert abs(p.value("wall_tile", sid) - m.TILE_H) < 1e-9
        assert abs(p.value("wet_band", sid) - (h - m.TILE_H)) < 1e-9
        assert m.ceiling(sid, wet=False) == pytest.approx(p.value("ceiling", sid), abs=1e-9)
        assert m.ceiling(sid) == pytest.approx(p.value("ceiling", sid, wet=True), abs=1e-9)
    # the owner figures as printed in the row: 4.34 / 4.04 / 3.84; ceilings 3.44 / 3.14 / 2.94 dry, 2.70 wet
    assert [round(p.value("plaster", s), 2) for s in ("GF", "1F", "2F", "ANNEX")] == [4.34, 4.04, 4.04, 3.84]
    assert [round(p.value("ceiling", s), 2) for s in ("GF", "1F", "2F", "ANNEX")] == [3.44, 3.14, 3.14, 2.94]
    # labels: every height uses an owner default (slab 0.16), so DEFAULT, never DRAWING-READ
    assert p.plaster("GF")["label"] == "DEFAULT"

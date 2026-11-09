"""T-517: build-up above the membrane of a roof-function exposed slab (R-T517-1 .. 6).

Normal fixture K517 (hand-calculated, NOT the training villa): a 5.00 x 4.00 m exposed slab draining to an outlet
gutter along one 5.00 m edge at a printed 1 %; printed 5 cm screed at the outlet (t0), 1:4; printed 3 cm tile bed,
1:4; porcelain finish to a hatch that stops 0.20 m off one 4.00 m face; protection sheet printed (m2); insulation
nowhere. Adverse: nothing printed (every layer HELD, never a default), stack incomplete, membrane as a row, a roof bed
from the owner floor band, finish over face, unnamed range, units, held zone, no outlet. Then the training villa
(finish hatch from the private drawing, skipped when absent)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t517"))
import t517_poolcourt_buildup as B   # noqa: E402
import t517_inputs as INP            # noqa: E402


def _zone(**kw):
    z = {"zone_id": "K517", "function": "ROOF", "held": "",
         "face_m2": {"value": 20.0, "source": "fixture 5.00 x 4.00"},
         "hatch_m2": {"value": 19.2, "source": "fixture hatch 4.80 x 4.00",
                      "edge_cause": "fixture: hatch stops 0.20 m off one 4.00 m face (planter strip printed)"},
         "upturn_lm": {"value": 18.0, "source": "fixture: faces round the slab"},
         "edges_lm": {"gutter_edge": {"value": 5.0, "source": "fixture"}},
         "falls": {"slope": 0.01, "outlet_drawn": True, "mean_rise_m": B.rect_one_edge_mean_rise(4.0, 0.01),
                   "source": "fixture: 'SLOPE 1%' to the gutter"}}
    z.update(kw)
    return z


def _prints(**kw):
    p = {"FALLS_SCREED": {"scope": "PRINTED", "source": "fixture section: '5 cm screed to falls 1:4'",
                          "thickness": {"value": 5, "unit": "cm", "source": "fixture section"},
                          "mix": {"printed": True, "ratio": "1:4", "source": "fixture section note"}},
         "INSULATION": {"scope": "UNKNOWN", "source": "fixture: printed nowhere", "thickness": None},
         "PROTECTION": {"scope": "PRINTED", "source": "fixture: 'protection sheet'", "thickness": None},
         "FINISH": {"scope": "PRINTED", "source": "fixture hatch", "thickness": None,
                    "material": {"value": "porcelain 60 x 60", "source": "fixture finish schedule"}},
         "FINISH_BED": {"scope": "PRINTED", "source": "fixture section: '3 cm bed 1:4'",
                        "thickness": {"value": 3, "unit": "cm", "source": "fixture section"},
                        "mix": {"printed": True, "ratio": "1:4", "source": "fixture section note"}}}
    p.update(kw)
    return p


def _by(rows, layer):
    hit = [r for r in rows if r["layer"] == layer]
    assert len(hit) == 1
    return hit[0]


@pytest.fixture(scope="module")
def conv_records():
    T514 = B._module(B.T514_PY, "t514_screed_bed_producers")
    records = T514.mix_records(True)
    conv, fails = T514.conversions(records)
    assert fails == []
    return B._module(B.T511_PY, "t511_cement_sand_census"), conv, records


# ---------------------------------------------------------------- normal (hand) --------------------------------------
def test_k517_normal_layers_by_hand():
    rows = B.ledger(_zone(), _prints())
    assert [r["layer"] for r in rows] == ["FALLS_SCREED", "INSULATION", "PROTECTION", "FINISH", "FINISH_BED"]
    fs = _by(rows, "FALLS_SCREED")
    # mean rise 0.01 x 4.00 / 2 = 0.02 m; volume 20.00 x (0.05 + 0.02) = 1.400 m3
    assert fs["volume_m3"] == pytest.approx(1.4, abs=1e-9) and fs["state"] == "MEASURED"
    assert fs["item_code"] == "FIN.ROOF.SCREED" and fs["owner_trade"] == "SCREED"
    fin = _by(rows, "FINISH")
    assert fin["quantity"] == pytest.approx(19.2) and fin["area_beside"]["difference_m2"] == pytest.approx(0.8)
    assert "planter strip" in fin["area_beside"]["cause"]
    bed = _by(rows, "FINISH_BED")
    assert bed["volume_m3"] == pytest.approx(19.2 * 0.03)          # 0.576 m3 on the finish area
    assert _by(rows, "PROTECTION")["quantity"] == pytest.approx(20.0)
    ins = _by(rows, "INSULATION")
    assert ins["state"] == "HELD" and ins["quantity"] is None and ins["scope_label"] == "UNKNOWN"


def test_k517_cement_sand_by_hand(conv_records):
    M, conv, records = conv_records
    rows = B.ledger(_zone(), _prints())
    fs = B.producer_state(_by(rows, "FALLS_SCREED"), M, conv, records)
    # 1.400 m3 x 8.0 bags = 11.200 bags; x 1.1 = 1.540 m3 sand (owner 1:4 figure, R-T514-3)
    assert fs["state"] == "PRODUCED" and fs["cement_bags"] == pytest.approx(11.2) and fs["sand_m3"] == pytest.approx(1.54)
    bed = B.producer_state(_by(rows, "FINISH_BED"), M, conv, records)
    # 0.576 x 8 = 4.608 bags; 0.576 x 1.1 = 0.6336 m3
    assert bed["cement_bags"] == pytest.approx(4.608) and bed["sand_m3"] == pytest.approx(0.6336)
    assert B.producer_state(_by(rows, "FINISH"), M, conv, records) is None       # SCOPE_OPEN code: no key
    assert B.producer_state(_by(rows, "INSULATION"), M, conv, records) is None   # NOT_A_KEY


def test_units_mm_and_rotation_invariance():
    a = B.ledger(_zone(), _prints())
    p = _prints()
    p["FALLS_SCREED"] = dict(p["FALLS_SCREED"], thickness={"value": 50, "unit": "mm", "source": "fixture"})
    b = B.ledger(_zone(falls=dict(_zone()["falls"], mean_rise_m=B.rect_one_edge_mean_rise(4.0, 0.01))), p)
    assert _by(a, "FALLS_SCREED")["volume_m3"] == _by(b, "FALLS_SCREED")["volume_m3"]
    # a rotated / mirrored slab: same face and hatch areas, same rise across the same 4.00 m -> same rows
    c = B.ledger(_zone(face_m2={"value": 20.0, "source": "rotated 90 deg"}), _prints())
    assert [r["quantity"] for r in a] == [r["quantity"] for r in c]


# ---------------------------------------------------------------- adverse --------------------------------------------
def test_adverse_nothing_printed_every_layer_held_never_zero():
    p = {"FALLS_SCREED": {"scope": "OWNER_RULE", "source": "Q-41", "thickness": None, "mix": None},
         "INSULATION": {"scope": "UNKNOWN", "source": "none", "thickness": None},
         "PROTECTION": {"scope": "UNKNOWN", "source": "none", "thickness": None},
         "FINISH": {"scope": "UNKNOWN", "source": "none", "thickness": None}}
    z = _zone(hatch_m2=None, falls={"slope": None, "outlet_drawn": False, "mean_rise_m": None, "source": "none"})
    rows = B.ledger(z, p)
    assert all(r["state"] == "HELD" and r["quantity"] is None for r in rows)
    fs = _by(rows, "FALLS_SCREED")
    assert fs["scope_label"] == "ASSUMED - OWNER-APPROVED" and fs["area_m2"] == 20.0
    assert any(m.startswith("THICKNESS") for m in fs["missing"]) and any(m.startswith("FALLS") for m in fs["missing"])
    assert any(m.startswith("AREA") for m in _by(rows, "FINISH")["missing"])       # no hatch: not the face figure
    assert _by(rows, "FINISH")["area_m2"] is None


def test_adverse_t0_printed_but_no_outlet_stays_held():
    z = _zone(falls={"slope": 0.01, "outlet_drawn": False, "mean_rise_m": None, "source": "slope only"})
    fs = _by(B.ledger(z, _prints()), "FALLS_SCREED")
    assert fs["state"] == "HELD" and fs["volume_m3"] is None and any("FALLS" in m for m in fs["missing"])


@pytest.mark.parametrize("bad, msg", [
    ({"drop": "INSULATION"}, "INCOMPLETE_STACK"),
    ({"add": ("MEMBRANE", {"scope": "PRINTED", "source": "x"})}, "MEMBRANE"),
    ({"add": ("FINISH_BED", {"scope": "OWNER_RULE", "source": "Q-45", "band_record": "UPC-TILE-BED-001"})},
     "OUT_OF_SCOPE"),
    ({"add": ("FINISH_BED", {"scope": "PRINTED", "source": "x", "band_record": "Q-45 B 3-4 cm"})}, "OUT_OF_SCOPE"),
    ({"add": ("SKIRTING", {"scope": "PRINTED", "source": "x"})}, "UNKNOWN_LAYER"),
])
def test_adverse_stack_refusals(bad, msg):
    p = _prints()
    if "drop" in bad:
        p.pop(bad["drop"])
    else:
        p[bad["add"][0]] = bad["add"][1]
    with pytest.raises(B.Refused, match=msg):
        B.ledger(_zone(), p)


def test_adverse_area_refusals():
    with pytest.raises(B.Refused, match="FINISH_OVER_FACE"):
        B.ledger(_zone(hatch_m2={"value": 20.5, "source": "x", "edge_cause": "x"}), _prints())
    with pytest.raises(B.Refused, match="UNNAMED_RANGE"):
        B.ledger(_zone(hatch_m2={"value": 19.2, "source": "x"}), _prints())
    with pytest.raises(B.Refused, match="HELD is never 0"):
        B.ledger(_zone(face_m2={"value": 0.0, "source": "x"}), _prints())
    with pytest.raises(B.Refused, match="function"):
        B.ledger(_zone(function="FLOOR"), _prints())


@pytest.mark.parametrize("t, msg", [({"value": 2, "unit": "in", "source": "x"}, "UNIT"),
                                    ({"value": 5, "unit": "cm"}, "UNSOURCED_THICKNESS"),
                                    ({"value": 0, "unit": "cm", "source": "x"}, "ZERO")])
def test_adverse_thickness(t, msg):
    p = _prints()
    p["FALLS_SCREED"] = dict(p["FALLS_SCREED"], thickness=t)
    with pytest.raises(B.Refused, match=msg):
        B.ledger(_zone(), p)


def test_adverse_held_zone_holds_every_layer_with_bound():
    z = _zone(held="covered above, open side", area_bound_m2=3.5)
    rows = B.ledger(z, _prints())
    assert all(r["state"] == "HELD" and r["area_m2"] is None and r["area_bound_m2"] == 3.5 for r in rows)


def test_adverse_mix_refusals(conv_records):
    M, conv, records = conv_records
    p = _prints()
    p["FALLS_SCREED"] = dict(p["FALLS_SCREED"], mix="UPC-TILE-BED-001")
    fs = _by(B.ledger(_zone(), p), "FALLS_SCREED")
    with pytest.raises(B.Refused, match="OUT_OF_SCOPE"):
        B.producer_state(fs, M, conv, records)
    with pytest.raises(B.Refused, match="UNSOURCED_MIX"):
        B.producer_state(dict(fs, mix={"ratio": "1:4"}), M, conv, records)
    with pytest.raises(B.Refused, match="UNSOURCED_MIX"):
        B.producer_state(dict(fs, mix={"printed": True, "ratio": "1:4"}), M, conv, records)
    held = B.producer_state(dict(fs, mix=None), M, conv, records)
    assert held["state"] == "HELD" and held["cement_bags"] is None
    assert any(m.startswith("LAYER_TYPE") for m in held["missing"])


def test_fall_ratio_refused():
    with pytest.raises(B.Refused, match="FALL"):
        B.rect_one_edge_mean_rise(4.0, 1.0)      # '1' for 1 % is a percentage number, not a ratio


def test_edge_rows_lengths_cited_heights_held():
    er = B.edge_rows(_zone(), _prints())
    assert sum(1 for r in er if r["kind"] == "UPSTAND") == 4
    assert all("height HELD" in r["state"] for r in er if r["kind"] == "UPSTAND")
    assert [r for r in er if r["kind"].startswith("EDGE")][0]["length_lm"] == 5.0


# ---------------------------------------------------------------- training villa -------------------------------------
def test_training_villa_without_drawing_finish_held():
    import t517_alsenan as AL
    m = AL.build(use_drawing=False)
    rows = {(r["zone"], r["layer"]): r for r in m["rows"]}
    fs = rows[("POOLCOURT-550", "FALLS_SCREED")]
    assert fs["area_m2"] == pytest.approx(4.906867, abs=1e-9) and fs["state"] == "HELD"
    assert fs["scope_label"] == "ASSUMED - OWNER-APPROVED"
    assert {m_.split(":")[0] for m_ in fs["missing"]} == {"THICKNESS", "FALLS"}
    assert rows[("POOLCOURT-550", "FINISH")]["area_m2"] is None
    assert all(r["state"] == "HELD" and r["area_bound_m2"] == pytest.approx(0.639573)
               for (z, _l), r in rows.items() if z == "POOLCOURT-550-LEDGE")
    assert all(r["quantity"] != 0 for r in m["rows"])
    up = [r for r in m["edge_rows"] if r["zone"] == "POOLCOURT-550" and r["kind"] == "UPSTAND"]
    # 1.838068 + 1.374508 + 0.654611 + 0.894779 + 0.431578 = 5.193544 lm (T-494 valued runs)
    assert up and all(r["length_lm"] == pytest.approx(5.193544, abs=1e-9) for r in up)
    edges = {r["kind"]: r["length_lm"] for r in m["edge_rows"] if r["zone"] == "POOLCOURT-550" and r["layer"] == "ALL"}
    assert edges == {"EDGE_TERMINATION:slab_edge": 6.869158, "EDGE_TERMINATION:void_edge": 4.321407}
    c = m["census"]
    assert c["keys_with_two_producers"] == 0 and c["fails"] == []
    assert c["existing_candidate_lines_on_zone"] == [] and c["existing_producer_hosts_on_zone"] == []
    assert c["t514_missing_hosts"] and "POOLCOURT-550" in c["t514_missing_hosts"][0]["element"]
    hosts = [i for i in c["info"] if i["code_class"] == "HOST"]
    assert [i["item_code"] for i in hosts] == ["FIN.ROOF.SCREED", "FIN.ROOF.SCREED"]     # one key per zone
    st = hosts[0]["cement_sand"]
    assert st["state"] == "HELD" and {x.split(":")[0] for x in st["missing"]} >= {"LAYER_TYPE", "MIX", "THICKNESS",
                                                                                   "FALLS"}
    assert set(c["states"].values()) == {"HELD"} and len(c["states"]) == 4    # 2 hosts x cement / sand
    s = m["sensitivity_falls_screed"]
    # 4.906867 x 0.01 = 0.049069 m3 per cm; x 8.0 = 0.392549 bags; x 1.1 = 0.053976 m3
    assert (s["m3_per_cm"], s["cement_bags_per_cm"], s["sand_m3_per_cm"]) == (0.049069, 0.392549, 0.053976)
    assert "NOT A QUANTITY" in s["label"]


def _have_dxf():
    sys.path.insert(0, str(ROOT / "research" / "agents_t486"))
    import t486_alsenan as A
    return A.default_dxf() is not None


@pytest.mark.skipif(not _have_dxf(), reason="private drawing not decoded in this checkout")
def test_training_villa_finish_hatch_from_drawing():
    import t517_alsenan as AL
    m = AL.build()
    h = m["hatch"]
    # hatches 1250 (two outer paths 1.855201 + 1.547525) + 1253 (1.116457), inside the open-sky net zone
    assert h["hatch_m2"] == pytest.approx(4.519172, abs=2e-6)
    assert h["open_sky_net_m2"] == pytest.approx(4.906867, abs=1e-6)
    assert h["gap_m2"] == pytest.approx(0.387695, abs=2e-6)
    assert h["outside_net_m2"] < 2e-5 and h["on_ledge_m2"] == 0.0
    fin = [r for r in m["rows"] if r["zone"] == "POOLCOURT-550" and r["layer"] == "FINISH"][0]
    assert fin["state"] == "MEASURED" and fin["quantity"] == pytest.approx(4.519172, abs=2e-6)
    assert fin["area_beside"]["face_reading_m2"] == pytest.approx(4.906867)
    assert "HATCH_EDGE_ON_LAYER_2" in fin["area_beside"]["cause"]
    assert fin["material"] is None and fin["material_missing"].startswith("MATERIAL")

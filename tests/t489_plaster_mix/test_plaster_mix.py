"""T-489: PLASTER_MATERIALS_TABLE_V2 (mix stage of each wall coat) + the research mix ledger beside V3.0.45.

Hand fixture K489 (synthetic, not the training villa): a dry face 100.00 m2 (normal case of the row), a tiled bathroom
face 40.00 m2, a stair-hall face HELD.
Conversion (owner Q-53 C): dry factor 1.33, cement 1,440 kg/m3, 50 kg bag; ratio 1:n by volume:
  1:4  cement 1.33 / 5 = 0.266 m3 = 383.04 kg = 7.6608 bags per m3; sand 1.33 x 4 / 5 = 1.064 m3 per m3
  1:3  0.3325 m3 = 478.8 kg = 9.576 bags; sand 0.9975 m3       1:5  0.221667 m3 = 319.2 kg = 6.384 bags; sand 1.108333
Normal: 100.00 m2 x 0.020 m = 2.000 m3 -> 1:4 (synthetic project spec) 2.000 x 7.6608 = 15.3216 bags, 2.128 m3 sand.
Render: 40.00 x 0.015 = >= 0.600 m3 (printed minimum) -> 1:4 >= 4.59648 bags, >= 0.6384 m3 sand: bounds only.
Adverse: no mix source -> cement / sand HELD naming the unreadable 1990 specification chapter 09200, never 0.
"""

import json
from pathlib import Path

import pytest

from engine.source import plaster_materials_table_v1 as V1
from engine.source import plaster_materials_table_v2 as V2

ROOT = Path(__file__).resolve().parents[2]
SPEC = "synthetic project specification, clause 09200-2.3 (test only)"

K489 = [
    {"id": "K-DRY", "class": V1.DRY, "area_m2": 100.00, "area_label": V1.PNET},
    {"id": "K-BATH", "class": V1.WET, "area_m2": 40.00, "area_label": V1.PNET},
    {"id": "K-HALL", "class": V1.DRY, "area_m2": None, "area_reason": "stair hall height HELD"},
]


def _layer(t, rid, layer):
    r = next(r for r in t["rows"] if r["id"] == rid)
    return next(x for x in r["layers"] if x["layer"] == layer)


def test_conversion_hand_values_per_m3():
    for n, bags, sand in ((3, 9.576, 0.9975), (4, 7.6608, 1.064), (5, 6.384, 1.108333333)):
        f = V2.per_m3(n)
        assert f["cement_bags"] == pytest.approx(bags) and f["sand_m3"] == pytest.approx(sand)
        assert f["cement_m3"] + f["sand_m3"] == pytest.approx(1.33)            # parts add up to the dry volume


def test_normal_100_m2_two_coat_plaster_with_a_sourced_mix():
    t = V2.table(K489[:1], mix={"WALL_PLASTER": {"sand_parts": 4, "source": SPEC, "level": 1}})
    x = _layer(t, "K-DRY", "WALL_PLASTER")
    assert x["mortar_m3"] == pytest.approx(2.0)
    assert x["cement_bags"] == pytest.approx(15.3216) and x["sand_m3"] == pytest.approx(2.128)
    assert x["materials_status"] == V2.OK and x["mix_label"] == "PROJECT DOCUMENT" and x["water"] == V2.HELD
    # the thickness is still the level-4 KSE reference: the figure is an estimate, s.5 HELD (never VERIFIED)
    assert x["label"] == V1.ENET and x["s5_status"] == V2.S5_HELD
    assert t["sums"]["WALL_PLASTER"]["cement_bags"] == pytest.approx(15.3216)


def test_s5_status_is_the_weakest_input_conversion_included():
    proj = {V1.RID: {"wall_plaster_thickness_m": {"value": 0.020, "level": 1, "source": SPEC}}}
    x = _layer(V2.table(K489[:1], project=proj, mix={"WALL_PLASTER": {"sand_parts": 4, "source": SPEC, "level": 1}}),
               "K-DRY", "WALL_PLASTER")
    # the bag conversion is the owner's Q-53 C convention (level 3): the weakest input makes it OWNER-APPROVED
    assert x["s5_status"] == V2.S5_OWNER and x["cement_bags"] == pytest.approx(15.3216)
    conv1 = dict(V2.CONVERSION, level=1, source="synthetic project spec: dry factor / density / bag printed")
    z = _layer(V2.table(K489[:1], project=proj, conversion=conv1,
                        mix={"WALL_PLASTER": {"sand_parts": 4, "source": SPEC, "level": 1}}), "K-DRY", "WALL_PLASTER")
    assert z["s5_status"] == V2.S5_DRAWING
    y =_layer(V2.table(K489[:1], project=proj, mix={"WALL_PLASTER": {"sand_parts": 4, "level": 2,
                                                                       "source": "owner decision (synthetic)"}}),
               "K-DRY", "WALL_PLASTER")
    assert y["s5_status"] == V2.S5_OWNER
    assert V2.S5_VERIFIED not in json.dumps(V2.table(K489, project=proj, mix={"WALL_PLASTER": {
        "sand_parts": 4, "source": SPEC, "level": 1}}), ensure_ascii=False)       # the table never verifies


def test_adverse_no_source_holds_cement_and_names_the_missing_source():
    t = V2.table(K489)
    for rid, ly in (("K-DRY", "WALL_PLASTER"), ("K-BATH", "LEVELLING_RENDER"), ("K-DRY", "BOND_COAT")):
        x = _layer(t, rid, ly)
        assert x["cement_bags"] is None and x["sand_m3"] is None and x["materials_status"] == V2.HELD
        assert x["s5_status"] == V2.S5_HELD
    x = _layer(t, "K-DRY", "WALL_PLASTER")
    assert "1990" in x["materials_reason"] and "09200" in x["materials_reason"] and "10 MB" in x["materials_reason"]
    assert t["sums"]["WALL_PLASTER"]["cement_bags"] is None                     # never 0
    assert "K-DRY" in t["sums"]["WALL_PLASTER"]["cement_not_in_sum"]
    s = x["sensitivity_not_a_quantity"]                                           # shown beside, not a quantity
    assert s["1:3"]["cement_bags"] == pytest.approx(19.152) and s["1:5"]["cement_bags"] == pytest.approx(12.768)


def test_render_minimum_gives_bounds_only():
    x = _layer(V2.table(K489[1:2], mix={"LEVELLING_RENDER": {"sand_parts": 4, "source": SPEC, "level": 1}}),
               "K-BATH", "LEVELLING_RENDER")
    assert x["materials_status"] == V2.AT_LEAST and x["cement_bags"] is None and x["sand_m3"] is None
    assert x["cement_bags_at_least"] == pytest.approx(4.59648) and x["sand_m3_at_least"] == pytest.approx(0.6384)
    assert x["s5_status"] == V2.S5_HELD


def test_bond_coat_with_a_mix_but_no_thickness_stays_held():
    x = _layer(V2.table(K489[:1], mix={"BOND_COAT": {"sand_parts": 2, "source": SPEC, "level": 1}}), "K-DRY",
               "BOND_COAT")
    assert x["cement_bags"] is None and x["materials_status"] == V2.HELD and x["sensitivity_not_a_quantity"] is None


def test_adverse_held_area_and_unclassified_face_are_never_zero():
    t = V2.table(K489 + [{"id": "K-REV", "class": None, "area_m2": 0.78, "area_label": V1.PNET}],
                 mix={"WALL_PLASTER": {"sand_parts": 4, "source": SPEC, "level": 1}})
    h = _layer(t, "K-HALL", "WALL_PLASTER")
    assert h["cement_bags"] is None and h["materials_status"] == V2.HELD and h["sensitivity_not_a_quantity"] is None
    r = next(r for r in t["rows"] if r["id"] == "K-REV")
    assert all(x["cement_bags"] is None and x["s5_status"] == V2.S5_HELD for x in r["layers"])
    assert t["sums"]["WALL_PLASTER"]["cement_bags"] is None
    assert {"K-HALL", "K-REV"} <= set(t["sums"]["WALL_PLASTER"]["cement_not_in_sum"])


@pytest.mark.parametrize("bad", [
    {"sand_parts": 3, "source": "owner Q-53 C stair bed 1:3", "level": 2},       # borrowed stair-bed ratio
    {"sand_parts": 4, "source": "Q-78 block mortar 1:4", "level": 2},            # borrowed block mortar
    {"sand_parts": 4, "level": 1},                                               # no source
    {"sand_parts": 4, "source": SPEC, "level": 5},                               # level outside 1-4
    {"sand_parts": 0, "source": SPEC, "level": 1},                               # 1:0 is not a mix
    {"sand_parts": -4, "source": SPEC, "level": 1},
])
def test_adverse_mix_refused(bad):
    with pytest.raises(ValueError):
        V2.table(K489[:1], mix={"WALL_PLASTER": bad})


def test_adverse_conversion_and_layer_refused():
    with pytest.raises(ValueError):
        V2.table(K489[:1], conversion=dict(V2.CONVERSION, dry_factor=133))       # a percentage, not a factor
    with pytest.raises(ValueError):
        V2.table(K489[:1], conversion=dict(V2.CONVERSION, source=""))
    with pytest.raises(ValueError):
        V2.table(K489[:1], mix={"SCREED": {"sand_parts": 4, "source": SPEC, "level": 1}})


def test_sensitivity_is_monotonic_and_mapping_never_releases_an_estimate():
    s = _layer(V2.table(K489[:1]), "K-DRY", "WALL_PLASTER")["sensitivity_not_a_quantity"]
    assert s["1:3"]["cement_bags"] > s["1:4"]["cement_bags"] > s["1:5"]["cement_bags"]
    assert s["1:3"]["sand_m3"] < s["1:4"]["sand_m3"] < s["1:5"]["sand_m3"]
    assert V2.S5_MAP[V1.ENET] == V2.S5_HELD and V2.S5_MAP["ENGINEERING ESTIMATE"] == V2.S5_HELD
    assert V2.S5_VERIFIED not in V2.S5_MAP.values()


def test_v1_is_untouched_and_module_unwired_without_family_terms():
    import re
    assert V1.METHOD_ID == "PLASTER_MATERIALS_TABLE_V1" and V2.SUPERSEDES is None
    assert V2.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"
    src = (ROOT / "engine/source/plaster_materials_table_v2.py").read_text(encoding="utf-8")
    assert '"FIN.' not in src and '"MAS.' not in src
    defs = re.findall(r"^\s*def\s+(\w+)", src, re.M)
    assert not [d for d in defs for term in ("spatter", "mortar", "glue", "dash_coat") if term in d.lower()]


# ------------------------------------------------------------------ the research reader (committed pinned inputs)
def _reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("t489", ROOT / "research/agents_t489/t489_plaster_mix.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_reader_reproduces_the_committed_ledger_and_the_t454_figures(tmp_path):
    R = _reader()
    led = R.build()
    R.write(led, tmp_path)
    for name in ("PLASTER_MIX_T489.json", "PLASTER_MIX_T489.csv"):
        assert (tmp_path / name).read_bytes() == (ROOT / "research/agents_t489/out" / name).read_bytes()
    sums = led["table"]["sums"]
    assert all(sums[ly]["cement_bags"] is None and sums[ly]["s5_status"] == V2.S5_HELD for ly in sums)
    rows = led["table"]["rows"]
    dry = sum(x["mortar_m3"] or 0 for r in rows for x in r["layers"] if x["layer"] == "WALL_PLASTER")
    wet = sum(x["mortar_m3_at_least"] or 0 for r in rows for x in r["layers"] if x["layer"] == "LEVELLING_RENDER")
    assert dry == pytest.approx(4.726962) and wet == pytest.approx(5.104557)   # = T-454, nothing re-measured
    assert sums["WALL_PLASTER"]["sensitivity_not_a_quantity"]["1:3"]["cement_bags"] == pytest.approx(45.265391)
    assert sums["LEVELLING_RENDER"]["sensitivity_not_a_quantity"]["1:5"]["cement_bags"] == pytest.approx(32.587491)

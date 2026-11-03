"""T-454: PLASTER_MATERIALS_TABLE_V1 + the research ledger beside V3.0.45.

Hand fixture K454 (a synthetic two-storey villa, not the training villa): dry living room faces 40.00 m2, dry corridor
12.50 m2, a tiled bathroom 25.00 m2, a tiled kitchen 18.40 m2, a stair-hall face HELD (range 30.00 .. 34.00 m2).
Hand values (reference: KSE 'Bayt Al-Omr' 2023, items 57 / 60 / 62 / 75):
  dry plaster 2.0 cm   (40.00 + 12.50) x 0.020 = 1.050 m3          ESTIMATED-NET (never VERIFIED)
  wet render >= 1.5 cm (25.00 + 18.40) x 0.015 = 0.651 m3 AT LEAST  HELD with the bound
  bond coat (spatter)  40.00 + 12.50 + 25.00 + 18.40 = 95.90 m2     mortar HELD (no thickness printed)
  cement / sand        HELD (no mix sourced)
"""

import csv
import io
import json
from pathlib import Path

import pytest

from engine.source import plaster_materials_table_v1 as P

ROOT = Path(__file__).resolve().parents[2]

K454 = [
    {"id": "K-GF-LIV", "class": P.DRY, "area_m2": 40.00, "area_label": P.PNET},
    {"id": "K-GF-COR", "class": P.DRY, "area_m2": 12.50, "area_label": P.VNET},
    {"id": "K-1F-BATH", "class": P.WET, "area_m2": 25.00, "area_label": P.PNET},
    {"id": "K-GF-KIT", "class": P.WET, "area_m2": 18.40, "area_label": P.PNET},
    {"id": "K-ST-HALL", "class": P.DRY, "area_m2": None, "area_reason": "stair hall height HELD"},
]


def _layer(t, rid, layer):
    r = next(r for r in t["rows"] if r["id"] == rid)
    return next(x for x in r["layers"] if x["layer"] == layer)


def test_normal_dry_plaster_is_an_estimate_from_the_two_coats():
    t = P.table(K454)
    x = _layer(t, "K-GF-LIV", "WALL_PLASTER")
    assert x["thickness_m"] == pytest.approx(0.015 + 0.005) and x["thickness_kind"] == "EXACT"
    assert x["thickness_basis"] == "ENGINEERING ESTIMATE" and "item 60" in x["thickness_source"]
    assert x["mortar_m3"] == pytest.approx(0.800) and x["status"] == P.OK and x["label"] == P.ENET
    assert x["sensitivity_m3_per_mm"] == pytest.approx(0.040)
    v = _layer(t, "K-GF-COR", "WALL_PLASTER")                     # a VERIFIED area does not make the material VERIFIED
    assert v["label"] == P.ENET and v["area_label"] == P.VNET
    assert t["sums"]["WALL_PLASTER"]["mortar_m3"] == pytest.approx(1.050)


def test_wet_render_minimum_is_a_bound_never_the_quantity():
    t = P.table(K454)
    x = _layer(t, "K-1F-BATH", "LEVELLING_RENDER")
    assert x["status"] == P.AT_LEAST and x["label"] == P.HELD
    assert x["mortar_m3"] is None and x["mortar_m3_at_least"] == pytest.approx(0.375)
    s = t["sums"]["LEVELLING_RENDER"]
    assert s["mortar_m3"] is None and s["mortar_m3_at_least"] == pytest.approx(0.651)
    assert not any(x["layer"] == "WALL_PLASTER" for r in t["rows"] if r["class"] == P.WET for x in r["layers"])


def test_bond_coat_area_on_every_face_and_its_volume_held():
    t = P.table(K454)
    s = t["sums"]["BOND_COAT"]
    assert s["area_m2"] == pytest.approx(95.90) and s["mortar_m3"] is None
    assert s["area_not_in_sum"] == ["K-ST-HALL"]
    x = _layer(t, "K-GF-KIT", "BOND_COAT")
    assert x["status"] == P.HELD and x["area_m2"] == pytest.approx(18.40) and x["area_label"] == P.PNET


def test_cement_and_sand_held_without_a_mix_and_never_borrowed():
    t = P.table(K454)
    for r in t["rows"]:
        for x in r["layers"]:
            assert x["cement_bags"] is None and x["sand_m3"] is None and x["materials_status"] == P.HELD
            assert x["water"] == P.HELD
    assert "NEEDS_MIX" in _layer(t, "K-GF-LIV", "WALL_PLASTER")["materials_reason"]
    assert t["sums"]["WALL_PLASTER"]["cement_bags"] is None


def test_adverse_held_area_is_never_zero():
    t = P.table(K454)
    r = next(r for r in t["rows"] if r["id"] == "K-ST-HALL")
    for x in r["layers"]:
        assert x["status"] == P.HELD and x["area_m2"] is None and x["mortar_m3"] is None and x["label"] == P.HELD
    assert "K-ST-HALL" in t["sums"]["WALL_PLASTER"]["mortar_not_in_sum"]


def test_adverse_millimetre_thickness_is_held_not_computed():
    proj = {P.RID: {"wall_plaster_thickness_m": {"value": 20, "level": 1, "source": "spec clause (synthetic)"}}}
    x = _layer(P.table(K454[:1], project=proj), "K-GF-LIV", "WALL_PLASTER")
    assert x["status"] == P.HELD and x["mortar_m3"] is None and "THICKNESS_OUT_OF_RANGE" in x["reason"]


def test_project_values_win_and_carry_the_area_label():
    proj = {P.RID: {"wall_plaster_thickness_m": {"value": 0.025, "level": 1, "source": "spec 09200 (synthetic)"}}}
    mix = {"WALL_PLASTER": {"cement_bags_per_m3": 8.0, "sand_m3_per_m3": 1.1, "source": "spec 09200 (synthetic)"}}
    x = _layer(P.table(K454[:1], project=proj, mix_figures=mix), "K-GF-LIV", "WALL_PLASTER")
    assert x["thickness_basis"] == "PROJECT DOCUMENT" and x["label"] == P.PNET
    assert x["mortar_m3"] == pytest.approx(1.000) and x["cement_bags"] == pytest.approx(8.0)
    assert x["sand_m3"] == pytest.approx(1.1)
    w = _layer(P.table(K454[2:3], mix_figures={"LEVELLING_RENDER": {"cement_bags_per_m3": 8.0, "sand_m3_per_m3": 1.1,
                                                                    "source": "synthetic"}}),
               "K-1F-BATH", "LEVELLING_RENDER")
    assert w["status"] == P.AT_LEAST and w["cement_bags"] == pytest.approx(3.0)   # a bound stays a bound


def test_adverse_inputs_refused():
    with pytest.raises(ValueError):
        P.table(K454 + [dict(K454[0])])                                         # one face reported twice
    with pytest.raises(ValueError):
        P.table([{"id": "x", "class": P.DRY, "area_m2": 5.0}])                  # a released area with no label
    with pytest.raises(ValueError):
        P.table(K454[:1], mix_figures={"WALL_PLASTER": {"cement_bags_per_m3": 8.0, "sand_m3_per_m3": 1.1}})
    with pytest.raises(ValueError):
        P.table([{"id": "x", "class": P.DRY, "area_m2": -1.0, "area_label": P.PNET}])


def test_unclassified_face_holds_every_layer_and_leaves_the_sums():
    t = P.table(K454 + [{"id": "K-REV", "class": None, "area_m2": 0.78, "area_label": P.PNET}])
    r = next(r for r in t["rows"] if r["id"] == "K-REV")
    assert all(x["status"] == P.HELD and "CLASS_NOT_ESTABLISHED" in x["reason"] for x in r["layers"])
    assert t["sums"]["BOND_COAT"]["area_m2"] == pytest.approx(95.90) and "K-REV" in t["sums"]["BOND_COAT"]["area_not_in_sum"]


def test_module_is_unwired_and_avoids_family_codes_and_terms():
    src = (ROOT / "engine/source/plaster_materials_table_v1.py").read_text(encoding="utf-8")
    assert P.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"
    assert '"FIN.' not in src and '"MAS.' not in src
    import re
    defs = re.findall(r"^\s*def\s+(\w+)", src, re.M)
    assert not [d for d in defs for term in ("spatter", "mortar", "glue", "dash_coat") if term in d.lower()]


# ------------------------------------------------------------------ the research reader (synthetic inputs)
def _reader():
    import importlib.util
    spec = importlib.util.spec_from_file_location("t454", ROOT / "research/agents_t454/t454_plaster_materials.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _line(lid, code, cls, el, net=None, lo=None, hi=None, binding=None):
    return {"line_id": lid, "item_code": code, "class": cls, "element_id": el, "measured_net": net, "held_low": lo,
            "held_high": hi, "binding": binding, "unit": "m2", "unbound_records": []}


def _inputs(tmp_path, lines, faces):
    li = tmp_path / "li.json"
    li.write_text(json.dumps({"lines": lines}), encoding="utf-8")
    b = tmp_path / "b.csv"
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["row_id", "family", "target"])
    w.writerows(faces)
    b.write_text(buf.getvalue(), encoding="utf-8")
    return li, b


def test_reader_classifies_from_the_binding_and_carries_bounds(tmp_path):
    R = _reader()
    lines = [_line("L-1", "FIN.PLASTER", "RELEASED", "K-LIV", 40.0),
             _line("L-2", "FIN.PLASTER", "RELEASED", "K-BATH", 25.0, binding={"binding": "VERIFIED_WHOLE"}),
             _line("L-3", "FIN.PLASTER", "HELD", "K-HALL", None, 30.0, 34.0),
             _line("L-4", "FIN.PLASTER", "RELEASED", "K-MIX", 9.0),
             _line("L-5", "FIN.PLASTER", "EXCLUDED", "K-OUT"),
             _line("L-6", "EXT.FENCE.PLASTER", "HELD", "K-FENCE")]
    faces = [("a", "INT_DRY_LINE", "L-1"), ("b", "INT_WET_FACE", "L-2"), ("c", "INT_WET_RESIDUAL", "L-2"),
             ("d", "INT_DRY_LINE", "L-3"), ("e", "INT_DRY_LINE", "L-4"), ("f", "INT_WET_FACE", "L-4")]
    led = R.build(*_inputs(tmp_path, lines, faces))
    rows = {r["id"]: r for r in led["table"]["rows"]}
    assert rows["L-1"]["class"] == P.DRY and rows["L-2"]["class"] == P.WET
    assert rows["L-4"]["class"] is None and "mix" in rows["L-4"]["class_reason"]       # mixed: never split by guess
    assert rows["L-6"]["class"] is None and [e["line_id"] for e in led["excluded"]] == ["L-5"]
    assert rows["L-2"]["layers"][0]["area_label"] == P.VNET                           # area label from the binding
    held = next(x for x in rows["L-3"]["layers"] if x["layer"] == "WALL_PLASTER")
    assert held["mortar_m3"] is None and held["mortar_m3_bound_beside"] == [pytest.approx(0.6), pytest.approx(0.68)]
    assert led["table"]["sums"]["WALL_PLASTER"]["mortar_m3"] == pytest.approx(0.800)


def test_reader_refuses_a_figure_on_a_held_line(tmp_path):
    R = _reader()
    with pytest.raises(R.LedgerError):
        R.build(*_inputs(tmp_path, [_line("L-1", "FIN.PLASTER", "HELD", "K", 5.0)], [("a", "INT_DRY_LINE", "L-1")]))


def test_reader_reproduces_the_committed_ledger(tmp_path):
    R = _reader()
    R.write(R.build(), tmp_path)
    for name in ("PLASTER_MATERIALS_T454.json", "PLASTER_MATERIALS_T454.csv"):
        assert (tmp_path / name).read_bytes() == (ROOT / "research/agents_t454/out" / name).read_bytes()


def test_committed_ledger_hand_checks():
    led = json.loads((ROOT / "research/agents_t454/out/PLASTER_MATERIALS_T454.json").read_text(encoding="utf-8"))
    rows = {r["id"]: r for r in led["table"]["rows"]}
    dry = next(x for x in rows["L-af9621f43bc316a871ea"]["layers"] if x["layer"] == "WALL_PLASTER")
    assert dry["area_m2"] == pytest.approx(51.415) and dry["mortar_m3"] == pytest.approx(1.0283)
    wet = next(x for x in rows["L-2948639faa08fa1cff81"]["layers"] if x["layer"] == "LEVELLING_RENDER")
    assert wet["mortar_m3_at_least"] == pytest.approx(0.787935) and wet["mortar_m3"] is None
    s = led["table"]["sums"]
    assert s["BOND_COAT"]["area_m2"] == pytest.approx(s["WALL_PLASTER"]["area_m2"] + s["LEVELLING_RENDER"]["area_m2"])

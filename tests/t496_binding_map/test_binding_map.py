"""T-496: materials binding map + check (research/agents_t496/t496_binding_map.py).

Fixture villa P496 (not the training villa), by hand, owner rules from AGENT_BRIEF:
  LB1 MAS.BLOCK black 0.20 VERIFIED 10.000 m2: 10 x 12.5 = 125 blocks; mortar 10 x 0.01475 = 0.1475 m3,
      cement 0.1475 x 8 = 1.18 bags, sand 0.1475 x 1.1 = 0.16225 m3.
  LW1 MAS.BLOCK white 0.15 DRAWING-CONFIRMED 8.000 m2: glue 8 x 3.5 = 28.0 kg, 28 / 25 = 1.12 bags (25 kg).
  LH1 MAS.BLOCK HELD (no net): units / laying HELD, never 0.
  PD1 FIN.PLASTER dry 20.000 m2: plaster 20 x 0.020 = 0.400 m3, a level-4 thickness -> ESTIMATE BESIDE a HELD figure.
  PW1 FIN.PLASTER wet 12.000 m2: render >= 12 x 0.015 = 0.180 m3 (AT_LEAST bound).
  TW1 FIN.WALL.TILE 12.000 m2 (same face as PW1): adhesive bound 12 / 5 = 2.4 .. 12 / 3 = 4.0 bags.
  TF1 FIN.FLOOR.PORCELAIN 9.000 m2: adhesive bound 1.8 .. 3.0 bags; its bed is candidate line BF1 (FIN.FLOOR.BED.DRY).
  OD1 EXT.FLOOR.OUTDOOR HELD [6.000, 6.000]: porcelain option adhesive 1.2 .. 2.0 bags; bed 6 x 0.03 x 1.05 = 0.189 ..
      6 x 0.04 x 1.05 = 0.252 m3, cement 1.512 .. bags, sand .. 0.2772 m3.
"""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t496"))

import t496_binding_map as M  # noqa: E402


def _ln(i, code, eid, cls, net=None, lo=None, hi=None, unit="m2"):
    return {"line_id": i, "item_code": code, "element_id": eid, "class": cls, "unit": unit, "measured_net": net,
            "held_low": lo, "held_high": hi}


def _cand():
    ls = [_ln("LB1", "MAS.BLOCK", "GF-WALLS#BLACK", "RELEASED", 10.0),
          _ln("LW1", "MAS.BLOCK", "GF-WALLS#WHITE", "RELEASED", 8.0),
          _ln("LH1", "MAS.BLOCK", "1F-WALLS", "HELD"),
          _ln("PD1", "FIN.PLASTER", "GF-R1:plaster", "RELEASED", 20.0),
          _ln("PW1", "FIN.PLASTER", "GF-R2:plaster", "RELEASED", 12.0),
          _ln("TW1", "FIN.WALL.TILE", "GF-R2:wall_tile", "RELEASED", 12.0),
          _ln("TF1", "FIN.FLOOR.PORCELAIN", "GF-R1:floor", "RELEASED", 9.0),
          _ln("BF1", "FIN.FLOOR.BED.DRY", "GF-R1:floor:bed", "RELEASED", 9.0),
          _ln("OD1", "EXT.FLOOR.OUTDOOR", "GF-COURT#T1", "HELD", lo=6.0, hi=6.0),
          _ln("SK1", "FIN.SKIRTING", "GF-R1:skirting", "RELEASED", 12.0, unit="lm")]
    return {"lines": {x["line_id"]: x for x in ls}, "changed": set(), "version": "FIXTURE P496", "sha256": "-"}


def _layer(layer, area, t=None, basis=None, mortar=None, at_least=None, label="HELD", s5=None):
    return {"layer": layer, "area_m2": area, "thickness_m": t, "thickness_basis": basis, "mortar_m3": mortar,
            "mortar_m3_at_least": at_least, "cement_bags": None, "sand_m3": None, "label": label, "s5_status": s5}


def _tables():
    blk = dict(item="BLOCK_COUNT", line_id="LB1", status="COMPUTED", label="VERIFIED-NET", material_type="BLACK",
               thickness_m=0.2, contract_net_m2=10.0, material_base_m2=10.0, theoretical_count=125.0)
    mor = dict(item="LAYING_MATERIAL", line_id="LB1", status="COMPUTED", label="PROVISIONAL-NET",
               material_type="BLACK", thickness_m=0.2, contract_net_m2=10.0, material_base_m2=10.0,
               mortar_per_m2=0.01475, mortar_installed_m3=0.1475, cement_bags=1.18, sand_m3_loose=0.16225)
    glu = dict(item="LAYING_MATERIAL", line_id="LW1", status="COMPUTED", label="PROVISIONAL-NET",
               material_type="WHITE", thickness_m=0.15, contract_net_m2=8.0, material_base_m2=8.0, kg_per_m2=3.5,
               consumption_kg=28.0, bags_25kg_net=1.12)
    hb = dict(item="BLOCK_COUNT", line_id="LH1", status="HELD", label="HELD", material_type=None, thickness_m=0.15,
              why="source line HELD")
    hl = dict(hb, item="LAYING_MATERIAL")
    t453 = {"source_lines": [{"line_id": "LB1", "class": "RELEASED", "net_m2": 10.0},
                             {"line_id": "LW1", "class": "RELEASED", "net_m2": 8.0},
                             {"line_id": "LH1", "class": "HELD", "net_m2": None}],
            "block_materials": [blk, mor, glu, hb, hl],
            "reconciliation": [{"line_id": "LB1", "walls": ["GF-W1"]}, {"line_id": "LW1", "walls": ["GF-W2"]}],
            "lintels": [{"opening_id": "D1", "host": "GF-W2", "decision": "REQUIRED", "width_m": 0.9,
                         "section_m": [0.15, 0.2], "face_m2": 0.34, "concrete_m3": 0.051}],
            "block_totals": {"black_0_20_by_label": {"VERIFIED-NET": {"theoretical_blocks": 125.0}}},
            "glue_groups": {"PROJECT": {"bags_to_buy": None},
                            "known_part_by_label": {"VERIFIED-NET": {"kg": 0.0}, "PROVISIONAL-NET": {"kg": 28.0}}},
            "mortar": {"black_0_20_provisional_net": {"m3": 0.1475}}}
    est = "ENGINEERING ESTIMATE"
    rows = [{"id": "PD1", "line_class": "RELEASED", "area_m2": 20.0, "held_low": None, "held_high": None,
             "class": "DRY_WALL_PLASTER",
             "layers": [_layer("BOND_COAT", 20.0), _layer("WALL_PLASTER", 20.0, 0.02, est, 0.4, label="ESTIMATED-NET")]},
            {"id": "PW1", "line_class": "RELEASED", "area_m2": 12.0, "held_low": None, "held_high": None,
             "class": "WET_WALL_RENDER",
             "layers": [_layer("BOND_COAT", 12.0), _layer("LEVELLING_RENDER", 12.0, 0.015, "MINIMUM", None, 0.18)]}]
    t454 = {"table": {"rows": rows, "sums": {"WALL_PLASTER": {"mortar_m3": 0.4},
                                             "LEVELLING_RENDER": {"mortar_m3_at_least": 0.18}}}, "excluded": []}
    t489 = copy.deepcopy(t454)
    for r in t489["table"]["rows"]:
        for L in r["layers"]:
            L["s5_status"] = "HELD"

    def trow(i, kind, area, lo, hi):
        return {"id": i, "status": "RELEASED", "kind": kind, "area_m2": area, "adhesive_bags": None,
                "adhesive_bound_bags": {"low": lo, "high": hi}, "adhesive_status": "HELD",
                "tiles_conservative": None, "tile_product": None}
    t455 = {"rows": [trow("TW1", "WET_WALL", 12.0, 2.4, 4.0), trow("TF1", "DRY_FLOOR", 9.0, 1.8, 3.0)],
            "by_item_code": {"FIN.WALL.TILE": {"bound_low": 2.4}, "FIN.FLOOR.PORCELAIN": {"bound_low": 1.8}},
            "purchase": {"adhesive": {"PROJECT": {"bags_to_buy": None, "bags_known": None}}}, "excluded_lines": []}
    bed = {"bed_m": [0.03, 0.04], "mortar_m3": {"low": 0.189, "high": 0.252},
           "cement_bags_50kg": {"low": 1.512, "high": 2.016}, "sand_m3_loose": {"low": 0.2079, "high": 0.2772}}
    t495 = {"finish_held_rows": [{"id": "OD1", "area_m2": None, "area_held_low_m2": 6.0, "area_held_high_m2": 6.0,
                                  "options": [{"finish": "PORCELAIN_CERAMIC", "status": "HELD",
                                               "adhesive_bags_20kg": {"low": 1.2, "high": 2.0}, "bed": bed},
                                              {"finish": "INTERLOCK", "status": "HELD", "adhesive_bags_20kg": None,
                                               "bed": None, "bed_reason": "no owner rule"}]}]}
    return {"T-453": t453, "T-454": t454, "T-489": t489, "T-455": t455, "T-495": t495}


def _kinds(m):
    return sorted({f["kind"] for f in m["failures"]})


def _get(m, table, line, kind, material=None):
    return [b for b in m["bindings"] if b["table"] == table and b["line_id"] == line and b["kind"] == kind
            and (material is None or b["material"] == material)]


# ------------------------------------------------------------------------------------------------ normal
def test_fixture_by_hand_passes_and_maps_every_row():
    m = M.run(_tables(), _cand(), pins=False)
    assert m["failures"] == []
    assert _get(m, "T-453", "LB1", "units_nr")[0]["value"] == 125.0
    assert [b["value"] for b in _get(m, "T-453", "LB1", "cement_bags")] == [1.18]
    assert _get(m, "T-453", "LW1", "glue_kg")[0]["value"] == 28.0
    held = _get(m, "T-453", "LH1", "units_nr")[0]
    assert held["value"] is None and held["wiring_state"] == "HELD"
    pd = _get(m, "T-454", "PD1", "mortar_m3", "WALL_PLASTER")[0]
    assert pd["value"] is None and pd["estimate_beside"] == 0.4 and pd["wiring_state"] == "ESTIMATE_BESIDE_HELD"
    pw = _get(m, "T-489", "PW1", "mortar_m3", "LEVELLING_RENDER")[0]
    assert pw["bound"] == [0.18, None] and pw["wiring_state"] == "BOUND_ONLY"
    assert _get(m, "T-455", "TW1", "adhesive_bags_20kg")[0]["bound"] == [2.4, 4.0]
    lint = [b for b in m["bindings"] if b["material"] == "LINTEL_RC"][0]
    assert lint["line_id"] == "LW1" and lint["wiring_state"] == "NO_CANDIDATE_LINE"
    wet = [a for a in m["aggregation"] if a["total"].startswith("wet-wall")][0]
    assert wet["sum_of_bound_rows"] == wet["table_prints"] == 12.0
    g = m["purchasing_groups_held_members"]
    assert g["TILE_ADHESIVE/PROJECT"]["members"] == 3 and g["TILE_ADHESIVE/PROJECT"]["to_buy"] is None
    assert g["MASONRY_LAYING/PROJECT"]["without_figure"] == ["LH1"]
    assert m["released_quantities_changed"] == 0


# ------------------------------------------------------------------------------------------------ adverse
def test_adverse_missing_line_id_fails():
    c = _cand()
    del c["lines"]["TW1"]
    m = M.run(_tables(), c, pins=False)
    assert "ABSENT_LINE" in _kinds(m)
    assert any("TW1" in f["why"] for f in m["failures"])


def test_adverse_held_input_producing_a_figure_fails():
    t = _tables()
    t["T-453"]["block_materials"][3]["theoretical_count"] = 0.0     # a HELD line printed as 0 blocks
    m = M.run(t, _cand(), pins=False)
    assert "HELD_YIELDS_FIGURE" in _kinds(m)


def test_adverse_candidate_line_turned_held_fails_stale_and_figure():
    c = _cand()
    c["lines"]["LB1"].update({"class": "HELD", "measured_net": None})
    m = M.run(_tables(), c, pins=False)
    assert {"STALE_INPUT", "HELD_YIELDS_FIGURE"} <= set(_kinds(m))


def test_adverse_one_line_bound_by_two_tables_fails():
    t = _tables()
    t["T-495"]["finish_held_rows"][0]["id"] = "TW1"           # the wall-tile line bound for adhesive twice
    c = _cand()
    c["lines"]["TW1"].update({"class": "HELD", "measured_net": None, "held_low": 6.0, "held_high": 6.0})
    m = M.run(t, c, pins=False)
    assert "DOUBLE_BOUND" in _kinds(m)                      # T-455 and T-495 adhesive on one line
    t2 = _tables()
    t2["T-455"]["rows"].append(dict(t2["T-455"]["rows"][1]))   # TF1 twice inside one table
    m2 = M.run(t2, _cand(), pins=False)
    assert "DOUBLE_BOUND" in _kinds(m2)


def test_adverse_read_chain_diverges_fails():
    t = _tables()
    t["T-489"]["table"]["rows"][0]["layers"][1]["mortar_m3"] = 0.41    # V2 no longer equals V1
    m = M.run(t, _cand(), pins=False)
    assert "CHAIN_DIVERGES" in _kinds(m) or "ARITHMETIC" in _kinds(m)
    assert any(f["kind"] == "CHAIN_DIVERGES" for f in m["failures"])


def test_adverse_cross_trade_bed_on_a_bedded_surface_fails():
    c = _cand()
    c["lines"]["BO1"] = _ln("BO1", "FIN.FLOOR.BED.DRY", "GF-COURT#T1:bed", "RELEASED", 6.0)
    m = M.run(_tables(), c, pins=False)
    assert "CROSS_TRADE_DOUBLE" in _kinds(m)


def test_adverse_bound_on_held_line_without_range_fails():
    c = _cand()
    c["lines"]["OD1"].update({"held_low": None, "held_high": None})
    t = _tables()
    t["T-495"]["finish_held_rows"][0].update({"area_held_low_m2": None, "area_held_high_m2": None})
    m = M.run(t, c, pins=False)
    assert "UNSOURCED_BOUND" in _kinds(m)


def test_adverse_group_to_buy_with_held_member_fails():
    t = _tables()
    t["T-455"]["purchase"]["adhesive"]["PROJECT"]["bags_to_buy"] = 9
    m = M.run(t, _cand(), pins=False)
    assert "GROUP_HELD_FIGURE" in _kinds(m)


def test_adverse_scope_line_unread_fails_never_zero():
    c = _cand()
    c["lines"]["LX9"] = _ln("LX9", "MAS.BLOCK", "2F-WALLS", "HELD")
    m = M.run(_tables(), c, pins=False)
    assert "SCOPE_LINE_UNREAD" in _kinds(m)


def test_adverse_line_changed_in_candidate_version_fails():
    c = _cand()
    c["changed"] = {"PD1"}
    m = M.run(_tables(), c, pins=False)
    assert "STALE_AT_V3047" in _kinds(m)


def test_adverse_unit_and_arithmetic():
    c = _cand()
    c["lines"]["TF1"]["unit"] = "lm"
    assert "UNIT" in _kinds(M.run(_tables(), c, pins=False))
    t = _tables()
    t["T-453"]["block_materials"][0]["theoretical_count"] = 120.0       # 10 m2 x 12.5 is 125
    t["T-453"]["block_totals"]["black_0_20_by_label"]["VERIFIED-NET"]["theoretical_blocks"] = 120.0
    assert "ARITHMETIC" in _kinds(M.run(t, _cand(), pins=False))


def test_adverse_undeclared_zero_subtotal_fails():
    t = _tables()
    t["T-455"]["by_item_code"]["FIN.WALL.TILE"]["v4_bags_known"] = 0.0
    m = M.run(t, _cand(), pins=False)
    assert "ZERO_SUBTOTAL" in _kinds(m)


# ------------------------------------------------------------------------------------------------ candidate V3.0.47
def test_candidate_v3047_passes_with_named_gaps_and_findings():
    m = M.run()
    assert m["failures"] == [], m["failures"][:5]
    assert m["candidate"] == "ARCH_TAKEOFF_V3.0.47" and m["candidate_sha256"].startswith("e86a53a8")
    agg = {a["total"]: a for a in m["aggregation"]}
    assert agg["T-453 black 0.20 blocks VERIFIED-NET nr"]["sum_of_bound_rows"] == 1346.55
    assert agg["T-453 AAC glue VERIFIED-NET kg"]["sum_of_bound_rows"] == 116.703
    assert agg["T-454 dry WALL_PLASTER mortar m3 (ESTIMATED-NET)"]["sum_of_bound_rows"] == 4.726962
    assert all(a["agree"] for a in m["aggregation"])
    g = m["purchasing_groups_held_members"]["MASONRY_LAYING/PROJECT"]
    assert len(g["without_figure"]) == 13 and g["to_buy"] is None          # T-453's 11 + 2 V3.0.46 lines
    assert m["scope_census"]["T-453|MAS.BLOCK"] == {"lines": 28, "read": 26,
                                                     "known_gaps": sorted(M.KNOWN_GAPS)}
    assert set(m["zero_subtotals_declared"].values()) == {"F-T496-1"}
    assert not any(b["wiring_state"] == "WIREABLE_FIGURE" and b["candidate_class"] != "RELEASED"
                   for b in m["bindings"])


def test_build_is_byte_identical(tmp_path):
    M.write(M.run(), tmp_path / "a")
    M.write(M.run(), tmp_path / "b")
    for f in ("BINDING_MAP_T496.json", "BINDING_MAP_T496.csv"):
        assert (tmp_path / "a" / f).read_bytes() == (tmp_path / "b" / f).read_bytes()
        assert (tmp_path / "a" / f).read_bytes() == (M.HERE / "out" / f).read_bytes()


def test_pins_refuse_a_changed_input(tmp_path, monkeypatch):
    bad = tmp_path / "x.json"
    bad.write_text(json.dumps({"x": 1}))
    monkeypatch.setitem(M.PINS, bad, "0" * 64)
    with pytest.raises(M.MapError):
        M._load(bad)

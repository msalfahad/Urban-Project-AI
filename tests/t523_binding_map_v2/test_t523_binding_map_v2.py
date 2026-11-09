"""T-523 material binding map V2: generic rules on a hand fixture (not the training villa) + the re-staging of the
merged T-496 map on the candidate of record.

Hand fixture K523 (a small villa, numbers by hand):
  tile area A, dry floor 12.0 m2, bed 0.03 .. 0.04 m: installed 0.36 .. 0.48 m3 -> cement 2.88 .. 3.84 bags (x 8)
      owner loss 5 %: 0.144 .. 0.192 bags -> procurement 3.024 .. 4.032 bags
  tile area B, wet floor 8.0 m2, bed 0.04 .. 0.06 m: installed 0.32 .. 0.48 m3 -> 2.56 .. 3.84 bags; loss 0.128 .. 0.192
      -> procurement 2.688 .. 4.032 bags
  CEMENT group (A + B): procurement 5.712 .. 8.064 bags -> ONE ceiling 6 .. 9 bags; per-area ceilings 4 + 3 = 7 ..
      5 + 5 = 10 (+1 bag, never bought)
  tile area C, wall 6.0 m2 / 5 m2 per bag = 1.2 bags; area D, floor 7.0 m2 / 3 = 2.333333 bags
  ADHESIVE group (C + D): 3.533333 -> ONE ceiling 4 bags; per-area ceilings 2 + 3 = 5
"""

import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "t523_binding_map_v2", os.path.join(ROOT, "research", "agents_t523", "t523_binding_map_v2.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

APPROX = dict(abs=1e-6)


def _bed(area, band, loss=0.05):
    inst = (area * band[0] * 8.0, area * band[1] * 8.0)
    return M.member(f"bed {area}", installed=inst, loss=(inst[0] * loss, inst[1] * loss), loss_state="SOURCED")


# ------------------------------------------------------------------ normal cases (K523 by hand) ---------------------
def test_cement_group_one_ceiling_per_villa():
    a, b = _bed(12.0, (0.03, 0.04)), _bed(8.0, (0.04, 0.06))
    assert a["installed"] == (pytest.approx(2.88), pytest.approx(3.84))
    g = M.group_purchase("CEMENT_50KG", [a, b], 1.0)
    assert g["status"] == "COMPUTED"
    assert g["procurement"] == [pytest.approx(5.712, **APPROX), pytest.approx(8.064, **APPROX)]
    assert g["to_buy"] == [6, 9]
    per_area = M.sum_of_subgroup_ceils([(3.024, 4.032), (2.688, 4.032)])
    assert per_area == [7, 10] and per_area[0] > g["to_buy"][0]                 # summed ceilings overstate


def test_adhesive_group_one_ceiling():
    c = M.member("C", installed=(6.0 / 5.0, 6.0 / 5.0))
    d = M.member("D", installed=(7.0 / 3.0, 7.0 / 3.0))
    g = M.group_purchase("TILE_ADHESIVE_20KG", [c, d], 1.0)
    assert g["procurement"] == [pytest.approx(3.533333, **APPROX)] * 2 and g["to_buy"] == [4, 4]
    assert M.sum_of_subgroup_ceils([c["installed"], d["installed"]]) == [5, 5]


def test_ratio_decides_the_stage():
    inst = 12.0 * 0.03
    assert M.stage_from_ratio(inst, inst, "TILE_BED_MORTAR") == (M.INSTALLED, None)
    assert M.stage_from_ratio(inst * 1.05, inst, "TILE_BED_MORTAR") == ("FOLDED", "Q45B_MORTAR_WASTE")


def _t495_like(area_lo, area_hi, folded=True):
    w = 1.05 if folded else 1.0
    b = {"table": "T-495", "row": "BED|L-K523|PORCELAIN_CERAMIC", "line_id": "L-K523", "material": "TILE_BED_MORTAR",
         "kind": "bed_mortar_m3@PORCELAIN_CERAMIC", "value": None,
         "bound": [round(area_lo * 0.03 * w, 6), round(area_hi * 0.04 * w, 6)], "stage": "INSTALLED",
         "status": "HELD", "group": None, "read": {"class_read": "HELD", "held_read": [area_lo, area_hi]},
         "note": None, "estimate_beside": None}
    tables = {"T-495": {"finish_held_rows": [{"id": "L-K523", "options": [
        {"finish": "PORCELAIN_CERAMIC", "bed": {"bed_m": [0.03, 0.04]}}]}]}}
    return b, tables


def test_folded_loss_is_split_into_installed_loss_procurement():
    b, tables = _t495_like(10.0, 10.0)                       # 10 m2: 0.300 .. 0.400 m3 installed, +5 % = 0.315 .. 0.420
    out = M.restage(b, tables)
    by = {x["stage"]: x for x in out}
    assert set(by) == {M.INSTALLED, M.LOSS, M.PROCUREMENT} and all(x["change"] == "MIS_STAGED" for x in out)
    assert by[M.INSTALLED]["bound"] == [pytest.approx(0.3), pytest.approx(0.4)]
    assert by[M.LOSS]["bound"] == [pytest.approx(0.015), pytest.approx(0.02)]
    assert by[M.LOSS]["factor"]["status"] == "ASSUMED - OWNER-APPROVED"
    assert by[M.PROCUREMENT]["bound"] == [pytest.approx(0.315), pytest.approx(0.42)]
    assert by[M.INSTALLED]["value"] is None                   # a HELD option stays a bound, never a figure
    assert by[M.LOSS]["kind"].endswith("@PORCELAIN_CERAMIC")  # still an option: never summed across options


def test_unfolded_figure_keeps_its_stage():
    b, tables = _t495_like(10.0, 10.0, folded=False)
    out = M.restage(b, tables)
    assert len(out) == 1 and out[0]["stage"] == M.INSTALLED and out[0]["change"] == "SAME"


# ------------------------------------------------------------------ adverse cases -----------------------------------
def test_loss_without_source_is_not_stacked_and_group_held():
    a = _bed(12.0, (0.03, 0.04))
    e = M.member("masonry", installed=(10.0, 10.0), loss_state="HELD")         # mortar waste: no source
    g = M.group_purchase("CEMENT_50KG", [a, e], 1.0)
    assert g["status"] == "HELD" and g["to_buy"] is None
    assert g["at_least"] == [pytest.approx(13.024), pytest.approx(14.032)]   # installed only for the held loss
    assert g["to_buy_at_least"] == [14, 15]
    assert "masonry (loss HELD)" in g["open"]


def test_held_installed_never_becomes_zero():
    g = M.group_purchase("CEMENT_50KG", [M.member("H1"), M.member("H2")], 1.0)
    assert g["status"] == "HELD" and g["at_least"] is None and g["to_buy"] is None
    assert g["to_buy_at_least"] is None                                         # nothing known: None, never 0
    g2 = M.group_purchase("CEMENT_50KG", [M.member("H1"), _bed(8.0, (0.04, 0.06))], 1.0)
    assert g2["status"] == "HELD" and g2["at_least"] == [pytest.approx(2.688), pytest.approx(4.032)]


def test_pre_rounded_member_refused():
    m = dict(M.member("R", installed=(3.0, 3.0)), rounded=True)
    with pytest.raises(M.MapV2Error):
        M.group_purchase("CEMENT_50KG", [m], 1.0)


def test_no_pack_record_no_ceiling():
    g = M.group_purchase("SAND_LOOSE", [M.member("S", installed=(1.32, 1.76))], None)
    assert g["status"] == "COMPUTED" and g["to_buy"] is None and g["procurement"] == [1.32, 1.76]


def test_two_producers_on_one_key_refused():
    base = {"line_id": "L-X", "material": "TILE_BED_MORTAR", "kind": "bed_mortar_m3", "stage": M.INSTALLED,
            "stage_v1": "INSTALLED", "value": 0.3, "bound": None, "estimate_beside": None}
    fails = M.check_one_producer([dict(base, table="T-500"), dict(base, table="T-495")])
    assert [f["kind"] for f in fails] == ["DOUBLE_PRODUCER"]
    ok = M.check_one_producer([dict(base, table="T-454", material="WALL_PLASTER", kind="mortar_m3"),
                               dict(base, table="T-489", material="WALL_PLASTER", kind="mortar_m3")])
    assert ok == []                                                            # declared READ chain, values agree
    bad = M.check_one_producer([dict(base, table="T-454", material="WALL_PLASTER", kind="mortar_m3"),
                                dict(base, table="T-489", material="WALL_PLASTER", kind="mortar_m3", value=0.31)])
    assert [f["kind"] for f in bad] == ["CHAIN_DIVERGES"]


def test_unknown_ratio_fails():
    b, tables = _t495_like(10.0, 10.0)
    b["bound"] = [round(10.0 * 0.03 * 1.07, 6), round(10.0 * 0.04 * 1.07, 6)]   # 7 %: no sourced factor
    with pytest.raises(M.MapV2Error, match="UNRESOLVED_STAGE"):
        M.restage(b, tables)


def test_stale_line_figure_goes_beside():
    b = {"line_id": "L-S", "stage_v1": "THEORETICAL", "value": 89.3375, "bound": None,
         "read": {"class_read": "RELEASED", "net_read": 25.525}}
    idx = {"lines": [{"line_id": "L-S", "class": "HELD", "measured_net": None}]}
    M.freshness([b], idx)
    assert b["value"] is None and b["beside"]["value"] == 89.3375 and b["fresh"].startswith("STALE_CLASS")
    b2 = dict(b, value=10.0, read={"class_read": "RELEASED", "net_read": 21.5261})
    M.freshness([b2], {"lines": [{"line_id": "L-S", "class": "RELEASED", "measured_net": 8.595}]})
    assert b2["value"] is None and b2["fresh"].startswith("STALE_NET")


# ------------------------------------------------------------------ the merged map re-staged ------------------------
@pytest.fixture(scope="module")
def v2():
    paths = list(M.PINS) + [os.path.join(ROOT, "research/agents_t496/out/BINDING_MAP_T496.json")]
    raw = {p: open(p, "rb").read() for p in paths}
    out = M.run()
    for p, r in raw.items():
        assert open(p, "rb").read() == r                                          # read only
    return out


def test_every_v1_binding_restaged_without_failure(v2):
    assert v2["failures"] == []
    assert v2["v1_bindings"] == v2["v1_read"] == 1202
    assert v2["v2_bindings"] == 1202 + 2 * 3                                      # 3 mis-staged rows -> 3 bindings each
    assert set(v2["stages"]) == {M.INSTALLED, M.LOSS, M.PROCUREMENT}
    assert v2["released_quantities_changed"] == 0


def test_mis_staged_t495_bed(v2):
    ms = v2["mis_staged"]
    assert len(ms) == 9 and {m["factor"] for m in ms if m["stage"] == M.LOSS} == {"Q45B_MORTAR_WASTE"}
    inst = sorted((m["line_id"], m["kind"], tuple(m["bound"])) for m in ms if m["stage"] == M.INSTALLED)
    # D-T518-2 by hand: 6.548912 x 0.03 / 0.04 and 10.6785 x 0.03 / 0.04 (the two options of the porch share one bed)
    assert [x[2] for x in inst] == [(pytest.approx(0.196467, **APPROX), pytest.approx(0.261956, **APPROX)),
                                    (pytest.approx(0.320355, **APPROX), pytest.approx(0.42714, **APPROX)),
                                    (pytest.approx(0.320355, **APPROX), pytest.approx(0.42714, **APPROX))]
    proc = [m for m in ms if m["stage"] == M.PROCUREMENT]
    assert all(m["bound"] == m["v1_figure"] for m in proc)                      # the V1 figure survives as procurement


def test_stale_on_v3057(v2):
    stale = sorted({b["line_id"] for b in v2["bindings"] if b["fresh"].startswith("STALE")})
    assert stale == ["L-76a4d8e50423fb02b914", "L-9056ebed77701b50abfc", "L-a6eedf5e4adec6d07618",
                     "L-adb393d6db51056d343b", "L-bbb82de298fecbafa11d", "L-e1e06ec149b44d4f6f8a",
                     "L-e90c9dd5ca08ffb64728"]
    assert all(b["table"] == "T-453" for b in v2["bindings"] if b["fresh"].startswith("STALE"))


def test_cement_restated(v2):
    c = v2["groups"]["CEMENT_SAND"]["CEMENT_50KG"]
    assert c["installed_known_part"] == [pytest.approx(125.12628, **APPROX), pytest.approx(164.620992, **APPROX)]
    assert c["installed_known_part"] == [pytest.approx(x, **APPROX) for x in c["t514_prints"]["installed_at_least"]]
    assert c["procurement_known_part_v1"] == [pytest.approx(x, **APPROX) for x in c["t514_prints"]["procurement_at_least"]]
    g = c["group"]
    assert g["status"] == "HELD" and g["to_buy"] is None
    # V2: + the 10.155552 installed bags of the masonry members whose loss is HELD (120.661015 + 10.155552)
    assert g["at_least"] == [pytest.approx(130.816567, **APPROX), pytest.approx(172.286014, **APPROX)]
    assert c["ceilings"]["one_ceiling_at_least"] == [131, 173]
    assert c["ceilings"]["sum_of_trade_ceilings"] == [133, 175]


def test_glue_and_adhesive_groups(v2):
    gl = v2["groups"]["AAC_GLUE_25KG"]
    assert gl["status"] == "HELD" and gl["to_buy"] is None
    assert {s["line"] for s in gl["stale_beside"]} == {"L-9056ebed77701b50abfc", "L-e90c9dd5ca08ffb64728",
                                                         "L-bbb82de298fecbafa11d"}
    ad = v2["groups"]["TILE_ADHESIVE_20KG"]
    assert ad["status"] == "HELD" and ad["at_least"] is None and ad["to_buy"] is None


def test_change_census(v2):
    # V1 INSTALLED rows 321 (T-453 mortar 4, T-454 / T-489 mortar 156 + 156, T-495 bed 5): 3 mis-staged, 318 SAME;
    # 60 lintel rows with no candidate line; every other V1 row was 'THEORETICAL' = INSTALLED by its code (RELABEL)
    assert v2["changes"] == {"MIS_STAGED": 9, "NO_LINE": 60, "RELABEL": 821, "SAME": 318}
    assert v2["fresh"]["STALE_CLASS"] + v2["fresh"].get("STALE_NET", 0) == 21


def test_t498_slice_known_parts(v2):
    s = v2["t498_slice"]["known_part_by_label"]
    # T-453 r2 read V3.0.45; on V3.0.57 2F L-76a4 (21.66 m2, 270.75 blocks, 0.319485 m3) and the white L-e90c
    # (21.476 m2 x 4.5 = 96.642 kg VERIFIED) / L-9056 (25.525 m2 x 3.5 = 89.3375 kg PROVISIONAL) are HELD lines
    assert s["units_nr|VERIFIED-NET"]["delta"] == pytest.approx(-270.75, **APPROX)
    assert s["mortar_m3|PROVISIONAL-NET"]["v1"] == pytest.approx(1.588929, **APPROX)
    assert s["mortar_m3|PROVISIONAL-NET"]["v2"] == pytest.approx(1.269444, **APPROX)
    assert s["cement_bags|PROVISIONAL-NET"]["v2"] == pytest.approx(10.155552, **APPROX)
    assert s["glue_kg|VERIFIED-NET"]["v2"] == pytest.approx(116.703 - 96.642, **APPROX)
    assert s["glue_kg|PROVISIONAL-NET"]["v2"] == pytest.approx(112.8725 - 89.3375, **APPROX)
    gl = v2["groups"]["AAC_GLUE_25KG"]
    # figures 20.061 / 25 + 23.535 / 25 = 1.74384 bags; fresh ranges 36.28818 .. 37.31778 minus L-bbb8 2.60577 ..
    # 2.86497 = 33.68241 .. 34.45281
    assert gl["at_least"] == [pytest.approx(35.42625, **APPROX), pytest.approx(36.19665, **APPROX)]
    assert gl["to_buy_at_least"] == [36, 37]

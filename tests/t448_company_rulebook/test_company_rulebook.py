"""T-448: Urban Projects Company Rulebook 1.0.0 - one worked example per OWNER CONFIRMED rule (hand-calculated, not
from any project), the hierarchy (project override, level 4 limits, HELD never 0) and adverse cases."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import company_rulebook_v1 as C  # noqa: E402

BOOK = ROOT / "rules" / C.REL
IDENTITY = re.compile("YEARS" + " 2013|7757-[A-Z]|(?i:als[ey]?n[ya]?an)")
OWNER_RULES = ("UPC-LINTEL-001", "UPC-ADHESIVE-001", "UPC-AAC-GLUE-001", "UPC-BLACK-BLOCK-001", "UPC-BLACK-MORTAR-001",
               "UPC-TILE-BED-001", "UPC-WETWALL-001", "UPC-HEIGHT-001", "UPC-BLOCK-OPENINGS-001")


# ---------------------------------------------------------------- the file

def test_every_owner_rule_has_id_value_unit_scope_source_and_level_3():
    book = C.load()
    ids = [r["rule_id"] for r in book["records"]]
    assert len(ids) == len(set(ids))
    for rid in OWNER_RULES:
        r = C.record(rid)
        assert r["level"] == 3 and r["basis"] == "OWNER CONFIRMED COMPANY RULE" and r["status"] == "OWNER_CONFIRMED"
        assert r["scope"].strip() and r["source"].strip() and r["version"] == "1.0.0"
        assert r["params"], rid
        for name, p in r["params"].items():
            assert "unit" in p and "value" in p, (rid, name)
            if name == "waste":                                # waste is separate: no company value, sourced only
                assert p["value"] is None, rid
            else:
                assert p["value"] is not None, (rid, name)    # an owner rule carries its value


def test_the_not_owner_given_layers_are_level_4_with_every_value_held():
    r = C.record("UPC-CEMENT-LAYERS-METHOD-001")
    assert r["level"] == 4 and r["basis"] == "ENGINEERING ESTIMATE"
    assert all(p["value"] is None for p in r["params"].values())


def test_registered_in_the_rule_store_manifest_and_carries_no_client_identity():
    man = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    rec = man["files"]["rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"]
    assert rec["kind"] == "AUTHORED" and rec["sha256"] == hashlib.sha256(BOOK.read_bytes()).hexdigest()
    for p in (BOOK, ROOT / "engine/source/company_rulebook_v1.py"):
        assert IDENTITY.search(p.read_text(encoding="utf-8")) is None, p
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools/m9_rules_manifest.py"), "check"], capture_output=True,
                       text=True)
    assert r.returncode == 0, r.stdout


def test_three_records_rederived_from_the_owner_text():
    """owner text (MISSION register 2026-11-02 / Q-45 / Q-75 / Q-78) -> the stored values."""
    assert C.param("UPC-AAC-GLUE-001", "kg_per_m2_by_thickness_m")["value"] == {"0.15": 3.5, "0.20": 4.5}
    assert C.param("UPC-AAC-GLUE-001", "bag_kg")["value"] == 25.0
    assert C.param("UPC-ADHESIVE-001", "coverage_m2_per_bag_by_size_cm")["value"] == {"60x60": 5.0, "120x60": 3.0,
                                                                                      "160x80": 3.0}
    assert C.param("UPC-ADHESIVE-001", "bag_kg")["value"] == 20.0
    assert C.param("UPC-LINTEL-001", "stock_lengths_m")["value"] == [1.20, 1.50, 2.50, 3.00, 4.00]
    assert 1.00 not in C.param("UPC-LINTEL-001", "stock_lengths_m")["value"]
    assert C.param("UPC-LINTEL-001", "min_bearing_each_side_m")["value"] == 0.15
    assert C.param("UPC-BLACK-BLOCK-001", "blocks_per_m2_40x20_module")["value"] == 12.5
    assert C.param("UPC-BLACK-MORTAR-001", "mix_cement_sand")["value"] == "1:4"


# ---------------------------------------------------------------- lintels

def test_lintel_owner_example_1_10_with_0_20_bearing_is_1_50():
    r = C.lintel(1.10, bearing={"m": 0.20, "source": "drawing detail (fixture)"})
    assert (r["status"], r["required_m"], r["piece_m"], r["count"]) == ("COMPUTED", 1.50, 1.50, 1)
    assert r["bearing_basis"] == "PROJECT DOCUMENT"


def test_lintel_company_minimum_bearing_and_stock_boundaries():
    r = C.lintel(1.10)                                   # 1.10 + 2 x 0.15 = 1.40 -> 1.50
    assert (r["required_m"], r["piece_m"], r["bearing_basis"]) == (1.40, 1.50, "OWNER CONFIRMED COMPANY RULE")
    assert C.lintel(0.90)["piece_m"] == 1.20             # 1.20 exactly fits (boundary, no float creep)
    assert C.lintel(0.70)["piece_m"] == 1.20             # 1.00 is not a company stock length
    assert C.lintel(3.70)["piece_m"] == 4.00             # 4.00 exactly
    assert "NOT_PERFORMED" in r["capacity_check"]


def test_lintel_adverse_long_span_flagged_missing_held_low_bearing_conflict():
    r = C.lintel(4.00, bearing={"m": 0.20, "source": "owner example"})     # needs 4.40 > 4.00
    assert r["status"] == "FLAGGED" and r["piece_m"] is None and r["required_m"] == 4.40
    assert C.lintel(3.71)["status"] == "FLAGGED"
    assert C.lintel(None)["status"] == "HELD"
    low = C.lintel(1.00, bearing={"m": 0.10, "source": "drawing note (fixture)"})
    assert low["status"] == "FLAGGED" and "CONFLICT" in low["why"]
    with pytest.raises(C.RulebookError):
        C.lintel(1.00, bearing={"m": 0.20})                               # a bearing with no source
    with pytest.raises(C.RulebookError):
        C.lintel(-1.0)


def test_lintel_supplier_record_adds_1_00_for_that_project_only():
    proj = {"UPC-LINTEL-001": {"stock_lengths_m": {"value": [1.00, 1.20, 1.50, 2.50, 3.00, 4.00], "level": 1,
                                                   "source": "supplier price list (fixture)"}}}
    r = C.lintel(0.70, project=proj)
    assert r["piece_m"] == 1.00 and r["stock_basis"] == "PROJECT DOCUMENT"
    assert C.lintel(0.70)["piece_m"] == 1.20                              # the rulebook is unchanged
    assert 1.00 not in C.record("UPC-LINTEL-001")["params"]["stock_lengths_m"]["value"]


# ---------------------------------------------------------------- tile adhesive

def test_adhesive_12_m2_of_120x60_is_4_bags_and_orientation_does_not_matter():
    for size in ("120x60", "60x120", (60, 120), "120 x 60"):
        g = C.adhesive_bags([{"id": "r1", "area_m2": 12.0, "tile_cm": size}])["groups"]["PROJECT"]
        assert (g["status"], g["bags_net"], g["bags_to_buy"]) == ("COMPUTED", 4.0, 4)


def test_adhesive_rounds_once_per_purchasing_group_not_per_room():
    rows = [{"id": f"room{i}", "area_m2": 2.2, "tile_cm": "60x60"} for i in range(5)]   # 5 x 0.44 bags
    res = C.adhesive_bags(rows)
    assert [r["consumption"] for r in res["rows"]] == [0.44] * 5                      # room values fractional
    assert res["groups"]["PROJECT"]["bags_to_buy"] == 3                                # ceil(2.2), not 5 x ceil
    rows2 = [dict(rows[0], purchasing_group="A"), dict(rows[1], purchasing_group="B")]
    gs = C.adhesive_bags(rows2)["groups"]
    assert gs["A"]["bags_to_buy"] == 1 and gs["B"]["bags_to_buy"] == 1


def test_adhesive_160x80_and_mixed_sizes():
    res = C.adhesive_bags([{"id": "a", "area_m2": 9.0, "tile_cm": "160x80"},     # 3.0 bags
                           {"id": "b", "area_m2": 7.5, "tile_cm": "60x60"}])     # 1.5 bags
    assert res["groups"]["PROJECT"]["bags_net"] == 4.5 and res["groups"]["PROJECT"]["bags_to_buy"] == 5


def test_adhesive_adverse_unknown_size_held_never_the_60x60_rate():
    res = C.adhesive_bags([{"id": "a", "area_m2": 10.0, "tile_cm": "30x60"},
                           {"id": "b", "area_m2": 10.0, "tile_cm": "60x60"}])
    a = res["rows"][0]
    assert a["status"] == "HELD" and a["consumption"] is None and "never the 60 x 60 rate" in a["why"]
    g = res["groups"]["PROJECT"]
    assert g["status"] == "HELD" and g["bags_to_buy"] is None and g["consumption_known"] == 2.0   # never 0
    for bad in ({"id": "m", "area_m2": 5, "tile_cm": "60x60", "material": "MARBLE"},
                {"id": "n", "area_m2": None, "tile_cm": "60x60"}, {"id": "s", "area_m2": 5}):
        assert C.adhesive_bags([bad])["groups"]["PROJECT"]["status"] == "HELD"


def test_adhesive_normal_class_only_by_a_sourced_project_classification():
    proj = {"UPC-ADHESIVE-001": {"normal_class_sizes": {"60x30": "owner project decision (fixture)"}}}
    r = C.adhesive_bags([{"id": "a", "area_m2": 10.0, "tile_cm": "30x60"}], project=proj)
    assert r["rows"][0]["coverage_m2_per_bag"] == 5.0 and r["rows"][0]["basis"] == "OWNER PROJECT DECISION"
    with pytest.raises(C.RulebookError):
        C.adhesive_bags([{"id": "a", "area_m2": 1, "tile_cm": "30x60"}],
                        project={"UPC-ADHESIVE-001": {"normal_class_sizes": {"60x30": ""}}})


def test_waste_kept_separate_and_only_with_a_source():
    rows = [{"id": "a", "area_m2": 12.0, "tile_cm": "120x60"}]
    g = C.adhesive_bags(rows, waste={"value": 0.10, "source": "supplier data (fixture)"})["groups"]["PROJECT"]
    assert g["bags_net"] == 4.0 and g["bags_to_buy"] == 5 and g["waste_applied"]     # ceil(4.4)
    assert C.adhesive_bags(rows)["groups"]["PROJECT"]["waste_applied"] is False
    with pytest.raises(C.RulebookError):
        C.adhesive_bags(rows, waste={"value": 0.05})


# ---------------------------------------------------------------- AAC glue, black block, mortar, bed

def test_aac_bond_bags_20_m2_of_20_cm_is_90_kg_and_4_bags():
    g = C.aac_bond_bags([{"id": "w1", "net_area_m2": 20.0, "thickness_m": 0.20}])["groups"]["PROJECT"]
    assert (g["consumption_known"], g["bags_net"], g["bags_to_buy"]) == (90.0, 3.6, 4)
    g15 = C.aac_bond_bags([{"id": "w2", "net_area_m2": 50.0, "thickness_m": 0.15}])["groups"]["PROJECT"]
    assert (g15["consumption_known"], g15["bags_to_buy"]) == (175.0, 7)                # 7.0 bags exactly


def test_aac_bond_bags_adverse_other_thickness_and_missing_area_held():
    res = C.aac_bond_bags([{"id": "a", "net_area_m2": 10.0, "thickness_m": 0.10},
                      {"id": "b", "net_area_m2": 10.0, "thickness_m": 0.20}])
    assert res["rows"][0]["status"] == "HELD" and res["groups"]["PROJECT"]["status"] == "HELD"
    assert res["groups"]["PROJECT"]["consumption_known"] == 45.0
    assert C.aac_bond_bags([{"id": "c", "net_area_m2": None, "thickness_m": 0.20}])["groups"]["PROJECT"]["bags_to_buy"] is None


def test_black_blocks_12_5_only_for_the_confirmed_40x20_module():
    r = C.black_blocks(10.0, 0.20)
    assert (r["status"], r["theoretical_count"], r["procurement_count"]) == ("COMPUTED", 125.0, None)
    assert C.black_blocks(10.0, 0.20, waste={"value": 0.03, "source": "evidence (fixture)"})["procurement_count"] == 129
    h = C.black_blocks(10.0, 0.15)
    assert h["status"] == "HELD" and "not borrowed" in h["why"]                         # 15 cm module not stated
    proj = {"UPC-BLACK-BLOCK-001": {"confirmed_modules_m": {"value": {"0.15": [0.40, 0.20], "0.20": [0.40, 0.20]},
                                                            "level": 1, "source": "block schedule (fixture)"}}}
    assert C.black_blocks(8.0, 0.15, project=proj)["theoretical_count"] == 100.0
    other = {"UPC-BLACK-BLOCK-001": {"confirmed_modules_m": {"value": {"0.20": [0.40, 0.25]}, "level": 1,
                                                             "source": "supplier (fixture)"}}}
    assert C.black_blocks(10.0, 0.20, project=other)["status"] == "HELD"
    assert C.black_blocks(None, 0.20)["status"] == "HELD"


def test_black_block_laying_materials_and_tile_bed_ranges():
    m = C.black_block_laying_materials(2.0)
    assert (m["mix"], m["cement_bags"], m["sand_m3_loose"]) == ("1:4", 16.0, 2.2)
    b = C.tile_bed(10.0, "WET")
    assert b["mortar_m3"] == (0.4, 0.6) and b["cement_bags"] == (3.2, 4.8) and b["sand_m3_loose"] == (0.44, 0.66)
    assert C.tile_bed(10.0, "REGULAR")["mortar_m3"] == (0.3, 0.4)
    assert C.tile_bed(10.0, "ROOF")["status"] == "HELD" and C.tile_bed(None, "WET")["status"] == "HELD"
    assert C.black_block_laying_materials(None)["status"] == "HELD"


def test_wet_wall_three_operations_and_heights_are_records():
    ops = [o["op"] for o in C.param("UPC-WETWALL-001", "operations")["value"]]
    assert ops == ["SPATTER_DASH", "LEVELLING_RENDER", "ADHESIVE_AND_PORCELAIN"]
    assert C.param("UPC-WETWALL-001", "second_fixing_bed")["value"] is False
    assert C.param("UPC-HEIGHT-001", "plaster_top")["value"] == "UNDERSIDE_OF_STRUCTURAL_SLAB_OR_ROOF"
    assert C.param("UPC-HEIGHT-001", "paint_top")["value"] == "FINISHED_CEILING"
    assert C.param("UPC-BLOCK-OPENINGS-001", "deduct_all_openings")["value"] is True


# ---------------------------------------------------------------- hierarchy and level 4

def test_cement_layers_held_until_sourced_and_level_4_cannot_replace_an_owner_value():
    r = C.cement_layer(20.0, "LEVELLING_RENDER")
    assert r["status"] == "HELD" and r["mortar_m3"] is None and r["sensitivity_m3_per_mm"] == 0.02
    est = {"UPC-CEMENT-LAYERS-METHOD-001": {"levelling_render_thickness_m": {
        "value": 0.015, "level": 4, "source": "reference book clause (fixture)"}}}
    e = C.cement_layer(20.0, "LEVELLING_RENDER", project=est)
    assert e["status"] == "COMPUTED" and e["mortar_m3"] == 0.3 and e["label"] == "ENGINEERING ESTIMATE"
    assert e["materials_status"] == "HELD"                                              # no mix given
    with pytest.raises(C.RulebookError):                                                # level 4 over level 3
        C.param("UPC-AAC-GLUE-001", "bag_kg",
                project={"UPC-AAC-GLUE-001": {"bag_kg": {"value": 30, "level": 4, "source": "x"}}})
    for bad in ({"value": 30, "level": 3, "source": "x"}, {"value": 30, "level": 1, "source": ""},
                {"value": None, "level": 1, "source": "x"}):
        with pytest.raises(C.RulebookError):
            C.param("UPC-AAC-GLUE-001", "bag_kg", project={"UPC-AAC-GLUE-001": {"bag_kg": bad}})
    with pytest.raises(C.RulebookError):
        C.cement_layer(1.0, "PAINT")


def test_a_project_override_never_changes_the_rulebook():
    before = C.digest()
    C.param("UPC-AAC-GLUE-001", "bag_kg",
            project={"UPC-AAC-GLUE-001": {"bag_kg": {"value": 30.0, "level": 2, "source": "owner decision (fixture)"}}})
    rec = C.load()
    rec["records"][0]["params"]["stock_lengths_m"]["value"].append(9.0)          # a caller mutating its copy
    assert C.digest() == before and 9.0 not in C.param("UPC-LINTEL-001", "stock_lengths_m")["value"]

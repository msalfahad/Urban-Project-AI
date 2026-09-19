"""Synthetic sheets for the plaster engine. No P7757 value anywhere."""

from __future__ import annotations

from engine import plaster_trade_engine as E
from engine import qs_measurement_region as M
from research.a21_trace_sufficiency_01 import parameters as PM
from tests.test_qs_measurement_region import fixture_a

PL = "NORMAL_INTERNAL_PLASTER"


def _region():
    walls, sites, openings = fixture_a()
    return M.build_region(region_id="A", physical_edges=walls, sites=sites,
                          openings=openings, trade=PL, basis="WALL_FACE_PLASTER")


def test_unknown_height_gives_not_established_and_a_readable_sheet():
    r = E.calculate(_region(), PM.default_registry(), treatment=PL)
    assert r["QUANTITY_STATE"]["PRINCIPAL_WALL_FACE"] == "NOT_ESTABLISHED"
    assert r["RESULT"]["PRINCIPAL_WALL_FACE_M2"] is None
    lines = {l["LINE"] for l in r["SHEET"]}
    assert {"HEIGHT", "WALL", "GROSS", "DEDUCTION", "REVEAL",
            "PRINCIPAL_WALL_FACE", "STEEL_CORNER_AND_EDGE_PROFILES"} <= lines
    assert any(l["LINE"] == "SYNTHETIC_CLOSURE" and l["AREA_M2"] == 0.0
               for l in r["SHEET"])


def test_owner_height_gives_owner_parametric_with_default_door_provisional():
    reg = PM.with_owner_value(PM.default_registry(), "APPLICABLE_PLASTER_HEIGHT",
                              3.0, "m", 2, "synthetic owner value")
    r = E.calculate(_region(), reg, treatment=PL)
    # walls 13.0 lm x 3.0 = 39.0 gross; door 1.0 x 2.20 default = 2.2
    gross = next(l for l in r["SHEET"] if l["LINE"] == "GROSS")["AREA_M2"]
    assert gross == 39.0
    assert r["RESULT"]["PRINCIPAL_WALL_FACE_M2"] == 36.8
    # the door HEIGHT is a temporary default, so the wall face is provisional
    assert r["QUANTITY_STATE"]["PRINCIPAL_WALL_FACE"] == "PROVISIONAL_DEFAULT_QUANTITY"
    # reveals need a depth the registry does not have -> not established,
    # and that does NOT drag the wall face down with it
    assert r["RESULT"]["REVEALS_AND_RETURNS_M2"] is None
    assert r["QUANTITY_STATE"]["REVEALS_AND_RETURNS"] == "NOT_ESTABLISHED"
    # profiles depend on the owner height only
    assert r["RESULT"]["STEEL_PROFILES_LM"] == 6.0
    assert r["QUANTITY_STATE"]["STEEL_PROFILES"] == "OWNER_PARAMETRIC_QUANTITY"
    assert r["RESULT"]["M2_AND_LM_ARE_NEVER_COMBINED"] is True


def test_every_input_from_source_gives_source_established():
    walls, sites, openings = fixture_a()
    openings[0]["height_m"] = 2.1
    openings[0]["height_source"] = "DRAWING"
    region = M.build_region(region_id="A", physical_edges=walls, sites=sites,
                            openings=openings, trade=PL, basis="WALL_FACE_PLASTER")
    reg = PM.default_registry()
    reg["APPLICABLE_PLASTER_HEIGHT"] = PM.parameter(
        "APPLICABLE_PLASTER_HEIGHT", 3.0, "m", "SPECIFICATION",
        "synthetic spec clause")
    reg["DOOR_REVEAL_DEPTH"] = PM.parameter(
        "DOOR_REVEAL_DEPTH", 0.2, "m", "DRAWING", "synthetic printed thickness")
    r = E.calculate(region, reg, treatment=PL)
    assert r["QUANTITY_STATE"]["PRINCIPAL_WALL_FACE"] == "SOURCE_ESTABLISHED_QUANTITY"
    assert r["QUANTITY_STATE"]["REVEALS_AND_RETURNS"] == "SOURCE_ESTABLISHED_QUANTITY"
    assert r["RESULT"]["PRINCIPAL_WALL_FACE_M2"] == 36.9        # 39.0 - 2.1
    assert r["RESULT"]["REVEALS_AND_RETURNS_M2"] == 1.04        # (4.2+1.0)*0.2


def test_unformed_region_yields_no_sheet():
    walls, _, _ = fixture_a()
    from tests.test_qs_measurement_region import site
    sites = [site("S-GAP", (2.5, 0), (1.5, 0), 1.0, kind="UNRESOLVED_GAP")]
    region = M.build_region(region_id="B", physical_edges=walls, sites=sites,
                            openings=[], trade=PL, basis="WALL_FACE_PLASTER")
    r = E.calculate(region, PM.default_registry(), treatment=PL)
    assert r["QUANTITY_STATE"] == "NOT_ESTABLISHED"    # no sheet, no lines
    assert r["SHEET"] == []


def test_reader_source_types_rank_and_weak_reads_are_flagged():
    walls, sites, openings = fixture_a()
    walls[0]["length_source"] = "DRAWING_SCALED_MEASUREMENT"
    region = M.build_region(region_id="A", physical_edges=walls, sites=sites,
                            openings=openings, trade=PL, basis="WALL_FACE_PLASTER")
    reg = PM.with_owner_value(PM.default_registry(), "APPLICABLE_PLASTER_HEIGHT",
                              3.0, "m", 2, "synthetic owner value")
    r = E.calculate(region, reg, treatment=PL)
    assert "DRAWING_SCALED_MEASUREMENT" in r["INPUTS_THAT_ARE_WEAK_READS"]
    # a scaled read is still a drawing read; the default door height is
    # what makes the wall face provisional, not the scale
    assert r["QUANTITY_STATE"]["PRINCIPAL_WALL_FACE"] == "PROVISIONAL_DEFAULT_QUANTITY"

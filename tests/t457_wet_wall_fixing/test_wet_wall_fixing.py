"""T-457 (owner directive 2026-11-02 C2, re-scoped by the owner's site practice): a wet wall carries ONE fixing material
(tile adhesive); the levelling render is its own operation beside the spatter dash (UPC-WETWALL-001); no second mortar
fixing bed. FINISH_MATERIALS_TABLE_V3. Synthetic hand cases only (no project).

Hand fixture: a 2.40 x 1.80 m bathroom, one 0.80 m door, tile to 2.70 m, one 0.60 x 0.60 m window:
    run 2 x (2.40 + 1.80) - 0.80 = 7.60 m; gross 7.60 x 2.70 = 20.52 m2; net 20.52 - 0.36 = 20.16 m2
    adhesive 20.16 / 5 = 4.032 bags (20 kg, porcelain, V1 value kept)
    V1 / V2 'bed' 20.16 x 0.02 x 1.05 = 0.42336 m3, 3.38688 bags, 0.465696 m3 sand (the layer V3 no longer prices)
    V3 render with a sourced 15 mm: 20.16 x 0.015 = 0.3024 m3; sensitivity 20.16 / 1000 = 0.02016 m3 per mm
Dry floor 20 m2 keeps its bed: 0.63 .. 0.84 m3, 5.04 .. 6.72 bags, 0.693 .. 0.924 m3 sand, 4 adhesive bags."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t456"))
sys.path.insert(0, str(ROOT / "research" / "agents_t457"))

from engine.source import company_rulebook_v1 as RB           # noqa: E402
from engine.source import finish_materials_table as V1        # noqa: E402
from engine.source import finish_materials_table_v2 as V2     # noqa: E402
from engine.source import finish_materials_table_v3 as V3     # noqa: E402

LAYER_RID = "UPC-CEMENT-LAYERS-METHOD-001"


def bath(u=1.0, **kw):
    s = 1.0 / u
    e = {"id": "WW-1", "floor": "GF", "kind": V1.WET_WALL, "wall_length": 8.40 * s, "door_widths": [0.80 * s],
         "height": 2.70 * s, "openings": [{"id": "W-1", "width": 0.60 * s, "height": 0.60 * s}], "unit_m": u}
    e.update(kw)
    return e


def render(t, level=1, source="project specification, wall tiling clause (synthetic)", name="levelling_render"):
    return {LAYER_RID: {f"{name}_thickness_m": {"value": t, "level": level, "source": source}}}


def ops(r):
    return {o["op"]: o for o in r["operations"]}


# ------------------------------------------------------------------ step 1: what V1 / V2 charge (reproduction)
def test_v2_charges_the_wet_wall_layer_as_a_bed_beside_the_adhesive():
    r = V2.row(bath())
    assert r["area_m2"] == pytest.approx(20.16)
    assert (r["bed_low_m"], r["mix"], r["mortar_status"]) == (0.02, "1:4", "PROVISIONAL")
    assert r["mortar_m3_low"] == pytest.approx(0.42336) and r["cement_bags_low"] == pytest.approx(3.38688)
    assert r["sand_m3_low"] == pytest.approx(0.465696) and r["adhesive_bags"] == pytest.approx(4.032)


# ------------------------------------------------------------------ normal case
def test_wet_wall_one_fixing_material_and_three_operations():
    r = V3.row(bath())
    assert r["area_m2"] == pytest.approx(20.16) and r["status"] == "RELEASED"
    assert r["fixing_material"] == "ADHESIVE" and r["adhesive_bags"] == pytest.approx(4.032)
    for k in V3.BED_KEYS:
        assert r[k] is None
    assert r["mortar_status"] == r["cement_sand_status"] == V3.NOT_APPLICABLE
    assert "NO_FIXING_BED" in r["mortar_reason"]
    assert [o["op"] for o in r["operations"]] == ["SPATTER_DASH", "LEVELLING_RENDER", "ADHESIVE_AND_PORCELAIN"]
    assert [o["by"].split()[0] for o in r["operations"]] == ["plasterer", "tiler", "tiler"]
    for o in r["operations"]:
        assert o["area_m2"] == pytest.approx(20.16)
    fixing = [o for o in r["operations"] if o.get("fixing_material")]
    assert len(fixing) == 1 and fixing[0]["adhesive_bags"] == pytest.approx(4.032)


def test_render_and_spatter_dash_held_without_a_sourced_thickness_never_2cm():
    o = ops(V3.row(bath()))
    for op in ("SPATTER_DASH", "LEVELLING_RENDER"):
        assert o[op]["mortar_m3"] is None and o[op]["mortar_status"] == "HELD"
        assert o[op]["thickness_m"] is None and o[op]["thickness_basis"] == "ASSUMPTION-UNRESOLVED"
        assert o[op]["sensitivity_m3_per_mm"] == pytest.approx(0.02016)
        assert o[op]["area_m2"] == pytest.approx(20.16)            # the area is never blocked by a material value


def test_render_with_a_project_thickness_is_computed_once():
    r = V3.row(bath(), project=render(0.015))
    o = ops(r)
    assert o["LEVELLING_RENDER"]["mortar_m3"] == pytest.approx(0.3024)
    assert o["LEVELLING_RENDER"]["thickness_basis"] == "PROJECT DOCUMENT"
    assert o["LEVELLING_RENDER"]["materials_status"] == "HELD"      # no sourced mix: cement / sand never borrowed
    assert o["SPATTER_DASH"]["mortar_m3"] is None                    # the override names the render only
    assert r["mortar_m3_low"] is None                                # never also a bed


def test_engineering_estimate_needs_its_source_and_is_labelled():
    o = ops(V3.row(bath(), project=render(0.015, level=4, source="reference book, render chapter (synthetic)")))
    assert o["LEVELLING_RENDER"]["thickness_basis"] == "ENGINEERING ESTIMATE"
    with pytest.raises(RB.RulebookError):
        V3.row(bath(), project=render(0.015, source=""))
    with pytest.raises(RB.RulebookError):
        V3.row(bath(), project=render(0.015, level=3))


@pytest.mark.parametrize("t", [15, 20.0, 0.5])
def test_render_thickness_in_mm_or_typo_is_held_never_computed(t):
    o = ops(V3.row(bath(), project=render(t)))["LEVELLING_RENDER"]
    assert o["mortar_m3"] is None and o["mortar_reason"].startswith("THICKNESS_OUT_OF_RANGE")


def test_millimetre_drawing_units_give_the_same_wet_wall():
    r = V3.row(bath(u=0.001))
    assert r["area_m2"] == pytest.approx(20.16)
    assert ops(r)["LEVELLING_RENDER"]["area_m2"] == pytest.approx(20.16)
    assert r["adhesive_bags"] == pytest.approx(4.032)


# ------------------------------------------------------------------ adverse: a second fixing bed is refused
@pytest.mark.parametrize("key", ["fixing_bed_m", "bed_m", "bed_low_m", "bed_high_m"])
def test_a_mortar_fixing_bed_asked_on_a_wet_wall_is_refused(key):
    with pytest.raises(ValueError, match="SECOND_FIXING_BED"):
        V3.row(bath(**{key: 0.02}))


def test_owner_values_bed_for_wet_wall_is_never_used_as_a_fixing_bed():
    vals = dict(V3.OWNER_VALUES)
    vals["bed_m"] = dict(vals["bed_m"], **{V1.WET_WALL: (0.03, 0.05)})
    r = V3.row(bath(), values=vals)
    assert r["mortar_m3_low"] is None and r["mortar_m3_high"] is None and r["fixing_material"] == "ADHESIVE"


# ------------------------------------------------------------------ adverse: the floors keep their own bed
@pytest.mark.parametrize("e", [
    {"id": "DF", "floor": "GF", "kind": V1.DRY_FLOOR, "area_m2": 20.0},
    {"id": "DFp", "floor": "GF", "kind": V1.DRY_FLOOR, "polygon": [(0, 0), (4, 0), (4, 5), (0, 5)]},
    {"id": "DFr", "floor": "GF", "kind": V1.DRY_FLOOR, "polygon": [(0, 0), (-5, 0), (-5, 4), (0, 4)]},   # rotated
    {"id": "DFm", "floor": "GF", "kind": V1.DRY_FLOOR, "polygon": [(0, 0), (0, 5), (4, 5), (4, 0)]},     # mirrored
    {"id": "DFmm", "floor": "GF", "kind": V1.DRY_FLOOR, "polygon": [(0, 0), (4000, 0), (4000, 5000), (0, 5000)],
     "unit_m": 0.001},
    {"id": "WF", "floor": "GF", "kind": V1.WET_FLOOR, "length": 2.4, "width": 1.8},
    {"id": "SF", "floor": "GF", "kind": V1.STAIR_FLIGHT, "steps": 10, "risers": 11, "riser": 0.17, "tread": 0.30,
     "width": 1.2},
    {"id": "SL", "floor": "GF", "kind": V1.STAIR_LANDING, "area_m2": 1.44},
    {"id": "RF", "floor": "RF", "kind": V1.ROOF, "area_m2": 50.0},
    {"id": "HF", "floor": "GF", "kind": V1.DRY_FLOOR, "area_status": "HELD", "candidate_m2": 12.0},
])
def test_every_other_kind_is_v2_byte_identical(e):
    assert V3.row(dict(e)) == V2.row(dict(e))


def test_dry_floor_keeps_its_bed_hand_values():
    r = V3.row({"id": "DF", "floor": "GF", "kind": V1.DRY_FLOOR, "area_m2": 20.0})
    assert (r["mortar_m3_low"], r["mortar_m3_high"]) == (pytest.approx(0.63), pytest.approx(0.84))
    assert (r["cement_bags_low"], r["cement_bags_high"]) == (pytest.approx(5.04), pytest.approx(6.72))
    assert (r["sand_m3_low"], r["sand_m3_high"]) == (pytest.approx(0.693), pytest.approx(0.924))
    assert r["adhesive_bags"] == pytest.approx(4.0) and "operations" not in r


def test_a_dry_tiled_wall_is_not_given_the_wet_build_up_silently():
    r = V3.row({"id": "DW", "floor": "GF", "kind": "DRY_WALL", "area_m2": 6.0})
    assert r["status"] == "HELD" and r["area_m2"] is None and "UNKNOWN_KIND" in r["reason"]
    assert "operations" not in r and r["adhesive_bags"] is None


# ------------------------------------------------------------------ held / missing never 0
def test_held_wet_wall_stays_blank_in_every_operation():
    r = V3.row(bath(height=None, candidate_height=2.70))
    assert r["status"] == "HELD" and r["area_m2"] is None and r["candidate_m2"] == pytest.approx(7.60 * 2.70)
    for o in r["operations"]:
        assert o["area_m2"] is None
    o = ops(r)
    assert o["LEVELLING_RENDER"]["mortar_reason"].startswith("AREA_HELD")
    assert o["ADHESIVE_AND_PORCELAIN"]["adhesive_bags"] is None
    assert o["ADHESIVE_AND_PORCELAIN"]["adhesive_status"] == "HELD"
    assert r["mortar_status"] == V3.NOT_APPLICABLE


def test_marble_wet_wall_adhesive_held_still_one_fixing_material():
    r = V3.row(bath(finish=V1.MARBLE_STONE))
    assert r["adhesive_bags"] is None and "ADHESIVE_COVERAGE_NOT_GIVEN" in r["adhesive_reason"]
    assert r["fixing_material"] == "ADHESIVE" and r["mortar_m3_low"] is None


# ------------------------------------------------------------------ totals
def test_bed_totals_are_floor_beds_only_and_operations_summed_apart():
    held = bath(id="WW-2", height=None)
    t = V3.table([bath(), {"id": "DF", "floor": "GF", "kind": V1.DRY_FLOOR, "area_m2": 20.0}, held],
                 project=render(0.015))
    p = t["project"]
    assert p["mortar_m3_low"] == pytest.approx(0.63) and p["mortar_m3_high"] == pytest.approx(0.84)
    assert (p["cement_bags_to_buy_low"], p["cement_bags_to_buy_high"]) == (6, 7)
    assert p["area_m2"] == pytest.approx(40.16) and p["adhesive_bags"] == pytest.approx(8.032)
    assert p["not_in_sum"]["area_m2"] == ["WW-2"]
    assert "mortar_m3_low" not in p["not_in_sum"]              # a wet wall's bed is not applicable, not held
    assert p["bed_not_applicable_rows"] == ["WW-1", "WW-2"]
    rend = p["wet_wall_operations"]["LEVELLING_RENDER"]
    assert rend["area_m2"] == pytest.approx(20.16) and rend["mortar_m3"] == pytest.approx(0.3024)
    assert rend["area_not_in_sum"] == ["WW-2"] and rend["mortar_not_in_sum"] == ["WW-2"]
    assert p["wet_wall_operations"]["SPATTER_DASH"]["mortar_m3"] is None
    v2 = V2.table([bath(), {"id": "DF", "floor": "GF", "kind": V1.DRY_FLOOR, "area_m2": 20.0}])["project"]
    assert v2["mortar_m3_low"] == pytest.approx(0.63 + 0.42336)  # what V3 removes from the floor-bed total


def test_only_wet_walls_bed_totals_none_never_0():
    p = V3.table([bath(), bath(id="WW-2")])["project"]
    for k in V3.BED_SUM_KEYS + ("cement_bags_to_buy_low", "cement_bags_to_buy_high"):
        assert p[k] is None
    assert not any(k in p["not_in_sum"] for k in V3.BED_SUM_KEYS)
    assert p["wet_wall_operations"]["LEVELLING_RENDER"]["area_m2"] == pytest.approx(40.32)


def test_duplicate_ids_refused():
    with pytest.raises(ValueError, match="duplicate"):
        V3.table([bath(), bath()])


# ------------------------------------------------------------------ guard: no current quantity moves
def test_v3_is_an_unwired_producer_off_the_candidate_and_released_paths():
    import json

    import t457_reproduce as R
    assert V3.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER" and V3.SUPERSEDES == V2.METHOD_ID
    c = R.candidate_path()
    assert not any(c["tables_in_closure"].values())
    assert c["adhesive_codes"] == [] and c["render_or_spatter_codes"] == []
    assert c["bed_codes"] == ["FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET"]        # floor beds only on the candidate
    assert c["one_plaster_line_per_room_refusal"] and c["one_backing_per_tile_line_refusal"]
    rel = json.loads((ROOT / "research/freeze_integrity/RELEASED_PATH_V2_9_ROUTE_G.json").read_text(encoding="utf-8"))
    assert "engine/source/finish_materials_table_v3.py" not in rel["code"]

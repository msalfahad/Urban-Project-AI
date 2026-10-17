"""R8.10 §12-§20, §31: trade-specific semantic necessity, object materiality per trade, duplicate occurrences."""

from __future__ import annotations

from engine.source import owner_scope as OS, room_topology as RT, topology as T, trade_regions as TR
from tests.r8_8 import helpers as H

FLOOR = TR.TradeTreatmentRule("FLOOR-RULE", 1, "FLOOR_FINISH", "PROJECT_OWNER_RULE", ("P-1", "P-2"),
                              by_name={"BATH": "CERAMIC", "BATHROOM": "CERAMIC", "KITCHEN": "CERAMIC"},
                              otherwise="PORCELAIN")
CEILING = TR.TradeTreatmentRule("CEILING-CLAIM", 1, "CEILING", "OWNER_CLAIM", ("C-1",), otherwise="CEILING_BY_AREA",
                                object_footprints=TR.NOT_DEDUCTED, scope_names=("M.B.ROOM", "DRESS", "HALL", "BATH"))


# ------------------------------------------------------------------------------- §16 the required examples
def test_hall_and_dining_with_the_same_floor_treatment_need_no_split():
    assert TR.zone_decision(["HALL", "DINING"], FLOOR)["state"] == TR.NOT_REQUIRED


def test_master_bedroom_and_dress_with_the_same_ceiling_treatment_need_no_split():
    d = TR.zone_decision(["M.B.ROOM", "DRESS"], CEILING)
    assert d["state"] == TR.NOT_REQUIRED and set(d["treatments"].values()) == {"CEILING_BY_AREA"}


def test_bedroom_and_bathroom_with_different_floor_treatments_require_the_split():
    assert TR.zone_decision(["BEDROOM", "BATHROOM"], FLOOR)["state"] == TR.REQUIRED


def test_kitchen_and_dining_with_different_floor_treatments_are_blocked_until_a_boundary_exists():
    assert TR.zone_decision(["KITCHEN", "DINING"], FLOOR)["state"] == TR.REQUIRED


def test_two_labels_with_unresolved_treatments_are_blocked():
    partial = TR.TradeTreatmentRule("PARTIAL", 1, "FLOOR_FINISH", "PROJECT_OWNER_RULE", ("P-3",),
                                    by_name={"HALL": "PORCELAIN"})
    d = TR.zone_decision(["HALL", "DINING"], partial)
    assert d["state"] == TR.UNRESOLVED and d["treatments"]["DINING"] is None


def test_an_unresolved_text_in_the_site_blocks_whole_site_treatment():
    assert TR.zone_decision(["HALL", "DINING"], FLOOR, unresolved_texts=["?"])["state"] == TR.UNRESOLVED


def test_an_authored_finish_boundary_inside_the_site_forbids_whole_site_treatment():
    assert TR.zone_decision(["HALL", "DINING"], FLOOR, authored_trade_boundary=True)["state"] == TR.REQUIRED


def test_the_mechanism_cannot_merge_every_open_plan_area():
    plans = [["HALL", "DINING"], ["BEDROOM", "BATHROOM"], ["KITCHEN", "DINING"], ["HALL", "BATH"]]
    assert [TR.zone_decision(p, FLOOR)["state"] for p in plans] == [TR.NOT_REQUIRED, TR.REQUIRED, TR.REQUIRED,
                                                                     TR.REQUIRED]


def test_treatment_never_comes_from_a_room_name_without_a_rule():
    empty = TR.TradeTreatmentRule("EMPTY", 1, "FLOOR_FINISH", "NONE", ())
    assert TR.zone_decision(["M.B.ROOM", "DRESS"], empty)["state"] == TR.UNRESOLVED


# ------------------------------------------------------------------------------- §15 scope of the ceiling claim
def test_the_ceiling_rule_does_not_transfer_outside_its_spaces():
    assert TR.zone_decision(["M.B.ROOM", "STAIR"], CEILING)["state"] == TR.UNRESOLVED


def test_the_apartment_ceiling_claim_does_not_transfer_outside_the_selected_apartment():
    c = OS.ScopedClaim("Q14", "CEILING_FOOTPRINT_EQUALS_FLOOR_FOOTPRINT", {}, "P", "REV_NEW", region_id="R1",
                       space_ids=frozenset({"M.B.ROOM", "DRESS"}), items=frozenset({"Q-14|CEILING_BY_AREA"}),
                       authority="PROJECT_OWNER")
    ok = dict(project="P", revision_id="REV_NEW", purpose=OS.SHADOW_DIAGNOSTIC, item="Q-14|CEILING_BY_AREA")
    assert OS.applies(c, region_id="R1", space_id="DRESS", **ok)["state"] == OS.APPLIES
    for bad in ({"region_id": "R2", "space_id": "DRESS"}, {"region_id": "R1", "space_id": "STAIR"}):
        assert OS.applies(c, **bad, **ok)["state"] == OS.OWNER_SCOPE_MISMATCH
    assert OS.applies(c, **dict(ok, revision_id="REV_OLD"), region_id="R1", space_id="DRESS")["state"] == \
        OS.OWNER_SCOPE_MISMATCH


# ------------------------------------------------------------------------------- §18-§19 trade materiality
def test_an_unresolved_object_is_non_material_where_the_trade_ignores_object_footprints():
    entry = {"effect": "CHANGES_AREA", "sources": ["REV_A|H1445||SEGMENT|0"]}
    assert TR.object_materiality(entry, CEILING)["state"] == TR.NON_MATERIAL
    assert TR.object_materiality(entry, FLOOR)["state"] == TR.MATERIAL           # floor: no object authority


def test_an_object_that_could_be_a_partition_is_material_to_every_trade():
    entry = {"effect": "SEPARATES_LABELS", "sources": ["REV_A|H9||SEGMENT|0"]}
    assert TR.object_materiality(entry, CEILING)["state"] == TR.MATERIAL


def test_non_materiality_never_assigns_a_global_role():
    i = H.inp(H.box(1, 0, 0, 500, 400) + [H.seg(60, 0, 100, 150, 100, layer="FIRNTUR"),
                                          H.seg(61, 150, 100, 150, 0, layer="FIRNTUR")],
              texts=[H.text(5, "DRESS", 300, 300)])
    r = RT.run(i, frame_insert=None)
    (s,) = [z for z in r["sites"] if z["labels"]]
    assert T.TOPOLOGY_ROLE_UNRESOLVED in s["issues"]
    m = TR.object_materiality(s["consequence"]["unknown"], CEILING)
    assert m["state"] == TR.NON_MATERIAL
    assert {a.role for k, a in r["roles"]["roles"].items() if "H60" in k or "H61" in k} == {"UNKNOWN_PHYSICAL"}


# ------------------------------------------------------------------------------- §20 duplicate occurrences
def sofa(occ, dx=0.0):
    return [H.part(f"9{k}", "SEGMENT", (100 + dx + 10 * k, 100, 110 + dx + 10 * k, 100), layer="PM", path=(occ,),
                   names={occ: "SF3"}) for k in range(3)]


def test_exact_duplicate_occurrences_are_detected_and_kept():
    i = H.inp(sofa("700047") + sofa("700051") + sofa("700052", dx=500))
    dup = TR.duplicate_occurrences(i)
    assert len(dup) == 1 and dup[0]["occurrences"] == ["700047", "700051"]
    assert dup[0]["state"] == TR.DUPLICATE and dup[0]["count_trades"] == TR.COUNT_RULE_REQUIRED
    assert len(i.parts) == 9                                                      # nothing deleted


def test_duplicate_geometry_cannot_change_an_area_topology():
    base = H.box(1, 0, 0, 500, 400)
    t = [H.text(5, "A", 300, 300)]
    one = RT.run(H.inp(base + sofa("700047"), texts=t), frame_insert=None)
    two = RT.run(H.inp(base + sofa("700047") + sofa("700051"), texts=t), frame_insert=None)
    assert [round(s["area"], 9) for s in one["sites"]] == [round(s["area"], 9) for s in two["sites"]]

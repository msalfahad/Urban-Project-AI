"""Generic tests: engine.source.slab_qto_authority (AD2 + PRE-S7.1 brief §20). Synthetic inputs only."""

import math

import pytest

from engine.source import slab_qto_authority as Q
from engine.source import slab_rebar_readiness as SR

TABLE = {100: "Y10@200", 125: "Y10@200", 150: "Y10@200", 175: "Y12@200", 200: "Y12@200", 250: "Y12@200",
         300: "Y12@200"}


# ------------------------------------------------------------------ rate QTO (Q-COUNT)
def test_five_bars_per_metre_over_3_6_m_is_18_equivalent_bars():
    r = Q.rate_qto(5, 3600)
    assert r["equivalent_bar_count"] == 18.0
    assert r["count_basis"] == Q.COUNT_RATE_DENSITY and r["density_fraction"] == 1.0


def test_rate_qto_adds_no_plus_one():
    r = Q.rate_qto(5, 3600)
    assert r["plus_one"] is False and r["equivalent_bar_count"] != 19.0


def test_rate_qto_is_never_rounded():
    r = Q.rate_qto(6, 3520.1)
    assert r["equivalent_bar_count"] == pytest.approx(21.1206) and r["rounded"] is False
    assert r["equivalent_bar_count"] not in (21.0, 22.0)
    half = Q.rate_qto(5, 1000, fraction=0.5)
    assert half["equivalent_bar_count"] == 2.5


def test_physical_bbs_count_stays_unresolved():
    assert Q.rate_qto(5, 3600)["physical_bbs_bar_count"] == Q.UNRESOLVED
    with pytest.raises(Q.SlabQtoError):
        Q.rate_qto(5, 3600, fraction=1.5)


# ------------------------------------------------------------------ explicit counts (Q-ABSCOUNT)
def test_explicit_count_needs_a_finite_bar_object():
    c = Q.explicit_count("3%%c16/Top", bound_object="SUPPORT_BAR_GRAPHIC")
    assert c["state"] == SR.COUNT_EXPLICIT and c["count"] == 3 and c["count_releases"]
    assert c["count_basis"] == Q.COUNT_SOURCE_EXPLICIT
    loose = Q.explicit_count("5Ø10", bound_object="PANEL")
    assert loose["state"] == Q.COUNT_NOTATION_AMBIGUOUS and loose["count"] is None and not loose["count_releases"]
    rate = Q.explicit_count("5Ø10/m")
    assert rate["state"] == "RATE" and rate["rate_per_m"] == 5


def test_a_released_count_with_an_unknown_length_stays_blocked():
    assert Q.lane(Q.COUNT_SOURCE_EXPLICIT, Q.EXTENT_BLOCKED) == Q.BLOCKED_UNQUANTIFIED
    assert Q.lane(Q.COUNT_SOURCE_EXPLICIT, Q.EXTENT_PROJECT_GEOMETRY) == Q.SOURCE_DERIVED_PHYSICAL
    assert Q.lane(Q.COUNT_RATE_DENSITY, Q.EXTENT_PROJECT_GEOMETRY) == Q.PROJECT_BASIS_QTO
    assert Q.lane(Q.COUNT_SOURCE_EXPLICIT, [Q.EXTENT_PROJECT_GEOMETRY, Q.EXTENT_URBAN_RULE]) == Q.PROJECT_BASIS_QTO
    with pytest.raises(Q.SlabQtoError):
        Q.check_label("VERIFIED_PHYSICAL")
    with pytest.raises(Q.SlabQtoError):
        Q.check_label("AS_BUILT")


# ------------------------------------------------------------------ 50 % (Q-50PCT)
def test_fifty_fifty_qto_split():
    d = Q.curtailment_density(source_states_split=True)
    assert d["state"] == Q.DENSITY_50_50
    assert d["continuous_density_fraction"] + d["curtailed_density_fraction"] == 1.0
    assert d["which_bars_stop"] == Q.UNRESOLVED and d["physical_sequencing"] == Q.UNRESOLVED
    assert Q.curtailment_density(source_states_split=False)["state"] == Q.BLOCKED_UNQUANTIFIED


def test_odd_physical_count_is_bbs_ambiguous():
    d = Q.curtailment_density(source_states_split=True, physical_count=7)
    assert d["bbs"] == Q.BBS_AMBIGUOUS_ODD_COUNT and d["extra_bar_assigned_to"] is None
    assert d["continuous_density_fraction"] == 0.5          # the QTO basis is unaffected


# ------------------------------------------------------------------ rule identity (Q-TOPEXT, Q-TOPOVR)
GENERIC = {"rule_id": "DETAIL", "layer": "TOP", "location": "OVER_SUPPORT", "role": "TOP_OVER_SUPPORT",
           "support": "BEAM", "dia_mm": None, "rate": None, "size_deferred_to": Q.FLOOR_PLAN_NOTE,
           "scope": Q.GENERIC_TYPICAL_DETAIL}
NOTE = {"rule_id": "NOTE", "layer": "TOP", "location": "OVER_SUPPORT", "role": "TOP_OVER_SUPPORT", "support": "BEAM",
        "dia_mm": 10, "rate": 5, "scope": Q.FLOOR_PLAN_NOTE}


def test_same_role_local_rule_overrides_generic():
    ident = Q.bar_role_identity(GENERIC, NOTE)
    assert ident["identity"] == Q.SAME_FAMILY and not ident["contradictions"]
    p = Q.same_role_precedence([{"rule_id": "DETAIL", "scope": Q.GENERIC_TYPICAL_DETAIL},
                                {"rule_id": "NOTE", "scope": Q.FLOOR_PLAN_NOTE}])
    assert p["governing"] == "NOTE" and p["overridden"] == ["DETAIL"] and p["summed"] is False
    assert p["overridden_state"] == Q.OVERRIDDEN_PROJECT_SOURCE
    ov = Q.local_override(same_role=True, same_location=True)
    assert ov["local"] == Q.LOCAL_SOURCE_OVERRIDE and ov["general"] == Q.GENERAL_RULE_SUPERSEDED_FOR_ROLE
    assert ov["additive"] is False


def test_different_role_rules_coexist():
    bottom = dict(NOTE, rule_id="BOT", layer="BOTTOM", location="IN_SPAN", role="BOTTOM")
    assert Q.bar_role_identity(GENERIC, bottom)["identity"] == Q.DIFFERENT_FAMILIES
    assert Q.local_override(same_role=False, same_location=True)["additive"] is True
    assert Q.local_override(same_role=True, same_location=True, second_family_evidence=True)["local"] == \
        Q.ADDITIVE_SECOND_FAMILY
    vague = dict(NOTE, support=None)
    assert Q.bar_role_identity(GENERIC, vague)["identity"] == Q.IDENTITY_UNRESOLVED
    tie = Q.same_role_precedence([{"rule_id": "A", "scope": Q.FLOOR_PLAN_NOTE},
                                  {"rule_id": "B", "scope": Q.FLOOR_PLAN_NOTE}])
    assert tie["state"] == SR.SOURCE_CONFLICT and tie["governing"] is None


def test_urban_top_extent_is_an_owner_rule_not_source_explicit():
    e = Q.top_extent(3000)
    assert e["extent_mm"] == pytest.approx(1000.0) and e["origin"] == SR.FACE_OF_SUPPORT
    assert e["authority"] == Q.URBAN_OWNER_MEASUREMENT_RULE and e["rule_id"] == Q.URBAN_TOP_EXTENT_RULE
    assert e["authority"] != Q.PROJECT_SOURCE_EXPLICIT
    assert Q.top_extent(3000, origin_explicit="FACE")["authority"] == Q.PROJECT_SOURCE_EXPLICIT


# ------------------------------------------------------------------ mismatch (Q-MISMATCH)
def test_mismatch_splits_left_and_right():
    m = Q.mismatch_split("S1", {"family": "A:X", "dia_mm": 10, "rate": 5}, {"family": "B:X", "dia_mm": 12, "rate": 5})
    assert m["state"] == "SPLIT_AT_SUPPORT" and m["chosen_by"] is None
    assert [r["run"] for r in m["runs"]] == ["S1:LEFT_PANEL_BAR_RUN", "S1:RIGHT_PANEL_BAR_RUN"]
    assert all(r["to"] == "SUPPORT_FACE" for r in m["runs"])
    same = Q.mismatch_split("S2", {"family": "A:X", "dia_mm": 10, "rate": 5}, {"family": "B:X", "dia_mm": 10, "rate": 5})
    assert same["state"] == "ONE_RUN_ACROSS_SUPPORT" and not same["blocked"]


def test_no_invented_lap():
    m = Q.mismatch_split("S1", {"family": "A:X", "dia_mm": 10, "rate": 5}, None)
    parts = {b["part"]: b["state"] for b in m["blocked"]}
    assert set(parts) == set(Q.TRANSITION_PARTS) and set(parts.values()) == {Q.BLOCKED_UNQUANTIFIED}
    items = Q.bottom_strip_items(3000, 3000, 1000, Q.END_CONTINUOUS_SPLIT, Q.END_NON_CONTINUOUS)
    tr = [i for i in items if i["item"] == "TRANSITION"]
    assert tr and all(i["lane_hint"] == "BLOCK" and i["integral"] is None for i in tr)


# ------------------------------------------------------------------ ownership transfer
def test_water_tank_ownership_transfer():
    t = Q.ownership_transfer("PANEL-T", kind="PANEL", to_stage="S8_SPECIAL_STRUCTURE",
                             region="WATER_TANK_SUPPORT_REGION", reason="designated water-tank place")
    assert t["state"] == Q.TRANSFERRED_S8 and t["quantity_lost"] is False and t["from_stage"] == "S7"
    cons = Q.transfer_conservation(["C1", "C2"], {"C1": Q.TRANSFERRED_S8, "C2": "RELEASED_ALL"})
    assert cons["every_object_once"] and cons["no_unknown"]
    assert not Q.transfer_conservation(["C1", "C2"], {"C1": Q.TRANSFERRED_S8})["every_object_once"]


def test_stair_lightwell_transfer_preserves_the_conflict():
    t = Q.ownership_transfer("PANEL-V", kind="PANEL", to_stage="S8_SPECIAL_STRUCTURE",
                             region="STAIR_LIGHTWELL_REGION", reason="void + stair + slab marks",
                             conflict_preserved=True)
    assert t["source_conflict_preserved"] is True and t["quantity_lost"] is False
    with pytest.raises(Q.SlabQtoError):
        Q.ownership_transfer("X", kind="PANEL", to_stage="", region="R", reason="r")


# ------------------------------------------------------------------ sunken slabs
def test_sunken_slab_mesh_retained():
    d = Q.sunken_decision(boundary=True, callout=True, thickness=True, supports=True)
    assert d["mesh"] == "RETAINED_IN_S7"
    assert Q.sunken_decision(boundary=True, callout=False, thickness=True, supports=True)["mesh"] == \
        Q.BLOCKED_UNQUANTIFIED


def test_sunken_edge_extras_blocked():
    d = Q.sunken_decision(boundary=True, callout=True, thickness=True, supports=True)
    assert set(d["extras"]) == set(Q.SUNKEN_EXTRAS) and set(d["extras"].values()) == {Q.BLOCKED_UNQUANTIFIED}
    s = Q.sunken_decision(boundary=True, callout=True, thickness=True, supports=True,
                          specified_extras=("LEVEL_CHANGE_DETAIL",))
    assert s["extras"]["LEVEL_CHANGE_DETAIL"] == "SPECIFIED" and s["extras"]["SUNKEN_EDGE_EXTRA"] == \
        Q.BLOCKED_UNQUANTIFIED


# ------------------------------------------------------------------ dense hatch
def test_cantilever_versus_bearing_wall_geometry():
    lines = [((0, 0), (5000, 0)), ((0, 200), (5000, 200))]                  # a 200 band, full length
    wall = Q.hatch_classification((0, 0, 3000, 200), structural_lines=lines)
    assert wall["state"] == Q.BEARING_WALL_CANDIDATE
    edge = [((0, 0), (5000, 0))]                                             # one outer support line only
    cant = Q.hatch_classification((0, 0, 3000, 600), structural_lines=edge,
                                  slab_faces_beyond=lambda side: False)
    assert cant["state"] == Q.CANTILEVER_CANDIDATE
    amb = Q.hatch_classification((0, 0, 3000, 600), structural_lines=edge, slab_faces_beyond=lambda side: True)
    assert amb["state"] == SR.CLASSIFICATION_BLOCKED
    none = Q.hatch_classification((0, 0, 3000, 600), structural_lines=[])
    assert none["state"] == SR.CLASSIFICATION_BLOCKED


# ------------------------------------------------------------------ local bar strips
def test_trapezoid_panel_local_bar_runs():
    trap = [(0, 0), (4000, 0), (3000, 3000), (0, 3000)]
    st = Q.bar_strips(trap, direction="X")
    assert len(st) == 1 and st[0]["L0"] == pytest.approx(4000) and st[0]["L1"] == pytest.approx(3000)
    assert st[0]["start_edge"] == (0, 3) and st[0]["end_edge"] == (0, 1)
    assert Q.strips_integral(st) == pytest.approx(Q.polygon_area(trap)) == pytest.approx(10.5e6)
    y = Q.bar_strips(trap, direction="Y")
    assert Q.strips_integral(y) == pytest.approx(10.5e6)
    assert Q.strips_reconcile(trap, direction="Y")["reconciled"]


def test_l_shaped_panel_local_bar_runs():
    ell = [(0, 0), (4000, 0), (4000, 2000), (2000, 2000), (2000, 4000), (0, 4000)]
    st = Q.bar_strips(ell, direction="X")
    runs = sorted((s["t0"], s["t1"], round(s["L0"]), s["end_edge"]) for s in st)
    assert runs == [(0, 2000, 4000, (0, 1)), (2000, 4000, 2000, (0, 3))]
    assert Q.strips_integral(st) == pytest.approx(12e6) == pytest.approx(Q.polygon_area(ell))
    assert Q.strips_reconcile(ell, direction="Y")["reconciled"]


def test_opening_clipped_local_bar_run():
    sq = [(0, 0), (4000, 0), (4000, 4000), (0, 4000)]
    hole = [(1000, 1000), (2000, 1000), (2000, 2000), (1000, 2000)]
    st = Q.bar_strips(sq, [hole], direction="X")
    mid = sorted((round(s["L0"]), s["start_edge"][0], s["end_edge"][0]) for s in st if s["t0"] == 1000)
    assert mid == [(1000, 0, 1), (2000, 1, 0)]                           # cut at the opening (ring 1)
    assert Q.strips_integral(st) == pytest.approx(16e6 - 1e6)
    items = Q.bottom_strip_items(1000, 1000, 1000, Q.END_NON_CONTINUOUS, Q.END_OPENING)
    assert [i["item"] for i in items if i["lane_hint"] == "RELEASE"] == ["IN_PANEL"]
    assert "END_DETAIL_AT_OPENING" in [i["item"] for i in items if i["lane_hint"] == "BLOCK"]


def test_crossing_integral_counts_the_shared_width_once():
    a = [((1000, 0), (1000, 3000))]                     # face of panel A
    b = [((1200, 1000), (1200, 4000))]                  # face of panel B, 200 beyond, offset 1000
    c = Q.crossing_integral(a, b, "X")
    assert c["width"] == pytest.approx(2000) and c["integral"] == pytest.approx(400000)
    assert c["gap_min"] == pytest.approx(200) == c["gap_max"]


def test_neighbour_beyond_a_face_is_found_by_geometry():
    a = [(0, 0), (3000, 0), (3000, 3000), (0, 3000)]
    b = [(3200, 0), (6000, 0), (6000, 1500), (3200, 1500)]           # across a 200 beam, lower half only
    c = [(3200, 1700), (6000, 1700), (6000, 3000), (3200, 3000)]     # upper part, past a 200 cross beam
    faces = {"B": (b, ()), "C": (c, ())}
    st = Q.bar_strips(a, direction="X", extra_breaks=[1500, 1700])
    assert [(s["t0"], s["t1"]) for s in st] == [(0, 1500), (1500, 1700), (1700, 3000)]
    hits = [Q.face_beyond(s["s_end"][0] * 0.5 + s["s_end"][1] * 0.5, 0.5 * (s["t0"] + s["t1"]), +1, faces, "X", 320)
            for s in st]
    assert [h["face"] if h else None for h in hits] == ["B", None, "C"]
    assert hits[0]["gap"] == pytest.approx(200)
    assert Q.face_beyond(0, 1000, -1, faces, "X", 320) is None       # nothing beyond the west face


# ------------------------------------------------------------------ continuity
def test_outside_edge_is_non_continuous():
    for side in Q.OTHER_SIDE_ABSENT:
        assert Q.edge_continuity(other_side=side)["state"] == SR.NON_CONTINUOUS
    assert Q.edge_continuity(other_side="NO_SLAB", support_kind="COLUMN")["state"] == SR.NON_CONTINUOUS


def test_excluded_but_physical_slab_is_not_an_outside_edge():
    for side in ("SLAB_EXCLUDED_SPECIAL", "SLAB_CLASSIFICATION_BLOCKED", "SLAB_TRANSFERRED", "CANTILEVER_CANDIDATE"):
        assert Q.edge_continuity(other_side=side)["state"] == SR.CONTINUITY_UNRESOLVED
    assert Q.edge_continuity(other_side="SLAB_IN_SCOPE", level_step=True)["state"] == SR.CONTINUITY_UNRESOLVED
    assert Q.edge_continuity(other_side="SLAB_IN_SCOPE")["state"] == SR.CONTINUOUS
    with pytest.raises(Q.SlabQtoError):
        Q.edge_continuity(other_side="SOMETHING")


# ------------------------------------------------------------------ cover, temperature, independence
def test_minimum_25_mm_cover_is_project_basis_only():
    c = Q.cover_lane({"basis": "MINIMUM_PROJECT_COVER", "value_mm": 25})
    assert c["lane"] == Q.PROJECT_BASIS_QTO and c["extent_basis"] == Q.EXTENT_MINIMUM_COVER
    assert "SOURCE_EXACT" in c["never"] and "AS_BUILT" in c["never"]
    assert Q.lane(Q.COUNT_SOURCE_EXPLICIT, [Q.EXTENT_PROJECT_GEOMETRY, Q.EXTENT_MINIMUM_COVER]) == Q.PROJECT_BASIS_QTO


def test_160_mm_temperature_stays_blocked():
    t = Q.temperature_item(160, TABLE)
    assert t["lane"] == Q.BLOCKED_UNQUANTIFIED and t["table_state"] == SR.TABLE_NO_EXACT_ROW
    assert t["value"] is None and t["interpolated"] is False
    assert Q.temperature_item(150, TABLE)["value"] == "Y10@200"


def test_component_blocking_does_not_block_unrelated_steel():
    temp = [{"lane": Q.BLOCKED_UNQUANTIFIED}]
    bottom = [{"lane": Q.PROJECT_BASIS_QTO}, {"lane": Q.PROJECT_BASIS_QTO}]
    assert Q.component_state(temp) == "BLOCKED" and Q.component_state(bottom) == "RELEASED_ALL"
    assert Q.component_state(bottom + [{"lane": Q.BLOCKED_UNQUANTIFIED}]) == "RELEASED_PARTIAL"
    assert Q.component_state([{"lane": Q.TRANSFERRED_S8}]) == Q.TRANSFERRED_S8


# ------------------------------------------------------------------ strip decomposition
def test_bottom_strip_items_respect_the_density_budget():
    for ends in [(Q.END_NON_CONTINUOUS, Q.END_NON_CONTINUOUS), (Q.END_CONTINUOUS_RUN, Q.END_NON_CONTINUOUS),
                 (Q.END_CONTINUOUS_RUN, Q.END_CONTINUOUS_RUN), (Q.END_UNRESOLVED, Q.END_CONTINUOUS_SPLIT),
                 (Q.END_OBLIQUE, Q.END_NO_SUPPORT)]:
        items = Q.bottom_strip_items(4000, 4000, 1000, *ends)
        assert Q.item_density_check(items), ends
    two = Q.bottom_strip_items(4000, 4000, 1000, Q.END_CONTINUOUS_RUN, Q.END_CONTINUOUS_RUN)
    curt = [i for i in two if i["item"] == "IN_PANEL_CURTAILED"][0]
    assert curt["run_factor"] == pytest.approx(0.75) and curt["integral"] == pytest.approx(0.75 * 4000 * 1000)
    unres = Q.bottom_strip_items(4000, 4000, 1000, Q.END_UNRESOLVED, Q.END_NON_CONTINUOUS)
    zone = [i for i in unres if i["item"] == "STOP_ZONE_UNRESOLVED"]
    assert len(zone) == 1 and zone[0]["lane_hint"] == "BLOCK" and zone[0]["integral"] is None
    assert math.isclose([i for i in unres if i["item"] == "IN_PANEL_CURTAILED"][0]["run_factor"], 0.875)

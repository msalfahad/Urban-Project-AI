"""T-010: wet / dry / held from the room label first, the sanitary drawing second (engine.source.wet_room_evidence).

Hand truth from the owner's answers, not from engine output:
- Q-13 = B with the label as primary evidence: a toilet-like object in a room labelled as a dry room does not make it
  wet; loose lines count as a toilet only on a plumbing / sanitary layer or with a drain or soil-pipe mark; no label
  and ambiguous evidence -> HELD with no wet and no dry quantity; a labelled bathroom missing fixtures in a drawing ->
  COORDINATION_CHECK, class kept.
- Q-06 = (a): a basin-only hand-wash space is wet (porcelain floor, full-height wall porcelain, waterproofing).
Quantities: the hand values in plan_fixtures.py (5.72 / 1.92 / 0.12 / 7.76 / 26.56 m2). Synthetic room, not a client
drawing; every geometric case runs untransformed, rotated 37 degrees, mirrored, in metres, and all three together.
"""

from __future__ import annotations

import pytest

from engine.source import wet_room_evidence as W

from . import plan_fixtures as F

TRANSFORMS = ["none", "rot37", "mirror", "metres", "rot37_mirror_metres"]


def _ev(tmp_path, transform, label=None, items=()):
    p = tmp_path / "room.dxf"
    poly = F.room_dxf(p, label=label, items=items, transform=transform)
    ents = F.read_plan(p)
    return W.plan_evidence(poly, ents, F.ROLES, ents["unit_m"]), poly


# ------------------------------------------------------------------------------------- L-P8-01 and Q-13 (plan)
@pytest.mark.parametrize("transform", TRANSFORMS)
@pytest.mark.parametrize("label", ["LOBBY", "موزع"])
def test_wc_sized_chair_in_a_labelled_lobby_is_dry(tmp_path, transform, label):
    """the L-P8-01 chair (seat 0.40 x 0.55 on a 0.45 x 0.15 back at the wall) with a basin, in a room labelled lobby:
    DRY by the label; the look-alike and the basin are a coordination check, never wet scope."""
    ev, _ = _ev(tmp_path, transform, label, ["WC_SIZED_CHAIR", "BASIN"])
    assert ev["wc_linework"] and not ev["wc_linework"][0]["on_sanitary_layer"]      # the profile does accept it
    r = W.assess(ev, None, polygon_m=[(0, 0), (1, 0), (1, 1)])
    assert r["class"] == W.DRY and r["reason"] == "LABEL_DRY"
    assert r["quantities"] is None
    assert any("WC_LINEWORK" in c and "BASIN" in c for c in r["coordination_checks"])


@pytest.mark.parametrize("transform", TRANSFORMS)
def test_wc_sized_chair_unlabelled_is_held_not_wet(tmp_path, transform):
    """the case the strict xfail of tests/m9_p2b8 documents: with no label and no basin, the chair stays HELD."""
    ev, _ = _ev(tmp_path, transform, None, ["WC_SIZED_CHAIR"])
    r = W.classify(ev)
    assert r["class"] == W.HELD and r["reason"] == "WET_DRY_NOT_ESTABLISHED"


@pytest.mark.parametrize("transform", TRANSFORMS)
def test_exploded_wc_on_furniture_layer_unlabelled_is_held(tmp_path, transform):
    ev, poly = _ev(tmp_path, transform, None, ["EXPLODED_WC_FURN"])
    r = W.assess(ev, None, polygon_m=F.to_m(poly, transform))
    assert r["class"] == W.HELD and r["reason"] == "WET_DRY_NOT_ESTABLISHED"
    assert r["quantities"] is None                       # no ceramic, no membrane from an uncertain shape
    assert F.FURN in r["basis"]


@pytest.mark.parametrize("transform", TRANSFORMS)
def test_exploded_wc_on_sanitary_layer_is_wet(tmp_path, transform):
    ev, _ = _ev(tmp_path, transform, None, ["EXPLODED_WC_SAN"])
    r = W.classify(ev)
    assert r["class"] == W.WET and r["reason"] == "FIXTURES_TOILET"
    assert ev["wc_linework"][0]["on_sanitary_layer"]


@pytest.mark.parametrize("transform", TRANSFORMS)
@pytest.mark.parametrize("drain", ["DRAIN_BLOCK", "DRAIN_TEXT"])
def test_exploded_wc_on_furniture_layer_with_a_drain_mark_is_wet(tmp_path, transform, drain):
    ev, _ = _ev(tmp_path, transform, None, ["EXPLODED_WC_FURN", drain])
    r = W.classify(ev)
    assert r["class"] == W.WET and "PLAN_WC_LINEWORK_WITH_DRAIN_MARK" in r["basis"]


def test_exploded_wc_on_furniture_layer_with_a_drain_on_the_sanitary_drawing_is_wet(tmp_path):
    ev, _ = _ev(tmp_path, "rot37", None, ["EXPLODED_WC_FURN"])
    r = W.classify(ev, [{"kind": "FLOOR_DRAIN", "ref": "drainage plan"}])
    assert r["class"] == W.WET and "PLAN_WC_LINEWORK_WITH_DRAIN_MARK" in r["basis"]


@pytest.mark.parametrize("transform", ["none", "rot37_mirror_metres"])
def test_named_wc_block_unlabelled_is_wet(tmp_path, transform):
    ev, _ = _ev(tmp_path, transform, None, ["WC_BLOCK"])
    assert ev["wc_linework"] == []                       # the block's own pan is the block, not a second WC
    assert W.classify(ev)["class"] == W.WET


# ------------------------------------------------------------------------------------- sanitary drawing
@pytest.mark.parametrize("label", ["BATH", "حمام", "W.C."])
def test_labelled_bathroom_with_fixtures_only_on_the_sanitary_drawing_is_wet(tmp_path, label):
    ev, _ = _ev(tmp_path, "mirror", label, [])
    assert ev["fixtures"] == []
    r = W.classify(ev, [{"kind": "WC"}, {"kind": "BASIN"}, {"kind": "FLOOR_DRAIN"}])
    assert r["class"] == W.WET and r["reason"] == "LABEL_WET"
    assert r["coordination_checks"] == []


def test_labelled_bathroom_with_no_fixture_anywhere_keeps_its_class_with_a_coordination_check(tmp_path):
    ev, _ = _ev(tmp_path, "rot37", "BATH", [])
    r = W.classify(ev, [])
    assert r["class"] == W.WET
    assert len(r["coordination_checks"]) == 1 and "neither the plan nor the sanitary" in r["coordination_checks"][0]
    r = W.classify(ev, None)                             # the sanitary drawing was not read
    assert r["class"] == W.WET and "no sanitary drawing was read" in r["coordination_checks"][0]


def test_labelled_bathroom_with_plan_fixtures_but_nothing_on_the_sanitary_drawing(tmp_path):
    ev, _ = _ev(tmp_path, "none", "BATH", ["WC_BLOCK"])
    r = W.classify(ev, [])
    assert r["class"] == W.WET and "sanitary drawing shows no" in r["coordination_checks"][0]
    assert W.classify(ev, None)["coordination_checks"] == []


def test_dry_label_with_a_wc_on_the_sanitary_drawing_stays_dry(tmp_path):
    ev, _ = _ev(tmp_path, "metres", "BEDROOM", [])
    r = W.classify(ev, [{"kind": "WC"}])
    assert r["class"] == W.DRY and "SANITARY_DRAWING_WC" in r["coordination_checks"][0]


def test_unlabelled_space_typed_by_the_sanitary_drawing(tmp_path):
    ev, _ = _ev(tmp_path, "none", None, [])
    assert W.classify(ev, [{"kind": "SHOWER"}])["class"] == W.WET
    assert W.classify(ev, [{"kind": "BASIN"}])["reason"] == "BASIN_ONLY_HAND_WASH"
    r = W.classify(ev, [{"kind": "FLOOR_DRAIN"}])          # a drain alone: balcony, plant room, laundry ... held
    assert r["class"] == W.HELD and r["reason"] == "WET_DRY_NOT_ESTABLISHED"
    assert W.classify(ev, [])["reason"] == "NO_LABEL_NO_EVIDENCE"
    with pytest.raises(ValueError):
        W.classify(ev, [{"kind": "SINK_OR_SOMETHING"}])


# ------------------------------------------------------------------------------------- Q-06 hand-wash spaces
@pytest.mark.parametrize("transform", TRANSFORMS)
@pytest.mark.parametrize("label", [None, "مغسلة", "HAND WASH", "المغاسل"])
def test_basin_only_hand_wash_space_is_wet_with_hand_quantities(tmp_path, transform, label):
    ev, poly = _ev(tmp_path, transform, label, ["BASIN_ON_SANITARY"])
    assert ev["sanitary_layer_segments"] == 0             # the basin's own linework is the basin, not more evidence
    r = W.assess(ev, [{"kind": "BASIN"}, {"kind": "FLOOR_DRAIN"}], polygon_m=F.to_m(poly, transform),
                 doors=[{"id": "D1", "width_m": 0.80, "wall_t_m": 0.15, "height_m": 2.20}],
                 windows=[{"id": "W1", "width_m": 0.60, "height_m": 0.80}],
                 clear_height={"value_m": 3.00, "source": "synthetic section"})
    assert r["class"] == W.WET and "Q-06" in r["rules"]
    assert r["reason"] == ("LABEL_WET" if label else "BASIN_ONLY_HAND_WASH")
    q = {x["item"]: x for x in r["quantities"]["items"]}
    assert q["FIN.FLOOR.WET_TILE"]["m2"] == pytest.approx(5.72, abs=1e-6)
    assert q["FIN.WP.FLOOR"]["m2"] == pytest.approx(5.72, abs=1e-6)
    assert q["FIN.WP.UPTURN"]["m2"] == pytest.approx(1.92, abs=1e-6)
    assert q["FIN.WP.DOORWAY"]["m2"] == pytest.approx(0.12, abs=1e-6)
    assert r["quantities"]["membrane"]["m2"] == pytest.approx(7.76, abs=1e-6)
    assert q["FIN.WALL.TILE"]["m2"] == pytest.approx(26.56, abs=1e-6)


def test_hand_wash_label_without_a_basin_is_wet_with_a_coordination_check(tmp_path):
    ev, _ = _ev(tmp_path, "none", "مغسلة", [])
    r = W.classify(ev, [])
    assert r["class"] == W.WET and "a basin" in r["coordination_checks"][0]


def test_basin_with_a_cooker_unlabelled_is_held(tmp_path):
    ev, _ = _ev(tmp_path, "none", None, ["BASIN", "COOKER"])
    r = W.classify(ev)
    assert r["class"] == W.HELD and "KITCHEN_APPLIANCE" in r["basis"]


# ------------------------------------------------------------------------------------- labels
@pytest.mark.parametrize("label, cls, reason", [
    ("حمام سباحة", W.NONE, "NO_ROOM_FINISH"),            # swimming pool: the first word is not the room (ROOM_VOCAB_V2)
    ("SWIMMING POOL", W.NONE, "NO_ROOM_FINISH"),
    ("مغسلة سيارات", W.HELD, "NO_LABEL_NO_EVIDENCE"),     # car wash: a held compound, never a hand-wash space
    ("KITCHEN", W.WET, "LABEL_WET"),
    ("مطبخ", W.WET, "LABEL_WET"),
    ("LAUNDRY", W.WET, "LABEL_WET"),
    ("حمام ماستر", W.WET, "LABEL_WET"),                  # master bathroom, not the bedroom
    ("STORE", W.DRY, "LABEL_DRY"),
])
def test_label_vocabulary(tmp_path, label, cls, reason):
    ev, _ = _ev(tmp_path, "none", label, [])
    r = W.classify(ev, [])
    assert (r["class"], r["reason"]) == (cls, reason)
    if label == "LAUNDRY":
        assert any(f.startswith("WET_SCOPE_PROJECT_CONFIRMATION") for f in r["flags"])


def test_wet_and_dry_labels_in_one_space_are_held():
    ev = {"labels": W.label_reading(["BATH", "DRESSING"])}
    r = W.classify(ev)
    assert r["class"] == W.HELD and r["reason"] == "WET_ZONE_EXTENT_NOT_DRAWN"


def test_room_tag_block_names_label_only_without_a_text():
    assert W.label_reading([], ["kit"])["codes"] == ["KITCHEN"]
    assert W.label_reading(["STORE"], ["kit"])["codes"] == ["STORE"]


# ------------------------------------------------------------------------------------- quantities: missing never 0
def test_missing_inputs_hold_their_item_never_zero():
    sq = [(0, 0), (2.6, 0), (2.6, 2.2), (0, 2.2)]
    q = W.wet_scope_quantities(sq, doors=[{"id": "D1", "width_m": 0.8, "wall_t_m": None, "height_m": None}])
    it = {x["item"]: x for x in q["items"]}
    assert it["FIN.WP.DOORWAY"]["state"] == W.HELD and it["FIN.WP.DOORWAY"]["m2"] is None
    assert it["FIN.WALL.TILE"]["state"] == W.HELD and it["FIN.WALL.TILE"]["m2"] is None
    assert q["membrane"]["state"] == W.HELD and q["membrane"]["m2"] is None
    q = W.wet_scope_quantities(sq, doors=[{"id": "D1", "width_m": 0.8, "wall_t_m": 0.15, "height_m": None}],
                               clear_height={"value_m": 3.0, "source": "x"})
    it = {x["item"]: x for x in q["items"]}
    assert it["FIN.WALL.TILE"]["state"] == W.HELD and it["FIN.WALL.TILE"]["gross_m2"] == pytest.approx(28.8)
    assert q["membrane"]["m2"] == pytest.approx(7.76)


def test_hole_in_the_floor_is_deducted():
    sq = [(0, 0), (2.6, 0), (2.6, 2.2), (0, 2.2)]
    duct = [(1.0, 0.8), (1.6, 0.8), (1.6, 1.4), (1.0, 1.4)]          # a 0.60 x 0.60 duct: 0.36 m2, 2.40 m edge
    q = W.wet_scope_quantities(sq, [duct])
    it = {x["item"]: x for x in q["items"]}
    assert it["FIN.WP.FLOOR"]["m2"] == pytest.approx(5.72 - 0.36)
    assert it["FIN.WP.UPTURN"]["m2"] == pytest.approx((9.60 + 2.40) * 0.20)


def test_held_space_carries_no_quantity():
    r = W.assess({"labels": W.label_reading([])}, [], polygon_m=[(0, 0), (2.6, 0), (2.6, 2.2), (0, 2.2)])
    assert r["class"] == W.HELD and r["quantities"] is None


def test_method_is_not_wired():
    assert W.policy_record()["wired"] is False

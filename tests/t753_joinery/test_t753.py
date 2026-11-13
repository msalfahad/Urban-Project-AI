"""T-753: B13-06 joinery census, research/agents_t753/t753_joinery.py (not wired).

Hand-made synthetic villa N753 (not the development villa), plan in metres, one floor 'GF':
  K1 kitchen  x 0.0 .. 3.0, y 0.0 .. 2.7 (wall faces). L-shaped base run 0.60 deep along the W wall (x = 0) and the
              N wall (y = 2.7): front W leg x = 0.6, y 0.0 .. 2.1; front N leg y = 2.1, x 0.6 .. 3.0; no end returns
              (it ends on the S wall y = 0 and on the E wall x = 3.0).
  HAND TRUTH: front lm = 2.1 + 2.4 = 4.500; plan m2 = W strip 0.6 x 2.7 = 1.62 + N strip 2.4 x 0.6 = 1.44 -> 3.060
              (the 0.6 x 0.6 corner square ONCE: two full leg rectangles would give 0.6 x 2.7 + 0.6 x 3.0 = 3.42,
              i.e. +0.36 = one corner square too many); depth 0.600; one inside corner.
  B1 bedroom  x 4.0 .. 8.0, y 0.0 .. 4.0. Wardrobe on the E wall (x = 8.0): front x = 7.4, y 1.0 .. 3.2 (2.200 lm),
              diagonal from (7.4, 1.0) to (8.0, 3.2) (the cupboard symbol), depth 0.600, plan 1.320 m2. No elevation
              prints its height: front face m2 HELD (None), never a default height.
  A 'WARDROBE' block that holds only TEXT is a label, never a unit. A closed lift box with a diagonal (1.6 x 1.5) is no
  cupboard (depth outside 0.30 .. 0.90). A fixture-layer line with a wall-layer twin 0.20 m away is a wall face.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t753"))
import t753_joinery as J  # noqa: E402


def kitchen(tf=lambda p: p):
    P = lambda x, y: tf((x, y))  # noqa: E731
    ring = [P(0.6, 0.0), P(0.6, 2.1), P(3.0, 2.1), P(3.0, 2.7), P(0.0, 2.7), P(0.0, 0.0)]
    front = [J.Seg("W", P(0.6, 0.0), P(0.6, 2.1), "5"), J.Seg("N", P(0.6, 2.1), P(3.0, 2.1), "5")]
    return J.Unit("K1-RUN", J.BASE_RUN, "GF", "K1", ring, front)


def wardrobe(height=None, tf=lambda p: p):
    P = lambda x, y: tf((x, y))  # noqa: E731
    ring = [P(7.4, 1.0), P(7.4, 3.2), P(8.0, 3.2), P(8.0, 1.0)]
    return J.Unit("B1-WR", J.CUPBOARD, "GF", "B1", ring, [J.Seg("F", P(7.4, 1.0), P(7.4, 3.2), "5")],
                  evidence=["diag D"], height_m=height, height_source="elevation E1" if height else "")


def rot_mirror(deg, mirror):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def tf(p):
        x, y = (-p[0] if mirror else p[0]), p[1]
        return (c * x - s * y + 120.0, s * x + c * y - 45.0)
    return tf


# ------------------------------------------------------------------------------------------------ normal cases
def test_l_shaped_kitchen_front_lm_and_corner_once():
    q = J.measure(kitchen())
    assert q["front_lm"]["value"] == pytest.approx(4.5, abs=1e-9)
    assert q["plan_m2"]["value"] == pytest.approx(3.06, abs=1e-9)
    assert q["plan_m2"]["value"] < 0.6 * 2.7 + 0.6 * 3.0 - 0.3          # the corner square is not counted twice
    assert q["inside_corners"] == 1
    assert q["depth_m"]["min"] == pytest.approx(0.6, abs=1e-9) and q["depth_m"]["max"] == pytest.approx(0.6, abs=1e-9)
    assert q["front_lm"]["status"] == J.DRAWING_CONFIRMED
    assert q["worktop_m2"]["material"]["value"] is None and q["worktop_m2"]["material"]["status"] == J.HELD
    assert q["cabinet_height_m"]["value"] is None and q["cabinet_height_m"]["status"] == J.HELD


@pytest.mark.parametrize("deg,mirror", [(0, False), (37, False), (90, True), (213.5, True)])
def test_rotation_mirror_translation_do_not_change_quantities(deg, mirror):
    tf = rot_mirror(deg, mirror)
    q = J.measure(kitchen(tf))
    assert q["front_lm"]["value"] == pytest.approx(4.5, abs=1e-6)
    assert q["plan_m2"]["value"] == pytest.approx(3.06, abs=1e-6)
    w = J.measure(wardrobe(tf=tf))
    assert w["front_lm"]["value"] == pytest.approx(2.2, abs=1e-6)
    assert w["plan_m2"]["value"] == pytest.approx(1.32, abs=1e-6)


def test_drawing_in_millimetres_scaled_once_gives_the_same_quantities():
    mm = kitchen(lambda p: (p[0] * 1000.0, p[1] * 1000.0))
    back = J.Unit(mm.unit_id, mm.kind, mm.floor, mm.room_id, [(x / 1000.0, y / 1000.0) for x, y in mm.ring],
                  [J.Seg(s.ref, (s.a[0] / 1000, s.a[1] / 1000), (s.b[0] / 1000, s.b[1] / 1000)) for s in mm.front])
    assert J.measure(back)["plan_m2"]["value"] == pytest.approx(3.06, abs=1e-9)
    with pytest.raises(ValueError):                                     # unscaled mm: a 600 'm' deep counter is refused
        J.measure(mm)


def test_wardrobe_with_printed_height_gives_front_face():
    w = J.measure(wardrobe(height=2.4))
    assert w["front_face_m2"]["value"] == pytest.approx(5.28, abs=1e-9)
    assert w["front_face_m2"]["status"] == J.DRAWING_CONFIRMED and w["pcs"] == 1


def test_cupboard_symbol_found_by_scan():
    f = J.Seg("F", (7.4, 1.0), (7.4, 3.2))
    d = J.Seg("D", (7.4, 1.0), (8.0, 3.2))
    assert J.cupboard_symbol(f, d)["depth_m"] == pytest.approx(0.6)
    assert J.find_cupboard_symbols([d, f]) == [("F", "D", 0.6, 2.2)]


def test_census_totals_by_room():
    c = J.census([kitchen(), wardrobe()],
                 not_drawn=[{"room_id": "K1", "item": "WALL_CABINETS", "reason": "not drawn"}])
    assert c["totals"][J.BASE_RUN] == {"pcs": 1, "front_lm": 4.5, "plan_m2": 3.06}
    assert c["totals"][J.CUPBOARD] == {"pcs": 1, "front_lm": 2.2, "plan_m2": 1.32}
    assert set(c["by_room"]) == {"GF/K1", "GF/B1"}
    assert c["not_drawn"][0]["value"] is None and c["not_drawn"][0]["status"] == J.NOT_DRAWN


# ----------------------------------------------------------------------------------------------- adverse cases
def test_wardrobe_without_printed_height_stays_held_never_a_default():
    w = J.measure(wardrobe())
    assert w["front_face_m2"]["value"] is None
    assert w["front_face_m2"]["status"] == J.HELD
    assert w["front_lm"]["value"] == pytest.approx(2.2)                 # the drawn front still measures


def test_text_only_block_is_never_a_unit():
    assert J.is_tag_block(["TEXT", "MTEXT"]) is True                    # a block named 'WARDROBE' printing a word
    assert J.is_tag_block(["LINE", "TEXT"]) is False
    assert J.is_tag_block([]) is False


def test_lift_box_with_diagonal_is_not_a_cupboard():
    f = J.Seg("L1", (0.0, 0.0), (0.0, 1.47))
    d = J.Seg("L2", (0.0, 0.0), (1.63, 1.47))                            # 1.63 m deep: a lift car, not joinery
    assert J.cupboard_symbol(f, d) is None
    assert J.find_cupboard_symbols([f, d]) == []


def test_front_with_a_wall_twin_is_a_wall_face():
    f = J.Seg("F", (7.4, 1.0), (7.4, 3.2), "5")
    d = J.Seg("D", (7.4, 1.0), (8.0, 3.2), "5")
    wall = J.Seg("W", (7.2, 0.8), (7.2, 3.4), "1")
    assert J.is_wall_face(f, [wall]) is True
    assert J.find_cupboard_symbols([f, d], [wall]) == []


def test_misread_outlines_are_refused():
    k = kitchen()
    with pytest.raises(ValueError):                                     # a front that is not on the outline
        J.measure(J.Unit("X", J.BASE_RUN, "GF", "K1", k.ring, [J.Seg("Z", (1.0, 1.0), (1.0, 1.8))]))
    with pytest.raises(ValueError):                                     # self-crossing outline
        J.measure(J.Unit("X", J.CUPBOARD, "GF", "B1", [(7.4, 1.0), (8.0, 3.2), (7.4, 3.2), (8.0, 1.0)],
                         [J.Seg("F", (7.4, 1.0), (7.4, 3.2))]))
    with pytest.raises(ValueError):                                     # missing front
        J.measure(J.Unit("X", J.CUPBOARD, "GF", "B1", wardrobe().ring, []))
    with pytest.raises(ValueError):                                     # unknown kind
        J.measure(J.Unit("X", "SOFA", "GF", "B1", wardrobe().ring, wardrobe().front))


def test_alsenan_reading_is_well_formed():
    sys.path.insert(0, str(ROOT / "research" / "agents_t753"))
    import t753_alsenan as A
    ids = [r["unit_id"] for r in A.READING]
    assert len(ids) == len(set(ids))
    for r in A.READING:
        assert r["kind"] in J.KINDS and r["front"] and len(r["ring"]) >= 3
    cpb = [r for r in A.READING if r["kind"] == J.CUPBOARD]
    assert all("diagonal" in r["evidence"][0] for r in cpb)
    # basins inside vanities are excluded by id (B12-01), never measured here
    for r in A.READING:
        if r["kind"] == J.VANITY:
            assert r["excluded"] and all("B12-01" in x for x in r["excluded"])
    assert all(x["value"] is None for x in J.census([], not_drawn=A.NOT_DRAWN)["not_drawn"])

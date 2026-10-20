"""T-081 rework: room levels V2 (owner Q-43: unmarked rooms) and the owner wall height (owner Q-43 heights rule, Q-48 A:
decor ceiling 0.15 m everywhere), registry UP-HGT-001 / UP-FIN-WALL-001 1.8.0. Hand truth, not a client drawing.

Owner wall height = floor-to-floor - 0.60 beam - 0.15 decor ceiling - 0.10 floor finishing:
    4.50 -> 4.50 - 0.60 - 0.15 - 0.10 = 3.65        4.20 -> 4.20 - 0.85 = 3.35        3.50 -> 2.65
    a beam drawn 0.75 m (or 0.50 m) deep over the room -> HELD for the owner (rule value 3.65 kept as a diagnostic)
Split ground floor (metres; x 0..30, y 0..20):
    HALL   (1,1)-(9,9)    '+0.90'           MAJLIS (11,1)-(17,7) '+0.20'          COURT (20,1)-(28,8) exterior '+0.15'
    BED    (1,11)-(7,17)  no mark, door D1 to HALL, nothing drawn across           -> OPENS_INTO +0.90
    BATH   (7,11)-(9,14)  no mark, door D2 to BED only, nothing drawn              -> OPENS_INTO +0.90 (via BED)
    STORE  (11,9)-(14,12) no mark, door D3 to HALL with a line across the doorway  -> HELD DOORWAY_LINES_DRAWN
    LOBBY  (14,9)-(17,12) no mark, doors to HALL and MAJLIS, nothing drawn          -> HELD OPENS_INTO_TWO_LEVELS
    GUEST  (17,13)-(20,17) no mark, door only to COURT                              -> HELD NO_OPENING_TO_A_LEVELLED_ROOM
    OFFICE (21,11)-(25,15) no mark, a section reads +0.20                          -> DRAWN +0.20
    WC     (25,11)-(27,13) no mark, two section readings +0.20 / +0.90             -> HELD DRAWN_LEVELS_DISAGREE
One-level first floor: LIVING '+4.40', ROOM / BATH no mark -> FLOOR_LEVEL +4.40; an unmarked STAIR stays HELD.
Variants: metres, millimetres, mirror, rotation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from engine.source import finish_height as FH1  # noqa: E402
from engine.source import finish_height_v2 as FH  # noqa: E402
from engine.source import room_levels as RL  # noqa: E402


def _ident(p):
    return p


def _mirror(p):
    return (-p[0], p[1])


def _rot90(p):
    return (-p[1], p[0])


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


class Plan:
    def __init__(self, unit_m=1.0, tf=_ident):
        self.u, self.tf, self.texts, self.rooms, self.n = unit_m, tf, [], [], 0

    def pt(self, p):
        q = self.tf(p)
        return (q[0] / self.u, q[1] / self.u)

    def text(self, value, p):
        self.n += 1
        x, y = self.pt(p)
        self.texts.append({"id": f"T{self.n}", "value": value, "x": x, "y": y, "layer": "TXT"})

    def room(self, rid, kind, rect):
        self.rooms.append({"room_id": rid, "kind": kind, "polygon": [self.pt(p) for p in _rect(*rect)]})


def split_floor(unit_m=1.0, tf=_ident):
    P = Plan(unit_m, tf)
    for rid, kind, rect in (("HALL", "DRY", (1, 1, 9, 9)), ("MAJLIS", "DRY", (11, 1, 17, 7)),
                            ("COURT", "EXTERIOR", (20, 1, 28, 8)), ("BED", "DRY", (1, 11, 7, 17)),
                            ("BATH", "WET", (7, 11, 9, 14)), ("STORE", "DRY", (11, 9, 14, 12)),
                            ("LOBBY", "DRY", (14, 9, 17, 12)), ("GUEST", "DRY", (17, 13, 20, 17)),
                            ("OFFICE", "DRY", (21, 11, 25, 15)), ("WC", "WET", (25, 11, 27, 13))):
        P.room(rid, kind, rect)
    P.text("+0.90", (5, 5))
    P.text("+0.20", (14, 4))
    P.text("+0.15", (24, 4))
    for p in ((0.2, 0.2), (29.8, 0.2), (0.2, 19.8), (29.8, 19.8)):
        P.text("%%p0.00", p)
    links = [{"opening_id": "D1", "rooms": ["HALL", "BED"], "doorway": RL.NONE_DRAWN},
             {"opening_id": "D2", "rooms": ["BED", "BATH"], "doorway": RL.NONE_DRAWN},
             {"opening_id": "D3", "rooms": ["HALL", "STORE"], "doorway": RL.LINES_DRAWN},
             {"opening_id": "D4", "rooms": ["HALL", "LOBBY"], "doorway": RL.NONE_DRAWN},
             {"opening_id": "D5", "rooms": ["MAJLIS", "LOBBY"], "doorway": RL.NONE_DRAWN},
             {"opening_id": "D6", "rooms": ["COURT", "GUEST"], "doorway": RL.NONE_DRAWN}]
    drawn = [{"room_id": "OFFICE", "level_m": 0.20, "kind": "SECTION", "source": "section X-X, level +0.20"},
             {"room_id": "WC", "level_m": 0.20, "kind": "SECTION", "source": "section X-X"},
             {"room_id": "WC", "level_m": 0.90, "kind": "SECTION", "source": "section Y-Y"},
             {"room_id": "BED", "level_m": 0.20, "kind": "SECTION"}]            # no source: never used
    return P, links, drawn


VARIANTS = [(1.0, _ident), (0.001, _ident), (0.001, _mirror), (1.0, _rot90), (0.01, _mirror)]


def _by_id(rep):
    return {r["room_id"]: r for r in rep["rooms"]}


@pytest.mark.parametrize("unit_m,tf", VARIANTS)
def test_split_floor_room_opens_into_a_levelled_room_with_nothing_drawn(unit_m, tf):
    P, links, drawn = split_floor(unit_m, tf)
    rep = RL.room_levels_v2(P.texts, P.rooms, floor="GF", links=links, drawn=drawn)
    r = _by_id(rep)
    assert r["HALL"]["state"] == "PRINTED" and r["MAJLIS"]["state"] == "PRINTED"
    assert r["BED"]["state"] == "OPENS_INTO" and r["BED"]["level_m"] == 0.90
    assert r["BED"]["source"][0]["opening_id"] == "D1"
    assert r["BATH"]["state"] == "OPENS_INTO" and r["BATH"]["level_m"] == 0.90
    assert r["BATH"]["source"][0]["room_id"] == "BED"                                 # the hop is recorded
    assert r["STORE"]["state"] == "HELD" and r["STORE"]["why"].startswith("DOORWAY_LINES_DRAWN")
    assert r["LOBBY"]["state"] == "HELD" and r["LOBBY"]["why"].startswith("OPENS_INTO_TWO_LEVELS")
    assert r["GUEST"]["state"] == "HELD" and r["GUEST"]["why"].startswith("NO_OPENING_TO_A_LEVELLED_ROOM")
    assert r["OFFICE"]["state"] == "DRAWN" and r["OFFICE"]["level_m"] == 0.20
    assert r["WC"]["state"] == "HELD" and r["WC"]["why"].startswith("DRAWN_LEVELS_DISAGREE")
    assert r["COURT"]["state"] == "NOT_A_FLOOR_ROOM"
    for x in rep["rooms"]:
        if x["state"] not in RL.LEVELLED:
            assert x["level_m"] is None                                          # never 0, never a guess
    st = rep["storey"]
    assert st["how"] == "SPLIT_LEVEL" and st["rooms_by_rule"] == {"FLOOR_LEVEL": 0, "DRAWN": 1, "OPENS_INTO": 2}
    assert st["rooms_held"] == 4
    z = {zz["level_m"]: zz for zz in rep["zones"]}
    assert sorted(z[0.90]["rooms_by_rule"]) == ["BATH", "BED"] and z[0.20]["rooms_by_rule"] == ["OFFICE"]
    assert rep["policy"]["policy_id"] == "ROOM_LEVELS_V2"


def test_split_floor_without_links_holds_every_unmarked_room():
    P, _, _ = split_floor()
    rep = RL.room_levels_v2(P.texts, P.rooms, floor="GF")
    for rid in ("BED", "BATH", "STORE", "LOBBY", "GUEST", "OFFICE", "WC"):
        assert _by_id(rep)[rid]["state"] == "HELD"


def test_doorway_not_read_holds():
    P, links, _ = split_floor()
    links = [dict(lk, doorway=RL.NOT_READ) if lk["opening_id"] == "D1" else lk for lk in links]
    r = _by_id(RL.room_levels_v2(P.texts, P.rooms, floor="GF", links=links))
    assert r["BED"]["why"].startswith("DOORWAY_NOT_READ") and r["BATH"]["state"] == "HELD"


@pytest.mark.parametrize("unit_m,tf", VARIANTS)
def test_unmarked_room_on_a_one_level_floor_takes_the_floor_level(unit_m, tf):
    P = Plan(unit_m, tf)
    P.room("LIVING", "DRY", (0, 0, 8, 6))
    P.room("ROOM", "DRY", (9, 0, 13, 4))
    P.room("BATH", "WET", (13, 0, 15, 3))
    P.room("STAIR", "STAIR", (0, 7, 3, 12))
    P.room("TERRACE", "EXTERIOR", (16, 0, 20, 4))
    P.text("+4.40", (4, 3))
    P.text("+4.40", (18, 2))                                 # a terrace mark: not a room level
    P.text("+3.20", (22, 8))                                 # an annex roof mark outside every room
    rep = RL.room_levels_v2(P.texts, P.rooms, floor="1F")
    r = _by_id(rep)
    assert rep["storey"]["how"] == "SINGLE_LEVEL"
    for rid in ("ROOM", "BATH"):
        assert r[rid]["state"] == "FLOOR_LEVEL" and r[rid]["level_m"] == 4.40
        assert r[rid]["why"].startswith("FLOOR_LEVEL") and "Q-43" in r[rid]["rule"]
        assert r[rid]["source"][0]["value_m"] == 4.40
    assert r["STAIR"]["state"] == "HELD" and r["STAIR"]["why"].startswith("STAIR_UNMARKED")
    assert r["TERRACE"]["state"] == "NOT_A_FLOOR_ROOM"
    assert sorted(rep["zones"][0]["rooms_by_rule"]) == ["BATH", "ROOM"]


def test_one_level_floor_with_a_two_level_room_holds_unmarked_rooms():
    P = Plan()
    P.room("A", "DRY", (0, 0, 5, 5))
    P.room("B", "DRY", (6, 0, 10, 5))
    P.room("C", "DRY", (11, 0, 15, 5))
    P.text("+4.40", (2, 2))
    P.text("+4.40", (7, 2))
    P.text("+4.20", (8, 3))
    r = _by_id(RL.room_levels_v2(P.texts, P.rooms, floor="1F"))
    assert r["C"]["state"] == "HELD" and r["C"]["why"].startswith("UNLEVELLED_ROOM")


def test_v1_is_unchanged_by_v2():
    P, links, drawn = split_floor()
    v1 = RL.room_levels(P.texts, P.rooms, floor="GF")
    assert _by_id(v1)["BED"]["state"] == "HELD" and v1["policy"]["policy_id"] == "ROOM_LEVELS_V1"


# ------------------------------------------------------------------------------------------- doorway reading
def _seg(i, a, b, layer="A", path=()):
    return {"id": i, "a": a, "b": b, "layer": layer, "path": list(path)}


@pytest.mark.parametrize("unit_m", [1.0, 0.001])
@pytest.mark.parametrize("axis", [(1.0, 0.0), (0.0, 1.0), (0.7071068, 0.7071068)])
def test_doorway_reading(unit_m, axis):
    ux, uy = axis
    nx, ny = -uy, ux
    c = (10.0, 5.0)

    def P(s, o):                                             # metres along / across the wall -> drawing units
        return ((c[0] + s * ux + o * nx) / unit_m, (c[1] + s * uy + o * ny) / unit_m)

    op = {"centre_m": c, "axis": axis, "width_m": 1.0, "wall_t_m": 0.20, "symbol_blocks": ["BLK1"]}
    wall = [_seg("w1", P(-3, 0.1), P(-0.5, 0.1)), _seg("w2", P(0.5, 0.1), P(3, 0.1)),        # faces stop at jambs
            _seg("w3", P(-3, -0.1), P(-0.5, -0.1)), _seg("w4", P(0.5, -0.1), P(3, -0.1))]
    leaf = [_seg("d1", P(-0.5, 0.1), P(-0.5, 1.0), "D", ["BLK1"]),
            _seg("d2", P(-0.45, 0.0), P(0.45, 0.0), "A", ["BLK1"])]                   # its own block: skipped
    assert RL.doorway_reading(op, wall + leaf, unit_m)["state"] == RL.NONE_DRAWN
    step = _seg("s1", P(-0.5, 0.1), P(0.5, 0.1))
    got = RL.doorway_reading(op, wall + leaf + [step], unit_m)
    assert got["state"] == RL.LINES_DRAWN and got["lines"] == ["s1"]
    assert RL.doorway_reading(op, wall + [dict(step, layer="W")], unit_m, skip_layers=("W",))["state"] == \
        RL.NONE_DRAWN
    short = _seg("s2", P(-0.2, 0.0), P(0.2, 0.0))                                      # 40 % of the width
    assert RL.doorway_reading(op, wall + [short], unit_m)["state"] == RL.NONE_DRAWN
    outside = _seg("s3", P(-0.5, 0.6), P(0.5, 0.6))                                    # beyond the wall band
    assert RL.doorway_reading(op, wall + [outside], unit_m)["state"] == RL.NONE_DRAWN
    assert RL.doorway_reading({"centre_m": c}, wall, unit_m)["state"] == RL.NOT_READ


# ============================================================================================ owner wall height
RULE = FH.owner_wall_rule()
ROOM = {"room_id": "R1", "state": "PRINTED", "level_m": 1.00}
SLAB_T = FH1.termination(inside_plate=True, plate_t_cm=16)
UNK_T = FH1.termination()
B60 = [{"D_m": 0.60, "source": "beam B1 20x60"}, {"D_m": 0.60, "source": "beam B2 20x60"}]


def _zone(f2f=4.50, state="PRINTED_DIMENSION", **kw):
    z = {"state": "BOUND", "ffl": {"value_m": 1.00, "state": "PRINTED"},
         "floor_to_floor": {"value_m": f2f, "state": state},
         "soffit": {"value_m": None, "state": "NOT_PRINTED"},
         "false_ceiling": {"value_m": None, "state": "NOT_PRINTED"},
         "next_slab_top": {"value_m": None, "state": "NOT_PRINTED"},
         "slab_thickness": {"value_m": 0.16, "state": "OWNER_RULE"},
         "clear_height": {"value_m": None, "state": "NOT_PRINTED"}}
    z.update(kw)
    return z


def test_owner_rule_values_come_from_the_registry_1_8_0():
    assert (RULE["beam_m"], RULE["decor_ceiling_m"], RULE["floor_finishing_m"]) == (0.60, 0.15, 0.10)
    assert RULE["rule_ref"] == "UP-HGT-001@1.8.0" and set(RULE["source"]) == {"Q-43", "Q-48"}
    import kb_build_1_8 as KB
    assert (ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.8.0.json").read_text(encoding="utf-8") == KB.TEXT
    reg = json.loads(KB.TEXT)
    base = json.loads((ROOT / "knowledge" / "URBAN_ENGINEERING_KNOWLEDGE_1.5.0.json").read_text(encoding="utf-8"))
    a = {r["rule_id"]: r for r in base["rules"]}
    b = {r["rule_id"]: r for r in reg["rules"]}
    assert sorted(k for k in a if a[k] != b[k]) == ["UP-FIN-WALL-001", "UP-HGT-001"] and set(a) == set(b)


@pytest.mark.parametrize("term", [SLAB_T, UNK_T])
def test_owner_rule_ground_floor_4_50_gives_3_65(term):
    h = FH.room_heights(room=ROOM, zone=_zone(), term=term, owner_rule=RULE, beams_over=B60)
    for q in ("PLASTER", "PAINT"):
        assert h[q]["state"] == "COMPUTED" and h[q]["height_m"] == pytest.approx(3.65)
        assert h[q]["governing"] == "OWNER_RULE"
    assert h["WALL_TILE"]["state"] == "NOT_APPLICABLE" and "ABOVE_CEILING" not in h and h["checks"] == []


@pytest.mark.parametrize("f2f,state,want", [(4.20, "DERIVED_FROM_PRINTED_LEVELS", 3.35), (3.50, "PRINTED_DIMENSION", 2.65)])
def test_owner_rule_first_floor_4_20_gives_3_35(f2f, state, want):
    room = {"room_id": "R2", "state": "FLOOR_LEVEL", "level_m": 5.50}
    h = FH.room_heights(room=room, zone=_zone(f2f, state), term=SLAB_T, owner_rule=RULE, beams_over=B60[:1])
    assert h["PLASTER"]["height_m"] == pytest.approx(want) and h["PAINT"]["height_m"] == pytest.approx(want)


@pytest.mark.parametrize("d", [0.75, 0.50])
def test_beam_deeper_than_0_60_holds_the_room(d):
    h = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, owner_rule=RULE,
                        beams_over=B60[:1] + [{"D_m": d, "source": "beam B9"}])
    for q in ("PLASTER", "PAINT"):
        assert h[q]["state"] == "HELD" and h[q]["height_m"] is None
        assert h[q]["why"].startswith("BEAM_DEPTH_NOT_0_60") and h[q]["owner_rule_height_m"] == pytest.approx(3.65)
    beam_t = FH1.termination(covering_bands=[{"type": "B1", "D_cm": 70, "bound": True, "coverage": 1.0}])
    t = FH.room_heights(room=ROOM, zone=_zone(), term=beam_t, owner_rule=RULE, beams_over=B60)
    assert t["PAINT"]["why"].startswith("BEAM_DEPTH_NOT_0_60")


def test_beams_not_read_hold_with_diagnostic():
    h = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, owner_rule=RULE)
    assert h["PLASTER"]["why"].startswith("BEAM_OVER_ROOM_NOT_CHECKED") and h["PLASTER"]["height_m"] is None
    assert h["PAINT"]["owner_rule_height_m"] == pytest.approx(3.65) and h["owner_rule"]["state"] == "HELD"
    n = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, owner_rule=RULE, beams_over=[])
    assert n["PAINT"]["why"].startswith("BEAM_NOT_DRAWN_OVER_ROOM")


def test_floor_to_floor_missing_or_unsourced_holds():
    for f2f in ({"value_m": None, "state": "HELD"}, {"value_m": 4.50, "state": "ASSUMED"},
                {"value_m": 4.50, "state": "PROJECT_FACT", "authority": "owner"}):           # a fact without source
        h = FH.room_heights(room=ROOM, zone=_zone(floor_to_floor=f2f), term=SLAB_T, owner_rule=RULE, beams_over=B60)
        assert h["PAINT"]["state"] == "HELD" and h["PAINT"]["why"].startswith("FLOOR_TO_FLOOR_NOT_ESTABLISHED")
        assert h["PAINT"]["height_m"] is None
    fact = {"value_m": 4.20, "state": "PROJECT_FACT", "authority": "owner Q-43", "source": "section, +9.70 / +13.90"}
    ok = FH.room_heights(room=ROOM, zone=_zone(floor_to_floor=fact), term=SLAB_T, owner_rule=RULE, beams_over=B60)
    assert ok["PAINT"]["height_m"] == pytest.approx(3.35)


def test_printed_ceiling_outranks_the_owner_rule():
    z = _zone(false_ceiling={"value_m": 2.80, "state": "PRINTED"}, soffit={"value_m": 3.15, "state": "PRINTED"})
    h = FH.room_heights(room=ROOM, zone=z, term=SLAB_T, owner_rule=RULE, beams_over=B60)
    assert h["PAINT"]["height_m"] == pytest.approx(2.80) and h["PAINT"]["governing"] == "SECTION"
    assert h["PLASTER"]["height_m"] == pytest.approx(3.15) and h["PLASTER"]["governing"] == "SECTION"
    a = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, owner_rule=RULE, beams_over=B60,
                        texts=[{"id": "t", "value": "C.H. 2.90"}])
    assert a["PAINT"]["height_m"] == pytest.approx(2.90) and a["PLASTER"]["governing"] == "OWNER_RULE"
    assert [c["code"] for c in a["checks"]] == []


def test_wet_room_tiles_take_the_owner_height_and_a_printed_tile_height_wins():
    h = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, wet=True, owner_rule=RULE, beams_over=B60)
    assert h["WALL_TILE"]["height_m"] == pytest.approx(3.65) and h["WALL_TILE"]["governing"] == "OWNER_RULE"
    assert "Q-48" in h["WALL_TILE"]["method"] and h["PAINT"]["applies"] is False
    t = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, wet=True, owner_rule=RULE, beams_over=B60,
                        texts=["TILES TO 2.40"])
    assert t["WALL_TILE"]["height_m"] == pytest.approx(2.40)
    held = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, wet=True, owner_rule=RULE)
    assert held["WALL_TILE"]["state"] == "HELD" and held["WALL_TILE"]["owner_rule_height_m"] == pytest.approx(3.65)


def test_v1_allowance_still_refused_and_a_typed_rule_is_an_error():
    h = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, owner_rule=RULE, beams_over=B60,
                        ceiling_allowance_m=0.150, buildup_above={"value_m": 0.10, "state": "URBAN_FALLBACK"})
    assert sorted(x["input"] for x in h["refused_inputs"]) == ["buildup_above", "ceiling_allowance_m"]
    assert h["PAINT"]["height_m"] == pytest.approx(3.65)                     # the rule, not the refused inputs
    for bad in ("4.09", "4.24", "4.19"):
        assert bad not in repr(h)
    with pytest.raises(ValueError):
        FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, owner_rule={"beam_m": 0.5, "decor_ceiling_m": 0.1,
                                                                         "floor_finishing_m": 0.0}, beams_over=B60)


def test_held_room_holds_and_v2_levelled_room_is_accepted():
    held = {"room_id": "X", "state": "HELD", "why": "OPENS_INTO_TWO_LEVELS: [0.2, 0.9]"}
    h = FH.room_heights(room=held, zone=_zone(), term=SLAB_T, owner_rule=RULE, beams_over=B60)
    assert h["PAINT"]["why"].startswith("ROOM_LEVEL_HELD") and h["PAINT"]["height_m"] is None
    P, links, drawn = split_floor()
    bath = _by_id(RL.room_levels_v2(P.texts, P.rooms, floor="GF", links=links, drawn=drawn))["BATH"]
    fr = {"zones": [{"ffl": {"value_m": 0.90}, "floor_to_floor": {"value_m": 4.50, "state": "PRINTED_DIMENSION"}}]}
    z = RL.zone_of_v2(bath, fr)
    assert z["state"] == "BOUND"
    w = FH.room_heights(room=bath, zone=dict(_zone(), **z), term=SLAB_T, wet=True, owner_rule=RULE, beams_over=B60)
    assert w["WALL_TILE"]["height_m"] == pytest.approx(3.65)
    assert RL.zone_of_v2({"state": "HELD", "why": "x"}, fr)["state"] == "HELD"


def test_without_owner_rule_nothing_changes():
    h = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, beams_over=B60)
    assert h["PAINT"]["state"] == "HELD" and h["PAINT"]["why"].startswith("CEILING_LEVEL_NOT_PRINTED")
    assert "owner_rule" not in h

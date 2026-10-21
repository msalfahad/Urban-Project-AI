"""T-081: room floor levels from the marks printed inside each room (engine/source/room_levels.py) and finish heights
from printed values and owner rules only (engine/source/finish_height_v2.py), against hand truth.

Hand plan (metres, not a client drawing), one ground-floor frame x 0..30, y 0..20:
    R1 HALL     (1,1)-(9,9)      '+0.90' at (5,5); 'F.C.L. +3.70' at (6,6) (a ceiling level, never a floor level)
    R2 MAJLIS   (11,1)-(17,7)    '+0.20' at (14,4)
    R3 BEDROOM  (1,11)-(7,17)    no mark                               -> HELD UNLEVELLED_ROOM
    R4 STAIR    (11,9)-(15,15)   '+0.20' at (12,10), '+0.90' at (14,14) -> HELD STAIR_LINKS_LEVELS
    R5 BATH     (17,9)-(20,12)   'F.F.L. +0.90' at (18,10), '+0.85' at (19,11) -> HELD TWO_LEVELS_IN_ROOM
    R6 YARD     (20,1)-(28,8)    exterior, '+0.15' at (24,4)          -> not a floor level (non-room level)
    R7 LIVING   (21,11)-(29,19)  column hole (24,14)-(26,16) with '+0.90' at (25,15) inside the hole -> HELD
    plot marks '%%p0.00' at the four frame corners and two edge midpoints (6, in no room)
Hand results: zones +0.20 (R2) and +0.90 (R1) -> SPLIT_LEVEL; rooms PRINTED 2, HELD 4 (R3, R4, R5, R7), R6 not a room.
The plan's most frequent level is 0.00 (six plot marks against three +0.90): finding
PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL. Variants: millimetres, centimetres, mirrored, rotated 90 degrees.

Three-storey integration (no section view): GF hall '+0.90' with the six plot marks, 1F room '+4.40', 2F room '+7.90'
-> section_binding with room levels: GF floor-to-floor 4.40 - 0.90 = 3.50 DERIVED_FROM_PRINTED_LEVELS, 1F 3.50,
2F HELD; the released plan-dominant level would give GF 4.40 - 0.00 = 4.40 (wrong by the 0.90 step).

Finish heights (hand zone records, section_binding shape):
    T80-HGT-1  floor-to-floor 4.50 PRINTED_DIMENSION, slab 0.16 OWNER_RULE, nothing else printed, a 0.150 ceiling
               allowance and a 0.10 URBAN_FALLBACK build-up offered -> both refused; plaster HELD, paint HELD; never
               4.50 - 0.10 - 0.16 - 0.15 = 4.09, 4.50 - 0.10 - 0.16 = 4.24 or 4.50 - 0.16 - 0.15 = 4.19
    printed    soffit 3.15, F.C.L. 2.80, next T.O.S. 3.35, slab 0.20 PRINTED_LEVELS (slab termination):
               plaster 3.15 (soffit; T.O.S. 3.35 - 0.20 = 3.15 agrees), paint 2.80, band above the ceiling 0.35
               (plaster yes, paint HELD); beam D 50 cm: plaster 3.35 - 0.50 = 2.85
    derived    floor-to-floor 3.50, printed build-up above 0.20, slab 0.16 OWNER_RULE: plaster 3.50 - 0.20 - 0.16 = 3.14
    annotation 'PLASTER TO 3.00' and 'C.H. 2.90' in the room outrank the section (3.15 / 2.80 kept as candidates)
    conflict   F.C.L. 2.80 and CLEAR HEIGHT 2.70 on the zone (same rank) -> paint CONFLICT, no value
    wet room   no tile text: wall tile = paint 2.80 (full height, UP-FIN-WALL-001), paint not applied;
               'TILES TO 2.40' -> 2.40
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import finish_height as FH1  # noqa: E402
from engine.source import finish_height_v2 as FH  # noqa: E402
from engine.source import room_levels as RL  # noqa: E402
from engine.source import section_binding as SB  # noqa: E402


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

    def room(self, rid, kind, rect, holes=()):
        self.rooms.append({"room_id": rid, "kind": kind, "polygon": [self.pt(p) for p in _rect(*rect)],
                           "holes": [[self.pt(p) for p in _rect(*h)] for h in holes]})

    def box(self, x0, y0, x1, y1):
        xs, ys = zip(*(self.pt(p) for p in _rect(x0, y0, x1, y1)))
        return (min(xs), min(ys), max(xs), max(ys))


def ground_plan(unit_m=1.0, tf=_ident):
    P = Plan(unit_m, tf)
    P.room("R1", "DRY", (1, 1, 9, 9))
    P.room("R2", "DRY", (11, 1, 17, 7))
    P.room("R3", "DRY", (1, 11, 7, 17))
    P.room("R4", "STAIR", (11, 9, 15, 15))
    P.room("R5", "WET", (17, 9, 20, 12))
    P.room("R6", "EXTERIOR", (20, 1, 28, 8))
    P.room("R7", "DRY", (21, 11, 29, 19), holes=[(24, 14, 26, 16)])
    P.text("+0.90", (5, 5))
    P.text("F.C.L. +3.70", (6, 6))
    P.text("+0.20", (14, 4))
    P.text("+0.20", (12, 10))
    P.text("+0.90", (14, 14))
    P.text("F.F.L. +0.90", (18, 10))
    P.text("+0.85", (19, 11))
    P.text("+0.15", (24, 4))
    P.text("+0.90", (25, 15))
    for p in ((0.2, 0.2), (29.8, 0.2), (0.2, 19.8), (29.8, 19.8), (15, 0.2), (15, 19.8)):
        P.text("%%p0.00", p)
    return P


def _by_id(rep):
    return {r["room_id"]: r for r in rep["rooms"]}


VARIANTS = [(1.0, _ident), (0.001, _ident), (0.01, _ident), (1.0, _mirror), (0.001, _mirror), (1.0, _rot90)]


@pytest.mark.parametrize("unit_m,tf", VARIANTS)
def test_room_levels_hand_truth(unit_m, tf):
    P = ground_plan(unit_m, tf)
    rep = RL.room_levels(P.texts, P.rooms, floor="GF", box=P.box(0, 0, 30, 20))
    r = _by_id(rep)
    assert r["R1"]["state"] == "PRINTED" and r["R1"]["level_m"] == 0.90
    assert r["R2"]["state"] == "PRINTED" and r["R2"]["level_m"] == 0.20
    assert r["R3"]["state"] == "HELD" and r["R3"]["why"].startswith("UNLEVELLED_ROOM") and r["R3"]["level_m"] is None
    assert r["R4"]["state"] == "HELD" and r["R4"]["why"].startswith("STAIR_LINKS_LEVELS")
    assert r["R4"]["printed_levels_m"] == [0.20, 0.90]
    assert r["R5"]["state"] == "HELD" and r["R5"]["why"].startswith("TWO_LEVELS_IN_ROOM")
    assert r["R5"]["printed_levels_m"] == [0.85, 0.90]
    assert r["R6"]["state"] == "NOT_A_FLOOR_ROOM"
    assert r["R7"]["state"] == "HELD" and r["R7"]["why"].startswith("UNLEVELLED_ROOM")     # the mark is in the hole
    assert [z["level_m"] for z in rep["zones"]] == [0.20, 0.90]
    assert rep["zones"][1]["rooms"] == ["R1"] and rep["zones"][0]["rooms"] == ["R2"]
    st = rep["storey"]
    assert st["how"] == "SPLIT_LEVEL" and st["rooms_printed"] == 2 and st["rooms_held"] == 4
    assert st["stair_links_m"] == [[0.20, 0.90]] and st["plan_dominant_level_m"] == 0.0
    # the ceiling level is kept apart, never a floor level
    assert [x["level_kind"] for x in r["R1"]["other_levels"]] == ["FCL"]
    # six plot marks + the mark in the column hole are outside every room; the yard level is a non-room level
    assert sorted(s["value_m"] for s in rep["outside_marks"]) == [0.0] * 6 + [0.90]
    assert [(s["value_m"], s["room_id"]) for s in rep["non_room_levels"]] == [(0.15, "R6")]
    codes = {f["code"]: f for f in rep["findings"]}
    assert codes["PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL"]["outside_marks_at_dominant"] == 6
    assert codes["TWO_LEVELS_IN_ROOM"]["room_id"] == "R5"


def test_no_held_room_takes_a_zone_level_or_zero():
    P = ground_plan()
    rep = RL.room_levels(P.texts, P.rooms, floor="GF")
    for r in rep["rooms"]:
        if r["state"] != "PRINTED":
            assert r["level_m"] is None


def test_single_level_storey_does_not_fill_unmarked_rooms():
    P = Plan()
    P.room("A", "DRY", (0, 0, 5, 5))
    P.room("B", "DRY", (6, 0, 10, 5))
    P.text("+4.40", (2, 2))
    rep = RL.room_levels(P.texts, P.rooms, floor="1F")
    r = _by_id(rep)
    assert rep["storey"]["how"] == "SINGLE_LEVEL" and rep["storey"]["levels_m"] == [4.40]
    assert r["B"]["state"] == "HELD" and r["B"]["level_m"] is None


def test_no_level_anywhere_is_held():
    P = Plan()
    P.room("A", "DRY", (0, 0, 5, 5))
    P.text("%%p0.00", (8, 8))
    rep = RL.room_levels(P.texts, P.rooms, floor="GF")
    assert rep["storey"]["how"] == "NOT_PRINTED" and rep["zones"] == []
    assert rep["findings"][0]["code"] == "FLOOR_LEVEL_NOT_PRINTED_IN_ANY_ROOM"


def test_nested_outline_takes_the_smallest_room_and_box_filters():
    P = Plan()
    P.room("BIG", "DRY", (0, 0, 10, 10))
    P.room("NICHE", "SERVICE", (2, 2, 4, 4))
    P.text("+1.00", (6, 6))
    P.text("+0.95", (3, 3))
    P.text("+9.99", (50, 50))                       # another sheet: outside the frame box, ignored
    rep = RL.room_levels(P.texts, P.rooms, floor="GF", box=(-1, -1, 11, 11))
    r = _by_id(rep)
    assert r["BIG"]["level_m"] == 1.00 and r["NICHE"]["level_m"] == 0.95
    assert rep["outside_marks"] == []


def _floor_plan(P, x0, rid, mark):
    P.room(rid, "DRY", (x0 + 1, 1, x0 + 9, 9))
    P.text(mark, (x0 + 5, 5))


@pytest.mark.parametrize("unit_m,tf", [(1.0, _ident), (0.001, _mirror)])
def test_three_storeys_floor_to_floor_from_room_levels(unit_m, tf):
    P = Plan(unit_m, tf)
    _floor_plan(P, 0, "G1", "+0.90")
    for p in ((0.2, 0.2), (9.8, 0.2), (0.2, 9.8), (9.8, 9.8), (5, 0.2), (5, 9.8)):
        P.text("%%p0.00", p)
    _floor_plan(P, 20, "F1", "+4.40")
    _floor_plan(P, 40, "S1", "+7.90")
    boxes = {"GF": P.box(0, 0, 10, 10), "1F": P.box(20, 0, 30, 10), "2F": P.box(40, 0, 50, 10)}
    rooms = {"GF": [P.rooms[0]], "1F": [P.rooms[1]], "2F": [P.rooms[2]]}
    pfs = []
    for fl in ("GF", "1F", "2F"):
        rl = RL.room_levels(P.texts, rooms[fl], floor=fl, box=boxes[fl])
        pfs.append({"floor": fl, "box": boxes[fl], "dominant_level_m": rl["storey"]["plan_dominant_level_m"],
                    "rooms": rooms[fl]})
        if fl == "GF":
            assert rl["storey"]["plan_dominant_level_m"] == 0.0 and rl["zones"][0]["level_m"] == 0.90
            gf = rl
    rep = SB.bind(P.texts, [], 1.0, [], unit_m, pfs)
    g = rep["floors"]["GF"]["zones"][0]
    assert g["ffl"]["value_m"] == 0.90
    assert g["floor_to_floor"]["state"] == "DERIVED_FROM_PRINTED_LEVELS"
    assert g["floor_to_floor"]["value_m"] == pytest.approx(3.50, abs=1e-9)        # never 4.40 from the plot level
    assert rep["floors"]["1F"]["zones"][0]["floor_to_floor"]["value_m"] == pytest.approx(3.50, abs=1e-9)
    assert rep["floors"]["2F"]["zones"][0]["floor_to_floor"]["state"] == "HELD"
    z = RL.zone_of(_by_id(gf)["G1"], rep["floors"]["GF"])
    assert z["state"] == "BOUND" and z["ffl"]["value_m"] == 0.90
    held = RL.zone_of({"state": "HELD", "why": "UNLEVELLED_ROOM: x"}, rep["floors"]["GF"])
    assert held["state"] == "HELD" and held["why"].startswith("ROOM_LEVEL_HELD")
    assert RL.zone_of({"state": "PRINTED", "level_m": 0.30}, rep["floors"]["GF"])["why"].startswith(
        "ZONE_NOT_REPORTED")


# ============================================================================================== finish heights
ROOM = {"room_id": "R1", "state": "PRINTED", "level_m": 0.90}


def _zone(**kw):
    z = {"state": "BOUND", "ffl": {"value_m": 0.90, "state": "PRINTED"},
         "floor_to_floor": {"value_m": 3.50, "state": "PRINTED_DIMENSION"},
         "soffit": {"value_m": None, "state": "NOT_PRINTED"},
         "false_ceiling": {"value_m": None, "state": "NOT_PRINTED"},
         "next_slab_top": {"value_m": None, "state": "NOT_PRINTED"},
         "slab_thickness": {"value_m": 0.16, "state": "OWNER_RULE"},
         "clear_height": {"value_m": None, "state": "NOT_PRINTED"}}
    for k, v in kw.items():
        z[k] = v
    return z


SLAB_T = FH1.termination(inside_plate=True, plate_t_cm=16)
BEAM_T = FH1.termination(covering_bands=[{"type": "B1", "D_cm": 50, "bound": True, "coverage": 1.0}])
UNK_T = FH1.termination()


def _heights(h):
    return [h[q]["height_m"] for q in ("PLASTER", "PAINT", "WALL_TILE")]


def test_t80_hgt_1_assumed_allowance_and_buildup_refused():
    z = _zone(floor_to_floor={"value_m": 4.50, "state": "PRINTED_DIMENSION"})
    h = FH.room_heights(room=ROOM, zone=z, term=SLAB_T, ceiling_allowance_m=0.150,
                        buildup_above={"value_m": 0.10, "state": "URBAN_FALLBACK"})
    assert h["PLASTER"]["state"] == "HELD" and "FLOOR_BUILDUP_ABOVE_NOT_PRINTED" in h["PLASTER"]["why"]
    assert h["PAINT"]["state"] == "HELD" and h["PAINT"]["why"].startswith("CEILING_LEVEL_NOT_PRINTED")
    assert _heights(h) == [None, None, None]
    assert sorted(x["input"] for x in h["refused_inputs"]) == ["buildup_above", "ceiling_allowance_m"]
    flat = repr(h)
    for bad in ("4.09", "4.24", "4.19"):
        assert bad not in flat


def test_project_fact_without_source_is_refused():
    h = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T,
                        buildup_above={"value_m": 0.20, "state": "PROJECT_FACT", "authority": "owner"})
    assert h["PLASTER"]["state"] == "HELD" and h["refused_inputs"][0]["input"] == "buildup_above"


def test_unknown_keyword_is_an_error():
    with pytest.raises(TypeError):
        FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, plaster_default_m=3.0)


def _printed_zone(**kw):
    base = dict(soffit={"value_m": 3.15, "state": "PRINTED"}, false_ceiling={"value_m": 2.80, "state": "PRINTED"},
                next_slab_top={"value_m": 3.35, "state": "PRINTED"},
                slab_thickness={"value_m": 0.20, "state": "PRINTED_LEVELS"})
    base.update(kw)
    return _zone(**base)


def test_printed_section_values_slab_and_beam():
    h = FH.room_heights(room=ROOM, zone=_printed_zone(), term=SLAB_T)
    assert h["PLASTER"]["state"] == "COMPUTED" and h["PLASTER"]["height_m"] == pytest.approx(3.15)
    assert len(h["PLASTER"]["candidates"]) == 2                           # soffit and T.O.S. - slab agree
    assert h["PAINT"]["height_m"] == pytest.approx(2.80) and h["PAINT"]["applies"] is True
    assert h["ABOVE_CEILING"]["band_m"] == pytest.approx(0.35) and h["ABOVE_CEILING"]["paint"] == "HELD"
    assert h["WALL_TILE"]["state"] == "NOT_APPLICABLE" and h["checks"] == []
    b = FH.room_heights(room=ROOM, zone=_printed_zone(), term=BEAM_T)
    assert b["PLASTER"]["height_m"] == pytest.approx(2.85)


def test_derived_plaster_needs_a_printed_buildup():
    h = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T,
                        buildup_above={"value_m": 0.20, "state": "PRINTED", "source": "section"})
    assert h["PLASTER"]["governing"] == "DERIVED" and h["PLASTER"]["height_m"] == pytest.approx(3.14)
    assert h["PAINT"]["state"] == "HELD"


def test_room_annotation_outranks_section():
    h = FH.room_heights(room=ROOM, zone=_printed_zone(), term=SLAB_T,
                        texts=[{"id": "a", "value": "PLASTER TO 3.00 M"}, {"id": "b", "value": "C.H. 2.90"}])
    assert h["PLASTER"]["height_m"] == pytest.approx(3.00) and h["PLASTER"]["governing"] == "ELEMENT_ANNOTATION"
    assert h["PAINT"]["height_m"] == pytest.approx(2.90)
    assert {c["value_m"] for c in h["PAINT"]["candidates"]} == {2.90, 2.80}


def test_same_rank_disagreement_is_a_conflict():
    h = FH.room_heights(room=ROOM, zone=_printed_zone(clear_height={"value_m": 2.70, "state": "PRINTED"}),
                        term=SLAB_T)
    assert h["PAINT"]["state"] == "CONFLICT" and h["PAINT"]["height_m"] is None


def test_wet_room_tile_full_height_and_printed():
    h = FH.room_heights(room=ROOM, zone=_printed_zone(), term=SLAB_T, wet=True)
    assert h["PAINT"]["applies"] is False and h["WALL_TILE"]["height_m"] == pytest.approx(2.80)
    assert "ABOVE_CEILING" not in h
    t = FH.room_heights(room=ROOM, zone=_printed_zone(), term=SLAB_T, wet=True, texts=["TILES TO 2.40"])
    assert t["WALL_TILE"]["height_m"] == pytest.approx(2.40)
    held = FH.room_heights(room=ROOM, zone=_zone(), term=SLAB_T, wet=True)
    assert held["WALL_TILE"]["state"] == "HELD" and held["WALL_TILE"]["height_m"] is None


def test_unknown_termination_and_held_room_or_zone():
    h = FH.room_heights(room=ROOM, zone=_printed_zone(), term=UNK_T)
    assert h["PLASTER"]["state"] == "HELD" and h["PLASTER"]["why"].startswith("TERMINATION_UNKNOWN")
    a = FH.room_heights(room=ROOM, zone=_printed_zone(), term=UNK_T, texts=["PLASTER TO 3.00 M"])
    assert a["PLASTER"]["height_m"] == pytest.approx(3.00)
    r = FH.room_heights(room={"room_id": "X", "state": "HELD", "why": "UNLEVELLED_ROOM: none"}, zone=_printed_zone(),
                        term=SLAB_T)
    assert _heights(r) == [None, None, None] and r["PLASTER"]["why"].startswith("ROOM_LEVEL_HELD")
    zz = FH.room_heights(room=ROOM, zone={"state": "HELD", "why": "ZONE_NOT_REPORTED"}, term=SLAB_T)
    assert zz["PAINT"]["why"].startswith("ZONE_HELD")


def test_checks_flag_never_clip():
    z = _printed_zone(false_ceiling={"value_m": 3.00, "state": "PRINTED"})
    h = FH.room_heights(room=ROOM, zone=z, term=BEAM_T)                  # beam soffit 2.85 under a 3.00 ceiling
    assert h["PAINT"]["height_m"] == pytest.approx(3.00) and h["PLASTER"]["height_m"] == pytest.approx(2.85)
    assert [c["code"] for c in h["checks"]] == ["PAINT_ABOVE_PLASTER"]


def test_policy_records():
    p = FH.policy_record()
    assert "the 0.150 m ceiling allowance" in p["never"] and "the 0.10 m floor build-up fallback" in p["never"]
    assert "OWNER_RULE" not in p["source_states"] and "OWNER_RULE" in p["slab_states"]
    assert "a missing level as 0" in RL.policy_record()["never"]


def test_v1_still_gives_the_assumed_height_v2_refuses():
    """the defect V2 answers, shown on the frozen V1 (unchanged): 4.50 - 0.10 - 0.16 - 0.150 = 4.09."""
    v1 = FH1.wall_heights(interval={"interval_m": 4.50, "authority": "printed"}, term=SLAB_T, room_ctrl_D_cm=16,
                          buildup_above_m=0.10)
    assert v1["PAINT"]["height_m"] == pytest.approx(4.09)
    v2 = FH.room_heights(room=ROOM, zone=_zone(floor_to_floor={"value_m": 4.50, "state": "PRINTED_DIMENSION"}),
                         term=SLAB_T, buildup_above={"value_m": 0.10, "state": "URBAN_FALLBACK"})
    assert v2["PAINT"]["height_m"] is None

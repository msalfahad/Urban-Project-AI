"""R-T292-1 on villa P (synthetic, NOT Alsenan; hand values below).

Villa P, one storey, owner finish height 3.00 m (dry) / tile height 2.70 m (wet):
  room P-1 (DRY bedroom, 4.00 x 3.00): faces N 4.00 (P-W1), E 3.00 (P-W2, door D1 0.90 x 2.10), S 4.00 (P-W3,
           window W1 1.20, sill 1.00, head 2.20), W 3.00 (P-W4). Gross 14.00 x 3.00 = 42.00 m2; D1 0.90 x 2.10 = 1.89;
           W1 1.20 x 1.20 = 1.44; net 38.67 m2 = N 12.00 + E 7.11 + S 10.56 + W 9.00.
  room P-2 (WET bath, 2.00 x 2.00): 8.00 m x 2.70 = 21.60 - door D2 0.80 x 2.10 = 1.68 -> tile 19.92 m2; no paint;
           plaster under the tile HELD (substrate question), never 0.
  A held window (no head printed) on face S: net 12.00 - 1.20 x 3.00 = 8.40 .. 12.00 (BOUNDED).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t292"))
import face_line_ledger as L  # noqa: E402

H = 3.00


def faces_p1():
    return [dict(face_id="P-1|P-W1", room="P-1", finish_class="DRY", length_m=4.00, length_source="DRAWN"),
            dict(face_id="P-1|P-W2", room="P-1", finish_class="DRY", length_m=3.00, length_source="DRAWN"),
            dict(face_id="P-1|P-W3", room="P-1", finish_class="DRY", length_m=4.00, length_source="DRAWN"),
            dict(face_id="P-1|P-W4", room="P-1", finish_class="DRY", length_m=3.00, length_source="DRAWN")]


OPS = {"P-1|P-W2": [dict(id="D1", w=0.90, sill=0.0, head=2.10)],
       "P-1|P-W3": [dict(id="W1", w=1.20, sill=1.00, head=2.20)]}


def lines():
    return [dict(line_id="L-PL-1", item_code=L.PLASTER, room_id="R1"),
            dict(line_id="L-PA-1", item_code=L.PAINT, room_id="R1"),
            dict(line_id="L-TI-2", item_code=L.TILE, room_id="R2"),
            dict(line_id="L-PL-2", item_code=L.PLASTER, room_id="R2"),
            dict(line_id="L-EXT", item_code=L.EXT, room_id="FACADE")]


def test_face_nets_hand_values():
    nets = {}
    for f in faces_p1():
        r = L.face_net(f["length_m"], H, H, OPS.get(f["face_id"], []))
        assert r[4] == pytest.approx(r[5])
        nets[f["face_id"]] = r[4]
    assert nets == pytest.approx({"P-1|P-W1": 12.00, "P-1|P-W2": 7.11, "P-1|P-W3": 10.56, "P-1|P-W4": 9.00})
    assert sum(nets.values()) == pytest.approx(38.67)
    room = L.face_net(14.00, H, H, OPS["P-1|P-W2"] + OPS["P-1|P-W3"])
    assert room[0] == pytest.approx(42.00) and room[4] == pytest.approx(38.67)


def test_wet_room_tile_and_substrate():
    r = L.face_net(8.00, 2.70, 2.70, [dict(id="D2", w=0.80, sill=0.0, head=2.10)])
    assert r[4] == pytest.approx(19.92)
    wet = dict(face_id="P-2|ALL", room="P-2", finish_class="WET", length_m=8.0, length_source="DRAWN")
    assert L.check_owner(wet, L.TILE)
    assert L.check_owner(wet, L.PLASTER)            # substrate row, carried HELD
    assert (("WET", L.PLASTER) in L.SUBSTRATE_ONLY)
    assert L.check_row(dict(face_id="P-2|ALL", status=L.HELD, net_lo=None, net_hi=None,
                            held_item="plaster under full-height tile not an owner rule"))


def test_held_window_is_bounded_never_zero():
    r = L.face_net(4.00, H, H, [dict(id="W1", w=1.20, sill=None, head=None)])
    assert (r[4], r[5]) == pytest.approx((8.40, 12.00)) and r[6] == ["W1"]
    assert L.check_row(dict(face_id="S", status=L.BOUNDED, net_lo=8.40, net_hi=12.00, held_item="W1 head"))
    with pytest.raises(L.LedgerError, match="HELD_AS_ZERO"):
        L.check_row(dict(face_id="S", status=L.BOUNDED, net_lo=0.0, net_hi=12.00, held_item="W1 head"))


def test_bind_normal_and_order_invariant():
    fs = faces_p1() + [dict(face_id="P-2|ALL", room="P-2", finish_class="WET", length_m=8.0, length_source="DRAWN"),
                       dict(face_id="P-1|OPEN", room="P-1", finish_class="VIRTUAL", length_m=1.0, length_source="DRAWN")]
    rm = {"P-1": ["R1"], "P-2": ["R2"]}
    b, uf, ul = L.bind(fs, lines(), rm)
    assert b[("P-1|P-W1", L.PLASTER)] == [("L-PL-1", 1.0)] and b[("P-1|P-W1", L.PAINT)] == [("L-PA-1", 1.0)]
    assert b[("P-2|ALL", L.TILE)] == [("L-TI-2", 1.0)] and ("P-2|ALL", L.PAINT) not in b
    assert uf == [] and [x["line_id"] for x in ul] == ["L-EXT"]      # exterior: listed, owned by the facade ledger
    b2, _, _ = L.bind(list(reversed(fs)), list(reversed(lines())), rm)
    assert b2 == b


def test_mirror_and_rotation_do_not_move_a_face():
    # a face is a length x height: a mirrored or rotated plan gives the same lengths, so the same nets
    a = sum(L.face_net(f["length_m"], H, H, OPS.get(f["face_id"], []))[4] for f in faces_p1())
    # rotated 90 degrees and mirrored: N -> E, E -> S (door), S -> W (window), W -> N; the openings stay on their faces
    rot = {"P-1|P-W1": "E", "P-1|P-W2": "S", "P-1|P-W3": "W", "P-1|P-W4": "N"}
    b = sum(L.face_net(f["length_m"], H, H, OPS.get(f["face_id"], []))[4]
            for f in sorted(faces_p1(), key=lambda f: rot[f["face_id"]]))
    assert a == pytest.approx(b) == pytest.approx(38.67)


def test_one_line_holding_two_rooms_with_declared_shares():
    fs = [dict(face_id="Z|A", room="Z", finish_class="DRY", length_m=2.0, length_source="DRAWN")]
    ln = [dict(line_id="L1", item_code=L.PLASTER, room_id="RZ1"), dict(line_id="L2", item_code=L.PLASTER, room_id="RZ2"),
          dict(line_id="P1", item_code=L.PAINT, room_id="RZ1")]
    b, _, _ = L.bind(fs, ln, {"Z": ["RZ1", "RZ2"]}, shares={("Z|A", L.PLASTER): {"L1": 0.75, "L2": 0.25}})
    assert b[("Z|A", L.PLASTER)] == [("L1", 0.75), ("L2", 0.25)]
    with pytest.raises(L.LedgerError, match="SHARE_SUM"):
        L.bind(fs, ln, {"Z": ["RZ1", "RZ2"]}, shares={("Z|A", L.PLASTER): {"L1": 0.75, "L2": 0.20}})


# ---------------------------------------------------------------------------------------------- adverse
def test_face_carried_by_two_lines_refused():
    ln = lines() + [dict(line_id="L-PL-1b", item_code=L.PLASTER, room_id="R1")]
    with pytest.raises(L.LedgerError, match="FACE_TWICE"):
        L.bind(faces_p1(), ln, {"P-1": ["R1"]})


def test_held_face_as_zero_refused():
    with pytest.raises(L.LedgerError, match="HELD_AS_ZERO"):
        L.check_row(dict(face_id="F", status=L.HELD, net_lo=0.0, net_hi=0.0, held_item="roof datum"))
    with pytest.raises(L.LedgerError, match="HELD_UNNAMED"):
        L.check_row(dict(face_id="F", status=L.HELD, net_lo=None, net_hi=None, held_item=""))


@pytest.mark.parametrize("src", ["SCHEDULE", "DIMENSION_TEXT", "CENSUS", "REGISTER_RUN", "WINDOW_WIDTH", "", None])
def test_schedule_length_refused(src):
    with pytest.raises(L.LedgerError, match="SCHEDULE_LENGTH"):
        L.check_length(dict(face_id="F", length_m=4.0, length_source=src))


def test_units_and_non_positive_refused():
    with pytest.raises(L.LedgerError, match="BAD_UNITS"):
        L.check_length(dict(face_id="F", length_m=4000.0, length_source="DRAWN"))
    with pytest.raises(L.LedgerError, match="NON_POSITIVE"):
        L.check_length(dict(face_id="F", length_m=0.0, length_source="DRAWN"))


def test_tiled_face_painted_and_exterior_and_open_side_refused():
    with pytest.raises(L.LedgerError, match="TILED_FACE_PAINTED"):
        L.check_owner(dict(face_id="F", finish_class="WET"), L.PAINT)
    with pytest.raises(L.LedgerError, match="EXTERIOR_INTERNAL"):
        L.check_owner(dict(face_id="F", finish_class="EXTERIOR"), L.PLASTER)
    with pytest.raises(L.LedgerError, match="FINISHED_OPEN_SIDE"):
        L.check_owner(dict(face_id="F", finish_class="VIRTUAL"), L.PAINT)
    with pytest.raises(L.LedgerError, match="FINISH_OWNER"):
        L.check_owner(dict(face_id="F", finish_class="DRY"), L.TILE)
    with pytest.raises(L.LedgerError, match="UNKNOWN_CLASS"):
        L.owners("BALCONY")


def test_opening_deducted_twice_refused():
    with pytest.raises(L.LedgerError, match="OPENING_TWICE"):
        L.check_openings([dict(room="P-1", opening_id="D1", face_id="P-1|P-W2"),
                          dict(room="P-1", opening_id="D1", face_id="P-1|P-W3")])
    # the same door seen from its two rooms is two room sides, not a double deduction
    assert L.check_openings([dict(room="P-1", opening_id="D1", face_id="a"), dict(room="P-3", opening_id="D1", face_id="b")])


def test_room_closure_and_unmatched_face():
    assert L.room_closure([4.0, 3.0, 4.0, 3.0], 14.0) == 0.0
    with pytest.raises(L.LedgerError, match="ROOM_OPEN"):
        L.room_closure([4.0, 3.0, 4.0], 14.0)          # a face dropped
    b, uf, ul = L.bind(faces_p1(), lines(), {"P-1": []})
    assert len(uf) == 8 and {u["reason"] for u in uf} == {"no candidate line of this code in the face's room"}


def test_status_rules():
    with pytest.raises(L.LedgerError, match="NO_CHECKER_RUN"):
        L.check_row(dict(face_id="F", status=L.VERIFIED, net_lo=1.0, net_hi=1.0))
    with pytest.raises(L.LedgerError, match="NO_SOURCE"):
        L.check_row(dict(face_id="F", status=L.AOA, net_lo=1.0, net_hi=1.0))
    with pytest.raises(L.LedgerError, match="NOT_DETERMINATE"):
        L.check_row(dict(face_id="F", status=L.AOA, net_lo=1.0, net_hi=2.0, source="Q-43"))
    with pytest.raises(L.LedgerError, match="DIFFERENCE_IN_TOTAL"):
        L.check_row(dict(face_id="F", status=L.DC, net_lo=1.0, net_hi=1.0, rule_difference_m2=0.69,
                         difference_in_total=True))
    with pytest.raises(L.LedgerError, match="UNKNOWN_STATUS"):
        L.check_row(dict(face_id="F", status="PROVISIONAL", net_lo=1.0, net_hi=1.0))


def test_reconcile_names_every_cause():
    assert L.reconcile(40.00, 38.67, [dict(cause="door width", m2=1.33)]) == 0.0
    with pytest.raises(L.LedgerError, match="UNEXPLAINED"):
        L.reconcile(40.00, 38.67, [dict(cause="door width", m2=0.50)])
    assert L.reconcile(None, 38.67, []) is None

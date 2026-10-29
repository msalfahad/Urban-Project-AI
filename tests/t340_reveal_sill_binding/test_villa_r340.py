"""Villa R340 by hand (not the development villa): two windows, two doors, one wet room, bound one owner per physical
component (R-T340-BIND-1); normal and adverse cases.

Hand figures (wall 0.20 m unless named; frames flush with the room face):
  W1 raised window 1.20 x 1.50, outside reveal depth 0.08: jambs 2 x 0.08 x 1.50 = 0.240, head 0.08 x 1.20 = 0.096,
     external sill 0.096 m2 (1.20 m.l, 1 pc); room side none.
  W2 floor-level window 1.00 x 2.10 over air: jambs 2 x 0.08 x 2.10 = 0.336, head 0.080, outside strip 0.080 m2.
  D1 bath door 0.80 x 2.20 in a 0.15 wall: reveal jambs 2 x 0.15 x 2.20 = 0.660, head 0.120 -> its FIN.PLASTER line
     0.780; marble threshold 0.80 x 0.15 = 0.120 in a BLOCKED closure strip line (polygon 0.1536, superseded).
  D2 dry door 0.90 x 2.20 in 0.20 wall, no plaster line: jambs 0.880 + head 0.180 = 1.060 m2 missing -> NEW row.
  Bath face F1 2.40 m x tile top 2.40 = 5.760 - D1 0.80 x 2.20 = 1.760 -> backing / tile net 4.000 m2.
"""
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t340"))
import t340_binding as B  # noqa: E402

DC, OA = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED (Q-55 C door height 2.20)"
NA = "DRAWING-CONFIRMED (no surface)"


def rv(o, kind, side, comp, m2, ml, state="MEASURED", ev=DC, line="NO_LINE"):
    return {"opening": o, "kind": kind, "side": side, "component": comp, "m2": "" if m2 is None else str(m2),
            "ml": "" if ml is None else str(ml), "state": state, "evidence": ev, "room": "B1", "line_id": line}


def sl(o, kind, comp, m2, ml, pcs, state="MEASURED", mat="UNKNOWN", line="NO_LINE"):
    return {"opening": o, "kind": kind, "component": comp, "m2": "" if m2 is None else str(m2),
            "edge_ml": "" if ml is None else str(ml), "pcs": "" if pcs is None else str(pcs), "state": state,
            "material": mat, "floor": "GF", "line_id": line}


REVEAL = [
    rv("W1", "WINDOW", "IN", "JAMBS", 0.0, 0.0, "NONE", NA), rv("W1", "WINDOW", "IN", "HEAD", 0.0, 0.0, "NONE", NA),
    rv("W1", "WINDOW", "IN", "SILL", 0.0, 0.0, "NONE", NA, "L-W1"),
    rv("W1", "WINDOW", "OUT", "JAMBS", 0.24, 3.0), rv("W1", "WINDOW", "OUT", "HEAD", 0.096, 1.2),
    rv("W1", "WINDOW", "OUT", "SILL", 0.096, 1.2, line="L-W1"),
    rv("W2", "FLOOR_GLAZING", "IN", "FLOOR_STRIP", 0.0, 0.0, "NONE", NA, "L-W2"),
    rv("W2", "FLOOR_GLAZING", "OUT", "JAMBS", 0.336, 4.2), rv("W2", "FLOOR_GLAZING", "OUT", "HEAD", 0.08, 1.0),
    rv("W2", "FLOOR_GLAZING", "OUT", "THRESHOLD", 0.08, 0.0, line="L-W2"),
    rv("D1", "DOOR", "THROUGH", "JAMBS", 0.66, 4.4, ev=OA, line="L-D1P"),
    rv("D1", "DOOR", "THROUGH", "HEAD", 0.12, 0.8, line="L-D1P"),
    rv("D2", "DOOR", "THROUGH", "JAMBS", 0.88, 4.4, ev=OA), rv("D2", "DOOR", "THROUGH", "HEAD", 0.18, 0.9),
]
SILLS = [
    sl("W1", "WINDOW", "SILL_IN", 0.0, 0.0, 0, "NONE", "-"), sl("W1", "WINDOW", "SILL_OUT", 0.096, 1.2, 1, line="L-W1"),
    sl("W2", "FLOOR_GLAZING", "THRESHOLD_IN", 0.0, 0.0, 0, "NONE", "-"),
    sl("W2", "FLOOR_GLAZING", "THRESHOLD_OUT", 0.08, 1.0, 1, line="L-W2"),
    sl("D1", "DOOR", "THRESHOLD", 0.12, 0.8, 1, mat="MARBLE", line="L-D1T"),
    sl("D1", "DOOR", "FINISH_CHANGE_EDGE", None, 1.6, None, mat="-"),
    sl("D2", "DOOR", "THRESHOLD", 0.18, 0.9, 1, mat="FLOOR PORCELAIN", line="L-D2T"),
]
LINES = {
    "L-W1": {"item_code": "ARCH.WINDOW_REVEAL", "measured_net": None, "low": None, "high": None},
    "L-W2": {"item_code": "ARCH.WINDOW_REVEAL", "measured_net": None, "low": None, "high": None},
    "L-D1P": {"item_code": "FIN.PLASTER", "measured_net": 0.78, "low": None, "high": None},
    "L-D1T": {"item_code": "ARCH.THRESHOLD", "measured_net": None, "low": None, "high": None},
    "L-D2T": {"item_code": "FIN.FLOOR.PORCELAIN", "measured_net": 0.18, "low": None, "high": None},
    "L-BACK": {"item_code": "FIN.PLASTER", "measured_net": 4.0, "low": None, "high": None},
    "L-TILE": {"item_code": "FIN.WALL.TILE", "measured_net": 4.0, "low": None, "high": None},
}
NEW = {("W1", "REVEAL_OUT_JAMBS"): "REVEAL.WINDOW_OUT|W1", ("W1", "REVEAL_OUT_HEAD"): "REVEAL.WINDOW_OUT|W1",
       ("W2", "REVEAL_OUT_JAMBS"): "REVEAL.WINDOW_OUT|W2", ("W2", "REVEAL_OUT_HEAD"): "REVEAL.WINDOW_OUT|W2",
       ("D2", "REVEAL_THROUGH_JAMBS"): "FIN.PLASTER|door jambs and head|D2",
       ("D2", "REVEAL_THROUGH_HEAD"): "FIN.PLASTER|door jambs and head|D2"}
RETYPE = {"L-D1T": ("FIN.MARBLE.THRESHOLD", "retype: wet doorway marble")}
PLASTER = {"D1": "L-D1P"}


def comps(reveal=REVEAL, sills=SILLS):
    return B.merge_ledgers(B.reveal_components(reveal), B.sill_components(sills))


def bind(c=None, lines=LINES, plaster=PLASTER, narrow=None, retype=RETYPE, new=NEW):
    return B.assign_owners(c or comps(), lines, plaster, narrow, retype, new)


def carriers():
    return {c["carrier"]: c for c in bind()[1]}


# ------------------------------------------------------------------------------------------------ normal
def test_hand_figures():
    c = carriers()
    assert c["NEW:REVEAL.WINDOW_OUT|W1"]["m2"] == pytest.approx(0.336)          # 0.240 + 0.096
    assert c["NEW:REVEAL.WINDOW_OUT|W2"]["m2"] == pytest.approx(0.416)          # 0.336 + 0.080
    assert c["L-D1P"]["action"] == "KEEP" and c["L-D1P"]["m2"] == pytest.approx(0.78)
    assert c["NEW:FIN.PLASTER|door jambs and head|D2"]["m2"] == pytest.approx(1.06)
    assert c["L-W1"]["action"] == "FILL" and c["L-W1"]["m2"] == pytest.approx(0.096) and c["L-W1"]["pcs"] == 1
    assert c["L-W2"]["m2"] == pytest.approx(0.08)
    assert c["L-D1T"]["action"] == "RETYPE_FILL" and c["L-D1T"]["item"] == "FIN.MARBLE.THRESHOLD"
    assert c["L-D1T"]["m2"] == pytest.approx(0.12)
    assert c["L-D2T"]["action"] == "KEEP"


def test_one_owner_per_component_and_room_side_none():
    rows, _ = bind()
    keys = [(r.opening, r.comp) for r in rows]
    assert len(keys) == len(set(keys)) == 16        # 19 ledger rows: 2 sills / strips shared, the edge not an item
    na = [r for r in rows if r.status == "NOT_APPLICABLE_WITH_EVIDENCE"]
    assert {(r.opening, r.comp) for r in na} == {("W1", "REVEAL_IN_JAMBS"), ("W1", "REVEAL_IN_HEAD"),
                                                 ("W1", "SILL_IN"), ("W2", "THRESHOLD_IN")}
    assert all(r.m2 == 0.0 for r in na)


def test_shared_sill_is_one_surface_with_material_and_count():
    c = comps()
    s = c[("W1", "SILL_OUT")]
    assert s.sources == ["T-313", "T-325"] and s.material == "UNKNOWN" and s.pcs == 1


def test_mirror_order_same_result():
    a = [(r.opening, r.comp, r.owner, r.m2) for r in bind()[0]]
    rr, ss = REVEAL[:], SILLS[:]
    random.Random(7).shuffle(rr)
    random.Random(8).shuffle(ss)
    b = [(r.opening, r.comp, r.owner, r.m2) for r in bind(comps(rr, ss))[0]]
    assert a == b


def test_held_part_beside_a_measured_part():
    r2 = [dict(x) for x in REVEAL]
    j = next(x for x in r2 if x["opening"] == "W1" and x["side"] == "OUT" and x["component"] == "JAMBS")
    j.update(m2="", ml="", state="HELD", evidence="HELD")
    c = {x["carrier"]: x for x in bind(comps(r2))[1]}["NEW:REVEAL.WINDOW_OUT|W1"]
    assert c["m2"] == pytest.approx(0.096) and c["held"] == "REVEAL_OUT_JAMBS" and "HELD beside" in c["note"]
    rows = [r for r in bind(comps(r2))[0] if r.comp == "REVEAL_OUT_JAMBS" and r.opening == "W1"]
    assert rows[0].m2 is None                      # held never 0


def test_within_bound_and_narrow():
    lines = dict(LINES, **{"L-D1P": {"item_code": "FIN.PLASTER", "measured_net": None, "low": 0.70, "high": 0.80}})
    c = {x["carrier"]: x for x in bind(lines=lines)[1]}
    assert c["L-D1P"]["action"] == "KEEP" and "WITHIN_BOUND" in c["L-D1P"]["note"]
    c = {x["carrier"]: x for x in bind(lines=lines, narrow={"L-D1P": (0.78, "printed")})[1]}
    assert c["L-D1P"]["action"] == "NARROW"


def test_wet_face_closes_and_reveal_outside_the_face():
    rows, _ = bind()
    clo = B.face_closure([{"face_id": "B1|F1", "length_m": 2.4, "top_m": 2.4, "net_m2": 4.0, "openings": ["D1"]}],
                         {("B1|F1", "D1"): 1.76})
    assert clo[0]["residual_m2"] == 0.0
    out = B.wet_cross_check([{"room": "B1", "opening": "D1", "face_id": "B1|F1", "band_m2": 1.76}], rows,
                            {"L-BACK"}, {"L-TILE"}, clo)
    assert {r["component"] for r in out} == {"REVEAL_THROUGH_JAMBS", "REVEAL_THROUGH_HEAD", "THRESHOLD"}
    assert all(r["overlap_m2"] == 0.0 and r["owner"] in ("L-D1P", "L-D1T") for r in out)


def test_layer_check_alias_and_named_difference():
    out = B.layer_check({"D1": 0.12, "D3": 0.20}, {"D1": 0.1196, "BATH-DOOR": 0.20}, {"BATH-DOOR": "D3"})
    r = {x["door"]: x for x in out}
    assert r["D1"]["result"].startswith("DIFFERS") and r["D1"]["difference_m2"] == pytest.approx(-0.0004)
    assert r["D3"]["result"] == "EQUAL"


# ------------------------------------------------------------------------------------------------ adverse
def test_door_reveal_second_carrier_refused():
    new = dict(NEW)
    new[("D1", "REVEAL_THROUGH_JAMBS")] = "FIN.PLASTER|door jambs and head|D1"
    with pytest.raises(B.BindingError, match="second carrier"):
        bind(new=new)


def test_door_reveal_in_a_line_other_than_its_plaster_line_refused():
    with pytest.raises(B.BindingError, match="second carrier"):
        bind(plaster={"D1": "L-OTHER"})


def test_reveal_in_a_sill_line_refused():
    r2 = [dict(x, line_id="L-W1") if x["opening"] == "W1" and x["component"] == "JAMBS" and x["side"] == "OUT" else x
          for x in REVEAL]
    with pytest.raises(B.BindingError, match="reveal owned by a ARCH.WINDOW_REVEAL"):
        bind(comps(r2))


def test_threshold_in_a_reveal_line_refused():
    s2 = [dict(x, line_id="L-D1P") if x["opening"] == "D1" and x["component"] == "THRESHOLD" else x for x in SILLS]
    with pytest.raises(B.BindingError, match="sill / threshold owned by a FIN.PLASTER"):
        bind(comps(sills=s2))


def test_threshold_under_two_doors_refused():
    s2 = [dict(x, line_id="L-D1T") if x["opening"] == "D2" and x["component"] == "THRESHOLD" else x for x in SILLS]
    with pytest.raises(B.BindingError, match="one carrier, one opening"):
        bind(comps(sills=s2))


def test_held_sill_as_zero_refused():
    s2 = [dict(x, state="UNRESOLVED", m2="0.0") if x["component"] == "SILL_OUT" else x for x in SILLS]
    with pytest.raises(B.BindingError, match="carries a figure"):
        comps(sills=s2)


def test_measured_missing_figure_refused():
    r2 = [dict(x, m2="") if x["opening"] == "D2" and x["component"] == "HEAD" else x for x in REVEAL]
    with pytest.raises(B.BindingError, match="missing never becomes 0"):
        comps(r2)


def test_missing_scope_without_a_row_refused():
    new = {k: v for k, v in NEW.items() if k[0] != "D2"}
    with pytest.raises(B.BindingError, match="no owner"):
        bind(new=new)


def test_ledgers_disagree_on_one_sill_refused():
    s2 = [dict(x, m2="0.12") if x["component"] == "SILL_OUT" else x for x in SILLS]
    with pytest.raises(B.BindingError, match="disagree"):
        comps(sills=s2)


def test_line_differs_from_ledger_refused():
    lines = dict(LINES, **{"L-D2T": {"item_code": "FIN.FLOOR.PORCELAIN", "measured_net": 0.20, "low": None,
                                     "high": None}})
    with pytest.raises(B.BindingError, match="differ"):
        bind(lines=lines)


def test_narrow_outside_bound_refused():
    lines = dict(LINES, **{"L-D1P": {"item_code": "FIN.PLASTER", "measured_net": None, "low": 0.70, "high": 0.75}})
    with pytest.raises(B.BindingError, match="bound"):
        bind(lines=lines, narrow={"L-D1P": (0.78, "x")})


def test_superseded_closure_polygon_refused():
    with pytest.raises(B.BindingError, match="superseded"):
        B.check_superseded({("D1", "THRESHOLD"): 0.1536}, {("D1", "THRESHOLD"): 0.1536})
    B.check_superseded({("D1", "THRESHOLD"): 0.12}, {("D1", "THRESHOLD"): 0.1536})


def test_reveal_counted_in_the_wet_face_refused():
    # the shared jamb: the face net carries the D1 jambs (4.000 + 0.660): closure fails
    clo = B.face_closure([{"face_id": "B1|F1", "length_m": 2.4, "top_m": 2.4, "net_m2": 4.66, "openings": ["D1"]}],
                         {("B1|F1", "D1"): 1.76})
    with pytest.raises(B.BindingError, match="face closure"):
        B.wet_cross_check([], bind()[0], {"L-BACK"}, {"L-TILE"}, clo)


def test_reveal_owned_by_a_backing_line_refused():
    lines = dict(LINES)
    rows, _ = bind()
    with pytest.raises(B.BindingError, match="backing / tile"):
        B.wet_cross_check([{"room": "B1", "opening": "D1", "face_id": "B1|F1", "band_m2": 1.76}], rows,
                          {"L-D1P"}, {"L-TILE"}, [])
    assert lines


def test_valued_face_with_held_deduction_refused():
    with pytest.raises(B.BindingError, match="held deduction"):
        B.face_closure([{"face_id": "B1|F1", "length_m": 2.4, "top_m": 2.4, "net_m2": 4.0, "openings": ["D1"]}],
                       {("B1|F1", "D1"): None})


def test_negative_and_unknown_component_refused():
    with pytest.raises(B.BindingError, match="negative"):
        comps([dict(REVEAL[3], m2="-0.24")] + REVEAL[4:])
    with pytest.raises(B.BindingError, match="unknown"):
        comps([dict(REVEAL[3], component="RETURN")])


def test_bound_to_a_line_not_in_the_candidate_refused():
    lines = {k: v for k, v in LINES.items() if k != "L-W2"}
    with pytest.raises(B.BindingError, match="not a line of the candidate"):
        bind(lines=lines)

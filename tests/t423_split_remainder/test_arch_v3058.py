"""T-423: ARCH_TAKEOFF_V3.0.58 (the T-246 split remainder) on the hand-calculated NON-Alsenan villa V423 (own
figures, no drawing):

  Bedroom R1 plan 4.000 x 5.000 = 20.000 m2 gross; a dome D-N (HELD) covers 3.0000 m2 of it -> decor 17.000 m2.
      Its ceiling line nets 17.000 with an EMPTY list (the T-330 FLAG): the list gets ONE item D-N over R1, qty
      20.000 - 17.000 = 3.000 m2, bound to the ledger print 3.0000 (half a unit of the 4th decimal: 0.00005).
  Bedroom R2 plan 19.016545, decor 18.6747 (ledger 4 dp), dome piece printed 0.3418: gap 0.341845 is within
      0.00005 of the print -> listed 0.341845 (the line's own unrounded gap, never a rounding move).
  Bath B1 tile line (owner height 2.80): face B1|W1 3.000 m x 2.80 = 8.400 less the door D-1 0.80 x 2.10 = 1.680 ->
      6.720 m2 on the record; its doorway piece B1|OFF:DOORWAY 0.900 m x 2.80 = 2.520 m2 with no hole. The door's
      contour segment is the doorway piece: move -> W1 8.400, doorway 0.840; room 9.240 m2 before and after.
  Kitchen K1: every face tiled to the coat top; its paint line BLOCKED_RFI -> NOT_APPLICABLE naming the tile line.
  Thresholds T1 (BY_SPEC) and T2 (URBAN_METHOD), one owner-rule marble: both URBAN_METHOD; T1 0.80 x 0.20 = 0.16 m2
      (0.80 m.l, 1 pc) carries measure_pair {m2 0.16, lm 0.8, nr 1} = its formula.
Adverse: dome print off by more than half a unit, stale binding (net / state / element), list already present,
applied twice, hole moved to a straight face, hole not on its face, hole larger than the doorway piece, carrying line
in another room / blank, paint line already valued, measure pair not the formula, two material states left, mm-scale
gap (unit slip), set aside AND changed, a quantity moved, mirrored villa (same result).
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3058 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "V423-SYNTHETIC", "e" * 64
REC = "wall_tile_v3021"


def _ln(code, eid, state, net=None, gross=None, room=None, unit="m2", formula=None, inputs=None, mat="BY_SPEC",
        floor="1F"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=state,
                        measured_net=net, gross=gross, element_id=eid, floor=floor, room_id=room,
                        formula=formula or f"synthetic {code} {eid}", inputs=inputs, rule_id="R-SYN",
                        rule_version="1", geometry_source="SYNTHETIC_FIXTURE", material_state=mat,
                        rfi={"question": "detail", "unlocks": eid} if state == "BLOCKED_RFI" else None,
                        notes="synthetic", **({} if code in BL.ITEMS else
                                              {"item_en": "item", "item_ar": "بند", "trade": "FLOOR_FINISH"}))


FACES = {"faces": [{"face_id": "B1|W1", "length_m": 3.0, "height_m": 2.8, "openings": [{"id": "D-1", "m2": 1.68}],
                    "net_m2": 6.72},
                   {"face_id": "B1|OFF:DOORWAY", "length_m": 0.9, "height_m": 2.8, "openings": [], "net_m2": 2.52}]}


def lines():
    return [
        _ln("FIN.CEILING", "R1:ceiling", "PROVISIONAL", 17.0, 20.0, room="R1"),
        _ln("FIN.CEILING", "R2:ceiling", "PROVISIONAL", 18.6747, 19.016545, room="R2"),
        _ln("FIN.WALL.TILE", "B1:wall tile", "PROVISIONAL", 9.24, 10.92, room="B1", inputs={REC: copy.deepcopy(FACES)}),
        _ln("FIN.WALL.TILE", "K1:wall tile", "PROVISIONAL", 30.0, 30.0, room="K1"),
        _ln("FIN.PAINT", "K1:paint", "BLOCKED_RFI", room="K1"),
        _ln("FIN.PAINT", "R1:paint", "PROVISIONAL", 40.0, 40.0, room="R1"),
        _ln("FIN.MARBLE.THRESHOLD", "T1 threshold strip", "MEASURED", 0.16, room="B1", mat="BY_SPEC",
            formula="T1 wet doorway threshold: clear width 0.8 x wall thickness 0.2 = 0.16 m2 (0.8 m.l, 1 pc); marble"),
        _ln("FIN.MARBLE.THRESHOLD", "T2 threshold strip", "MEASURED", 0.18, room="B2", mat="URBAN_METHOD",
            formula="T2 wet doorway threshold: clear width 0.9 x wall thickness 0.2 = 0.18 m2 (0.9 m.l, 1 pc); marble"),
        _ln("FIN.FLOOR.CERAMIC", "B1:FLOOR", "MEASURED", 6.0, 6.0, room="B1"),
    ]


LN = lines()
ID = {ln["location"]["element_id"]: ln["line_id"] for ln in LN}


def _x(eid, ln=None):
    b = ln or next(x for x in LN if x["location"]["element_id"] == eid)
    x = {"item_code": b["item_code"], "element_id": eid, "unit": b["unit"], "evidence_state": b["evidence_state"]}
    if b.get("gross") is not None:
        x.update(gross=b["gross"], measured_net=b["measured_net"])
    return x


def _src(t):
    return {"task": t, "file": f"research/v423/{t}.csv", "sha256": t[-1] * 64, "merge_commit": "d" * 40,
            "checker_run": f"checker {t} Gate A PASS"}


def entries():
    return [
        {"action": "LIST_CEILING", "line_id": ID["R1:ceiling"], "expect": _x("R1:ceiling"), "source_tasks": ["T-A"],
         "items": [{"id": "DOME:D-N:over:R1", "print_m2": 3.0, "source": "dome table"}]},
        {"action": "LIST_CEILING", "line_id": ID["R2:ceiling"], "expect": _x("R2:ceiling"), "source_tasks": ["T-A"],
         "items": [{"id": "DOME:D-E:over:R2", "print_m2": 0.3418, "source": "dome table"}]},
        {"action": "MOVE_FACE_DEDUCTION", "line_id": ID["B1:wall tile"], "expect": _x("B1:wall tile"),
         "source_tasks": ["T-B"], "rec_key": REC, "opening_id": "D-1", "from_face": "B1|W1",
         "to_face": "B1|OFF:DOORWAY", "finding": "OPENING_OFF_ITS_FACE"},
        {"action": "NOT_APPLICABLE", "line_id": ID["K1:paint"], "expect": _x("K1:paint"), "source_tasks": ["T-B"],
         "evidence": "every face tiled to the coat top", "carried_by": ID["K1:wall tile"]},
        {"action": "MATERIAL_STATE", "line_id": ID["T1 threshold strip"], "expect": _x("T1 threshold strip"),
         "source_tasks": ["T-C"], "material_state": "URBAN_METHOD", "rule_source": "owner marble threshold rule"},
        {"action": "MEASURE_PAIR", "line_id": ID["T1 threshold strip"], "expect": _x("T1 threshold strip"),
         "source_tasks": ["T-C"], "m2": 0.16, "ml": 0.8, "pcs": 1},
    ]


def doc(ents=None, aside=()):
    return {"schema": A.INPUTS_SCHEMA, "project_id": PID, "sources": [_src("T-A"), _src("T-B"), _src("T-C")],
            "set_aside": list(aside), "entries": entries() if ents is None else ents}


def run(d=None, prev=None):
    prev = prev if prev is not None else copy.deepcopy(LN)
    ch, log = A.changes_for(A.load_inputs(d or doc(), PID), prev)
    return prev, ch, log


def _by(out, eid):
    return next(x for x in out if x["location"]["element_id"] == eid)


def _new():
    prev, ch, log = run()
    out, ident = A.integrate(prev, ch)
    return prev, ch, out, ident


# ------------------------------------------------------------------------------------------------- normal case
def test_hand_values():
    prev, ch, out, ident = _new()
    r1 = _by(out, "R1:ceiling")
    assert r1["deductions"] == [dict(r1["deductions"][0], id="DOME:D-N:over:R1", qty=3.0, unit="m2")]
    assert r1["gross"] - r1["deductions"][0]["qty"] == pytest.approx(r1["measured_net"])
    r2 = _by(out, "R2:ceiling")
    assert r2["deductions"][0]["qty"] == pytest.approx(0.341845, abs=1e-9)        # the line's own gap, unrounded
    assert abs(r2["gross"] - r2["deductions"][0]["qty"] - r2["measured_net"]) <= A.TOL
    b1 = _by(out, "B1:wall tile")
    f = {x["face_id"]: x for x in b1["calculation"]["inputs"][REC]["faces"]}
    assert f["B1|W1"]["net_m2"] == pytest.approx(8.4) and f["B1|W1"]["openings"] == []
    assert f["B1|OFF:DOORWAY"]["net_m2"] == pytest.approx(0.84)
    assert [o["id"] for o in f["B1|OFF:DOORWAY"]["openings"]] == ["D-1"]
    assert sum(x["net_m2"] for x in f.values()) == pytest.approx(9.24) == b1["measured_net"]
    k1 = _by(out, "K1:paint")
    assert k1["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and k1["measured_net"] is None
    assert ID["K1:wall tile"] in k1["notes"]
    t1 = _by(out, "T1 threshold strip")
    assert t1["material_state"] == "URBAN_METHOD" and t1["measured_net"] == 0.16
    assert t1["measure_pair"]["measures"] == {"m2": 0.16, "lm": 0.8, "nr": 1}
    assert t1["measure_pair"]["price_one_basis"] is True
    s = ident["split_remainder"]
    assert (s["ceiling_lists"], s["face_moves"], s["not_applicable"], s["measure_pairs"]) == (2, 1, 1, 1)
    assert s["threshold_states"] == {"URBAN_METHOD": 2}


def test_no_quantity_and_no_total_moves():
    prev, ch, out, ident = _new()
    for a, b in zip(prev, out):
        assert a["line_id"] == b["line_id"] and a["measured_net"] == b["measured_net"]
        assert a.get("bounded_range") == b.get("bounded_range")
    t0, t1 = A304.code_totals(prev), A304.code_totals(out)
    for k in set(t0) | set(t1):
        a, b = dict(t0.get(k) or {}), dict(t1.get(k) or {})
        if k.startswith("FIN.PAINT"):       # the K1 paint line leaves the blocked count (and the line count): 1
            assert (a.pop("blocked_lines") - b.pop("blocked_lines"), a.pop("lines") - b.pop("lines")) == (1, 1)
        assert a == b, k
    assert ident["outside_rows"] == len(prev) - 5 and ident["replaced"] == 5


def test_write_files(tmp_path):
    prev, ch, log = run()
    names, ident, led = A.write(tmp_path, prev, ch, log)
    assert "V3_0_58_BOQ_LINES.json" in names and len(led["rows"]) == 5
    assert ident["diff"]["vs_base"] == {"SAME": 4, "CHANGED_TEXT_ONLY": 4, "CHANGED": 1}   # K1 paint: state only


def test_mirror_same_result():
    """a mirrored villa (rooms relabelled, faces in the other order): the same figures move the same way."""
    prev = copy.deepcopy(LN)
    b1 = next(x for x in prev if x["location"]["element_id"] == "B1:wall tile")
    b1["calculation"]["inputs"][REC]["faces"].reverse()
    _, ch, _ = run(prev=prev)
    out, _ = A.integrate(prev, ch)
    f = {x["face_id"]: x for x in _by(out, "B1:wall tile")["calculation"]["inputs"][REC]["faces"]}
    assert (f["B1|W1"]["net_m2"], f["B1|OFF:DOORWAY"]["net_m2"]) == (8.4, 0.84)


# ------------------------------------------------------------------------------------------------- adverse cases
def _with(i, **kw):
    e = entries()
    e[i] = dict(e[i], **kw)
    return doc(e)


def test_dome_print_off_by_more_than_half_unit():
    with pytest.raises(A.InputsError, match="does not close by id"):
        run(_with(1, items=[{"id": "DOME:D-E:over:R2", "print_m2": 0.3419, "source": "x"}]))


def test_stale_binding_refused():
    for k, v in (("measured_net", 17.1), ("evidence_state", "MEASURED"), ("element_id", "R9:ceiling")):
        x = dict(_x("R1:ceiling"), **{k: v})
        with pytest.raises(A.InputsError, match="stale"):
            run(_with(0, expect=x))


def test_list_already_present_and_applied_twice():
    prev = copy.deepcopy(LN)
    prev[0]["deductions"] = [{"id": "x", "qty": 3.0, "unit": "m2"}]
    with pytest.raises(A.InputsError, match="already lists"):
        run(prev=prev)
    p, ch, _ = run()
    out, _ = A.integrate(p, ch)
    with pytest.raises(A.InputsError, match="applied once"):
        run(prev=out)


def test_hole_moves_only_to_the_doorway_piece():
    with pytest.raises(A.InputsError, match="OFF:DOORWAY"):
        run(_with(2, to_face="B1|W2"))
    with pytest.raises(A.InputsError, match="not once on"):
        run(_with(2, opening_id="D-9"))


def test_hole_larger_than_doorway_piece():
    prev = copy.deepcopy(LN)
    b1 = next(x for x in prev if x["location"]["element_id"] == "B1:wall tile")
    b1["calculation"]["inputs"][REC]["faces"][1]["net_m2"] = 1.0
    with pytest.raises(A.InputsError, match="below 0"):
        run(prev=prev)


def test_carrying_line_must_be_a_valued_tile_line_of_the_room():
    with pytest.raises(A.InputsError, match="carrying line"):
        run(_with(3, carried_by=ID["B1:wall tile"]))
    with pytest.raises(A.InputsError, match="carrying line"):
        run(_with(3, carried_by=ID["R1:paint"]))


def test_valued_paint_line_never_not_applicable():
    with pytest.raises(A.InputsError, match="only a blank paint line"):
        run(_with(3, line_id=ID["R1:paint"], expect=_x("R1:paint")))


def test_measure_pair_must_equal_formula():
    with pytest.raises(A.InputsError, match="not the formula"):
        run(_with(5, ml=0.9))
    with pytest.raises(A.InputsError, match="1 pc"):
        run(_with(5, pcs=2))
    with pytest.raises(A.InputsError, match="outside"):
        run(_with(5, m2=160.0 * 10))          # mm-scale slip


def test_two_material_states_left_refused():
    e = entries()
    e[4] = dict(e[4], material_state="BY_SPEC")    # T1 stays BY_SPEC beside T2 URBAN_METHOD
    prev, ch, _ = run(doc(e))
    with pytest.raises(ValueError, match="one material state"):
        A.integrate(prev, ch)


def test_set_aside_and_changed_refused():
    with pytest.raises(A.InputsError, match="set aside AND changed"):
        A.load_inputs(doc(aside=[{"line_id": ID["R1:ceiling"], "why": "x"}]), PID)
    with pytest.raises(A.InputsError, match="stale name"):
        run(doc(aside=[{"line_id": "L-" + "0" * 20, "why": "x"}]))


def test_quantity_move_refused_by_check():
    prev, ch, _ = run()
    ch[0]["after"]["measured_net"] = 16.0
    with pytest.raises(ValueError):
        A.integrate(prev, ch)


def test_unknown_code_and_action():
    with pytest.raises(A.InputsError, match="not a code"):
        run(_with(0, expect=dict(_x("R1:ceiling"), item_code="FIN.FLOOR.CERAMIC")))
    with pytest.raises(A.InputsError, match="action"):
        run(_with(0, action="REVALUE"))


def test_no_inputs_no_change():
    ch, log = A.changes_for(None, copy.deepcopy(LN))
    assert ch == [] and log["state"] == "NO_PROJECT_INPUT"
    assert A.load_inputs(None) is None and A30.METHOD

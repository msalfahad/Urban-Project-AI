"""T-315 r2 (Gate B F-T315-C1 / C2): one owner per wall base when a tiled room is split over engine rooms, on a
hand-calculated NON-Alsenan villa (W315B), normal and adverse.

Villa W315B, GF open pantry K1, owner height 3.65 (Q-48 A), every drawn wall hosts a counter -> every drawn wall tiled
full height (UP-PANTRY-003), the east side OPEN 2.40 (tiles nothing). By hand:
  faces  K1|N 3.00 x 3.65 = 10.95 less window WK 1.00 x (2.50 - 1.00) = 1.50 -> 9.45; K1|W 2.40 x 3.65 = 8.76;
         K1|S 3.00 x 3.65 = 10.95.  Tile 29.16 m2 on 8.40 m of wall; contour 8.40 + open 2.40 = 10.80 m.  (ADD)
  base   the pantry's wall base 3.00 (N) + 2.40 (W: Wn 1.40 + Ws 1.00) + 3.00 (S) = 8.40 lm, all under full-height tile.
  engine rooms (merged split): EK = the counter cell, wholly inside K1 (WHOLE); EZ = dining + pantry open zone (PART).
         EK skirting 2.20 lm = Ws 1.00 + S 1.20      -> every metre on tiled faces: NOT_APPLICABLE (no figure)
         EZ skirting 17.40 lm = N 3.00 + Wn 1.40 + S 1.00 + dining walls D 12.00
                                                       -> SPLIT 5.40 on tiled faces: rest 12.00 lm (the dining) kept
         EZ range 0 .. 2.50 lm = WK 1.00 (sill window on K1|N, tiled below the sill) + WD 1.50 (a dining window)
                                                       -> SPLIT 1.00: range 0 .. 1.50
         S 3.00 - 1.20 - 1.00 = 0.80 lm of the pantry base lies on no engine room boundary (no line carries it).
  closure 2.20 + 5.40 + 0.80 = 8.40 lm = the pantry base.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3021 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-w315b", "f" * 64
OA = A.OA
H = "Q-48 A owner height GF"


def _ln(code, room, ev, net=None, unit="lm", rng=None, ents=(), el=None, inputs=None):
    ln = BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit=unit, evidence_state=ev,
                      measured_net=net, element_id=el or f"W:{code}:{room}", floor="GF", room_id=room,
                      physical_element="skirting" if code == "FIN.SKIRTING" else "wall", gross=net,
                      bounded_range=rng, formula="w315b candidate", documents=[{"file": "w315b.dxf"}], rule_id="R",
                      rule_version="1",
                      rfi={"question": "height not established", "unlocks": room} if ev == "BLOCKED_RFI" else None,
                      inputs=inputs if inputs is not None else {}, notes="w315b",
                      deductions=[{"lm": 1.0, "what": "door"}] if code == "FIN.SKIRTING" and net else ())
    ln["source"]["entities"] = {"basis": "ROOM_BOUNDARY", "entities": [{"handle": h} for h in ents]}
    return BL.validate(ln)


def lines():
    return [_ln(A.TILE, "BX", "BLOCKED_RFI", unit="m2"),                       # another room's blank tile line
            _ln("FIN.SKIRTING", "EK", "SOURCE_DERIVED", 2.20, ents=("Ws", "S")),
            _ln("FIN.SKIRTING", "EZ", "SOURCE_DERIVED", 17.40, ents=("N", "Wn", "S", "D")),
            _ln("FIN.SKIRTING", "EZ", "BOUNDED_EXPOSURE", rng={"low": 0.0, "high": 2.50, "basis": "sill or floor"},
                ents=("WK", "WD"), el="W:FIN.SKIRTING:EZ:RANGE"),
            _ln("FIN.PAINT", "EK", "BLOCKED_RFI", unit="m2", ents=("Ws", "S")),
            _ln("FIN.PAINT", "EZ", "BLOCKED_RFI", unit="m2", ents=("N", "Wn", "S", "D")),
            _ln("FIN.PLASTER", "EZ", "BLOCKED_RFI", unit="m2", ents=("N", "Wn", "S", "D")),
            _ln("FIN.SKIRTING", "LV", "SOURCE_DERIVED", 11.0, ents=("L",))]       # a living room elsewhere


def _id(ls, room, code="FIN.SKIRTING", rng=False):
    return next(ln["line_id"] for ln in ls if ln["location"]["room_id"] == room and ln["item_code"] == code
                and (ln["evidence_state"] == "BOUNDED_EXPOSURE") == rng)


def _face(fid, length, net, ops=()):
    return {"face_id": fid, "wall_id": fid.split("|")[1], "length_m": length, "height_m": 3.65, "height_source": H,
            "openings": [{"id": o, "m2": m} for o, m in ops], "net_m2": net}


def doc(ls=None):
    ls = ls or lines()
    return {"schema": A.INPUTS_SCHEMA, "project": PID,
            "sources": [{"file": "w315b_faces.csv", "sha256": "a" * 64, "task": "T-W1", "merge_commit": "m1",
                         "checker_run": "c1"},
                        {"file": "w315b_base_ledger.csv", "sha256": "b" * 64, "task": "T-W2", "merge_commit": "m2",
                         "checker_run": "c2"}],
            "records": [
                {"kind": "HELD", "line_id": _id(ls, "BX", A.TILE), "room": "BX", "engine_room": "BX", "floor": "GF",
                 "task": "T-W1", "evidence_status": "HELD", "reasons": ["room level not drawn"]},
                {"kind": "ADD", "room": "K1", "engine_room": "EK", "floor": "GF", "task": "T-W1", "value": 29.16,
                 "evidence_status": OA, "assumption": "Q-48 A owner height GF 3.65",
                 "faces": [_face("K1|N", 3.00, 9.45, [("WK", 1.50)]), _face("K1|W", 2.40, 8.76),
                           _face("K1|S", 3.00, 10.95)],
                 "contour": {"contour_m": 10.80, "open_m": 2.40, "not_tiled_m": 0.0, "source": "w315b walk"},
                 "engine_room_split": [{"engine_room": "EK", "share": "WHOLE", "source": "w315b room split"},
                                       {"engine_room": "EZ", "share": "PART", "source": "w315b room split"}]}],
            "base_ownership": [
                {"line_id": _id(ls, "EK"), "item_code": "FIN.SKIRTING", "engine_room": "EK", "floor": "GF",
                 "tiled_room": "K1", "task": "T-W2", "action": "NOT_APPLICABLE", "before": 2.20,
                 "on_tiled_faces": [{"entity": "Ws", "face_id": "K1|W", "qty": 1.00},
                                    {"entity": "S", "face_id": "K1|S", "qty": 1.20}],
                 "evidence_status": OA, "assumption": "Q-37 A / Q-48 A full-height tile owns the base",
                 "basis": "counter cell wholly inside the pantry"},
                {"line_id": _id(ls, "EZ"), "item_code": "FIN.SKIRTING", "engine_room": "EZ", "floor": "GF",
                 "tiled_room": "K1", "task": "T-W2", "action": "SPLIT", "before": 17.40,
                 "on_tiled_faces": [{"entity": "N", "face_id": "K1|N", "qty": 3.00},
                                    {"entity": "Wn", "face_id": "K1|W", "qty": 1.40},
                                    {"entity": "S", "face_id": "K1|S", "qty": 1.00}],
                 "evidence_status": OA, "assumption": "Q-37 A / Q-48 A full-height tile owns the base",
                 "basis": "open zone in part inside the pantry"},
                {"line_id": _id(ls, "EZ", rng=True), "item_code": "FIN.SKIRTING", "engine_room": "EZ",
                 "floor": "GF", "tiled_room": "K1", "task": "T-W2", "action": "SPLIT", "before": [0.0, 2.50],
                 "on_tiled_faces": [{"entity": "WK", "face_id": "K1|N", "qty": 1.00}],
                 "evidence_status": OA, "assumption": "Q-37 A / Q-48 A full-height tile owns the base",
                 "basis": "the base below the pantry's sill window is tiled"}],
            "declared": {"HELD": {"lines": 1, "m2": 0.0}, "ADD": {"lines": 1, "m2": 29.16}}}


def run(d=None, ls=None):
    ls = ls or lines()
    d = A.load_inputs(d or doc(ls))
    ch, logs, faces = A.changes_for(d, ls)
    out, ident = A.integrate(ls, ch)
    rows = A.cross_trade(out, d, faces)
    return ls, ch, logs, faces, out, ident, rows


def _by(out):
    return {ln["line_id"]: ln for ln in out}


# ------------------------------------------------------------------------------------------------ normal
def test_pantry_base_carried_off_by_source_entity_open_plan_rest_kept():
    ls, ch, logs, _f, out, ident, rows = run()
    by = _by(out)
    ek = by[_id(ls, "EK")]
    assert ek["evidence_state"] == "NOT_APPLICABLE_WITH_EVIDENCE" and ek["measured_net"] is None
    assert ek["bounded_range"] is None and "NOT_APPLICABLE" in ek["notes"]
    ez = by[_id(ls, "EZ")]
    assert ez["evidence_state"] == "SOURCE_DERIVED" and ez["measured_net"] == pytest.approx(12.00, abs=1e-9)
    assert ez["deductions"][-1]["lm"] == pytest.approx(5.40, abs=1e-9)          # the tiled share named
    rg = by[_id(ls, "EZ", rng=True)]
    assert rg["evidence_state"] == "BOUNDED_EXPOSURE"
    assert (rg["bounded_range"]["low"], rg["bounded_range"]["high"]) == (0.0, pytest.approx(1.50, abs=1e-9))
    tile = [ln for ln in out if ln["item_code"] == A.TILE and ln["location"]["room_id"] == "EK"]
    assert len(tile) == 1 and tile[0]["measured_net"] == pytest.approx(29.16, abs=1e-9)
    assert ident["base_ownership_replaced"] == 3 and ident["added"] == 1
    assert logs[0]["base_ownership"]["actions"] == {"NOT_APPLICABLE": 1, "SPLIT": 2}
    # the living room's skirting, the paint and plaster lines: byte-identical
    b = _by(ls)
    for lid in (_id(ls, "LV"), _id(ls, "EK", "FIN.PAINT"), _id(ls, "EZ", "FIN.PAINT"), _id(ls, "EZ", "FIN.PLASTER")):
        assert A30.line_sha(by[lid]) == A30.line_sha(b[lid])
    assert all(r["paint_figure"] == "NONE" for r in rows)
    assert all(_id(ls, "EZ") in r["shared_engine_room_lines"] for r in rows if r["room"] == "K1")


def test_base_closure_by_hand():
    """2.20 (EK, whole) + 5.40 (EZ part) + 0.80 (no engine room) = 8.40 lm = the pantry base 3.00 + 2.40 + 3.00."""
    d = doc()
    parts = [sum(p["qty"] for p in b["on_tiled_faces"]) for b in d["base_ownership"][:2]]
    assert parts == [pytest.approx(2.20), pytest.approx(5.40)]
    assert sum(parts) + 0.80 == pytest.approx(3.00 + 2.40 + 3.00)


def test_write_lists_every_base_entity(tmp_path):
    ls = lines()
    d = A.load_inputs(doc(ls))
    ch, logs, faces = A.changes_for(d, ls)
    names, ident, led = A.write(tmp_path, ls, ch, logs, faces, d, released_lines=[])
    assert "V3_0_21_BASE.csv" in names
    assert len(led["base_ownership"]) == 6
    assert ident["diff"]["vs_v3_0_20"] == {"SAME": len(ls) - 3, "CHANGED": 3, "ADDED": 1}
    base_rows = [r for r in led["rows"] if r["piece"] == "BASE_OWNERSHIP"]
    assert {r["line_id"] for r in base_rows} == {_id(ls, "EK"), _id(ls, "EZ"), _id(ls, "EZ", rng=True)}
    assert all(r["assumption"].startswith("Q-37 A") for r in base_rows)


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut=None, ls=None):
    ls = ls or lines()
    d = doc(ls)
    if mut:
        mut(d)
    with pytest.raises((A.InputsError, ValueError)):
        run(d=d, ls=ls)


def _drop(lid_of):
    def m(d):
        d["base_ownership"] = [b for b in d["base_ownership"] if b["line_id"] != lid_of(lines())]
    return m


def test_unnamed_line_of_an_engine_room_wholly_inside_the_tiled_room_is_attributed_and_refused():
    """F-T315-C1: the counter cell's skirting names no room; the cell lies wholly inside the fully tiled pantry, so the
    line IS the pantry's: a figure on it is skirting under full-height tile, refused."""
    _bad(_drop(lambda ls: _id(ls, "EK")))


def test_unnamed_skirting_of_a_part_engine_room_without_its_split_refused():
    """F-T315-C2: the open zone's skirting runs on the pantry walls in part: without a base record its tiled share is
    unchecked (a possible double count), refused."""
    _bad(_drop(lambda ls: _id(ls, "EZ")))


def test_range_line_on_the_tiled_window_base_without_its_split_refused():
    _bad(_drop(lambda ls: _id(ls, "EZ", rng=True)))


def test_skirting_on_a_tiled_face_by_an_entity_the_line_does_not_name_refused():
    _bad(lambda d: d["base_ownership"][1]["on_tiled_faces"][0].update(entity="X9"))


def test_shared_room_note_instead_of_a_split_refused():
    def m(d):
        r = d["records"][1]
        r.pop("engine_room_split")
        r["engine_room_shared"] = True
    _bad(m)


def test_not_applicable_on_a_line_with_an_open_plan_rest_refused():
    """the whole open-zone line carried off would drop the dining's 12.00 lm (never 0 for the rest)."""
    _bad(lambda d: d["base_ownership"][1].update(action="NOT_APPLICABLE"))


def test_split_taking_the_whole_figure_refused():
    def m(d):
        d["base_ownership"][0]["action"] = "SPLIT"           # 2.20 of 2.20: the rest would be a 0 line
    _bad(m)


def test_stale_before_refused():
    _bad(lambda d: d["base_ownership"][1].update(before=17.50))


def test_part_on_a_face_that_is_not_tiled_refused():
    _bad(lambda d: d["base_ownership"][1]["on_tiled_faces"].append({"entity": "D", "face_id": "K1|E", "qty": 2.0}))


def test_base_record_for_an_engine_room_outside_the_split_refused():
    def m(d):
        d["records"][1]["engine_room_split"] = d["records"][1]["engine_room_split"][:1]
    _bad(m)


def test_unnamed_paint_figure_in_a_part_engine_room_refused():
    ls = lines()
    ls[5] = _ln("FIN.PAINT", "EZ", "PROVISIONAL", 60.0, unit="m2", ents=("N", "Wn", "S", "D"),
                el=ls[5]["location"]["element_id"])
    _bad(ls=ls)


def test_line_named_twice_refused():
    _bad(lambda d: d["base_ownership"].append(copy.deepcopy(d["base_ownership"][0])))


def test_part_entity_sum_not_the_whole_figure_for_not_applicable_refused():
    _bad(lambda d: d["base_ownership"][0]["on_tiled_faces"][1].update(qty=1.10))

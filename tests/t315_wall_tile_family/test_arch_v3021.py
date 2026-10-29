"""T-315: ARCH_TAKEOFF_V3.0.21 (the wall-tile family carried face by face from a merged face ledger) on a
hand-calculated NON-Alsenan villa (W315), normal and adverse.

Villa W315, owner manual method (each tiled face length x its height, less each opening's part inside the band), by
hand:
  B1 bath (1F), printed tile height 2.60: contour 2.40 x 3.00 = 10.80 m, all faces tiled. N 2.40 with window W1 0.60
     wide, sill 1.80, head 2.40 -> part inside [0, 2.60] = 0.60 x 0.60 = 0.36: 6.24 - 0.36 = 5.88; E 3.00 x 2.60 = 7.80;
     S 2.40 with door D1 0.80 x 2.10 = 1.68: 6.24 - 1.68 = 4.56; W 7.80. Gross 28.08, net 26.04 m2 (FILL, the
     candidate's blank tile line).
  B2 bath (GF): the room level is not drawn: the tile line stays BLANK (HELD), never 0.
  P1 open pantry (GF), owner height 3.65: box 3.00 x 2.00 = contour 10.00 m; east edge OPEN 2.00 (tiles nothing);
     counters against the north (3.00) and west (2.00) walls (hosts, whole wall); the south wall 3.00 hosts nothing ->
     not tiled. N 3.00 x 3.65 = 10.95 less window W2 1.00 x (2.50 - 1.00) = 1.50 -> 9.45; W 2.00 x 3.65 = 7.30. Net
     16.75 m2 on 5.00 m of wall (closure 5.00 + open 2.00 + not tiled 3.00 = 10.00). The candidate has NO tile line in
     P1 -> ONE new line (ADD).
Family totals: blank 2 lines -> 26.04 + 16.75 = 42.79 m2 in 2 valued lines, 1 blank.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3021 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-w315", "e" * 64
OA = A.OA
DOCS = [{"file": "w315.dxf"}]


def _ln(code, room, ev, net=None, floor="1F", el=None):
    held = ev not in BL.QUANTITY_STATES
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m2", evidence_state=ev,
                        measured_net=net, element_id=el or f"W:{code}:{room}", floor=floor, room_id=room,
                        physical_element="wall_tile" if code == A.TILE else "wall face",
                        formula="w315 candidate", documents=DOCS, rule_id="R", rule_version="1",
                        rfi={"question": "tile height not established", "unlocks": room} if ev == "BLOCKED_RFI" else None,
                        inputs={"room": room}, notes="w315")


def lines():
    return [_ln(A.TILE, "B1", "BLOCKED_RFI"), _ln(A.TILE, "B2", "BLOCKED_RFI", floor="GF"),
            _ln("FIN.PAINT", "B1", "NOT_APPLICABLE_WITH_EVIDENCE"),
            _ln("FIN.PAINT", "B2", "NOT_APPLICABLE_WITH_EVIDENCE", floor="GF"),
            _ln("FIN.PLASTER", "B1", "BLOCKED_RFI"),
            _ln("FIN.PAINT", "P1", "BLOCKED_RFI", floor="GF"),
            _ln("FIN.PLASTER", "P1", "BLOCKED_RFI", floor="GF"),
            _ln("FIN.CEILING", "P1", "PROVISIONAL", 6.0, floor="GF")]


def _ids(ls):
    return {(ln["location"]["room_id"], ln["item_code"]): ln["line_id"] for ln in ls}


def _face(fid, length, h, net, ops=(), src="printed tile height (detail T1)"):
    return {"face_id": fid, "wall_id": fid.split("|")[1], "length_m": length, "height_m": h, "height_source": src,
            "openings": [{"id": o, "m2": m} for o, m in ops], "net_m2": net}


def doc(ls=None):
    ids = _ids(ls or lines())
    b1 = [_face("B1|N", 2.40, 2.60, 5.88, [("W1", 0.36)]), _face("B1|E", 3.00, 2.60, 7.80),
          _face("B1|S", 2.40, 2.60, 4.56, [("D1", 1.68)]), _face("B1|W", 3.00, 2.60, 7.80)]
    p1 = [_face("P1|N", 3.00, 3.65, 9.45, [("W2", 1.50)], "Q-48 A owner height GF"),
          _face("P1|W", 2.00, 3.65, 7.30, (), "Q-48 A owner height GF")]
    return {"schema": A.INPUTS_SCHEMA, "project": PID,
            "sources": [{"file": "w315_faces.csv", "sha256": "a" * 64, "task": "T-W1", "merge_commit": "m1",
                         "checker_run": "c1"}],
            "records": [
                {"kind": "FILL", "line_id": ids[("B1", A.TILE)], "room": "B1", "engine_room": "B1", "floor": "1F",
                 "task": "T-W1", "value": 26.04, "evidence_status": A.DC, "faces": b1,
                 "contour": {"contour_m": 10.80, "open_m": 0.0, "not_tiled_m": 0.0, "source": "w315 walk"}},
                {"kind": "HELD", "line_id": ids[("B2", A.TILE)], "room": "B2", "engine_room": "B2", "floor": "GF",
                 "task": "T-W1", "evidence_status": "HELD", "reasons": ["room level not drawn"]},
                {"kind": "ADD", "room": "P1", "engine_room": "P1", "floor": "GF", "task": "T-W1", "value": 16.75,
                 "evidence_status": OA, "assumption": "Q-48 A owner height GF 3.65", "faces": p1,
                 "contour": {"contour_m": 10.00, "open_m": 2.00, "not_tiled_m": 3.00, "source": "w315 walk"}}],
            "declared": {"FILL": {"lines": 1, "m2": 26.04}, "HELD": {"lines": 1, "m2": 0.0},
                         "ADD": {"lines": 1, "m2": 16.75}}}


def run(d=None, ls=None, tmp=None):
    ls = ls or lines()
    d = A.load_inputs(d or doc(ls))
    ch, logs, faces = A.changes_for(d, ls)
    out, ident = A.integrate(ls, ch)
    return ls, ch, logs, faces, out, ident, d


# ------------------------------------------------------------------------------------------------ normal
def test_hand_fixture_fill_held_add():
    ls, ch, logs, faces, out, ident, _ = run()
    by = {(ln["location"]["room_id"], ln["item_code"]): ln for ln in out}
    b1 = by[("B1", A.TILE)]
    assert b1["line_id"] == _ids(ls)[("B1", A.TILE)]                  # same line id
    assert b1["evidence_state"] == "SOURCE_DERIVED" and b1["measured_net"] == pytest.approx(26.04, abs=1e-9)
    assert b1["gross"] == pytest.approx(28.08, abs=1e-9)
    assert b1["rfi"] is None
    om = b1["calculation"]["inputs"]["owner_manual_method"]
    assert sorted((d["opening"], d["m2"]) for d in om["deductions"]) == [("D1", 1.68), ("W1", 0.36)]
    b2 = by[("B2", A.TILE)]
    assert b2["evidence_state"] == "BLOCKED_RFI" and b2["measured_net"] is None and b2["bounded_range"] is None
    p1 = by[("P1", A.TILE)]
    assert p1["evidence_state"] == "PROVISIONAL" and p1["measured_net"] == pytest.approx(16.75, abs=1e-9)
    assert p1["calculation"]["inputs"]["assumption"].startswith("Q-48 A")
    assert ident["replaced"] == 1 and ident["added"] == 1 and len(out) == len(ls) + 1
    assert ident["wall_tile_family"] == {"lines": 3, "valued": 2, "blank": 1, "m2": 42.79}
    assert logs[0]["kinds"] == {"FILL": 1, "HELD": 1, "ADD": 1}
    assert len(faces) == 6 and len({f["face_id"] for f in faces}) == 6


def test_every_other_line_byte_identical_and_held_line_untouched():
    ls, ch, _l, _f, out, ident, _ = run()
    from engine.source import arch_v30 as A30
    b = {ln["line_id"]: ln for ln in ls}
    changed = {c["after"]["line_id"] for c in ch}
    for ln in out:
        if ln["line_id"] not in changed:
            assert A30.line_sha(ln) == A30.line_sha(b[ln["line_id"]])
    assert ident["outside_rows_identical_to_v3_0_20"] == len(ls) - 1


def test_cross_trade_rows_tile_once_no_paint_backing_named():
    ls, ch, _l, faces, out, _i, d = run()
    rows = A.cross_trade(out, d, faces)
    tiled = [r for r in rows if r["tile_net_m2"] != "HELD"]
    assert len(tiled) == 6 and all(r["paint_figure"] == "NONE" for r in rows)
    assert all("OWN LINE" in r["backing"] for r in rows)
    assert any(r["tile_line"] == _ids(ls)[("B2", A.TILE)] and r["tile_net_m2"] == "HELD" for r in rows)


def test_write_files(tmp_path):
    ls, ch, logs, faces, _o, _i, d = run()
    names, ident, led = A.write(tmp_path, ls, ch, logs, faces, d, released_lines=[])
    assert "V3_0_21_CROSS_TRADE.csv" in names and "V3_0_21_FACES.csv" in names
    assert led["integration_package"] is True and led["released_default"] is False
    assert {r["action"] for r in led["rows"]} == {"REPLACE", "ADD", "KEEP_HELD"}
    assert ident["diff"]["vs_v3_0_20"] == {"SAME": len(ls) - 1, "CHANGED": 1, "ADDED": 1}


def test_paint_on_the_not_tiled_pantry_wall_is_named_not_refused():
    ls = lines()
    ls[5] = _ln("FIN.PAINT", "P1", "PROVISIONAL", 10.95, floor="GF", el=ls[5]["location"]["element_id"])
    _ls, _c, _l, faces, out, _i, d = run(ls=ls)
    rows = A.cross_trade(out, d, faces)
    assert all(r["paint_figure"].startswith("FIGURE ON THE NOT-TILED") for r in rows if r["engine_room"] == "P1")


# ------------------------------------------------------------------------------------------------ adverse
def _bad(mut, err=A.InputsError, ls=None):
    ls = ls or lines()
    d = doc(ls)
    mut(d)
    with pytest.raises((err, ValueError)):
        dd = A.load_inputs(d)
        ch, logs, faces = A.changes_for(dd, ls)
        out, _ = A.integrate(ls, ch)
        A.cross_trade(out, dd, faces)


def test_held_line_carried_as_zero_refused():
    _bad(lambda d: d["records"][1].update(value=0.0))


def test_paint_figure_on_a_fully_tiled_bath_refused():
    ls = lines()
    ls[2] = _ln("FIN.PAINT", "B1", "PROVISIONAL", 28.08, el=ls[2]["location"]["element_id"])
    _bad(lambda d: None, ls=ls)


def test_paint_figure_in_a_held_wet_room_refused():
    ls = lines()
    ls[3] = _ln("FIN.PAINT", "B2", "PROVISIONAL", 20.0, floor="GF", el=ls[3]["location"]["element_id"])
    _bad(lambda d: None, ls=ls)


def test_face_in_two_lines_refused():
    _bad(lambda d: d["records"][2]["faces"].append(copy.deepcopy(d["records"][0]["faces"][1])))


def test_opening_twice_in_one_room_refused():
    def m(d):
        f = d["records"][0]["faces"][1]
        f["openings"] = [{"id": "D1", "m2": 1.68}]
        f["net_m2"] = 7.80 - 1.68
    _bad(m)


def test_height_in_mm_refused():
    def m(d):
        f = d["records"][0]["faces"][1]
        f["height_m"], f["net_m2"] = 2600, 3.00 * 2600
    _bad(m)


def test_height_without_source_refused():
    _bad(lambda d: d["records"][0]["faces"][1].update(height_source=""))


def test_universal_default_height_needs_a_source_and_a_missing_height_is_held():
    _bad(lambda d: d["records"][0]["faces"][1].update(height_m=None))


def test_face_net_not_length_times_height_less_openings_refused():
    _bad(lambda d: d["records"][0]["faces"][0].update(net_m2=6.24))        # W1 not deducted


def test_value_not_the_sum_of_faces_refused():
    def m(d):
        d["records"][0]["value"] = 28.08
        d["declared"]["FILL"]["m2"] = 28.08
    _bad(m)


def test_room_not_closing_refused():
    _bad(lambda d: d["records"][2]["contour"].update(not_tiled_m=0.0))     # the pantry south wall dropped silently


def test_open_edge_tiled_refused_by_closure():
    def m(d):
        r = d["records"][2]
        r["faces"].append(_face("P1|OPEN", 2.00, 3.65, 7.30, (), "Q-48 A owner height GF"))
        r["value"] = 24.05
        d["declared"]["ADD"]["m2"] = 24.05
    _bad(m)                                                                 # 7.00 + open 2.00 + 3.00 != 10.00


def test_add_into_a_room_with_a_tile_line_refused():
    def m(d):
        r = d["records"][2]
        r["engine_room"] = "B2"
    _bad(m)


def test_candidate_tile_line_not_named_refused():
    def m(d):
        d["records"].pop(1)
        d["declared"]["HELD"]["lines"] = 0
    _bad(m)


def test_stale_fill_on_a_line_with_a_figure_refused():
    ls = lines()
    ls[0] = _ln(A.TILE, "B1", "PROVISIONAL", 25.0, el=ls[0]["location"]["element_id"])
    _bad(lambda d: None, ls=ls)


def test_verified_without_checker_run_refused():
    _bad(lambda d: d["records"][0].update(evidence_status=A.VER))


def test_owner_approved_without_its_source_refused():
    _bad(lambda d: d["records"][2].update(assumption=None))


def test_declared_totals_drift_refused():
    _bad(lambda d: d["declared"]["ADD"].update(m2=16.80))


def test_second_tile_line_in_one_room_refused_by_family_check():
    ls, ch, *_ = run()
    out, _ = A.integrate(ls, ch)
    dup = copy.deepcopy(next(ln for ln in out if ln["location"]["room_id"] == "B1" and ln["item_code"] == A.TILE))
    dup["line_id"] = "L-dup"
    with pytest.raises(ValueError):
        A.check_tile_family(out + [dup])


def test_translation_of_ids_and_order_does_not_change_totals():
    """mirror / rotation have no meaning on a face ledger (lengths only): the invariant is that the face order and the
    face ids do not change the line figure."""
    ls = lines()
    d = doc(ls)
    d["records"][0]["faces"].reverse()
    for f in d["records"][0]["faces"]:
        f["face_id"] = f["face_id"].replace("B1|", "B1|M-")
    _ls, _c, _l, _f, out, _i, _d = run(d=d, ls=ls)
    b1 = next(ln for ln in out if ln["location"]["room_id"] == "B1" and ln["item_code"] == A.TILE)
    assert b1["measured_net"] == pytest.approx(26.04, abs=1e-9)


def test_skirting_figure_on_a_full_height_tiled_bath_refused():
    ls = lines() + [_ln("FIN.SKIRTING", "B1", "SOURCE_DERIVED", 9.2)]
    _bad(lambda d: None, ls=ls)


def test_shared_engine_room_line_naming_no_room_is_not_attributed():
    """an open zone (dining + pantry) in one engine room: a room-level paint line with a figure that names no room is
    listed as not attributable to the pantry, never refused and never counted as the pantry's."""
    ls = lines()
    zone = _ln("FIN.PAINT", "P1", "PROVISIONAL", 55.0, floor="GF", el="W:FIN.PAINT:P1:ZONE")
    zone["calculation"]["inputs"] = {}
    ls.append(zone)
    d = doc(ls)
    d["records"][2]["engine_room_shared"] = True
    d["records"][2]["contour"]["not_tiled_m"] = 3.0
    _ls, _c, _l, faces, out, _i, dd = run(d=d, ls=ls)
    rows = [r for r in A.cross_trade(out, dd, faces) if r["engine_room"] == "P1"]
    assert all(zone["line_id"] in r["shared_engine_room_lines"] for r in rows)
    assert all(zone["line_id"] not in r["paint_lines"] for r in rows)


def test_same_zone_line_not_shared_is_attributed_and_checked():
    """the same room-level line in an engine room that is the pantry's alone belongs to the pantry: with every pantry
    wall tiled (no not-tiled face) its figure is paint under tile and refused."""
    ls = lines()
    zone = _ln("FIN.PAINT", "P1", "PROVISIONAL", 55.0, floor="GF", el="W:FIN.PAINT:P1:ZONE")
    zone["calculation"]["inputs"] = {}
    ls.append(zone)

    def m(d):
        r = d["records"][2]
        r["faces"].append(_face("P1|S", 3.00, 3.65, 10.95, (), "Q-48 A owner height GF"))
        r["contour"]["not_tiled_m"] = 0.0
        r["value"] = 27.70
        d["declared"]["ADD"]["m2"] = 27.70
    _bad(m, ls=ls)

"""T-331: ARCH_TAKEOFF_V3.0.22 (the plaster backing behind the wall tile carried face by face into the blank
FIN.PLASTER lines, bound to the room's own wall-tile line, the HELD band beside the figure) on a hand-calculated
NON-Alsenan villa (W331), normal and adverse.

Villa W331, by hand:
  B1 bath (1F): contour 2.00 x 2.50 = 9.00 m, every face tiled, printed tile top 2.40 m, slab soffit 3.00 m.
     N 2.00 with window W1 0.60 wide, sill 1.80, head 2.70: part inside [0, 2.40] = 0.60 x 0.60 = 0.36 ->
       2.00 x 2.40 - 0.36 = 4.44; E 2.50 x 2.40 = 6.00; S 2.00 with door D1 0.80 x 2.10 = 1.68 -> 4.80 - 1.68 = 3.12;
       W 6.00. Tile (V3.0.21 FILL) = backing = 19.56 m2, gross 21.60, deductions W1 0.36 + D1 1.68 = 2.04.
     Band above the tile: owner method (plaster top = tile top) 0; drawing-derived (plaster to the soffit) = 9.00 x
       0.60 = 5.40 less W1's part inside [2.40, 3.00] = 0.60 x 0.30 = 0.18 -> 5.22 m2 (N 1.02, E 1.50, S 1.20, W
       1.50), HELD: no specification says whether plaster runs above the ceiling.
  B2 bath (GF): the room level is not drawn: tile and backing stay BLANK (HELD), drawing band 0 .. 4.00, never 0.
  L1 living (GF): dry; its plaster and paint lines carry 30.0 m2 each and are not touched.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402
from engine.source import arch_v3021 as A21  # noqa: E402
from engine.source import arch_v3022 as A  # noqa: E402
from engine.source import boq_line as BL  # noqa: E402

PID, REV = "villa-w331", "f" * 64
DOCS = [{"file": "w331.dxf"}]
TILE_H = "printed tile height (detail T7)"


def _ln(code, room, ev, net=None, floor="1F"):
    return BL.make_line(project_id=PID, revision_set_sha256=REV, item_code=code, unit="m2", evidence_state=ev,
                        measured_net=net, element_id=f"W:{code}:{room}", floor=floor, room_id=room,
                        physical_element="wall_tile" if code == A.TILE else "wall face", formula="w331 candidate",
                        documents=DOCS, rule_id="R", rule_version="1",
                        rfi={"question": "wall finish height not established", "unlocks": room}
                        if ev == "BLOCKED_RFI" else None, inputs={"room": room}, notes="w331")


def lines_3020():
    return [_ln(A.TILE, "B1", "BLOCKED_RFI"), _ln(A.TILE, "B2", "BLOCKED_RFI", floor="GF"),
            _ln(A.PLASTER, "B1", "BLOCKED_RFI"), _ln(A.PLASTER, "B2", "BLOCKED_RFI", floor="GF"),
            _ln("FIN.PAINT", "B1", "NOT_APPLICABLE_WITH_EVIDENCE"),
            _ln("FIN.PAINT", "B2", "NOT_APPLICABLE_WITH_EVIDENCE", floor="GF"),
            _ln(A.PLASTER, "L1", "PROVISIONAL", 30.0, floor="GF"), _ln("FIN.PAINT", "L1", "PROVISIONAL", 30.0, floor="GF")]


def _ids(ls):
    return {(ln["location"]["room_id"], ln["item_code"]): ln["line_id"] for ln in ls}


B1_FACES = [("B1|N", 2.00, 4.44, [("W1", 0.36)], (0.0, 1.02)), ("B1|E", 2.50, 6.00, [], (0.0, 1.50)),
            ("B1|S", 2.00, 3.12, [("D1", 1.68)], (0.0, 1.20)), ("B1|W", 2.50, 6.00, [], (0.0, 1.50))]


def _tile_doc(ls):
    ids = _ids(ls)
    faces = [{"face_id": f, "wall_id": f.split("|")[1], "length_m": ln, "height_m": 2.40, "height_source": TILE_H,
              "openings": [{"id": o, "m2": m} for o, m in ops], "net_m2": net} for f, ln, net, ops, _b in B1_FACES]
    return {"schema": A21.INPUTS_SCHEMA, "project": PID,
            "sources": [{"file": "w331_tile.csv", "sha256": "a" * 64, "task": "T-W1", "merge_commit": "m1",
                         "checker_run": "c1"}],
            "records": [{"kind": "FILL", "line_id": ids[("B1", A.TILE)], "room": "B1", "engine_room": "B1",
                         "floor": "1F", "task": "T-W1", "value": 19.56, "evidence_status": A.DC, "faces": faces,
                         "contour": {"contour_m": 9.0, "open_m": 0.0, "not_tiled_m": 0.0, "source": "w331 walk"}},
                        {"kind": "HELD", "line_id": ids[("B2", A.TILE)], "room": "B2", "engine_room": "B2",
                         "floor": "GF", "task": "T-W1", "evidence_status": "HELD", "reasons": ["room level not drawn"]}],
            "declared": {"FILL": {"lines": 1, "m2": 19.56}, "HELD": {"lines": 1, "m2": 0.0}}}


def lines_3021():
    ls = lines_3020()
    d = A21.load_inputs(_tile_doc(ls))
    ch, _logs, _f = A21.changes_for(d, ls)
    return A21.integrate(ls, ch)[0]


def _bface(fid, ln, net, ops, band):
    return {"face_id": fid, "wall_id": fid.split("|")[1], "length_m": ln, "height_m": 2.40, "height_source": TILE_H,
            "openings": [{"id": o, "m2": m} for o, m in ops], "net_m2": net, "tile_net_m2": net, "band_owner_m2": 0.0,
            "band_dwg": list(band)}


def doc(ls):
    ids = _ids(ls)
    return {"schema": A.INPUTS_SCHEMA, "project": PID,
            "sources": [{"file": "w331_backing.csv", "sha256": "b" * 64, "task": "T-W2", "merge_commit": "m2",
                         "checker_run": "c2"}],
            "records": [
                {"kind": "FILL", "line_id": ids[("B1", A.PLASTER)], "tile_line_id": ids[("B1", A.TILE)], "room": "B1",
                 "engine_room": "B1", "floor": "1F", "task": "T-W2", "value": 19.56, "evidence_status": A.OA,
                 "assumption": "UP-FIN-PAINT-001 substrate; coat per the owner's answer",
                 "faces": [_bface(*f) for f in B1_FACES],
                 "band": {"owner_m2": 0.0, "owner_basis": "owner plaster top = tile top", "drawing_low": 0.0,
                          "drawing_high": 5.22, "status": "HELD", "reason": "no specification of plaster above the "
                                                                          "ceiling"}},
                {"kind": "HELD", "line_id": ids[("B2", A.PLASTER)], "tile_line_id": ids[("B2", A.TILE)], "room": "B2",
                 "engine_room": "B2", "floor": "GF", "task": "T-W2", "evidence_status": "HELD",
                 "reasons": ["room level not drawn"],
                 "band": {"owner_m2": 0.0, "owner_basis": "with the tile height", "drawing_low": 0.0,
                          "drawing_high": 4.0, "status": "HELD", "reason": "room level not drawn"}}],
            "declared": {"FILL": {"lines": 1, "m2": 19.56}, "HELD": {"lines": 1}}}


def run(d=None, ls=None):
    ls = ls or lines_3021()
    d = A.load_inputs(d or doc(ls))
    ch, logs, faces = A.changes_for(d, ls)
    out, ident = A.integrate(ls, ch, d)
    return ls, ch, logs, faces, out, ident, d


# ------------------------------------------------------------------------------------------------ normal
def test_hand_fixture_fill_with_band_and_held():
    ls, ch, logs, faces, out, ident, _ = run()
    by = {(ln["location"]["room_id"], ln["item_code"]): ln for ln in out}
    p = by[("B1", A.PLASTER)]
    assert p["line_id"] == _ids(ls)[("B1", A.PLASTER)]
    assert p["evidence_state"] == "PROVISIONAL" and p["measured_net"] == pytest.approx(19.56, abs=1e-9)
    assert p["gross"] == pytest.approx(21.60, abs=1e-9) and p["rfi"] is None
    assert sorted((d["opening_id"], d["area"], d["unit"]) for d in p["deductions"]) == [("D1", 1.68, "m2"),
                                                                                        ("W1", 0.36, "m2")]
    assert p["gross"] - sum(d["area"] for d in p["deductions"]) == pytest.approx(p["measured_net"], abs=5e-4)
    band = p["calculation"]["inputs"]["wet_backing_v3022"]["band_above_tile"]
    assert band["owner_method_m2"] == 0.0 and band["drawing_derived_m2"] == {"low": 0.0, "high": 5.22}
    assert band["status"] == "HELD" and band["release_status"] == "NOT RELEASED"
    assert "0.0 .. 5.22 m2 HELD" in p["notes"] and "0.0 .. 5.22 m2 HELD" in p["calculation"]["formula"]
    assert "0 by rule (UP-FIN-PAINT-001)" in p["notes"]
    h = by[("B2", A.PLASTER)]
    assert h["evidence_state"] == "BLOCKED_RFI" and h["measured_net"] is None and h["bounded_range"] is None
    assert "HELD with the tile height" in h["notes"] and "0.0 .. 4.0 m2 HELD" in h["notes"]
    assert ident["filled"] == 1 and ident["held_noted"] == 1 and ident["added"] == 0
    assert ident["wet_backing_family"] == {"lines": 2, "valued": 1, "blank": 1, "m2": 19.56}
    assert logs[0]["band_drawing_m2"] == {"low": 0.0, "high": 9.22} and logs[0]["band_owner_m2"] == 0.0
    assert len(faces) == 4 and all(f["closure_m2"] == 0.0 for f in faces)


def test_backing_equals_tile_and_dry_lines_byte_identical():
    ls, ch, _l, _f, out, ident, _ = run()
    by = {(ln["location"]["room_id"], ln["item_code"]): ln for ln in out}
    assert by[("B1", A.PLASTER)]["measured_net"] == by[("B1", A.TILE)]["measured_net"]
    b = {ln["line_id"]: ln for ln in ls}
    changed = {c["after"]["line_id"] for c in ch}
    assert len(changed) == 2
    for ln in out:
        if ln["line_id"] not in changed:
            assert A30.line_sha(ln) == A30.line_sha(b[ln["line_id"]])
    assert ident["outside_rows_identical_to_v3_0_21"] == len(ls) - 2


def test_mirror_order_same_result():
    ls = lines_3021()
    d = doc(ls)
    d["records"][0]["faces"] = list(reversed(d["records"][0]["faces"]))
    *_x, out_m, _i, _d = run(d, ls)
    *_y, out_n, _j, _e = run(None, ls)
    pm = next(x for x in out_m if x["location"]["room_id"] == "B1" and x["item_code"] == A.PLASTER)
    pn = next(x for x in out_n if x["location"]["room_id"] == "B1" and x["item_code"] == A.PLASTER)
    assert pm["measured_net"] == pn["measured_net"] and pm["gross"] == pn["gross"]


def test_cross_trade_two_layers_paint_zero_by_rule():
    _ls, _ch, _l, _f, out, _i, d = run()
    rows = A.cross_trade(out, d)
    assert len(rows) == 2
    assert all("two layers by rule" in r["layers"] and r["paint"].startswith("0 BY RULE (UP-FIN-PAINT-001") for r in rows)


def test_write_files(tmp_path):
    ls, ch, logs, faces, _o, _i, d = run()
    names, ident, led = A.write(tmp_path, ls, ch, logs, faces, d, released_lines=[])
    assert "V3_0_22_BOQ_LINES.json" in names and "V3_0_22_CROSS_TRADE.csv" in names
    assert ident["diff"]["vs_v3_0_21"] == {"SAME": len(ls) - 2, "CHANGED": 1, "CHANGED_TEXT_ONLY": 1}
    assert led["integration_package"] is True and led["released_default"] is False
    assert "WALL_TILE_BACKING" not in led["waiting_pieces"]
    csv_text = (tmp_path / "V3_0_22_INTEGRATION_LEDGER.csv").read_text(encoding="utf-8")
    assert "0.0 .. 5.22" in csv_text and "D1 1.68" in csv_text


# ------------------------------------------------------------------------------------------------ adverse
def _refused(mut, match=None, err=A.InputsError):
    ls = lines_3021()
    d = doc(ls)
    mut(d, ls)
    with pytest.raises(err, match=match):
        run(d, ls)


def test_band_written_as_zero_refused():
    def m(d, _ls):
        d["records"][0]["band"]["drawing_high"] = 0.0
    _refused(m, "band written as 0")


def test_band_bare_number_or_missing_refused():
    def m(d, _ls):
        d["records"][0]["band"] = 0
    _refused(m, "never a bare number")

    def m2(d, _ls):
        d["records"][0].pop("band")
    _refused(m2, "never a bare number")


def test_band_range_not_held_refused():
    def m(d, _ls):
        d["records"][0]["band"]["status"] = "DRAWING-CONFIRMED"
    _refused(m, "HELD with its reason")


def test_backing_on_a_paint_line_refused():
    def m(d, ls):
        d["records"][0]["line_id"] = _ids(ls)[("B1", "FIN.PAINT")]
    _refused(m, "not FIN.PLASTER")


def test_held_line_filled_refused():
    def m(d, ls):
        r = d["records"][1]
        r.update(kind="FILL", value=19.56, evidence_status=A.OA, assumption="x",
                 faces=[_bface(f"B2|{x}", *rest) for x, (_f, *rest) in zip("NESW", B1_FACES)])
        r["band"]["drawing_high"] = 5.22
        d["declared"] = {"FILL": {"lines": 2, "m2": 39.12}, "HELD": {"lines": 0}}
    _refused(m, "a held line is never filled")


def test_held_record_with_figure_refused():
    def m(d, _ls):
        d["records"][1]["value"] = 10.0
    _refused(m, "carries no figure")


def test_one_face_filled_twice_refused():
    def m(d, _ls):
        d["records"][0]["faces"].append(copy.deepcopy(d["records"][0]["faces"][1]))
    _refused(m, "backed twice")


def test_face_not_the_tile_face_refused():
    def m(d, _ls):
        f = d["records"][0]["faces"][1]
        f.update(length_m=2.60, net_m2=6.24, tile_net_m2=6.24)
        d["records"][0]["value"] = 19.80
        d["declared"]["FILL"]["m2"] = 19.80
    _refused(m, "differs from the tile line")


def test_backing_differs_from_tile_on_a_face_refused():
    def m(d, _ls):
        d["records"][0]["faces"][1]["tile_net_m2"] = 5.90
    _refused(m, "backing - tile = 0")


def test_height_in_mm_refused():
    def m(d, _ls):
        d["records"][0]["faces"][1]["height_m"] = 2400
    _refused(m, "mm, a typo")


def test_tile_line_without_record_refused():
    def m(d, _ls):
        d["records"].pop(1)
        d["declared"]["HELD"] = {"lines": 0}
    _refused(m, "no backing record")


def test_stale_plaster_line_refused():
    ls = lines_3021()
    d = doc(ls)
    for ln in ls:
        if ln["line_id"] == d["records"][0]["line_id"]:
            ln.update(evidence_state="PROVISIONAL", measured_net=12.0, rfi=None)
    with pytest.raises(A.InputsError, match="only a blank plaster line"):
        run(d, ls)


def test_paint_figure_on_backed_room_refused():
    ls, _ch, _l, _f, out, _i, d = run()
    for ln in out:
        if ln["location"]["room_id"] == "B1" and ln["item_code"] == "FIN.PAINT":
            ln.update(evidence_state="PROVISIONAL", measured_net=5.0)
    with pytest.raises(ValueError, match="no paint over porcelain"):
        A.cross_trade(out, d)


def test_declared_total_mismatch_refused():
    def m(d, _ls):
        d["declared"]["FILL"]["m2"] = 20.0
    _refused(m, "declared FILL")


# ------------------------------------------------------------------------------------------------ note completion
def _noted(full, cut_at=60):
    ln = _ln("FIN.SKIRTING", "L1", "NOT_APPLICABLE_WITH_EVIDENCE", floor="GF")
    ln["unit"] = "lm"
    ln["calculation"]["inputs"]["base_ownership_v3021"] = {"assumption": full}
    ln["notes"] = f"w331; ARCH_TAKEOFF_V3.0.21: NOT_APPLICABLE: skirting on the tile of P1 (one owner per base, " \
                  f"{full[:cut_at]}); entities"
    return ln


def test_note_completed_from_the_line_record():
    full = "one owner per wall base: full-height wall tile owns the base (rule X / rule Y), owner-approved source Z"
    ln = _noted(full)
    after = A.note_line(ln, {"line_id": ln["line_id"], "task": "T-W2", "field": "base_ownership_v3021"})
    assert f"{full});" in after["notes"] and after["notes"].count(full) == 1
    assert after["calculation"]["inputs"]["note_completion_v3022"]["cut_at_chars"] == 60
    a, b = copy.deepcopy(ln), copy.deepcopy(after)
    for x in (a, b):
        x.pop("notes")
        x.pop("calculation")
    assert a == b


def test_note_already_complete_refused():
    full = "one owner per wall base: full-height wall tile owns the base (rule X / rule Y), owner-approved source Z"
    ln = _noted(full, cut_at=len(full))
    with pytest.raises(A.InputsError, match="nothing cut"):
        A.note_line(ln, {"line_id": ln["line_id"], "task": "T-W2", "field": "base_ownership_v3021"})
